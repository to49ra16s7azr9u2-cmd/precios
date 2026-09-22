#!/usr/bin/env python3
"""Usa la taxonomía de Mercado Libre como segunda opinión sobre la nuestra.

DE DÓNDE SALE EL DATO
---------------------
dominios_ml.py recupera, ficha por ficha, el `domain_id` que Mercado Libre le
puso a ese producto: "MLM-DRILL_BITS" a una broca, "MLM-BED_SHEETS" a un juego
de sábanas. No es una adivinanza nuestra sobre el nombre: es la clasificación
de quien lo vende, hecha para México y sobre el producto de catálogo.

Un intento anterior falló justo por eso: emparejaba el NOMBRE del dominio
("Mini PCs") contra nuestros títulos, y recogía 15,622 fichas que eran
lavadoras mini, ventiladores mini y bocinas mini. Aquí el dominio viene pegado
a la ficha, así que ese error no se puede repetir.

CÓMO SE LEE
-----------
Un dominio no equivale a una subcategoría nuestra: MLM-CELLPHONES cubre
Android y iPhone por igual, y eso está bien. Lo que sí dice algo es el caso
contrario: si de 900 fichas de MLM-BED_SHEETS 880 están en «Blancos y ropa de
cama», las 20 que están en «Muebles» son sospechosas.

Así que el mandato se APRENDE de nuestro propio catálogo: para cada dominio se
mira dónde cae la mayoría, y sólo se opina cuando esa mayoría es aplastante
(--dominio-min de acuerdo) y hay bastantes fichas para creerle (--min-fichas).
Donde el dominio se reparte entre varias subcategorías, se calla.

DOS NIVELES
-----------
  --nivel categoria   más seguro: el dominio decide la categoría. Un juego de
                      sábanas en Muebles está mal se mire como se mire.
  --nivel sub         más fino y más ruidoso: dentro de la categoría correcta,
                      el dominio decide la subcategoría.

SALIDA
------
Con --salida escribe el JSON que come aplicar_movimientos.py, agrupado por
"cat | sub | cat2 | sub2", para revisar grupo por grupo antes de mover nada.

USO
---
    python3 scripts/auditar_por_dominio.py --mandato
    python3 scripts/auditar_por_dominio.py --nivel categoria --salida /tmp/mover.json
    python3 scripts/auditar_por_dominio.py --nivel sub --min-fichas 60 --dominio-min 0.90
"""
import argparse
import collections
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog  # noqa: E402
from dominios_ml import SALIDA, ids_del_catalogo  # noqa: E402


def dominio_por_ficha(products):
    """{id de ficha nuestra: dominio de Mercado Libre}"""
    if not os.path.exists(SALIDA):
        print(f"falta {SALIDA}: corre antes scripts/dominios_ml.py", file=sys.stderr)
        return {}
    with io.open(SALIDA, encoding="utf-8") as f:
        dom_por_mlm = json.load(f)
    out = {}
    for pid, mlm in ids_del_catalogo(products).items():
        d = dom_por_mlm.get(mlm)
        if d:
            out[pid] = d
    return out


