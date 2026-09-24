#!/usr/bin/env python3
"""Clasifica lo último que quedaba sin clasificar, reentrenando el modelo en
cada ronda (24-sep-2026, a pedido del usuario: «そのつど学習モデルもアップデ
ートさせていってください»).

QUÉ QUEDABA
-----------
Después de clasificar_otros.py: 655 fichas en «Otros / Varios» y 527 en
categorías reales pero sin subcategoría (o en un comodín). Son las difíciles:
ni las reglas ni el modelo con los umbrales del híbrido estaban seguros.

CÓMO
----
1. Los grupos que se ven a simple vista dentro de Varios (cuadros,
   matamosquitos, material de laboratorio, tripiés, portacelulares) van por
   regla (reubicar_otros.reubicar_varios).
2. Lo demás, por rondas. En cada ronda se ENTRENA de nuevo el modelo del
   catálogo (categoría y subcategoría) y los vecinos con el catálogo tal como
   quedó después de la ronda anterior: lo que se acaba de clasificar ya
   cuenta como ejemplo para lo que sigue. Una ficha rara que se parece a
   otra rara que ya encontró casa la sigue en la ronda siguiente.
3. Se empieza con los umbrales del híbrido (8 nats, vecinos 50%, título
   coherente) y sólo cuando una ronda ya no clasifica nada se baja un
   escalón, hasta 2 nats. Lo que ni así tiene margen se queda donde está:
   un escalón sin margen acertaba la mitad. Cada ficha queda anotada con el
   escalón que la clasificó (data/clasificacion-restantes.json).

USO
---
    python3 scripts/clasificar_restantes.py              # sólo informa
    python3 scripts/clasificar_restantes.py --aplicar
"""
import argparse
import collections
import datetime
import io
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import load_catalog, save_catalog  # noqa: E402
import clasificar_captura_perifericos as C  # noqa: E402
import reubicar_otros as R  # noqa: E402

CANDADO = os.path.join(AQUI, "..", "data", "clasificacion-a-mano.json")
REGISTRO = os.path.join(AQUI, "..", "data", "clasificacion-restantes.json")
COMODIN = {"Otros", "Varios", "Otro", "Otros juegos", "Otro calzado", "Otros accesorios gamer"}

# (margen en nats sobre la segunda, fracción de vecinos, exigir título coherente)
# Un quinto escalón sin margen se probó y se quitó: acertaba ~50% en una
# muestra a mano (el mueble de baño a «Alacenas de cocina», el aparador a
# «Escritorios de oficina»), casi siempre porque a esas fichas les faltaba
# una subcategoría propia -- que ahora ponen las reglas de grupo
# (reubicar_otros.por_grupo) antes de las rondas.
# El cuarto (2 nats, sin título coherente) cambiaba de CATEGORÍA con ~57% de
# aciertos en otra muestra (fundas de parrilla a «Estufas», miniaturas de
# adorno a «Instrumentos musicales»): tampoco entra.
ESCALONES_CAT = [(8, 0.5, True), (6, 0.5, True), (4, 0.45, True)]
# (margen en nats sobre la segunda subcategoría, fracción de vecinos de la misma categoría)
# El cuarto escalón de subcategoría (2 nats, 45% de vecinos) acertaba ~57%
# en una muestra a mano (hidrolavadoras a «Jardinería», un libro a «Juegos
# Xbox»): se aplicó el 24-sep y se deshizo. Hasta el tercero, ~80%.
ESCALONES_SUB = [(8, 0.7), (6, 0.6), (4, 0.5)]


def pendientes(prods):
    v = [p for p in prods if p.get("category") == "Otros"]
    n = [p for p in prods if p.get("category") not in (None, "Otros")
         and (not p.get("subcategory") or p.get("subcategory") in COMODIN)]
    return v, n


