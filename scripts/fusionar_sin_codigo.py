#!/usr/bin/env python3
"""Fusiones entre tiendas para fichas SIN código de modelo en el nombre.

POR QUÉ (27-sep-2026)
---------------------
merge_amazon_cross_store.py exige un código de modelo compartido. De las
484,973 fichas de una sola tienda, 407,934 no tienen ninguno («Colchón En
Caja Matrimonial Nooz Essential 14cm», «Bocina Marshall Middleton Negra»):
esas nunca se comparaban con la misma ficha de otra tienda.

Medido en los shards publicados:
  - misma marca y categoría, nombre con >= 80% de palabras en común y precio
    a <= 1.3x: 6,667 fichas con un probable gemelo, pero en una muestra de 60
    sólo ~72% eran el mismo artículo. Lo que fallaba era siempre un número o
    un color: iPhone 15 / 16, Redmi Note 14 / 15, Resident Evil 7 / 6, pack
    de 6 / de 4, maleta 27" / 24", gris / azul;
  - exigiendo además los MISMOS números, colores que no choquen y
    motivo_no() de merge_amazon_cross_store (medida, piezas, color, regalo):
    4,154 fichas, ~90% en una muestra de 70; los errores que quedaban eran
    tallas («talla g» / «talla m») y medidas de cama («individual» /
    «individual/matrimonial»), que aquí también tienen que coincidir.

Qué NO entra:
  - Autopartes: el modelo del auto hace de código y une piezas distintas
    del mismo vehículo (de ahí sale la mayoría de «marca distinta»).
  - fichas sin marca útil («Genérica», vacía): sin marca, un nombre parecido
    no basta.

Escribe un informe con el mismo formato que merge_amazon_cross_store.py
--informe; lo aplica fusionar_vetado.py, que vuelve a filtrar (medidas,
paquete, códigos, reacondicionado, precio a 1.8x). Nunca se fusiona sin ese
filtro.

USO
---
    python3 scripts/fusionar_sin_codigo.py --informe /tmp/sin_codigo.json [--muestra 40]
    python3 scripts/fusionar_vetado.py /tmp/sin_codigo.json [--aplicar]
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
import audit_gtin_matches as ag  # noqa: E402
import merge_amazon_cross_store as M  # noqa: E402
from data_io import load_catalog, texto_plano  # noqa: E402
from sanear_marcas import clave_marca  # noqa: E402

JACCARD = 0.8
PRECIO = 1.3
FUERA = {"Autopartes"}
SIN_MARCA = {"", "generica", "generico", "generic", "sinmarca", "na", "oem", "nd"}
MAX_GRUPO = 3000     # marcas-categoría más grandes que esto: demasiadas comparaciones

COLORES = set("""negro negra blanco blanca gris azul rojo roja verde amarillo amarilla rosa
morado morada cafe dorado dorada plata plateado plateada beige marino naranja turquesa vino
chocolate nogal oxford cromo cromado cr hueso marfil lila fucsia violeta transparente
multicolor arena tabaco miel natural salmon menta coral""".split())
# Tallas y medidas de cama: «talla g» / «talla m», «individual» / «matrimonial».
TALLA_RE = re.compile(r"\btalla\s+(xxs|xs|s|m|l|xl|xxl|xxxl|ch|g|eg|xg|chica|mediana|grande|\d+)\b")
CAMA = {"individual", "matrimonial", "queen", "king", "twin", "full", "cuna", "california"}


def numeros(nombre):
    return set(re.findall(r"\d+(?:[.,]\d+)?", texto_plano(nombre or "")))


def palabras(nombre):
    return set(re.findall(r"[a-z]+", texto_plano(nombre or "")))


def tallas(nombre):
    t = texto_plano(nombre or "")
    return set(TALLA_RE.findall(t)) | (palabras(nombre) & CAMA)


# Marcas de una palabra con >= 30 fichas; se llena en candidatos(). Sirve para
# ver que los dos títulos no nombren marcas distintas aunque el campo diga lo
# mismo («Cargador ... Belug» contra «Cargador portátil baseus ...», las dos
# con brand=Belug en la tienda).
MARCAS_CONOCIDAS = set()


def marcas_en_titulo(nombre):
    return palabras(nombre) & MARCAS_CONOCIDAS


def compatibles(a, b):
    """Los chequeos que el nombre parecido no alcanza a ver."""
    na, nb = a.get("name") or "", b.get("name") or ""
    if numeros(na) != numeros(nb):
        return False
    ma, mb = marcas_en_titulo(na), marcas_en_titulo(nb)
    if ma and mb and not (ma & mb):
        return False
    ca, cb = palabras(na) & COLORES, palabras(nb) & COLORES
    if ca and cb and ca != cb:
        return False
    if tallas(na) != tallas(nb):
        return False
    return M.motivo_no(a, b) is None


def candidatos(products):
    """Grupos (listas de fichas) de la misma cosa en tiendas distintas."""
    tok, precio = {}, {}

    def T(p):
        if p["id"] not in tok:
            tok[p["id"]] = ag._tokens(p.get("name") or "")
        return tok[p["id"]]

    cuenta = collections.Counter(texto_plano(p.get("brand") or "").strip() for p in products)
    MARCAS_CONOCIDAS.clear()
    MARCAS_CONOCIDAS.update(m for m, n in cuenta.items()
                            if n >= 30 and re.fullmatch(r"[a-z]{4,}", m or "")
                            and clave_marca(m) not in SIN_MARCA)

    idx = collections.defaultdict(list)
    for p in products:
        if not p.get("offers") or p.get("category") in FUERA:
            continue
        k = clave_marca(p.get("brand"))
        if k in SIN_MARCA:
            continue
        idx[(k, p.get("category"))].append(p)
        precio[p["id"]] = M.precio_min(p)

    padre = {}

    def raiz(x):
        while padre.get(x, x) != x:
            padre[x] = padre.get(padre[x], padre[x])
            x = padre[x]
        return x

    por_id = {}
    for (k, cat), grupo in idx.items():
        if len(grupo) < 2 or len(grupo) > MAX_GRUPO:
            continue
        for a in grupo:
            ta_ = M.tiendas_de(a)
            if len(ta_) != 1 or M.codigos(a.get("name") or ""):
                continue
            pa, toka = precio.get(a["id"]), T(a)
            if not pa or not toka:
                continue
            mejor = None
            for b in grupo:
                if b["id"] == a["id"] or (M.tiendas_de(b) & ta_):
                    continue
                pb = precio.get(b["id"])
                if not pb or max(pa, pb) / min(pa, pb) > PRECIO:
                    continue
                tokb = T(b)
                if not tokb:
                    continue
                j = len(toka & tokb) / len(toka | tokb)
                if j >= JACCARD and (mejor is None or j > mejor[0]) and compatibles(a, b):
                    mejor = (j, b)
            if mejor:
                b = mejor[1]
                por_id[a["id"]], por_id[b["id"]] = a, b
                ra, rb = raiz(a["id"]), raiz(b["id"])
                if ra != rb:
                    padre[rb] = ra

    grupos = collections.defaultdict(list)
    for pid, p in por_id.items():
        grupos[raiz(pid)].append(p)
    ok, ambiguos = [], 0
    for fichas in grupos.values():
        if M.grupo_coherente(fichas):
            ok.append(sorted(fichas, key=M.id_num))
        else:
            ambiguos += 1
    return ok, ambiguos


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--informe", required=True)
    ap.add_argument("--muestra", type=int, default=30)
    args = ap.parse_args()

    data = load_catalog()
    grupos, ambiguos = candidatos(data["products"])
    print(f"Grupos sin código: {len(grupos):,} ({sum(len(g) for g in grupos):,} fichas); "
          f"descartados por ambiguos: {ambiguos:,}")
    print("Por categoría:", collections.Counter(g[0].get("category") for g in grupos).most_common(12))
    random.seed(1)
    for g in random.sample(grupos, min(args.muestra, len(grupos))):
        print()
        for p in g:
            print(f"    {sorted(M.tiendas_de(p))!s:34} {M.precio_min(p)!s:>9}  {p['name'][:85]}")
    with open(args.informe, "w", encoding="utf-8") as f:
        json.dump([[{"id": p["id"], "tiendas": sorted(M.tiendas_de(p)), "categoria": p.get("category"),
                     "nombre": p["name"], "precio": M.precio_min(p)} for p in g] for g in grupos],
                  f, ensure_ascii=False, indent=1)
    print(f"\nInforme: {args.informe}  (aplicar SÓLO con fusionar_vetado.py)")


if __name__ == "__main__":
    main()
