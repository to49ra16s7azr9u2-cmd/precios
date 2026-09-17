#!/usr/bin/env python3
"""Busca fichas que están en la categoría o subcategoría equivocada.

Pasa el NOMBRE de cada ficha por el clasificador de capturas
(clasificar_captura_perifericos.py: FUERA -> CABECERA -> REGLAS -> sub_*) y
compara con lo que la ficha tiene guardado. Una diferencia no es
automáticamente un error --el clasificador también se equivoca--, pero un
grupo grande de diferencias con el mismo destino ("Consolas -> Software:
163") casi siempre lo es, y es lo que este informe pone arriba.

    python3 scripts/auditar_subcategorias.py                 # informe
    python3 scripts/auditar_subcategorias.py --salida x.json # + detalle
    python3 scripts/auditar_subcategorias.py --categoria Videojuegos
"""
import argparse
import collections
import io
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import load_catalog  # noqa: E402


def cargar_clasificador():
    ruta = os.path.join(AQUI, "clasificar_captura_perifericos.py")
    src = io.open(ruta, encoding="utf-8").read()
    head = src[:src.index("\ncaptura = json.load")]
    argv, sys.argv = sys.argv, ["x", "/dev/null", "/dev/null"]
    g = {"__file__": ruta}
    exec(compile(head, "clasificador", "exec"), g)
    sys.argv = argv
    # El reparto de subcategoría, tal como lo hace el bloque final del
    # clasificador: se lee de su propio código para no copiarlo a mano.
    cola = src[src.index("\ncaptura = json.load"):]
    despacho = {}
    for cat, fn, o_sub in re.findall(r"cat == '([^']+)': sub = (sub_\w+)\(tn\)( or sub)?", cola):
        despacho[cat] = (g[fn], bool(o_sub))
    return g, despacho


def clasificar(g, despacho, titulo):
    """(categoría, subcategoría, motivo) que el clasificador daría hoy."""
    tn = g["T"](titulo)
    for rx, m in g["FUERA"]:
        if rx.search(tn):
            return None, None, "fuera: " + m
    for rx, m in g["CABECERA"]:
        if rx.search(tn[:55]):
            return None, None, "fuera: " + m
    hit = next((v for rx, v in g["REGLAS"] if rx.search(tn)), None)
    if not hit:
        return None, None, "no encaja"
    cat, sub, _ = hit
    fn = despacho.get(cat)
    if fn:
        s = fn[0](tn)
        sub = (s or sub) if fn[1] else s
    return cat, sub, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--categoria")
    ap.add_argument("--salida")
    ap.add_argument("--min", type=int, default=20, help="grupos menores no se imprimen")
    args = ap.parse_args()
    g, despacho = cargar_clasificador()
    products = load_catalog()["products"]
    if args.categoria:
        products = [p for p in products if p["category"] == args.categoria]
    grupos = collections.defaultdict(list)
    por_cat = collections.Counter()
    for p in products:
        cat, sub, motivo = clasificar(g, despacho, p.get("name", ""))
        por_cat[p["category"]] += 1
        if motivo:
            clave = (p["category"], p.get("subcategory"), "(" + motivo.split(":")[0] + ")", motivo)
        elif cat != p["category"]:
            clave = (p["category"], p.get("subcategory"), cat, sub)
        elif sub and sub != p.get("subcategory"):
            clave = (p["category"], p.get("subcategory"), cat, sub)
        else:
            continue
        grupos[clave].append(p)
    filas = sorted(grupos.items(), key=lambda kv: -len(kv[1]))
    print(f"Fichas revisadas: {len(products):,}. Con diferencia: {sum(len(v) for v in grupos.values()):,}\n")
    print("== Cambio de CATEGORÍA (el clasificador la pondría en otra)")
    for (c, s, c2, s2), ps in filas:
        if c2.startswith("(") or c2 == c or len(ps) < args.min:
            continue
        print(f"{len(ps):6}  {c} / {s}  ->  {c2} / {s2}")
        for p in ps[:2]:
            print(f"          {p.get('name', '')[:90]}")
    print("\n== Cambio de SUBCATEGORÍA dentro de la misma categoría")
    for (c, s, c2, s2), ps in filas:
        if c2 != c or len(ps) < args.min:
            continue
        print(f"{len(ps):6}  {c} / {s}  ->  {s2}")
        for p in ps[:2]:
            print(f"          {p.get('name', '')[:90]}")
    print("\n== El clasificador las DESCARTARÍA (accesorio, refacción, no encaja)")
    for (c, s, c2, s2), ps in filas:
        if not c2.startswith("(") or len(ps) < args.min:
            continue
        print(f"{len(ps):6}  {c} / {s}  ->  {s2[:70]}")
        for p in ps[:2]:
            print(f"          {p.get('name', '')[:90]}")
    if args.salida:
        det = {" | ".join(str(x) for x in k): [p["id"] for p in v] for k, v in filas}
        io.open(args.salida, "w", encoding="utf-8").write(json.dumps(det, ensure_ascii=False, indent=0))
        print(f"\nDetalle en {args.salida}")


if __name__ == "__main__":
    main()
