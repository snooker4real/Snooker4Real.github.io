#!/bin/sh
# Publie les maquettes : copie site/leadflow/ dans un clone de Snooker4Real.github.io (chemin en argument), sans les dossiers privés de page.
set -e
[ -n "$1" ] || { echo "usage: publish.sh <clone>" >&2; exit 1; }
dest="$1/leadflow"
rm -rf "$dest" && mkdir -p "$dest"
cp site/leadflow/index.html "$dest/"
for d in site/leadflow/*/; do
  [ -f "$d/index.html" ] && cp -R "$d" "$dest/$(basename "$d")"
done
find "$dest" -name ".DS_Store" -delete
echo "$(ls -d "$dest"/*/ | wc -l | tr -d ' ') maquettes copiées dans $dest"
