#!/usr/bin/env python3
"""Pone al día los precios de las ofertas que vinieron de un feed de Soicos.

importar_captura_tienda.py sólo da de alta lo NUEVO: una oferta que ya está
en el catálogo no se toca aunque la tienda haya cambiado el precio. Esto
toma la captura fresca de soicos_a_captura.py y, para cada oferta de esa
tienda que ya está (misma url de la tienda dentro del deeplink), pone el
precio, el precio anterior y el stock de hoy.

Lo que el feed ya no trae (agotado o retirado) no se borra -- el producto
queda, con su historial --: se cuenta y se lista, para decidir aparte.

USO
---
    python3 scripts/soicos_a_captura.py --env <fuera del repo> --programa 11897 --tienda sams_mx --salida /tmp/sams.json
    python3 scripts/refrescar_soicos.py /tmp/sams.json --tienda sams_mx --dry-run
    python3 scripts/refrescar_soicos.py /tmp/sams.json --tienda sams_mx
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog, url_real  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("captura")
    ap.add_argument("--tienda", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    feed = {}
    for it in json.load(open(args.captura, encoding="utf-8")):
        if it.get("store") == args.tienda:
            feed[url_real(it["url"]) or it["url"]] = it
    data = load_catalog()
    cambian, iguales, ausentes = 0, 0, []
    for p in data["products"]:
        for o in p.get("offers") or []:
            if o.get("storeId") != args.tienda:
                continue
            it = feed.get(url_real(o.get("url")) or o.get("url"))
            if not it:
                ausentes.append((p["id"], p["name"]))
                continue
            nuevo = {"price": it["price"], "stock": "in_stock"}
            if it.get("listPrice") and it["listPrice"] > it["price"]:
                nuevo["listPrice"] = it["listPrice"]
            if all(o.get(k) == v for k, v in nuevo.items()) and ("listPrice" in nuevo or "listPrice" not in o):
                iguales += 1
                continue
            o.update(nuevo)
            if "listPrice" not in nuevo:
                o.pop("listPrice", None)
            # El deeplink del feed es el vigente (cambia si Soicos rehace el
            # enlace del programa).
            o["url"] = it["url"]
            cambian += 1
    print(f"ofertas de {args.tienda}: precio al día {iguales:,}; cambian {cambian:,}; ya no están en el feed {len(ausentes):,}")
    for pid, n in ausentes[:15]:
        print(f"  sin feed  {pid:>9}  {n[:70]}")
    if args.dry_run or not cambian:
        print("(--dry-run: no se guardó nada)" if args.dry_run else "nada que cambiar")
        return
    save_catalog(data)
    print("Guardado.")


if __name__ == "__main__":
    main()
