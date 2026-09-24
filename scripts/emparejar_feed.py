#!/usr/bin/env python3
"""Suma la oferta de una tienda grande (feed de Soicos) SÓLO a las fichas que
el catálogo ya tiene, sin dar de alta el resto.

POR QUÉ
-------
Walmart (750 mil productos) y Bodega Aurrerá (843 mil) no se pueden dar de
alta enteras: Coppel entró completa (150 mil fichas) y comparte producto con
otra tienda en menos de 800. Lo que un comparador gana con una tienda así es
su precio en los productos que YA compara; lo demás serían cientos de miles
de fichas de una sola tienda, sin página, que sólo engordan el catálogo.

CÓMO EMPAREJA
-------------
Para cada producto del feed:

  1. Candidatas: las fichas con el mismo código de barras (sin ceros a la
     izquierda), o que nombran como palabra entera un código de modelo del
     producto (7+ caracteres con letras y números; los códigos que nombran
     más de 8 fichas no sirven: son de CPU, de serie, de colección).
  2. El segundo filtro de fusionar_vetado.py, el mismo que se exige a toda
     fusión: mismas medidas y capacidades, paquete en las dos o en ninguna,
     los mismos códigos, y precio a menos de 1.8x.
  3. Gana la candidata que más tiendas compara. Una ficha recibe una sola
     oferta de la tienda, y no se toca la que ya tiene una.

No se borra ni se absorbe nada: sólo se agrega una oferta.

USO
---
    python3 scripts/emparejar_feed.py /tmp/walmart.json --tienda walmart_mx --informe /tmp/w.json
    python3 scripts/emparejar_feed.py /tmp/walmart.json --tienda walmart_mx --aplicar
"""
import argparse
import collections
import json
import os
import random
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import load_catalog, save_catalog, url_real  # noqa: E402
import adjuntar_tienda_de_marca as A  # noqa: E402
import fusionar_vetado as FV  # noqa: E402
from importar_captura_tienda import TIENDAS  # noqa: E402

MAX_FICHAS_POR_CODIGO = 8
CADENA_WALMART = {"walmart_mx", "bodega_aurrera", "sams_mx"}


def gtin_norm(g):
    g = re.sub(r"\D", "", str(g or "")).lstrip("0")
    return g if len(g) >= 7 else None


# «2baterias», «10cubos», «3niveles»: un número pegado a una palabra no es
# un código de modelo (unía una pulidora con un rotomartillo por «con
# 2baterías»), ni una medida «175x196» (unía dos salas de otro modelo).
RX_NUMERO_Y_PALABRA = re.compile(r"^\d+[a-z]{4,}$|^\d+x\d+")


def codigos(nombre):
    return {c for c in A.codigos(nombre) if not RX_NUMERO_Y_PALABRA.match(c)}


