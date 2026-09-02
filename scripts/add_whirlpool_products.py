#!/usr/bin/env python3
"""Agrega productos Whirlpool (whirlpool.mx) al catálogo, vía Admitad.

POR QUÉ WHIRLPOOL Y CÓMO
-------------------------
A diferencia de Coppel (robots.txt prohíbe /p/* y /c/*, sin feed en Admitad)
y Liverpool (Akamai Bot Manager protege el precio, que además ni siquiera
viaja en el HTML inicial), whirlpool.mx:

  - robots.txt permite /p (páginas de producto) explícitamente, con una
    línea "Allow: /p?idsku=*$" pensada para Google Merchant Center -- el
    propio sitio está optimizado para que herramientas de catálogo lo lean.
  - Sin protección de bots detectable (sin _abck/bm_sz/cf_clearance).
  - Cada página de producto trae JSON-LD schema.org/Product COMPLETO
    (name, brand, image, mpn, sku, gtin, offers.price/priceCurrency/
    availability) -- mismo mecanismo que ya se usa para SUNSKY/GeekBuying/
    theluxurycloset/Glasseslit (ver refresh_other_stores.py), pero más
    simple: el precio YA está en MXN (sin conversión de moneda).
  - Hay un sitemap de productos dedicado (sitemap/product-0.xml, 532 URLs)
    para descubrirlos sin necesidad de rastrear categorías.

Es una tienda de una sola marca (no marketplace): cada producto tiene una
sola oferta, igual que SUNSKY etc. -- no aplica el patrón "sellers" de
Mercado Libre.

FILTRADO
--------
El sitemap mezcla páginas que no son productos reales para este catálogo:
  - Páginas de servicio (instalaciones, garantías, desempaques) -- no traen
    JSON-LD Product, se descartan solas al no poder extraerse nada.
  - Consumibles/refacciones (pastillas Affresh, filtros de repuesto, kits
    de conexión, trims metálicos, cepillos) -- mismo criterio que ACCESSORY/
    BANNED en add_products.py: no son el producto en sí.
  - Fuera de stock (availability != InStock) -- se omiten en esta carga
    inicial; si vuelven a haber stock, una corrida futura los recogerá.

USO
---
    python3 scripts/add_whirlpool_products.py --dry-run --limit 30
    python3 scripts/add_whirlpool_products.py --affiliate-base "<link>"
"""
import argparse
import html
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITEMAP_URL = "https://www.whirlpool.mx/sitemap/product-0.xml"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept-Language": "es-MX,es;q=0.9",
    "Accept-Encoding": "gzip",
}

# Páginas de servicio / no-producto que aparecen en el sitemap de productos
# por error de origen (no tienen JSON-LD Product, pero se descartan por
# nombre antes de gastar un pedido).
SERVICE_SLUGS = {
    "instalaciones", "desempaques", "pisos-superiores",
    "garantias-extendidas", "garantia-premium",
}

# Consumibles / refacciones / accesorios -- no son "el producto" que se
# compara en el catálogo, son partes de reemplazo o insumos.
ACCESSORY_RE = re.compile(
    r"affresh|pastilla|limpiador|limpieza|filtro-de-|filtro-a-everydrop|"
    r"pedestal|motor-interno|refaccion|kit-de-conexion|trim-metalico|"
    r"cepillo-para|bomba-flojet|dryer-rack|regulador-electronico-de-voltaje|"
    r"kit-premium-de-parrillas|parrilla-para-asar-/",
    re.I,
)

LD_JSON_RE = re.compile(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S)

_domain_lock = threading.Lock()
_last_request = [0.0]
MIN_INTERVAL = 0.5


def _throttle():
    with _domain_lock:
        wait = MIN_INTERVAL - (time.time() - _last_request[0])
        if wait > 0:
            time.sleep(wait)
        _last_request[0] = time.time()


def _safe_url(url):
    """Codifica caracteres no-ASCII en la ruta (el sitemap de whirlpool.mx
    trae algunas URLs con comillas tipográficas “”/pulgadas o ³ sin escapar,
    que rompen la línea de petición HTTP si se mandan tal cual)."""
    parts = urllib.parse.urlsplit(url)
    path = urllib.parse.quote(parts.path, safe="/-_.~")
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))


def fetch(url, retries=2):
    url = _safe_url(url)
    for attempt in range(retries + 1):
        _throttle()
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=25) as r:
                raw = r.read()
                import gzip
                if raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                return raw.decode("utf-8", errors="ignore")
        except Exception:
            if attempt == retries:
                return None
            time.sleep(1.5 * (attempt + 1))
    return None


def candidate_urls():
    html = fetch(SITEMAP_URL)
    if not html:
        print("No se pudo bajar el sitemap de productos", file=sys.stderr)
        sys.exit(2)
    locs = re.findall(r"<loc>([^<]+)</loc>", html)
    out = []
    for u in locs:
        slug = urllib.parse.urlparse(u).path.strip("/").rsplit("/", 1)[0].lower()
        bare = slug.rstrip("/")
        if bare in SERVICE_SLUGS:
            continue
        if ACCESSORY_RE.search(u):
            continue
        out.append(u)
    return out


