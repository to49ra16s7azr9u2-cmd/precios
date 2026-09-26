#!/usr/bin/env python3
"""Tres votos independientes para mover una ficha: origen, vecinos y precio.

POR QUÉ (26-sep-2026)
---------------------
Cada juez solo se equivoca de una forma distinta:
  - la categoría de la TIENDA (origen_categorias.py) no conoce nuestros
    cortes: sus «Accesorios e interiores» caen casi todos en Autopartes pero
    los cubrevolantes van en Autos y motos. Sola acertaba 5 de 60.
  - los VECINOS (las 25 fichas de nombre más parecido) arrastran los errores
    en bloque: si 30 copias del mismo mal título están juntas, se votan
    entre ellas.
  - el PRECIO no dice qué es la cosa, sólo si cabe en un lugar.
Cuando los tres apuntan al mismo sitio, el error de uno no alcanza.

LOS VOTOS
---------
  1. Origen: para cada categoría de la tienda (departamento del feed o rama
     de la url) se aprende del propio catálogo a qué categoría nuestra va.
     Vota sólo si la mayoría es aplastante (>= MANDATO, con >= MIN_ORIGEN
     fichas), y si la ficha tiene varias categorías de origen, todas deben
     votar lo mismo.
  2. Vecinos: >= MIN_VOTO de las K fichas más parecidas están en esa
     categoría; su subcategoría mayoritaria es el destino.
  3. Precio: cabe entre 1/4 y 4 veces la mediana de la subcategoría destino.
Y dos guardas contra votos que no son independientes (primera corrida,
26-sep-2026: 3,364 «coincidencias», casi todas cubrevolantes «para toyota
tercel 1988» mandados a Bobinas de encendido):
  - los vecinos se buscan sólo con lo que va ANTES de «para»: lo que sigue
    es el vehículo o el aparato compatible, no lo que la cosa es, y era
    justo eso lo que juntaba cubrevolantes con bobinas del mismo modelo.
  - la CABEZA del nombre (auditar_subcategorias_tienda.cabeza) veta: si esa
    palabra vive en su mayoría en la categoría actual, no se mueve.
Lo que está en el candado (clasificacion-a-mano.json) donde lo dejaron no
se toca.

SALIDA
------
--salida escribe el JSON de aplicar_movimientos.py ("cat | sub | cat2 | sub2").

USO
---
    python3 scripts/juez_origen.py --salida /tmp/juez-origen.json
    python3 scripts/aplicar_movimientos.py /tmp/juez-origen.json --todos --motivo "juez de origen"
"""
import argparse
import collections
import json
import math
import os
import random
import statistics
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import ROOT, load_catalog  # noqa: E402
from detectar_mal_clasificados import tokens  # noqa: E402
from origen_categorias import cargar, claves_de_oferta  # noqa: E402
from auditar_subcategorias_tienda import cabeza  # noqa: E402
import re  # noqa: E402

MANDATO = 0.9
MIN_ORIGEN = 30
K = 25
MIN_VOTO = 0.6
MIN_VOTO_SUB = 0.5
MAX_DF = 3000
CANDADO = os.path.join(ROOT, "data", "clasificacion-a-mano.json")


RX_PARA = re.compile(r"\s(para|compatible con|p/)\s", re.I)
MIN_CABEZA = 20
# Cortes que nuestra taxonomía hace a propósito y la tienda no: lo comercial
# aparte de lo doméstico, lo inteligente aparte de lo común, los tachones
# en su deporte y no en Calzado. El origen y los vecinos los cruzan juntos
# porque el título es casi el mismo; medido en la primera muestra (26-sep):
# freidoras industriales a Electrodomésticos, plafones wifi a Iluminación,
# tachones Pirma y Puma a Tenis para hombre, bocinas de auto a Bocinas.
CORTES_A_PROPOSITO = {
    ("Equipo comercial", "Electrodomésticos"), ("Equipo comercial", "Cocina y comedor"),
    ("Domótica y hogar inteligente", "Iluminación"), ("Domótica y hogar inteligente", "Bocinas"),
    ("Deportes y fitness", "Calzado"), ("Autos y motos", "Bocinas"), ("Autos y motos", "Autopartes"),
    ("Autopartes", "Autos y motos"), ("Videojuegos", "Juguetes"), ("Mascotas", "Muebles"),
    ("Electrodomésticos", "Cocina y comedor"), ("Suplementos", "Belleza y cuidado personal"),
}


def lo_que_es(nombre):
    """El nombre sin lo que viene después de «para»: el objeto, no su compatibilidad."""
    return RX_PARA.split(nombre or "", maxsplit=1)[0]


def precio(p):
    ps = [o.get("price") for o in p.get("offers") or [] if o.get("price")]
    return min(ps) if ps else None


