#!/usr/bin/env python3
"""Toma lo que capturó la extensión de Chrome (ver conversación: popup.js
exporta {asin, title, price, photo, url} por producto) y para cada uno busca
el product_id que le corresponde en el catálogo de ComparaMEX -- el paso que
faltaba entre "capturé datos de Amazon" y add_amazon_offers.py.

CRITERIO DE MATCHING
---------------------
El proyecto ya probó el matching difuso por título puro en otra etapa y dio
falsos positivos a montones (dos productos con nombre parecido pero
distinto). Acá se aplica el mismo criterio conservador que en
audit_cross_store.py:

  - Si el título capturado y un candidato mencionan una capacidad
    (256GB/128GB/1TB) y NO coinciden, el candidato queda excluido aunque
    comparta muchas otras palabras -- una contradicción de capacidad es la
    señal más fuerte de que es OTRO producto.
  - Entre lo que sobrevive ese filtro, se puntúa por palabras en común
    (4+ letras, sin relleno) + bonus si coincide color y variante
    (Pro Max/Pro/Plus/Mini/Air/SE).
  - Solo se asigna automático si hay un candidato con el puntaje más alto
    de forma NO empatada y por encima de un mínimo. Cualquier otro caso
    (cero candidatos, empate, puntaje bajo) se deja para revisión manual
    con la lista de candidatos a la vista -- nunca se adivina.

USO
---
    python3 scripts/match_amazon_capture.py captura.json
    python3 scripts/match_amazon_capture.py captura.json -o resuelto.json

`captura.json` es la lista exportada por la extensión. La salida
(resuelto.json, o captura.resuelto.json si no se pasa -o) es una lista lista
para revisar y pasarle a add_amazon_offers.py: los ítems ya resueltos traen
`product_id`; los que necesitan una decisión traen `candidates` en vez de
`product_id`, para completar a mano antes de importar.
"""
import argparse
import json
import os
import re
import sys
import unicodedata
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog  # noqa: E402

STOP = {
    "para", "con", "del", "los", "las", "por", "que", "este", "esta", "color",
    "pack", "paquete", "unidades", "pulgadas", "pulg", "inch", "the", "and",
    "with", "for",
}
VARIANTS = ("pro max", "pro", "plus", "mini", "air", "se")
COLORS = (
    "negro", "black", "blanco", "white", "azul", "blue", "rosa", "pink",
    "dorado", "gold", "plata", "silver", "gris", "gray", "grey", "verde",
    "green", "morado", "purpura", "purple", "naranja", "orange", "titanio",
    "titanium", "rojo", "red", "amarillo", "yellow",
)
MIN_SCORE = 3


def norm(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def words(s):
    return {t for t in re.split(r"[^a-z]+", norm(s)) if len(t) >= 4} - STOP


def capacities(s):
    return set(re.findall(r"(\d+)\s*(gb|tb)\b", norm(s).replace("-", " ")))


def variant_of(s):
    n = norm(s)
    for v in VARIANTS:
        if v in n:
            return v
    return None


def color_of(s):
    n = norm(s)
    for c in COLORS:
        if re.search(rf"\b{c}\b", n):
            return c
    return None


def candidates_for(item, products):
    title = item.get("title") or ""
    tw = words(title)
    if not tw:
        return []
    tc = capacities(title)
    tv = variant_of(title)
    tcol = color_of(title)

    scored = []
    for p in products:
        pw = words(p["name"])
        overlap = tw & pw
        if not overlap:
            continue
        pc = capacities(p["name"])
        if tc and pc and not (tc & pc):
            continue  # contradicción de capacidad: descartado sin más vueltas
        score = len(overlap)
        pv = variant_of(p["name"])
        if tv and pv:
            score += 2 if tv == pv else -3
        elif tv and not pv:
            score -= 1  # el candidato no menciona la variante que sí trae el título capturado
        pcol = color_of(p["name"])
        if tcol and pcol:
            score += 1 if tcol == pcol else -2
        if tc and pc and (tc & pc):
            score += 2
        scored.append((score, p))
    scored.sort(key=lambda sp: -sp[0])
    return scored


def resolve(item, products):
    scored = candidates_for(item, products)
    if not scored:
        return None, []
    top_score = scored[0][0]
    tied = [p for s, p in scored if s == top_score]
    if len(tied) == 1 and top_score >= MIN_SCORE:
        return tied[0], scored[:5]
    return None, scored[:5]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--output")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        captured = json.load(f)

    data = load_catalog()
    products = data["products"]

    out = []
    auto, review = 0, 0
    for item in captured:
        asin = item.get("asin")
        if not asin:
            continue
        match, top5 = resolve(item, products)
        row = {"asin": asin, "price": item.get("price"), "photo": item.get("photo")}
        if match:
            row["product_id"] = match["id"]
            row["_matched_name"] = match["name"]  # informativo, add_amazon_offers.py lo ignora
            print(f"  OK  {asin}  '{item.get('title', '')[:45]}'")
            print(f"        -> {match['id']}  {match['name'][:55]}")
            auto += 1
        else:
            row["candidates"] = [
                {"product_id": p["id"], "name": p["name"], "score": s} for s, p in top5
            ]
            print(f"  ??  {asin}  '{item.get('title', '')[:45]}'  ({len(top5)} candidatos, revisar a mano)")
            for s, p in top5:
                print(f"        [{s:>2}] {p['id']}  {p['name'][:55]}")
            review += 1
        out.append(row)

    out_path = args.output or (os.path.splitext(args.input)[0] + ".resuelto.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"\nResueltos automáticamente: {auto}   Necesitan revisión manual: {review}")
    print(f"Escrito: {out_path}")
    if review:
        print("Completá 'product_id' en los que quedaron con 'candidates' antes de "
              "pasarle el archivo a add_amazon_offers.py.")


if __name__ == "__main__":
    main()
