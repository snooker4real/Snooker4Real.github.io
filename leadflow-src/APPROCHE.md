# Approche commerciale LEADFLOW — 72 prospects lyonnais

Ce document dit dans quel ordre contacter les prospects, quoi leur dire et quelle formule pousser. Les devis sont dans `devis/index.html`, les maquettes sur `https://snooker4real.github.io/leadflow/<slug>/`.

## L'idée en une phrase

Tu n'arrives pas avec une offre, tu arrives avec le travail déjà fait : « J'ai préparé votre site, regardez-le sur mon téléphone. » La maquette remplace l'argumentaire.

## Avant le premier contact

1. **La liste est déjà recoupée avec Google Maps.** Sur 100 commerces repérés, 28 sont sortis : 9 fermés, 6 qui ont déjà un bon site, 6 introuvables (ni fiche Google ni SIREN), 2 franchises, 2 dont la fiche Google ne correspondait pas, 2 restaurants universitaires et 1 restaurant dont le site interdit le démarchage. Un seul prospect reste sans fiche Google (Asia Bti, confirmé par SIRENE) : sa fiche est à créer, c'est l'offre.
2. **Vérifie ton en-tête de devis** dans `render.py` (`ISSUER`). Il est prérempli avec CATCHEE GROUP (SIRET 994 785 871 00017) ; téléphone et e-mail sont renseignés, la mention « TVA non applicable » correspond à la franchise en base. Relance ensuite `python3 deliver.py build`.
3. **Relis la maquette avant de la montrer.** Les prestations listées pour les artisans et les salons sont des prestations types du métier, pas les leurs. Corrige ce que tu sais faux.
4. **Prépare ta réponse sur les photos.** Presque toutes les maquettes reprennent des photos de la fiche Google Maps, et parfois le logo, la police ou les textes du site de l'établissement. Certaines photos Maps ont été prises par des clients, et on y reconnaît parfois des personnes. C'est tolérable pour une démonstration non référencée montrée au propriétaire. Avant toute mise en ligne réelle, il te faut son accord écrit et ses propres photos (c'est une clause du devis).
5. **Regarde chaque maquette avant de la montrer.** Les photos sont choisies automatiquement : retire celle qui montre un concurrent, une publicité ou un client reconnaissable.

## Par qui commencer

Trie `devis/index.html` et le dashboard par score, puis applique ce filtre :

| Priorité | Critère | Pourquoi |
|---|---|---|
| 1 | Score ≥ 60, téléphone et SIREN connus | Besoin net, entreprise vérifiée, joignable |
| 2 | Site injoignable ou copyright ancien | Le propriétaire a déjà payé un site : il sait ce que ça vaut |
| 3 | Restaurant avec menu en PDF | Petit ticket (170 €), décision rapide, porte d'entrée pour le reste |
| 4 | Aucun site, pas de téléphone | Passage physique uniquement |

Vise 10 contacts par jour. Au-delà, tu ne personnalises plus.

## Le canal selon le métier

- **Restaurants** : passe sur place entre 15 h et 17 h, jamais pendant un service. Demande le gérant par son nom (il figure sur le devis quand SIRENE le donne).
- **Coiffeurs, barbiers, instituts** : passe le mardi ou le mercredi matin, les créneaux creux. Le samedi est perdu d'avance.
- **Artisans** : appelle entre 7 h 30 et 8 h 30 ou entre 12 h et 13 h 30, puis envoie le lien par SMS. Ils ne sont jamais au local.

Le démarchage téléphonique et par e-mail entre professionnels est autorisé si le message concerne leur activité, que tu t'identifies et que tu proposes de ne plus être recontacté. Tiens une liste des refus et respecte-la. Fais valider ce point par ta CCI ou un juriste avant d'automatiser quoi que ce soit.

## La séquence

| Jour | Action | Message |
|---|---|---|
| J0 | Passage ou appel, maquette en main | Script ci-dessous |
| J0 + 1 h | SMS avec le lien de la maquette | « Bonjour M. X, voici le site dont on a parlé : [lien]. Jonathan, LEADFLOW » |
| J+2 | Envoi du devis en PDF | « Trois façons de régler, la moins chère est en colonne 3. » |
| J+7 | Relance unique par téléphone | « Je libère la maquette vendredi, vous voulez qu'on la garde ? » |
| J+14 | Clôture | « Je retire la maquette. Si le sujet revient, vous avez mon numéro. » |

Retire vraiment la maquette après la clôture, ou sur simple demande. Un commerçant qui découvre son nom sur un site qu'il n'a pas demandé doit pouvoir le faire disparaître dans la journée.

## Le script (30 secondes)

> « Bonjour, Jonathan, je suis développeur à Lyon. En cherchant un [plombier / restaurant / coiffeur] dans le quartier, je n'ai pas trouvé votre site, alors je vous en ai préparé un. Je peux vous le montrer ? Ça prend une minute. »

Puis tais-toi et tends le téléphone. Trois règles :

- **Cite le constat précis** du devis : « votre site ne répond plus », « votre carte est un PDF illisible sur mobile ». Jamais « votre présence en ligne est perfectible ».
- **Ne parle pas de prix avant qu'il le demande.** Quand il demande, donne le mensuel de l'abonnement, pas le total.
- **Sors avec une suite datée** : « je repasse jeudi à 15 h avec le devis », pas « je vous laisse réfléchir ».

## Quelle formule pousser

Chaque devis propose les trois. Exemple pour un site vitrine avec fiche Google (800 € + 68 €/mois) :

| Formule | Le client paie | Sur 24 mois | Pour toi |
|---|---|---|---|
| 1. Comptant | 800 € puis 68 €/mois, sans engagement | 2 432 € | Trésorerie immédiate, récurrent fragile |
| 2. Abonnement | 107 €/mois, engagement 24 mois | 2 568 € | Aucun frein à la signature, tu avances le travail |
| 3. Annuel | 720 € + 680 € à la commande | 2 080 € | Le plus de cash d'un coup, 14 % de remise |

- **Présente l'abonnement par défaut.** « 107 € par mois, rien à sortir aujourd'hui » se décide sur place. C'est aussi la formule qui te rapporte le plus.
- **Garde l'annuel pour celui qui dit « c'est cher par mois ».** Il a de la trésorerie : montre-lui qu'il économise 488 €.
- **Le comptant sert d'ancre** et rassure ceux qui refusent tout engagement.

Limite à connaître : avec l'abonnement tu travailles avant d'être payé. Fais signer une autorisation de prélèvement et plafonne-toi à 5 abonnements en cours de production.

## Les objections

| Il dit | Tu réponds |
|---|---|
| « J'ai déjà Facebook / Instagram » | « Vos clients vous y suivent. Ceux qui ne vous connaissent pas cherchent sur Google, et là vous n'apparaissez pas. » |
| « Je travaille au bouche-à-oreille » | « Justement : la personne à qui on vous recommande vous cherche sur Google avant d'appeler. » |
| « Mon neveu va me le faire » | « Très bien. Je vous laisse la maquette comme modèle. Je repasse dans un mois voir où il en est ? » |
| « C'est trop cher » | « Un client de plus par mois le rembourse. Combien vaut un client chez vous ? » |
| « Je n'ai pas le temps » | « Il est déjà fait. Il me faut dix minutes pour valider les textes et vos horaires. » |

## Ce que tu peux espérer

Le dashboard affiche 54 470 € d'installations et 4 033 €/mois si les 72 signaient tout. Personne n'obtient ça. Hypothèse de travail, à corriger après tes 20 premiers contacts : 72 contacts donnent 20 conversations, 7 devis remis et 2 à 4 signatures, soit environ 1 500 à 3 000 € d'installations et 120 à 230 €/mois de récurrent. Ce sont des estimations, pas des mesures.

Note tes résultats réels par canal et par métier dès la première semaine. Le segment qui signe le mieux devient ta seule cible le mois suivant.

## Tes coûts à ne pas oublier

- **Réservation en ligne** : la licence de l'outil (Planity, Zenchef, Calendly…) est à ta charge dans le mensuel de 39 €. Vérifie le tarif de l'outil avant de signer, sinon tu vends à perte.
- **Nom de domaine et hébergement** : environ 15 € par an et par client pour le domaine. GitHub Pages sert aux maquettes, pas aux sites livrés.
- **Fiche Google** : il faut l'accès du propriétaire. Prévois de le faire avec lui, sur son téléphone, le jour de la signature.
- **Assurance et statut** : responsabilité civile professionnelle et conditions générales de vente avant la première facture.
