#!/usr/bin/env python3
"""Refresca precios (y baja lo agotado) de los productos de Elektra.

POR QUÉ HACE FALTA
------------------
Elektra es hoy la tienda dominante del catálogo -- ~76,000 de las ~88,000
ofertas guardadas -- y hasta ahora NINGUNA de ellas se podía refrescar:
refresh_prices.py cubre Mercado Libre y refresh_other_stores.py cubre
SUNSKY/theluxurycloset/GeekBuying/Glasseslit/Whirlpool. O sea que el 89%
de los precios del sitio se quedaban congelados en el momento de la
importación. Para un comparador de precios eso es justo el defecto que no
se puede tener: el usuario ve un precio en la lista, entra a la tienda, y
el precio es otro.

CÓMO
----
No se pide producto por producto (serían ~76,000 pedidos). Se re-recorren
las MISMAS categorías del importador (CATEGORY_MAP de
add_elektra_products.py) con la misma API pública de VTEX que autoriza el
robots.txt de Elektra (`Allow: /api/catalog_system/pub/products/search?fq=*`),
de a 50 productos por pedido, y se arma un mapa url -> (precio, listPrice,
disponible). Después se aplica ese mapa al catálogo. Son ~1,500 pedidos
para cubrir las 76,000 ofertas, contra 76,000 del camino ingenuo.

QUÉ SE PODA Y QUÉ NO (importante)
---------------------------------
Hay dos situaciones distintas y NO se tratan igual:

  - "visto y agotado": el producto apareció en el recorrido pero sin
    existencias o sin precio. Es una baja REAL y se poda (--no-prune lo
    desactiva).
  - "no visto": el producto no apareció en ningún lado del recorrido. Eso
    NO prueba que se haya dado de baja -- pudo cambiarse a una categoría
    que este script no recorre, o alguna página del recorrido pudo fallar.
    Podar por esto podría borrar decenas de miles de productos por un
    recorrido incompleto, así que por defecto NO se poda: se informa y hay
    que pedirlo expresamente con --prune-missing.

Además, si el recorrido junta mucho menos de lo esperado (ver
MIN_WALK_RATIO) el script se planta y no escribe nada: es la señal de que
la API respondió mal, no de que Elektra se quedó sin catálogo.

USO
---
    python3 scripts/refresh_elektra.py --dry-run
    python3 scripts/refresh_elektra.py
    python3 scripts/refresh_elektra.py --no-prune
    python3 scripts/refresh_elektra.py --limit-categories 3   # prueba rápida
"""
import argparse
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from add_elektra_products import CATEGORY_MAP, PAGE_SIZE, SEARCH_URL, fetch_json, vendedor_publicable  # noqa: E402
from elektra_specs import specs_from  # noqa: E402
from data_io import load_catalog, save_catalog, url_real  # noqa: E402

# Si el recorrido junta menos de esta fracción de las urls de Elektra que ya
# están en el catálogo, algo salió mal en la API y no se toca nada.
MIN_WALK_RATIO = 0.5




def real_url(offer_url):
    # Elektra se guarda sin afiliado: sin ulp=, el enlace ya es el real.
    return url_real(offer_url) or offer_url


def walk_category(path):
    """Todos los productos de una categoría, de a PAGE_SIZE. A diferencia de
    iter_category del importador no corta por --limit: acá se necesita el
    barrido completo para que "no visto" signifique algo."""
    frm = 0
    while True:
        to = frm + PAGE_SIZE - 1
        batch = fetch_json(f"{SEARCH_URL}?fq=C:/{path}/&_from={frm}&_to={to}")
        if not batch:
            return
        for p in batch:
            yield p
        if len(batch) < PAGE_SIZE:
            return
        frm += PAGE_SIZE


