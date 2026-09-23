#!/usr/bin/env python3
"""Con qué palabras arrancan los nombres de cada categoría, sacado del catálogo.

POR QUÉ
-------
El 23-sep-2026 se buscó de dónde venían los errores de clasificación que
llenaban la parte barata de las listas (tapetes en Laptops, imanes en
Refrigeradores). De 1,305 fichas corregidas, 1,071 las seguía clasificando
mal el clasificador de ese día: el error no era viejo, se iba a repetir con
cada captura. La causa común: las reglas buscan la palabra de la categoría
EN CUALQUIER PARTE del título, y la encuentran donde es complemento o
atributo, no sujeto:

    "Kazoo, un buen compañero para GUITARRA"        -> Guitarras
    "Organizador de zapatos para CLOSET"            -> Roperos
    "Pulsera de CHAPA de oro"                       -> Cerraduras (chapa)
    "Cuerpo de aceleración para Dodge CHARGER"      -> Cargadores
    "Sillón de masaje con ALTAVOZ"                  -> Bocinas
    "Tapete ... 27 pulgadas, PORTÁTIL"              -> Laptops

Un nombre de producto arranca por lo que ES. Este script anota, para cada
categoría, las palabras con que arrancan los nombres de sus fichas (con su
lift contra el catálogo entero, como atipicos.py), y para cada sustantivo
de arranque frecuente, a qué categoría pertenece casi siempre. El
clasificador (clasificar_captura_perifericos.py) lo usa para revisar cada
decisión de sus reglas: si la regla dice "Herramientas" pero el nombre
arranca por "pulsera", manda el sustantivo.

Se regenera en cada corrida (final7), así que aprende de cada corrección.

    python3 scripts/vocabulario_cabeza.py
"""
import collections
import json
import os
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atipicos  # noqa: E402
from data_io import load_catalog  # noqa: E402

SALIDA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "data", "vocabulario-cabeza.json")
LIFT_MIN = 3.0
FRACCION_MIN = 0.01      # la palabra aparece en al menos 1% de los arranques de la categoría
MIN_FICHAS_PALABRA = 25  # un sustantivo con menos apariciones no decide nada
SHARE_SUSTANTIVO = 0.7   # y decide sólo si el 70% de las fichas que arrancan con él son de UNA categoría
# Una marca no es un sustantivo: «Xiaomi Air Fryer» arranca por Xiaomi y el
# 95% de lo que arranca por Xiaomi es un celular. Se descarta la palabra si
# es la marca de al menos MIN_FICHAS_MARCA fichas y eso es al menos el 5% de
# las que arrancan con ella («silla» es la marca de tres fichas entre miles
# de sillas: sigue valiendo).
MIN_FICHAS_MARCA = 3
FRACCION_MARCA = 0.05


def _plano(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def main():
    productos = load_catalog()["products"]
    antes = atipicos.PALABRAS_CABEZA
    atipicos.PALABRAS_CABEZA = 4
    por_cat = collections.defaultdict(collections.Counter)
    n_cat = collections.Counter()
    global_df = collections.Counter()
    primera = collections.defaultdict(collections.Counter)
    icono = collections.defaultdict(collections.Counter)
    marcas = collections.Counter(_plano(p.get("brand")) for p in productos if p.get("brand"))
    total = 0
    for p in productos:
        cab = atipicos.cabeza(p)
        palabras = {w for w, _ in cab}
        global_df.update(palabras)
        total += 1
        cat = p.get("category")
        if not cat:
            continue
        por_cat[cat].update(palabras)
        n_cat[cat] += 1
        if cab:
            primera[cab[0][0]][(cat, p.get("subcategory"))] += 1
            if p.get("image"):
                icono[(cab[0][0], cat, p.get("subcategory"))][p["image"]] += 1
    atipicos.PALABRAS_CABEZA = antes

    cats = {}
    for cat, cuenta in por_cat.items():
        n = n_cat[cat]
        voc = {}
        for w, c in cuenta.items():
            if c < max(3, FRACCION_MIN * n):
                continue
            lift = (c / n) / (global_df[w] / total)
            if lift >= LIFT_MIN:
                voc[w] = round(lift, 1)
        cats[cat] = voc

    sustantivos = {}
    for w, cuenta in primera.items():
        tot = sum(cuenta.values())
        if tot < MIN_FICHAS_PALABRA:
            continue
        if marcas[w] >= MIN_FICHAS_MARCA and marcas[w] >= FRACCION_MARCA * tot:
            continue
        por_categoria = collections.Counter()
        for (cat, _), c in cuenta.items():
            por_categoria[cat] += c
        cat, c = por_categoria.most_common(1)[0]
        if c / tot < SHARE_SUSTANTIVO:
            continue
        sub, _ = max(((s, k) for (cc, s), k in cuenta.items() if cc == cat), key=lambda t: t[1])
        img = icono[(w, cat, sub)].most_common(1)
        sustantivos[w] = [cat, sub, round(c / tot, 2), tot, img[0][0] if img else "box"]

    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump({"cats": cats, "sustantivos": sustantivos}, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(cats)} categorías, {sum(len(v) for v in cats.values()):,} palabras; "
          f"{len(sustantivos):,} sustantivos que deciden -> {os.path.relpath(SALIDA)}")


if __name__ == "__main__":
    main()
