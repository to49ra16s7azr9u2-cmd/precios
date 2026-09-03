#!/usr/bin/env python3
"""Fusiona los productos "combo" (celular + audífonos/smartwatch/bocina de
regalo) con la ficha del mismo celular SIN el combo, en vez de dejarlos
como dos productos de catálogo separados -- a pedido explícito del
usuario tras ver que el mismo Moto G67 aparecía dos veces (una ficha
"pelada" y otra idéntica con "...con Smartwatch y Audífonos").

CÓMO SE DETECTA EL COMBO
------------------------
El nombre del producto trae la marca del regalo pegada al final del
nombre real del equipo: "...con Smartwatch y Audífonos", "...+ Audífonos
213 De Regalo", "...con Audífonos y Bocina". BUNDLE_RE reconoce esas
formas.

CÓMO SE EMPAREJA CON EL PRODUCTO "PELADO"
------------------------------------------
Mismo criterio conservador que match_amazon_capture.py (mismas funciones,
reusadas tal cual): marca, línea/número de modelo (model_of para
Samsung/Xiaomi/Motorola/Huawei/OPPO/realme, generation_of+variant_of para
iPhone), capacidad y color tienen que coincidir EXACTO contra un único
candidato en la categoría Celulares que no sea a su vez un combo. Si hay
cero candidatos o más de uno (p. ej. el nombre del combo no dice el color
y hay varios colores posibles), se deja sin tocar y se lista para
revisión manual -- nunca se adivina.

QUÉ HACE CON LAS OFERTAS
-------------------------
Cada oferta del producto-combo se mueve al producto pelado, marcada con
`bundleNote` (lo que trae de regalo, sacado del propio nombre del combo)
para que se muestre junto al precio en vez de perderse. El producto-combo
queda sin ofertas y se elimina del catálogo.

USO
---
    python3 scripts/merge_bundle_offers.py --dry-run
    python3 scripts/merge_bundle_offers.py
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog  # noqa: E402
from match_amazon_capture import (  # noqa: E402
    BRAND_WORDS, capacities, color_of, generation_of, model_of, variant_of,
    words,
)

BUNDLE_RE = re.compile(
    r"\s*(?:con\s+(?:smartwatch\s+y\s+)?audíf|con\s+audif|"
    r"\+\s*audíf|\+\s*audif).*$",
    re.IGNORECASE,
)
# BUNDLE_RE (arriba) exige un conector ("con "/"+ ") justo antes de
# "audífonos" para poder CORTAR el nombre ahí y sacar la nota -- pero un
# candidato a "pelado" tiene que estar libre de CUALQUIER mención de regalo,
# tenga o no ese conector. Sin este chequeo aparte, "Samsung Galaxy A03 ...
# Azul Audifonos y Bocina" (sin "con"/"+") se colaba como si fuera el
# producto pelado -- y en los hechos es OTRO combo, con OTRO regalo
# (bocina en vez de smartwatch), no el mismo equipo sin nada.
ANY_GIFT_HINT_RE = re.compile(r"\baudíf|\baudif|\bsmartwatch\b|\bbocina\b", re.IGNORECASE)


def bundle_note(name):
    m = BUNDLE_RE.search(name)
    if not m:
        return None
    extra = m.group(0).strip()
    extra = re.sub(r"^\+?\s*", "", extra)
    extra = re.sub(r"^con\s+", "", extra, flags=re.IGNORECASE)
    extra = re.sub(r"\s*de regalo\s*$", "", extra, flags=re.IGNORECASE)
    extra = re.sub(r"\s+", " ", extra).strip()
    return f"Incluye {extra[0].lower()}{extra[1:]}" if extra else None


def matches(bundle, other, tw, tg, tv, tc, tcol, tm):
    if other["id"] == bundle["id"] or ANY_GIFT_HINT_RE.search(other["name"]):
        return False
    pw = words(other["name"])
    if not (tw & pw):
        return False
    if tw & BRAND_WORDS and not ((tw & BRAND_WORDS) & pw):
        return False
    pg = generation_of(other["name"])
    if tg and pg and tg != pg:
        return False
    pv = variant_of(other["name"])
    if tv != pv:
        return False
    pc = capacities(other["name"])
    if tc and pc and not (tc & pc):
        return False
    if tc and not pc:
        return False
    pcol = color_of(other["name"])
    if tcol and pcol and tcol != pcol:
        return False
    if tcol and not pcol:
        return False
    pm = model_of(other["name"])
    if tm and pm and tm != pm:
        return False
    if tm and not pm:
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = load_catalog()
    products = data["products"]
    by_cat = {}
    for p in products:
        by_cat.setdefault(p.get("category"), []).append(p)

    merged, unresolved = 0, []
    drop_ids = set()
    for bundle in products:
        if bundle.get("category") != "Celulares" or not BUNDLE_RE.search(bundle["name"]):
            continue
        note = bundle_note(bundle["name"])
        if not note:
            continue
        tw = words(bundle["name"])
        tg = generation_of(bundle["name"])
        tv = variant_of(bundle["name"])
        tc = capacities(bundle["name"])
        tcol = color_of(bundle["name"])
        tm = model_of(bundle["name"])

        candidates = [
            p for p in by_cat.get("Celulares", [])
            if matches(bundle, p, tw, tg, tv, tc, tcol, tm)
        ]
        if len(candidates) != 1:
            unresolved.append((bundle, candidates))
            continue

        target = candidates[0]
        existing_urls = {o.get("url") for o in target.setdefault("offers", [])}
        for o in bundle.get("offers") or []:
            if o.get("url") in existing_urls:
                continue
            o = dict(o)
            o["bundleNote"] = note
            target["offers"].append(o)
        drop_ids.add(bundle["id"])
        merged += 1
        print(f"  {bundle['id']} -> {target['id']}  ({note})")
        print(f"      combo: {bundle['name'][:70]}")
        print(f"      pelado: {target['name'][:70]}")

    print(f"\nFusionados: {merged}")
    if unresolved:
        print(f"\nSin candidato único, revisar a mano ({len(unresolved)}):")
        for bundle, candidates in unresolved:
            print(f"  {bundle['id']}  {bundle['name'][:70]}")
            for c in candidates[:5]:
                print(f"        candidato: {c['id']}  {c['name'][:65]}")
            if not candidates:
                print("        (ningún candidato en Celulares)")

    if args.dry_run:
        print("\n(--dry-run: no se escribió nada)")
        return
    if not merged:
        return

    data["products"] = [p for p in products if p["id"] not in drop_ids]
    save_catalog(data)
    print(f"\nCatálogo actualizado: {len(data['products'])} productos ({len(drop_ids)} combos eliminados, fusionados en su producto pelado).")


if __name__ == "__main__":
    main()
