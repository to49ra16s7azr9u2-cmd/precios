"""Las tiendas que publican su catálogo entero en JSON por una ruta abierta:
Shopify (`/products.json`) y WooCommerce (`/wp-json/wc/store/products`).

POR QUÉ
-------
Después de VTEX (vtex_stores.py) esta es la segunda plataforma que se repite
entre las tiendas mexicanas, y la más barata de leer: no hay API de catálogo
que descubrir ni árbol de categorías que mapear a mano, porque el propio JSON
trae el tipo de producto y las etiquetas que la tienda le puso. De 65
dominios probados, seis contestan con productos de verdad por una de estas
dos rutas.

Igual que con VTEX, lo que cambia por tienda vive acá y el importador
(add_json_products.py) es uno solo.

QUÉ ENTRA Y QUÉ NO
------------------
El mismo criterio que rige a Elektra, Chedraui y Martí: nada de ropa ni
calzado, ni consumibles (alimentos, cosméticos, papelería, limpieza), ni
bolsas ni mochilas. Por eso de Fantasías Miguel no entra la mercería y de
Oggi no entra nada: es una tienda de jeans y el sitio no compara ropa. Se
deja registrada igual, con el mapa vacío, para no volver a probarla.

CÓMO SE CLASIFICA
-----------------
Shopify da `product_type` y `tags`; WooCommerce da `categories[].name`. Los
dos son texto de la tienda, no un id estable, así que el mapa es de
expresión regular a (categoría, subcategoría, icono) o a una función
nombre -> tupla | None, como en VTEX. El primero que engancha gana, y lo que
no engancha con nada se descarta: heredar una categoría por descarte sería
adivinar.
"""
import re

from add_elektra_products import (  # noqa: E402
    cat_audio, cat_bano, cat_celulares, cat_computo_accesorios,
    cat_electrodomesticos, cat_juguetes, cat_muebles,
    cat_telefonia_accesorios, cat_tv, norm,
)


def fijo(categoria, subcategoria, icono):
    return (categoria, subcategoria, icono)


# ---------------------------------------------------------------------------
# Maskota (maskota.com.mx, Shopify): todo para mascotas
# ---------------------------------------------------------------------------
# El alimento y las medicinas quedan fuera por consumibles, que es la misma
# regla que deja el súper de Chedraui afuera. Entra el objeto duradero: la
# cama, la transportadora, el comedero, el juguete, la correa y el arenero,
# que son justo las subcategorías que el sitio ya tiene en Mascotas.

def mk_mascotas(name):
    n = norm(name)
    if any(k in n for k in ("alimento", "croqueta", "snack", "premio", "suplemento",
                            "shampoo", "medicamento", "pipeta", "desparasit", "vitamina",
                            "pañal", "toallita", "arena para gato ", "arena aglutinante")):
        return None
    if "transportadora" in n or "canil" in n or "jaula" in n:
        return "Mascotas", "Transportadoras", "paw"
    if "cama" in n or "colchoneta" in n or "tapete" in n:
        return "Mascotas", "Camas", "paw"
    if "casa" in n or "caseta" in n:
        return "Mascotas", "Casas para mascotas", "paw"
    if "bebedero" in n or "fuente de agua" in n:
        return "Mascotas", "Bebederos", "paw"
    if "comedero" in n or "plato" in n or "tazon" in n or "dispensador" in n:
        return "Mascotas", "Comederos", "paw"
    if "correa" in n or "arnes" in n or "collar" in n or "pechera" in n:
        return "Mascotas", "Correas", "paw"
    if "arenero" in n or "caja de arena" in n or "sanitario" in n:
        return "Mascotas", "Areneros", "paw"
    if "juguete" in n or "pelota" in n or "mordedera" in n or "rascador" in n:
        return "Mascotas", "Juguetes", "paw"
    return None


MASKOTA = {r".*": mk_mascotas}


# ---------------------------------------------------------------------------
# Gonher (gonher.com.mx, WooCommerce): filtros y refacciones de auto
# ---------------------------------------------------------------------------
# Gonher es fabricante de filtros. Lo que vende es refacción de auto, que el
# sitio ya tiene en Refacciones / Para autos. El aceite y los aditivos no
# entran: son consumibles.

def gh_auto(name):
    n = norm(name)
    if any(k in n for k in ("aceite", "aditivo", "lubricante", "anticongelante",
                            "liquido de frenos", "grasa", "limpiador", "spray")):
        return None
    return "Refacciones", "Para autos", "gear"


GONHER = {r".*": gh_auto}


# ---------------------------------------------------------------------------
# Doto (doto.com.mx, Shopify): tienda de tecnología
# ---------------------------------------------------------------------------
# El primer intento clasificaba por el NOMBRE, encadenando los categorizadores
# de Elektra hasta que alguno contestara. Salió mal: cat_celulares es el último
# y contesta casi siempre, así que entraron tarjetas madre, perfumes, juegos de
# Switch y hasta un refrigerador como "Celulares / Android" -- 1,403 de 2,159
# productos mal puestos.
#
# Doto sí publica una taxonomía propia en product_type, con la forma
# "Computadoras;Componentes;Tarjeta madre;AMD". Eso es lo que se mapea acá: es
# lo que la tienda afirma del producto, no lo que se adivina del título. Lo que
# no engancha con ninguna entrada se descarta, que es la regla de este módulo.

