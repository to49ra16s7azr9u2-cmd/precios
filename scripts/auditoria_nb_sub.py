#!/usr/bin/env python3
"""Fichas en la subcategoría equivocada, según el propio catálogo, sin que
cada ficha vote por sí misma (08-oct-2026).

POR QUÉ
-------
detectar_mal_clasificados.py ya entrena un bayesiano ingenuo con el catálogo
y propone mover lo que otra subcategoría explica mucho mejor. Pero puntúa la
subcategoría actual CON la ficha dentro: cada palabra suya que no aparece en
otra ficha (un modelo, una marca rara, un par de palabras) suma al «voto» de
su propia subcategoría, y a las fichas de cola larga eso les regala 6 u 8
nats, justo el margen que se exige para moverlas. Medido con muestras al azar,
los errores que quedan son esos: «barra de labios» en spa, «cuna moisés» en
carriolas, «cable» en cargadores.

Acá se puntúa la subcategoría actual SIN la ficha (dejando una fuera, como ya
hace reclasificar_hibrido.py con las categorías) y las palabras que salen en
una sola ficha de la categoría se ignoran.

SÓLO LEE LOS FRAGMENTOS (data/cat/*.json.gz), no el catálogo entero: va
categoría por categoría y no pasa de ~2 GB. La categoría de cada ficha es la
del archivo.

USO
---
    python3 scripts/auditoria_nb_sub.py --salida /tmp/nb.json            # todas
    python3 scripts/auditoria_nb_sub.py --categoria "Belleza y cuidado personal" --margen 6 --ejemplos 6
El JSON es {"cat | sub | cat | sub2": [ids]} (lo que lee aplicar_movimientos.py)
y a su lado, con «.detalle» antes de la extensión, {id: [margen, nombre]}.
"""
import argparse
import collections
import glob
import gzip
import io
import json
import math
import multiprocessing
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
from detectar_mal_clasificados import tokens  # noqa: E402

MIN_FICHAS_CLASE = 15
SIN_SUB = {None, "", "Otros"}


def slug(nombre):
    from data_io import slugify
    return slugify(nombre)


def cargar_categoria(nombre):
    """[(id, nombre, sub)] de todos los fragmentos de la categoría."""
    out = []
    carpeta = os.environ.get("CAT_DIR") or os.path.join(ROOT, "data", "cat")
    for fn in sorted(glob.glob(os.path.join(carpeta, slug(nombre) + "-*.json.gz"))):
        try:
            with gzip.open(fn, "rt", encoding="utf-8") as f:
                for p in json.load(f):
                    out.append((p["id"], p.get("name") or "", p.get("subcategory")))
        except Exception as e:  # un fragmento a medio escribir: se avisa y se sigue
            print(f"  AVISO: no se pudo leer {os.path.basename(fn)}: {e}", file=sys.stderr)
    return out


def auditar(nombre, margen, min_df=2):
    fichas = cargar_categoria(nombre)
    ts_de = []
    df = collections.Counter()
    for pid, n, sub in fichas:
        ts = tokens(n)
        ts_de.append(ts)
        df.update(ts)
    quedan = {t for t, c in df.items() if c >= min_df}
    # estadísticas por clase
    doc = collections.Counter()
    post = collections.defaultdict(dict)   # token -> {clase: fichas}
    den = collections.Counter()            # clase -> suma de fichas-por-token
    utiles = []
    for (pid, n, sub), ts in zip(fichas, ts_de):
        ts = ts & quedan
        utiles.append(ts)
        if sub in SIN_SUB:
            continue
        doc[sub] += 1
        den[sub] += len(ts)
        for t in ts:
            d = post[t]
            d[sub] = d.get(sub, 0) + 1
    clases = [c for c, k in doc.items() if k >= MIN_FICHAS_CLASE]
    if len(clases) < 2:
        return []
    total = sum(doc[c] for c in clases)
    V = len(quedan) or 1
    LOG = [0.0] + [math.log(i) for i in range(1, len(fichas) + 3)]
    prior = {c: math.log(doc[c] / total) for c in clases}
    claseset = set(clases)
    salida = []
    for (pid, n, sub), ts in zip(fichas, utiles):
        if sub not in claseset or len(ts) < 3:
            continue
        m = len(ts)
        # puntaje base de cada clase: prior - m*log(den+V)  (la actual, sin la ficha)
        s = {}
        for c in clases:
            if c == sub:
                s[c] = math.log((doc[c] - 1) / total) - m * math.log(den[c] - m + V)
            else:
                s[c] = prior[c] - m * math.log(den[c] + V)
        for t in ts:
            for c, k in post[t].items():
                if c not in claseset:
                    continue
                s[c] += LOG[k] if c == sub else LOG[k + 1]
        mejor = max(s, key=s.get)
        if mejor == sub:
            continue
        mg = s[mejor] - s[sub]
        if mg >= margen:
            salida.append((pid, n, sub, mejor, round(mg, 1)))
    return salida


def _tarea(args):
    nombre, margen = args
    try:
        return nombre, auditar(nombre, margen)
    except Exception as e:  # pragma: no cover
        print(f"  ERROR en {nombre}: {e}", file=sys.stderr)
        return nombre, []


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--categoria", action="append", default=[], help="repetible; por omisión, todas")
    ap.add_argument("--margen", type=float, default=6.0, help="nats sobre la subcategoría actual")
    ap.add_argument("--ejemplos", type=int, default=4)
    ap.add_argument("--min", type=int, default=5, help="grupos menores no se imprimen")
    ap.add_argument("--procesos", type=int, default=2)
    ap.add_argument("--salida")
    args = ap.parse_args()

    with io.open(os.path.join(ROOT, "data", "index.json"), encoding="utf-8") as f:
        cats = json.load(f)["categories"]
    if args.categoria:
        cats = [c for c in cats if c in args.categoria]
    grupos = collections.defaultdict(list)
    detalle = {}
    ejemplos = collections.defaultdict(list)
    with multiprocessing.Pool(args.procesos) as pool:
        for nombre, filas in pool.imap_unordered(_tarea, [(c, args.margen) for c in cats]):
            print(f"{nombre}: {len(filas)} propuestas", flush=True)
            for pid, n, sub, mejor, mg in filas:
                k = f"{nombre} | {sub} | {nombre} | {mejor}"
                grupos[k].append(pid)
                detalle[pid] = [mg, n[:110]]
                if len(ejemplos[k]) < args.ejemplos:
                    ejemplos[k].append(f"[{mg}] {n[:84]}")
    total = sum(len(v) for v in grupos.values())
    print(f"\nFichas a mover: {total:,} en {len(grupos)} grupos\n")
    for k, ids in sorted(grupos.items(), key=lambda kv: -len(kv[1])):
        if len(ids) < args.min:
            continue
        print(f"{len(ids):5}  {k}")
        for e in ejemplos[k]:
            print(f"         {e}")
    if args.salida:
        with io.open(args.salida, "w", encoding="utf-8") as f:
            json.dump(dict(grupos), f, ensure_ascii=False, indent=0)
        base, ext = os.path.splitext(args.salida)
        with io.open(base + ".detalle" + ext, "w", encoding="utf-8") as f:
            json.dump(detalle, f, ensure_ascii=False)
        print(f"\nDetalle en {args.salida}")


if __name__ == "__main__":
    main()
