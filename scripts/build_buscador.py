#!/usr/bin/env python3
"""Escribe el índice de búsqueda por palabra (data/buscar/).

POR QUÉ
-------
Con 860 mil fichas, buscar «samsung» bajaba 36 de las 56 categorías
enteras (~48 MB con gzip) para filtrar en el navegador: data/search-index.json
solo dice QUÉ CATEGORÍAS tienen la palabra, no qué fichas. Este índice dice
qué fichas, y trae lo justo de cada una para contar, ordenar y filtrar sin
bajar la ficha: la SPA baja el archivo de la palabra (unos cientos de KB) y
después solo las filas de la página que se ve.

QUÉ ESCRIBE
-----------
data/buscar/meta.json
    {"v": 1, "cats": [...], "subs": [[...], ...], "filas": 100}
    cats/subs son las listas a las que apuntan los índices de abajo.

data/buscar/b/<pre>.json.gz     (pre = las 3 primeras letras de la raíz)
    {"<raíz>": POSTING | "*"}
    "*" = palabra frecuente, con archivo propio en data/buscar/w/<raíz>.json.gz
    (así un prefijo -- «sams» -- encuentra sus palabras sin bajar un
    vocabulario entero).

POSTING = [ids, f, p, c, s], columnas del mismo largo:
    ids  número de ficha (p12345 -> 12345), en orden y como diferencias
    f    bits: 1 nombre, 2 categoría/subcategoría, 4 marca, 8 usado o
         reacondicionado, 16 atípico (ver atipicos.py); + 32 * rango de
         popularidad (popularityRank de js/app.js, 0-10)
    p    precio más bajo, en pesos enteros (sin envío)
    c    índice de categoría en meta.cats
    s    índice de subcategoría en meta.subs[c] (-1 sin subcategoría)

data/buscar/f/<n>.json.gz       (n = número de ficha // FILAS)
    {"p12345": ficha ligera, igual a la de su shard de categoría, con
     "category" y "_i" (su posición en la categoría: ubica el chunk de detalle)}

La raíz es la misma de la SPA (searchStem de js/app.js): sin acentos, en
minúsculas, partida entre letras y números («iphone17» -> iphone, 17), y sin
el plural -s/-es de las palabras largas. Las palabras vacías («de», «para»)
y las letras sueltas no se indexan: son el 10% de todo el índice y no
distinguen nada.

USO
---
    python3 scripts/build_buscador.py
"""
import collections
import json
import os
import re
import shutil
import sys
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import ROOT, MANIFEST_PATH, leer_json, escribir_texto_json, nombre_logico  # noqa: E402

SALIDA = os.path.join(ROOT, "data", "buscar")
FILAS = 400         # fichas por bloque de filas (400 comprime ~6% mejor que 100)
FRECUENTE = 1500      # desde cuántas fichas una palabra va en archivo propio
VACIAS = {
    "de", "del", "la", "el", "los", "las", "para", "con", "sin", "por", "en",
    "al", "y", "o", "e", "u", "un", "una", "unos", "unas", "a", "que", "se",
    "su", "sus", "the", "and", "for", "of", "with",
}
USADO_RE = re.compile(r"preowned|usado|reacondicionad", re.I)


def normalizar(s):
    # NFKC antes: nombres con «ＵＳＢ» o «１ＴＢ» en ancho completo se indexan
    # como «usb» / «1tb», igual que la consulta (ver normalizeIndexWord en app.js).
    s = unicodedata.normalize("NFD", unicodedata.normalize("NFKC", s or ""))
    return "".join(c for c in s if not ("̀" <= c <= "ͯ")).lower()


def raiz(w):
    if len(w) >= 7 and w.endswith("es"):
        return w[:-2]
    if len(w) >= 5 and w.endswith("s"):
        return w[:-1]
    return w


def palabras(texto):
    t = normalizar(texto)
    t = re.sub(r"([a-z])(\d)", r"\1 \2", t)
    t = re.sub(r"(\d)([a-z])", r"\1 \2", t)
    salida = set()
    for w in re.findall(r"[a-z0-9]+", t):
        if w in VACIAS or (len(w) == 1 and not w.isdigit()):
            continue
        salida.add(raiz(w))
    return salida


def ofertas_de(p):
    ofs = list(p.get("offers") or [])
    for v in p.get("colorVariants") or []:
        ofs.extend(v.get("offers") or [])
    return ofs


