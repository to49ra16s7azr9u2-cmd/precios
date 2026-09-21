"""El catálogo de Coppel sale de su propio sitemap, no de una API.

POR QUÉ NO ES COMO CHEDRAUI Y MARTÍ
-----------------------------------
Las tiendas de vtex_stores.py contestan `/api/catalog_system/pub/products/
search`, la API pública del motor VTEX: una llamada devuelve cincuenta
productos con precio, existencia, marca, foto, ficha técnica y EAN. Coppel
no corre sobre VTEX --esa ruta contesta 404-- y su API interna es
`/graphql`, que su robots.txt prohíbe expresamente:

    # API interna -- no indexable
    Disallow: /graphql

De dónde sale entonces el catálogo: del sitemap que Coppel publica para los
buscadores. `https://www.coppel.com/sitemap.xml` es un índice; de ahí cuelga
`/l/sitemap/sitemap-pdp.xml`, que es otro índice con 47 archivos, uno por
familia de producto. Medido el 21 de septiembre de 2026: 669,056 urls de
producto, todas de la forma `https://www.coppel.com/pdp/<slug>-pm-<id>`.

Que `/pdp/` se puede leer lo dice el mismo robots.txt. Prohíbe `/p/*` y
`/c/*` --la navegación facetada, que genera infinitas urls repetidas-- pero
`/pdp/` no empieza por `/p/`: son rutas distintas, y las fichas de producto
son justamente lo que Coppel quiere que un buscador lea. Por eso están en el
sitemap.

De cada ficha se lee el bloque JSON-LD `@type: Product` que Coppel pone para
los buscadores: nombre, marca, foto, sku, precio, moneda y existencia. Es el
mismo dato que la tienda le da a Google, leído de la misma manera.

EL SITEMAP ESTÁ VIEJO
---------------------
Dice "Última actualización: 10 de Septiembre 2025". En ese año largo se le
cayeron del catálogo muchas de las fichas que sigue listando: a cerca de una
de cada cinco urls, Coppel contesta 302 a la portada. cosechar_coppel.py las
anota en data/coppel/fallidas.txt y no las vuelve a pedir.

Dos cosas que se siguen de ahí. La primera: eso NO es un bloqueo por país
--la respuesta trae "set-cookie: ak_geo=US", pero esa cookie viene en todas,
también en las que sí devuelven la ficha; diez urls sacadas de una página de
categoría viva contestan diez-- así que no hay nada que arreglar con una IP
mexicana. La segunda, y esta sí importa: si el sitemap tiene un año, también
le FALTA lo que Coppel empezó a vender desde entonces. Las páginas de
categoría (/ct/...) sí están al día, pero sirven diecisiete productos cada
una y el resto lo piden por /graphql, que su robots.txt prohíbe. Por ahora
el sitemap es la única enumeración completa que la tienda publica.

QUÉ NO TRAE
-----------
EAN/GTIN. Las tiendas VTEX lo dan y por eso sus productos se cruzan con los
de Mercado Libre por código de barras (match_by_gtin.py). Acá no hay: el
cruce de Coppel tiene que apoyarse en marca + nombre
(merge_amazon_cross_store.py), que acierta menos. Es la limitación real de
esta fuente y conviene tenerla presente al revisar las fusiones.

QUÉ FAMILIAS ENTRAN
-------------------
Las que el sitio compara. Coppel es en buena parte una tienda de ropa,
zapatos, perfumería y muebles de sala: de sus 669,056 fichas, las familias
de abajo son ~350,000. El criterio es el mismo que se fijó con Elektra y se
repitió con Chedraui y Martí (ver vtex_stores.py): nada de ropa, calzado,
perfumería ni consumibles, porque no hay categoría del sitio donde se
comparen.
"""
import re
import urllib.parse

SITEMAP_INDICE = "https://www.coppel.com/l/sitemap/sitemap-pdp.xml"

# La segunda fuente, y la que está al día. Son 2,019 páginas de categoría
# (1,995 de ellas hojas), con los mismos nombres de familia en el primer
# tramo de la ruta que los archivos del sitemap de producto. Cada hoja sirve
# diecisiete fichas en el HTML; el resto de su lista lo pide por /graphql,
# que el robots.txt prohíbe, y los parámetros de paginación (?pageSize=,
# ?fromPage=) también están prohibidos. O sea: no sustituye al sitemap de
# producto, pero es lo único que trae lo que Coppel empezó a vender después
# de septiembre de 2025.
SITEMAP_CATEGORIAS = "https://www.coppel.com/l/sitemap/sitemap-categorias.xml"

