#!/usr/bin/env python3
"""Detecta (y opcionalmente quita) ofertas pegadas al producto EQUIVOCADO.

EL PROBLEMA
-----------
Las fichas de tiendas distintas se unieron en algún momento por "código de
modelo": si dos productos comparten un código tipo G100 o M607, se
tomaron como el mismo producto. Ese criterio produce falsos positivos
espectaculares, porque el mismo código lo usan fabricantes que no tienen
nada que ver entre sí. Casos reales encontrados en el catálogo:

    Motorola G100 (celular)        <- sistema de guitarra Gemini GMU-G100
    Corsair K100 (teclado)         <- memoria USB Kodak K100
    Logitech M100 (mouse)          <- hub inteligente Aqara M100
    Canon T100 (cámara réflex)     <- foco LED T100 de 30 W
    Brady M610 (etiquetadora)      <- cuerdas de ukelele Martin M610

No es solo un precio de más en la tabla: es un precio FALSO (casi siempre
mucho más barato, porque el otro producto es más barato) y un botón "Ver
oferta" que manda al comprador a otra cosa.

CÓMO SE DETECTA
---------------
La url de las tiendas que no son Mercado Libre lleva el nombre del
producto en el slug, así que se compara contra el nombre guardado:

  1. Se toman solo las palabras ALFABÉTICAS de 4+ letras de cada lado. Se
     descarta a propósito el código de modelo (que es justo lo que produjo
     el match equivocado) y las palabras de relleno.
  2. Si NO comparten ni una palabra, el slug describe otro producto.
  3. Escape: si el slug menciona la MARCA del producto, se conserva. Sin
     esta regla se irían casos correctos donde la tienda usa otro nombre
     para lo mismo ("Frigobar 128 L" vs "refrigerador-compacto-128-l-
     negro-...-whirlpool").

Las urls de Mercado Libre (/p/MLM…) no se revisan: son numéricas, no
describen el producto. Tampoco las de Amazon MX (/dp/ASIN): a propósito no
llevan slug descriptivo (ver affiliate_url() en add_amazon_offers.py), así
que lo único "alfabético" que hay para comparar es "amazon"/"https" -- eso
no comparte nada con ningún nombre de producto real y marcaba como
sospechosas TODAS las ofertas de Amazon por igual, sin importar si eran
correctas.

LO QUE EL SLUG NO PUEDE DECIR
-----------------------------
Revisando los 47 "mismatches" que reportaba esta auditoría el 2026-09-11
resultó que NINGUNO era un producto equivocado. Eran tres cosas que el slug
por sí solo no puede distinguir de un match malo:

  * Chedraui publica 221 productos con linkText literal "null-3906703": su
    propia API devuelve ese slug, la página carga el producto correcto, y
    productName coincide letra por letra con la ficha. Elektra tiene 2 así
    y 1 con slug "1711104-vendedor-…" (listado de vendedor). Un slug sin
    palabras no describe OTRO producto, describe ninguno: se salta igual
    que los de Mercado Libre y Amazon.
  * "LG" tiene dos letras y la regla de escape exigía tres, así que el
    minicomponente LG CJ45 quedaba marcado aunque el slug dijera "lg".
  * Elektra deja el slug viejo cuando renombra un producto: la ficha de la
    Xtreme PC "32gb 1tb" vive en el slug "…64gb-ddr5-4tb…", pero
    productName, el nombre del SKU y el EAN dicen 32gb/1tb. La regla de
    capacidades no tiene forma de saberlo desde el slug.

Por eso, antes de dar por malo un match en una tienda VTEX (Elektra,
Chedraui, Martí), se le pregunta a la API de la tienda por ese mismo slug
(`/api/catalog_system/pub/products/search/<slug>/p`) y si el productName
que devuelve es el nombre de la ficha, no es un mismatch: es la tienda
describiendo su propio producto de dos maneras. Son pocos pedidos (solo
los sospechosos) y es lo único que distingue "slug viejo" de "producto
equivocado". --sin-red lo desactiva y deja la heurística sola.

USO
---
    python3 scripts/audit_cross_store.py            # solo reporta
    python3 scripts/audit_cross_store.py --fix      # quita las ofertas malas
    python3 scripts/audit_cross_store.py --sin-red  # sin consultar a las tiendas
"""
import argparse
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from add_elektra_products import fetch_json  # noqa: E402
from data_io import load_catalog, save_catalog, sin_acentos as _norm, url_real  # noqa: E402
from vtex_stores import TIENDAS  # noqa: E402

