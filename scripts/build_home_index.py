#!/usr/bin/env python3
"""Escribe data/home-index.json: el índice que usan los dos buscadores de
la portada (categorías y marcas) para responder a un nombre de producto.

POR QUÉ
-------
El buscador de categorías casaba solo contra el nombre de la categoría y
sus subcategorías, así que "bosch" o "colchón inflable" no encontraban
nada. Reusar data/search-index.json no sirve: ese índice guarda PRESENCIA
(¿esta categoría puede tener la palabra?) porque su trabajo es decidir qué
shards bajar, y con eso "iphone" toca 29 de 54 categorías -- fundas,
cargadores y cables incluidos. Como filtro de portada eso es ruido.

Este índice guarda RELEVANCIA: por palabra, solo las categorías y las
marcas donde esa palabra pesa de verdad (al menos MIN_FICHAS fichas y al
menos UMBRAL del total de la palabra), ordenadas de más a menos.

QUÉ GUARDA
----------
{"cats": [...], "brands": [...],
 "w": {"taladro": {"c": [12, 3], "b": [4, 51, 9]}}}

"cats" repite el orden de data/search-index.json a propósito: el campo "k"
de data/marcas.json (las categorías donde vende cada marca) numera sobre
esa misma lista, y si las dos se desfasan el resultado es mudo pero
incorrecto.

USO
---
    python3 scripts/build_home_index.py [--dry-run]
"""
import argparse
import collections
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import load_catalog  # noqa: E402

ROOT = os.path.dirname(AQUI)
SALIDA = "data/home-index.json"

MIN_FICHAS = 10       # una palabra con menos fichas no merece entrada propia
MIN_EN_GRUPO = 3      # ni una categoría/marca con menos fichas de esa palabra
UMBRAL = 0.08         # ...ni con menos del 8% de las fichas de la palabra
MAX_CATS = 8
MAX_MARCAS = 10

_RX = re.compile(r"[^a-z0-9]+")


def palabras(texto):
    t = (texto or "").lower()
    t = t.translate(str.maketrans("áéíóúñü", "aeiounu"))
    return {w for w in _RX.split(t) if len(w) >= 3}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = load_catalog()
    try:
        with open(os.path.join(ROOT, "data", "search-index.json"), encoding="utf-8") as f:
            cats = json.load(f).get("cats") or []
    except (OSError, ValueError):
        cats = []
    if not cats:
        sys.exit("falta data/search-index.json: córrelo antes (build_search_index.py)")
    pos_cat = {c: i for i, c in enumerate(cats)}

    marcas = [m["n"] for m in json.load(
        open(os.path.join(ROOT, "data", "marcas.json"), encoding="utf-8"))]
    pos_marca = {m.lower(): i for i, m in enumerate(marcas)}

    por_cat = collections.defaultdict(collections.Counter)
    por_marca = collections.defaultdict(collections.Counter)
    total = collections.Counter()
    for p in data["products"]:
        ic = pos_cat.get(p.get("category"))
        im = pos_marca.get((p.get("brand") or "").lower())
        if ic is None and im is None:
            continue
        for w in palabras(p.get("name")):
            total[w] += 1
            if ic is not None:
                por_cat[w][ic] += 1
            if im is not None:
                por_marca[w][im] += 1

    def recortar(cuenta, n, techo, cuota=True):
        # La cuota (8% de las fichas de la palabra) separa la categoría que
        # de verdad tiene el producto de la que solo lo nombra de pasada.
        # Con las marcas no sirve: "taladro" lo venden cincuenta marcas y
        # ninguna llega al 8%, así que ahí basta con tener fichas.
        corte = max(MIN_EN_GRUPO, int(n * UMBRAL)) if cuota else MIN_EN_GRUPO
        return [i for i, c in cuenta.most_common(techo) if c >= corte]

    w = {}
    for palabra, n in total.items():
        if n < MIN_FICHAS:
            continue
        c = recortar(por_cat.get(palabra) or collections.Counter(), n, MAX_CATS)
        b = recortar(por_marca.get(palabra) or collections.Counter(), n, MAX_MARCAS, cuota=False)
        if not c and not b:
            continue
        ent = {}
        if c:
            ent["c"] = c
        if b:
            ent["b"] = b
        w[palabra] = ent

    cuerpo = json.dumps({"cats": cats, "brands": marcas, "w": w},
                        ensure_ascii=False, separators=(",", ":"))
    print(f"palabras: {len(w):,} de {len(total):,}   tamaño: {len(cuerpo) / 1024:.0f} KB")
    for q in ("iphone", "taladro", "colchon", "bosch", "shimano"):
        e = w.get(q) or {}
        print(f"  {q}: cats={[cats[i] for i in e.get('c', [])][:5]}"
              f" marcas={[marcas[i] for i in e.get('b', [])][:5]}")
    if args.dry_run:
        print("\n--dry-run: no se escribió nada")
        return
    with open(os.path.join(ROOT, SALIDA), "w", encoding="utf-8") as f:
        f.write(cuerpo)
    print(f"\n{SALIDA} escrito.")


if __name__ == "__main__":
    main()
