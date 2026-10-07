#!/usr/bin/env python3
"""Consigue el itemId de las ofertas de Mercado Libre que no lo tienen, para
poder pedirles la calificación.

POR QUÉ (07-oct-2026)
---------------------
/reviews sólo contesta con el id de una PUBLICACIÓN (sellers[].itemId), no con
el id de catálogo (.../p/MLM123) que es el que trae la url de la oferta.
42,595 ofertas de Mercado Libre vivían sin ningún itemId (sobre todo las que
entraron por búsqueda de catálogo), llevaban `reviewCount: 0` por omisión y
refresh_ml_reviews las saltaba como «ya revisadas» sin haberlas preguntado
nunca: 35 mil fichas que sólo vende Mercado Libre sin una estrella.

QUÉ HACE
--------
Para cada oferta de ML con url de catálogo y sin itemId pide /item?id=MLM… (que
ya devuelve sellers[].itemId) y guarda hasta 4 en `offer.itemIds`.
NO toca `offer.sellers` (la interfaz muestra esa lista de vendedores).
Quita el `reviewCount: 0` que no era una respuesta de ML, para que
refresh_ml_reviews la vea como pendiente. Las que no devuelven publicaciones
(catálogo muerto) se anotan con `itemIdsChecked` y no se vuelven a pedir en
30 días.

Prioridad: primero las fichas con 2 o más tiendas (la calificación de ML ahí
ayuda a elegir entre tiendas), luego el resto, por tandas diarias (--limit)
para no pasarse de la cuota de 100 mil/día del Worker.

USO
---
    python3 scripts/ml_itemids.py --dry-run --limit 50
    python3 scripts/ml_itemids.py --limit 8000
    python3 scripts/refresh_ml_reviews.py --skip-existing --limit 5000
"""
import argparse
import datetime
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog  # noqa: E402
from refresh_ml_reviews import _ofertas_de, get_json  # noqa: E402

ITEM = "https://comparamx-mercadolibre-proxy.comparamx.workers.dev/item"
CATALOGO = re.compile(r"/p/(MLM\d+)")
MAX_ITEMS = 4
DIAS_RECONSULTA = 30


def _reciente(o, hoy):
    d = o.get("itemIdsChecked")
    try:
        return bool(d) and (hoy - datetime.date.fromisoformat(d)).days < DIAS_RECONSULTA
    except ValueError:
        return False


def pendientes(products):
    """[(prioridad, producto, oferta, id de catálogo)]; 0 = ficha con 2+ tiendas."""
    hoy = datetime.date.today()
    out = []
    for p in products:
        tiendas = {o.get("storeId") for o in _ofertas_de(p)}
        for o in _ofertas_de(p):
            if o.get("storeId") != "mercadolibre" or o.get("itemIds") or _reciente(o, hoy):
                continue
            if any(s.get("itemId") for s in o.get("sellers") or []):
                continue
            if (o.get("reviewCount") or 0) > 0:
                continue
            m = CATALOGO.search(o.get("url") or "")
            if m:
                out.append((0 if len(tiendas) >= 2 else 1, p, o, m.group(1)))
    out.sort(key=lambda x: x[0])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--concurrency", type=int, default=5)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--save-every", type=int, default=2000)
    args = ap.parse_args()
    data = load_catalog()
    todo = pendientes(data["products"])
    print(f"Ofertas de Mercado Libre sin itemId por resolver: {len(todo):,} "
          f"(de fichas con 2+ tiendas: {sum(1 for t in todo if t[0] == 0):,})")
    if args.limit:
        todo = todo[:args.limit]
    if not todo:
        return 0
    lock = Lock()
    st = {"hechas": 0, "con_items": 0, "sin_items": 0, "sin_respuesta": 0}
    hoy = datetime.date.today().isoformat()
    t0 = time.time()

    def work(t):
        _, p, o, mid = t
        r = get_json(f"{ITEM}?id={mid}")
        with lock:
            st["hechas"] += 1
            n = st["hechas"]
            if n % 250 == 0:
                print(f"  {n}/{len(todo)} · {st['con_items']} con itemId · {n / max(1e-9, time.time() - t0):.1f}/s", flush=True)
            if args.save_every and not args.dry_run and n % args.save_every == 0:
                save_catalog(data)
                print(f"  [guardado parcial en {n}]", flush=True)
            if r is None or r.get("error"):
                st["sin_respuesta"] += 1       # no se anota: se reintenta mañana
                return
            ids = []
            for s in r.get("sellers") or []:
                it = s.get("itemId")
                if it and it not in ids:
                    ids.append(it)
            if not ids:
                st["sin_items"] += 1
                o["itemIdsChecked"] = hoy
                return
            st["con_items"] += 1
            o["itemIds"] = ids[:MAX_ITEMS]
            if o.get("reviewCount") == 0:
                o.pop("reviewCount")           # el 0 era un valor por omisión, no una respuesta

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        list(pool.map(work, todo))
    print("=== Resumen ===")
    for k, v in st.items():
        print(f"  {k}: {v}")
    if args.dry_run:
        print("(--dry-run: no se guardó nada)")
        return 0
    save_catalog(data)
    print("Guardado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
