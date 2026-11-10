"""LEADFLOW Livrables — pour chaque prospect : site de démonstration, devis à 3 formules, kit fiche locale.

Usage : python3 deliver.py enrich   -> enrich.json + photos, logos et polices dans site/leadflow/<slug>/
        python3 deliver.py menus    -> ajoute à enrich.json les cartes extraites des PDF (demande pypdf)
        python3 deliver.py build    -> site/leadflow/<slug>/index.html, devis/<slug>.html, devis/index.html
"""
import hashlib, html, json, os, re, ssl, subprocess, sys, time, urllib.parse, urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

from prospect import MENU, OFFERS, SIRENE, UA, audit_site, fetch, get_json, links, menu_pages, norm, overpass, pdf_menus, score

SITE, DEVIS = "site/leadflow", "devis"
GENERIC = re.compile(r"^(inherit|initial|unset|sans-serif|serif|monospace|cursive|system-ui|-apple-system|blinkmacsystemfont|"
                     r"arial|helvetica|helvetica neue|segoe ui|times|times new roman|georgia|verdana|tahoma|courier.*|var\(.*|"
                     r".*(awesome|icon|glyph|swiper|slick|eicons|fontello|material|star|themify|ionicons|elegant).*)$", re.I)
NOISE = re.compile(r"cookie|rgpd|navigateur|javascript|mentions légales|tous droits|newsletter|404|not found|wayback", re.I)
SKIP_IMG = re.compile(r"logo|icon|sprite|pixel|avatar|badge|flag|loader|placeholder|gravatar|emoji|/_static/|\.svg|\.gif|data:", re.I)


def slugs(prospects):
    """Un slug unique par prospect, stable d'un run à l'autre (les doublons reçoivent le n° OSM)."""
    out, seen = [], Counter(norm(p["name"]).replace(" ", "-") for p in prospects)
    for p in prospects:
        s = norm(p["name"]).replace(" ", "-") or "etablissement"
        # le slug posé au premier passage reste : une enseigne corrigée d'après Google ne change pas l'adresse de la maquette
        out.append(p.get("slug") or (s if seen[s] == 1 else f"{s}-{p['osm'].rsplit('/', 1)[1]}"))
    return out


