#!/usr/bin/env python3
"""Precios que no son precios: marcadores de relleno, errores de captura y
descuentos imposibles.

POR QUÉ (07-oct-2026)
---------------------
Al revisar lo CARO entre lo barato de cada subcategoría salieron cosas que no
eran productos caros sino precios falsos:

  - Walmart/Bodega con «$99,999» en 42 ofertas: discos Austromex de $500 (en
    Mercado Libre cuestan eso), una mesa de exploración, un videojuego de PS4.
    Es el precio que el vendedor del marketplace pone cuando no quiere vender.
  - Mercado Libre con «$9,999» en una zapatera que Elektra vende a $319.
  - Mercado Libre con $9,652,236 en unos «audífonos Xiaomi Redmi 15» y
    $10,000,009 en una multiherramienta de bici.
  - «Antes $619,900» en un colchón que cuesta $2,239 (la etiqueta de «-99%»).

Qué se hace, por oferta:

  R1  precio de relleno (99,999 o más de la forma 99…9; 9,999 sólo si otra
      fuente lo ve a menos del 25%) en Walmart/Bodega/Sam's o Mercado Libre, y
      NINGUNA fuente independiente lo confirma (±15%). Elektra y Coppel no:
      una moto Benelli de $99,999 es real (tres tiendas coinciden), y las
      máquinas de coser Janome de gama alta también.
  R2  precio de 1 millón o más y 5,000 veces la mediana de su subcategoría,
      sin que otra fuente lo confirme.
  R3  «precio de lista» (el «antes») de más de 8 veces el precio: se quita el
      precio de lista, la oferta se queda.

Una oferta marcada por R1/R2 se QUITA de la ficha si queda alguna otra; si era
la única, la ficha se oculta (data/fichas-ocultas.json.gz, motivo «precio
imposible»; no se borra nada). Todo queda anotado en
data/precios-descartados.json con tienda, url, precio y motivo.

«Fuente independiente»: Walmart, Bodega Aurrera y Sam's son el MISMO catálogo
(una ficha en Walmart y en Bodega no confirma nada); cada otra tienda cuenta
aparte.

USO
---
    python3 scripts/sanear_precios.py              # informe
    python3 scripts/sanear_precios.py --aplicar    # lo corre regenerar_sitio.sh
"""
import argparse
import collections
import datetime
import gzip
import json
import os
import statistics
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import ROOT, load_catalog, save_catalog  # noqa: E402

GRUPO = {"walmart_mx": "walmart", "bodega_aurrera": "walmart", "sams_mx": "walmart"}
TIENDAS_CON_RELLENO = {"walmart", "mercadolibre"}
TOLERANCIA = 0.15
RELLENO_FUERTE = {99999, 999999, 9999999, 99999999}
RELLENO_FLOJO = {9999}
MIN_ABSURDO = 1_000_000
VECES_MEDIANA = 5000
LISTA_MAX_VECES = 8
MOTIVO_OCULTA = "precio imposible"
DESCARTADOS = os.path.join(ROOT, "data", "precios-descartados.json")
OCULTAS = os.path.join(ROOT, "data", "fichas-ocultas.json.gz")


def fuente(o):
    return GRUPO.get(o.get("storeId"), o.get("storeId"))


def _precio(o):
    v = o.get("price")
    return v if isinstance(v, (int, float)) and v > 0 else None


def confirmada(oferta, ofertas):
    """¿Otra fuente independiente tiene un precio a ±15% de éste?"""
    p = _precio(oferta)
    f = fuente(oferta)
    for o in ofertas:
        q = _precio(o)
        if o is oferta or q is None or fuente(o) == f:
            continue
        if abs(q - p) <= TOLERANCIA * p:
            return True
    return False


def veredicto(oferta, ofertas, mediana):
    """«relleno», «absurdo» o None."""
    p = _precio(oferta)
    if p is None:
        return None
    f = fuente(oferta)
    if f in TIENDAS_CON_RELLENO and not confirmada(oferta, ofertas):
        if p in RELLENO_FUERTE:
            return "relleno"
        if p in RELLENO_FLOJO:
            otros = [_precio(o) for o in ofertas if o is not oferta and _precio(o) is not None and fuente(o) != f]
            if otros and min(otros) < 0.25 * p:
                return "relleno"
    if p >= MIN_ABSURDO and mediana and p >= VECES_MEDIANA * mediana and not confirmada(oferta, ofertas):
        return "absurdo"
    return None


