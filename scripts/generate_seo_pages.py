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
import collections
import datetime
import json
import os
import re
import shutil
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog  # noqa: E402

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
# autodeclaración que un buscador lee como contenido de poco valor, además de
# contradecir lo que el sitio hace de verdad: los precios se rehacen todos los
# días con el workflow refresh-precios.yml. Lo que sí hay que decir --que un
# precio puede cambiar entre la actualización y la compra-- se dice sin
# llamarse demo.
STORE_ORDER_NOTE = (
    "Los precios se actualizan automáticamente todos los días desde cada "
    "tienda. Aun así pueden cambiar en cualquier momento: confirma el precio "
    "final en la tienda antes de comprar. Para ver la comparación "
    "interactiva, con mapa de tiempos de entrega por municipio y reseñas, "
    "usa el enlace a la versión completa."
)


def slugify(text):
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text).strip("-").lower()
    return slug


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
    """
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
    return (
        f'<div class="{css_class} has-photo">'
        f'<img class="product-photo product-photo-detail" src="{html_escape(foto)}" '
        f'alt="{html_escape(product["name"])}" referrerpolicy="no-referrer" '
        f'loading="lazy" decoding="async">'
        f'</div>'
    )


def page_shell(title, description, canonical_path, body, depth, extra_head="", robots="index, follow", og_image=None):
    """depth = niveles bajo la raíz del sitio (para las rutas relativas ../)."""
    prefix = "../" * depth
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
<meta property="og:type" content="product">
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
    ComparaMEX — comparador de precios para México, para que compres sin arrepentimientos (colores inspirados en Mercari). Precios actualizados automáticamente todos los días; sin afiliación con las tiendas listadas.
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
    opciones = [o for o in purchase_options(product) if o.get("price")] or product["offers"]
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


def related_products(product, all_products, n=4):
    """Mismos criterios que un bloque 'productos relacionados' de Kakaku:
    misma categoría, ordenados por cercanía de precio (no aleatorio), sin
    incluir el producto actual."""
    same_cat = [p for p in all_products if p["category"] == product["category"] and p["id"] != product["id"]]
    price = min_price(product)
    same_cat.sort(key=lambda p: abs(min_price(p) - price))
    return same_cat[:n]


def seller_total(product):
    """Vendedores distintos, mismo criterio que sellerTotal() en js/app.js.

    Casi todo el catálogo viene de Mercado Libre, así que "1 tienda" no
    informaba nada; lo que varía es cuántos vendedores compiten por el mismo
    producto, que es además sobre lo que se calcula el precio "Desde".
    """
    return sum((o.get("sellerCount") or 1) for o in purchase_options(product)) or 1


def purchase_options(product):
    """Espejo de purchaseOptions() en js/app.js. Las variantes de color
    SUSTITUYEN a la oferta base (no se suman), o se contaría dos veces la
    misma publicación.

    Hay dos formatos de variante conviviendo en el catálogo y este archivo
    solo entendía el viejo:
      viejo (merge_color_variants.py): {"color", "price", "url", ...}
      nuevo (merge_by_color.py):       {"color", "offers": [ ... ]}
    Con el nuevo, contar `v.get("sellerCount")` daba 1 por color (sin
    importar cuántos vendedores tuviera de verdad), y seller_rows() leía
    product["offers"], que tras la fusión son solo las del color más barato
    -- o sea que la página estática se publicaba sin las ofertas de los
    demás colores.
    """
    variants = product.get("colorVariants") or []
    offers = product.get("offers") or []
    # Con UNA sola variante también se expande (antes el umbral era > 1): son
    # 7 productos donde ese único color es otra publicación, más barata, que
    # quedaba invisible. Con el dedupe por url de abajo no se cuenta doble.
    if variants and any("offers" in v for v in variants):
        out = []
        for v in variants:
            for oferta in v.get("offers") or []:
                copia = dict(oferta)
                copia["colorLabel"] = v.get("color")
                out.append(copia)
        # Las ofertas de product["offers"] que NO están en ninguna variante
        # son publicaciones distintas (otra tienda, pegada después por
        # match_by_gtin.py) y se muestran también. Sin esto, la oferta de
        # Mercado Libre a $12,161 de un teléfono que Elektra tenía a $13,999
        # en todos sus colores no aparecía en ningún lado: ni en la ficha ni
        # en el "desde". 37 productos con la oferta más barata escondida.
        out.extend(_ofertas_fuera_de_variantes(offers, out))
        return out or offers
    if variants and offers:
        base = offers[0]
        out = []
        for v in variants:
            copia = dict(base)
            copia["price"] = v.get("price")
            copia["url"] = v.get("url")
            copia["photo"] = v.get("photo")
            copia["listPrice"] = base.get("listPrice") if v.get("url") == base.get("url") else None
            copia["sellerCount"] = v.get("sellerCount")
            copia["lowestPrice"] = v.get("lowestPrice")
            copia["sellers"] = v.get("sellers")
            copia["colorLabel"] = v.get("color")
            out.append(copia)
        out.extend(_ofertas_fuera_de_variantes(offers, out))
        return out
    return offers


def _ofertas_fuera_de_variantes(offers, ya):
    """Las ofertas base cuya url no aparece entre las ya expandidas."""
    urls = {o.get("url") for o in ya if o.get("url")}
    return [dict(o) for o in offers if o.get("url") and o["url"] not in urls]


def seller_rows(product):
    """Una fila por vendedor, igual que sellerRows() en js/app.js.

    Una publicación de catálogo de Mercado Libre puede tener varios
    vendedores con precios distintos. Cada fila lleva su propia URL
    (?pdp_filters=item_id:...), así que el precio que se publica es el que se
    paga al hacer clic EN ESA fila.
    """
    out = []
    for o in purchase_options(product):
        sellers = o.get("sellers") or []
        # Se abre en filas por vendedor solo si TODOS tienen su enlace: una
        # fila con el precio de un vendedor y el enlace de otro publicaría un
        # precio que no es el que se paga al hacer clic. Sin enlace propio se
        # deja la oferta como una sola fila.
        if len(sellers) < 2 or not all(sl.get("url") for sl in sellers):
            out.append(o)
            continue
        for i, sl in enumerate(sellers):
            row = dict(o)
            row["price"] = sl["price"]
            row["url"] = sl["url"]
            # listPrice/lowestPrice se midieron sobre la publicación entera,
            # no sobre este vendedor: mostrarlos en su fila sería un "-30%"
            # contra un precio que no es el suyo.
            row["listPrice"] = sl.get("listPrice")
            row["lowestPrice"] = None
            row["sellerCount"] = None
            row["shippingFee"] = sl.get("shippingFee")
            row["sellerState"] = sl.get("state")
            row["sellerOfficial"] = bool(sl.get("official"))
            row["isBuyBox"] = i == 0
            out.append(row)
    return out


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
    cambios = {t: dict(zip(s[::2], s[1::2])) for t, s in por_tienda.items()}
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


def sparkline_svg(serie, ancho=560, alto=90):
    """Gráfico de la evolución, en SVG inline.

    Sin JavaScript ni librería a propósito: estas páginas son estáticas y las
    ve un rastreador antes que una persona. Un <svg> se pinta igual con el
    JS apagado y no agrega ninguna petición.
    """
    if len(serie) < 2:
        return ""
    precios = [p for _, p in serie]
    lo, hi = min(precios), max(precios)
    # Un respiro debajo del mínimo: sin él, un tramo plano al precio más bajo
    # queda pegado al borde de abajo y el área sombreada no se ve.
    span = (hi - lo) or max(hi * 0.1, 1)
    lo -= span * 0.12
    span = hi - lo
    dias = [d for d, _ in serie]
    d0, d1 = dias[0], dias[-1]
    ancho_dias = (d1 - d0) or 1
    pad = 10
    def xy(d, p):
        x = pad + (d - d0) / ancho_dias * (ancho - 2 * pad)
        y = pad + (1 - (p - lo) / span) * (alto - 2 * pad)
        return f"{x:.1f},{y:.1f}"
    linea = " ".join(xy(d, p) for d, p in serie)
    area = f"{pad},{alto - pad} " + linea + f" {ancho - pad},{alto - pad}"
    return (
        f'<svg class="price-spark" viewBox="0 0 {ancho} {alto}" '
        f'role="img" aria-label="Evolución del precio: de {money(precios[0])} a {money(precios[-1])}">'
        f'<polygon points="{area}" fill="rgba(255,2,17,.08)"/>'
        f'<polyline points="{linea}" fill="none" stroke="var(--red)" stroke-width="2" '
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


def bajada_de(product_id):
    """La mayor bajada VIGENTE de este producto, o None.

    (pct, tienda, precio_antes, precio_ahora, día_del_cambio)

    Se mide DENTRO de una misma tienda, nunca sobre el mínimo entre tiendas.
    Cuando a un producto se le suma una segunda tienda más barata, el mínimo
    cae de golpe, pero nadie bajó ningún precio: solo apareció otro vendedor.
    Medido así, el ranking se llenaba de "Minecraft bajó 93%" que en realidad
    era "Elektra lo tenía a $9,864 y ahora también está en Mercado Libre a
    $699".
    """
    mejor = None
    for tienda, flat in (historial_de(product_id) or {}).items():
        pares = list(zip(flat[::2], flat[1::2]))
        if len(pares) < 2:
            continue
        (dia_antes, antes), (dia_ahora, ahora) = pares[-2], pares[-1]
        # null al final = la tienda ya no lo vende: no hay bajada vigente.
        if ahora is None or antes is None or ahora >= antes or not antes:
            continue
        if dia_ahora - dia_antes < DIAS_SOSTENIDO:
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
        f"<p>Entre el {fecha_larga(serie[0][0])} y el {fecha_larga(serie[-1][0])} "
        f"osciló entre {money(lo)} (el {fecha_larga(dia_lo)}) y {money(hi)} "
        f"(el {fecha_larga(dia_hi)})."
        if hi != lo else
        f"<p>No se ha movido de {money(lo)} desde el {fecha_larga(serie[0][0])}."
    ) + "</p>"

    return f"""
