#!/usr/bin/env python3
"""Da de alta productos NUEVOS a partir de una captura de Amazon.com.mx.

POR QUÉ HACE FALTA ADEMÁS DE add_amazon_offers.py
--------------------------------------------------
add_amazon_offers.py agrega una oferta a un producto que YA existe: hay que
pasarle un product_id. Pero en cada lote de captura aparecen equipos que el
catálogo no tiene en esa configuración exacta -- un iPhone 12 Pro de 512 GB
cuando solo está el de 256, un Xiaomi Pad 7 de 8+256 en gris cuando están
el de 12+256 gris y el de 8+256 azul. Esos no se pueden "agregar a" nada, y
hasta ahora se daban de alta a mano, sin dejar rastro de con qué criterio.

CUÁNDO ALTA Y CUÁNDO NO
-----------------------
Alta SOLO cuando ninguna ficha del catálogo es ese mismo equipo. Ante la
duda -- "Azul" de Amazon contra "Titanium Silverblue" del catálogo, sin
saber si son el mismo acabado -- se da de alta aparte en vez de pegarle la
oferta a la ficha parecida: una ficha repetida se ve y se arregla, un
precio puesto en el producto equivocado no se ve y engaña al comprador.
(Es el mismo criterio de merge_by_signature.py y match_amazon_capture.py.)

SIN PRECIO NO HAY ALTA
----------------------
Una captura sin `price` es un anuncio que Amazon mostró sin oferta de
compra en ese momento. Dar de alta un producto cuyo único precio no existe
sería publicar una ficha vacía en un comparador de precios, así que esos se
saltan y se informan. De los 53 anuncios capturados que nunca aterrizaron,
5 son exactamente este caso -- no eran un olvido.

FORMATO DE ENTRADA (JSON)
-------------------------
Lista de objetos, uno por producto nuevo:

    [
      {"asin": "B08L7SPX9N",
       "title": "Apple iPhone 12 Pro (512 GB) - Color grafito",
       "price": 28181.04,
       "photo": "https://m.media-amazon.com/images/I/...jpg",
       "brand": "APPLE", "category": "Celulares", "subcategory": "iPhone",
       "image": "phone"}
    ]

  image  clave del set de ilustraciones (data/icons.json) que se muestra
         mientras no carga la foto -- la misma que ya usa esa categoría.

USO
---
    python3 scripts/add_amazon_standalone.py nuevos.json --dry-run
    python3 scripts/add_amazon_standalone.py nuevos.json --tag comparamex0d-20
"""
import argparse
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog  # noqa: E402

AMAZON_STORE = "amazon_mx"


def next_id(products, data=None):
    """Primer id libre, y NUNCA uno que ya se haya usado.

    Antes devolvía max(ids existentes) + 1. Si un producto se daba de baja
    --refresh_prices.py poda las publicaciones que Mercado Libre retira, y
    alguna vez se borra a mano-- ese id volvía a quedar libre y el siguiente
    alta se lo llevaba. Pasó de verdad: se dio de baja p125291 (una UGREEN de
    10,000 mAh con precio mal capturado) y el alta siguiente reusó el mismo
    id para otro power bank. Eso rompe cosas que no se ven:

      - /producto/p125291/ ya está indexada por Google apuntando al primero.
      - Los favoritos y el historial de la cuenta guardan ids (Firestore).
      - data/hist/ guarda la serie de precios por id: dos productos
        distintos terminarían compartiendo una sola serie.

    Así que el máximo histórico se guarda en data.json (meta.maxProductId) y
    el id siguiente sale de ahí, no de lo que hay hoy en el catálogo.
    """
    top = 0
    for p in products:
        m = re.match(r"p(\d+)$", p.get("id", ""))
        if m:
            top = max(top, int(m.group(1)))
    if data is not None:
        top = max(top, int((data.get("meta") or {}).get("maxProductId") or 0))
    return top + 1


def registrar_max_id(data, ultimo_id):
    """Deja anotado en el manifiesto el id más alto que se llegó a usar."""
    n = int(re.sub(r"\D", "", str(ultimo_id)) or 0)
    meta = data.setdefault("meta", {})
    meta["maxProductId"] = max(int(meta.get("maxProductId") or 0), n)


def existing_asins(products):
    out = set()
    for p in products:
        offers = list(p.get("offers") or [])
        for v in p.get("colorVariants") or []:
            offers += list(v.get("offers") or [])
        for o in offers:
            for a in re.findall(r"/dp/([A-Z0-9]{10})", o.get("url") or ""):
                out.add(a)
    return out


