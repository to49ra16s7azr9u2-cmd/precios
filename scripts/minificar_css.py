#!/usr/bin/env python3
"""Genera css/style.min.css a partir de css/style.css.

POR QUÉ
-------
Las páginas cargan style.min.css, no style.css. El minificado se venía
armando a mano y se quedó atrás: style.css tenía cambios de dos días después
que el sitio no estaba sirviendo. Eso es peor que no minificar, porque el
archivo que se edita y el que se publica dejan de ser el mismo y la diferencia
no se ve en ningún lado hasta que algo no se aplica.

Con esto el minificado se regenera en un comando y deja de ser un artefacto
que alguien tiene que acordarse de actualizar.

QUÉ HACE
--------
Quita comentarios y espacio sobrante. Nada más: no reordena reglas, no
fusiona selectores ni toca los valores. Un minificador que "optimiza" puede
cambiar la cascada, y acá la cascada está peleada a mano en varios lugares
(ver los comentarios de style.css).

Los comentarios se van del publicado pero siguen en style.css, que es el
archivo que se lee y se edita.

USO
---
    python3 scripts/minificar_css.py
    python3 scripts/minificar_css.py --dry-run
"""
import argparse
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ENTRADA = os.path.join(AQUI, "..", "css", "style.css")
SALIDA = os.path.join(AQUI, "..", "css", "style.min.css")


def minificar(css):
    # Los comentarios primero, para que su contenido no confunda al resto.
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    # Espacio alrededor de los separadores que no cambia nada.
    css = re.sub(r"\s*([{}:;,>])\s*", r"\1", css)
    # El punto y coma antes de cerrar la llave sobra.
    css = re.sub(r";}", "}", css)
    # Saltos y sangrías que quedaron.
    css = re.sub(r"\s+", " ", css).strip()
    return css + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with open(ENTRADA, encoding="utf-8") as f:
        original = f.read()
    salida = minificar(original)

    previo = ""
    if os.path.exists(SALIDA):
        with open(SALIDA, encoding="utf-8") as f:
            previo = f.read()

    print(f"style.css      {len(original):>8,} bytes")
    print(f"style.min.css  {len(salida):>8,} bytes  ({100 - 100 * len(salida) / len(original):.0f}% menos)")
    if previo:
        print(f"el publicado tenía {len(previo):,} bytes"
              + ("  -- SIN CAMBIOS" if previo == salida else "  -- se actualiza"))

    if args.dry_run:
        print("\n--dry-run: no se escribió nada")
        return
    if previo == salida:
        print("\nnada que escribir")
        return
    with open(SALIDA, "w", encoding="utf-8") as f:
        f.write(salida)
    print("\nGuardado.")


if __name__ == "__main__":
    main()
