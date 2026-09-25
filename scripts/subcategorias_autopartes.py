#!/usr/bin/env python3
"""Vuelve a poner la subcategoría de Autopartes por la pieza que nombra el
título (reglas_nuevas.sub_autoparte).

POR QUÉ (25-sep-2026)
---------------------
El usuario vio problemas de clasificación en lo importado de Walmart. En una
muestra de 150 fichas de Walmart, casi la mitad de las autopartes tenía una
subcategoría ajena: amortiguadores en «Bujías y encendido», manijas de puerta
en «Frenos», soportes de motor en «Enfriamiento», salpicaderas de auto en
«Carenados» (de moto). sub_autoparte toma la pieza que el título nombra
primero; en una muestra de 70 cambios acertó los 70.

Solo cambia fichas donde sub_autoparte reconoce una pieza; lo demás se deja.
Lo corregido a mano (data/clasificacion-a-mano.json) no se toca.

USO
---
    python3 scripts/subcategorias_autopartes.py            # cuenta
    python3 scripts/subcategorias_autopartes.py --aplicar
"""
import argparse
import collections
import io
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import ROOT, load_catalog, save_catalog  # noqa: E402
import clasificar_captura_perifericos as C  # noqa: E402
import reglas_nuevas  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()
    ruta = os.path.join(ROOT, "data", "clasificacion-a-mano.json")
    candado = json.load(io.open(ruta, encoding="utf-8")) if os.path.exists(ruta) else {}
    data = load_catalog()
    cambios = collections.Counter()
    for p in data["products"]:
        if p.get("category") != "Autopartes" or p["id"] in candado:
            continue
        s = reglas_nuevas.sub_autoparte(C.T(p.get("name") or ""))
        if s and s != p.get("subcategory"):
            cambios[s] += 1
            p["subcategory"] = s
    print(f"Cambiarían {sum(cambios.values()):,}:", cambios.most_common())
    if args.aplicar:
        save_catalog(data)
        print("Guardado.")


if __name__ == "__main__":
    main()
