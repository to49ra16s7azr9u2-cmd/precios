#!/usr/bin/env python3
"""Las tiendas que venden un solo rubro deciden la categoría de sus fichas.

POR QUÉ (26-sep-2026)
---------------------
Sephora sólo vende belleza, pero 16 de sus fichas estaban en otras
categorías por choques de palabras: «Moisture Surge 100H Auto-Replenishing
Hydrator» en Autos y motos (por «auto»), «Microfiber Hair Towel» en Blancos,
«Chanel Espejo Doble» en Decoración, «Shark Glossi (herramienta 2 en 1 para
secado)» en Herramientas. Cuando la ficha la vende SÓLO una tienda de un
rubro, el rubro de la tienda sabe más que cualquier palabra suelta.

Sólo se usa con tiendas de UN rubro, y sólo sobre fichas que vende únicamente
esa tienda. Mueve la categoría y deja la subcategoría vacía cuando la vieja
no existe en la nueva; completar_subcategorias.py la llena después.

USO
---
    python3 scripts/prior_tienda.py            # informe
    python3 scripts/prior_tienda.py --aplicar
"""
import argparse
import collections
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import load_catalog, save_catalog  # noqa: E402

MARCA_MIN = 200     # fichas de la marca en el catálogo
MARCA_SHARE = 0.97  # parte de ellas en Autopartes

RUBRO = {
    "sephora_mx": "Belleza y cuidado personal",
    "maskota": "Mascotas",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()
    data = load_catalog()
    subs = {c["id"]: {s["id"] for s in c.get("subcategories") or []} for c in data["categories"]}
    movidas = collections.Counter()
    for p in data["products"]:
        tiendas = {o.get("storeId") for o in p.get("offers") or []}
        if len(tiendas) != 1:
            continue
        rubro = RUBRO.get(next(iter(tiendas)))
        if not rubro or p.get("category") == rubro:
            continue
        movidas[(p.get("category"), rubro)] += 1
        if args.aplicar:
            p["category"] = rubro
            if p.get("subcategory") not in subs.get(rubro, ()):
                p["subcategory"] = None
    # Marcas de refacciones (26-sep-2026): Hushan, SYD, Moog, Tong Yang,
    # K-Nadian, Rodatech... venden sólo piezas de auto (>= 97% de sus fichas
    # en Autopartes), pero 600+ de sus fichas estaban en Herramientas,
    # Cocina, Componentes de PC, Joyería o Climatización por una palabra
    # («Manija», «Plato amortiguador», «Anillo retención», «Tubo de
    # enfriamiento»). La marca manda.
    import re
    import unicodedata
    import reglas_nuevas

    def _t(x):
        return unicodedata.normalize("NFKD", (x or "").lower()).encode("ascii", "ignore").decode()
    marca_cat = collections.defaultdict(collections.Counter)
    for p in data["products"]:
        b = _t(p.get("brand")).strip()
        if b:
            marca_cat[b][p.get("category")] += 1
    refaccioneras = {b for b, c in marca_cat.items()
                     if sum(c.values()) >= MARCA_MIN and c["Autopartes"] / sum(c.values()) >= MARCA_SHARE}
    for p in data["products"]:
        b = _t(p.get("brand")).strip()
        if b not in refaccioneras or p.get("category") in ("Autopartes", "Autos y motos"):
            continue
        movidas[(p.get("category"), "Autopartes (marca de refacciones)")] += 1
        if args.aplicar:
            p["category"] = "Autopartes"
            sub = reglas_nuevas.sub_autoparte(re.sub(r"\s+", " ", _t(p.get("name"))))
            p["subcategory"] = sub if sub in subs.get("Autopartes", ()) else "Para autos"
    for (a, b), n in movidas.most_common():
        print(f"  {n:4}  {a} -> {b}")
    print(f"fichas de tiendas de un rubro fuera de su rubro: {sum(movidas.values())}")
    if args.aplicar and movidas:
        save_catalog(data)
        print("Guardado.")


if __name__ == "__main__":
    main()
