#!/usr/bin/env python3
"""Genera páginas estáticas indexables (SEO) a partir de data/data.json.

Por qué existen estas páginas además de index.html
----------------------------------------------------
ComparaMEX es una SPA: todo el contenido (nombre de producto, precios,
specs, reseñas) se pinta con JavaScript después de cargar la página, con
rutas por hash (#/p/p1). Un buscador que no ejecute JS ve una página en
blanco, y aunque la ejecute, una URL con "#" no es una página distinta
para fines de indexación: todo el catálogo competiría por la única URL
"/". Kakaku.com, con quien se compara este proyecto, en cambio tiene una
URL real por producto — eso es a propósito lo que se replica aquí.

Este script genera una página HTML estática y autocontenida por producto
y por categoría, con el contenido ya renderizado en el HTML (visible sin
JS), metadatos (title/description/Open Graph) y datos estructurados
JSON-LD (schema.org Product). Cada página enlaza de vuelta a la SPA
interactiva (mapa de entrega, reseñas, gráfico de precio) para quien
llegue desde un buscador y quiera esa experiencia completa.

Cuándo correrlo
----------------
Cada vez que cambie data/data.json (nuevo producto, precio, tienda).
No es un paso de build obligatorio para que el sitio funcione -index.html
sigue sirviendo la app completa sin esto-, es un generador opcional que
crea contenido adicional para buscadores. Uso:

    python3 scripts/generate_seo_pages.py

Antes de desplegar a producción, edita SITE_URL más abajo con el dominio
real: un canonical o una URL de Open Graph apuntando a un dominio
equivocado (o a localhost) es peor para SEO que no tenerlas.
"""
import argparse
import collections
import datetime
import json
import os
import re
import shutil
import sys
import unicodedata
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, slugify  # noqa: E402
from familias_subcategorias import agrupar as agrupar_familias  # noqa: E402
from roles_subcategorias import ORDEN as ORDEN_ROLES, TITULOS as TITULOS_ROL, es_producto, rol_de  # noqa: E402
from web_summary import purchase_options, seller_rows, seller_total  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS_PATH = os.path.join(ROOT, "data", "icons.json")

SITE_URL = "https://comparamex.com"

# Mismo tag de Google Analytics (GA4) que index.html, para que las visitas
# que aterrizan directo en una página estática de producto/categoría desde
# el buscador (sin pasar por la SPA) también se cuenten.
#
# Estas páginas no tienen el aviso de cookies (viven fuera de la SPA, sin
# app.js) -- por defecto Consent Mode queda denegado, igual que en la SPA
# antes de que alguien responda al aviso, y solo se concede solo si ya
# había una elección guardada en localStorage de una visita anterior a la
# SPA (mismo origen, mismo storage). Un visitante nuevo que aterriza
# directo en una de estas páginas no se cuenta hasta que entre a la SPA y
# responda al aviso ahí.
GA_SNIPPET = """<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('consent', 'default', {
    'analytics_storage': 'denied',
    'ad_storage': 'denied',
    'ad_user_data': 'denied',
    'ad_personalization': 'denied'
  });
  try {
    if (localStorage.getItem('comparamexCookieConsent') === 'accepted') {
      gtag('consent', 'update', {
        'analytics_storage': 'granted',
        'ad_storage': 'granted',
        'ad_user_data': 'granted',
        'ad_personalization': 'granted'
      });
    }
  } catch (e) {}
</script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NZ0RG4S274"></script>
<script>
  gtag('js', new Date());
  gtag('config', 'G-NZ0RG4S274');
</script>"""

with open(ICONS_PATH, encoding="utf-8") as f:
    ICONS = json.load(f)


def svg_icon(key, cls=""):
    """Ilustración SVG en línea (data/icons.json), en vez de emoji, para que
    estas páginas estáticas usen el mismo set de iconos que la SPA (ver
    icon() en js/app.js)."""
    inner = ICONS.get(key) or ICONS["box"]
    css_class = f" {cls}" if cls else ""
    return f'<svg class="icon{css_class}" viewBox="0 0 24 24" aria-hidden="true">{inner}</svg>'

# Estas páginas cargaban css/style.css SIN minificar: 114 KB en vez de 56 KB,
# en las ~82 mil páginas, y son justo las que reciben la primera visita desde
# un buscador.
#
# A propósito NO llevan la huella de contenido (?v=<hash>) que index.html sí
# lleva: el hash cambia con cada retoque del CSS y eso reescribiría las 82 mil
# páginas --y las metería en el commit-- por un cambio de color. La portada,
# que es donde un cambio invisible sí molestó de verdad, la conserva (ver
# stampCacheBusting() en build.mjs); acá alcanza con el max-age de 10 minutos
# de GitHub Pages, porque a una ficha se llega desde Google una vez, no se
# vuelve a ella cada día.
CSS_HREF = "css/style.min.css"

# Antes esta nota decía "precios de referencia para propósitos de
# demostración". Iba en las ~82 mil fichas y es exactamente la clase de
# autodeclaración que un buscador lee como contenido de poco valor. Después
# decía "se actualizan automáticamente todos los días desde cada tienda", que
# tampoco es verdad para todo el catálogo: Amazon, AliExpress, Alibaba y
# otras tiendas chicas (3,128 productos) no tienen de dónde refrescarse y
# conservan el precio del día que se cargaron. Lo que sí hay que decir --que
# un precio puede cambiar entre la actualización y la compra-- se dice sin
# prometer una frecuencia.
# Nota de retraso. Va CHICA y en todos lados donde se enseñe un precio: la
# ficha, las listas por categoría y subcategoría, las páginas de marca y las
# de bajadas de precio. El precio que se publica es el que se guardó en la
# última pasada de refresh_prices.py, no el que la tienda tiene ahora mismo,
# y en las tiendas que no se pueden refrescar (Amazon y las chicas) es el
# del día que se cargaron. Decirlo una vez en el pie no alcanza: el que
# llega desde Google a una lista ve veinte precios antes de bajar hasta ahí.
NOTA_LAG = ("Los precios se toman de cada tienda y pueden llevar algunas "
            "horas de retraso.")
NOTA_LAG_HTML = f'<p class="nota-lag">{NOTA_LAG}</p>'

STORE_ORDER_NOTE = (
    "Los precios pueden cambiar en cualquier momento: confirma el precio "
    "final en la tienda antes de comprar. Para ver la comparación "
    "interactiva, con mapa de tiempos de entrega por municipio y reseñas, "
    "usa el enlace a la versión completa."
)




def money(n):
    return "$" + format(round(n), ",d")


def plural(n, singular, plural_form):
    """Mismo criterio que plural() en js/app.js: con casi todos los productos
    en una sola tienda, "1 tiendas" salía en cada ficha y cada ranking."""
    return f"{n} {singular if n == 1 else plural_form}"


def html_escape(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def store_by_id(data, store_id):
    return next(s for s in data["stores"] if s["id"] == store_id)


def min_price(product):
    """Precio "desde", contando las variantes de color.

    Leía solo product["offers"], que tras la fusión por color son solo las
    del color más barato AL MOMENTO de fusionar. Si después otro color bajó,
    el mínimo real vive en colorVariants y la ficha decía "desde $13,999" para
    un iPhone 16 que estaba a $13,749 en otro color (79 productos, medidos
    contra el mínimo real). purchase_options() ya sabe expandir los dos
    formatos de variante; se reutiliza en vez de repetir la regla.

    Y se mide sobre seller_rows(), no sobre purchase_options(): una
    publicación de catálogo de Mercado Libre puede traer varios vendedores,
    cada uno con SU precio y SU enlace, y la tabla de ofertas de esta misma
    página ya los abre en filas (ver seller_rows). Midiendo sobre
    purchase_options() la cabecera decía "desde $13,749" justo encima de una
    tabla cuya primera fila era $13,000 -- 627 productos con el precio de
    portada más caro que el que se paga al hacer clic. minPrice() en
    js/app.js siempre midió sobre sellerRows(); esto es lo mismo.
    """
    precios = [o["price"] for o in seller_rows(product) if o.get("price") is not None]
    if precios:
        return min(precios)
    precios = [o["price"] for o in purchase_options(product) if o.get("price")]
    return min(precios) if precios else min(o["price"] for o in product["offers"])


# Los campos que valen su default en TODO el catálogo (reviewCount=0,
# rating=null, reviews=[], ...) ya no se guardan en data/products-N.json
# -- ver scripts/trim_catalog.py. Acá se leen siempre con .get() y un
# default explícito: si faltan, el resultado tiene que ser el mismo que
# cuando estaban escritos.
def total_review_count(product):
    return sum(o.get("reviewCount") or 0 for o in product["offers"])


def seller_total(product):
    """Cuántos vendedores ofrecen el producto -- el mismo número que la SPA
    muestra como "N vendedores" (ver sellerTotal en js/app.js). Un producto
    de catálogo de Mercado Libre puede tener varios vendedores en una sola
    oferta; una ficha fusionada por color los tiene repartidos por variante.
    Se usa para desempatar el ranking (ver más abajo)."""
    return sum((o.get("sellerCount") or 1) for o in purchase_options(product))


def is_used(product):
    return any(
        s.get("label") == "Condición" and re.search(r"preowned|usado", s.get("value", ""), re.I)
        for s in product.get("specs", [])
    )


def aggregate_rating(product):
    total_reviews = sum(o.get("reviewCount") or 0 for o in product["offers"])
    if total_reviews == 0:
        return 0, 0
    weighted = sum((o.get("rating") or 0) * (o.get("reviewCount") or 0) for o in product["offers"])
    return round(weighted / total_reviews, 1), total_reviews


def product_photo_html(product, css_class="detail-icon"):
    """La foto del producto, o la ilustración de la categoría si no hay.

    Estas páginas mostraban SIEMPRE el SVG de la categoría, aunque el 99.9%
    del catálogo (80,632 de 80,697) tiene foto: ninguna ficha entraba en
    Google Imágenes y el JSON-LD quedaba sin `image`, que es obligatorio para
    que Google considere el resultado enriquecido de Producto.

    referrerpolicy="no-referrer" por lo mismo que renderProductMedia() en
    js/app.js: algunos CDN rechazan la carga por Referer.
    """
    foto = product.get("photo")
    if not foto:
        return f'<div class="{css_class}">{svg_icon(product.get("image", "box"))}</div>'
    # La foto grande de la ficha es el elemento más grande de la página (el
    # LCP que mide Google): con loading="lazy" el navegador la dejaba para
    # después del resto. Las miniaturas de las listas sí van diferidas. El
    # ancho y alto declarados sólo reservan la proporción (el css las lleva
    # al tamaño de su recuadro); sin ellos Lighthouse marca cada imagen.
    principal = css_class == "detail-icon"
    lado = 400 if principal else 56
    carga = 'fetchpriority="high"' if principal else 'loading="lazy"'
    return (
        f'<div class="{css_class} has-photo">'
        f'<img class="product-photo product-photo-detail" src="{html_escape(foto)}" '
        f'alt="{html_escape(product["name"])}" referrerpolicy="no-referrer" '
        f'width="{lado}" height="{lado}" {carga} decoding="async">'
        f'</div>'
    )


def page_shell(title, description, canonical_path, body, depth, extra_head="", robots="index, follow", og_image=None):
    """depth = niveles bajo la raíz del sitio (para las rutas relativas ../).

    depth=None es el caso del 404: GitHub Pages sirve /404.html como
    respuesta de CUALQUIER url mala, incluida /producto/loquesea/, y el
    navegador resuelve las rutas relativas contra ESA url, no contra la
    raíz. Con "css/style.min.css" la hoja de estilos se buscaba en
    /producto/loquesea/css/ y la página de error salía sin un solo estilo.
    Con la raíz absoluta funciona a cualquier profundidad.
    """
    prefijo = "/" if depth is None else "../" * depth
    prefix = prefijo
    canonical = f"{SITE_URL}{canonical_path}"
    # noai/noimageai va SIEMPRE, sin importar qué valor de robots use cada
    # llamador (index/follow normal, o noindex en alguna página puntual):
    # es una señal aparte, de entrenamiento de IA, no de indexado en
    # buscadores -- las dos cosas no deberían tener que decidirse juntas en
    # cada call site.
    robots_full = f"{robots}, noai, noimageai"
    # Una página noindex (el 404) no declara canonical: decir "la versión
    # buena de esto soy yo" en una página de error es contradictorio.
    canonical_tag = (
        "" if "noindex" in robots else f'<link rel="canonical" href="{canonical}">\n'
    )
    og_image_tag = (
        f'<meta property="og:image" content="{html_escape(og_image)}">\n' if og_image else ""
    )
    return f"""<!DOCTYPE html>
<html lang="es-MX">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html_escape(title)}</title>
<meta name="description" content="{html_escape(description)}">
<meta name="robots" content="{robots_full}">
{canonical_tag}
<meta property="og:type" content="{'product' if canonical_path.startswith('/producto/') else 'website'}">
<meta property="og:site_name" content="ComparaMEX">
<meta property="og:locale" content="es_MX">
<meta property="og:title" content="{html_escape(title)}">
<meta property="og:description" content="{html_escape(description)}">
<meta property="og:url" content="{canonical}">
{og_image_tag}<meta name="theme-color" content="#FF0211">
<!-- Las fotos salen de CDN de terceros. El preconnect adelanta el DNS + TLS
     de los dos que cubren casi todo el catálogo, que si no se pagan recién
     cuando el navegador encuentra el primer <img> -- y esa primera imagen es
     justo el elemento más grande de la página (el LCP que mide Google). -->
<link rel="preconnect" href="https://http2.mlstatic.com" crossorigin>
<link rel="preconnect" href="https://elektra.vteximg.com.br" crossorigin>
<link rel="icon" href="{prefix}icons/icon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" href="{prefix}icons/icon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="{prefix}icons/apple-touch-icon.png">
<link rel="stylesheet" href="{prefix}{CSS_HREF}">
{GA_SNIPPET}
{extra_head}
</head>
<body>
<header class="topbar">
  <div class="topbar-top">
    <div class="topbar-inner">
      <a class="brand" href="{prefix}">
        <img class="brand-icon" src="{prefix}icons/icon.svg" alt="" width="30" height="30">
        <span class="brand-mark">Compara<span class="brand-mx">MEX</span></span>
      </a>
    </div>
  </div>
</header>
<main class="container">
{body}
</main>
<footer class="site-footer">
  <div class="container">
    <p><a href="{prefijo}marca/">Todas las marcas</a> &middot; <a href="{prefijo}ofertas/">Ofertas de hoy</a></p>
    ComparaMEX — comparador de precios para México, para que compres sin arrepentimientos (colores inspirados en Mercari). Los precios pueden cambiar en cualquier momento. No tenemos relación comercial con las tiendas que comparamos; los enlaces de la sección «Marcas y ofertas» de la portada sí son de afiliado.
  </div>
</footer>
</body>
</html>
"""


def breadcrumb_json_ld(items):
    """items: lista de (nombre, url|None). url=None para el último elemento
    (la página actual no necesita item en BreadcrumbList)."""
    entries = []
    for i, (name, url) in enumerate(items, start=1):
        entry = {"@type": "ListItem", "position": i, "name": name}
        if url:
            entry["item"] = url
        entries.append(entry)
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": entries}
    return json.dumps(ld, ensure_ascii=False, indent=2)


def product_json_ld(product, data, canonical):
    avg, count = aggregate_rating(product)
    # seller_rows() y no purchase_options(): mismas filas que la tabla de
    # ofertas de la página y que min_price(), así el lowPrice que ve Google
    # es el mismo precio que ve el visitante. Con purchase_options() los
    # datos estructurados declaraban un precio MÁS ALTO que el visible, que
    # es justo lo que invalida el resultado enriquecido de Producto.
    opciones = [o for o in seller_rows(product) if o.get("price") is not None] or product["offers"]
    offers = [
        {
            "@type": "Offer",
            "url": canonical,
            "priceCurrency": "MXN",
            "price": o["price"],
            "availability": (
                "https://schema.org/InStock"
                if o.get("stock") == "in_stock"
                else "https://schema.org/LimitedAvailability"
                if o.get("stock") == "low_stock"
                else "https://schema.org/PreOrder"
            ),
            "seller": {"@type": "Organization", "name": store_by_id(data, o["storeId"])["name"]},
        }
        # Mismas opciones de compra que la tabla de la página: con las
        # variantes de color expandidas, no solo product["offers"].
        for o in opciones
    ]
    ld = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product["name"],
        "brand": {"@type": "Brand", "name": product["brand"]},
        "category": product["category"],
        "url": canonical,
        "offers": {
            "@type": "AggregateOffer",
            "priceCurrency": "MXN",
            "lowPrice": min(o["price"] for o in opciones),
            "highPrice": max(o["price"] for o in opciones),
            "offerCount": len(opciones),
            "offers": offers,
        },
    }
    # `image` es requisito de Google para el resultado enriquecido de
    # Producto: sin él la ficha no califica, por más completo que esté el
    # resto. Lo teníamos guardado y no lo declarábamos.
    if product.get("photo"):
        ld["image"] = product["photo"]

    # El código de barras es la señal más fuerte para que Google entienda que
    # nuestra ficha y la de otra tienda son el MISMO artículo. Solo se declara
    # el que Mercado Libre confirmó (scripts/confirm_gtins.py deja
    # product["gtin"]): el `ean` suelto de Elektra incluye consecutivos
    # internos de la tienda, y declarar uno equivocado haría que Google
    # fusionara nuestra ficha con otro producto -- peor que no declarar nada.
    gtin = str(product.get("gtin") or "")
    propiedad = {8: "gtin8", 12: "gtin12", 13: "gtin13", 14: "gtin14"}.get(len(gtin))
    if propiedad:
        ld[propiedad] = gtin

    if product.get("specs"):
        # Descripción a partir de la ficha técnica real. No se inventa texto:
        # son las mismas etiquetas y valores que se ven en la tabla.
        partes = [f"{sp['label']}: {sp['value']}" for sp in product["specs"][:6]]
        ld["description"] = f"{product['name']}. " + ". ".join(partes) + "."

    if count > 0:
        ld["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": avg,
            "reviewCount": count,
        }
    return json.dumps(ld, ensure_ascii=False, indent=2)


_POR_CAT_CON_PAGINA = {}


def related_products(product, all_products, n=4):
    """Mismos criterios que un bloque 'productos relacionados' de Kakaku:
    misma categoría, ordenados por cercanía de precio (no aleatorio), sin
    incluir el producto actual."""
    # El índice por categoría lo arma main() una sola vez. Sin él esta función
    # recorría el catálogo entero en CADA ficha: 19 mil páginas por 267 mil
    # productos. Si no está armado (uso suelto), cae al recorrido de siempre.
    candidatos = _POR_CAT_CON_PAGINA.get(product["category"]) if _POR_CAT_CON_PAGINA else None
    if candidatos is None:
        candidatos = [p for p in all_products if p["category"] == product["category"]]
    same_cat = [p for p in candidatos if p["id"] != product["id"]]
    price = min_price(product)
    same_cat.sort(key=lambda p: abs(min_price(p) - price))
    return same_cat[:n]


# ---------------------------------------------------------------- historial

# data/hist/<slug>-<n>.json, escrito por scripts/record_price_history.py.
# Se carga entero una vez (3.4 MB) en vez de por producto: son 82 mil fichas.
_HIST = None


def historial_de(product_id):
    global _HIST
    if _HIST is None:
        _HIST = {}
        carpeta = os.path.join(ROOT, "data", "hist")
        if os.path.isdir(carpeta):
            for nombre in os.listdir(carpeta):
                if not nombre.endswith(".json"):
                    continue
                try:
                    with open(os.path.join(carpeta, nombre), encoding="utf-8") as f:
                        _HIST.update(json.load(f))
                except (OSError, ValueError):
                    continue
    return _HIST.get(product_id) or {}


MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre")


def fecha_larga(dia):
    d = HIST_EPOCH + datetime.timedelta(days=dia)
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def serie_diaria(por_tienda, hasta=None):
    """[(día, precio mínimo entre tiendas)] día a día, sin huecos.

    El archivo guarda solo los cambios, así que para dibujar hay que arrastrar
    el último precio conocido de cada tienda hasta que cambie. Se arrastra
    hasta HOY, no hasta el último cambio: que un precio no se haya movido no
    significa que se dejara de mirar, y si la serie terminara en el último
    cambio la ficha diría "entre el 2 y el 7" cuando el 8 también se anotó.
    """
    # "_v" (qué vendedor ponía el mínimo) no es una tienda: se salta.
    cambios = {t: dict(zip(s[::2], s[1::2])) for t, s in por_tienda.items()
               if not t.startswith("_")}
    cambios = {t: c for t, c in cambios.items() if c}
    if not cambios:
        return []
    if hasta is None:
        hasta = (datetime.date.today() - HIST_EPOCH).days
    primero = min(min(c) for c in cambios.values())
    ultimo = max(hasta, max(max(c) for c in cambios.values()))
    vigente, salida = {}, []
    for dia in range(primero, ultimo + 1):
        for tienda, c in cambios.items():
            if dia in c:
                # null = la tienda dejó de vender ese día: sale del mínimo.
                if c[dia] is None:
                    vigente.pop(tienda, None)
                else:
                    vigente[tienda] = c[dia]
        if vigente:
            salida.append((dia, min(vigente.values())))
    return salida


MESES_CORTOS = ("ene", "feb", "mar", "abr", "may", "jun", "jul",
                "ago", "sep", "oct", "nov", "dic")


def fecha_corta(dia):
    d = HIST_EPOCH + datetime.timedelta(days=dia)
    return f"{d.day} {MESES_CORTOS[d.month - 1]}"


