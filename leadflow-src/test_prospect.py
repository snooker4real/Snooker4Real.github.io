"""Tests hors ligne : python3 -m unittest test_prospect"""
import unittest
from prospect import guess_domains, menu_pages, norm, parse_place, pdf_menus, pick_etab, score, site_matches

LYON = (45.7640, 4.8357)
SITE_OK = {"https": True, "mobile": True, "booking": True, "pdf_menu": "", "year": None}


def cand(seg="artisan", tags=None, site_url=None, site=None, google=None):
    return {"seg": seg, "tags": {"phone": "1", "opening_hours": "x"} if tags is None else tags, "site_url": site_url, "site": site, "google": google}


class Score(unittest.TestCase):
    def test_no_site_unconfirmed_vs_confirmed(self):
        s, o, i = score(cand("beauté", tags={}))
        self.assertEqual((s, o), (45, ["site", "reservation", "fiche"]))
        g = {"hours": True, "photos": 8, "reviews": 30}
        s, o, i = score(cand("beauté", google=g))
        self.assertEqual((s, o), (50, ["site", "reservation"]))
        self.assertIn("confirmé", i[0])

    def test_pdf_menu(self):
        s, o, _ = score(cand("restaurant", site_url="x", site={**SITE_OK, "pdf_menu": "x/carte.pdf"}))
        self.assertEqual((s, o), (20, ["menu"]))

    def test_healthy_business_has_no_offer(self):
        self.assertEqual(score(cand(site_url="x", site=SITE_OK))[1], [])

    def test_blocked_site_is_not_reported_down(self):
        s, o, i = score(cand(site_url="x", site={"blocked": True}))
        self.assertEqual((s, o), (0, []))

    def test_weak_google_listing(self):
        s, o, i = score(cand(site_url="x", site=SITE_OK, google={"hours": False, "photos": 2, "reviews": 40}))
        self.assertEqual((s, o, i), (20, ["fiche"], ["Fiche Google faible : horaires, 2 photos"]))


class Sirene(unittest.TestCase):
    def etab(self, lat, lon, state="A"):
        return {"siren": "1", "nom_complet": "X", "matching_etablissements": [
            {"latitude": str(lat), "longitude": str(lon), "etat_administratif": state, "adresse": "a"}]}

    def test_matches_nearby_and_reads_status(self):
        self.assertEqual(pick_etab([self.etab(45.7641, 4.8357, "F")], *LYON)["status"], "fermé")

    def test_rejects_homonym_far_away(self):
        self.assertIsNone(pick_etab([self.etab(45.6338, 4.6116)], *LYON))  # Chaussan, ~20 km


class Google(unittest.TestCase):
    def test_parse_and_distance_guard(self):
        p = {"places": [{"location": {"latitude": 45.7641, "longitude": 4.8357}, "photos": [{}] * 3,
                         "userRatingCount": 12, "businessStatus": "OPERATIONAL"}]}
        g = parse_place(p, *LYON)
        self.assertEqual((g["photos"], g["reviews"], g["hours"], g["website"]), (3, 12, False, ""))
        p["places"][0]["location"] = {"latitude": 45.80, "longitude": 4.8357}
        self.assertIsNone(parse_place(p, *LYON))


class Web(unittest.TestCase):
    def test_norm_and_domains(self):
        self.assertEqual(norm("L’Atelier Vintage-Café"), "l atelier vintage cafe")
        self.assertIn("https://www.les-incorruptibles.fr", guess_domains("Les Incorruptibles"))
        self.assertEqual(guess_domains("L'Atelier"), [])

    def test_guessed_site_needs_visible_name_and_city(self):
        page = "<title>Home Comfort</title><p>Chauffage à {}</p><script>var x='wroistatlyonid'</script>"
        self.assertTrue(site_matches(page.format("Lyon 3e"), "homecomfort"))
        self.assertFalse(site_matches(page.format("Nantes"), "homecomfort"))

    def test_menu_links(self):
        urls = ["https://r.fr/la-carte", "https://r.fr/contact", "https://autre.fr/menu", "https://r.fr/doc/menu.PDF"]
        self.assertEqual(menu_pages(urls, "r.fr"), ["https://r.fr/la-carte"])
        self.assertEqual(pdf_menus(urls), ["https://r.fr/doc/menu.PDF"])


if __name__ == "__main__":
    unittest.main()
