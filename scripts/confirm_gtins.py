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

REANUDABLE
La primera versión guardaba solo al final, después de ~100 minutos de
consultas. El proceso se murió a los 2,000 productos y se perdió todo. Ahora
cada tanda se anota en data/gtin-confirmados.json --tanto los códigos
confirmados como los que NO confirmaron, para no volver a preguntar por
ellos-- y ese archivo se vuelca al catálogo al terminar o con --apply. Una
corrida cortada a la mitad no pierde nada: la siguiente sigue donde quedó.

USO
    python3 scripts/confirm_gtins.py --dry-run --limit 50
    python3 scripts/confirm_gtins.py            # consulta lo que falte y aplica
    python3 scripts/confirm_gtins.py --apply     # solo vuelca lo ya consultado
"""
import argparse
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import cargar_checkpoint, guardar_checkpoint, load_catalog, save_catalog
from match_by_gtin import BY_GTIN, get_json, normalize_gtin

# El JSON-LD de schema.org nombra la propiedad según el largo del código.
POR_LARGO = {8: "gtin8", 12: "gtin12", 13: "gtin13", 14: "gtin14"}

CHECKPOINT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "gtin-confirmados.json",
)
# Cada cuántos resultados se vuelca el avance a disco. 200 son ~80 segundos
# de consultas: lo máximo que se pierde si el proceso se muere.
CADA = 200




def gtins_de(product):
    """Códigos normalizados que publica alguna oferta de este producto."""
    vistos = []
    for o in product.get("offers") or []:
        g = normalize_gtin(o.get("ean"))
        if g and g not in vistos:
            vistos.append(g)
    return vistos


def candidatos(products, ya_consultados):
    for p in products:
        if p.get("gtin") or p["id"] in ya_consultados:
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


def aplicar(data, estado):
    """Vuelca el checkpoint al catálogo. Devuelve cuántos productos cambiaron."""
    puestos = 0
    for p in data["products"]:
        g = estado.get(p["id"])
        if g and g != "-" and p.get("gtin") != g:
            p["gtin"] = g
            puestos += 1
    return puestos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true",
                    help="solo volcar al catálogo lo ya consultado, sin pedir nada")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--concurrency", type=int, default=4)
    args = ap.parse_args()

    data = load_catalog()
    estado = cargar_checkpoint(CHECKPOINT)
    print(f"Checkpoint: {len(estado):,} productos ya consultados "
          f"({sum(1 for v in estado.values() if v != '-'):,} con código confirmado)")

    if args.apply:
        n = aplicar(data, estado)
        print(f"Productos con gtin nuevo: {n:,}")
        if not args.dry_run and n:
            save_catalog(data)
            print("Guardado.")
        return

    todo = list(candidatos(data["products"], estado))
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
                # Sin respuesta NO se anota: la próxima corrida lo reintenta.
                stats["sin_respuesta"] += 1
            elif ok:
                estado[p["id"]] = g
                stats["confirmados"] += 1
            else:
                estado[p["id"]] = "-"   # consultado y no confirma
                stats["no_confirma"] += 1
            hechos = sum(stats.values())
            if hechos % CADA == 0 and not args.dry_run:
                guardar_checkpoint(CHECKPOINT, estado)
            if hechos % 500 == 0:
                v = hechos / max(1, time.time() - t0)
                falta = (len(todo) - hechos) / max(v, 0.01) / 60
                print(f"  {hechos:,}/{len(todo):,}  confirmados={stats['confirmados']:,}"
                      f"  ({v:.1f}/s, faltan ~{falta:.0f} min)", flush=True)

    try:
        with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
            list(pool.map(work, todo))
    finally:
        if not args.dry_run:
            guardar_checkpoint(CHECKPOINT, estado)

    print("=== Resumen ===")
    for k, v in stats.items():
        print(f"  {k}: {v:,}")

    if args.dry_run:
        print("(--dry-run: no se escribió nada)")
        return
    n = aplicar(data, estado)
    print(f"Productos con gtin nuevo: {n:,}")
    if n:
        save_catalog(data)
        print("Guardado.")


if __name__ == "__main__":
    main()
