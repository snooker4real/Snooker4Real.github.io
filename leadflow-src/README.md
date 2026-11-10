# LEADFLOW Prospect

Trouve des TPE autour d'un point (Lyon par défaut), audite leur présence web et estime la prestation à leur vendre.

```bash
python3 prospect.py                                  # ~5-8 min, aucune dépendance
GOOGLE_PLACES_API_KEY=xxx python3 prospect.py        # + audit des fiches Google
python3 -m unittest test_prospect                    # tests hors ligne
```

Sorties : `prospects.json` et `dashboard.html` (non versionnés : données de prospects).

## Pipeline

1. **OpenStreetMap** (Overpass) : artisans, restaurants, coiffure/beauté dans le rayon.
2. **Annuaire des entreprises** (SIRENE, gratuit) : rapprochement par nom + position (< 150 m). Les établissements fermés sont écartés ; le SIREN est affiché.
3. **Google Places** (optionnel) : site, horaires, photos, avis, statut. Confirme l'absence de site.
4. **Recherche de site** : sans site connu ni fiche Google, teste des domaines plausibles (`nom.fr`, `nom.com`…). Retenu seulement si la page cite le nom et Lyon.
5. **Audit du site** : joignable, HTTPS, mobile, réservation en ligne, menu PDF (pages « carte/menu » suivies), copyright ancien.
6. **Score et offres** : 100 prospects, segments équilibrés, vérifiés SIRENE et joignables d'abord.

## Fiabilité des constats

| Constat | Fiabilité |
|---|---|
| Aucun site (confirmé Google) | haute |
| Aucun site trouvé (OSM + domaines testés) | moyenne : vérifier avant contact |
| Site injoignable | haute (DNS mort, domaine expiré, page 404) |
| Fiche Google faible | haute (avec clé) ; sans clé, repli sur la fiche OSM |

## Google Places

Clé à créer dans Google Cloud Console (API « Places API (New) »). Les champs site/avis relèvent du palier Enterprise de Text Search :
compter quelques dizaines de dollars pour ~300 recherches au-delà du quota gratuit. Les conditions Google limitent la conservation
des données Places : ne pas les stocker durablement hors d'un usage de prospection ponctuel.

## Cadre légal

Prospection B2B par e-mail : message en rapport avec l'activité du destinataire, identification de l'expéditeur, opposition simple.
Attribution : © contributeurs OpenStreetMap (ODbL) ; annuaire des entreprises (Licence Ouverte).

## Livrables : maquettes, devis, approche

```
python3 deliver.py enrich   # tags OSM, SIRENE, identité reprise des sites (photos, logo, polices, couleur)
python3 deliver.py google   # recoupe avec gmaps/matched.json (fiches Google Maps), écarte les fermés, refait le score
python3 deliver.py menus    # cartes PDF -> texte (demande pypdf)
python3 deliver.py build    # site/leadflow/<slug>/ + devis/<slug>.html + devis/index.html
```

Les maquettes sont publiées en copiant `site/leadflow/` dans le dépôt `Snooker4Real.github.io` : elles répondent sur `https://snooker4real.github.io/leadflow/<slug>/`, non référencées. `APPROCHE.md` décrit la démarche commerciale. L'en-tête des devis se règle dans `render.py` (`ISSUER`).

## Prospects, produits, maquettes et devis

Tableau généré par `python3 deliver.py build`, trié par score. Les devis sont des fichiers locaux (`devis/`, non versionnés) ; les maquettes sont en ligne.