def extract_product(page_html, url):
    for block in LD_JSON_RE.findall(page_html):
        try:
            data = json.loads(block)
        except Exception:
            continue
        if isinstance(data, list):
            candidates = data
        else:
            candidates = [data]
        # ProductGroup (sharkninja.mx): el Offer real vive en hasVariant[],
        # no en el nodo de arriba. Se agregan como candidatos aparte,
        # priorizando el variant cuya url coincide con la página pedida
        # (una página puede listar más de un color).
        expanded = []
        for node in candidates:
            if isinstance(node, dict) and "ProductGroup" in (
                node.get("@type") if isinstance(node.get("@type"), list) else [node.get("@type")]
            ):
                variants = node.get("hasVariant") or []
                matching = [v for v in variants if isinstance(v, dict) and v.get("url") == url]
                expanded.extend(matching or [v for v in variants if isinstance(v, dict)])
        candidates = expanded + candidates
        for node in candidates:
            if not isinstance(node, dict):
                continue
            t = node.get("@type")
            types = t if isinstance(t, list) else [t]
            if "Product" not in types:
                continue
            offers = node.get("offers")
            if isinstance(offers, dict) and offers.get("offers"):
                sub = offers["offers"]
                offer = sub[0] if isinstance(sub, list) else sub
            elif isinstance(offers, list):
                offer = offers[0] if offers else None
            else:
                offer = offers
            if not isinstance(offer, dict):
                continue
            avail = str(offer.get("availability") or "")
            in_stock = "InStock" in avail
            price = offer.get("price")
            currency = offer.get("priceCurrency") or "MXN"
            if price is None:
                continue
            try:
                price = float(str(price).replace(",", ""))
            except ValueError:
                continue
            name = node.get("name")
            return {
                "name": html.unescape(name) if name else name,
                "image": node.get("image"),
                "description": node.get("description") or "",
                "sku": node.get("sku") or node.get("mpn"),
                "price": price,
                "currency": currency,
                "in_stock": in_stock,
                "url": _safe_url(url),
            }
    return None


# ---------------------------------------------------------------------------
# Categorización: por palabras clave en el NOMBRE real (JSON-LD), no en el
# slug de la URL -- el nombre es lo que un humano compara contra el resto
# del catálogo, el slug a veces es menos descriptivo (p. ej. solo el SKU).
# ---------------------------------------------------------------------------
def categorize(name):
    n = name.lower()
    if "frigobar" in n:
        return "Refrigeradores", "Frigobares y mini refrigeradores", "fridge"
    if "cava" in n:
        return "Refrigeradores", "Frigobares y mini refrigeradores", "fridge"
    if "refrigerador" in n:
        sub = "Uso comercial" if "comercial" in n else "Refrigeradores"
        return "Refrigeradores", sub, "fridge"
    if "congelador" in n:
        return "Refrigeradores", "Congeladores", "fridge"
    if (
        "minisplit" in n or "mini split" in n or "aire acondicionado" in n
        or "climatizacion" in n or "equipo piso techo" in n or "toneladas" in n
    ):
        return "Climatización", "Aires acondicionados", "snowflake"
    if "deshumidificador" in n:
        return "Climatización", "Deshumidificadores", "snowflake"
    if "enfriador de aire evaporativo" in n or "climatizador evaporativo" in n:
        return "Climatización", "Climatizadores evaporativos", "snowflake"
    if "torre de lavado" in n or "centro de lavado" in n:
        return "Lavadoras", "Centros de lavado", "washer"
    if "secadora" in n and "lavadora" not in n:
        return "Lavadoras", "Secadoras", "washer"
    if "lavadora" in n or "lavasecadora" in n or "combo" in n:
        if "carga superior" in n:
            return "Lavadoras", "Carga superior", "washer"
        if "carga frontal" in n:
            return "Lavadoras", "Carga frontal", "washer"
        if "semiautomatica" in n or "semiautomática" in n:
            return "Lavadoras", "Semiautomáticas", "washer"
        return "Lavadoras", "Lavasecadoras", "washer"
    if "microondas" in n:
        return "Electrodomésticos", "Microondas", "appliance"
    if "lavavajilla" in n:
        return "Electrodomésticos", "Lavavajillas", "appliance"
    if "campana" in n:
        return "Electrodomésticos", "Campanas de cocina", "appliance"
    if "cafetera" in n:
        return "Cafeteras", None, "coffee"
    if "triturador de desperdicios" in n:
        return "Electrodomésticos", "Otros", "appliance"
    if "dispensador" in n or "despachador" in n or "purificador de agua" in n or "enfriador de agua" in n:
        return "Electrodomésticos", "Purificadores de agua", "appliance"
    if "estufa" in n or "horno" in n or "parrilla" in n or "calienta platos" in n:
        return "Electrodomésticos", "Estufas y hornos", "appliance"
    return None, None, None


