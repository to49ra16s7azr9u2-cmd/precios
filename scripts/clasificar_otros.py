#!/usr/bin/env python3
"""Clasifica lo que estaba sin clasificar (24-sep-2026).

Tres grupos, medidos ese día sobre 461,945 fichas:

  A. La categoría «Otros» (7,845): salvo «Varios», cada subcategoría tiene
     su casa (reubicar_otros.py). Se mueve el grupo entero con sus
     excepciones (el arrancador de batería que estaba en Estaciones de
     energía va a Autos; la regadera que estaba en Baño, a Herramientas).
  B. «Otros / Varios» (661): ficha por ficha, con los tres jueces del
     híbrido: el modelo del catálogo prefiere una categoría por MARGEN nats,
     el título arranca como esa categoría y los vecinos la respaldan. Lo que
     no pasa los tres se queda en Varios.
  C. Fichas sin subcategoría o en una subcategoría comodín dentro de una
     categoría real (~3,600): primero el repartidor del clasificador para
     esa categoría; si no reconoce el título, el modelo de subcategorías de
     esa categoría, pero sólo si los vecinos de la misma categoría están
     mayoritariamente en esa subcategoría. La CATEGORÍA no se toca.

Lo movido se anota en el candado manual (data/clasificacion-a-mano.json)
cuando la ficha ya tenía candado en su lugar viejo, para que el candado no
la considere «fuera de su sitio».

USO
---
    python3 scripts/clasificar_otros.py              # sólo informa
    python3 scripts/clasificar_otros.py --aplicar
"""
import argparse
import collections
import io
import json
import os
import random
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import load_catalog, save_catalog  # noqa: E402
import clasificar_captura_perifericos as C  # noqa: E402
import reubicar_otros as R  # noqa: E402
from vecinos_catalogo import Vecinos, MIN_VOTO  # noqa: E402

CANDADO = os.path.join(AQUI, "..", "data", "clasificacion-a-mano.json")
COMODIN = {"Otros", "Varios", "Otro", "Otros juegos", "Otro calzado", "Otros accesorios gamer"}
MARGEN = 8.0            # nats, como el híbrido
MARGEN_SUB = 8.0        # nats entre la mejor subcategoría y la segunda
VOTO_SUB = 0.7          # con 4 nats y 50% de vecinos acertaba ~72% (muestra a mano)


