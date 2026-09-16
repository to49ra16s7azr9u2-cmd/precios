#!/usr/bin/env python3
"""Quita de data.json las subcategorías comodín que quedaron vacías.

"Otros", "Varios", "Otros juegos" no nombran un producto: nadie busca
"otros muebles", no tienen página de SEO propia que valga la pena y en el
paso 2 del sitio ("¿qué tipo buscas?") ocupan un lugar sin decir nada.

Este script NO mueve fichas -- de eso se encarga
repartir_sin_subcategoria.py. Solo borra del manifiesto las entradas que ya
no tienen ninguna ficha, para que no sigan apareciendo en el nav y en los
filtros. Una subcategoría comodín que TODAVÍA tiene fichas no se toca y se
informa: borrarla dejaría a esas fichas apuntando a algo que no existe.
"""
import argparse
import collections
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import load_catalog  # noqa: E402

COMODIN = {"Otros", "Varios", "Otro", "Otros juegos", "Otro calzado"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    data = load_catalog()
    uso = collections.Counter((p["category"], p.get("subcategory")) for p in data["products"])
    ruta = os.path.join(AQUI, "..", "data", "data.json")
    manifiesto = json.load(open(ruta, encoding="utf-8"))

    quitadas, con_fichas = [], []
    for cat in manifiesto["categories"]:
        subs = cat.get("subcategories") or []
        quedan = []
        for s in subs:
            if s["id"] in COMODIN:
                n = uso[(cat["id"], s["id"])]
                if n == 0:
                    quitadas.append(f"{cat['id']} / {s['id']}")
                    continue
                con_fichas.append((f"{cat['id']} / {s['id']}", n))
            quedan.append(s)
        cat["subcategories"] = quedan

    print(f"Subcategorías comodín vacías que se quitan: {len(quitadas)}")
    for q in quitadas:
        print(f"  - {q}")
    if con_fichas:
        print(f"\nTodavía con fichas (no se tocan): {len(con_fichas)}")
        for q, n in sorted(con_fichas, key=lambda x: -x[1]):
            print(f"  {n:6,}  {q}")
    if args.aplicar and quitadas:
        json.dump(manifiesto, open(ruta, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("\ndata.json actualizado.")
    elif not args.aplicar:
        print("\n(sin --aplicar no se escribió nada)")


if __name__ == "__main__":
    main()
