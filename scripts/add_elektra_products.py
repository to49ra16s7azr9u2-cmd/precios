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

def norm(name):
    """minúsculas y sin acentos -- el catálogo de Elektra mezcla formas
    acentuadas/sin acentuar del mismo producto (p. ej. "Batería portatil" y
    "Bateria Portátil" en el mismo listado), así que cada categorizador
    compara sobre esta forma normalizada en vez de repetir cada variante."""
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", name.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


EARBUDS_RE = re.compile(
    r"airpods|galaxy buds|enco buds|enco air|redmi buds|earbuds|"
    r"audifono|auricular",
    re.I,
)


def cat_audio(name):
    n = norm(name)
    if EARBUDS_RE.search(n):
        wireless = "inalambric" in n or "bluetooth" in n or "airpods" in n or "buds" in n
        return "Audífonos", ("Earbuds inalámbricos" if wireless else "Diadema con cable"), "headphones"
    if any(k in n for k in (
        "barra de sonido", "soundbar", "home theater", "home cinema",
        "minicomponente", "mini componente", "torre de sonido", "teatro en casa",
    )):
        return "Bocinas", "Barras de sonido y home theater", "speaker"
    if "bocina" in n or "altavoz" in n or "parlante" in n or "speaker" in n or "bafle" in n:
        return "Bocinas", None, "speaker"
    if "tocadiscos" in n or "consola de sonido" in n:
        return "Instrumentos musicales", "DJ y producción", "guitar"
    return None


def cat_computo_accesorios(name):
    n = norm(name)
    if "teclado" in n:
        return "Teclados", "Mecánicos" if "mecanic" in n else "Membrana", "keyboard"
    if re.search(r"\bmouse\b|\bmause\b|\bratonn?\b", n):
        return "Mouse", "Gaming" if "gaming" in n or "gamer" in n else "Oficina", "mouse"
    if "webcam" in n or "camara web" in n:
        return "Computadoras", "Webcams", "cpu"
    if "memoria ram" in n or re.search(r"\bram\b", n):
        return "Computadoras", "Memoria RAM", "cpu"
    if any(k in n for k in ("disco duro", "ssd", "memoria usb", "unidad flash", "microsd", "micro sd", "tarjeta sd", "memoria micro sd")):
        return "Almacenamiento", None, "storage"
    if any(k in n for k in ("router", "repetidor wifi", "extensor de red", "punto de acceso", "access point", "modem", "módem")):
        return "Redes", None, "wifi"
    return cat_audio(name)


def cat_telefonia_accesorios(name):
    n = norm(name)
    if "cargador" in n or "adaptador de corriente" in n:
        return "Cargadores y adaptadores", "Cargadores", "charger"
    if EARBUDS_RE.search(n):
        wireless = "inalambric" in n or "bluetooth" in n or "airpods" in n or "buds" in n
        return "Audífonos", ("Earbuds inalámbricos" if wireless else "Earbuds con cable"), "headphones"
    if any(k in n for k in ("power bank", "cargador portatil")) or re.search(r"bateri?a\s*portatil", n):
        return "Baterías portátiles", None, "battery"
    if any(k in n for k in ("microsd", "micro sd", "tarjeta sd", "memoria micro sd")):
        return "Almacenamiento", None, "storage"
    return None


def cat_electronica_accesorios(name):
    return cat_telefonia_accesorios(name) or cat_audio(name)


def cat_tv(name):
    n = norm(name)
    if "proyector" in n:
        return "Proyectores y accesorios", "Proyectores", "projector"
    if any(k in n for k in ("roku", "chromecast", "fire tv", "apple tv", "reproductor de streaming", "convertidor a smart tv")):
        return "Televisores", "Dispositivos de streaming", "tv"
    if "televisor" in n or "pantalla" in n or "smart tv" in n or re.search(r"\btv\b", n):
        return "Televisores", ("4K y QLED" if any(k in n for k in ("4k", "qled", "uhd", "oled")) else "Full HD y HD"), "tv"
    return None


def cat_monitores_proyeccion(name):
    n = norm(name)
    if "monitor" in n:
        return "Monitores", "Gaming" if "gaming" in n or "gamer" in n else "Oficina", "monitor"
    if "proyector" in n:
        return "Proyectores y accesorios", "Proyectores", "projector"
    return None


def cat_videojuegos(name):
    n = norm(name)
    if "consola" in n:
        return "Videojuegos", "Consolas", "gamepad"
    if any(k in n for k in (
        "control ", "controlador", "mando ", "joystick", "volante", "headset gamer",
        "audifono gamer", "chatpad", "grip", "almohadilla", "adaptador para control",
        "adaptador para juegos", "base de carga", "cargador para control",
    )):
        return "Videojuegos", "Accesorios", "gamepad"
    if any(k in n for k in ("figura", "funko", "peluche", "playera", "taza", "mochila", "poster")):
        return None  # merchandising/coleccionables, no es el tipo de producto de este catálogo
    return "Videojuegos", "Software", "gamepad"


