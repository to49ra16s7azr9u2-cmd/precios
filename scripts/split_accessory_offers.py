#!/usr/bin/env python3
"""Saca de una ficha las ofertas que en realidad son OTRO producto.

EL PROBLEMA
-----------
Auditando precios se buscaron ofertas que valen 1.9x o más que la más
barata del mismo producto. En cinco casos la diferencia no era una
diferencia de precio entre tiendas: era que la oferta barata NO ES EL
PRODUCTO.

    Proyector BenQ MH560 ($17,399 en Mercado Libre)
        <- "control para proyector BenQ MS560/MX560/MW560/MH560" ($1,171)
    Impresora Kyocera MA2600cwfx ($8,450)
        <- "cartucho de tóner negro Kyocera TK-5452K" ($2,082)
    Audífonos Sony WH-CH720N ($1,529)
        <- "estuche rígido Fintie para Sony WH-CH720N" ($506)
    Campana empotrable de 60 cm ($6,099)
        <- campana de PARED de 90 cm, otro modelo ($12,099)
    Combo estufa + campana de 76 cm ($10,699)
        <- solo la campana WH7610BB, sin la estufa ($2,399)

Es el peor error posible en un comparador: el sitio anunciaba el
proyector a $1,171 -- el precio del control remoto -- y "Ver oferta"
mandaba al comprador a comprar el control. Es exactamente el mismo daño
que documenta audit_cross_store.py para las uniones por nombre.

QUÉ HACE, Y POR QUÉ NO SOLO BORRA
---------------------------------
La oferta mal puesta ES un producto real de la tienda: borrarla sería
tirar un dato bueno. Cada una se MUEVE a donde corresponde -- a una ficha
que ya existe cuando la hay (la campana de 76 cm ya estaba en el catálogo
por su cuenta), o a una ficha nueva cuando no. El catálogo termina con
los mismos precios que antes, cada uno en el producto que de verdad es.

CÓMO SE ENCONTRARON
-------------------
Ofertas cuyo slug de Elektra dice "<accesorio> ... para ..." mientras el
nombre del producto no habla de un accesorio. El detector marcó 5, dos de
ellas falsos positivos que NO se tocan (un juego de brocas que se vende en
estuche, una mesa de ping pong que incluye funda: ahí el accesorio es
parte del mismo producto). Las dos campanas salieron de la revisión a
mano de los outliers entre tiendas. Por eso la lista va escrita acá y no
se aplica sola: son cinco casos verificados uno por uno.

USO
---
    python3 scripts/split_accessory_offers.py --dry-run
    python3 scripts/split_accessory_offers.py
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, next_id, registrar_max_id, save_catalog  # noqa: E402

# (ficha de la que sale, fragmento que identifica la oferta, destino)
# destino: {"to": "pNNN"} mueve a una ficha existente
#          {"new": {...}} crea una ficha nueva con esos campos
MOVES = [
    {
        "from": "p29261",
        "match": "control-para-proyector-benq",
        "new": {
            "name": "Control remoto para proyector BenQ MS560 / MX560 / MW560 / MH560",
            "brand": "BenQ", "category": "Proyectores y accesorios",
            "subcategory": "Accesorios", "image": "projector",
        },
    },
    {
        "from": "p28666",
        "match": "cartucho-de-toner-negro-kyocera-tk-5452k",
        "new": {
            "name": "Cartucho de tóner negro Kyocera TK-5452K para MA2600cwfx",
            "brand": "KYOCERA", "category": "Impresoras",
            "subcategory": "Consumibles", "image": "printer",
        },
    },
    {
        "from": "p29909",
        "match": "estuche-rigido-para-auriculares-fintie",
        "new": {
            # Categoría "Otros/Varios": Audífonos no tiene subcategoría de
            # accesorios, y meterlo en "Diadema inalámbrica" lo dejaría
            # compitiendo en la lista contra audífonos de verdad.
            "name": "Estuche rígido Fintie para audífonos Sony WH-CH720N / CH520 / XM6 / XM5",
            "brand": "FINTIE", "category": "Otros",
            "subcategory": "Varios", "image": "box",
        },
    },
    {
        "from": "p36264",
        "match": "whw9910s",   # cae en las DOS ofertas del modelo de pared de 90 cm
        "new": {
            "name": "Campana Whirlpool de pared 90 cm acero inoxidable WHW9910S",
            "brand": "Whirlpool", "category": "Electrodomésticos",
            "subcategory": "Campanas de cocina", "image": "appliance",
        },
    },
    {
        # La campana de 76 cm ya tiene su propia ficha en el catálogo: la
        # oferta de Elektra va ahí, no a una nueva.
        "from": "p36429",
        "match": "campana-whirlpool-wh7610bb",
        "to": "p36328",
    },
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = load_catalog()
    by_id = {p["id"]: p for p in data["products"]}
    nid = next_id(data["products"], data)
    created = []

    for mv in MOVES:
        src = by_id.get(mv["from"])
        if not src:
            print(f"  {mv['from']}: no existe, se salta", file=sys.stderr)
            continue
        moving = [o for o in (src.get("offers") or [])
                  if mv["match"] in (o.get("url") or "").lower()]
        if not moving:
            print(f"  {mv['from']}: ya no tiene la oferta '{mv['match']}', se salta")
            continue
        src["offers"] = [o for o in src["offers"] if o not in moving]

        if "to" in mv:
            dst = by_id.get(mv["to"])
            if not dst:
                print(f"  destino {mv['to']} no existe -- se aborta este movimiento", file=sys.stderr)
                src["offers"].extend(moving)
                continue
            seen = {o.get("url") for o in dst.setdefault("offers", [])}
            added = [o for o in moving if o.get("url") not in seen]
            dst["offers"].extend(added)
            print(f"  {mv['from']} -> {mv['to']}: {len(added)} oferta(s) movida(s)")
        else:
            spec = mv["new"]
            dst = {
                "id": f"p{nid}",
                "name": spec["name"],
                "brand": spec["brand"],
                "category": spec["category"],
                "subcategory": spec["subcategory"],
                "image": spec["image"],
                "specs": [],
                "offers": moving,
            }
            photo = next((o.get("photo") for o in moving if o.get("photo")), None)
            if photo:
                dst["photo"] = photo
            data["products"].append(dst)
            by_id[dst["id"]] = dst
            created.append(dst)
            nid += 1
            print(f"  {mv['from']} -> {dst['id']} (nueva): {len(moving)} oferta(s)  {spec['name'][:56]}")

        left = [(o.get("storeId"), o.get("price")) for o in src.get("offers") or []]
        print(f"       {mv['from']} queda con {left}")

    if args.dry_run:
        print("\n(--dry-run: no se escribió nada)")
        return
    registrar_max_id(data, nid - 1)
    save_catalog(data)
    print(f"\nGuardado. Fichas nuevas: {len(created)}; catálogo: {len(data['products'])} productos")


if __name__ == "__main__":
    main()
