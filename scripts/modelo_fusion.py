#!/usr/bin/env python3
"""Modelo aprendido para decidir si dos fichas son EL MISMO producto.

POR QUÉ
-------
Las fusiones de hoy van por reglas: mismo código de barras, o un código de
modelo en común y el veto de fusionar_vetado.py. Eso es preciso pero ciego a
lo que no trae código: en merge_amazon_cross_store.py el motivo número uno
de «no se fusiona» es «sin código de modelo» (376 mil fichas), y de los
productos de Walmart que se probaron, el 98% no encontró candidata.

DE DÓNDE SALEN LAS ETIQUETAS
----------------------------
Del código de barras, que es una prueba independiente del nombre: un
producto del feed de Walmart o de Sam's (nombre de ESA tienda) contra las
fichas del catálogo que se le parecen por el nombre (los 10 vecinos de
vecinos_catalogo.py, que es como se buscarán candidatas en uso real) y que
tienen código de barras propio. Mismo código -> 1; otro código -> 0. Los
negativos son justo los difíciles: nombres parecidos de productos distintos
(otra capacidad, otro color, otro modelo de la misma línea).

EL MODELO
---------
Regresión logística (numpy, sin dependencias) sobre rasgos del par: parecido
de palabras pesado por rareza, códigos en común y en conflicto, medidas
iguales o distintas, números, marca, precio, paquete y reacondicionado. Los
pesos quedan en data/modelo-fusion.json (se versiona; es chico).

CÓMO SE USA
-----------
Como un juez más, nunca solo: una unión propuesta por el modelo tiene que
pasar TAMBIÉN el veto de fusionar_vetado.py, y el umbral se fija para una
precisión de 97% o más en la parte del conjunto que no se usó para entrenar.

USO
---
    python3 scripts/modelo_fusion.py entrenar --feed /tmp/walmart.json --feed /tmp/sams.json
    python3 scripts/modelo_fusion.py probar "Licuadora Oster 10 vel BLSTMG" 1299 "Licuadora Oster BLSTMG-B00 1.25 L" 1199
"""
import argparse
import collections
import json
import math
import os
import random
import re
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import fusionar_vetado as FV  # noqa: E402

RUTA_MODELO = os.path.join(RAIZ, "data", "modelo-fusion.json")
RX_TOKEN = re.compile(r"[a-z0-9]+")
RX_NUM = re.compile(r"\d+(?:[.,]\d+)?")
# Lo que separa dos productos de la misma línea (medido en los falsos
# positivos del primer entrenamiento: el juego «Deluxe» contra el normal,
# «Buds 8 Active» contra «Buds 8 Lite», la PC con otra tarjeta de video).
EDICIONES = {"deluxe", "ultimate", "edition", "edicion", "collection", "coleccion", "goty", "premium",
             "special", "especial", "definitive", "definitiva", "complete", "completa", "gold", "standard"}
VARIANTES = {"pro", "max", "plus", "mini", "ultra", "lite", "active", "air", "se", "fe", "neo", "slim", "prime", "xl"}
PLATAFORMAS = {"ps4", "ps5", "xbox", "switch", "nsw", "pc", "one"}
RX_NUM_LARGO = re.compile(r"(?<![\d.])\d{3,5}(?![\d.])")
COLORES = {"negro", "negra", "blanco", "blanca", "gris", "azul", "rojo", "roja", "rosa", "verde", "plata",
           "plateado", "dorado", "oro", "morado", "lila", "amarillo", "naranja", "cafe", "beige", "grafito",
           "black", "white", "gray", "grey", "blue", "red", "pink", "green", "silver", "gold", "purple",
           "titanio", "menta", "coral", "turquesa", "vino", "marino", "crema"}

NOMBRES = ["cos_idf", "jaccard", "cubre_min", "cubre_max", "cod_comun", "cod_solo_a", "cod_solo_b",
           "cod_conflicto", "med_igual", "med_conflicto", "num_jaccard", "precio_log", "precio_18",
           "paquete_distinto", "usado_distinto", "marca_igual", "marca_distinta", "largo_ratio",
           "color_distinto", "color_igual", "edicion_distinta", "variante_distinta",
           "plataforma_distinta", "num_largo_distinto", "num_largo_igual"]


def toks(s):
    return RX_TOKEN.findall(FV.norm(s))


