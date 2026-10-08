#!/usr/bin/env python3
"""Fichas en la subcategoría equivocada según un segundo modelo, independiente
del bayesiano (08-oct-2026).

POR QUÉ
-------
auditoria_nb_sub.py y detectar_mal_clasificados.py usan el mismo tipo de modelo
con el que se clasificó el catálogo: lo que ese modelo clasificó mal, él mismo
lo vuelve a ver bien (muestra del 8-oct: 1 de 12 errores aparecía en la lista
del bayesiano). Acá se entrena un SVM lineal con palabras sueltas + pares de
palabras + marca + tiendas que venden la ficha, y se puntúa CADA ficha con un
modelo que no la vio (validación cruzada por bloques). Es otro punto de vista:
las fichas donde los dos coinciden en la subcategoría correcta casi siempre
son errores de verdad.

NECESITA scikit-learn (no es dependencia del sitio):
    pip install --target /tmp/skl_env scikit-learn ; PYTHONPATH=/tmp/skl_env python3 ...

SÓLO LEE LOS FRAGMENTOS (data/cat/*.json.gz), categoría por categoría; CAT_DIR
apunta a una copia si la cadena de regeneración está reescribiéndolos.

USO
---
    PYTHONPATH=/tmp/skl_env python3 scripts/auditoria_lineal_sub.py --categoria "Muebles" --salida /tmp/lin.json
El JSON es {"cat | sub | cat | sub2": [ids]} (lo que lee aplicar_movimientos.py)
y a su lado, con «.detalle» antes de la extensión, {id: [margen, nombre, sub, [[sub2, margen], ...]]}.
"""
import argparse
import collections
import glob
import gzip
import io
import json
import os
import re
import sys
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)

MIN_FICHAS_CLASE = 15
SIN_SUB = {None, "", "Otros"}


def T(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s)


def slug(nombre):
    from data_io import slugify
    return slugify(nombre)


def cargar_categoria(nombre):
    """[(id, nombre, marca, sub, tiendas)] de todos los fragmentos de la categoría."""
    out = []
    carpeta = os.environ.get("CAT_DIR") or os.path.join(ROOT, "data", "cat")
    for fn in sorted(glob.glob(os.path.join(carpeta, slug(nombre) + "-*.json.gz"))):
        try:
            with gzip.open(fn, "rt", encoding="utf-8") as f:
                for p in json.load(f):
                    tiendas = sorted({o.get("storeId") for o in (p.get("offers") or []) if o.get("storeId")})
                    out.append((p["id"], p.get("name") or "", p.get("brand") or "", p.get("subcategory"), tiendas))
        except Exception as e:
            print(f"  AVISO: no se pudo leer {os.path.basename(fn)}: {e}", file=sys.stderr)
    return out


def texto(nombre, marca, tiendas):
    t = T(nombre)
    extra = []
    if marca:
        extra.append("zmarca_" + re.sub(r"[^a-z0-9]+", "_", T(marca)).strip("_"))
    for s in tiendas:
        extra.append("ztienda_" + re.sub(r"[^a-z0-9]+", "_", str(s)))
    return t + " " + " ".join(extra)


def auditar(nombre, margen, folds=4, topn=3):
    import numpy as np
    from sklearn.feature_extraction.text import HashingVectorizer, TfidfTransformer
    from sklearn.model_selection import KFold
    from sklearn.svm import LinearSVC

    fichas = cargar_categoria(nombre)
    utiles = [i for i, f in enumerate(fichas) if f[3] not in SIN_SUB]
    cont = collections.Counter(fichas[i][3] for i in utiles)
    clases = sorted(c for c, k in cont.items() if k >= MIN_FICHAS_CLASE)
    if len(clases) < 2:
        return []
    cidx = {c: j for j, c in enumerate(clases)}
    usar = [i for i in utiles if fichas[i][3] in cidx]
    if len(usar) < 100:
        return []
    docs = [texto(fichas[i][1], fichas[i][2], fichas[i][4]) for i in usar]
    y = np.array([cidx[fichas[i][3]] for i in usar])
    vec = HashingVectorizer(analyzer="word", ngram_range=(1, 2), n_features=2 ** 20,
                            alternate_sign=False, norm=None, token_pattern=r"(?u)\b[a-z0-9_][a-z0-9_]+\b")
    X = vec.transform(docs)
    X = TfidfTransformer(sublinear_tf=True).fit_transform(X)
    scores = np.zeros((len(usar), len(clases)), dtype=np.float32)
    kf = KFold(n_splits=folds, shuffle=True, random_state=7)
    for tr, te in kf.split(np.arange(len(usar))):
        presentes = np.unique(y[tr])
        modelo = LinearSVC(C=0.6, loss="squared_hinge", max_iter=2000)
        modelo.fit(X[tr], y[tr])
        d = modelo.decision_function(X[te])
        if len(presentes) == 2 and d.ndim == 1:      # caso binario
            d = np.stack([-d, d], axis=1)
        sc = np.full((len(te), len(clases)), -9.0, dtype=np.float32)
        sc[:, presentes] = d
        scores[te] = sc
    salida = []
    for k, i in enumerate(usar):
        fila = scores[k]
        actual = y[k]
        otros = fila.copy()
        otros[actual] = -1e9
        orden = np.argsort(-otros)[:topn]
        mg = float(otros[orden[0]] - fila[actual])
        if mg >= margen:
            alts = [[clases[j], round(float(otros[j] - fila[actual]), 2)] for j in orden]
            salida.append((fichas[i][0], fichas[i][1], fichas[i][3], clases[orden[0]], round(mg, 2), alts))
    return salida


def _tarea(args):
    nombre, margen, folds = args
    try:
        return nombre, auditar(nombre, margen, folds)
    except Exception as e:  # pragma: no cover
        import traceback
        traceback.print_exc()
        print(f"  ERROR en {nombre}: {e}", file=sys.stderr)
        return nombre, []


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--categoria", action="append", default=[], help="repetible; por omisión, todas")
    ap.add_argument("--excluir", action="append", default=[], help="categorías que se saltan")
    ap.add_argument("--margen", type=float, default=0.3, help="puntaje SVM de la mejor subcategoría ajena sobre la actual")
    ap.add_argument("--folds", type=int, default=4)
    ap.add_argument("--procesos", type=int, default=2)
    ap.add_argument("--ejemplos", type=int, default=4)
    ap.add_argument("--min", type=int, default=5, help="grupos menores no se imprimen")
    ap.add_argument("--salida")
    args = ap.parse_args()

    with io.open(os.path.join(ROOT, "data", "index.json"), encoding="utf-8") as f:
        cats = json.load(f)["categories"]
    if args.categoria:
        cats = [c for c in cats if c in args.categoria]
    cats = [c for c in cats if c not in args.excluir]
    grupos = collections.defaultdict(list)
    detalle = {}
    ejemplos = collections.defaultdict(list)
    import multiprocessing
    with multiprocessing.Pool(args.procesos) as pool:
        for nombre, filas in pool.imap_unordered(_tarea, [(c, args.margen, args.folds) for c in cats]):
            print(f"{nombre}: {len(filas)} propuestas", flush=True)
            for pid, n, sub, mejor, mg, alts in filas:
                k = f"{nombre} | {sub} | {nombre} | {mejor}"
                grupos[k].append(pid)
                detalle[pid] = [mg, n[:110], sub, alts]
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
