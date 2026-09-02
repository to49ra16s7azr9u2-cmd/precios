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


def load_catalog():
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)
    products = []
    for fname in manifest.get("productFiles", []):
        with open(os.path.join(ROOT, fname), encoding="utf-8") as f:
            products.extend(json.load(f))
    manifest["products"] = products
    manifest.pop("productFiles", None)
    return manifest


def save_catalog(data):
    products = data.pop("products", [])
    chunks = [products[i:i + CHUNK_SIZE] for i in range(0, len(products), CHUNK_SIZE)] or [[]]
    product_files = []
    for i, chunk in enumerate(chunks, 1):
        fname = f"data/products-{i}.json"
        product_files.append(fname)
        with open(os.path.join(ROOT, fname), "w", encoding="utf-8") as f:
            json.dump(chunk, f, **COMPACT)

    # Si el catálogo se redujo, borra los archivos de productos que ya
    # sobran (si no, quedarían productos fantasma que loadData() de
    # js/app.js seguiría cargando).
    i = len(chunks) + 1
    while True:
        stale = os.path.join(ROOT, f"data/products-{i}.json")
        if not os.path.exists(stale):
            break
        os.remove(stale)
        i += 1

    data["productFiles"] = product_files
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    data["products"] = products
