#!/bin/sh
# Publie dans un clone de Snooker4Real.github.io (chemin en argument) : les maquettes (dossiers avec une page) et le code versionné, tous dans leadflow/.
set -e
[ -n "$1" ] || { echo "usage: publish.sh <clone>" >&2; exit 1; }
dest="$1/leadflow"
mkdir -p "$dest"
for d in "$dest"/*/; do  # maquette retirée en local : retirée en ligne ; seuls les dossiers avec une page sont concernés
  [ -f "$d/index.html" ] && [ ! -f "site/leadflow/$(basename "$d")/index.html" ] && rm -rf "$d"
done
cp site/leadflow/index.html "$dest/"
for d in site/leadflow/*/; do
  [ -f "$d/index.html" ] && rm -rf "$dest/$(basename "$d")" && cp -R "$d" "$dest/$(basename "$d")"
done
git archive HEAD | tar -x -C "$dest"
find "$dest" -name ".DS_Store" -delete
echo "$(ls "$dest"/*/index.html | wc -l | tr -d ' ') maquettes dans $dest"
