#!/usr/bin/env python3
"""Mueve la parte de belleza de "Salud y belleza" a "Belleza y cuidado personal".

POR QUÉ
-------
El catálogo tenía dos departamentos de belleza. "Aparatos de belleza" --hoy
"Belleza y cuidado personal"-- y "Salud y belleza", que además de salud
(baumanómetros, básculas, cuidado dental, scooters de movilidad) guardaba
490 rasuradoras, 274 fichas de cuidado del cabello, 169 de depilación, 93 de
rastrillos y 22 masajeadores: exactamente lo mismo que la otra categoría ya
tenía en subcategorías con el MISMO nombre.

QUÉ SE MUEVE Y QUÉ NO
---------------------
Se mueve lo que es belleza. Se queda lo que es salud, que no debe acabar
mezclado: Cuidado dental, Movilidad, Salud, Básculas y Equipo de monitoreo
médico. Al quedarse sin belleza, la categoría pasa a llamarse "Salud".

"Cuidado personal" (426) no se mueve en bloque porque adentro hay de todo
--crema para rizos, protector solar, depiladora Braun, juego de peluquería--:
cada ficha pasa por sub_belleza(), el mismo repartidor que usa el
clasificador, y la que no reparte conserva su subcategoría.

NO se borra ninguna ficha ni ninguna oferta: solo cambian de categoría.
"""
import re
import sys
import collections

sys.path.insert(0, "scripts")
from data_io import load_catalog, save_catalog  # noqa: E402

VIEJA = "Salud y belleza"
NUEVA_BELLEZA = "Belleza y cuidado personal"
VIEJA_RENOMBRADA = "Salud"

# Subcategoría de origen -> subcategoría de destino. None = la decide
# sub_belleza() ficha por ficha.
MUEVE = {
    "Rasuradoras": "Rasuradoras",
    "Cuidado del cabello": "Cuidado del cabello",
    "Depilación": "Depilación",
    "Masajeadores": "Masajeadores",
    # El rastrillo y sus cuchillas son afeitado: Belleza no tiene
    # "Rastrillos", y Rasuradoras es donde el catálogo ya guarda lo de
    # afeitar.
    "Rastrillos": "Rasuradoras",
    # Las 308 que sub_belleza() no reparte son igual de belleza --taza y
    # brocha de afeitar, hojas Gillette, pinzas de cejas, producto para
    # peinar, loción para tatuajes--: conservan su nombre de siempre en una
    # subcategoría "Cuidado personal" dentro de Belleza.
    "Cuidado personal": None,
}
SE_QUEDA = {"Cuidado dental", "Movilidad", "Salud", "Básculas",
            "Equipo de monitoreo médico"}


def cargar_sub_belleza():
    """sub_belleza() del clasificador, sin ejecutar su main."""
    src = open("scripts/clasificar_captura_perifericos.py", encoding="utf-8").read()
    src = src.split("captura = json.load")[0]
    g = {"__file__": "scripts/clasificar_captura_perifericos.py", "__name__": "_m"}
    exec(compile(src, "clasificador", "exec"), g)
    return g["T"], g["sub_belleza"]


def main():
    aplicar = "--aplicar" in sys.argv
    T, sub_belleza = cargar_sub_belleza()
    data = load_catalog()

    subs_destino = set()
    for c in data["categories"]:
        if c["id"] == NUEVA_BELLEZA:
            subs_destino = {s["id"] for s in c["subcategories"]}

    movidas = collections.Counter()
    quedan = collections.Counter()
    sin_destino = collections.Counter()
    for p in data["products"]:
        if p.get("category") != VIEJA:
            continue
        sub = p.get("subcategory")
        if sub not in MUEVE:
            quedan[sub] += 1
            continue
        destino = MUEVE[sub]
        if destino is None:
            destino = sub_belleza(T(p.get("name") or "")) or sub
        if destino not in subs_destino:
            # No inventamos subcategorías: si el destino no existe en la
            # categoría de belleza, la ficha se queda donde está.
            sin_destino[(sub, destino)] += 1
            quedan[sub] += 1
            continue
        movidas[(sub, destino)] += 1
        if aplicar:
            p["category"] = NUEVA_BELLEZA
            p["subcategory"] = destino

    print(f"A mover: {sum(movidas.values()):,}")
    for (o, d), n in movidas.most_common():
        print(f"  {n:6}  {o}  ->  {d}")
    if sin_destino:
        print("\nSin subcategoría de destino (se quedan):")
        for (o, d), n in sin_destino.most_common():
            print(f"  {n:6}  {o}  ->  {d}")
    print(f"\nSe quedan en {VIEJA}: {sum(quedan.values()):,}")
    for s, n in quedan.most_common():
        print(f"  {n:6}  {s}")

    if not aplicar:
        print("\n(ensayo: corré con --aplicar para escribir)")
        return

    for c in data["categories"]:
        if c["id"] == VIEJA:
            c["id"] = VIEJA_RENOMBRADA
            c["name"] = VIEJA_RENOMBRADA
            c["subcategories"] = [s for s in c["subcategories"] if s["id"] in SE_QUEDA]
    for p in data["products"]:
        if p.get("category") == VIEJA:
            p["category"] = VIEJA_RENOMBRADA
    save_catalog(data)
    print("\nCatálogo guardado.")


if __name__ == "__main__":
    main()
