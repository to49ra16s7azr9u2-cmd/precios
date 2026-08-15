#!/usr/bin/env python3
"""Genera páginas estáticas indexables (SEO) a partir de data/data.json.

Por qué existen estas páginas además de index.html
----------------------------------------------------
ComparaMX es una SPA: todo el contenido (nombre de producto, precios,
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
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "data", "data.json")

# TODO: cambiar por el dominio real antes de desplegar a producción.
SITE_URL = "https://comparamx.example"

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


def aggregate_rating(product):
    total_reviews = sum(o["reviewCount"] for o in product["offers"])
    if total_reviews == 0:
        return 0, 0
    weighted = sum(o["rating"] * o["reviewCount"] for o in product["offers"])
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
<link rel="stylesheet" href="{prefix}css/style.css">
{extra_head}
</head>
<body>
<header class="topbar">
  <div class="topbar-top">
    <div class="topbar-inner">
      <a class="brand" href="{prefix}index.html">
        <span class="brand-mark">Compara<span class="brand-mx">MX</span></span>
      </a>
    </div>
  </div>
</header>
<main class="container">
{body}
</main>
<footer class="site-footer">
  <div class="container">
    ComparaMX — comparador de precios estilo Kakaku.com para México (colores inspirados en Mercari). Proyecto de demostración (MVP), sin afiliación con las tiendas listadas.
  </div>
</footer>
</body>
</html>
"""


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


def render_product_page(product, data):
    cat = next(c for c in data["categories"] if c["id"] == product["category"])
    cat_slug = slugify(cat["name"])
    price = min_price(product)
    avg, count = aggregate_rating(product)
    canonical_path = f"/producto/{product['id']}/"
    canonical = f"{SITE_URL}{canonical_path}"
    n_stores = len(product["offers"])

    description = (
        f"Compara el precio de {product['name']} entre {n_stores} tiendas mexicanas. "
        f"Desde {money(price)} MXN. Envío, disponibilidad y calificación por tienda."
    )

    rows = sorted(product["offers"], key=lambda o: o["price"])
    table_rows = []
    for o in rows:
        store = store_by_id(data, o["storeId"])
        ship = "Envío gratis" if o["shippingFee"] == 0 else money(o["shippingFee"])
        stock_label = {
            "in_stock": "En stock",
            "low_stock": "Últimas piezas",
            "backorder": "Sobre pedido",
        }.get(o["stock"], o["stock"])
        table_rows.append(
            f"<tr><td>{html_escape(store['name'])}</td>"
            f"<td class=\"price-cell\"><span class=\"price-line\">{money(o['price'])}</span></td>"
            f"<td>{ship}</td><td>{stock_label}</td>"
            f"<td>{o['rating']} / 5 ({o['reviewCount']} reseñas)</td></tr>"
        )

    specs_rows = "".join(
        f"<tr><th>{html_escape(s['label'])}</th><td>{html_escape(s['value'])}</td></tr>"
        for s in product["specs"]
    )

    body = f"""
<nav class="breadcrumb">
  <a href="../../index.html">Inicio</a> &gt;
  <a href="../../categoria/{cat_slug}/index.html">{html_escape(cat['name'])}</a> &gt;
  {html_escape(product['name'])}
</nav>
<div class="detail-head">
  <div class="detail-icon" style="font-size:56px">{product.get('image', '📦')}</div>
  <div class="detail-headinfo">
    <p class="muted small">{html_escape(product['brand'])}</p>
    <h1>{html_escape(product['name'])}</h1>
    <p class="detail-rating">{avg} / 5 ({count} calificaciones)</p>
    <p class="detail-fromprice">Desde <strong>{money(price)}</strong> en {n_stores} tiendas</p>
  </div>
</div>
<div class="panel">
  <h2>Comparación de precios</h2>
  <div class="table-scroll">
    <table class="compare-table">
      <thead><tr><th>Tienda</th><th>Precio</th><th>Envío</th><th>Disponibilidad</th><th>Calificación</th></tr></thead>
      <tbody>{''.join(table_rows)}</tbody>
    </table>
  </div>
  <p class="disclaimer">{STORE_ORDER_NOTE}</p>
</div>
<div class="panel">
  <h2>Especificaciones</h2>
  <table class="spec-table">{specs_rows}</table>
</div>
<div class="panel" style="text-align:center">
  <h2>Ver la comparación interactiva</h2>
  <p class="muted small">Mapa de tiempo de entrega por municipio, historial de precio de 30 días y reseñas de compradores.</p>
  <a class="buy-btn" href="../../index.html#/p/{product['id']}">Abrir ComparaMX interactivo →</a>
</div>
"""
    extra_head = f'<script type="application/ld+json">\n{product_json_ld(product, data, canonical)}\n</script>'
    title = f"{product['name']} — Compara precios en México | ComparaMX"
    return page_shell(title, description, canonical_path, body, depth=2, extra_head=extra_head)


