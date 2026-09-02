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
from add_elektra_products import CATEGORY_MAP, PAGE_SIZE, SEARCH_URL, fetch_json  # noqa: E402
from data_io import load_catalog, save_catalog  # noqa: E402

# Si el recorrido junta menos de esta fracción de las urls de Elektra que ya
# están en el catálogo, algo salió mal en la API y no se toca nada.
MIN_WALK_RATIO = 0.5


def real_url(offer_url):
    """URL real de la tienda a partir de un enlace de afiliado (parámetro
    ulp=), sin disparar la redirección. Elektra hoy se guarda sin afiliado,
    pero el importador ya soporta --affiliate-base, así que el refresco
    tiene que entender las dos formas."""
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(offer_url).query)
    ulp = qs.get("ulp", [None])[0]
    return urllib.parse.unquote(ulp) if ulp else offer_url


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
    """(precio, listPrice, disponible) vigentes de un producto de la API."""
    items = product.get("items") or []
    if not items:
        return None, None, False
    sellers = items[0].get("sellers") or []
    if not sellers:
        return None, None, False
    offer = sellers[0].get("commertialOffer") or {}
    price = offer.get("Price")
    list_price = offer.get("ListPrice")
    available = bool(price) and offer.get("AvailableQuantity", 0) > 0
    return price, list_price, available


def elektra_offers(product):
    for o in product.get("offers") or []:
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
    for i, path in enumerate(paths, 1):
        seen = 0
        for p in walk_category(path):
            url = p.get("link")
            if not url:
                continue
            price, list_price, available = current_offer(p)
            live[url] = (price, list_price, available)
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

    stats = {"revisados": 0, "precio": 0, "sin_cambio": 0, "agotado": 0, "no_visto": 0}
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
            price, list_price, available = entry
            if not available:
                stats["agotado"] += 1
                dead_urls.add(o["url"])
                continue
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
            if offers and not alive:
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
