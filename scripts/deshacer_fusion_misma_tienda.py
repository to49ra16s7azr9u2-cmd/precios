#!/usr/bin/env python3
"""Vuelve a separar las fichas que merge_same_store.py juntó de más.

QUÉ PASÓ
--------
merge_same_store.py decide que dos fichas son la misma publicación repetida
cuando coinciden nombre, marca, categoría, subcategoría y el archivo de la
foto. Eso describe bien lo que hace Elektra (repetir un SKU), pero se
corrió sobre el catálogo YA con las capturas de Amazon dentro, y en Amazon
los ASIN de una misma familia --las tallas de un instrumento, las medidas
de una pantalla, las capacidades de un filtro-- comparten título y foto
principal por diseño. Resultado medido: 1,522 fichas absorbidas, de las
cuales 744 de Amazon, y entre ellas una pirámide de cuarzo de $2,076
fusionada con la de $11,160 (el título decía "3 pulgadas - 20 pulgadas") y
un lavavajillas de $78,686 con el de $220,539.

QUÉ HACE ESTO
-------------
Deshace SOLO lo que no debió fusionarse, y sin perder nada: la fusión no
tiró ofertas, las apiló en la ficha que sobrevivió (`principal["offers"]
.append(o)`), así que la oferta propia de esa ficha sigue siendo offers[0]
y cada oferta de más es una ficha que hay que devolver.

  - Todas las fichas con varias ofertas de amazon_mx.
  - Del resto de las tiendas, las que tienen varias ofertas de la misma
    tienda con precios a más de MAX_RATIO entre sí.

La oferta original (offers[0]) se queda con el id, la url y el historial de
precios de la ficha. Cada oferta de más sale como ficha nueva, con id nuevo
tomado de next_id() --nunca uno ya usado, ver data_io-- copiando nombre,
marca, categoría, subcategoría, foto y specs de la ficha de la que salió.

USO
---
    python3 scripts/deshacer_fusion_misma_tienda.py --dry-run
    python3 scripts/deshacer_fusion_misma_tienda.py
"""
import argparse
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, next_id, registrar_max_id, save_catalog  # noqa: E402
from merge_same_store import AMAZON, MAX_RATIO  # noqa: E402

# Campos que la ficha nueva hereda de la que la contenía.
CAMPOS = ("name", "brand", "category", "subcategory", "image", "photo",
          "specs", "reviews", "gtin", "mlQuery")
# De esos, los que TODA ficha del catálogo tiene aunque estén vacíos. El
# resto del código los lee con corchetes (render_product_page hace
# product["specs"] y p["brand"]), así que una ficha sin la clave --y no con
# la clave vacía-- revienta el generador de páginas con un KeyError. Pasó:
# la primera versión de este script solo copiaba lo que no estuviera vacío
# y dejó 1,561 fichas sin "specs" y 1,504 sin "brand".
CAMPOS_SIEMPRE = {"name": "", "brand": "", "category": "", "specs": [], "image": "box"}


def hay_que_separar(p):
    """(True, motivo) si esta ficha junta ofertas que no son el mismo producto."""
    # Las fichas de colores (merge_by_color) tienen a propósito una oferta
    # por color de la misma tienda, y a precios distintos: ahí las varias
    # ofertas son la función, no el error. merge_same_store nunca las tocó
    # (las descarta antes de agrupar), así que no hay nada que deshacer.
    if p.get("colorVariants"):
        return False, None
    ofertas = p.get("offers") or []
    if len(ofertas) < 2:
        return False, None
    por_tienda = collections.Counter(o.get("storeId") for o in ofertas)
    repetidas = [t for t, n in por_tienda.items() if n > 1]
    if not repetidas:
        return False, None
    if AMAZON in repetidas:
        return True, "varias ofertas de Amazon (ASIN de la misma familia)"
    for t in repetidas:
        precios = [o.get("price") for o in ofertas
                   if o.get("storeId") == t and o.get("price")]
        if len(precios) > 1 and max(precios) / min(precios) > MAX_RATIO:
            return True, f"precios a {max(precios) / min(precios):.1f}x dentro de {t}"
    return False, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--muestra", type=int, default=12)
    args = ap.parse_args()

    data = load_catalog()
    products = data["products"]
    siguiente = next_id(products, data)
    motivos = collections.Counter()
    nuevas, tocadas, ejemplos = [], 0, []

    for p in products:
        separar, motivo = hay_que_separar(p)
        if not separar:
            continue
        motivos[motivo.split(" (")[0].split(" dentro")[0]] += 1
        tocadas += 1
        ofertas = p["offers"]
        # La primera oferta es la que ya tenía la ficha antes de fusionar
        # (merge_same_store hace append de las demás), así que se queda.
        propia, sobrantes = ofertas[0], ofertas[1:]
        # Solo salen las que repiten tienda con la propia o entre ellas; una
        # oferta de OTRA tienda es una comparación legítima y se queda.
        quedan, salen = [propia], []
        vistas = {propia.get("storeId")}
        for o in sobrantes:
            if o.get("storeId") in vistas:
                salen.append(o)
            else:
                quedan.append(o)
                vistas.add(o.get("storeId"))
        if not salen:
            continue
        p["offers"] = quedan
        if len(ejemplos) < args.muestra:
            ejemplos.append((p, motivo, len(salen)))
        for o in salen:
            ficha = {"id": f"p{siguiente}"}
            siguiente += 1
            for c in CAMPOS:
                if p.get(c) not in (None, "", [], {}):
                    ficha[c] = p[c]
            for c, vacio in CAMPOS_SIEMPRE.items():
                ficha.setdefault(c, p.get(c, vacio) if p.get(c) is not None else vacio)
            ficha["offers"] = [o]
            nuevas.append(ficha)

    print(f"Fichas que juntaban ofertas distintas: {tocadas:,}")
    for m, n in motivos.most_common():
        print(f"  {n:6,}  {m}")
    print(f"Fichas devueltas al catálogo: {len(nuevas):,}")
    for p, motivo, n in ejemplos:
        print(f"\n  {p['id']}  {motivo}  (+{n} ficha(s))")
        print(f"    {p['name'][:88]}")

    if args.dry_run:
        print("\n(--dry-run: no se escribió nada)")
        return
    data["products"] = products + nuevas
    if nuevas:
        registrar_max_id(data, siguiente - 1)
    save_catalog(data)
    print(f"\nCatálogo: {len(data['products']):,} productos")


if __name__ == "__main__":
    main()
