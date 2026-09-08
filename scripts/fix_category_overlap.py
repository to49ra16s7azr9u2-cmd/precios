#!/usr/bin/env python3
"""Arregla dos categorías que se pisan con otras del sitio.

CÓMO SE ENCONTRARON
-------------------
Barriendo el catálogo por la PALABRA CABEZA del nombre (el primer
sustantivo, que en español es lo que dice qué es el producto) y buscando
las que aparecen repartidas entre varias categorías. Salieron dos casos
reales; el resto de las coincidencias eran homónimos legítimos ("disco"
duro / de corte / de freno, "teclado" de computadora / musical, "mesa" de
comedor / de juego), que se dejan como están.

1. SMARTWATCHES EN JOYERÍA
   104 relojes inteligentes guardados en "Joyería y bisutería", teniendo
   "Relojes inteligentes" al lado. Se mudan. Los relojes normales de
   joyería (2,311) no se tocan: solo se mueve lo que se declara
   smartwatch o reloj inteligente, y nunca un accesorio PARA uno (correas,
   fundas, protectores, cargadores), que sí es bisutería o accesorio.

2. "COMPUTADORAS" NO TIENE COMPUTADORAS
   Sus 252 productos son motherboards, memorias, disipadores, webcams,
   tabletas gráficas y docks -- sus propias subcategorías lo dicen
   ("Componentes", "Periféricos y accesorios", "Memoria RAM", "Webcams").
   En la portada quedaba al lado de "Computadoras de escritorio" (648) y
   parecían la misma categoría duplicada; quien entraba buscando una
   computadora se encontraba tarjetas madre.

   No se reparten sus productos: son un grupo coherente y útil. Lo que
   estaba mal era el nombre, así que la categoría pasa a llamarse
   "Componentes y accesorios de PC". Como el id de una categoría ES su
   nombre, hay que reescribir product.category de los 252.

USO
---
    python3 scripts/fix_category_overlap.py --dry-run
    python3 scripts/fix_category_overlap.py
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog  # noqa: E402

VIEJA = "Computadoras"
NUEVA = "Componentes y accesorios de PC"
JOYERIA = "Joyería y bisutería"
RELOJES = "Relojes inteligentes"

_ES_SMARTWATCH = re.compile(r"smart\s?watch|reloj(es)? intelig", re.I)
# Accesorios PARA un smartwatch: no son smartwatches.
_ACCESORIO = re.compile(
    r"correa|extensible|banda para|pulsera para|malla para|protector|mica\b|"
    r"funda|cargador|base de carga|soporte", re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = load_catalog()
    productos = data["products"]

    mudados = []
    for p in productos:
        if p.get("category") != JOYERIA:
            continue
        nombre = p.get("name", "")
        if _ES_SMARTWATCH.search(nombre) and not _ACCESORIO.search(nombre):
            p["category"] = RELOJES
            p["subcategory"] = "Smartwatches"
            p["image"] = "watch"
            mudados.append(nombre[:56])

    renombrados = 0
    for p in productos:
        if p.get("category") == VIEJA:
            p["category"] = NUEVA
            renombrados += 1
    for c in data["categories"]:
        if c.get("id") == VIEJA:
            c["id"] = NUEVA
            c["name"] = NUEVA

    print(f"Smartwatches movidos de {JOYERIA} a {RELOJES}: {len(mudados)}")
    for n in mudados[:10]:
        print(f"   {n}")
    if len(mudados) > 10:
        print(f"   ... y {len(mudados) - 10} más")
    print(f'\nCategoría "{VIEJA}" renombrada a "{NUEVA}": {renombrados} productos')

    if args.dry_run:
        print("\n(--dry-run: no se escribió nada)")
        return
    save_catalog(data)
    print("\nGuardado. Después: sync_subcategories.py, compute_facets.py y "
          "generate_seo_pages.py; y borrar categoria/computadoras/ y la shard vieja.")


if __name__ == "__main__":
    main()