def dias_de_eje(d0, d1):
    """Hasta 4 fechas repartidas entre la primera y la última, sin repetir."""
    n = min(4, d1 - d0 + 1)
    if n <= 1:
        return [d0]
    dias = [round(d0 + (d1 - d0) * i / (n - 1)) for i in range(n)]
    return sorted(set(dias))


def precios_de_eje(lo, hi):
    """Tres marcas de precio (mínimo, medio, máximo), o una sola si no varió."""
    if hi <= lo:
        return [lo]
    return [lo, (lo + hi) / 2, hi]


def sparkline_svg(serie, ancho=560, alto=92):
    """Gráfico de la evolución, en SVG inline, con ejes.

    Sin JavaScript ni librería a propósito: estas páginas son estáticas y las
    ve un rastreador antes que una persona. Un <svg> se pinta igual con el
    JS apagado y no agrega ninguna petición.

    Lleva eje de precios a la izquierda (mínimo, medio, máximo) y de fechas
    abajo: sin ellos la línea era una forma sin escala y el lector tenía que
    deducir del texto de arriba cuánto valía cada tramo y de qué día era.
    Mismo dibujo que sparklineSvg() en js/app.js.
    """
    if len(serie) < 2:
        return ""
    precios = [p for _, p in serie]
    lo_real, hi_real = min(precios), max(precios)
    # Un respiro debajo del mínimo y encima del máximo: sin él, un tramo plano
    # al precio más bajo queda pegado al borde y el área sombreada no se ve.
    span = (hi_real - lo_real) or max(hi_real * 0.1, 1)
    lo = lo_real - span * 0.12
    hi = hi_real + span * 0.12
    span = hi - lo
    dias = [d for d, _ in serie]
    d0, d1 = dias[0], dias[-1]
    ancho_dias = (d1 - d0) or 1
    izq, der, arriba, abajo = 64, 24, 6, 18
    x0, x1 = izq, ancho - der
    y0, y1 = arriba, alto - abajo

    def x_de(d):
        return x0 + (d - d0) / ancho_dias * (x1 - x0)

    def y_de(p):
        return y0 + (1 - (p - lo) / span) * (y1 - y0)

    def xy(d, p):
        return f"{x_de(d):.1f},{y_de(p):.1f}"

    linea = " ".join(xy(d, p) for d, p in serie)
    area = f"{x0},{y1} " + linea + f" {x1:.1f},{y1}"
    ejes = []
    for p in precios_de_eje(lo_real, hi_real):
        y = y_de(p)
        ejes.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" class="spark-grid"/>')
        ejes.append(f'<text x="{x0 - 6}" y="{y + 3:.1f}" text-anchor="end" class="spark-label">{money(p)}</text>')
    for d in dias_de_eje(d0, d1):
        x = x_de(d)
        ejes.append(f'<line x1="{x:.1f}" y1="{y1}" x2="{x:.1f}" y2="{y1 + 4}" class="spark-tick"/>')
        ejes.append(f'<text x="{x:.1f}" y="{alto - 5}" text-anchor="middle" class="spark-label">{fecha_corta(d)}</text>')
    ejes.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" class="spark-axis"/>')
    ejes.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" class="spark-axis"/>')
    return (
        f'<svg class="price-spark" viewBox="0 0 {ancho} {alto}" '
        f'role="img" aria-label="Evolución del precio: de {money(precios[0])} a {money(precios[-1])}">'
        + "".join(ejes)
        + f'<polygon points="{area}" fill="rgba(255,2,17,.08)"/>'
        f'<polyline points="{linea}" fill="none" stroke="var(--red)" stroke-width="1.5" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
        f'</svg>'
    )


# Cuántos días tiene que haberse sostenido el precio anterior para creerle a
# una bajada. Un precio que aparece un solo día y desaparece es casi siempre
# un dato malo que se corrigió --Elektra publicó un juego de Xbox a $10,933--
# y anunciarlo como "88% de descuento" mandaría a la gente a una tienda donde
# no hay tal descuento. Una promoción de verdad dura.
DIAS_SOSTENIDO = 2

# Debajo de esto la bajada no vale una fila en un ranking.
BAJADA_MINIMA_PCT = 10.0


def vendedor_en(serie_v, dia):
    """Quién ponía el mínimo de la tienda el día `dia` según "_v", o None si
    el historial no lo sabe (no hay anotación de ese día ni de antes)."""
    quien = None
    visto = False
    for d, v in zip(serie_v[::2], serie_v[1::2]):
        if d > dia:
            break
        quien, visto = v, True
    return quien if visto else None


def bajada_de(product_id):
    """La mayor bajada VIGENTE de este producto, o None.

    (pct, tienda, precio_antes, precio_ahora, día_del_cambio)

    Se mide DENTRO de una misma tienda, nunca sobre el mínimo entre tiendas.
    Cuando a un producto se le suma una segunda tienda más barata, el mínimo
    cae de golpe, pero nadie bajó ningún precio: solo apareció otro vendedor.
    Medido así, el ranking se llenaba de "Minecraft bajó 93%" que en realidad
    era "Elektra lo tenía a $9,864 y ahora también está en Mercado Libre a
    $699".

    Y dentro de la tienda, de un MISMO vendedor. Lo mismo pasaba puertas
    adentro: en Mercado Libre un vendedor nuevo más barato en la misma
    publicación, y en Elektra el vaivén entre Elektra y un tercero del
    marketplace cuando a Elektra se le acaba la existencia. Se comprobaron
    contra las tiendas las 40 bajadas de 70% o más: 27 eran reales y 13 eran
    un cambio de vendedor (el precio "de antes" seguía ahí, de otro). Por eso
    se exige que quien tenía el precio de antes el día anterior a la bajada
    sea quien tiene el de ahora (ver "_v" en record_price_history.py). Si el
    historial no sabe quién era, no es una bajada: no se adivina.
    """
    mejor = None
    historial = historial_de(product_id) or {}
    vendedores = historial.get("_v") or {}
    for tienda, flat in historial.items():
        if tienda.startswith("_"):
            continue
        pares = list(zip(flat[::2], flat[1::2]))
        if len(pares) < 2:
            continue
        (dia_antes, antes), (dia_ahora, ahora) = pares[-2], pares[-1]
        # null al final = la tienda ya no lo vende: no hay bajada vigente.
        if ahora is None or antes is None or ahora >= antes or not antes:
            continue
        if dia_ahora - dia_antes < DIAS_SOSTENIDO:
            continue
        serie_v = vendedores.get(tienda) or []
        quien_antes = vendedor_en(serie_v, dia_ahora - 1)
        quien_ahora = vendedor_en(serie_v, dia_ahora)
        if quien_antes is None or quien_antes != quien_ahora:
            continue
        pct = 100 * (antes - ahora) / antes
        if pct < BAJADA_MINIMA_PCT:
            continue
        if mejor is None or pct > mejor[0]:
            mejor = (pct, tienda, antes, ahora, dia_ahora)
    return mejor


def render_price_history(product):
    """Panel de evolución del precio, o "" si todavía no hay dos puntos.

    Es la parte de la ficha que ninguna otra página tiene: se construye día a
    día desde que empezamos a anotar y no se puede reconstruir después. Para
    las fichas de una sola tienda --el 81% del catálogo-- es además lo único
    con lo que se puede comparar algo.
    """
    por_tienda = historial_de(product["id"])
    serie = serie_diaria(por_tienda)
    if len(serie) < 2:
        return ""
    precios = [p for _, p in serie]
    lo, hi = min(precios), max(precios)
    dia_lo = next(d for d, p in serie if p == lo)
    dia_hi = next(d for d, p in serie if p == hi)
    hoy = precios[-1]

    # Si la serie no llega a hoy es que ninguna tienda lo vende ya (todas las
    # series terminan en null). No se dice "hoy está en": no está.
    if serie[-1][0] < (datetime.date.today() - HIST_EPOCH).days:
        return ""

    if hoy <= lo:
        veredicto = (
            f'<p class="history-verdict history-low">Hoy está en '
            f'<strong>{money(hoy)}</strong>: el precio más bajo que le registramos.</p>'
        )
    else:
        subida = round(100 * (hoy - lo) / lo)
        veredicto = (
            f'<p class="history-verdict">Hoy está en <strong>{money(hoy)}</strong>, '
            f'{money(hoy - lo)} ({subida}%) por encima de su mínimo registrado.</p>'
        )

    rango = (
        f'<p class="history-range">Entre el {fecha_larga(serie[0][0])} y el {fecha_larga(serie[-1][0])} '
        f"osciló entre {money(lo)} (el {fecha_larga(dia_lo)}) y {money(hi)} "
        f"(el {fecha_larga(dia_hi)})."
        if hi != lo else
        f'<p class="history-range">No se ha movido de {money(lo)} desde el {fecha_larga(serie[0][0])}.'
    ) + "</p>"

    return f"""
<div class="panel detail-anchor-target" id="historyPanel">
  <h2>Evolución del precio</h2>
  {veredicto}
  {rango}
  {sparkline_svg(serie)}
  <p class="muted small">El historial arranca el {fecha_larga(serie[0][0])},
  que es cuando empezamos a guardarlo — no antes.</p>
</div>
"""


# Sólo publica página estática el producto que de verdad se puede COMPARAR.
#
# Search Console avisó de dos cosas a la vez: "error del servidor (5xx)" y
# "duplicada: Google eligió otra canónica". Las dos salen del mismo sitio.
# El sitio publicado pesaba 5.2 GB -- 240,984 fichas de ~20 KB cada una --
# contra el límite de 1 GB de GitHub Pages, y el 93% de esas fichas tenía UNA
# sola oferta. Una página que dice "compara el precio entre 1 vendedor" no
# compara nada: es la página fina que Google agrupa con otra parecida y
# descarta, y encima multiplicada por 240,000 es la que revienta el hosting.
#
# El producto NO se borra: sigue en data/, en el buscador y en las listas por
# categoría. Lo que deja de existir es su URL propia, hasta que aparezca un
# segundo vendedor y la ficha tenga algo que comparar.
MIN_OFERTAS_PARA_PAGINA = 2

# Se llena en main() antes de escribir nada, porque las listas por categoría
# y de marca enlazan a las fichas y necesitan saber cuáles existen.
_CON_PAGINA = set()


def tiene_pagina(product):
    return len(product.get("offers") or []) >= MIN_OFERTAS_PARA_PAGINA


def enlace_producto(p, prefijo):
    """El nombre enlaza sólo si esa ficha tiene página publicada.

    Sin esto, una página de categoría enlazaría a 50 URLs de las que hoy
    existen 4: el resto serían 404 servidos desde nuestro propio sitio.
    """
    nombre = html_escape(p["name"])
    if p["id"] in _CON_PAGINA:
        return f'<a href="{prefijo}producto/{p["id"]}/">{nombre}</a>'
    return nombre


def render_product_page(product, data, subs_con_pagina=None):
    cat = next(c for c in data["categories"] if c["id"] == product["category"])
    cat_slug = slugify(cat["name"])
    sub = None
    if product.get("subcategory"):
        sub = next(
            (s for s in cat.get("subcategories", []) if s["id"] == product["subcategory"]), None
        )
    # Si la subcategoría tiene página propia, la miga apunta AHÍ. Antes iba a
    # "../../#/list?cat=..&sub=..", una url con # que un buscador no sigue
    # como página aparte: las ~82 mil fichas colgaban todas del listado
    # general de su categoría y las páginas de subcategoría no recibían un
    # solo enlace interno.
    # La clave es el PAR (categoría, subcategoría): 18 ids se repiten entre
    # categorías ("Otros" en 12, "Accesorios" en 6, "Android" en 2), así que
    # con solo el id de la subcategoría un celular podía terminar enlazando a
    # la página "Android" de otra categoría.
    sub_tiene_pagina = bool(sub) and (cat["id"], sub["id"]) in (subs_con_pagina or set())
    price = min_price(product)
    avg, count = aggregate_rating(product)
    canonical_path = f"/producto/{product['id']}/"
    canonical = f"{SITE_URL}{canonical_path}"
    n_sellers = seller_total(product)

    # Si el historial dice algo que ninguna otra página puede decir, va en la
    # descripción: es lo que decide si alguien hace clic desde el buscador.
    nota_historial = ""
    serie_desc = serie_diaria(historial_de(product["id"]))
    if len(serie_desc) >= 2:
        precios_desc = [x for _, x in serie_desc]
        if precios_desc[-1] <= min(precios_desc):
            nota_historial = " Hoy está en su precio más bajo registrado."
        elif precios_desc[-1] < precios_desc[0]:
            nota_historial = f" Bajó de {money(precios_desc[0])} a {money(precios_desc[-1])}."
    description = (
        f"Compara el precio de {product['name']} entre {plural(n_sellers, 'vendedor', 'vendedores')} en México. "
        f"Desde {money(price)} MXN.{nota_historial} Envío, disponibilidad y calificación por tienda."
    )

    SHIPPING_CALC_STORE_IDS = ("aliexpress", "alibaba", "sunsky", "geekbuying")
    shipping_calc_store_id = next(
        (o["storeId"] for o in product["offers"] if o["storeId"] in SHIPPING_CALC_STORE_IDS), None
    )
    shipping_calc_html = ""
    if shipping_calc_store_id:
        shipping_calc_store = store_by_id(data, shipping_calc_store_id)
        shipping_calc_html = f"""
<div class="panel detail-anchor-target" id="shippingPanel">
  <h2>Estimación de envío internacional</h2>
  <p class="muted small">Este producto se vende en {html_escape(shipping_calc_store['name'])}. Usa la calculadora de envío por peso y tamaño de ComparaMEX para estimar el costo a México.</p>
  <a class="buy-btn" href="../../#/envio">Abrir calculadora de envío →</a>
</div>
"""

    rows = sorted(seller_rows(product), key=lambda o: o["price"])
    table_rows = []
    for o in rows:
        store = store_by_id(data, o["storeId"])
        # Igual que en el SPA (ver renderOfferRows en js/app.js): 6 de las
        # 11 tiendas del catálogo publican un umbral fijo de envío gratis en
        # USD, investigado por tienda -- se compara contra el precio real de
        # esta oferta (priceOriginal, todas estas 6 cotizan en USD).
        price_original = o.get("priceOriginal") or {}
        price_usd = price_original.get("amount") if price_original.get("currency") == "USD" else None
        threshold = store.get("freeShippingThresholdUSD")
        qualifies_free = threshold is not None and price_usd is not None and price_usd >= threshold
        ship = (
            "Envío gratis" if o.get("shippingFee") == 0
            else money(o["shippingFee"]) if o.get("shippingFee") is not None
            else "Envío gratis" if qualifies_free
            # Ninguna tienda trae shippingFee numérico real todavía, y las
            # que sí tienen productos son de envío internacional directo
            # (sin hubRegion) -- se dice eso en vez de dejar la columna en
            # blanco.
            else "Envío internacional" if not store.get("hubRegion")
            else "—"
        )
        stock_label = {
            "in_stock": "En stock",
            "low_stock": "Últimas piezas",
            "backorder": "Sobre pedido",
        }.get(o.get("stock"), o.get("stock") or "—")
        rating_label = "—" if o.get("rating") is None else f"{o['rating']} / 5 ({o.get('reviewCount') or 0} reseñas)"
        if store.get("logoImg"):
            dot = (
                f'<span class="store-dot has-logo">'
                f'<img src="../../{store["logoImg"]}" alt="{html_escape(store["name"])}" loading="lazy"></span>'
            )
        else:
            dot = f'<span class="store-dot" style="background:{store["color"]}">{store["logo"]}</span>'
        variants = o.get("variants") or []
        variants_html = ""
        if variants:
            pills = "".join(
                f'<a class="variant-pill" href="{v["url"]}" target="_blank" rel="nofollow noopener">'
                f'<img src="{v["photo"]}" alt="" loading="lazy"><span>{html_escape(v["label"])}</span></a>'
                for v in variants
            )
            variants_html = (
                f'<div class="variant-pills"><span class="variant-pills-label">{svg_icon("palette")} {len(variants) + 1} variantes:</span>'
                f'<a class="variant-pill active" href="{o["url"]}" target="_blank" rel="nofollow noopener">'
                f'<img src="{o.get("photo") or product.get("photo") or ""}" alt="" loading="lazy"><span>Esta</span></a>{pills}</div>'
            )
        # Alibaba es mayorista, a diferencia del resto de las tiendas del
        # catálogo: mismo aviso que en el SPA (ver renderOfferRows en
        # js/app.js) para no dar a entender que 1 unidad siempre se puede
        # comprar y enviar sola.
        wholesale_html = (
            '<span class="wholesale-badge" title="Alibaba es una plataforma mayorista: '
            "este producto puede tener un pedido mínimo (MOQ) mayor a 1 unidad. Verifica "
            'la cantidad mínima en la página del producto antes de comprar.">'
            + svg_icon("alert-triangle") + " Posible pedido mínimo</span>"
        ) if o["storeId"] == "alibaba" else ""
        # "N vendedores · desde $X": mismo dato y mismo criterio que en el SPA
        # (ver renderOfferRows en js/app.js). Un producto de catálogo de
        # Mercado Libre puede tener varios vendedores con precios distintos, y
        # el precio publicado es el de la caja de compra.
        sellers_html = ""
        if o["storeId"] == "mercadolibre" and (o.get("sellerCount") or 0) > 1:
            lowest = o.get("lowestPrice")
            cheaper = ""
            if lowest and lowest < o["price"]:
                pct = round((1 - lowest / o["price"]) * 100)
                cheaper = f' · desde {money(lowest)} <span class="sellers-save">-{pct}%</span>'
            sellers_html = (
                '<span class="sellers-badge" title="Mercado Libre lista varios vendedores '
                "para este mismo producto. El precio de arriba es el de la caja de compra, "
                'que es el que se cobra al entrar.">'
                + svg_icon("shopping-bag") + f' {o["sellerCount"]} vendedores{cheaper}</span>'
            )
        table_rows.append(
            f'<tr><td><span class="store-badge">{dot} {html_escape(store["name"])}'
            + (f' <span class="store-color-label">· {html_escape(o["sellerState"])}</span>' if o.get("sellerState") else "")
            + '</span>'
            + ('<span class="seller-tag official">Tienda oficial</span>' if o.get("sellerOfficial") else "")
            + ('<span class="seller-tag buybox">Vendedor por defecto</span>' if o.get("isBuyBox") else "")
            + f'{sellers_html}{wholesale_html}{variants_html}</td>'
            f"<td class=\"price-cell\"><span class=\"price-line\">{money(o['price'])}</span>"
            + (f'<span class="bundle-badge">{svg_icon("headphones")} {html_escape(o["bundleNote"])}</span>' if o.get("bundleNote") else "")
            + "</td>"
            f"<td>{ship}</td><td>{stock_label}</td>"
            f"<td>{rating_label}</td></tr>"
        )

    specs_rows = "".join(
        f"<tr><th>{html_escape(s['label'])}</th><td>{html_escape(s['value'])}</td></tr>"
        for s in product["specs"]
    )

    # Texto de reseñas real (no simulado, viene del catálogo curado) para que
    # los buscadores tengan contenido único que indexar, no solo la tabla de
    # precios: es el punto "UGC" del comparativo con Kakaku.com.
    review_items = "".join(
        f'<div class="review-item">'
        f'<div class="review-stars">{"★" * r["rating"]}{"☆" * (5 - r["rating"])}</div>'
        f'<div class="review-meta"><strong>{html_escape(r["author"])}</strong> — {html_escape(r["date"])}</div>'
        f'<p class="review-comment">{html_escape(r["comment"])}</p>'
        f"</div>"
        for r in (product.get("reviews") or [])
    )
    reviews_html = (
        f'<div class="panel detail-anchor-target" id="reviewsPanel"><h2>Reseñas de compradores</h2><div class="review-list">{review_items}</div></div>'
        if product.get("reviews")
        else ""
    )

    related = related_products(product, data["products"])
    # La foto de verdad, como en el resto de las listas: estas tarjetas
    # llevaban SIEMPRE el icono gris de la categoría, así que cuatro
    # celulares distintos se veían idénticos y no invitaban a entrar.
    related_items = "".join(
        f'<a class="related-item" href="../../producto/{r["id"]}/">'
        f'{product_photo_html(r, "row-icon related-icon")}'
        f'<span class="related-name">{html_escape(r["name"])}</span>'
        f'<span class="related-price">{"Desde " if len(r["offers"]) > 1 else ""}{money(min_price(r))}</span>'
        f"</a>"
        for r in related
    )
    related_html = (
        f'<div class="panel"><h2>Productos relacionados</h2><div class="related-grid">{related_items}</div></div>'
        if related
        else ""
    )

    if sub_tiene_pagina:
        sub_crumb = (
            f'<a href="../../categoria/{cat_slug}/{slugify(sub["name"])}/">'
            f'{html_escape(sub["name"])}</a> &gt;'
        )
    elif sub:
        sub_crumb = (
            f'<a href="../../#/list?cat={cat["id"]}&sub={sub["id"]}">{html_escape(sub["name"])}</a> &gt;'
        )
    else:
        sub_crumb = ""

    # Mismo menú que el SPA (renderDetailQuickNav en js/app.js), en el mismo
    # hueco junto al nombre. Acá son <a href="#id"> lisos: el salto lo hace el
    # navegador y .detail-anchor-target (scroll-margin-top) evita que el
    # título quede tapado. "Envío" y "Comentarios" solo se listan si la página
    # de verdad tiene esa sección -- la calculadora de envío existe solo para
    # AliExpress/Alibaba/SUNSKY/Geekbuying, y las reseñas solo si el producto
    # ya tiene alguna.
    history_html = render_price_history(product)
    if bajada_de(product["id"]):
        history_html += (
            f'<p style="text-align:center; margin:-6px 0 14px"><a class="chip" '
            f'href="../../ofertas/">{svg_icon("chart")} Ver todo lo que bajó de precio hoy</a></p>'
        )
    quicknav_items = [("comparePanel", "tag", "Precios")]
    if history_html:
        quicknav_items.append(("historyPanel", "chart", "Evolución"))
    quicknav_items.append(("specsPanel", "pencil", "Especificaciones"))
    if shipping_calc_html:
        quicknav_items.append(("shippingPanel", "pin", "Envío"))
    if reviews_html:
        quicknav_items.append(("reviewsPanel", "trophy", "Comentarios"))
    # Último botón: el único que sale de la ficha, a la lista de la
    # categoría. Va acá porque la cuadrícula es de dos columnas y con cinco
    # botones quedaba un hueco vacío (a pedido del usuario). En la versión
    # interactiva lo pone renderDetailQuickNav() en js/app.js.
    quicknav_html = (
        '<nav class="detail-quicknav">'
        + "".join(
            f'<a class="detail-quicknav-btn" href="#{qid}">{svg_icon(ic)}'
            f' <span class="detail-quicknav-label">{label}</span></a>'
            for qid, ic, label in quicknav_items
        )
        + f'<a class="detail-quicknav-btn detail-quicknav-cat" href="../../categoria/{cat_slug}/">'
        f'{svg_icon("crown")} <span class="detail-quicknav-label">'
        f'Populares de {html_escape(cat["name"])}</span></a>'
        + "</nav>"
    )

    body = f"""
<nav class="breadcrumb">
  <a href="../../">Inicio</a> &gt;
  <a href="../../categoria/{cat_slug}/">{html_escape(cat['name'])}</a> &gt;
  {sub_crumb}
  {html_escape(product['name'])}
</nav>
<div class="detail-head">
  {product_photo_html(product)}
  <div class="detail-headinfo">
    <p class="muted small">{html_escape(product['brand'])}</p>
    <h1>{html_escape(product['name'])}{f'<span class="used-badge" title="Producto usado/preowned">{svg_icon("rotate")} Usado</span>' if is_used(product) else ''}</h1>
    <p class="detail-rating">{f'{avg} / 5 ({plural(count, "calificación", "calificaciones")})' if count else 'Sin calificaciones todavía'}</p>
    <p class="detail-fromprice">{'Desde ' if n_sellers > 1 else ''}<strong>{money(price)}</strong> en {plural(n_sellers, "vendedor", "vendedores")}</p>
    {NOTA_LAG_HTML}
  </div>
  {quicknav_html}
</div>
<div class="panel detail-anchor-target" id="comparePanel">
  <h2>Comparación de precios</h2>
  <div class="table-scroll">
    <table class="compare-table">
      <thead><tr><th>Vendedor</th><th>Precio</th><th>Envío</th><th>Disponibilidad</th><th>Calificación</th></tr></thead>
      <tbody>{''.join(table_rows)}</tbody>
    </table>
  </div>
  <p class="disclaimer">{NOTA_LAG} {STORE_ORDER_NOTE}</p>
</div>
{history_html}
<div class="panel detail-anchor-target" id="specsPanel">
  <h2>Especificaciones</h2>
  <table class="spec-table">{specs_rows}</table>
</div>
{shipping_calc_html}
{reviews_html}
{related_html}
<div class="panel" style="text-align:center">
  <h2>Ver la comparación interactiva</h2>
  <p class="muted small">Mapa de tiempo de entrega por municipio, comparación completa por tienda y reseñas de compradores.</p>
  <a class="buy-btn" href="../../#/p/{product['id']}">Abrir ComparaMEX interactivo →</a>
</div>
"""
    migas = [
        ("Inicio", f"{SITE_URL}/"),
        (cat["name"], f"{SITE_URL}/categoria/{cat_slug}/"),
    ]
    if sub_tiene_pagina:
        migas.append((sub["name"], f"{SITE_URL}/categoria/{cat_slug}/{slugify(sub['name'])}/"))
    migas.append((product["name"], None))
    breadcrumbs = breadcrumb_json_ld(migas)
    extra_head = (
        f'<script type="application/ld+json">\n{product_json_ld(product, data, canonical)}\n</script>\n'
        f'<script type="application/ld+json">\n{breadcrumbs}\n</script>\n'
        # Suma una visita al contador de la categoría (ver js/popularidad.js).
        # Es lo que alimenta el ranking "en vivo" de la portada: sin esto solo
        # contaría quien navega dentro de la aplicación, y a estas páginas es
        # adonde llega el tráfico de los buscadores. No manda identificadores
        # ni usa cookies: suma uno a "Herramientas" y ya.
        f'<script src="../../js/popularidad.js" defer></script>\n'
        f'<script defer>document.addEventListener("DOMContentLoaded",function(){{'
        f'window.ComparaMXVistas&&window.ComparaMXVistas.contar('
        f'{json.dumps(product.get("category") or "", ensure_ascii=False)},'
        f'{json.dumps(product["id"])});}});</script>'
    )
    title = f"{product['name']} — Compara precios en México | ComparaMEX"
    return page_shell(title, description, canonical_path, body, depth=2,
                      extra_head=extra_head, og_image=product.get("photo"))


