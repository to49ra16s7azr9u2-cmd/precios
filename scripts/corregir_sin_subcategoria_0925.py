#!/usr/bin/env python3
"""Mueve de categoría las fichas sin subcategoría cuya categoría está mal
(revisión del 25-sep-2026, después de que el usuario vio errores en lo
importado de Walmart y Mercado Libre).

Las fichas que ningún repartidor pudo meter en una subcategoría eran en
buena parte de OTRA categoría, puestas ahí por una palabra suelta:
«Gato de patín 3 ton» (un gato de auto) y «Libro el gato que enseña el zen»
en Mascotas, «Bocina claxon para ...» sin subcategoría en Autos. Solo se
aplican los movimientos revisados con muestra (10 de 10 en cada uno):

  - gatos mecánicos/hidráulicos -> Autos, bicicletas y motos / Accesorios y refacciones
  - bocinas claxon -> Autopartes, por la pieza (reglas_nuevas.sub_autoparte)
  - libros (reglas_nuevas los reconoce por editorial, tapa, ISBN) -> Libros
  - power banks en Cargadores -> Baterías portátiles

Solo toca fichas SIN subcategoría y no toca lo corregido a mano.

USO
---
    python3 scripts/corregir_sin_subcategoria_0925.py [--aplicar]
"""
import argparse
import collections
import io
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import ROOT, load_catalog, save_catalog  # noqa: E402
import clasificar_captura_perifericos as C  # noqa: E402
import reglas_nuevas  # noqa: E402

RX_GATO = re.compile(r'^(\S+ ){0,1}gatos? (de patin|patin|hidraulicos?|hidroneumaticos?|mecanicos?|de botella|tijera|'
                     r'para remolque|de carretilla|de piso|electrico)\b')


def destino(p, tn):
    if RX_GATO.search(tn):
        return 'Autos, bicicletas y motos', 'Accesorios y refacciones'
    if re.match(r'(bocinas? )?claxon', tn):
        return 'Autopartes', reglas_nuevas.sub_autoparte(tn) or 'Sistema eléctrico y sensores'
    nc = reglas_nuevas.nueva_categoria(tn, C.sub_refaccion, C.sub_libro_fino)
    if nc and nc[0] == 'Libros' and nc[1]:
        return 'Libros', nc[1]
    if p['category'] == 'Cargadores y adaptadores' and re.search(r'\bpower ?banks?\b|\bbateria portatil\b', tn):
        d = C.decidir({'asin': p['id'], 'title': p['name']})
        if d.get('category') == 'Baterías portátiles' and d.get('subcategory'):
            return 'Baterías portátiles', d['subcategory']
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()
    ruta = os.path.join(ROOT, "data", "clasificacion-a-mano.json")
    candado = json.load(io.open(ruta, encoding="utf-8")) if os.path.exists(ruta) else {}
    data = load_catalog()
    movidas = collections.Counter()
    for p in data["products"]:
        if p.get("subcategory") or p["id"] in candado:
            continue
        d = destino(p, C.T(p.get("name") or ""))
        if d and d[0] != p["category"] or (d and d[1] != p.get("subcategory")):
            movidas[(p["category"], d[0], d[1])] += 1
            p["category"], p["subcategory"] = d
    for k, n in movidas.most_common(30):
        print(f"{n:7,}  {k[0]} -> {k[1]} / {k[2]}")
    print(f"Total: {sum(movidas.values()):,}")
    if args.aplicar:
        save_catalog(data)
        print("Guardado.")


if __name__ == "__main__":
    main()
