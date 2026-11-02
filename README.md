# Snooker4Real.github.io

Portfolio personnel, en PWA, avec la page de liens /links.

**Stack** : HTML / CSS / JS

## Fonctionnalités

- Portfolio avec manifest, service worker, sitemap, robots.txt
- Page de liens /links (sans collecte d'email ici)
- Dockerfile + nginx + deploy.sh pour un déploiement auto-hébergé

## Démarrage

```bash
python3 -m http.server 8000   # servir le site sur http://localhost:8000
```

## Docker

```bash
docker compose -f compose.yaml up --build
```

## Structure

```
assets/
links/
nginx/
Dockerfile
compose.yaml
deploy.sh
index.html
manifest.json
robots.txt
sitemap.xml
sw.js
```