# Una subcategoría con menos productos que esto no llega a página propia: la
# lista quedaría casi vacía, sería casi idéntica a la de la categoría padre
# (contenido duplicado) y solo gastaría presupuesto de rastreo. Con 30 hay
# 193 subcategorías con página; con 100, 98.
# Mismo día 0 que scripts/record_price_history.py: los días del historial son
# la cantidad de días desde acá.
HIST_EPOCH = datetime.date(2026, 9, 1)

# Subcategorías que NO entran en el listado por defecto de su categoría: son
# piezas sueltas (filtros, mopas, cartuchos) que se compran cuando ya se tiene
# el aparato, y mezcladas con el resto el ranking de Aspiradoras abría con un
# kit de mopas. Mismo criterio que SUBCATEGORIAS_OPT_IN en js/app.js. Siguen
# teniendo su propia página, que es donde alguien que busca un filtro llega.
SUBCATEGORIAS_OPT_IN = {"Accesorios"}

MIN_PRODUCTOS_SUBCATEGORIA = 30

# "Otros" es el cajón de sastre de cada categoría: nadie busca "otros
# muebles", y una página así solo sería una lista sin tema. No lleva página
# propia por más productos que tenga (los suyos siguen en la de la categoría).
SUBCATEGORIAS_SIN_PAGINA = {"otros", "otras", "otro", "otra", "varios", "general"}

# La página estática no es interactiva (no hay paginación de JS acá), así que
# se limita a un top fijo en vez de volcar la categoría entera: sin esto,
# "Moda y accesorios" generaba un solo archivo HTML de ~4MB con miles de
# filas. El resto queda a un clic con el link a la SPA, que sí pagina.
STATIC_LIST_CAP = 100


def subcategorias_con_pagina(cat, products_de_la_cat):
    """[(sub, productos)] de las subcategorías que llegan al mínimo.

    Se usa en tres sitios (generación, enlaces desde la categoría padre y
    sitemap), así que el criterio vive en un solo lugar.
    """
    salida = []
    for sub in cat.get("subcategories", []):
        if sub["name"].strip().lower() in SUBCATEGORIAS_SIN_PAGINA:
            continue
        items = [p for p in products_de_la_cat if p.get("subcategory") == sub["id"]]
        if len(items) >= MIN_PRODUCTOS_SUBCATEGORIA:
            salida.append((sub, items))
    return salida


# Subcategorías cuyo nombre es un modificador y no dice qué es sin su
# categoría: "4K" (Televisores), "Android" (Celulares), "De escoba"
# (Aspiradoras), "27 pulgadas" (Monitores). En el <title> y el <h1> van con
# la categoría adelante -- "Televisores 4K" es lo que alguien escribe en el
# buscador; "4K — Comparar precios" no le dice ni a Google ni a nadie que
# son televisores. La miga de pan sigue con el nombre corto: ahí la
# categoría ya está un escalón arriba.
_MODIFICADOR = re.compile(
    r"^(\d|de |del |con |sin |para |hasta |uso |tipo |[A-Z0-9]{1,4}\b|"
    r"\w+(icos|icas|ales|bles|ados|adas|idos|idas|ivos|ivas|entes|antes|ares)\b|"
    r"android|windows|gamer|gaming|mediana|grande|peque|carga )", re.IGNORECASE)
# Nombres propios que no se bajan a minúscula al ir detrás de la categoría.
_NOMBRE_PROPIO = {"Android", "Windows", "Apple", "Bluetooth", "Chromebook", "Smart", "Linux"}


def nombre_completo_sub(cat, sub_name):
    """El nombre de la subcategoría que se entiende sin su categoría."""
    cat_name = cat["name"]
    if cat_name == "Libros" and not sub_name.lower().startswith("libros"):
        return f"Libros de {sub_name[0].lower() + sub_name[1:]}"
    if not _MODIFICADOR.match(sub_name):
        return sub_name
    primera = sub_name.split(" ", 1)[0]
    # Siglas y nombres propios conservan su forma (4K, HD, Android).
    conserva = primera.isupper() or any(c.isupper() for c in primera[1:]) or primera in _NOMBRE_PROPIO
    cola = sub_name if conserva else sub_name[0].lower() + sub_name[1:]
    if re.match(r"(uso|carga) ", cola, re.IGNORECASE):
        cola = "de " + cola
    return f"{cat_name} {cola}"


FAMILIA_MIN_PRODUCTOS = 20


def familias_con_pagina(cat, products_de_la_cat):
    """[(familia, [(sub, productos)], productos)] de las familias con página.

    Es el escalón del medio (familias_subcategorias.py): en Deportes y fitness
    el deporte -- Fútbol, Natación --, que es justo lo que se busca ("artículos
    de fútbol") y no tenía página. La url es /categoria/<cat>/<familia>/, así
    que una familia cuyo nombre choca con una subcategoría de la misma
    categoría no la lleva (la subcategoría manda).
    """
    subs = subcategorias_con_pagina(cat, products_de_la_cat)
    por_nombre = {sub["name"]: (sub, items) for sub, items in subs}
    slugs_sub = {slugify(s["name"]) for s in cat.get("subcategories", [])}
    cuenta = {n: len(it) for n, (_, it) in por_nombre.items()}
    productores = [n for n in por_nombre if rol_de(cat["name"], n) == "producto"]
    grupos = [(f, m) for f, m in agrupar_familias(cat["name"], productores, cuenta) if f]
    if len(grupos) < 2:
        return []
    salida = []
    for familia, miembros in grupos:
        if slugify(familia) in slugs_sub or len(miembros) < 2:
            continue
        pares = [por_nombre[m] for m in miembros]
        items = [p for _, it in pares for p in it]
        if len(items) >= FAMILIA_MIN_PRODUCTOS:
            salida.append((familia, pares, items))
    return salida


def familia_de_sub(cat, sub_name, products_de_la_cat, _cache={}):
    """La familia con página de una subcategoría, o None."""
    clave = cat["id"]
    if clave not in _cache:
        _cache[clave] = {
            sub["name"]: familia
            for familia, pares, _ in familias_con_pagina(cat, products_de_la_cat)
            for sub, _ in pares
        }
    return _cache[clave].get(sub_name)


def _valor_eje(p, campo):
    """El dato por el que corta un eje. "price" no es un facet: es el precio
    más barato de hoy, el mismo que imprime la fila (min_price)."""
    if campo == "price":
        return min_price(p)
    return (p.get("facets") or {}).get(campo)


def _tier_de(valor, tiers):
    """En qué tramo de un eje cae un valor. Mismo criterio que
    materializeQualityAxes() de js/app.js: min es exclusivo y max inclusivo,
    para que los tramos de quality-axes.json no se pisen ni dejen huecos."""
    if valor is None:
        return ""
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return ""
    for t in tiers:
        lo, hi = t.get("min"), t.get("max")
        if lo is not None and v <= float(lo):
            continue
        if hi is not None and v > float(hi):
            continue
        return t.get("id") or ""
    return ""


def ejes_de_subcategoria(cat, sub):
    """Los ejes de "Compara calidad" de esta subcategoría exacta.

    A diferencia de ejes_de_categoria(), que junta los de todas las
    subcategorías para la guía de compra, acá hace falta el eje exacto: los
    botones filtran la lista de ESTA página, así que un eje de otra
    subcategoría dejaría a todas las filas fuera de todos sus tramos.
    """
    entrada = QUALITY_AXES.get(f"{cat['id']}/{sub['name']}") or {}
    ejes = []
    for eje in entrada.get("axes", []):
        tiers = [t for t in (eje.get("tiers") or []) if t.get("name") and t.get("id")]
        if eje.get("label") and eje.get("field") and len(tiers) >= 2:
            ejes.append((eje, tiers))
    # Tres, como en la SPA (QUALITY_KEYS en js/app.js).
    return ejes[:3]


def compara_calidad_html(ejes, products, prefijo):
    """El bloque "Compara calidad" de la página estática.

    Es el mismo de la SPA (ver QUALITY_AXES en js/app.js) y con la misma
    regla: cada tramo DICE de qué campo sale y qué corte usa ("Hasta 20 W"),
    nunca una puntuación inventada. Un producto sin ese campo publicado no
    entra en ningún tramo, así que cada eje muestra sobre cuántos productos
    está hablando -- si no se dijera, un filtro que esconde la mitad de la
    lista parecería un error.
    """
    if not ejes:
        return ""
    bloques = []
    for eje, tiers in ejes:
        campo = eje["field"]
        con_dato = sum(1 for p in products if _valor_eje(p, campo) is not None)
        # Misma regla que renderQualityPicker() en js/app.js: si casi nadie
        # de la página puede contestar el eje, el eje no se dibuja.
        if con_dato < 4 or con_dato < len(products) * 0.05:
            continue
        botones = []
        for t in tiers:
            n = sum(
                1 for p in products
                if _tier_de(_valor_eje(p, campo), tiers) == t["id"]
            )
            if not n:
                continue
            botones.append(
                f'<button type="button" class="cq-tier" data-eje="{html_escape(campo)}"'
                f' data-tier="{html_escape(t["id"])}">'
                f'<span class="cq-tier-name">{html_escape(t["name"])}</span>'
                f'<span class="cq-tier-spec">{html_escape(t.get("spec") or "")}</span>'
                + (f'<span class="cq-tier-use">{html_escape(t["use"])}</span>' if t.get("use") else "")
                + f'<span class="cq-tier-n">{n}</span></button>'
            )
        if len(botones) < 2:
            continue
        bloques.append(
            f'<div class="cq-axis" data-eje="{html_escape(campo)}">'
            f'<div class="cq-axis-head">{html_escape(eje["label"])}'
            f'<span class="cq-axis-crit">{html_escape(eje.get("criterion") or "")}</span>'
            f'<span class="cq-axis-n">{con_dato} de {len(products)} lo publican</span></div>'
            f'<div class="cq-tiers">{"".join(botones)}</div></div>'
        )
    if not bloques:
        return ""
    return (
        '<section class="cq">'
        f'<div class="cq-head"><img class="cq-logo" src="{prefijo}icons/logo-comparacalidad.png"'
        ' alt="Compara calidad">'
        '<span class="cq-sub">Elige el nivel que buscas y la lista se filtra sola.</span>'
        '<button type="button" class="cq-clear" hidden>Quitar filtro</button></div>'
        + "".join(bloques) + "</section>"
    )


# Orden de la lista estática. Son las mismas opciones de la barra de la SPA
# (ver .sort-bar en index.html) menos "Relevancia", que solo tiene sentido
# con una búsqueda escrita: acá no hay consulta que puntuar.
SORT_BAR_HTML = (
    '<p class="nota-lag">Los precios se toman de cada tienda y pueden llevar '
    'algunas horas de retraso.</p>'
    '<div class="sort-bar static-sort" role="group" aria-label="Ordenar la lista">'
    '<div class="sort-bar-options">'
    '<button type="button" class="sort-opt active" data-sort="pop">Popularidad</button>'
    '<button type="button" class="sort-opt" data-sort="price_asc">Más baratos</button>'
    '<button type="button" class="sort-opt" data-sort="price_desc">Más caros</button>'
    '<button type="button" class="sort-opt" data-sort="rating">Mejor calificados</button>'
    '</div></div>'
)

# Ordenar y filtrar sin bajar nada: los datos de cada fila ya están en sus
# data-*, así que la página estática hace lo mismo que la SPA sin pedirle
# nada al servidor. Si el visitante tiene el JS apagado, la lista se queda
# en el orden por popularidad con el que se generó, que es el bueno.
LIST_JS = """
<script>
(function () {
  var lista = document.getElementById('lista');
  if (!lista) return;
  var filas = [].slice.call(lista.querySelectorAll('.product-row'));
  var orden = 'pop';
  var filtros = {};
  var num = function (f, k) { var v = parseFloat(f.getAttribute(k)); return isNaN(v) ? -1 : v; };
  var aplicar = function () {
    var claves = Object.keys(filtros);
    var visibles = filas.filter(function (f) {
      return claves.every(function (k) { return f.getAttribute('data-q-' + k) === filtros[k]; });
    });
    visibles.sort(function (a, b) {
      if (orden === 'price_asc') return num(a, 'data-price') - num(b, 'data-price');
      if (orden === 'price_desc') return num(b, 'data-price') - num(a, 'data-price');
      if (orden === 'rating') return num(b, 'data-rating') - num(a, 'data-rating') || num(b, 'data-pop') - num(a, 'data-pop');
      return num(b, 'data-pop') - num(a, 'data-pop') || num(b, 'data-sellers') - num(a, 'data-sellers');
    });
    filas.forEach(function (f) { f.hidden = true; });
    visibles.forEach(function (f, i) {
      f.hidden = false;
      lista.appendChild(f);
      // El puesto se recalcula: una lista ordenada por precio con los
      // números del ranking de popularidad al lado dice dos cosas
      // distintas a la vez. Con el orden original vuelve la corona.
      var b = f.querySelector('.rank-badge');
      if (b) b.innerHTML = (orden === 'pop' && !claves.length && i === 0) ? f.getAttribute('data-corona') : String(i + 1);
      f.className = f.className.replace(/ ?rank-[234]/g, '') +
        ((orden === 'pop' && !claves.length && i >= 1 && i <= 3) ? ' rank-' + (i + 1) : '');
    });
    var vacio = document.getElementById('lista-vacia');
    if (vacio) vacio.hidden = visibles.length > 0;
    var cuenta = document.getElementById('lista-cuenta');
    if (cuenta) cuenta.textContent = visibles.length;
  };
  [].forEach.call(document.querySelectorAll('.static-sort .sort-opt'), function (b) {
    b.addEventListener('click', function () {
      [].forEach.call(document.querySelectorAll('.static-sort .sort-opt'), function (o) {
        o.classList.toggle('active', o === b);
      });
      orden = b.getAttribute('data-sort');
      aplicar();
    });
  });
  var limpiar = document.querySelector('.cq-clear');
  [].forEach.call(document.querySelectorAll('.cq-tier'), function (b) {
    b.addEventListener('click', function () {
      var eje = b.getAttribute('data-eje'), tier = b.getAttribute('data-tier');
      var puesto = filtros[eje] === tier;
      if (puesto) delete filtros[eje]; else filtros[eje] = tier;
      [].forEach.call(document.querySelectorAll('.cq-tier[data-eje="' + eje + '"]'), function (o) {
        o.classList.toggle('is-active', !puesto && o === b);
      });
      if (limpiar) limpiar.hidden = !Object.keys(filtros).length;
      aplicar();
    });
  });
  if (limpiar) limpiar.addEventListener('click', function () {
    filtros = {};
    [].forEach.call(document.querySelectorAll('.cq-tier'), function (o) { o.classList.remove('is-active'); });
    limpiar.hidden = true;
    aplicar();
  });
})();
</script>
"""


# La página de marca: orden (con "Más vendedores"), filtro por categoría y
# buscador, los tres sobre las mismas filas y a la vez. El puesto se
# recalcula como en LIST_JS: la corona solo con el orden original y sin
# filtros.
BRAND_LIST_JS = """
<script>
// Va antes de la lista en el HTML, así que espera a que exista.
document.addEventListener('DOMContentLoaded', function () {
  var lista = document.getElementById('prodLista');
  if (!lista) return;
  var filas = [].slice.call(lista.querySelectorAll('.product-row'));
  var orden = 'pop', cat = '', q = '';
  var campo = document.getElementById('prodFiltro');
  var cuenta = document.getElementById('prodFiltroCuenta');
  var num = function (f, k) { var v = parseFloat(f.getAttribute(k)); return isNaN(v) ? -1 : v; };
  var sinAcentos = function (s) { return s.normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').toLowerCase(); };
  var textos = filas.map(function (f) { return sinAcentos(f.textContent); });
  var aplicar = function () {
    var visibles = filas.filter(function (f, i) {
      return (!cat || f.getAttribute('data-cat') === cat) && (!q || textos[i].indexOf(q) !== -1);
    });
    visibles.sort(function (a, b) {
      if (orden === 'price_asc') return num(a, 'data-price') - num(b, 'data-price');
      if (orden === 'price_desc') return num(b, 'data-price') - num(a, 'data-price');
      if (orden === 'rating') return num(b, 'data-rating') - num(a, 'data-rating') || num(b, 'data-pop') - num(a, 'data-pop');
      if (orden === 'sellers') return num(b, 'data-sellers') - num(a, 'data-sellers') || num(b, 'data-stores') - num(a, 'data-stores') || num(b, 'data-pop') - num(a, 'data-pop');
      return num(b, 'data-pop') - num(a, 'data-pop') || num(b, 'data-sellers') - num(a, 'data-sellers');
    });
    var original = orden === 'pop' && !cat && !q;
    filas.forEach(function (f) { f.hidden = true; });
    visibles.forEach(function (f, i) {
      f.hidden = false;
      lista.appendChild(f);
      var b = f.querySelector('.rank-badge');
      if (b) b.innerHTML = (original && i === 0) ? f.getAttribute('data-corona') : String(i + 1);
      f.className = f.className.replace(/ ?rank-[234]/g, '') + ((original && i >= 1 && i <= 3) ? ' rank-' + (i + 1) : '');
    });
    if (cuenta) cuenta.textContent = (cat || q) ? (visibles.length ? visibles.length + ' de ' + filas.length + ' productos' : 'Ningún producto coincide.') : '';
  };
  [].forEach.call(document.querySelectorAll('.static-sort .sort-opt'), function (b) {
    b.addEventListener('click', function () {
      [].forEach.call(document.querySelectorAll('.static-sort .sort-opt'), function (o) { o.classList.toggle('active', o === b); });
      orden = b.getAttribute('data-sort');
      aplicar();
    });
  });
  [].forEach.call(document.querySelectorAll('.cat-filter .cat-opt'), function (b) {
    b.addEventListener('click', function () {
      cat = b.getAttribute('data-cat') || '';
      [].forEach.call(document.querySelectorAll('.cat-filter .cat-opt'), function (o) { o.classList.toggle('is-active', o === b); });
      aplicar();
    });
  });
  if (campo) campo.addEventListener('input', function () { q = sinAcentos(campo.value.trim()); aplicar(); });
});
</script>
"""


