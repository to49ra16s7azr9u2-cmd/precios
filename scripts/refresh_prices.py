#!/usr/bin/env python3
"""Actualiza los precios guardados en data/data.json contra Mercado Libre, y
opcionalmente saca del catálogo lo que ya no se puede comprar.

POR QUÉ HACE FALTA
------------------
La ficha de producto refresca precios en vivo al abrirla (ver refreshLiveOffers
en js/app.js), pero el resto del sitio no: la portada, los rankings, las listas
por categoría y las páginas estáticas de SEO se pintan con lo que hay guardado
en data/data.json. Si eso queda viejo, el usuario ve un precio en la lista,
entra, y ve otro — que es justo lo que reportó (iPhone 17 256 GB: $15,896
guardado contra $18,485 reales).

Este script recorre el catálogo y pide a cada producto su precio vigente por su
id de catálogo (.../p/MLM…), que es exacto y barato (2 subpeticiones), en vez de
volver a buscarlo por texto.

Con --prune (activado por defecto; --no-prune lo desactiva) también saca del
catálogo las publicaciones que Mercado Libre ya no tiene a la venta ("sin
ofertas activas" / 404 "No winners found"): mostrar un precio y un botón "Ver
oferta" que lleva a una página sin nada que comprar es peor que no listar el
producto. Un producto fusionado por color (colorVariants) que pierde solo
ALGUNOS colores se queda con los que sigan vivos; solo se elimina el producto
entero cuando NINGUNA de sus opciones de compra sigue activa.

REQUIERE el Worker con el endpoint /item?id= desplegado (backend/
mercadolibre-worker). Contra el Worker viejo todas las llamadas responden 400 y
el script no cambia nada (lo dice y termina).

USO
---
    python3 scripts/refresh_prices.py --dry-run --limit 50   # ver qué cambiaría
    python3 scripts/refresh_prices.py --limit 500            # aplicar por tandas
    python3 scripts/refresh_prices.py                        # catálogo completo, con poda
    python3 scripts/refresh_prices.py --no-prune              # solo precios, sin borrar nada

Es reanudable: --offset salta los primeros N productos, así se puede avanzar por
tandas sin repetir. Guarda en cada tanda (--save-every) para no perder el avance
si se interrumpe. La poda se aplica siempre al final, sobre el catálogo
completo (no por tanda), así una corrida con --offset/--limit nunca borra un
producto por no haber sido parte de esa tanda.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHIPPING_RATES_PATH = os.path.join(ROOT, "data", "shipping-rates.json")
PROXY = "https://comparamx-mercadolibre-proxy.comparamx.workers.dev/item"

CATALOG_ID = re.compile(r"/p/(MLM\d+)")


def catalog_id(url):
    m = CATALOG_ID.search(url or "")
    return m.group(1) if m else None


def seller_url(product_id, item_id):
    """Enlace a la oferta de UN vendedor dentro de un producto de catálogo.

    La API no da el permalink de cada publicación (viene vacío en
    /products/{id} y /items/{id} responde 403 con el token de esta app), así
    que se arma sobre la URL del producto de catálogo -- la que el sitio ya
    usaba -- agregándole el filtro que Mercado Libre entiende para abrir a un
    vendedor concreto. Verificado a mano contra dos publicaciones del iPhone
    17: abrieron $18,855 y $19,499 en vez del precio de la caja de compra.

    Si Mercado Libre dejara de reconocer el parámetro, la URL sigue siendo la
    del producto: se degrada a lo que se mostraba antes, no a un 404.
    """
    return f"https://www.mercadolibre.com.mx/p/{product_id}?pdp_filters=item_id:{item_id}"


def sellers_of(res, product_id):
    """Vendedores normalizados de la respuesta del Worker, listos para guardar.

    Solo tiene sentido guardar la lista cuando hay MÁS DE UNO: con uno solo
    el frontend no expande filas (sellerRows exige length >= 2) y el dato es
    peso muerto -- guardarlo igual infló data.json en ~4,800 productos sin
    ningún beneficio antes de que se notara acá.
    """
    out = []
    for s in res.get("sellers") or []:
        item_id, price = s.get("itemId"), s.get("price")
        if not item_id or not isinstance(price, (int, float)) or price <= 0:
            continue
        row = {"itemId": item_id, "price": price, "url": seller_url(product_id, item_id)}
        # Solo se guardan los campos que de verdad traen dato: un null por
        # vendedor multiplicado por ~7,700 productos es peso muerto en el JSON
        # que el navegador descarga en cada visita.
        if s.get("listPrice"):
            row["listPrice"] = s["listPrice"]
        if s.get("shippingFee") == 0:
            row["shippingFee"] = 0
        if s.get("state"):
            row["state"] = s["state"]
        if s.get("official"):
            row["official"] = True
        out.append(row)
    return out if len(out) > 1 else []


def fetch_by_id(mlm_id, retries=2):
    """Precio vigente de un producto de catálogo. None si no se pudo."""
    url = f"{PROXY}?id={urllib.parse.quote(mlm_id)}"
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ComparaMEX-refresh/1.0"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            # 404 = sin ofertas activas / producto retirado: es una respuesta
            # legítima, no un fallo de red, así que no se reintenta.
            if e.code in (400, 404):
                return {"__http": e.code}
            if attempt == retries:
                return None
            time.sleep(1.5 * (attempt + 1))
        except Exception:
            if attempt == retries:
                return None
            time.sleep(1.5 * (attempt + 1))
    return None


def targets_of(product):
    """(etiqueta, nodo) por cada precio actualizable del producto."""
    out = []
    for i, o in enumerate(product.get("offers") or []):
        if catalog_id(o.get("url")):
            out.append((f"offer[{i}]", o))
    for i, v in enumerate(product.get("colorVariants") or []):
        if catalog_id(v.get("url")):
            out.append((f"variant[{i}]", v))
    return out


def prune_dead(products, dead_ids):
    """Saca del catálogo lo que ya no se puede comprar en ninguna tienda.

    dead_ids: ids de catálogo (MLM…) confirmados sin ofertas activas.
    Devuelve (productos_sobrevivientes, ids_removidos, variantes_recortadas).
    """
    survivors = []
    removed = []
    trimmed = 0
    for p in products:
        offers = p.get("offers") or []
        variants = p.get("colorVariants") or []
        if len(variants) > 1:
            alive = [v for v in variants if catalog_id(v.get("url")) not in dead_ids]
            if not alive:
                removed.append(p["id"])
                continue
            if len(alive) < len(variants):
                trimmed += len(variants) - len(alive)
                p["colorVariants"] = alive
                # offers[0] es la base compartida (tienda, puntos, calificación,
                # stock) de la que cada variante toma esos campos -- si su URL
                # era justo la que murió, se repunta a la más barata que
                # sobreviva para que ese apuntador siga siendo válido.
                if offers and catalog_id(offers[0].get("url")) not in {catalog_id(v["url"]) for v in alive}:
                    cheapest = min(alive, key=lambda v: v["price"])
                    offers[0] = {**offers[0], "price": cheapest["price"], "url": cheapest["url"], "photo": cheapest.get("photo")}
            survivors.append(p)
            continue
        # Sin fusión de color: se recortan directo de offers[] las que tengan
        # id de catálogo y estén muertas (una oferta sin id de catálogo -- otra
        # tienda -- nunca se toca acá, no se pudo verificar).
        alive_offers = [
            o for o in offers
            if not (catalog_id(o.get("url")) and catalog_id(o["url"]) in dead_ids)
        ]
        if not alive_offers:
            removed.append(p["id"])
            continue
        if len(alive_offers) < len(offers):
            trimmed += len(offers) - len(alive_offers)
            p["offers"] = alive_offers
        survivors.append(p)
    return survivors, removed, trimmed


def refresh_usd_mxn_rate():
    """Actualiza el tipo de cambio de la calculadora de envío.

    data/shipping-rates.json guarda las tarifas en USD y un `usdToMxn` que
    js/app.js usa para mostrarlas en pesos. Ese número estaba escrito a mano
    y nada lo tocaba: los precios de producto sí se recalculaban con el tipo
    de cambio del día (refresh_other_stores.py), pero el del envío se
    quedaba congelado, así que con el tiempo la columna "Costo estimado"
    iba a decir pesos calculados con un dólar viejo.

    Si la consulta falla se deja el valor que había: es preferible una
    cotización de ayer que romper la corrida diaria entera.
    """
    try:
        req = urllib.request.Request(
            "https://api.exchangerate-api.com/v4/latest/USD",
            headers={"User-Agent": "ComparaMEX-bot/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            rate = json.loads(r.read().decode("utf-8"))["rates"]["MXN"]
    except Exception as e:
        print(f"  tipo de cambio: no se pudo consultar ({e}); se deja el guardado")
        return False
    with open(SHIPPING_RATES_PATH, encoding="utf-8") as f:
        rates = json.load(f)
    old = rates["meta"].get("usdToMxn")
    rate = round(float(rate), 2)
    if old == rate:
        print(f"  tipo de cambio: sin cambio ({rate} MXN/USD)")
        return False
    rates["meta"]["usdToMxn"] = rate
    rates["meta"]["lastUpdated"] = time.strftime("%Y-%m-%d")
    with open(SHIPPING_RATES_PATH, "w", encoding="utf-8") as f:
        json.dump(rates, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"  tipo de cambio: {old} -> {rate} MXN/USD")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="máximo de productos a procesar (0 = todos)")
    ap.add_argument("--offset", type=int, default=0, help="saltar los primeros N productos")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--save-every", type=int, default=100, help="guardar cada N productos")
    ap.add_argument("--dry-run", action="store_true", help="no escribe data.json")
    ap.add_argument("--prune", dest="prune", action="store_true", default=True,
                     help="saca del catálogo lo que quedó sin ofertas activas (default)")
    ap.add_argument("--no-prune", dest="prune", action="store_false",
                     help="solo actualiza precios, no borra nada")
    args = ap.parse_args()

    if not args.dry_run:
        refresh_usd_mxn_rate()

    data = load_catalog()

    all_products = data["products"]
    products = all_products[args.offset:]
    if args.limit:
        products = products[: args.limit]
    print(f"Productos a revisar: {len(products)} (offset {args.offset})")

    # Sonda única antes de empezar: si el Worker desplegado todavía no entiende
    # ?id=, no tiene sentido lanzar miles de llamadas que van a fallar todas
    # (y, peor, con --prune activado se leería "sin ofertas activas" en TODO
    # el catálogo y se borraría todo).
    probe_id = next(
        (catalog_id(n["url"]) for p in products for _, n in targets_of(p)),
        None,
    )
    if probe_id is None:
        print("Ninguno de estos productos tiene URL de catálogo de Mercado Libre; nada que hacer.")
        return
    probe = fetch_by_id(probe_id)
    if probe is None or probe.get("__http") == 400:
        print(
            "El Worker no reconoce ?id= (HTTP 400).\n"
            "Despliega la versión nueva antes de usar este script:\n"
            "    cd backend/mercadolibre-worker && npx wrangler deploy",
            file=sys.stderr,
        )
        raise SystemExit(2)

    stats = {"revisados": 0, "actualizados": 0, "sin_cambio": 0, "sin_oferta": 0, "error": 0, "precios": 0, "fotos": 0}
    max_delta = []
    dead_ids = set()

    def work(product):
        changed = False
        for label, node in targets_of(product):
            cid = catalog_id(node["url"])
            res = fetch_by_id(cid)
            if res is None:
                stats["error"] += 1
                continue
            if res.get("__http") == 404 or res.get("__http") == 400 or not res.get("price"):
                stats["sin_oferta"] += 1
                dead_ids.add(cid)
                continue
            new_price = res["price"]
            old_price = node.get("price")
            # Cuántos vendedores tiene ese producto de catálogo y a cuánto lo
            # da el más barato. El Worker ya calculaba las dos cosas y las
            # tiraba: no se guardaban en ningún lado. Midiendo sobre una
            # muestra de 119 productos, el 41% tiene MÁS DE UN vendedor, así
            # que sin este dato la ficha decía "1 opción de compra" en miles
            # de productos donde sí hay comparación posible.
            #
            # Se escriben ANTES del corte por "precio sin cambios" de abajo:
            # si no, un producto cuyo precio no se movió nunca llegaría a
            # actualizar su número de vendedores.
            sc = res.get("sellerCount")
            if isinstance(sc, int) and sc > 0 and node.get("sellerCount") != sc:
                node["sellerCount"] = sc
                changed = True
            lowest = res.get("lowestPrice")
            # lowestPrice solo tiene sentido si de verdad es más barato que
            # el de la caja de compra; el Worker ya manda null cuando no.
            if lowest and lowest < new_price:
                if node.get("lowestPrice") != lowest:
                    node["lowestPrice"] = lowest
                    changed = True
            elif node.get("lowestPrice") is not None:
                node["lowestPrice"] = None
                changed = True
            # Vendedores uno por uno, para armar una fila por vendedor en la
            # tabla. Va junto a los dos campos de arriba, antes del corte por
            # "precio sin cambios".
            sellers = sellers_of(res, cid)
            if sellers and node.get("sellers") != sellers:
                node["sellers"] = sellers
                changed = True
            elif not sellers and node.get("sellers"):
                del node["sellers"]
                changed = True
            # Foto faltante: 343 productos de Mercado Libre no tenían NINGUNA
            # imagen (ni en el producto ni en la oferta) y se pintaban como
            # una tarjeta vacía. El Worker ya devuelve la foto en cada
            # consulta y no se estaba usando. Va junto a los campos de arriba,
            # antes del corte por "precio sin cambios": si no, un producto con
            # precio estable no recuperaría nunca su imagen. Solo se rellena
            # lo que falta -- una foto ya elegida no se pisa.
            photo = res.get("photo")
            if photo:
                if not product.get("photo"):
                    product["photo"] = photo
                    stats["fotos"] += 1
                    changed = True
                if not node.get("photo"):
                    node["photo"] = photo
                    changed = True
            if old_price is not None and abs(new_price - old_price) < 0.005:
                stats["sin_cambio"] += 1
                continue
            if old_price:
                max_delta.append((abs(new_price - old_price) / old_price, product["id"], product["name"], old_price, new_price))
            node["price"] = new_price
            # priceOriginal es el precio tachado: solo se guarda si de verdad
            # es mayor que el vigente. Si el descuento se terminó, se limpia el
            # listPrice viejo en vez de dejar un "-30%" que ya no existe.
            lp = res.get("priceOriginal")
            if lp and lp > new_price:
                node["listPrice"] = lp
            elif "listPrice" in node:
                node["listPrice"] = None
            if res.get("shippingFree"):
                node["shippingFee"] = 0
            stats["precios"] += 1
            changed = True
        return changed

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        for i, changed in enumerate(pool.map(work, products), 1):
            stats["revisados"] += 1
            if changed:
                stats["actualizados"] += 1
            if i % 25 == 0:
                print(f"  {i}/{len(products)} — {stats['precios']} precios actualizados, {len(dead_ids)} sin ofertas", flush=True)
            if not args.dry_run and args.save_every and i % args.save_every == 0:
                save_catalog(data)

    removed_ids = []
    trimmed = 0
    if args.prune and dead_ids:
        before = len(all_products)
        survivors, removed_ids, trimmed = prune_dead(all_products, dead_ids)
        data["products"] = survivors
        print(f"\nPoda: {before - len(survivors)} productos sin ninguna oferta activa, "
              f"{trimmed} variantes de color individuales recortadas (producto sobrevive con las demás).")

    if not args.dry_run:
        save_catalog(data)

    print("\n=== Resumen ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    if args.prune:
        print(f"  productos_eliminados: {len(removed_ids)}")
        print(f"  variantes_recortadas: {trimmed}")
    max_delta.sort(reverse=True)
    if max_delta:
        print("\n  Mayores diferencias contra lo guardado:")
        for pct, pid, name, old, new in max_delta[:15]:
            print(f"   {pct*100:5.1f}%  {pid}  {name[:44]:44}  {old:>10,.2f} -> {new:>10,.2f}")
    if removed_ids:
        print(f"\n  Productos eliminados ({len(removed_ids)}): {', '.join(removed_ids[:30])}"
              + (" ..." if len(removed_ids) > 30 else ""))
    if args.dry_run:
        print("\n(--dry-run: no se escribió data/data.json)")


if __name__ == "__main__":
    main()
