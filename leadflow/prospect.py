"""LEADFLOW Prospect — trouve des TPE autour de Lyon, audite leur présence web, estime la prestation à vendre.

Usage : python3 prospect.py [--lat 45.764 --lon 4.8357 --radius 5000 --limit 100 --departement 69]
Option : GOOGLE_PLACES_API_KEY=... python3 prospect.py  -> audit des fiches Google (payant, voir README).
Sorties : prospects.json + dashboard.html.

Sources : OpenStreetMap via Overpass (ODbL, attribution requise), annuaire officiel des entreprises
(recherche-entreprises.api.gouv.fr, données SIRENE ouvertes), Google Places API (optionnel).
"""
import argparse, json, math, os, re, ssl, time, unicodedata, urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date

UA = "LeadflowAudit/0.2 (audit de visibilite locale)"
OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter",
            "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]
SIRENE = "https://recherche-entreprises.api.gouv.fr/search"
PLACES = "https://places.googleapis.com/v1/places:searchText"
MATCH_M = 150  # distance max (m) pour considérer que deux sources parlent du même établissement

SEGMENTS = {
    "artisan": ['craft~"^(plumber|electrician|roofer|carpenter|painter|hvac|locksmith|tiler|glaziery|plasterer|builder|stonemason)$"'],
    "restaurant": ['amenity~"^(restaurant|cafe|fast_food)$"'],
    "beauté": ['shop~"^(hairdresser|beauty|barber)$"'],
}

# Prix indicatifs HT (milieu de fourchette du plan) : (installation, mensuel)
OFFERS = {
    "site": ("Site vitrine", 600, 29),
    "refonte": ("Refonte site obsolète", 900, 0),
    "reservation": ("Réservation en ligne", 350, 39),
    "menu": ("Menu numérique", 170, 19),
    "fiche": ("Optimisation fiche locale", 200, 39),
}

BOOKING = re.compile(r"planity|treatwell|kiute|calendly|zenchef|thefork|lafourchette|booksy|r[ée]serv|prendre (un )?rendez|\brdv\b|booking", re.I)
YEAR = re.compile(r"(?:©|&copy;|copyright)\D{0,20}((?:19|20)\d\d)", re.I)
MENU = re.compile(r"menu|carte|plats?|dejeuner|déjeuner|formule", re.I)
LOCAL = re.compile(r"\b(69\d{3}|lyon|villeurbanne)\b")


# ---------- utilitaires ----------

def norm(s):
    """'L’Atelier Vintage' -> 'l atelier vintage' (sans accents, ponctuation retirée)."""
    s = unicodedata.normalize("NFKD", re.sub(r"[-'’]", " ", s)).encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9 ]", "", s).split())


def dist_m(lat1, lon1, lat2, lon2):
    x = math.radians(lon2 - lon1) * math.cos(math.radians((lat1 + lat2) / 2))
    return 6_371_000 * math.hypot(x, math.radians(lat2 - lat1))