def render_subcategory_page(cat, sub, products, data, pares_familia=None):
    """Página de una subcategoría ("Sillas de oficina", "Cargadores USB-C").

    Es el hueco más grande que tenía el sitio: había 48 páginas de categoría
    y ~82 mil de producto, y NADA en medio. Las consultas de mitad de embudo
    ("sillas de oficina precio", "cargadores usb c baratos") son justo las
    que un comparador puede ganar, y no había ninguna página a la que
    llevaran. Además le dan a las fichas un enlace interno desde una página
    temática, en vez de colgar todas del listado general de la categoría.
    """
    # Con pares_familia es la página de una FAMILIA (el deporte, en Deportes
    # y fitness): `sub` trae sólo el nombre de la familia y `products` son
    # los de todas sus subcategorías. Se reusa esta misma página porque es
    # la misma pregunta un escalón más arriba ("artículos de fútbol" en vez
    # de "balones de fútbol").
    cat_slug = slugify(cat["name"])
    sub_slug = slugify(sub["name"])
    canonical_path = f"/categoria/{cat_slug}/{sub_slug}/"
    productos_cat = [p for p in data["products"] if p["category"] == cat["id"]]
    if pares_familia:
        tipos = [s["name"] for s, _ in pares_familia]
        nombre_largo = f"{sub['name']}: {', '.join(t.lower() for t in tipos[:3])}" + (" y más" if len(tipos) > 3 else "")
        familia = None
    else:
        nombre_largo = nombre_completo_sub(cat, sub["name"])
        familia = familia_de_sub(cat, sub["name"], productos_cat)
    precios = [min_price(p) for p in products if p.get("offers")]
    rango = ""
    if precios:
        rango = f" Precios desde {money(min(precios))} hasta {money(max(precios))} MXN."
    # Google corta la descripción alrededor de los 160 caracteres, así que
    # volcar 40 marcas ahí no aporta nada y se lee como relleno de palabras
    # clave. Van las marcas con más productos, pocas, y el resto de la lista
    # queda en el cuerpo de la página, que es donde sí se puede leer entera.
    por_marca = collections.Counter(p["brand"] for p in products if p.get("brand"))
    top_marcas = [m for m, _ in por_marca.most_common(5)]
    marcas_note = f" Marcas como {', '.join(top_marcas)}." if top_marcas else ""
    description = (
        f"Compara precios de {nombre_largo[0].lower() + nombre_largo[1:] if not nombre_largo.split(' ')[0].isupper() else nombre_largo} en México entre tiendas: "
        f"{len(products)} productos.{rango}{marcas_note}"
    )

    ranked = sorted(products, key=lambda p: (total_review_count(p), seller_total(p)), reverse=True)
    shown = ranked[:STATIC_LIST_CAP]
    ejes = [] if pares_familia else ejes_de_subcategoria(cat, sub)
    rows = []
    for i, p in enumerate(shown, start=1):
        corona = svg_icon("crown")
        rank_badge = corona if i == 1 else str(i)
        rank_class = f" rank-{i}" if 2 <= i <= 4 else ""
        used_badge = (
            f'<span class="used-badge" title="Producto usado/preowned">{svg_icon("rotate")} Usado</span>'
            if is_used(p) else ""
        )
        # Los datos con los que la página ordena y filtra viajan en la fila.
        # Es el mismo dato que ya se muestra, no uno paralelo: el precio del
        # data-price es el que se imprime al lado.
        rating, n_reviews = aggregate_rating(p)
        n_vendedores = seller_total(p)
        q_attrs = "".join(
            f' data-q-{html_escape(eje["field"])}="{_tier_de(_valor_eje(p, eje["field"]), tiers)}"'
            for eje, tiers in ejes
        )
        rows.append(
            f'<div class="product-row has-rank{rank_class}"'
            f' data-price="{min_price(p)}" data-pop="{n_reviews}" data-rating="{rating}"'
            f' data-sellers="{n_vendedores}" data-corona="{html_escape(corona)}"{q_attrs}>'
            f'<span class="rank-badge">{rank_badge}</span>'
            f'{product_photo_html(p, "row-icon")}'
            f'<div class="row-info">'
            f'<div class="row-brand">{html_escape(p["brand"])}</div>'
            f'<div class="row-name">{enlace_producto(p, "../../../")}{used_badge}</div>'
            # Las estrellas van como carácter y no como svg_icon: data/icons.json
            # no trae una estrella, y la ficha de producto ya pinta sus reseñas
            # con "★"/"☆" (ver render_product_page), así que es el mismo signo.
            + (f'<div class="row-rating"><span class="row-stars">'
               f'{"★" * int(round(rating))}{"☆" * (5 - int(round(rating)))}</span> {rating} '
               f'<span class="row-rating-n">({n_reviews:,})</span></div>' if n_reviews else "")
            + f'</div>'
            f'<div class="row-priceblock">'
            # "Desde" en TODAS las filas, no solo en las de varios vendedores:
            # el precio es siempre el más bajo de los que se conocen, y que la
            # palabra aparezca y desaparezca según la fila se leía como si
            # unas filas dijeran otra cosa que las demás.
            f'<div class="row-from">Desde</div>'
            f'<div class="row-price">{money(min_price(p))}</div>'
            f'<div class="row-sellers">{svg_icon("shopping-bag")} '
            f'{plural(n_vendedores, "vendedor", "vendedores")}</div>'
            f'</div>'
            f'</div>'
        )
    more_note = (
        f'<p class="muted small" style="text-align:center; margin-top:10px">'
        f'Mostrando los {len(shown)} más populares de {len(products)}.</p>'
        if len(products) > len(shown) else ""
    )

    # Las marcas dejan de ser texto suelto y pasan a ser enlaces a su página:
    # es el cruce marca x subcategoría, que es por donde entra la búsqueda
    # "colchones restonic" en vez de solo "colchones" o solo "restonic".
    marcas_todas = [m for m, _ in por_marca.most_common()]
    enlaces_marca = []
    for m in marcas_todas[:60]:
        sl = _SLUG_DE_MARCA.get(clave_marca(m))
        enlaces_marca.append(
            f'<a href="../../../marca/{sl}/">{html_escape(m)}</a>' if sl else html_escape(m)
        )
    marcas_html = (
        f'<p class="muted small">Marcas comparadas: '
        f'{", ".join(enlaces_marca)}'
        + (f' y {len(marcas_todas) - 60} más.' if len(marcas_todas) > 60 else '.')
        + '</p>'
        if marcas_todas else ""
    )

    # Enlaces a las subcategorías hermanas: sin esto cada página quedaría en
    # una rama muerta del sitio, alcanzable solo desde el sitemap.
    #
    # Va por subcategorias_con_pagina y no por su propia cuenta: acá había una
    # copia del criterio que miraba el mínimo pero no la lista de nombres sin
    # página, y enlazaba a «Otros» y «Varios», que nunca se generan. Eran los
    # 15 enlaces rotos del sitio.
    hermanas = []
    if pares_familia:
        for otra, items in pares_familia:
            hermanas.append(
                f'<a class="chip" href="../{slugify(otra["name"])}/">'
                f'{html_escape(otra["name"])} ({len(items)})</a>'
            )
        titulo_hermanas = f"{html_escape(sub['name'])} por tipo"
    else:
        for otra, items in subcategorias_con_pagina(cat, productos_cat):
            if otra["id"] == sub["id"]:
                continue
            hermanas.append(
                f'<a class="chip" href="../{slugify(otra["name"])}/">'
                f'{html_escape(otra["name"])} ({len(items)})</a>'
            )
        titulo_hermanas = f"Otras subcategorías de {html_escape(cat['name'])}"
    hermanas_html = (
        f'<div class="panel"><h2>{titulo_hermanas}</h2>'
        f'<div class="chip-row">{"".join(hermanas)}</div></div>'
        if hermanas else ""
    )
    # Arriba de todo, en la página de familia: sus tipos son lo primero que se
    # elige (Fútbol -> Balones), igual que en la SPA.
    tipos_arriba = hermanas_html if pares_familia else ""
    if pares_familia:
        hermanas_html = ""
    miga_familia = (
        f' &gt; <a href="../{slugify(familia)}/">{html_escape(familia)}</a>' if familia else ""
    )
    ids_enlace = ",".join(s["id"] for s, _ in pares_familia) if pares_familia else sub["id"]

    body = f"""
<nav class="breadcrumb"><a href="../../../">Inicio</a> &gt; <a href="../">{html_escape(cat['name'])}</a>{miga_familia} &gt; {html_escape(sub['name'])}</nav>
<div class="list-head"><h1>{svg_icon("trophy")} {html_escape(nombre_largo)} — comparar precios ({len(products)})</h1></div>
<p class="muted small">{html_escape(description)}</p>
{tipos_arriba}
{marcas_html}
{compara_calidad_html(ejes, shown, '../../../')}
{SORT_BAR_HTML}
<div class="product-list" id="lista">{''.join(rows)}</div>
<p class="muted small" id="lista-vacia" hidden>Ningún producto de esta lista publica ese dato. Quita el filtro para ver todos.</p>
<div class="panel" style="text-align:center; margin-top:20px">
  <a class="buy-btn" href="../../../#/list?cat={quote(cat['id'])}&amp;sub={quote(ids_enlace)}">Ver con filtros interactivos →</a>
  {more_note}
</div>
{hermanas_html}
{LIST_JS}
"""
    breadcrumbs = breadcrumb_json_ld([
        ("Inicio", f"{SITE_URL}/"),
        (cat["name"], f"{SITE_URL}/categoria/{cat_slug}/"),
    ] + ([(familia, f"{SITE_URL}/categoria/{cat_slug}/{slugify(familia)}/")] if familia else []) + [
        (sub["name"], None),
    ])
    lista_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"{nombre_largo} — comparar precios en México",
        "numberOfItems": len([p for p in shown if tiene_pagina(p)]),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i,
                "url": f"{SITE_URL}/producto/{p['id']}/",
                "name": p["name"],
            }
            for i, p in enumerate([p for p in shown if tiene_pagina(p)], start=1)
        ],
    }, ensure_ascii=False, indent=2)
    extra_head = (
        f'<script type="application/ld+json">\n{breadcrumbs}\n</script>\n'
        f'<script type="application/ld+json">\n{lista_ld}\n</script>'
    )
    title = f"{nombre_largo} — Comparar precios en México | ComparaMEX"
    return page_shell(title, description, canonical_path, body, depth=3,
                      extra_head=extra_head, og_image=next((p.get("photo") for p in shown if p.get("photo")), None))


# ------------------------------------------------------------------ ofertas

OFERTAS_TOPE = 100

# Mínimo de bajadas para que una categoría tenga su propia página de ofertas.
MIN_BAJADAS_PARA_PAGINA = 30

# [(nombre de categoría, cuántas bajadas)] para los enlaces de la página
# general. Lo llena main() antes de pintar, porque contarlo dentro sería
# recorrer el catálogo entero otra vez.
_por_categoria = []


def _fila_de_oferta(p, bajada, prefijo):
    pct, tienda, antes, ahora, dia = bajada
    return (
        f'<div class="product-row oferta-row">'
        f'{product_photo_html(p, "row-icon")}'
        f'<div class="row-info">'
        f'<div class="row-brand">{html_escape(p["brand"])}</div>'
        f'<div class="row-name">{enlace_producto(p, prefijo)}</div>'
        f'<div class="muted small">En {html_escape(store_by_id_name(p, tienda))}, '
        f'desde el {fecha_larga(dia)}</div>'
        f'</div>'
        f'<div class="row-priceblock">'
        f'<div class="oferta-antes">{money(antes)}</div>'
        f'<div class="row-price">{money(ahora)}</div>'
        f'<div class="oferta-pct">-{pct:.0f}%</div>'
        f'</div>'
        f'</div>'
    )


def store_by_id_name(product, store_id):
    """Nombre legible de la tienda, con el id como respaldo."""
    return _NOMBRES_TIENDA.get(store_id, store_id)


# Se llena en main() desde data["stores"], que es donde vive el nombre
# legible de cada tienda.
_NOMBRES_TIENDA = {}


def render_ofertas_page(items, data, cat=None):
    """Ranking de bajadas de precio. `items` = [(bajada, producto)] ya ordenado.

    Es la página que más se mueve del sitio --cambia todos los días con el
    refresco-- y la única que se puede armar con datos que no tiene nadie más:
    hay que haber estado mirando el precio ayer para saber que hoy bajó.
    """
    donde = f" en {cat['name'].lower()}" if cat else ""
    slug = slugify(cat["name"]) if cat else None
    canonical_path = f"/ofertas/{slug}/" if cat else "/ofertas/"
    prefijo = "../../" if cat else "../"
    mostrados = items[:OFERTAS_TOPE]
    description = (
        f"Productos que bajaron de precio{donde} en tiendas de México, "
        f"según nuestro registro diario. {len(items)} bajadas detectadas; "
        f"se listan las {len(mostrados)} mayores."
        if items else
        f"Productos que bajaron de precio{donde} en tiendas de México, "
        f"según nuestro registro diario. Hoy no hay ninguna bajada confirmada."
    )
    # La página general se publica aunque hoy no haya nada: cuelga del menú
    # principal, y un 404 ahí es peor que decir que hoy no hay bajadas. Pasa
    # el día en que se estrena una regla nueva (la de mismo vendedor dejó sin
    # respaldo a todas las bajadas anteriores) y volvería a pasar si un día
    # ningún precio se moviera.
    filas = "".join(_fila_de_oferta(p, b, prefijo) for b, p in mostrados) or (
        '<p class="empty-state">Hoy no hay ninguna bajada que podamos confirmar. '
        'Volvemos a revisar los precios cada día; en cuanto un vendedor baje el '
        'suyo y lo sostenga, aparece acá.</p>'
    )

    if cat:
        migas = (
            f'<nav class="breadcrumb"><a href="{prefijo}">Inicio</a> &gt; '
            f'<a href="../">Bajaron de precio</a> &gt; {html_escape(cat["name"])}</nav>'
        )
        titulo = f"{cat['name']}: productos que bajaron de precio"
        otras = ""
    else:
        migas = f'<nav class="breadcrumb"><a href="{prefijo}">Inicio</a> &gt; Bajaron de precio</nav>'
        titulo = "Productos que bajaron de precio"
        chips = "".join(
            f'<a class="chip" href="{slugify(nombre)}/">{html_escape(nombre)} ({n})</a>'
            for nombre, n in sorted(_por_categoria, key=lambda x: -x[1])
            if n >= MIN_BAJADAS_PARA_PAGINA
        )
        otras = (
            f'<div class="panel"><h2>Por categoría</h2>'
            f'<div class="chip-row">{chips}</div></div>' if chips else ""
        )

    body = f"""
{migas}
<div class="list-head"><h1>{svg_icon("chart")} {html_escape(titulo)}</h1></div>
<p class="muted small">Comparamos el precio de cada producto con el que tenía
antes en la MISMA tienda y del MISMO vendedor. No entran los productos que
aparecen más baratos solo porque se les sumó otro vendedor, ni los que
cambian de vendedor dentro de la tienda: eso no es una bajada. Tampoco los
precios que estuvieron un solo día, que casi siempre son un dato que la
tienda corrigió.</p>
{NOTA_LAG_HTML}
<div class="product-list">{filas}</div>
{{otras}}
<div class="panel" style="text-align:center; margin-top:20px">
  <a class="buy-btn" href="{prefijo}#/list">Ver el catálogo completo con filtros →</a>
</div>
"""
    body = body.replace("{otras}", otras)
    breadcrumbs = breadcrumb_json_ld(
        [("Inicio", f"{SITE_URL}/"), ("Bajaron de precio", f"{SITE_URL}/ofertas/"),
         (cat["name"], None)]
        if cat else
        [("Inicio", f"{SITE_URL}/"), ("Bajaron de precio", None)]
    )
    lista_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": titulo,
        "numberOfItems": len([x for x in mostrados if tiene_pagina(x[1])]),
        "itemListElement": [
            {"@type": "ListItem", "position": i,
             "url": f"{SITE_URL}/producto/{p['id']}/", "name": p["name"]}
            for i, (_, p) in enumerate([x for x in mostrados if tiene_pagina(x[1])], start=1)
        ],
    }, ensure_ascii=False, indent=2)
    extra_head = (
        f'<script type="application/ld+json">\n{breadcrumbs}\n</script>\n'
        f'<script type="application/ld+json">\n{lista_ld}\n</script>'
    )
    title = f"{titulo} — México | ComparaMEX"
    return page_shell(title, description, canonical_path, body,
                      depth=2 if cat else 1, extra_head=extra_head,
                      og_image=next((p.get("photo") for _, p in mostrados if p.get("photo")), None))


# ---------------------------------------------------------------------
# Guía de compra de la categoría (el formato que usa kakaku.com)
# ---------------------------------------------------------------------
# La página de categoría era un h1 con el conteo, los chips de subcategoría
# y la lista. Eso compite mal: la búsqueda que trae gente a un comparador no
# es "impresoras" a secas sino "mejores impresoras 2026", "cuánto cuesta una
# impresora", "qué impresora comprar". kakaku.com contesta las tres en la
# misma página --選び方 (cómo elegir), ランキング (ranking) y el mes en el
# título-- y por eso sale primero.
#
# Todo lo que se escribe acá sale del catálogo, no de un texto fijo: los
# ejes de "cómo elegir" son los que calcula compute_quality_axes.py, los
# tramos de precio son los percentiles reales de la categoría y las
# respuestas de las preguntas se arman con los números del día. Un texto
# genérico repetido en 52 páginas es exactamente lo que un buscador lee
# como relleno.
MES_ANIO = f"{MESES[datetime.date.today().month - 1]} de {datetime.date.today().year}"
HOY_LARGO = (f"{datetime.date.today().day} de "
             f"{MESES[datetime.date.today().month - 1]} de {datetime.date.today().year}")


def _cargar_quality_axes():
    """Los ejes que calcula compute_quality_axes.py. Si el archivo no está
    (nadie corrió ese paso todavía), la guía simplemente no se dibuja: es
    una sección de más, no un requisito para publicar la categoría."""
    ruta = os.path.join(ROOT, "data", "quality-axes.json")
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


QUALITY_AXES = _cargar_quality_axes()


def ejes_de_categoria(cat, products, data):
    """Ejes de "cómo elegir" de la categoría, deduplicados por etiqueta.

    quality-axes.json está indexado por "Categoría/Subcategoría" (lo arma
    compute_quality_axes.py), así que para la categoría entera se juntan los
    de sus subcategorías y se queda el que cubre más productos.
    """
    ejes = {}
    por_sub = collections.Counter(p.get("subcategory") for p in products)
    for sub, n in por_sub.most_common():
        for eje in (QUALITY_AXES.get(f"{cat['id']}/{sub}") or {}).get("axes", []):
            if eje.get("field") == "price":
                continue
            label = eje.get("label")
            tiers = [t for t in (eje.get("tiers") or []) if t.get("name")]
            if not label or len(tiers) < 2 or label in ejes:
                continue
            ejes[label] = (eje, tiers, n)
    return list(ejes.values())[:4]


def como_elegir_html(cat, products, ejes):
    if not ejes:
        return ""
    bloques = []
    for eje, tiers, _ in ejes:
        filas = "".join(
            f'<div class="guia-tier">'
            f'<div class="guia-tier-nombre">{html_escape(t["name"])}</div>'
            f'<div class="guia-tier-spec">{html_escape(t.get("spec") or "")}</div>'
            + (f'<div class="guia-tier-uso">{html_escape(t["use"])}</div>' if t.get("use") else "")
            + '</div>'
            for t in tiers
        )
        criterio = eje.get("criterion")
        bloques.append(
            f'<div class="guia-eje">'
            f'<h3>{html_escape(eje["label"])}'
            + (f' <span class="muted small">({html_escape(criterio)})</span>' if criterio else "")
            + f'</h3><div class="guia-tiers">{filas}</div></div>'
        )
    return (
        f'<div class="panel" id="como-elegir">'
        f'<h2>{svg_icon("check-circle")} Cómo elegir {html_escape(cat["name"].lower())}</h2>'
        f'<p class="muted small">Lo que de verdad separa un modelo de otro en esta '
        f'categoría, con los rangos que hay hoy en el catálogo.</p>'
        f'<div class="guia-ejes">{"".join(bloques)}</div></div>'
    )


