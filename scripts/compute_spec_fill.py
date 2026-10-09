#!/usr/bin/env python3
"""Marca las fichas con muy pocos datos técnicos (menos del 20% de lo que
suele decir una ficha de su subcategoría) para avisarlo en la lista y en la
página del producto.

POR QUÉ
-------
Una ficha con precio pero sin RAM, procesador ni almacenamiento (una PC, una
laptop) no se puede comparar: quien lee la lista cree que «Desde $2,899» es
equivalente a la de al lado. Que falte el dato en TODAS las tiendas que la
venden es una información útil por sí sola, y hoy el sitio no la da.

QUÉ ES «LO QUE SUELE DECIR»
---------------------------
Se mide contra el propio catálogo, no contra una lista escrita a mano: en
cada subcategoría, los campos de `facets` que traen al menos el 30% de sus
fichas (con un mínimo de 30 fichas y 3 campos) son los que se esperan. La
ficha se llena con:

  - esos campos de `facets` (que ya juntan lo que dicen el nombre y las
    especificaciones de CUALQUIERA de las tiendas), y
  - las especificaciones propias (`specs`), contadas aparte para las que no
    son un campo con filtro: 6 o más con contenido cuentan como lleno.

El porcentaje es el mayor de los dos. Menos de 20% -> `sparse: true` en la
ficha (y el campo se quita cuando deja de cumplirse). Las subcategorías sin
campos esperados (cuadros, libros, ropa) no se marcan: no hay con qué medir.

USO
---
    python3 scripts/compute_spec_fill.py --dry-run
    python3 scripts/compute_spec_fill.py
"""
import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog  # noqa: E402

PREVALENCIA = 0.30
MIN_FICHAS = 30
MIN_CAMPOS = 3
UMBRAL = 0.20
SPECS_LLENO = 6
# Etiquetas que no describen el producto (identificadores y rellenos).
SIN_VALOR = {"modelo", "marca", "sku", "fraud check", "numero de modelo", "número de modelo", "ean", "gtin",
             "codigo", "código", "referencia", "id", "garantia", "garantía", "origen", "pais de origen",
             "país de origen", "condicion", "condición", "vendedor", "tienda"}


def specs_utiles(p):
    n = 0
    for s in p.get("specs") or []:
        lbl = (s.get("label") or "").strip().lower()
        val = str(s.get("value") or "").strip()
        if lbl and val and lbl not in SIN_VALOR and val.lower() not in ("n/a", "na", "-", "no aplica", "ninguno"):
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    data = load_catalog()
    prods = data["products"]

    por_sub = collections.defaultdict(list)
    for p in prods:
        por_sub[(p.get("category"), p.get("subcategory"))].append(p)

    esperados = {}
    for clave, ps in por_sub.items():
        if len(ps) < MIN_FICHAS:
            continue
        cuenta = collections.Counter()
        for p in ps:
            for k, v in (p.get("facets") or {}).items():
                if v not in (None, "", []):
                    cuenta[k] += 1
        campos = {k for k, n in cuenta.items() if n / len(ps) >= PREVALENCIA}
        if len(campos) >= MIN_CAMPOS:
            esperados[clave] = campos

    marcadas = quitadas = medidas = 0
    por_cat = collections.Counter()
    hist = collections.Counter()
    for p in prods:
        campos = esperados.get((p.get("category"), p.get("subcategory")))
        if not campos:
            if p.pop("sparse", None):
                quitadas += 1
            continue
        medidas += 1
        f = p.get("facets") or {}
        llenos = sum(1 for k in campos if f.get(k) not in (None, "", []))
        fill = max(llenos / len(campos), min(1.0, specs_utiles(p) / SPECS_LLENO))
        hist[int(fill * 5) * 20] += 1
        if fill < UMBRAL:
            if not p.get("sparse"):
                marcadas += 1
            p["sparse"] = True
            por_cat[p.get("category")] += 1
        elif p.pop("sparse", None):
            quitadas += 1

    print(f"Subcategorías con campos esperados: {len(esperados)} de {len(por_sub)}")
    print(f"Fichas medidas: {medidas:,} de {len(prods):,}")
    print("Reparto de la tasa de llenado (%):", dict(sorted(hist.items())))
    total = sum(por_cat.values())
    print(f"Con pocos datos (< {UMBRAL:.0%}): {total:,} ({total / max(medidas, 1):.1%} de las medidas)")
    for c, n in por_cat.most_common(15):
        print(f"  {n:7,}  {c}")
    print(f"Nuevas marcas: {marcadas:,}   quitadas: {quitadas:,}")
    if args.dry_run:
        print("(--dry-run: no se guardó nada)")
        return
    save_catalog(data)
    print("Catálogo guardado.")


if __name__ == "__main__":
    main()