# Las familias del sitemap de Coppel que sí se importan, con la categoría del
# sitio que se usa como PISTA cuando el clasificador por nombre no decide.
# Las que están comentadas existen y se dejan nombradas a propósito: así se
# ve que fueron consideradas y descartadas, no olvidadas.
FAMILIAS = {
    "celulares":                 "Celulares",
    "electronica":               None,   # mezcla: decide el nombre
    "cocina-electrodomesticos":  "Electrodomésticos",
    "linea-blanca":              None,   # lavadoras, refris, estufas: por nombre
    "consolas-videojuegos":      "Videojuegos",
    "ferreteria-mejoras-hogar":  "Herramientas",
    "hogar-muebles":             "Muebles",
    "salas-recamaras-comedores": "Muebles",
    "juguetes":                  "Juguetes y bebés",
    "bebes":                     "Juguetes y bebés",
    "mascotas":                  "Mascotas",
    "bicicletas":                "Autos, bicicletas y motos",
    "motos-movilidad":           "Autos, bicicletas y motos",
    "automotriz":                "Refacciones",
    "deportes":                  "Deportes y fitness",
    "instrumentos-musicales":    "Instrumentos musicales",
    "relojes-lentes-joyeria":    None,   # relojes sí, lentes no: por nombre
    "optica":                    None,   # lentes de sol y armazones: casi todo fuera
    # --- fuera a propósito ---------------------------------------------
    # "damas", "hombres", "mujeres", "ninos-adolecentes", "zapateria":
    #     ropa y calzado. 150,000 fichas que el sitio no compara.
    # "perfumes-cosmeticos": 129,000 fichas de consumible.
    # "libros-revistas-comics": el sitio tiene Libros, pero son 16,571
    #     fichas sin ISBN en el JSON-LD; sin código no hay con qué cruzarlas
    #     y entrarían todas como ficha de un solo vendedor.
    # "maletas-bolsas-mochilas": mismo criterio que Elektra (bolsas fuera).
}

# Las familias con las que conviene empezar: son donde el catálogo ya tiene
# productos con los que cruzar, así que cada ficha de Coppel que entre tiene
# posibilidades de convertirse en una SEGUNDA oferta de algo que ya está --
# que es lo que sirve a un comparador-- en vez de una ficha suelta más.
# Son ~84,000 fichas contra las ~350,000 de FAMILIAS entero.
PRIORITARIAS = [
    "celulares", "linea-blanca", "cocina-electrodomesticos",
    "consolas-videojuegos", "electronica", "deportes",
    "bicicletas", "instrumentos-musicales",
]

RE_PDP = re.compile(r"https://www\.coppel\.com/pdp/[^\s<>\"]+")
RE_ID = re.compile(r"-pm-(\d+)$")
RE_CT = re.compile(r"https://www\.coppel\.com/ct/[^\s<>\"]+")
# En la página de categoría los enlaces vienen relativos.
RE_PDP_RELATIVA = re.compile(r"/pdp/[a-z0-9\-]+-pm-\d+")


def familia_de_categoria(url_ct):
    """'https://www.coppel.com/ct/electronica/tablets/cat000068' -> 'electronica'."""
    try:
        return url_ct.split("/ct/", 1)[1].split("/")[0]
    except IndexError:
        return ""


def familia_de(url_sitemap):
    """'…/l/sitemap/ferreteria-mejoras-hogar2.xml' -> 'ferreteria-mejoras-hogar'.

    Las familias grandes se parten en varios archivos numerados; el número
    no es parte del nombre.
    """
    base = urllib.parse.urlparse(url_sitemap).path.rsplit("/", 1)[-1]
    base = base[:-4] if base.endswith(".xml") else base
    return re.sub(r"\d+$", "", base)


def id_de(url_pdp):
    """El id de producto que Coppel pone al final de la url ('…-pm-5002363')."""
    m = RE_ID.search(urllib.parse.urlparse(url_pdp).path)
    return m.group(1) if m else None