def tramos_de_precio(products):
    """Tres o cuatro tramos con los percentiles reales de la categoría."""
    precios = sorted(pr for pr in (min_price(p) for p in products) if pr)
    if len(precios) < 40:
        return []
    def pct(q):
        return precios[min(len(precios) - 1, int(len(precios) * q))]
    def redondo(v):
        if v >= 10000:
            return int(round(v / 1000.0) * 1000)
        if v >= 1000:
            return int(round(v / 100.0) * 100)
        return int(round(v / 10.0) * 10)
    cortes = sorted({redondo(pct(q)) for q in (0.25, 0.5, 0.75)})
    if len(cortes) < 2:
        return []
    tramos = [(None, cortes[0])]
    for a, b in zip(cortes, cortes[1:]):
        tramos.append((a, b))
    tramos.append((cortes[-1], None))
    salida = []
    for lo, hi in tramos:
        n = sum(1 for pr in precios if (lo is None or pr >= lo) and (hi is None or pr < hi))
        if n:
            salida.append((lo, hi, n))
    return salida


def presupuesto_html(cat, products):
    tramos = tramos_de_precio(products)
    if not tramos:
        return ""
    chips = []
    for lo, hi, n in tramos:
        if lo is None:
            etiqueta, params = f"Hasta {money(hi)}", f"max={hi}"
        elif hi is None:
            etiqueta, params = f"{money(lo)} o más", f"min={lo}"
        else:
            etiqueta, params = f"{money(lo)} a {money(hi)}", f"min={lo}&max={hi}"
        chips.append(
            f'<a class="chip" href="../../#/list?cat={quote(cat["id"])}&{params}">'
            f'{html_escape(etiqueta)} <span class="muted">({n})</span></a>'
        )
    return (
        f'<div class="panel" id="presupuesto">'
        f'<h2>{svg_icon("tag")} Por presupuesto</h2>'
        f'<div class="chip-row">{"".join(chips)}</div></div>'
    )


def marcas_destacadas_html(por_marca):
    enlaces = []
    for m, n in por_marca.most_common(24):
        if clave_marca(m) in MARCAS_EXCLUIDAS:
            continue
        sl = _SLUG_DE_MARCA.get(clave_marca(m))
        if sl:
            enlaces.append(f'<a class="chip" href="../../marca/{sl}/">{html_escape(m)} '
                           f'<span class="muted">({n})</span></a>')
    if not enlaces:
        return ""
    return (
        f'<div class="panel" id="marcas"><h2>{svg_icon("tag")} Marcas</h2>'
        f'<div class="chip-row">{"".join(enlaces[:18])}</div></div>'
    )


def faq_categoria(cat, products, ejes, ranked, tiendas_cat):
    """Preguntas y respuestas con los números del catálogo de hoy.

    Se marcan como FAQPage para que el buscador pueda mostrarlas como
    "People also ask". Ninguna respuesta se inventa: todas salen de
    `products`, así que si mañana cambia el catálogo cambia la respuesta.
    """
    nombre = cat["name"].lower()
    precios = sorted(pr for pr in (min_price(p) for p in products) if pr)
    qa = []
    if len(precios) >= 10:
        mediana = precios[len(precios) // 2]
        qa.append((
            f"¿Cuánto cuesta comprar {nombre} en México?",
            f"En ComparaMEX hay {len(precios):,} productos de {nombre} con precio. "
            f"El más barato está en {money(precios[0])}, el más caro en {money(precios[-1])} "
            f"y la mitad del catálogo se consigue por {money(mediana)} o menos."
        ))
    # La pregunta que más se escribe en el buscador. Va segunda, justo
    # después del precio: es la misma consulta al catálogo, y contestarla acá
    # -- y no solo en /barato/<slug>/ -- es lo que hace que la categoría
    # también pueda salir para "<producto> mas barato".
    baratos = _barato_listables(products, cat)
    if baratos:
        pr_b, p_b = baratos[0]
        sing_b = SINGULAR.get(cat["name"], (None, None))[0]
        qa.append((
            f"¿Cuál es {'el ' + sing_b if sing_b else 'el producto'} más barato en {nombre.lower()}?",
            f"Hoy es {p_b['name']}, en {money(pr_b)}"
            + (f", comparando {seller_total(p_b)} vendedores. " if seller_total(p_b) > 1 else ". ")
            + f"La lista completa, ordenada de menor a mayor precio y sin accesorios, "
              f"está en la página de {nombre.lower()} más baratos."
        ))
    if ranked:
        top = ranked[0]
        qa.append((
            f"¿Cuál es el producto más popular en {nombre}?",
            f"Hoy encabeza el ranking {top['name']}, desde {money(min_price(top))} "
            f"en {'una tienda' if seller_total(top) == 1 else f'{seller_total(top)} vendedores'}."
        ))
    if ejes:
        criterios = ", ".join(e[0]["label"].lower() for e in ejes)
        qa.append((
            f"¿Qué hay que mirar para elegir {nombre}?",
            f"En esta categoría lo que más separa un modelo de otro es: {criterios}. "
            f"Arriba, en \"Cómo elegir\", está el rango de cada uno con los valores "
            f"que hay hoy en el catálogo."
        ))
    if len(tiendas_cat) > 1:
        qa.append((
            f"¿En qué tiendas puedo comparar precios de {nombre}?",
            f"Esta categoría compara {len(tiendas_cat)} tiendas mexicanas: "
            f"{', '.join(sorted(tiendas_cat)[:8])}"
            + ("." if len(tiendas_cat) <= 8 else f" y {len(tiendas_cat) - 8} más.")
        ))
    if not qa:
        return "", ""
    html = "".join(
        f'<div class="faq-item"><h3>{html_escape(p)}</h3><p>{html_escape(r)}</p></div>'
        for p, r in qa
    )
    json_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": p,
             "acceptedAnswer": {"@type": "Answer", "text": r}}
            for p, r in qa
        ],
    }, ensure_ascii=False, indent=2)
    return (
        f'<div class="panel" id="preguntas">'
        f'<h2>{svg_icon("search")} Preguntas frecuentes</h2>{html}</div>'
    ), json_ld


# ---------------------------------------------------------------------
# La página de "lo más barato" de cada categoría
# ---------------------------------------------------------------------
# La búsqueda que más gente escribe no es "celulares" ni "mejores celulares":
# es "celular mas barato". Hoy esa búsqueda la contestan artículos de
# revista --una selección de siete modelos que alguien eligió a mano y que
# envejece en un mes-- porque no hay nadie contestándola con precios de
# verdad. Un comparador sí puede: la respuesta es una consulta al catálogo,
# y cambia sola todos los días.
#
# El singular hace falta porque la búsqueda va en singular ("celular mas
# barato", no "celulares mas baratos"). No se deduce con una regla: hay
# categorías compuestas ("Autos, bicicletas y motos") donde el singular no
# significa nada. Las que no están en el mapa publican la página igual, solo
# que el titular va en plural.
SINGULAR = {
    "Celulares": ("celular", "el"),
    "Laptops": ("laptop", "la"),
    "Tabletas": ("tableta", "la"),
    "Monitores": ("monitor", "el"),
    "Bocinas": ("bocina", "la"),
    "Teclados": ("teclado", "el"),
    "Televisores": ("televisor", "el"),
    "Lavadoras": ("lavadora", "la"),
    "Aspiradoras": ("aspiradora", "la"),
    "Cafeteras": ("cafetera", "la"),
    "Refrigeradores": ("refrigerador", "el"),
    "Impresoras": ("impresora", "la"),
    "Drones": ("dron", "el"),
    "Proyectores y accesorios": ("proyector", "el"),
    "Relojes inteligentes": ("reloj inteligente", "el"),
    "Cámaras de seguridad": ("cámara de seguridad", "la"),
    "Computadoras de escritorio": ("computadora de escritorio", "la"),
    "Audífonos y auriculares": ("audífono", "el"),
    "Baterías portátiles (power bank)": ("power bank", "el"),
    "Cargadores y adaptadores": ("cargador", "el"),
    "Videojuegos": ("videojuego", "el"),
    "Muebles": ("mueble", "el"),
    "Herramientas": ("herramienta", "la"),
    "Mascotas": ("producto para mascotas", "el"),
    "Juegos de mesa": ("juego de mesa", "el"),
    "Instrumentos musicales": ("instrumento musical", "el"),
    "Libros": ("libro", "el"),
    "Calzado": ("calzado", "el"),
    "Suplementos": ("suplemento", "el"),
    "Almacenamiento": ("disco", "el"),
}

# El producto más barato de una categoría casi nunca es el producto: es su
# accesorio. Medido el 21 de septiembre de 2026: en Refrigeradores ganaba un
# filtro de vegetales de $199, en Televisores un receptor de espejo de $224
# y en Herramientas una placa ciega de $38.
#
# Esto se tapaba con un patrón sobre el NOMBRE de la subcategoría más una
# lista escrita a mano. Ahora lo contesta roles_subcategorias.py, que dice
# qué papel juega cada subcategoría DENTRO de su categoría -- que es la
# pregunta correcta, porque un cable es accesorio en Celulares y es el
# producto en "Cargadores y adaptadores". La idea es de kakaku.com, que
# agrupa su portada de PC en 本体 / 周辺機器 / パーツ en vez de listar 125
# subcategorías en plano.

# Lo que queda después de los dos filtros de arriba son errores sueltos de
# clasificación, y esta página los premia: el filtro de agua metido en
# Refrigeradores vale $199 contra una mediana de miles, así que gana el
# primer puesto de "el refrigerador más barato". Esos los marca
# save_catalog con "a" (ver scripts/atipicos.py).


# Menos de esto la página sería una lista de veinte filas que dice lo mismo
# que la categoría: no aporta y gasta presupuesto de rastreo.
# Debajo de esto, el ranking de la categoría usa todas sus fichas en vez de
# sólo las del papel "producto": más vale un ranking con accesorios que uno
# de cuatro filas.
MIN_PARA_RANKING_PROPIO = 12

# Debajo de esto una categoría no publica página: cuatro filas no son una
# página de categoría, son una url vacía con un título.
MIN_PRODUCTOS_CATEGORIA = 12

MIN_PARA_PAGINA_BARATO = 40
BARATO_TOPE = 60


def _barato_listables(products, cat=None):
    """Los productos de la categoría que pueden encabezar un "más barato".

    Se van los accesorios (SUBCATEGORIAS_OPT_IN): en Celulares los veinte
    productos más baratos del catálogo son pegamento, pinzas de apertura y
    fundas. Una página que abra con eso contesta mal la pregunta y no la
    vuelve a leer nadie.
    """
    salida = []
    for p in products:
        sub = p.get("subcategory")
        # El papel de la subcategoría dentro de SU categoría: sólo el grupo
        # "producto" puede encabezar un "lo más barato".
        if sub in SUBCATEGORIAS_OPT_IN or not es_producto(p.get("category"), sub):
            continue
        # La ficha suelta MAL CLASIFICADA dentro de una subcategoría de
        # producto (el filtro de agua metido en Refrigeradores). Antes se
        # descartaba todo lo que valía menos del 15% de la mediana, y con
        # eso también la bocina de $179 que sí es una bocina; ahora se
        # descarta sólo lo que además no se llama como sus vecinas (la
        # marca "a" que pone save_catalog, ver atipicos.py).
        if p.get("a"):
            continue
        # Solo lo que tiene página propia, o sea lo que vieron dos tiendas.
        # No es un capricho de coherencia interna: la ficha de un solo
        # vendedor es de donde sale casi toda la basura mal clasificada, y
        # esta página la premia -- el error más barato de la categoría le
        # gana el titular al producto real. Medido hoy en Celulares: el
        # primer puesto era un micrófono de $75 metido en "Android", y el
        # segundo una pelota de voleibol en "Resistentes". Con dos tiendas
        # de por medio ese ruido no llega: nadie cruza un error con otro.
        if not tiene_pagina(p):
            continue
        pr = min_price(p)
        if pr:
            salida.append((pr, p))
    salida.sort(key=lambda t: (t[0], t[1]["name"]))
    return salida


def _fila_barato(pr, p, prefijo, puesto):
    """Misma fila que el ranking de la categoría, pero el puesto es el precio.

    La insignia de posición (.rank-badge) se reutiliza tal cual: acá el 1 no
    es "el más popular" sino "el más barato", y el resto del sitio ya sabe
    dibujarla.
    """
    n = seller_total(p)
    # Mismo medallero que el resto del sitio: corona al primero, y
    # dorado/plata/bronce del 2 al 4 (ver .rank-badge en style.css). Acá la
    # corona se la lleva el más barato, que es de lo que trata la página.
    clase = f" rank-{puesto}" if 2 <= puesto <= 4 else ""
    insignia = svg_icon("crown") if puesto == 1 else str(puesto)
    return (
        f'<div class="product-row has-rank{clase}">'
        f'<span class="rank-badge">{insignia}</span>'
        f'{product_photo_html(p, "row-icon")}'
        f'<div class="row-info">'
        f'<div class="row-brand">{html_escape(p["brand"])}</div>'
        f'<div class="row-name">{enlace_producto(p, prefijo)}</div>'
        f'<div class="muted small">'
        + (f'{html_escape(str(p.get("subcategory")))} &middot; ' if p.get("subcategory") else "")
        + (f'{n} vendedores comparados' if n > 1 else 'un vendedor')
        + f'</div></div>'
        f'<div class="row-priceblock">'
        f'<div class="row-from">Desde</div>'
        f'<div class="row-price">{money(pr)}</div></div>'
        f'</div>'
    )


def render_barato_page(cat, products, data):
    """/barato/<slug>/ — lo más económico de la categoría, con precio de hoy."""
    slug = slugify(cat["name"])
    nombre = cat["name"]
    plural = nombre.lower()
    sing, art = SINGULAR.get(nombre, (None, None))
    # "la lavadora más barato" no lo escribe nadie. El artículo ya trae el
    # género, así que el adjetivo sale de ahí.
    bar = "barata" if art == "la" else "barato"
    prefijo = "../../"
    canonical_path = f"/barato/{slug}/"

    orden = _barato_listables(products, cat)
    mostrados = orden[:BARATO_TOPE]
    barato_pr, barato_p = orden[0]
    precios = [pr for pr, _ in orden]
    mediana = precios[len(precios) // 2]

    if sing:
        h1 = f"{plural.capitalize()} más baratos de México"
        titulo_seo = f"{sing.capitalize()} más {bar} en México"
        pregunta = f"¿Cuál es {art} {sing} más {bar}?"
    else:
        h1 = f"{plural.capitalize()} más baratos de México"
        titulo_seo = f"{nombre} baratos en México"
        pregunta = f"¿Qué es lo más barato en {plural}?"

    # La respuesta corta va primero y en una sola frase: es la que el
    # buscador puede levantar tal cual como fragmento destacado.
    respuesta = (
        f"{'Hoy ' + art + ' ' + sing + ' más ' + bar + ' de México es' if sing else 'Hoy lo más barato es'} "
        f"{barato_p['name']}, en {money(barato_pr)}, "
        f"comparando {seller_total(barato_p)} vendedores."
    )

    # Lo más barato de cada tipo: es la tabla que un artículo de revista no
    # puede escribir, porque tendría que revisar el catálogo entero cada día.
    por_sub = {}
    for pr, p in orden:
        s = p.get("subcategory")
        if s and s not in por_sub:
            por_sub[s] = (pr, p)
    filas_sub = "".join(
        f'<tr><td>{html_escape(s)}</td>'
        f'<td>{enlace_producto(p, prefijo)}</td>'
        f'<td class="num">{money(pr)}</td></tr>'
        for s, (pr, p) in sorted(por_sub.items(), key=lambda kv: kv[1][0])[:25]
    )
    tabla_sub = (
        f'<div class="panel"><h2>{svg_icon("chart")} Lo más barato de cada tipo de '
        f'{plural}</h2><div class="tabla-scroll"><table class="tabla-barato">'
        f'<thead><tr><th>Tipo</th><th>El más barato hoy</th><th class="num">Precio</th></tr></thead>'
        f'<tbody>{filas_sub}</tbody></table></div></div>'
    ) if len(por_sub) >= 3 else ""

    tiendas_cat = sorted({
        store_by_id_name(p, o.get("storeId"))
        for _pr, p in orden for o in (p.get("offers") or []) if o.get("storeId")
    })

    filas = "".join(
        _fila_barato(pr, p, prefijo, i)
        for i, (pr, p) in enumerate(mostrados, start=1)
    )

    qa = [
        (pregunta, respuesta),
        (
            f"¿Cuánto hay que gastar como mínimo en {plural}?",
            f"De los {len(orden):,} {plural} con precio que compara ComparaMEX, "
            f"el más barato cuesta {money(precios[0])} y la mitad del catálogo "
            f"está por debajo de {money(mediana)}. Abajo de {money(precios[0])} "
            f"no hay nada hoy en las tiendas que seguimos."
        ),
    ]
    if len(tiendas_cat) > 1:
        qa.append((
            f"¿Dónde comprar {plural} baratos en México?",
            f"Esta lista compara el precio de cada modelo en {len(tiendas_cat)} tiendas: "
            f"{', '.join(tiendas_cat[:8])}"
            + ("." if len(tiendas_cat) <= 8 else f" y {len(tiendas_cat) - 8} más.")
            + " El precio que se muestra es el más bajo de todas ellas."
        ))
    faq_html = "".join(
        f'<div class="faq-item"><h3>{html_escape(p)}</h3><p>{html_escape(r)}</p></div>'
        for p, r in qa
    )

    migas = (
        f'<nav class="breadcrumb"><a href="{prefijo}">Inicio</a> &gt; '
        f'<a href="{prefijo}categoria/{slug}/">{html_escape(nombre)}</a> &gt; Más baratos</nav>'
    )

    body = f"""
{migas}
<div class="list-head"><h1>{html_escape(h1)}</h1></div>
<p class="lead-barato"><strong>{html_escape(pregunta)}</strong> {html_escape(respuesta)}</p>
<p class="muted small">Precios de {HOY_LARGO}, tomados de {len(tiendas_cat)} tiendas
mexicanas. La lista se rehace sola cada día: no es una selección escrita a
mano, es el catálogo ordenado de menor a mayor precio. No entran accesorios,
ni los productos que vimos en una sola tienda: un precio que nadie más
confirma no sirve para decir qué es lo más barato.</p>
{NOTA_LAG_HTML}
<div class="panel"><h2>{svg_icon("chart")} Los {len(mostrados)} {plural} más baratos de hoy</h2>
<div class="product-list">{filas}</div></div>
{tabla_sub}
<div class="panel" id="preguntas"><h2>{svg_icon("search")} Preguntas frecuentes</h2>{faq_html}</div>
<div class="panel" style="text-align:center; margin-top:20px">
  <a class="buy-btn" href="{prefijo}categoria/{slug}/">Ver {html_escape(plural)}: ranking, guía y filtros →</a>
</div>
"""
    breadcrumbs = breadcrumb_json_ld([
        ("Inicio", f"{SITE_URL}/"),
        (nombre, f"{SITE_URL}/categoria/{slug}/"),
        ("Más baratos", None),
    ])
    lista_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"{titulo_seo} — {MES_ANIO}",
        "numberOfItems": len([1 for _pr, p in mostrados if tiene_pagina(p)]),
        "itemListElement": [
            {"@type": "ListItem", "position": i,
             "url": f"{SITE_URL}/producto/{p['id']}/", "name": p["name"]}
            for i, (_pr, p) in enumerate(
                [x for x in mostrados if tiene_pagina(x[1])], start=1)
        ],
    }, ensure_ascii=False, indent=2)
    faq_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": p,
             "acceptedAnswer": {"@type": "Answer", "text": r}}
            for p, r in qa
        ],
    }, ensure_ascii=False, indent=2)
    extra_head = (
        f'<script type="application/ld+json">\n{breadcrumbs}\n</script>\n'
        f'<script type="application/ld+json">\n{lista_ld}\n</script>\n'
        f'<script type="application/ld+json">\n{faq_ld}\n</script>'
    )
    description = (
        f"{titulo_seo}, {MES_ANIO}: desde {money(precios[0])}. "
        f"{len(orden):,} modelos ordenados de menor a mayor precio, "
        f"comparados en {len(tiendas_cat)} tiendas. Sin accesorios."
    )[:158]
    title = f"{titulo_seo} — {MES_ANIO} | ComparaMEX"
    return page_shell(title, description, canonical_path, body, depth=2,
                      extra_head=extra_head,
                      og_image=next((p.get("photo") for _pr, p in mostrados if p.get("photo")), None))


