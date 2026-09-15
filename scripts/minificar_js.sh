#!/bin/sh
# Genera js/app.min.js y js/firebase-init.min.js desde sus fuentes.
#
# POR QUÉ
# -------
# Las páginas cargan app.min.js, no app.js. El minificado se venía armando a
# mano y se quedó dos días atrás: app.js tenía cambios que el sitio no estaba
# sirviendo, y no había forma de notarlo salvo que algo dejara de funcionar.
# Es el mismo problema que tenía style.min.css (ver scripts/minificar_css.py).
#
# esbuild ya está en node_modules. No se hace bundle ni se transpila: app.js
# es un solo archivo y funciona tal cual en los navegadores que soporta el
# sitio; acá solo se acorta.
set -e
cd "$(dirname "$0")/.."
for f in app firebase-init; do
  ./node_modules/.bin/esbuild "js/$f.js" --minify --target=es2019 \
      --outfile="js/$f.min.js" --log-level=warning
  printf '%-22s %8s -> %8s bytes\n' "$f.min.js" \
      "$(wc -c < "js/$f.js")" "$(wc -c < "js/$f.min.js")"
done
