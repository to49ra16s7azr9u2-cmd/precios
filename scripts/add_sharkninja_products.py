#!/usr/bin/env python3
"""Agrega productos SharkNinja (sharkninja.mx -- marcas Ninja y Shark) al
catálogo. Mismo patrón que Whirlpool (add_whirlpool_products.py, de donde
se reutiliza fetch/_safe_url/extract_product): robots.txt permite las
páginas de producto, sin protección de bots, JSON-LD schema.org/Product
completo en cada una, ya en MXN. Descubrimiento vía el sitemap dedicado de
productos (sitemap_0-product.xml, 119 URLs) en vez de categorías.

Se excluyen accesorios/refacciones (cuchillas, bases, tapas, vasos de
repuesto) y artículos de merchandising sin relación con electrodomésticos
(vasos/botellas de viaje Ninja Thirsti/SipPerfect) -- no son el tipo de
producto que compara este catálogo.

USO
---
    python3 scripts/add_sharkninja_products.py --dry-run
    python3 scripts/add_sharkninja_products.py --affiliate-base "<link>"
"""
import argparse
import json
import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from add_whirlpool_products import fetch, extract_product, _safe_url  # noqa: E402
from data_io import load_catalog, save_catalog  # noqa: E402
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITEMAP_URL = "https://www.sharkninja.mx/sitemap_0-product.xml"

ACCESSORY_RE = re.compile(
    r"taza de viaje|botella de viaje|vaso para licuadora|vaso total crushing|"
    r"vasos? tritan|tazon de|base de carga|base motor|base de motor|"
    r"cuchilla|set de cuchillas|clip para|tapa de pico|"
    r"concentrador de peinado|cepillo plano shark|rizadores shark|"
    r"paquete de \d+ vasos",
    re.I,
)


def categorize(name):
    n = name.lower()
    if ACCESSORY_RE.search(n):
        return None, None, None
    # "knockbox"/"kit de repuesto" solos son el accesorio de repuesto; en un
    # nombre "... y Knockbox/Kit de Repuesto Combo" es un aparato real
    # empaquetado con el accesorio -- sí se compara.
    if ("knockbox" in n or "kit de repuesto" in n) and "combo" not in n:
        return None, None, None
    if "freidora de aire" in n or "air fryer" in n or "airfryer" in n:
        return "Electrodomésticos", "Freidoras de aire", "appliance"
    if "horno" in n:
        return "Electrodomésticos", "Freidoras de aire", "appliance"
    if "licuadora" in n or "exprimidor" in n:
        return "Electrodomésticos", "Licuadoras y extractores", "appliance"
    if "aspiradora robot" in n:
        return "Aspiradoras", "Robots aspiradores", "vacuum"
    if "aspiradora" in n:
        return "Aspiradoras", "Inalámbricas y de mano", "vacuum"
    if "cafetera" in n or "espresso" in n or "café" in n:
        return "Cafeteras", None, "coffee"
    if "ventilador" in n:
        return "Climatización", "Ventiladores", "snowflake"
    if any(x in n for x in ("multiestilizador", "flexstyle", "estilizador", "rizador", "cepillo secador", "cepillo con secador", "sistema de peinado", "shark glam", "shark® glam")):
        return "Aparatos de belleza", "Estilizadores y afeitado", "sparkle"
    if any(x in n for x in ("facialpro", "cryoglow", "depuffi", "mascarilla facial", "sistema de enfriamiento personal")):
        return "Aparatos de belleza", "Faciales", "sparkle"
    if "olla a presion" in n or "olla a presión" in n:
        return "Electrodomésticos", "Pequeños electrodomésticos de cocina", "appliance"
    if any(x in n for x in ("procesador", "sistema de cocina", "sistema de cocción", "creami", "slushi", "preparador de bowls")):
        return "Electrodomésticos", "Pequeños electrodomésticos de cocina", "appliance"
    return None, None, None


def candidate_urls():
    html = fetch(SITEMAP_URL)
    if not html:
        print("No se pudo bajar el sitemap de productos", file=sys.stderr)
        sys.exit(2)
    return re.findall(r"<loc>([^<]+)</loc>", html)


def affiliate_url(base, target_url):
    if not base:
        return target_url
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}ulp={urllib.parse.quote(target_url, safe='')}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--affiliate-base", default=None)
    args = ap.parse_args()

    urls = candidate_urls()
    print(f"Candidatas en el sitemap: {len(urls)}")

    data = load_catalog()
    existing_urls = {o["url"] for p in data["products"] for o in (p.get("offers") or [])}
    existing_target_urls = {
        urllib.parse.parse_qs(urllib.parse.urlparse(u).query).get("ulp", [u])[0]
        for u in existing_urls
    }

    def work(url):
        html = fetch(url)
        if not html:
            return ("sin_datos", url, None)
        info = extract_product(html, url)
        if not info or not info.get("name"):
            return ("sin_json_ld", url, None)
        if not info["in_stock"]:
            return ("sin_stock", url, None)
        if info["currency"] != "MXN":
            return ("moneda_inesperada", url, info)
        cat, sub, icon_key = categorize(info["name"])
        if not cat:
            return ("excluida", url, info)
        already = _safe_url(url) in existing_target_urls
        return ("ok_already" if already else "ok_new", url, {**info, "category": cat, "subcategory": sub, "icon": icon_key})

    results = {}
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        for status, url, info in pool.map(work, urls):
            results.setdefault(status, []).append((url, info))

    print("\n=== Resumen ===")
    for k, v in results.items():
        print(f"  {k}: {len(v)}")

    max_id = 0
    for p in data["products"]:
        m = re.match(r"p(\d+)$", p["id"])
        if m:
            max_id = max(max_id, int(m.group(1)))

    added = []
    for url, info in results.get("ok_new", []):
        max_id += 1
        offer_url = affiliate_url(args.affiliate_base, info["url"])
        photo = info["image"] if isinstance(info["image"], str) else (info["image"][0] if info.get("image") else None)
        product = {
            "id": f"p{max_id}",
            "name": info["name"],
            "brand": "Shark" if "shark" in info["name"].lower() else "Ninja",
            "category": info["category"],
            "image": info["icon"],
            "photo": photo,
            "specs": [],
            "reviews": [],
            "offers": [{
                "storeId": "sharkninja",
                "price": info["price"],
                "url": offer_url,
                "photo": photo,
                "shippingFee": None,
                "points": None,
                "rating": None,
                "reviewCount": 0,
                "stock": "in_stock",
                "verified": False,
            }],
        }
        if info.get("subcategory"):
            product["subcategory"] = info["subcategory"]
        added.append(product)

    print(f"\nNuevos productos a agregar: {len(added)}")
    if args.dry_run:
        print("(--dry-run: no se escribió data/data.json)\n")
        for p in added:
            print(f"  [{p['category']} / {p.get('subcategory')}] {p['name']}  ->  ${p['offers'][0]['price']:,.2f} MXN")
        for status in ("sin_datos", "sin_json_ld", "excluida"):
            for url, info in results.get(status, []):
                name = info["name"] if info else None
                print(f"  {status}: {url} | {name}")
        return

    if not added:
        return

    stores = data.setdefault("stores", [])
    if not any(s["id"] == "sharkninja" for s in stores):
        stores.append({
            "id": "sharkninja",
            "name": "SharkNinja",
            "hubRegion": None,
            "color": "#111111",
            "logo": "SN",
            "typicalShippingDays": [3, 8],
        })

    data["products"].extend(added)
    save_catalog(data)
    print(f"Catálogo actualizado: +{len(added)} productos, total {len(data['products'])}")


if __name__ == "__main__":
    main()