def cat_cocina(name):
    n = norm(name)
    if "microondas" in n:
        return "Electrodomésticos", "Microondas", "appliance"
    if "lavavajilla" in n:
        return "Electrodomésticos", "Lavavajillas", "appliance"
    if "campana" in n:
        return "Electrodomésticos", "Campanas de cocina", "appliance"
    if "cafetera" in n or "espresso" in n or "molino de cafe" in n or "molinillo de cafe" in n:
        return "Cafeteras", None, "coffee"
    if "freidora de aire" in n or "air fryer" in n:
        return "Electrodomésticos", "Freidoras de aire", "appliance"
    if "licuadora" in n or "extractor de jugos" in n:
        return "Electrodomésticos", "Licuadoras y extractores", "appliance"
    if "estufa" in n or "horno" in n or "parrilla" in n:
        return "Electrodomésticos", "Estufas y hornos", "appliance"
    if any(k in n for k in ("olla", "batidora", "tostador", "sandwichera", "waflera", "vaporera", "arrocera")):
        return "Electrodomésticos", "Pequeños electrodomésticos de cocina", "appliance"
    return None


# Accesorios (correas, fundas, cargadores, protectores) que se cuelan en
# categorías de "el aparato en sí" -- Wearables y Tablets y Accesorios de
# Elektra mezclan el dispositivo real con todos sus accesorios en la misma
# categoría del árbol.
WEARABLE_ACCESSORY_RE = re.compile(
    r"correa|banda(?!\s+de actividad)|pulsera(?!\s*inteligente)|funda|protector|"
    r"mica|cargador|cable|estuche|cristal templado|vidrio templado|"
    r"base de carga|repuesto|cubierta",
    re.I,
)


def cat_wearables(name):
    n = norm(name)
    if WEARABLE_ACCESSORY_RE.search(n):
        return None
    if "banda de actividad" in n or "pulsera inteligente" in n or "rastreador de actividad" in n:
        return "Relojes inteligentes", "Bandas de actividad", "watch"
    if "reloj" in n or "smartwatch" in n or "smart watch" in n or "ring" in n:
        return "Relojes inteligentes", "Smartwatches", "watch"
    return None


TABLET_ACCESSORY_RE = re.compile(
    r"funda|estuche|protector|mica|cristal templado|vidrio templado|teclado|"
    r"lapiz|pluma|stylus|soporte|cable|cargador|correa",
    re.I,
)


def cat_tabletas(name):
    n = norm(name)
    if TABLET_ACCESSORY_RE.search(n):
        return None
    if "tablet" in n or "ipad" in n:
        return "Tabletas", ("Apple" if "ipad" in n or "apple" in n else "Android"), "tablet"
    return None


def cat_impresion(name):
    n = norm(name)
    if "impresora 3d" in n or "escaner 3d" in n:
        return "Impresión 3D", "Impresoras" if "impresora" in n else "Escáneres 3D", "printer3d"
    if "filamento" in n:
        return "Impresión 3D", "Filamentos", "printer3d"
    if "resina" in n and "impresion" in n:
        return "Impresión 3D", "Accesorios y repuestos", "printer3d"
    if any(k in n for k in (
        "cartucho de tinta", "cartucho de toner", "cartucho de tóner", "toner",
        "tóner", "tinta para impresora", "etiquetas termorretractiles",
        "papel fotografico", "papel termico", "cinta para impresora",
    )):
        return "Impresoras", "Consumibles", "printer"
    if "impresora" in n or "multifuncional" in n or "escaner" in n or "scanner" in n or "plotter" in n:
        tipo = "Térmica" if "termica" in n else ("Láser" if "laser" in n else "Inyección de tinta")
        return "Impresoras", tipo, "printer"
    return None


def cat_climatizacion(name):
    n = norm(name)
    if "ventilador" in n:
        return "Climatización", "Ventiladores", "snowflake"
    if "calefactor" in n or "calentador de ambiente" in n:
        return "Climatización", "Calefactores", "snowflake"
    if "deshumidificador" in n:
        return "Climatización", "Deshumidificadores", "snowflake"
    if "humidificador" in n:
        return "Climatización", "Humidificadores", "snowflake"
    if "purificador de aire" in n:
        return "Climatización", "Purificadores de aire", "snowflake"
    if "climatizador evaporativo" in n or "enfriador evaporativo" in n:
        return "Climatización", "Climatizadores evaporativos", "snowflake"
    if "minisplit" in n or "mini split" in n or "aire acondicionado" in n:
        return "Climatización", "Aires acondicionados", "snowflake"
    return None


