"""Rendu HTML des livrables : site de démonstration, devis à 3 formules, kit fiche locale."""
import hashlib, html, json, math, os, re, subprocess, urllib.parse
from datetime import date, timedelta

from prospect import OFFERS, norm

BASE_URL = "https://snooker4real.github.io/leadflow"
PRICES = {label: (setup, mrr) for label, setup, mrr in OFFERS.values()}
E = lambda s: html.escape(str(s or ""), quote=True)

# type OSM -> (libellé, prestations types à valider avec le client)
TYPES = {
    "plumber": ("Plombier", ["Dépannage et recherche de fuite", "Installation sanitaire", "Chauffe-eau et ballon", "Rénovation de salle de bain"]),
    "electrician": ("Électricien", ["Dépannage électrique", "Mise aux normes du tableau", "Installation et rénovation", "Éclairage et domotique"]),
    "roofer": ("Couvreur", ["Réparation de toiture", "Zinguerie et gouttières", "Étanchéité", "Pose de fenêtres de toit"]),
    "carpenter": ("Menuisier", ["Menuiserie sur mesure", "Portes et fenêtres", "Agencement intérieur", "Parquet et escaliers"]),
    "painter": ("Peintre", ["Peinture intérieure", "Ravalement de façade", "Revêtements muraux", "Finitions décoratives"]),
    "hvac": ("Chauffagiste", ["Entretien de chaudière", "Pompe à chaleur", "Climatisation", "Dépannage chauffage"]),
    "locksmith": ("Serrurier", ["Ouverture de porte", "Changement de serrure", "Blindage et sécurisation", "Reproduction de clés"]),
    "tiler": ("Carreleur", ["Pose de carrelage", "Faïence et mosaïque", "Salle de bain et cuisine", "Terrasse extérieure"]),
    "glaziery": ("Vitrier", ["Remplacement de vitrage", "Double vitrage", "Miroirs sur mesure", "Vitrines de commerce"]),
    "plasterer": ("Plâtrier", ["Cloisons et doublages", "Faux plafonds", "Isolation intérieure", "Enduits et finitions"]),
    "builder": ("Entreprise de bâtiment", ["Rénovation complète", "Maçonnerie", "Extension et aménagement", "Coordination de chantier"]),
    "stonemason": ("Tailleur de pierre", ["Taille et restauration", "Façades en pierre", "Escaliers et dallages", "Pièces sur mesure"]),
    "restaurant": ("Restaurant", []), "cafe": ("Café", []), "fast_food": ("Restauration rapide", []),
    "hairdresser": ("Salon de coiffure", ["Coupe et brushing", "Coloration et balayage", "Soins du cheveu", "Coiffure de cérémonie"]),
    "beauty": ("Institut de beauté", ["Soins du visage", "Épilation", "Manucure et beauté des pieds", "Modelages"]),
    "barber": ("Barbier", ["Coupe homme", "Taille de barbe", "Rasage traditionnel", "Soin visage"]),
}
# Repli quand l'établissement n'a aucune identité en ligne à reprendre : (couleur, police des titres, police du texte)
PALETTES = {
    "restaurant": [("#a8431f", "Playfair Display", "Inter"), ("#1f5a4a", "Fraunces", "Karla"), ("#7a1f2b", "Cormorant Garamond", "Work Sans"),
                   ("#b8860b", "DM Serif Display", "DM Sans"), ("#2b4a6f", "Libre Caslon Text", "Nunito Sans")],
    "beauté": [("#8a5a5a", "Cormorant Garamond", "Jost"), ("#3d5a4c", "Marcellus", "Mulish"), ("#6b4a7a", "Playfair Display", "Poppins"),
               ("#b0603f", "Italiana", "Outfit"), ("#2f5d62", "Bodoni Moda", "Manrope")],
    "artisan": [("#1f4e8c", "Archivo", "Inter"), ("#b3541e", "Barlow Condensed", "Barlow"), ("#22543d", "Space Grotesk", "IBM Plex Sans"),
                ("#8c1c13", "Oswald", "Source Sans 3"), ("#3a3f8f", "Sora", "Rubik")],
}
LAYOUTS = 6  # mises en page distinctes, voir THEMES
CUISINE = {"french": "Cuisine française", "italian": "Cuisine italienne", "japanese": "Cuisine japonaise", "chinese": "Cuisine chinoise", "asian": "Cuisine asiatique",
           "indian": "Cuisine indienne", "lebanese": "Cuisine libanaise", "thai": "Cuisine thaïe", "vietnamese": "Cuisine vietnamienne", "regional": "Cuisine régionale",
           "korean": "Cuisine coréenne", "mexican": "Cuisine mexicaine", "turkish": "Cuisine turque", "coffee_shop": "Café", "crepe": "Crêpes", "seafood": "Fruits de mer",
           "barbecue": "Barbecue", "noodle": "Nouilles", "ramen": "Ramen", "sandwich": "Sandwichs", "salad": "Salades", "ice_cream": "Glaces"}
DAYS = {"Mo": "Lun", "Tu": "Mar", "We": "Mer", "Th": "Jeu", "Fr": "Ven", "Sa": "Sam", "Su": "Dim", "PH": "Jours fériés"}
FLAGS = [("takeaway", "Vente à emporter"), ("delivery", "Livraison"), ("outdoor_seating", "Terrasse"), ("diet:vegetarian", "Options végétariennes"),
         ("diet:vegan", "Options véganes"), ("wheelchair", "Accessible PMR"), ("air_conditioning", "Climatisation"),
         ("internet_access", "Wi-Fi"), ("reservation", "Réservation conseillée"), ("payment:cards", "Carte bancaire acceptée")]


