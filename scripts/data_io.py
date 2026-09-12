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
import urllib.parse

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
#   url        8.5 MB en crudo -- la parte más pesada después de las fotos
#   sellers    2.1 MB -- el desglose por vendedor de Mercado Libre
#   ean        el código de barras de la publicación. js/ no lo lee NUNCA
#              (0 referencias); solo lo usan match_by_gtin.py y
#              refresh_elektra.py, del lado de Python. Son dígitos al azar, o
#              sea lo peor que le puede pasar a gzip: sacarlo solo de la shard
#              de Muebles baja 536 -> 495 KB comprimidos (-7.7%).
#   topReview  la reseña destacada por tienda. Solo la pinta
#              renderStoreReviews(), que corre en la ficha DESPUÉS de
#              `await ensureDetail(product)` (js/app.js), no en el listado.
#              -2.1% en la misma shard.
#   photo      la foto DE LA OFERTA (no la del producto, que se queda). Solo
#              la lee renderOfferRows() para las pastillas de variantes, en la
#              ficha; la tarjeta del listado usa product.photo. 1.64 MB en
#              crudo entre todas las shards, -5% a -7% con gzip.
#
# `specs` NO se saca aunque también parezca "de ficha": los filtros de
# Condición/MagSafe/Tamaño del listado lo leen, así que sacarlo rompería el
# filtrado. Tampoco se saca la url de los productos con colorVariants: ahí
# purchaseOptions() compara `v.url === base.url` para decidir a qué variante
# le corresponde el listPrice, y eso corre también en el listado (son 286
# productos, no mueve la aguja).
DETAIL_OFFER_FIELDS = ("url", "sellers", "ean", "topReview", "photo", "sellerId")

# Con colorVariants la url TIENE que quedarse en la shard (purchaseOptions()
# compara `v.url === base.url` para saber a qué variante le toca cada
# listPrice, y eso corre en el listado). El resto sí se puede mover.
DETAIL_OFFER_FIELDS_CON_VARIANTES = tuple(
    f for f in DETAIL_OFFER_FIELDS if f != "url"
)

# La ficha técnica completa (importada de Elektra, hasta 16 campos por
# producto) NO puede viajar en la shard que el navegador baja al entrar a una
# categoría: son ~45 MB repartidos entre las shards, y sola la de
# Herramientas pasaría de 3.4 MB a ~8 MB. Se va al detalle, que se pide
# recién al abrir la ficha.
#
# Menos estas etiquetas, que el LISTADO sí lee para filtrar y ordenar (ver
# isUsed/hasMagSafe/sizeOf/usageBadge en js/app.js): si se fueran al
# detalle, los filtros dejarían de funcionar en la lista.
#
# "Peso" estuvo acá por productWeightKg(), que leía el spec para la
# calculadora de envío. Esa función ya no existe: la calculadora usa el peso
# del PAQUETE que publican SUNSKY/GeekBuying en la propia oferta
# (shippingWeightKg), y de los productos de esas tiendas ninguno trae el
# spec "Peso" (son 8,766 productos de Elektra/Mercado Libre). Viajaba en
# cada shard para un lector que no existía; ahora va al detalle con el
# resto de la ficha técnica, que es donde se muestra.
SPEC_LABELS_EN_LISTADO = ("Condición", "MagSafe", "Tamaño", "Uso")

# Campos del PRODUCTO (no de cada oferta) que tampoco hacen falta en el
# listado. Viajan en el detalle con el nombre prefijado por "_", igual que
# "_specs".
#
#   mlQuery  el término de búsqueda para pedirle el precio en vivo a Mercado
#            Libre. Solo lo usa fetchLiveOffer(), que corre desde renderDetail
#            después de `await ensureDetail(product)`. 0.47 MB en crudo, y en
#            Celulares --donde casi todo lo tiene-- vale un 7% de la shard.
DETAIL_PRODUCT_FIELDS = ("mlQuery",)

# Chunks de detalle chicos (~2,000 productos, ~100 KB con gzip): abrir una
# ficha baja UN chunk, no el catálogo entero de detalles.
DETAIL_CHUNK_SIZE = 2000


