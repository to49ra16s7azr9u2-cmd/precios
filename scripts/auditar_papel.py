#!/usr/bin/env python3
"""Busca la ficha que está en una subcategoría de PRODUCTO pero es un accesorio.

CÓMO LAS ENCUENTRA
------------------
Por cómo ARRANCA el nombre. Un producto se nombra por lo que es ("Taladro
Truper de 1/2"); un accesorio se nombra por lo que es y para qué va ("Cable
para micrófono de 6 m", "Filtro de ósmosis inversa Hydrofast"). Cuando una
ficha abre diciendo "cable", "filtro", "funda" o "repuesto" y está en una
subcategoría cuyo papel es "producto" (ver roles_subcategorias.py), casi
siempre está mal puesta.

EL DESCARTE QUE HACE QUE SIRVA
------------------------------
Que la categoría o la subcategoría NO se llamen ya así. Un cargador dentro
de "Cargadores y adaptadores" abre diciendo "cargador" y está en su casa;
una manguera de freno dentro de Refacciones también. Sin ese descarte la
auditoría devolvía 11,006 fichas y casi todas eran correctas; con él,
4,319, y la mayoría son errores de verdad.

USO
---
    python3 scripts/auditar_papel.py                # las 40 peores
    python3 scripts/auditar_papel.py --todas        # el listado completo
    python3 scripts/auditar_papel.py --categoria Audífonos
"""
import argparse
import collections
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog  # noqa: E402
from roles_subcategorias import es_producto  # noqa: E402

CABEZA = re.compile(
    r"^(?:\W*)(?:kit de |juego de |set de |paquete de |pack de )?"
    r"(cable|cables|funda|fundas|carcasa|estuche|mica|micas|protector|protectores|"
    r"soporte|soportes|adaptador|adaptadores|repuesto|repuestos|"
    r"refaccion|refacciones|filtro|filtros|correa|correas|"
    r"bolsa|bolsas|mochila|candado|candados|almohadilla|almohadillas|"
    r"tornillo|tornillos|pila|pilas|cargador|cargadores|"
    r"control remoto|bombilla|manija|perilla|"
    r"aspa|aspas|rodamiento|balero|empaque|junta|manguera|"
    r"tapa|tapas|pedestal|tripie|tripode)\b")

# La categoría cuyo papel ES la parte: acá una manguera de freno está bien.
CATEGORIAS_DE_PARTES = {"Refacciones"}


def T(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def _raiz(w):
    return w[:-2] if w.endswith("es") else (w[:-1] if w.endswith("s") else w)


def sospechosas(products, categoria=None):
    """{(categoría, subcategoría): [(palabra, producto)]}"""
    hall = collections.defaultdict(list)
    for p in products:
        cat, sub = p.get("category"), p.get("subcategory")
        if not sub or cat in CATEGORIAS_DE_PARTES:
            continue
        if categoria and cat != categoria:
            continue
        if not es_producto(cat, sub):
            continue
        m = CABEZA.match(T(p["name"]))
        if not m:
            continue
        w = _raiz(m.group(1))
        if w in T(cat) or w in T(sub):
            continue
        hall[(cat, sub)].append((w, p))
    return hall


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--categoria")
    ap.add_argument("--todas", action="store_true")
    ap.add_argument("--muestras", type=int, default=3)
    args = ap.parse_args()

    d = load_catalog()
    hall = sospechosas(d["products"], args.categoria)
    total = sum(len(v) for v in hall.values())
    print(f"sospechosas: {total:,} en {len(hall)} subcategorías\n")
    orden = sorted(hall.items(), key=lambda kv: -len(kv[1]))
    for k, ps in (orden if args.todas else orden[:40]):
        print(f"### {len(ps):>4}  {k[0]} / {k[1]}")
        for w, p in ps[:args.muestras]:
            print(f"        [{w}] {p['name'][:66]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