def current_offer(product):
    """(precio, listPrice, disponible, ean, sellerId) vigentes de un producto
    de la API. El precio es el del vendedor que elige vendedor_publicable()
    (el más barato con existencia, Elektra a igual precio), no el del primero
    de la lista.

    El `ean` no se usa para mostrar nada: es el código de barras del
    fabricante, y sirve para reconocer que este producto de Elektra es
    EXACTAMENTE el mismo que uno de Mercado Libre y poder comparar precios
    de verdad entre tiendas (ver scripts/match_by_gtin.py). Se aprovecha
    que este recorrido ya pasa por los ~76,000 productos de Elektra: pedirlo
    aparte serían 76,000 peticiones más.

    OJO: no todos los `ean` de Elektra son códigos del fabricante. Se ven
    tres casos en datos reales: GTIN real (Motorola Edge 60 ->
    0840023287053), un código con prefijo GS1 de México (7502316438988) y
    códigos internos de la tienda (iPhone 17 Pro -> 0400064180616). Los dos
    últimos simplemente no van a encontrar nada del otro lado; el filtro de
    plausibilidad vive en match_by_gtin.py, no acá -- este script guarda lo
    que la tienda publica, sin interpretarlo.
    """
    items = product.get("items") or []
    if not items:
        return None, None, False, None, None
    ean = (items[0].get("ean") or "").strip() or None
    vendedor = vendedor_publicable(items[0])
    if not vendedor:
        return None, None, False, ean, None
    offer = vendedor.get("commertialOffer") or {}
    seller_id = str(vendedor["sellerId"]) if vendedor.get("sellerId") is not None else None
    return offer.get("Price"), offer.get("ListPrice"), True, ean, seller_id


