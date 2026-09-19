#!/usr/bin/env python3
"""Encuentra fichas que están en la categoría o subcategoría equivocada,
dejando que el propio catálogo diga cómo se llama lo que hay en cada una.

LA IDEA
-------
auditar_subcategorias.py pasa cada nombre por el clasificador de reglas y
compara. Sirve, pero el clasificador también se equivoca, y cuando los dos
discrepan no hay con qué desempatar.

Acá el árbitro es el catálogo mismo: con 300 mil fichas casi todas bien
puestas, las palabras de los nombres de "Mesas de comedor" son distintas de
las de "Mesas de centro", y una ficha de Mesas de centro cuyo nombre solo
tiene palabras de comedor está mal puesta. Es un clasificador bayesiano
ingenuo entrenado sobre el catálogo: uno para la categoría (con todo el
catálogo) y uno por categoría para la subcategoría.

Una ficha se propone mover solo cuando las DOS fuentes coinciden en el
destino: el modelo del catálogo (con un margen claro) y el clasificador de
reglas (el informe --salida de auditar_subcategorias.py). Dos jueces
independientes de acuerdo se equivocan mucho menos que uno.

USO
---
    python3 scripts/auditar_subcategorias.py --salida /tmp/aud.json
    python3 scripts/detectar_mal_clasificados.py --reglas /tmp/aud.json --salida /tmp/mover.json
    python3 scripts/detectar_mal_clasificados.py --reglas /tmp/aud.json --solo-modelo   # sin exigir acuerdo
    python3 scripts/detectar_mal_clasificados.py --reglas /tmp/aud.json --categoria Muebles --ejemplos 8
"""
import argparse
import collections
import io
import json
import math
import os
import re
import sys
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import load_catalog  # noqa: E402

# Margen mínimo (en nats de log-verosimilitud) entre el destino propuesto y
# la clase actual. 6 nats ~ 400 veces más probable. Alto a propósito: mover
# una ficha bien puesta crea un error nuevo; dejar una mal puesta deja el que
# ya había.
MARGEN_MIN = 6.0
# Con menos fichas que esto una subcategoría no tiene con qué "hablar".
MIN_FICHAS_CLASE = 15

RX_TOKEN = re.compile(r"[a-z0-9]+")
PARAR = {"de", "la", "el", "y", "con", "para", "en", "por", "a", "un", "una", "los", "las", "del", "al", "o", "e",
         "the", "of", "and", "for", "with", "x", "cm", "mm", "kg", "g", "ml", "l", "pz", "pzas", "pcs", "set", "kit",
         "color", "negro", "blanco", "gris", "azul", "rojo", "rosa", "verde", "nuevo", "original", "envio", "gratis"}


def tokens(nombre):
    n = unicodedata.normalize("NFKD", nombre or "").encode("ascii", "ignore").decode().lower()
    ts = [t for t in RX_TOKEN.findall(n) if len(t) >= 2 and t not in PARAR and not t.isdigit()]
    # Bigramas: "mesa comedor" pesa distinto que "mesa" y "comedor" sueltos.
    out = set(ts)
    out.update(a + "_" + b for a, b in zip(ts, ts[1:]))
    return out


