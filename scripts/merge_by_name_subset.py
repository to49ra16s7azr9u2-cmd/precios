#!/usr/bin/env python3
"""Fusiona fichas de tiendas distintas que son el mismo producto aunque no
tengan código de modelo, cuando el nombre corto está ENTERO dentro del largo.

POR QUÉ
-------
merge_amazon_cross_store.py exige un código de modelo compartido, y
153,000 fichas de una sola tienda no tienen ninguno: colchones, bicicletas,
edredones, licuadoras, juguetes... Para esas, el parecido de nombre por
palabras compartidas (>= 60%) se probó y dio un 45% de fusiones malas:
"Soul Clear" contra "Soul Track", "Kit Granja" contra "Kit Construcción",
"Eurobox" contra "Rest Resort" -- nombres que comparten casi todo y
difieren en la única palabra que importa.

La regla que sí aguantó la revisión a mano es la de SUBCONJUNTO: todas las
palabras útiles del nombre más corto tienen que estar en el más largo (una
tienda escribe "Karcher Aspiradora Multifuncional KWD 2" y la otra
"Aspiradora Karcher 15 Litros para Sólidos y Líquidos KWD 2"). Una palabra
de más en el corto que no esté en el largo -- "clear", "granja",
"eurobox" -- lo descarta. Encima de eso, todo lo que ya exige
merge_amazon_cross_store.py (misma categoría, marca declarada e idéntica
en las dos, sin contradicción de medida/cantidad/color/versión/regalo,
precio a menos de 2.5x, grupo coherente) y tres chequeos propios:

  - Números sueltos iguales ("Flip 3" no es "Flip 7"; "Pro 5" no es
    "Pro 4"), incluidos los romanos ("GTA V" no es "GTA VI") y las
    siglas cortas de variante ("SE", "FE", "16X" no es "16").
  - Tazas iguales (una cafetera de 10 tazas no es la de 12).
  - Colores de mueble y blancos ("marrón", "nogal", "hueso"...), que
    color_of() no conoce: un librero blanco no es el marrón.

Quedan fuera las categorías donde el nombre no alcanza para decidir:
Celulares (los junta merge_by_signature.py por firma), Libros (por ISBN),
Videojuegos (la plataforma no siempre está en el nombre), Refacciones,
Otros, Ropa y Joyería.

USO
---
    python3 scripts/merge_by_name_subset.py --dry-run
    python3 scripts/merge_by_name_subset.py
"""
import argparse
import collections
import json
import os
import random
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audit_gtin_matches as ag  # noqa: E402
import merge_amazon_cross_store as M  # noqa: E402
from data_io import id_num, load_catalog, save_catalog  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCLUIDAS = {"Celulares", "Libros", "Otros", "Refacciones", "Videojuegos",
             "Ropa y accesorios", "Joyería y bisutería"}
MIN_PALABRAS = 4

_UNIDAD = re.compile(
    r"^(?:gb|tb|mb|mah|w|kw|v|hz|ghz|mhz|k|p|l|lt|lts|litros?|ml|kg|kilos?|g|cm|mm|m|in|"
    r"hp|btu|db|rpm|ah|a|lm|mp|fps|x|pcs|pz|pzs|pzas|piezas?|pulgadas?|pulg|ton|oz|onzas?|"
    r"lb|lbs|ft|mts|bar|psi|pies|p3|tazas?|quemadores|puertas?|vel|velocidades|canales|"
    r"nucleos|watts?|amp|amperios|horas?|hrs|dias?|meses|anos?|%|pack|unidades|cajones|"
    r"repisas|niveles|plazas|personas|luces|botones|modos|programas|funciones)$")
ROMANOS = {"ii", "iii", "iv", "vi", "vii", "viii", "ix", "xi", "xii"}
# "i5" contra "i7" son dos letras y ag._tokens() las tira (mínimo 3): una
# IdeaPad Slim 3 Core i5 se juntó con la Core i7. Se comparan aparte.
VARIANTE_CORTA = {"se", "fe", "xl", "xs", "xr", "xt", "gt", "rs", "ti", "go", "ai", "4g", "5g",
                  "i3", "i5", "i7", "i9", "r3", "r5", "r7", "r9", "m1", "m2", "m3", "m4", "m5"}
_NUM_LETRA = re.compile(r"^\d{1,3}[a-z]$")   # 16x, 15e, 14s
COLORES_EXTRA = {
    "marron", "cafe", "chocolate", "nogal", "roble", "cedro", "caoba", "arena", "hueso",
    "marfil", "ocre", "tabaco", "cerezo", "miel", "wengue", "encino", "pino", "maple",
    "grafito", "carbon", "humo", "aqua", "turquesa", "menta", "lavanda", "lila", "vino",
    "camel", "taupe", "olivo", "oliva", "mostaza", "terracota", "coral", "fucsia",
}
_TAZAS = re.compile(r"(\d+)\s*tazas?")


