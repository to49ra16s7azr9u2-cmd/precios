#!/usr/bin/env python3
"""Refresca precios (y baja lo agotado) de los productos de una tienda VTEX.

Es refresh_elektra.py hecho genérico para las tiendas de vtex_stores.py
(Elektra, Chedraui, Martí): se re-recorren las mismas categorías del
importador con la API pública de catálogo, de a 50 productos por pedido,
se arma un mapa url -> (precio, listPrice, disponible, ean, vendedor) y se
aplica al catálogo. El "cómo" y el "qué se poda" están explicados en el
encabezado de refresh_elektra.py y no cambian:

  - "visto y agotado" se poda (--no-prune lo desactiva);
  - "no visto" NO se poda salvo --prune-missing;
  - si el recorrido cubre menos de MIN_WALK_RATIO de las urls que ya están
    en el catálogo, no se escribe nada (la API respondió mal).

USO
---
    python3 scripts/refresh_vtex.py --store chedraui --dry-run
    python3 scripts/refresh_vtex.py --store marti
    python3 scripts/refresh_vtex.py --store elektra --no-prune
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from add_elektra_products import PAGE_SIZE, fetch_json, vendedor_publicable  # noqa: E402
from data_io import load_catalog, save_catalog, url_real  # noqa: E402
from elektra_specs import specs_from  # noqa: E402
from vtex_stores import TIENDAS, search_url  # noqa: E402

# Si el recorrido junta menos de esta fracción de las urls de la tienda que
# ya están en el catálogo, algo salió mal en la API y no se toca nada.
MIN_WALK_RATIO = 0.5


def current_offer(product):
    """(precio, listPrice, disponible, ean, sellerId) vigentes de un producto
    de la API. El precio es el del vendedor que elige vendedor_publicable()
    (el más barato con existencia, la tienda a igual precio), no el del
    primero de la lista. El `ean` se guarda aunque no siempre sea un código
    del fabricante (ver match_by_gtin.py): acá se anota lo que publica la
    tienda, sin interpretarlo."""
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


def walk_category(store_id, path):
    base = search_url(store_id)
    frm = 0
    while True:
        batch = fetch_json(f"{base}?fq=C:/{path}/&_from={frm}&_to={frm + PAGE_SIZE - 1}")
        if not batch:
            return
        for p in batch:
            yield p
        if len(batch) < PAGE_SIZE:
            return
        frm += PAGE_SIZE


def ofertas_de(product, store_id):
    """Las ofertas de la tienda, incluidas las de colorVariants[].offers."""
    for o in product.get("offers") or []:
        if o.get("storeId") == store_id:
            yield o
    for v in product.get("colorVariants") or []:
        for o in v.get("offers") or []:
            if o.get("storeId") == store_id:
                yield o


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True, choices=sorted(TIENDAS))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--prune", dest="prune", action="store_true", default=True)
    ap.add_argument("--no-prune", dest="prune", action="store_false")
    ap.add_argument("--prune-missing", action="store_true")
    ap.add_argument("--limit-categories", type=int, default=0, help="solo para pruebas")
    args = ap.parse_args(argv)
    tienda = TIENDAS[args.store]

    data = load_catalog()
    catalog_urls = {
        url_real(o["url"]) or o["url"]
        for p in data["products"]
        for o in ofertas_de(p, args.store)
        if o.get("url")
    }
    print(f"Ofertas de {tienda['nombre']} en el catálogo: {len(catalog_urls)} urls distintas")
    if not catalog_urls:
        return

    paths = list(tienda["categorias"])
    if args.limit_categories:
        paths = paths[: args.limit_categories]

    live, fichas = {}, {}
    for i, path in enumerate(paths, 1):
        seen = 0
        for p in walk_category(args.store, path):
            url = p.get("link")
            if not url:
                continue
            live[url] = current_offer(p)
            fichas[url] = specs_from(p)
            seen += 1
        print(f"  [{i}/{len(paths)}] {path}: {seen} productos ({len(live)} acumulados)")

    covered = len(catalog_urls & set(live))
    ratio = covered / len(catalog_urls)
    print(f"\nRecorrido: {len(live)} productos vivos; cubre {covered} ({ratio:.0%}) de las urls del catálogo")
    if ratio < MIN_WALK_RATIO and not args.limit_categories:
        print(f"ABORTA: el recorrido cubrió menos del {MIN_WALK_RATIO:.0%} del catálogo. "
              "Eso apunta a un problema de la API, no a bajas masivas. No se escribió nada.",
              file=sys.stderr)
        sys.exit(2)

    stats = {"revisados": 0, "precio": 0, "sin_cambio": 0, "agotado": 0, "no_visto": 0, "ficha_tecnica": 0}
    deltas = []
    dead_urls, missing_urls = set(), set()
    for p in data["products"]:
        for o in ofertas_de(p, args.store):
            url = url_real(o.get("url") or "") or o.get("url")
            if not url:
                continue
            stats["revisados"] += 1
            entry = live.get(url)
            if entry is None:
                stats["no_visto"] += 1
                missing_urls.add(o["url"])
                continue
            ficha = fichas.get(url) or []
            if ficha and len(ficha) > len(p.get("specs") or []) and p.get("specs") != ficha:
                p["specs"] = ficha
                stats["ficha_tecnica"] += 1
            price, list_price, available, ean, seller_id = entry
            if ean and o.get("ean") != ean:
                o["ean"] = ean
            if not available:
                stats["agotado"] += 1
                dead_urls.add(o["url"])
                continue
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
    print(f"\nCatálogo actualizado: {stats['precio']} precios, {removed} bajas, total {len(data['products'])} productos")


if __name__ == "__main__":
    main()
