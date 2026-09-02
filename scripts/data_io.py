"""Carga/guardado del catálogo, con los productos partidos en varios
archivos (data/products-N.json) en vez de un solo data.json gigante.

POR QUÉ
-------
data.json llegó a 62.68 MB (58,233 productos) -- GitHub ya avisa a partir
de 50 MB, y su límite duro es 100 MB por archivo (rechaza el push). Agregar
Refacciones Automotrices de Elektra (~247,853 productos) hubiera llevado el
archivo a ~340 MB, un push que simplemente falla. En vez de eso, data.json
pasa a ser un manifiesto chico (meta/categorías/tiendas/regiones) más una
lista `productFiles`; los productos viven en data/products-1.json,
data/products-2.json, etc., cada uno de CHUNK_SIZE productos -- bien por
debajo del límite incluso si el catálogo sigue creciendo.

Los scripts existentes (add_*.py, generate_seo_pages.py, refresh_*.py) solo
necesitan cambiar `json.load(open(DATA_PATH))` / `json.dump(data, ...)` por
`load_catalog()` / `save_catalog(data)` -- el dict que devuelve/recibe
`load_catalog`/`save_catalog` tiene la misma forma de siempre
({meta, categories, ..., products: [...]}), así que el resto del código de
cada script no cambia.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
MANIFEST_PATH = os.path.join(DATA_DIR, "data.json")

# ~15,000 productos por archivo: con el tamaño promedio actual (~1.1KB/
# producto) deja cada chunk en ~16MB, bien debajo del aviso de 50MB de
# GitHub incluso si el promedio por producto crece.
CHUNK_SIZE = 15000

# Los archivos de productos se escriben SIN indentación. Con 87k productos
# el sangrado eran ~18 MB de espacios que el navegador igual tiene que
# descargar y parsear (gzip los comprime bien, pero el parseo y la memoria
# no se benefician). Nadie lee estos archivos a mano -- un diff de 87,000
# productos no es revisable con o sin sangrado -- así que el formato legible
# no compra nada. El manifiesto (data.json) sí queda indentado: es chico y
# sí se lee/edita a mano.
COMPACT = {"ensure_ascii": False, "separators": (",", ":")}

# Campos de la oferta que SOLO hacen falta en la ficha de producto (la tabla
# de ofertas y sus botones "Ver oferta"), nunca en portada/listas/búsqueda.
# Se sacan del archivo que el navegador descarga al abrir y viven en
# data/details-N.json, que el SPA pide recién al abrir una ficha:
#
#   url      8.5 MB en crudo -- la parte más pesada después de las fotos
#   sellers  2.1 MB -- el desglose por vendedor de Mercado Libre
#
# `specs` NO se saca aunque también parezca "de ficha": los filtros de
# Condición/MagSafe/Tamaño del listado lo leen, así que sacarlo rompería el
# filtrado. Tampoco se saca la url de los productos con colorVariants: ahí
# purchaseOptions() compara `v.url === base.url` para decidir a qué variante
# le corresponde el listPrice, y eso corre también en el listado (son 286
# productos, no mueve la aguja).
DETAIL_OFFER_FIELDS = ("url", "sellers")

# Chunks de detalle chicos (~2,000 productos, ~100 KB con gzip): abrir una
# ficha baja UN chunk, no el catálogo entero de detalles.
DETAIL_CHUNK_SIZE = 2000


def _split_detail(product):
    """Devuelve (producto_para_el_navegador, detalle) separando los campos
    que solo hace falta bajar al abrir la ficha."""
    offers = product.get("offers") or []
    if not offers or product.get("colorVariants"):
        return product, None
    detail = {}
    light_offers = []
    for i, o in enumerate(offers):
        light = o
        for field in DETAIL_OFFER_FIELDS:
            if o.get(field) is not None:
                if light is o:
                    light = dict(o)
                detail.setdefault(field, {})[str(i)] = light.pop(field)
        light_offers.append(light)
    if not detail:
        return product, None
    light_product = dict(product)
    light_product["offers"] = light_offers
    return light_product, detail


def load_catalog():
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)
    products = []
    for fname in manifest.get("productFiles", []):
        with open(os.path.join(ROOT, fname), encoding="utf-8") as f:
            products.extend(json.load(f))

    # Los detalles se vuelven a pegar acá: del lado de Python (importadores,
    # refrescos, generador de páginas SEO) el catálogo se sigue viendo
    # completo, como antes de partirlo.
    details = {}
    for fname in manifest.get("detailFiles", []):
        path = os.path.join(ROOT, fname)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            details.update(json.load(f))
    if details:
        for p in products:
            d = details.get(p["id"])
            if not d:
                continue
            for field, by_index in d.items():
                for idx, value in by_index.items():
                    i = int(idx)
                    if i < len(p.get("offers") or []):
                        p["offers"][i][field] = value

    manifest["products"] = products
    manifest.pop("productFiles", None)
    manifest.pop("detailFiles", None)
    return manifest


def _remove_stale(prefix, first_index):
    i = first_index
    while True:
        stale = os.path.join(ROOT, f"data/{prefix}-{i}.json")
        if not os.path.exists(stale):
            break
        os.remove(stale)
        i += 1


def save_catalog(data):
    products = data.pop("products", [])

    # Se separan los campos de "solo ficha" ANTES de partir en chunks, para
    # que el archivo que baja el navegador no los lleve.
    light, details = [], {}
    for p in products:
        light_p, detail = _split_detail(p)
        light.append(light_p)
        if detail:
            details[p["id"]] = detail

    chunks = [light[i:i + CHUNK_SIZE] for i in range(0, len(light), CHUNK_SIZE)] or [[]]
    product_files = []
    for i, chunk in enumerate(chunks, 1):
        fname = f"data/products-{i}.json"
        product_files.append(fname)
        with open(os.path.join(ROOT, fname), "w", encoding="utf-8") as f:
            json.dump(chunk, f, **COMPACT)
    # Si el catálogo se redujo, borra los archivos que ya sobran (si no,
    # quedarían productos fantasma que loadData() de js/app.js seguiría
    # cargando).
    _remove_stale("products", len(chunks) + 1)

    # Los detalles se parten alineados con el ORDEN de products: el SPA sabe
    # en qué chunk está una ficha por su posición en el arreglo
    # (floor(indice / detailChunkSize)), sin necesidad de un índice
    # id -> archivo de 87,000 entradas.
    detail_files = []
    n_detail_chunks = max(1, -(-len(light) // DETAIL_CHUNK_SIZE))
    for i in range(n_detail_chunks):
        piece = {
            p["id"]: details[p["id"]]
            for p in light[i * DETAIL_CHUNK_SIZE:(i + 1) * DETAIL_CHUNK_SIZE]
            if p["id"] in details
        }
        fname = f"data/details-{i + 1}.json"
        detail_files.append(fname)
        with open(os.path.join(ROOT, fname), "w", encoding="utf-8") as f:
            json.dump(piece, f, **COMPACT)
    _remove_stale("details", n_detail_chunks + 1)

    data["productFiles"] = product_files
    data["detailFiles"] = detail_files
    data["detailChunkSize"] = DETAIL_CHUNK_SIZE
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    data["products"] = products