def elektra_offers(product):
    """Todas las ofertas de Elektra del producto, INCLUIDAS las que viven
    dentro de colorVariants[].offers (formato de merge_by_color.py).

    Antes solo recorría product["offers"]. Un producto fusionado por color
    guarda cada color con sus propias ofertas, y la ficha muestra ESAS (ver
    purchaseOptions en js/app.js), así que el precio que la gente veía en un
    teléfono de Elektra con varios colores no se refrescaba nunca: el Vivo
    Y11D estaba a $5,999 en la oferta base (refrescada) y a $6,999 en la
    variante Negro --misma url-- que es la que se mostraba. 63 ofertas así.
    """
    for o in product.get("offers") or []:
        if o.get("storeId") == "elektra":
            yield o
    for v in product.get("colorVariants") or []:
        for o in v.get("offers") or []:
            if o.get("storeId") == "elektra":
                yield o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--prune", dest="prune", action="store_true", default=True,
                    help="baja lo que el recorrido vio agotado (por defecto)")
    ap.add_argument("--no-prune", dest="prune", action="store_false")
    ap.add_argument("--prune-missing", action="store_true",
                    help="además baja lo que no apareció en el recorrido (ver nota del encabezado)")
    ap.add_argument("--limit-categories", type=int, default=0, help="solo para pruebas")
    args = ap.parse_args()

    data = load_catalog()
    catalog_urls = {
        real_url(o["url"])
        for p in data["products"]
        for o in elektra_offers(p)
        if o.get("url")
    }
    print(f"Ofertas de Elektra en el catálogo: {len(catalog_urls)} urls distintas")
    if not catalog_urls:
        return

    paths = list(CATEGORY_MAP.keys())
    if args.limit_categories:
        paths = paths[: args.limit_categories]

    live = {}
    fichas = {}
    for i, path in enumerate(paths, 1):
        seen = 0
        for p in walk_category(path):
            url = p.get("link")
            if not url:
                continue
            live[url] = current_offer(p)
            # La ficha técnica viene en la MISMA respuesta que el precio: se
            # aprovecha el recorrido que ya se está haciendo (ver
            # elektra_specs.py). Antes se descargaba y se tiraba.
            fichas[url] = specs_from(p)
            seen += 1
        print(f"  [{i}/{len(paths)}] {path}: {seen} productos ({len(live)} acumulados)")

    covered = len(catalog_urls & set(live))
    ratio = covered / len(catalog_urls)
    print(f"\nRecorrido: {len(live)} productos vivos; cubre {covered} "
          f"({ratio:.0%}) de las urls del catálogo")
    if ratio < MIN_WALK_RATIO and not args.limit_categories:
        print(f"ABORTA: el recorrido cubrió menos del {MIN_WALK_RATIO:.0%} del catálogo. "
              "Eso apunta a un problema de la API, no a bajas masivas. No se escribió nada.",
              file=sys.stderr)
        sys.exit(2)

    stats = {"revisados": 0, "precio": 0, "sin_cambio": 0, "agotado": 0, "no_visto": 0,
             "ficha_tecnica": 0}
    deltas = []
    dead_urls, missing_urls = set(), set()

    for p in data["products"]:
        for o in elektra_offers(p):
            url = real_url(o.get("url") or "")
            if not url:
                continue
            stats["revisados"] += 1
            entry = live.get(url)
            if entry is None:
                stats["no_visto"] += 1
                missing_urls.add(o["url"])
                continue
            # Ficha técnica: se escribe en el PRODUCTO (no en la oferta) y
            # solo si trae algo. No se pisa una ficha que ya tenga el
            # producto de otra fuente con MÁS campos: la de Elektra es buena,
            # pero no es razón para tirar una mejor.
            ficha = fichas.get(url) or []
            if ficha and len(ficha) > len(p.get("specs") or []):
                if p.get("specs") != ficha:
                    p["specs"] = ficha
                    stats["ficha_tecnica"] += 1
            price, list_price, available, ean, seller_id = entry
            # El código de barras se guarda aunque el producto esté agotado o
            # el precio no se haya movido: es un dato del producto, no de la
            # oferta de hoy.
            if ean and o.get("ean") != ean:
                o["ean"] = ean
            if not available:
                stats["agotado"] += 1
                dead_urls.add(o["url"])
                continue
            # Quién vende a este precio se anota aunque el precio no se haya
            # movido: es lo que le permite al historial saber si mañana
            # cambió el precio o cambió el vendedor.
            if seller_id and o.get("sellerId") != seller_id:
                o["sellerId"] = seller_id
            old = o.get("price")
            if old is not None and abs(price - old) < 0.01:
                stats["sin_cambio"] += 1
            else:
                if old:
                    deltas.append((abs(price - old) / old, p["name"], old, price))
                o["price"] = price
                stats["precio"] += 1
            # listPrice manda los sellos de descuento del sitio: se sincroniza
            # siempre, incluso si el precio no se movió -- si la tienda quitó
            # el precio de lista, el descuento dejó de existir y no puede
            # seguir anunciándose.
            if list_price and list_price > price:
                o["listPrice"] = list_price
            else:
                o.pop("listPrice", None)

    print("\n=== Resumen ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    deltas.sort(reverse=True)
    if deltas:
        print("\nMayores cambios de precio:")
        for pct, name, old, new in deltas[:10]:
            print(f"  {pct:>6.0%}  {name[:60]:<60} ${old:,.2f} -> ${new:,.2f}")

    to_drop = set()
    if args.prune:
        to_drop |= dead_urls
    if args.prune_missing:
        to_drop |= missing_urls
    elif missing_urls:
        print(f"\n{len(missing_urls)} ofertas no aparecieron en el recorrido y se "
              "DEJARON como estaban (usar --prune-missing para darlas de baja).")

    removed = 0
    if to_drop:
        survivors = []
        for p in data["products"]:
            offers = p.get("offers") or []
            alive = [o for o in offers if o.get("url") not in to_drop]
            # Las ofertas de Elektra dentro de las variantes de color también
            # se dan de baja; una variante que se queda sin ofertas se va.
            variantes = p.get("colorVariants") or []
            if variantes and any("offers" in v for v in variantes):
                nuevas = []
                for v in variantes:
                    vivas = [o for o in (v.get("offers") or []) if o.get("url") not in to_drop]
                    if vivas:
                        nuevas.append({**v, "offers": vivas})
                if len(nuevas) != len(variantes) or any(
                    len(n["offers"]) != len(v.get("offers") or []) for n, v in zip(nuevas, variantes)
                ):
                    p["colorVariants"] = nuevas
                if not alive and not nuevas:
                    removed += 1
                    continue
            elif offers and not alive:
                removed += 1
                continue
            if len(alive) < len(offers):
                p["offers"] = alive
            survivors.append(p)
        data["products"] = survivors
        print(f"\nProductos dados de baja: {removed} (quedan {len(data['products'])})")

    if args.dry_run:
        print("\n(--dry-run: no se escribió nada)")
        return
    save_catalog(data)
    print(f"\nCatálogo actualizado: {stats['precio']} precios, {removed} bajas, "
          f"total {len(data['products'])} productos")


if __name__ == "__main__":
    main()
