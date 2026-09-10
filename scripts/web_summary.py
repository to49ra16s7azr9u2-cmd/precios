"""Resumen precalculado de Inicio, para que la portada no tenga que bajar
el catálogo entero.

POR QUÉ
-------
Hasta ahora TODO visitante bajaba data/products-1..6.json (35 MB en crudo,
5.3 MB con gzip, 84 mil productos) antes de ver nada, porque Inicio se
calculaba recorriendo el catálogo completo en el navegador: el conteo de
cada tarjeta de categoría, el sello "Hasta -70%" y los rankings.

Nada de eso necesita el catálogo en el navegador: son agregados que no
dependen del visitante. Acá se calculan una vez, al guardar el catálogo, y
viajan dentro del manifiesto (unos pocos KB). El navegador solo baja la
shard de la categoría que el usuario abre.

MISMO CRITERIO QUE js/app.js
----------------------------
Las funciones de abajo son el espejo en Python de las de js/app.js
(bestDiscountPct, sellerRows, purchaseOptions, shippingFeeInfo,
reviewStarPoints, sellerTotal, isUsed). Es la misma convención que ya sigue
scripts/generate_seo_pages.py con seller_total()/seller_rows(). Si cambia
la regla de un lado hay que cambiarla del otro, o Inicio mostraría un sello
o un ranking distinto al de la vista de categoría.

Lo que NO se puede precalcular es la parte que depende del visitante
(clics/vistas/favoritos guardados en localStorage). Por eso no se guarda un
ranking ya resuelto sino un POOL de candidatos por categoría: el navegador
le vuelve a aplicar el puntaje del visitante encima y recién ahí decide el
orden final.
"""

# Espejo de SHIPPING_ESTIMATE_MXN en js/app.js.
SHIPPING_ESTIMATE_MXN = {
    "mercadolibre": 99,
    "sunsky": 150,
    "geekbuying": 180,
    "molnija": 200,
    "glasseslit": 100,
    "woodestic": 280,
    "aliexpress": 130,
    "alibaba": 350,
    "theluxurycloset": 500,
    "whirlpool": 550,
}

# Cuántos candidatos por categoría se guardan para los rankings de Inicio.
# El bloque muestra 3; se guarda el doble para que el puntaje del visitante
# (clics/vistas/favoritos, que solo el navegador conoce) todavía pueda
# reordenar algo. Más pool no compra casi nada y sí pesa: con 12 el archivo
# de Inicio eran 72 KB con gzip, con 6 son ~36 KB.
#
# OJO, esto sí cambia el comportamiento respecto de antes: hasta ahora el
# ranking se calculaba sobre el catálogo entero en el navegador, así que un
# producto muy visto por ESTE visitante podía subir al top 3 desde
# cualquier parte del catálogo. Ahora solo puede reordenar dentro del pool.
# Lo que el visitante vio sigue teniendo su propio bloque en Inicio ("Más
# visto en este navegador" e historial), que no depende de esto.
RANKING_POOL = 6


def _shipping_fee(offer, stores_by_id):
    """Espejo de shippingFeeInfo() en js/app.js."""
    if offer.get("shippingFee") is not None:
        return offer["shippingFee"]
    store = stores_by_id.get(offer.get("storeId"))
    threshold = store.get("freeShippingThresholdUSD") if store else None
    original = offer.get("priceOriginal") or {}
    price_usd = original.get("amount") if original.get("currency") == "USD" else None
    if threshold is not None and price_usd is not None and price_usd >= threshold:
        return 0
    return SHIPPING_ESTIMATE_MXN.get(offer.get("storeId"), 0)


def _display_price(offer, stores_by_id, include_shipping):
    price = offer.get("price")
    if price is None:
        return None
    return price + _shipping_fee(offer, stores_by_id) if include_shipping else price


def _display_list_price(offer, stores_by_id, include_shipping):
    list_price = offer.get("listPrice")
    if list_price is None:
        return None
    return list_price + _shipping_fee(offer, stores_by_id) if include_shipping else list_price


# ---------------------------------------------------------------------------
# Las opciones de compra de un producto, UNA sola definición para todo Python
# (resumen de Inicio, páginas estáticas, historial de precios). Espejo de
# purchaseOptions()/sellerRows()/sellerTotal() en js/app.js: si cambia una
# regla allá, cambia acá, y en ningún otro lado -- generate_seo_pages.py
# tenía su propia copia, más completa (url por vendedor, isBuyBox,
# colorLabel), y la de acá se había quedado atrás; ahora vive acá la completa.

def _ofertas_fuera_de_variantes(offers, ya):
    """Las ofertas base cuya url no aparece entre las ya expandidas."""
    urls = {o.get("url") for o in ya if o.get("url")}
    return [dict(o) for o in offers if o.get("url") and o["url"] not in urls]


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


def seller_total(product):
    """Vendedores distintos, mismo criterio que sellerTotal() en js/app.js.

    Casi todo el catálogo viene de Mercado Libre, así que "1 tienda" no
    informaba nada; lo que varía es cuántos vendedores compiten por el mismo
    producto, que es además sobre lo que se calcula el precio "Desde".
    """
    return sum((o.get("sellerCount") or 1) for o in purchase_options(product)) or 1


