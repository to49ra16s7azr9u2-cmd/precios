#!/usr/bin/env python3
"""Envuelve en su enlace de afiliado las ofertas que ya están guardadas.

POR QUÉ
-------
Los enlaces de afiliado se aplican al importar, así que las tiendas que se
dieron de alta antes de tener programa quedaron con la url pelada de la tienda.
Cuando el programa se aprueba semanas después, esos productos siguen sin
monetizar y reimportar la tienda entera para conseguirlo es caro y arriesgado:
se perderían precios, agrupaciones y el historial.

Esto hace lo único que hace falta: reescribir la url de esas ofertas. No toca
precio, ni foto, ni stock, ni el id del producto.

CUÁNDO SE USA
-------------
Cada vez que se aprueba un programa nuevo. Se agrega el enlace en
afiliados.py y se corre esto con el storeId.

QUÉ RESPETA
-----------
Una oferta que YA tiene enlace de afiliado no se vuelve a envolver: envolver
dos veces rompe el enlace (el ulp= de adentro se escapa dentro del de afuera)
y manda al comprador a una página de error. Por eso se detecta el ulp= previo
y esas ofertas se saltan. Es idempotente: correrlo dos veces no cambia nada la
segunda.

USO
---
    python3 scripts/aplicar_afiliados.py --tienda sharkninja --dry-run
    python3 scripts/aplicar_afiliados.py --tienda sharkninja
    python3 scripts/aplicar_afiliados.py --todas
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from afiliados import BASES, TAG_AMAZON, base_de  # noqa: E402
from data_io import load_catalog, save_catalog, url_afiliado, url_real  # noqa: E402

# Mercado Libre no tiene un enlace base que envuelva cualquier url: cada
# producto lleva el suyo, generado a mano en el panel y emparejado por
# ml_enlaces.py. Por eso esa tienda se resuelve con un mapa, no con url_afiliado.
MAPAS = {"mercadolibre": "data/ml-afiliados.json"}
# Amazon no envuelve la url: le agrega el tag de Associates como parámetro.
# add_amazon_offers.py y add_amazon_standalone.py ya lo ponen al importar,
# pero 1,821 ofertas de los primeros lotes quedaron con el /dp/ASIN/ pelado
# (medido el 15 de septiembre de 2026) y ni el sitio ni este script las
# tocaban: cada clic ahí se iba sin comisión.
AMAZON = "amazon_mx"


def con_tag_amazon(url):
    if "tag=" in url:
        return url
    return url + ("&" if "?" in url else "?") + "tag=" + TAG_AMAZON


def cargar_mapa(store_id):
    ruta = MAPAS.get(store_id)
    if not ruta or not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tienda", action="append", default=[],
                    help="storeId a envolver (se puede repetir)")
    ap.add_argument("--todas", action="store_true",
                    help="todas las tiendas que tengan enlace en afiliados.py")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    objetivo = list(args.tienda)
    if args.todas:
        objetivo = [s for s, b in BASES.items() if b] + list(MAPAS) + [AMAZON]
    if not objetivo:
        ap.error("se necesita --tienda o --todas")

    sin_enlace = [s for s in objetivo if s != AMAZON and not base_de(s) and not cargar_mapa(s)]
    if sin_enlace:
        print("sin enlace en afiliados.py, se ignoran:", ", ".join(sin_enlace))
        objetivo = [s for s in objetivo if s == AMAZON or base_de(s) or cargar_mapa(s)]

    data = load_catalog()
    mapas = {s: cargar_mapa(s) for s in objetivo}
    envueltas = {s: 0 for s in objetivo}
    ya_tenian = {s: 0 for s in objetivo}
    sin_enlace_propio = {s: 0 for s in objetivo}

    for p in data["products"]:
        for o in (p.get("offers") or []):
            sid = o.get("storeId")
            if sid not in envueltas or not o.get("url"):
                continue
            if sid == AMAZON:
                nueva = con_tag_amazon(o["url"])
                if nueva == o["url"]:
                    ya_tenian[sid] += 1
                else:
                    o["url"] = nueva
                    envueltas[sid] += 1
                continue
            if url_real(o["url"]) or "/social/" in o["url"]:   # ya venía envuelta
                ya_tenian[sid] += 1
                continue
            mapa = mapas.get(sid)
            if mapa is not None:
                enlace = mapa.get(o["url"])
                if not enlace:
                    # Producto sin enlace generado todavía: se deja la url de la
                    # tienda. Media ficha monetizada es mejor que una rota.
                    sin_enlace_propio[sid] += 1
                    continue
                o["url"] = enlace
            else:
                o["url"] = url_afiliado(base_de(sid), o["url"])
            envueltas[sid] += 1

    total = sum(envueltas.values())
    for s in objetivo:
        extra = (f"   sin enlace propio {sin_enlace_propio[s]:6,}"
                 if mapas.get(s) is not None else "")
        print(f"  {s:24} envueltas {envueltas[s]:6,}   ya tenían {ya_tenian[s]:6,}{extra}")
    print(f"\nofertas modificadas: {total:,}")

    if args.dry_run:
        print("--dry-run: no se escribió nada")
        return
    if not total:
        print("nada que cambiar")
        return
    save_catalog(data)
    print("Guardado.")


if __name__ == "__main__":
    main()