def numeros(nombre):
    """Números y siglas de variante que separan dos modelos de la misma línea."""
    t = ag._limpiar(nombre).split()
    out = set()
    for i, w in enumerate(t):
        if w in ROMANOS or w in VARIANTE_CORTA or _NUM_LETRA.match(w) and not _UNIDAD.match(w[-1]):
            out.add(w)
            continue
        if w.isdigit() and len(w) <= 4 and not 1990 <= int(w) <= 2030:
            sig = t[i + 1] if i + 1 < len(t) else ""
            ant = t[i - 1] if i else ""
            if _UNIDAD.match(sig) or ant in ("de", "x", "por", "para"):
                continue
            out.add(w)
    return out


def colores_extra(nombre):
    return {w for w in ag._limpiar(nombre).split() if w in COLORES_EXTRA}


def motivo_no(a, b):
    ma, mb = M.marca_de(a), M.marca_de(b)
    if not (ma and mb and ma == mb):
        return "marca ausente o distinta"
    na, nb = a["name"], b["name"]
    if numeros(na) != numeros(nb):
        return "números o variante distintos"
    if set(_TAZAS.findall(ag._limpiar(na))) != set(_TAZAS.findall(ag._limpiar(nb))):
        return "tazas distintas"
    ca, cb = colores_extra(na), colores_extra(nb)
    if ca and cb and ca != cb:
        return "color distinto"
    return M.motivo_no(a, b)


def resolver(products):
    fichas, por_tok = {}, collections.defaultdict(list)
    for i, p in enumerate(products):
        if not p.get("offers") or p.get("category") in EXCLUIDAS or M.codigos(p["name"]):
            continue
        toks = ag._tokens(p["name"])
        if len(toks) < MIN_PALABRAS:
            continue
        fichas[i] = toks
        for t in toks:
            por_tok[(p["category"], t)].append(i)

    padre = {}

    def raiz(x):
        while padre.get(x, x) != x:
            x = padre[x]
        return x

    motivos = collections.Counter()
    for i, toks in fichas.items():
        a = products[i]
        ta = M.tiendas_de(a)
        if len(ta) != 1:
            continue
        cnt = collections.Counter()
        for t in toks:
            for j in por_tok.get((a["category"], t), ()):
                if j != i:
                    cnt[j] += 1
        # Subconjunto: las palabras compartidas son TODAS las del más corto.
        cands = [products[j] for j, n in cnt.items()
                 if n == min(len(toks), len(fichas[j])) and not (M.tiendas_de(products[j]) & ta)]
        if not cands:
            continue
        pasan = []
        for b in cands:
            m = motivo_no(a, b)
            if m is None:
                pasan.append(b)
            else:
                motivos[m] += 1
        if not pasan:
            continue
        if len(pasan) > 1 and not M.grupo_coherente(pasan):
            motivos["ambiguo"] += 1
            continue
        for b in pasan:
            ra, rb = raiz(a["id"]), raiz(b["id"])
            if ra != rb:
                padre[rb] = ra
    por_id = {p["id"]: p for p in products}
    grupos = collections.defaultdict(list)
    for pid in set(padre) | set(padre.values()):
        grupos[raiz(pid)].append(por_id[pid])
    buenos = []
    for g in grupos.values():
        if len(g) > 1 and M.grupo_coherente(g):
            buenos.append(sorted(g, key=id_num))
        else:
            motivos["grupo ambiguo"] += len(g)
    return buenos, motivos, len(fichas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--muestra", type=int, default=25)
    ap.add_argument("--informe")
    ap.add_argument("--keep-pages", action="store_true")
    args = ap.parse_args()

    data = load_catalog()
    products = data["products"]
    grupos, motivos, n = resolver(products)
    print(f"Fichas sin código consideradas: {n:,}   grupos fusionables: {len(grupos):,}")
    print("Rechazos:", ", ".join(f"{m} {k:,}" for m, k in motivos.most_common(8)))
    combos = collections.Counter(tuple(sorted(set().union(*(M.tiendas_de(p) for p in g)))) for g in grupos)
    print("Combinaciones de tiendas:", ", ".join(f"{'+'.join(c)} {k:,}" for c, k in combos.most_common(8)))
    random.seed(21)
    for g in random.sample(grupos, min(args.muestra, len(grupos))):
        print()
        for p in g:
            print("    " + M._linea(p))
    if args.informe:
        with open(args.informe, "w", encoding="utf-8") as f:
            json.dump([[{"id": p["id"], "tiendas": sorted(M.tiendas_de(p)), "categoria": p.get("category"),
                         "nombre": p["name"], "precio": M.precio_min(p)} for p in g] for g in grupos],
                      f, ensure_ascii=False, indent=1)
        print(f"\nInforme: {args.informe}")
    if args.dry_run:
        print("\n(--dry-run: no se escribió nada)")
        return
    absorbidas = set()
    for g in grupos:
        _, resto = M.fusionar(g)
        absorbidas.update(p["id"] for p in resto)
    data["products"] = [p for p in products if p["id"] not in absorbidas]
    save_catalog(data)
    print(f"\nFichas absorbidas: {len(absorbidas):,}; catálogo: {len(data['products']):,} productos")
    if not args.keep_pages:
        gone = 0
        for pid in absorbidas:
            path = os.path.join(ROOT, "producto", pid)
            if os.path.isdir(path):
                shutil.rmtree(path)
                gone += 1
        print(f"Páginas estáticas borradas: {gone}")


if __name__ == "__main__":
    main()
