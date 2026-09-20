#!/usr/bin/env python3
"""Busca fichas que están en una categoría a la que no pertenecen, sin
listas de palabras escritas a mano.

POR QUÉ
-------
Las reglas del clasificador atrapan lo que alguien ya vio. Lo que se coló
por la taxonomía de la tienda no lo ve nadie hasta que aparece en la lista:
un tapete para plantas entre las laptops, una cámara espía entre los
monitores, un baumanómetro entre los celulares. Cada uno necesitaba su
regla, y la regla solo existía después del hallazgo.

CÓMO
----
El vocabulario de cada categoría se APRENDE del propio catálogo:

  1. Se cuenta en cuántas fichas de cada categoría aparece cada palabra.
  2. Una palabra es CARACTERÍSTICA de la categoría si aparece mucho más
     seguido ahí que en el catálogo entero (lift) y en bastantes fichas.
     "ram", "ssd" y "core" son características de Laptops; "de" y "negro"
     no lo son de nada, y se caen solas sin lista de palabras vacías.
  3. Una ficha es sospechosa cuando OTRA categoría le queda mucho mejor
     que la suya. Pedir que no traiga NINGUNA palabra de la propia se
     probó primero y deja pasar demasiado: al tapete de plantas que estaba
     entre las laptops lo salvaba la palabra "pulgadas", que es
     característica de Laptops. Lo que decide es la diferencia.
  4. Para esas se busca de qué OTRA categoría sí trae vocabulario, y se
     propone como destino. Eso es lo que hace el informe accionable: no
     dice "esto está raro", dice "esto parece de Mascotas".

El informe se revisa a mano; con --mover escribe además el JSON de grupos
que lee aplicar_movimientos.py, pero solo con las que pasan el corte.

USO
---
    python3 scripts/auditar_vocabulario.py --salida /tmp/sospechosas.tsv
    python3 scripts/auditar_vocabulario.py --categorias Laptops Monitores
    python3 scripts/auditar_vocabulario.py --mover /tmp/mover.json --corte 4
"""
import argparse
import collections
import json
import math
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import load_catalog  # noqa: E402

RX_TOKEN = re.compile(r'[a-z]{3,}')


def T(s):
    s = (s or '').lower()
    return s.translate(str.maketrans('áéíóúñü', 'aeiounu'))


def tokens(nombre):
    """Palabras de tres letras o más. Los números quedan fuera a propósito:
    "256", "12" y "2024" aparecen en todo y no dicen de qué rubro es."""
    return set(RX_TOKEN.findall(T(nombre)))