def hours_fr(oh):
    """'Mo-Fr 09:00-18:00; Su off' -> [('Lun-Ven', '09:00-18:00'), ('Dim', 'fermé')]"""
    out = []
    for part in filter(None, (x.strip() for x in (oh or "").split(";"))):
        part = re.sub(r"\b(Mo|Tu|We|Th|Fr|Sa|Su|PH)\b", lambda m: DAYS[m.group(1)], part).replace("off", "fermé").replace("24/7", "7j/7 24h/24")
        m = re.match(r"(.*?)\s+(\d.*|fermé)$", part)
        out.append((m.group(1), m.group(2).replace(",", " · ")) if m else ("", part))
    return out


def city_of(address, tags):
    cp = tags.get("addr:postcode") or next(iter(re.findall(r"\b(69\d{3})\b", address)), "")
    if re.match(r"6900[1-9]$", cp):
        return f"Lyon {cp[-1]}{'er' if cp[-1] == '1' else 'e'}"
    return tags.get("addr:city") or {"69100": "Villeurbanne", "69300": "Caluire-et-Cuire"}.get(cp) or (re.sub(r".*\b69\d{3}\s*", "", address).title() if cp else "Lyon")


def formulas(setup, mrr):
    """Trois façons de facturer la même prestation. Montants HT."""
    sub = mrr + math.ceil(setup * 1.15 / 24)
    cash = round(setup * 0.9)
    return [
        {"name": "Comptant", "pitch": "Vous êtes propriétaire tout de suite, sans engagement.", "setup": setup, "monthly": mrr, "yearly": 0,
         "terms": "30 % à la commande, solde à la mise en ligne." + (" Mensuel sans engagement, résiliable à tout moment." if mrr else ""), "total24": setup + 24 * mrr},
        {"name": "Abonnement", "pitch": "Aucun apport : tout est lissé sur 24 mois.", "setup": 0, "monthly": sub, "yearly": 0,
         "terms": "Engagement 24 mois, prélèvement mensuel. Au terme, le tarif repasse au mensuel de la formule Comptant.", "total24": 24 * sub},
        {"name": "Annuel", "pitch": "Le moins cher : 10 % de remise et 2 mois offerts." if mrr else "Le moins cher : 10 % de remise pour un règlement à la commande.", "setup": cash, "monthly": 0, "yearly": 10 * mrr,
         "terms": "Installation remisée de 10 % et 12 mois de service réglés à la commande (10 mois facturés)." if mrr else "Installation remisée de 10 %, réglée en totalité à la commande.", "total24": cash + 20 * mrr},
    ]


def text_on(color):
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    return "#111" if (0.299 * r + 0.587 * g + 0.114 * b) > 160 else "#fff"


def brand_of(e):
    """Identité reprise du site de l'établissement. Une copie d'archive de plus de 3 ans est ignorée : le commerce a pu changer de main."""
    b = e.get("brand") or {}
    snap = re.search(r"web\.archive\.org/web/(\d{4})", b.get("url", ""))
    if snap and int(snap.group(1)) < date.today().year - 3:
        return {}
    desc = b.get("description", "")
    # une vraie phrase, pas une liste de mots-clés pour moteurs de recherche
    sentence = len(desc) >= 60 and re.search(r"\b(vous|nous|notre|votre|nos|vos|est|sont|propose|accueille|découvrez)\b", desc, re.I)
    return {**b, "description": desc if sentence and not BAD_TEXT.search(desc) else "",
            "paragraphs": [x for x in b.get("paragraphs", []) if not BAD_TEXT.search(x)],
            "logo": "" if b.get("logo", "").endswith(".svg") else b.get("logo", "")}


BAD_TEXT = re.compile(r"internet explorer|prohibited|commercial steps|démarch|mettre à jour|cookie|javascript|\ufffd|\||\d\d[ .]?\d\d[ .]?\d\d[ .]?\d\d", re.I)


def trusted(p):
    """SIRENE est rapproché par distance : on ne s'y fie que si la raison sociale ressemble à l'enseigne."""
    words = lambda s: {w for w in norm(s).split() if len(w) >= 4}
    return bool(words(p["name"]) & words(p["legal_name"]))


def nice(address):
    """'13 QUAI PERRACHE 69002 LYON 3EME' -> '13 Quai Perrache 69002 Lyon 3eme'"""
    small = {"de", "des", "du", "la", "le", "les", "et", "en", "sur", "aux", "au"}
    out = " ".join(w.lower() if i and w.lower() in small else "-".join(x.lower() if x.lower() in small else x.capitalize() for x in w.split("-")) for i, w in enumerate(address.split()))
    return re.sub(r"\b([DL])'(\w)", lambda m: m.group(1).lower() + "'" + m.group(2).upper(), out)


def own_social(urls, name):
    """Ne garde que les comptes dont l'adresse contient un mot du nom : écarte celui de l'agence web du site d'origine."""
    words = [w for w in norm(name).split() if len(w) >= 4]
    return [u for u in dict.fromkeys(x.rstrip("/") for x in urls) if any(w in norm(u).replace(" ", "") for w in words)]