def resumen(p):
    ofs = [o for o in ofertas_de(p) if isinstance(o.get("price"), (int, float)) and o["price"] > 0]
    if not ofs:
        return None
    en_stock = [o for o in ofs if o.get("stock") != "out_of_stock"] or ofs
    barata = min(en_stock, key=lambda o: o["price"])
    vendedores = sum(o.get("sellerCount") or 1 for o in (p.get("offers") or [])) or 1
    lista = barata.get("listPrice")
    dto = round((1 - barata["price"] / lista) * 100) if lista and lista > barata["price"] else 0
    rango = (min(vendedores - 1, 2) * 2 + (2 if p.get("photo") else 0)
             + (1 if p.get("specs") else 0) + (min(3, round(dto / 15)) if dto else 0))
    usado = any(s.get("label") == "Condición" and USADO_RE.search(str(s.get("value") or ""))
                for s in p.get("specs") or [])
    return round(barata["price"]), rango, usado


def main():
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)
    cats = list(manifest["categoryFiles"].keys())
    subs = []
    idx_sub = []
    for c in cats:
        cat = next((x for x in manifest["categories"] if x["id"] == c), {"subcategories": []})
        lista = [s["id"] for s in cat.get("subcategories") or []]
        subs.append(lista)
        idx_sub.append({s: i for i, s in enumerate(lista)})
    palabras_cat = {}

    postings = collections.defaultdict(list)   # raíz -> [(id, f, p, c, s)]
    filas = collections.defaultdict(dict)
    n = 0
    for ci, c in enumerate(cats):
        pos = 0
        for fname in manifest["categoryFiles"][c]:
            for p in leer_json(fname):
                i = pos
                pos += 1
                num = int(p["id"][1:])
                p["category"] = c
                p["_i"] = i
                filas[num // FILAS][p["id"]] = p
                r = resumen(p)
                if r is None:
                    continue
                precio, rango, usado = r
                sub = p.get("subcategory") or ""
                si = idx_sub[ci].get(sub, -1)
                if si == -1 and sub:
                    subs[ci].append(sub)
                    si = idx_sub[ci][sub] = len(subs[ci]) - 1
                clave_cat = (c, sub)
                if clave_cat not in palabras_cat:
                    palabras_cat[clave_cat] = palabras(f"{c} {sub}")
                nombre = palabras(p.get("name"))
                marca = palabras(p.get("brand"))
                base = (8 if usado else 0) + (16 if p.get("a") else 0) + 32 * rango
                for w in nombre | marca | palabras_cat[clave_cat]:
                    f = base + (1 if w in nombre else 0) + (2 if w in palabras_cat[clave_cat] else 0) \
                        + (4 if w in marca else 0)
                    postings[w].append((num, f, precio, ci, si))
                n += 1

    if os.path.isdir(SALIDA):
        viejos = {os.path.relpath(os.path.join(d, x), SALIDA)
                  for d, _, xs in os.walk(SALIDA) for x in xs}
    else:
        viejos = set()
    escritos = set()

    def escribir(rel, obj):
        escribir_texto_json(os.path.join(SALIDA, rel), json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
        escritos.add(rel + ".gz" if rel != "meta.json" else rel)

    def columnas(lista):
        lista.sort()
        ids, fs, ps, cs, ss = [], [], [], [], []
        prev = 0
        for num, f, p, c, s in lista:
            ids.append(num - prev)
            prev = num
            fs.append(f)
            ps.append(p)
            cs.append(c)
            ss.append(s)
        return [ids, fs, ps, cs, ss]

    cubetas = collections.defaultdict(dict)
    propios = 0
    for w, lista in postings.items():
        cubeta = cubetas[w[:3]]
        if len(lista) >= FRECUENTE:
            cubeta[w] = "*"
            escribir(f"w/{w}.json", columnas(lista))
            propios += 1
        else:
            cubeta[w] = columnas(lista)
    for pre, cubeta in cubetas.items():
        escribir(f"b/{pre}.json", cubeta)
    for k, fila in filas.items():
        escribir(f"f/{k}.json", fila)

    # Los .json.gz de rutas que ya no existen (una palabra que dejó de ser
    # frecuente, un bloque de fichas vaciado) se borran.
    borrados = 0
    for rel in viejos - escritos:
        if rel == "meta.json" or not rel.endswith(".json.gz"):
            continue
        os.remove(os.path.join(SALIDA, rel))
        borrados += 1

    # meta.json al final: la SPA solo usa el índice si está, y así nunca ve
    # un meta nuevo apuntando a archivos a medio escribir.
    escribir("meta.json", {"v": 1, "cats": cats, "subs": subs, "filas": FILAS})
    peso = sum(os.path.getsize(os.path.join(d, x)) for d, _, xs in os.walk(SALIDA) for x in xs)
    print(f"Índice de búsqueda: {n:,} fichas, {len(postings):,} raíces "
          f"({propios:,} con archivo propio), {len(cubetas):,} cubetas, {len(filas):,} bloques de filas; "
          f"{peso / 1e6:.1f} MB en disco, {borrados} archivos viejos borrados")


if __name__ == "__main__":
    main()
