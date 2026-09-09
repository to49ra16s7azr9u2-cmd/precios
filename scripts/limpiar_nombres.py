#!/usr/bin/env python3
"""Deja los nombres y marcas en texto plano, sin entidades HTML.

Algunos títulos llegaron de la tienda ya escapados y se guardaron así:
'Pantalla móvil inteligente MESWAO de 32&quot;'. En el sitio eso se leía de
dos maneras distintas según dónde apareciera -- 32" en la fila de la lista
(que inyecta el nombre tal cual) y 32&quot; en el atributo title (que sí
escapa). Guardado en texto plano, se lee igual en todos lados, y además deja
de bloquear el escape en el render: escapar un nombre que ya venía escapado
sería mostrar 32&quot; en la lista también.

USO
    python3 scripts/limpiar_nombres.py --dry-run
    python3 scripts/limpiar_nombres.py
"""
import argparse
import html
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog

ENTIDAD = re.compile(r"&(?:#\d+|#x[0-9a-fA-F]+|[a-zA-Z][a-zA-Z0-9]{1,9});")
CAMPOS = ("name", "brand")

# Un nombre sin NINGUNA palabra ("0.45", "500") es un título que la tienda
# dejó en el número de modelo. En la tarjeta y en el <title> de su página se
# leía así, tal cual, sin decir qué es el producto.
#
# No se inventa un nombre: se arma con lo que la propia ficha ya declara, en
# este orden y salteando lo que falte -- el tipo de producto de la ficha
# técnica, la marca y el modelo. Si con eso tampoco sale una palabra, se
# deja como está y se avisa.
SIN_PALABRA = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{3,}")
ETIQUETAS_DE_TIPO = ("Tipo de Herramienta", "Tipo de Producto", "Tipo", "Categoría")


def nombre_desde_la_ficha(product):
    """Un nombre armado con datos que ya están en el producto, o None."""
    specs = {s.get("label"): (s.get("value") or "").strip()
             for s in (product.get("specs") or [])}
    tipo = next((specs[e] for e in ETIQUETAS_DE_TIPO if specs.get(e)), "")
    marca = (product.get("brand") or "").strip()
    modelo = specs.get("Modelo", "")
    partes = [x for x in (tipo, marca, modelo) if x]
    nuevo = " ".join(partes).strip()
    if not SIN_PALABRA.search(nuevo):
        return None
    return nuevo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = load_catalog()
    cambios = 0
    for p in data["products"]:
        for campo in CAMPOS:
            v = p.get(campo)
            if not v or not ENTIDAD.search(v):
                continue
            # Una sola pasada: si el título trae un "&amp;" que de verdad es
            # parte del nombre, dos pasadas lo convertirían en otra cosa.
            nuevo = html.unescape(v)
            if nuevo != v:
                if cambios < 20:
                    print(f"  {p['id']:>9} {campo}: {v[:60]!r} -> {nuevo[:60]!r}")
                p[campo] = nuevo
                cambios += 1

    sin_nombre = renombrados = 0
    for p in data["products"]:
        if SIN_PALABRA.search(p.get("name") or ""):
            continue
        sin_nombre += 1
        nuevo = nombre_desde_la_ficha(p)
        if not nuevo:
            print(f"  {p['id']:>9} sin nombre y sin datos para armar uno: "
                  f"{p.get('name')!r} -- se deja como está")
            continue
        print(f"  {p['id']:>9} name: {p['name']!r} -> {nuevo!r}")
        p["name"] = nuevo
        renombrados += 1

    print(f"\nCampos limpiados: {cambios}")
    print(f"Nombres que eran solo un número: {sin_nombre} "
          f"({renombrados} rearmados desde su ficha técnica)")
    cambios += renombrados
    if args.dry_run:
        print("(--dry-run: no se escribió nada)")
        return
    if cambios:
        save_catalog(data)
        print("Catálogo guardado.")


if __name__ == "__main__":
    main()
