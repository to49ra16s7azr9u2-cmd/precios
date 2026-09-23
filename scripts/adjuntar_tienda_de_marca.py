#!/usr/bin/env python3
"""Pega la oferta de una tienda de marca a la ficha que ya compara ese producto.

EL PROBLEMA
-----------
whirlpool.mx vende su lavadora 8MWTW2024MJM, y la misma lavadora ya está en
el catálogo con Elektra, Mercado Libre, Amazon y Coppel. Pero la ficha de
Whirlpool quedaba sola:

  - merge_by_gtin.py tiene el código de barras (7501545634208) en común,
    pero Elektra publicó esa lavadora TRES veces con el mismo código, y un
    grupo con dos fichas de la misma tienda es trabajo de
    merge_same_store.py: lo deja entero sin tocar.
  - merge_amazon_cross_store.py compara nombres, y whirlpool.mx no escribe
    el modelo en el nombre ("Lavadora 20kg Carga Superior Blanca Agitador").

Una tienda de marca es la fuente más confiable del precio de lista de su
propio producto; que su oferta quede en una ficha aparte es justo lo que un
comparador no puede tener.

CÓMO DECIDE
-----------
Para cada ficha que SOLO vende esta tienda:

  1. Candidatas: las fichas de otras tiendas con el mismo código de barras,
     o que nombran el mismo código de modelo como palabra entera (se tolera
     el guion o el espacio en medio: "8Mwtw-2024Mjm" es 8MWTW2024MJM). El
     código tiene que tener 7 caracteres o más: los cortos coinciden por
     casualidad.
  2. Misma categoría.
  3. Precio: la oferta de la marca y la más barata de la candidata no se
     separan más de 2.5 veces.
  4. Un combo sólo con un combo.

De las que pasan, gana la que más tiendas compara (a igualdad, la de código
de barras igual y después la de id más bajo). La oferta se agrega a esa
ficha y la ficha sola se absorbe, igual que en los demás scripts de fusión.

USO
---
    python3 scripts/adjuntar_tienda_de_marca.py --tienda whirlpool --dry-run
    python3 scripts/adjuntar_tienda_de_marca.py --tienda whirlpool
"""
import argparse
import collections
import os
import re
import shutil
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN_CODIGO = 7
MAX_RATIO_PRECIO = 2.5


def T(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def compacto(s):
    return re.sub(r"[^a-z0-9]", "", T(s))


def codigos(nombre):
    """Los códigos de modelo del nombre: letras y números juntos, 7+."""
    out = set()
    for tok in re.split(r"[\s,()/+]+", T(nombre)):
        c = re.sub(r"[^a-z0-9]", "", tok)
        if len(c) >= MIN_CODIGO and re.search(r"\d", c) and re.search(r"[a-z]", c):
            out.add(c)
    return out


def nombra(nombre, codigo):
    """¿El nombre trae `codigo` como palabra entera, con o sin guiones?"""
    patron = r"(?<![a-z0-9])" + r"[\s\-.]?".join(map(re.escape, codigo)) + r"(?![a-z0-9])"
    return re.search(patron, T(nombre)) is not None


def precio_min(p, excluir=None):
    xs = [o["price"] for o in p.get("offers") or [] if o.get("price") and o.get("storeId") != excluir]
    return min(xs) if xs else None


def es_combo(n):
    return bool(re.search(r"\bcombo\b|\+", T(n)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tienda", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    tienda = args.tienda

    data = load_catalog()
    productos = data["products"]
    solas = [p for p in productos if {o.get("storeId") for o in p.get("offers") or []} == {tienda}]
    otras = [p for p in productos if not any(o.get("storeId") == tienda for o in p.get("offers") or [])]
    por_gtin = collections.defaultdict(list)
    por_cat = collections.defaultdict(list)
    for p in otras:
        if p.get("gtin"):
            por_gtin[str(p["gtin"])].append(p)
        por_cat[p.get("category")].append((compacto(p.get("name")), p))
    print(f"fichas sólo de {tienda}: {len(solas)}")

    motivos = collections.Counter()
    uniones = []
    usadas = set()
    for w in solas:
        cands = {}
        for p in por_gtin.get(str(w.get("gtin") or ""), []):
            cands[p["id"]] = (p, True)
        for c in codigos(w.get("name")):
            for comp, p in por_cat.get(w.get("category"), []):
                if c in comp and nombra(p.get("name"), c):
                    cands.setdefault(p["id"], (p, False))
        if not cands:
            motivos["sin candidata"] += 1
            continue
        pw = precio_min(w)
        buenas = []
        for p, por_codigo_barras in cands.values():
            if p.get("category") != w.get("category"):
                motivos["otra categoría"] += 1
                continue
            if es_combo(w.get("name")) != es_combo(p.get("name")):
                motivos["combo contra aparato solo"] += 1
                continue
            pp = precio_min(p)
            if pw and pp and max(pw, pp) / min(pw, pp) > MAX_RATIO_PRECIO:
                motivos["precio muy distinto"] += 1
                continue
            tiendas = len({o.get("storeId") for o in p.get("offers") or []})
            idn = int(re.sub(r"\D", "", p["id"]) or 0)
            buenas.append((-tiendas, not por_codigo_barras, idn, p))
        if not buenas:
            continue
        buenas.sort(key=lambda t: t[:3])
        jefe = buenas[0][3]
        if jefe["id"] in usadas:
            motivos["la candidata ya recibió otra ficha de la tienda"] += 1
            continue
        usadas.add(jefe["id"])
        uniones.append((w, jefe))

    print(f"uniones: {len(uniones)}")
    for k, v in motivos.most_common():
        print(f"  no: {v:4}  {k}")
    for w, j in uniones[:25]:
        print(f"  {w['id']:>8} ${precio_min(w):>9,.0f}  {w['name'][:55]}")
        print(f"   -> {j['id']:>6} ${precio_min(j) or 0:>9,.0f}  {j['name'][:55]}  "
              f"[{', '.join(sorted({o['storeId'] for o in j['offers']}))}]")
    if args.dry_run or not uniones:
        print("(--dry-run: no se escribió nada)" if args.dry_run else "")
        return

    absorbidas = set()
    for w, jefe in uniones:
        urls = {o.get("url") for o in jefe.get("offers") or []}
        for o in w.get("offers") or []:
            if o.get("url") not in urls:
                jefe.setdefault("offers", []).append(o)
        for campo in ("gtin", "photo"):
            if not jefe.get(campo) and w.get(campo):
                jefe[campo] = w[campo]
        absorbidas.add(w["id"])
    data["products"] = [p for p in productos if p["id"] not in absorbidas]
    save_catalog(data)
    for pid in absorbidas:
        ruta = os.path.join(ROOT, "producto", pid)
        if os.path.isdir(ruta):
            shutil.rmtree(ruta)
    print(f"Guardado: {len(absorbidas)} fichas unidas; catálogo {len(data['products']):,}")


if __name__ == "__main__":
    main()
