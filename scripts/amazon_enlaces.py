#!/usr/bin/env python3
"""Botón «Ver precio en Amazon» en toda ficha que sea el mismo producto que
una de Amazon, y ninguna foto de Amazon en el sitio (pedido del usuario,
26-sep-2026).

POR QUÉ
-------
Amazon quedó en «solo enlace» (tienda_solo_enlace.py): su precio no se
muestra y las 189 mil fichas que eran solo de Amazon salieron del catálogo
publicado (viven en data/tiendas-ocultas.json.gz). Muchas de ellas son el
mismo producto que otra tienda vende y que sí está en el sitio, pero nunca
se fusionaron. Acá se busca esa gemela con los mismos criterios de
merge_amazon_cross_store.py (código de modelo, marca, versión, medidas,
parecido de nombre, precio a menos de 2.5x, candidata única) y, en vez de
fusionar, a la ficha visible se le agrega el enlace de afiliado. La ficha
de Amazon sigue guardada tal cual.

Y las fotos: las políticas del Programa de Afiliados solo permiten mostrar
imágenes de Amazon obtenidas por su API o sus enlaces. Una ficha cuya foto
es de Amazon toma la de otra de sus ofertas; si no hay otra, se queda sin
foto (el sitio pone el ícono de la categoría).

USO
---
    python3 scripts/amazon_enlaces.py            # informe
    python3 scripts/amazon_enlaces.py --aplicar
"""
import argparse
import collections
import os
import random
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import merge_amazon_cross_store as M  # noqa: E402
import ocultar_tiendas as O  # noqa: E402
from data_io import load_catalog, save_catalog  # noqa: E402

AMAZON = "amazon_mx"
DOMINIOS_AMAZON = ("media-amazon.com", "images-amazon.com", "ssl-images-amazon.com")


def es_foto_amazon(url):
    return bool(url) and any(d in url for d in DOMINIOS_AMAZON)


def enlaces_nuevos(data):
    guardado = O.leer()
    ocultas = [p for p in guardado.get("productos", [])
               if {o.get("storeId") for o in p.get("offers") or []} == {AMAZON}]
    visibles = data["products"]
    grupos, motivos = M.resolver(visibles + ocultas, solo_amazon=True)
    ids_ocultas = {p["id"] for p in ocultas}
    por_id = {p["id"]: p for p in visibles}
    pares = []
    for g in grupos:
        amz = [p for p in g if p["id"] in ids_ocultas]
        vis = [p for p in g if p["id"] in por_id]
        if len(amz) != 1 or not vis:
            continue
        url = next((o.get("url") for o in amz[0].get("offers") or [] if o.get("url")), None)
        if url:
            pares.extend((por_id[v["id"]], amz[0], url) for v in vis)
    return pares, motivos, len(ocultas)


def cambiar_fotos(data):
    cambiadas = sin_foto = 0
    for p in data["products"]:
        if not es_foto_amazon(p.get("photo")):
            continue
        otra = next((o.get("photo") for o in p.get("offers") or []
                     if o.get("photo") and not es_foto_amazon(o["photo"])), None)
        if not otra:
            otra = next((v.get("photo") for v in p.get("colorVariants") or []
                         if v.get("photo") and not es_foto_amazon(v["photo"])), None)
        if otra:
            p["photo"] = otra
            cambiadas += 1
        else:
            p.pop("photo", None)
            sin_foto += 1
        for o in p.get("offers") or []:
            if es_foto_amazon(o.get("photo")):
                o.pop("photo", None)
    return cambiadas, sin_foto


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--muestra", type=int, default=40)
    args = ap.parse_args()
    data = load_catalog()
    pares, motivos, n_ocultas = enlaces_nuevos(data)
    ya = sum(1 for v, _, _ in pares if any(e.get("storeId") == AMAZON for e in v.get("enlaces") or []))
    print(f"fichas de Amazon guardadas: {n_ocultas:,}; con gemela visible: {len(pares):,} (ya enlazadas: {ya:,})")
    for m, n in motivos.most_common(6):
        print(f"  {n:8,}  {m}")
    random.seed(7)
    for v, a, _ in random.sample(pares, min(args.muestra, len(pares))):
        print(f"  VISIBLE {v['name'][:70]}\n   AMAZON {a['name'][:70]}")
    if not args.aplicar:
        return
    n = 0
    for v, _, url in pares:
        enl = v.setdefault("enlaces", [])
        if not any(e.get("storeId") == AMAZON for e in enl):
            enl.append({"storeId": AMAZON, "url": url})
            n += 1
    c, s = cambiar_fotos(data)
    save_catalog(data)
    print(f"Guardado: {n:,} botones nuevos de Amazon; fotos de Amazon cambiadas por otra tienda: {c:,}, "
          f"quitadas (sin otra foto): {s:,}")


if __name__ == "__main__":
    main()
