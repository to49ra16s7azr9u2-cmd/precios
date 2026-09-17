#!/usr/bin/env python3
"""Mide qué categorías del catálogo NO alcanza el clasificador.

POR QUÉ
-------
Cuatro veces seguidas apareció el mismo agujero: una categoría con sus
subcategorías, sus fichas y hasta su repartidor sub_*() escrito... y ninguna
regla en REGLAS que la alcance. Mascotas (2,358 camas para perro como
Muebles/Camas), Deportes y fitness (498 aparatos de gimnasio como
Muebles/Sillas), Belleza (1,740 aparatos descartados) y Blancos y ropa de
cama (1,202 protectores de colchón como Muebles/Colchones). Cada una se
descubrió cuando llegó una captura de ese rubro, tarde y a mano.

CÓMO SE MIDE
------------
No se cuentan reglas: se prueba. Se toma una muestra de las fichas que el
catálogo YA tiene en cada categoría --puestas ahí por la taxonomía de la
tienda de origen, no por este clasificador-- y se les pasa el mismo
procedimiento que a una captura: FUERA, CABECERA y REGLAS. Si el
clasificador no devuelve la categoría en la que la ficha vive, es que esa
categoría no está cubierta y la próxima captura del rubro entrará mal.

El resultado se lee como una tasa de acierto por categoría. Una categoría
con 4,221 fichas y 6% de acierto es un agujero; una con 90% está cubierta.

USO
---
    python3 scripts/auditar_cobertura_clasificador.py            # 300 por categoría
    python3 scripts/auditar_cobertura_clasificador.py --muestra 1000
"""
import argparse
import collections
import random
import sys

sys.path.insert(0, "scripts")
from data_io import load_catalog  # noqa: E402


def cargar_clasificador():
    """FUERA, CABECERA, REGLAS y T() sin ejecutar el main del script."""
    ruta = "scripts/clasificar_captura_perifericos.py"
    src = open(ruta, encoding="utf-8").read().split("captura = json.load")[0]
    g = {"__file__": ruta, "__name__": "_clasificador"}
    exec(compile(src, ruta, "exec"), g)
    return g


def veredicto(g, titulo):
    """('ok'|'fuera'|'sin regla'|'otra', categoría propuesta)."""
    tn = g["T"](titulo)
    motivo = (next((m for rx, m in g["FUERA"] if rx.search(tn)), None)
              or next((m for rx, m in g["CABECERA"] if rx.search(tn[:55])), None))
    if motivo:
        return "fuera", motivo
    hit = next((v for rx, v in g["REGLAS"] if rx.search(tn)), None)
    if not hit:
        return "sin regla", None
    return "regla", hit[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--muestra", type=int, default=300,
                    help="fichas por categoría (por defecto %(default)s)")
    ap.add_argument("--min-fichas", type=int, default=100,
                    help="ignorar categorías con menos fichas que esto")
    args = ap.parse_args()

    g = cargar_clasificador()
    data = load_catalog()
    por_cat = collections.defaultdict(list)
    for p in data["products"]:
        if p.get("name"):
            por_cat[p["category"]].append(p["name"])

    filas = []
    random.seed(7)
    for cat, nombres in por_cat.items():
        if len(nombres) < args.min_fichas:
            continue
        muestra = random.sample(nombres, min(args.muestra, len(nombres)))
        cuenta = collections.Counter()
        destinos = collections.Counter()
        for n in muestra:
            tipo, dato = veredicto(g, n)
            if tipo == "regla":
                if dato == cat:
                    cuenta["ok"] += 1
                else:
                    cuenta["otra"] += 1
                    destinos[dato] += 1
            else:
                cuenta[tipo] += 1
        filas.append((cat, len(nombres), len(muestra), cuenta, destinos))

    filas.sort(key=lambda f: f[3]["ok"] / f[2])
    print(f"{'categoría':<34} {'fichas':>7} {'acierto':>8} {'fuera':>6} "
          f"{'sin regla':>10} {'otra cat':>9}   a dónde se va")
    print("-" * 118)
    for cat, total, n, c, destinos in filas:
        pct = c["ok"] / n
        dest = ", ".join(f"{d} {v}" for d, v in destinos.most_common(3))
        print(f"{cat:<34} {total:>7,} {pct:>7.0%} {c['fuera']:>6} "
              f"{c['sin regla']:>10} {c['otra']:>9}   {dest[:44]}")


if __name__ == "__main__":
    main()