def mejor_sub(modelo, cat, ts, excluir=COMODIN):
    ps = modelo.subs[cat].puntajes(ts) if cat in modelo.subs else {}
    orden = sorted(((s, x) for s, x in ps.items() if s and s not in excluir), key=lambda kv: -kv[1])
    if not orden:
        return None, 0.0
    return orden[0][0], (orden[0][1] - orden[1][1]) if len(orden) > 1 else 99.0


def votos_sub(modelo, cat, pid, titulo, sub_de):
    v = collections.Counter()
    for q, w in modelo.vecinos.mas_parecidas(titulo=titulo):
        if q != pid and modelo.vecinos.cat.get(q) == cat:
            v[sub_de.get(q)] += w
    tot = sum(v.values())
    return {s: x / tot for s, x in v.items()} if tot else {}


def sub_repartidor(p, cat):
    d = C._decidir_base({"asin": p["id"], "title": p.get("name") or "", "_forzar": (cat, None, None)})
    s = d.get("subcategory") if d.get("estado") == "alta" and d.get("category") == cat else None
    return None if s in COMODIN else s


def ronda(prods, modelo, e_cat, e_sub):
    """Propuestas de UNA ronda con el modelo recién entrenado."""
    m_cat, v_cat, coh = ESCALONES_CAT[e_cat]
    m_sub, v_sub = ESCALONES_SUB[e_sub]
    sub_de = {p["id"]: p.get("subcategory") for p in prods}
    varios, sin_sub = pendientes(prods)
    out = []
    for p in varios:
        nombre = p.get("name") or ""
        ts = modelo._tokens(nombre)
        if not ts:
            continue
        pt = {c: x for c, x in modelo.m.puntajes(ts).items() if c != "Otros"}
        if not pt:
            continue
        orden = sorted(pt.items(), key=lambda kv: -kv[1])
        cat = orden[0][0]
        margen = orden[0][1] - orden[1][1] if len(orden) > 1 else 99.0
        if margen < m_cat:
            continue
        if coh and not C.es_coherente(nombre, cat, p.get("brand") or ""):
            continue
        vv = modelo.vecinos.votos(titulo=nombre)
        if v_cat and not (vv.get(cat, 0) >= v_cat and vv.get(cat, 0) >= max(vv.values(), default=0)):
            continue
        sub = sub_repartidor(p, cat) or mejor_sub(modelo, cat, ts)[0]
        out.append((p, cat, sub, f"categoría escalón {e_cat + 1}"))
    for p in sin_sub:
        cat, nombre = p["category"], p.get("name") or ""
        ts = modelo._tokens(nombre)
        if not ts:
            continue
        sub, margen = mejor_sub(modelo, cat, ts)
        if not sub or margen < m_sub:
            continue
        if v_sub:
            vs = votos_sub(modelo, cat, p["id"], nombre, sub_de)
            if vs.get(sub, 0) < v_sub:
                continue
        out.append((p, cat, sub, f"subcategoría escalón {e_sub + 1}"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--muestras")
    args = ap.parse_args()

    data = load_catalog()
    prods = data["products"]
    cats = {c["id"]: c for c in data["categories"]}
    hechos = []   # (p, cat_vieja, sub_vieja, cat, sub, via)

    # 1. Reglas para los grupos claros de Varios
    for p in prods:
        if p.get("category") == "Otros" and p.get("subcategory") == "Varios":
            r = R.reubicar_varios(C.T(p.get("name") or ""))
            if r:
                hechos.append((p, p["category"], p.get("subcategory"), r[0], r[1], "regla"))
                p["category"], p["subcategory"] = r
    # 1b. Grupos a los que les faltaba subcategoría (muebles de baño,
    # aparadores, power banks archivados en Cargadores...)
    for p in prods:
        cat, sub = p.get("category"), p.get("subcategory")
        if cat == "Otros" or not sub or sub in COMODIN:
            r = R.por_grupo(cat, C.T(p.get("name") or ""))
            if r:
                c2, s2 = r
                s2 = s2 or sub_repartidor(p, c2)
                if s2:
                    hechos.append((p, cat, sub, c2, s2, "regla de grupo"))
                    p["category"], p["subcategory"] = c2, s2
    print(f"regla: {len(hechos)}")

    # 2. Rondas con el modelo reentrenado cada vez
    e_cat = e_sub = 0
    n_ronda = 0
    while True:
        varios, sin_sub = pendientes(prods)
        if not varios and not sin_sub:
            break
        n_ronda += 1
        modelo = C.ModeloCatalogo(prods)
        props = ronda(prods, modelo, e_cat, e_sub)
        print(f"ronda {n_ronda}: pendientes {len(varios)} Varios + {len(sin_sub)} sin subcategoría; "
              f"escalón categoría {e_cat + 1}, subcategoría {e_sub + 1}: se clasifican {len(props)}")
        if props:
            for p, cat, sub, via in props:
                hechos.append((p, p["category"], p.get("subcategory"), cat, sub, f"ronda {n_ronda}, {via}"))
                p["category"], p["subcategory"] = cat, sub
            continue
        # Nada nuevo con estos umbrales: se baja un escalón donde todavía hay pendientes.
        subio = False
        if varios and e_cat < len(ESCALONES_CAT) - 1:
            e_cat += 1
            subio = True
        if sin_sub and e_sub < len(ESCALONES_SUB) - 1:
            e_sub += 1
            subio = True
        if not subio:
            break

    varios, sin_sub = pendientes(prods)
    print(f"\nclasificadas: {len(hechos):,}; siguen sin clasificar: {len(varios)} Varios + {len(sin_sub)} sin subcategoría")
    por_via = collections.Counter(h[5].split(", ")[-1] for h in hechos)
    for k, n in sorted(por_via.items()):
        print(f"  {n:5}  {k}")
    grupos = collections.Counter((h[1], h[2], h[3], h[4]) for h in hechos)
    for (c, s, c2, s2), n in grupos.most_common(30):
        print(f"{n:5}  {c} / {s}  ->  {c2} / {s2}")
    if args.muestras:
        json.dump([[h[0]["name"][:100], h[1], h[2], h[3], h[4], h[5]] for h in hechos],
                  open(args.muestras, "w"), ensure_ascii=False, indent=1)
    if not args.aplicar:
        print("\n(sin --aplicar: no se tocó el catálogo)")
        return

    for _, _, _, c2, s2, _ in hechos:
        existentes = {s["id"] for s in cats[c2].get("subcategories") or []}
        if s2 and s2 not in existentes:
            cats[c2].setdefault("subcategories", []).append(
                {"id": s2, "name": s2, "icon": cats[c2].get("icon") or "box"})
    candado = json.load(io.open(CANDADO, encoding="utf-8"))
    registro = {}
    for p, c0, s0, c2, s2, via in hechos:
        if candado.get(p["id"], [None])[0] == c0:
            candado[p["id"]] = [c2, s2]
        if c2 != c0:
            p["image"] = R.ICONO.get(c2, cats[c2].get("icon") or p.get("image"))
        registro[p["id"]] = {"de": [c0, s0], "a": [c2, s2], "via": via,
                             "fecha": datetime.date.today().isoformat()}
    usadas = {p.get("subcategory") for p in prods if p.get("category") == "Otros"}
    cats["Otros"]["subcategories"] = [s for s in cats["Otros"]["subcategories"] if s["id"] in usadas]
    save_catalog(data)
    with io.open(CANDADO, "w", encoding="utf-8") as f:
        json.dump(candado, f, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    with io.open(REGISTRO, "w", encoding="utf-8") as f:
        json.dump(registro, f, ensure_ascii=False, indent=1, sort_keys=True)
    print(f"Guardado: {len(hechos):,} fichas.")


if __name__ == "__main__":
    main()
