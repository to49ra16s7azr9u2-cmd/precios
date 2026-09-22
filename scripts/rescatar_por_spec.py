#!/usr/bin/env python3
"""Saca del balde genérico la ficha cuyo dato está en el VALOR de una spec.

EL PROBLEMA
-----------
Varias subcategorías conviven con sus propias variantes y se quedan con el
grueso: "Sábanas" al lado de "Sábanas queen size", "Colchones" al lado de
"Colchones matrimoniales". Medido el 21 de septiembre de 2026, había 10,351
fichas atrapadas así en todo el catálogo.

La primera explicación era que faltaba afinar el clasificador. No: el
clasificador se niega ante la duda, que es lo correcto, y el dato
sencillamente no está en el nombre. "Juego de sábanas Coyuchi Satén de
algodón orgánico" no dice de qué tamaño es.

DÓNDE SÍ ESTÁ
-------------
En la ficha técnica, pero no en la etiqueta que uno buscaría. El tamaño de
esas sábanas aparece dentro de «Contenido del Empaque» = "1 sábana
ajustable tamaño queen 1 sábana plana". El mapa de compute_facets.py va de
ETIQUETA a campo, así que un dato escondido en el valor de otra etiqueta le
pasa por al lado.

Esto busca el patrón en el valor de CUALQUIER spec, no en la etiqueta que
le correspondería.

POR QUÉ NO ARREGLA LOS OTROS BALDES
-----------------------------------
Se probó lo mismo con los tres baldes más grandes y no hay nada que sacar:
de las 3,087 "Bocinas Bluetooth" sólo el 28% trae ficha técnica y ninguna
tiene columna de watts; de las 588 "Freidoras de aire", el 4%. Lo que la
tienda no publica no se puede clasificar, y rellenarlo sería inventar.

USO
---
    python3 scripts/rescatar_por_spec.py --dry-run
    python3 scripts/rescatar_por_spec.py --aplicar
"""
import argparse
import collections
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog  # noqa: E402

# (categoría, balde genérico, patrón, {valor capturado: subcategoría destino})
# El destino tiene que existir ya: esto reparte, no inventa taxonomía.
RESCATES = [
    ("Blancos y ropa de cama", "Sábanas",
     r"\b(king|queen|matrimonial|individual|cuna)\b",
     {"king": "Sábanas king size", "queen": "Sábanas queen size",
      "matrimonial": "Sábanas matrimoniales", "individual": "Sábanas individuales",
      "cuna": "Sábanas para cuna y bebé"}),
    ("Muebles", "Colchones",
     r"\b(king|queen|matrimonial|individual|cuna)\b",
     {"king": "Colchones king size", "queen": "Colchones queen size",
      "matrimonial": "Colchones matrimoniales", "individual": "Colchones individuales",
      "cuna": "Colchones infantiles y de cuna"}),
]


def T(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def rescatar(products, subs_validas):
    movidos, cuenta = [], collections.Counter()
    for cat, balde, patron, destinos in RESCATES:
        rx = re.compile(patron)
        for p in products:
            if p.get("category") != cat or p.get("subcategory") != balde:
                continue
            # Si el NOMBRE ya lo dice, el clasificador tuvo su oportunidad y
            # decidió dejarlo acá: no se le pasa por encima.
            if rx.search(T(p["name"])):
                continue
            for sp in (p.get("specs") or []):
                m = rx.search(T(str(sp.get("value"))))
                if not m:
                    continue
                destino = destinos.get(m.group(1))
                if destino and (cat, destino) in subs_validas:
                    movidos.append((p, balde, destino, sp.get("label")))
                    cuenta[f"{cat} | {balde} -> {destino}"] += 1
                break
    return movidos, cuenta


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = load_catalog()
    subs_validas = {(c["id"], s["id"]) for c in data["categories"]
                    for s in (c.get("subcategories") or [])}
    movidos, cuenta = rescatar(data["products"], subs_validas)

    for k, n in cuenta.most_common():
        print(f"  {n:>4}  {k}")
    print(f"\nrescatadas: {len(movidos):,}")
    for p, balde, destino, etiqueta in movidos[:6]:
        print(f"    «{etiqueta}» -> {destino}")
        print(f"       {p['name'][:66]}")

    if not args.aplicar:
        print("\n(sin --aplicar no se guarda nada)")
        return 0
    for p, _balde, destino, _etq in movidos:
        p["subcategory"] = destino
    save_catalog(data)
    print("\nCatálogo guardado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