def render_category_page(cat, products, data):
    slug = slugify(cat["name"])
    # El ranking de la categoría no lista las piezas sueltas; el conteo y los
    # enlaces a subcategorías sí las cuentan, porque su página existe.
    productos_listables = [
        p for p in products if p.get("subcategory") not in SUBCATEGORIAS_OPT_IN
    ]
    # Y el ranking tampoco lista lo que no es el producto de la categoría.
    # Medido el 21 de septiembre de 2026 en "Autos, bicicletas y motos": 8
    # de los 10 primeros eran amplificadores de auto, autoestéreos y cascos
    # de moto -- el primer vehículo aparecía en el sexto puesto. En
    # Televisores, el primero y el tercero eran sticks de Roku.
    #
    # No se pierden: cada uno sigue en su subcategoría, con su página y su
    # propio ranking, y desde acá se llega por los chips agrupados. Lo que
    # cambia es qué contesta esta página, que se llama "ranking de <la
    # categoría>". Si el corte dejara la lista casi vacía (una categoría
    # que sea casi toda accesorios), se usa el conjunto completo antes que
    # publicar un ranking de cuatro filas.
    del_papel_producto = [
        p for p in productos_listables
        if es_producto(cat["name"], p.get("subcategory"))
    ]
    pool_ranking = (del_papel_producto
                    if len(del_papel_producto) >= MIN_PARA_RANKING_PROPIO
                    else productos_listables)
    canonical_path = f"/categoria/{slug}/"
    # Igual que en la de subcategoría: Google corta cerca de los 160
    # caracteres. Acá se volcaban TODAS las marcas de la categoría (la de
    # Componentes de PC listaba más de 200), o sea una descripción que nadie
    # llega a leer y que se ve como relleno de palabras clave.
    por_marca = collections.Counter(p["brand"] for p in products if p.get("brand"))
    top_marcas = [m for m, _ in por_marca.most_common(5)]
    brands_note = f" Marcas como {', '.join(top_marcas)}." if top_marcas else ""
    description = (
        f"Compara precios de {cat['name'].lower()} entre tiendas mexicanas: "
        f"{len(products)} productos.{brands_note}"
    )
    # Mismo criterio de "popular" que la SPA (sortByPopularity en
    # js/app.js): ranking por reseñas totales, no por precio — es el paso 2
    # del recorrido categoría → populares → precio. Y con el mismo
    # desempate por número de vendedores: hoy ninguna oferta del catálogo
    # trae reseñas, así que sin él TODA la categoría empataba en 0 y el
    # "top 100" que ve el buscador era el orden crudo de importación.
    ranked = sorted(pool_ranking, key=lambda p: (total_review_count(p), seller_total(p)), reverse=True)
    # La página estática no es interactiva (no hay paginación de JS aquí),
    # así que se limita a un top fijo en vez de volcar la categoría entera:
    # sin esto, "Moda y accesorios" generaba un solo archivo HTML de ~4MB
    # con miles de filas. El resto queda a un clic con el link de abajo,
    # que ya manda a la SPA con filtros interactivos (y ahí sí paginada).
    shown = ranked[:STATIC_LIST_CAP]
    rows = []
    for i, p in enumerate(shown, start=1):
        corona = svg_icon("crown")
        rank_badge = corona if i == 1 else str(i)
        rank_class = f" rank-{i}" if 2 <= i <= 4 else ""
        variant_count = max([len(o.get("variants") or []) for o in p["offers"]], default=0)
        variant_badge = f'<span class="variant-count-badge" title="También disponible en otros colores/tallas">{svg_icon("palette")} +{variant_count}</span>' if variant_count else ""
        used_badge = f'<span class="used-badge" title="Producto usado/preowned">{svg_icon("rotate")} Usado</span>' if is_used(p) else ""
        # Mismos datos por fila que en la página de subcategoría: el orden y
        # el filtro de la página trabajan con ellos, y la calificación y los
        # vendedores se muestran porque un precio sin decir contra cuántas
        # tiendas se comparó no es una comparación.
        rating, n_reviews = aggregate_rating(p)
        n_vendedores = seller_total(p)
        rows.append(
            f'<div class="product-row has-rank{rank_class}"'
            f' data-price="{min_price(p)}" data-pop="{n_reviews}" data-rating="{rating}"'
            f' data-sellers="{n_vendedores}" data-corona="{html_escape(corona)}">'
            f'<span class="rank-badge">{rank_badge}</span>'
            f'{product_photo_html(p, "row-icon")}'
            f'<div class="row-info">'
            f'<div class="row-brand">{html_escape(p["brand"])}</div>'
            f'<div class="row-name">{enlace_producto(p, "../../")}{used_badge}{variant_badge}</div>'
            + (f'<div class="row-rating"><span class="row-stars">'
               f'{"★" * int(round(rating))}{"☆" * (5 - int(round(rating)))}</span> {rating} '
               f'<span class="row-rating-n">({n_reviews:,})</span></div>' if n_reviews else "")
            + f'</div>'
            f'<div class="row-priceblock">'
            f'<div class="row-from">Desde</div>'
            f'<div class="row-price">{money(min_price(p))}</div>'
            f'<div class="row-sellers">{svg_icon("shopping-bag")} '
            f'{plural(n_vendedores, "vendedor", "vendedores")}</div>'
            f'</div>'
            f'</div>'
        )
    more_note = (
        f"<p class=\"muted small\" style=\"text-align:center; margin-top:10px\">"
        f"Mostrando los {len(shown)} más populares de {len(pool_ranking)}.</p>"
        if len(pool_ranking) > len(shown) else ""
    )
    # Enlaces a las subcategorías con página propia. Sin esto esas páginas
    # solo serían alcanzables desde el sitemap, que es la peor forma de que
    # un buscador las encuentre y les dé importancia.
    # Los tipos, agrupados por el papel que juegan en la categoría (ver
    # roles_subcategorias.py). Antes era una sola fila: Muebles sacaba 66
    # chips seguidos donde "Camas" y "Accesorios y organizadores de
    # escritorio" pesaban lo mismo. Es lo que hace kakaku.com en su portada
    # de PC, que separa 本体 de 周辺機器 y de パーツ en vez de listar las 125
    # subcategorías de corrido.
    #
    # El grupo "Productos" no lleva encabezado: es lo que el visitante vino
    # a ver, y ponerle un título por encima sólo agrega un renglón entre él
    # y los chips. Los encabezados aparecen recién a partir del segundo
    # grupo, que es donde hacen falta para explicar el corte.
    # Y dentro de «Productos», un escalón más: las familias de
    # familias_subcategorias.py. Es el tercer nivel que usa kakaku: パソコン no
    # lista sus 125 subcategorías de corrido, las agrupa en ノートパソコン,
    # デスクトップ, PCパーツ. Sin esto Muebles seguía sacando cincuenta chips
    # seguidos con «Sillas de oficina» y «Colchones king size» al mismo nivel.
    subs_html = ""
    subs = subcategorias_con_pagina(cat, products)
    if subs:
        chip_de = {}
        por_rol = collections.OrderedDict((r, []) for r in ORDEN_ROLES)
        for sub, items in subs:
            chip_de[sub["name"]] = (
                f'<a class="chip" href="{slugify(sub["name"])}/">'
                f'{html_escape(sub["name"])} ({len(items)})</a>'
            )
            por_rol[rol_de(cat["name"], sub["name"])].append(sub["name"])
        cuenta_sub = {sub["name"]: len(items) for sub, items in subs}
        bloques = []
        for i, rol in enumerate(ORDEN_ROLES):
            if not por_rol[rol]:
                continue
            titulo = ("" if i == 0 else
                      f'<h3 class="grupo-rol">{html_escape(TITULOS_ROL[rol])}</h3>')
            if i == 0:
                familias = agrupar_familias(cat["name"], por_rol[rol], cuenta_sub)
                con_pagina = {f for f, _, _ in familias_con_pagina(cat, products)}
                filas = []
                for familia, miembros in familias:
                    if familia in con_pagina:
                        enc = (f'<h4 class="grupo-familia"><a href="{slugify(familia)}/">'
                               f'{html_escape(familia)}</a></h4>')
                    else:
                        enc = (f'<h4 class="grupo-familia">{html_escape(familia)}</h4>'
                               if familia else "")
                    filas.append(enc + '<div class="chip-row">'
                                 + "".join(chip_de[m] for m in miembros) + '</div>')
                bloques.append(titulo + "".join(filas))
            else:
                bloques.append(f'{titulo}<div class="chip-row">'
                               + "".join(chip_de[m] for m in por_rol[rol]) + '</div>')
        subs_html = (
            f'<div class="panel"><h2>Buscar por tipo de {html_escape(cat["name"].lower())}</h2>'
            + "".join(bloques) + '</div>'
        )

    # Enlace a las bajadas de precio de esta categoría, si tiene página. Sin
    # esto /ofertas/<cat>/ solo colgaría del sitemap.
    # Va como un chip más del índice de la página (pedido del usuario,
    # 21-sep): suelto y centrado ocupaba media pantalla y empujaba el
    # ranking fuera del primer vistazo.
    ofertas_chip = ""
    n_bajadas = sum(1 for p in products if bajada_de(p["id"]))
    if n_bajadas >= MIN_BAJADAS_PARA_PAGINA:
        ofertas_chip = (
            f'<a class="chip chip-icono" href="../../ofertas/{slug}/">'
            f'{svg_icon("chart")} {n_bajadas} bajaron de precio</a>'
        )

    # Las secciones nuevas (ver el bloque de arriba): salen del catálogo, no
    # de un texto fijo.
    ejes = ejes_de_categoria(cat, products, data)
    tiendas_cat = {o.get("storeId") for p in products for o in (p.get("offers") or []) if o.get("storeId")}
    nombres_tienda = {s["id"]: s.get("name") or s["id"] for s in (data.get("stores") or [])}
    faq_html, faq_json = faq_categoria(
        cat, products, ejes, shown, {nombres_tienda.get(t, t) for t in tiendas_cat})

    # Índice de la página, al estilo de las pestañas de kakaku.com: son
    # anclas, no pestañas de JavaScript, para que funcionen en la página
    # estática y el buscador las lea como enlaces internos.
    # El índice se arma con las secciones que de verdad se pintaron: una
    # categoría sin ejes no tiene "Cómo elegir", y una cuyas marcas no
    # llegan a tener página propia no tiene "Marcas". Enlazar a un ancla que
    # no existe deja el clic sin efecto.
    guia_html = como_elegir_html(cat, products, ejes)
    presu_html = presupuesto_html(cat, products)
    marcas_html = marcas_destacadas_html(por_marca)
    indice = []
    if guia_html:
        indice.append('<a class="chip" href="#como-elegir">Cómo elegir</a>')
    indice.append('<a class="chip" href="#ranking">Ranking</a>')
    if presu_html:
        indice.append('<a class="chip" href="#presupuesto">Por presupuesto</a>')
    if marcas_html:
        indice.append('<a class="chip" href="#marcas">Marcas</a>')
    if faq_html:
        indice.append('<a class="chip" href="#preguntas">Preguntas</a>')
    if ofertas_chip:
        indice.append(ofertas_chip)
    # El chip de "más baratos" va al final y con su propia página detrás: es
    # la entrada por la que llega quien buscó "<producto> mas barato", y
    # desde acá es también el enlace que la hace rastreable.
    if len(_barato_listables(products, cat)) >= MIN_PARA_PAGINA_BARATO:
        indice.append(
            f'<a class="chip chip-icono" href="../../barato/{slug}/">'
            f'{svg_icon("tag")} Los más baratos</a>'
        )
    indice_html = f'<div class="chip-row chip-row-indice">{"".join(indice)}</div>'

    body = f"""
<nav class="breadcrumb"><a href="../../">Inicio</a> &gt; {html_escape(cat['name'])}</nav>
<div class="list-head"><h1>{svg_icon("trophy")} {html_escape(cat['name'])}: los más populares de {MES_ANIO}</h1></div>
<p class="muted">{len(productos_listables)} productos comparados entre {len(tiendas_cat)} tiendas mexicanas. Precios actualizados el {HOY_LARGO}.</p>
{indice_html}
{subs_html}
{guia_html}
{presu_html}
<div class="panel" id="ranking"><h2>{svg_icon("crown")} Ranking de {html_escape(cat['name'].lower())} — {MES_ANIO}</h2>
{SORT_BAR_HTML}
<div class="product-list" id="lista">{''.join(rows)}</div></div>
<div class="panel" style="text-align:center; margin-top:20px">
  <a class="buy-btn" href="../../#/list?cat={quote(cat['id'])}">Ver con filtros interactivos →</a>
  {more_note}
</div>
{marcas_html}
{faq_html}
{LIST_JS}
"""
    breadcrumbs = breadcrumb_json_ld([
        ("Inicio", f"{SITE_URL}/"),
        (cat["name"], None),
    ])
    # El ranking, además, como ItemList: es lo que le dice al buscador que
    # esta página ES un ranking y en qué orden, que es justo la consulta que
    # se quiere ganar ("mejores <categoría> 2026").
    item_list = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"{cat['name']}: los más populares de {MES_ANIO}",
        "numberOfItems": len([p for p in shown[:10] if tiene_pagina(p)]),
        "itemListElement": [
            {"@type": "ListItem", "position": i,
             "url": f"{SITE_URL}/producto/{p['id']}/",
             "name": p["name"]}
            for i, p in enumerate([p for p in shown[:10] if tiene_pagina(p)], start=1)
        ],
    }, ensure_ascii=False, indent=2)
    extra_head = (
        f'<script type="application/ld+json">\n{breadcrumbs}\n</script>'
        f'<script type="application/ld+json">\n{item_list}\n</script>'
        + (f'<script type="application/ld+json">\n{faq_json}\n</script>' if faq_json else "")
    )
    title = f"{cat['name']}: ranking de los más populares — {MES_ANIO} | ComparaMEX"
    description = (
        f"Ranking de {cat['name'].lower()} en México, {MES_ANIO}: {len(productos_listables)} "
        f"productos comparados entre {len(tiendas_cat)} tiendas, cómo elegir y precios desde "
        f"{money(min((pr for pr in (min_price(p) for p in products) if pr), default=0))}."
    )[:300]
    return page_shell(title, description, canonical_path, body, depth=2, extra_head=extra_head)


# Límite real de Google es 50,000 URLs (y 50MB) por archivo de sitemap;
# se corta antes, en 40,000, para dejar margen y no rozarlo justo cuando el
# catálogo crezca un poco más entre una corrida y la siguiente.
SITEMAP_CHUNK_SIZE = 40000


# Fecha del último cambio REAL de cada página, para el <lastmod> del sitemap.
# Sin esto, un buscador que ve 82 mil URLs sin fecha no tiene forma de saber
# cuáles volver a rastrear y reparte el presupuesto a ciegas -- justo el
# problema de un catálogo donde cada día cambian de precio unas pocas miles de
# fichas y el resto queda igual. write_if_changed() ya sabe exactamente cuáles
# cambiaron; acá solo se guarda esa fecha entre corridas.
LASTMOD_FILE = os.path.join(ROOT, "data", "seo-lastmod.json")


def load_lastmod():
    try:
        with open(LASTMOD_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _xml_escape(text):
    return (
        str(text).replace("&", "&amp;").replace("<", "&lt;")
        .replace(">", "&gt;").replace('"', "&quot;")
    )


def _urlset_xml(urls, lastmod=None, images=None):
    """urls: lista de URLs. images: {url: foto} para el sitemap de imágenes.

    La extensión image: es la forma de decirle a Google que estas páginas
    tienen una foto asociada; sin ella tiene que descubrirlas rastreando el
    HTML. Con 80,632 fichas con foto, es la puerta a Búsqueda de Imágenes,
    que para un comparador de productos es tráfico de intención de compra.
    """
    lastmod = lastmod or {}
    images = images or {}
    filas = []
    for u in urls:
        partes = [f"<loc>{_xml_escape(u)}</loc>"]
        fecha = lastmod.get(u)
        if fecha:
            partes.append(f"<lastmod>{fecha}</lastmod>")
        foto = images.get(u)
        if foto:
            partes.append(f"<image:image><image:loc>{_xml_escape(foto)}</image:loc></image:image>")
        filas.append("  <url>" + "".join(partes) + "</url>")
    entries = "\n".join(filas)
    ns_image = (
        ' xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"' if images else ""
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"{ns_image}>\n'
        f"{entries}\n</urlset>\n"
    )


def write_sitemaps(data, root, lastmod=None, ofertas_urls=(), marca_urls=(),
                   barato_urls=()):
    """Escribe el árbol de sitemaps y devuelve las rutas escritas.

    Un solo sitemap.xml con más de 50,000 URLs es inválido para Google; en
    vez de eso, sitemap.xml pasa a ser un ÍNDICE (sitemapindex) que apunta a
    archivos separados -- las páginas de producto (la parte que más crece,
    se cortan en tandas de SITEMAP_CHUNK_SIZE) y un archivo aparte para el
    inicio + categorías (chico, no necesita cortarse). robots.txt sigue
    apuntando a sitemap.xml sin cambios: los buscadores siguen el índice
    solos hasta las URLs reales.
    """
    written = []

    page_urls = [f"{SITE_URL}/"]
    for cat in data["categories"]:
        cat_slug = slugify(cat["name"])
        page_urls.append(f"{SITE_URL}/categoria/{cat_slug}/")
        productos_cat = [p for p in data["products"] if p["category"] == cat["id"]]
        for sub, _ in subcategorias_con_pagina(cat, productos_cat):
            page_urls.append(f"{SITE_URL}/categoria/{cat_slug}/{slugify(sub['name'])}/")
        for familia, _, _ in familias_con_pagina(cat, productos_cat):
            page_urls.append(f"{SITE_URL}/categoria/{cat_slug}/{slugify(familia)}/")
    page_urls.extend(ofertas_urls)
    page_urls.extend(barato_urls)
    page_urls.extend(marca_urls)
    pages_path = os.path.join(root, "sitemap-pages.xml")
    if write_if_changed(pages_path, _urlset_xml(page_urls, lastmod)):
        written.append(pages_path)
    sitemap_files = ["sitemap-pages.xml"]

    product_urls = []
    product_images = {}
    for p in data["products"]:
        if not tiene_pagina(p):
            continue
        u = f"{SITE_URL}/producto/{p['id']}/"
        product_urls.append(u)
        if p.get("photo"):
            product_images[u] = p["photo"]
    chunks = [product_urls[i:i + SITEMAP_CHUNK_SIZE] for i in range(0, len(product_urls), SITEMAP_CHUNK_SIZE)] or [[]]
    for i, chunk in enumerate(chunks, 1):
        name = f"sitemap-products-{i}.xml"
        path = os.path.join(root, name)
        if write_if_changed(path, _urlset_xml(chunk, lastmod, product_images)):
            written.append(path)
        sitemap_files.append(name)

    # Si el catálogo encogió, sobran archivos de una tanda anterior. El
    # índice deja de nombrarlos, pero el archivo se queda publicado con sus
    # URLs viejas -- sitemap-products-3.xml sobrevivió así con 703 productos,
    # uno de ellos ya dado de baja (404 servido desde un sitemap). Se borran.
    sobrante = len(chunks) + 1
    while True:
        viejo = os.path.join(root, f"sitemap-products-{sobrante}.xml")
        if not os.path.exists(viejo):
            break
        os.remove(viejo)
        written.append(viejo + " (borrado)")
        sobrante += 1

    index_entries = "\n".join(f"  <sitemap><loc>{SITE_URL}/{name}</loc></sitemap>" for name in sitemap_files)
    index_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{index_entries}\n</sitemapindex>\n"
    )
    index_path = os.path.join(root, "sitemap.xml")
    if write_if_changed(index_path, index_xml):
        written.append(index_path)
    return written


# Bots de IA conocidos (entrenamiento de modelos, o que un asistente de IA
# use en el momento para "leer" una página y contestar con eso) -- se
# bloquean explícitamente por nombre, aparte del "Allow: /" general para
# buscadores normales (Googlebot, Bingbot, etc.), que se deja intacto para
# no perder el tráfico de búsqueda que scripts/generate_seo_pages.py existe
# para conseguir.
#
# OJO, esto es best-effort: robots.txt es una convención que un bot
# CUMPLIDOR respeta porque quiere (así lo hacen OpenAI/Anthropic/Google
# según sus propias políticas publicadas), pero nada impide que un scraper
# que no le importa las reglas lo ignore -- no hay forma de "garantizar"
# el bloqueo solo con este archivo. El bloqueo real, a nivel de red (que sí
# corta tráfico que miente sobre su User-Agent), depende de si el hosting
# lo ofrece -- p. ej. el toggle "Block AI Bots" del panel de Cloudflare
# (Security -> Bots), que huella la conexión en vez de confiar en el
# nombre que el visitante dice tener.
_AI_BOT_USER_AGENTS = [
    # OpenAI
    "GPTBot", "ChatGPT-User", "OAI-SearchBot",
    # Anthropic
    "ClaudeBot", "Claude-Web", "anthropic-ai", "Claude-SearchBot", "Claude-User",
    # Common Crawl (fuente de entrenamiento de facto para casi todo modelo grande)
    "CCBot",
    # Google (entrenamiento de modelos -- Googlebot normal, de búsqueda, NO se toca)
    "Google-Extended",
    # Apple (Apple Intelligence -- Applebot normal, de búsqueda, NO se toca)
    "Applebot-Extended",
    # Meta / Facebook
    "FacebookBot", "Meta-ExternalAgent", "Meta-ExternalFetcher",
    # ByteDance / TikTok
    "Bytespider",
    # Perplexity
    "PerplexityBot", "Perplexity-User",
    # Amazon
    "Amazonbot",
    # Cohere
    "cohere-ai", "cohere-training-data-crawler",
    # You.com
    "YouBot",
    # Diffbot
    "Diffbot",
    # webz.io (vende datos de entrenamiento)
    "Omgilibot", "Omgili", "Webzio-Extended",
    "ICC-Crawler",
    "Timpibot",
    "ImagesiftBot",
    # Allen Institute for AI (dataset Dolma/OLMo)
    "Ai2Bot", "Ai2Bot-Dolma",
    # Mistral
    "MistralAI-User",
]


def write_if_changed(path, body):
    """Escribe solo si el contenido cambió; devuelve True si escribió.

    Con 84 mil páginas de producto, reescribirlas todas en cada corrida de
    precios (ver .github/workflows/refresh-prices.yml) metería 84 mil
    archivos "modificados" en cada commit aunque solo se hubiera movido un
    precio -- el historial de git crecería varios GB al año y el diff de
    cada corrida sería ilegible. Comparando antes de escribir, el commit
    muestra exactamente qué páginas cambiaron de verdad.
    """
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            if f.read() == body:
                return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    return True