def tiendas(p):
    return {o.get("storeId") for o in p.get("offers") or []}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("captura")
    ap.add_argument("--tienda", required=True, choices=sorted(TIENDAS))
    ap.add_argument("--informe")
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()
    tienda = args.tienda

    items = [it for it in json.load(open(args.captura, encoding="utf-8")) if it.get("store") == tienda and it.get("price")]
    data = load_catalog()
    productos = data["products"]
    ya = {url_real(o.get("url")) or o.get("url") for p in productos for o in p.get("offers") or []
          if o.get("storeId") == tienda}
    items = [it for it in items if (url_real(it["url"]) or it["url"]) not in ya]
    print(f"productos del feed sin oferta en el catálogo: {len(items):,}")

    otras = [p for p in productos if tienda not in tiendas(p) and p.get("offers")]
    por_gtin = collections.defaultdict(list)
    por_codigo = collections.defaultdict(list)
    for p in otras:
        g = gtin_norm(p.get("gtin"))
        if g:
            por_gtin[g].append(p)
        for c in codigos(p.get("name")):
            por_codigo[c].append(p)
    por_codigo = {c: ps for c, ps in por_codigo.items() if len(ps) <= MAX_FICHAS_POR_CODIGO}

    # Walmart, Bodega Aurrerá y Sam's son de la misma cadena y numeran igual
    # sus artículos (/ip/<nombre>/<id>): el mismo id en otra de las tres es
    # el mismo artículo, aunque cada una lo nombre distinto.
    from importar_captura_tienda import id_de_url
    por_articulo = {}
    for p in otras:
        for o in p.get("offers") or []:
            if o.get("storeId") in CADENA_WALMART:
                a = id_de_url(o.get("url"))
                if a:
                    por_articulo.setdefault(a, p)

    motivos = collections.Counter()
    elegidas = {}   # id de ficha -> (item, por_gtin)
    for it in items:
        a = id_de_url(it["url"]) if tienda in CADENA_WALMART else None
        p = por_articulo.get(a) if a else None
        if p is not None:
            pm = A.precio_min(p)
            if pm and max(pm, it["price"]) / min(pm, it["price"]) > 3:
                motivos["mismo artículo de la cadena, precio 3x"] += 1
            elif p["id"] in elegidas:
                motivos["la ficha ya recibió otra oferta de la tienda"] += 1
            else:
                elegidas[p["id"]] = (it, True, p)
            continue
        cands = {}
        g = gtin_norm(it.get("gtin"))
        for p in por_gtin.get(g, []) if g else []:
            cands[p["id"]] = (p, True)
        for c in codigos(it["title"]):
            for p in por_codigo.get(c, []):
                if A.nombra(p.get("name"), c):
                    cands.setdefault(p["id"], (p, False))
        if not cands:
            motivos["sin candidata"] += 1
            continue
        buenas = []
        for p, por_barras in cands.values():
            m = FV.motivo([{"nombre": p["name"], "precio": A.precio_min(p)},
                           {"nombre": it["title"], "precio": it["price"]}])
            if m:
                motivos["veto: " + m.split(" [")[0].split(" (")[0].split(" 1")[0].split(" 2")[0]] += 1
                continue
            buenas.append((-len(tiendas(p)), not por_barras, p["id"], p, por_barras))
        if not buenas:
            continue
        buenas.sort(key=lambda t: t[:3])
        _, _, pid, p, por_barras = buenas[0]
        if pid in elegidas:
            motivos["la ficha ya recibió otra oferta de la tienda"] += 1
            continue
        elegidas[pid] = (it, por_barras, p)

    print(f"ofertas que se suman: {len(elegidas):,} "
          f"(por código de barras {sum(1 for x in elegidas.values() if x[1]):,}, por código de modelo {sum(1 for x in elegidas.values() if not x[1]):,})")
    for k, v in motivos.most_common(12):
        print(f"  no: {v:8,}  {k}")
    muestra = list(elegidas.values())
    random.Random(1).shuffle(muestra)
    for it, por_barras, p in muestra[:30]:
        print(f"  {'GTIN' if por_barras else 'cod '} ${it['price']:>9,.0f}  {it['title'][:58]}")
        print(f"        ${A.precio_min(p) or 0:>9,.0f}  {p['name'][:58]}  [{', '.join(sorted(tiendas(p)))}]")
    if args.informe:
        json.dump([[{"id": p["id"], "tiendas": sorted(tiendas(p)), "categoria": p.get("category"),
                     "nombre": p["name"], "precio": A.precio_min(p)},
                    {"id": it["id"], "tiendas": [tienda], "nombre": it["title"], "precio": it["price"],
                     "gtin": por_barras}] for it, por_barras, p in elegidas.values()],
                  open(args.informe, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"Informe: {args.informe}")
    if not args.aplicar:
        print("(sin --aplicar: no se tocó el catálogo)")
        return
    for pid, (it, _, p) in elegidas.items():
        o = {"storeId": tienda, "price": it["price"], "stock": "in_stock", "url": it["url"]}
        if it.get("listPrice") and it["listPrice"] > it["price"]:
            o["listPrice"] = it["listPrice"]
        p["offers"].append(o)
        if not p.get("gtin") and it.get("gtin"):
            p["gtin"] = it["gtin"]
    stores = data.setdefault("stores", [])
    if elegidas and not any(s["id"] == tienda for s in stores):
        stores.append(dict(TIENDAS[tienda]["store"]))
    save_catalog(data)
    print(f"Guardado: {len(elegidas):,} ofertas de {tienda} sumadas a fichas existentes.")


if __name__ == "__main__":
    main()