<div class="panel detail-anchor-target" id="historyPanel">
  <h2>Evolución del precio</h2>
  {veredicto}
  {rango}
  {sparkline_svg(serie)}
  <p class="muted small">Anotamos el precio de esta ficha todos los días. El
  historial arranca el {fecha_larga(serie[0][0])}, que es cuando empezamos a
  guardarlo — no antes.</p>
</div>
"""


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
    related_items = "".join(
        f'<a class="related-item" href="../../producto/{r["id"]}/">'
        f'<span class="row-icon">{svg_icon(r.get("image", "box"))}</span>'
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
    quicknav_html = (
        '<nav class="detail-quicknav">'
        + "".join(
            f'<a class="detail-quicknav-btn" href="#{qid}">{svg_icon(ic)} {label}</a>'
            for qid, ic, label in quicknav_items
        )
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
  <p class="disclaimer">{STORE_ORDER_NOTE}</p>
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
        f'<script type="application/ld+json">\n{breadcrumbs}\n</script>'
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
SUBCATEGORIAS_OPT_IN = {"Accesorios y repuestos"}

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


def render_subcategory_page(cat, sub, products, data):
    """Página de una subcategoría ("Sillas de oficina", "Cargadores USB-C").

    Es el hueco más grande que tenía el sitio: había 48 páginas de categoría
    y ~82 mil de producto, y NADA en medio. Las consultas de mitad de embudo
    ("sillas de oficina precio", "cargadores usb c baratos") son justo las
    que un comparador puede ganar, y no había ninguna página a la que
    llevaran. Además le dan a las fichas un enlace interno desde una página
    temática, en vez de colgar todas del listado general de la categoría.
    """
    cat_slug = slugify(cat["name"])
    sub_slug = slugify(sub["name"])
    canonical_path = f"/categoria/{cat_slug}/{sub_slug}/"
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
        f"Compara precios de {sub['name'].lower()} en México entre tiendas: "
        f"{len(products)} productos.{rango}{marcas_note}"
    )

    ranked = sorted(products, key=lambda p: (total_review_count(p), seller_total(p)), reverse=True)
    shown = ranked[:STATIC_LIST_CAP]
    rows = []
    for i, p in enumerate(shown, start=1):
        rank_badge = svg_icon("crown") if i == 1 else str(i)
        rank_class = f" rank-{i}" if 2 <= i <= 4 else ""
        used_badge = (
            f'<span class="used-badge" title="Producto usado/preowned">{svg_icon("rotate")} Usado</span>'
            if is_used(p) else ""
        )
        rows.append(
            f'<div class="product-row has-rank{rank_class}">'
            f'<span class="rank-badge">{rank_badge}</span>'
            f'{product_photo_html(p, "row-icon")}'
            f'<div class="row-info">'
            f'<div class="row-brand">{html_escape(p["brand"])}</div>'
            f'<div class="row-name"><a href="../../../producto/{p["id"]}/">{html_escape(p["name"])}</a>{used_badge}</div>'
            f'</div>'
            f'<div class="row-priceblock">'
            + (f'<div class="row-from">Desde</div>' if len(p["offers"]) > 1 else "")
            + f'<div class="row-price">{money(min_price(p))}</div>'
            f'</div>'
            f'</div>'
        )
    more_note = (
        f'<p class="muted small" style="text-align:center; margin-top:10px">'
        f'Mostrando los {len(shown)} más populares de {len(products)}.</p>'
        if len(products) > len(shown) else ""
    )

    marcas_todas = [m for m, _ in por_marca.most_common()]
    marcas_html = (
        f'<p class="muted small">Marcas comparadas: '
        f'{html_escape(", ".join(marcas_todas[:60]))}'
        + (f' y {len(marcas_todas) - 60} más.' if len(marcas_todas) > 60 else '.')
        + '</p>'
        if marcas_todas else ""
    )

    # Enlaces a las subcategorías hermanas: sin esto cada página quedaría en
    # una rama muerta del sitio, alcanzable solo desde el sitemap.
    hermanas = []
    for otra in cat.get("subcategories", []):
        if otra["id"] == sub["id"]:
            continue
        n = sum(1 for p in data["products"]
                if p["category"] == cat["id"] and p.get("subcategory") == otra["id"])
        if n >= MIN_PRODUCTOS_SUBCATEGORIA:
            hermanas.append(
                f'<a class="chip" href="../{slugify(otra["name"])}/">{html_escape(otra["name"])} ({n})</a>'
            )
    hermanas_html = (
        f'<div class="panel"><h2>Otras subcategorías de {html_escape(cat["name"])}</h2>'
        f'<div class="chip-row">{"".join(hermanas)}</div></div>'
        if hermanas else ""
    )

    body = f"""