def render_producto_retirado(product, data):
    """Página de un producto que dejó de publicarse.

    El catálogo solo publica ficha cuando hay dos o más tiendas vendiendo
    (MIN_OFERTAS_PARA_PAGINA): comparar precios con un solo vendedor no es
    comparar nada. Pero cuando una ficha baja del mínimo, su url ya está
    indexada, y borrar la carpeta mandaba a un 404 a quien llegaba desde un
    resultado de Google. Un callejón sin salida.

    Esta página dice por qué no está y ofrece la salida más cercana: su
    subcategoría, su categoría y unos cuantos productos hermanos que sí
    tienen ficha. Va con noindex para que el buscador la deje ir, y con
    follow para que siga los enlaces de salida.
    """
    cat = next((c for c in data["categories"] if c["id"] == product.get("category")), None)
    cat_slug = slugify(cat["name"]) if cat else ""
    sub_nombre = product.get("subcategory")
    sub_slug = slugify(sub_nombre) if sub_nombre else ""
    # Hermanos con página: los de la misma subcategoría, y si no alcanzan,
    # los de la categoría. Se ordenan por número de tiendas, que es lo que
    # hace útil una comparación.
    def _con_pagina(lista):
        return [q for q in lista if q["id"] != product["id"] and q["id"] in _CON_PAGINA]
    mismos = [q for q in data["products"] if q.get("category") == product.get("category")]
    hermanos = _con_pagina([q for q in mismos if q.get("subcategory") == sub_nombre]) if sub_nombre else []
    if len(hermanos) < 6:
        hermanos += [q for q in _con_pagina(mismos) if q not in hermanos]
    hermanos.sort(key=lambda q: -len(q.get("offers") or []))
    hermanos = hermanos[:8]

    filas = "".join(
        f'<li><a href="../../producto/{q["id"]}/">{html_escape(q["name"])}</a>'
        f' <span class="muted">· {len(q.get("offers") or [])} tiendas</span></li>'
        for q in hermanos
    )
    salidas = []
    if cat and sub_slug:
        salidas.append(f'<a class="chip" href="../../categoria/{cat_slug}/{sub_slug}/">'
                       f'{html_escape(sub_nombre)}</a>')
    if cat:
        salidas.append(f'<a class="chip" href="../../categoria/{cat_slug}/">'
                       f'{html_escape(cat["name"])}</a>')
    body = f"""
<div class="panel">
  <h1>{html_escape(product["name"])}</h1>
  <p class="muted">Ya no publicamos esta ficha: hoy la vende una sola tienda, y
     ComparaMEX existe para comparar entre varias. Si vuelve a haber dos o más,
     la ficha vuelve sola.</p>
  <p>{"".join(salidas)}</p>
</div>
{f'''<div class="panel">
  <h2>Productos parecidos que sí puedes comparar</h2>
  <ul class="plain-list">{filas}</ul>
</div>''' if filas else ""}
<div class="panel" style="text-align:center">
  <p><a class="buy-btn" href="../../">Volver al inicio de ComparaMEX →</a></p>
</div>
"""
    return page_shell(
        f'{product["name"]} — ya no disponible | ComparaMEX',
        "Esta ficha dejó de publicarse porque hoy la vende una sola tienda. "
        "Mira productos parecidos con varias tiendas.",
        f'/producto/{product["id"]}/', body, depth=2, robots="noindex, follow",
    )


REDIRECCIONES_PATH = os.path.join(ROOT, "data", "redirecciones.json")


def render_redireccion(destino):
    """Página que manda a `destino` (ruta relativa a la raíz del sitio).

    GitHub Pages no sirve 301, así que esto es lo que Google trata como una:
    canonical al destino y refresh inmediato. Sin ella, renombrar una
    subcategoría dejaba la url vieja --ya indexada y quizá enlazada-- en un
    404, y lo ganado por esa página se perdía.
    """
    url = f"{SITE_URL}/{destino}"
    return f"""<!DOCTYPE html>
<html lang="es-MX">
<head>
<meta charset="utf-8">
<title>Esta sección se mudó | ComparaMEX</title>
<link rel="canonical" href="{url}">
<meta http-equiv="refresh" content="0; url=/{destino}">
</head>
<body>
<p>Esta sección ahora está en <a href="/{destino}">{url}</a>.</p>
</body>
</html>
"""


def escribir_redirecciones(data):
    """Escribe las páginas de data/redirecciones.json. Devuelve (escritas,
    rutas viejas a conservar)."""
    if not os.path.exists(REDIRECCIONES_PATH):
        return [], set()
    with open(REDIRECCIONES_PATH, encoding="utf-8") as f:
        rutas = json.load(f).get("rutas", {})
    # Una ruta vieja que volvió a ser subcategoría (o categoría) de verdad es
    # de la página, no de la redirección.
    vigentes = set()
    for cat in data["categories"]:
        cs = slugify(cat["name"])
        vigentes.add(f"categoria/{cs}/")
        for sub in cat.get("subcategories") or []:
            vigentes.add(f"categoria/{cs}/{slugify(sub['name'])}/")
    escritas, conservar = [], set()
    for vieja, nueva in rutas.items():
        vieja, nueva = vieja.strip("/") + "/", nueva.strip("/") + "/"
        if not os.path.exists(os.path.join(ROOT, nueva, "index.html")):
            # El destino no tiene página (bajó del mínimo): la categoría de
            # arriba es mejor aterrizaje que un 404.
            padre = "/".join(nueva.strip("/").split("/")[:2]) + "/"
            if not os.path.exists(os.path.join(ROOT, padre, "index.html")):
                continue
            nueva = padre
        if vieja in vigentes:
            continue
        # Sólo las urls que llegaron a publicarse: una subcategoría que nunca
        # tuvo página (bajo el mínimo) no tiene nada que redirigir.
        if not os.path.isdir(os.path.join(ROOT, vieja)):
            continue
        ruta = os.path.join(ROOT, vieja, "index.html")
        if write_if_changed(ruta, render_redireccion(nueva)):
            escritas.append(ruta)
        conservar.add(vieja)
    return escritas, conservar


def borrar_paginas_huerfanas(data, ofertas_vigentes, marcas_vigentes=None,
                             barato_vigentes=None, dry_run=False, conservar=frozenset()):
    """Borra las páginas de productos y categorías que ya no están.

    `ofertas_vigentes` son los slugs de categoría que SÍ tuvieron página de
    bajadas en esta corrida ("" es la general). Las demás se borran: una
    página de bajadas que dejó de reescribirse seguía publicada con las
    bajadas del día que se escribió, ya sin respaldo en el historial.

    write_if_changed() solo escribe; nada borraba. Cuando refresh_prices.py
    poda una publicación que Mercado Libre dio de baja, el producto sale del
    catálogo pero su página seguía publicada, con el precio del día que
    murió. Medido: 1,078 fichas así, indexables y con un precio que ya no
    existe -- exactamente lo que un comparador no puede tener.

    Solo se borra lo que este mismo script genera (producto/<id>/,
    categoria/<slug>/ y sus subcategorías, ofertas/<slug>/) y solo si el id o
    el slug no está en el catálogo de esta corrida.
    """
    # "Vivo" es el que TIENE página, no el que está en el catálogo: cuando
    # un producto se queda con una sola oferta deja de publicarse y su
    # carpeta se borra acá.
    vivos = {p["id"] for p in data["products"] if tiene_pagina(p)}
    en_catalogo = {p["id"]: p for p in data["products"]}
    borrados = {"producto": 0, "categoria": 0, "ofertas": 0, "marca": 0,
                "barato": 0}
    retirados = 0

    carpeta = os.path.join(ROOT, "producto")
    if os.path.isdir(carpeta):
        for nombre in os.listdir(carpeta):
            ruta = os.path.join(carpeta, nombre)
            if not os.path.isdir(ruta) or nombre in vivos:
                continue
            producto = en_catalogo.get(nombre)
            if producto is not None:
                # Sigue en el catálogo, solo bajó del mínimo de tiendas: en
                # vez de borrar la carpeta y mandar un 404 a quien venga de
                # Google, queda una página que explica y ofrece salidas.
                if not dry_run:
                    write_if_changed(os.path.join(ruta, "index.html"),
                                     render_producto_retirado(producto, data))
                retirados += 1
                continue
            borrados["producto"] += 1
            if not dry_run:
                shutil.rmtree(ruta)
    if retirados:
        print(f"Fichas retiradas (una sola tienda, con página de salida): {retirados:,}")

    slugs_cat = {slugify(c["name"]) for c in data["categories"]}
    subs_por_cat = {}
    for cat in data["categories"]:
        productos_cat = [p for p in data["products"] if p["category"] == cat["id"]]
        subs_por_cat[slugify(cat["name"])] = {
            slugify(f) for f, _, _ in familias_con_pagina(cat, productos_cat)
        } | {
            slugify(sub["name"]) for sub, _ in subcategorias_con_pagina(cat, productos_cat)
        }

    carpeta = os.path.join(ROOT, "categoria")
    if os.path.isdir(carpeta):
        for nombre in os.listdir(carpeta):
            ruta = os.path.join(carpeta, nombre)
            if not os.path.isdir(ruta):
                continue
            if nombre not in slugs_cat:
                borrados["categoria"] += 1
                if not dry_run:
                    shutil.rmtree(ruta)
                continue
            # Subcategorías que dejaron de tener página propia (bajaron del
            # mínimo, o se renombraron).
            for sub in os.listdir(ruta):
                sub_ruta = os.path.join(ruta, sub)
                if f"categoria/{nombre}/{sub}/" in conservar:
                    continue  # redirección de una subcategoría renombrada
                if os.path.isdir(sub_ruta) and sub not in subs_por_cat[nombre]:
                    # Una subcategoría que deja de tener página (bajó del
                    # mínimo, se repartió) ya pudo quedar indexada o enlazada
                    # desde afuera: en vez de un 404 queda una redirección a
                    # su categoría. La que ya es redirección se deja como está.
                    indice = os.path.join(sub_ruta, "index.html")
                    try:
                        with open(indice, encoding="utf-8") as f:
                            ya_redirige = 'http-equiv="refresh"' in f.read(3000)
                    except OSError:
                        ya_redirige = False
                    if ya_redirige:
                        continue
                    borrados["categoria"] += 1
                    if not dry_run:
                        shutil.rmtree(sub_ruta)
                        if os.path.exists(os.path.join(ruta, "index.html")):
                            os.makedirs(sub_ruta, exist_ok=True)
                            write_if_changed(indice, render_redireccion(f"categoria/{nombre}/"))

    carpeta = os.path.join(ROOT, "ofertas")
    if os.path.isdir(carpeta):
        for nombre in os.listdir(carpeta):
            ruta = os.path.join(carpeta, nombre)
            if os.path.isdir(ruta) and nombre not in ofertas_vigentes:
                borrados["ofertas"] += 1
                if not dry_run:
                    shutil.rmtree(ruta)
        general = os.path.join(carpeta, "index.html")
        if "" not in ofertas_vigentes and os.path.exists(general):
            borrados["ofertas"] += 1
            if not dry_run:
                os.remove(general)

    # Las marcas se caen de la lista cuando bajan del mínimo de productos
    # (marcas_con_pagina), y su carpeta se quedaba publicada: 13 páginas de
    # marca sobrevivían de corridas viejas, con precios de hace días y, desde
    # que las fichas finas dejaron de publicarse, con 116 enlaces a 404.
    # marca/index.html es el listado de todas y no se toca.
    if marcas_vigentes is not None:
        carpeta = os.path.join(ROOT, "marca")
        if os.path.isdir(carpeta):
            for nombre in os.listdir(carpeta):
                ruta = os.path.join(carpeta, nombre)
                if os.path.isdir(ruta) and nombre not in marcas_vigentes:
                    borrados["marca"] += 1
                    if not dry_run:
                        shutil.rmtree(ruta)

    # Igual que las de marca: una categoría que se queda por debajo del
    # mínimo deja de generar su página de "lo más barato" y la vieja seguía
    # publicada, con los precios del día en que se escribió.
    if barato_vigentes is not None:
        carpeta = os.path.join(ROOT, "barato")
        if os.path.isdir(carpeta):
            for nombre in os.listdir(carpeta):
                ruta = os.path.join(carpeta, nombre)
                if os.path.isdir(ruta) and nombre not in barato_vigentes:
                    borrados["barato"] += 1
                    if not dry_run:
                        shutil.rmtree(ruta)

    return borrados


def render_404(data):
    """Página de error de GitHub Pages.

    Sin un 404.html propio, cualquier url mala del dominio caía en la página
    genérica de GitHub: sin la marca, sin un solo enlace de vuelta al sitio y
    sin forma de seguir buscando. Un rastreador que llega ahí no tiene por
    dónde continuar. Va con noindex, que es lo correcto para un error.
    """
    cats = "".join(
        f'<a class="chip" href="/categoria/{slugify(c["name"])}/">{html_escape(c["name"])}</a>'
        for c in data["categories"]
    )
    # Cuando la url es la de una ficha que dejó de publicarse, esta misma
    # página se convierte en su despedida: GitHub Pages sirve /404.html para
    # CUALQUIER url mala, así que basta con mirar la dirección. El nombre y
    # la categoría salen de data/retirados/, partido en trozos de 2,000 ids
    # para bajar 240 KB y no el índice entero (ver
    # scripts/build_retirados_index.py). Escribir una página de verdad para
    # cada una serían 197 mil archivos HTML, doce veces lo que publica el
    # sitio, y eso deshace lo que se ganó publicando solo lo comparable.
    script = """
<script>
(function () {
  var m = location.pathname.match(/\\/producto\\/(p(\\d+))\\/?$/);
  if (!m) return;
  var caja = document.getElementById('retirado');
  if (!caja) return;
  var base = '/data/retirados/';
  fetch(base + 'meta.json').then(function (r) { return r.json(); }).then(function (meta) {
    return fetch(base + Math.floor(+m[2] / meta.tamano) + '.json')
      .then(function (r) { return r.json(); })
      .then(function (trozo) { return { meta: meta, ficha: trozo[m[1]] }; });
  }).then(function (d) {
    if (!d.ficha) return;
    var nombre = d.ficha[0], i = d.ficha[1], sub = d.ficha[2];
    var slug = i >= 0 ? d.meta.slugs[i] : null;
    var cat = i >= 0 ? d.meta.categorias[i] : null;
    var h = document.createElement('div');
    var enlaces = '';
    if (slug) {
      if (sub) {
        enlaces += '<a class="chip" href="/categoria/' + slug + '/' +
          sub.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '')
             .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') + '/">' + sub + '</a>';
      }
      enlaces += '<a class="chip" href="/categoria/' + slug + '/">' + cat + '</a>';
    }
    h.innerHTML = '<h1>' + nombre + '</h1>' +
      '<p class="muted">Ya no publicamos esta ficha: hoy la vende una sola tienda, y ' +
      'ComparaMEX existe para comparar entre varias. Si vuelve a haber dos o más, la ficha vuelve sola.</p>' +
      (enlaces ? '<p>' + enlaces + '</p>' : '');
    caja.innerHTML = '';
    caja.appendChild(h);
    caja.style.textAlign = 'left';
    document.title = nombre + ' — ya no disponible | ComparaMEX';
  }).catch(function () {});
})();
</script>
"""
    body = f"""
<div class="panel" id="retirado" style="text-align:center">
  <h1>Esta página no existe</h1>
  <p class="muted">Puede que el producto ya no esté en el catálogo, o que la dirección tenga un error.</p>
  <p><a class="buy-btn" href="/">Volver al inicio de ComparaMEX →</a></p>
</div>
<div class="panel">
  <h2>Buscar por categoría</h2>
  <div class="chip-row">{cats}</div>
</div>
{script}
"""
    return page_shell(
        "Página no encontrada | ComparaMEX",
        "La página que buscas no existe. Vuelve al inicio de ComparaMEX o busca por categoría.",
        "/404.html", body, depth=None, robots="noindex, follow",
    )


def build_robots():
    ai_block = "".join(f"User-agent: {ua}\nDisallow: /\n\n" for ua in _AI_BOT_USER_AGENTS)
    return (
        f"{ai_block}"
        "User-agent: *\n"
        "Allow: /\n"
        # data/ son los archivos JSON crudos del catálogo (ver
        # scripts/data_io.py) -- ni Google ni Bing necesitan indexarlos (lo
        # que indexan son las páginas HTML de producto/categoría, que ya
        # traen el contenido renderizado), y de paso quita la ruta más
        # directa para bajarse el catálogo entero saltándose las páginas.
        "Disallow: /data/\n"
        f"Sitemap: {SITE_URL}/sitemap.xml\n"
    )


def hide_empty_taxonomy(data):
    """Quita categorías y subcategorías que se quedaron sin productos, o
    con tan pocos que su página no dice nada.

    Mismo criterio que `hideEmptyTaxonomy` en js/app.js: una subcategoría
    vacía es un enlace a una lista vacía, y como página estática además sería
    contenido indexable sin nada dentro.

    El mínimo no estaba y hacía falta. Medido el 21 de septiembre de 2026:
    "Calzado" publicaba su página con CUATRO productos y "Fitness" con ocho
    repartidos en Grande / Mediana / Pequeña. Una página de categoría con
    cuatro filas no ayuda a nadie y, para un buscador, es exactamente lo que
    penaliza: una url indexable sin contenido. Las que no llegan siguen
    existiendo en el catálogo y sus fichas se ven en la búsqueda y en su
    página de producto; lo que no tienen es página de categoría propia.
    """
    with_products = collections.Counter()
    for p in data.get("products", []):
        with_products[(p["category"], p.get("subcategory") or "")] += 1
        with_products[p["category"]] += 1
    cats = []
    for c in data.get("categories", []):
        if with_products[c["id"]] < MIN_PRODUCTOS_CATEGORIA:
            continue
        c = dict(c)
        c["subcategories"] = [
            s for s in c.get("subcategories", []) if with_products[(c["id"], s["id"])]
        ]
        cats.append(c)
    data["categories"] = cats
    return data



# ---------------------------------------------------------------------------
# Páginas de marca (/marca/<slug>/)
# ---------------------------------------------------------------------------
# Falta un eje entero de navegación. El sitio tiene páginas por categoría, por
# subcategoría y por producto, pero "samsung precios mexico" o "colchones
# restonic" no llegan a ninguna parte: el que busca por marca entra a una
# ficha suelta o a nada. Son consultas de mitad de embudo, con intención de
# compra, y un comparador puede contestarlas mejor que la propia marca porque
# muestra el precio en varias tiendas a la vez.
#
# También le da a cada ficha un segundo enlace interno desde una página
# temática distinta de su categoría, que es lo que hace que una ficha
# enterrada a tres clics del inicio se rastree.

MIN_PRODUCTOS_MARCA = 20

# clave de marca -> slug de su página. Se llena en main() una sola vez; las
# páginas de subcategoría lo consultan para enlazar sin recalcular nada.
_SLUG_DE_MARCA = {}

# Marcas que no son marcas. El catálogo usa el campo para lo que la tienda
# haya puesto ahí, y a veces pone "GENERICO" o su propio nombre (los libros de
# Gandhi vienen todos con brand=Gandhi porque el importador no lee la
# editorial). Una página de "marca Genérico" con 2,899 productos sueltos no
# contesta ninguna búsqueda y se lee como spam.
MARCAS_EXCLUIDAS = {
    "generico", "generica", "genericos", "genericas", "generic", "sinmarca",
    "nodisponible", "na", "otros", "varios", "importado", "oem",
    # Nombres de tienda que quedaron en el campo de marca.
    "gandhi", "aliexpress", "chedraui", "maskota", "miniso", "elektra",
    "marti", "juguetron", "doto", "sunsky", "geekbuying",
}


