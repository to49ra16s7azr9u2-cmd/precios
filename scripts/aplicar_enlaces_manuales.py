#!/usr/bin/env python3
"""Enlaces de afiliado puestos a mano (SiteStripe de Amazon, etc.).

El usuario copia en SiteStripe el enlace de un producto concreto de Amazon y
lo pasa; acá se guarda en data/enlaces-manuales.json con las fichas a las que
corresponde, y cada regeneración lo vuelve a poner como `enlaces` (el botón
«Ver precio en Amazon» va directo a ese producto en vez de a la búsqueda).
Sin precio: la tienda está en «solo enlace» (tienda_solo_enlace.py).

Formato de data/enlaces-manuales.json:
    [{"storeId": "amazon_mx", "url": "...", "ids": ["p26570", ...],
      "nota": "iPhone 17 256 GB (SiteStripe, 26-sep-2026)"}]

USO
---
    python3 scripts/aplicar_enlaces_manuales.py
"""
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import ROOT, load_catalog, save_catalog  # noqa: E402

ARCHIVO = os.path.join(ROOT, "data", "enlaces-manuales.json")


def main():
    if not os.path.exists(ARCHIVO):
        print("sin enlaces manuales")
        return
    reglas = json.load(open(ARCHIVO, encoding="utf-8"))
    data = load_catalog()
    por_id = {p["id"]: p for p in data["products"]}
    puestos = cambiados = faltan = 0
    for r in reglas:
        for pid in r["ids"]:
            p = por_id.get(pid)
            if not p:
                faltan += 1
                continue
            enl = p.setdefault("enlaces", [])
            actual = next((e for e in enl if e.get("storeId") == r["storeId"]), None)
            if actual is None:
                enl.append({"storeId": r["storeId"], "url": r["url"]})
                puestos += 1
            elif actual.get("url") != r["url"]:
                actual["url"] = r["url"]
                cambiados += 1
    if puestos or cambiados:
        save_catalog(data)
    print(f"enlaces manuales: {puestos} nuevos, {cambiados} actualizados, {faltan} fichas que ya no están")


if __name__ == "__main__":
    main()
