#!/usr/bin/env python3
"""Escribe data/marcas.json: el índice de marcas que la portada necesita.

POR QUÉ
-------
/marca/<slug>/ tiene una página por cada marca con 20 productos o más (784
al escribir esto), pero la portada no podía ofrecerlas: la lista de marcas
solo existe dentro de generate_seo_pages.py, y el navegador no baja el
catálogo entero en Inicio. Sin este archivo, la pestaña "Marcas" de la
portada tendría que mandar a la página de marcas y volver, en vez de
mostrarlas ahí mismo.

Es la misma idea que data/search-index.json: un índice chico, aparte del
catálogo, para que Inicio pueda responder sin bajar 214 mil fichas.

QUÉ GUARDA
----------
[{"n": nombre, "s": slug, "c": cuántos productos}], ordenado de más a
menos productos. Las claves son de una letra a propósito: son 784
entradas y este archivo se baja en la portada.

El nombre, el slug y el mínimo salen de generate_seo_pages.py --se
importa-- para que no puedan desincronizarse: si la página de una marca se
llama /marca/spring-air/, el enlace de la portada dice exactamente eso.

USO
---
    python3 scripts/build_marcas_index.py
    python3 scripts/build_marcas_index.py --dry-run
"""
import argparse
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import load_catalog  # noqa: E402
from generate_seo_pages import marcas_con_pagina  # noqa: E402

SALIDA = "data/marcas.json"
ROOT = os.path.dirname(AQUI)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = load_catalog()
    marcas = sorted(marcas_con_pagina(data), key=lambda m: -len(m[2]))
    salida = [{"n": nombre, "s": slug, "c": len(items)} for nombre, slug, items in marcas]
    cuerpo = json.dumps(salida, ensure_ascii=False, separators=(",", ":"))
    print(f"marcas con página: {len(salida):,}")
    print(f"tamaño: {len(cuerpo) / 1024:.0f} KB")
    if salida:
        print("primeras:", ", ".join(f"{m['n']} ({m['c']})" for m in salida[:6]))
    if args.dry_run:
        print("\n--dry-run: no se escribió nada")
        return
    with open(os.path.join(ROOT, SALIDA), "w", encoding="utf-8") as f:
        f.write(cuerpo)
    print(f"\n{SALIDA} escrito.")

    # Se anuncia en el manifiesto, igual que el índice de búsqueda: si el
    # archivo no está, la portada cae al enlace de siempre a /marca/.
    ruta = os.path.join(ROOT, "data", "data.json")
    with open(ruta, encoding="utf-8") as f:
        manifiesto = json.load(f)
    if manifiesto.get("brandIndexFile") != SALIDA:
        manifiesto["brandIndexFile"] = SALIDA
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(manifiesto, f, ensure_ascii=False)
        print("data/data.json: brandIndexFile anunciado")


if __name__ == "__main__":
    main()