def best_discount_pct(product, stores_by_id, include_shipping):
    """Espejo de bestDiscountPct() en js/app.js: el descuento de la oferta
    MÁS BARATA, no el mayor descuento del producto."""
    rows = [r for r in seller_rows(product) if r.get("price") is not None]
    if not rows:
        return None
    cheapest = min(rows, key=lambda r: _display_price(r, stores_by_id, include_shipping))
    price = _display_price(cheapest, stores_by_id, include_shipping)
    list_price = _display_list_price(cheapest, stores_by_id, include_shipping)
    if not list_price or list_price <= price:
        return None
    return round((1 - price / list_price) * 100)


def review_star_points(product):
    """Espejo de reviewStarPoints() en js/app.js, sin la parte de las reseñas
    que el visitante escribió en su propio navegador (localStorage)."""
    points = {5: 10, 4: 8, 3: 6}
    return sum(points.get(r.get("rating"), 0) for r in (product.get("reviews") or []))


def is_used(product):
    """Espejo de isUsed() en js/app.js."""
    import re
    for s in product.get("specs") or []:
        if s.get("label") == "Condición" and re.search(
            r"preowned|usado|reacondicionad", str(s.get("value") or ""), re.I
        ):
            return True
    return False


SUBCATEGORIAS_OPT_IN = {"Accesorios y repuestos"}


def _ranking_pool(products, n):
    """Espejo de topByPopularity() en js/app.js para un visitante nuevo
    (sin clics/vistas/favoritos guardados): puntaje de reseñas, y como
    desempate la cantidad de vendedores. El orden de empate se resuelve por
    el orden del catálogo, igual que el sort estable de JavaScript."""
    # Fuera del ranking las piezas sueltas: un filtro de aspiradora no compite
    # con una aspiradora (mismo criterio que SUBCATEGORIAS_OPT_IN en
    # js/app.js y generate_seo_pages.py; ver scripts/split_accesorios.py).
    candidates = [
        p for p in products
        if not is_used(p) and p.get("subcategory") not in SUBCATEGORIAS_OPT_IN
    ]
    ranked = sorted(
        enumerate(candidates),
        key=lambda t: (-review_star_points(t[1]), -seller_total(t[1]), t[0]),
    )
    return [p for _, p in ranked[:n]]


def build_summary(light_products, stores, categories):
    """Devuelve los campos de Inicio que van dentro del manifiesto.

    `light_products` son los productos YA sin los campos de solo-ficha (lo
    mismo que baja el navegador), para que el sello de oferta se calcule
    sobre exactamente los mismos datos que tendrá la SPA.
    """
    stores_by_id = {s["id"]: s for s in stores}

    by_cat = {}
    for p in light_products:
        by_cat.setdefault(p.get("category"), []).append(p)

    # Estadísticas para el sello "Hasta -N%" de cada tarjeta de categoría.
    # Se guardan los dos escenarios del toggle "Incluir envío" porque el
    # descuento se calcula sobre el precio mostrado, y ese toggle lo cambia
    # (ver displayPrice/displayListPrice en js/app.js). Son dos números por
    # categoría: mucho más barato que bajar el catálogo para recalcularlo.
    stats = {}
    for cat_id, products in by_cat.items():
        # `subs` reemplaza el recorrido del catálogo que hacía
        # hideEmptyTaxonomy() en js/app.js: una subcategoría sin productos no
        # se muestra en el nav ni en el filtro (sería un enlace a una lista
        # vacía), y sin esto el navegador no tendría cómo saberlo sin bajar
        # la categoría entera.
        subs = {}
        for p in products:
            subs[p.get("subcategory") or ""] = subs.get(p.get("subcategory") or "", 0) + 1
        entry = {"n": len(products), "subs": subs}
        for include_shipping, suffix in ((False, ""), (True, "Ship")):
            discounted = 0
            best = 0
            for p in products:
                d = best_discount_pct(p, stores_by_id, include_shipping)
                if d:
                    discounted += 1
                    if d > best:
                        best = d
            entry["discounted" + suffix] = discounted
            entry["max" + suffix] = best
        stats[cat_id] = entry

    # Pool de candidatos de los rankings de Inicio. Por categoría alcanza
    # con RANKING_POOL; el bloque "Ranking general" necesita su propio pool
    # global porque los mejores de todo el catálogo no son necesariamente
    # los mejores de las 3 categorías más grandes.
    pools = {"general": _ranking_pool(light_products, RANKING_POOL)}
    for cat_id, products in by_cat.items():
        pools[cat_id] = _ranking_pool(products, RANKING_POOL)

    # Un mismo producto puede estar en varios pools (el general y el de su
    # categoría). Se guarda UNA sola vez y los pools quedan como listas de
    # id, para que el navegador tenga un solo objeto por producto.
    records = {}
    pool_ids = {}
    for key, products in pools.items():
        pool_ids[key] = [p["id"] for p in products]
        for p in products:
            records[p["id"]] = p

    return {
        "totalProducts": len(light_products),
        "categoryStats": stats,
        "homePools": pool_ids,
        "homeProducts": list(records.values()),
    }
