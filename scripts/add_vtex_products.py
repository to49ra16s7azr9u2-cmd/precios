#!/usr/bin/env python3
"""Agrega al catálogo los productos de una tienda VTEX (ver vtex_stores.py).

Es add_elektra_products.py hecho genérico: la misma API pública de catálogo
(`/api/catalog_system/pub/products/search?fq=C:/padre/hijo/`, de a 50), el
mismo criterio de qué entra y qué no, y el mismo formato de producto. Lo que
cambia por tienda vive en vtex_stores.TIENDAS: dominio, ids de categoría y
a qué categoría del sitio va cada una.

Lo que se guarda de cada producto:
  - precio, precio de lista y vendedor del vendedor más barato CON
    existencia (ver vendedor_publicable en add_elektra_products.py);
  - foto, marca, EAN (para el cruce por código de barras con Mercado Libre,
    ver match_by_gtin.py) y la ficha técnica (elektra_specs.py, que es de
    VTEX, no de Elektra).

USO
---
    python3 scripts/add_vtex_products.py --store chedraui --preset tecnologia --dry-run --limit 40
    python3 scripts/add_vtex_products.py --store chedraui --preset todo
    python3 scripts/add_vtex_products.py --store marti --category-path 82/119
"""
import argparse
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from add_elektra_products import PAGE_SIZE, fetch_json, vendedor_publicable  # noqa: E402
from data_io import load_catalog, next_id, registrar_max_id, save_catalog  # noqa: E402
from elektra_specs import specs_from  # noqa: E402
from vtex_stores import TIENDAS, junk_re_de, resolver, search_url  # noqa: E402


def iter_category(store_id, path, limit=None):
    base = search_url(store_id)
    frm, seen = 0, 0
    while True:
        batch = fetch_json(f"{base}?fq=C:/{path}/&_from={frm}&_to={frm + PAGE_SIZE - 1}")
        if not batch:
            return
        for p in batch:
            yield p
            seen += 1
            if limit and seen >= limit:
                return
        if len(batch) < PAGE_SIZE:
            return
        frm += PAGE_SIZE


def producto_de(store_id, p, mapping, junk_re):
    """(producto nuevo, motivo de descarte). Uno de los dos es None."""
    tienda = TIENDAS[store_id]
    name = (p.get("productName") or "").strip()
    if not name:
        return None, "sin_nombre"
    if junk_re.search(name):
        return None, "junk"
    resuelto = resolver(mapping, name)
    if not resuelto:
        return None, "sin_categoria"
    category, subcategory, icon_key = resuelto
    items = p.get("items") or []
    if not items:
        return None, "sin_stock"
    vendedor = vendedor_publicable(items[0])
    if not vendedor:
        return None, "sin_stock"
    offer = vendedor.get("commertialOffer") or {}
    price = offer.get("Price")
    url = p.get("link")
    if not url:
        return None, "sin_url"
    images = items[0].get("images") or []
    photo = images[0].get("imageUrl") if images else None
    offer_out = {
        "storeId": store_id,
        "price": price,
        "url": url,
        "photo": photo,
        "shippingFee": None,
        "points": None,
        "rating": None,
        "reviewCount": 0,
        "stock": "in_stock",
        "verified": False,
    }
    if vendedor.get("sellerId") is not None:
        offer_out["sellerId"] = str(vendedor["sellerId"])
    list_price = offer.get("ListPrice")
    if list_price and list_price > price:
        offer_out["listPrice"] = list_price
    ean = (items[0].get("ean") or "").strip()
    if ean:
        offer_out["ean"] = ean
    product = {
        "name": name,
        "brand": p.get("brand") or tienda["nombre"],
        "category": category,
        "image": icon_key,
        "photo": photo,
        "specs": specs_from(p),
        "reviews": [],
        "offers": [offer_out],
    }
    if subcategory:
        product["subcategory"] = subcategory
    return product, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True, choices=sorted(TIENDAS))
    ap.add_argument("--category-path", action="append", default=[], help="padre/hijo del árbol de la tienda")
    ap.add_argument("--preset")
    ap.add_argument("--limit", type=int, default=0, help="límite POR categoría, para pruebas")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    tienda = TIENDAS[args.store]
    paths = list(args.category_path)
    if args.preset:
        if args.preset not in tienda["presets"]:
            print(f"Presets de {args.store}: {', '.join(tienda['presets'])}", file=sys.stderr)
            sys.exit(2)
        paths += tienda["presets"][args.preset]
    if not paths:
        print("Se requiere --category-path o --preset", file=sys.stderr)
        sys.exit(2)

    data = load_catalog()
    existing_urls = {o.get("url") for p in data["products"] for o in (p.get("offers") or [])}
    existing_urls |= {
        urllib.parse.parse_qs(urllib.parse.urlparse(u).query).get("ulp", [u])[0]
        for u in existing_urls if u
    }
    max_id = next_id(data["products"], data) - 1

    added, seen_product_ids = [], set()
    stats = {"revisados": 0, "duplicada": 0, "junk": 0, "sin_categoria": 0,
             "sin_stock": 0, "sin_url": 0, "sin_nombre": 0}
    por_categoria = {}
    for path in paths:
        mapping = tienda["categorias"].get(path)
        if not mapping:
            print(f"AVISO: {args.store} no tiene mapeo para {path}, se omite", file=sys.stderr)
            continue
        junk_re = junk_re_de(args.store, path)
        antes = len(added)
        for p in iter_category(args.store, path, limit=args.limit or None):
            stats["revisados"] += 1
            pid = p.get("productId")
            if pid in seen_product_ids or p.get("link") in existing_urls:
                stats["duplicada"] += 1
                continue
            product, motivo = producto_de(args.store, p, mapping, junk_re)
            if motivo:
                stats[motivo] += 1
                continue
            seen_product_ids.add(pid)
            max_id += 1
            product = {"id": f"p{max_id}", **product}
            added.append(product)
            clave = (product["category"], product.get("subcategory"))
            por_categoria[clave] = por_categoria.get(clave, 0) + 1
        print(f"  {path}: +{len(added) - antes}")

    print("\n=== Resumen ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print(f"  agregables: {len(added)}")
    print("\nPor categoría del sitio:")
    for (cat, sub), n in sorted(por_categoria.items(), key=lambda x: -x[1]):
        print(f"  {n:5d}  {cat} / {sub}")

    if args.dry_run:
        print("\n(--dry-run: no se escribió nada)")
        for p in added[:40]:
            print(f"  [{p['category']} / {p.get('subcategory')}] {p['brand']} - {p['name'][:70]}  ->  ${p['offers'][0]['price']:,.2f}")
        if len(added) > 40:
            print(f"  ... y {len(added) - 40} más")
        return
    if not added:
        return

    stores = data.setdefault("stores", [])
    if not any(s["id"] == args.store for s in stores):
        stores.append(dict(tienda["store"]))
    data["products"].extend(added)
    registrar_max_id(data, max_id)
    save_catalog(data)
    print(f"\nCatálogo actualizado: +{len(added)} productos de {tienda['nombre']}, total {len(data['products'])}")


if __name__ == "__main__":
    main()