def fetch_bytes(url, limit=6_000_000, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as r:
        return r.read(limit), r.headers.get("Content-Type", "")


# ---------- collecte ----------

def osm_tags(prospects):
    ids = {}
    for p in prospects:
        kind, n = p["osm"].rsplit("/", 2)[1:]
        ids.setdefault(kind, []).append(n)
    url = lambda e: f"https://www.openstreetmap.org/{e['type']}/{e['id']}"
    try:
        q = "".join(f"{k}(id:{','.join(v)});" for k, v in ids.items())
        els = overpass(f"[out:json][timeout:60];({q});out center tags;")
        return {url(e): {**e["tags"], "_lat": e.get("center", e)["lat"], "_lon": e.get("center", e)["lon"]} for e in els}
    except RuntimeError:
        # Overpass saturé : l'API OSM donne les mêmes tags (sans coordonnées pour les bâtiments, donc sans plan d'accès)
        els = [e for k, v in ids.items() for e in get_json(f"https://api.openstreetmap.org/api/0.6/{k}s.json?{k}s={','.join(v)}")["elements"]]
        return {url(e): {**e.get("tags", {}), **({"_lat": e["lat"], "_lon": e["lon"]} if "lat" in e else {})} for e in els}


def sirene_detail(siren):
    try:
        r = get_json(f"{SIRENE}?q={siren}")["results"][0]
    except Exception:
        return {}
    boss = next((d for d in r.get("dirigeants") or [] if d.get("type_dirigeant") == "personne physique"), None)
    return {"since": (r.get("date_creation") or "")[:4], "naf": r.get("activite_principale", ""),
            "boss": f"{boss['prenoms'].split()[0].title()} {boss['nom'].split(' (')[0].title()}" if boss and boss.get("prenoms") else "",
            "role": (boss or {}).get("qualite") or ""}


def page(url):
    """-> (html, url finale, source). Site en panne : dernière copie de la Wayback Machine."""
    if not re.match(r"https?://", url):
        url = "http://" + url
    try:
        return (*fetch(url, 12), "site")
    except Exception:
        try:
            snap = get_json("https://archive.org/wayback/available?url=" + urllib.parse.quote(url), timeout=20)["archived_snapshots"].get("closest")
            if snap and snap.get("available"):
                # id_ = page d'origine, sans la barre d'outils ni les réécritures d'archive.org
                return (*fetch(re.sub(r"/web/(\d+)/", r"/web/\1id_/", snap["url"]).replace("http://web.", "https://web."), 25), "archive")
        except Exception:
            pass
    return None


def first_family(decl):
    return decl.split(",")[0].strip().strip("\"'!").replace(" important", "").strip()


def extract(doc, base):
    """Ce qu'on peut reprendre d'une page : textes, images, polices, couleur, réseaux."""
    def meta(key):
        m = (re.search(rf'<meta[^>]+(?:name|property)=["\']{key}["\'][^>]*content=["\']([^"\']+)', doc, re.I)
             or re.search(rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]*(?:name|property)=["\']{key}["\']', doc, re.I))
        return html.unescape(m.group(1)).strip() if m else ""
    join = lambda u: urllib.parse.urljoin(base, html.unescape(u.strip()))
    visible = re.sub(r"(?is)<(script|style|noscript|svg|nav|footer)\b.*?</\1>", " ", doc)
    text = lambda s: " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())

    paras = []
    for p in re.findall(r"(?is)<p\b[^>]*>(.*?)</p>", visible):
        t = text(p)
        if 80 <= len(t) <= 700 and not NOISE.search(t) and t not in paras:
            paras.append(t)

    imgs, logo = [], ""
    for tag in re.findall(r"(?is)<img\b[^>]*>", doc):
        src = re.search(r'(?:data-src|data-lazy-src|src)=["\']([^"\']+)', tag, re.I)
        if not src:
            continue
        if re.search(r"logo", tag, re.I) and not logo and not src.group(1).startswith("data:"):
            logo = join(src.group(1))
        elif not SKIP_IMG.search(src.group(1)):
            imgs.append(join(src.group(1)))
    imgs += [join(u) for u in re.findall(r'background(?:-image)?:\s*url\(["\']?([^"\')]+)', doc, re.I) if not SKIP_IMG.search(u)]
    if meta("og:image"):
        imgs.insert(0, join(meta("og:image")))

    sheets = [join(h) for tag in re.findall(r"(?is)<link\b[^>]*>", doc) if re.search(r"stylesheet", tag, re.I)
              for h in re.findall(r'href=["\']([^"\']+)', tag, re.I)]
    return {
        "title": text(re.search(r"(?is)<title[^>]*>(.*?)</title>", doc).group(1)) if re.search(r"(?is)<title", doc) else "",
        "description": meta("description") or meta("og:description"),
        "h1": [t for t in (text(h) for h in re.findall(r"(?is)<h[12]\b[^>]*>(.*?)</h[12]>", visible)) if 3 < len(t) < 120][:6],
        "paragraphs": paras[:4], "images": list(dict.fromkeys(imgs)), "logo": logo,
        "theme": meta("theme-color"), "sheets": sheets,
        "inline_css": " ".join(re.findall(r"(?is)<style[^>]*>(.*?)</style>", doc)),
        "social": sorted({u.split("?")[0] for u in re.findall(r'href=["\'](https?://(?:www\.)?(?:facebook|instagram)\.com/[^"\']+)', doc, re.I)
                          if not re.search(r"sharer|/share|/tr\?|/plugins", u)})[:2],
        "email": next(iter(re.findall(r'mailto:([\w.+-]+@[\w-]+\.[\w.-]+)', doc)), ""),
    }


def css_brand(css):
    """-> (police des titres, police du texte, {famille: url woff2}, couleur dominante non grise)."""
    fams = [f for f in (first_family(d) for d in re.findall(r"font-family\s*:\s*([^;}]+)", css, re.I)) if f and not GENERIC.match(f)]
    rule = lambda sel: next((f for f in (first_family(d) for d in re.findall(
        rf"(?:^|[}},\s]){sel}\b[^{{}}]*\{{[^}}]*?font-family\s*:\s*([^;}}]+)", css, re.I)) if f and not GENERIC.match(f)), "")
    top = [f for f, _ in Counter(fams).most_common(2)]
    body = rule("body") or (top[0] if top else "")
    heading = rule("h1") or rule("h2") or (top[1] if len(top) > 1 else body)
    faces = {}
    for block in re.findall(r"@font-face\s*\{([^}]+)\}", css, re.I):
        fam, url = re.search(r"font-family\s*:\s*([^;]+)", block, re.I), re.search(r'url\(["\']?([^"\')]+\.woff2)[^"\')]*["\']?\)', block, re.I)
        if fam and url:
            faces.setdefault(first_family(fam.group(1)), url.group(1))
    colors = Counter()
    for h in re.findall(r"#([0-9a-f]{6}|[0-9a-f]{3})\b", css, re.I):
        h = (h if len(h) == 6 else "".join(c * 2 for c in h)).lower()
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        if max(r, g, b) - min(r, g, b) >= 45 and 40 < (r + g + b) / 3 < 215:
            colors[h] += 1
    return heading, body, faces, ("#" + colors.most_common(1)[0][0]) if colors else ""


def on_google_fonts(family):
    try:
        fetch_bytes("https://fonts.googleapis.com/css2?family=" + urllib.parse.quote_plus(family), 2000, 8)
        return True
    except Exception:
        return False


def dimensions(path):
    d = re.findall(r"pixel(?:Width|Height): (\d+)", subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", path], capture_output=True, text=True).stdout)
    return (int(d[0]), int(d[1])) if len(d) == 2 else (0, 0)


def light_logo(path):
    """Vrai si le logo est clair (blanc sur transparent) : il lui faut un fond sombre pour rester lisible."""
    bmp = path + ".bmp"
    subprocess.run(["sips", "-s", "format", "bmp", "-z", "16", "16", path, "--out", bmp], capture_output=True)
    if not os.path.exists(bmp):
        return False
    raw = open(bmp, "rb").read()
    os.remove(bmp)
    start, bpp = int.from_bytes(raw[10:14], "little"), raw[28] // 8
    px = [raw[i:i + bpp] for i in range(start, len(raw) - bpp + 1, bpp)]
    px = [p for p in px if bpp < 4 or p[3] > 60]  # pixels opaques seulement
    return bool(px) and sum(sum(p[:3]) for p in px) / (3 * len(px)) > 205


def good_photo(dims):
    """Écarte bandeaux, pictogrammes et vignettes : une photo fait au moins 600 x 400 et n'est ni carrée-icône ni panoramique."""
    w, h = dims
    return w >= 600 and h >= 400 and max(w, h) / max(min(w, h), 1) <= 2.2 and not (w == h and w <= 600)


def save_image(url, path):
    """Télécharge une vraie photo (>= 500 px de large) et la ramène à 1600 px. -> nom du fichier ou None."""
    try:
        data, ctype = fetch_bytes(url)
    except Exception:
        return None
    ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}.get(ctype.split(";")[0].strip())
    if not ext or len(data) < 20_000:
        return None
    with open(f"{path}.{ext}", "wb") as f:
        f.write(data)
    dims = dimensions(f"{path}.{ext}")
    if not good_photo(dims):
        os.remove(f"{path}.{ext}")
        return None
    if max(dims) > 1600:
        subprocess.run(["sips", "-Z", "1600", f"{path}.{ext}"], capture_output=True)
    return os.path.basename(f"{path}.{ext}")


def brand(url, folder):
    got = page(url)
    if not got:
        return {}
    doc, final, source = got
    b = extract(doc, final)
    css = b.pop("inline_css")
    is_gf = lambda u: urllib.parse.urlparse(u).netloc == "fonts.googleapis.com"
    gfonts = [h for h in b["sheets"] if is_gf(h)]
    for sheet in [s for s in b.pop("sheets") if not is_gf(s)][:5]:
        try:
            sheet_css = fetch(sheet, 10)[0]
            css += " " + re.sub(r'url\(["\']?(?!data:)([^"\')]+)', lambda m: "url(" + urllib.parse.urljoin(sheet, m.group(1)), sheet_css)
        except Exception:
            pass
    gfonts += [u for u in re.findall(r'@import\s+(?:url\()?["\']?(https?://fonts\.googleapis\.com/[^"\')\s;]+)', css)]
    heading, body, faces, color = css_brand(css)
    os.makedirs(f"{folder}/img", exist_ok=True)

    fonts = {"links": gfonts[:2], "faces": {}, "heading": heading, "body": body}
    for fam in dict.fromkeys(f for f in (heading, body) if f):
        if any(fam.replace(" ", "+") in g or urllib.parse.quote(fam) in g for g in gfonts):
            continue
        if on_google_fonts(fam):
            fonts["links"].append("https://fonts.googleapis.com/css2?family=" + urllib.parse.quote_plus(fam) + ":wght@400;600;700&display=swap")
        elif fam in faces:
            try:
                name = norm(fam).replace(" ", "-") + ".woff2"
                with open(f"{folder}/img/{name}", "wb") as f:
                    f.write(fetch_bytes(faces[fam])[0])
                fonts["faces"][fam] = "img/" + name
            except Exception:
                pass

    photos, seen = [], set()
    for u in b.pop("images")[:30]:
        if len(photos) == 7:
            break
        name = save_image(u, f"{folder}/img/photo-{len(photos) + 1}")
        if name:
            digest = hashlib.md5(open(f"{folder}/img/{name}", "rb").read()).hexdigest()
            if digest in seen:
                os.remove(f"{folder}/img/{name}")
            else:
                seen.add(digest)
                photos.append("img/" + name)
    logo = ""
    if b["logo"]:
        try:
            data, ctype = fetch_bytes(b["logo"])
            ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}.get(ctype.split(";")[0].strip())
            if ext and data:
                with open(f"{folder}/img/logo.{ext}", "wb") as f:
                    f.write(data)
                logo = f"img/logo.{ext}"
                b["logo_light"] = light_logo(f"{folder}/{logo}")
        except Exception:
            pass
    return {**b, "source": source, "url": final, "photos": photos, "logo": logo, "fonts": fonts, "color": b["theme"] or color}


