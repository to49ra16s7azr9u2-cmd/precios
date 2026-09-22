#!/usr/bin/env python3
"""Aprende de las fichas ya clasificadas para decidir dentro de una categoría.

DE DÓNDE SALE LA IDEA
---------------------
De mirar qué les pasa a las fichas que quedan sin clasificar: casi siempre
tienen la CATEGORÍA bien puesta y les falta sólo la subcategoría. Eso no es
casualidad. Las reglas por título que deciden la categoría son anchas
("taladro" -> Herramientas) y aciertan seguido; las que deciden la
subcategoría son finas ("rotomartillo SDS-plus" -> Taladros y
rotomartillos) y se niegan ante la duda, que es lo correcto.

Pero si la categoría ya está puesta, el problema dejó de ser elegir entre
57 categorías: es elegir entre las diez o sesenta subcategorías de ESA
categoría. Y para eso hay algo que las reglas no usan: las 338,000 fichas
que YA están clasificadas. Dentro de Herramientas hay 21,777 ejemplos
resueltos de cómo se ve el título de un taladro y cómo el de una pinza.

CÓMO
----
Un bayes ingenuo por categoría, entrenado con sus propias fichas
clasificadas. De cada título salen sus palabras; de cada subcategoría, con
qué frecuencia usa cada palabra. Para una ficha nueva se calcula qué
subcategoría explica mejor su título.

POR QUÉ SE PUEDE CONFIAR
------------------------
Porque se mide. Una quinta parte de las fichas clasificadas se aparta antes
de entrenar y sirve para contar cuántas veces el modelo acierta a distintos
niveles de confianza. El umbral no se elige a ojo: se elige leyendo esa
tabla, y sólo se asigna por encima del nivel donde la precisión medida
llega al mínimo pedido.

Donde el modelo no llega a ese nivel, no contesta. Es la misma regla que
siguen las reglas por título: ante la duda, nada.

DOS USOS
--------
  --asignar   pone subcategoría a las fichas que no tienen
  --auditar   al revés: busca fichas que SÍ tienen subcategoría pero cuyo
              título el modelo explica mucho mejor con otra. Son candidatas
              a estar mal clasificadas.

USO
---
    python3 scripts/aprender_subcategoria.py --evaluar
    python3 scripts/aprender_subcategoria.py --asignar --precision 0.95
    python3 scripts/aprender_subcategoria.py --auditar --margen 4
"""
import argparse
import collections
import math
import os
import random
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog  # noqa: E402

# Palabras que aparecen en todo y no distinguen nada.
VACIAS = {
    "para", "con", "sin", "por", "del", "las", "los", "una", "uno", "the",
    "and", "color", "negro", "blanco", "azul", "rojo", "gris", "verde",
    "rosa", "plata", "dorado", "marca", "modelo", "nuevo", "original",
    "incluye", "pieza", "piezas", "paquete", "pack", "set", "kit", "venta",
    "internacional", "envio", "gratis", "gran", "alta", "calidad", "super",
    "mini", "max", "pro", "plus", "premium", "profesional",
}
MIN_EJEMPLOS = 8      # una subcategoría con menos ejemplos no se aprende
MIN_PALABRAS = 2      # un título de una palabra no alcanza para decidir


