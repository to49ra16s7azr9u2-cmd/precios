#!/usr/bin/env python3
"""Vuelve a pasar por el clasificador de HOY las fichas que ya están en el catálogo.

POR QUÉ
-------
El 23-sep-2026, al buscar la causa de los errores que quedaban, salió que
muchas fichas mal puestas ya las clasificaría bien el clasificador actual:
las reglas se usan sólo al dar de alta, y cuando una regla se corrige la
corrección vale para lo que entra después, no para lo que ya entró con la
regla vieja. Ejemplo: la regla de All in One aceptaba «todo en uno» en
cualquier título, y metió en Computadoras de escritorio carriolas Doona,
recortadoras Philips, pasta dental y sistemas de PA. Se arregló la regla,
pero esas fichas seguían ahí.

kakaku.com no tiene este problema porque la categoría vive en un maestro
central: si cambia la definición de 電気ケトル, se remapean los productos.
Este script es ese remapeo: arma una captura con las fichas de una
categoría, la pasa por clasificar_captura_perifericos.py tal cual (reglas,
FUERA, el sustantivo que manda, los repartidores de subcategoría) y
propone mover las que hoy caen en OTRA categoría.

QUÉ NO HACE
-----------
  - No borra: lo que hoy iría a FUERA o no encaja en nada se queda donde
    está (el catálogo no pierde fichas por esto).
  - No mueve solo: escribe {grupo: [ids]} para aplicar_movimientos.py, y el
    informe muestra ejemplos por grupo para revisarlos antes.
  - Sólo categoría: si la categoría de hoy es la misma, no toca la
    subcategoría (eso es trabajo de sync_subcategories y los repartidores).

USO
---
    python3 scripts/reclasificar_con_reglas_de_hoy.py --categoria "Computadoras de escritorio" --salida /tmp/mov.json
    python3 scripts/aplicar_movimientos.py /tmp/mov.json --todos --min 1 --motivo "..."
"""
import argparse
import collections
import json
import os
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import load_catalog  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--categoria", action="append", required=True)
    ap.add_argument("--subcategoria", help="sólo las fichas de esta subcategoría")
    ap.add_argument("--salida", required=True)
    ap.add_argument("--ejemplos", type=int, default=3)
    args = ap.parse_args()

    data = load_catalog()
    fichas = [p for p in data["products"] if p.get("category") in args.categoria
              and (not args.subcategoria or p.get("subcategory") == args.subcategoria)]
    por_id = {p["id"]: p for p in fichas}
    captura = [{"asin": p["id"], "title": p["name"], "price": 1.0, "photo": p.get("photo"), "url": ""}
               for p in fichas]
    with tempfile.TemporaryDirectory() as tmp:
        entrada = os.path.join(tmp, "cap.json")
        salida = os.path.join(tmp, "alta.json")
        with open(entrada, "w", encoding="utf-8") as f:
            json.dump(captura, f, ensure_ascii=False)
        subprocess.run([sys.executable, os.path.join(AQUI, "clasificar_captura_perifericos.py"), entrada, salida],
                       check=True, stdout=subprocess.DEVNULL)
        with open(salida, encoding="utf-8") as f:
            alta = json.load(f)

    grupos = collections.defaultdict(list)
    for a in alta:
        p = por_id.get(a["asin"])
        if not p or not a.get("category") or a["category"] == p["category"]:
            continue
        clave = f'{p["category"]} | {p.get("subcategory")} | {a["category"]} | {a.get("subcategory")}'
        grupos[clave].append(p["id"])
    print(f"fichas revisadas: {len(fichas):,}; hoy caerían en otra categoría: "
          f"{sum(len(v) for v in grupos.values()):,} en {len(grupos)} grupos")
    for k, v in sorted(grupos.items(), key=lambda kv: -len(kv[1])):
        print(f"{len(v):5}  {k}")
        for x in v[:args.ejemplos]:
            print(f"         {por_id[x]['name'][:90]}")
    with open(args.salida, "w", encoding="utf-8") as f:
        json.dump(grupos, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