# El precio más barato entre los vendedores de una publicación, calculado con
# la MISMA regla que sellerRows() en js/app.js y seller_rows() en
# generate_seo_pages.py: solo si son 2 o más y TODOS traen su propio enlace
# (una fila con el precio de un vendedor y el enlace de otro publicaría un
# precio que no se paga).
#
# Se guarda en la shard porque `sellers` se va al detalle: sin este número, la
# lista mostraba el precio de la caja de compra y la ficha --ya con los
# detalles bajados-- mostraba el del vendedor más barato. Eran 608 productos
# diciendo dos precios distintos para el mismo artículo, con diferencias de
# hasta 5x (un refrigerador "Desde $37,998" en la lista que por dentro estaba
# a $6,565), y además el orden por precio los ponía donde no correspondía.
def _vendedor_mas_barato(sellers, precio_oferta):
    if not sellers or len(sellers) < 2:
        return None
    if not all(sl.get("url") for sl in sellers):
        return None
    con_precio = [sl for sl in sellers if sl.get("price") is not None]
    if not con_precio:
        return None
    mejor = min(con_precio, key=lambda sl: sl["price"])
    if precio_oferta is not None and mejor["price"] >= precio_oferta:
        return None
    barato = {"price": mejor["price"]}
    if mejor.get("shippingFee") is not None:
        barato["shippingFee"] = mejor["shippingFee"]
    # El precio de lista DE ESE VENDEDOR (no el de la publicación entera):
    # sin él, la ficha marcaba el descuento y la fila del listado no, para el
    # mismo producto y el mismo precio. Son 71 ofertas.
    if mejor.get("listPrice"):
        barato["listPrice"] = mejor["listPrice"]
    return barato


def _mover_campos_de_producto(product, light, detail):
    """Pasa DETAIL_PRODUCT_FIELDS de `light` a `detail` (prefijados con _)."""
    for field in DETAIL_PRODUCT_FIELDS:
        if product.get(field) is not None:
            detail["_" + field] = light.pop(field)


# VTEX (Elektra, Chedraui, Martí, Whirlpool) cuelga de cada imagen un
# "?v=6391549575..." que solo sirve para que el navegador de la tienda no la
# cachee de más. La imagen se sirve idéntica sin él (se comprobó con curl en
# vteximg.com.br y en vtexassets.com),
# y son 22 caracteres que no comprimen -- medidos, el 11% del peso gzip de
# la shard de Muebles. Se quita al guardar, así vale para lo que ya está en
# el catálogo y para lo que importe cualquier script de aquí en adelante.
_VERSION_VTEX_RE = re.compile(r"\?v=\d+$")


def _sin_version_vtex(url):
    if isinstance(url, str) and ("vteximg.com.br/" in url or "vtexassets.com/" in url):
        return _VERSION_VTEX_RE.sub("", url)
    return url


def _fotos_sin_version(product):
    if product.get("photo"):
        product["photo"] = _sin_version_vtex(product["photo"])
    for o in product.get("offers") or []:
        if o.get("photo"):
            o["photo"] = _sin_version_vtex(o["photo"])
    for v in product.get("colorVariants") or []:
        if v.get("photo"):
            v["photo"] = _sin_version_vtex(v["photo"])
        for o in v.get("offers") or []:
            if o.get("photo"):
                o["photo"] = _sin_version_vtex(o["photo"])


def _split_detail(product):
    """Devuelve (producto_para_el_navegador, detalle) separando los campos
    que solo hace falta bajar al abrir la ficha."""
    _fotos_sin_version(product)
    offers = product.get("offers") or []
    specs = product.get("specs") or []
    specs_pesadas = [s for s in specs if s.get("label") not in SPEC_LABELS_EN_LISTADO]
    if not offers:
        # Aun sin ofertas que aligerar, la ficha técnica sí se puede mover.
        light = dict(product)
        detail = {}
        if specs_pesadas:
            detail["_specs"] = specs
            light["specs"] = [s for s in specs if s.get("label") in SPEC_LABELS_EN_LISTADO]
            if not light["specs"]:
                light.pop("specs", None)
        _mover_campos_de_producto(product, light, detail)
        if not detail:
            return product, None
        return light, detail
    campos = (
        DETAIL_OFFER_FIELDS_CON_VARIANTES if product.get("colorVariants")
        else DETAIL_OFFER_FIELDS
    )
    detail = {}
    light_offers = []
    for i, o in enumerate(offers):
        light = o
        for field in campos:
            if o.get(field) is not None:
                if light is o:
                    light = dict(o)
                detail.setdefault(field, {})[str(i)] = light.pop(field)
        # Los vendedores acaban de irse al detalle: queda su precio mínimo,
        # que es lo único que el listado necesita de ellos (ver
        # _vendedor_mas_barato).
        if "sellers" in campos and o.get("sellers"):
            barato = _vendedor_mas_barato(o["sellers"], o.get("price"))
            if barato:
                if light is o:
                    light = dict(o)
                light["cheapestSeller"] = barato
        light_offers.append(light)
    if specs_pesadas:
        detail["_specs"] = specs
    light_product = dict(product)
    _mover_campos_de_producto(product, light_product, detail)
    if not detail:
        return product, None
    light_product["offers"] = light_offers
    if specs_pesadas:
        ligeras = [s for s in specs if s.get("label") in SPEC_LABELS_EN_LISTADO]
        if ligeras:
            light_product["specs"] = ligeras
        else:
            light_product.pop("specs", None)
    return light_product, detail