<!-- prospects:start -->
| # | Prospect | Métier | Ville | Téléphone | Produits | Installation | Mensuel | Score | Maquette | Devis |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Taravel | artisan | Villeurbanne | +33 4 72 81 77 41 | Site vitrine, Optimisation fiche locale | 800 € | 68 €/mois | 80 | [voir](https://snooker4real.github.io/leadflow/taravel/) | [LF-2026-157150](devis/taravel.html) |
| 2 | Pradal Frères | artisan | Lyon 6e | — | Site vitrine, Optimisation fiche locale | 800 € | 68 €/mois | 80 | [voir](https://snooker4real.github.io/leadflow/pradal-freres/) | [LF-2026-993203](devis/pradal-freres.html) |
| 3 | Multitude | artisan | Lyon 3e | +33 4 72 33 71 34 | Site vitrine, Optimisation fiche locale | 800 € | 68 €/mois | 80 | [voir](https://snooker4real.github.io/leadflow/multitude/) | [LF-2026-244380](devis/multitude.html) |
| 4 | Plomberie Blein | artisan | Lyon 7e | 0478380765 | Site vitrine, Optimisation fiche locale | 800 € | 68 €/mois | 80 | [voir](https://snooker4real.github.io/leadflow/plomberie-blein/) | [LF-2026-726518](devis/plomberie-blein.html) |
| 5 | B2A | artisan | Lyon 7e | 0481911424 | Site vitrine, Optimisation fiche locale | 800 € | 68 €/mois | 70 | [voir](https://snooker4real.github.io/leadflow/b2a/) | [LF-2026-074846](devis/b2a.html) |
| 6 | Vaquier | artisan | Lyon 7e | 0437374901 | Site vitrine, Optimisation fiche locale | 800 € | 68 €/mois | 70 | [voir](https://snooker4real.github.io/leadflow/vaquier/) | [LF-2026-277824](devis/vaquier.html) |
| 7 | La Biosthétique Patricia Bert-Gauthier | beauté | Lyon 4e | +33 4 78 28 72 66 | Site vitrine, Réservation en ligne, Optimisation fiche locale | 1150 € | 107 €/mois | 70 | [voir](https://snooker4real.github.io/leadflow/la-biosthetique-patricia-bert-gauthier/) | [LF-2026-153668](devis/la-biosthetique-patricia-bert-gauthier.html) |
| 8 | Plomberie Manzanarès | artisan | Lyon 7e | +33478610121 | Site vitrine, Optimisation fiche locale | 800 € | 68 €/mois | 70 | [voir](https://snooker4real.github.io/leadflow/plomberie-manzanares/) | [LF-2026-663695](devis/plomberie-manzanares.html) |
| 9 | Jérôme Romanyck | beauté | Lyon 3e | +33478604621 | Site vitrine, Réservation en ligne, Optimisation fiche locale | 1150 € | 107 €/mois | 60 | [voir](https://snooker4real.github.io/leadflow/jerome-romanyck/) | [LF-2026-303894](devis/jerome-romanyck.html) |
| 10 | Hair Passion | beauté | Lyon 7e | +33 4 78 72 75 88 | Site vitrine, Réservation en ligne, Optimisation fiche locale | 1150 € | 107 €/mois | 60 | [voir](https://snooker4real.github.io/leadflow/hair-passion/) | [LF-2026-211902](devis/hair-passion.html) |
| 11 | Beautiful Day | beauté | Lyon 3e | +33478622041 | Site vitrine, Réservation en ligne, Optimisation fiche locale | 1150 € | 107 €/mois | 60 | [voir](https://snooker4real.github.io/leadflow/beautiful-day/) | [LF-2026-704411](devis/beautiful-day.html) |
| 12 | Coif' Détente | beauté | Lyon 3e | +33 4 72 34 59 99 | Site vitrine, Réservation en ligne, Optimisation fiche locale | 1150 € | 107 €/mois | 60 | [voir](https://snooker4real.github.io/leadflow/coif-detente/) | [LF-2026-074518](devis/coif-detente.html) |
| 13 | Verlène | beauté | Lyon 7e | +33472718986 | Site vitrine, Réservation en ligne, Optimisation fiche locale | 1150 € | 107 €/mois | 60 | [voir](https://snooker4real.github.io/leadflow/verlene/) | [LF-2026-052947](devis/verlene.html) |
| 14 | Glance Coiffure | beauté | Lyon 8e | +33478764055 | Site vitrine, Réservation en ligne, Optimisation fiche locale | 1150 € | 107 €/mois | 60 | [voir](https://snooker4real.github.io/leadflow/glance-coiffure/) | [LF-2026-696353](devis/glance-coiffure.html) |
| 15 | Salon Luc | beauté | Lyon 1er | +33 4 78 39 01 31 | Site vitrine, Réservation en ligne, Optimisation fiche locale | 1150 € | 107 €/mois | 60 | [voir](https://snooker4real.github.io/leadflow/salon-luc/) | [LF-2026-402509](devis/salon-luc.html) |
| 16 | N’Hair’J | beauté | Lyon 3e | +33 4 37 91 63 50 | Site vitrine, Optimisation fiche locale | 800 € | 68 €/mois | 60 | [voir](https://snooker4real.github.io/leadflow/n-hair-j/) | [LF-2026-213914](devis/n-hair-j.html) |
| 17 | La Maison de la Clé | artisan | Lyon 1er | +33 4 78 27 33 75 | Site vitrine, Optimisation fiche locale | 800 € | 68 €/mois | 60 | [voir](https://snooker4real.github.io/leadflow/la-maison-de-la-cle/) | [LF-2026-181366](devis/la-maison-de-la-cle.html) |
| 18 | Plomberie Charlemagne | artisan | Lyon 2e | 0478426876 | Site vitrine, Optimisation fiche locale | 800 € | 68 €/mois | 60 | [voir](https://snooker4real.github.io/leadflow/plomberie-charlemagne/) | [LF-2026-856864](devis/plomberie-charlemagne.html) |
| 19 | Espace coiffure par Cécile Andine | beauté | Caluire-et-Cuire | +33478082903 | Site vitrine, Optimisation fiche locale | 800 € | 68 €/mois | 60 | [voir](https://snooker4real.github.io/leadflow/espace-coiffure-par-cecile-andine/) | [LF-2026-039488](devis/espace-coiffure-par-cecile-andine.html) |
| 20 | Le petit salon | beauté | Lyon 5e | +33981871371 | Site vitrine, Optimisation fiche locale | 800 € | 68 €/mois | 60 | [voir](https://snooker4real.github.io/leadflow/le-petit-salon/) | [LF-2026-574290](devis/le-petit-salon.html) |
| 21 | Rep-Serrures | artisan | Lyon 6e | +33 478 520 785 | Site vitrine, Optimisation fiche locale | 800 € | 68 €/mois | 60 | [voir](https://snooker4real.github.io/leadflow/rep-serrures/) | [LF-2026-497710](devis/rep-serrures.html) |
| 22 | Buvette Bonaparte | restaurant | Lyon 2e | — | Site vitrine, Optimisation fiche locale | 800 € | 68 €/mois | 60 | [voir](https://snooker4real.github.io/leadflow/buvette-bonaparte/) | [LF-2026-145936](devis/buvette-bonaparte.html) |
| 23 | Cameleone Coiffure | beauté | Lyon 3e | 0478547620 | Site vitrine, Réservation en ligne, Optimisation fiche locale | 1150 € | 107 €/mois | 60 | [voir](https://snooker4real.github.io/leadflow/cameleone-coiffure/) | [LF-2026-579345](devis/cameleone-coiffure.html) |
| 24 | My158 Coiffure & Art | beauté | Lyon 7e | +33 6 14 26 04 94 | Site vitrine, Réservation en ligne, Optimisation fiche locale | 1150 € | 107 €/mois | 60 | [voir](https://snooker4real.github.io/leadflow/my158-coiffure-art/) | [LF-2026-773841](devis/my158-coiffure-art.html) |
| 25 | Tina création | beauté | Caluire-et-Cuire | +33 4 72 00 86 94 | Site vitrine, Réservation en ligne, Optimisation fiche locale | 1150 € | 107 €/mois | 60 | [voir](https://snooker4real.github.io/leadflow/tina-creation/) | [LF-2026-166107](devis/tina-creation.html) |
| 26 | Caroline Coiffure | beauté | Lyon 8e | +33 9 83 89 53 00 | Site vitrine, Réservation en ligne, Optimisation fiche locale | 1150 € | 107 €/mois | 60 | [voir](https://snooker4real.github.io/leadflow/caroline-coiffure/) | [LF-2026-678582](devis/caroline-coiffure.html) |
| 27 | Coiffure et barbier Saroli Victor | beauté | Lyon 8e | +33 4 78 72 05 67 | Site vitrine, Réservation en ligne, Optimisation fiche locale | 1150 € | 107 €/mois | 60 | [voir](https://snooker4real.github.io/leadflow/victorio/) | [LF-2026-269458](devis/victorio.html) |
| 28 | Les Incorruptibles | beauté | Lyon 2e | +33 4 78 42 76 18 | Site vitrine, Optimisation fiche locale | 800 € | 68 €/mois | 60 | [voir](https://snooker4real.github.io/leadflow/les-incorruptibles/) | [LF-2026-757077](devis/les-incorruptibles.html) |
| 29 | Côté Parc | restaurant | Villeurbanne | +33 4 37 43 12 36 | Site vitrine, Optimisation fiche locale | 800 € | 68 €/mois | 60 | [voir](https://snooker4real.github.io/leadflow/cote-parc/) | [LF-2026-013914](devis/cote-parc.html) |
| 30 | Le Genova | restaurant | Lyon 3e | +33 4 72 68 06 67 | Site vitrine, Optimisation fiche locale | 800 € | 68 €/mois | 60 | [voir](https://snooker4real.github.io/leadflow/le-genova/) | [LF-2026-331855](devis/le-genova.html) |
| 31 | Marion Esthétique | beauté | Lyon 3e | +33 4 72 34 03 96 | Site vitrine, Réservation en ligne | 950 € | 68 €/mois | 50 | [voir](https://snooker4real.github.io/leadflow/marion-esthetique/) | [LF-2026-487550](devis/marion-esthetique.html) |
| 32 | Petezki & Fils | artisan | Lyon 8e | +33 4 78 76 00 04 | Refonte site obsolète, Optimisation fiche locale | 1100 € | 39 €/mois | 50 | [voir](https://snooker4real.github.io/leadflow/petezki-fils/) | [LF-2026-068084](devis/petezki-fils.html) |
| 33 | Du Monde Ailleurs | restaurant | Lyon 2e | +33 9 84 54 58 44 | Site vitrine | 600 € | 29 €/mois | 50 | [voir](https://snooker4real.github.io/leadflow/du-monde-ailleurs/) | [LF-2026-811138](devis/du-monde-ailleurs.html) |
| 34 | Ramen Masa | restaurant | Lyon 7e | 0472733514 | Site vitrine | 600 € | 29 €/mois | 50 | [voir](https://snooker4real.github.io/leadflow/ramen-masa/) | [LF-2026-718453](devis/ramen-masa.html) |
| 35 | Ginette et Marius | restaurant | Lyon 8e | +33 4 78 74 00 02 | Site vitrine | 600 € | 29 €/mois | 50 | [voir](https://snooker4real.github.io/leadflow/ginette-et-marius/) | [LF-2026-449540](devis/ginette-et-marius.html) |
| 36 | Chez Micheline | restaurant | Lyon 2e | +33478928287 | Site vitrine | 600 € | 29 €/mois | 50 | [voir](https://snooker4real.github.io/leadflow/chez-micheline/) | [LF-2026-109613](devis/chez-micheline.html) |
| 37 | Enjoy | restaurant | Lyon 3e | +33 9 74 64 09 19 | Site vitrine | 600 € | 29 €/mois | 50 | [voir](https://snooker4real.github.io/leadflow/enjoy/) | [LF-2026-718443](devis/enjoy.html) |
| 38 | Caract'hair | beauté | Villeurbanne | +33 4 69 84 55 57 | Site vitrine | 600 € | 29 €/mois | 50 | [voir](https://snooker4real.github.io/leadflow/caract-hair/) | [LF-2026-858221](devis/caract-hair.html) |
| 39 | Le Lyon de l'Atlas | restaurant | Lyon 8e | +33 4 78 00 56 81 | Site vitrine | 600 € | 29 €/mois | 50 | [voir](https://snooker4real.github.io/leadflow/le-lyon-de-l-atlas/) | [LF-2026-207812](devis/le-lyon-de-l-atlas.html) |
| 40 | Qualitec Chauffage | artisan | Lyon 2e | 0478383838 | Site vitrine | 600 € | 29 €/mois | 50 | [voir](https://snooker4real.github.io/leadflow/qualitec-chauffage/) | [LF-2026-673692](devis/qualitec-chauffage.html) |
| 41 | L'Industrie | restaurant | Lyon 8e | +33 4 78 76 44 65 | Site vitrine | 600 € | 29 €/mois | 50 | [voir](https://snooker4real.github.io/leadflow/l-industrie/) | [LF-2026-948298](devis/l-industrie.html) |
| 42 | Asia Bti | artisan | Lyon 7e | — | Site vitrine, Optimisation fiche locale | 800 € | 68 €/mois | 45 | [voir](https://snooker4real.github.io/leadflow/asia-bti/) | [LF-2026-915669](devis/asia-bti.html) |
| 43 | Coiffeur Franck Brévi | beauté | Lyon 7e | +33 4 72 73 15 38 | Refonte site obsolète, Réservation en ligne | 1250 € | 39 €/mois | 45 | [voir](https://snooker4real.github.io/leadflow/coiffeur-franck-brevi/) | [LF-2026-457089](devis/coiffeur-franck-brevi.html) |
| 44 | Adonys | restaurant | Lyon 2e | +33437575645 | Refonte site obsolète, Optimisation fiche locale | 1100 € | 39 €/mois | 40 | [voir](https://snooker4real.github.io/leadflow/adonys/) | [LF-2026-109620](devis/adonys.html) |
| 45 | Zéphir | artisan | Lyon 7e | 0609907405 | Refonte site obsolète, Optimisation fiche locale | 1100 € | 39 €/mois | 40 | [voir](https://snooker4real.github.io/leadflow/zephir/) | [LF-2026-530818](devis/zephir.html) |
| 46 | Gema Bat | artisan | Lyon 3e | +33 6 58 70 53 08 | Refonte site obsolète, Optimisation fiche locale | 1100 € | 39 €/mois | 40 | [voir](https://snooker4real.github.io/leadflow/gema-bat/) | [LF-2026-699316](devis/gema-bat.html) |
| 47 | Les Évadés | restaurant | Lyon 5e | +33 4 72 04 19 65 | Menu numérique, Optimisation fiche locale | 370 € | 58 €/mois | 30 | [voir](https://snooker4real.github.io/leadflow/les-evades/) | [LF-2026-252048](devis/les-evades.html) |
| 48 | Vélcroc | restaurant | Lyon 6e | +33 9 63 21 11 89 | Menu numérique, Optimisation fiche locale | 370 € | 58 €/mois | 30 | [voir](https://snooker4real.github.io/leadflow/velcroc/) | [LF-2026-293641](devis/velcroc.html) |
| 49 | Fratelli Parisi | restaurant | Lyon 6e | +33 4 78 89 61 13 | Menu numérique, Optimisation fiche locale | 370 € | 58 €/mois | 30 | [voir](https://snooker4real.github.io/leadflow/fratelli-parisi/) | [LF-2026-998574](devis/fratelli-parisi.html) |
| 50 | R. André & Fils | artisan | Lyon 3e | +33 4 78 58 44 88 | Refonte site obsolète, Optimisation fiche locale | 1100 € | 39 €/mois | 20 | [voir](https://snooker4real.github.io/leadflow/r-andre-fils/) | [LF-2026-428361](devis/r-andre-fils.html) |
| 51 | Beauty Success L'Institut Lyon Monplaisir | beauté | Lyon 8e | +33 437905382 | Refonte site obsolète, Optimisation fiche locale | 1100 € | 39 €/mois | 20 | [voir](https://snooker4real.github.io/leadflow/citron-vert-freres-lumiere/) | [LF-2026-918227](devis/citron-vert-freres-lumiere.html) |
| 52 | Abadom | artisan | Lyon 7e | +33 4 72 72 06 06 | Refonte site obsolète, Optimisation fiche locale | 1100 € | 39 €/mois | 20 | [voir](https://snooker4real.github.io/leadflow/abadom/) | [LF-2026-582428](devis/abadom.html) |
| 53 | Cassard & Bazin | artisan | Lyon 2e | +33478374274 | Refonte site obsolète, Optimisation fiche locale | 1100 € | 39 €/mois | 20 | [voir](https://snooker4real.github.io/leadflow/cassard-bazin/) | [LF-2026-227201](devis/cassard-bazin.html) |
| 54 | Le Bouchon des Carnivores | restaurant | Lyon 2e | +33 4 78 42 97 69 | Refonte site obsolète | 900 € | 0 €/mois | 20 | [voir](https://snooker4real.github.io/leadflow/le-bouchon-des-carnivores/) | [LF-2026-109622](devis/le-bouchon-des-carnivores.html) |
| 55 | Dilibat | artisan | Lyon 3e | 0478620585 | Optimisation fiche locale | 200 € | 39 €/mois | 20 | aucune | [LF-2026-588617](devis/dilibat.html) |
| 56 | Têtedoie | restaurant | Lyon 5e | +33 4 78 29 40 10 | Menu numérique | 170 € | 19 €/mois | 20 | [voir](https://snooker4real.github.io/leadflow/tetedoie/) | [LF-2026-690944](devis/tetedoie.html) |
| 57 | Ushi | restaurant | Lyon 2e | — | Menu numérique | 170 € | 19 €/mois | 20 | [voir](https://snooker4real.github.io/leadflow/ushi/) | [LF-2026-110370](devis/ushi.html) |
| 58 | Home Comfort | artisan | Lyon 6e | +33472744763 | Refonte site obsolète, Optimisation fiche locale | 1100 € | 39 €/mois | 20 | [voir](https://snooker4real.github.io/leadflow/home-comfort/) | [LF-2026-825493](devis/home-comfort.html) |
| 59 | Serrurerie Europe Clés | artisan | Lyon 2e | 0478420842 | Refonte site obsolète, Optimisation fiche locale | 1100 € | 39 €/mois | 20 | [voir](https://snooker4real.github.io/leadflow/serrurerie-europe-cles/) | [LF-2026-991303](devis/serrurerie-europe-cles.html) |
| 60 | La Maison du Tui Na | beauté | Lyon 2e | 0952840209 | Optimisation fiche locale | 200 € | 39 €/mois | 20 | aucune | [LF-2026-169786](devis/espace-tuina.html) |
| 61 | Épicure | restaurant | Lyon 6e | +33449130060 | Menu numérique | 170 € | 19 €/mois | 20 | [voir](https://snooker4real.github.io/leadflow/epicure/) | [LF-2026-477188](devis/epicure.html) |
| 62 | MamMam | restaurant | Lyon 2e | +33 4 78 82 63 21 | Refonte site obsolète | 900 € | 0 €/mois | 10 | [voir](https://snooker4real.github.io/leadflow/mammam/) | [LF-2026-110364](devis/mammam.html) |
| 63 | Alter Eben | artisan | Villeurbanne | 0478854710 | Optimisation fiche locale | 200 € | 39 €/mois | 10 | aucune | [LF-2026-952597](devis/alter-eben.html) |
| 64 | France Expert Énergie | artisan | Lyon 6e | 0985035584 | Optimisation fiche locale | 200 € | 39 €/mois | 10 | aucune | [LF-2026-793717](devis/france-expert-energie.html) |
| 65 | Glam | beauté | Lyon 9e | +33478403821 | Optimisation fiche locale | 200 € | 39 €/mois | 10 | aucune | [LF-2026-922058](devis/glam.html) |
| 66 | Balamani | beauté | Lyon 3e | +33 6 35 40 08 98 | Optimisation fiche locale | 200 € | 39 €/mois | 10 | aucune | [LF-2026-660158](devis/balamani.html) |
| 67 | L'Esprit Bistrot | restaurant | Lyon 8e | +33 4 78 74 38 42 | Optimisation fiche locale | 200 € | 39 €/mois | 10 | [voir](https://snooker4real.github.io/leadflow/l-esprit-bistrot/) | [LF-2026-733700](devis/l-esprit-bistrot.html) |
| 68 | Nachos | restaurant | Lyon 2e | +33481913772 | Optimisation fiche locale | 200 € | 39 €/mois | 10 | aucune | [LF-2026-109628](devis/nachos.html) |
| 69 | Établissement Richez | artisan | Lyon 7e | +33478985373 | Refonte site obsolète | 900 € | 0 €/mois | 10 | [voir](https://snooker4real.github.io/leadflow/etablissement-richez/) | [LF-2026-650575](devis/etablissement-richez.html) |
| 70 | Gena Multiservices Habitat | artisan | Lyon 8e | +33 4 26 72 24 96 | Optimisation fiche locale | 200 € | 39 €/mois | 10 | aucune | [LF-2026-717132](devis/gena-multiservices-habitat.html) |
| 71 | Antonio & Marco Caluire-et-Cuire | restaurant | Caluire-et-Cuire | +33 4 78 31 01 20 | Optimisation fiche locale | 200 € | 39 €/mois | 10 | aucune | [LF-2026-640591](devis/antonio-marco-caluire-et-cuire.html) |
| 72 | Samak | artisan | Villeurbanne | +334 78 68 04 60;+337 55 59 25 69 | Optimisation fiche locale | 200 € | 39 €/mois | 10 | aucune | [LF-2026-371155](devis/samak.html) |
<!-- prospects:end -->
