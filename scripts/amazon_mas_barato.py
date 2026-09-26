#!/usr/bin/env python3
"""¿Qué tan seguido Amazon tiene el precio más bajo? Por subcategoría.

QUÉ ES
------
Para cada ficha que tiene precio de Amazon Y de al menos otra tienda, se
mira si Amazon era la más barata (más de 0.5% por debajo de la mejor de las
demás). El porcentaje se da por subcategoría; donde hay menos de MIN_N
comparaciones se sube a la categoría, y si tampoco alcanza, al total.

El botón «Buscar en Amazon» de la ficha lo muestra al lado del título
(js/app.js y generate_seo_pages.py: amazon_mas_barato_texto).

APAGADO POR AHORA (26-sep-2026)
-------------------------------
Hoy la única fuente de precios de Amazon son las capturas de septiembre
(data/tiendas-ocultas.json.gz, tienda amazon_mx), que NO vienen de la API.
Las reglas de Amazon Afiliados piden que lo que se muestre de sus precios
venga de la API y esté al día, así que el archivo sale con "activo": false y
queda fuera de lo publicado (_config.yml, exclude). El sitio no muestra nada.

Para prenderlo: con la Creators API (o un permiso escrito de Amazon
Afiliados), recalcular con esos precios, correr con --activar y sacar
data/amazon-mas-barato.json del exclude de _config.yml.

USO
---
    python3 scripts/amazon_mas_barato.py              # informe + archivo apagado
    python3 scripts/amazon_mas_barato.py --activar    # sólo con datos de la API
"""
import argparse
import collections
import datetime
import gzip
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import DATA_DIR, load_catalog  # noqa: E402

SALIDA = os.path.join(DATA_DIR, "amazon-mas-barato.json")
OCULTAS = os.path.join(DATA_DIR, "tiendas-ocultas.json.gz")
MIN_N = 20          # comparaciones mínimas para dar un porcentaje propio
MARGEN = 0.995      # Amazon tiene que estar 0.5% por debajo: un empate no cuenta


def precios_amazon():
    with gzip.open(OCULTAS, "rt", encoding="utf-8") as f:
        d = json.load(f)
    out = collections.defaultdict(list)
    for x in d.get("ofertas") or []:
        o = x.get("offer") or {}
        if o.get("storeId") == "amazon_mx" and o.get("price"):
            out[x["productId"]].append(o["price"])
    return {pid: min(v) for pid, v in out.items()}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--activar", action="store_true", help="sólo con precios de la API de Amazon")
    args = ap.parse_args()
    amz = precios_amazon()
    data = load_catalog()
    por_sub = collections.defaultdict(lambda: [0, 0])
    por_cat = collections.defaultdict(lambda: [0, 0])
    total = [0, 0]
    for p in data["products"]:
        a = amz.get(p["id"])
        if not a:
            continue
        otras = [o["price"] for o in p.get("offers") or [] if o.get("price") and o.get("storeId") != "amazon_mx"]
        for v in p.get("colorVariants") or []:
            otras += [o["price"] for o in v.get("offers") or [] if o.get("price") and o.get("storeId") != "amazon_mx"]
        if not otras:
            continue
        gana = int(a < min(otras) * MARGEN)
        for acc in (por_sub[f"{p['category']}|{p.get('subcategory') or ''}"], por_cat[p["category"]], total):
            acc[0] += gana
            acc[1] += 1

    def pct(v):
        return [round(100 * v[0] / v[1]), v[1]]

    salida = {
        "activo": bool(args.activar),
        "fecha": datetime.date.today().isoformat(),
        "fuente": "api" if args.activar else "capturas de septiembre de 2026 (no API; no publicar)",
        "min_n": MIN_N,
        "subcategorias": {k: pct(v) for k, v in por_sub.items() if v[1] >= MIN_N},
        "categorias": {k: pct(v) for k, v in por_cat.items() if v[1] >= MIN_N},
        "total": pct(total) if total[1] else None,
    }
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, separators=(",", ":"))
    print(f"comparaciones: {total[1]:,}; Amazon más barato: {salida['total'][0] if total[1] else '-'}%")
    print(f"subcategorías con porcentaje propio: {len(salida['subcategorias'])}; categorías: {len(salida['categorias'])}")
    print(f"-> {SALIDA} (activo: {salida['activo']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