# Cuántas veces el precio más caro que ya tiene esa subcategoría puede
# superarse antes de sospechar de la captura. Tres es holgado: deja pasar un
# producto legítimamente más caro que todo lo que hay, y frena los órdenes de
# magnitud, que es lo que produce una captura mal alineada.
FACTOR_PRECIO_ABSURDO = 3
# Con menos productos que esto la comparación no dice nada.
MIN_PARA_COMPARAR = 10


def techos_por_subcategoria(products):
    """{(categoria, subcategoria): precio máximo del catálogo} para el control.

    Una captura de Amazon puede traer el precio de OTRO anuncio (pasó: en un
    lote de 41, diecisiete compartían valor con un producto distinto, y una
    UGREEN de 10,000 mAh y una AsperX de 27,600 mAh 162.5W tenían el mismo
    número). El precio de un power bank no se puede verificar sin volver a
    Amazon, pero sí se puede comparar contra lo que ya vale esa misma
    subcategoría: los 26 productos de "10,000 a 20,000 mAh" del catálogo van
    de $197 a $2,184, así que un $56,999 no es un producto caro, es un dato
    malo.
    """
    por = collections.defaultdict(list)
    for p in products:
        precios = [o["price"] for o in (p.get("offers") or []) if o.get("price")]
        for v in p.get("colorVariants") or []:
            precios += [o["price"] for o in (v.get("offers") or []) if o.get("price")]
            if v.get("price"):
                precios.append(v["price"])
        if precios:
            por[(p["category"], p.get("subcategory"))].append(min(precios))
    return {k: max(v) for k, v in por.items() if len(v) >= MIN_PARA_COMPARAR}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="JSON con los productos nuevos")
    ap.add_argument("--tag", help="tracking id de Amazon Associates")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        items = json.load(f)

    data = load_catalog()
    known = existing_asins(data["products"])
    cat_ids = {c["id"]: {s["id"] for s in (c.get("subcategories") or [])}
               for c in data["categories"]}
    nid = next_id(data["products"], data)
    techos = techos_por_subcategoria(data["products"])

    created, skipped = [], []
    for it in items:
        asin = (it.get("asin") or "").strip().upper()
        if not asin:
            skipped.append((it.get("title", "?"), "sin asin"))
            continue
        if asin in known:
            skipped.append((it.get("title", "?"), "ese ASIN ya está en el catálogo"))
            continue
        if it.get("price") in (None, "", 0):
            skipped.append((it.get("title", "?"), "sin precio (Amazon no mostró oferta de compra)"))
            continue
        cat = it.get("category")
        if cat not in cat_ids:
            skipped.append((it.get("title", "?"), f"categoría desconocida: {cat}"))
            continue
        sub = it.get("subcategory")
        if sub and sub not in cat_ids[cat]:
            skipped.append((it.get("title", "?"), f"subcategoría desconocida: {cat}/{sub}"))
            continue
        techo = techos.get((cat, sub))
        precio = it["price"]
        if techo and precio > techo * FACTOR_PRECIO_ABSURDO:
            skipped.append((
                it.get("title", "?"),
                f"precio inverosímil: ${precio:,.2f} cuando lo más caro de "
                f"{cat}/{sub} en el catálogo es ${techo:,.2f} -- revisar la captura",
            ))
            continue

        url = f"https://www.amazon.com.mx/dp/{asin}/"
        if args.tag:
            url += f"?tag={args.tag}"
        product = {
            "id": f"p{nid}",
            "name": it["title"],
            "brand": it.get("brand") or "",
            "category": cat,
            "subcategory": sub,
            "image": it.get("image") or "box",
            "photo": it.get("photo"),
            "specs": [],
            "offers": [{
                "storeId": AMAZON_STORE,
                "price": it["price"],
                "stock": "in_stock",
                "url": url,
            }],
        }
        if not product["photo"]:
            del product["photo"]
        data["products"].append(product)
        known.add(asin)
        created.append(product)
        nid += 1

    for name, why in skipped:
        print(f"  SALTADO  {name[:64]:64} {why}")
    print(f"\nAltas: {len(created)}   saltados: {len(skipped)}")
    for p in created:
        print(f"  {p['id']:9} {p['category']}/{p['subcategory']}  ${p['offers'][0]['price']:>10,.2f}  {p['name'][:58]}")

    if args.dry_run:
        print("\n(--dry-run: no se guardó nada)")
        return
    if not created:
        print("\nNada que guardar.")
        return
    registrar_max_id(data, nid - 1)
    save_catalog(data)
    print(f"\nGuardado. Catálogo: {len(data['products'])} productos")
    print("Recordá correr compute_facets.py y generate_seo_pages.py después.")


if __name__ == "__main__":
    main()