class Rasgos:
    """Calcula el vector de rasgos de un par con el idf del catálogo."""

    def __init__(self, idf, idf_max):
        self.idf, self.idf_max = idf, idf_max

    def w(self, t):
        return self.idf.get(t, self.idf_max)

    def __call__(self, a, pa, ma, b, pb, mb):
        na, nb = FV.norm(a), FV.norm(b)
        ta, tb = set(toks(a)), set(toks(b))
        comun = ta & tb
        wa, wb, wc = (sum(self.w(t) for t in x) for x in (ta, tb, comun))
        cos = wc / math.sqrt(wa * wb) if wa and wb else 0.0
        jac = len(comun) / len(ta | tb) if ta | tb else 0.0
        cub_a, cub_b = (wc / wa if wa else 0.0), (wc / wb if wb else 0.0)
        ca, cb = FV.codigos(na), FV.codigos(nb)
        cc = ca & cb
        ma_, mb_ = FV.medidas(na), FV.medidas(nb)
        numa, numb = set(RX_NUM.findall(na)), set(RX_NUM.findall(nb))
        numj = len(numa & numb) / len(numa | numb) if numa | numb else 0.5
        if pa and pb:
            plog = abs(math.log(pa / pb))
        else:
            plog = 0.0
        nla, nlb = set(RX_NUM_LARGO.findall(na)), set(RX_NUM_LARGO.findall(nb))
        marca_a, marca_b = FV.norm(ma or ""), FV.norm(mb or "")
        marca_igual = 1.0 if marca_a and marca_b and (marca_a == marca_b or marca_a in nb or marca_b in na) else 0.0
        marca_dist = 1.0 if marca_a and marca_b and not marca_igual else 0.0
        return [cos, jac, min(cub_a, cub_b), max(cub_a, cub_b),
                min(len(cc), 3), min(len(ca - cb), 3), min(len(cb - ca), 3),
                1.0 if ca and cb and not cc else 0.0,
                1.0 if ma_ and mb_ and ma_ == mb_ else 0.0,
                1.0 if ma_ and mb_ and ma_ != mb_ else 0.0,
                numj, min(plog, 3.0), 1.0 if plog >= math.log(1.8) else 0.0,
                1.0 if bool(FV.PAQUETE_RE.search(na)) != bool(FV.PAQUETE_RE.search(nb)) else 0.0,
                1.0 if bool(FV.USADO_RE.search(na)) != bool(FV.USADO_RE.search(nb)) else 0.0,
                marca_igual, marca_dist,
                min(len(ta), len(tb)) / max(len(ta), len(tb), 1),
                1.0 if (ta & COLORES) and (tb & COLORES) and not (ta & tb & COLORES) else 0.0,
                1.0 if ta & tb & COLORES else 0.0,
                1.0 if (ta & EDICIONES) ^ (tb & EDICIONES) else 0.0,
                1.0 if (ta & VARIANTES) ^ (tb & VARIANTES) else 0.0,
                1.0 if (ta & PLATAFORMAS) and (tb & PLATAFORMAS) and not (ta & tb & PLATAFORMAS) else 0.0,
                1.0 if nla and nlb and nla != nlb else 0.0,
                1.0 if nla and nla == nlb else 0.0]


def idf_de(productos):
    df = collections.Counter()
    for p in productos:
        df.update(set(toks(p.get("name"))))
    n = max(len(productos), 1)
    idf = {t: math.log(n / k) for t, k in df.items()}
    return idf, math.log(n)


class ModeloFusion:
    def __init__(self, pesos, media, desv, umbral, idf, idf_max):
        self.pesos, self.media, self.desv, self.umbral = np.array(pesos), np.array(media), np.array(desv), umbral
        self.rasgos = Rasgos(idf, idf_max)

    @classmethod
    def cargar(cls, productos, ruta=RUTA_MODELO):
        m = json.load(open(ruta, encoding="utf-8"))
        idf, idf_max = idf_de(productos)
        return cls(m["pesos"], m["media"], m["desv"], m["umbral"], idf, idf_max)

    def prob(self, a, pa, ma, b, pb, mb):
        x = (np.array(self.rasgos(a, pa, ma, b, pb, mb)) - self.media) / self.desv
        z = self.pesos[0] + x @ self.pesos[1:]
        return float(1 / (1 + math.exp(-z)))

    def mismo(self, *par):
        return self.prob(*par) >= self.umbral


def logistica(X, y, l2=1e-3, iters=3000, lr=0.5):
    X1 = np.hstack([np.ones((len(X), 1)), X])
    w = np.zeros(X1.shape[1])
    pos = y.mean()
    peso = np.where(y == 1, 0.5 / pos, 0.5 / (1 - pos))   # clases balanceadas
    for _ in range(iters):
        p = 1 / (1 + np.exp(-(X1 @ w)))
        g = X1.T @ ((p - y) * peso) / len(y) + l2 * np.r_[0, w[1:]]
        w -= lr * g
    return w