def mandatos(products, doms, nivel, min_fichas, acuerdo, empuje=1.5):
    """{dominio: destino} para los dominios que mandan de verdad.

    El destino es la categoría (nivel=categoria) o el par (cat, sub)
    (nivel=sub) donde cae la mayoría aplastante de las fichas de ese dominio.

    Con la mayoría sola no alcanza, y se ve en Celulares: el 88% de nuestros
    celulares están en «Android», así que MLM-CELLPHONES apunta a «Android»
    por inercia, y entonces acusa de mal clasificado a todo iPhone. No está
    distinguiendo nada; está repitiendo cuál es la subcategoría más grande.

    El freno es pedir EMPUJE: que la proporción dentro del dominio supere a la
    proporción dentro de la categoría por un factor. MLM-CELLPHONES no lo
    supera (0.88 contra 0.88) y se calla; MLM-DRILL_BITS sí (1.00 contra 0.04)
    y manda.
    """
    por_dom = collections.defaultdict(collections.Counter)
    base = collections.defaultdict(collections.Counter)
    for p in products:
        cat = p.get("category")
        if nivel == "sub" and cat and p.get("subcategory"):
            base[cat][p["subcategory"]] += 1
        d = doms.get(p["id"])
        if not d:
            continue
        if nivel == "categoria":
            clave = cat
        else:
            clave = (cat, p.get("subcategory"))
            if not clave[1]:
                clave = None
        if clave:
            por_dom[d][clave] += 1
    out = {}
    for d, c in por_dom.items():
        total = sum(c.values())
        if total < min_fichas:
            continue
        destino, n = c.most_common(1)[0]
        if n / total < acuerdo:
            continue
        if nivel == "sub":
            cat, sub = destino
            cuantas = sum(base[cat].values())
            if not cuantas:
                continue
            if (n / total) / (base[cat][sub] / cuantas) < empuje:
                continue
        out[d] = (destino, n, total)
    return out


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nivel", choices=["categoria", "sub"], default="categoria")
    ap.add_argument("--min-fichas", type=int, default=40,
                    help="fichas mínimas del dominio para hacerle caso (%(default)s)")
    ap.add_argument("--dominio-min", type=float, default=0.88,
                    help="proporción mínima de acuerdo (%(default)s)")
    ap.add_argument("--empuje", type=float, default=1.5,
                    help="con --nivel sub, cuánto tiene que superar el dominio "
                         "a la proporción de esa subcategoría en su categoría (%(default)s)")
    ap.add_argument("--min-grupo", type=int, default=3,
                    help="grupos con menos fichas no se listan (%(default)s)")
    ap.add_argument("--mandato", action="store_true",
                    help="listar los dominios que mandan y salir")
    ap.add_argument("--salida", help="JSON de movimientos para aplicar_movimientos.py")
    ap.add_argument("--limite", type=int, default=45)
    args = ap.parse_args()

    data = load_catalog()
    doms = dominio_por_ficha(data["products"])
    if not doms:
        return 1
    print(f"fichas con dominio de Mercado Libre: {len(doms):,}")
    manda = mandatos(data["products"], doms, args.nivel, args.min_fichas,
                     args.dominio_min, args.empuje)
    print(f"dominios con mandato ({args.nivel}, >={args.min_fichas} fichas, "
          f">={args.dominio_min:.0%} de acuerdo): {len(manda)}\n")

    if args.mandato:
        for d, (destino, n, total) in sorted(manda.items(), key=lambda kv: -kv[1][2])[:args.limite]:
            etq = destino if args.nivel == "categoria" else f"{destino[0]} / {destino[1]}"
            print(f"  {total:>6,} fichas  {d:42} -> {etq}   ({n/total:.0%})")
        return 0

    grupos = collections.defaultdict(list)
    for p in data["products"]:
        d = doms.get(p["id"])
        if d not in manda:
            continue
        destino = manda[d][0]
        if args.nivel == "categoria":
            if p.get("category") == destino:
                continue
            # Sin subcategoría destino: se deja que el clasificador la ponga.
            clave = f"{p.get('category')} | {p.get('subcategory') or ''} | {destino} | "
        else:
            actual = (p.get("category"), p.get("subcategory"))
            if actual == destino or not actual[1]:
                continue
            clave = f"{actual[0]} | {actual[1]} | {destino[0]} | {destino[1]}"
        grupos[clave].append(p["id"])

    nombres = {p["id"]: p["name"] for p in data["products"]}
    orden = sorted(grupos.items(), key=lambda kv: -len(kv[1]))
    total = sum(len(v) for _k, v in orden if len(v) >= args.min_grupo)
    print(f"fichas que el dominio contradice (grupos de {args.min_grupo}+): {total:,}\n")
    for clave, ids in orden[:args.limite]:
        if len(ids) < args.min_grupo:
            break
        print(f"  {len(ids):>5}  {clave}")
        for pid in ids[:2]:
            print(f"           {nombres[pid][:68]}")

    if args.salida:
        salida = {k: v for k, v in grupos.items() if len(v) >= args.min_grupo}
        with io.open(args.salida, "w", encoding="utf-8") as f:
            json.dump(salida, f, ensure_ascii=False, indent=1)
        print(f"\n-> {args.salida} ({len(salida)} grupos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
