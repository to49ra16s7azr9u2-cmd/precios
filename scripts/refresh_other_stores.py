#!/usr/bin/env python3
"""Refresca precios y poda bajas para las tiendas SIN API en vivo conectada
(SUNSKY, theluxurycloset, GeekBuying, Glasseslit — ver LIVE_API_CONFIG en
js/app.js, donde solo mercadolibre está enabled). scripts/refresh_prices.py
ya cubre Mercado Libre; este script es su equivalente para estas 4.

POR QUÉ ESTAS 4 Y NO LAS OTRAS
------------------------------
Se probó primero a mano (curl a una URL real de cada tienda) qué tan
confiable es leer el precio vigente sin una API oficial:

  - SUNSKY, theluxurycloset, GeekBuying, Glasseslit: la página del producto
    trae datos estructurados legibles a máquina -- JSON-LD schema.org/Product
    (precio, moneda, disponibilidad) o al menos meta og:price:amount/currency.
    Ninguna bloqueó el pedido ni exigió JavaScript.
  - AliExpress: redirige según la región detectada del pedido a un id de
    producto DISTINTO (probado con datos reales: pedir el id X devolvió una
    página del id Y, "adaptado" a EE.UU.) -- el precio que se leería no
    sería confiablemente el de la publicación enlazada. Necesitaría su API
    oficial de afiliados, no scraping.
  - Alibaba: sin datos estructurados de precio en la página (B2B, cotiza por
    cantidad); Molnija (ruso) y Woodestic (WooCommerce) tienen precio en
    texto plano sin marcado estándar, piden un parser dedicado por sitio con
    volumen demasiado chico (28 y 64 productos) para justificarlo todavía.

Estas 4 suman 2,506 de los ~4,500 productos "de referencia" del catálogo.

CÓMO LLEGA A LA URL REAL
-------------------------
Las ofertas de estas tiendas están guardadas como enlaces de afiliado de
Admitad (dominios de tracking como rzekl.com, codeaven.com, ad.admitad.com…),
con la URL real de la tienda en el parámetro `ulp=`. Se decodifica ese
parámetro en vez de seguir la redirección HTTP -- seguirla contaría un clic
de afiliado real por cada producto revisado, todos los días, ensuciando las
estadísticas del programa sin que haya un visitante de verdad detrás.

MONEDA
------
Las 4 cotizan en USD; el catálogo guarda todo en MXN. Se convierte con el
tipo de cambio del día (api.exchangerate-api.com, gratis, sin API key) --
mismo mecanismo que ya se usa (implícito) para los precios existentes: el
guardado de un producto SUNSKY de prueba, $7,854 MXN, contra sus $462.00 USD
reales, implica ~17.0 MXN/USD, casi exacto al tipo de cambio del día en que
se escribió este script (17.03).

USO
---
    python3 scripts/refresh_other_stores.py --dry-run --limit 30
    python3 scripts/refresh_other_stores.py
    python3 scripts/refresh_other_stores.py --no-prune   # solo precios
"""
import argparse
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "data", "data.json")

SUPPORTED_STORES = {"sunsky", "theluxurycloset", "geekbuying", "glasseslit"}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

LD_JSON_RE = re.compile(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S)
OG_PRICE_RE = re.compile(r'<meta[^>]+(?:og|product):price:amount[^>]+content=["\']([^"\']+)', re.I)
OG_CURRENCY_RE = re.compile(r'<meta[^>]+(?:og|product):price:currency[^>]+content=["\']([^"\']+)', re.I)


def real_url(offer_url):
    """URL real de la tienda a partir del enlace de afiliado de Admitad
    (parámetro ulp=), sin disparar la redirección (que contaría un clic)."""
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(offer_url).query)
    ulp = qs.get("ulp", [None])[0]
    return urllib.parse.unquote(ulp) if ulp else None


# Límite de ritmo POR DOMINIO (no global): con varias tiendas mezcladas en el
# mismo pool de hilos, un concurrency alto igual pega varias veces por
# segundo al MISMO sitio si a ese hilo le tocan varios productos seguidos de
# esa tienda. Probando en vivo, SUNSKY empezó a devolver 403 tras unas pocas
# decenas de pedidos en poco tiempo -- nada catastrófico (fetch_html
# devuelve None, se cuenta como "sin_datos", nunca se confunde con "sin
# stock"), pero desperdicia el pedido. Un mínimo de separación por dominio
# reduce cuántos pedidos terminan bloqueados sin cambiar el resultado final.
_domain_locks = {}
_domain_last_request = {}
_domain_lock_guard = threading.Lock()
MIN_INTERVAL_PER_DOMAIN = 0.6


def _throttle(domain):
    with _domain_lock_guard:
        lock = _domain_locks.setdefault(domain, threading.Lock())
    with lock:
        last = _domain_last_request.get(domain, 0)
        wait = MIN_INTERVAL_PER_DOMAIN - (time.time() - last)
        if wait > 0:
            time.sleep(wait)
        _domain_last_request[domain] = time.time()