def accent(color):
    """Une couleur de marque n'est reprise que si elle tient lieu d'accent : ni grise, ni trop claire, ni trop sombre."""
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", color or ""):
        return False
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    return max(r, g, b) - min(r, g, b) >= 45 and 40 < (r + g + b) / 3 < 200


# logos récupérés qui ne sont pas ceux de l'établissement (bannière téléphone, hébergeur, mosaïque de marques)
WRONG_LOGO = {"abadom", "mammam", "petezki-fils"}


def identity(p, e, slug, k=0):
    """Police, couleur et photos : celles de l'établissement si on les a trouvées, sinon un repli par métier."""
    b = brand_of(e)
    pal = PALETTES[p["segment"]][k % 5]
    fonts = b.get("fonts") or {}
    usable = lambda fam: fam and (fam in fonts.get("faces", {}) or any(fam.replace(" ", "+") in l or urllib.parse.quote(fam) in l for l in fonts.get("links", [])))
    heading, body = (fonts.get("heading") if usable(fonts.get("heading")) else None), (fonts.get("body") if usable(fonts.get("body")) else None)
    links = list(fonts.get("links", []))
    missing = [f for f, own in ((pal[1], heading), (pal[2], body)) if not own]
    if missing:
        links.append("https://fonts.googleapis.com/css2?" + "&".join("family=" + urllib.parse.quote_plus(f) + ":wght@400;600;700" for f in dict.fromkeys(missing)) + "&display=swap")
    color = b["color"] if accent(b.get("color")) else pal[0]
    return {"heading": heading or pal[1], "body": body or pal[2], "links": links, "faces": fonts.get("faces", {}), "color": color,
            "photos": ((e.get("google") or {}).get("photos", []) + b.get("photos", []))[:9], "logo": "" if slug in WRONG_LOGO else b.get("logo", ""),
            "own_font": bool(heading or body), "own_color": color != pal[0], "layout": k % LAYOUTS}


CSS = """
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;font:17px/1.6 var(--fb),system-ui,sans-serif;color:#1d1d1b;background:#fbfaf7}
h1,h2,h3{font-family:var(--fh),Georgia,serif;line-height:1.15;margin:0 0 .5em}
h1{font-size:clamp(2.2rem,6vw,4rem)}h2{font-size:clamp(1.6rem,3.5vw,2.3rem)}
a{color:inherit}img{max-width:100%;display:block}
.demo{background:#1d1d1b;color:#e9e7e0;font:13px/1.4 system-ui,sans-serif;text-align:center;padding:7px 16px}
header{position:sticky;top:0;z-index:5;background:#fbfaf7ee;backdrop-filter:blur(8px);border-bottom:1px solid #e6e2d8}
.bar{max-width:1100px;margin:0 auto;padding:12px 20px;display:flex;align-items:center;gap:20px}
.brand{font:700 1.25rem var(--fh),Georgia,serif;text-decoration:none;margin-right:auto;display:flex;align-items:center;gap:10px}
.brand img{max-height:44px;max-width:160px}
nav a{text-decoration:none;font-size:.95rem;margin-left:18px}nav a:hover{color:var(--c)}
.btn{display:inline-block;background:var(--c);color:var(--ct);padding:12px 22px;border-radius:999px;text-decoration:none;font-weight:600;border:0;font:600 1rem var(--fb),sans-serif;cursor:pointer}
.btn.ghost{background:transparent;color:inherit;border:1.5px solid currentColor}
.hero{position:relative;min-height:72vh;display:flex;align-items:flex-end;color:#fff;background:linear-gradient(135deg,var(--c),#1d1d1b)}
.hero>img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.hero::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,#0000 25%,#000c)}
.hero div{position:relative;z-index:1;max-width:1100px;width:100%;margin:0 auto;padding:60px 20px}
.hero p{font-size:1.2rem;max-width:44ch;margin:0 0 1.4em}.hero .btn{margin:0 10px 10px 0}
.kicker{text-transform:uppercase;letter-spacing:.14em;font-size:.8rem;font-weight:600;opacity:.9;margin:0 0 .8em}
section{max-width:1100px;margin:0 auto;padding:72px 20px}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:40px;align-items:start}
.two>img{width:100%;aspect-ratio:4/3;object-fit:cover}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;padding:0;list-style:none}
.cards li{background:#fff;border:1px solid #e6e2d8;border-radius:14px;padding:22px;font-weight:600;border-top:3px solid var(--c)}
.chips{display:flex;flex-wrap:wrap;gap:8px;padding:0;list-style:none}.chips li{border:1px solid #cfcabd;border-radius:999px;padding:5px 14px;font-size:.92rem}
.gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}.gallery img{width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:12px}
.menu h3{margin-top:1.6em;color:var(--c)}.menu p{margin:.35em 0;border-bottom:1px dotted #cfcabd;padding-bottom:.35em}
table{border-collapse:collapse;width:100%}td{padding:7px 0;border-bottom:1px solid #e6e2d8}td:last-child{text-align:right;font-variant-numeric:tabular-nums}
.panel{background:#fff;border:1px solid #e6e2d8;border-radius:16px;padding:28px}
form{display:grid;gap:12px}label{font-size:.9rem;font-weight:600;display:grid;gap:4px}
input,select,textarea{font:inherit;padding:11px 12px;border:1px solid #cfcabd;border-radius:10px;background:#fff;width:100%}
#ok{display:none;background:#eef6ee;border:1px solid #9cc79c;border-radius:10px;padding:12px;font-size:.95rem}
iframe{width:100%;height:320px;border:0;border-radius:16px}
footer{background:#1d1d1b;color:#bdb9ad;font-size:.88rem;padding:36px 20px;text-align:center}footer a{color:#fff}
.call{display:none}
@media(max-width:720px){nav{display:none}section{padding:52px 20px}.call{display:block;position:fixed;left:16px;right:16px;bottom:14px;text-align:center;z-index:6;box-shadow:0 6px 20px #0004}body{padding-bottom:76px}}
"""


