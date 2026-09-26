#!/usr/bin/env python3
"""Fichas con un precio imposible para su subcategoría: dos jueces a la vez.

POR QUÉ (26-sep-2026)
---------------------
En una subcategoría de PRODUCTO, una ficha que cuesta menos del 8% de la
mediana casi nunca es ese producto: controles remotos entre los televisores
de 50" ($312 contra $7,409), controles de minisplit entre los minisplit,
pestillos y termómetros entre los refrigeradores, conjuntos de ropa entre
las sillas de comedor, bastones «plegables» entre los celulares plegables,
tintas entre las impresoras. Medido: 1,804 fichas así en subcategorías con
mediana de $800 o más.

El precio solo no alcanza para decidir a dónde va. Se usan dos jueces que
no se miran entre sí:
  1. los VECINOS (las 25 fichas más parecidas del catálogo entero, mismo
     criterio que vecinos_catalogo.py) votan una categoría/subcategoría
     distinta con al menos el 60%;
  2. el PRECIO cabe en el destino: está entre 1/4 y 4 veces la mediana de
     esa subcategoría.
Si los dos coinciden, se mueve. Si no, se deja y se lista.

USO
---
    python3 scripts/precio_atipico.py              # informe
    python3 scripts/precio_atipico.py --aplicar
"""
import argparse
import collections
import datetime
import json
import math
import os
import random
import statistics
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import load_catalog, save_catalog  # noqa: E402
from detectar_mal_clasificados import tokens  # noqa: E402
from roles_subcategorias import PRODUCTO, rol_de  # noqa: E402

FRACCION = 0.08      # por debajo de esto de la mediana, es sospechosa
MEDIANA_MIN = 800    # sólo subcategorías caras: en las baratas el 8% es ruido
MIN_FICHAS = 40
VECES_ACCESORIO = 12      # en una subcategoría de accesorio/parte, 12 veces la mediana
PRECIO_MIN_ACCESORIO = 3000
K = 25
MAX_DF = 3000
MIN_VOTO = 0.6


def precio(p):
    ps = [o.get("price") for o in p.get("offers") or [] if o.get("price")]
    return min(ps) if ps else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--muestras", type=int, default=40)
    args = ap.parse_args()
    data = load_catalog()
    prods = data["products"]

    por_sub = collections.defaultdict(list)
    for p in prods:
        x = precio(p)
        if x and p.get("subcategory"):
            por_sub[(p["category"], p["subcategory"])].append(x)
    mediana = {k: statistics.median(v) for k, v in por_sub.items() if len(v) >= 10}

    # Lo que una decisión a mano dejó donde está no se toca (candado).
    ruta_candado = os.path.join(os.path.dirname(AQUI), "data", "clasificacion-a-mano.json")
    candado = json.load(open(ruta_candado, encoding="utf-8")) if os.path.exists(ruta_candado) else {}
    sospechosas = []
    for p in prods:
        fijo = candado.get(p["id"])
        if fijo and fijo[0] == p.get("category") and (fijo[1] or None) == (p.get("subcategory") or None):
            continue
        k = (p.get("category"), p.get("subcategory"))
        x = precio(p)
        if not x or k not in mediana or len(por_sub[k]) < MIN_FICHAS:
            continue
        if rol_de(*k) == PRODUCTO:
            if mediana[k] >= MEDIANA_MIN and x < FRACCION * mediana[k]:
                sospechosas.append(p)
        # Al revés: el aparato entero metido entre sus accesorios («Aspiradora
        # ... con filtro HEPA» en Filtros, «Impresora 3D ... + filamento» en
        # Filamentos, Apple Watch en Correas). 501 fichas el 26-sep-2026.
        elif x > VECES_ACCESORIO * mediana[k] and x > PRECIO_MIN_ACCESORIO:
            sospechosas.append(p)
    print(f"sospechosas por precio: {len(sospechosas):,}")

    # Índice de palabras del catálogo entero (para los vecinos).
    idx = collections.defaultdict(list)
    df = collections.Counter()
    for i, p in enumerate(prods):
        for w in set(tokens(p.get("name") or "")):
            df[w] += 1
            idx[w].append(i)
    n = len(prods)
    pos = {p["id"]: i for i, p in enumerate(prods)}

    mover = []
    no = collections.Counter()
    for p in sospechosas:
        sc = collections.Counter()
        for w in set(tokens(p.get("name") or "")):
            d = df[w]
            if 0 < d <= MAX_DF:
                peso = math.log(n / d)
                for j in idx[w]:
                    if j != pos[p["id"]]:
                        sc[j] += peso
        top = sc.most_common(K)
        if len(top) < 8:
            no["pocos vecinos"] += 1
            continue
        votos = collections.Counter((prods[j]["category"], prods[j].get("subcategory")) for j, _ in top)
        (c2, s2), k = votos.most_common(1)[0]
        if (c2, s2) == (p["category"], p["subcategory"]) or not s2 or k / len(top) < MIN_VOTO:
            no["los vecinos no proponen otro lugar"] += 1
            continue
        m2 = mediana.get((c2, s2))
        x = precio(p)
        if not m2 or not (m2 / 4 <= x <= m2 * 4):
            no["el precio no cabe en el destino"] += 1
            continue
        mover.append((p, c2, s2))
    print(f"se mueven: {len(mover):,}")
    for k, v in no.most_common():
        print(f"  no se mueven: {v:6,}  {k}")
    grupos = collections.Counter((p["category"], p["subcategory"], c2, s2) for p, c2, s2 in mover)
    for k, v in grupos.most_common(25):
        print(f"  {v:4}  {k[0]} / {k[1]}  ->  {k[2]} / {k[3]}")
    random.seed(5)
    for p, c2, s2 in random.sample(mover, min(args.muestras, len(mover))):
        print(f"   ${precio(p):8,.0f}  {p['category']}/{p['subcategory']} -> {c2}/{s2} | {p['name'][:70]}")
    if args.aplicar and mover:
        for p, c2, s2 in mover:
            p["category"], p["subcategory"] = c2, s2
        save_catalog(data)
        # Bitácora, igual que aplicar_movimientos.py, para saber después qué movió esto.
        ruta_bit = os.path.join(os.path.dirname(AQUI), "data", "movimientos-aplicados.json")
        bit = json.load(open(ruta_bit, encoding="utf-8")) if os.path.exists(ruta_bit) else []
        bit.append({"fecha": datetime.date.today().isoformat(), "origen": "precio_atipico.py",
                    "motivo": "precio imposible para su subcategoría (vecinos + precio)",
                    "grupos": {f"{a} | {b} | {c} | {d}": n for (a, b, c, d), n in grupos.items()}})
        json.dump(bit, open(ruta_bit, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("Guardado.")


if __name__ == "__main__":
    main()
