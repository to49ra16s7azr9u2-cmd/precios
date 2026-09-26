#!/usr/bin/env python3
"""La categoría que le puso la tienda de origen a cada producto.

POR QUÉ (26-sep-2026)
---------------------
El clasificador decidía sólo con el título, y el título engaña: marcas que
parecen palabras de la categoría («Casa del Anillo», «El Gato»), números de
parte leídos como tipo («spf10d4» en un subwoofer). La tienda que vende el
producto ya lo clasificó en su propio árbol, y ese dato se tiraba al dar de
alta la ficha.

Aquí se guarda, por (tienda, id del producto en la tienda) y no por ficha
nuestra: las fusiones mueven ofertas de una ficha a otra y cambian el id
nuestro, pero la oferta de Walmart 00064203401252 sigue siendo la misma.

    data/origen-categorias.json.gz   {"walmart_mx": {"00064203401252": "Libreros", ...}, ...}

Además del departamento del feed, la url de Walmart y Bodega trae la rama
del árbol de la tienda (/ip/escritorios-y-muebles-de-oficina/...): esa se
lee al vuelo de la oferta con rama_de_url(), no hace falta guardarla.

LO QUE NO ES
------------
Un mapa directo a nuestras categorías. Medido el 26-sep-2026 sobre 589,514
fichas de Walmart/Bodega: los departamentos con una mayoría de 90% en una
categoría nuestra discrepan en 13,247 fichas, y de 60 al azar sólo 5 eran
errores nuestros. Los árboles no cortan igual (los cubrevolantes están bien
en Autos y motos aunque su departamento caiga casi todo en Autopartes) y el
departamento a veces está mal (un kit de distribución en «Tinte de cabello»).
Por eso es un voto entre tres (ver juez_origen.py), nunca la decisión sola.

USO
---
    python3 scripts/origen_categorias.py --desde captura1.json captura2.json   # registrar
    python3 scripts/origen_categorias.py                                        # resumen
"""
import argparse
import collections
import gzip
import io
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(AQUI)
ARCHIVO = os.path.join(ROOT, "data", "origen-categorias.json.gz")

# /ip/<rama>/<producto>/<id>: la rama es el árbol de la tienda.
RX_RAMA_WALMART = re.compile(r"(?:walmart\.com\.mx|bodegaaurrera\.com\.mx)/ip/([a-z0-9-]+)/[^/?#]+/\d+")


def cargar():
    if not os.path.exists(ARCHIVO):
        return {}
    with gzip.open(ARCHIVO, "rt", encoding="utf-8") as f:
        return json.load(f)


def guardar(mapa):
    tmp = ARCHIVO + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=9) as f:
        json.dump(mapa, f, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    os.replace(tmp, ARCHIVO)


def registrar(items, mapa=None):
    """Mete {store, id, dept} de una captura/feed. Devuelve cuántos cambiaron."""
    propio = mapa is None
    if propio:
        mapa = cargar()
    n = 0
    for it in items:
        tienda, pid, dept = it.get("store"), str(it.get("id") or "").strip(), (it.get("dept") or "").strip()
        if not (tienda and pid and dept):
            continue
        t = mapa.setdefault(tienda, {})
        if t.get(pid) != dept:
            t[pid] = dept
            n += 1
    if propio and n:
        guardar(mapa)
    return n


def rama_de_url(url):
    """La rama del árbol de Walmart/Bodega en la url de la oferta, o None."""
    from data_io import url_real
    u = (url_real(url) or url or "").lower()
    m = RX_RAMA_WALMART.search(u)
    return m.group(1) if m else None


def claves_de_oferta(o, mapa):
    """Las categorías de origen de una oferta: [("depto", tienda, valor), ("rama", tienda, valor)]."""
    from importar_captura_tienda import id_de_url
    tienda = o.get("storeId")
    out = []
    pid = id_de_url(o.get("url") or "")
    d = (mapa.get(tienda) or {}).get(pid) if pid else None
    if d:
        out.append(("depto", tienda, d))
    r = rama_de_url(o.get("url") or "")
    if r:
        out.append(("rama", tienda, r))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--desde", nargs="*", default=[], help="capturas o feeds convertidos (lista de {store,id,dept})")
    args = ap.parse_args()
    mapa = cargar()
    total = 0
    for ruta in args.desde:
        items = json.load(io.open(ruta, encoding="utf-8"))
        n = registrar(items, mapa)
        total += n
        print(f"{os.path.basename(ruta)}: {len(items):,} filas, {n:,} registradas")
        del items
    if total:
        guardar(mapa)
    for tienda, t in sorted(mapa.items()):
        c = collections.Counter(t.values())
        print(f"{tienda:16} {len(t):>8,} productos  {len(c):>5,} categorías de origen")


if __name__ == "__main__":
    sys.path.insert(0, AQUI)
    main()