def fetch_html(url, retries=2):
    domain = urllib.parse.urlparse(url).netloc
    for attempt in range(retries + 1):
        _throttle(domain)
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.read().decode("utf-8", errors="ignore")
        except Exception:
            if attempt == retries:
                return None
            time.sleep(1.5 * (attempt + 1))
    return None


def _find_all_products(node, out):
    """Recorre un árbol JSON-LD (soporta @graph anidado) juntando TODOS los
    nodos @type Product con un campo offers -- una página de producto puede
    traer más de uno (p. ej. theluxurycloset agrega un carrusel de
    "también te puede interesar" con su propio JSON-LD por artículo, además
    del producto principal)."""
    if isinstance(node, dict):
        t = node.get("@type")
        types = t if isinstance(t, list) else [t]
        if "Product" in types and node.get("offers"):
            out.append(node)
        for v in node.values():
            _find_all_products(v, out)
    elif isinstance(node, list):
        for item in node:
            _find_all_products(item, out)


def _pick_offers(products, target_path):
    """De varios nodos Product en la misma página, el que de verdad
    corresponde al producto pedido -- por si el orden de aparición en el
    HTML no fuera confiable (no se puede asumir que el primero sea siempre
    el principal). Se matchea por si la URL del target_path (la ruta de la
    página que se pidió) aparece dentro de offers.url; si ninguno matchea
    (o no hay target_path que comparar), se cae al primero encontrado."""
    for p in products:
        offers = p.get("offers")
        offers_url = (offers.get("url") if isinstance(offers, dict) else None) or ""
        if target_path and target_path in offers_url:
            return offers
    return products[0]["offers"] if products else None


def extract_price(html, target_url=None):
    """(price, currency, available) leídos de la página, o None si no se
    pudo leer nada confiable.

    available=False SOLO cuando el propio campo estructurado `availability`
    de schema.org/Offer lo dice explícitamente (OutOfStock/Discontinued).
    NO se usa una búsqueda de texto tipo "sold out" en toda la página como
    señal de baja: se probó con datos reales (Glasseslit, producto con
    $39.95 y en stock, confirmado con una consulta en vivo aparte) y dio un
    falso positivo -- el texto aparecía en otra parte de la página (reseñas,
    carrusel de "productos relacionados", etc.), no en la ficha del producto
    en sí. Un falso positivo acá borra un producto que sigue a la venta, así
    que la barra para "muerto" es deliberadamente alta: solo el campo
    `availability` del propio Offer, nunca texto suelto.
    """
    target_path = urllib.parse.urlparse(target_url).path if target_url else None
    for block in LD_JSON_RE.findall(html):
        try:
            data = json.loads(block)
        except Exception:
            continue
        products = []
        _find_all_products(data, products)
        offers = _pick_offers(products, target_path)
        if not offers:
            continue
        if isinstance(offers, list):
            offers = offers[0] if offers else None
        if not isinstance(offers, dict):
            continue
        avail = str(offers.get("availability") or "")
        available = "OutOfStock" not in avail and "Discontinued" not in avail
        price = offers.get("price")
        currency = offers.get("priceCurrency") or "USD"
        if price:
            try:
                return float(str(price).replace(",", "")), currency, available
            except ValueError:
                pass
        # JSON-LD con Product pero sin precio (p. ej. agotado): la señal de
        # disponibilidad sigue siendo válida aunque no haya precio que leer.
        if avail:
            return None, currency, available

    # Sin JSON-LD con disponibilidad explícita: og:price alcanza para
    # actualizar el precio, pero NUNCA para dar de baja el producto (no hay
    # una señal de "agotado" confiable en este camino -- ver el docstring).
    m = OG_PRICE_RE.search(html)
    if m:
        cm = OG_CURRENCY_RE.search(html)
        currency = cm.group(1) if cm else "USD"
        try:
            return float(m.group(1)), currency, True
        except ValueError:
            pass

    return None


def targets_of(product):
    out = []
    for i, o in enumerate(product.get("offers") or []):
        if o.get("storeId") in SUPPORTED_STORES:
            out.append((f"offer[{i}]", o))
    for i, v in enumerate(product.get("colorVariants") or []):
        # Los colorVariants heredan storeId de offers[0] (ver purchaseOptions
        # en js/app.js); mismo criterio acá.
        base_store = (product.get("offers") or [{}])[0].get("storeId")
        if base_store in SUPPORTED_STORES:
            out.append((f"variant[{i}]", v))
    return out