# Six mises en page : deux maquettes voisines ne partagent ni structure, ni palette, ni polices
THEMES = [
    "",  # 0 — photo plein écran, texte en bas à gauche
    """main{display:flex;flex-direction:column}main>section{width:100%}
.hero{min-height:0;display:grid;grid-template-columns:1.05fr 1fr;align-items:stretch;color:#1d1d1b;background:color-mix(in srgb,var(--c) 11%,#fbfaf7)}
.hero>img{position:static;order:2;height:100%;min-height:560px;border-radius:0 0 0 96px}.hero::after{display:none}
.hero div{align-self:center;padding:72px 48px;margin:0}.hero .btn.ghost{color:#1d1d1b}.nophoto .hero{grid-template-columns:1fr;border-left:14px solid var(--c)}
.cards li{border-top:0;border-left:3px solid var(--c);border-radius:4px}#contact{order:-1}
@media(max-width:720px){.hero{grid-template-columns:1fr}.hero>img{min-height:260px;border-radius:0}.hero div{padding:44px 20px}}""",
    """main{display:flex;flex-direction:column}main>section{width:100%}#photos{order:-1}
header .bar{flex-direction:column;gap:6px}.brand{margin:0}header .btn{display:none}
.hero{flex-direction:column;align-items:center;text-align:center;background:#fbfaf7;color:#1d1d1b;min-height:0;padding:28px 0 0}
.hero>img{position:static;order:2;width:min(1100px,92%);height:440px;border-radius:220px 220px 20px 20px}.hero::after{display:none}
.hero div{padding:36px 20px 28px}.hero p{margin-inline:auto}.hero .btn.ghost{color:#1d1d1b}h1{font-style:italic;font-weight:400}
section h2{text-align:center}section h2::after{content:"";display:block;width:56px;height:2px;background:var(--c);margin:14px auto 0}
.cards li{text-align:center;border:0;border-bottom:1px solid #cfcabd;border-radius:0;background:transparent}.chips{justify-content:center}""",
    """body{background:#111;color:#ececea}header{background:#111e;border-color:#2a2a2a}.demo{background:var(--c);color:var(--ct)}
h1,h2{text-transform:uppercase;letter-spacing:.03em}.kicker{color:color-mix(in srgb,var(--c) 55%,#fff)!important}
.btn{border-radius:4px}.cards li,.panel{background:#1b1b1b;border-color:#2e2e2e}.cards li{border-top:0;border-bottom:3px solid var(--c);border-radius:4px}.brand img{background:#fff;padding:4px 8px;border-radius:6px}
input,select,textarea{background:#111;color:#ececea;border-color:#3a3a3a}td{border-color:#2e2e2e}.chips li{border-color:#444}
.hero{min-height:86vh;align-items:center}.hero::after{background:#000a}.gallery{grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:4px}.gallery img,.two>img{border-radius:0}
footer{background:#000}#ok{background:#18261a;border-color:#2f5a34}""",
    """body{background:#fff}main{display:flex;flex-direction:column;counter-reset:s}main>section{width:100%;border-top:2px solid #1d1d1b;counter-increment:s}
main>section>h2::before,main>section>.two>div:first-child>h2::before{content:"0" counter(s) " / ";color:var(--c);font-size:.6em;vertical-align:middle}
h1{font-size:clamp(2.6rem,9vw,6.4rem);text-transform:uppercase;letter-spacing:-.02em}.hero{min-height:64vh;align-items:center}.hero::after{background:#0009}
.btn{border-radius:0}.cards{grid-template-columns:1fr;gap:0}.cards li{border:0;border-bottom:1px solid #1d1d1b;border-radius:0;background:transparent;font-size:1.25rem;padding:18px 0}
.panel{border-radius:0;border:2px solid #1d1d1b}.gallery img,.two>img,iframe{border-radius:0}.chips li{border-radius:0;border-color:#1d1d1b}
header{border-bottom:2px solid #1d1d1b;background:#fff}""",
    """body{background:color-mix(in srgb,var(--c) 8%,#fff)}header{position:static;background:transparent;border:0}
.hero{margin:8px 20px 0;border-radius:36px;overflow:hidden;min-height:62vh;align-items:center;text-align:center}.hero::after{background:#0008}.hero p{margin-inline:auto}
.cards li{border:0;border-radius:26px;box-shadow:0 10px 28px #0000000f;padding:28px}.panel{border:0;border-radius:30px;box-shadow:0 10px 34px #00000012}
.gallery{grid-template-columns:repeat(auto-fit,minmax(200px,1fr))}.gallery img{border-radius:50% 50% 22px 22px;aspect-ratio:3/4}.two>img{border-radius:30px}
.chips li{background:#fff;border:0;box-shadow:0 2px 8px #0000000f}iframe{border-radius:30px}footer{margin:0 20px 20px;border-radius:30px}""",
]