def dt_sub(name, opciones, defecto=None):
    """La primera opción (regex, subcategoría) que aparezca en el nombre."""
    n = norm(name)
    for rx, sub in opciones:
        if re.search(rx, n):
            return sub
    return defecto


def dt_laptop(name):
    return ('Laptops', dt_sub(name, [(r'gamer|gaming|nitro|victus|rog\b|tuf\b', 'Gamer')],
                              'Oficina'), 'laptop')


def dt_almacenamiento(name):
    n = norm(name)
    if 'ssd' in n or 'estado solido' in n:
        return ('Almacenamiento', 'SSD', 'storage')
    if 'externo' in n or 'portatil' in n:
        return ('Almacenamiento', 'Externo', 'storage')
    return ('Almacenamiento', 'Interno', 'storage')


def dt_audifonos(name):
    n = norm(name)
    dia = 'diadema' in n or 'over ear' in n or 'on ear' in n
    # Los earbuds se venden por nombre de línea ("Galaxy Buds", "AirPods") sin
    # decir que son inalámbricos, que es lo que son.
    inal = ('inalambric' in n or 'bluetooth' in n or 'true wireless' in n
            or 'tws' in n or 'buds' in n or 'airpods' in n)
    if dia:
        return ('Audífonos', 'Diadema inalámbrica' if inal else 'Diadema con cable', 'headphones')
    return ('Audífonos', 'Earbuds inalámbricos' if inal else 'Earbuds con cable', 'headphones')


def dt_cocina(name):
    """La ruta "Licuadoras y Cafeteras" junta dos aparatos distintos."""
    n = norm(name)
    if 'cafetera' in n or 'espresso' in n or 'cafe' in n:
        return ('Cafeteras', None, 'coffee')
    if 'licuadora' in n:
        return ('Electrodomésticos', 'Licuadoras', 'appliance')
    return ('Electrodomésticos', 'Pequeños electrodomésticos de cocina', 'appliance')


def dt_horno(name):
    n = norm(name)
    if 'freidora' in n or 'air fryer' in n:
        return ('Electrodomésticos', 'Freidoras de aire', 'appliance')
    if 'microondas' in n:
        return ('Electrodomésticos', 'Microondas', 'appliance')
    return ('Electrodomésticos', 'Hornos', 'appliance')


def dt_lavadora(name):
    n = norm(name)
    if 'lavasecadora' in n:
        return ('Lavadoras', 'Lavasecadoras', 'washer')
    if 'secadora' in n:
        return ('Lavadoras', 'Secadoras', 'washer')
    if 'carga frontal' in n:
        return ('Lavadoras', 'Carga frontal', 'washer')
    return ('Lavadoras', 'Carga superior', 'washer')


def dt_celular(name):
    n = norm(name)
    return ('Celulares', 'iPhone' if 'iphone' in n else 'Android', 'phone')


def dt_tv(name):
    n = norm(name)
    return ('Televisores', '4K' if '4k' in n or 'uhd' in n else 'HD', 'tv')


# El orden manda: lo específico antes que lo general, porque el primero que
# engancha gana. Las rutas se comparan ya normalizadas (sin acentos, en
# minúsculas), por eso acá van sin acentos.
DOTO = {
    r'computadoras;laptops': dt_laptop,
    r'computadoras;monitores': fijo('Monitores', None, 'monitor'),
    r'computadoras;escritorio': fijo('Computadoras de escritorio', 'Torre', 'desktop'),
    r'computadoras;componentes;almacenamiento': dt_almacenamiento,
    r'computadoras;componentes;memoria': fijo('Componentes y accesorios de PC', 'Memoria RAM', 'cpu'),
    r'computadoras;(componentes|tarjeta de video|tarjeta madre|procesadores)':
        fijo('Componentes y accesorios de PC', 'Componentes', 'cpu'),
    r'computadoras;accesorios;audifonos': dt_audifonos,
    r'computadoras;(accesorios|perifericos)': fijo('Componentes y accesorios de PC', 'Accesorios', 'cpu'),
    r'computadoras;impresion': fijo('Impresoras', None, 'printer'),
    r'tablets?': fijo('Tabletas', None, 'tablet'),
    # Las fundas y micas no se comparan acá, igual que en el resto del sitio.
    r'celulares;accesorios': None,
    r'(celulares;smartphones|reacondicionados;celulares)': dt_celular,
    r'smart tv|televisiones': dt_tv,
    r'audio;bocinas': fijo('Bocinas', None, 'speaker'),
    r'audio;audifonos': dt_audifonos,
    r'gadgets;smartwatch': fijo('Relojes inteligentes', 'Smartwatches', 'watch'),
    r'videojuegos;consolas': fijo('Videojuegos', 'Consolas', 'gamepad'),
    r'videojuegos;juegos': fijo('Videojuegos', 'Software', 'gamepad'),
    r'videojuegos': fijo('Videojuegos', 'Accesorios', 'gamepad'),
    r'juguetes': fijo('Juguetes y bebés', 'Otros', 'toy'),
    r'linea blanca;lavadoras': dt_lavadora,
    r'linea blanca;refrigeradores': fijo('Refrigeradores', 'Refrigeradores', 'fridge'),
    r'linea blanca;estufas': fijo('Electrodomésticos', 'Estufas', 'appliance'),
    r'electrodomesticos;licuadoras y cafeteras': dt_cocina,
    r'electrodomesticos;hornos y freidoras': dt_horno,
    r'electrodomesticos;aspiradoras': fijo('Aspiradoras', None, 'vacuum'),
    r'electrodomesticos;extractores y exprimidores':
        fijo('Electrodomésticos', 'Extractores de jugo', 'appliance'),
}


