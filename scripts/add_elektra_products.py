#!/usr/bin/env python3
"""Agrega productos de Elektra (elektra.mx) al catálogo -- SIN link de
afiliado todavía (ver nota de PRECIO/URL abajo). Coppel resultó bloqueado
(robots.txt prohíbe /p/*, /c/* y hasta /graphql) y Liverpool.com.mx está
protegido con Akamai Bot Manager; Elektra es la primera tienda mexicana
"de verdad" (SKUs del mercado MX, no el catálogo de exportación china que
usan SUNSKY/GeekBuying/etc.) donde el acceso a los datos es sencillo:

  - robots.txt de elektra.mx permite explícitamente
    `Allow: /api/catalog_system/pub/products/search?fq=*` -- es la propia
    tienda invitando a usar esa API, no un rincón sin proteger.
  - Es VTEX (mismo motor que whirlpool.mx): API pública de catálogo, JSON
    limpio con precio/stock/marca/categoría/imagen, ya en MXN.
  - El filtro `fq=C:/id_padre/id_hijo/` (con el PATH completo de category
    ids, no solo el id de la hoja -- se armó mal la primera vez y devolvía
    0 resultados) es la forma soportada de listar por categoría, con
    paginación _from/_to de 50 en 50 (VTEX limita el tamaño de página).

DESCUBRIMIENTO DE CATEGORÍAS
-----------------------------
`/api/catalog_system/pub/category/tree/N` (sin "?", así que ni siquiera
entra en las reglas de robots.txt sobre "/*?") da el árbol completo. El
catálogo de Elektra es enorme (~48,000 productos solo en las categorías de
electrónica/línea blanca/cómputo/telefonía/videojuegos) -- se agrega por
tandas de categorías explícitas (CATEGORY_MAP abajo), no todo de una vez.

PRECIO/URL: SIN AFILIADO (por ahora)
--------------------------------------
A diferencia de Whirlpool/SharkNinja/Motorola, todavía no hay una forma de
monetizar los clics a Elektra (no tiene programa propio visible, y el
único camino en Admitad es vía Takeads con aprobación pendiente). Se agrega
igual el precio real con el link directo a elektra.mx (storeId="elektra",
sin envolver en ulp=) porque el valor de la comparación de precio es real
hoy mismo; el día que haya link de afiliado, ese campo `url` es lo único
que hay que reemplazar (ver --affiliate-base, opcional).

USO
---
    python3 scripts/add_elektra_products.py --dry-run --category-path 1371645/1371678 --limit 100
    python3 scripts/add_elektra_products.py --preset linea_blanca
    python3 scripts/add_elektra_products.py --preset linea_blanca --affiliate-base "<link>"
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "data", "data.json")
SEARCH_URL = "https://www.elektra.mx/api/catalog_system/pub/products/search"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept-Language": "es-MX,es;q=0.9",
    "Accept-Encoding": "gzip",
}
PAGE_SIZE = 50

# category_path (padre/hijo de category/tree) -> (categoría, subcategoría, icono)
# del catálogo. Presets agrupan varias rutas relacionadas.
CATEGORY_MAP = {
    "1371645/1371678": ("Refrigeradores", "Refrigeradores", "fridge"),
    "1371645/1371679": ("Lavadoras", None, "washer"),
}
PRESETS = {
    "linea_blanca": ["1371645/1371678", "1371645/1371679"],
}

# Marcas/rutas que no aportan al catálogo o son de terceros claramente
# fuera de foco (p. ej. refacciones sueltas) -- mismo criterio que
# add_products.py (BANNED/ACCESSORY) pero acotado a lo visto en Elektra.
JUNK_RE = re.compile(
    r"\brefacci[oó]n|repuesto|garant[ií]a extendida|servicio de instalaci[oó]n|"
    r"\bfiltro de agua\b|manguera(s)? de|kit de instalaci[oó]n|"
    # Neveras/hieleras/loncheras NO eléctricas (bolsas o cajas aislantes
    # sin motor de refrigeración) -- se cuelan en "Refrigeradores" pero no
    # son el tipo de aparato que este catálogo compara.
    r"hielera|enfriador de almuerzo|enfriador t[eé]rmico|lonchera t[eé]rmica|"
    r"fiambrera|bolsas? de hielo reutilizable|bombilla|everydrop|"
    r"affresh|tabletas? limpiadora",
    re.I,
)


def fetch_json(url, retries=3):
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=25) as r:
                raw = r.read()
                if raw[:2] == b"\x1f\x8b":
                    import gzip
                    raw = gzip.decompress(raw)
                return json.loads(raw.decode("utf-8"))
        except Exception:
            if attempt == retries:
                return None
            time.sleep(1.5 * (attempt + 1))
    return None


def iter_category(category_path, limit=None):
    frm = 0
    seen = 0
    while True:
        to = frm + PAGE_SIZE - 1
        url = f"{SEARCH_URL}?fq=C:/{category_path}/&_from={frm}&_to={to}"
        batch = fetch_json(url)
        if not batch:
            break
        for p in batch:
            yield p
            seen += 1
            if limit and seen >= limit:
                return
        if len(batch) < PAGE_SIZE:
            break
        frm += PAGE_SIZE


def affiliate_url(base, target_url):
    if not base:
        return target_url
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}ulp={urllib.parse.quote(target_url, safe='')}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category-path", action="append", default=[], help="padre/hijo, ej. 1371645/1371678")
    ap.add_argument("--preset", choices=list(PRESETS.keys()))
    ap.add_argument("--limit", type=int, default=0, help="límite POR categoría, para pruebas")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--affiliate-base", default=None)
    args = ap.parse_args()

    paths = list(args.category_path)
    if args.preset:
        paths += PRESETS[args.preset]
    if not paths:
        print("Se requiere --category-path o --preset", file=sys.stderr)
        sys.exit(2)

    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    existing_urls = {o["url"] for p in data["products"] for o in (p.get("offers") or [])}
    existing_target_urls = {
        urllib.parse.parse_qs(urllib.parse.urlparse(u).query).get("ulp", [u])[0]
        for u in existing_urls
    }

    max_id = 0
    for p in data["products"]:
        m = re.match(r"p(\d+)$", p["id"])
        if m:
            max_id = max(max_id, int(m.group(1)))

    added, seen_product_ids = [], set()
    stats = {"revisados": 0, "sin_stock": 0, "junk": 0, "sin_precio": 0, "duplicada": 0}
    for path in paths:
        mapping = CATEGORY_MAP.get(path)
        if not mapping:
            print(f"AVISO: sin mapeo de categoría para {path}, se omite", file=sys.stderr)
            continue
        category, subcategory, icon_key = mapping
        print(f"\n== {path} -> {category}/{subcategory} ==")
        for p in iter_category(path, limit=args.limit or None):
            stats["revisados"] += 1
            pid = p.get("productId")
            if pid in seen_product_ids:
                stats["duplicada"] += 1
                continue
            name = p.get("productName") or ""
            if JUNK_RE.search(name):
                stats["junk"] += 1
                continue
            items = p.get("items") or []
            if not items:
                stats["sin_stock"] += 1
                continue
            sellers = items[0].get("sellers") or []
            if not sellers:
                stats["sin_stock"] += 1
                continue
            offer = sellers[0].get("commertialOffer") or {}
            price = offer.get("Price")
            avail_qty = offer.get("AvailableQuantity", 0)
            if not price or avail_qty <= 0:
                stats["sin_stock"] += 1
                continue
            url = p.get("link")
            if not url or url in existing_urls or url in existing_target_urls:
                stats["duplicada"] += 1
                continue
            list_price = offer.get("ListPrice")
            images = items[0].get("images") or []
            photo = images[0]["imageUrl"] if images else None

            seen_product_ids.add(pid)
            max_id += 1
            offer_out = {
                "storeId": "elektra",
                "price": price,
                "url": affiliate_url(args.affiliate_base, url),
                "photo": photo,
                "shippingFee": None,
                "points": None,
                "rating": None,
                "reviewCount": 0,
                "stock": "in_stock",
                "verified": False,
            }
            if list_price and list_price > price:
                offer_out["listPrice"] = list_price
            product = {
                "id": f"p{max_id}",
                "name": name,
                "brand": p.get("brand") or "Elektra",
                "category": category,
                "image": icon_key,
                "photo": photo,
                "specs": [],
                "reviews": [],
                "offers": [offer_out],
            }
            if subcategory:
                product["subcategory"] = subcategory
            added.append(product)

    print("\n=== Resumen ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print(f"  agregables: {len(added)}")

    if args.dry_run:
        print("\n(--dry-run: no se escribió data/data.json)")
        for p in added[:30]:
            print(f"  [{p['category']} / {p.get('subcategory')}] {p['brand']} - {p['name']}  ->  ${p['offers'][0]['price']:,.2f} MXN")
        if len(added) > 30:
            print(f"  ... y {len(added) - 30} más")
        return

    if not added:
        return

    stores = data.setdefault("stores", [])
    if not any(s["id"] == "elektra" for s in stores):
        stores.append({
            "id": "elektra",
            "name": "Elektra",
            "hubRegion": None,
            "color": "#E30613",
            "logo": "EL",
            "typicalShippingDays": [3, 10],
        })

    data["products"].extend(added)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"data/data.json actualizado: +{len(added)} productos, total {len(data['products'])}")


if __name__ == "__main__":
    main()
