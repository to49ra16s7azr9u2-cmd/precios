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

ELEKTRA (04-oct-2026)
---------------------
Desde que se importó el árbol entero (elektra_arbol_a_captura.py) el
catálogo tiene ~234 mil urls de Elektra y las 95 categorías de ELEKTRA_MAP
ven ~65 mil: la regla del MIN_WALK_RATIO abortaba todos los días sin
refrescar nada (además, una categoría padre se corta en 2,500 productos).
Ahora, además de esas 95, cada día se recorre una QUINTA parte de las 843
hojas del árbol (rotando por fecha, partidas por precio), así que cada
publicación se refresca al menos cada 5 días sin que la corrida pase de
~1 h más (la API de Elektra tarda ~2 s por pedido). Y la prueba de que «la
API respondió mal» es la de verdad: si más de la mitad de las categorías
recorridas no devolvió nada (como el 26-sep, cuando el User-Agent de
Chrome recibía 403), no se escribe nada.

USO
---
    python3 scripts/refresh_vtex.py --store chedraui --dry-run
    python3 scripts/refresh_vtex.py --store marti
    python3 scripts/refresh_vtex.py --store elektra --no-prune
"""
import argparse
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from add_elektra_products import HEADERS, PAGE_SIZE, fetch_json, vendedor_publicable  # noqa: E402
from data_io import load_catalog, save_catalog, url_real  # noqa: E402
from ean_dudosos import ean_utilizable  # noqa: E402
import elektra_arbol_a_captura as arbol  # noqa: E402
from elektra_specs import specs_from  # noqa: E402
from vtex_stores import TIENDAS, exigir_autorizacion, search_url  # noqa: E402

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


def hojas_rotativas(paths, n):
    """Las hojas del árbol de Elektra que tocan hoy (una de cada n, rotando
    por fecha). Mismas exclusiones que la importación
    (elektra_arbol_a_captura.py)."""
    import datetime
    from soicos_a_captura import DEPARTAMENTOS_FUERA
    tree = arbol.fetch_json(f"{arbol.BASE}/category/tree/4")
    if not tree:
        print("AVISO: no se pudo leer el árbol de categorías de Elektra; sólo las de siempre.")
        return []
    # Todas las hojas, también las que cuelgan de una de `paths`: una
    # categoría padre de ELEKTRA_MAP se recorre sin partir por precio y VTEX
    # corta en 2,500 productos, así que las 95 ven ~65 mil de ~234 mil.
    hojas = [p for p, nombres in arbol.hojas(tree)
             if nombres[0].strip().lower() not in arbol.DEPTOS_FUERA
             and not any(DEPARTAMENTOS_FUERA.search(x) for x in nombres)]
    k = datetime.date.today().toordinal() % max(1, n)
    return hojas[k::max(1, n)]


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
    ap.add_argument("--rotacion", type=int, default=5,
                    help="Elektra: cuántos días tarda en recorrerse el resto del árbol (default 5)")
    args = ap.parse_args(argv)
    exigir_autorizacion(args.store)
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
    rotativas = hojas_rotativas(paths, args.rotacion) if args.store == "elektra" and not args.limit_categories else []
    if rotativas:
        print(f"Hojas del árbol de hoy, además de las {len(paths)} categorías (1 de cada {args.rotacion}): {len(rotativas)}")

    # Sonda: un pedido a la primera categoría, mostrando el error tal cual.
    # fetch_json se traga los errores y devuelve None, así que cuando la
    # tienda bloquea la IP del runner (Elektra desde GitHub Actions, 26-sep-
    # 2026: 95 categorías con 0 productos, 17 min perdidos) no se sabía por
    # qué. Si la sonda no trae nada, se sale ya.
    sonda = f"{search_url(args.store)}?fq=C:/{paths[0]}/&_from=0&_to=0"
    try:
        with urllib.request.urlopen(urllib.request.Request(sonda, headers=HEADERS), timeout=25) as r:
            print(f"Sonda: HTTP {r.status}")
    except Exception as e:  # noqa: BLE001
        print(f"ABORTA: la API de {tienda['nombre']} no responde desde aquí ({e!r}). No se escribió nada.")
        return 2

    live, fichas = {}, {}
    vacias = 0
    recorridos = [(path, None) for path in paths] + [(path, "arbol") for path in rotativas]
    for i, (path, modo) in enumerate(recorridos, 1):
        seen = 0
        productos = arbol.recorrer_entera(path) if modo else walk_category(args.store, path)
        for p in productos:
            url = p.get("link")
            if not url:
                continue
            live[url] = current_offer(p)
            fichas[url] = specs_from(p)
            seen += 1
        if not seen:
            vacias += 1
        print(f"  [{i}/{len(recorridos)}] {path}: {seen} productos ({len(live)} acumulados)")

    covered = len(catalog_urls & set(live))
    ratio = covered / len(catalog_urls)
    print(f"\nRecorrido: {len(live)} productos vivos; cubre {covered} ({ratio:.0%}) de las urls del catálogo; "
          f"{vacias} de {len(recorridos)} categorías sin nada")
    if rotativas:
        # Elektra: el recorrido de un día ve a propósito sólo una parte del
        # catálogo; lo que delata una API caída son las categorías vacías.
        if vacias > len(recorridos) / 2:
            print("ABORTA: más de la mitad de las categorías no devolvió nada. Eso apunta a un problema "
                  "de la API. No se escribió nada.", file=sys.stderr)
            sys.exit(2)
    elif ratio < MIN_WALK_RATIO and not args.limit_categories:
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
            if not ean_utilizable(o):
                # El código que publica la tienda en esta oferta no es el de
                # lo que vende (ver scripts/ean_dudosos.py). Si se reescribe
                # acá, el refresco de mañana deshace la separación hecha a
                # mano y el multipack vuelve a unirse con la pieza suelta.
                o.pop("ean", None)
            elif ean and o.get("ean") != ean:
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
    sys.exit(main())