<nav class="breadcrumb"><a href="../../../">Inicio</a> &gt; <a href="../">{html_escape(cat['name'])}</a> &gt; {html_escape(sub['name'])}</nav>
<div class="list-head"><h1>{svg_icon("trophy")} {html_escape(sub['name'])} — comparar precios ({len(products)})</h1></div>
<p class="muted small">{html_escape(description)}</p>
{marcas_html}
<div class="product-list">{''.join(rows)}</div>
<div class="panel" style="text-align:center; margin-top:20px">
  <a class="buy-btn" href="../../../#/list?cat={cat['id']}&amp;sub={sub['id']}">Ver con filtros interactivos →</a>
  {more_note}
</div>
{hermanas_html}
"""
    breadcrumbs = breadcrumb_json_ld([
        ("Inicio", f"{SITE_URL}/"),
        (cat["name"], f"{SITE_URL}/categoria/{cat_slug}/"),
        (sub["name"], None),
    ])
    lista_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"{sub['name']} — comparar precios en México",
        "numberOfItems": len(shown),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i,
                "url": f"{SITE_URL}/producto/{p['id']}/",
                "name": p["name"],
            }
            for i, p in enumerate(shown, start=1)
        ],
    }, ensure_ascii=False, indent=2)
    extra_head = (
        f'<script type="application/ld+json">\n{breadcrumbs}\n</script>\n'
        f'<script type="application/ld+json">\n{lista_ld}\n</script>'
    )
    title = f"{sub['name']} — Comparar precios en México | ComparaMEX"
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
        f'<div class="row-name"><a href="{prefijo}producto/{p["id"]}/">{html_escape(p["name"])}</a></div>'
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
    )
    filas = "".join(_fila_de_oferta(p, b, prefijo) for b, p in mostrados)

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
antes en la MISMA tienda. No entran los productos que aparecen más baratos
solo porque se les sumó otro vendedor: eso no es una bajada. Tampoco los
precios que estuvieron un solo día, que casi siempre son un dato que la
tienda corrigió.</p>
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
        "numberOfItems": len(mostrados),
        "itemListElement": [
            {"@type": "ListItem", "position": i,
             "url": f"{SITE_URL}/producto/{p['id']}/", "name": p["name"]}
            for i, (_, p) in enumerate(mostrados, start=1)
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


def render_category_page(cat, products, data):
    slug = slugify(cat["name"])
    # El ranking de la categoría no lista las piezas sueltas; el conteo y los
    # enlaces a subcategorías sí las cuentan, porque su página existe.
    productos_listables = [
        p for p in products if p.get("subcategory") not in SUBCATEGORIAS_OPT_IN
    ]
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
    ranked = sorted(products, key=lambda p: (total_review_count(p), seller_total(p)), reverse=True)
    # La página estática no es interactiva (no hay paginación de JS aquí),
    # así que se limita a un top fijo en vez de volcar la categoría entera:
    # sin esto, "Moda y accesorios" generaba un solo archivo HTML de ~4MB
    # con miles de filas. El resto queda a un clic con el link de abajo,
    # que ya manda a la SPA con filtros interactivos (y ahí sí paginada).
    shown = ranked[:STATIC_LIST_CAP]
    rows = []
    for i, p in enumerate(shown, start=1):
        rank_badge = svg_icon("crown") if i == 1 else str(i)
        rank_class = f" rank-{i}" if 2 <= i <= 4 else ""
        variant_count = max([len(o.get("variants") or []) for o in p["offers"]], default=0)
        variant_badge = f'<span class="variant-count-badge" title="También disponible en otros colores/tallas">{svg_icon("palette")} +{variant_count}</span>' if variant_count else ""
        used_badge = f'<span class="used-badge" title="Producto usado/preowned">{svg_icon("rotate")} Usado</span>' if is_used(p) else ""
        rows.append(
            f'<div class="product-row has-rank{rank_class}">'
            f'<span class="rank-badge">{rank_badge}</span>'
            f'{product_photo_html(p, "row-icon")}'
            f'<div class="row-info">'
            f'<div class="row-brand">{html_escape(p["brand"])}</div>'
            f'<div class="row-name"><a href="../../producto/{p["id"]}/">{html_escape(p["name"])}</a>{used_badge}{variant_badge}</div>'
            f'</div>'
            f'<div class="row-priceblock">'
            + (f'<div class="row-from">Desde</div>' if len(p["offers"]) > 1 else "")
            + f'<div class="row-price">{money(min_price(p))}</div>'
            f'</div>'
            f'</div>'
        )
    more_note = (
        f"<p class=\"muted small\" style=\"text-align:center; margin-top:10px\">"
        f"Mostrando los {len(shown)} más populares de {len(productos_listables)}.</p>"
        if len(productos_listables) > len(shown) else ""
    )
    # Enlaces a las subcategorías con página propia. Sin esto esas páginas
    # solo serían alcanzables desde el sitemap, que es la peor forma de que
    # un buscador las encuentre y les dé importancia.
    subs_html = ""
    subs = subcategorias_con_pagina(cat, products)
    if subs:
        chips = "".join(
            f'<a class="chip" href="{slugify(sub["name"])}/">{html_escape(sub["name"])} ({len(items)})</a>'
            for sub, items in subs
        )
        subs_html = (
            f'<div class="panel"><h2>Buscar por tipo de {html_escape(cat["name"].lower())}</h2>'
            f'<div class="chip-row">{chips}</div></div>'
        )

    # Enlace a las bajadas de precio de esta categoría, si tiene página. Sin
    # esto /ofertas/<cat>/ solo colgaría del sitemap.
    ofertas_link = ""
    n_bajadas = sum(1 for p in products if bajada_de(p["id"]))
    if n_bajadas >= MIN_BAJADAS_PARA_PAGINA:
        ofertas_link = (
            f'<p style="text-align:center; margin:10px 0"><a class="chip" '
            f'href="../../ofertas/{slug}/">{svg_icon("chart")} '
            f'{n_bajadas} productos bajaron de precio en {html_escape(cat["name"].lower())}</a></p>'
        )

    body = f"""
