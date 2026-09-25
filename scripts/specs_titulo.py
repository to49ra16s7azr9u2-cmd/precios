#!/usr/bin/env python3
"""Especificaciones sacadas del NOMBRE para las categorías donde casi nadie
trae specs (pedido del usuario, 26-sep-2026: «スペック情報が薄い»).

Medido antes de esto: Autopartes 0.5% con facets (365 mil fichas), Calzado
0%, Ropa 0.6%, Decoración 0.1%, Limpieza 0.2%, Mascotas 6%. Los filtros de
la lista y la tabla de la ficha salen de `facets`; sin ellos, en esas
categorías no había por qué afinar.

Reglas conservadoras, igual que specs_extract.py: si el nombre dice dos
cosas distintas (dos colores, dos géneros, dos marcas de auto) no se elige
ninguna. compute_facets.py las aplica DESPUÉS de las propias de cada
categoría y nunca pisa un campo que ya tenga valor.
"""
import re
import unicodedata


def _norm(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " " + re.sub(r"\s+", " ", s.lower()) + " "


def _unico(vals):
    vals = [v for v in vals if v is not None]
    return vals[0] if len(set(vals)) == 1 else None


# ------------------------------------------------------------- vehículos
# Marca del vehículo al que le queda la pieza. "ram" y "seat" solo cuentan
# con un modelo o un año al lado (son también palabras comunes); "mini"
# solo como "mini cooper".
_MARCAS_AUTO = {
    "nissan": "Nissan", "chevrolet": "Chevrolet", "chevy": "Chevrolet", "volkswagen": "Volkswagen",
    "vw": "Volkswagen", "ford": "Ford", "toyota": "Toyota", "honda": "Honda", "mazda": "Mazda",
    "kia": "Kia", "hyundai": "Hyundai", "dodge": "Dodge", "chrysler": "Chrysler", "jeep": "Jeep",
    "renault": "Renault", "mitsubishi": "Mitsubishi", "suzuki": "Suzuki", "bmw": "BMW",
    "mercedes": "Mercedes-Benz", "mercedes-benz": "Mercedes-Benz", "audi": "Audi", "peugeot": "Peugeot",
    "fiat": "Fiat", "buick": "Buick", "cadillac": "Cadillac", "gmc": "GMC", "subaru": "Subaru",
    "volvo": "Volvo", "acura": "Acura", "infiniti": "Infiniti", "lincoln": "Lincoln", "mg": "MG",
    "chirey": "Chirey", "jac": "JAC", "baic": "BAIC", "byd": "BYD", "freightliner": "Freightliner",
    "international": None, "italika": "Italika", "yamaha": "Yamaha", "bajaj": "Bajaj", "vento": "Vento",
    "kawasaki": "Kawasaki", "ktm": "KTM", "harley": "Harley-Davidson", "harley-davidson": "Harley-Davidson",
    "pontiac": "Pontiac", "land rover": "Land Rover", "porsche": "Porsche", "lexus": "Lexus",
    "cupra": "Cupra", "opel": "Opel", "isuzu": "Isuzu", "hino": "Hino", "kenworth": "Kenworth",
}
_MARCA_RE = re.compile(r"(?<![a-z0-9])(" + "|".join(sorted((re.escape(k) for k in _MARCAS_AUTO if _MARCAS_AUTO[k]),
                                                        key=len, reverse=True)) + r")(?![a-z0-9])")
_AMBIGUAS = re.compile(r"(?<![a-z0-9])(ram|seat)\s+(\d{3,4}|ibiza|leon|toledo|cordoba|ateca|arona|altea|promaster|700)\b")
_ANIO = r"(19[5-9]\d|20[0-2]\d)"
_RANGO_RE = re.compile(_ANIO + r"\s*(?:-|a|al|hasta|/|–)\s*" + r"(19[5-9]\d|20[0-2]\d|\d{2})(?!\d)")
_SUELTO_RE = re.compile(r"(?<![\d.,/])" + _ANIO + r"(?![\d.,])")
_NO_MODELO = {"para", "de", "del", "con", "y", "a", "al", "compatible", "original", "genuino", "oem",
              "tipo", "modelo", "motor", "auto", "carro", "camioneta", "the", "en", "sin", "delantero",
              "trasero", "izquierdo", "derecho", "par", "juego", "kit", "set", "pieza", "piezas", "l4",
              "v6", "v8", "4x4", "4x2", "std", "aut", "automatico", "estandar", "gasolina", "diesel",
              # Marcas de la PIEZA y palabras de catálogo que caen donde iría el modelo.
              "walker", "green", "keep", "syd", "moog", "dai", "trw", "gates", "bosch", "polyway", "generica",
              "nueva", "generacion", "soporte", "caja", "porta", "monroe", "gonher", "kyb", "ngk", "denso",
              "cardic", "garanti", "clemex", "beco", "fiamm", "prestone", "partech", "husky", "star", "linea"}


def _fmt_modelo(palabras):
    return " ".join(p.upper() if (len(p) <= 3 or re.search(r"\d", p)) else p.capitalize() for p in palabras)


def _es_codigo(w):
    """«c10», «3500», «hd», «s350», «f-150»: parte del nombre de un modelo."""
    return bool(re.fullmatch(r"[a-z]{0,3}-?\d{2,4}[a-z]{0,2}|[a-z]{1,2}", w)) and w not in _NO_MODELO


def vehiculo(nombre):
    """(marca, modelo, [años]) del vehículo compatible, o (None, None, []).

    El modelo sale de dos formas de escribir que conviven en el catálogo:
    «... para Chevrolet Aveo 2008 al 2017» (la marca antes: el modelo va
    entre la marca y el año) y «Soporte motor juke 2011 a 2018 nissan»
    (la marca después: el modelo es lo que está justo antes del año).
    """
    n = _norm(nombre)
    ms = list(_MARCA_RE.finditer(n))
    marcas = {_MARCAS_AUTO[m.group(1)] for m in ms}
    amb = _AMBIGUAS.search(n)
    if amb:
        marcas.add("RAM" if amb.group(1) == "ram" else "SEAT")
    if "mini cooper" in n:
        marcas.add("MINI")
    marca = next(iter(marcas)) if len(marcas) == 1 else None
    m_anio = _RANGO_RE.search(n) or _SUELTO_RE.search(n)
    modelo = None
    if marca:
        m = ms[0] if ms else amb
        # «ITALIKA Soporte Caja...»: la marca abre el nombre y no hay año --
        # es la marca de la pieza, no el vehículo al que le queda.
        abre = m is not None and not n[:m.start()].strip()
        if m is not None and m_anio is None and abre:
            pass
        elif m is not None and (m_anio is None or m.start() < m_anio.start()):
            fin = m_anio.start() if m_anio else len(n)
            palabras = []
            for w in n[m.end():fin].split()[:2]:
                w = w.strip(",.;:()")
                if not w or w in _NO_MODELO or "/" in w or re.fullmatch(r"[lv]\d|[\d.,]+l?", w):
                    break
                palabras.append(w)
            if palabras:
                modelo = marca + " " + _fmt_modelo(palabras)
        elif m_anio is not None:
            antes = [w.strip(",.;:()") for w in n[:m_anio.start()].split()]
            palabras = []
            for w in reversed(antes[1:]):          # la primera palabra es la pieza
                if _es_codigo(w):
                    palabras.insert(0, w)
                    continue
                if not palabras and w not in _NO_MODELO and len(w) > 2 and not re.search(r"\d", w):
                    palabras.insert(0, w)
                break
            if palabras:
                modelo = marca + " " + _fmt_modelo(palabras)
    anios = set()
    for a, b in _RANGO_RE.findall(n):
        a = int(a)
        b = int(b) if len(b) == 4 else int(str(a)[:2] + b)
        if a <= b <= 2027 and b - a <= 45:
            anios.update(range(a, b + 1))
    if not anios:
        sueltos = sorted({int(x) for x in _SUELTO_RE.findall(n)})
        if sueltos and (len(sueltos) <= 3 or sueltos[-1] - sueltos[0] + 1 == len(sueltos)):
            anios = set(sueltos)
    anios = sorted(a for a in anios if 1950 <= a <= 2027)
    # Un año solo sin marca de auto al lado es más seguido un modelo o un
    # código de pieza que un año del vehículo.
    if not marca:
        anios = []
    return marca, modelo, anios


def posicion(nombre):
    n = _norm(nombre)
    d = bool(re.search(r"\bdelanter[oa]s?\b|\bfrontal(es)?\b", n))
    t = bool(re.search(r"\btraser[oa]s?\b|\bposterior(es)?\b", n))
    if d and t:
        return "Delantero y trasero"
    return "Delantero" if d else "Trasero" if t else None


def lado(nombre):
    n = _norm(nombre)
    i = bool(re.search(r"\bizquierd[oa]s?\b|\bpiloto\b|\blado conductor\b", n))
    r = bool(re.search(r"\bderech[oa]s?\b|\bcopiloto\b|\bpasajero\b", n))
    if i and r:
        return "Ambos lados"
    return "Izquierdo" if i else "Derecho" if r else None


_LLANTA_RE = re.compile(r"\b(1[3-9]\d|2\d\d|3[0-4]\d)\s*/\s*([2-8]\d)\s*z?r?\s*-?\s*(1[2-9]|2[0-6])\b")


def medida_llanta(nombre):
    m = _LLANTA_RE.search(_norm(nombre))
    return f"{m.group(1)}/{m.group(2)} R{m.group(3)}" if m else None


# ------------------------------------------------------------- moda y hogar
_COLORES = (
    ("Multicolor", r"multicolor|arcoiris|arco iris|colores surtidos"),
    ("Negro", r"negr[oa]s?|black"), ("Blanco", r"blanc[oa]s?|white"), ("Gris", r"gris(es)?|grey|gray|grafito"),
    ("Plata", r"platead[oa]s?|plata|silver"), ("Dorado", r"dorad[oa]s?|oro rosa|gold"),
    ("Azul", r"azul(es)?|marino|navy|turquesa"), ("Rojo", r"roj[oa]s?|vino|guinda|red"),
    ("Rosa", r"rosas?|rosad[oa]|fucsia|pink"), ("Verde", r"verdes?|olivo|menta|green"),
    ("Amarillo", r"amarill[oa]s?|mostaza|yellow"), ("Naranja", r"naranja|anaranjad[oa]|orange"),
    ("Morado", r"morad[oa]s?|lila|violeta|purple"), ("Café", r"(?<!para )(?<!de )(?<!taza )(?<!tazas )cafe(?! (?:en grano|molido|soluble|americano|expreso|espresso|organico))|marron|chocolate|nogal|brown|camel"),
    ("Beige", r"beige|arena|crema|nude|hueso|marfil"), ("Transparente", r"transparente|cristal"),
)
_COLOR_RX = [(lbl, re.compile(r"(?<![a-z])(?:" + rx + r")(?![a-z])")) for lbl, rx in _COLORES]


def color(nombre):
    """El color si el nombre nombra uno solo (o «multicolor»)."""
    n = _norm(nombre)
    # "Rosa de los vientos", "vino tinto", "oro 14k" no son colores de la
    # pieza; tampoco lo que va después de "compatible con".
    n = re.split(r"\bcompatible (?:con|para)\b", n)[0]
    hits = [lbl for lbl, rx in _COLOR_RX if rx.search(n)]
    if "Multicolor" in hits:
        return "Multicolor"
    return hits[0] if len(hits) == 1 else None


_GENEROS = (
    ("Niña", r"\bnina\b|\bninas\b|\bgirls?\b"), ("Niño", r"\bnino\b|\bninos\b|\bboys?\b|\binfantil\b|\bjunior\b|\bkids?\b"),
    ("Bebé", r"\bbebes?\b|\bbaby\b"),
    ("Mujer", r"\bmujer(es)?\b|\bdama(s)?\b|\bfemenin[oa]\b|\bwomen'?s?\b"),
    ("Hombre", r"\bhombres?\b|\bcaballeros?\b|\bmasculin[oa]\b|\bmen'?s?\b|\bel\b(?= )(?=.*\btenis\b)"),
    ("Unisex", r"\bunisex\b"),
)
_GEN_RX = [(lbl, re.compile(rx)) for lbl, rx in _GENEROS]


def genero(nombre):
    n = _norm(nombre)
    hits = {lbl for lbl, rx in _GEN_RX if rx.search(n)}
    if "Unisex" in hits or {"Hombre", "Mujer"} <= hits:
        return "Unisex"
    if {"Niño", "Niña"} <= hits:
        return "Niño"
    return next(iter(hits)) if len(hits) == 1 else None


_TALLA_MX_RE = re.compile(r"\b(?:talla|numero|no\.?|#)\s*(1[2-9]|2\d|3[0-2])(?:[.,]5)?\b|\b(2[2-9]|3[0-2])(?:[.,]5)?\s*(?:mx|cm)\b")


def talla_calzado(nombre):
    m = _TALLA_MX_RE.search(_norm(nombre))
    if not m:
        return None
    return float(re.sub(",", ".", m.group(0).split()[-1].rstrip("mxc"))) if False else int(m.group(1) or m.group(2))


_MASCOTAS = (("Perro", r"\bperros?\b|\bcanin[oa]s?\b|\bcachorros?\b|\bdog\b"),
             ("Gato", r"\bgat[oa]s?\b|\bgatitos?\b|\bfelin[oa]s?\b|\bcat\b|\barenero\b"),
             ("Ave", r"\baves?\b|\bpajaros?\b|\bloros?\b|\bperiquitos?\b|\bcanarios?\b"),
             ("Pez", r"\bpec(es)?\b|\bpez\b|\bacuario\b|\bpecera\b"),
             ("Roedor", r"\bhamster\b|\bconejos?\b|\bcuyos?\b|\bhuron(es)?\b|\bchinchilla\b|\broedor(es)?\b"),
             ("Reptil", r"\breptil(es)?\b|\btortugas?\b|\biguanas?\b|\bterrario\b"))
_MASC_RX = [(lbl, re.compile(rx)) for lbl, rx in _MASCOTAS]


def mascota(nombre):
    n = _norm(nombre)
    hits = {lbl for lbl, rx in _MASC_RX if rx.search(n)}
    if hits == {"Perro", "Gato"}:
        return "Perro y gato"
    return next(iter(hits)) if len(hits) == 1 else None


# ------------------------------------------------------------- iluminación
def temperatura_luz(nombre):
    n = _norm(nombre)
    hits = set()
    if re.search(r"\brgb\b|multicolor|colores", n):
        hits.add("RGB / colores")
    if re.search(r"luz calida|blanco calido|\bcalida\b|\b2700 ?k\b|\b3000 ?k\b|\bwarm\b", n):
        hits.add("Cálida")
    if re.search(r"luz fria|blanco frio|\bfria\b|luz de dia|\b6500 ?k\b|\b6000 ?k\b|\bdaylight\b", n):
        hits.add("Fría")
    if re.search(r"luz neutra|blanco neutro|\bneutra\b|\b4000 ?k\b|\b4100 ?k\b", n):
        hits.add("Neutra")
    return next(iter(hits)) if len(hits) == 1 else None


_SOCKET_RE = re.compile(r"\b(e27|e26|e14|e12|e40|gu10|gu5\.3|mr16|g9|g4|t8|t5|b22)\b")


def base_foco(nombre):
    vals = {m.group(1).upper() for m in _SOCKET_RE.finditer(_norm(nombre))}
    return next(iter(vals)) if len(vals) == 1 else None


# ------------------------------------------------------------- audio
def conexion_audio(nombre):
    n = _norm(nombre)
    inal = bool(re.search(r"inalambric|bluetooth|\btws\b|wireless|\bbt\b", n))
    cable = bool(re.search(r"\bcon cable\b|alambric|\bjack 3\.?5|\b3\.5 ?mm\b|\busb-?c con cable\b|\bwired\b", n))
    if inal and not cable:
        return "Inalámbrico"
    if cable and not inal:
        return "Con cable"
    return None


def cancelacion_ruido(nombre):
    n = _norm(nombre)
    return "Sí" if re.search(r"cancelacion (activa )?de ruido|\banc\b|noise cancell", n) else None


# ------------------------------------------------------------- consumibles
_UNIDADES_RE = re.compile(r"(?<![\d.,])(\d{1,4})\s*(capsulas|caps|tabletas|tabs|softgels|gomitas|sobres|piezas|pzs|pz|unidades)\b")


def unidades(nombre, lo=2, hi=2000):
    vals = {int(m.group(1)) for m in _UNIDADES_RE.finditer(_norm(nombre))}
    vals = {v for v in vals if lo <= v <= hi}
    return next(iter(vals)) if len(vals) == 1 else None


def forma_suplemento(nombre):
    n = _norm(nombre)
    for lbl, rx in (("Cápsulas", r"capsulas|\bcaps\b|softgels?"), ("Tabletas", r"tabletas|\btabs\b|comprimidos"),
                    ("Gomitas", r"gomitas|gummies"), ("Polvo", r"\bpolvo\b|\bscoops?\b|\blb\b|\blibras?\b"),
                    ("Líquido", r"liquido|gotas|jarabe|\bml\b")):
        if re.search(rx, n):
            return lbl
    return None


def inalambrico_herramienta(nombre):
    n = _norm(nombre)
    if re.search(r"inalambric|\bcordless\b|\ba bateria\b|\bcon bateria\b|\bsin cable\b|\b(12|18|20|40|60) ?v\b(?!.*\bcable\b)", n):
        return "Inalámbrica"
    if re.search(r"\balambric|\bcon cable\b|\belectrica\b.*\b\d{3,4} ?w\b|\b\d{3,4} ?w\b", n):
        return "Con cable"
    return None