def get_usd_mxn_rate():
    try:
        req = urllib.request.Request("https://api.exchangerate-api.com/v4/latest/USD", headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
        return data["rates"]["MXN"]
    except Exception as e:
        print(f"No se pudo obtener el tipo de cambio USD/MXN en vivo ({e}); "
              f"no se puede seguir sin él.", file=sys.stderr)
        raise SystemExit(2)


def prune_dead(products, dead_urls):
    survivors, removed, trimmed = [], [], 0
    for p in products:
        offers = p.get("offers") or []
        variants = p.get("colorVariants") or []
        if len(variants) > 1 and any(v["url"] in dead_urls for v in variants):
            alive = [v for v in variants if v["url"] not in dead_urls]
            if not alive:
                removed.append(p["id"])
                continue
            if len(alive) < len(variants):
                trimmed += len(variants) - len(alive)
                p["colorVariants"] = alive
                if offers and offers[0].get("url") not in {v["url"] for v in alive}:
                    cheapest = min(alive, key=lambda v: v["price"])
                    offers[0] = {**offers[0], "price": cheapest["price"], "url": cheapest["url"], "photo": cheapest.get("photo")}
            survivors.append(p)
            continue
        alive_offers = [o for o in offers if o["url"] not in dead_urls]
        if offers and not alive_offers:
            removed.append(p["id"])
            continue
        if len(alive_offers) < len(offers):
            trimmed += len(offers) - len(alive_offers)
            p["offers"] = alive_offers
        survivors.append(p)
    return survivors, removed, trimmed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--save-every", type=int, default=200)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--prune", dest="prune", action="store_true", default=True)
    ap.add_argument("--no-prune", dest="prune", action="store_false")
    args = ap.parse_args()

    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    all_products = data["products"]

    candidates = [p for p in all_products if targets_of(p)]
    products = candidates[args.offset:]
    if args.limit:
        products = products[: args.limit]
    print(f"Productos con oferta en {sorted(SUPPORTED_STORES)}: {len(candidates)}; a revisar ahora: {len(products)}")
    if not products:
        return

    rate = get_usd_mxn_rate()
    print(f"Tipo de cambio USD/MXN de hoy: {rate}")

    stats = {"revisados": 0, "precios": 0, "sin_cambio": 0, "sin_datos": 0, "sin_stock": 0}
    dead_urls = set()
    max_delta = []

    def work(product):
        changed = False
        for label, node in targets_of(product):
            url = real_url(node["url"])
            if not url:
                stats["sin_datos"] += 1
                continue
            html = fetch_html(url)
            if not html:
                stats["sin_datos"] += 1
                continue
            result = extract_price(html, target_url=url)
            if not result:
                stats["sin_datos"] += 1
                continue
            price_usd, currency, available = result
            if not available:
                stats["sin_stock"] += 1
                dead_urls.add(node["url"])
                continue
            if price_usd is None:
                stats["sin_datos"] += 1
                continue
            fx = rate if currency == "USD" else 1.0
            if currency not in ("USD", "MXN"):
                # Moneda no contemplada (p. ej. si algún producto cambia de
                # tienda de origen): no se inventa una conversión.
                stats["sin_datos"] += 1
                continue
            new_price = round(price_usd * fx, 2)
            old_price = node.get("price")
            if old_price is not None and abs(new_price - old_price) / max(old_price, 1) < 0.01:
                stats["sin_cambio"] += 1
                continue
            if old_price:
                max_delta.append((abs(new_price - old_price) / old_price, product["id"], product["name"], old_price, new_price))
            node["price"] = new_price
            stats["precios"] += 1
            changed = True
        return changed

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        for i, changed in enumerate(pool.map(work, products), 1):
            stats["revisados"] += 1
            if i % 50 == 0:
                print(f"  {i}/{len(products)} — {stats['precios']} precios, {len(dead_urls)} sin stock", flush=True)
            if not args.dry_run and args.save_every and i % args.save_every == 0:
                with open(DATA_PATH, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

    removed_ids, trimmed = [], 0
    if args.prune and dead_urls:
        before = len(all_products)
        survivors, removed_ids, trimmed = prune_dead(all_products, dead_urls)
        data["products"] = survivors
        print(f"\nPoda: {before - len(survivors)} productos sin stock en ninguna de sus ofertas de estas tiendas, "
              f"{trimmed} variantes recortadas.")

    if not args.dry_run:
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print("\n=== Resumen ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    if args.prune:
        print(f"  productos_eliminados: {len(removed_ids)}")
        print(f"  variantes_recortadas: {trimmed}")
    max_delta.sort(reverse=True)
    if max_delta:
        print("\n  Mayores diferencias:")
        for pct, pid, name, old, new in max_delta[:15]:
            print(f"   {pct*100:5.1f}%  {pid}  {name[:44]:44}  {old:>10,.2f} -> {new:>10,.2f}")
    if removed_ids:
        print(f"\n  Eliminados ({len(removed_ids)}): {', '.join(removed_ids[:30])}" + (" ..." if len(removed_ids) > 30 else ""))
    if args.dry_run:
        print("\n(--dry-run: no se escribió data/data.json)")


if __name__ == "__main__":
    main()