def enrich(prospects):
    tags = osm_tags(prospects)
    out = {}
    for p, slug in zip(prospects, slugs(prospects)):  # séquentiel : quota de 7 req/s de l'annuaire
        out[slug] = {"tags": tags.get(p["osm"], {}), "sirene": sirene_detail(p["siren"]) if p["siren"] else {}}
        time.sleep(0.15)
    with ThreadPoolExecutor(8) as pool:
        todo = [(p, s) for p, s in zip(prospects, slugs(prospects)) if p["website"]]
        for (p, slug), b in zip(todo, pool.map(lambda ps: brand(ps[0]["website"], f"{SITE}/{ps[1]}"), todo)):
            out[slug]["brand"] = b
    return out


PLATFORM = re.compile(r"planity|treatwell|booksy|kiute|thefork|lafourchette|zenchef|facebook|instagram|eatbu|sites\.google|business\.site|"
                      r"site-solocal|privateaser|linktr|pagesjaunes|ubereats|deliveroo|doctolib|borneoapp|cookie\.menu|frmaps", re.I)
BOOKS = re.compile(r"planity|treatwell|booksy|kiute|thefork|lafourchette|zenchef|doctolib", re.I)
WEEK = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def google_hours(rows):
    """Lignes du tableau d'horaires de Maps -> [('Lundi', '12:00–14:00 · 19:30–22:00')], du lundi au dimanche."""
    out = {}
    for row in rows:
        day = next((d for d in WEEK if row.lower().startswith(d)), None)
        if day and "(" not in row and "férié" not in row.lower():  # semaine avec jour férié : l'horaire affiché n'est pas l'habituel
            spans = re.findall(r"\d{1,2}:\d{2}\s*–\s*\d{1,2}:\d{2}", row)
            out[day] = " · ".join(spans) or ("Ouvert 24h/24" if "24" in row else "Fermé")
    if out and set(out.values()) == {"Ouvert 24h/24"}:  # valeur par défaut d'une fiche jamais renseignée : aucun commerce de quartier n'est ouvert jour et nuit
        return []
    return [(d.capitalize(), out[d]) for d in WEEK if d in out]