def sub_por_repartidor(p, cat):
    d = C._decidir_base({"asin": p["id"], "title": p.get("name") or "", "_forzar": (cat, None, None)})
    s = d.get("subcategory") if d.get("estado") == "alta" and d.get("category") == cat else None
    return None if s in COMODIN else s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--muestras", default=None, help="json con muestras para revisar a mano")
    args = ap.parse_args()

    data = load_catalog()
    prods = data["products"]
    modelo = C.ModeloCatalogo()
    vec = modelo.vecinos
    subs_de = {c["id"]: [s["id"] for s in (c.get("subcategories") or [])] for c in data["categories"]}
    sub_de_id = {p["id"]: p.get("subcategory") for p in prods}

    cambios = []          # (p, cat_nueva, sub_nueva, grupo)
    quedan = collections.Counter()
    for p in prods:
        cat, sub = p.get("category"), p.get("subcategory")
        tn = C.T(p.get("name") or "")
        # D: agarraderas de celular que se quedó una regla de teléfonos (o
        # cualquier otra: «Popsockets ... patas de perro» en Mascotas).
        if R.AGARRE.search(tn) and (cat in ("Celulares", "Otros") or re.search(r'popsocket|pop ?grip', tn)) \
                and sub != R.SOPORTES:
            cambios.append((p, "Celulares", R.SOPORTES, "D agarraderas"))
            continue
        if cat == "Otros" and sub != "Varios":
            r = R.reubicar(cat, sub, tn)
            if r:
                c2, s2 = r
                if s2 is None:
                    s2 = sub_por_repartidor(p, c2)
                cambios.append((p, c2, s2, "A"))
            else:
                quedan["A sin destino"] += 1
            continue
        if cat == "Otros":            # Varios
            prop = modelo.categoria(p.get("name") or "")
            if not prop:
                quedan["B el modelo no decide"] += 1
                continue
            c2 = prop[0]
            if c2 == "Otros" or not C.es_coherente(p.get("name") or "", c2, p.get("brand") or ""):
                quedan["B el título no arranca como la categoría"] += 1
                continue
            if not vec.respalda(c2, "Otros", pid=p["id"]):
                quedan["B los vecinos no la respaldan"] += 1
                continue
            s2 = sub_por_repartidor(p, c2) or prop[1]
            cambios.append((p, c2, s2, "B"))
            continue
        if sub and sub not in COMODIN:
            continue
        # C: categoría real, sin subcategoría o en comodín
        s2 = sub_por_repartidor(p, cat)
        via = "repartidor"
        if not s2 and cat in modelo.subs:
            ps = modelo.subs[cat].puntajes(modelo._tokens(p.get("name")))
            orden = sorted(((s, v) for s, v in ps.items() if s not in COMODIN), key=lambda kv: -kv[1])
            if orden and (len(orden) == 1 or orden[0][1] - orden[1][1] >= MARGEN_SUB):
                cand = orden[0][0]
                votos = collections.Counter()
                for q, w in vec.mas_parecidas(pid=p["id"]):
                    if vec.cat.get(q) == cat:
                        votos[sub_de_id.get(q)] += w
                tot = sum(votos.values())
                if tot and votos[cand] / tot >= VOTO_SUB:
                    s2, via = cand, "modelo+vecinos"
        if s2 and s2 != sub:
            cambios.append((p, cat, s2, "C " + via))
        else:
            quedan["C sin subcategoría segura"] += 1

    por = collections.Counter(g for _, _, _, g in cambios)
    print(f"cambios: {len(cambios):,}  {dict(por)}")
    for k, n in quedan.most_common():
        print(f"  se quedan: {n:6,}  {k}")
    grupos = collections.Counter((p.get("category"), p.get("subcategory"), c2, s2) for p, c2, s2, _ in cambios)
    for (c, s, c2, s2), n in grupos.most_common(45):
        print(f"{n:6}  {c} / {s}  ->  {c2} / {s2}")
    if args.muestras:
        random.seed(5)
        out = {}
        for g in sorted(por):
            xs = [x for x in cambios if x[3] == g]
            out[g] = [[x[0]["name"][:100], x[0].get("category"), x[0].get("subcategory"), x[1], x[2]]
                      for x in random.sample(xs, min(40, len(xs)))]
        json.dump(out, open(args.muestras, "w"), ensure_ascii=False, indent=1)
    if not args.aplicar:
        print("\n(sin --aplicar: no se tocó el catálogo)")
        return

    # Categoría nueva y subcategorías nuevas en data.categories
    cats = {c["id"]: c for c in data["categories"]}
    if R.SOLAR not in cats:
        data["categories"].append({"id": R.SOLAR, "name": R.SOLAR, "icon": "sun", "subcategories": []})
        cats[R.SOLAR] = data["categories"][-1]
    necesarias = collections.defaultdict(list)
    for _, c2, s2, _ in cambios:
        if s2 and s2 not in necesarias[c2]:
            necesarias[c2].append(s2)
    for c2, ss in necesarias.items():
        existentes = {s["id"] for s in cats[c2].get("subcategories") or []}
        orden = R.SUBS_SOLAR if c2 == R.SOLAR else ss
        for s2 in orden:
            if s2 in ss and s2 not in existentes:
                cats[c2].setdefault("subcategories", []).append(
                    {"id": s2, "name": s2, "icon": R.ICONO.get(c2, cats[c2].get("icon") or "box")})
    candado = json.load(io.open(CANDADO, encoding="utf-8"))
    for p, c2, s2, _ in cambios:
        viejo = candado.get(p["id"])
        if viejo and viejo[0] == p.get("category"):
            candado[p["id"]] = [c2, s2]
        if c2 != p.get("category"):
            p["image"] = R.ICONO.get(c2, cats[c2].get("icon") or p.get("image"))
        p["category"], p["subcategory"] = c2, s2
    # «Otros» deja en su lista sólo lo que todavía tiene fichas.
    usadas = {p.get("subcategory") for p in prods if p.get("category") == "Otros"}
    cats["Otros"]["subcategories"] = [s for s in cats["Otros"]["subcategories"] if s["id"] in usadas]
    save_catalog(data)
    with io.open(CANDADO, "w", encoding="utf-8") as f:
        json.dump(candado, f, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    print(f"Guardado: {len(cambios):,} fichas.")


if __name__ == "__main__":
    main()
