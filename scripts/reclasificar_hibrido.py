#!/usr/bin/env python3
"""Reclasifica el catálogo con tres jueces: el modelo del catálogo, el
sustantivo del principio del título y las reglas (24-sep-2026).

POR QUÉ
-------
Medido contra el catálogo entero, cuando las reglas del clasificador y el
catálogo discrepan, la regla tiene razón sólo en ~2 de cada 10 casos: el
catálogo es «reglas + años de correcciones a mano» y es mejor que las
reglas solas. Un bayesiano entrenado sobre ese catálogo, en cambio, acertó
el 95% de 4,000 títulos que no había visto. Así que para reordenar lo que
ya está en el catálogo, manda el modelo, con dos controles:

  1. El MODELO (bayesiano sobre nombres y pares de palabras, el de
     detectar_mal_clasificados.py) prefiere otra categoría por MARGEN nats
     o más sobre la actual. Se puntúa la categoría actual SIN la propia
     ficha (dejando una fuera): si no, cada ficha votaría por sí misma.
  2. El SUSTANTIVO: el título arranca como los productos de la categoría
     nueva (es_coherente de clasificar_captura_perifericos.py).
  3. Las REGLAS no respaldan la categoría actual (si la regla de hoy dice
     la actual, hace falta un margen mucho mayor) ni proponen una tercera.

Lo movido a mano (data/clasificacion-a-mano.json) y lo que viene del árbol
de Mercado Libre no se toca. Una ficha que una DEFINICIÓN del clasificador
pone en su categoría actual no se mueve nunca. La subcategoría nueva la
eligen los repartidores del clasificador.

USO
---
    python3 scripts/reclasificar_hibrido.py --informe /tmp/h.json      # sólo propone
    python3 scripts/reclasificar_hibrido.py --aplicar
"""
import argparse
import collections
import datetime
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
from data_io import load_catalog, save_catalog  # noqa: E402
from detectar_mal_clasificados import tokens  # noqa: E402

CANDADO = os.path.join(ROOT, "data", "clasificacion-a-mano.json")
# Lo que este script ya movió una vez no se vuelve a mover: el modelo se
# reentrena con cada corrida y, sin esto, una ficha dudosa podría ir y
# venir entre dos categorías.
YA_MOVIDAS = os.path.join(ROOT, "data", "clasificacion-hibrida.json")
BITACORA = os.path.join(ROOT, "data", "movimientos-aplicados.json")
MARGEN = 8.0              # nats sobre la categoría actual
MARGEN_CONTRA_REGLA = 16.0  # si la regla de hoy respalda la categoría actual
MIN_FICHAS_CLASE = 15
FUENTES_ESTRUCTURADAS = {"mercadolibre"}

_M = None  # modelo compartido con los procesos (fork)


class Modelo:
    """Bayes multinomial con índice invertido: puntuar 460 mil títulos contra
    55 categorías en Python puro tarda un par de minutos en vez de media
    hora, porque sólo se recorren las categorías donde aparece cada token."""

    def __init__(self, productos):
        self.doc = collections.Counter()
        self.cnt = collections.defaultdict(collections.Counter)
        for p in productos:
            c = p.get("category")
            if not c or c == "Otros":
                continue
            ts = tokens(p.get("name"))
            self.doc[c] += 1
            self.cnt[c].update(ts)
        self.cats = [c for c, n in self.doc.items() if n >= MIN_FICHAS_CLASE]
        self.N = sum(self.doc.values())
        vocab = set()
        for c in self.cats:
            vocab.update(self.cnt[c])
        self.V = len(vocab)
        self.ntok = {c: sum(self.cnt[c].values()) for c in self.cats}
        self.prior = {c: math.log(self.doc[c] / self.N) for c in self.cats}
        self.lbase = {c: math.log(1 / (self.ntok[c] + self.V)) for c in self.cats}
        self.inv = collections.defaultdict(list)
        for c in self.cats:
            den = self.ntok[c] + self.V
            base = self.lbase[c]
            for t, k in self.cnt[c].items():
                self.inv[t].append((c, math.log((k + 1) / den) - base))

    def puntajes(self, ts):
        n = len(ts)
        s = {c: self.prior[c] + n * self.lbase[c] for c in self.cats}
        for t in ts:
            for c, d in self.inv.get(t, ()):
                s[c] += d
        return s

    def puntaje_sin_si_misma(self, ts, c):
        """La categoría `c` puntuada como si la ficha no estuviera en ella."""
        if c not in self.ntok or self.doc[c] < 2:
            return None
        den = self.ntok[c] - len(ts) + self.V
        s = math.log((self.doc[c] - 1) / (self.N - 1))
        cnt = self.cnt[c]
        for t in ts:
            s += math.log((max(cnt.get(t, 0) - 1, 0) + 1) / den)
        return s


def _evaluar(par):
    pid, nombre, cat = par
    ts = tokens(nombre)
    if len(ts) < 3:
        return pid, None
    pt = _M.puntajes(ts)
    mejor = max(pt, key=pt.get)
    if mejor == cat:
        return pid, None
    actual = _M.puntaje_sin_si_misma(ts, cat) if cat in _M.doc else None
    if actual is None:
        return pid, None
    return pid, (mejor, round(pt[mejor] - actual, 2))


def cargar_json(ruta, defecto):
    try:
        with io.open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return defecto


