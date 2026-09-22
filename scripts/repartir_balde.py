#!/usr/bin/env python3
"""Vuelve a pasar el clasificador por un balde concreto del catálogo.

PARA QUÉ
--------
Cuando se parte un balde genérico en subcategorías nuevas —«Componentes» en
gabinetes, fuentes, procesadores, tarjetas y enfriamiento— la regla nueva sólo
alcanza a lo que entre a partir de ese día. Las fichas que ya estaban siguen
en el balde: nadie las vuelve a mirar.

Esto las vuelve a mirar. Arma una captura con las fichas de ese balde, la pasa
por el mismo clasificador que usan las importaciones, y escribe el JSON de
movimientos que lee aplicar_movimientos.py. Así la regla nueva se escribe una
sola vez y vale para lo viejo y para lo nuevo.

Se propone el movimiento sólo cuando el clasificador se decide; si contesta
que no sabe, la ficha se queda donde está.

USO
---
    python3 scripts/repartir_balde.py "Componentes y accesorios de PC" "Componentes" \
        --salida /tmp/mover_componentes.json
"""
import argparse
import collections
import io
import json
import os
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import load_catalog, url_real  # noqa: E402

CLASIFICADOR = os.path.join(AQUI, "clasificar_captura_perifericos.py")


def como_captura(p):
    o = (p.get("offers") or [{}])[0]
    return {"asin": p["id"], "title": p.get("name") or "",
            "price": o.get("price"), "photo": p.get("photo") or p.get("image") or "",
            "url": url_real(o.get("url", "")) or o.get("url", "")}


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("categoria")
    ap.add_argument("subcategoria", help="el balde; '' para las fichas sin subcategoría")
    ap.add_argument("--salida", required=True)
    ap.add_argument("--muestras", type=int, default=2)
    ap.add_argument("--misma-categoria", action="store_true",
                    help="descartar lo que el clasificador manda a otra categoría")
    args = ap.parse_args()

    data = load_catalog()
    balde = [p for p in data["products"]
             if p.get("category") == args.categoria
             and (p.get("subcategory") or "") == args.subcategoria]
    print(f"fichas en el balde: {len(balde):,}")
    if not balde:
        return 1

    tmp = tempfile.mkdtemp(prefix="balde-")
    entrada, salida = os.path.join(tmp, "in.json"), os.path.join(tmp, "out.json")
    with io.open(entrada, "w", encoding="utf-8") as f:
        json.dump([como_captura(p) for p in balde], f, ensure_ascii=False)
    r = subprocess.run([sys.executable, CLASIFICADOR, entrada, salida],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-2000:], file=sys.stderr)
        return 1
    with io.open(salida, encoding="utf-8") as f:
        nuevo = {a["asin"]: (a.get("category"), a.get("subcategory")) for a in json.load(f)}

    grupos, muestras = collections.defaultdict(list), collections.defaultdict(list)
    nombres = {p["id"]: p.get("name") or "" for p in balde}
    sin_opinion = 0
    for p in balde:
        cat2, sub2 = nuevo.get(p["id"], (None, None))
        if not cat2 or not sub2:
            sin_opinion += 1
            continue
        if args.misma_categoria and cat2 != args.categoria:
            continue
        if (cat2, sub2) == (p.get("category"), p.get("subcategory") or None):
            continue
        k = f"{args.categoria} | {args.subcategoria or None} | {cat2} | {sub2}"
        grupos[k].append(p["id"])
        if len(muestras[k]) < args.muestras:
            muestras[k].append(nombres[p["id"]][:74])

    for k, ids in sorted(grupos.items(), key=lambda kv: -len(kv[1])):
        print(f"  {len(ids):>5}  {k}")
        for m in muestras[k]:
            print(f"           {m}")
    print(f"\nse mueven {sum(len(v) for v in grupos.values()):,} en {len(grupos)} grupos; "
          f"el clasificador no se decide en {sin_opinion:,} y ésas se quedan.")
    with io.open(args.salida, "w", encoding="utf-8") as f:
        json.dump(grupos, f, ensure_ascii=False, indent=0)
    print(f"-> {args.salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
