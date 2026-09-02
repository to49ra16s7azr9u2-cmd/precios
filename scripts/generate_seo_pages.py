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
import json
import os
import re
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

STORE_ORDER_NOTE = (
    "Los precios de esta página son de referencia para propósitos de "
    "demostración y no están confirmados en tiempo real con cada tienda. "
    "Para ver la comparación interactiva, con mapa de tiempos de entrega "
    "por municipio y reseñas, usa el enlace a la versión completa."
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
    return min(o["price"] for o in product["offers"])


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
    variants = product.get("colorVariants") or []
    if len(variants) > 1:
        return sum((v.get("sellerCount") or 1) for v in variants)
    return sum((o.get("sellerCount") or 1) for o in (product.get("offers") or []))


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


def page_shell(title, description, canonical_path, body, depth, extra_head="", robots="index, follow"):
    """depth = niveles bajo la raíz del sitio (para las rutas relativas ../)."""
    prefix = "../" * depth
    canonical = f"{SITE_URL}{canonical_path}"
    return f"""<!DOCTYPE html>
<html lang="es-MX">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html_escape(title)}</title>
<meta name="description" content="{html_escape(description)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="product">
<meta property="og:title" content="{html_escape(title)}">
<meta property="og:description" content="{html_escape(description)}">
<meta property="og:url" content="{canonical}">
<meta name="theme-color" content="#FF0211">
<link rel="icon" href="{prefix}icons/icon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" href="{prefix}icons/icon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="{prefix}icons/apple-touch-icon.png">
<link rel="stylesheet" href="{prefix}css/style.css">
{GA_SNIPPET}
{extra_head}
</head>
<body>
<header class="topbar">
  <div class="topbar-top">
    <div class="topbar-inner">
      <a class="brand" href="{prefix}index.html">
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
    ComparaMEX — comparador de precios para México, para que compres sin arrepentimientos (colores inspirados en Mercari). Proyecto de demostración (MVP), sin afiliación con las tiendas listadas.
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
    offers = [
        {
            "@type": "Offer",
            "url": canonical,
            "priceCurrency": "MXN",
            "price": o["price"],
            "availability": (
                "https://schema.org/InStock"
                if o["stock"] == "in_stock"
                else "https://schema.org/LimitedAvailability"
                if o["stock"] == "low_stock"
                else "https://schema.org/PreOrder"
            ),
            "seller": {"@type": "Organization", "name": store_by_id(data, o["storeId"])["name"]},
        }
        for o in product["offers"]
    ]
    ld = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product["name"],
        "brand": {"@type": "Brand", "name": product["brand"]},
        "category": product["category"],
        "offers": {
            "@type": "AggregateOffer",
            "priceCurrency": "MXN",
            "lowPrice": min(o["price"] for o in product["offers"]),
            "highPrice": max(o["price"] for o in product["offers"]),
            "offerCount": len(product["offers"]),
            "offers": offers,
        },
    }
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
    # Mismas opciones de compra que purchaseOptions() en js/app.js: las
    # variantes de color SUSTITUYEN a la oferta base (no se suman), o se
    # contaría dos veces la misma publicación.
    variants = product.get("colorVariants") or []
    options = variants if len(variants) > 1 else product["offers"]
    return sum((o.get("sellerCount") or 1) for o in options) or 1


def seller_rows(product):
    """Una fila por vendedor, igual que sellerRows() en js/app.js.

    Una publicación de catálogo de Mercado Libre puede tener varios
    vendedores con precios distintos. Cada fila lleva su propia URL
    (?pdp_filters=item_id:...), así que el precio que se publica es el que se
    paga al hacer clic EN ESA fila.
    """
    out = []
    for o in product["offers"]:
        sellers = o.get("sellers") or []
        if len(sellers) < 2:
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


def render_product_page(product, data):
    cat = next(c for c in data["categories"] if c["id"] == product["category"])
    cat_slug = slugify(cat["name"])
    sub = None
    if product.get("subcategory"):
        sub = next(
            (s for s in cat.get("subcategories", []) if s["id"] == product["subcategory"]), None
        )
    price = min_price(product)
    avg, count = aggregate_rating(product)
    canonical_path = f"/producto/{product['id']}/"
    canonical = f"{SITE_URL}{canonical_path}"
    n_sellers = seller_total(product)

    description = (
        f"Compara el precio de {product['name']} entre {plural(n_sellers, 'vendedor', 'vendedores')} en México. "
        f"Desde {money(price)} MXN. Envío, disponibilidad y calificación por tienda."
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
  <a class="buy-btn" href="../../index.html#/envio">Abrir calculadora de envío →</a>
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
        }.get(o["stock"], o["stock"])
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
            f"<td class=\"price-cell\"><span class=\"price-line\">{money(o['price'])}</span></td>"
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
        f'<a class="related-item" href="../../producto/{r["id"]}/index.html">'
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

    sub_crumb = (
        f'<a href="../../index.html#/list?cat={cat["id"]}&sub={sub["id"]}">{html_escape(sub["name"])}</a> &gt;'
        if sub else ""
    )

    # Mismo menú que el SPA (renderDetailQuickNav en js/app.js), en el mismo
    # hueco junto al nombre. Acá son <a href="#id"> lisos: el salto lo hace el
    # navegador y .detail-anchor-target (scroll-margin-top) evita que el
    # título quede tapado. "Envío" y "Comentarios" solo se listan si la página
    # de verdad tiene esa sección -- la calculadora de envío existe solo para
    # AliExpress/Alibaba/SUNSKY/Geekbuying, y las reseñas solo si el producto
    # ya tiene alguna.
    quicknav_items = [("comparePanel", "tag", "Precios"),
                      ("specsPanel", "pencil", "Especificaciones")]
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
  <a href="../../index.html">Inicio</a> &gt;
  <a href="../../categoria/{cat_slug}/index.html">{html_escape(cat['name'])}</a> &gt;
  {sub_crumb}
  {html_escape(product['name'])}
</nav>
<div class="detail-head">
  <div class="detail-icon">{svg_icon(product.get('image', 'box'))}</div>
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
  <a class="buy-btn" href="../../index.html#/p/{product['id']}">Abrir ComparaMEX interactivo →</a>
</div>
"""
    breadcrumbs = breadcrumb_json_ld([
        ("Inicio", f"{SITE_URL}/index.html"),
        (cat["name"], f"{SITE_URL}/categoria/{cat_slug}/"),
        (product["name"], None),
    ])
    extra_head = (
        f'<script type="application/ld+json">\n{product_json_ld(product, data, canonical)}\n</script>\n'
        f'<script type="application/ld+json">\n{breadcrumbs}\n</script>'
    )
    title = f"{product['name']} — Compara precios en México | ComparaMEX"
    return page_shell(title, description, canonical_path, body, depth=2, extra_head=extra_head)


def render_category_page(cat, products, data):
    slug = slugify(cat["name"])
    canonical_path = f"/categoria/{slug}/"
    brands_note = (
        f" Marcas: {', '.join(sorted({p['brand'] for p in products}))}." if products else ""
    )
    description = (
        f"Compara precios de {cat['name'].lower()} entre tiendas mexicanas."
        f"{brands_note} {len(products)} productos comparados."
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
    STATIC_LIST_CAP = 100
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
            f'<span class="row-icon">{svg_icon(p.get("image", "box"))}</span>'
            f'<div class="row-info">'
            f'<div class="row-brand">{html_escape(p["brand"])}</div>'
            f'<div class="row-name"><a href="../../producto/{p["id"]}/index.html">{html_escape(p["name"])}</a>{used_badge}{variant_badge}</div>'
            f'</div>'
            f'<div class="row-priceblock">'
            + (f'<div class="row-from">Desde</div>' if len(p["offers"]) > 1 else "")
            + f'<div class="row-price">{money(min_price(p))}</div>'
            f'</div>'
            f'</div>'
        )
    more_note = (
        f"<p class=\"muted small\" style=\"text-align:center; margin-top:10px\">"
        f"Mostrando los {len(shown)} más populares de {len(products)}.</p>"
        if len(products) > len(shown) else ""
    )
    body = f"""
<nav class="breadcrumb"><a href="../../index.html">Inicio</a> &gt; {html_escape(cat['name'])}</nav>
<div class="list-head"><h1>{svg_icon("trophy")} {html_escape(cat['name'])} — más populares ({len(products)})</h1></div>
<div class="product-list">{''.join(rows)}</div>
<div class="panel" style="text-align:center; margin-top:20px">
  <a class="buy-btn" href="../../index.html#/list?cat={cat['id']}">Ver con filtros interactivos →</a>
  {more_note}
</div>
"""
    breadcrumbs = breadcrumb_json_ld([
        ("Inicio", f"{SITE_URL}/index.html"),
        (cat["name"], None),
    ])
    extra_head = f'<script type="application/ld+json">\n{breadcrumbs}\n</script>'
    title = f"{cat['name']} — Comparar precios en México | ComparaMEX"
    return page_shell(title, description, canonical_path, body, depth=2, extra_head=extra_head)


# Límite real de Google es 50,000 URLs (y 50MB) por archivo de sitemap;
# se corta antes, en 40,000, para dejar margen y no rozarlo justo cuando el
# catálogo crezca un poco más entre una corrida y la siguiente.
SITEMAP_CHUNK_SIZE = 40000


def _urlset_xml(urls):
    entries = "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entries}\n</urlset>\n'


def write_sitemaps(data, root):
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

    page_urls = [f"{SITE_URL}/index.html"]
    for cat in data["categories"]:
        page_urls.append(f"{SITE_URL}/categoria/{slugify(cat['name'])}/")
    pages_path = os.path.join(root, "sitemap-pages.xml")
    with open(pages_path, "w", encoding="utf-8") as f:
        f.write(_urlset_xml(page_urls))
    written.append(pages_path)
    sitemap_files = ["sitemap-pages.xml"]

    product_urls = [f"{SITE_URL}/producto/{p['id']}/" for p in data["products"]]
    chunks = [product_urls[i:i + SITEMAP_CHUNK_SIZE] for i in range(0, len(product_urls), SITEMAP_CHUNK_SIZE)] or [[]]
    for i, chunk in enumerate(chunks, 1):
        name = f"sitemap-products-{i}.xml"
        path = os.path.join(root, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(_urlset_xml(chunk))
        written.append(path)
        sitemap_files.append(name)

    index_entries = "\n".join(f"  <sitemap><loc>{SITE_URL}/{name}</loc></sitemap>" for name in sitemap_files)
    index_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{index_entries}\n</sitemapindex>\n"
    )
    index_path = os.path.join(root, "sitemap.xml")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_xml)
    written.append(index_path)
    return written


def build_robots():
    return f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n"


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

    for product in data["products"]:
        out_dir = os.path.join(ROOT, "producto", product["id"])
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "index.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(render_product_page(product, data))
        written.append(out_path)

    for cat in data["categories"]:
        products = [p for p in data["products"] if p["category"] == cat["id"]]
        slug = slugify(cat["name"])
        out_dir = os.path.join(ROOT, "categoria", slug)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "index.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(render_category_page(cat, products, data))
        written.append(out_path)

    written += write_sitemaps(data, ROOT)

    robots_path = os.path.join(ROOT, "robots.txt")
    with open(robots_path, "w", encoding="utf-8") as f:
        f.write(build_robots())
    written.append(robots_path)

    print(f"Generadas {len(written)} páginas/archivos SEO en {ROOT}:")
    for path in written:
        print(" -", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