class Bayes:
    """Naive Bayes multinomial con suavizado, sobre conjuntos de tokens."""

    def __init__(self):
        self.doc = collections.Counter()               # clase -> fichas
        self.tok = collections.defaultdict(collections.Counter)  # clase -> token -> fichas con ese token
        self.vocab = set()

    def entrenar(self, clase, ts):
        self.doc[clase] += 1
        c = self.tok[clase]
        for t in ts:
            c[t] += 1
        self.vocab.update(ts)

    def preparar(self):
        self.total = sum(self.doc.values())
        self.V = len(self.vocab) or 1
        self.ntok = {c: sum(cnt.values()) for c, cnt in self.tok.items()}

    def puntajes(self, ts):
        """{clase: log P(clase) + sum log P(token|clase)} con Laplace."""
        out = {}
        for c, n in self.doc.items():
            if n < MIN_FICHAS_CLASE:
                continue
            base = math.log(n / self.total)
            den = self.ntok[c] + self.V
            cnt = self.tok[c]
            s = base
            for t in ts:
                s += math.log((cnt.get(t, 0) + 1) / den)
            out[c] = s
        return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reglas", help="JSON de auditar_subcategorias.py --salida (clave 'cat | sub | cat2 | sub2' -> ids)")
    ap.add_argument("--solo-modelo", action="store_true", help="proponer aunque el clasificador de reglas no coincida")
    ap.add_argument("--margen", type=float, default=MARGEN_MIN)
    ap.add_argument("--categoria", help="limitar a fichas que hoy están en esta categoría")
    ap.add_argument("--ejemplos", type=int, default=4, help="nombres de muestra por grupo")
    ap.add_argument("--min", type=int, default=10, help="grupos menores no se imprimen")
    ap.add_argument("--salida", help="JSON con {clave de grupo: [ids]}")
    args = ap.parse_args()

    data = load_catalog()
    productos = data["products"]
    subs_de = {c["id"]: {s["id"] for s in (c.get("subcategories") or [])} for c in data["categories"]}

    reglas = {}
    if args.reglas:
        for k, ids in json.load(io.open(args.reglas, encoding="utf-8")).items():
            partes = [x.strip() for x in k.split("|")]
            if len(partes) != 4:
                continue
            cat2, sub2 = partes[2], (None if partes[3] == "None" else partes[3])
            for pid in ids:
                reglas[pid] = (cat2, sub2)

    # Entrenar
    modelo_cat = Bayes()
    modelo_sub = collections.defaultdict(Bayes)
    toks = {}
    for p in productos:
        ts = tokens(p.get("name"))
        toks[p["id"]] = ts
        cat, sub = p.get("category"), p.get("subcategory")
        if not cat or cat == "Otros":
            continue
        modelo_cat.entrenar(cat, ts)
        if sub and sub != "Otros":
            modelo_sub[cat].entrenar(sub, ts)
    modelo_cat.preparar()
    for m in modelo_sub.values():
        m.preparar()

    grupos = collections.defaultdict(list)
    ejemplos = collections.defaultdict(list)
    for p in productos:
        cat, sub = p.get("category"), p.get("subcategory")
        if args.categoria and cat != args.categoria:
            continue
        ts = toks[p["id"]]
        if len(ts) < 3:
            continue
        # 1) ¿categoría equivocada?
        pc = modelo_cat.puntajes(ts)
        if not pc:
            continue
        mejor_cat = max(pc, key=pc.get)
        destino = None
        if mejor_cat != cat and cat in pc and pc[mejor_cat] - pc[cat] >= args.margen:
            # subcategoría dentro de la categoría nueva
            ms = modelo_sub.get(mejor_cat)
            ps = ms.puntajes(ts) if ms else {}
            mejor_sub = max(ps, key=ps.get) if ps else None
            destino = (mejor_cat, mejor_sub)
        elif mejor_cat == cat or cat not in pc:
            # 2) ¿subcategoría equivocada dentro de la misma categoría?
            ms = modelo_sub.get(cat)
            ps = ms.puntajes(ts) if ms else {}
            if ps:
                mejor_sub = max(ps, key=ps.get)
                if sub in ps:
                    if mejor_sub != sub and ps[mejor_sub] - ps[sub] >= args.margen:
                        destino = (cat, mejor_sub)
                elif not sub or sub == "Otros":
                    # Sin subcategoría: se propone la del modelo si domina con
                    # claridad a la segunda.
                    orden = sorted(ps.values(), reverse=True)
                    if len(orden) == 1 or orden[0] - orden[1] >= args.margen:
                        destino = (cat, mejor_sub)
        if not destino or destino == (cat, sub):
            continue
        if destino[1] and destino[1] not in subs_de.get(destino[0], set()):
            continue
        # 3) ¿el clasificador de reglas opina lo mismo?
        r = reglas.get(p["id"])
        if not args.solo_modelo:
            if not r:
                continue
            if r[0] != destino[0]:
                continue
            # En subcategoría basta que la categoría coincida cuando el
            # movimiento es de categoría; si es de subcategoría, tiene que
            # coincidir la subcategoría.
            if destino[0] == cat and r[1] != destino[1]:
                continue
        k = f"{cat} | {sub} | {destino[0]} | {destino[1]}"
        grupos[k].append(p["id"])
        if len(ejemplos[k]) < args.ejemplos:
            ejemplos[k].append(p["name"][:80])

    total = sum(len(v) for v in grupos.values())
    print(f"Fichas a mover: {total:,} en {len(grupos)} grupos"
          + ("" if args.solo_modelo else " (modelo del catálogo Y clasificador de reglas de acuerdo)") + "\n")
    for k, ids in sorted(grupos.items(), key=lambda kv: -len(kv[1])):
        if len(ids) < args.min:
            continue
        print(f"{len(ids):5}  {k}")
        for e in ejemplos[k]:
            print(f"         {e}")
    if args.salida:
        json.dump(dict(grupos), io.open(args.salida, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(f"\nDetalle en {args.salida}")


if __name__ == "__main__":
    main()