def slugify(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s[:60]


def ensure_taxonomy(categories):
    """Agrega las subcategorías nuevas (Congeladores, Secadoras, Centros de
    lavado, Microondas, Lavavajillas, Campanas de cocina) a las categorías
    ya existentes si todavía no están, sin tocar el resto."""
    needed = {
        "Refrigeradores": [("Congeladores", "fridge")],
        "Lavadoras": [("Secadoras", "washer"), ("Centros de lavado", "washer")],
        "Electrodomésticos": [
            ("Microondas", "appliance"),
            ("Lavavajillas", "appliance"),
            ("Campanas de cocina", "appliance"),
        ],
    }
    by_id = {c["id"]: c for c in categories}
    for cat_id, subs in needed.items():
        cat = by_id.get(cat_id)
        if not cat:
            continue
        existing = {s["id"] for s in cat.get("subcategories", [])}
        for sub_id, icon in subs:
            if sub_id not in existing:
                cat.setdefault("subcategories", []).append({"id": sub_id, "name": sub_id, "icon": icon})


def affiliate_url(base, target_url):
    if not base:
        return target_url
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}ulp={urllib.parse.quote(target_url, safe='')}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--affiliate-base", default=None, help="Link base de Admitad (deeplink) para whirlpool.mx")
    args = ap.parse_args()

    urls = candidate_urls()
    print(f"Candidatas tras filtrar servicio/consumibles: {len(urls)} de 532")
    if args.limit:
        urls = urls[: args.limit]

    data = load_catalog()
    existing_urls = {o["url"] for p in data["products"] for o in (p.get("offers") or [])}
    existing_target_urls = {
        urllib.parse.parse_qs(urllib.parse.urlparse(u).query).get("ulp", [u])[0]
        for u in existing_urls
    }

    results = []
    seen_sku = set()

    def work(url):
        html = fetch(url)
        if not html:
            return ("sin_datos", url, None)
        info = extract_product(html, url)
        if not info or not info.get("name"):
            return ("sin_json_ld", url, None)
        if not info["in_stock"]:
            return ("sin_stock", url, None)
        if info["currency"] not in ("MXN",):
            return ("moneda_inesperada", url, info)
        cat, sub, icon_key = categorize(info["name"])
        if not cat:
            return ("sin_categoria", url, info)
        return ("ok", url, {**info, "category": cat, "subcategory": sub, "icon": icon_key})

    stats = {}
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        for i, (status, url, info) in enumerate(pool.map(work, urls), 1):
            stats[status] = stats.get(status, 0) + 1
            if status == "ok":
                results.append(info)
            if i % 50 == 0:
                print(f"  {i}/{len(urls)} revisados...", flush=True)

    print("\n=== Resumen de extracción ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    max_id = 0
    for p in data["products"]:
        m = re.match(r"p(\d+)$", p["id"])
        if m:
            max_id = max(max_id, int(m.group(1)))

    added = []
    dupes = 0
    for info in results:
        sku = info.get("sku") or slugify(info["name"])
        if sku in seen_sku:
            dupes += 1
            continue
        seen_sku.add(sku)
        target_url = info["url"]
        if target_url in existing_urls or target_url in existing_target_urls:
            dupes += 1
            continue
        max_id += 1
        offer_url = affiliate_url(args.affiliate_base, target_url)
        product = {
            "id": f"p{max_id}",
            "name": info["name"],
            "brand": "Whirlpool",
            "category": info["category"],
            "image": info["icon"],
            "photo": info["image"] if isinstance(info["image"], str) else (info["image"][0] if info["image"] else None),
            "specs": [],
            "reviews": [],
            "offers": [
                {
                    "storeId": "whirlpool",
                    "price": info["price"],
                    "url": offer_url,
                    "photo": info["image"] if isinstance(info["image"], str) else (info["image"][0] if info["image"] else None),
                    "shippingFee": None,
                    "points": None,
                    "rating": None,
                    "reviewCount": 0,
                    "stock": "in_stock",
                    "verified": False,
                }
            ],
        }
        if info.get("subcategory"):
            product["subcategory"] = info["subcategory"]
        added.append(product)

    print(f"\nNuevos productos a agregar: {len(added)} (duplicados/omitidos: {dupes})")

    if args.dry_run:
        print("\n(--dry-run: no se escribió data/data.json)\n")
        for p in added[:20]:
            print(f"  [{p['category']} / {p.get('subcategory')}] {p['name']}  ->  ${p['offers'][0]['price']:,.2f} MXN")
        if len(added) > 20:
            print(f"  ... y {len(added) - 20} más")
        return

    if not added:
        return

    ensure_taxonomy(data["categories"])

    stores = data.setdefault("stores", [])
    if not any(s["id"] == "whirlpool" for s in stores):
        stores.append({
            "id": "whirlpool",
            "name": "Whirlpool",
            "hubRegion": None,
            "color": "#7B0028",
            "logo": "WP",
            "typicalShippingDays": [5, 12],
        })

    data["products"].extend(added)
    save_catalog(data)
    print(f"Catálogo actualizado: +{len(added)} productos, total {len(data['products'])}")


if __name__ == "__main__":
    main()
