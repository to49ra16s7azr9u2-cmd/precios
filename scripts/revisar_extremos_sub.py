#!/usr/bin/env python3
"""Los 20 más baratos y los 20 más caros de CADA SUBCATEGORÍA, por los tres
jueces (26-sep-2026, pedido del usuario: «全小カテゴリのMas baratoトップ２０、
Mas caroトップ２０は確認し直してください»).

POR QUÉ
-------
revisar_extremos.py miraba por categoría y solo fichas con página propia;
el usuario encontró los errores en la lista de una SUBCATEGORÍA, que muestra
todas las fichas (también las de un vendedor): en Celulares/Resistentes,
ordenado por precio, un libro («Adicción al celular»), otro libro con marca
Xiaomi, fundas con nombre de teléfono; en Laptops, mochilas y una tarjeta
madre.

CÓMO
----
Mismo orden que la lista de la SPA (sortedProducts de js/app.js): «Más
baratos» con las atípicas (campo «a») al final, «Más caros» de mayor a menor.
A cada ficha se le preguntan los tres jueces de revisar_extremos.py (regla,
modelo del catálogo --que ya suma los ejemplos verificados--, vecinos) y,
dentro de la misma categoría, dos jueces de subcategoría (la regla y el
modelo de subcategorías). Se marca:
  - CATEGORÍA: dos jueces coinciden en otra categoría, o uno muy seguro.
  - SUBCATEGORÍA: la regla y el modelo coinciden en otra subcategoría con
    nombre (no comodín) de la misma categoría.
--salida escribe los marcados agrupados (origen -> destino) para revisar;
--aplicar mueve los ids aprobados (--aprobadas: id -> [cat, sub]), los deja
en el candado manual y los suma a los ejemplos verificados.

USO
---
    python3 scripts/revisar_extremos_sub.py --salida /tmp/ext.json
    python3 scripts/revisar_extremos_sub.py --aprobadas aprobadas.json --aplicar
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
MIN_FICHAS = 5


def extremos(prods):
    import generate_seo_pages as G
    grupos = collections.defaultdict(list)
    for p in prods:
        if not p.get("category") or not p.get("subcategory"):
            continue
        try:
            pr = G.min_price(p)
        except (ValueError, KeyError, TypeError):
            continue
        if pr and pr > 0:
            grupos[(p["category"], p["subcategory"])].append((pr, p))
    out = {}
    for k, xs in grupos.items():
        if len(xs) < MIN_FICHAS:
            continue
        baratos = sorted(xs, key=lambda x: (1 if x[1].get("a") else 0, x[0]))[:N]
        caros = sorted(xs, key=lambda x: -x[0])[:N]
        vistos = set()
        filas = []
        for lado, lista in (("barato", baratos), ("caro", caros)):
            for pr, p in lista:
                if p["id"] not in vistos:
                    vistos.add(p["id"])
                    filas.append((lado, pr, p))
        out[k] = filas
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--salida")
    ap.add_argument("--aprobadas")
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()
    data = load_catalog()
    prods = data["products"]

    if args.aplicar:
        import ejemplos_verificados as EV
        aprobadas = json.load(open(args.aprobadas, encoding="utf-8"))
        cats = {c["id"]: c for c in data["categories"]}
        candado = json.load(io.open(CANDADO, encoding="utf-8"))
        n, ejs = 0, []
        for p in prods:
            if p["id"] in aprobadas:
                c2, s2 = aprobadas[p["id"]]
                assert c2 in cats and s2 in {s["id"] for s in cats[c2].get("subcategories") or []}, (p["id"], c2, s2)
                if p["category"] != c2:
                    p["image"] = cats[c2].get("icon") or p.get("image")
                p["category"], p["subcategory"] = c2, s2
                candado[p["id"]] = [c2, s2]
                ejs.append({"nombre": p.get("name"), "cat": c2, "sub": s2})
                n += 1
        save_catalog(data)
        with io.open(CANDADO, "w", encoding="utf-8") as f:
            json.dump(candado, f, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        m = EV.agregar(ejs, "revisión de extremos por subcategoría (26-sep)")
        print(f"Guardado: {n} fichas movidas (candado manual); {m} ejemplos verificados nuevos.")
        return

    import clasificar_captura_perifericos as C
    from partir_genericas import es_generica
    modelo = C.ModeloCatalogo(prods)
    marcadas, revisadas = [], 0
    ext = extremos(prods)
    print(f"subcategorías: {len(ext):,}", flush=True)
    for (cat, sub), filas in sorted(ext.items()):
        for lado, pr, p in filas:
            revisadas += 1
            nombre = p.get("name") or ""
            d = C.decidir({"asin": p["id"], "title": nombre})
            regla = (d.get("category"), d.get("subcategory")) if d.get("estado") == "alta" else (None, None)
            ts = modelo._tokens(nombre)
            pt = modelo.m.puntajes(ts) if ts else {}
            mod = max(pt, key=pt.get) if pt else None
            margen = (pt.get(mod, 0) - pt.get(cat, 0)) if mod and cat in pt else 0.0
            vv = modelo.vecinos.votos(pid=p["id"])
            vec = max(vv, key=vv.get) if vv else None
            voto = vv.get(vec, 0) if vec else 0.0
            otras = collections.Counter(c for c in (regla[0], mod, vec) if c and c != cat)
            prop = None
            if otras:
                dest, k = otras.most_common(1)[0]
                if k >= 2 or (mod == dest and margen >= 8) or (vec == dest and voto >= 0.6):
                    dsub = regla[1] if regla[0] == dest else None
                    if not dsub and dest in modelo.subs:
                        sp = modelo.subs[dest].puntajes(ts)
                        sp = {s: v for s, v in sp.items() if not es_generica(dest, s)}
                        dsub = max(sp, key=sp.get) if sp else None
                    prop = ("categoría", dest, dsub, k)
            if not prop and regla[0] == cat and regla[1] and regla[1] != sub and not es_generica(cat, regla[1]) \
                    and cat in modelo.subs:
                sp = modelo.subs[cat].puntajes(ts)
                if sp and max(sp, key=sp.get) == regla[1]:
                    prop = ("subcategoría", cat, regla[1], 2)
            if prop:
                marcadas.append({"id": p["id"], "lado": lado, "precio": pr, "cat": cat, "sub": sub,
                                 "nombre": nombre, "nivel": prop[0], "a_cat": prop[1], "a_sub": prop[2],
                                 "votos": prop[3], "regla": regla, "modelo": [mod, round(margen, 1)],
                                 "vecinos": [vec, round(voto, 2)]})
        if revisadas % 5000 < len(filas):
            print(f"  {revisadas:,} revisadas, {len(marcadas):,} marcadas", flush=True)
    print(f"revisadas: {revisadas:,}; marcadas: {len(marcadas):,}")
    grupos = collections.Counter(f"{m['cat']}/{m['sub']} -> {m['a_cat']}/{m['a_sub']}" for m in marcadas)
    for g, n in grupos.most_common(40):
        print(f"{n:5}  {g}")
    if args.salida:
        json.dump(marcadas, open(args.salida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