# Los ids de producto NO se reciclan. Vivían copiados en tres importadores;
# el cuarto (add_elektra_products.py) se los perdió y volvió a calcular el id
# como max(los que hay hoy) + 1, que es justo el error que esto arregla.
#
# Si un producto se da de baja --refresh_prices.py poda las publicaciones que
# Mercado Libre retira, merge_by_url.py junta fichas repetidas, y alguna vez
# se borra a mano-- su id quedaba libre y el alta siguiente se lo llevaba.
# Pasó de verdad con p125291. Lo que rompe no se ve de inmediato:
#
#   - /producto/pNNN/ ya está indexada por Google apuntando al primero.
#   - Los favoritos y el historial de la cuenta guardan ids (Firestore).
#   - data/hist/ guarda la serie de precios por id: dos productos distintos
#     terminarían compartiendo una sola serie.
#
# Por eso el máximo histórico se guarda en data.json (meta.maxProductId) y el
# id siguiente sale de ahí, no de lo que hay hoy en el catálogo.
def next_id(products, data=None):
    """Primer id libre, y NUNCA uno que ya se haya usado."""
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


# ---------------------------------------------------------------------------
# Texto: una sola manera de quitar acentos en todos los scripts.
#
# Vivía copiada ocho veces (norm, _norm) con dos formas Unicode distintas, NFD
# y NFKD, que NO son equivalentes sobre este catálogo -- medido sobre los
# 80,932 productos:
#
#   NFKD arregla   "13p³" -> "13p3" (14 refrigeradores sin faceta de pies³),
#                  "65¨pulgadas" -> '65"pulgadas' (2 televisores sin tamaño),
#                  y los espacios duros (U+00A0/U+202F) que hay en 5,112 títulos.
#   NFKD rompe     "FreeSync™" -> "freesynctm" (111 productos en audit_cross_store),
#                  "Nintendo Switch™ 2" pierde la plataforma,
#                  y '⅜"' -> '3⁄8"' que se lee como 8 pulgadas.
#
# Así que no se usa ninguna de las dos a secas: NFD (que deja ™ y ⅜ como
# símbolos aparte, que es lo que conviene) más esta tabla con lo que NFKD sí
# resolvía bien. Contra lo que había, cambia exactamente los 16 casos buenos y
# ninguno malo (ver el commit que la trajo).
_TABLA_SIMBOLOS = str.maketrans({
    "\u00a0": " ", "\u202f": " ", "\u2009": " ",   # espacios duros y finos
    "²": "2", "³": "3",                              # superíndices
    "¨": '"', "\u2033": '"', "\u201d": '"', "\u201c": '"',   # "pulgadas"
    "\u2032": "'", "\u2019": "'", "\u2018": "'",
})


def sin_acentos(s):
    """Minúsculas y sin acentos, conservando puntuación y símbolos."""
    s = unicodedata.normalize("NFD", (s or "").translate(_TABLA_SIMBOLOS))
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def texto_plano(s):
    """sin_acentos() y además todo lo que no es letra o dígito pasa a UN
    espacio: para comparar palabras, no para leer medidas con punto."""
    return re.sub(r"[^a-z0-9]+", " ", sin_acentos(s)).strip()


