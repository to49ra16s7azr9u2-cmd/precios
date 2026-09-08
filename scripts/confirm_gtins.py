#!/usr/bin/env python3
"""Marca en cada producto el GTIN que Mercado Libre CONFIRMA, en product["gtin"].

Para qué: las páginas SEO pueden declarar `gtin13` en el JSON-LD de Product,
que es la señal más fuerte que tiene Google para saber que dos páginas hablan
del MISMO artículo (y la que habilita el bloque de comparación de precios).
Pero declarar un código equivocado es peor que no declarar ninguno: Google
fusionaría nuestra ficha con otro producto.

Por qué no basta el `ean` que ya tenemos: es el código que publica la API de
Elektra, y en datos reales muchos son consecutivos internos de la tienda, no
códigos de fabricante (un iPhone 17 Pro con 0400064180616). El dígito de
control NO sirve para separarlos: se comprobó sobre el catálogo entero y el
100% de los `ean` lo pasa, los internos incluidos.

Así que la única confirmación honesta es preguntar: se consulta /by-gtin y
solo se guarda el código si Mercado Libre devuelve UN producto de catálogo
cuyo campo gtin incluye ese mismo código. Si no responde, si no encuentra
nada, o si hay más de un resultado, no se guarda nada -- no se adivina.

Se consultan solo los productos que YA tienen una oferta de Mercado Libre
junto a la de Elektra (son los que el cruce por GTIN unió en su día): el
resto ya se sabe que no coincide con nada, y volver a preguntar por ellos
serían ~48 mil peticiones para nada.

USO
    python3 scripts/confirm_gtins.py --dry-run --limit 50
    python3 scripts/confirm_gtins.py
"""
import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog
from match_by_gtin import BY_GTIN, get_json, normalize_gtin

# El JSON-LD de schema.org nombra la propiedad según el largo del código.
POR_LARGO = {8: "gtin8", 12: "gtin12", 13: "gtin13", 14: "gtin14"}


def gtins_de(product):
    """Códigos normalizados que publica alguna oferta de este producto."""
    vistos = []
    for o in product.get("offers") or []:
        g = normalize_gtin(o.get("ean"))
        if g and g not in vistos:
            vistos.append(g)
    return vistos


def candidatos(products):
    for p in products:
        if p.get("gtin"):
            continue
        tiendas = {o.get("storeId") for o in (p.get("offers") or [])}
        if "mercadolibre" not in tiendas:
            continue
        for g in gtins_de(p):
            yield p, g
            break


def confirmar(gtin):
    """True si Mercado Libre devuelve UN producto cuyo gtin incluye este."""
    res = get_json(f"{BY_GTIN}?gtin={gtin}")
    if res is None:
        return None  # sin respuesta: se reintenta en otra corrida
    results = res.get("results") or []
    if len(results) != 1:
        return False
    publicados = {normalize_gtin(x) for x in str(results[0].get("gtin") or "").split(",")}
    publicados.discard(None)
    return gtin in publicados


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--concurrency", type=int, default=4)
    args = ap.parse_args()

    data = load_catalog()
    todo = list(candidatos(data["products"]))
    if args.limit:
        todo = todo[:args.limit]
    print(f"Por consultar: {len(todo):,} productos")

    stats = {"confirmados": 0, "no_confirma": 0, "sin_respuesta": 0}
    lock = Lock()
    t0 = time.time()

    def work(item):
        p, g = item
        ok = confirmar(g)
        with lock:
            if ok is None:
                stats["sin_respuesta"] += 1
            elif ok:
                p["gtin"] = g
                stats["confirmados"] += 1
            else:
                stats["no_confirma"] += 1
            hechos = sum(stats.values())
            if hechos % 500 == 0:
                v = hechos / max(1, time.time() - t0)
                falta = (len(todo) - hechos) / max(v, 0.01) / 60
                print(f"  {hechos:,}/{len(todo):,}  confirmados={stats['confirmados']:,}"
                      f"  ({v:.1f}/s, faltan ~{falta:.0f} min)", flush=True)

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        list(pool.map(work, todo))

    print("=== Resumen ===")
    for k, v in stats.items():
        print(f"  {k}: {v:,}")

    if args.dry_run:
        print("(--dry-run: no se escribió nada)")
        return
    save_catalog(data)
    print("Guardado.")


if __name__ == "__main__":
    main()