<nav class="breadcrumb"><a href="../../">Inicio</a> &gt; {html_escape(cat['name'])}</nav>
<div class="list-head"><h1>{svg_icon("trophy")} {html_escape(cat['name'])} — más populares ({len(productos_listables)})</h1></div>
{ofertas_link}
{subs_html}
<div class="product-list">{''.join(rows)}</div>
<div class="panel" style="text-align:center; margin-top:20px">
  <a class="buy-btn" href="../../#/list?cat={cat['id']}">Ver con filtros interactivos →</a>
  {more_note}
</div>
"""
    breadcrumbs = breadcrumb_json_ld([
        ("Inicio", f"{SITE_URL}/"),
        (cat["name"], None),
    ])
    extra_head = f'<script type="application/ld+json">\n{breadcrumbs}\n</script>'
    title = f"{cat['name']} — Comparar precios en México | ComparaMEX"
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


def write_sitemaps(data, root, lastmod=None, ofertas_urls=()):
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
    page_urls.extend(ofertas_urls)
    pages_path = os.path.join(root, "sitemap-pages.xml")
    if write_if_changed(pages_path, _urlset_xml(page_urls, lastmod)):
        written.append(pages_path)
    sitemap_files = ["sitemap-pages.xml"]

    product_urls = []
    product_images = {}
    for p in data["products"]:
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


def borrar_paginas_huerfanas(data, dry_run=False):
    """Borra las páginas de productos y categorías que ya no están.

    write_if_changed() solo escribe; nada borraba. Cuando refresh_prices.py
    poda una publicación que Mercado Libre dio de baja, el producto sale del
    catálogo pero su página seguía publicada, con el precio del día que
    murió. Medido: 1,078 fichas así, indexables y con un precio que ya no
    existe -- exactamente lo que un comparador no puede tener.

    Solo se borra lo que este mismo script genera (producto/<id>/,
    categoria/<slug>/ y sus subcategorías, ofertas/<slug>/) y solo si el id o
    el slug no está en el catálogo de esta corrida.
    """
    vivos = {p["id"] for p in data["products"]}
    borrados = {"producto": 0, "categoria": 0, "ofertas": 0}

    carpeta = os.path.join(ROOT, "producto")
    if os.path.isdir(carpeta):
        for nombre in os.listdir(carpeta):
            ruta = os.path.join(carpeta, nombre)
            if os.path.isdir(ruta) and nombre not in vivos:
                borrados["producto"] += 1
                if not dry_run:
                    shutil.rmtree(ruta)

    slugs_cat = {slugify(c["name"]) for c in data["categories"]}
    subs_por_cat = {}
    for cat in data["categories"]:
        productos_cat = [p for p in data["products"] if p["category"] == cat["id"]]
        subs_por_cat[slugify(cat["name"])] = {
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
                if os.path.isdir(sub_ruta) and sub not in subs_por_cat[nombre]:
                    borrados["categoria"] += 1
                    if not dry_run:
                        shutil.rmtree(sub_ruta)

    carpeta = os.path.join(ROOT, "ofertas")
    if os.path.isdir(carpeta):
        for nombre in os.listdir(carpeta):
            ruta = os.path.join(carpeta, nombre)
            if os.path.isdir(ruta) and nombre not in slugs_cat:
                borrados["ofertas"] += 1
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
    body = f"""
