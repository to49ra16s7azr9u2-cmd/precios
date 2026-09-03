#!/usr/bin/env python3
"""Registra en data.categories las subcategorías que ya usan productos reales
pero nunca se agregaron a la lista estática.

POR QUÉ
-------
Cada categorizador nuevo (los de add_elektra_products.py, sobre todo) puede
devolver una subcategoría inventada en el momento, y el producto se guarda con
ella sin más. Pero la lista de subcategorías que ve la interfaz NO se deduce de
los productos: sale de data.categories[].subcategories. Todo lo que no esté ahí
queda invisible en dos lugares:

  - el panel de Filtros no ofrece esa subcategoría como opción, aunque haya
    cientos de productos marcados con ella;
  - la miga de pan de la ficha salta de la categoría directo al nombre del
    producto (subcategoryById la busca en esa lista y devuelve null).

Cuando se detectó, había 40 subcategorías así, afectando a 14,880 productos.

Es idempotente: solo agrega lo que falte, así que conviene correrlo después de
cada importación.

USO
---
    python3 scripts/sync_subcategories.py --dry-run
    python3 scripts/sync_subcategories.py
"""
import argparse
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = load_catalog()
    cat_by_id = {c["id"]: c for c in data["categories"]}

    # Ícono más común entre los productos de cada (categoría, subcategoría)
    # huérfana, por si algún outlier trae uno raro.
    icon_votes = {}
    counts = Counter()
    for p in data["products"]:
        cat, sub = p.get("category"), p.get("subcategory")
        if not sub:
            continue
        c = cat_by_id.get(cat)
        if c and any(s["id"] == sub for s in (c.get("subcategories") or [])):
            continue
        counts[(cat, sub)] += 1
        icon_votes.setdefault((cat, sub), Counter())[p.get("image") or "box"] += 1

    added = 0
    for (cat, sub), n in sorted(counts.items(), key=lambda kv: -kv[1]):
        c = cat_by_id.get(cat)
        if not c:
            print(f"AVISO: la categoría '{cat}' no está declarada (subcategoría "
                  f"'{sub}', {n} productos) -- se omite: hay que agregar la categoría misma")
            continue
        icon = icon_votes[(cat, sub)].most_common(1)[0][0]
        c.setdefault("subcategories", []).append({"id": sub, "name": sub, "icon": icon})
        print(f"  + [{cat}] {sub}  (icono={icon}, {n} productos)")
        added += 1

    print(f"\nSubcategorías agregadas: {added}")
    if args.dry_run:
        print("(--dry-run: no se escribió nada)")
        return
    if added:
        save_catalog(data)
        print("data.json actualizado.")


if __name__ == "__main__":
    main()
