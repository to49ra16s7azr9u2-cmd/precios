#!/usr/bin/env python3
"""Refresca precios de DelSol, Avera, Farmatodo y Reuse (los que entran por
tiendas_soicos_a_captura.py) volviendo a leer el catálogo abierto de cada
sitio y comparando por la url real de la oferta.

Mismas reglas que refresh_vtex.py:
  - lo que no aparece en el recorrido (agotado o retirado de la tienda) se
    DEJA como estaba: el sitio promete que nada se borra por agotarse;
  - si el recorrido ve menos de MIN_WALK_RATIO de las ofertas que el catálogo
    tiene de la tienda, algo salió mal en el sitio y no se escribe nada
    (sale con 2).

USO
---
    python3 scripts/refrescar_tiendas_soicos.py --store avera --dry-run
    python3 scripts/refrescar_tiendas_soicos.py --store farmatodo
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tiendas_soicos_a_captura as T  # noqa: E402
from data_io import load_catalog, save_catalog, url_real  # noqa: E402

MIN_WALK_RATIO = 0.5
RECORRIDOS = {
    "reuse_mx": lambda: T.shopify("reuse_mx"),
    "avera": lambda: T.shopify("avera"),
    "farmatodo": T.farmatodo,
    "delsol": T.delsol,
}


def ofertas_de(p, store):
    for o in p.get("offers") or []:
        if o.get("storeId") == store:
            yield o
    for v in p.get("colorVariants") or []:
        for o in v.get("offers") or []:
            if o.get("storeId") == store:
                yield o


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--store", required=True, choices=sorted(RECORRIDOS))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    items = RECORRIDOS[args.store]()
    live = {url_real(it["url"]) or it["url"]: it for it in items}
    print(f"Recorrido: {len(live)} productos con existencia en {args.store}")
    data = load_catalog()
    stats = {"revisados": 0, "precio": 0, "sin_cambio": 0, "no_visto": 0}
    deltas = []
    for p in data["products"]:
        for o in ofertas_de(p, args.store):
            url = url_real(o.get("url") or "") or o.get("url")
            if not url:
                continue
            stats["revisados"] += 1
            it = live.get(url)
            if it is None:
                stats["no_visto"] += 1
                continue
            old = o.get("price")
            if old is not None and abs(it["price"] - old) < 0.01:
                stats["sin_cambio"] += 1
            else:
                if old:
                    deltas.append((abs(it["price"] - old) / old, p["name"], old, it["price"]))
                o["price"] = it["price"]
                stats["precio"] += 1
            if it.get("listPrice") and it["listPrice"] > it["price"]:
                o["listPrice"] = it["listPrice"]
            else:
                o.pop("listPrice", None)
            o["stock"] = "in_stock"
    vistas = stats["revisados"] - stats["no_visto"]
    if stats["revisados"] and vistas / stats["revisados"] < MIN_WALK_RATIO:
        print(f"ABORTA: el recorrido cubrió {vistas}/{stats['revisados']} de las ofertas de {args.store} "
              f"(menos del {MIN_WALK_RATIO:.0%}). Eso apunta a un problema del sitio. No se escribió nada.",
              file=sys.stderr)
        sys.exit(2)
    print("\n=== Resumen ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    deltas.sort(reverse=True)
    for pct, name, old, new in deltas[:10]:
        print(f"  {pct:>6.0%}  {name[:60]:<60} ${old:,.2f} -> ${new:,.2f}")
    if args.dry_run:
        print("\n(--dry-run: no se escribió nada)")
        return
    save_catalog(data)
    print(f"\nCatálogo actualizado: {stats['precio']} precios")


if __name__ == "__main__":
    main()
