#!/usr/bin/env python3
"""Junta en UNA ficha las publicaciones de una tienda que son el mismo
artículo en otra variante (otro modelo de auto, otro color, otra talla), y
deja cada publicación como variante elegible de la oferta (4-oct-2026).

EL CASO
-------
Elektra (y en menor medida Coppel y Walmart) publica el mismo artículo una
vez por cada auto en el que va, o por cada color, con la MISMA foto y el
MISMO precio y sólo el final del título distinto:

    2 Bocinas Slim 200w Suzuki Swift+ 2004-2010        $499   (2,412 así)
    Espejo Retrovisor para Toyota Highlander 2020 a 2023  $729   (1,585 así)
    Estéreo 7" CarPlay Inalámbrico Seat Ibiza 2018-2023  $1,599 (1,122 así)

En el sitio eran miles de filas idénticas. Ningún merge_* las tocaba:
merge_same_store y merge_misma_foto exigen el MISMO nombre, y aquí el nombre
cambia en el modelo de auto o el color.

POR QUÉ COMO VARIANTES Y NO TIRANDO LAS DEMÁS
--------------------------------------------
merge_misma_foto se queda con una oferta por tienda y descarta las otras
urls. Aquí eso dejaría al que busca el espejo de su Jetta con el enlace del
de una Highlander. Cada publicación absorbida queda en
offer.variants = [{label, url[, photo]}], que la ficha ya muestra (pastillas
y, con muchas, una lista para elegir: ver renderOfferRows en js/app.js y
generate_seo_pages.py).

CUÁNDO SE JUNTA
---------------
  * todas las publicaciones de la ficha en la misma tienda (lo que ya se
    emparejó con otra tienda es de un modelo concreto y no se toca); las fichas con colores
    (colorVariants) entran con todas sus publicaciones, y las variantes van en
    la oferta del primer color, que es con lo que se arma su tabla;
  * misma foto: el nombre del archivo cuando es propio («07503060608016.jpeg»,
    «D_NQ_NP_2X_975593-MLM...jpg»); si es genérico («1.jpeg», «img.png»), el
    id del asset de la tienda, que es la misma imagen subida una vez;
  * precio a menos de 2% entre la más barata y la más cara;
  * misma marca (o sin marca) y el nombre del mismo artículo: la primera
    palabra igual, o al menos la mitad de las palabras en común. Con la misma
    foto y precio hay publicaciones que son otro artículo de la misma línea
    («Bumper ... Hello Kitty» y «Carcasa ... Hello Kitty» a $285): la
    primera palabra distinta y pocas palabras en común las deja separadas.

QUÉ FICHA QUEDA Y CÓMO SE LLAMA
-------------------------------
La de id más bajo (la que ya está indexada); todas son de la misma categoría
y subcategoría. Si todos los nombres empiezan igual y lo que cambia es el
final, la ficha pasa a llamarse con lo común («Espejo Retrovisor», y si lo
que cambia es el auto, «Espejo Retrovisor para auto (varios modelos)») y la
etiqueta de cada variante es lo que sigue («Toyota Highlander 2020 a
2023»). Si lo que cambia está en medio («... Individual Gris+ Almohada» /
«... Azul+ ...»), el nombre se queda y la etiqueta son las palabras propias
de esa publicación. Las absorbidas se redirigen a la que queda
(registrar_fusiones), como en los demás merge_*.

USO
---
    python3 scripts/merge_variantes_tienda.py --dry-run
    python3 scripts/merge_variantes_tienda.py
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

RATIO = 1.02
_GENERICA = re.compile(r"^(\d{1,3}|img|image|imagen|foto|photo|principal|main|default|producto|frente|front)?"
                       r"[-_ ]?\d{0,3}\.(jpe?g|png|webp|gif)(\.(jpe?g|png|webp))?$", re.I)
_VTEX = re.compile(r"/arquivos/ids/(\d+)(?:-\d+-\d+)?/([^/?#]+)")
_ANIOS = re.compile(r"\b(19[3-9]\d|20[0-4]\d)\b")
# La llanta de otra medida es otro producto (las subcategorías van por rin y
# Comparacalidad compara medidas), aunque Bodega le ponga la misma foto y
# el mismo precio a varias.
_MEDIDA_LLANTA = re.compile(r"(?<!\d)\d{3}/\d{2}\s?z?r\s?\d|\b\d{2}x\d{1,2}(\.\d{1,2})?-?r?\d{2}\b|\brin\s?\d{2}\b")
# Elektra escribe la medida de muchas formas («235 70/ R 16», «185 65 r14»):
# cualquier llanta o rin queda fuera, se lea o no su medida.
# Sólo cuando el título ES una llanta («Llanta ...», «Paquete de 2 llantas
# ...»): el «Sensor de presión de neumáticos» para 40 autos sí es uno solo.
_ES_LLANTA = re.compile(r"^(\d+ |paquete (de )?\d+ |set (de )?\d+ |juego (de )?\d+ )?(llantas?|neumaticos?|rines?|rin)\b")
# El sufijo del almacén de Elektra («... Gris RGH» / «... Gris TRY»): la
# misma publicación desde otro almacén, no una variante.
_CODIGO_ALMACEN = re.compile(r"^[A-Z]{2,4}$")
_CONECTOR = {"para", "de", "del", "con", "compatible", "compatibles", "la", "el", "los", "las", "y", "en", "a",
             "por", "tipo", "modelo", "-", "+", "|", "/", ",", "–", "—"}


def norm(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def clave_foto(p):
    u = (p.get("photo") or "").split("?")[0]
    if not u:
        return None
    m = _VTEX.search(u)
    if m:
        archivo = m.group(2)
        return ("vtex-id", m.group(1)) if _GENERICA.match(archivo) or len(archivo) < 12 else ("archivo", archivo)
    archivo = os.path.basename(u)
    if _GENERICA.match(archivo) or len(archivo) < 12:
        return ("url", u)
    return ("archivo", archivo)


_MARCAS_VACIAS = {"generico", "generica", "genericos", "generic", "sinmarca", "otros", "otra", "na", "nd", "varios"}


def marca_comparable(b):
    """La marca para comparar: sin espacios ni signos («T&s Brass» = «ts brass»
    -> «tsbrass»), y vacía si es «Genérico»/«Sin marca»."""
    n = norm(b).replace(" ", "")
    return "" if n in _MARCAS_VACIAS else n


def misma_marca(a, b):
    a, b = marca_comparable(a), marca_comparable(b)
    return not a or not b or a == b or (min(len(a), len(b)) >= 2 and (a.startswith(b) or b.startswith(a)))


def mismo_articulo(a, b):
    ta, tb = norm(a).split(), norm(b).split()
    if not ta or not tb:
        return False
    if ta[0] == tb[0]:
        return True
    sa, sb = set(ta), set(tb)
    return len(sa & sb) / len(sa | sb) >= 0.5


def racimos_por_precio(ps):
    """Parte una lista en tramos de precio donde la más cara no pasa de RATIO
    veces la más barata."""
    ps = sorted(ps, key=lambda p: p["offers"][0]["price"])
    out, cur = [], []
    for p in ps:
        if cur and p["offers"][0]["price"] > RATIO * cur[0]["offers"][0]["price"]:
            out.append(cur)
            cur = []
        cur.append(p)
    if cur:
        out.append(cur)
    return [g for g in out if len(g) > 1]


def palabras(nombre):
    """Palabras del nombre tal como están escritas, con su forma normalizada."""
    out = []
    for w in nombre.split():
        n = norm(w)
        out.append((w, n))
    return out


def prefijo_comun(nombres):
    listas = [palabras(n) for n in nombres]
    k = 0
    while all(len(l) > k for l in listas) and len({l[k][1] for l in listas}) == 1:
        k += 1
    # Una palabra cortada por la tienda («Inal» de «Inalámbrico») no corta
    # el prefijo de las demás, pero aquí basta con lo que coincide entero.
    while k > 0 and (listas[0][k - 1][1] in _CONECTOR or not listas[0][k - 1][1]):
        k -= 1
    return k


def nombre_familia(nombres, jefe):
    """El nombre de un grupo que cambia de auto en auto: el comienzo común
    («Foco oem») y las demás palabras que tiene al menos el 80% del grupo
    («ford original»), sin números ni conectores, y «para auto (varios
    modelos)». None si no quedan al menos dos palabras."""
    k = prefijo_comun(nombres)
    cuenta = collections.Counter(w for n in nombres for w in set(norm(n).split()))
    ws = palabras(jefe)
    quedan, vistas = [], set()
    for i, (w, n) in enumerate(ws):
        if not n or n in vistas:
            continue
        if i < k or (cuenta[n] >= 0.8 * len(nombres) and not re.search(r"\d", n)
                     and n not in _CONECTOR and n != "al"):
            quedan.append(w)
            vistas.add(n)
    while quedan and norm(quedan[-1]) in _CONECTOR | {"al"}:
        quedan.pop()
    if len(quedan) < 2:
        return None
    base = " ".join(quedan)
    return base + ("" if "auto" in norm(base).split() else " para auto (varios modelos)")


def etiqueta(nombre, k, comunes):
    ws = palabras(nombre)
    if k:
        resto = [w for w, _ in ws[k:]]
        while resto and norm(resto[0]) in _CONECTOR | {""}:
            resto = resto[1:]
    else:
        resto = [w for w, n in ws if n and n not in comunes]
    txt = " ".join(resto).strip(" -+|,")
    return (txt[:57] + "…") if len(txt) > 58 else txt


def publicaciones(p):
    """[(oferta, color)] de todas las publicaciones de la ficha: las ofertas y,
    en una ficha con colores (merge_by_color), las de cada color."""
    out = [(o, None) for o in p.get("offers") or []]
    for v in p.get("colorVariants") or []:
        out += [(o, v.get("color")) for o in v.get("offers") or []]
    return out


def oferta_ancla(p):
    """La oferta que lleva las variantes. Con colores, la tabla de la ficha se
    arma con las ofertas de cada color (no con product.offers): va en la del
    primer color."""
    for v in p.get("colorVariants") or []:
        if v.get("offers"):
            return v["offers"][0]
    return p["offers"][0]


def grupos_fusionables(data):
    por_clave = collections.defaultdict(list)
    for p in data["products"]:
        ofs = p.get("offers") or []
        if not ofs or not ofs[0].get("price") or not ofs[0].get("url"):
            continue
        # Una sola tienda: lo que ya se emparejó con otra tienda es de un
        # modelo concreto. Las fichas con colores (las «Pantalla Techo Auto»
        # de cada auto en negro y gris) entran.
        # Basta con que todas sus publicaciones sean de la misma tienda: el
        # control de aire de Elektra «para Carrier» ya traía dos SKU juntos
        # (merge_same_store) y con «una sola oferta» quedaba fuera.
        if len({o.get("storeId") for o, _ in publicaciones(p)}) != 1:
            continue
        if _MEDIDA_LLANTA.search((p.get("name") or "").lower()) or _ES_LLANTA.search(norm(p.get("name"))) \
                or "Llantas" in (p.get("subcategory") or "") or "Rines" in (p.get("subcategory") or ""):
            continue
        f = clave_foto(p)
        if f:
            # Misma categoría y subcategoría: lo que se reparte por medida
            # (rin, pulgadas, capacidad) no se junta entre subcategorías.
            por_clave[(ofs[0].get("storeId"), p.get("category"), p.get("subcategory"), f)].append(p)
    grupos = []
    descartes = collections.Counter()
    for ps in por_clave.values():
        if len(ps) < 2:
            continue
        for g in racimos_por_precio(ps):
            g = sorted(g, key=id_num)
            jefe = g[0]
            ok = [jefe]
            for p in g[1:]:
                if not misma_marca(jefe.get("brand"), p.get("brand")):
                    descartes["otra marca"] += 1
                elif not mismo_articulo(jefe["name"], p["name"]):
                    descartes["otro artículo"] += 1
                else:
                    ok.append(p)
            if len(ok) > 1:
                grupos.append(ok)
    return grupos, descartes


def aplicar(data, grupos):
    fuera, renombradas = set(), 0
    for g in grupos:
        jefe = g[0]
        o = oferta_ancla(jefe)
        nombres = [p["name"] for p in g]
        # Lo que ya era variante de alguna (corridas anteriores) entra igual.
        previas = []
        for p in g:
            previas += oferta_ancla(p).get("variants") or []
        k = prefijo_comun(nombres)
        largo = len(" ".join(w for w, _ in palabras(jefe["name"])[:k]))
        if k < 2 or largo < 10:
            k = 0
        comunes = set.intersection(*[set(norm(n).split()) for n in nombres])
        variantes, urls = [], {po["url"] for po, _ in publicaciones(jefe) if po.get("url")}
        for p in g[1:]:
            for po, color in publicaciones(p):
                if not po.get("url") or po["url"] in urls:
                    continue
                urls.add(po["url"])
                v = {"label": etiqueta(p["name"], k, comunes) or p["name"][:58], "url": po["url"]}
                if color:
                    v["label"] = f"{v['label']} · {color}"
                if norm(p["name"]) == norm(jefe["name"]) and not color or _CODIGO_ALMACEN.match(v["label"]):
                    # La misma publicación repetida, o desde otro almacén
                    # («... RGH» / «... TRY»): se guarda (así el importador la
                    # reconoce y no la vuelve a dar de alta), pero la ficha no
                    # la ofrece como variante.
                    v["dup"] = True
                foto = po.get("photo") or p.get("photo")
                if foto and foto != jefe.get("photo"):
                    v["photo"] = foto
                variantes.append(v)
        for v in previas:
            if v.get("url") and v["url"] not in urls:
                urls.add(v["url"])
                variantes.append(v)
        if variantes and not k and len(g) >= 3 and sum(1 for n in nombres if _ANIOS.search(n)) >= 0.8 * len(nombres):
            # Sin un comienzo común largo y lo que cambia es el auto: el nombre
            # de la primera publicación («... 1966 a 1969 excalibur ...»)
            # describía uno solo de los 3,670.
            nuevo = nombre_familia(nombres, jefe["name"])
            if nuevo:
                jefe.setdefault("nombreTienda", jefe["name"])
                jefe["name"] = nuevo
                renombradas += 1
        if variantes:
            variantes.sort(key=lambda v: norm(v["label"]))
            o["variants"] = variantes
            # Las palabras de las variantes para el buscador: quien busca
            # «espejo jetta» tiene que encontrar el espejo aunque la ficha ya
            # no se llame «... para Volkswagen Jetta ...».
            propias = set(norm(jefe["name"]).split())
            alias = []
            for v in [{"label": jefe["name"]}] + [v for v in variantes if not v.get("dup")]:
                for w in norm(v["label"]).split():
                    if len(w) >= 3 and w not in propias:
                        propias.add(w)
                        alias.append(w)
            if alias:
                jefe["alias"] = " ".join(alias[:400])
            if k:
                o["variantLabel"] = etiqueta(jefe["name"], k, comunes) or "Esta"
                base = " ".join(w for w, _ in palabras(jefe["name"])[:k])
                autos = sum(1 for n in nombres if _ANIOS.search(n[len(base):]))
                nuevo = base + (" para auto (varios modelos)" if autos >= len(nombres) / 2 and "auto" not in norm(base).split() else "")
                if nuevo != jefe["name"]:
                    jefe.setdefault("nombreTienda", jefe["name"])
                    jefe["name"] = nuevo
                    renombradas += 1
        for p in g[1:]:
            for campo in ("specs", "gtin", "brand"):
                if not jefe.get(campo) and p.get(campo):
                    jefe[campo] = p[campo]
            fuera.add(p["id"])
    data["products"] = [p for p in data["products"] if p["id"] not in fuera]
    return fuera, renombradas


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--muestra", type=int, default=15)
    args = ap.parse_args()
    data = load_catalog()
    grupos, descartes = grupos_fusionables(data)
    por_tienda = collections.Counter(oferta_ancla(g[0]).get("storeId") for g in grupos)
    print(f"variantes de una misma publicación -> grupos: {len(grupos):,}; "
          f"fichas absorbidas: {sum(len(g) - 1 for g in grupos):,}; no: {dict(descartes)}")
    print("   por tienda:", dict(por_tienda.most_common()))
    random.seed(4)
    for g in random.sample(grupos, min(args.muestra, len(grupos))):
        print(f"   {len(g):5} ${g[0]['offers'][0]['price']:,.0f} | " + " | ".join(p["name"][:45] for p in g[:3]))
    if args.dry_run:
        import copy
        prueba = {"products": [copy.deepcopy(p) for g in grupos for p in g]}
        aplicar(prueba, [[next(q for q in prueba["products"] if q["id"] == p["id"]) for p in g]
                         for g in random.sample(grupos, min(args.muestra, len(grupos)))])
        for p in prueba["products"]:
            if oferta_ancla(p).get("variants"):
                vs = oferta_ancla(p)["variants"]
                print(f"   -> «{p['name']}» [{oferta_ancla(p).get('variantLabel', 'Esta')}] + "
                      + ", ".join(v["label"] for v in vs[:4]) + (f" … ({len(vs)})" if len(vs) > 4 else ""))
        print("(--dry-run: no se escribió nada)")
        return 0
    fuera, renombradas = aplicar(data, grupos)
    save_catalog(data)
    registrar_fusiones((p["id"], g[0]["id"]) for g in grupos for p in g[1:])
    print(f"Guardado: {len(fuera):,} fichas absorbidas como variantes; {renombradas:,} renombradas; "
          f"catálogo {len(data['products']):,}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