# ---------------------------------------------------------------------------
# Refacciones Originales (refaccionesoriginales.mx, Shopify)
# ---------------------------------------------------------------------------

def ro_auto(name):
    n = norm(name)
    if any(k in n for k in ("aceite", "aditivo", "lubricante", "anticongelante", "grasa")):
        return None
    return "Refacciones", "Para autos", "gear"


REFACCIONES_ORIGINALES = {r".*": ro_auto}


# ---------------------------------------------------------------------------
# Fantasías Miguel (fantasiasmiguel.com, Shopify): manualidades
# ---------------------------------------------------------------------------
# Casi todo su catálogo es mercería y material de manualidades, que es
# consumible y no se compara acá. Entra lo poco que es objeto duradero con
# categoría propia: marcos, espejos, lámparas y organizadores.

def fm_deco(name):
    n = norm(name)
    if "lampara" in n or "luz led" in n or "serie de luces" in n:
        return "Iluminación", "Lámparas de escritorio", "bulb"
    if "espejo" in n:
        return "Decoración de hogar y jardín", "Otros", "box"
    if "organizador" in n or "caja organizadora" in n:
        return "Otros", "Organización del hogar", "box"
    if "jarron" in n or "florero" in n:
        return "Decoración de hogar y jardín", "Jarrones", "box"
    if "vela" in n:
        return "Decoración de hogar y jardín", "Velas", "box"
    return None


FANTASIAS_MIGUEL = {r".*": fm_deco}


# ---------------------------------------------------------------------------
# Registro
# ---------------------------------------------------------------------------

TIENDAS_JSON = {
    "maskota": {
        "nombre": "Maskota",
        "dominio": "www.maskota.com.mx",
        "plataforma": "shopify",
        "categorias": MASKOTA,
        "store": {"id": "maskota", "name": "Maskota", "hubRegion": None,
                  "color": "#00A0DF", "logo": "MK", "typicalShippingDays": [3, 8], "logoImg": "icons/stores/maskota.png"},
    },
    # Gonher contesta la ruta de WooCommerce, pero es el catálogo del
    # fabricante y no una tienda: los 72 productos vienen con precio 0 y casi
    # todos son aceites y fluidos, que además son consumibles. Se deja
    # registrada con el mapa para no volver a probarla, pero no se importa.
    "gonher": {
        "nombre": "Gonher",
        "sin_precios": True,
        "dominio": "www.gonher.com.mx",
        "plataforma": "woocommerce",
        "categorias": GONHER,
        "store": {"id": "gonher", "name": "Gonher", "hubRegion": None,
                  "color": "#0B5FA5", "logo": "GH", "typicalShippingDays": [4, 10]},
    },
    "doto": {
        "nombre": "Doto",
        "dominio": "www.doto.com.mx",
        "plataforma": "shopify",
        "categorias": DOTO,
        "store": {"id": "doto", "name": "Doto", "hubRegion": None,
                  "color": "#F03C2E", "logo": "DT", "typicalShippingDays": [3, 10]},
    },
    "refacciones_originales": {
        "nombre": "Refacciones Originales",
        "dominio": "www.refaccionesoriginales.mx",
        "plataforma": "shopify",
        "categorias": REFACCIONES_ORIGINALES,
        "store": {"id": "refacciones_originales", "name": "Refacciones Originales",
                  "hubRegion": None, "color": "#1F3A5F", "logo": "RO",
                  "typicalShippingDays": [4, 12]},
    },
    "fantasias_miguel": {
        "nombre": "Fantasías Miguel",
        "dominio": "www.fantasiasmiguel.com",
        "plataforma": "shopify",
        "categorias": FANTASIAS_MIGUEL,
        "store": {"id": "fantasias_miguel", "name": "Fantasías Miguel", "hubRegion": None,
                  "color": "#E4007C", "logo": "FM", "typicalShippingDays": [3, 9]},
    },
}


def resolver(mapping, texto_tienda, nombre):
    """La primera entrada cuyo patrón engancha con lo que la tienda dice del
    producto (product_type, tags o categoría). El valor puede ser la tupla
    fija o una función del nombre."""
    t = norm(texto_tienda or "")
    for patron, valor in mapping.items():
        if re.search(patron, t):
            return valor(nombre) if callable(valor) else valor
    return None
