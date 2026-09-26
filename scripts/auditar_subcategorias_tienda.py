#!/usr/bin/env python3
"""Revisa, subcategoría por subcategoría, las fichas de una tienda que no
encajan donde están.

POR QUÉ
-------
26-sep-2026: el usuario notó que lo de Walmart y Bodega Aurrerá estaba
especialmente mal clasificado. Son ~590 mil fichas (68% del catálogo), y
una muestra a mano dio ~10% mal fuera de Autopartes. Los errores no eran
aleatorios: eran familias enteras que una palabra suelta del título mandaba
al lugar equivocado (la editorial «Diana» -> dardos, la marca de
impermeabilizante «Acuario» -> acuarios, «Disfraces Tudi» -> bloques).

QUÉ HACE
--------
Un nombre de producto arranca por lo que ES («Impermeabilizante acriterm
acuario 19 l»). Para cada ficha se toma esa palabra de arranque (la
«cabeza», saltando «juego de», «set de», cantidades, etc.) y se mira:

  * qué tan común es esa cabeza EN SU SUBCATEGORÍA, y
  * dónde vive esa cabeza en el resto del catálogo.

Una ficha es atípica cuando su cabeza es rara en su subcategoría (menos del
UMBRAL_LOCAL de las fichas de ahí) y en el catálogo vive mayormente en otro
lugar. El informe las agrupa por (subcategoría, cabeza, lugar habitual)
para revisarlas a mano grupo por grupo y escribir la regla que las arregla
(mover_por_regla.py) y la que evita que vuelvan (el clasificador).

No mueve nada: sólo informa.

USO
---
    python3 scripts/auditar_subcategorias_tienda.py --tiendas walmart_mx,bodega_aurrera \\
        --salida /tmp/auditoria-wb.json
"""
import argparse
import collections
import gzip
import json
import os
import re
import sys
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import DATA_DIR, MANIFEST_PATH  # noqa: E402

ROOT = os.path.dirname(DATA_DIR)
UMBRAL_LOCAL = 0.03      # la cabeza es rara en la subcategoría si es menos del 3%
MIN_GLOBAL = 15          # y en el catálogo aparece al menos tantas veces
MIN_LUGAR = 0.5          # con al menos la mitad en otro lugar

RELLENO = {
    "de", "del", "la", "el", "los", "las", "para", "con", "y", "en", "a", "al", "por", "sin", "un", "una",
    "set", "kit", "paquete", "pack", "juego", "par", "pares", "combo", "duo", "trio", "lote",
    "nuevo", "nueva", "original", "marca", "venta", "internacional", "pieza", "piezas", "pzas", "pza", "pz",
    "pzs", "pcs", "unidades", "x", "mini", "super", "pro", "premium", "exclusiva", "exclusivo", "oferta",
    "the", "for", "and", "with", "of", "de", "s", "pzas", "c", "u",
}
_CANT = re.compile(r"^\d+([a-z]{0,4})?$")


def T(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def cabeza(nombre):
    """Primera palabra con contenido del nombre, en singular aproximado."""
    for w in re.split(r"[^a-z0-9]+", T(nombre)):
        if not w or w in RELLENO or _CANT.match(w) or len(w) < 3:
            continue
        if len(w) > 4 and w.endswith("es") and not w.endswith(("ses", "ces")):
            w = w[:-2]
        elif len(w) > 3 and w.endswith("s"):
            w = w[:-1]
        return w
    return None


def productos():
    m = json.load(open(MANIFEST_PATH, encoding="utf-8"))
    for cat, files in m["categoryFiles"].items():
        for fn in files if isinstance(files, list) else [files]:
            path = os.path.join(ROOT, fn)
            if not os.path.exists(path):
                path += ".gz"
            op = gzip.open if path.endswith(".gz") else open
            with op(path, "rt", encoding="utf-8") as f:
                for p in json.load(f):
                    p.setdefault("category", cat)
                    yield p


def tiendas_de(p):
    ts = {o.get("storeId") for o in p.get("offers") or []}
    for v in p.get("colorVariants") or []:
        ts |= {o.get("storeId") for o in v.get("offers") or []}
    return ts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tiendas", default="walmart_mx,bodega_aurrera")
    ap.add_argument("--salida", required=True)
    args = ap.parse_args()
    tiendas = set(args.tiendas.split(","))

    filas = []                                           # (id, cat, sub, cabeza, nombre, de_la_tienda)
    en_sub = collections.defaultdict(collections.Counter)  # (cat, sub) -> cabeza -> n
    tam_sub = collections.Counter()
    donde = collections.defaultdict(collections.Counter)   # cabeza -> (cat, sub) -> n
    for p in productos():
        h = cabeza(p.get("name"))
        k = (p["category"], p.get("subcategory") or None)
        tam_sub[k] += 1
        if not h:
            continue
        en_sub[k][h] += 1
        donde[h][k] += 1
        if tiendas_de(p) & tiendas:
            filas.append((p["id"], k[0], k[1], h, (p.get("name") or "")[:110]))

    grupos = collections.defaultdict(list)
    for pid, cat, sub, h, nombre in filas:
        k = (cat, sub)
        local = en_sub[k][h] / max(tam_sub[k], 1)
        if local >= UMBRAL_LOCAL:
            continue
        glob = donde[h]
        n = sum(glob.values())
        if n < MIN_GLOBAL:
            continue
        # dónde vive la cabeza fuera de esta subcategoría
        lugar, nl = max(((kk, v) for kk, v in glob.items() if kk != k), key=lambda t: t[1], default=(None, 0))
        if not lugar or nl / n < MIN_LUGAR:
            continue
        grupos[(cat, sub, h, lugar[0], lugar[1], round(nl / n, 2))].append((pid, nombre))

    salida = [{"cat": k[0], "sub": k[1], "cabeza": k[2], "vive_en": [k[3], k[4]], "fraccion": k[5],
               "n": len(v), "fichas": v} for k, v in sorted(grupos.items(), key=lambda kv: -len(kv[1]))]
    with open(args.salida, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False)
    n_sub = len({(g["cat"], g["sub"]) for g in salida})
    print(f"fichas de {sorted(tiendas)}: {len(filas):,}; atípicas: {sum(g['n'] for g in salida):,} "
          f"en {len(salida):,} grupos de {n_sub:,} subcategorías -> {args.salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
