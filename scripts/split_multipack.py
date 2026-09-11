#!/usr/bin/env python3
"""Separa fichas donde un PAQUETE y la PIEZA SUELTA quedaron como un mismo
producto.

EL PROBLEMA
-----------
Un comparador de precios solo tiene sentido si las dos filas de la tabla se
pueden comparar. Cuando una fila es un paquete de 50 y la otra una pieza,
la comparación no es una diferencia de precio entre tiendas: es una
diferencia de unidad, y el sitio la presenta como si fuera una ganga.

Los dos casos del catálogo, encontrados buscando fichas cuyo nombre declara
un paquete ("50PZ", "KIT 10 piezas") y cuyas ofertas difieren 4x o más:

    Disco de corte Makita D-71685        Elektra $929 (50 piezas)
                                         Mercado Libre $35 (una pieza)   26x
    Memoria microSD ADATA 64GB           Elektra $1,777 (kit de 10)
                                         Mercado Libre $233 (una pieza)
                                         Elektra $289 (una pieza)         7.6x

En el primero la ficha decía "desde $35" sobre un paquete de $929. En el
segundo, "desde $233" sobre un kit de $1,777.

CÓMO LLEGARON A UNIRSE, Y POR QUÉ NO BASTA CON SEPARARLAS
----------------------------------------------------------
La memoria se unió por código de barras: Elektra le pegó al kit de 10 el
EAN de una sola tarjeta (4713435796849), el mismo de su propia ficha de la
pieza suelta, y match_by_gtin.py hizo lo que le toca hacer con un código
que coincide. Separarlas sin más no arregla nada: el refresco de mañana
vuelve a escribir ese `ean` y el cruce vuelve a unirlas. Por eso esa
publicación queda anotada en scripts/ean_dudosos.py, que es lo que impide
las dos cosas.

El disco Makita no tiene `gtin` a nivel de ficha, así que no vino de ahí
sino de una unión por nombre; como la ficha nueva se llama distinto (sin
"50PZ"), la coincidencia exacta de nombre que exige merge_cross_store.py ya
no se da y no hay nada extra que bloquear.

QUÉ SE QUEDA CON QUÉ ID
-----------------------
La ficha original conserva su id y se queda con el PAQUETE, porque su
nombre y su ficha técnica describen el paquete ("Contenido del Empaque: 50
Discos..."). Las ofertas de pieza suelta salen a una ficha nueva. Así
ninguna URL existente queda apuntando a un producto que cambió de
significado.

USO
---
    python3 scripts/split_multipack.py --dry-run
    python3 scripts/split_multipack.py
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, next_id, registrar_max_id, save_catalog  # noqa: E402
from ean_dudosos import ean_utilizable  # noqa: E402

# from:  ficha que se queda con el paquete
# match: fragmentos de URL de las ofertas que son PIEZA SUELTA y salen
# new:   ficha nueva que las recibe
SEPARACIONES = [
    {
        "from": "p121156",
        "match": ["mercadolibre.com.mx/p/MLM19954255"],
        "new": {
            "name": "Disco de corte para acero inoxidable Makita D-71685 4-1/2 pulgadas",
            "brand": "MAKITA",
            "category": "Herramientas",
            "subcategory": "Accesorios para herramientas eléctricas",
            "image": "wrench",
        },
    },
    {
        "from": "p49509",
        "match": [
            "mercadolibre.com.mx/p/MLM6172244",
            "micro-sd-hc-64gb-con-adaptador-sd-clase-10-adata",
        ],
        "new": {
            "name": "Memoria microSD HC 64GB clase 10 ADATA con adaptador SD",
            "brand": "ADATA",
            "category": "Almacenamiento",
            "subcategory": "Memorias y tarjetas",
            "image": "storage",
            # El código de barras es de la pieza, así que se va con la pieza.
            "gtin": "4713435796849",
        },
    },
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = load_catalog()
    by_id = {p["id"]: p for p in data["products"]}
    nid = next_id(data["products"], data)
    creadas = []

    for sep in SEPARACIONES:
        src = by_id.get(sep["from"])
        if not src:
            print(f"  {sep['from']}: no existe, se salta", file=sys.stderr)
            continue
        def es_pieza(o):
            u = (o.get("url") or "").lower()
            return any(frag.lower() in u for frag in sep["match"])
        piezas = [o for o in (src.get("offers") or []) if es_pieza(o)]
        if not piezas:
            print(f"  {sep['from']}: ya no tiene ofertas de pieza suelta, se salta")
            continue
        src["offers"] = [o for o in src["offers"] if o not in piezas]

        # El paquete se queda sin código: el que tenía es el de la pieza.
        if src.pop("gtin", None):
            print(f"  {sep['from']}: se le quita el gtin (era el de la pieza)")
        for o in src["offers"]:
            if o.get("ean") and not ean_utilizable(o):
                o.pop("ean")
                print(f"  {sep['from']}: se descarta el ean de {o.get('storeId')}")

        spec = sep["new"]
        dst = {
            "id": f"p{nid}",
            "name": spec["name"],
            "brand": spec["brand"],
            "category": spec["category"],
            "subcategory": spec["subcategory"],
            "image": spec["image"],
            "specs": [],
            "offers": piezas,
        }
        if spec.get("gtin"):
            dst["gtin"] = spec["gtin"]
        foto = next((o.get("photo") for o in piezas if o.get("photo")), None)
        if foto:
            dst["photo"] = foto
        data["products"].append(dst)
        by_id[dst["id"]] = dst
        creadas.append(dst)
        nid += 1

        queda = [(o.get("storeId"), o.get("price")) for o in src.get("offers") or []]
        sale = [(o.get("storeId"), o.get("price")) for o in piezas]
        print(f"  {sep['from']} {src['name'][:52]}")
        print(f"      paquete se queda con {queda}")
        print(f"      {dst['id']} (nueva) se lleva {sale}  {spec['name'][:50]}")

    if args.dry_run:
        print("\n(--dry-run: no se escribió nada)")
        return
    registrar_max_id(data, nid - 1)
    save_catalog(data)
    print(f"\nGuardado. Fichas nuevas: {len(creadas)}; catálogo: {len(data['products'])} productos")


if __name__ == "__main__":
    main()
