"""Carga/guardado del catálogo, con los productos partidos POR CATEGORÍA
(data/cat/<slug>-N.json) en vez de un solo data.json gigante.

POR QUÉ SE PARTIÓ
-----------------
data.json llegó a 62.68 MB (58,233 productos) -- GitHub ya avisa a partir
de 50 MB, y su límite duro es 100 MB por archivo (rechaza el push). Agregar
Refacciones Automotrices de Elektra (~247,853 productos) hubiera llevado el
archivo a ~340 MB, un push que simplemente falla. En vez de eso, data.json
pasa a ser un manifiesto chico (meta/categorías/tiendas/regiones) y los
productos viven en archivos aparte.

POR QUÉ AHORA SE PARTE POR CATEGORÍA
------------------------------------
La partición anterior (data/products-N.json, 15,000 productos por archivo
en el orden en que venían) era ciega a la categoría, así que el navegador
no podía bajar "solo lo que la página necesita": para pintar CUALQUIER
página había que bajar los 6 archivos enteros -- 35 MB en crudo, 5.3 MB con
gzip, 84 mil productos -- y parsearlos antes de mostrar nada.

Partido por categoría, abrir Celulares baja 165 KB (gzip) en vez de 5.3 MB,
y Monitores 45 KB. Inicio no baja ninguna shard: los conteos, los sellos de
oferta y los rankings vienen precalculados en el manifiesto (ver
scripts/web_summary.py).

De paso, cada commit de catálogo pesa mucho menos: agregar un lote de
monitores reescribe la shard de Monitores, no los 35 MB de products-N.json.

QUÉ NO CAMBIA
-------------
Los scripts (add_*.py, generate_seo_pages.py, refresh_*.py) siguen usando
`load_catalog()` / `save_catalog(data)`, que devuelven/reciben el catálogo
COMPLETO con la misma forma de siempre ({meta, categories, ...,
products: [...]}). Toda la partición vive acá adentro.
"""
import json
import os
import re
import unicodedata

import web_summary

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
MANIFEST_PATH = os.path.join(DATA_DIR, "data.json")
CAT_DIR = "data/cat"
DET_DIR = "data/det"
INDEX_FILE = "data/index.json"
HOME_FILE = "data/home.json"

# Tope por archivo de categoría. Ninguna categoría real se le acerca hoy (la
# más grande, Herramientas, son ~7,300 productos / 3 MB en crudo), pero evita
# que una categoría que crezca sola vuelva a acercarse al límite de 100 MB
# por archivo de GitHub.
CATEGORY_CHUNK_SIZE = 15000

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


def slugify(text):
    """Mismo slug que scripts/generate_seo_pages.py (categoria/<slug>/), para
    que el archivo de una categoría se llame igual que su página."""
    normalized = unicodedata.normalize("NFKD", text or "")
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text).strip("-").lower()


def _category_slugs(category_ids):
    """slug único por categoría. Dos categorías distintas podrían reducirse
    al mismo slug (acentos, símbolos); en ese caso la segunda lleva sufijo,
    para que nunca se pisen dos archivos."""
    slugs, used = {}, set()
    for cat_id in category_ids:
        base = slugify(cat_id) or "sin-categoria"
        slug, i = base, 2
        while slug in used:
            slug, i = f"{base}-{i}", i + 1
        used.add(slug)
        slugs[cat_id] = slug
    return slugs


def _file_lists(mapping):
    """Aplana {catId: [archivos]} a una sola lista, en orden."""
    return [f for files in mapping.values() for f in files]


def load_catalog():
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)

    # Partición por categoría (actual) o, si el árbol viene de antes de la
    # migración, la partición ciega por conteo.
    product_files = _file_lists(manifest.get("categoryFiles", {})) or manifest.get("productFiles", [])
    products = []
    for fname in product_files:
        with open(os.path.join(ROOT, fname), encoding="utf-8") as f:
            products.extend(json.load(f))

    # Los detalles se vuelven a pegar acá: del lado de Python (importadores,
    # refrescos, generador de páginas SEO) el catálogo se sigue viendo
    # completo, como antes de partirlo.
    detail_files = manifest.get("detailFiles", [])
    if isinstance(detail_files, dict):
        detail_files = _file_lists(detail_files)
    details = {}
    for fname in detail_files:
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
    for key in (
        "productFiles", "detailFiles", "categoryFiles", "totalProducts",
        "categoryStats", "homePools", "indexFile", "homeFile",
    ):
        manifest.pop(key, None)
    return manifest


def _write(fname, payload):
    path = os.path.join(ROOT, fname)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, **COMPACT)


