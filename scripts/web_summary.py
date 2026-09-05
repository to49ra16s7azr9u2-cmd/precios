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


def purchase_options(product):
    """Espejo de purchaseOptions() en js/app.js."""
    variants = product.get("colorVariants") or []
    offers = product.get("offers") or []
    if len(variants) > 1 and offers:
        base = offers[0]
        out = []
        for v in variants:
            o = dict(base)
            o["price"] = v.get("price")
            o["url"] = v.get("url")
            o["photo"] = v.get("photo")
            # Igual que en la SPA: el listPrice de la oferta base solo vale
            # para la variante que ES esa misma publicación.
            o["listPrice"] = base.get("listPrice") if v.get("url") == base.get("url") else None
            o["sellerCount"] = v.get("sellerCount")
            o["lowestPrice"] = v.get("lowestPrice")
            o["sellers"] = v.get("sellers")
            out.append(o)
        return out
    return offers


def seller_rows(product):
    """Espejo de sellerRows() en js/app.js."""
    out = []
    for o in purchase_options(product):
        sellers = o.get("sellers") or []
        if len(sellers) < 2:
            out.append(o)
            continue
        for i, s in enumerate(sellers):
            row = dict(o)
            row["price"] = s.get("price")
            row["listPrice"] = s.get("listPrice") or None
            row["lowestPrice"] = None
            row["shippingFee"] = s.get("shippingFee")
            row["sellerCount"] = None
            out.append(row)
    return out


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


def seller_total(product):
    """Espejo de sellerTotal() en js/app.js."""
    return sum((o.get("sellerCount") or 1) for o in purchase_options(product))


def is_used(product):
    """Espejo de isUsed() en js/app.js."""
    import re
    for s in product.get("specs") or []:
        if s.get("label") == "Condición" and re.search(
            r"preowned|usado|reacondicionad", str(s.get("value") or ""), re.I
        ):
            return True
    return False


def _ranking_pool(products, n):
    """Espejo de topByPopularity() en js/app.js para un visitante nuevo
    (sin clics/vistas/favoritos guardados): puntaje de reseñas, y como
    desempate la cantidad de vendedores. El orden de empate se resuelve por
    el orden del catálogo, igual que el sort estable de JavaScript."""
    candidates = [p for p in products if not is_used(p)]
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