def vocabularios(prods, df_min, lift_min):
    """Palabra -> lift, por categoría."""
    n_cat = collections.Counter()
    df_cat = collections.defaultdict(collections.Counter)
    df_all = collections.Counter()
    for p in prods:
        c = p['category']
        n_cat[c] += 1
        for t in p['_tok']:
            df_cat[c][t] += 1
            df_all[t] += 1
    N = len(prods)
    vocab = {}
    for c, n in n_cat.items():
        v = {}
        for t, df in df_cat[c].items():
            if df < df_min:
                continue
            lift = (df / n) / (df_all[t] / N)
            if lift >= lift_min:
                v[t] = lift
        vocab[c] = v
    return vocab, n_cat


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--salida', default='data/vocabulario-sospechosas.tsv')
    ap.add_argument('--categorias', nargs='*', help='solo estas categorías')
    ap.add_argument('--df-min', type=int, default=25,
                    help='una palabra tiene que estar en tantas fichas de la categoría')
    ap.add_argument('--lift-min', type=float, default=3.0,
                    help='cuántas veces más seguido que en el catálogo entero')
    ap.add_argument('--corte', type=float, default=3.0,
                    help='puntaje mínimo del destino propuesto para tomarlo en serio')
    ap.add_argument('--ratio', type=float, default=3.0,
                    help='cuántas veces mejor tiene que quedarle la otra categoría')
    ap.add_argument('--mover', help='escribe el JSON de grupos para aplicar_movimientos.py')
    ap.add_argument('--ventaja-min', type=float, default=15.0,
                    help='solo se mueven las que le sacan tanta ventaja a su categoría. '
                         'El corte se midió revisando a mano 12 propuestas al azar de '
                         'cada banda: de 15 para arriba salieron todas bien; entre 9 y '
                         '15 la mitad eran discutibles (un inodoro inteligente propuesto '
                         'para Decoración, un protector de cuna para Blancos); abajo de '
                         '6 son casi todas malas. El informe completo se sigue '
                         'escribiendo entero: el corte es solo para lo que se mueve solo.')
    ap.add_argument('--muestras', type=int, default=8)
    args = ap.parse_args()

    data = load_catalog()
    prods = [p for p in data['products'] if p.get('category')]
    for p in prods:
        p['_tok'] = tokens(p.get('name'))
    vocab, n_cat = vocabularios(prods, args.df_min, args.lift_min)
    print(f"categorías: {len(vocab)}   fichas: {len(prods):,}")
    print(f"vocabulario aprendido (palabras con df>={args.df_min} y lift>={args.lift_min}):")
    for c in sorted(vocab, key=lambda c: -n_cat[c])[:6]:
        top = sorted(vocab[c], key=vocab[c].get, reverse=True)[:12]
        print(f"   {c[:28]:30} {len(vocab[c]):4} palabras   p.ej. {', '.join(top)}")

    objetivo = [p for p in prods
                if not args.categorias or p['category'] in args.categorias]
    # Puntaje de una ficha contra un vocabulario: suma de log(lift) de las
    # palabras que comparte. El log evita que una sola palabra rarísima
    # (lift 200) pese más que cuatro palabras claramente del rubro.
    def puntaje(tok, v):
        return sum(math.log(v[t]) for t in tok if t in v)

    filas = []
    for p in objetivo:
        c = p['category']
        propio = puntaje(p['_tok'], vocab.get(c) or {})
        mejor, mejor_p = None, 0.0
        for c2, v2 in vocab.items():
            if c2 == c:
                continue
            s = puntaje(p['_tok'], v2)
            if s > mejor_p:
                mejor, mejor_p = c2, s
        if mejor_p < args.corte or mejor_p < propio * args.ratio:
            continue
        filas.append((mejor_p - propio, p, mejor, propio, mejor_p))
    filas.sort(key=lambda f: -f[0])

    with open(args.salida, 'w', encoding='utf-8') as f:
        f.write("ventaja\tpropio\tdestino\tcategoria\tsubcategoria\t"
                "destino_propuesto\tid\tnombre\n")
        for d, p, mejor, propio, mp in filas:
            f.write(f"{d:.2f}\t{propio:.2f}\t{mp:.2f}\t{p['category']}\t"
                    f"{p.get('subcategory') or ''}\t{mejor or ''}\t{p['id']}\t"
                    f"{(p.get('name') or '')[:160]}\n")

    por_cat = collections.Counter(p['category'] for _, p, _, _, _ in filas)
    print(f"\nFichas que encajan mucho mejor en otra categoría: {len(filas):,}")
    print("Por categoría (top 15):")
    for c, n in por_cat.most_common(15):
        print(f"   {n:5}  {c}   ({100 * n / max(n_cat[c], 1):.1f}% de la categoría)")

    fuertes = [(d, p, m) for d, p, m, _, _ in filas]
    print(f"\nCorte: destino >= {args.corte} y al menos {args.ratio}x mejor que la propia")
    for s, p, m in fuertes[:args.muestras]:
        print(f"   {s:5.2f}  {p['category']} -> {m}")
        print(f"          {(p.get('name') or '')[:96]}")
    print(f"\nInforme completo: {args.salida}")

    if args.mover:
        grupos = collections.defaultdict(list)
        reg = {c['id']: {sc['id'] for sc in (c.get('subcategories') or [])}
               for c in data['categories']}
        saltadas = 0
        for s, p, m in fuertes:
            if s < args.ventaja_min:
                continue
            # Sin subcategoría de destino: la pone el reparto posterior.
            if not reg.get(m):
                saltadas += 1
                continue
            grupos[f"{p['category']} | {p.get('subcategory')} | {m} | "].append(p['id'])
        json.dump(grupos, open(args.mover, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=0)
        print(f"Grupos para aplicar_movimientos: {sum(len(v) for v in grupos.values())} "
              f"fichas en {len(grupos)} grupos -> {args.mover}")


if __name__ == '__main__':
    main()
