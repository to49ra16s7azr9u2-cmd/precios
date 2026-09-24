#!/usr/bin/env python3
"""Los 20 más baratos y los 20 más caros de cada categoría, otra vez por los
tres filtros (24-sep-2026, a pedido del usuario: «各カテゴリのmasbarato上位
二十件、mascaroの上位二十件もフィルターにかけ直してみてください»).

POR QUÉ LOS EXTREMOS
--------------------
Es lo primero que ve quien ordena por precio, y es donde se juntan los
errores: arriba del «Más caros» de Celulares estaban un Surface Studio, un
triciclo y un NAS; abajo del «Más baratos», fundas y refacciones. Un error
en medio de 3,000 fichas casi no se ve; uno en el primer renglón, sí.

CÓMO
----
Mismo orden que la página (js/app.js sortedProducts): sólo fichas con
página, precio «desde» de min_price(), y en «Más baratos» las atípicas
(atipicos.py) al final. A cada una se le preguntan los tres jueces:

  1. la regla (clasificar_captura_perifericos.decidir sobre el título),
  2. el modelo del catálogo (categoría con más puntaje y su margen),
  3. los vecinos (la categoría con más peso entre las 25 más parecidas).

Se marca la ficha cuando al menos DOS jueces coinciden en una categoría
distinta de la actual, o uno solo muy seguro (modelo con 8 nats o más,
vecinos con 60% o más). Con --aplicar se mueven sólo las que están en el
archivo --aprobadas (revisadas a mano: id -> [categoría, subcategoría]) y
quedan en el candado manual.

USO
---
    python3 scripts/revisar_extremos.py --salida extremos.json
    python3 scripts/revisar_extremos.py --aprobadas aprobadas.json --aplicar
"""
import argparse
import collections
import io
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import load_catalog, save_catalog  # noqa: E402

CANDADO = os.path.join(AQUI, "..", "data", "clasificacion-a-mano.json")
N = 20


def extremos(prods):
    import generate_seo_pages as G
    from atipicos import marcar
    atip = marcar(prods)
    por_cat = collections.defaultdict(list)
    for p in prods:
        if G.tiene_pagina(p) and p.get("category"):
            try:
                por_cat[p["category"]].append((G.min_price(p), p))
            except (ValueError, KeyError):
                continue
    out = {}
    for cat, xs in por_cat.items():
        baratos = sorted(xs, key=lambda x: (x[1]["id"] in atip, x[0]))[:N]
        caros = sorted(xs, key=lambda x: -x[0])[:N]
        out[cat] = [("barato", pr, p) for pr, p in baratos] + [("caro", pr, p) for pr, p in caros]
    return out


def jueces(p, modelo):
    import clasificar_captura_perifericos as C
    nombre = p.get("name") or ""
    d = C.decidir({"asin": p["id"], "title": nombre})
    regla = (d.get("category"), d.get("subcategory")) if d.get("estado") == "alta" else (None, None)
    ts = modelo._tokens(nombre)
    pt = modelo.m.puntajes(ts) if ts else {}
    orden = sorted(pt.items(), key=lambda kv: -kv[1])
    mod = orden[0][0] if orden else None
    margen = (pt.get(mod, 0) - pt.get(p["category"], 0)) if mod and p["category"] in pt else 0.0
    vv = modelo.vecinos.votos(pid=p["id"])
    vec = max(vv, key=vv.get) if vv else None
    return regla, mod, margen, vec, vv.get(vec, 0) if vec else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida")
    ap.add_argument("--aprobadas")
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    data = load_catalog()
    prods = data["products"]

    if args.aplicar:
        aprobadas = json.load(open(args.aprobadas, encoding="utf-8"))
        cats = {c["id"]: c for c in data["categories"]}
        candado = json.load(io.open(CANDADO, encoding="utf-8"))
        import reubicar_otros as R
        n = 0
        for p in prods:
            if p["id"] in aprobadas:
                c2, s2 = aprobadas[p["id"]]
                assert c2 in cats and s2 in {s["id"] for s in cats[c2].get("subcategories") or []}, (p["id"], c2, s2)
                if p["category"] != c2:
                    p["image"] = R.ICONO.get(c2, cats[c2].get("icon") or p.get("image"))
                p["category"], p["subcategory"] = c2, s2
                candado[p["id"]] = [c2, s2]
                n += 1
        save_catalog(data)
        with io.open(CANDADO, "w", encoding="utf-8") as f:
            json.dump(candado, f, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        print(f"Guardado: {n} fichas movidas (y en el candado manual).")
        return

    import clasificar_captura_perifericos as C
    modelo = C.ModeloCatalogo(prods)
    marcadas, revisadas = [], 0
    for cat, xs in sorted(extremos(prods).items()):
        for lado, pr, p in xs:
            revisadas += 1
            regla, mod, margen, vec, voto = jueces(p, modelo)
            otras = collections.Counter(c for c in (regla[0], mod, vec) if c and c != cat)
            if not otras:
                continue
            dest, k = otras.most_common(1)[0]
            # Un solo juez en contra cuenta sólo si está muy seguro: el
            # modelo con 8 nats o más, o los vecinos con 60% o más.
            if k < 2 and not ((mod == dest and margen >= 8) or (vec == dest and voto >= 0.6)):
                continue
            marcadas.append({"id": p["id"], "lado": lado, "precio": pr, "cat": cat,
                             "sub": p.get("subcategory"), "nombre": p.get("name"),
                             "propuesta": dest, "votos": k,
                             "regla": regla, "modelo": [mod, round(margen, 1)],
                             "vecinos": [vec, round(voto, 2)]})
    print(f"revisadas: {revisadas:,}; marcadas: {len(marcadas)}")
    for m in marcadas:
        print(f"{m['lado']:6} {m['cat'][:22]:22} -> {m['propuesta'][:22]:22} ({m['votos']}) "
              f"${m['precio']:>9,.0f} | {m['nombre'][:80]}")
    if args.salida:
        json.dump(marcadas, open(args.salida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