def medianas(productos):
    por = collections.defaultdict(list)
    for p in productos:
        precios = [_precio(o) for o in p.get("offers") or [] if _precio(o) is not None]
        if precios and p.get("subcategory"):
            por[(p.get("category"), p["subcategory"])].append(min(precios))
    return {k: statistics.median(v) for k, v in por.items() if len(v) >= 20}


def _misma(a, b):
    return a.get("url") == b.get("url") and a.get("storeId") == b.get("storeId") and a.get("price") == b.get("price")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--muestras", type=int, default=12)
    args = ap.parse_args()
    data = load_catalog()
    productos = data["products"]
    med = medianas(productos)
    quitar = []        # (producto, [ofertas], motivo)
    ocultar = []       # (producto, motivos)
    listas = []        # (producto, oferta)
    for p in productos:
        ofertas = p.get("offers") or []
        malas = []
        m = med.get((p.get("category"), p.get("subcategory")))
        for o in ofertas:
            v = veredicto(o, ofertas, m)
            if v:
                malas.append((o, v))
            lp, pr = o.get("listPrice"), _precio(o)
            if pr and isinstance(lp, (int, float)) and lp > LISTA_MAX_VECES * pr:
                listas.append((p, o))
        if not malas:
            continue
        if len(malas) == len(ofertas):
            ocultar.append((p, malas))
        else:
            quitar.append((p, malas))
    n_of = sum(len(m) for _, m in quitar) + sum(len(m) for _, m in ocultar)
    print(f"Ofertas con precio falso: {n_of} (en {len(quitar)} fichas con otras ofertas y {len(ocultar)} fichas sin ninguna otra)")
    print(f"«Precio de lista» imposible (más de {LISTA_MAX_VECES} veces el precio): {len(listas)} ofertas")
    for p, malas in (quitar + ocultar)[:args.muestras]:
        for o, v in malas[:2]:
            print(f"   {v:8} {o['storeId']:14} ${o['price']:>12,.0f}  {p['name'][:60]}")
    for p, o in listas[:args.muestras // 2]:
        print(f"   lista    {o['storeId']:14} ${o['price']:>10,.0f} (antes ${o['listPrice']:,.0f})  {p['name'][:50]}")
    if not args.aplicar:
        print("(sin --aplicar: no se escribió nada)")
        return 0
    hoy = datetime.date.today().isoformat()
    bitacora = json.load(open(DESCARTADOS, encoding="utf-8")) if os.path.exists(DESCARTADOS) else {"ofertas": []}
    ya = {(x["id"], x.get("url"), x["precio"]) for x in bitacora["ofertas"]}
    for p, malas in quitar + ocultar:
        for o, v in malas:
            clave = (p["id"], o.get("url"), o["price"])
            if clave not in ya:
                bitacora["ofertas"].append({"fecha": hoy, "id": p["id"], "nombre": p["name"][:100], "tienda": o["storeId"],
                                            "url": o.get("url"), "precio": o["price"], "motivo": v})
                ya.add(clave)
    for p, malas in quitar:
        fuera = [o for o, _ in malas]
        p["offers"] = [o for o in p["offers"] if not any(o is x for x in fuera)]
        for var in p.get("colorVariants") or []:
            if isinstance(var.get("offers"), list):
                var["offers"] = [o for o in var["offers"] if not any(_misma(o, x) for x in fuera)]
    for p, o in listas:
        o.pop("listPrice", None)
    ids_ocultar = {p["id"] for p, _ in ocultar}
    if ids_ocultar:
        archivo = {"fichas": []}
        if os.path.exists(OCULTAS):
            with gzip.open(OCULTAS, "rt", encoding="utf-8") as f:
                archivo = json.load(f)
        archivo["fichas"].extend({"motivo": MOTIVO_OCULTA, "fecha": hoy, "ficha": p} for p, _ in ocultar)
        data["products"] = [p for p in productos if p["id"] not in ids_ocultar]
        tmp = OCULTAS + ".tmp"
        with gzip.open(tmp, "wt", encoding="utf-8") as f:
            json.dump(archivo, f, ensure_ascii=False, separators=(",", ":"))
        os.replace(tmp, OCULTAS)
    with open(DESCARTADOS, "w", encoding="utf-8") as f:
        json.dump(bitacora, f, ensure_ascii=False, indent=0)
    save_catalog(data)
    print(f"Guardado: {len(quitar)} fichas sin la oferta falsa, {len(ids_ocultar)} fichas ocultas, {len(listas)} precios de lista quitados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