def requalify(prospects, data, maps, unlisted=None):
    """Recoupe chaque prospect avec sa fiche Google Maps : écarte les fermés, réaudite le site que Google connaît, refait le score."""
    kept = []
    for p, slug in zip(prospects, slugs(prospects)):
        d, e = maps.get(slug), data[slug]
        if slug in (unlisted or {}):  # cherché à la main sur Maps, à ses coordonnées : aucune fiche
            if unlisted[slug] or not p["siren"]:
                print(f"écarté, invérifiable : {p['name']} ({unlisted[slug] or 'ni fiche Google ni SIREN'})")
                continue
            offers = list(dict.fromkeys(p["offers"] + [OFFERS["fiche"][0]]))
            price = {label: (a, b) for label, a, b in OFFERS.values()}
            setup, mrr = sum(price[o][0] for o in offers), sum(price[o][1] for o in offers)
            kept.append({**p, "issues": [i for i in p["issues"] if not i.startswith("Fiche OSM")] + ["Aucune fiche Google à cette adresse : à créer"],
                         "offers": offers, "setup": setup, "mrr": mrr, "year1": setup + 12 * mrr})
            continue
        if not d:
            kept.append(p)
            continue
        if d["closed"]:
            print(f"fermé définitivement : {p['name']}")
            continue
        own = d["website"] if d["website"] and not PLATFORM.search(d["website"]) else ""
        site_url = own or p["website"]  # le site que Google connaît est plus à jour que celui d'OSM, souvent mort
        g = {"hours": bool(d["hours"]), "photos": len(d["photos"]), "reviews": int(d["reviews"] or 0)}
        s, offers, issues = score({"seg": p["segment"], "tags": e["tags"], "site_url": site_url, "google": g,
                                   "site": audit_site(site_url, p["segment"]) if site_url else None})
        if d["website"] and not site_url:
            issues = [i for i in issues if not i.startswith("Aucun site")]
            issues.insert(0, "Pas de site propre : seulement une page " + urllib.parse.urlparse(d["website"]).netloc.removeprefix("www."))
            if BOOKS.search(d["website"]) and "reservation" in offers:
                offers.remove("reservation")
        if not offers:
            print(f"rien à vendre : {p['name']} ({site_url})")
            continue
        folder = f"{SITE}/{slug}"
        os.makedirs(f"{folder}/img", exist_ok=True)
        had = (e.get("google") or {}).get("photos", [])
        if had and all(os.path.exists(f"{folder}/{f}") for f in had):  # déjà téléchargées lors d'un passage précédent
            photos = [os.path.basename(f) for f in had]
        else:
            photos = [n for n in (save_image(u, f"{folder}/img/g-{i}") for i, u in enumerate(d["photos"][:8], 1)) if n]
        e["google"] = {"photos": ["img/" + n for n in photos], "hours": google_hours(d["hours"]), "address": d["address"].strip(),
                       "category": d["category"], "platform": d["website"] if not own else ""}
        old = e.get("brand") or {}
        lost = any(not os.path.exists(f"{folder}/{f}") for f in old.get("photos", []) + [old.get("logo")] * bool(old.get("logo")))
        if site_url and (old.get("asked") != site_url and own and own != p["website"] or lost):
            e["brand"] = {**brand(site_url, folder), "asked": site_url}
        setup, mrr = sum(OFFERS[o][1] for o in offers), sum(OFFERS[o][2] for o in offers)
        words = lambda x: {w for w in norm(x).split() if len(w) >= 4}
        kept.append({**p, "slug": slug, "name": p["name"] if words(p["name"]) & words(d["name"]) else d["name"],  # enseigne changée : Google fait foi
                     "website": site_url, "website_source": p["website_source"] or ("Google" if own else ""),
                     "phone": p["phone"] or d["phone"], "address": d["address"].strip() or p["address"],
                     "google": d["url"].split("?")[0], "rating": float(d["rating"].replace(",", ".")) if d["rating"] else None,
                     "reviews": g["reviews"], "score": s, "issues": issues, "offers": [OFFERS[o][0] for o in offers],
                     "setup": setup, "mrr": mrr, "year1": setup + 12 * mrr})
    key = lambda p: (-p["score"], not p["siren"], not p["phone"], -p["year1"])
    return sorted(kept, key=key), data