def get_json(url, data=None, headers=None, timeout=30):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})})
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def fetch(url, timeout=8):
    """-> (html, url finale). Lève en cas d'échec."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as r:
        raw = r.read(500_000)
        try:
            return raw.decode("utf-8"), r.geturl()
        except UnicodeDecodeError as e:
            if e.start >= len(raw) - 3 and len(raw) == 500_000:  # coupure au milieu d'un caractère
                return raw[:e.start].decode("utf-8"), r.geturl()
            # vieux sites en latin-1 : sinon les accents disparaissent
            return raw.decode("cp1252", "ignore"), r.geturl()


def links(html, base):
    return [urllib.parse.urljoin(base, h) for h in re.findall(r'href=["\']?([^"\' >]+)', html, re.I)]


def website_of(tags):
    return tags.get("website") or tags.get("contact:website") or tags.get("url")


def phone_of(tags):
    return tags.get("phone") or tags.get("contact:phone") or ""


# ---------- sources ----------

def overpass(q):
    """Les instances publiques saturent souvent : on essaie chaque miroir, deux tours."""
    err = None
    for url in OVERPASS * 2:
        try:
            return get_json(url, urllib.parse.urlencode({"data": q}).encode(), timeout=90)["elements"]
        except Exception as e:
            err = e
            time.sleep(3)
    raise RuntimeError(f"Overpass indisponible : {err}")


def fetch_osm(lat, lon, radius, per_segment):
    out = []
    for seg, filters in SEGMENTS.items():
        body = "".join(f'nwr[{f}]["name"](around:{radius},{lat},{lon});' for f in filters)
        els = overpass(f"[out:json][timeout:60];({body});out center tags;")
        # Joignables d'abord : un prospect sans téléphone ni site est inexploitable. Puis ordre stable par id.
        els.sort(key=lambda e: (not (phone_of(e["tags"]) or website_of(e["tags"])), e["id"]))
        for e in els[:per_segment]:
            c = e.get("center", e)
            out.append({"seg": seg, "tags": e["tags"], "lat": c["lat"], "lon": c["lon"],
                        "osm": f"https://www.openstreetmap.org/{e['type']}/{e['id']}"})
        time.sleep(2)  # politesse envers l'instance publique Overpass
    return out


def pick_etab(results, lat, lon):
    """Établissement SIRENE le plus proche (< MATCH_M) parmi les résultats de l'annuaire, sinon None."""
    best = None
    for r in results:
        for e in r.get("matching_etablissements", []):
            if not (e.get("latitude") and e.get("longitude")):
                continue
            d = dist_m(lat, lon, float(e["latitude"]), float(e["longitude"]))
            if d < MATCH_M and (best is None or d < best["dist"]):
                best = {"siren": r["siren"], "legal_name": r["nom_complet"], "address": e.get("adresse", ""),
                        "status": "actif" if e.get("etat_administratif") == "A" else "fermé", "dist": round(d)}
    return best


def sirene(name, lat, lon, dep):
    url = SIRENE + "?" + urllib.parse.urlencode({"q": name, "departement": dep, "per_page": 10})
    for attempt in range(3):
        try:
            return pick_etab(get_json(url)["results"], lat, lon)
        except urllib.error.HTTPError as e:
            if e.code != 429:
                return None
            time.sleep(1 + attempt)  # quota de l'API : 7 requêtes/s
        except Exception:
            return None
    return None


def parse_place(resp, lat, lon):
    """Réponse Places API (New) -> constats de fiche, ou None si le résultat est trop loin pour être le même."""
    places = resp.get("places") or []
    if not places:
        return None
    p = places[0]
    loc = p.get("location", {})
    if not loc or dist_m(lat, lon, loc["latitude"], loc["longitude"]) > MATCH_M:
        return None
    return {"website": p.get("websiteUri", ""), "phone": p.get("nationalPhoneNumber", ""),
            "rating": p.get("rating"), "reviews": p.get("userRatingCount", 0),
            "hours": bool(p.get("regularOpeningHours")), "photos": len(p.get("photos", [])),
            "status": p.get("businessStatus", ""), "maps": p.get("googleMapsUri", "")}


def google_place(name, lat, lon, key):
    body = {"textQuery": name, "maxResultCount": 1, "languageCode": "fr",
            "locationBias": {"circle": {"center": {"latitude": lat, "longitude": lon}, "radius": float(MATCH_M)}}}
    fields = ",".join("places." + f for f in ("location", "websiteUri", "nationalPhoneNumber", "rating", "userRatingCount",
                                              "regularOpeningHours", "photos", "businessStatus", "googleMapsUri"))
    try:
        resp = get_json(PLACES, json.dumps(body).encode(),
                        {"Content-Type": "application/json", "X-Goog-Api-Key": key, "X-Goog-FieldMask": fields})
    except Exception:
        return None
    return parse_place(resp, lat, lon)


# ---------- audit ----------

def guess_domains(name):
    slug = norm(name).split()
    core = [w for w in slug if w not in ("l", "le", "la", "les", "d", "de", "du", "des", "chez", "et")]
    if len(core) < 2 and len("".join(core)) < 10:  # 'L'Atelier', 'Multitude' : trop génériques, homonymes garantis
        return []
    stems = dict.fromkeys(["".join(slug), "-".join(slug), "".join(core)])
    return [f"https://www.{s}{suffix}" for s in stems for suffix in (".fr", ".com")]


def find_site(name):
    """Teste des domaines plausibles ; retenu seulement si la page cite le nom ET une localisation lyonnaise."""
    want = norm(name).replace(" ", "")
    for url in guess_domains(name):
        try:
            html, final = fetch(url, timeout=5)
        except Exception:
            continue
        if site_matches(html, want):
            return final
    return None


