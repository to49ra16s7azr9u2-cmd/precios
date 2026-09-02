#!/usr/bin/env python3
"""Fusiona en un solo producto las fichas que son el MISMO producto físico
publicado por tiendas distintas, para que el sitio muestre una comparación
de precios real en vez de dos fichas sueltas.

EL PROBLEMA
-----------
Cada importador (Mercado Libre, Elektra, Whirlpool...) da de alta sus
productos por su lado, así que el mismo producto termina como dos fichas
separadas. El usuario ve una y nunca se entera de la otra -- justo lo
contrario de para lo que existe el sitio. Ejemplos reales del catálogo al
escribir esto:

    Impresora HP Smart Tank 520     Mercado Libre $3,299  |  Elektra $1,999
    Consola Nintendo Switch 2       Mercado Libre $9,115  |  Elektra $11,999
    Refrigerador French Door 24.5p3 Whirlpool    $29,999  |  Elektra $50,199

QUÉ SE FUSIONA Y QUÉ NO
-----------------------
Solo se fusionan grupos que cumplen TODAS estas condiciones:

  1. Mismo `category` y mismo nombre normalizado (minúsculas, sin acentos,
     sin espacios de más). Es coincidencia EXACTA de nombre, no parecido:
     el matching difuso por título ya se probó en este proyecto y daba
     falsos positivos a mansalva.
  2. Cada ficha del grupo tiene exactamente UNA oferta.
  3. Todas las tiendas del grupo son distintas.

La condición 3 es la que evita el error grave. Muchas tiendas usan un
nombre comercial genérico para SKUs distintos: Whirlpool tiene cuatro
"Estufa de gas al piso 30\" con 6 quemadores gris" con cuatro precios y
cuatro urls -- son modelos diferentes, no duplicados. Si dos fichas del
grupo son de la MISMA tienda, el grupo entero se descarta: dos productos
de una tienda con el mismo nombre son casi siempre SKUs distintos mal
nombrados, y fusionarlos escondería un producto real.

QUÉ FICHA SOBREVIVE
-------------------
La de id más bajo (la más vieja, la que probablemente ya esté indexada en
buscadores), para no romper su URL. Si a esa le falta foto o specs y la
otra las tiene, se las queda: se conserva la URL vieja Y el mejor dato de
las dos.

USO
---
    python3 scripts/merge_cross_store.py --dry-run
    python3 scripts/merge_cross_store.py
"""
import argparse
import os
import re
import shutil
import sys
import unicodedata
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def norm_name(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip()


def id_num(product):
    m = re.match(r"p(\d+)$", product.get("id", ""))
    return int(m.group(1)) if m else 10**9


def mergeable_groups(products):
    groups = defaultdict(list)
    for p in products:
        groups[(p.get("category"), norm_name(p.get("name")))].append(p)

    out = []
    for (category, name), ps in groups.items():
        if len(ps) < 2 or not name:
            continue
        if any(len(p.get("offers") or []) != 1 for p in ps):
            continue
        stores = [(p["offers"][0] or {}).get("storeId") for p in ps]
        if None in stores or len(set(stores)) != len(stores):
            continue
        out.append((category, name, sorted(ps, key=id_num)))
    return out


def same_url_groups(products):
    """Fichas distintas que apuntan a la MISMA url de tienda: es literalmente
    la misma publicación cargada dos veces (pasó con SUNSKY, una vez con el
    título corto y otra con el título largo del proveedor). No hay nada que
    interpretar acá -- misma url es el mismo producto -- así que se fusionan
    aunque los nombres no coincidan palabra por palabra."""
    by_url = defaultdict(list)
    for p in products:
        for o in p.get("offers") or []:
            url = o.get("url")
            if url:
                by_url[url].append(p)
    groups, seen = [], set()
    for url, ps in by_url.items():
        uniq = {p["id"]: p for p in ps}
        if len(uniq) < 2:
            continue
        key = tuple(sorted(uniq))
        if key in seen:
            continue
        seen.add(key)
        groups.append((url, sorted(uniq.values(), key=id_num)))
    return groups


def merge_group(ps):
    """Fusiona una lista de fichas en la primera (la de id más bajo).
    Devuelve (principal, sobrantes)."""
    primary, rest = ps[0], ps[1:]
    seen_urls = {o.get("url") for o in primary.get("offers") or []}
    for other in rest:
        for offer in other.get("offers") or []:
            if offer.get("url") in seen_urls:
                continue
            seen_urls.add(offer.get("url"))
            primary.setdefault("offers", []).append(offer)
        # Se completa lo que le falte a la principal con lo que traiga la otra
        # ficha: la principal se elige por id (URL), no por calidad de datos.
        if not primary.get("photo") and other.get("photo"):
            primary["photo"] = other["photo"]
        if not primary.get("specs") and other.get("specs"):
            primary["specs"] = other["specs"]
        if not primary.get("reviews") and other.get("reviews"):
            primary["reviews"] = other["reviews"]
        if not primary.get("brand") and other.get("brand"):
            primary["brand"] = other["brand"]
        if not primary.get("subcategory") and other.get("subcategory"):
            primary["subcategory"] = other["subcategory"]
    return primary, rest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--keep-pages", action="store_true",
                    help="no borra las páginas estáticas de las fichas absorbidas")
    args = ap.parse_args()

    data = load_catalog()
    absorbed = set()

    url_groups = same_url_groups(data["products"])
    print(f"Fichas duplicadas (misma url de tienda): {len(url_groups)}")
    for url, ps in url_groups:
        primary, rest = merge_group(ps)
        absorbed.update(p["id"] for p in rest)
        print(f"  {primary['id']} <- {', '.join(p['id'] for p in rest)}   {url[:60]}")
        print(f"      se conserva: {primary['name'][:70]}")

    groups = mergeable_groups(data["products"])
    print(f"\nGrupos fusionables (mismo producto en tiendas distintas): {len(groups)}")
    if not groups and not url_groups:
        return

    for category, name, ps in groups:
        primary, rest = merge_group(ps)
        absorbed.update(p["id"] for p in rest)
        prices = sorted(
            (o.get("price"), o.get("storeId")) for o in primary["offers"] if o.get("price")
        )
        spread = ""
        if len(prices) > 1 and prices[-1][0]:
            spread = f"  (dif. {(prices[-1][0] - prices[0][0]) / prices[-1][0]:.0%})"
        detail = " | ".join(f"{s} ${pr:,.0f}" for pr, s in prices)
        print(f"  [{category}] {name[:58]}")
        print(f"      {primary['id']} <- {', '.join(p['id'] for p in rest)}   {detail}{spread}")

    data["products"] = [p for p in data["products"] if p["id"] not in absorbed]
    print(f"\nFichas absorbidas: {len(absorbed)}; catálogo: {len(data['products'])} productos")

    if args.dry_run:
        print("(--dry-run: no se escribió nada)")
        return

    save_catalog(data)
    if not args.keep_pages:
        gone = 0
        for pid in absorbed:
            path = os.path.join(ROOT, "producto", pid)
            if os.path.isdir(path):
                shutil.rmtree(path)
                gone += 1
        print(f"Páginas estáticas borradas: {gone}")
    print("Catálogo actualizado.")


if __name__ == "__main__":
    main()