PRICE = re.compile(r"\d+(?:[.,]\d{1,2})?\s*€|€\s*\d+")


LEADER = re.compile(r"[\s.\ufffd·…_]{3,}")
PRICE_ONLY = re.compile(r"\d+(?:[.,]\d{1,2})?\s*€")
TRAILING = re.compile(r"^(.{6,}?) … (\d{1,3}(?:[.,]\d{1,2})?)\s*€?$")
JUNK = re.compile(r"RCS|capital|chèque|allerg|www\.|@|prix nets|service compris|^\(\d", re.I)


def parse_menu(text):
    """Texte brut d'une carte PDF -> [(rubrique, [lignes])] ; [] si ça ne ressemble pas à une carte.

    Trois mises en forme courantes : prix sur la ligne, prix regroupés après les plats, carte sans prix.
    """
    sections, cur, waiting = [], None, []
    def add(item):
        nonlocal cur
        if cur is None:
            cur = ("La carte", [])
            sections.append(cur)
        cur[1].append(item)
        return item
    for line in text.splitlines():
        line = " ".join(LEADER.sub(" … ", line.replace("•", " ")).split()).strip("… ")
        if re.fullmatch(r"(?:\S ){2,}\S", line):  # « E N T R É E S »
            line = line.replace(" ", "")
        line = re.sub(r"\b([B-NP-XZ]) ([A-Za-zéèêÉÈ]{4,})", r"\1\2", line)  # « L yonnaiserie » : pas A, O ni Y, qui sont des mots
        if not 2 <= len(line) <= 150 or JUNK.search(line):
            continue
        if PRICE_ONLY.fullmatch(line):
            if waiting:
                waiting.pop(0)[1] = line.replace(" ", "")
        elif TRAILING.match(line) or PRICE.search(line):
            m = TRAILING.match(line)
            add([m.group(1), m.group(2) + " €"] if m else [line, "inclus"])
        elif len(line) <= 40 and (line.isupper() or line.istitle()) and re.search(r"[A-Za-zÀ-ÿ]{3}", line) and not re.search(r"\d", line):
            cur = (line.capitalize(), [])
            sections.append(cur)
            waiting = []
        elif len(line) >= 8 and re.search(r"[A-Za-zÀ-ÿ]{4}", line):
            waiting.append(add([line, None]))
    priced = sum(1 for _, items in sections for i in items if i[1])
    fmt = lambda i: i[0] if i[1] in (None, "inclus") else f"{i[0]} … {i[1]}"
    if priced >= 8:
        out = [(t, [fmt(i) for i in items if i[1]][:14]) for t, items in sections]
    elif len([1 for _, items in sections if len(items) >= 2]) >= 2:
        out = [(t, [fmt(i) for i in items][:10]) for t, items in sections]
    else:
        return []
    out = [(t, items) for t, items in out if items][:8]
    return out if sum(len(i) for _, i in out) >= 8 else []


