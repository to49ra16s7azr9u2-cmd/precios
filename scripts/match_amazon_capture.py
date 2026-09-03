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
    # "titanio natural" y "titanio del desierto" van primero y a propósito:
    # son colores DISTINTOS del iPhone Pro, y ni "natural" ni "desierto" son
    # palabras de color por sí solas -- así que sin esta entrada compuesta
    # los dos colapsaban al "titanio" genérico y se leían como el mismo
    # color (se vio un caso real: un 16 Pro Titanio del Desierto resolvió
    # solo contra un candidato Titanio Natural). "Titanio Negro"/"Titanio
    # Blanco" NO necesitan esto -- "negro"/"blanco" ya son colores por sí
    # solos más abajo en la lista, y agregarlos acá como compuestos
    # rompía la comparación contra un candidato que dice apenas "Negro"
    # sin la palabra "titanio".
    "titanio natural", "natural titanium", "titanio del desierto",
    "desert titanium",
    "negro", "black", "blanco", "white", "azul", "blue", "rosa", "pink",
    "dorado", "gold", "plata", "silver", "gris", "gray", "grey", "verde",
    "green", "morado", "purpura", "purple", "naranja", "orange", "titanio",
    "titanium", "rojo", "red", "amarillo", "yellow", "grafito", "graphite",
    "medianoche", "media noche", "midnight", "salvia", "sage", "oro",
)
MIN_SCORE = 3


def norm(s):
    # Separar transiciones minúscula->mayúscula ANTES de pasar todo a
    # minúsculas -- varios títulos capturados vienen con palabras pegadas
    # por un salto de línea que se perdió al leer la página ("EsimMorado",
    # "128GBNegroDesbloqueado"). Sin este split, "\bmorado\b" no encuentra
    # límite de palabra dentro de "esimmorado" y el color desaparece sin
    # aviso -- eso fue lo que dejó pasar una coincidencia con la variante
    # equivocada de color en la corrida real de esta captura.
    #
    # OJO: "iPhone" en sí mismo es una transición minúscula->mayúscula
    # ("i" + "Phone") -- sin esta excepción, el split de arriba rompe
    # "iphone" en "i phone" y con eso deja de encontrar el ancla que usan
    # generation_of/VARIANT_RE, lo cual fue MUCHO peor que el bug que se
    # quería arreglar (varias generaciones distintas volvieron a
    # confirmarse solas). Se normaliza el nombre de marca primero para que
    # no le quede ninguna transición de mayúscula que partir.
    s = re.sub(r"iphone", "iphone", s or "", flags=re.IGNORECASE)
    s = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", s)
    # "128GBNegro": GB y la palabra siguiente quedan mayúscula-mayúscula, así
    # que el split de arriba no lo separa -- y sin el espacio, capacities()
    # no encuentra el límite de palabra que necesita después de "gb"/"tb" y
    # la capacidad del propio título capturado desaparece (se vio un caso
    # real: un 128GB así resolvió solo contra un candidato de 256GB porque
    # ya no había nada con qué contradecirlo).
    s = re.sub(r"(\d+\s*(?:gb|tb))(?=[a-zA-Z])", r"\1 ", s, flags=re.IGNORECASE)
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def words(s):
    return {t for t in re.split(r"[^a-z]+", norm(s)) if len(t) >= 4} - STOP


def capacities(s):
    n = norm(s).replace("-", " ")
    caps = set(re.findall(r"(\d+)\s*(gb|tb)\b", n))
    # Algunos anuncios escriben "128G" en vez de "128GB" -- pero una "G"
    # suelta también es como se escribe la generación de red ("4G", "5G"),
    # así que solo cuenta como almacenamiento cuando el número tiene 2+
    # dígitos: ningún almacenamiento real es de 1-9 GB, y no existe una red
    # "64G". Sin este piso, "128G" se perdía por completo -- se vio un caso
    # real de un 64GB capturado resolviendo solo contra un candidato de
    # 128G porque no había nada con qué contradecirlo.
    caps |= {(num, "gb") for num in re.findall(r"\b(\d{2,4})g\b", n)}
    return caps


def generation_of(s):
    # El número de generación ("14", "15", "16e", "17"...) es el dato que MÁS
    # importa para no confundir un iPhone con otro -- y words() lo descarta
    # por completo, porque el regex de tokenización trata los dígitos como
    # separadores. Sin esto, "iPhone 14" y "iPhone 15 Pro" comparten tantas
    # palabras (apple/iphone/gb/color/...) que el puntaje los daba por
    # iguales; así fue como salieron auto-confirmados varios pares de
    # generación distinta en la primera corrida real.
    m = re.search(r"iphone\s*(\d{1,2})\s*(e)?\b", norm(s))
    if not m:
        return None
    return m.group(1) + (m.group(2) or "")


VARIANT_RE = re.compile(
    r"iphone\s*(?:\d{1,2}e?)?\s*(" + "|".join(re.escape(v) for v in VARIANTS) + r")\b"
)