def main():
    global _M
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--informe")
    ap.add_argument("--margen", type=float, default=MARGEN)
    args = ap.parse_args()

    data = load_catalog()
    productos = data["products"]
    por_id = {p["id"]: p for p in productos}
    _M = Modelo(productos)
    with multiprocessing.Pool(max(1, os.cpu_count() or 1)) as pool:
        res = dict(pool.imap_unordered(
            _evaluar, [(p["id"], p.get("name") or "", p.get("category")) for p in productos], chunksize=2000))
    prefieren = {pid: v for pid, v in res.items() if v and v[1] >= args.margen}
    print(f"fichas: {len(productos):,}; el modelo prefiere otra categoría con margen >= {args.margen}: {len(prefieren):,}")

    import clasificar_captura_perifericos as clasif
    a_mano = cargar_json(CANDADO, {})
    ya_movidas = cargar_json(YA_MOVIDAS, {})
    subs_de = {c["id"]: {s["id"] for s in (c.get("subcategories") or [])} for c in data["categories"]}

    motivos = collections.Counter()
    mover = collections.defaultdict(list)
    for pid, (nueva, margen) in prefieren.items():
        p = por_id[pid]
        cat = p.get("category")
        if nueva not in subs_de:
            continue
        if a_mano.get(pid, [None])[0] == cat:
            motivos["candado: movida a mano"] += 1
            continue
        if pid in ya_movidas:
            motivos["ya la movió este script antes"] += 1
            continue
        tiendas = {o.get("storeId") for o in p.get("offers") or []}
        if tiendas and tiendas <= FUENTES_ESTRUCTURADAS:
            motivos["fuente estructurada (Mercado Libre)"] += 1
            continue
        dr = clasif.decidir({"asin": pid, "title": p.get("name") or ""})
        regla = dr.get("category") if dr.get("estado") == "alta" else None
        n_regla = dr.get("regla")
        if regla == cat and (dr.get("via") in ("explicito", "antes_de_fuera")
                             or (isinstance(n_regla, int) and n_regla < clasif.N_DEFINICIONES)):
            motivos["una definición la pone en su categoría actual"] += 1
            continue
        if regla and regla not in (cat, nueva):
            motivos["la regla propone una tercera categoría"] += 1
            continue
        if regla == cat and margen < MARGEN_CONTRA_REGLA:
            motivos["la regla respalda la actual"] += 1
            continue
        if not clasif.es_coherente(p.get("name") or "", nueva, p.get("brand") or ""):
            motivos["el título no arranca como la categoría nueva"] += 1
            continue
        # La subcategoría la eligen los repartidores del clasificador, como
        # si la regla hubiera dicho la categoría nueva.
        if regla == nueva:
            sub = dr.get("subcategory")
        else:
            df = clasif.decidir({"asin": pid, "title": p.get("name") or "", "_forzar": (nueva, None, None)})
            sub = df.get("subcategory") if df.get("category") == nueva else None
        if sub and sub not in subs_de[nueva]:
            sub = None
        mover[(cat, p.get("subcategory"), nueva, sub)].append((pid, margen))

    total = sum(len(v) for v in mover.values())
    print(f"se mueven: {total:,} en {len(mover)} grupos")
    for k, n in motivos.most_common():
        print(f"  no se mueven: {n:7,}  {k}")
    for k, v in sorted(mover.items(), key=lambda kv: -len(kv[1]))[:30]:
        print(f"{len(v):6}  {k[0]} / {k[1]}  ->  {k[2]} / {k[3]}")
        for pid, m in v[:2]:
            print(f"            [{m:5.1f}] {por_id[pid]['name'][:80]}")
    if args.informe:
        with open(args.informe, "w", encoding="utf-8") as f:
            json.dump({" | ".join(map(str, k)): v for k, v in mover.items()}, f, ensure_ascii=False)
    if not args.aplicar or not total:
        if not args.aplicar:
            print("\n(sin --aplicar: no se tocó el catálogo)")
        return
    icono = {}
    for pp in productos:
        icono.setdefault((pp.get("category"), pp.get("subcategory")), pp.get("image"))
        icono.setdefault((pp.get("category"), None), pp.get("image"))
    for (cat, sub, nueva, sub2), ids in mover.items():
        for pid, _ in ids:
            p = por_id[pid]
            p["category"], p["subcategory"] = nueva, sub2
            ya_movidas[pid] = [cat, nueva]
            ic = icono.get((nueva, sub2)) or icono.get((nueva, None))
            if ic:
                p["image"] = ic
    save_catalog(data)
    with io.open(YA_MOVIDAS, "w", encoding="utf-8") as f:
        json.dump(ya_movidas, f, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    bit = cargar_json(BITACORA, [])
    bit.append({"fecha": datetime.date.today().isoformat(), "origen": "reclasificar_hibrido.py",
                "motivo": "modelo del catálogo + sustantivo + reglas", "automatico": True,
                "grupos": {f"{k[0]} | {k[1]} | {k[2]} | {k[3]}": len(v) for k, v in mover.items()}})
    with io.open(BITACORA, "w", encoding="utf-8") as f:
        json.dump(bit, f, ensure_ascii=False, indent=1)
    print(f"\nGuardado: {total:,} fichas movidas.")


if __name__ == "__main__":
    main()