def pdf_text(raw):
    """Texte des 4 premières pages ; si le PDF n'est qu'une image, OCR avec tesseract quand il est installé."""
    import io, pypdf, shutil, tempfile
    pages = pypdf.PdfReader(io.BytesIO(raw)).pages[:4]
    text = "\n".join(pg.extract_text() or "" for pg in pages)
    if len(text) >= 400 or not shutil.which("tesseract"):
        return text
    out = []
    for pg in pages:
        for img in list(pg.images)[:2]:
            with tempfile.NamedTemporaryFile(suffix="." + img.name.rsplit(".", 1)[-1]) as f:
                f.write(img.data)
                f.flush()
                out.append(subprocess.run(["tesseract", f.name, "-", "-l", "fra" if "fra" in subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True).stdout else "eng", "--psm", "4"], capture_output=True, text=True).stdout)
    return "\n".join(out)


def menus(prospects, data):
    """Transforme les cartes PDF en carte lisible. pypdf est optionnel : sans lui, aucune carte n'est extraite."""
    for p, slug in zip(prospects, slugs(prospects)):
        data[slug].pop("menu", None)
        if "Menu en PDF" not in p["issues"] or not p["website"]:
            continue
        try:
            doc, final = fetch(p["website"] if p["website"].startswith("http") else "http://" + p["website"], 12)
            home = links(doc, final)
            pdfs = [u for u in pdf_menus(home) if MENU.search(u)]
            for sub in menu_pages(home, urllib.parse.urlparse(final).netloc):
                pdfs += pdf_menus(links(*fetch(sub, 8)))
        except Exception:
            continue
        # la carte d'abord : ni la carte des vins, ni les allergènes, ni la version anglaise
        pdfs = sorted(dict.fromkeys(pdfs), key=lambda u: bool(re.search(r"vin|boisson|allerg|_EN|sylvestre|noel", u, re.I)))
        for pdf in pdfs[:3]:
            try:
                menu = parse_menu(pdf_text(fetch_bytes(pdf, 20_000_000, 30)[0]))
            except Exception:
                menu = []
            if menu:
                data[slug]["menu"], data[slug]["menu_pdf"] = menu, pdf
                break
        print(f"{p['name']}: {sum(len(i) for _, i in data[slug].get('menu', []))} lignes de carte ({len(pdfs)} PDF)")
    return data


