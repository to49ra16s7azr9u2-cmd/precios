#!/usr/bin/env python3
"""Junta cada ficha de Amazon con la ficha del MISMO producto que ya
tiene otra tienda, para que el sitio compare precios en vez de mostrar dos
fichas sueltas.

POR QUÉ HACE FALTA
------------------
importar_captura_amazon.py da de alta cada captura como fichas NUEVAS: no
busca si el producto ya está. Resultado medido el 15 de septiembre de
2026: Amazon es la tienda más grande del catálogo (96,128 ofertas, el 47%)
y sin embargo solo 172 de sus 96,117 fichas (0.2%) están en más de una
tienda. Lo demás son fichas de una sola oferta, sin specs ni precio de
lista, que en el orden por popularidad quedan debajo de las ~80,000 de las
otras tiendas -- por eso "no se ve Amazon" aunque sea casi la mitad del
catálogo. Las fichas de Amazon no traen GTIN, así que merge_by_gtin.py no
las alcanza, y merge_cross_store.py exige el nombre IDÉNTICO, que entre
Amazon y otra tienda no pasa casi nunca.

CÓMO SE DECIDE QUE SON EL MISMO PRODUCTO
----------------------------------------
Se reutilizan los criterios que ya se calibraron a mano en este proyecto
(audit_gtin_matches.py, merge_by_url.py, merge_by_gtin.py), todos a la
vez. Una ficha de Amazon se fusiona con otra solo si:

  1. Están en la misma categoría, y la otra ficha NO es de Amazon ni tiene
     ya una oferta de Amazon.
  2. Comparten un CÓDIGO DE MODELO: un token con letras y dígitos, de 5+
     caracteres (o 4 cuando no es una abreviatura de especificación tipo
     "ddr5"/"usb3"). Se excluyen las medidas con unidad ("100w", "128gb",
     "1080p"): son especificaciones, no identifican un modelo.
  3. La marca coincide. Si las dos fichas declaran marca, tiene que ser la
     misma; si solo una la declara, la palabra tiene que aparecer en el
     nombre de la otra; si ninguna la declara, se exige más parecido de
     nombre (ver 5).
  4. No se contradicen en nada de lo que las dos declaran: versión
     (pro/plus/lite...), medida con la misma unidad (pulgadas, gb, w,
     btu...), cantidad de piezas, ni color. Es _misma_version() de
     merge_by_url.py + cantidad() de merge_by_gtin.py + color_of() de
     match_amazon_capture.py.
  5. Los nombres se parecen: palabras compartidas sobre el nombre más corto
     >= 0.34 (el umbral calibrado en audit_gtin_matches.py), o >= 0.5 si
     ninguna declara marca.
  6. El precio más bajo de una tienda no está a 2.5x o más del de la otra.
  7. Es la ÚNICA candidata que pasa todo lo anterior, y ninguna otra ficha
     de Amazon resuelve contra la misma candidata (dos fichas de Amazon
     apuntando a la misma cosa son casi siempre dos variantes que los
     chequeos no separaron -- se dejan las dos sin tocar).

Cualquier caso que no cumpla TODO queda como está: el sitio prefiere dos
fichas sueltas a una fusión equivocada.

QUÉ FICHA SOBREVIVE
-------------------
La de id más bajo, como en todos los merge_*.py (su URL es la más vieja y
la más probablemente indexada). Se queda con todas las ofertas y hereda
foto/specs/marca/subcategoría si le faltaban. El historial de precios de
la absorbida lo poda record_price_history.py; para las fichas de Amazon
son uno o dos días, y la serie de amazon_mx arranca en la sobreviviente.

USO
---
    python3 scripts/merge_amazon_cross_store.py --dry-run
    python3 scripts/merge_amazon_cross_store.py --dry-run --muestra 60
    python3 scripts/merge_amazon_cross_store.py
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
import merge_by_url as mu  # noqa: E402
from data_io import id_num, load_catalog, save_catalog, texto_plano  # noqa: E402
from match_amazon_capture import color_of  # noqa: E402
from merge_by_gtin import cantidad  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AMAZON = "amazon_mx"
MIN_SIMILITUD = ag.MIN_SIMILITUD          # 0.34, calibrado a mano
MIN_SIMILITUD_SIN_MARCA = 0.5
MAX_RATIO = 2.5

# Un número con unidad es una especificación, no un modelo: "100w" lo
# comparten todos los cargadores de 100 W. Lo mismo "2x4", "1080p", "4k60".
_MEDIDA_RE = re.compile(
    r"^\d+(?:\.\d+)?(?:gb|tb|mb|kb|mah|wh|kwh|w|kw|v|kv|hz|ghz|mhz|khz|k|p|"
    r"l|ml|kg|g|mg|cm|mm|m|km|in|hp|btu|db|rpm|ah|a|ma|lm|mp|fps|x|pcs|pz|"
    r"pzas|ton|oz|lb|lbs|ft|mts|bar|psi|nm|ppm|dpi|ohm|bit|bits|cc|pulg|btus|"
    r"cal|pk|ct)$|^\d+x\d+(?:x\d+)?$|^\d+k\d+$"
)
# Abreviaturas de especificación de 4 letras que parecen código pero no lo
# son: comparten "ddr5"/"usb3"/"wifi6"/"gen4" miles de productos distintos.
_ESPEC_CORTA_RE = re.compile(r"^[a-z]{1,3}\d$|^\d[a-z]{1,3}$")
# Número seguido de a lo sumo dos letras ("8365u", "1355u", "270h", "4060",
# "1500r"): así se escriben los procesadores, las tarjetas gráficas y las
# curvaturas de monitor, que comparten productos DISTINTOS. En la primera
# corrida una Dell Latitude 5400 se fusionó con una Latitude 7400 porque las
# dos traen el mismo Core i5-8365U.
# A lo sumo UNA letra: con dos ("9637am", "1713mjq") ya suelen ser códigos
# de modelo reales, y excluirlos dejó pasar unas bocinas JBL Stage3 68MF
# contra las Stage3 9637AM. Los pocos procesadores con dos letras (13650HX)
# van aparte.
# Tres dígitos solo con sufijo u/h (Core 7 150U, 270H): "627f" (una bocina
# JBL) es un modelo real y excluirlo dejó pasar Stage3 627F contra Stage3
# 9637AM.
_COMPONENTE_RE = re.compile(r"^\d{4,5}(?:[a-z]|hx|hs|kf|ks|hk)?$|^\d{3}[uh]$")
# Medida de llanta ("205/55R16" -> "55r16"): la comparten todas las llantas
# de esa medida, de cualquier modelo. Se vio un HU71 fusionado con un HH11.
_LLANTA_RE = re.compile(r"^\d{2,3}r\d{2}$")
# Sistema operativo, conectividad y protección escritos como un token:
# especificaciones que comparten miles de productos. "w11p" (Windows 11
# Pro) juntó una Dell Pro 16 con una Dell Pro 14.
_ESPECIFICACIONES = {
    "w11p", "w11h", "w10p", "w10h", "win11", "win10", "win11p", "win11h",
    "wifi5", "wifi6", "wifi7", "wifi6e", "ddr3", "ddr4", "ddr5", "lpddr5",
    "lpddr4", "lpddr5x", "usb2", "usb3", "usbc", "hdmi2", "bt5", "ipx4",
    "ipx5", "ipx6", "ipx7", "ipx8", "ip54", "ip65", "ip67", "ip68", "mp3",
    "mp4", "h264", "h265", "4k60", "4k120", "2k165", "fhd1080", "3d",
    "type-c", "gen1", "gen2", "gen3", "gen4", "gen5", "pcie4", "pcie5",
    "nvme", "m2", "sata3", "x64", "x86", "5ghz", "2ghz", "24ghz",
    # Procesadores Intel serie N: empiezan con letra, así que
    # _COMPONENTE_RE no los agarra, y los comparten cientos de laptops
    # baratas de marcas distintas ("Laptop HP 14 N150" x 40 en Elektra).
    "n95", "n97", "n100", "n150", "n200", "n305", "n4000", "n4020",
    "n4120", "n4500", "n5095", "n5100", "n6000", "n250",
    "hdr10", "hdr400", "hdr600", "hdr1000", "hdr10+", "hlg10", "dci-p3",
    # Marcas con dígitos en el nombre: las comparten TODOS sus productos.
    "8bitdo", "insta360", "1hora", "1more", "3doodler", "4moms", "1byone",
    "b1000", "3m",
}
# Clase de velocidad Wi-Fi ("AC1200", "AX3000", "BE6500", "N300"): la
# comparten todos los routers y mesh de esa clase. Un Deco M3 se juntó con
# otro Deco sin modelo por compartir "ac1200".
_WIFI_RE = re.compile(r"^(?:ac|ax|be|n)\d{3,5}$")
# Lo que separa dos anuncios del mismo modelo en unidades de venta
# distintas: un regalo incluido, un combo, o que sea reacondicionado. Se
# suma a MARCADORES de merge_by_url.py: si uno lo dice y el otro no, no se
# fusionan. Un Krups con "3 cajas de cápsulas de regalo" se había juntado
# con el Krups pelado, y un Amazon Renewed con uno nuevo tendría el mismo
# problema a peor precio.
_MARCADORES_EXTRA = {
    "regalo", "gratis", "combo", "bundle", "reacondicionado",
    "reacondicionada", "renewed", "refurbished", "usado", "usada",
    "seminuevo", "seminueva", "outlet", "exhibicion", "demo", "paquete", "kit",
}
# Pulgadas escritas con comillas ("16\"", "15.6''") -- UNIDADES de
# merge_by_url.py solo reconoce la palabra: una laptop de 16" pasaba por
# la misma que una de 14".
_PULGADAS_COMILLAS_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:\"|''|”|“|″)")
# Unidades que UNIDADES de merge_by_url.py no mira y que en línea blanca,
# muebles y herramientas son lo que separa dos modelos: una campana de 60 cm
# se había juntado con una de 70x44x12.4 cm.
_UNIDADES_EXTRA = (
    (re.compile(r"(\d+(?:\.\d+)?)\s*cm\b"), "cm"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*mm\b"), "mm"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(?:kg|kilos?|kgs)\b"), "kg"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(?:l|lt|lts|litros?)\b"), "l"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(?:pies|p3|ft3)\b"), "pies"),
    (re.compile(r"(\d+)\s*quemadores\b"), "quemadores"),
    (re.compile(r"(\d+)\s*(?:puertas?)\b"), "puertas"),
)


def medidas_extra(nombre):
    limpio = mu._normalizar(nombre)
    return {u: {float(x) for x in rx.findall(limpio)} for rx, u in _UNIDADES_EXTRA if rx.search(limpio)}


# Lo que viene después de "compatible" nombra los aparatos CON LOS QUE el
# producto funciona, no lo que el producto es: un cargador de terceros
# "Compatible con DeWalt DCB107 DCB112" se había fusionado con la batería
# DeWalt DCB107. Mismo criterio que titulo_propio() en match_amazon_capture.py.
_COMPATIBLE_RE = re.compile(r"\bcompatible", re.IGNORECASE)
# "NB-CP2L Batería y cargador PARA Canon SELPHY CP1500": lo que sigue a
# "para" es el aparato al que sirve. Pero "Campana PARA cocina ... CEV90T"
# trae el código después, así que solo se corta en "para" cuando lo de
# antes ya tiene un código propio.
_PARA_RE = re.compile(r"\bpara\b", re.IGNORECASE)


def titulo_propio(nombre):
    propio = _COMPATIBLE_RE.split(nombre or "", 1)[0]
    partes = _PARA_RE.split(propio, 1)
    if len(partes) == 2 and ag._codigos(partes[0]):
        return partes[0]
    return propio


def codigos(nombre):
    """Códigos de modelo del nombre (ver punto 2 del docstring)."""
    nombre = titulo_propio(nombre)
    out = set()
    for w in ag._codigos(nombre):
        if _MEDIDA_RE.match(w):
            continue
        if len(w) == 4 and _ESPEC_CORTA_RE.match(w):
            continue
        if _COMPONENTE_RE.match(w) or _LLANTA_RE.match(w) or _WIFI_RE.match(w) or w in _ESPECIFICACIONES:
            continue
        out.add(w)
    return out


def codigos_pegados(nombre):
    """Los mismos códigos pero con el guion pegado: "wf-1000xm3" entero.

    ag._limpiar() parte por el guion, así que los Sony WF-1000XM3 (in-ear) y
    WH-1000XM3 (diadema) compartían "1000xm3" y se fusionaban. Con el guion
    pegado el prefijo de línea forma parte del código."""
    n = ag._limpiar(re.sub(r"(?<=[A-Za-z0-9])-(?=[A-Za-z0-9])", "", titulo_propio(nombre)))
    return {w for w in n.split()
            if len(w) >= 5 and any(c.isdigit() for c in w) and any(c.isalpha() for c in w)
            and not _MEDIDA_RE.match(w) and not _COMPONENTE_RE.match(w)
            and not _LLANTA_RE.match(w) and not _WIFI_RE.match(w) and w not in _ESPECIFICACIONES}


def codigos_pegados_compatibles(a, b):
    """False si los dos nombres tienen códigos con guion pegado y ninguno
    de un lado coincide con (o está contenido en) alguno del otro."""
    ka, kb = codigos_pegados(a), codigos_pegados(b)
    if not ka or not kb:
        return True
    for x in ka:
        for y in kb:
            if x == y or (len(x) >= 5 and x in y) or (len(y) >= 5 and y in x):
                return True
    return False


# "Lavadora Hisense WSA1102PCN + Foset PAGA4X Parrilla": un "+" seguido de
# una palabra es otro producto incluido en el precio. "8 + 256GB" (un "+"
# entre números) no cuenta: es la forma de escribir RAM y almacenamiento.
_MAS_PRODUCTO_RE = re.compile(r"\+\s*[A-Za-zÁÉÍÓÚáéíóúÑñ]")


def marcadores_extra(nombre):
    out = {w for w in ag._limpiar(nombre).split() if w in _MARCADORES_EXTRA}
    if _MAS_PRODUCTO_RE.search(nombre or ""):
        out.add("paquete")
    return out


def pulgadas_comillas(nombre):
    n = (nombre or "").lower()
    n = re.sub(r"(?<=\d),(?=\d)", ".", n)
    return {float(x) for x in _PULGADAS_COMILLAS_RE.findall(n)}


def tiendas_de(p):
    return {o.get("storeId") for o in p.get("offers") or [] if o.get("storeId")}


def es_de_amazon(p):
    return tiendas_de(p) == {AMAZON}


# Submarcas que las tiendas escriben como marca propia.
ALIAS_MARCA = {"soundcore": "anker", "iem": "mabe", "redmi": "xiaomi", "poco": "xiaomi",
               "logitech g": "logitech", "black and decker": "black+decker",
               "black & decker": "black+decker", "kärcher": "karcher"}


def marca_de(p):
    m = texto_plano(p.get("brand") or "").strip()
    return ALIAS_MARCA.get(m, m)


def marca_coincide(a, b):
    """(True/False, hace_falta_mas_parecido)."""
    ma, mb = marca_de(a), marca_de(b)
    if ma and mb:
        return ma == mb, False
    if ma or mb:
        marca = ma or mb
        otro = texto_plano(titulo_propio((b if ma else a).get("name") or ""))
        return re.search(r"(?<![a-z0-9])" + re.escape(marca) + r"(?![a-z0-9])", otro) is not None, False
    return True, True


def similitud(a, b):
    """Palabras compartidas sobre el nombre más corto, SIN el atajo de
    ag.similitud() que devuelve 1.0 apenas comparten un código: acá el
    código ya es requisito, así que se quiere medir el resto del nombre."""
    ta, tb = ag._tokens(a), ag._tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))


def precio_min(p, tienda=None):
    ps = [o.get("price") for o in p.get("offers") or []
          if o.get("price") and (tienda is None or o.get("storeId") == tienda)]
    return min(ps) if ps else None


def motivo_no(a, b):
    """None si se pueden fusionar; si no, el motivo (para las estadísticas)."""
    na, nb = a.get("name") or "", b.get("name") or ""
    ok, exigir_mas = marca_coincide(a, b)
    if not ok:
        return "marca distinta"
    if not mu._misma_version(na, nb):
        return "versión/medida distinta"
    if marcadores_extra(na) != marcadores_extra(nb):
        return "regalo/combo/reacondicionado en uno solo"
    pa_, pb_ = pulgadas_comillas(na), pulgadas_comillas(nb)
    if pa_ and pb_ and pa_ != pb_:
        return "versión/medida distinta"
    ma, mb = medidas_extra(na), medidas_extra(nb)
    for u, v in ma.items():
        if u in mb and v != mb[u]:
            return "versión/medida distinta"
    if not codigos_pegados_compatibles(na, nb):
        return "códigos de modelo distintos"
    ka, kb = codigos(na), codigos(nb)
    if (ka - kb) and (kb - ka):
        # Comparten un código pero CADA una trae además otro que la otra no
        # tiene: "HU71" contra "HH11" con la misma medida de llanta. Si solo
        # una trae códigos de más (un SKU interno de la tienda, un sufijo
        # "-Alb"), no cuenta como contradicción.
        return "códigos de modelo distintos"
    if cantidad(na) != cantidad(nb):
        return "cantidad de piezas distinta"
    ca, cb = color_of(na), color_of(nb)
    if ca and cb and ca != cb:
        return "color distinto"
    s = similitud(na, nb)
    if s < (MIN_SIMILITUD_SIN_MARCA if exigir_mas else MIN_SIMILITUD):
        return "nombres que no se parecen"
    pa, pb = precio_min(a), precio_min(b)
    if pa and pb and max(pa, pb) / min(pa, pb) >= MAX_RATIO:
        return f"precio a {MAX_RATIO:.0f}x o más"
    return None


RECHAZOS = []   # (ficha origen, candidata, motivo) -- para --ver-motivo


def es_origen(p, solo_amazon):
    """Una ficha de UNA sola tienda: la que puede tener gemela en otra."""
    if not p.get("offers") or len(tiendas_de(p)) != 1:
        return False
    return es_de_amazon(p) if solo_amazon else True


def resolver(products, solo_amazon=True):
    """Devuelve (grupos, motivos): grupos = [[fichas del mismo producto]],
    motivos = Counter de por qué lo demás no se fusionó.

    Cada ficha de una sola tienda busca, entre las fichas de OTRAS tiendas,
    las que comparten un código de modelo y pasan todos los chequeos. Los
    pares se juntan en grupos (si A cruza con B y B con C, los tres van
    juntos) y un grupo se fusiona solo si es coherente: tiendas distintas
    dos a dos y cada par pasa los chequeos. Dos fichas de Amazon que apuntan
    a la misma candidata quedan en un grupo con la tienda repetida, y por
    eso no se tocan: son casi siempre dos variantes que los chequeos no
    separaron.
    """
    por_codigo = collections.defaultdict(list)
    for p in products:
        if not p.get("offers"):
            continue
        for c in codigos(p.get("name") or ""):
            por_codigo[c].append(p)

    motivos = collections.Counter()
    padre = {}

    def raiz(x):
        while padre.get(x, x) != x:
            padre[x] = padre.get(padre[x], padre[x])
            x = padre[x]
        return x

    def unir(a, b):
        ra, rb = raiz(a), raiz(b)
        if ra != rb:
            padre[rb] = ra

    por_id = {}
    for a in products:
        if not es_origen(a, solo_amazon):
            continue
        cs = codigos(a.get("name") or "")
        if not cs:
            motivos["sin código de modelo"] += 1
            continue
        ta = tiendas_de(a)
        vistos, candidatos = set(), []
        for c in cs:
            for b in por_codigo.get(c, ()):
                if b["id"] == a["id"] or b["id"] in vistos or (tiendas_de(b) & ta):
                    continue
                vistos.add(b["id"])
                candidatos.append(b)
        if not candidatos:
            motivos["ningún producto de otra tienda con ese código"] += 1
            continue
        pasan, razones = [], collections.Counter()
        for b in candidatos:
            m = motivo_no(a, b)
            if m is None:
                pasan.append(b)
            else:
                razones[m] += 1
                RECHAZOS.append((a, b, m))
        if not pasan:
            motivos[razones.most_common(1)[0][0]] += 1
            continue
        por_id[a["id"]] = a
        for b in pasan:
            por_id[b["id"]] = b
            unir(a["id"], b["id"])

    grupos_por_raiz = collections.defaultdict(list)
    for pid in por_id:
        grupos_por_raiz[raiz(pid)].append(por_id[pid])
    grupos = []
    for fichas in grupos_por_raiz.values():
        if grupo_coherente(fichas):
            grupos.append(sorted(fichas, key=id_num))
        else:
            motivos["grupo ambiguo (tienda repetida o par que no pasa)"] += len(fichas)
            for p in fichas:
                RECHAZOS.append((p, fichas[0] if fichas[0] is not p else fichas[-1], "grupo ambiguo"))
    return grupos, motivos


def grupo_coherente(fichas):
    """True si las fichas son de tiendas distintas dos a dos y cada par
    pasa los mismos chequeos que se le exigen a la ficha de origen."""
    vistas = set()
    for p in fichas:
        t = tiendas_de(p)
        if t & vistas:
            return False
        vistas |= t
    for i, p in enumerate(fichas):
        for q in fichas[i + 1:]:
            if motivo_no(p, q) is not None:
                return False
    return True


def fusionar(fichas):
    """Deja todo en la ficha de id más bajo. Devuelve (jefe, absorbidas)."""
    jefe, *resto = sorted(fichas, key=id_num)
    if es_de_amazon(jefe):
        # La categoría de una ficha de Amazon la decidió el clasificador
        # por el título; la de la otra tienda viene de la taxonomía de la
        # tienda, que es más confiable. Si difieren, manda la de la tienda.
        for otra in resto:
            if not es_de_amazon(otra) and otra.get("category") != jefe.get("category"):
                jefe["category"] = otra["category"]
                jefe["subcategory"] = otra.get("subcategory")
                break
    urls = {o.get("url") for o in jefe.get("offers") or [] if o.get("url")}
    for otra in resto:
        for o in otra.get("offers") or []:
            if o.get("url") in urls:
                continue
            jefe.setdefault("offers", []).append(o)
            urls.add(o.get("url"))
        for campo in ("subcategory", "gtin", "photo", "image", "brand", "specs", "reviews"):
            if not jefe.get(campo) and otra.get(campo):
                jefe[campo] = otra[campo]
    return jefe, resto


def _linea(p):
    return f"{'/'.join(sorted(tiendas_de(p)))[:3].upper()} {p['id']}  ${precio_min(p) or 0:>10,.0f}  [{p.get('category')}] {p['name'][:85]}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--todas-las-tiendas", action="store_true",
                    help="cualquier ficha de una sola tienda como origen, no solo Amazon")
    ap.add_argument("--muestra", type=int, default=25, help="grupos al azar que se listan")
    ap.add_argument("--informe", help="escribe todos los grupos en este JSON")
    ap.add_argument("--keep-pages", action="store_true")
    ap.add_argument("--ver-motivo", help="lista pares rechazados por este motivo")
    args = ap.parse_args()

    data = load_catalog()
    products = data["products"]
    solo_amazon = not args.todas_las_tiendas
    n_origen = sum(1 for p in products if es_origen(p, solo_amazon))
    grupos, motivos = resolver(products, solo_amazon)
    print(f"Fichas de origen ({'solo Amazon' if solo_amazon else 'una sola tienda'}): {n_origen:,}   grupos fusionables: {len(grupos):,}")
    print("No fusionadas, por motivo:")
    for m, n in motivos.most_common():
        print(f"  {n:7,}  {m}")
    combos = collections.Counter(tuple(sorted(set().union(*(tiendas_de(p) for p in g)))) for g in grupos)
    print("Combinaciones de tiendas:", ", ".join(f"{'+'.join(c)} {n:,}" for c, n in combos.most_common(10)))
    print(f"Grupos con categorías distintas: {sum(1 for g in grupos if len({p.get('category') for p in g}) > 1):,}")

    random.seed(5)
    for g in random.sample(grupos, min(args.muestra, len(grupos))):
        print()
        for p in g:
            print("    " + _linea(p))

    if args.ver_motivo:
        lista = [r for r in RECHAZOS if r[2] == args.ver_motivo]
        print(f"\nRechazados por '{args.ver_motivo}': {len(lista):,}")
        for a, b, _ in random.sample(lista, min(args.muestra, len(lista))):
            print(f"\n  marca={a.get('brand')!r} / {b.get('brand')!r}")
            print("    " + _linea(a))
            print("    " + _linea(b))

    if args.informe:
        with open(args.informe, "w", encoding="utf-8") as f:
            json.dump([[{"id": p["id"], "tiendas": sorted(tiendas_de(p)), "categoria": p.get("category"),
                         "nombre": p["name"], "precio": precio_min(p)} for p in g] for g in grupos],
                      f, ensure_ascii=False, indent=1)
        print(f"\nInforme: {args.informe}")

    if args.dry_run:
        print("\n(--dry-run: no se escribió nada)")
        return

    absorbidas = set()
    for g in grupos:
        _, resto = fusionar(g)
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
