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

    print(f"\nCampos limpiados: {cambios}")
    if args.dry_run:
        print("(--dry-run: no se escribió nada)")
        return
    if cambios:
        save_catalog(data)
        print("Catálogo guardado.")


if __name__ == "__main__":
    main()