def aprender(prods, mapa):
    """Del catálogo: las categorías de origen de cada ficha, cuántas fichas de
    cada categoría de origen caen en cada categoría nuestra, dónde vive cada
    cabeza de nombre, y el mandato (categoría de origen -> categoría nuestra
    cuando la mayoría es aplastante). También lo usa reportes_categoria.py."""
    claves = {}
    cuenta = collections.defaultdict(collections.Counter)
    por_cabeza = collections.defaultdict(collections.Counter)
    for i, p in enumerate(prods):
        h = cabeza(p.get("name"))
        if h:
            por_cabeza[h][p["category"]] += 1
        ks = set()
        for o in p.get("offers") or []:
            ks.update(claves_de_oferta(o, mapa))
        if ks:
            claves[i] = ks
            for k in ks:
                cuenta[k][p["category"]] += 1
    mandato = {}
    for k, c in cuenta.items():
        tot = sum(c.values())
        cat, n = c.most_common(1)[0]
        if tot >= MIN_ORIGEN and n / tot >= MANDATO:
            mandato[k] = cat
    return claves, cuenta, por_cabeza, mandato


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--salida")
    ap.add_argument("--muestras", type=int, default=40)
    args = ap.parse_args()

    mapa = cargar()
    data = load_catalog()
    prods = data["products"]
    candado = json.load(open(CANDADO, encoding="utf-8")) if os.path.exists(CANDADO) else {}

    # 1. qué categoría nuestra le toca a cada categoría de la tienda
    claves, cuenta, por_cabeza, mandato = aprender(prods, mapa)
    print(f"fichas con categoría de origen: {len(claves):,}; categorías de origen: {len(cuenta):,}; "
          f"con mandato: {len(mandato):,}")

    candidatas = []
    for i, ks in claves.items():
        p = prods[i]
        votos = {mandato[k] for k in ks if k in mandato}
        if len(votos) != 1:
            continue
        cat = votos.pop()
        if cat == p["category"]:
            continue
        h = cabeza(p.get("name"))
        ch = por_cabeza.get(h)
        if ch and sum(ch.values()) >= MIN_CABEZA and ch[p["category"]] / sum(ch.values()) >= 0.5:
            continue   # la palabra que dice qué es vive aquí
        if ch and sum(ch.values()) >= MIN_CABEZA and ch[cat] / sum(ch.values()) < 0.3:
            continue   # y en el destino casi no se usa («Espejo valery» a Sillas de oficina)
        if (p["category"], cat) in CORTES_A_PROPOSITO:
            continue
        fijo = candado.get(p["id"])
        if fijo and fijo[0] == p["category"] and (fijo[1] or None) == (p.get("subcategory") or None):
            continue
        candidatas.append((i, cat))
    print(f"el origen propone otra categoría para: {len(candidatas):,}")

    # 2. vecinos
    idx = collections.defaultdict(list)
    df = collections.Counter()
    for i, p in enumerate(prods):
        for w in set(tokens(p.get("name") or "")):
            df[w] += 1
            idx[w].append(i)
    n = len(prods)
    por_sub = collections.defaultdict(list)
    for p in prods:
        x = precio(p)
        if x and p.get("subcategory"):
            por_sub[(p["category"], p["subcategory"])].append(x)
    mediana = {k: statistics.median(v) for k, v in por_sub.items() if len(v) >= 10}
    por_cat = collections.defaultdict(list)
    for (c, _), v in por_sub.items():
        por_cat[c].extend(v)
    mediana_cat = {c: statistics.median(v) for c, v in por_cat.items() if len(v) >= 10}

    mover, no = [], collections.Counter()
    for i, cat in candidatas:
        p = prods[i]
        sc = collections.Counter()
        for w in set(tokens(lo_que_es(p.get("name")))):
            d = df[w]
            if 0 < d <= MAX_DF:
                peso = math.log(n / d)
                for j in idx[w]:
                    if j != i:
                        sc[j] += peso
        top = sc.most_common(K)
        if len(top) < 8:
            no["pocos vecinos"] += 1
            continue
        en_cat = [prods[j] for j, _ in top if prods[j]["category"] == cat]
        if len(en_cat) / len(top) < MIN_VOTO:
            no["los vecinos no están de acuerdo con el origen"] += 1
            continue
        subs = collections.Counter(q.get("subcategory") for q in en_cat if q.get("subcategory"))
        if not subs:
            no["sin subcategoría destino"] += 1
            continue
        s2, ns = subs.most_common(1)[0]
        # La subcategoría de los vecinos es menos confiable que la categoría
        # (espejos laterales mandados a «Faros», un juego de Xbox a
        # «Controles para Xbox»): sólo se usa si la mitad de los vecinos
        # está ahí. Si no, se mueve la categoría y completar_subcategorias.py
        # decide la subcategoría con su modelo.
        if ns / len(top) < MIN_VOTO_SUB:
            s2 = None
        m2, x = (mediana.get((cat, s2)) if s2 else mediana_cat.get(cat)), precio(p)
        if not m2 or not x or not (m2 / 4 <= x <= m2 * 4):
            no["el precio no cabe en el destino"] += 1
            continue
        mover.append((p, cat, s2))

    print(f"los tres votos coinciden: {len(mover):,}")
    for k, v in no.most_common():
        print(f"  no: {v:7,}  {k}")
    grupos = collections.defaultdict(list)
    for p, c2, s2 in mover:
        grupos[f"{p['category']} | {p.get('subcategory') or None} | {c2} | {s2}"].append(p["id"])
    for k, v in sorted(grupos.items(), key=lambda kv: -len(kv[1]))[:30]:
        print(f"  {len(v):5}  {k}")
    random.seed(11)
    for p, c2, s2 in random.sample(mover, min(args.muestras, len(mover))):
        print(f"   ${precio(p):9,.0f}  {p['category']}/{p.get('subcategory')} -> {c2}/{s2} | {p['name'][:70]}")
    if args.salida:
        json.dump(grupos, open(args.salida, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(f"-> {args.salida}")


if __name__ == "__main__":
    main()
