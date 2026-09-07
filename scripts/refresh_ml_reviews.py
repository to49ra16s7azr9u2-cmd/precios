#!/usr/bin/env python3
"""Trae la calificación y la reseña más votada de Mercado Libre.

POR QUÉ
-------
El sitio compara precios pero no dice nada sobre si el producto es bueno.
El filtro de "Calificación" y el orden "Mejor calificados" existen en la
interfaz desde hace tiempo y NUNCA tuvieron datos: hoy hay 0 ofertas con
rating en todo el catálogo.

De las tres tiendas grandes, Mercado Libre es la única que publica
reseñas: Amazon no tiene API abierta y Elektra devuelve 404 en su API de
reseñas (probado). Así que esto llena la calificación de las ofertas de
Mercado Libre y deja las demás como están -- que es lo honesto: la
estrella que se muestra es la de ESA tienda, no un promedio inventado
entre tiendas que no publican nada.

DÓNDE SE GUARDA
---------------
En la OFERTA, no en el producto:

    offer.rating       promedio que publica Mercado Libre (ej. 4.8)
    offer.reviewCount  cuántas reseñas lo sostienen
    offer.topReview    la reseña con más "me gusta"

Es la forma que ya espera la interfaz: aggregateRating() en js/app.js
pondera offer.rating por offer.reviewCount, así que un producto con dos
tiendas que califican promedia bien solo, y uno sin datos sigue sin
estrellas en vez de aparecer con cero.

EL ID QUE PIDE LA API NO ES EL QUE GUARDAMOS
--------------------------------------------
/reviews quiere el id de una PUBLICACIÓN (sellers[].itemId); con el id de
producto de catálogo -- el que va en la url de la oferta -- responde 404.
Las reseñas igual son del producto: dos publicaciones del mismo producto
devuelven las mismas. Por eso alcanza con el itemId de cualquier vendedor.

Las ofertas sin ningún itemId guardado se saltan y se informan: pedir el
detalle para conseguirlo sería duplicar las peticiones, y se puede hacer
después con refresh_prices.py, que ya baja vendedores.

USO
---
    python3 scripts/refresh_ml_reviews.py --dry-run --limit 50
    python3 scripts/refresh_ml_reviews.py --limit 1000
    python3 scripts/refresh_ml_reviews.py
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog  # noqa: E402

REVIEWS = "https://comparamx-mercadolibre-proxy.comparamx.workers.dev/reviews"

# El texto de la reseña se recorta: se muestra como cita en la ficha, no
# como un artículo, y sin tope una sola reseña puede traer 2,000 caracteres
# que hay que descargar en la shard de la categoría.
MAX_CONTENT = 400


def _get_curl(url):
    """Salida para entornos detrás de un proxy que rechaza a urllib (ver la
    misma nota en match_by_gtin.py: acá urllib recibe 403 y curl pasa)."""
    try:
        out = subprocess.run(["curl", "-s", "--max-time", "30", url],
                             capture_output=True, text=True, timeout=40)
        return json.loads(out.stdout) if out.stdout.strip() else None
    except Exception:
        return None


def get_json(url, retries=2):
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 403:
                got = _get_curl(url)
                if got is not None:
                    return got
            if e.code in (400, 404):
                return None
            if attempt == retries:
                return None
            time.sleep(1.5 * (attempt + 1))
        except Exception:
            if attempt == retries:
                return _get_curl(url)
            time.sleep(1.5 * (attempt + 1))
    return None


# Cuántas publicaciones distintas del mismo producto se prueban antes de
# darlo por "sin reseñas". Hace falta porque NO todas responden lo mismo:
# del iPhone 17 Pro Max (256 GB) plata, la primera publicación devuelve 0
# reseñas y las otras cuatro devuelven 18 con promedio 4.3. Quedarse con la
# primera perdía la calificación de miles de productos.
MAX_ITEMS_POR_OFERTA = 4


def _ofertas_de(product):
    """Todas las ofertas del producto, incluidas las que viven dentro de una
    variante de color del formato nuevo (merge_by_color.py). Sin esto, las
    reseñas de las fichas fusionadas por color no se consultaban nunca: su
    oferta de Mercado Libre no está en product["offers"] sino adentro de la
    variante."""
    out = list(product.get("offers") or [])
    for v in product.get("colorVariants") or []:
        if "offers" in v:
            out += list(v.get("offers") or [])
    return out


def ml_offers_with_items(products, skip_existing=False):
    """(producto, oferta, [itemIds]) de cada oferta de Mercado Libre que
    tenga con qué consultar las reseñas."""
    out, sin_item = [], 0
    for p in products:
        for o in _ofertas_de(p):
            if o.get("storeId") != "mercadolibre":
                continue
            # Reanudar sin repetir: una corrida cortada a la mitad se
            # continúa sin volver a pedir lo que ya trajo respuesta.
            if skip_existing and o.get("reviewCount") is not None:
                continue
            items = []
            for s in o.get("sellers") or []:
                it = s.get("itemId")
                if it and it not in items:
                    items.append(it)
            if items:
                out.append((p, o, items[:MAX_ITEMS_POR_OFERTA]))
            else:
                sin_item += 1
    return out, sin_item


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--concurrency", type=int, default=5)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-existing", action="store_true",
                    help="saltar las ofertas que ya tienen reviewCount")
    ap.add_argument("--save-every", type=int, default=2000,
                    help="guardar cada N ofertas consultadas (0 = solo al final)")
    args = ap.parse_args()

    data = load_catalog()
    todo, sin_item = ml_offers_with_items(data["products"], args.skip_existing)
    print(f"Ofertas de Mercado Libre con itemId: {len(todo)}")
    print(f"Ofertas de Mercado Libre SIN itemId (se saltan): {sin_item}")
    todo = todo[args.offset:]
    if args.limit:
        todo = todo[: args.limit]
    if not todo:
        print("Nada que consultar.")
        return
    print(f"A consultar en esta tanda: {len(todo)}\n")

    stats = {"consultados": 0, "con_reseñas": 0, "sin_reseñas": 0,
             "sin_promedio": 0, "sin_respuesta": 0}
    lock = Lock()
    ejemplos = []

    t0 = time.time()

    def work(item):
        product, offer, item_ids = item
        # Se prueban varias publicaciones del mismo producto y se corta en
        # la primera que traiga reseñas (ver MAX_ITEMS_POR_OFERTA).
        res = None
        for iid in item_ids:
            r = get_json(f"{REVIEWS}?id={iid}")
            if r and not r.get("error"):
                res = r
                if r.get("total"):
                    break
        with lock:
            stats["consultados"] += 1
            n = stats["consultados"]
            if n % 250 == 0:
                hechas = n / max(1e-9, time.time() - t0)
                faltan = (len(todo) - n) / hechas / 60 if hechas else 0
                print(f"  {n}/{len(todo)} ({100*n//len(todo)}%) · "
                      f"{stats['con_reseñas']} con reseñas · {hechas:.1f}/s · "
                      f"faltan ~{faltan:.0f} min", flush=True)
            if args.save_every and not args.dry_run and n % args.save_every == 0:
                save_catalog(data)
                print(f"  [guardado parcial en {n}]", flush=True)
            if not res:
                stats["sin_respuesta"] += 1
                return
            total = res.get("total") or 0
            avg = res.get("average")
            if not total:
                stats["sin_reseñas"] += 1
                return
            # Sin promedio publicado no se inventa uno con la página que
            # bajamos: se guarda el conteo y la reseña destacada, y el
            # producto simplemente no muestra estrellas.
            if avg is None:
                stats["sin_promedio"] += 1
            else:
                offer["rating"] = avg
            offer["reviewCount"] = total
            top = res.get("top")
            if top and top.get("content"):
                texto = top["content"].strip()
                if len(texto) > MAX_CONTENT:
                    texto = texto[:MAX_CONTENT].rsplit(" ", 1)[0] + "…"
                offer["topReview"] = {
                    "rate": top.get("rate"),
                    "title": (top.get("title") or "").strip() or None,
                    "content": texto,
                    "likes": top.get("likes") or 0,
                }
            stats["con_reseñas"] += 1
            if len(ejemplos) < 12:
                ejemplos.append((product["name"][:38], avg, total,
                                 (top or {}).get("likes"), ((top or {}).get("title") or "")[:26]))

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        list(pool.map(work, todo))

    print("=== Resumen ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    if ejemplos:
        print("\n  Ejemplos:")
        for name, avg, total, likes, title in ejemplos:
            print(f"   {str(avg):>4}★ {total:>7} reseñas  {name:38} top: {likes} me gusta · {title}")

    if args.dry_run:
        print("\n(--dry-run: no se guardó nada)")
        return
    if stats["con_reseñas"]:
        save_catalog(data)
        print(f"\nGuardado: {stats['con_reseñas']} ofertas con calificación de Mercado Libre.")
    else:
        print("\nNada que guardar.")


if __name__ == "__main__":
    main()