def clave_marca(nombre):
    """Misma marca escrita de otra forma -> misma clave.

    En el catálogo conviven SAMSUNG con 2,262 fichas y Samsung con 182; sin
    agrupar saldrían dos páginas compitiendo entre ellas por la misma
    búsqueda, que es lo peor que se puede hacer en SEO.
    """
    n = unicodedata.normalize("NFKD", nombre or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", n.lower())


def nombre_canonico(grafias):
    """La grafía que se muestra, entre todas las que usa el catálogo.

    Se prefiere una que NO esté toda en mayúsculas, porque suele ser la que
    escribió una persona ("VentDepot" antes que "VENTDEPOT"). Si todas gritan,
    se pasa a capitalización de título salvo las siglas cortas, que se quedan
    como están: HP, JBL y LG no son "Hp", "Jbl" ni "Lg".
    """
    mixtas = {g: n for g, n in grafias.items() if not g.isupper()}
    if mixtas:
        return max(mixtas.items(), key=lambda kv: kv[1])[0]
    top = max(grafias.items(), key=lambda kv: kv[1])[0]
    return top if len(top) <= 4 else top.title()


def marcas_con_pagina(data):
    """[(nombre, slug, productos)] de las marcas que llegan al mínimo."""
    por_clave = collections.defaultdict(lambda: (collections.Counter(), []))
    for p in data["products"]:
        b = (p.get("brand") or "").strip()
        if not b:
            continue
        k = clave_marca(b)
        if not k or k in MARCAS_EXCLUIDAS:
            continue
        grafias, items = por_clave[k]
        grafias[b] += 1
        items.append(p)
    salida = []
    usados = {}
    for k, (grafias, items) in por_clave.items():
        if len(items) < MIN_PRODUCTOS_MARCA:
            continue
        nombre = nombre_canonico(grafias)
        # El slug se arma del nombre, con guiones: /marca/spring-air/ se lee y
        # se comparte mejor que /marca/springair/. La clave de agrupación NO
        # sirve como slug justamente porque aplasta los espacios.
        slug = slugify(nombre) or k
        if usados.get(slug, k) != k:      # dos marcas distintas, mismo slug
            slug = f"{slug}-{k[:6]}"
        usados[slug] = k
        salida.append((nombre, slug, items))
    salida.sort(key=lambda x: -len(x[2]))
    return salida


def render_brand_page(nombre, slug, products, data):
    precios = [min_price(p) for p in products if p.get("offers")]
    rango = ""
    if precios:
        rango = f" Precios desde {money(min(precios))} hasta {money(max(precios))} MXN."
    por_cat = collections.Counter(p["category"] for p in products)
    cats_top = [c for c, _ in por_cat.most_common(4)]
    cats_note = f" Principalmente en {', '.join(c.lower() for c in cats_top)}." if cats_top else ""
    description = (
        f"Precios de {nombre} en México comparados entre tiendas: "
        f"{len(products)} productos.{rango}{cats_note}"
    )

    logo = logo_de_marca(slug)
    logo_titulo = (f'<img class="marca-logo-titulo" src="../../{logo}" alt="Logo de {html_escape(nombre)}">'
                   if logo else svg_icon("tag"))

    ranked = sorted(products, key=lambda p: (total_review_count(p), seller_total(p)), reverse=True)
    shown = ranked[:STATIC_LIST_CAP]
    rows = []
    for i, p in enumerate(shown, start=1):
        corona = svg_icon("crown")
        rank_badge = corona if i == 1 else str(i)
        rank_class = f" rank-{i}" if 2 <= i <= 4 else ""
        used_badge = (
            f'<span class="used-badge" title="Producto usado/preowned">{svg_icon("rotate")} Usado</span>'
            if is_used(p) else ""
        )
        # Los datos con los que la página ordena y filtra viajan en la fila
        # (mismo esquema que las páginas de subcategoría): precio, reseñas,
        # calificación, vendedores y la categoría.
        rating, n_reviews = aggregate_rating(p)
        n_vendedores = seller_total(p)
        n_tiendas = len({o.get("storeId") for o in purchase_options(p)})
        vendedores = (
            (f'{plural(n_tiendas, "tienda", "tiendas")} · ' if n_tiendas > 1 else "")
            + plural(n_vendedores, "vendedor", "vendedores")
        )
        rows.append(
            f'<div class="product-row has-rank{rank_class}"'
            f' data-price="{min_price(p)}" data-pop="{n_reviews}" data-rating="{rating}"'
            f' data-sellers="{n_vendedores}" data-stores="{n_tiendas}" data-corona="{html_escape(corona)}"'
            f' data-cat="{html_escape(p.get("category") or "")}">'
            f'<span class="rank-badge">{rank_badge}</span>'
            f'{product_photo_html(p, "row-icon")}'
            f'<div class="row-info">'
            f'<div class="row-brand">{html_escape(p.get("category") or "")}</div>'
            f'<div class="row-name">{enlace_producto(p, "../../")}{used_badge}</div>'
            + (f'<div class="row-rating"><span class="row-stars">'
               f'{"★" * int(round(rating))}{"☆" * (5 - int(round(rating)))}</span> {rating} '
               f'<span class="row-rating-n">({n_reviews:,})</span></div>' if n_reviews else "")
            + f'</div>'
            f'<div class="row-priceblock">'
            f'<div class="row-from">Desde</div>'
            f'<div class="row-price">{money(min_price(p))}</div>'
            f'<div class="row-sellers">{svg_icon("shopping-bag")} {vendedores}</div>'
            f'</div>'
            f'</div>'
        )
    more_note = (
        f'<p class="muted small" style="text-align:center; margin-top:10px">'
        f'Mostrando los {len(shown)} más populares de {len(products)}.</p>'
        if len(products) > len(shown) else ""
    )

    # En qué categorías vende la marca, con enlace: es la forma natural de
    # seguir navegando desde acá, y cruza el eje de marca con el de categoría.
    chips = []
    for cat_id, n in por_cat.most_common(12):
        cat = next((c for c in data["categories"] if c["id"] == cat_id), None)
        if cat:
            chips.append(
                f'<a class="chip" href="../../categoria/{slugify(cat["name"])}/">'
                f'{html_escape(cat["name"])} ({n})</a>'
            )
    cats_html = (
        f'<div class="panel"><h2>Categorías donde vende {html_escape(nombre)}</h2>'
        f'<div class="chip-row">{"".join(chips)}</div></div>'
        if chips else ""
    )

    # Orden, filtro por categoría y buscador sobre las filas que ya están en
    # el HTML: no piden nada al servidor y, con el JS apagado, la lista se
    # queda en el orden por popularidad con el que se generó. Las categorías
    # se cuentan sobre las filas mostradas (lo que de verdad se puede
    # filtrar), no sobre los productos de la marca: "Impresoras (12)" con
    # ocho filas se leería como una promesa rota. El buscador solo aparece
    # cuando hay filas como para perderse.
    cats_filas = collections.Counter(p.get("category") or "" for p in shown)
    cat_botones = "".join(
        f'<button type="button" class="cat-opt" data-cat="{html_escape(c)}">{html_escape(c)} '
        f'<span class="cat-opt-n">{n}</span></button>'
        for c, n in cats_filas.most_common() if c
    )
    filtro_cats = (
        f'<div class="cat-filter" role="group" aria-label="Filtrar por categoría">'
        f'<button type="button" class="cat-opt is-active" data-cat="">Todas las categorías '
        f'<span class="cat-opt-n">{len(shown)}</span></button>{cat_botones}</div>'
        if len(cats_filas) > 1 else ""
    )
    buscador_campo = (
        f'<input id="prodFiltro" type="search" class="marca-filtro" placeholder="Buscar dentro de {html_escape(nombre)}..."'
        f' aria-label="Buscar productos de {html_escape(nombre)}" autocomplete="off">'
        if len(shown) >= 20 else ""
    )
    buscador = f"""
<div class="panel" id="prodFiltroCaja">
  <div class="sort-bar static-sort" role="group" aria-label="Ordenar la lista">
    <div class="sort-bar-options">
      <button type="button" class="sort-opt active" data-sort="pop">Popularidad</button>
      <button type="button" class="sort-opt" data-sort="price_asc">Más baratos</button>
      <button type="button" class="sort-opt" data-sort="price_desc">Más caros</button>
      <button type="button" class="sort-opt" data-sort="rating">Mejor calificados</button>
      <button type="button" class="sort-opt" data-sort="sellers">Más vendedores</button>
    </div>
  </div>
  {filtro_cats}
  {buscador_campo}
  <p class="muted small" id="prodFiltroCuenta"></p>
</div>
{BRAND_LIST_JS}
"""
    body = f"""
<nav class="breadcrumb"><a href="../../">Inicio</a> &gt; <a href="../">Marcas</a> &gt; {html_escape(nombre)}</nav>
<div class="list-head"><h1>{logo_titulo} {html_escape(nombre)} — comparar precios ({len(products)})</h1></div>
<p class="muted small">{html_escape(description)}</p>
{NOTA_LAG_HTML}
{buscador}
<div class="product-list" id="prodLista">{''.join(rows)}</div>
<div class="panel" style="text-align:center; margin-top:20px">
  {more_note}
</div>
{cats_html}
"""
    return page_shell(
        title=f"{nombre}: precios en México — ComparaMEX",
        description=description,
        canonical_path=f"/marca/{slug}/",
        body=body,
        depth=2,
        # breadcrumb_json_ld devuelve el JSON pelado: el <script> lo pone
        # quien llama. Sin envolverlo, el JSON salía como texto visible
        # arriba de la página.
        extra_head='<script type="application/ld+json">\n'
                   + breadcrumb_json_ld([
                       ("Inicio", f"{SITE_URL}/"),
                       ("Marcas", f"{SITE_URL}/marca/"),
                       (nombre, f"{SITE_URL}/marca/{slug}/"),
                   ]) + "\n</script>",
    )


def logo_de_marca(slug):
    """Ruta relativa a la raíz del logo bajado por build_marcas_logos.py, o None."""
    ruta = os.path.join(ROOT, "icons", "marcas", slug + ".png")
    return f"icons/marcas/{slug}.png" if os.path.exists(ruta) else None


def iniciales_de(nombre):
    return "".join(w[0] for w in nombre.split()[:2] if w).upper()


def render_brand_index(marcas):
    total = sum(len(items) for _, _, items in marcas)
    description = (
        f"Todas las marcas que compara ComparaMEX: {len(marcas)} marcas y "
        f"{total:,} productos con precios de varias tiendas de México."
    )
    # Cada marca es una tarjeta con su logo (icons/marcas/, bajado de
    # Wikidata o del sitio oficial) o, si no lo hay, sus iniciales en el
    # mismo recuadro. El nombre y la cuenta van siempre en texto: eso es lo
    # que filtra el buscador y lo que lee Google.
    filas = []
    for nombre, slug, items in marcas:
        logo = logo_de_marca(slug)
        cuadro = (f'<img src="../{logo}" alt="" loading="lazy" decoding="async">' if logo
                  else html_escape(iniciales_de(nombre)))
        filas.append(
            f'<a class="marca-card{" has-logo" if logo else ""}" href="{slug}/">'
            f'<span class="marca-card-logo" aria-hidden="true">{cuadro}</span>'
            f'<span class="marca-card-name">{html_escape(nombre)}</span>'
            f'<span class="marca-card-count">{len(items):,} productos</span></a>'
        )
    filas = "".join(filas)
    # 779 chips no se recorren con la vista. El filtro es JS suelto sobre lo
    # que ya está en el HTML: no pide nada al servidor, no cambia la URL y si
    # el JS no corre la lista sigue completa y enlazada, que es lo que ve
    # Google. Por eso el campo arranca oculto y lo muestra el propio script.
    buscador = """
<div class="panel" id="marcaFiltroCaja" hidden>
  <input id="marcaFiltro" type="search" class="marca-filtro"
         placeholder="Filtrar marcas: Samsung, Bosch, Lego..."
         aria-label="Filtrar marcas" autocomplete="off">
  <p class="muted small" id="marcaFiltroCuenta"></p>
</div>
<script>
document.addEventListener("DOMContentLoaded", function () {
  var caja = document.getElementById("marcaFiltroCaja");
  var campo = document.getElementById("marcaFiltro");
  var cuenta = document.getElementById("marcaFiltroCuenta");
  var chips = Array.prototype.slice.call(document.querySelectorAll("#marcaLista .marca-card"));
  if (!caja || !campo || !chips.length) return;
  caja.hidden = false;
  var sinAcentos = function (s) {
    return s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  };
  var textos = chips.map(function (c) { var n = c.querySelector(".marca-card-name"); return sinAcentos(n ? n.textContent : c.textContent); });
  var filtrar = function () {
    var q = sinAcentos(campo.value.trim());
    var visibles = 0;
    for (var i = 0; i < chips.length; i++) {
      var ok = !q || textos[i].indexOf(q) !== -1;
      chips[i].hidden = !ok;
      if (ok) visibles++;
    }
    cuenta.textContent = q ? visibles + " de " + chips.length + " marcas" : "";
  };
  campo.addEventListener("input", filtrar);
});
</script>
"""
    body = f"""
<nav class="breadcrumb"><a href="../">Inicio</a> &gt; Marcas</nav>
<div class="list-head"><h1>{svg_icon("tag")} Marcas ({len(marcas)})</h1></div>
<p class="muted small">{html_escape(description)}</p>
{buscador}
<div class="panel"><div class="marca-grid" id="marcaLista">{filas}</div></div>
"""
    return page_shell(
        title="Marcas comparadas — ComparaMEX",
        description=description,
        canonical_path="/marca/",
        body=body,
        depth=1,
        extra_head='<script type="application/ld+json">\n'
                   + breadcrumb_json_ld([
                       ("Inicio", f"{SITE_URL}/"),
                       ("Marcas", f"{SITE_URL}/marca/"),
                   ]) + "\n</script>",
    )


def main():
    # Este script NO tiene --dry-run: escribe las 80 mil páginas siempre (con
    # write_if_changed, así que solo toca las que cambiaron). Antes ignoraba
    # en silencio cualquier argumento, y "generate_seo_pages.py --dry-run"
    # --que es como se prueban todos los demás scripts de esta carpeta--
    # hacía una regeneración completa creyendo uno que no escribía nada.
    argparse.ArgumentParser(
        description="Genera las páginas estáticas. No tiene modo de prueba: "
                    "usa write_if_changed, así que reescribe solo lo que cambió."
    ).parse_args()
    data = hide_empty_taxonomy(load_catalog())

    written = []
    lastmod = load_lastmod()
    hoy = datetime.date.today().isoformat()

    def marcar(url):
        lastmod[url] = hoy

    # Qué subcategorías tienen página propia, calculado UNA vez: cada ficha
    # necesita saberlo para su miga, y hacerlo por producto sería recorrer el
    # catálogo entero 82 mil veces.
    subs_con_pagina = set()
    for cat in data["categories"]:
        productos_cat = [p for p in data["products"] if p["category"] == cat["id"]]
        for sub, _ in subcategorias_con_pagina(cat, productos_cat):
            subs_con_pagina.add((cat["id"], sub["id"]))

    # Las marcas se resuelven ANTES de escribir nada, porque las páginas de
    # subcategoría enlazan a ellas: si el mapa se llenara después, esos
    # enlaces saldrían como texto plano en la primera corrida.
    _CON_PAGINA.clear()
    _CON_PAGINA.update(p["id"] for p in data["products"] if tiene_pagina(p))
    _POR_CAT_CON_PAGINA.clear()
    for _p in data["products"]:
        if tiene_pagina(_p):
            _POR_CAT_CON_PAGINA.setdefault(_p["category"], []).append(_p)

    marcas = marcas_con_pagina(data)
    _SLUG_DE_MARCA.clear()
    for _nombre, _slug, _items in marcas:
        for _p in _items:
            _SLUG_DE_MARCA[clave_marca(_p.get("brand"))] = _slug

    for product in data["products"]:
        if not tiene_pagina(product):
            continue
        out_dir = os.path.join(ROOT, "producto", product["id"])
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "index.html")
        if write_if_changed(out_path, render_product_page(product, data, subs_con_pagina)):
            written.append(out_path)
            marcar(f"{SITE_URL}/producto/{product['id']}/")

    subcats_generadas = 0
    familias_generadas = 0
    for cat in data["categories"]:
        products = [p for p in data["products"] if p["category"] == cat["id"]]
        slug = slugify(cat["name"])
        out_dir = os.path.join(ROOT, "categoria", slug)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "index.html")
        if write_if_changed(out_path, render_category_page(cat, products, data)):
            written.append(out_path)
            marcar(f"{SITE_URL}/categoria/{slug}/")

        for sub, items in subcategorias_con_pagina(cat, products):
            sub_slug = slugify(sub["name"])
            sub_dir = os.path.join(out_dir, sub_slug)
            os.makedirs(sub_dir, exist_ok=True)
            sub_path = os.path.join(sub_dir, "index.html")
            subcats_generadas += 1
            if write_if_changed(sub_path, render_subcategory_page(cat, sub, items, data)):
                written.append(sub_path)
                marcar(f"{SITE_URL}/categoria/{slug}/{sub_slug}/")

        # El escalón del medio: en Deportes y fitness, el deporte (Fútbol,
        # Natación). Ver familias_con_pagina.
        for familia, pares, items in familias_con_pagina(cat, products):
            fam_slug = slugify(familia)
            fam_dir = os.path.join(out_dir, fam_slug)
            os.makedirs(fam_dir, exist_ok=True)
            fam_path = os.path.join(fam_dir, "index.html")
            familias_generadas += 1
            if write_if_changed(fam_path, render_subcategory_page(
                    cat, {"id": familia, "name": familia}, items, data, pares_familia=pares)):
                written.append(fam_path)
                marcar(f"{SITE_URL}/categoria/{slug}/{fam_slug}/")

    # Ranking de bajadas de precio. Va después de las fichas porque usa el
    # mismo historial ya cargado, y antes del sitemap para que sus urls entren.
    _NOMBRES_TIENDA.update(
        {st["id"]: st.get("name") or st["id"] for st in (data.get("stores") or [])}
    )
    bajadas_por_cat = {}
    todas_bajadas = []
    for product in data["products"]:
        b = bajada_de(product["id"])
        if not b:
            continue
        todas_bajadas.append((b, product))
        bajadas_por_cat.setdefault(product["category"], []).append((b, product))
    todas_bajadas.sort(key=lambda x: -x[0][0])

    _por_categoria.clear()
    for cat in data["categories"]:
        n = len(bajadas_por_cat.get(cat["id"]) or [])
        if n:
            _por_categoria.append((cat["name"], n))

    # Páginas de marca. Van después de las fichas porque comparten el mismo
    # ranking por popularidad, y antes del sitemap para que sus urls entren.
    marca_urls = []
    marca_dir = os.path.join(ROOT, "marca")
    os.makedirs(marca_dir, exist_ok=True)
    path = os.path.join(marca_dir, "index.html")
    if write_if_changed(path, render_brand_index(marcas)):
        written.append(path)
        marcar(f"{SITE_URL}/marca/")
    marca_urls.append(f"{SITE_URL}/marca/")
    for nombre, slug, items in marcas:
        d = os.path.join(marca_dir, slug)
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, "index.html")
        if write_if_changed(path, render_brand_page(nombre, slug, items, data)):
            written.append(path)
            marcar(f"{SITE_URL}/marca/{slug}/")
        marca_urls.append(f"{SITE_URL}/marca/{slug}/")
    print(f"Marcas con página propia: {len(marcas):,} "
          f"(mínimo {MIN_PRODUCTOS_MARCA} productos)")

    ofertas_dir = os.path.join(ROOT, "ofertas")
    os.makedirs(ofertas_dir, exist_ok=True)
    ofertas_urls = []
    ofertas_vigentes = {""}
    path = os.path.join(ofertas_dir, "index.html")
    if write_if_changed(path, render_ofertas_page(todas_bajadas, data)):
        written.append(path)
        marcar(f"{SITE_URL}/ofertas/")
    ofertas_urls.append(f"{SITE_URL}/ofertas/")

    # Una categoría con cuatro bajadas no merece página propia: sería casi
    # igual a la general y solo gastaría presupuesto de rastreo.
    for cat in data["categories"]:
        items = sorted(bajadas_por_cat.get(cat["id"]) or [], key=lambda x: -x[0][0])
        if len(items) < MIN_BAJADAS_PARA_PAGINA:
            continue
        slug = slugify(cat["name"])
        d = os.path.join(ofertas_dir, slug)
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, "index.html")
        if write_if_changed(path, render_ofertas_page(items, data, cat)):
            written.append(path)
            marcar(f"{SITE_URL}/ofertas/{slug}/")
        ofertas_urls.append(f"{SITE_URL}/ofertas/{slug}/")
        ofertas_vigentes.add(slug)

    print(f"Bajadas de precio publicables: {len(todas_bajadas):,} "
          f"({len(ofertas_urls)} páginas)")

    # "<producto> más barato" es la búsqueda con más volumen del sector y hoy
    # la contestan artículos de revista. La respuesta sale del catálogo, así
    # que se publica como página propia por categoría.
    barato_dir = os.path.join(ROOT, "barato")
    os.makedirs(barato_dir, exist_ok=True)
    barato_urls = []
    barato_vigentes = set()
    for cat in data["categories"]:
        productos_cat = [p for p in data["products"] if p["category"] == cat["id"]]
        if len(_barato_listables(productos_cat, cat)) < MIN_PARA_PAGINA_BARATO:
            continue
        slug = slugify(cat["name"])
        d = os.path.join(barato_dir, slug)
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, "index.html")
        if write_if_changed(path, render_barato_page(cat, productos_cat, data)):
            written.append(path)
            marcar(f"{SITE_URL}/barato/{slug}/")
        barato_urls.append(f"{SITE_URL}/barato/{slug}/")
        barato_vigentes.add(slug)

    print(f"Páginas de \"lo más barato\": {len(barato_urls)}")

    # La portada no la escribe este script, pero su contenido (los carruseles
    # de data/home.json) sale del mismo catálogo: si cambió alguna ficha,
    # cambió también lo que se ve en la portada.
    if written:
        marcar(f"{SITE_URL}/")

    # Las urls que ya no existen (productos borrados, subcategorías que
    # bajaron del mínimo) se sacan del registro para que no crezca sin fin.
    vigentes = {f"{SITE_URL}/"} | set(ofertas_urls) | set(barato_urls)
    vigentes |= {f"{SITE_URL}/producto/{p['id']}/" for p in data["products"] if tiene_pagina(p)}
    for cat in data["categories"]:
        slug = slugify(cat["name"])
        vigentes.add(f"{SITE_URL}/categoria/{slug}/")
        productos_cat = [p for p in data["products"] if p["category"] == cat["id"]]
        for sub, _ in subcategorias_con_pagina(cat, productos_cat):
            vigentes.add(f"{SITE_URL}/categoria/{slug}/{slugify(sub['name'])}/")
    lastmod = {u: f for u, f in lastmod.items() if u in vigentes}

    written += write_sitemaps(data, ROOT, lastmod, ofertas_urls, marca_urls,
                               barato_urls)

    if write_if_changed(LASTMOD_FILE, json.dumps(lastmod, ensure_ascii=False, indent=0, sort_keys=True)):
        written.append(LASTMOD_FILE)

    robots_path = os.path.join(ROOT, "robots.txt")
    if write_if_changed(robots_path, build_robots()):
        written.append(robots_path)

    redirecciones, conservar = escribir_redirecciones(data)
    written += redirecciones
    borrados = borrar_paginas_huerfanas(
        data, ofertas_vigentes, {slug for _n, slug, _i in marcas}, barato_vigentes,
        conservar=conservar)
    if any(borrados.values()):
        print("Páginas borradas (el producto o la categoría ya no está): "
              + ", ".join(f"{v:,} de {k}/" for k, v in borrados.items() if v))

    path_404 = os.path.join(ROOT, "404.html")
    if write_if_changed(path_404, render_404(data)):
        written.append(path_404)

    print(f"Subcategorías con página propia: {subcats_generadas}; familias: {familias_generadas}")
    print(f"Generadas {len(written)} páginas/archivos SEO en {ROOT}:")
    for path in written[:200]:
        print(" -", os.path.relpath(path, ROOT))
    if len(written) > 200:
        print(f" ... y {len(written) - 200} más")


if __name__ == "__main__":
    main()