def render_category_page(cat, products, data):
    slug = slugify(cat["name"])
    canonical_path = f"/categoria/{slug}/"
    description = (
        f"Compara precios de {cat['name'].lower()} entre tiendas mexicanas: "
        f"{', '.join(sorted({p['brand'] for p in products}))}. "
        f"{len(products)} productos comparados."
    )
    rows = []
    for p in sorted(products, key=min_price):
        rows.append(
            f'<div class="product-row">'
            f'<span class="row-icon">{p.get("image", "📦")}</span>'
            f'<div class="row-info">'
            f'<div class="row-brand">{html_escape(p["brand"])}</div>'
            f'<div class="row-name"><a href="../../producto/{p["id"]}/index.html">{html_escape(p["name"])}</a></div>'
            f'</div>'
            f'<div class="row-priceblock">'
            f'<div class="row-from">Desde</div>'
            f'<div class="row-price">{money(min_price(p))}</div>'
            f'</div>'
            f'</div>'
        )
    body = f"""
<nav class="breadcrumb"><a href="../../index.html">Inicio</a> &gt; {html_escape(cat['name'])}</nav>
<div class="list-head"><h1>{html_escape(cat['name'])} ({len(products)})</h1></div>
<div class="product-list">{''.join(rows)}</div>
<div class="panel" style="text-align:center; margin-top:20px">
  <a class="buy-btn" href="../../index.html#/list?cat={cat['id']}">Ver con filtros interactivos →</a>
</div>
"""
    title = f"{cat['name']} — Comparar precios en México | ComparaMX"
    return page_shell(title, description, canonical_path, body, depth=2)


def build_sitemap(data):
    urls = [f"{SITE_URL}/index.html"]
    for cat in data["categories"]:
        urls.append(f"{SITE_URL}/categoria/{slugify(cat['name'])}/")
    for p in data["products"]:
        urls.append(f"{SITE_URL}/producto/{p['id']}/")
    entries = "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entries}\n</urlset>\n'


def build_robots():
    return f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n"


def main():
    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

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

    sitemap_path = os.path.join(ROOT, "sitemap.xml")
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write(build_sitemap(data))
    written.append(sitemap_path)

    robots_path = os.path.join(ROOT, "robots.txt")
    with open(robots_path, "w", encoding="utf-8") as f:
        f.write(build_robots())
    written.append(robots_path)

    print(f"Generadas {len(written)} páginas/archivos SEO en {ROOT}:")
    for path in written:
        print(" -", os.path.relpath(path, ROOT))
    if SITE_URL == "https://comparamx.example":
        print(
            "\nAVISO: SITE_URL sigue en el valor de ejemplo. Antes de desplegar a "
            "producción, edita SITE_URL en scripts/generate_seo_pages.py con el "
            "dominio real y vuelve a correr este script."
        )


if __name__ == "__main__":
    main()
