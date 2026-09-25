#!/usr/bin/env python3
"""Pasa a gzip lo que haya quedado plano en las carpetas comprimidas.

Las carpetas de COMPRIMIDOS (data_io.py) se publican como <nombre>.json.gz,
y la SPA pide siempre el .gz. Quien escribe con escribir_texto_json ya deja
el .gz, pero un archivo que nadie reescribió (un trozo de historial sin
cambios, por ejemplo) quedaría plano y la página no lo encontraría. Esto
corre al final de regenerar_sitio.sh y deja todo en .gz; es idempotente.

USO
---
    python3 scripts/comprimir_datos.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import ROOT, COMPRIMIDOS, comprimido, escribir_texto_json  # noqa: E402


def main():
    pasados = 0
    for carpeta in COMPRIMIDOS:
        ruta = os.path.join(ROOT, carpeta)
        if not os.path.isdir(ruta):
            continue
        for nombre in sorted(os.listdir(ruta)):
            if not nombre.endswith(".json"):
                continue
            fname = carpeta + nombre
            if not comprimido(fname):
                continue
            # El plano manda: si quedó, es lo último que se escribió.
            with open(os.path.join(ruta, nombre), encoding="utf-8") as f:
                texto = f.read()
            if os.path.exists(os.path.join(ruta, nombre + ".gz")):
                os.remove(os.path.join(ruta, nombre + ".gz"))
            escribir_texto_json(fname, texto)
            pasados += 1
    print(f"archivos pasados a gzip: {pasados}")


if __name__ == "__main__":
    main()
