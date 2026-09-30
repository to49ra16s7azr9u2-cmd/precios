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
         reacondicionado, 16 atípico (ver atipicos.py), 512 la palabra es
         la CABEZA del nombre (ver cabeza_del_nombre); + 32 * rango de
         popularidad (popularityRank de js/app.js, 0-10, bits 32-256)
    p    precio más bajo, en pesos enteros (sin envío), con la regla de la
         SPA (precio_como_la_spa): el orden por precio de la búsqueda coincide
         con el precio que muestra la fila
    c    índice de categoría en meta.cats
    s    índice de subcategoría en meta.subs[c] (-1 sin subcategoría)

data/buscar/f/<n>.json.gz       (n = número de ficha // FILAS)
    {"p12345": ficha ligera, igual a la de su shard de categoría, con
     "category" y "_i" (su posición en la categoría: ubica el chunk de detalle)}

data/buscar/c/<i>.json.gz        (i = índice de la categoría en meta.cats)
    Solo para las categorías enormes (RESUMEN_MIN_SHARDS o más shards, hoy
    Autopartes: 364 mil fichas, 194 MB de JSON). La SPA abre la categoría
    con esto en vez de bajar sus shards: una fila por ficha, en el orden del
    catálogo, con lo justo para filtrar, contar y ordenar, y después baja
    solo las filas de la página que se ve (data/buscar/f).
    {"n": fichas, "id": [...], "f": [...], "p": [...], "v": [...], "s": [...],
     "m": [...], "marcas": [...], "facetas": {campo: {"dic": [...], "col": [...]}}}
    id  número de ficha, como diferencia con el anterior
    f   8 usado, 16 atípico, 1 con foto; + 32 * rango de popularidad
    p   precio más bajo en centavos (el mismo «Desde» de la SPA)
    v   número de vendedores (sellerTotal de la SPA)
    s   índice de subcategoría en meta.subs[i] (-1 sin subcategoría)
    m   índice de marca en "marcas" (-1 sin marca)
    facetas: cada campo con su diccionario de valores ("dic", ordenado).
        "col" es una lista con -1 (no tiene), un índice, o una lista de
        índices (campos con varios valores) en la que un número negativo -k
        quiere decir «y todos los que siguen hasta k» ([3, -7] = 3,4,5,6,7:
        los años de un modelo suelen ser seguidos).
        "txt" en lugar de "col" (campos de un solo valor): un carácter por
        ficha, " " = no tiene, y si no la letra número índice de LETRAS
        (ASCII desde "#" sin la barra invertida, y después U+00A1...). Una
        cadena se lee mucho más rápido que una lista de 364 mil números.
        "s" y "m" van igual, como cadena, cuando caben en LETRAS.
    El precio, el rango y los vendedores se calculan con la MISMA regla que
    la SPA (precio_como_la_spa): el orden de la lista no cambia según se
    haya abierto la categoría con el resumen o con sus shards.

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
import math
import os
import re
import shutil
import sys
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import ROOT, MANIFEST_PATH, leer_json, escribir_texto_json, nombre_logico  # noqa: E402

SALIDA = os.path.join(ROOT, "data", "buscar")
# Fichas por bloque de filas. Era 400 (comprime ~6% mejor que 100), pero
# cada fila de una página de resultados cae en un bloque distinto: 20 filas
# pedían 18 bloques de ~164 KB de JSON, ~3 MB a leer en el teléfono para
# mostrar 20 fichas (29-sep: «buscar un nombre también es pesado»). Con 100
# se lee la cuarta parte por página.
FILAS = 100
FRECUENTE = 1500      # desde cuántas fichas una palabra va en archivo propio
RESUMEN_MIN_SHARDS = 8  # categorías con resumen propio (data/buscar/c)
FACETA_MIN = 0.01     # un campo entra al resumen si lo tiene al menos el 1%
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


# Palabras que abren un nombre sin ser lo que el producto ES («Mini lavadora
# portátil», «Nuevo taladro»): la cabeza es la siguiente.
# Lo mismo con los contenedores («Juego de sábanas», «Kit de limpieza»,
# «2 piezas funda»): lo que se compra es lo de adentro. La SPA aplica la
# misma regla a la consulta (CONTENEDORES_CONSULTA en js/app.js).
NO_CABEZA = {"mini", "nuevo", "nueva", "nuevos", "nuevas", "original", "originales", "super", "gran",
             "juego", "juegos", "set", "sets", "kit", "kits", "par", "pares", "paquete", "paquetes",
             "pack", "packs", "lote", "combo", "combos", "pieza", "piezas", "pza", "pzas", "pz", "pzs"}
BIT_CABEZA = 512


def cabeza_del_nombre(nombre, marca):
    """La raíz de lo que el producto ES: la primera palabra del nombre que no
    es vacía, ni número, ni de la marca, ni de NO_CABEZA. «Secadora de ropa
    Samsung 24 kg» -> secadora; «Sábanas para secadora Downy» -> sabana;
    «Samsung secadora 24 kg» -> secadora. Buscar «secadora de ropa» y
    ordenar por precio ponía arriba sábanas y soportes «para secadora»
    (28-sep, captura del usuario): la SPA ordena primero lo que tiene la
    palabra buscada como cabeza."""
    de_marca = palabras(marca)
    t = normalizar(nombre)
    t = re.sub(r"([a-z])(\d)", r"\1 \2", t)
    t = re.sub(r"(\d)([a-z])", r"\1 \2", t)
    for w in re.findall(r"[a-z0-9]+", t):
        if w in VACIAS or len(w) < 3 or any(c.isdigit() for c in w) or w in NO_CABEZA:
            continue
        r = raiz(w)
        if r in de_marca:
            continue
        return r
    return None


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
    """(precio en pesos enteros, rango, usado), con las reglas de la SPA."""
    r = precio_como_la_spa(p)
    if r is None or r[0] <= 0:
        return None
    precio, rango, _ = r
    return _jsround(precio), rango, _es_usado(p)


def _jsround(x):
    """Math.round de JavaScript (Python redondea al par)."""
    return math.floor(x + 0.5)


def _fuera_de_variantes(p, variants):
    urls = set()
    for v in variants:
        if v.get("url"):
            urls.add(v["url"])
        for o in v.get("offers") or []:
            if o.get("url"):
                urls.add(o["url"])
    return [o for o in (p.get("offers") or []) if o.get("url") and o["url"] not in urls]


def _opciones_de_compra(p):
    """purchaseOptions de js/app.js, sin filtro de color."""
    variants = p.get("colorVariants") or []
    if variants and any(v.get("offers") for v in variants):
        return [o for v in variants for o in (v.get("offers") or [])] + _fuera_de_variantes(p, variants)
    if variants:
        base = (p.get("offers") or [{}])[0]
        return [dict(base, price=v.get("price"), url=v.get("url"),
                     listPrice=base.get("listPrice") if v.get("url") == base.get("url") else None,
                     sellerCount=v.get("sellerCount"), sellers=v.get("sellers") or None)
                for v in variants] + _fuera_de_variantes(p, variants)
    return p.get("offers") or []


def _filas_de_vendedor(p):
    """sellerRows de js/app.js (solo precio y precio de lista)."""
    filas = []
    for o in _opciones_de_compra(p):
        sellers = o.get("sellers")
        if not sellers or len(sellers) < 2 or not all(x.get("url") for x in sellers):
            cs = o.get("cheapestSeller")
            if not sellers and cs:
                filas.append({"price": cs.get("price"), "listPrice": cs.get("listPrice")})
            else:
                filas.append(o)
        else:
            filas.extend({"price": x.get("price"), "listPrice": x.get("listPrice") or None} for x in sellers)
    return filas


def _es_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def precio_como_la_spa(p):
    """(precio, rango, vendedores) con las reglas de minPrice, popularityRank
    y sellerTotal de js/app.js (sin envío ni filtro de color). None si no
    hay ningún precio."""
    filas = _filas_de_vendedor(p)
    if not filas:
        return None
    barata = filas[0]
    for b in filas[1:]:
        if _es_num(b.get("price")) and _es_num(barata.get("price")) and b["price"] < barata["price"]:
            barata = b
    precio = barata.get("price")
    if not _es_num(precio):
        return None
    lista = barata.get("listPrice")
    dto = _jsround((1 - precio / lista) * 100) if _es_num(lista) and lista and lista > precio else None
    vendedores = sum((o.get("sellerCount") or 1) for o in _opciones_de_compra(p))
    rango = (min(vendedores - 1, 2) * 2 + (2 if p.get("photo") else 0)
             + (1 if p.get("specs") else 0) + (min(3, _jsround(dto / 15)) if dto else 0))
    return precio, rango, vendedores


def _es_usado(p):
    return any(s.get("label") == "Condición" and USADO_RE.search(str(s.get("value") or ""))
               for s in p.get("specs") or [])


# 91 letras ASCII y después 1,887 de dos bytes en UTF-8 (U+00A1-U+07FF).
LETRAS = [chr(c) for c in range(35, 127) if chr(c) != "\\"] + [chr(c) for c in range(0xA1, 0x800)]


def _letra(i):
    return " " if i < 0 else LETRAS[i]


def _con_rangos(indices):
    """[3, 4, 5, 6, 7, 10] -> [3, -7, 10]: tramos de 3 o más seguidos."""
    xs = sorted(set(indices))
    out = []
    i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[j + 1] == xs[j] + 1:
            j += 1
        if j - i >= 2:
            out += [xs[i], -xs[j]]
        else:
            out += xs[i:j + 1]
        i = j + 1
    return out


def _valor_orden(v):
    return (0, v, "") if _es_num(v) else (1, 0, str(v))


def resumen_de_categoria(fichas, idx_sub, subs_cat):
    """El resumen de data/buscar/c para una categoría (ver arriba)."""
    ids, fs, ps, vs, ss, ms = [], [], [], [], [], []
    marcas, idx_marca = [], {}
    # Solo las fichas con precio (las demás no entran al resumen): así cada
    # valor de los diccionarios de facetas lo tiene al menos una ficha.
    con_precio = []
    for p in fichas:
        r = precio_como_la_spa(p)
        if r is not None:
            con_precio.append((p, r))
    fichas = [p for p, _ in con_precio]
    presentes = collections.Counter()
    for p in fichas:
        for k, v in (p.get("facets") or {}).items():
            if v not in (None, "", []):
                presentes[k] += 1
    total = len(fichas) or 1
    campos = sorted(k for k, n in presentes.items() if n / total >= FACETA_MIN)
    # Diccionarios ordenados (números de menor a mayor): así los años
    # seguidos quedan en índices seguidos y se pueden escribir como tramo.
    valores = {k: {} for k in campos}
    multi = {k: False for k in campos}
    for p in fichas:
        facetas = p.get("facets") or {}
        for k in campos:
            v = facetas.get(k)
            if v in (None, "", []):
                continue
            if isinstance(v, list):
                multi[k] = True
                for x in v:
                    valores[k].setdefault(json.dumps(x, ensure_ascii=False), x)
            else:
                valores[k].setdefault(json.dumps(v, ensure_ascii=False), v)
    dics, idx_dic = {}, {}
    for k in campos:
        orden = sorted(valores[k].items(), key=lambda kv: _valor_orden(kv[1]))
        dics[k] = [v for _, v in orden]
        idx_dic[k] = {clave: i for i, (clave, _) in enumerate(orden)}
    cols = {k: [] for k in campos}

    def indice(k, v):
        return idx_dic[k][json.dumps(v, ensure_ascii=False)]

    prev = 0
    for p, r in con_precio:
        precio, rango, vendedores = r
        num = int(p["id"][1:])
        ids.append(num - prev)
        prev = num
        fs.append((8 if _es_usado(p) else 0) + (16 if p.get("a") else 0)
                  + (1 if p.get("photo") else 0) + 32 * rango)
        ps.append(_jsround(precio * 100))
        vs.append(vendedores)
        sub = p.get("subcategory") or ""
        si = idx_sub.get(sub, -1)
        if si == -1 and sub:
            subs_cat.append(sub)
            si = idx_sub[sub] = len(subs_cat) - 1
        ss.append(si)
        marca = p.get("brand") or ""
        if marca:
            if marca not in idx_marca:
                idx_marca[marca] = len(marcas)
                marcas.append(marca)
            ms.append(idx_marca[marca])
        else:
            ms.append(-1)
        facetas = p.get("facets") or {}
        for k in campos:
            v = facetas.get(k)
            if v in (None, "", []):
                cols[k].append(-1)
            elif isinstance(v, list):
                cols[k].append(_con_rangos([indice(k, x) for x in v]))
            else:
                cols[k].append(indice(k, v))
    salida = {}
    for k in campos:
        if not multi[k] and len(dics[k]) <= len(LETRAS):
            salida[k] = {"dic": dics[k], "txt": "".join(_letra(i) for i in cols[k])}
        else:
            salida[k] = {"dic": dics[k], "col": cols[k]}
    como_texto = lambda col: "".join(_letra(i) for i in col) if max(col, default=-1) < len(LETRAS) else col
    return {"n": len(ids), "id": ids, "f": fs, "p": ps, "v": vs, "s": como_texto(ss), "m": como_texto(ms),
            "marcas": marcas, "facetas": salida}


# Código de barras -> fichas, para el lector de la SPA (30-sep, «Aだけ進め
# ましょう»). Las tiendas lo publican como GTIN-14, EAN-13, UPC-A (12) o
# EAN-8, casi siempre con ceros a la izquierda de relleno: sin esos ceros
# los cuatro coinciden con lo que lee la cámara. Partido por los dos últimos
# dígitos (reparten parejo): la SPA baja un solo archivo de ~35 KB por código.
GTIN_PARTES = 100


def gtin_normal(g):
    d = re.sub(r"\D", "", str(g or ""))
    if len(d) not in (8, 12, 13, 14):
        return None
    d = d.lstrip("0")
    return d if len(d) >= 6 else None


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
    gtins = collections.defaultdict(list)       # código -> [(-tiendas, id)]
    filas = collections.defaultdict(dict)
    n = 0
    resumenes = {}
    for ci, c in enumerate(cats):
        pos = 0
        con_resumen = len(manifest["categoryFiles"][c]) >= RESUMEN_MIN_SHARDS
        fichas_cat = [] if con_resumen else None
        for fname in manifest["categoryFiles"][c]:
            for p in leer_json(fname):
                if con_resumen:
                    fichas_cat.append(p)
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
                g = gtin_normal(p.get("gtin"))
                if g:
                    tiendas = len({o.get("storeId") for o in p.get("offers") or []})
                    gtins[g].append((-tiendas, num))
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
                cabeza = cabeza_del_nombre(p.get("name"), p.get("brand"))
                for w in nombre | marca | palabras_cat[clave_cat]:
                    f = base + (1 if w in nombre else 0) + (2 if w in palabras_cat[clave_cat] else 0) \
                        + (4 if w in marca else 0) + (BIT_CABEZA if w == cabeza else 0)
                    postings[w].append((num, f, precio, ci, si))
                n += 1
        if con_resumen:
            resumenes[ci] = resumen_de_categoria(fichas_cat, idx_sub[ci], subs[ci])
            fichas_cat = None

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
    for ci, r in resumenes.items():
        escribir(f"c/{ci}.json", r)
    # Varias fichas con el mismo código (colores que no se fusionaron, la
    # misma publicación dos veces): primero la que más tiendas compara.
    partes = collections.defaultdict(dict)
    for g, lista in gtins.items():
        partes[int(g[-2:]) % GTIN_PARTES][g] = [f"p{num}" for _, num in sorted(lista)]
    for k in range(GTIN_PARTES):
        escribir(f"g/{k:02d}.json", partes.get(k, {}))

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
    escribir("meta.json", {"v": 1, "cats": cats, "subs": subs, "filas": FILAS,
                           "resumen": sorted(cats[ci] for ci in resumenes), "gtin": GTIN_PARTES})
    peso = sum(os.path.getsize(os.path.join(d, x)) for d, _, xs in os.walk(SALIDA) for x in xs)
    print(f"Índice de búsqueda: {n:,} fichas, {len(postings):,} raíces "
          f"({propios:,} con archivo propio), {len(cubetas):,} cubetas, {len(filas):,} bloques de filas; "
          f"{peso / 1e6:.1f} MB en disco, {borrados} archivos viejos borrados; "
          f"{len(gtins):,} códigos de barras")


if __name__ == "__main__":
    main()
