#!/usr/bin/env python3
"""Marcas que Elektra cambió por otra parecida.

POR QUÉ (27-sep-2026)
---------------------
El feed de Elektra (VTEX, marketplace) no trae la marca que escribió el
vendedor sino la más parecida de su propio catálogo de marcas. El título
dice la verdadera y el campo dice otra:

    «Pañales Pura talla N 28 unidades»                    brand=PURINA
    «Mochila Travelon Classic Grande Antirrobo 20L»       brand=REVLON
    «SSD TEAMGROUP MP33PRO 2TB NVMe»                      brand=TEGO
    «Esponja de Soldadura Metcal AC-Y10»                  brand=METAMUCIL
    «Rubor en Polvo Benefit WANDERful World»              brand=BENETTON

Medido el 27-sep-2026 en los shards publicados: en 47% de las fichas de
sólo Elektra la marca no aparece en el título (en Bodega 8%, Coppel 26% casi
todo «Genérica», Mercado Libre 15%). Cuando además hay en el título una
palabra que se le parece (mismas dos primeras letras, parecido >= 0.6) son
7,507 fichas de sólo Elektra y en una muestra de 30 la marca estaba mal en
28. En las otras tiendas esa misma señal casi siempre es la marca bien
escrita de otra forma («Kumho Tire» / kumho), por eso esto es SÓLO para
marcas escritas como las escribe Elektra (todo mayúsculas) en fichas con
oferta de Elektra.

Qué rompía:
  - la página /marca/purina/ listaba pañales, la de Revlon mochilas;
  - las fusiones: merge_amazon_cross_store compara marcas y, si las dos
    fichas tienen una y no son iguales, no fusiona («marca distinta», 31,023
    fichas en la corrida del 27-sep). Una marca vacía, en cambio, se busca en
    el título de la otra ficha.

Qué hace: la marca pasa a ser la palabra del título que se le parece, si esa
palabra está escrita con mayúscula; si está en minúscula, queda vacía (vacía
es mejor que equivocada). Si la palabra parecida es una palabra corriente
(«Acero» por ACROS) no se toca: ahí el parecido es casualidad.

USO
---
    python3 scripts/sanear_marcas.py              # informe
    python3 scripts/sanear_marcas.py --aplicar
"""
import argparse
import collections
import difflib
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import load_catalog, save_catalog, texto_plano  # noqa: E402

PARECIDO = 0.6
# Una palabra que aparece en minúscula en tantos títulos es una palabra
# corriente, no una marca.
MAX_MINUSCULA = 20
RX_GENERICA = re.compile(r"^(generic[oa]?s?|sin marca|n a|na|none|otros?|varios)$")
RX_PALABRA = re.compile(r"[A-Za-zÀ-ÿÏï][A-Za-zÀ-ÿÏï0-9]{2,}")


def _plano(s):
    return re.sub(r"[^a-z0-9]+", " ", texto_plano(s or "")).strip()


def marca_en_titulo(marca, nombre):
    m, n = _plano(marca), _plano(nombre)
    if not m:
        return True
    # «ROGGA HOME» en «Base de Cama Rogga Gris»: la primera palabra basta.
    primera = m.split()[0]
    if " " in m and len(primera) >= 4 and re.search(r"(?<![a-z0-9])" + re.escape(primera) + r"(?![a-z0-9])", n):
        return True
    return (re.search(r"(?<![a-z0-9])" + re.escape(m) + r"(?![a-z0-9])", n) is not None
            or m.replace(" ", "") in n.replace(" ", ""))


def palabra_parecida(marca, nombre):
    """(palabra del título, parecido) más parecida a la marca, o (None, 0)."""
    m = _plano(marca).replace(" ", "")
    mejor, r = None, 0.0
    # La primera palabra no: en Elektra es el tipo de producto («Termo Goku
    # Blanco» con marca TERMOMANIA), no la marca.
    for w in RX_PALABRA.findall(nombre or "")[1:]:
        wp = _plano(w).replace(" ", "")
        if wp[:2] != m[:2]:
            continue
        x = difflib.SequenceMatcher(None, m, wp).ratio()
        if x > r:
            mejor, r = w, x
    return mejor, r


def es_de_elektra(p):
    marca = (p.get("brand") or "").strip()
    return (any(o.get("storeId") == "elektra" for o in p.get("offers") or [])
            and marca == marca.upper() and any(c.isalpha() for c in marca))


def minusculas(products):
    """{palabra: nº de títulos de Elektra donde aparece escrita en minúscula}.

    Sólo Elektra: escribe sus títulos con minúscula salvo nombres propios.
    Bodega y Walmart los escriben todo en minúscula (ahí «magefesa» sale en
    minúscula y no por eso es palabra corriente) y Coppel pone mayúscula a
    cada palabra."""
    c = collections.Counter()
    for p in products:
        if {o.get("storeId") for o in p.get("offers") or []} != {"elektra"}:
            continue
        for w in set(RX_PALABRA.findall(p.get("name") or "")):
            if w[0].islower():
                c[_plano(w)] += 1
    return c


def correccion(p, comunes):
    """Marca nueva (posiblemente "") o None si no hay nada que corregir."""
    marca = p.get("brand") or ""
    if (not es_de_elektra(p) or RX_GENERICA.match(_plano(marca))
            or marca_en_titulo(marca, p.get("name"))):
        return None
    w, r = palabra_parecida(marca, p.get("name"))
    if w is None or r < PARECIDO:
        return None
    if comunes.get(_plano(w), 0) >= MAX_MINUSCULA:
        # Se parece a una palabra corriente («Acero» por ACROS): no es la
        # señal de que Elektra la cambió, se deja como está.
        return None
    return w if w[0].isupper() else ""


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--muestra", type=int, default=40)
    args = ap.parse_args()

    data = load_catalog()
    products = data["products"]
    comunes = minusculas(products)
    cambios = []
    for p in products:
        nueva = correccion(p, comunes)
        if nueva is not None:
            cambios.append((p, p.get("brand"), nueva))
    vacias = sum(1 for _, _, n in cambios if not n)
    print(f"Marcas de Elektra que no son las del título: {len(cambios):,} "
          f"(corregidas por la del título {len(cambios) - vacias:,}, vaciadas {vacias:,})")
    for p, vieja, nueva in cambios[:: max(1, len(cambios) // args.muestra)][: args.muestra]:
        print(f"  {p['id']:>9}  {vieja[:18]:18} -> {nueva[:18] or '(vacía)':18}  {p['name'][:70]}")
    if args.aplicar and cambios:
        for p, _, nueva in cambios:
            p["brand"] = nueva
        save_catalog(data)
        print("Guardado.")


if __name__ == "__main__":
    main()
