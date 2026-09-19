#!/usr/bin/env python3
"""Arma los lotes de urls de Mercado Libre que faltan por enlace de afiliado,
listos para pegar en el generador del panel (Link Builder, 30 por vez).

POR QUÉ
-------
Mercado Libre no tiene API de afiliados ni un enlace base que envuelva
cualquier url: cada producto necesita su enlace generado en el panel, de a
30. El catálogo tiene 48,334 ofertas de Mercado Libre y solo 731 con enlace
(19 de septiembre de 2026). Generar todo a mano es inviable, así que el orden
importa: primero las fichas que tienen página pública (dos o más vendedores,
son las que reciben clics de buscadores), y dentro de ellas las de más
reseñas en Mercado Libre, que es lo más parecido a "más vendidas" que da la
API.

QUÉ PRODUCE
-----------
    data/ml-pendientes/lote-001.txt ... lote-NNN.txt   (30 urls cada uno)
    data/ml-pendientes/README.txt                      (el procedimiento)

Cada lote es lo que se pega en el generador. Lo que el panel devuelve se
guarda en data/ml-pendientes/salida.txt (todo junto, en cualquier orden,
de cuantos lotes se quiera) y ml_enlaces.py lo empareja por contenido:

    python3 scripts/ml_enlaces.py --entrada data/ml-pendientes/todas.txt \\
        --salida data/ml-pendientes/salida.txt
    python3 scripts/aplicar_afiliados.py --tienda mercadolibre

Al volver a correr este script, las urls que ya tienen enlace en
data/ml-afiliados.json desaparecen de los lotes; los números de lote se
rehacen desde 001.

USO
---
    python3 scripts/ml_lotes.py                # los 100 primeros lotes, priorizados
    python3 scripts/ml_lotes.py --solo-con-pagina
    python3 scripts/ml_lotes.py --max-lotes 50
"""
import argparse
import json
import os
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import load_catalog  # noqa: E402

MAPA = os.path.join(AQUI, "..", "data", "ml-afiliados.json")
CARPETA = os.path.join(AQUI, "..", "data", "ml-pendientes")
POR_LOTE = 30

README = """LOTES DE URLS PARA EL GENERADOR DE ENLACES DE MERCADO LIBRE
============================================================

1. Entra al panel de afiliados de Mercado Libre > "Generar enlaces".
2. Abre lote-001.txt, copia sus 30 urls y pégalas en el generador.
3. Copia TODO lo que devuelva el panel (los enlaces .../social/...) y
   pégalo al final de salida.txt (un enlace por línea). El orden no importa
   y pueden mezclarse varios lotes en el mismo archivo: el emparejado es por
   contenido, no por posición.
4. Sigue con lote-002.txt, lote-003.txt... los que alcances.
5. Cuando quieras aplicar lo que llevas:

   python3 scripts/ml_enlaces.py --entrada data/ml-pendientes/todas.txt --salida data/ml-pendientes/salida.txt
   python3 scripts/aplicar_afiliados.py --tienda mercadolibre
   python3 scripts/ml_lotes.py          # rehace los lotes sin lo ya enlazado

Los lotes van en orden de prioridad: primero los productos con página
pública (dos o más vendedores), ordenados por número de reseñas.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo-con-pagina", action="store_true",
                    help="solo fichas con dos o más ofertas")
    ap.add_argument("--max-lotes", type=int, default=100,
                    help="cuántos lotes escribir (0 = todos); 100 son 3,000 urls, más de lo que se genera en una semana")
    args = ap.parse_args()

    mapa = json.load(open(MAPA, encoding="utf-8")) if os.path.exists(MAPA) else {}
    data = load_catalog()
    pend = {}
    for p in data["products"]:
        ofertas = p.get("offers") or []
        for o in ofertas:
            if o.get("storeId") != "mercadolibre":
                continue
            url = (o.get("url") or "").split("?")[0]
            if not url or "/social/" in url or url in mapa:
                continue
            try:
                resenas = int(float(o.get("reviewCount") or 0))
            except ValueError:
                resenas = 0
            con_pagina = len(ofertas) >= 2
            if args.solo_con_pagina and not con_pagina:
                continue
            # clave de orden: con página primero, luego más reseñas
            pend[url] = (0 if con_pagina else 1, -resenas)
    urls = sorted(pend, key=lambda u: pend[u])
    con_pag = sum(1 for u in urls if pend[u][0] == 0)
    print(f"pendientes: {len(urls)}  (con página: {con_pag}, sin página: {len(urls) - con_pag})")

    if os.path.isdir(CARPETA):
        salida = os.path.join(CARPETA, "salida.txt")
        respaldo = open(salida, encoding="utf-8").read() if os.path.exists(salida) else None
        shutil.rmtree(CARPETA)
    else:
        respaldo = None
    os.makedirs(CARPETA)
    if respaldo:
        with open(os.path.join(CARPETA, "salida.txt"), "w", encoding="utf-8") as f:
            f.write(respaldo)
    lotes = [urls[i:i + POR_LOTE] for i in range(0, len(urls), POR_LOTE)]
    if args.max_lotes:
        lotes = lotes[:args.max_lotes]
    for n, lote in enumerate(lotes, 1):
        with open(os.path.join(CARPETA, f"lote-{n:03d}.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lote) + "\n")
    with open(os.path.join(CARPETA, "todas.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(u for lote in lotes for u in lote) + "\n")
    with open(os.path.join(CARPETA, "README.txt"), "w", encoding="utf-8") as f:
        f.write(README)
    print(f"{len(lotes)} lotes de {POR_LOTE} en {os.path.relpath(CARPETA)}/")


if __name__ == "__main__":
    main()
