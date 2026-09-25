#!/usr/bin/env python3
"""Busca fichas de una tienda que están en la CATEGORÍA equivocada, con dos
jueces independientes que tienen que coincidir.

POR QUÉ (25-sep-2026)
---------------------
El usuario vio muchos errores de clasificación en lo importado de Walmart y
Bodega Aurrerá (644 mil fichas que solo venden ellas). En una muestra de 150
salieron, por ejemplo, pintura vinílica en Mascotas/Acuarios y tapones para
dormir en Audífonos. Esas fichas entraron por el clasificador de reglas con
el departamento de Walmart como respaldo, sin otro control.

CÓMO
----
1. Un bayesiano ingenuo (el de detectar_mal_clasificados.py) se entrena con
   las fichas de las DEMÁS tiendas, que ya pasaron varias rondas de revisión,
   y puntúa cada ficha de la tienda auditada.
2. Si el bayesiano prefiere otra categoría con margen claro (--margen nats),
   la ficha pasa por el clasificador de reglas de hoy (decidir(), sin
   departamento).
3. Se propone mover solo si los dos coinciden en el destino. Se agrupa por
   «Origen>Destino» con muestra para revisar a mano; --aplicar mueve solo los
   grupos aprobados (--grupos), con la subcategoría que da la regla.
   Lo corregido a mano no se toca.

USO
---
    python3 scripts/auditar_categorias_tienda.py --informe /tmp/aud_wm.json
    python3 scripts/auditar_categorias_tienda.py --aplicar --grupos "Mascotas>Herramientas" ...
"""
import argparse
import collections
import io
import json
import os
import random
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import ROOT, load_catalog, save_catalog  # noqa: E402
from detectar_mal_clasificados import Bayes, tokens  # noqa: E402
import clasificar_captura_perifericos as C  # noqa: E402

AUDITADAS = {"walmart_mx", "bodega_aurrera"}


def tiendas(p):
    st = set()
    for o in p.get("offers") or []:
        st.add(o.get("storeId") or o.get("store"))
    return st


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--informe")
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--grupos", nargs="*", default=[])
    ap.add_argument("--margen", type=float, default=6.0)
    ap.add_argument("--solo-modelo", action="store_true",
                    help="proponer también sin acuerdo de la regla (subcategoría por el modelo de subcategorías)")
    args = ap.parse_args()
    ruta = os.path.join(ROOT, "data", "clasificacion-a-mano.json")
    candado = json.load(io.open(ruta, encoding="utf-8")) if os.path.exists(ruta) else {}

    data = load_catalog()
    modelo = Bayes()
    subs = collections.defaultdict(Bayes)   # categoría -> modelo de subcategoría
    auditar = []
    for p in data["products"]:
        st = tiendas(p)
        if st and st <= AUDITADAS:
            auditar.append(p)
        else:
            ts = tokens(p.get("name"))
            modelo.entrenar(p["category"], ts)
            if p.get("subcategory"):
                subs[p["category"]].entrenar(p["subcategory"], ts)
    modelo.preparar()
    for m in subs.values():
        m.preparar()
    print(f"Entrenado con {modelo.total:,} fichas de otras tiendas; auditando {len(auditar):,}", flush=True)

    grupos = collections.defaultdict(list)
    dudosas = 0
    for i, p in enumerate(auditar):
        if p["id"] in candado:
            continue
        pts = modelo.puntajes(tokens(p.get("name")))
        if not pts:
            continue
        mejor = max(pts, key=pts.get)
        actual = pts.get(p["category"])
        if mejor == p["category"] or (actual is not None and pts[mejor] - actual < args.margen):
            continue
        dudosas += 1
        margen = round(pts[mejor] - actual, 1) if actual is not None else 99
        d = C.decidir({"asin": p["id"], "title": p["name"]})
        if d.get("category") == mejor and d.get("subcategory"):
            grupos[f"{p['category']}>{mejor}"].append((p, mejor, d["subcategory"], margen))
        elif args.solo_modelo and mejor in subs:
            sp = subs[mejor].puntajes(tokens(p.get("name")))
            if sp:
                grupos[f"{p['category']}>{mejor} (modelo)"].append((p, mejor, max(sp, key=sp.get), margen))
        if i % 100000 == 0:
            print(f"  {i:,} revisadas, {dudosas:,} dudosas", flush=True)

    resumen = {k: len(v) for k, v in sorted(grupos.items(), key=lambda kv: -len(kv[1]))}
    for k, n in list(resumen.items())[:70]:
        print(f"{n:7,}  {k}")
    print(f"Dudosas por el modelo: {dudosas:,}; con acuerdo de la regla: {sum(resumen.values()):,} en {len(resumen)} grupos")
    if args.informe:
        random.seed(25)
        muestra = {k: [(p["name"][:90], p.get("subcategory"), s, m) for p, _c, s, m in random.sample(v, min(20, len(v)))]
                   for k, v in grupos.items()}
        with io.open(args.informe, "w", encoding="utf-8") as f:
            json.dump({"resumen": resumen, "muestra": muestra}, f, ensure_ascii=False, indent=1)
    if args.aplicar:
        n = 0
        for g in args.grupos:
            for p, cat, sub, _m in grupos.get(g, []):
                p["category"], p["subcategory"] = cat, sub
                n += 1
        save_catalog(data)
        print(f"Guardado: {n:,} fichas movidas en {len(args.grupos)} grupos.")


if __name__ == "__main__":
    main()