def _remove_stale(dirname, keep):
    """Borra los .json del directorio que ya no están en el manifiesto. Sin
    esto, una categoría que se vacía (o que cambia de nombre, y con él de
    slug) dejaría su archivo viejo colgado y la SPA seguiría pudiendo
    cargar productos fantasma."""
    path = os.path.join(ROOT, dirname)
    if not os.path.isdir(path):
        return
    keep_names = {os.path.basename(f) for f in keep}
    for name in os.listdir(path):
        if name.endswith(".json") and name not in keep_names:
            os.remove(os.path.join(path, name))


def _product_index(light, slugs):
    """Índice id -> categoría para las rutas que llegan con un id y sin
    categoría: enlace directo a una ficha (#/p/pNNN), favoritos e historial.

    Se guarda como TRAMOS [primer id, categoría] sobre los ids ordenados, no
    como un mapa de 84 mil entradas: los productos se importan por lote de
    una misma categoría, así que quedan ~4,200 tramos (12 KB con gzip). Un
    arreglo posicional pesaría menos hoy, pero crece con el id MÁS ALTO y no
    con la cantidad de productos -- con el tiempo los ids se van salteando y
    ese formato se degrada solo.
    """
    cat_order = list(slugs.keys())
    cat_index = {cat_id: i for i, cat_id in enumerate(cat_order)}
    numbered, extra = [], {}
    for p in light:
        m = re.fullmatch(r"p(\d+)", p["id"])
        idx = cat_index.get(p.get("category"))
        if idx is None:
            continue
        if m:
            numbered.append((int(m.group(1)), idx))
        else:
            # id que no sigue el formato pN (no debería haber, pero si
            # aparece uno no puede quedar sin poder resolverse).
            extra[p["id"]] = idx
    runs = []
    for num, idx in sorted(numbered):
        if not runs or runs[-1][1] != idx:
            runs.append([num, idx])
    return {"categories": cat_order, "runs": runs, "extra": extra}


def save_catalog(data):
    products = data.pop("products", [])

    # Se separan los campos de "solo ficha" ANTES de partir, para que el
    # archivo que baja el navegador no los lleve.
    light, details = [], {}
    for p in products:
        light_p, detail = _split_detail(p)
        light.append(light_p)
        if detail:
            details[p["id"]] = detail

    # Agrupado por categoría, conservando el orden del catálogo dentro de
    # cada una (los rankings desempatan por ese orden, ver web_summary).
    groups = {}
    for p in light:
        groups.setdefault(p.get("category") or "", []).append(p)
    slugs = _category_slugs(groups.keys())

    category_files, detail_files = {}, {}
    for cat_id, items in groups.items():
        slug = slugs[cat_id]
        chunks = [
            items[i:i + CATEGORY_CHUNK_SIZE]
            for i in range(0, len(items), CATEGORY_CHUNK_SIZE)
        ] or [[]]
        files = []
        for i, chunk in enumerate(chunks, 1):
            fname = f"{CAT_DIR}/{slug}-{i}.json"
            files.append(fname)
            _write(fname, chunk)
        category_files[cat_id] = files

        # Los detalles se parten por POSICIÓN DENTRO DE LA CATEGORÍA: la SPA
        # ya cargó la shard de la categoría cuando abre una ficha, así que
        # sabe el índice del producto ahí y con él el chunk
        # (floor(indice / detailChunkSize)) -- sin bajar un índice
        # id -> archivo de 84 mil entradas.
        dfiles = []
        n_chunks = max(1, -(-len(items) // DETAIL_CHUNK_SIZE))
        for i in range(n_chunks):
            piece = {
                p["id"]: details[p["id"]]
                for p in items[i * DETAIL_CHUNK_SIZE:(i + 1) * DETAIL_CHUNK_SIZE]
                if p["id"] in details
            }
            fname = f"{DET_DIR}/{slug}-{i + 1}.json"
            dfiles.append(fname)
            _write(fname, piece)
        detail_files[cat_id] = dfiles

    _remove_stale(CAT_DIR, _file_lists(category_files))
    _remove_stale(DET_DIR, _file_lists(detail_files))
    # Restos de la partición anterior (ciega por conteo), que ya nadie lee.
    for legacy in os.listdir(DATA_DIR):
        if re.fullmatch(r"(products|details)-\d+\.json", legacy):
            os.remove(os.path.join(DATA_DIR, legacy))

    _write(INDEX_FILE, _product_index(light, slugs))

    # Todo lo que Inicio necesita saber del catálogo sin bajarlo: conteos,
    # sellos de oferta y el pool de candidatos de los rankings.
    summary = web_summary.build_summary(light, data.get("stores", []), data.get("categories", []))
    _write(HOME_FILE, summary.pop("homeProducts"))

    data["categoryFiles"] = category_files
    data["detailFiles"] = detail_files
    data["detailChunkSize"] = DETAIL_CHUNK_SIZE
    data["indexFile"] = INDEX_FILE
    data["homeFile"] = HOME_FILE
    data.update(summary)
    data.pop("productFiles", None)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    data["products"] = products
