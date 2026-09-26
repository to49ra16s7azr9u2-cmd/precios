#!/usr/bin/env python3
"""Rellena la subcategoría de las fichas que no tienen, con sus vecinos.

POR QUÉ (26-sep-2026)
---------------------
Después de las reglas y del repartidor de cada categoría
(repartir_sin_subcategoria.py) quedaban ~1,800 fichas sin subcategoría: el
repartidor no se decide o la categoría no tiene repartidor (Autos y motos,
Juguetes, Libros...). Casi todas entran por feeds cuya taxonomía da la
categoría pero no el tipo de producto (Walmart por Soicos: 3.3% de sus
fichas sin subcategoría, contra 0.04% de Mercado Libre, que trae dominio).
Una ficha sin subcategoría no aparece en ninguna lista de tipo ni en sus
rankings: en la práctica, no existe para quien navega.

CÓMO
----
Las 25 fichas más parecidas de la MISMA categoría (palabras poco comunes en
común, pesadas por lo raras que son; mismo criterio que vecinos_catalogo.py)
votan su subcategoría. Se asigna sólo si al menos 5 votan y el 60% coincide.

Y sólo en las categorías donde eso acierta: antes de asignar nada, se mide
en cada categoría escondiendo la subcategoría de 300 fichas que ya la tienen
y viendo si los vecinos la adivinan. Medido el 26-sep-2026: 88-98% en casi
todas, 82% en Libros. Se exige PRECISION_MIN; la categoría que no llega se
deja como está y se lista.

Nunca cambia una subcategoría puesta: sólo llena las vacías.

USO
---
    python3 scripts/completar_subcategorias.py            # informe
    python3 scripts/completar_subcategorias.py --aplicar
"""
import argparse
import collections
import math
import os
import random
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import load_catalog, save_catalog  # noqa: E402
from detectar_mal_clasificados import tokens  # noqa: E402

K = 25
MAX_DF = 4000
MIN_VOTO = 0.6
MIN_VOTOS = 5
PRECISION_MIN = 0.85
MUESTRA = 300


class Indice:
    def __init__(self, ref):
        self.ref = ref
        self.toks = [set(tokens(p.get("name") or "")) for p in ref]
        self.idx = collections.defaultdict(list)
        self.df = collections.Counter()
        for i, t in enumerate(self.toks):
            for w in t:
                self.df[w] += 1
                self.idx[w].append(i)
        self.n = len(ref)

    def votar(self, t, excluir=None):
        sc = collections.Counter()
        for w in t:
            d = self.df[w]
            if 0 < d <= MAX_DF:
                peso = math.log(self.n / d)
                for j in self.idx[w]:
                    if j != excluir:
                        sc[j] += peso
        top = sc.most_common(K)
        if len(top) < MIN_VOTOS:
            return None
        votos = collections.Counter(self.ref[j]["subcategory"] for j, _ in top)
        sub, n = votos.most_common(1)[0]
        return sub if n >= MIN_VOTOS and n / len(top) >= MIN_VOTO else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()
    data = load_catalog()
    por_cat = collections.defaultdict(list)
    for p in data["products"]:
        por_cat[p["category"]].append(p)
    random.seed(0)
    total = asignadas = 0
    fuera = []
    for cat, lista in sorted(por_cat.items()):
        vacias = [p for p in lista if not p.get("subcategory")]
        if not vacias:
            continue
        total += len(vacias)
        ref = [p for p in lista if p.get("subcategory")]
        if len(ref) < 200:
            fuera.append((cat, len(vacias), "pocas fichas de referencia"))
            continue
        ix = Indice(ref)
        ok = dec = 0
        for i in random.sample(range(len(ref)), min(MUESTRA, len(ref))):
            s = ix.votar(ix.toks[i], excluir=i)
            if s:
                dec += 1
                ok += s == ref[i]["subcategory"]
        prec = ok / dec if dec else 0
        if prec < PRECISION_MIN:
            fuera.append((cat, len(vacias), f"precisión medida {prec:.0%}"))
            continue
        n = 0
        for p in vacias:
            s = ix.votar(set(tokens(p.get("name") or "")))
            if s:
                n += 1
                if args.aplicar:
                    p["subcategory"] = s
        asignadas += n
        print(f"  {cat:34} sin subcategoría {len(vacias):5,}  asignadas {n:5,}  (precisión medida {prec:.0%})")
    for cat, n, porque in fuera:
        print(f"  {cat:34} sin subcategoría {n:5,}  NO se toca: {porque}")
    print(f"fichas sin subcategoría: {total:,}; asignadas por vecinos: {asignadas:,}")
    if args.aplicar and asignadas:
        save_catalog(data)
        print("Guardado.")


if __name__ == "__main__":
    main()