def site_matches(html, want):
    """Nom et localisation lyonnaise dans le texte visible (hors scripts, où 'lyon' traîne au hasard)."""
    text = norm(re.sub(r"<[^>]+>", " ", re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", html)))
    return want in text.replace(" ", "") and bool(LOCAL.search(text))


def pdf_menus(urls):
    return [u for u in urls if urllib.parse.urlparse(u).path.lower().endswith(".pdf")]


def menu_pages(urls, host):
    return list(dict.fromkeys(u for u in urls if urllib.parse.urlparse(u).netloc == host
                              and MENU.search(urllib.parse.urlparse(u).path) and not pdf_menus([u])))[:2]


def audit_site(url, seg):
    """Constats techniques d'un site : {'down'}, {'blocked'} ou le détail."""
    if not url.startswith("http"):
        url = "http://" + url
    try:
        html, final = fetch(url)
    except urllib.error.HTTPError as e:
        # 401/403/429 = le site existe mais refuse notre robot : ne pas le déclarer en panne
        return {"blocked": True} if e.code in (401, 403, 429) else {"down": True}
    except Exception:
        return {"down": True}
    home = links(html, final)
    pdfs = [u for u in pdf_menus(home) if MENU.search(u)]
    if seg == "restaurant":  # la carte est rarement sur l'accueil : on suit jusqu'à 2 liens « menu / carte »
        for page in menu_pages(home, urllib.parse.urlparse(final).netloc):
            try:
                sub, sub_final = fetch(page, timeout=6)
                # une annexe allergènes ou des CGV ne sont pas une carte
                pdfs += [u for u in pdf_menus(links(sub, sub_final)) if not re.search(r"allerg|cgv|mentions", u, re.I)]
            except Exception:
                pass
    years = [int(y) for y in YEAR.findall(html)]
    return {
        "https": final.startswith("https"),
        "mobile": bool(re.search(r'name=["\']?viewport', html, re.I)),
        "booking": bool(BOOKING.search(html)),
        "pdf_menu": pdfs[0] if pdfs else "",
        "year": max(years) if years else None,
    }


def score(c):
    """Candidat audité -> (score 0-100, offres, constats lisibles)."""
    seg, site, g = c["seg"], c.get("site"), c.get("google")
    issues, offers, pts = [], [], 0
    if not c.get("site_url"):
        offers.append("site")
        if g:
            issues.append("Aucun site (confirmé par la fiche Google)"); pts += 50
        else:
            issues.append("Aucun site trouvé (OSM + domaines testés)"); pts += 35
    elif site.get("down"):
        issues.append("Site injoignable"); offers.append("site"); pts += 50
    elif site.get("blocked"):
        issues.append("Site non auditable (robot refusé)")
    else:
        old = site["year"] and site["year"] < date.today().year - 4
        if not site["mobile"]:
            issues.append("Site non adapté mobile"); pts += 20
        if not site["https"]:
            issues.append("Pas de HTTPS"); pts += 10
        if old:
            issues.append(f"Copyright {site['year']}"); pts += 10
        if not site["mobile"] or old:
            offers.append("refonte")
        if seg == "beauté" and not site["booking"]:
            issues.append("Pas de réservation en ligne visible"); offers.append("reservation"); pts += 35
        if seg == "restaurant" and site["pdf_menu"]:
            issues.append("Menu en PDF"); offers.append("menu"); pts += 20
    if seg == "beauté" and "site" in offers:
        offers.append("reservation")
    if g:
        gaps = [lbl for ok, lbl in ((g["hours"], "horaires"), (g["photos"] >= 5, f"{g['photos']} photos"),
                                    (g["reviews"] >= 10, f"{g['reviews']} avis")) if not ok]
        if gaps:
            issues.append("Fiche Google faible : " + ", ".join(gaps)); offers.append("fiche"); pts += 10 * len(gaps)
    else:
        t = c["tags"]
        gaps = [lbl for k, lbl in (("opening_hours", "horaires"), ("phone", "téléphone")) if not (t.get(k) or t.get("contact:" + k))]
        if gaps:
            issues.append("Fiche OSM incomplète : " + ", ".join(gaps)); offers.append("fiche"); pts += 10
    return min(pts, 100), offers, issues


# ---------- pipeline ----------

def build(lat, lon, radius, limit, dep, gkey):
    cands = fetch_osm(lat, lon, radius, limit)
    print(f"{len(cands)} candidats OSM")

    for c in cands:  # séquentiel : quota de 7 req/s de l'annuaire
        c["sirene"] = sirene(c["tags"]["name"], c["lat"], c["lon"], dep)
        time.sleep(0.15)
    with ThreadPoolExecutor(8) as pool:
        gs = pool.map(lambda c: google_place(c["tags"]["name"], c["lat"], c["lon"], gkey) if gkey else None, cands)
        for c, g in zip(cands, gs):
            c["google"] = g
    closed = [c for c in cands if (c["sirene"] or {}).get("status") == "fermé" or (c["google"] or {}).get("status") == "CLOSED_PERMANENTLY"]
    cands = [c for c in cands if c not in closed]
    print(f"{len(closed)} établissements fermés écartés")

    for c in cands:
        c["site_url"], c["site_source"] = next(((u, s) for u, s in ((website_of(c["tags"]), "OSM"), ((c["google"] or {}).get("website"), "Google")) if u), (None, None))
    with ThreadPoolExecutor(16) as pool:
        found = pool.map(lambda c: None if c["site_url"] or c["google"] else find_site(c["tags"]["name"]), cands)
        for c, u in zip(cands, found):
            if u:
                c["site_url"], c["site_source"] = u, "domaine deviné"
        sites = pool.map(lambda c: audit_site(c["site_url"], c["seg"]) if c["site_url"] else None, cands)
        for c, s in zip(cands, sites):
            c["site"] = s

    prospects = []
    for c in cands:
        s, offers, issues = score(c)
        if not offers:
            continue
        t, sir, g = c["tags"], c["sirene"] or {}, c["google"] or {}
        setup, mrr = sum(OFFERS[o][1] for o in offers), sum(OFFERS[o][2] for o in offers)
        prospects.append({
            "name": t["name"], "segment": c["seg"], "type": t.get("craft") or t.get("amenity") or t.get("shop"),
            "address": " ".join(filter(None, [t.get("addr:housenumber"), t.get("addr:street"), t.get("addr:postcode")])) or sir.get("address", ""),
            "phone": phone_of(t) or g.get("phone", ""),
            "website": c["site_url"] or "", "website_source": c["site_source"] or "",
            "siren": sir.get("siren", ""), "legal_name": sir.get("legal_name", ""),
            "verified": "SIRENE" if sir else "non trouvé dans SIRENE",
            "google": g.get("maps", ""), "rating": g.get("rating"), "reviews": g.get("reviews"),
            "osm": c["osm"], "score": s, "issues": issues, "offers": [OFFERS[o][0] for o in offers],
            "setup": setup, "mrr": mrr, "year1": setup + 12 * mrr,
        })
    # Équilibre les segments : à tour de rôle le meilleur restant de chaque segment ; vérifiés et joignables d'abord
    key = lambda p: (-p["score"], not p["siren"], not p["phone"])
    by_seg = {seg: sorted([p for p in prospects if p["segment"] == seg], key=key) for seg in SEGMENTS}
    picked = []
    while len(picked) < limit and any(by_seg.values()):
        for seg in SEGMENTS:
            if by_seg[seg] and len(picked) < limit:
                picked.append(by_seg[seg].pop(0))
    return sorted(picked, key=lambda p: (key(p), -p["year1"]))


def render(prospects, path, google_on):
    tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard_template.html"), encoding="utf-8").read()
    data = json.dumps(prospects, ensure_ascii=False).replace("</", "<\\/")
    src = "OpenStreetMap, annuaire SIRENE" + (", Google Places" if google_on else "")
    open(path, "w", encoding="utf-8").write(tpl.replace("/*DATA*/[]", data).replace("{{DATE}}", date.today().isoformat()).replace("{{SOURCES}}", src))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lat", type=float, default=45.7640)
    ap.add_argument("--lon", type=float, default=4.8357)
    ap.add_argument("--radius", type=int, default=5000)
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--departement", default="69")
    a = ap.parse_args()
    gkey = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not gkey:
        print("GOOGLE_PLACES_API_KEY absente : fiches Google non auditées (repli sur OSM).")
    ps = build(a.lat, a.lon, a.radius, a.limit, a.departement, gkey)
    json.dump(ps, open("prospects.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    render(ps, "dashboard.html", bool(gkey))
    print(f"{len(ps)} prospects · installations {sum(p['setup'] for p in ps)} € · MRR {sum(p['mrr'] for p in ps)} €/mois → dashboard.html")