def needs_site(p, e):
    """Une maquette seulement quand elle résout un constat : pas de site, site à refaire, réservation, ou carte extraite."""
    return bool({"Site vitrine", "Refonte site obsolète", "Réservation en ligne"} & set(p["offers"]) or e.get("menu"))


PROSPECTS_START, PROSPECTS_END = "<!-- prospects:start -->", "<!-- prospects:end -->"


def readme_table(rows):
    """Réécrit dans README.md le tableau prospects / produits / maquette / devis (entre deux marqueurs)."""
    import render
    lines = ["| # | Prospect | Métier | Ville | Téléphone | Produits | Installation | Mensuel | Score | Maquette | Devis |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(sorted(rows, key=lambda r: -r["p"]["score"]), 1):
        p = r["p"]
        products = ", ".join(p["offers"])
        site = f"[voir](https://snooker4real.github.io/leadflow/{r['slug']}/)" if r["site"] else "aucune"
        lines.append(f"| {i} | {p['name']} | {p['segment']} | {render.city_of(p['address'], {})} | {p['phone'] or '—'} | {products} | {p['setup']} € | {p['mrr']} €/mois | {p['score']} | {site} | [{r['n']}](devis/{r['slug']}.html) |")
    block = f"{PROSPECTS_START}\n" + "\n".join(lines) + f"\n{PROSPECTS_END}"
    text = open("README.md", encoding="utf-8").read()
    if PROSPECTS_START in text:
        text = re.sub(re.escape(PROSPECTS_START) + ".*?" + re.escape(PROSPECTS_END), lambda _: block, text, flags=re.S)
    else:
        text = text.rstrip() + "\n\n## Prospects, produits, maquettes et devis\n\nTableau généré par `python3 deliver.py build`, trié par score. Les devis sont des fichiers locaux (`devis/`, non versionnés) ; les maquettes sont en ligne.\n\n" + block + "\n"
    open("README.md", "w", encoding="utf-8").write(text)


def build(prospects, data):
    import render
    os.makedirs(DEVIS, exist_ok=True)
    for old in os.listdir(DEVIS):  # pas de devis orphelin pour un prospect sorti de la liste
        os.remove(f"{DEVIS}/{old}")
    rows = []
    # Les restaurants universitaires sortent d'OSM comme des restaurants mais ne sont pas des clients possibles
    keep = [(p, s) for p, s in zip(prospects, slugs(prospects)) if not re.search(r"universitaire|resto u\b|crous", norm(p["name"]))]
    # cartes retranscrites à la main quand l'extraction automatique du PDF donne un texte inexploitable
    manual = json.load(open("menus_manual.json", encoding="utf-8")) if os.path.exists("menus_manual.json") else {}
    rank = Counter()
    for p, slug in keep:
        e = data.get(slug, {})
        if slug in manual:
            e = {**e, "menu": manual[slug]}
        site = needs_site(p, e)
        k = rank[p["segment"]]  # rang dans le métier : deux voisins n'ont jamais la même mise en page
        rank[p["segment"]] += 1
        if site:
            os.makedirs(f"{SITE}/{slug}", exist_ok=True)
            open(f"{SITE}/{slug}/index.html", "w", encoding="utf-8").write(render.site_html(p, e, slug, k))
        number = f"LF-{date.today():%Y}-{p['osm'].rsplit('/', 1)[1][-6:]}"  # stable d'un run à l'autre
        open(f"{DEVIS}/{slug}.html", "w", encoding="utf-8").write(render.devis_html(p, e, slug, number, site))
        idn = render.identity(p, e, slug, k)
        assets = ", ".join(filter(None, [f"{len(idn['photos'])} photos" if idn["photos"] else "", "logo" if idn["logo"] else "",
                                         "police" if idn["own_font"] else "", "couleur" if idn["own_color"] else "", "carte" if e.get("menu") else ""]))
        rows.append({"n": number, "p": p, "slug": slug, "site": site, "assets": assets or "aucun élément repris",
                     "boss": (e.get("sirene") or {}).get("boss", ""), "f": render.formulas(p["setup"], p["mrr"])})
    open(f"{DEVIS}/index.html", "w", encoding="utf-8").write(render.index_html(rows))
    readme_table(rows)
    live = {r["slug"] for r in rows if r["site"]}
    for folder in os.listdir(SITE):  # prospect écarté ou sans maquette : plus de page (les images restent, publish.sh ne copie que les dossiers avec une page)
        if folder not in live and os.path.exists(f"{SITE}/{folder}/index.html"):
            os.remove(f"{SITE}/{folder}/index.html")
    open(f"{SITE}/index.html", "w", encoding="utf-8").write(
        '<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="robots" content="noindex, nofollow"><title>LEADFLOW</title>'
        '<body style="font:16px system-ui;margin:15vh auto;max-width:40ch;text-align:center"><h1>LEADFLOW</h1><p>Maquettes de démonstration, accessibles par lien direct.</p>')
    return rows


if __name__ == "__main__":
    prospects = json.load(open("prospects.json", encoding="utf-8"))
    if sys.argv[1:] == ["enrich"]:
        data = enrich(prospects)
        json.dump(data, open("enrich.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        b = [d.get("brand") or {} for d in data.values()]
        print(f"{len(data)} prospects · {sum(1 for x in b if x)} sites lus ({sum(1 for x in b if x.get('source') == 'archive')} via archive) · "
              f"{sum(len(x.get('photos', [])) for x in b)} photos · {sum(1 for x in b if x.get('fonts', {}).get('heading'))} polices reprises")
    elif sys.argv[1:] == ["google"]:
        from prospect import render as dashboard
        data = json.load(open("enrich.json", encoding="utf-8"))
        if not os.path.exists("prospects.osm.json"):
            json.dump(prospects, open("prospects.osm.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        prospects = json.load(open("prospects.osm.json", encoding="utf-8"))
        ps, data = requalify(prospects, data, json.load(open("gmaps/matched.json", encoding="utf-8")),
                             json.load(open("gmaps/unlisted.json", encoding="utf-8")) if os.path.exists("gmaps/unlisted.json") else None)
        json.dump(ps, open("prospects.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        json.dump(data, open("enrich.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        dashboard(ps, "dashboard.html", True)
        print(f"{len(ps)} prospects · installations {sum(p['setup'] for p in ps)} € · MRR {sum(p['mrr'] for p in ps)} €/mois")
    elif sys.argv[1:] == ["menus"]:
        data = menus(prospects, json.load(open("enrich.json", encoding="utf-8")))
        json.dump(data, open("enrich.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    elif sys.argv[1:] == ["build"]:
        rows = build(prospects, json.load(open("enrich.json", encoding="utf-8")))
        print(f"{len(rows)} devis · {sum(r['site'] for r in rows)} maquettes · {sum(r['assets'] != 'aucun élément repris' for r in rows)} avec identité reprise")
    else:
        sys.exit(__doc__)