def cat_electrodomesticos(name):
    base = cat_cocina(name)
    if base:
        return base
    n = norm(name)
    if "aspiradora robot" in n:
        return "Aspiradoras", "Robots aspiradores", "vacuum"
    if "aspiradora" in n:
        return "Aspiradoras", "Inalámbricas y de mano", "vacuum"
    if "secadora de pelo" in n or "secadora de cabello" in n:
        return "Electrodomésticos", "Secadoras de pelo", "appliance"
    if "plancha" in n and "cabello" not in n:
        return "Electrodomésticos", "Planchas", "appliance"
    if "purificador de agua" in n:
        return "Electrodomésticos", "Purificadores de agua", "appliance"
    if "maquina de coser" in n:
        return "Electrodomésticos", "Máquinas de coser", "appliance"
    if "robot limpiacristales" in n:
        return "Electrodomésticos", "Robots limpiacristales", "appliance"
    return None


# category_path (padre/hijo de category/tree) -> (categoría, subcategoría, icono)
# fijos, O un callable name(str)->(categoría, subcategoría, icono)|None para
# categorías "cajón de sastre" de Elektra donde el producto real varía
# renglón a renglón (se resuelve por palabras clave del nombre; None = no
# es el tipo de producto que compara este catálogo, se descarta).
CATEGORY_MAP = {
    # Línea blanca
    "1371645/1371678": ("Refrigeradores", "Refrigeradores", "fridge"),
    "1371645/1371679": ("Lavadoras", None, "washer"),
    "1371645/1371680": cat_cocina,
    "1371645/1371681": cat_climatizacion,
    "1371645/1371682": cat_electrodomesticos,
    # Electrónica
    "1371643/1371670": cat_tv,
    "1371643/1371672": cat_audio,
    "1371643/1371671": cat_electronica_accesorios,
    "1371643/1371674": ("Cámaras y fotografía", None, "camera"),
    "1371643/831911": ("Domótica y hogar inteligente", None, "house"),
    "1371643/4642048": ("Instrumentos musicales", None, "guitar"),
    # Cómputo
    "1371654/1371720": ("Laptops", "Oficina y estudio", "laptop"),
    "1371654/1371721": ("Computadoras de escritorio", None, "desktop"),
    "1371654/1371722": cat_monitores_proyeccion,
    "1371654/1371724": ("Almacenamiento", None, "storage"),
    "1371654/1371725": cat_impresion,
    "1371654/1371727": cat_computo_accesorios,
    "1371654/1371728": cat_tabletas,
    # Telefonía
    "1371655/1371729": ("Celulares", "Android", "phone"),
    "1371655/1371730": cat_telefonia_accesorios,
    "1371655/1371733": cat_wearables,
    # Videojuegos
    "1371652/127631": cat_videojuegos,
    "1371652/127647": cat_videojuegos,
    "1371652/127682": cat_videojuegos,
    "1371652/4754776": cat_videojuegos,
    "1371652/4754782": cat_videojuegos,
    # Herramientas
    "4845836/4845852": ("Herramientas", "Herramientas eléctricas", "wrench"),
}
PRESETS = {
    "linea_blanca": ["1371645/1371678", "1371645/1371679"],
    "linea_blanca_resto": ["1371645/1371680", "1371645/1371681", "1371645/1371682"],
    "electronica": ["1371643/1371670", "1371643/1371672", "1371643/1371671", "1371643/1371674", "1371643/831911", "1371643/4642048"],
    "computo": ["1371654/1371720", "1371654/1371721", "1371654/1371722", "1371654/1371724", "1371654/1371725", "1371654/1371727", "1371654/1371728"],
    "telefonia": ["1371655/1371729", "1371655/1371730", "1371655/1371733"],
    "videojuegos": ["1371652/127631", "1371652/127647", "1371652/127682", "1371652/4754776", "1371652/4754782"],
    "herramientas": ["4845836/4845852"],
}
PRESETS["todo"] = (
    PRESETS["linea_blanca"] + PRESETS["linea_blanca_resto"] + PRESETS["electronica"]
    + PRESETS["computo"] + PRESETS["telefonia"] + PRESETS["videojuegos"] + PRESETS["herramientas"]
)

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
    stats = {"revisados": 0, "sin_stock": 0, "junk": 0, "sin_precio": 0, "duplicada": 0, "sin_categoria": 0}
    for path in paths:
        mapping = CATEGORY_MAP.get(path)
        if not mapping:
            print(f"AVISO: sin mapeo de categoría para {path}, se omite", file=sys.stderr)
            continue
        dynamic = callable(mapping)
        print(f"\n== {path} -> {'(por palabra clave)' if dynamic else '/'.join(str(x) for x in mapping[:2])} ==")
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
            if dynamic:
                resolved = mapping(name)
                if not resolved:
                    stats["sin_categoria"] += 1
                    continue
                category, subcategory, icon_key = resolved
            else:
                category, subcategory, icon_key = mapping
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
