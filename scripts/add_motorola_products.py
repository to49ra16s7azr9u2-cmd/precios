#!/usr/bin/env python3
"""Agrega productos Motorola (motorola.com.mx) al catálogo desde el feed
CSV que exporta Admitad directo -- a diferencia de Coppel/Liverpool/
Whirlpool, acá no hace falta scraping ni JSON-LD: el feed ya trae nombre,
precio, imagen, categoría y el link de afiliado (con `ulp=`) listo para
usar.

USO
---
    python3 scripts/add_motorola_products.py --dry-run
    python3 scripts/add_motorola_products.py --feed-url "<url del export_adv_products>"
    python3 scripts/add_motorola_products.py --feed-file ruta/local.csv
"""
import argparse
import csv
import io
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "data", "data.json")

# categoryId del feed -> (categoría, subcategoría) del catálogo. "MotoCare"
# (planes de garantía/protección extendida, no un producto físico) se
# excluye por completo -- ver EXCLUDE_CATEGORIES.
CATEGORY_MAP = {
    "Smartphones - razr": ("Celulares", "Android"),
    "Smartphones - Familia Edge": ("Celulares", "Android"),
    "Smartphones - Familia Moto G": ("Celulares", "Android"),
    "Smartphones - Familia Signature": ("Celulares", "Android"),
    "Accesorios - Cargadores": ("Cargadores y adaptadores", "Cargadores"),
    "Accesorios - Audífono": ("Audífonos", "Earbuds inalámbricos"),
    "Accesorios - Smartwatch": ("Relojes inteligentes", "Smartwatches"),
    "Accesorios - Bocina": ("Bocinas", "Pequeña"),
    "Accesorios - Rastreador": ("Otros", None),
    "Accesorios - Pen": ("Otros", None),
}
EXCLUDE_CATEGORIES = {"MotoCare"}

CATEGORY_ICON = {
    "Celulares": "phone",
    "Cargadores y adaptadores": "charger",
    "Audífonos": "headphones",
    "Relojes inteligentes": "watch",
    "Bocinas": "speaker",
    "Otros": "box",
}


def parse_price(raw):
    if not raw:
        return None
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return None


def load_rows(feed_url, feed_file):
    if feed_file:
        with open(feed_file, encoding="utf-8") as f:
            text = f.read()
    else:
        req = urllib.request.Request(feed_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            text = r.read().decode("utf-8")
    return list(csv.DictReader(io.StringIO(text), delimiter=";"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feed-url", default=None)
    ap.add_argument("--feed-file", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not args.feed_url and not args.feed_file:
        print("Se requiere --feed-url o --feed-file", file=sys.stderr)
        sys.exit(2)

    rows = load_rows(args.feed_url, args.feed_file)
    print(f"Filas en el feed: {len(rows)}")

    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    existing_urls = {o["url"] for p in data["products"] for o in (p.get("offers") or [])}

    max_id = 0
    for p in data["products"]:
        m = re.match(r"p(\d+)$", p["id"])
        if m:
            max_id = max(max_id, int(m.group(1)))

    added, skipped = [], {"excluida": 0, "no_disponible": 0, "sin_precio": 0, "duplicada": 0, "sin_categoria": 0}
    for row in rows:
        cat_id = row.get("categoryId", "")
        if cat_id in EXCLUDE_CATEGORIES:
            skipped["excluida"] += 1
            continue
        if row.get("available") != "true":
            skipped["no_disponible"] += 1
            continue
        mapping = CATEGORY_MAP.get(cat_id)
        if not mapping:
            skipped["sin_categoria"] += 1
            print("  sin mapeo de categoría:", cat_id, "|", row.get("name"))
            continue
        category, subcategory = mapping
        price = parse_price(row.get("price"))
        if price is None:
            skipped["sin_precio"] += 1
            continue
        url = row.get("url")
        if not url or url in existing_urls:
            skipped["duplicada"] += 1
            continue
        old_price = parse_price(row.get("oldprice"))

        max_id += 1
        offer = {
            "storeId": "motorola",
            "price": price,
            "url": url,
            "photo": row.get("picture") or None,
            "shippingFee": None,
            "points": None,
            "rating": None,
            "reviewCount": 0,
            "stock": "in_stock",
            "verified": False,
        }
        if old_price and old_price > price:
            offer["listPrice"] = old_price
        product = {
            "id": f"p{max_id}",
            "name": row.get("name") or row.get("nombre_producto"),
            "brand": "Motorola",
            "category": category,
            "image": CATEGORY_ICON.get(category, "box"),
            "photo": row.get("picture") or None,
            "specs": [],
            "reviews": [],
            "offers": [offer],
        }
        if subcategory:
            product["subcategory"] = subcategory
        added.append(product)
        existing_urls.add(url)

    print(f"\nNuevos productos: {len(added)}")
    for k, v in skipped.items():
        print(f"  {k}: {v}")

    if args.dry_run:
        print("\n(--dry-run: no se escribió data/data.json)")
        for p in added:
            print(f"  [{p['category']} / {p.get('subcategory')}] {p['name']}  ->  ${p['offers'][0]['price']:,.2f} MXN")
        return

    if not added:
        return

    stores = data.setdefault("stores", [])
    if not any(s["id"] == "motorola" for s in stores):
        stores.append({
            "id": "motorola",
            "name": "Motorola",
            "hubRegion": None,
            "color": "#5A3EBA",
            "logo": "MT",
            "typicalShippingDays": [3, 7],
        })

    data["products"].extend(added)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"data/data.json actualizado: +{len(added)} productos, total {len(data['products'])}")


if __name__ == "__main__":
    main()