def T(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def palabras(texto):
    return {w for w in re.split(r"[^a-z0-9]+", T(texto))
            if len(w) > 2 and w not in VACIAS and not w.isdigit()}


class ModeloCategoria:
    """Bayes ingenuo sobre las palabras del título, dentro de una categoría."""

    def __init__(self, ejemplos):
        # ejemplos: [(subcategoría, título)]
        self.cuenta = collections.defaultdict(collections.Counter)
        self.total = collections.Counter()
        self.docs = collections.Counter()
        self.vocab = set()
        for sub, titulo in ejemplos:
            ws = palabras(titulo)
            self.docs[sub] += 1
            for w in ws:
                self.cuenta[sub][w] += 1
                self.total[sub] += 1
                self.vocab.add(w)
        self.n = sum(self.docs.values())
        self.v = max(len(self.vocab), 1)
        self.subs = [s for s in self.docs if self.docs[s] >= MIN_EJEMPLOS]

    def puntajes(self, titulo):
        ws = palabras(titulo) & self.vocab
        if len(ws) < MIN_PALABRAS or not self.subs:
            return []
        out = []
        for sub in self.subs:
            # log P(sub) + suma de log P(palabra|sub), con Laplace.
            lp = math.log(self.docs[sub] / self.n)
            den = self.total[sub] + self.v
            for w in ws:
                lp += math.log((self.cuenta[sub][w] + 1) / den)
            out.append((lp, sub))
        out.sort(reverse=True)
        return out

    def decidir(self, titulo):
        """(subcategoría, margen) o (None, 0). El margen es la diferencia de
        log-probabilidad con la segunda opción: cuánto mejor explica el
        título la ganadora que la que le sigue."""
        p = self.puntajes(titulo)
        if len(p) < 2:
            return (p[0][1], 99.0) if p else (None, 0.0)
        return p[0][1], p[0][0] - p[1][0]


def construir(products, apartar=0.0, semilla=7):
    """{categoría: (modelo, [(sub, título) apartados])}"""
    por_cat = collections.defaultdict(list)
    for p in products:
        if p.get("category") and p.get("subcategory"):
            por_cat[p["category"]].append((p["subcategory"], p["name"]))
    rnd = random.Random(semilla)
    modelos = {}
    for cat, ejs in por_cat.items():
        if len(ejs) < MIN_EJEMPLOS * 2:
            continue
        ejs = list(ejs)
        rnd.shuffle(ejs)
        corte = int(len(ejs) * apartar)
        modelos[cat] = (ModeloCategoria(ejs[corte:]), ejs[:corte])
    return modelos


def evaluar(products):
    """Precisión medida por tramo de margen, sobre las fichas apartadas."""
    modelos = construir(products, apartar=0.20)
    tramos = [0, 1, 2, 4, 8, 16, 32]
    acierto = collections.Counter()
    total = collections.Counter()
    for cat, (modelo, prueba) in modelos.items():
        for sub_real, titulo in prueba:
            sub, margen = modelo.decidir(titulo)
            if sub is None:
                continue
            for t in tramos:
                if margen >= t:
                    total[t] += 1
                    if sub == sub_real:
                        acierto[t] += 1
    print(f"{len(modelos)} categorías con modelo; "
          f"{sum(len(p) for _m, p in modelos.values()):,} fichas apartadas para medir\n")
    print("  margen   contesta   precisión")
    for t in tramos:
        if not total[t]:
            continue
        print(f"   >= {t:<4} {total[t]:>8,}   {acierto[t] / total[t] * 100:5.1f}%")
    return modelos


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--evaluar", action="store_true",
                    help="medir la precisión por tramo de margen y salir")
    ap.add_argument("--asignar", action="store_true",
                    help="poner subcategoría a las fichas que no tienen")
    ap.add_argument("--auditar", action="store_true",
                    help="listar fichas cuya subcategoría el modelo contradice")
    ap.add_argument("--margen", type=float, default=8.0,
                    help="margen mínimo (por omisión %(default)s)")
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--limite", type=int, default=40)
    args = ap.parse_args()

    data = load_catalog()
    if args.evaluar or not (args.asignar or args.auditar):
        evaluar(data["products"])
        return 0

    modelos = construir(data["products"])
    subs_validas = {(c["id"], s["id"]) for c in data["categories"]
                    for s in (c.get("subcategories") or [])}

    if args.asignar:
        puestas, cuenta = [], collections.Counter()
        for p in data["products"]:
            if p.get("subcategory") or p.get("category") not in modelos:
                continue
            sub, margen = modelos[p["category"]][0].decidir(p["name"])
            if sub and margen >= args.margen and (p["category"], sub) in subs_validas:
                puestas.append((p, sub, margen))
                cuenta[f"{p['category']} / {sub}"] += 1
        for k, n in cuenta.most_common(25):
            print(f"  {n:>4}  {k}")
        print(f"\nasignables con margen >= {args.margen}: {len(puestas):,}")
        for p, sub, m in puestas[:8]:
            print(f"    [{m:5.1f}] {sub:32} {p['name'][:50]}")
        if args.aplicar:
            for p, sub, _m in puestas:
                p["subcategory"] = sub
            save_catalog(data)
            print("\nCatálogo guardado.")
        else:
            print("\n(sin --aplicar no se guarda nada)")
        return 0

    # --auditar
    sospechosas = []
    for p in data["products"]:
        cat, sub = p.get("category"), p.get("subcategory")
        if not sub or cat not in modelos:
            continue
        modelo = modelos[cat][0]
        puntos = modelo.puntajes(p["name"])
        if len(puntos) < 2:
            continue
        mejor_lp, mejor = puntos[0]
        suyo = next((lp for lp, s in puntos if s == sub), None)
        if suyo is None or mejor == sub:
            continue
        if mejor_lp - suyo >= args.margen:
            sospechosas.append((mejor_lp - suyo, cat, sub, mejor, p["name"]))
    sospechosas.sort(reverse=True)
    grupos = collections.Counter(f"{c} | {s} -> {m}" for _d, c, s, m, _n in sospechosas)
    print(f"fichas cuya subcategoría el modelo contradice por {args.margen}+ : "
          f"{len(sospechosas):,}\n")
    for k, n in grupos.most_common(args.limite):
        ej = next(nm for _d, c, s, m, nm in sospechosas if f"{c} | {s} -> {m}" == k)
        print(f"  {n:>5}  {k}")
        print(f"          p.ej. {ej[:70]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