def pares_de_entrenamiento(feeds, productos, max_items=25000, k=10, semilla=1):
    from emparejar_feed import gtin_norm
    from vecinos_catalogo import Vecinos
    con_gtin = [p for p in productos if gtin_norm(p.get("gtin")) and p.get("offers")]
    tiendas_de = {p["id"]: {o.get("storeId") for o in p["offers"]} for p in con_gtin}
    por_id = {p["id"]: p for p in con_gtin}
    gtins = {gtin_norm(p["gtin"]) for p in con_gtin}
    v = Vecinos(con_gtin)
    items = []
    for f in feeds:
        for it in json.load(open(f, encoding="utf-8")):
            g = gtin_norm(it.get("gtin"))
            if g and g in gtins and it.get("price"):
                items.append((it, g))
    random.Random(semilla).shuffle(items)
    items = items[:max_items]
    # Los que no tienen su gemelo en el catálogo también sirven (sólo
    # negativos), en la misma cantidad: así se ve el caso real, en el que la
    # mayoría de lo que llega NO tiene gemelo.
    pares = []
    for it, g in items:
        vistos = set()
        for q, _ in v.mas_parecidas(titulo=it["title"], k=k):
            p = por_id[q]
            if it["store"] in tiendas_de[q]:
                continue
            vistos.add(q)
            pares.append((it, p, 1 if gtin_norm(p["gtin"]) == g else 0, g))
    return pares


def precio_min(p):
    xs = [o["price"] for o in p.get("offers") or [] if o.get("price")]
    return min(xs) if xs else None


def entrenar(args):
    from data_io import load_catalog
    productos = load_catalog()["products"]
    idf, idf_max = idf_de(productos)
    R = Rasgos(idf, idf_max)
    pares = pares_de_entrenamiento(args.feed, productos)
    print(f"pares: {len(pares):,}; mismo producto: {sum(y for _, _, y, _ in pares):,}")
    # separar por código de barras: el mismo producto nunca en los dos lados
    grupos = sorted({g for *_, g in pares})
    random.Random(7).shuffle(grupos)
    prueba = set(grupos[: len(grupos) // 5])
    X, y, es_prueba, ej = [], [], [], []
    for it, p, lab, g in pares:
        X.append(R(it["title"], it["price"], it.get("brand"), p["name"], precio_min(p), p.get("brand")))
        y.append(lab)
        es_prueba.append(g in prueba)
        ej.append((it["title"], p["name"], lab))
    X, y, es_prueba = np.array(X, dtype=float), np.array(y, dtype=float), np.array(es_prueba)
    media, desv = X[~es_prueba].mean(0), X[~es_prueba].std(0) + 1e-9
    Xn = (X - media) / desv
    w = logistica(Xn[~es_prueba], y[~es_prueba])
    p = 1 / (1 + np.exp(-(np.hstack([np.ones((len(Xn), 1)), Xn]) @ w)))
    pt, yt = p[es_prueba], y[es_prueba]
    print(f"prueba: {int(es_prueba.sum()):,} pares, {int(yt.sum()):,} positivos")
    umbral = None
    for u in [0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.93, 0.95, 0.97, 0.98, 0.99]:
        sel = pt >= u
        prec = yt[sel].mean() if sel.any() else float("nan")
        rec = (yt[sel].sum() / yt.sum()) if yt.sum() else float("nan")
        print(f"  umbral {u:.2f}: precisión {prec:.3f}  cobertura {rec:.3f}  ({int(sel.sum())} pares)")
        if umbral is None and sel.any() and prec >= 0.97:
            umbral = u
    umbral = umbral or 0.99
    print("pesos:")
    for n, x in sorted(zip(NOMBRES, w[1:]), key=lambda t: -abs(t[1])):
        print(f"  {n:18} {x:+.2f}")
    json.dump({"pesos": w.tolist(), "media": media.tolist(), "desv": desv.tolist(), "umbral": umbral,
               "rasgos": NOMBRES, "pares": len(pares)},
              open(args.salida, "w", encoding="utf-8"), indent=1)
    print(f"umbral elegido (precisión >= 97% en prueba): {umbral}  -> {args.salida}")
    # errores en prueba, para mirar a mano
    idx = [i for i in range(len(y)) if es_prueba[i] and p[i] >= umbral and y[i] == 0][:15]
    for i in idx:
        print(f"  FALSO +  {p[i]:.2f}  {ej[i][0][:55]}  ||  {ej[i][1][:55]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("entrenar")
    e.add_argument("--feed", action="append", required=True)
    e.add_argument("--salida", default=RUTA_MODELO)
    pr = sub.add_parser("probar")
    pr.add_argument("a")
    pr.add_argument("pa", type=float)
    pr.add_argument("b")
    pr.add_argument("pb", type=float)
    args = ap.parse_args()
    if args.cmd == "entrenar":
        entrenar(args)
    else:
        from data_io import load_catalog
        m = ModeloFusion.cargar(load_catalog()["products"])
        print(f"{m.prob(args.a, args.pa, None, args.b, args.pb, None):.3f} (umbral {m.umbral})")


if __name__ == "__main__":
    main()
