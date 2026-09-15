#!/usr/bin/env python3
"""Escribe data/search-index.json: palabra -> en qué categorías aparece.

POR QUÉ
-------
Buscar en el sitio obligaba a bajar el catálogo ENTERO. El listado carga por
categoría (data/cat/<slug>-N.json), pero una búsqueda puede caer en cualquiera,
así que ensureAllProducts() pedía los 53 shards de una vez: 91.7 MB en crudo,
17.5 MB con gzip. Con el catálogo en 200 mil fichas eso dejó de funcionar --
buscar "ninja" devolvía cero productos, no porque no hubiera (hay 332) sino
porque la carga no llegaba a término. Y como era un Promise.all, un solo shard
que fallara dejaba la lista vacía sin decir nada.

Este índice invierte el problema: dice de antemano qué categorías pueden tener
la palabra, y el navegador baja solo esas. "ninja" toca 8 de 53.

QUÉ GUARDA
----------
{"cats": ["Celulares", ...], "words": {"ninja": [3, 7, 12]}} -- la lista de
categorías y, por palabra, sus índices DENTRO DE ESA LISTA.

La lista va en el propio archivo a propósito. El primer intento guardaba solo
los índices y los resolvía contra data.categoryFiles del manifiesto: son 52
entradas, mientras que data.categories tiene 56 (las vacías no llegan a tener
shard). Los índices no coincidían y el resultado era mudo pero incorrecto --
"colchon restonic" resolvía a "Computadoras de escritorio" y "Aspiradoras".
Con la lista adentro, el archivo se interpreta solo y no puede desfasarse.

Solo palabras de 3 letras o más, del nombre y de la marca, normalizadas sin
acentos. No guarda ids de producto: eso volvería a ser un archivo del tamaño
del catálogo, y para decidir qué bajar no hace falta.

El filtrado fino lo sigue haciendo el navegador sobre los productos ya
bajados, con las mismas reglas de siempre (literalQueryMatch/fuzzyQueryMatch).
Este índice solo evita bajar de más; no decide qué se muestra.

USO
---
    python3 scripts/build_search_index.py
    python3 scripts/build_search_index.py --dry-run
"""
import argparse
import collections
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog  # noqa: E402

SALIDA = "data/search-index.json"
MIN_LARGO = 3


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]", " ", s)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = load_catalog()
    # Solo las categorías que de verdad tienen shard: son las únicas que el
    # navegador puede pedir, y es la lista que se guarda en el archivo.
    with open("data/data.json", encoding="utf-8") as f:
        manifiesto_previo = json.load(f)
    cats = [c for c in (manifiesto_previo.get("categoryFiles") or {})]
    if not cats:
        cats = [c["id"] for c in data["categories"]]
    idx = {c: i for i, c in enumerate(cats)}

    tokens = collections.defaultdict(set)
    for p in data["products"]:
        ci = idx.get(p.get("category"))
        if ci is None:
            continue
        palabras = set(norm(p.get("name")).split()) | set(norm(p.get("brand")).split())
        for w in palabras:
            if len(w) >= MIN_LARGO:
                tokens[w].add(ci)

    salida = {"cats": cats,
              "words": {w: sorted(v) for w, v in sorted(tokens.items())}}
    cuerpo = json.dumps(salida, separators=(",", ":"))
    print(f"categorías: {len(cats)}")
    print(f"palabras: {len(salida['words']):,}")
    print(f"tamaño:   {len(cuerpo) / 1e6:.2f} MB (sin comprimir)")
    ws = salida["words"]
    tocadas = sum(len(v) for v in ws.values()) / max(1, len(ws))
    print(f"categorías por palabra, promedio: {tocadas:.1f} de {len(cats)}")

    if args.dry_run:
        print("\n--dry-run: no se escribió nada")
        return
    with open(SALIDA, "w", encoding="utf-8") as f:
        f.write(cuerpo)
    print(f"\n{SALIDA} escrito.")

    # Se anuncia en el manifiesto para que el navegador sepa pedirlo; si el
    # archivo no está, app.js cae al comportamiento viejo (bajar todo).
    manifiesto = manifiesto_previo
    if manifiesto.get("searchIndexFile") != SALIDA:
        manifiesto["searchIndexFile"] = SALIDA
        with open("data/data.json", "w", encoding="utf-8") as f:
            json.dump(manifiesto, f, ensure_ascii=False)
        print("data/data.json: searchIndexFile anunciado")


if __name__ == "__main__":
    main()
