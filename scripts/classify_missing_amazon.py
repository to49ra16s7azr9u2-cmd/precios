#!/usr/bin/env python3
"""Clasifica los ítems de una captura de Amazon YA CORRIDA por
match_amazon_capture.py (con `candidates` para los no auto-confirmados)
en tres grupos, a pedido explícito del usuario tras ver ~200 capturas sin
agregar por ambigüedad de compañía telefónica:

  new_model     ningún candidato en el catálogo -- el modelo no existe
                todavía, hay que darlo de alta como producto nuevo.
  carrier_only  todos los candidatos son EL MISMO equipo (mismo nombre
                una vez sacada la palabra de compañía) en distintas
                versiones de compañía (AT&T/Telcel/Movistar/Libre) -- si
                el título de Amazon dice "desbloqueado"/"libre" se
                resuelve directo contra el candidato "Libre"; si no dice
                nada, es candidato a crear una versión "Otro".
  real_ambiguity los candidatos difieren en algo más que la compañía
                (color, capacidad, modelo distinto) -- sigue habiendo
                una ambigüedad real que no corresponde adivinar, se deja
                para revisión manual como siempre.

USO
---
    python3 scripts/classify_missing_amazon.py <resuelto.json> <input_original.json>

`input_original.json` es el archivo que se le pasó a match_amazon_capture.py
-- el resuelto no trae "title" (solo asin/price/photo/candidates), y hace
falta para mostrar algo legible.
"""
import json
import re
import sys

CARRIER_RE = re.compile(r"\b(AT&T|Telcel|Movistar|Libre)\b", re.IGNORECASE)
UNLOCKED_HINT_RE = re.compile(r"\b(desbloqueado|desbloqueada|unlocked|libre)\b", re.IGNORECASE)


def norm_no_carrier(name):
    s = CARRIER_RE.sub("", name)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def main():
    items = json.load(open(sys.argv[1], encoding="utf-8"))
    titles = {}
    if len(sys.argv) > 2:
        for it in json.load(open(sys.argv[2], encoding="utf-8")):
            titles[it["asin"]] = it.get("title", "")
    for it in items:
        it["title"] = titles.get(it["asin"], "")

    new_model, carrier_only, real_ambiguity, already_ok = [], [], [], []
    for it in items:
        if "candidates" not in it:
            already_ok.append(it)
            continue
        cands = it["candidates"]
        if not cands:
            new_model.append(it)
            continue
        # candidates_for() devuelve el top-5 por score, no solo los que de
        # verdad empatan -- un caso real: "Samsung Galaxy A16 4GB 128GB
        # Gris" trajo los 3 candidatos AT&T/Movistar/Libre EMPATADOS en
        # score 8, más una tablet y un duplicado con "Gray" en inglés en
        # los puestos 4 y 5 con score menor. Sin filtrar por el score más
        # alto, esos dos ruidos rompían la comparación "todos son el mismo
        # equipo" y el caso se perdía como ambigüedad real. Solo los
        # candidatos EMPATADOS en el score más alto cuentan acá.
        top_score = max(c["score"] for c in cands)
        top_cands = [c for c in cands if c["score"] == top_score]
        # Con UN solo candidato en el tope, "todas las firmas son iguales"
        # es trivial (hay una sola) -- eso NO es ambigüedad de compañía, es
        # un candidato débil sin nada mejor cerca (score bajo, sin
        # color/modelo declarado, etc.). Un caso real: "XIAOMI Poco M7,
        # Plata, 256GB" con un único candidato que era un LABIAL.
        if len(top_cands) < 2:
            real_ambiguity.append(it)
            continue
        sigs = {norm_no_carrier(c["name"]) for c in top_cands}
        if len(sigs) == 1:
            it["candidates"] = top_cands  # descarta el ruido de score menor
            carrier_only.append(it)
        else:
            real_ambiguity.append(it)

    print(f"ya resueltos (no deberían estar acá): {len(already_ok)}")
    print(f"modelo nuevo (sin ningún candidato):   {len(new_model)}")
    print(f"solo ambiguo por compañía:             {len(carrier_only)}")
    print(f"ambigüedad real (color/modelo/etc):    {len(real_ambiguity)}")

    json.dump(new_model, open("new_model.json", "w"), ensure_ascii=False, indent=2)
    json.dump(carrier_only, open("carrier_only.json", "w"), ensure_ascii=False, indent=2)
    json.dump(real_ambiguity, open("real_ambiguity.json", "w"), ensure_ascii=False, indent=2)

    print("\n--- modelo nuevo ---")
    for it in new_model:
        print(f"  {it['asin']}  {it['title'][:80]}")

    print("\n--- solo ambiguo por compañía (candidatos) ---")
    for it in carrier_only:
        unlocked = "DESBLOQUEADO" if UNLOCKED_HINT_RE.search(it["title"]) else ""
        print(f"  {it['asin']}  {it['title'][:70]}  {unlocked}")
        for c in it["candidates"][:5]:
            print(f"        {c['product_id']}  {c['name'][:70]}")


if __name__ == "__main__":
    main()
