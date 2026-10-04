#!/usr/bin/env python3
"""La foto de la ficha, de la tienda que no la cambia de lugar (04-oct-2026).

Elektra y Chedraui (VTEX) vuelven a subir sus imágenes con otro id y la url
vieja da 404: medido el 04-oct, 29% de las fotos de Elektra de fichas viejas
y 15% de las de Chedraui, contra 0% de Mercado Libre, Coppel, Walmart y
AliExpress. La foto de la ficha sale de la oferta con la que se dio de alta,
así que una ficha que también vende Mercado Libre podía quedar «sin foto»
teniendo a mano una que no se rompe.

Para las fichas con la foto en una de esas tiendas y otra oferta con foto de
una tienda estable, la foto de la ficha pasa a ser la de la estable (la de
cada oferta no se toca). Las fichas con colores se dejan: cada color tiene
la suya. Corre en cada regeneración (idempotente).

USO
---
    python3 scripts/foto_estable.py --dry-run
    python3 scripts/foto_estable.py
"""
import argparse
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog  # noqa: E402

# Donde la url de una foto deja de existir cuando la tienda la vuelve a subir.
VOLATILES = {"elektra.vteximg.com.br", "chedrauimx.vteximg.com.br", "www.sephora.com.mx"}
# Las que no se rompieron en la medición, en este orden de preferencia.
ESTABLES = ("http2.mlstatic.com", "cdn5.coppel.com", "i5.walmartimages.com.mx", "i5.walmartimages.com",
            "ae-pic-a1.aliexpress-media.com")


def host(u):
    m = re.match(r"https?://([^/]+)/", u or "")
    return m.group(1) if m else ""


def foto_estable(p):
    for h in ESTABLES:
        for o in p.get("offers") or []:
            if o.get("photo") and host(o["photo"]) == h:
                return o["photo"]
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    data = load_catalog()
    est = collections.Counter()
    for p in data["products"]:
        h = host(p.get("photo"))
        if h not in VOLATILES or p.get("colorVariants"):
            continue
        nueva = foto_estable(p)
        if nueva:
            p["photo"] = nueva
            est[f"{h} -> {host(nueva)}"] += 1
    print(f"fotos de ficha cambiadas a una tienda estable: {sum(est.values()):,}")
    for k, v in est.most_common():
        print(f"   {v:7,}  {k}")
    if args.dry_run:
        print("(--dry-run: no se escribió nada)")
        return 0
    if est:
        save_catalog(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