# Slugs que no llevan ni una palabra del producto: "null-3906703" (linkText
# que Chedraui publica tal cual) y "1711104-vendedor-1300834768" (listado de
# vendedor en Elektra). No describen otro producto, no describen ninguno.
SLUG_SIN_NOMBRE = re.compile(r"/(?:null|\d+-vendedor)-\d+/p/?$")

STOP = {
    "para", "con", "del", "los", "las", "por", "que", "este", "esta", "color",
    "negro", "blanco", "gris", "plateado", "pack", "paquete", "unidades",
    "pulgadas", "pulg", "inch",
}




def real_url(offer_url):
    # Sin ulp=, el propio enlace: acá se audita lo que hay, no se descarta.
    return url_real(offer_url) or (offer_url or "")


def words(s):
    return {t for t in re.split(r"[^a-z]+", _norm(s)) if len(t) >= 4} - STOP


def capacities(s):
    """Capacidades tipo "256 GB" / "1 TB" que aparecen en un texto."""
    return set(re.findall(r"(\d+)\s*(gb|tb)\b", _norm(s).replace("-", " ")))




def mismatches(products):
    out = []
    for p in products:
        offers = p.get("offers") or []
        if len({o.get("storeId") for o in offers}) < 2:
            continue
        name_words = words(p.get("name"))
        name_caps = capacities(p.get("name"))
        if not name_words:
            continue
        brand = _norm(p.get("brand") or "")
        brand0 = re.split(r"[^a-z0-9]+", brand)[0] if brand else ""
        for o in offers:
            url = real_url(o.get("url"))
            if not url or "/p/MLM" in url or ("amazon.com" in url and "/dp/" in url):
                continue
            if SLUG_SIN_NOMBRE.search(url):
                continue
            slug = _norm(urllib.parse.unquote(url))

            # Regla 2: capacidades que se contradicen. Cuando el código de
            # modelo coincide pero el producto es OTRO de la misma familia
            # (dos laptops, dos SSD), las palabras sí se parecen y la regla
            # de abajo no lo ve; lo que no se puede contradecir es la
            # capacidad. Ej.: "Asus ... 64gb ... 4gb" contra un
            # "laptop-lm-7500 ... 6gb-ram-128gb": no comparten ninguna.
            #
            # Algunas tiendas arman el slug pegando RAM+almacenamiento sin
            # separador ("12+512GB" -> "12512gb"): el número que capacities()
            # extrae ("12512") nunca va a ser IGUAL a "512" aunque el equipo
            # sea el mismo -- se vieron 2 casos reales (Elektra, Galaxy Z
            # Fold8/Flip8) marcados como "mismatch" por esto solo. Alcanza
            # con que el número del slug TERMINE en el de la ficha (el orden
            # RAM-primero-luego-almacenamiento es el que usan estos feeds).
            slug_caps = capacities(slug)
            if name_caps and slug_caps and not (
                name_caps & slug_caps
                or any(
                    s_unit == n_unit and s_num.endswith(n_num)
                    for s_num, s_unit in slug_caps
                    for n_num, n_unit in name_caps
                )
            ):
                out.append((p, o, url))
                continue

            if brand0 and len(brand0) >= 3 and brand0 in slug:
                continue
            # Una marca de dos letras ("LG", "HP") no puede buscarse como
            # substring -- "lg" está dentro de "pulgadas" -- pero sí como
            # token entero del slug.
            if brand0 and brand0 in re.split(r"[^a-z0-9]+", slug):
                continue
            # Solo el PATH de la url describe el producto -- el dominio
            # ("sunsky-online.com") no dice nada del producto, pero antes se
            # incluía igual cuando la url no terminaba en "/p" (el caso de
            # Sunsky, cuyo link real es solo un id numérico: /v/3164753).
            # words("https://www.sunsky-online.com/v/3164753") daba
            # {"sunsky", "online", "https"} -- palabras que NUNCA van a
            # aparecer en el nombre de ningún producto, así que CUALQUIER
            # oferta de Sunsky con url puramente numérica quedaba marcada
            # como "mismatch" sin serlo. Usar solo el path evita eso.
            # words() sobre el PATH entero (no solo el último segmento): un
            # slug de Elektra termina en "/p" y tomar nada más ese último
            # segmento dejaba "p" -- ni una palabra de 4+ letras, así que
            # slug_words quedaba vacío y la regla de abajo nunca comparaba
            # nada (ningún mismatch real de Elektra se detectaba más).
            path = urllib.parse.urlparse(slug).path or slug
            slug_words = words(path)
            if slug_words and not (name_words & slug_words):
                out.append((p, o, url))
    return out