<div class="panel" style="text-align:center">
  <h1>Esta página no existe</h1>
  <p class="muted">Puede que el producto ya no esté en el catálogo, o que la dirección tenga un error.</p>
  <p><a class="buy-btn" href="/">Volver al inicio de ComparaMEX →</a></p>
</div>
<div class="panel">
  <h2>Buscar por categoría</h2>
  <div class="chip-row">{cats}</div>
</div>
"""
    return page_shell(
        "Página no encontrada | ComparaMEX",
        "La página que buscas no existe. Vuelve al inicio de ComparaMEX o busca por categoría.",
        "/404.html", body, depth=0, robots="noindex, follow",
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
    """Quita categorías y subcategorías que se quedaron sin productos.

    Mismo criterio que `hideEmptyTaxonomy` en js/app.js: una subcategoría
    vacía es un enlace a una lista vacía, y como página estática además sería
    contenido indexable sin nada dentro.
    """
    with_products = set()
    for p in data.get("products", []):
        with_products.add((p["category"], p.get("subcategory") or ""))
        with_products.add(p["category"])
    cats = []
    for c in data.get("categories", []):
        if c["id"] not in with_products:
            continue
        c = dict(c)
        c["subcategories"] = [
            s for s in c.get("subcategories", []) if (c["id"], s["id"]) in with_products
        ]
        cats.append(c)
    data["categories"] = cats
    return data


def main():
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

    for product in data["products"]:
        out_dir = os.path.join(ROOT, "producto", product["id"])
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "index.html")
        if write_if_changed(out_path, render_product_page(product, data, subs_con_pagina)):
            written.append(out_path)
            marcar(f"{SITE_URL}/producto/{product['id']}/")

    subcats_generadas = 0
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

    ofertas_dir = os.path.join(ROOT, "ofertas")
    os.makedirs(ofertas_dir, exist_ok=True)
    ofertas_urls = []
    if todas_bajadas:
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

    print(f"Bajadas de precio publicables: {len(todas_bajadas):,} "
          f"({len(ofertas_urls)} páginas)")

    # La portada no la escribe este script, pero su contenido (los carruseles
    # de data/home.json) sale del mismo catálogo: si cambió alguna ficha,
    # cambió también lo que se ve en la portada.
    if written:
        marcar(f"{SITE_URL}/")

    # Las urls que ya no existen (productos borrados, subcategorías que
    # bajaron del mínimo) se sacan del registro para que no crezca sin fin.
    vigentes = {f"{SITE_URL}/"} | set(ofertas_urls)
    vigentes |= {f"{SITE_URL}/producto/{p['id']}/" for p in data["products"]}
    for cat in data["categories"]:
        slug = slugify(cat["name"])
        vigentes.add(f"{SITE_URL}/categoria/{slug}/")
        productos_cat = [p for p in data["products"] if p["category"] == cat["id"]]
        for sub, _ in subcategorias_con_pagina(cat, productos_cat):
            vigentes.add(f"{SITE_URL}/categoria/{slug}/{slugify(sub['name'])}/")
    lastmod = {u: f for u, f in lastmod.items() if u in vigentes}

    written += write_sitemaps(data, ROOT, lastmod, ofertas_urls)

    if write_if_changed(LASTMOD_FILE, json.dumps(lastmod, ensure_ascii=False, indent=0, sort_keys=True)):
        written.append(LASTMOD_FILE)

    robots_path = os.path.join(ROOT, "robots.txt")
    if write_if_changed(robots_path, build_robots()):
        written.append(robots_path)

    borrados = borrar_paginas_huerfanas(data)
    if any(borrados.values()):
        print("Páginas borradas (el producto o la categoría ya no está): "
              + ", ".join(f"{v:,} de {k}/" for k, v in borrados.items() if v))

    path_404 = os.path.join(ROOT, "404.html")
    if write_if_changed(path_404, render_404(data)):
        written.append(path_404)

    print(f"Subcategorías con página propia: {subcats_generadas}")
    print(f"Generadas {len(written)} páginas/archivos SEO en {ROOT}:")
    for path in written[:200]:
        print(" -", os.path.relpath(path, ROOT))
    if len(written) > 200:
        print(f" ... y {len(written) - 200} más")


if __name__ == "__main__":
    main()
