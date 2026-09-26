#!/usr/bin/env python3
"""Junta las fichas con el MISMO nombre y la MISMA foto aunque sus tiendas se
solapen (26-sep-2026).

EL CASO
-------
Los feeds de Soicos traen el mismo artículo de Walmart y de Bodega Aurrerá, y
Bodega además por su segundo programa (la Despensa). Así quedaba una ficha
«Walmart + Bodega» y otra «Bodega» sola del mismo artículo:

    Llanta hankook kinergy st h735 215/60r16 95h   walmart $2,517 | bodega $2,517
    Llanta hankook kinergy st h735 215/60r16 95h   bodega $2,733

merge_cross_store.py no las junta porque las dos tienen Bodega («dos fichas
de una misma tienda con el mismo nombre suelen ser SKU distintos»), y
merge_same_store.py tampoco, porque sus tiendas no son las mismas. Medido:
5,162 grupos, 8,819 fichas.

CUÁNDO SE JUNTA
---------------
El nombre sólo no alcanza: «Ventilador de pedestal tornado» son siete
ventiladores distintos de $6,000 a $14,700. Hace falta, además:

  * la MISMA foto (el nombre del archivo, no la url entera: el id del asset
    cambia cuando la tienda la vuelve a subir), que es lo que separa la
    misma publicación de dos variantes;
  * misma categoría y marca;
  * precio a menos de 1.5x entre la más barata y la más cara.

Se queda la ficha de id más bajo con todas las ofertas (una por tienda, la
más barata) y las absorbidas se redirigen a ella.

SEGUNDA PASADA: MISMO NOMBRE EXACTO, OTRA FOTO
----------------------------------------------
Walmart y Bodega son marketplaces: el mismo «Faro rio 2016 kia izquierdo
genérica» lo publican tres vendedores, cada uno con su foto; Coppel da de
alta el mismo gabinete en cuatro SKU con el mismo título. En la página son
tarjetas idénticas. Medido el 26-sep: 14,805 grupos. Pero una tienda
también usa el mismo nombre comercial para modelos distintos (las cuatro
«Estufa de gas al piso 30"» de Whirlpool, a precios distintos), así que:

  * precio a menos de 2% entre fichas: se juntan (no hay nada en la página
    que las distinga);
  * hasta 15%: sólo si el nombre es específico (trae un código de modelo o
    un año: «Faro rio 2016 kia...», «... Rt05c ...»);
  * más que eso: no se tocan.

USO
---
    python3 scripts/merge_misma_foto.py --dry-run
    python3 scripts/merge_misma_foto.py
"""
import argparse
import collections
import os
import random
import re
import sys
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import id_num, load_catalog, registrar_fusiones, save_catalog  # noqa: E402

MAX_RATIO = 1.5
RATIO_IGUAL = 1.02        # segunda pasada: precio prácticamente igual
RATIO_ESPECIFICO = 1.15   # segunda pasada: nombre con código o año
_CODIGO = re.compile(r"\b(?=[a-z0-9]*\d)(?=[a-z0-9]*[a-z])[a-z0-9]{4,}\b")
_ANIO = re.compile(r"\b(19[5-9]\d|20[0-4]\d)\b")


def especifico(nombre_norm):
    return bool(_CODIGO.search(nombre_norm) or _ANIO.search(nombre_norm))


def norm(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def foto(p):
    u = (p.get("photo") or "").split("?")[0]
    base = os.path.basename(u)
    return base if len(base) >= 12 else None


def ofertas(p):
    out = list(p.get("offers") or [])
    for v in p.get("colorVariants") or []:
        out += v.get("offers") or []
    return out


def precio_min(p):
    ps = [o.get("price") for o in ofertas(p) if o.get("price")]
    return min(ps) if ps else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--muestra", type=int, default=15)
    args = ap.parse_args()
    data = load_catalog()
    grupos = collections.defaultdict(list)
    for p in data["products"]:
        f = foto(p)
        if not f or p.get("colorVariants"):
            continue    # las fusionadas por color las maneja merge_by_color
        grupos[(p.get("category"), norm(p.get("brand")), norm(p.get("name")), f)].append(p)

    fusionar = []
    motivos = collections.Counter()
    for k, ps in grupos.items():
        if len(ps) < 2:
            continue
        precios = [precio_min(p) for p in ps]
        if None in precios:
            motivos["sin precio"] += 1
            continue
        if max(precios) >= MAX_RATIO * min(precios):
            motivos["precio"] += 1
            continue
        fusionar.append(sorted(ps, key=id_num))
    print(f"misma foto -> grupos: {len(fusionar):,}; fichas absorbidas: {sum(len(g) - 1 for g in fusionar):,}; "
          f"no: {dict(motivos)}")

    # Segunda pasada: mismo nombre exacto con otra foto (ver arriba).
    ya = {p["id"] for g in fusionar for p in g}
    grupos2 = collections.defaultdict(list)
    for p in data["products"]:
        if p["id"] in ya or p.get("colorVariants"):
            continue
        n = norm(p.get("name"))
        if len(n.split()) >= 4:
            grupos2[(p.get("category"), norm(p.get("brand")), n)].append(p)
    motivos2 = collections.Counter()
    antes = len(fusionar)
    for (_c, _b, n), ps in grupos2.items():
        if len(ps) < 2:
            continue
        precios = [precio_min(p) for p in ps]
        if None in precios:
            motivos2["sin precio"] += 1
            continue
        r = max(precios) / min(precios)
        if r < RATIO_IGUAL or (r < RATIO_ESPECIFICO and especifico(n)):
            fusionar.append(sorted(ps, key=id_num))
        else:
            motivos2["precio distinto" if especifico(n) else "nombre genérico"] += 1
    print(f"mismo nombre -> grupos: {len(fusionar) - antes:,}; "
          f"fichas absorbidas: {sum(len(g) - 1 for g in fusionar[antes:]):,}; no: {dict(motivos2)}")
    random.seed(2)
    for g in random.sample(fusionar[antes:], min(args.muestra, len(fusionar) - antes)):
        print("  ", " | ".join(f"{p['id']} {sorted({o.get('storeId') for o in ofertas(p)})} ${precio_min(p):,.0f}" for p in g),
              "|", g[0]["name"][:60])
    if args.dry_run:
        print("(--dry-run: no se escribió nada)")
        return 0

    fuera = set()
    for g in fusionar:
        jefe = g[0]
        for p in g[1:]:
            for o in p.get("offers") or []:
                # Una oferta por tienda: si ya está, se queda la más barata
                # (con el mismo nombre y la misma foto no hay cómo distinguir
                # dos SKU de la misma tienda en la página).
                previa = next((x for x in jefe.setdefault("offers", []) if x.get("storeId") == o.get("storeId")), None)
                if previa:
                    if o.get("price") and (not previa.get("price") or o["price"] < previa["price"]):
                        previa.clear()
                        previa.update(o)
                    continue
                jefe["offers"].append(o)
            for campo in ("specs", "gtin", "subcategory", "brand"):
                if not jefe.get(campo) and p.get(campo):
                    jefe[campo] = p[campo]
            fuera.add(p["id"])
    data["products"] = [p for p in data["products"] if p["id"] not in fuera]
    save_catalog(data)
    registrar_fusiones((p["id"], g[0]["id"]) for g in fusionar for p in g[1:])
    print(f"Guardado: {len(fuera):,} fichas absorbidas; catálogo {len(data['products']):,}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