def site_html(p, e, slug, k=0):
    t, b, sir, g = e.get("tags", {}), brand_of(e), e.get("sirene") or {}, e.get("google") or {}
    idn = identity(p, e, slug, k)
    p = {**p, "address": nice(p["address"]), "phone": p["phone"].split(";")[0].strip()}
    label, services = TYPES.get(p["type"], (p["type"].title(), []))
    if g.get("category"):  # la catégorie Google décrit mieux le métier que le type OSM ; nos prestations types ne restent que si les deux concordent
        same = norm(label)[:5] in norm(g["category"]) or norm(g["category"])[:5] in norm(label)
        label, services = g["category"], services if same else []
    city, name = city_of(p["address"], t), p["name"]
    resto, booking = p["segment"] == "restaurant", True
    tel = re.sub(r"[^\d+]", "", p["phone"])
    about = b.get("paragraphs", [])[:2] or [
        f"{name}, {label.lower()} à {city}" + (f", vous accueille au {p['address']}." if p["address"] else ".")
        + (f" L'entreprise est en activité depuis {sir['since']}." if sir.get("since") and trusted(p) and int(sir["since"]) < date.today().year - 1 else "")]
    cuisine = [CUISINE.get(c.strip(), c.strip().replace("_", " ").capitalize()) for c in t.get("cuisine", "").split(";") if c.strip()] if resto else []
    chips = cuisine + [lab for key, lab in FLAGS if t.get(key) in ("yes", "wlan", "only")]
    if p.get("rating") and p["rating"] >= 4 and (p.get("reviews") or 0) >= 10:
        chips.append(f"{str(p['rating']).replace('.', ',')} ★ sur Google ({p['reviews']} avis)")
    tagline = (b.get("description") or "")[:170] or (f"{label} à {city}." if g.get("category") and not services else None) or (", ".join(services[:3]).capitalize() + f" à {city}." if services else f"{cuisine[0]} à {city}." if cuisine else f"Bienvenue {name if name.lower().startswith('chez ') else 'chez ' + name}.")
    hours, menu = g.get("hours") or hours_fr(t.get("opening_hours")), e.get("menu") or []
    cta = "Réserver une table" if resto else "Prendre rendez-vous" if p["segment"] == "beauté" else "Demander un devis"
    lat, lon = t.get("_lat"), t.get("_lon")
    social = own_social(b.get("social", []), name) + [u for u in (t.get("contact:facebook"), t.get("contact:instagram")) if u and u.startswith("https://")]
    faces = "".join(f'@font-face{{font-family:"{css_name(f)}";src:url("{E(u)}") format("woff2");font-display:swap}}' for f, u in idn["faces"].items())
    # logo clair : pastille sombre ; logo foncé sur le thème sombre : pastille blanche (réglée dans le thème)
    chip = ' style="background:#1d1d1b;padding:4px 8px;border-radius:6px"' if b.get("logo_light") else ""
    ld = {"@context": "https://schema.org", "@type": "Restaurant" if resto else "LocalBusiness", "name": name, "telephone": p["phone"],
          "address": p["address"], "openingHours": t.get("opening_hours", ""), **({"geo": {"@type": "GeoCoordinates", "latitude": lat, "longitude": lon}} if lat else {})}

    sections = [f'<section id="apropos"><div class="two"><div><p class="kicker" style="color:var(--c)">{E(label)} · {E(city)}</p><h2>{E(name)}</h2>'
                + "".join(f"<p>{E(x)}</p>" for x in about) + (f'<ul class="chips">{"".join(f"<li>{E(c)}</li>" for c in chips)}</ul>' if chips else "") + "</div>"
                + (f'<img src="{E(idn["photos"][1])}" alt="{E(name)}" style="border-radius:16px" loading="lazy">' if len(idn["photos"]) > 1 else "") + "</div></section>"]
    if services:
        sections.append(f'<section id="prestations"><h2>Nos prestations</h2><ul class="cards">{"".join(f"<li>{E(s)}</li>" for s in services)}</ul></section>')
    if menu:
        sections.append('<section id="carte" class="menu"><h2>La carte</h2><div class="two">' + "".join(
            f'<div><h3>{E(title)}</h3>{"".join(f"<p>{E(i)}</p>" for i in items)}</div>' for title, items in menu) + "</div></section>")
    if len(idn["photos"]) > 2:
        sections.append(f'<section id="photos"><h2>En images</h2><div class="gallery">{"".join(f"""<img src="{E(u)}" alt="{E(name)}" loading="lazy">""" for u in idn["photos"][2:])}</div></section>')
    form = f"""<div class="panel"><h2>{E(cta)}</h2><form onsubmit="event.preventDefault();document.getElementById('ok').style.display='block'">
<label>Nom<input required autocomplete="name"></label><label>Téléphone<input type="tel" required autocomplete="tel"></label>
{'<label>Date<input type="date" required></label><label>Heure<input type="time" required></label>' if p["segment"] != "artisan" else ''}
{'<label>Nombre de couverts<select><option>2</option><option>3</option><option>4</option><option>5</option><option>6 et plus</option></select></label>' if resto else '<label>Votre besoin<textarea rows="3"></textarea></label>'}
<button class="btn">Envoyer la demande</button><p id="ok">Démonstration : sur le site final, cette demande arrive par e-mail et SMS chez {E(name)}, avec confirmation automatique au client.</p></form></div>"""
    contact = (f'<div><h2>Nous trouver</h2><p>{E(p["address"] or city)}</p>'
               + (f'<p><a class="btn" href="tel:{E(tel)}">{E(p["phone"])}</a></p>' if tel else "")
               + (f'<table>{"".join(f"<tr><td>{E(d)}</td><td>{E(h)}</td></tr>" for d, h in hours)}</table>' if hours else "")
               + "".join(f'<p><a href="{E(u)}" rel="noopener">{"Instagram" if "instagram" in u else "Facebook"}</a></p>' for u in dict.fromkeys(social))
               + (f'<p><a href="https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=18/{lat}/{lon}" rel="noopener">Itinéraire</a></p>' if lat else "") + "</div>")
    sections.append(f'<section id="contact"><div class="two">{contact}{form if booking else ""}</div>'
                    + (f'<p><iframe title="Plan d\'accès" loading="lazy" src="https://www.openstreetmap.org/export/embed.html?bbox={lon - .004},{lat - .002},{lon + .004},{lat + .002}&amp;layer=mapnik&amp;marker={lat},{lon}"></iframe></p>' if lat else "") + "</section>")
    nav = "".join(f'<a href="#{i}">{l}</a>' for i, l in (("apropos", "À propos"), ("prestations", "Prestations"), ("carte", "La carte"), ("photos", "Photos"), ("contact", "Contact")) if f'id="{i}"' in "".join(sections))
    hero_btn = (f'<a class="btn" href="#contact">{E(cta)}</a>' if booking else "") + (f'<a class="btn ghost" href="tel:{E(tel)}">Appeler</a>' if tel else "")
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{E(name)} — {E(label)} à {E(city)}</title><meta name="description" content="{E(tagline)}">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>{"".join(f'<link rel="stylesheet" href="{E(l)}">' for l in idn["links"])}
<style>:root{{--c:{idn["color"]};--ct:{text_on(idn["color"])};--fh:"{css_name(idn["heading"])}";--fb:"{css_name(idn["body"])}"}}{faces}{CSS}{THEMES[idn["layout"]]}</style>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False).replace("<", "\\u003c")}</script></head><body class="t{idn["layout"]}{"" if idn["photos"] else " nophoto"}">
<div class="demo">Maquette de démonstration préparée pour {E(name)} · contenus à valider avec l'établissement · page non référencée</div>
<header><div class="bar"><a class="brand" href="#">{f'<img src="{E(idn["logo"])}" alt="{E(name)}"{chip}>' if idn["logo"] else E(name)}</a><nav>{nav}</nav>{f'<a class="btn" href="tel:{E(tel)}">Appeler</a>' if tel else ""}</div></header>
<div class="hero">{f'<img src="{E(idn["photos"][0])}" alt="{E(name)}">' if idn["photos"] else ""}<div><p class="kicker">{E(label)} · {E(city)}</p><h1>{E(name)}</h1><p>{E(tagline)}</p>{hero_btn}</div></div>
<main>{"".join(sections)}</main>
<footer><p><strong>{E(name)}</strong>{" · " + E(p["address"]) if p["address"] else ""}</p>
<p>Maquette réalisée par LEADFLOW. Carte © contributeurs OpenStreetMap.{" Photos reprises de la fiche Google et du site de l'établissement, à valider avec lui." if idn["photos"] else ""}</p></footer>
{f'<a class="btn call" href="tel:{E(tel)}">Appeler {E(name)}</a>' if tel else ""}
</body></html>"""


# ---------- devis ----------

LINES = {
    "Site vitrine": "Site vitrine une page, adapté mobile : présentation, prestations, horaires, plan d'accès, bouton d'appel, référencement local (balises, données structurées). Mensuel : hébergement, nom de domaine, certificat HTTPS, mises à jour et modifications de contenu.",
    "Refonte site obsolète": "Refonte du site existant : reprise de vos textes, photos et identité (police, couleurs), mise au format mobile, HTTPS, redirection des anciennes adresses.",
    "Réservation en ligne": "Module de réservation ou de prise de rendez-vous en ligne, confirmation et rappel automatiques par SMS ou e-mail. Mensuel : licence de l'outil et support.",
    "Menu numérique": "Carte numérique lisible sur mobile, accessible par QR code, modifiable sans réimpression. Mensuel : hébergement et mises à jour de la carte.",
    "Optimisation fiche locale": "Création ou reprise de la fiche Google Business Profile : catégories, horaires, description, photos, lien vers le site. Mensuel : publications, réponses aux avis, suivi des appels.",
}
ISSUER = {"name": "LEADFLOW", "legal": "CATCHEE GROUP, SAS", "siret": "SIRET 994 785 871 00017", "address": "41 rue Jacquemars Giélée, 59800 Lille",
          "contact": "07 58 91 68 77 · cindanojonathan@gmail.com", "vat": "TVA non applicable, art. 293 B du CGI"}
# Les constats du dashboard parlent de nos sources ; le client, lui, lit un devis
CLIENT_WORDING = [("Aucun site trouvé (OSM + domaines testés)", "Aucun site internet trouvé"), ("Fiche OSM incomplète", "Informations en ligne incomplètes"),
                  ("Site injoignable", "Site internet injoignable")]
eur = lambda n: f"{n:,.0f} €".replace(",", " ")

DEVIS_CSS = ".qr{margin-top:10px;width:92px;text-align:center}.qr svg{width:92px;height:92px;display:block}.qr small{font-size:.66rem;line-height:1.2;display:block;margin-top:3px}" + """
body{font:14px/1.5 system-ui,-apple-system,sans-serif;color:#1c1c1a;margin:0;background:#f1f0ec}
.sheet{background:#fff;max-width:820px;margin:24px auto;padding:44px 48px;box-shadow:0 1px 6px #0002}
h1{font-size:26px;margin:0}h2{font-size:15px;text-transform:uppercase;letter-spacing:.08em;margin:28px 0 8px;border-bottom:2px solid #1c1c1a;padding-bottom:4px}
.head,.parties{display:flex;justify-content:space-between;gap:32px}.parties{margin-top:24px}.parties div{flex:1}
small,.muted{color:#6b6b66}table{border-collapse:collapse;width:100%}th,td{padding:8px 6px;border-bottom:1px solid #dedcd4;text-align:left;vertical-align:top}
th{font-size:12px;color:#6b6b66}td.n,th.n{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
.f{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.f div{border:1.5px solid #dedcd4;border-radius:10px;padding:14px}
.f .best{border-color:#1c1c1a}.f b{font-size:16px}.f .p{font-size:22px;font-weight:700;margin:6px 0 2px}.f ul{padding-left:16px;margin:8px 0 0}
.box{border:1px dashed #9a9a94;border-radius:8px;padding:12px;margin-top:8px}.sign{display:flex;gap:32px;margin-top:28px}.sign div{flex:1;border:1px solid #dedcd4;height:96px;padding:8px}
a{color:#2f5bd3}@media print{body{background:#fff}.sheet{box-shadow:none;margin:0;padding:24px}.noprint{display:none}.pb{break-before:page}}
@media(max-width:640px){.sheet{padding:20px}.f{grid-template-columns:1fr}.head,.parties{flex-direction:column}}
"""


def fiche_kit(p, e):
    t = e.get("tags", {})
    label, services = TYPES.get(p["type"], (p["type"].title(), []))
    city = city_of(p["address"], t)
    desc = f"{p['name']}, {label.lower()} à {city}. " + (", ".join(services) + ". " if services else "") + "Contactez-nous par téléphone ou directement depuis notre site."
    hours = (e.get("google") or {}).get("hours") or hours_fr(t.get("opening_hours"))
    return f"""<h2 class="pb">Annexe — kit fiche Google Business Profile</h2><p class="muted">Contenu prêt à saisir dès que vous nous donnez accès à votre fiche (ou à sa création).</p>
<table><tr><td>Nom</td><td>{E(p["name"])}</td></tr><tr><td>Catégorie principale</td><td>{E(label)}</td></tr>
<tr><td>Adresse</td><td>{E(nice(p["address"])) or "<em>à confirmer</em>"}</td></tr><tr><td>Téléphone</td><td>{E(p["phone"]) or "<em>à confirmer</em>"}</td></tr>
<tr><td>Horaires</td><td>{"<br>".join(f"{E(d)} {E(h)}" for d, h in hours) or "<em>à confirmer : absents de toutes les sources</em>"}</td></tr>
<tr><td>Description ({len(desc)}/750)</td><td>{E(desc)}</td></tr>
<tr><td>Photos à fournir</td><td>Façade, intérieur, équipe, {"5 plats signature, la carte" if p["segment"] == "restaurant" else "5 réalisations avant/après"} — 10 photos minimum.</td></tr>
<tr><td>Premiers avis</td><td>SMS type aux 10 derniers clients : « Bonjour, merci de votre confiance. Un avis en 30 secondes nous aiderait beaucoup : [lien court] — {E(p["name"])} »</td></tr></table>"""


def css_name(n):
    return re.sub(r"['\"\\<>&]", "", n)


def qr_svg(url):
    # qrencode (brew install qrencode) ; sans lui le devis reste valable, simplement sans QR
    try:
        out = subprocess.run(["qrencode", "-t", "SVG", "-m", "0", "-o", "-", url], capture_output=True, text=True, timeout=10, check=True).stdout
    except (OSError, subprocess.SubprocessError):
        return ""
    return re.sub(r"^.*?(?=<svg)", "", out, flags=re.S)


def devis_html(p, e, slug, number, has_site):
    ok = trusted(p)
    sir, t = (e.get("sirene") or {}) if ok else {}, e.get("tags", {})
    p = {**p, "address": nice(p["address"]), "siren": p["siren"] if ok else "", "legal_name": p["legal_name"] if ok else ""}
    today = date.today()
    fs = formulas(p["setup"], p["mrr"])
    issues = p["issues"]
    for ours, theirs in CLIENT_WORDING:
        issues = [i.replace(ours, theirs) for i in issues]
    rows = "".join(f'<tr><td><strong>{E(o)}</strong><br><span class="muted">{E(LINES[o])}</span></td><td class="n">{eur(PRICES[o][0])}</td><td class="n">{eur(PRICES[o][1]) + "/mois" if PRICES[o][1] else "—"}</td></tr>' for o in p["offers"])
    cards = "".join(f"""<div class="{'best' if f['name'] == 'Abonnement' else ''}"><b>{i}. {f['name']}</b><br><span class="muted">{f['pitch']}</span>
<p class="p">{eur(f['setup']) if f['setup'] else eur(f['monthly']) + '/mois'}</p>
<span class="muted">{('puis ' + eur(f['monthly']) + '/mois') if f['setup'] and f['monthly'] else ('+ ' + eur(f['yearly']) + '/an') if f['yearly'] else 'sans apport' if not f['setup'] else 'paiement unique'}</span>
<ul><li>{f['terms']}</li><li>Coût total sur 24 mois : <strong>{eur(f['total24'])}</strong></li></ul></div>""" for i, f in enumerate(fs, 1))
    demo = f'{BASE_URL}/{slug}/'
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Devis {number} — {E(p["name"])}</title><style>{DEVIS_CSS}</style></head><body><div class="sheet">
<div class="head"><div><h1>Devis {number}</h1><small>Émis le {today:%d/%m/%Y} · valable jusqu'au {today + timedelta(days=30):%d/%m/%Y}</small></div>
<div style="text-align:right"><strong>{E(ISSUER["name"])}</strong><br><small>{E(ISSUER["legal"])}<br>{E(ISSUER["siret"])}<br>{E(ISSUER["address"])}<br>{E(ISSUER["contact"])}</small></div></div>
<div class="parties"><div><small>Client</small><br><strong>{E(p["name"])}</strong><br>{E(p["legal_name"]) + "<br>" if p["legal_name"] and p["legal_name"].lower() != p["name"].lower() else ""}
{E(p["address"])}<br>{"SIREN " + E(p["siren"]) if p["siren"] else '<em class="muted">SIREN à confirmer</em>'}
{"<br>À l'attention de " + E(sir["boss"]) + (" (" + E(sir["role"]) + ")" if sir.get("role") else "") if sir.get("boss") else ""}</div>
<div><small>Constats</small><ul style="margin:4px 0;padding-left:16px">{"".join(f"<li>{E(i)}</li>" for i in issues)}</ul>
{f'<a class="noprint" href="{demo}">Voir la maquette en ligne</a><br><small>{demo}</small>' if has_site else ""}
{f'<div class="qr">{qr_svg(demo)}<small>Scannez pour voir votre site</small></div>' if has_site and qr_svg(demo) else ""}</div></div>
<h2>Prestations</h2><table><tr><th>Désignation</th><th class="n">Installation HT</th><th class="n">Mensuel HT</th></tr>{rows}
<tr><td><strong>Total</strong></td><td class="n"><strong>{eur(p["setup"])}</strong></td><td class="n"><strong>{eur(p["mrr"]) + "/mois" if p["mrr"] else "—"}</strong></td></tr></table>
<h2>Trois façons de régler — à cocher</h2><div class="f">{cards}</div>
<h2>Conditions</h2><ul style="padding-left:16px;margin:4px 0">
<li>Prix hors taxes. {E(ISSUER["vat"])}.</li><li>Mise en ligne sous 10 jours ouvrés après réception des contenus et de l'acompte éventuel.</li>
<li>Le client fournit ou valide textes, photos et horaires, et garantit détenir les droits sur les photos et le logo transmis.</li>
<li>Formule Comptant ou Annuel : le site et le nom de domaine appartiennent au client dès le paiement intégral. Formule Abonnement : au terme des 24 mois.</li>
<li>Deux séries de retouches incluses avant mise en ligne. Paiement à 30 jours ; pénalités de retard au taux légal et indemnité forfaitaire de 40 €.</li></ul>
<div class="sign"><div><small>Formule retenue : ☐ 1 Comptant ☐ 2 Abonnement ☐ 3 Annuel</small></div><div><small>Date, signature et mention « Bon pour accord »</small></div></div>
{fiche_kit(p, e) if "Optimisation fiche locale" in p["offers"] else ""}
</div></body></html>"""


def index_html(rows):
    """Tableau de bord local des livrables : un prospect par ligne, maquette et devis."""
    tr = "".join(f'<tr><td>{r["n"]}</td><td><strong>{E(r["p"]["name"])}</strong><br><small>{E(r["p"]["segment"])} · {E(r["boss"])}</small></td>'
                 f'<td>{"<a href=" + chr(34) + BASE_URL + "/" + r["slug"] + "/" + chr(34) + ">maquette</a>" if r["site"] else "—"}<br><small>{E(r["assets"])}</small></td>'
                 f'<td><a href="{r["slug"]}.html">devis</a></td><td class="n">{eur(r["p"]["setup"])}</td><td class="n">{eur(r["p"]["mrr"])}</td>'
                 f'<td class="n">{eur(r["f"][1]["monthly"])}/mois</td><td class="n">{eur(r["f"][2]["setup"] + r["f"][2]["yearly"])}</td></tr>' for r in rows)
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>LEADFLOW Devis et maquettes</title>
<style>{DEVIS_CSS}.sheet{{max-width:1100px}}</style></head><body><div class="sheet"><h1>Devis et maquettes</h1>
<p class="muted">{len(rows)} devis · {sum(1 for r in rows if r["site"])} maquettes en ligne · généré le {date.today():%d/%m/%Y}. Document interne : ne pas publier.</p>
<div style="overflow-x:auto"><table><tr><th>N°</th><th>Prospect</th><th>Maquette</th><th>Devis</th><th class="n">Comptant</th><th class="n">+ mensuel</th><th class="n">Abonnement</th><th class="n">Annuel (1re année)</th></tr>{tr}</table></div></div></body></html>"""
