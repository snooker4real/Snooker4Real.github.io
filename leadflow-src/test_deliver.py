"""Tests hors ligne : python3 -m unittest test_deliver"""
import os, tempfile, unittest
from deliver import css_brand, extract, good_photo, google_hours, needs_site, parse_menu, requalify, slugs
from render import THEMES, brand_of, city_of, devis_html, formulas, hours_fr, identity, nice, own_social, site_html

P = {"name": "Chez <Léa>", "segment": "restaurant", "type": "restaurant", "address": "3 RUE X 69002 LYON", "phone": "+33 4 00 00 00 00",
     "siren": "123", "legal_name": "LEA SAS", "osm": "https://www.openstreetmap.org/node/1", "issues": ["Aucun site trouvé"],
     "offers": ["Site vitrine", "Optimisation fiche locale"], "setup": 800, "mrr": 68}


class Deliver(unittest.TestCase):
    def test_slugs_are_unique(self):
        ps = [{"name": "Le Café", "osm": "x/node/1"}, {"name": "Le Cafe", "osm": "x/node/2"}, {"name": "Ushi", "osm": "x/node/3"}]
        self.assertEqual(slugs(ps), ["le-cafe-1", "le-cafe-2", "ushi"])

    def test_formulas(self):
        cash, sub, year = formulas(800, 68)
        self.assertEqual((cash["setup"], cash["monthly"], cash["total24"]), (800, 68, 2432))
        self.assertEqual((sub["setup"], sub["monthly"], sub["total24"]), (0, 107, 2568))
        self.assertEqual((year["setup"], year["yearly"], year["total24"]), (720, 680, 2080))

    def test_hours_and_city(self):
        self.assertEqual(hours_fr("Mo-Fr 09:00-12:00,14:00-18:00; Su off"), [("Lun-Ven", "09:00-12:00 · 14:00-18:00"), ("Dim", "fermé")])
        self.assertEqual(city_of("3 RUE X 69001 LYON", {}), "Lyon 1er")
        self.assertEqual(city_of("", {"addr:postcode": "69100"}), "Villeurbanne")

    def test_extract_reuses_text_images_and_skips_noise(self):
        doc = ('<title>Léa</title><meta name="description" content="Bistrot"><img class="logo" src="/l.png"><img src="a.jpg"><img src="icon.png">'
               '<p>' + "Cuisine du marché faite maison. " * 4 + '</p><p>' + "Nous utilisons des cookies pour le site. " * 3 + '</p>'
               '<a href="https://www.instagram.com/lea/?hl=fr">i</a>')
        b = extract(doc, "https://lea.fr/")
        self.assertEqual((b["description"], b["logo"], b["images"], b["social"]), ("Bistrot", "https://lea.fr/l.png", ["https://lea.fr/a.jpg"], ["https://www.instagram.com/lea/"]))
        self.assertEqual(len(b["paragraphs"]), 1)

    def test_css_brand(self):
        css = ("body{font-family:'Lato',sans-serif;color:#333}h1{font-family:\"Abril Fatface\",serif;color:#c0392b}.x{color:#c0392b}"
               ".i{font-family:FontAwesome}@font-face{font-family:Abril Fatface;src:url(/f/abril.woff2) format('woff2')}")
        self.assertEqual(css_brand(css), ("Abril Fatface", "Lato", {"Abril Fatface": "/f/abril.woff2"}, "#c0392b"))

    def test_brand_identity_wins_over_fallback(self):
        e = {"brand": {"color": "#c0392b", "photos": ["img/photo-1.jpg"], "fonts": {"heading": "Lato", "body": "", "faces": {},
                                                                                   "links": ["https://fonts.googleapis.com/css2?family=Lato"]}}}
        idn = identity(P, e, "chez-lea")
        self.assertEqual((idn["heading"], idn["color"], idn["own_font"]), ("Lato", "#c0392b", True))
        self.assertFalse(identity(P, {}, "chez-lea")["own_font"])

    def test_pages_escape_and_flag_demo(self):
        page = site_html(P, {"tags": {"_lat": 45.76, "_lon": 4.83, "cuisine": "french"}}, "chez-lea")
        self.assertIn("Chez &lt;Léa&gt;", page)
        self.assertNotIn("<Léa>", page)
        self.assertIn('content="noindex, nofollow"', page)
        self.assertIn("Maquette de démonstration", page)
        quote = devis_html(P, {}, "chez-lea", "LF-1", True)
        self.assertIn("2 568 €", quote)
        self.assertIn("kit fiche Google", quote)

    def test_parse_menu_keeps_priced_lines_or_nothing(self):
        text = "ENTRÉES\n" + "\n".join(f"Plat {i} 12,50 €" for i in range(5)) + "\nDesserts\nune phrase sans prix\n" + "\n".join(f"Tarte maison {i} 8€" for i in range(4))
        self.assertEqual([(t, len(i)) for t, i in parse_menu(text)], [("Entrées", 5), ("Desserts", 4)])
        self.assertEqual(parse_menu("Bienvenue\nPlat 12 €"), [])

    def test_google_maps_requalifies(self):
        self.assertEqual(google_hours(["mardi12:00–14:0019:30–22:00\ue14d", "lundiFermé"]), [("Lundi", "Fermé"), ("Mardi", "12:00–14:00 · 19:30–22:00")])
        self.assertEqual(google_hours(["mercredi(Armistice)Fermé Horaires des jours fériés"]), [])
        self.assertEqual(google_hours(["lundiOuvert 24h/24", "mardiOuvert 24h/24"]), [])  # fiche jamais renseignée
        maps = lambda **k: {"le-cafe": {"closed": False, "website": "", "hours": ["lundi9:00–18:00"], "photos": [], "reviews": "40", "rating": "4,5",
                                        "phone": "04", "address": "1 Rue X, 69001 Lyon", "category": "Café", "url": "https://g/x?y", "name": "Le Café", **k}}
        ps = [{**P, "name": "Le Café", "segment": "beauté", "website": "", "website_source": "", "phone": "", "address": "4"}]
        data = {"le-cafe": {"tags": {}}}
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(tempfile.mkdtemp())  # requalify range les photos dans site/ : pas dans le vrai dossier
        self.assertEqual(requalify(ps, data, maps(closed=True))[0], [])
        out = requalify(ps, data, maps(website="https://www.planity.com/le-cafe"))[0][0]
        self.assertEqual((out["offers"], out["phone"], out["address"], out["rating"]), (["Site vitrine", "Optimisation fiche locale"], "04", "1 Rue X, 69001 Lyon", 4.5))
        self.assertIn("planity.com", out["issues"][0])
        renamed = requalify(ps, data, maps(name="Chez Paulette"))[0]
        self.assertEqual((renamed[0]["name"], slugs(renamed)), ("Chez Paulette", ["le-cafe"]))  # enseigne changée, adresse de maquette stable
        self.assertEqual(requalify([{**ps[0], "siren": ""}], data, {}, {"le-cafe": ""})[0], [])  # ni fiche ni SIREN fiable : écarté
        kept = requalify([{**ps[0], "siren": "1", "score": 40}], data, {}, {"le-cafe": ""})[0][0]
        self.assertIn("Optimisation fiche locale", kept["offers"])
        self.assertIn("à créer", kept["issues"][-1])

    def test_photo_and_text_filters(self):
        self.assertEqual([good_photo(d) for d in ((1600, 900), (600, 160), (512, 512), (480, 640))], [True, False, False, False])
        self.assertEqual(nice("9 RUE DES FRERES D'ANVERS 69300 CALUIRE-ET-CUIRE"), "9 Rue des Freres d'Anvers 69300 Caluire-et-Cuire")
        self.assertEqual(own_social(["https://instagram.com/creasens.agency/", "https://facebook.com/chabertetfils"], "Comptoir Chabert et Fils"), ["https://facebook.com/chabertetfils"])

    def test_tagline_must_be_a_sentence(self):
        keep = "Au cœur du 8e, notre bistrot vous accueille midi et soir avec une cuisine de saison."
        self.assertEqual(brand_of({"brand": {"description": keep}})["description"], keep)
        self.assertEqual(brand_of({"brand": {"description": "Coiffeur créateur. Salon de coiffure lyon 7e gerland. Coiffure mixte, coloration."}})["description"], "")

    def test_neighbours_get_different_layouts(self):
        pages = [site_html(P, {}, "chez-lea", k) for k in range(len(THEMES))]
        self.assertEqual(len({p.split("<body class=")[1][:4] for p in pages}), len(THEMES))
        self.assertEqual(len({identity(P, {}, "x", k)["heading"] for k in range(5)}), 5)

    def test_needs_site(self):
        self.assertTrue(needs_site(P, {}))
        menu_only = {**P, "offers": ["Menu numérique"]}
        self.assertFalse(needs_site(menu_only, {}))
        self.assertTrue(needs_site(menu_only, {"menu": [["Entrées", ["Œuf"]]]}))


if __name__ == "__main__":
    unittest.main()
