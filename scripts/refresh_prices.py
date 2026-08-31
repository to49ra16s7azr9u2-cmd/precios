#!/usr/bin/env python3
"""Actualiza los precios guardados en data/data.json contra Mercado Libre.

POR QUÉ HACE FALTA
------------------
La ficha de producto refresca precios en vivo al abrirla (ver refreshLiveOffers
en js/app.js), pero el resto del sitio no: la portada, los rankings, las listas
por categoría y las ~11,762 páginas estáticas de SEO se pintan con lo que hay
guardado en data/data.json. Si eso queda viejo, el usuario ve un precio en la
lista, entra, y ve otro — que es justo lo que reportó (iPhone 17 256 GB: $15,896
guardado contra $18,485 reales).

Este script recorre el catálogo y pide a cada producto su precio vigente por su
id de catálogo (.../p/MLM…), que es exacto y barato (2 subpeticiones), en vez de
volver a buscarlo por texto.

REQUIERE el Worker con el endpoint /item?id= desplegado (backend/
mercadolibre-worker). Contra el Worker viejo todas las llamadas responden 400 y
el script no cambia nada (lo dice y termina).

USO
---
    python3 scripts/refresh_prices.py --dry-run --limit 50   # ver qué cambiaría
    python3 scripts/refresh_prices.py --limit 500            # aplicar por tandas
    python3 scripts/refresh_prices.py                        # catálogo completo

Es reanudable: --offset salta los primeros N productos, así se puede avanzar por
tandas sin repetir. Guarda en cada tanda (--save-every) para no perder el avance
si se interrumpe.
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "data", "data.json")
PROXY = "https://comparamx-mercadolibre-proxy.comparamx.workers.dev/item"

CATALOG_ID = re.compile(r"/p/(MLM\d+)")


def catalog_id(url):
    m = CATALOG_ID.search(url or "")
    return m.group(1) if m else None


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
    """(etiqueta, url, setter) por cada precio actualizable del producto."""
    out = []
    for i, o in enumerate(product.get("offers") or []):
        if catalog_id(o.get("url")):
            out.append((f"offer[{i}]", o))
    for i, v in enumerate(product.get("colorVariants") or []):
        if catalog_id(v.get("url")):
            out.append((f"variant[{i}]", v))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="máximo de productos a procesar (0 = todos)")
    ap.add_argument("--offset", type=int, default=0, help="saltar los primeros N productos")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--save-every", type=int, default=100, help="guardar cada N productos")
    ap.add_argument("--dry-run", action="store_true", help="no escribe data.json")
    args = ap.parse_args()

    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    products = data["products"][args.offset:]
    if args.limit:
        products = products[: args.limit]
    print(f"Productos a revisar: {len(products)} (offset {args.offset})")

    # Sonda única antes de empezar: si el Worker desplegado todavía no entiende
    # ?id=, no tiene sentido lanzar miles de llamadas que van a fallar todas.
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

    stats = {"revisados": 0, "actualizados": 0, "sin_cambio": 0, "sin_oferta": 0, "error": 0, "precios": 0}
    max_delta = []

    def work(product):
        changed = False
        for label, node in targets_of(product):
            res = fetch_by_id(catalog_id(node["url"]))
            if res is None:
                stats["error"] += 1
                continue
            if res.get("__http") == 404 or res.get("__http") == 400 or not res.get("price"):
                stats["sin_oferta"] += 1
                continue
            new_price = res["price"]
            old_price = node.get("price")
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
                print(f"  {i}/{len(products)} — {stats['precios']} precios actualizados", flush=True)
            if not args.dry_run and args.save_every and i % args.save_every == 0:
                with open(DATA_PATH, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

    if not args.dry_run:
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print("\n=== Resumen ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    max_delta.sort(reverse=True)
    if max_delta:
        print("\n  Mayores diferencias contra lo guardado:")
        for pct, pid, name, old, new in max_delta[:15]:
            print(f"   {pct*100:5.1f}%  {pid}  {name[:44]:44}  {old:>10,.2f} -> {new:>10,.2f}")
    if args.dry_run:
        print("\n(--dry-run: no se escribió data/data.json)")


if __name__ == "__main__":
    main()