def _dominio_vtex(url):
    host = urllib.parse.urlparse(url).netloc.lower()
    for store_id, t in TIENDAS.items():
        if host == t["dominio"]:
            return store_id, t["dominio"]
    return None, None


def confirmar_con_la_tienda(bad):
    """Separa los sospechosos de tiendas VTEX en (siguen malos, eran slug viejo).

    Le pregunta a la API de la tienda por el slug exacto de la oferta. Si el
    productName que devuelve es el nombre de la ficha, la oferta apunta al
    producto correcto y el slug es solo la forma vieja o vacía en que la
    tienda lo escribió. Si la API no responde, se deja como sospechoso: no
    se absuelve a ciegas."""
    malos, absueltos = [], []
    for p, o, url in bad:
        store_id, dominio = _dominio_vtex(url)
        if not dominio:
            malos.append((p, o, url))
            continue
        slug = urllib.parse.urlparse(url).path.strip("/").removesuffix("/p")
        resp = fetch_json(f"https://{dominio}/api/catalog_system/pub/products/search/{slug}/p")
        nombre_api = resp[0].get("productName") if isinstance(resp, list) and resp and isinstance(resp[0], dict) else None
        if nombre_api and words(nombre_api) == words(p.get("name")):
            absueltos.append((p, o, url, nombre_api))
        else:
            malos.append((p, o, url))
    return malos, absueltos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--sin-red", action="store_true",
                    help="no consultar la API de las tiendas VTEX para confirmar")
    args = ap.parse_args()

    data = load_catalog()
    bad = mismatches(data["products"])
    if bad and not args.sin_red:
        bad, absueltos = confirmar_con_la_tienda(bad)
        if absueltos:
            print(f"Sospechosos que la propia tienda confirma como correctos "
                  f"(slug viejo, no producto equivocado): {len(absueltos)}")
            for p, o, url, nombre_api in absueltos:
                print(f"  {p['id']}  {o.get('storeId')}  {nombre_api[:60]}")
            print()
    print(f"Ofertas pegadas a un producto que no es el suyo: {len(bad)}\n")
    for p, o, url in bad:
        print(f"  {p['id']}  {p['name'][:50]}")
        print(f"        {o.get('storeId')} ${o.get('price'):,.0f}  {url[:88]}")

    if not bad:
        return
    if not args.fix:
        print("\n(usar --fix para quitarlas)")
        return

    drop = {(p["id"], id(o)) for p, o, _ in bad}
    removed_products = 0
    survivors = []
    for p in data["products"]:
        offers = p.get("offers") or []
        alive = [o for o in offers if (p["id"], id(o)) not in drop]
        if offers and not alive:
            removed_products += 1
            continue
        p["offers"] = alive
        survivors.append(p)
    data["products"] = survivors
    save_catalog(data)
    print(f"\nOfertas quitadas: {len(bad)}; productos sin ninguna oferta viva: {removed_products}")
    print(f"Catálogo: {len(data['products'])} productos.")


if __name__ == "__main__":
    main()
