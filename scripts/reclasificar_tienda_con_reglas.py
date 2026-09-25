#!/usr/bin/env python3
"""Vuelve a pasar por el clasificador de HOY las fichas que solo venden
Walmart y Bodega Aurrerá, y propone mover las que hoy caerían en otra
categoría.

POR QUÉ (25-sep-2026)
---------------------
Esas 644 mil fichas entraron el 24-sep con el clasificador de ese día. Desde
entonces se corrigieron muchas reglas (departamentos de Walmart revisados a
mano, categorías nuevas, guardas de palabras sueltas), y el usuario vio
errores como pintura vinílica en Mascotas o tapones para dormir en Audífonos:
hoy la pintura va a Herramientas. Un bayesiano entrenado con las demás
tiendas no sirvió de juez (en esas tiendas casi no hay autopartes ni ropa y
proponía sacar de ahí lo que estaba bien).

Se usa el departamento de la tienda (de las capturas del feed), como en la
prueba del 25-sep sobre las fichas que se habían saltado. Se agrupa por
«Origen>Destino» con muestra; --aplicar mueve solo los grupos aprobados.
Lo corregido a mano no se toca.

USO
---
    python3 scripts/reclasificar_tienda_con_reglas.py --capturas a.json b.json --informe /tmp/r.json
    python3 scripts/reclasificar_tienda_con_reglas.py --capturas a.json b.json --aplicar --grupos "X>Y" ...
"""
import argparse
import collections
import io
import json
import multiprocessing as mp
import os
import random
import re
import sys
import urllib.parse

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import ROOT, load_catalog, save_catalog  # noqa: E402
import clasificar_captura_perifericos as C  # noqa: E402

TIENDAS = {"walmart_mx", "bodega_aurrera"}
RX_ID = re.compile(r"/(\d{6,16})(?:[/?#]|$)")


def id_de_url(url):
    u = urllib.parse.unquote(url or "")
    m = RX_ID.search(u.split("?dl=")[-1])
    return m.group(1) if m else None


def _decidir(args):
    pid, nombre, dept = args
    item = {"asin": pid, "title": nombre}
    if dept:
        item["dept"] = dept
    d = C.decidir(item)
    return pid, d.get("category"), d.get("subcategory")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--capturas", nargs="+", required=True)
    ap.add_argument("--informe")
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--grupos", nargs="*", default=[])
    ap.add_argument("--hilos", type=int, default=4)
    args = ap.parse_args()

    dept = {}
    for f in args.capturas:
        for it in json.load(io.open(f, encoding="utf-8")):
            if it.get("dept"):
                dept[str(it.get("id"))] = it["dept"]
    print(f"Departamentos: {len(dept):,}", flush=True)

    ruta = os.path.join(ROOT, "data", "clasificacion-a-mano.json")
    candado = json.load(io.open(ruta, encoding="utf-8")) if os.path.exists(ruta) else {}
    data = load_catalog()
    por_id = {}
    trabajo = []
    for p in data["products"]:
        ofs = p.get("offers") or []
        st = {o.get("storeId") or o.get("store") for o in ofs}
        if not st or not st <= TIENDAS or p["id"] in candado:
            continue
        dp = next((dept[i] for i in (id_de_url(o.get("url")) for o in ofs) if i and i in dept), None)
        por_id[p["id"]] = p
        trabajo.append((p["id"], p.get("name") or "", dp))
    print(f"Fichas a revisar: {len(trabajo):,} ({sum(1 for t in trabajo if t[2]):,} con departamento)", flush=True)

    grupos = collections.defaultdict(list)
    with mp.get_context("fork").Pool(args.hilos) as pool:
        for i, (pid, cat, sub) in enumerate(pool.imap_unordered(_decidir, trabajo, chunksize=500)):
            p = por_id[pid]
            if cat and sub and cat != p["category"]:
                grupos[f"{p['category']}>{cat}"].append((p, cat, sub))
            if i % 100000 == 0:
                print(f"  {i:,}", flush=True)

    resumen = {k: len(v) for k, v in sorted(grupos.items(), key=lambda kv: -len(kv[1]))}
    for k, n in list(resumen.items())[:80]:
        print(f"{n:7,}  {k}")
    print(f"Cambiarían de categoría: {sum(resumen.values()):,} en {len(resumen)} grupos")
    if args.informe:
        random.seed(25)
        muestra = {k: [(p["name"][:90], p.get("subcategory"), s) for p, _c, s in random.sample(v, min(20, len(v)))]
                   for k, v in grupos.items()}
        with io.open(args.informe, "w", encoding="utf-8") as f:
            json.dump({"resumen": resumen, "muestra": muestra}, f, ensure_ascii=False, indent=1)
    if args.aplicar:
        n = 0
        for g in args.grupos:
            for p, cat, sub in grupos.get(g, []):
                p["category"], p["subcategory"] = cat, sub
                n += 1
        save_catalog(data)
        print(f"Guardado: {n:,} fichas movidas en {len(args.grupos)} grupos.")


if __name__ == "__main__":
    main()