# ---------------------------------------------------------------------------
# Capacidad en mAh: una sola lectura para las dos categorías que la usan.
#
# Vivía escrita dos veces --buckets_mah en clasificar_subcategorias.py y
# tramo_mah en classify_cargadores.py-- y ninguna de las dos leía el separador
# de miles, que en este catálogo aparece de tres formas: "27,600mAh",
# "10.000 mAh" y "25 000 mAh". Como texto_plano convierte coma y punto en
# espacio, un "\d{3,6}" leía "27 600mah" como 600 mAh: un power bank de 27,600
# terminaba en el tramo "Hasta 10,000 mAh", que es justo el filtro de quien
# busca uno chico. Nueve productos estaban así.
#
# El grupo de miles solo se junta si el primer número arranca palabra. Sin esa
# condición, "Estuche para Galaxy Buds Live SM-R180 600 mAh" se leía como
# 180,600 mAh: el "180" es del modelo SM-R180 y la capacidad son 600 mAh. Con
# ella, "180" queda descartado por venir pegado a la "r" y se lee el 600.
_CAPACIDAD_MAH = re.compile(
    r"(?<![a-z0-9])(\d{1,3}(?: \d{3})+|\d{3,6}) ?m ?ah\b"
)
# Más allá de esto no es una capacidad, es un número mal leído.
MAH_MAXIMO = 500000


def capacidad_mah(nombre):
    """Los mAh que declara el título, o None si no declara ninguno."""
    m = _CAPACIDAD_MAH.search(texto_plano(nombre))
    if not m:
        return None
    valor = int(m.group(1).replace(" ", ""))
    return valor if 0 < valor <= MAH_MAXIMO else None


# 10,000 justo va en "Hasta 10,000 mAh": es lo que dice la etiqueta y es donde
# estaban los 36 que ya había clasificados a mano.
def tramo_mah(nombre):
    """La subcategoría de baterías portátiles que le toca al título."""
    mah = capacidad_mah(nombre)
    if mah is None:
        return None
    if mah <= 10000:
        return "Hasta 10,000 mAh"
    if mah <= 20000:
        return "10,000 a 20,000 mAh"
    return "Más de 20,000 mAh"


# ---------------------------------------------------------------------------
# Ids de producto.
def id_num(product):
    """El número del id ("p123" -> 123). Sin número, al final de cualquier orden."""
    m = re.match(r"p(\d+)$", product.get("id", ""))
    return int(m.group(1)) if m else 10**9


# ---------------------------------------------------------------------------
# Checkpoints de scripts largos (confirm_gtins, audit_gtin_matches): un json
# que se reescribe cada tantos productos para poder retomar.
def cargar_checkpoint(ruta):
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def guardar_checkpoint(ruta, estado):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=0, sort_keys=True)
    os.replace(tmp, ruta)  # atómico: nunca queda un json a medio escribir


# ---------------------------------------------------------------------------
# Enlaces de afiliado (Admitad envuelve la url real en ?ulp=).
def url_afiliado(base, target_url):
    """Envuelve target_url en el enlace de afiliado `base`; sin base, tal cual."""
    if not base:
        return target_url
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}ulp={urllib.parse.quote(target_url, safe='')}"


def url_real(offer_url):
    """La url de la tienda que hay dentro de un enlace de afiliado (ulp=), sin
    disparar la redirección. None si el enlace no es de afiliado."""
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(offer_url or "").query)
    ulp = qs.get("ulp", [None])[0]
    return urllib.parse.unquote(ulp) if ulp else None


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
                # "_algo" es un campo del PRODUCTO (_specs, _mlQuery), no un
                # mapa índice-de-oferta -> valor.
                if field.startswith("_"):
                    p[field[1:]] = by_index
                    continue
                for idx, value in by_index.items():
                    i = int(idx)
                    if i < len(p.get("offers") or []):
                        p["offers"][i][field] = value
    # cheapestSeller es un derivado de `sellers` que solo existe para la
    # shard (ver _vendedor_mas_barato): con el catálogo ya completo sobra, y
    # se recalcula solo en el próximo save_catalog.
    for p in products:
        for o in p.get("offers") or []:
            o.pop("cheapestSeller", None)

    manifest["products"] = products
    for key in (
        "productFiles", "detailFiles", "categoryFiles", "totalProducts",
        "categoryStats", "homePools", "indexFile", "homeFile",
    ):
        manifest.pop(key, None)
    return manifest


def _write(fname, payload):
    """Escribe el archivo SOLO si su contenido cambió.

    Importa desde que hay una corrida automática de precios (ver
    .github/workflows/refresh-prices.yml): save_catalog reescribe las 49
    shards de categoría en cada corrida, y si se reescriben todas aunque no
    haya cambiado nada, cada corrida mete ~5 MB de blobs nuevos en el
    historial de git -- varios GB al año por precios que casi siempre son
    los mismos. Comparando antes de escribir, el commit de cada corrida
    toca solo las categorías donde de verdad se movió un precio.
    """
    path = os.path.join(ROOT, fname)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    body = json.dumps(payload, **COMPACT)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            if f.read() == body:
                return
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)


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
