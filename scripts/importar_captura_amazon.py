#!/usr/bin/env python3
"""Mete al catálogo una captura del marcador de Amazon, de una vez.

Es la cadena que hasta ahora se corría a mano cada vez que llegaba una
captura, en el orden de siempre:

  1. Se juntan los archivos que se le pasen y se quitan los ASIN repetidos
     (el marcador acumula, así que una captura suele contener a la anterior).
  2. Se quitan los ASIN que el catálogo ya tiene en alguna oferta
     (existing_asins de add_amazon_standalone.py): esos ya están.
  3. Lo que queda pasa por clasificar_captura_perifericos.py, que decide
     categoría y subcategoría por el título -- o por el departamento de
     Amazon, si la captura lo trae -- y descarta con motivo lo que no es un
     producto.
  4. Lo clasificado entra con add_amazon_standalone.py, que salta lo que no
     trae precio y avisa de precios fuera de rango.

Después hay que correr compute_facets.py, record_price_history.py y
generate_seo_pages.py, como con cualquier alta; el script lo recuerda.

USO
---
    python3 scripts/importar_captura_amazon.py capturas/amazon-2026-09-14-3120.json
    python3 scripts/importar_captura_amazon.py capturas/*.json --dry-run
    python3 scripts/importar_captura_amazon.py captura.json --solo-clasificar

--dry-run corre todo menos el alta. --solo-clasificar se queda en el paso 3
y deja el resultado en <captura>.alta.json para revisarlo antes de dar de
alta con add_amazon_standalone.py a mano.
"""
import argparse
import io
import json
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from add_amazon_standalone import existing_asins  # noqa: E402
from data_io import load_catalog  # noqa: E402

TAG = "comparamex0d-20"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capturas", nargs="+", help="JSON del marcador (uno o varios)")
    ap.add_argument("--tag", default=TAG, help="tracking id de Amazon Associates")
    ap.add_argument("--dry-run", action="store_true", help="todo menos el alta")
    ap.add_argument("--solo-clasificar", action="store_true",
                    help="clasificar y parar; deja <captura>.alta.json")
    args = ap.parse_args()

    # 1. juntar y desduplicar
    vistos, items = set(), []
    for ruta in args.capturas:
        for it in json.load(io.open(ruta, encoding="utf-8")):
            asin = (it.get("asin") or "").strip().upper()
            if not asin or asin in vistos:
                continue
            vistos.add(asin)
            items.append(it)
    print(f"Capturados: {len(items)} ASIN distintos en {len(args.capturas)} archivo(s)")
    if not items:
        return

    # 2. quitar lo que el catálogo ya tiene
    conocidos = existing_asins(load_catalog()["products"])
    nuevos = [it for it in items if it["asin"].upper() not in conocidos]
    print(f"Ya en el catálogo: {len(items) - len(nuevos)}   nuevos: {len(nuevos)}")
    if not nuevos:
        return

    base = os.path.splitext(args.capturas[0])[0]
    ruta_nuevos, ruta_alta = base + ".nuevos.json", base + ".alta.json"
    json.dump(nuevos, io.open(ruta_nuevos, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # 3. clasificar
    print(f"\n== clasificar_captura_perifericos.py ({len(nuevos)} anuncios) ==")
    env = {**os.environ, "PYTHONPATH": AQUI}
    r = subprocess.run([sys.executable, os.path.join(AQUI, "clasificar_captura_perifericos.py"),
                        ruta_nuevos, ruta_alta], env=env)
    if r.returncode:
        sys.exit("el clasificador falló")
    os.remove(ruta_nuevos)
    alta = json.load(io.open(ruta_alta, encoding="utf-8"))
    if args.solo_clasificar:
        print(f"\nClasificados en {ruta_alta}. Para darlos de alta:\n"
              f"  python3 scripts/add_amazon_standalone.py {ruta_alta} --tag {args.tag}")
        return
    if not alta:
        os.remove(ruta_alta)
        print("\nNada que dar de alta.")
        return

    # 4. alta
    print(f"\n== add_amazon_standalone.py ({len(alta)} fichas) ==")
    cmd = [sys.executable, os.path.join(AQUI, "add_amazon_standalone.py"), ruta_alta, "--tag", args.tag]
    if args.dry_run:
        cmd.append("--dry-run")
    r = subprocess.run(cmd, env=env)
    if r.returncode:
        sys.exit("el alta falló; el JSON clasificado queda en " + ruta_alta)
    os.remove(ruta_alta)
    if not args.dry_run:
        print("\nAhora: python3 scripts/compute_facets.py && "
              "python3 scripts/record_price_history.py && "
              "python3 scripts/generate_seo_pages.py")


if __name__ == "__main__":
    main()