def variant_of(s):
    # Tiene que anclarse justo después de "iphone" (como aparece siempre en
    # un título/nombre real: "iPhone 17 Pro Max", "iPhone Air"...), y no
    # buscar la palabra suelta en cualquier parte del texto. Dos bugs reales
    # que dio esa versión más simple:
    #   - "se" como substring aparece dentro de "disenado", "trasera", etc.
    #     (arreglado antes con \b, pero \b solo no alcanza)
    #   - "Chip A19 Pro" aparece en la descripción de CUALQUIER iPhone de
    #     gama alta, incluido el iPhone Air -- así que "pro" suelto se
    #     detectaba como si el propio teléfono fuera el modelo Pro.
    m = VARIANT_RE.search(norm(s))
    return m.group(1) if m else None


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
    tg = generation_of(title)

    scored = []
    for p in products:
        pw = words(p["name"])
        overlap = tw & pw
        if not overlap:
            continue
        # "iphone" es la palabra que más importa de todas para este catálogo
        # -- si el título capturado la trae, el candidato tiene que traerla
        # también. Sin este chequeo, un "iPhone XR" resolvió solo contra un
        # iPad de la misma capacidad y color: nada en el puntaje exigía que
        # el candidato fuera siquiera un iPhone, porque "iphone" en sí no es
        # una de las palabras que se comparan a propósito (capacidad,
        # generación, variante, color) y una palabra ausente de un lado no
        # resta puntos, solo deja de sumarlos.
        if "iphone" in tw and "iphone" not in pw:
            continue
        pc = capacities(p["name"])
        if tc and pc and not (tc & pc):
            continue  # contradicción de capacidad: descartado sin más vueltas
        pg = generation_of(p["name"])
        if tg and pg and tg != pg:
            continue  # contradicción de generación (14 vs 15 Pro, 16 vs 16e, ...): descartado
        pcol = color_of(p["name"])
        if tcol and pcol and tcol != pcol:
            continue  # contradicción de color: descartado (a diferencia de capacidad y
            # generación, el color a veces se corrige con un bonus más abajo,
            # pero un choque directo -- grafito vs azul -- es tan mal candidato
            # como una capacidad distinta: se vio un caso real donde ganaba por
            # el bonus de variante a pesar del color equivocado)
        pv = variant_of(p["name"])
        if tv != pv:
            continue  # Pro Max, Pro, Plus, Mini, Air, SE y "base" (ninguno de esos)
            # son equipos DISTINTOS con precio distinto, no una diferencia de
            # redacción -- mismo criterio que capacidad/generación/color. Un
            # nombre de catálogo bien armado dice "Pro" cuando lo es y no lo
            # dice cuando no lo es (y lo mismo vale para el título capturado),
            # así que si no coinciden ninguno de los dos es el otro -- se vio
            # un caso real donde un "iPhone 15" base ganaba por pura suerte de
            # palabras contra un "iPhone 15 Plus" en el catálogo.
        score = len(overlap)
        if tv and pv:
            score += 2
        if tcol and pcol and tcol == pcol:
            score += 1
        if tc and pc and (tc & pc):
            score += 2
        if tg and pg and tg == pg:
            score += 2
        scored.append((score, p))
    scored.sort(key=lambda sp: -sp[0])
    return scored


def resolve(item, products):
    title = item.get("title") or ""
    scored = candidates_for(item, products)
    if not scored:
        return None, []
    top_score = scored[0][0]
    tied = [p for s, p in scored if s == top_score]
    if "iphone" not in words(title):
        # generation_of()/VARIANT_RE -- las dos protecciones que evitan
        # confundir un modelo con otro -- están ancladas a la palabra
        # "iphone" y no hacen nada para el resto del catálogo. Sin ellas
        # acá solo queda overlap de palabras + capacidad + color, que
        # resultó insuficiente: en una corrida real con celulares que no
        # son iPhone, un Huawei se confirmó solo contra un Samsung, otro
        # contra unos audífonos, y varios pares Galaxy/Redmi/Pura con
        # número de modelo distinto (S23+ vs S24+, Note 14 vs Note 15,
        # Pura 70 vs Pura 90s) se dieron por iguales. Hasta que haya un
        # chequeo de marca/modelo tan estricto como el de iPhone, todo lo
        # que no diga "iphone" va a revisión manual sin excepción.
        return None, scored[:5]
    if len(tied) == 1 and top_score >= MIN_SCORE:
        match = tied[0]
        tcol = color_of(item.get("title") or "")
        pcol = color_of(match["name"])
        if tcol and not pcol:
            # El título capturado trae color pero el nombre del candidato no
            # menciona ninguno -- no hay forma de confirmar que sea el mismo
            # color, y un nombre "genérico" así le gana por overlap de
            # palabras a cualquier variante de color real del mismo modelo
            # (se vio un caso real: dos capturas de colores distintos
            # resolviendo las DOS al mismo producto sin color declarado).
            # Mejor mandar a revisión manual que asumir.
            return None, scored[:5]
        return match, scored[:5]
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
