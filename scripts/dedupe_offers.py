#!/usr/bin/env python3
"""Quita ofertas duplicadas dentro de un mismo producto.

De dónde salen: los scripts de fusión (merge_cross_store, merge_by_signature,
merge_monitor_duplicates, merge_bundle_offers) juntan varias publicaciones en
un solo producto y le pegan la oferta de cada una. Cuando una tienda publica
el mismo artículo N veces --Elektra lo hace con las autopartes, una
publicación por año/modelo compatible-- el producto fusionado termina con N
ofertas idénticas que solo se distinguen por el `ean` (el código de barras
interno de esa publicación, que el navegador nunca lee).

El efecto era visible: "Antena Tiburón Fm/am Estéreo Acura Cl 2003-2013"
tenía 2,161 ofertas iguales, la ficha decía "en 2,161 vendedores" y ese
producto solo ocupaba 164 KB de los 600 KB de data/home.json.

Criterio de igualdad: todos los campos salvo `url` y `ean`, es decir misma
tienda, mismo precio, mismo precio de lista, mismo stock, mismo envío y mismos
vendedores. Dos ofertas que difieran en cualquiera de esos NO se tocan. Se
conserva la primera aparición completa (con su url y su ean), así que el
enlace sigue funcionando y match_by_gtin.py conserva un código por tienda.

Se comprobó antes de aplicarlo que el 99.8% de lo que quita es de Elektra
(3,219 de 3,224 ofertas; el resto: sharkninja 3, amazon_mx 2) y que NO toca
ninguna oferta de Mercado Libre, donde varias publicaciones al mismo precio sí
pueden ser vendedores distintos.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog

DRY_RUN = "--dry-run" in sys.argv


# `url` y `ean` identifican la PUBLICACIÓN, no la oferta: dos publicaciones de
# la misma tienda al mismo precio son, para quien compra, la misma oferta.
CAMPOS_DE_PUBLICACION = ("url", "ean")


def _clave(oferta):
    return json.dumps(
        {k: v for k, v in oferta.items() if k not in CAMPOS_DE_PUBLICACION},
        sort_keys=True, ensure_ascii=False, default=str,
    )


def dedupe(offers):
    """Devuelve la lista sin duplicados, conservando el orden original.

    Si la que se conserva no traía `ean` y una de las descartadas sí, se le
    pasa ese código: es el único dato de la publicación descartada que sirve
    para algo (match_by_gtin.py) y perderlo sería perder un cruce entre
    tiendas.
    """
    vistas, salida = {}, []
    for o in offers:
        k = _clave(o)
        if k in vistas:
            quedo = vistas[k]
            if not quedo.get("ean") and o.get("ean"):
                quedo["ean"] = o["ean"]
            continue
        vistas[k] = o
        salida.append(o)
    return salida


def main():
    data = load_catalog()
    productos = data["products"]

    quitadas, tocados, peores = 0, 0, []
    for p in productos:
        offers = p.get("offers") or []
        if len(offers) < 2:
            continue
        limpias = dedupe(offers)
        if len(limpias) == len(offers):
            continue
        tocados += 1
        quitadas += len(offers) - len(limpias)
        peores.append((len(offers) - len(limpias), len(offers), len(limpias), p.get("name", "")))
        p["offers"] = limpias

    peores.sort(reverse=True)
    print(f"Productos con ofertas duplicadas: {tocados:,}")
    print(f"Ofertas eliminadas: {quitadas:,}")
    for n, antes, despues, nombre in peores[:10]:
        print(f"   -{n:6,}  ({antes} -> {despues})  {nombre[:60]}")
    if len(peores) > 10:
        print(f"   ... y {len(peores) - 10:,} productos más")

    if DRY_RUN:
        print("\n(--dry-run: no se escribió nada)")
        return
    data["products"] = productos
    save_catalog(data)
    print("\nGuardado.")


if __name__ == "__main__":
    main()
