#!/usr/bin/env python3
"""Pasa a las categorías nuevas del 25-sep las fichas que YA estaban en otra.

reaplicar_reglas.py no sirve para esto: su veto bayesiano se entrena con el
catálogo de hoy, donde Calzado, Libros o Bolsas casi no tienen fichas, así
que vetaría justamente estas mudanzas (el catálogo «prefiere» Deportes para
unos tenis porque ahí están todos los tenis mal puestos).

Qué hace: pasa el nombre de cada ficha por reglas_nuevas.nueva_categoria()
(las reglas inconfundibles por primera palabra) y agrupa lo que cambiaría de
categoría por (origen -> destino). Con --informe escribe una muestra de cada
grupo para revisarla a mano; con --aplicar mueve SOLO los grupos listados en
--grupos (revisados, con 80%+ de aciertos en la muestra). Lo movido a mano
(data/clasificacion-a-mano.json) no se toca.

USO
---
    python3 scripts/migrar_por_reglas_nuevas.py --informe /tmp/grupos.json
    python3 scripts/migrar_por_reglas_nuevas.py --aplicar --grupos "Deportes y fitness>Calzado" ...
"""
import argparse
import collections
import io
import json
import os
import random
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)

from data_io import load_catalog, save_catalog  # noqa: E402
import reglas_nuevas  # noqa: E402
from reorganizar_categorias import destino  # noqa: E402
import clasificar_captura_perifericos as C  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--informe")
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--grupos", nargs="*", default=[], help='"Origen>Destino" aprobados')
    args = ap.parse_args()

    candado = {}
    ruta = os.path.join(ROOT, "data", "clasificacion-a-mano.json")
    if os.path.exists(ruta):
        with io.open(ruta, encoding="utf-8") as f:
            candado = json.load(f)

    data = load_catalog()
    grupos = collections.defaultdict(list)
    for p in data["products"]:
        if p["id"] in candado:
            continue
        tn = C.T(p.get("name") or "")
        nc = reglas_nuevas.nueva_categoria(tn, C.sub_refaccion, C.sub_libro_fino)
        if not nc:
            continue
        cat, sub = destino(nc[0], nc[1])
        actual = destino(p.get("category"), p.get("subcategory"))[0]
        if cat == actual:
            continue
        grupos[f"{actual}>{cat}"].append((p, cat, sub))

    random.seed(25)
    resumen = {k: len(v) for k, v in sorted(grupos.items(), key=lambda kv: -len(kv[1]))}
    for k, n in list(resumen.items())[:60]:
        print(f"{n:8,}  {k}")
    print(f"Total que cambiaría: {sum(resumen.values()):,} en {len(resumen)} grupos")
    if args.informe:
        muestra = {k: [(p["name"][:90], sub) for p, _c, sub in random.sample(v, min(25, len(v)))]
                   for k, v in grupos.items()}
        with io.open(args.informe, "w", encoding="utf-8") as f:
            json.dump({"resumen": resumen, "muestra": muestra}, f, ensure_ascii=False, indent=1)
        print(f"Muestra en {args.informe}")
    if not args.aplicar:
        return
    movidas = 0
    for g in args.grupos:
        for p, cat, sub in grupos.get(g, []):
            p["category"], p["subcategory"] = cat, sub
            movidas += 1
    save_catalog(data)
    print(f"Guardado: {movidas:,} fichas movidas en {len(args.grupos)} grupos.")


if __name__ == "__main__":
    main()
