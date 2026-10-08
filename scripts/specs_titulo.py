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
    # 08-oct-2026: marcas viejas que traen las refacciones importadas (Oldsmobile,
    # Plymouth, Mercury...) y que dejaban la ficha sin ninguna fila.
    "oldsmobile": "Oldsmobile", "plymouth": "Plymouth", "mercury": "Mercury", "saturn": "Saturn",
    "daewoo": "Daewoo", "studebaker": "Studebaker", "hummer": "Hummer", "datsun": "Datsun",
    "saab": "Saab", "daihatsu": "Daihatsu", "ssangyong": "SsangYong", "tesla": "Tesla", "scion": "Scion",
    "jaguar": "Jaguar", "citroen": "Citroën", "skoda": "Škoda", "lada": "Lada", "mahindra": "Mahindra",
    "maserati": "Maserati", "alfa romeo": "Alfa Romeo", "range rover": "Land Rover", "geo": "Geo",
    "mack": "Mack", "foton": "Foton", "changan": "Changan", "geely": "Geely", "dina": "Dina",
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
              "cardic", "garanti", "clemex", "beco", "fiamm", "prestone", "partech", "husky", "star", "linea",
              # Más marcas de la pieza (08-oct-2026): «Bobina ... oldsmobile intran-flotamex».
              "melling", "fallone", "rexite", "intran-flotamex", "intran", "flotamex", "k-nadian", "nadian", "tyc",
              "depo", "spq", "king", "dorman", "delco", "mopar", "acdelco", "tong", "yang", "trw", "sachs", "kayaba",
              "boge", "gabriel", "bogas", "walker", "rodatech", "rodatec", "cooltech", "geba", "premium", "dc",
              "gasket", "gaskets", "reakosound", "hivoz", "interautomex", "valucraft", "ag", "oem"}


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
    # código de pieza que un año del vehículo. Un RANGO («2012 a 2015») sí es
    # de años aunque la marca no esté en el nombre («Faro niebla sandero 2012 a
    # 2015»): 19 mil refacciones se quedaban sin ninguna fila (08-oct-2026).
    if not marca and not _RANGO_RE.search(n):
        anios = []
    return marca, modelo, anios


def posicion(nombre):
    n = _norm(nombre)
    # «del izq», «tra der»: abreviaturas de los catálogos de refacciones.
    d = bool(re.search(r"\bdelanter[oa]s?\b|\bfrontal(es)?\b|\bdel\.? (izq|der|inf|sup|secc)", n))
    t = bool(re.search(r"\btraser[oa]s?\b|\bposterior(es)?\b|\btras?\.? (izq|der|inf|sup)", n))
    if d and t:
        return "Delantero y trasero"
    return "Delantero" if d else "Trasero" if t else None


def lado(nombre):
    n = _norm(nombre)
    i = bool(re.search(r"\bizquierd[oa]s?\b|\bpiloto\b|\blado conductor\b|\bizq\b", n))
    r = bool(re.search(r"\bderech[oa]s?\b|\bcopiloto\b|\bpasajero\b|\bder\b", n))
    if i and r:
        return "Ambos lados"
    return "Izquierdo" if i else "Derecho" if r else None


_LLANTA_RE = re.compile(r"\b(1[3-9]\d|2\d\d|3[0-4]\d)\s*/\s*([2-8]\d)\s*z?r?\s*-?\s*(1[2-9]|2[0-6])\b")


def medida_llanta(nombre):
    m = _LLANTA_RE.search(_norm(nombre))
    return f"{m.group(1)}/{m.group(2)} R{m.group(3)}" if m else None


# El índice de carga y de velocidad que va después de la medida: «185/65 R15
# 88H», «LT265/70R17 121/118S». La letra es la velocidad máxima que la
# llanta aguanta cargada, que es lo que la separa por desempeño: 41 mil
# llantas sólo tenían el precio en Compara calidad (04-oct-2026) y el 87%
# dice su letra.
_VELOCIDAD_LLANTA_RE = re.compile(r"(?<![\d/.])(\d{2,3})(?:/\d{2,3})?\s?([qrsthvwyz])\b")
VELOCIDADES_LLANTA = {"q": "Hasta 190 km/h", "r": "Hasta 190 km/h", "s": "Hasta 190 km/h", "t": "Hasta 190 km/h",
                      "h": "210 a 240 km/h", "v": "210 a 240 km/h",
                      "w": "270 km/h o más", "y": "270 km/h o más", "z": "270 km/h o más"}


def velocidad_llanta(nombre):
    n = _norm(nombre)
    if not (_LLANTA_RE.search(n) or re.search(r"\bllantas?\b|\bneumaticos?\b", n)):
        return None
    tramos = {VELOCIDADES_LLANTA[m.group(2)] for m in _VELOCIDAD_LLANTA_RE.finditer(n)
              if 50 <= int(m.group(1)) <= 130}
    return next(iter(tramos)) if len(tramos) == 1 else None


_HP_RE = re.compile(r"(?<![\d./])(\d+\s+\d/\d|\d/\d|\d{1,2}(?:\.\d{1,2})?)\s*(?:hp|caballos?(?: de fuerza)?)\b")


def caballos(nombre):
    """Caballos de fuerza de una bomba («Bomba Truper 1/2 HP», «1 1/2 hp»):
    el 77% de las bombas de agua lo dice y sólo se comparaban por precio."""
    vals = set()
    for m in _HP_RE.finditer(_norm(nombre)):
        t = m.group(1).split()
        v = sum(float(a) / float(b) for a, b in (x.split("/") for x in t if "/" in x)) + sum(float(x) for x in t if "/" not in x)
        if 0.1 <= v <= 30:
            vals.add(round(v, 2))
    return next(iter(vals)) if len(vals) == 1 else None


_CONTACTOS_RE = re.compile(r"\b(\d{1,2})\s*(?:contactos|tomas|salidas|enchufes|tomacorrientes)\b")


def contactos(nombre):
    """Contactos de una regleta («Multicontacto 6 contactos»)."""
    vals = {int(m.group(1)) for m in _CONTACTOS_RE.finditer(_norm(nombre)) if 2 <= int(m.group(1)) <= 24}
    return next(iter(vals)) if len(vals) == 1 else None


_TV_MAX_RE = re.compile(r"(?:hasta|para (?:tvs?|televisor(?:es)?|pantallas?)(?: de)?(?: hasta)?|pantallas? de(?: hasta)?|tvs? de(?: hasta)?)"
                        r"\s*(\d{2,3})\s*(?:\"|pulgadas|pulg\b|in\b)?")


def tv_maxima(nombre):
    """La pantalla más grande que aguanta un mueble para TV («Mesa para TV
    de hasta 65 pulgadas»)."""
    vals = {int(m.group(1)) for m in _TV_MAX_RE.finditer(_norm(nombre)) if 24 <= int(m.group(1)) <= 100}
    return max(vals) if vals else None


_QUEMADORES_RE = re.compile(r"\b(\d{1,2})\s*quemadores?\b")


def quemadores(nombre):
    """Quemadores de una parrilla de gas («Asador 4 quemadores»)."""
    vals = {int(m.group(1)) for m in _QUEMADORES_RE.finditer(_norm(nombre)) if 1 <= int(m.group(1)) <= 10}
    return next(iter(vals)) if len(vals) == 1 else None


_PELDANOS_RE = re.compile(r"\b(\d{1,2})\s*(?:peldanos|escalones|pasos)\b")


def peldanos(nombre):
    """Peldaños de una escalera («Escalera de tijera 5 peldaños»)."""
    vals = {int(m.group(1)) for m in _PELDANOS_RE.finditer(_norm(nombre)) if 2 <= int(m.group(1)) <= 30}
    return next(iter(vals)) if len(vals) == 1 else None


# ---------------------------------------------------------------- suplementos
# Nutrientes e ingredientes de un suplemento, para elegir varios en Compara
# calidad (04-oct-2026: los suplementos sólo se comparaban por precio y no
# tienen ficha técnica; el 69% dice lo que trae en el nombre). (nombre que
# se muestra, regex sobre el nombre normalizado).
NUTRIENTES = [
    ("Multivitamínico", r"\bmulti-? ?vitamin|\bmultivitaminico|\bmulti-?vitaminas?\b|vitaminas y minerales|vitamins and minerals"),
    ("Vitamina A", r"\bretinol\b|\bbeta ?caroteno|\bbetacaroteno"),
    ("Complejo B", r"\bcomplejo b\b|\bb ?complex\b|\bcomplejo de vitaminas b\b|\bvitaminas? (del )?complejo b\b|\bb-?(50|100)\b"),
    ("Vitamina B6", r"\bpiridoxina\b|\bp5p\b"),
    ("Vitamina B12", r"\bb-?12\b|cobalamina\b"),
    ("Biotina", r"\bbiotina\b|\bbiotin\b"),
    ("Ácido fólico", r"\bacido folico\b|\bfolato\b|\bmetilfolato\b|\bfolic\b|\bfolate\b"),
    ("Vitamina C", r"\bacido ascorbico\b|\bascorbato\b"),
    ("Vitamina D", r"\bd3\b|\bcolecalciferol\b"),
    ("Vitamina E", r"\btocoferol"),
    ("Vitamina K", r"\bk2\b|\bmk-?7\b|\bmenaquinona"),
    ("Calcio", r"\bcalcio\b|\bcalcium\b"),
    ("Magnesio", r"\bmagnesio\b|\bmagnesium\b"),
    ("Zinc", r"\bzinc\b"),
    ("Hierro", r"\bhierro\b|\biron\b|\bferroso\b|\bferrico\b"),
    ("Potasio", r"\bpotasio\b|\bpotassium\b"),
    ("Selenio", r"\bselenio\b|\bselenium\b"),
    ("Yodo", r"\byodo\b|\biodine\b"),
    ("Electrolitos", r"\belectrolit"),
    ("Omega 3", r"\bomega ?-?3\b|\bepa\b|\bdha\b|aceite de pescado|\bfish oil\b|\bkrill\b|higado de bacalao"),
    ("Colágeno", r"\bcolageno\b|\bcollagen\b"),
    ("Ácido hialurónico", r"\bhialuronico\b|\bhyaluronic\b"),
    ("Proteína", r"\bproteina\b|\bprotein\b|\bwhey\b|suero de leche|\bcaseina\b"),
    ("Creatina", r"\bcreatina\b|\bcreatine\b"),
    ("Aminoácidos", r"\bbcaa|\baminoacidos?\b|\bamino acids?\b|\bleucina\b|\beaa\b"),
    ("Glutamina", r"\bglutamina\b|\bglutamine\b"),
    ("L-Carnitina", r"\bcarnitina\b|\bcarnitine\b"),
    ("Probióticos", r"\bprobiotic|\blactobacil|\bbifidobacter"),
    ("Fibra y prebióticos", r"\bfibra\b|\bfiber\b|\bpsyllium\b|\binulina\b|\bprebiotic"),
    ("Enzimas digestivas", r"\benzimas?\b|\benzymes?\b|\bbromelina\b|\bpapaina\b"),
    ("Melatonina", r"\bmelatonina\b|\bmelatonin\b"),
    ("Ashwagandha", r"\bashwagandha\b"),
    ("Cúrcuma", r"\bcurcuma\b|\bturmeric\b|\bcurcumina\b"),
    ("Jengibre", r"\bjengibre\b|\bginger\b"),
    ("Ginseng", r"\bginseng\b"),
    ("Maca", r"\bmaca\b"),
    ("Moringa", r"\bmoringa\b"),
    ("Espirulina", r"\bespirulina\b|\bspirulina\b|\bchlorella\b|\bclorela\b"),
    ("Colina", r"\bcolina\b|\bcholine\b"),
    ("Glucosamina", r"\bglucosamina\b|\bglucosamine\b"),
    ("Condroitina", r"\bcondroitina\b|\bchondroitin\b"),
    ("MSM", r"\bmsm\b|\bmetilsulfonilmetano\b"),
    ("Coenzima Q10", r"\bq-?10\b|\bcoq-?10\b|\bcoenzima\b|\bubiquinol\b"),
    ("Luteína", r"\bluteina\b|\blutein\b|\bzeaxantina\b"),
    ("Resveratrol", r"\bresveratrol\b"),
    ("Quercetina", r"\bquercetina\b|\bquercetin\b"),
    ("Cafeína", r"\bcafeina\b|\bcaffeine\b"),
    ("Vinagre de manzana", r"vinagre de manzana|apple cider vinegar"),
    ("Cardo mariano", r"cardo mariano|milk thistle|\bsilimarina\b"),
    ("Arándano", r"\barandanos?\b|\bcranberry\b"),
    ("Equinácea", r"\bequinacea\b|\bechinacea\b"),
    ("Saúco", r"\bsauco\b|\belderberry\b"),
    ("Valeriana", r"\bvaleriana\b|\bvalerian\b"),
    ("Hongos funcionales", r"melena de leon|lion.?s mane|\breishi\b|\bcordyceps\b|\bchaga\b|\bmushroom\b|\bhongos?\b"),
    ("Calostro", r"\bcalostro\b|\bcolostrum\b"),
    ("Ajo", r"\bajo\b|\bgarlic\b"),
    ("Berberina", r"\bberberina\b|\bberberine\b"),
    ("Ácido alfa lipoico", r"alfa lipoico|alpha lipoic"),
    ("Isoflavonas", r"\bisoflavon"),
    ("Té verde", r"\bte verde\b|\bgreen tea\b"),
    ("Inositol", r"\binositol\b"),
    ("D-Manosa", r"\bd-? ?manosa\b|\bd-? ?mannose\b"),
    ("Shilajit", r"\bshilajit\b"),
    ("Clorofila", r"\bclorofila\b|\bchlorophyll\b"),
    ("Orégano", r"\boregano\b"),
]
_NUTRIENTES_RX = [(n, re.compile(r)) for n, r in NUTRIENTES]

# «vitamina c», «vitaminas a, c y d», «vitamina d3 + k2», «vitaminas b6 y b12»
_VIT_LISTA = re.compile(r"\bvit(?:amina|amin)?s?\.?\s+((?:(?:a|b|b\d{1,2}|c|d|d\d|e|k|k\d)\b(?:\s*(?:,|y|\+|&|/|-)\s*|\s+))*"
                        r"(?:a|b|b\d{1,2}|c|d|d\d|e|k|k\d)\b)")
_LETRA = {"a": "Vitamina A", "b": "Complejo B", "b1": "Complejo B", "b2": "Complejo B", "b3": "Complejo B",
          "b5": "Complejo B", "b6": "Vitamina B6", "b7": "Biotina", "b9": "Ácido fólico", "b12": "Vitamina B12",
          "c": "Vitamina C", "d": "Vitamina D", "d2": "Vitamina D", "d3": "Vitamina D", "e": "Vitamina E",
          "k": "Vitamina K", "k1": "Vitamina K", "k2": "Vitamina K"}


# «sin hierro», «libre de cafeína», «iron free»: lo que el nombre dice que NO trae.
_SIN_ANTES = re.compile(r"\b(?:sin|libre de|no contiene|free of)\s+(?:\w+\s+)?$")
_SIN_DESPUES = re.compile(r"^\s*-?\s*free\b")


def _afirmado(n, m):
    return not _SIN_ANTES.search(n[max(0, m.start() - 25):m.start()]) and not _SIN_DESPUES.search(n[m.end():m.end() + 8])


def nutrientes(nombre):
    """Lista ordenada de los nutrientes e ingredientes que el nombre de un
    suplemento dice que trae («Vitamina d3 zinc vitamina c ajo negro» ->
    Ajo, Vitamina C, Vitamina D, Zinc), o None."""
    n = _norm_nutr(nombre)
    out = {nom for nom, rx in _NUTRIENTES_RX if any(_afirmado(n, m) for m in rx.finditer(n))}
    for m in _VIT_LISTA.finditer(n):
        if not _afirmado(n, m):
            continue
        for tok in re.findall(r"[a-z]\d{0,2}", m.group(1)):
            if tok in _LETRA:
                out.add(_LETRA[tok])
    return sorted(out) or None


def _norm_nutr(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9+&/,.\- ]", " ", s)).strip()


# ------------------------------------------------- controles y consumibles
# «Control compatible con Samsung», «Tóner HP 105A»: la marca del aparato
# para el que sirve es lo que se elige (04-oct-2026: Controles para TV,
# Tóner y Cartuchos sólo se comparaban por precio; 63-75% la dice).
_MARCAS_TV = (("Samsung", r"samsung"), ("LG", r"\blg\b"), ("Sony", r"\bsony\b|\bbravia\b"),
              ("Hisense", r"hisense"), ("TCL", r"\btcl\b"), ("Roku", r"\broku\b"), ("Philips", r"philips"),
              ("Panasonic", r"panasonic"), ("Sharp", r"\bsharp\b"), ("Vizio", r"vizio"), ("Sanyo", r"sanyo"),
              ("JVC", r"\bjvc\b"), ("RCA", r"\brca\b"), ("Westinghouse", r"westinghouse"), ("Hyundai", r"hyundai"),
              ("Polaroid", r"polaroid"), ("Insignia", r"insignia"), ("Onn", r"\bonn\b"), ("Toshiba", r"toshiba"),
              ("Haier", r"\bhaier\b"), ("Apple TV", r"apple tv"), ("Fire TV", r"fire ?tv|fire stick"),
              ("Xiaomi", r"xiaomi|\bmi box\b"), ("Motorola", r"motorola"), ("Atvio", r"atvio"), ("Daewoo", r"daewoo"),
              ("Element", r"\belement\b"), ("Aiwa", r"\baiwa\b"), ("Vios", r"\bvios\b"), ("Kalley", r"kalley"))
_MARCAS_TV_RX = [(n, re.compile(r)) for n, r in _MARCAS_TV]


def marca_tv(nombre):
    """Para qué marca de TV es un control: la que dice el nombre, o
    «Universal» si dice universal o nombra tres marcas o más. En «TCL Roku
    TV» la tele es TCL (Roku es el sistema)."""
    n = _norm(nombre)
    marcas = [nom for nom, rx in _MARCAS_TV_RX if rx.search(n)]
    if re.search(r"\buniversal\b", n) or len(marcas) >= 3:
        return "Universal"
    if len(marcas) == 2 and "Roku" in marcas:
        marcas.remove("Roku")
    return marcas[0] if len(marcas) == 1 else None


_MARCAS_IMPRESORA = (("HP", r"\bhp\b|hewlett"), ("Canon", r"\bcanon\b"), ("Epson", r"\bepson\b"),
                     ("Brother", r"\bbrother\b"), ("Samsung", r"samsung|\bsamsng\b"), ("Lexmark", r"lexmark"),
                     ("Xerox", r"xerox"), ("Ricoh", r"\bricoh\b"), ("Kyocera", r"kyocera"), ("Pantum", r"pantum"),
                     ("Konica Minolta", r"konica|minolta|bizhub"), ("Dell", r"\bdell\b"), ("OKI", r"\boki(data)?\b"))
_MARCAS_IMPRESORA_RX = [(n, re.compile(r)) for n, r in _MARCAS_IMPRESORA]
# El genérico nombra la marca del tóner y la de la impresora: «Toner xerox
# compatible hp laserjet» es para HP.
_PARA_MARCA = re.compile(r"\b(para|compatibles?|con|for|en|p/)\s+(uso\s+en\s+|impresoras?\s+)?$")
# Códigos de pieza de una sola marca (medido el 04-oct sobre los que no
# nombran marca: 12 de 12 en cada grupo de la muestra).
_CODIGOS_IMPRESORA = tuple((n, re.compile(r)) for n, r in (
    ("HP", r"\b(c[bcefz]|q)\d{3,4}[a-z]{1,2}\b|\bw\d{4}[a-z]{1,2}\b"),
    ("Brother", r"\b(tn|dr|lc)-? ?\d{2,4}|\bbtd?-?\d{2,4}"),
    ("Samsung", r"\b(mlt|clt)-?[a-z]?\d{3}"),
    ("Kyocera", r"\btk-? ?\d{3,4}\b"),
    ("Xerox", r"\b(006|106|108|113|013|101)r\d{4,5}\b"),
    ("Canon", r"\b(crg|pgi|cli|gi|pfi|pg|cl|gpr)-? ?\d{2,4}"),
))
# «12A», «206X» en un tóner: la numeración de HP LaserJet.
_TONER_HP = re.compile(r"(?<![\w-])\d{2,3}[ax]\b")
# «T544», «T504» en una tinta: Epson (no «dcp-t520w», que es Brother).
_TINTA_EPSON = re.compile(r"(?<![\w-])t\d{3}[a-z0-9]{0,4}\b")
# Modelos de Konica (bizhub c258...) con códigos TN que también usa Brother.
_MODELO_KONICA = re.compile(r"\bc[2-6]\d{2}e?\b")


def marca_impresora(nombre):
    """Para qué marca de impresora es un tóner o un cartucho (también los
    genéricos «compatible con HP», y por el código de la pieza)."""
    n = _norm(nombre)
    hallazgos = [(nom, m) for nom, rx in _MARCAS_IMPRESORA_RX for m in [rx.search(n)] if m]
    marcas = {nom for nom, _ in hallazgos}
    if len(marcas) == 1:
        return marcas.pop()
    if len(marcas) > 1:
        para = {nom for nom, m in hallazgos if _PARA_MARCA.search(n[max(0, m.start() - 25):m.start()])}
        if len(para) == 1:
            return para.pop()
    por_codigo = {nom for nom, rx in _CODIGOS_IMPRESORA if rx.search(n)}
    if "toner" in n and _TONER_HP.search(n):
        por_codigo.add("HP")
    if "tinta" in n and _TINTA_EPSON.search(n):
        por_codigo.add("Epson")
    if "Brother" in por_codigo and _MODELO_KONICA.search(n):
        por_codigo.discard("Brother")
    if marcas:
        por_codigo &= marcas
    return por_codigo.pop() if len(por_codigo) == 1 else None


# «Color negro», «color: cian» es la etiqueta, no la tinta de color; y hay
# marcas y modelos con «color» en el nombre.
_COLOR_ETIQUETA = re.compile(r"\bcolou?r(es)?\s*:?\s*(?=(negr[oa]|black|cian|cyan|magenta|amarillo|yellow|roj[oa]|azul)\b)"
                             r"|\bcolou?r ?(print|make|vista)\b|\bcolor4\w*|\bprofessor colou?r\b|\brelcolor\b"
                             r"|\blecolor\b|\bjustcolor\b|\bcolor ?laser ?jet\b|\blaser ?jet (pro )?colou?r\b")
_LETRAS_CMY = re.compile(r"\bc\b\W{0,3}\bm\b\W{0,3}\by\b")


def color_tinta(nombre):
    """Negro, Color o Negro y color (paquetes)."""
    n = _COLOR_ETIQUETA.sub(" ", _norm(nombre))
    negro = bool(re.search(r"\bnegr[oa]s?\b|\bblack\b|\bbk\b|\bk\b(?=.*\b(c|m|y)\b)", n))
    color = bool(re.search(r"\btri-?colou?r\b|\bcolou?r(es)?\b|\bcian\b|\bcyan\b|\bmagenta\b|\bamarill[oa]\b|\byellow\b"
                           r"|\bcmy\b|\broj[oa]\b|\bred\b|\bnaranja\b|\borange\b|\bazul\b|\bblue\b", n)
                 or _LETRAS_CMY.search(n)
                 # «BT5001Y BT5001C BT5001M»: el color va pegado al código.
                 or len(set(re.findall(r"\d([cmy])\b", n))) >= 2)
    if re.search(r"\bcmyk|\b4 colores\b|negro y color|black (and|&|y) colou?r|\bkit\b.*\bcolor", n):
        return "Negro y color"
    if negro and color:
        return "Negro y color"
    if negro:
        return "Negro"
    if color:
        return "Color"
    # «PGI-250XL CLI-251XL», «240XL/241XL»: el negro y el de color de Canon.
    if re.search(r"\b(pgi?)-? ?\d{2,3}.*\b(cli?)-? ?\d{2,3}", n):
        return "Negro y color"
    m = re.search(r"\b(\d{2,3})xl\s*/\s*(\d{2,3})xl\b", n)
    if m and int(m.group(2)) == int(m.group(1)) + 1:
        return "Negro y color"
    return None


# ------------------------------------------------- juguetes por franquicia
# Un Funko, una figura o un set de bloques se elige por la saga o la serie
# (04-oct-2026: Funko, Bloques, Muñecas y Figuras a escala sólo se
# comparaban por precio). En orden: la primera que aparece gana (Star Wars y
# Marvel antes que Disney, que es dueña de las dos; Sanrio antes que anime).
_FRANQUICIAS = (
    ("Star Wars", r"star ?wars|mandalorian|darth vader|\byoda\b|grogu|stormtrooper|\bjedi\b|skywalker|boba fett"
                  r"|chewbacca|\bandor\b|ahsoka|dark trooper|clone wars"),
    ("Superhéroes", r"\bmarvel\b|spider-?man|hombre arana|avengers|vengadores|iron ?man\b|\bhulk\b|\bthor\b"
                    r"|capitan america|captain america|x-?men\b|wolverine|deadpool|black panther|pantera negra"
                    r"|guardianes de la galaxia|guardians of the galaxy|\bvenom|\bloki\b|\bgroot\b|thanos"
                    r"|doctor strange|wakanda|wandavision|\bdc\b|batman|superman|wonder woman|mujer maravilla"
                    r"|\bjoker\b|guason|harley quinn|aquaman|justice league|liga de la justicia|gotham|catwoman"
                    r"|shazam|linterna verde|green lantern|super ?heroes|superheroe"),
    ("Harry Potter", r"harry potter|hogwarts|wizarding world|fantastic beasts|animales fantasticos|hermione"
                     r"|dumbledore|voldemort|quidditch"),
    ("Pokémon", r"pokemon|pikachu"),
    ("Sanrio", r"sanrio|hello kitty|kuromi|cinnamoroll|my melody|pompompurin|pochacco"),
    ("Anime", r"dragon ball|\bgoku\b|\bvegeta\b|naruto|one piece|\bluffy\b|demon slayer|kimetsu|my hero academia"
              r"|boku no hero|jujutsu|sailor moon|attack on titan|shingeki|saint seiya|caballeros del zodiaco"
              r"|hunter x hunter|\bbleach\b|chainsaw man|pochita|spy x family|evangelion|death note|fairy tail"
              r"|cowboy bebop|ghibli|totoro|\banime\b|boruto|tokyo revengers|haikyu"
              r"|solo leveling|frieren|yu-?gi-?oh|digimon|siete pecados|seven deadly sins"),
    ("Videojuegos", r"super mario|mario bros|mario kart|\bmario\b|nintendo|zelda|\bsonic\b|minecraft|fortnite"
                    r"|\bhalo\b|overwatch|call of duty|five nights|\bfnaf\b|roblox|among us|\bkirby\b"
                    r"|street fighter|mortal kombat|god of war|the last of us|resident evil|skibidi|playstation"
                    r"|\bxbox\b|pop!? games|cuphead|hollow knight|genshin|league of legends|valorant"
                    r"|assassin'?s creed|animal crossing|splatoon|poppy playtime|huggy wuggy|\bangry birds\b"),
    ("Disney y Pixar", r"disney|pixar|frozen|\belsa\b|mickey|minnie|\bstitch\b|toy story|encanto|moana|sirenita"
                       r"|little mermaid|cenicienta|cinderella|aladdin|rapunzel|enredados|\bariel\b|\blilo\b"
                       r"|winnie|\bpooh\b|rey leon|lion king|monsters,? inc|buzz lightyear|\bwoody\b|\bnemo\b"
                       r"|intensa-?mente|inside out|rayo mcqueen|lightning mcqueen|blancanieves|snow white"
                       r"|maleficent|\bwish\b"),
    ("Jurassic World", r"jurassic"),
    ("Terror", r"stranger things|\bvecna\b|chucky|pennywise|freddy krueger|jason voorhees|viernes 13|michael myers"
               r"|\bscream\b|ghostface|merlina|wednesday|addams|annabelle|el conjuro|exorcista|beetlejuice"
               r"|terrifier|art the clown|\bsaw\b|jigsaw|universal monsters|dracula|frankenstein"),
    ("Series y películas", r"simpsons?\b|rick (and|y) morty|tmnt|tortugas ninja|ninja turtles|power rangers"
                             r"|snoopy|peanuts|looney tunes|bugs bunny|bob esponja|spongebob|scooby|avatar|\baang\b"
                             r"|star trek|breaking bad|game of thrones|juego de tronos|house of the dragon"
                             r"|futurama|south park|hora de aventura|adventure time|gravity falls|steven universe"
                             r"|he-?man|masters of the universe|thundercats|transformers|ghostbusters"
                             r"|cazafantasmas|paw patrol|patrulla canina|peppa|\bbluey\b|granja de zenon"
                             r"|chicas superpoderosas|powerpuff|plaza sesamo|sesame street|cocomelon|baby shark"
                             r"|pocoyo|godzilla|king kong|\bkong\b|lord of the rings|senor de los anillos|hobbit"),
    ("Música y deportes", r"\b(pop|funko)!? rocks\b|elvis|michael jackson|freddie mercury|\bkiss\b|metallica"
                          r"|\bbts\b|\bk-?pop\b|\bnfl\b|\bnba\b|\bmlb\b|futbol|\bmessi\b|ronaldo|\bjordan\b|\bwwe\b"
                          r"|lucha libre"),
)
_FRANQUICIAS_RX = [(n, re.compile(r)) for n, r in _FRANQUICIAS]


def franquicia(nombre):
    """La saga o la serie de un juguete de colección (Funko, figuras,
    peluches), o None."""
    n = _norm(nombre)
    return next((nom for nom, rx in _FRANQUICIAS_RX if rx.search(n)), None)


# Las líneas propias de LEGO, después de las franquicias («LEGO Star Wars»
# es Star Wars). «Para adultos»: Icons, Botanicals, Architecture, Ideas.
_TEMAS_BLOQUES = tuple((n, re.compile(r)) for n, r in (
    ("City", r"\bcity\b"), ("Ninjago", r"ninjago"), ("Friends", r"\bfriends\b|heartlake"),
    ("Technic", r"technic"), ("Creator", r"\bcreator\b(?! expert)"), ("Duplo", r"\bduplo\b"),
    ("Speed Champions", r"speed champions"),
    ("Para adultos", r"\bicons\b|creator expert|botanical|\bflores\b|ramo de|architecture|\blego ideas\b"
                     r"|\blego art\b|\b18\+|para adultos"),
))


def tema_bloques(nombre):
    """Franquicia o línea de un set de bloques."""
    f = franquicia(nombre)
    if f:
        return f
    n = _norm(nombre)
    return next((nom for nom, rx in _TEMAS_BLOQUES if rx.search(n)), None)


_LINEAS_MUNECA = tuple((n, re.compile(r)) for n, r in (
    ("Barbie", r"barbie|\bkelly\b|chelsea|skipper|\bken\b"),
    ("Monster High", r"monster high|draculaura|clawdeen|frankie stein"),
    ("L.O.L. Surprise", r"\blol\b|l\.o\.l|\bomg\b"),
    ("Rainbow High", r"rainbow high"),
    ("Bratz", r"bratz"),
    ("Polly Pocket", r"polly pocket"),
    ("Gabby's Dollhouse", r"gabby"),
    ("Disney", r"disney|princesa|frozen|\belsa\b|\banna\b|moana|\bariel\b|rapunzel|cenicienta"
                         r"|\bwish\b|encanto|mirabel"),
    ("Bebés", r"\bbebe|\bbaby\b|reborn|nenuco|cry ?babies|recien nacid|\bbebot"),
))


def linea_muneca(nombre):
    """La línea de una muñeca (Barbie, Monster High...), o «Bebés»."""
    n = _norm(nombre)
    return next((nom for nom, rx in _LINEAS_MUNECA if rx.search(n)), None)


# ------------------------------------------------- cocina, muebles y más
# Lo que decide la compra y casi siempre dice el nombre (04-oct-2026: estas
# subcategorías sólo se comparaban por precio).
def material_sarten(nombre):
    """La superficie de una sartén, comal u olla. Una de acero con
    recubrimiento antiadherente cuenta como antiadherente (así se usa)."""
    n = _norm(nombre)
    if re.search(r"hierro (fundido|colado|vaciado)|cast iron|\bfundicion\b", n):
        return "Hierro fundido"
    if re.search(r"acero al carbono|carbon steel", n):
        return "Acero al carbono"
    if re.search(r"\bceramic", n):
        return "Cerámica"
    if re.search(r"antiadheren|antiadhesiv|teflon|granito|\bpiedra\b|marmol|titanio|non-?stick", n):
        return "Antiadherente"
    if re.search(r"acero inoxidable|\binox\b|stainless|tri-?ply|\b[35] capas\b|triple capa", n):
        return "Acero inoxidable"
    if re.search(r"\bcobre\b|copper", n):
        return "Cobre"
    return None


_CAJA_WATCH_RE = re.compile(r"\b(38|40|41|42|44|45|46|49)(?=\s*mm\b|\s*/|\s*,|\s+y\s|\s*-\s*\d)")


def caja_apple_watch(nombre):
    """El tamaño de reloj para el que es una correa: «38/40/41 mm» o
    «42/44/45/49 mm». Si nombra los dos (variantes), None. El Series 10 y 11
    de 42 mm usa las chicas."""
    n = _norm(nombre)
    ms = {int(x) for x in _CAJA_WATCH_RE.findall(n)}
    if not ms:
        return None
    if max(ms) <= 41 or (ms == {42} and re.search(r"\bseries? ?1[01]\b", n)):
        return "38 a 41 mm"
    if min(ms) >= 42:
        return "42 a 49 mm"
    return None


def conector_audio(nombre):
    """El conector de unos audífonos de cable."""
    n = _norm(nombre)
    if re.search(r"lightning", n):
        return "Lightning"
    if re.search(r"usb-? ?c\b|tipo-? ?c\b|type-? ?c\b|\busbc\b", n):
        return "USB-C"
    if re.search(r"3\.5 ?mm|\bjack\b|\baux(iliar)?\b|\bplug\b", n):
        return "3.5 mm"
    return None


def tipo_bascula(nombre):
    """Báscula de baño: inteligente (grasa, músculo, app), digital o
    analógica."""
    n = _norm(nombre)
    if re.search(r"grasa|composicion|bluetooth|\bapp\b|\bimc\b|\bbmi\b|bioimpedancia|inteligente|smart|wi-?fi"
                 r"|metricas|analizador|masa muscular|corporal (y|con) ", n):
        return "Inteligente"
    if re.search(r"digital|\blcd\b|electronica|\bled\b", n):
        return "Digital"
    if re.search(r"analogica|mecanica|de aguja|\bdial\b|de reloj", n):
        return "Analógica"
    return None


_NIVELES_RE = re.compile(r"\b(\d{1,2})\s*(niveles|nichos|repisas|entrepanos|estantes|cubos|compartimentos|baldas"
                         r"|anaqueles|pisos|charolas)\b")
_CAJONES_RE = re.compile(r"\b(\d{1,2})\s*(cajones|gavetas)\b")


def niveles_mueble(nombre):
    """Niveles, repisas o nichos de un librero o una zapatera."""
    vals = {int(m.group(1)) for m in _NIVELES_RE.finditer(_norm(nombre)) if 2 <= int(m.group(1)) <= 20}
    return next(iter(vals)) if len(vals) == 1 else None


def cajones_mueble(nombre):
    """Cajones de una cómoda o cajonera."""
    vals = {int(m.group(1)) for m in _CAJONES_RE.finditer(_norm(nombre)) if 2 <= int(m.group(1)) <= 20}
    return next(iter(vals)) if len(vals) == 1 else None


# ------------------------------------------------- PC, belleza y aparatos
# Socket por chipset cuando el nombre no lo dice («B650M» es AM5): 96% de
# las tarjetas madre dicen el chipset y 75% el socket (04-oct-2026).
_CHIP = r"(?:[a-z]{0,2})\b"
_SOCKET_RE = (("AM5", r"\bam5\b|\b(a620|b650|x670|b840|b850|x870)" + _CHIP),
              ("AM4", r"\bam4\b|\b(a320|b350|x370|b450|x470|a520|b550|x570)" + _CHIP),
              ("LGA 1851", r"\b(lga ?|socket ?)?1851\b|\b(h810|b860|z890)" + _CHIP),
              ("LGA 1700", r"\b(lga ?|socket ?)?1700\b|\b(h610|b660|h670|z690|b760|h770|z790)" + _CHIP),
              ("LGA 1200", r"\b(lga ?|socket ?)?1200\b|\b(h410|b460|h470|z490|h510|b560|h570|z590)" + _CHIP),
              ("LGA 1151", r"\b(lga ?|socket ?)?1151\b|\b(h310|b360|b365|h370|z370|z390)" + _CHIP))
_SOCKET_RX = [(n, re.compile(r)) for n, r in _SOCKET_RE]


def socket_tarjeta(nombre):
    """Socket de una tarjeta madre (AM5, AM4, LGA 1851, 1700, 1200)."""
    n = _norm(nombre)
    vals = {nom for nom, rx in _SOCKET_RX if rx.search(n)}
    return vals.pop() if len(vals) == 1 else None


def formato_gabinete(nombre):
    """El formato más grande que admite un gabinete: E-ATX, ATX, Micro ATX
    o Mini ITX («media torre» es ATX)."""
    n = _norm(nombre)
    if re.search(r"\be-? ?atx\b|full ?tower|torre completa|\bxl-?atx\b", n):
        return "E-ATX"
    if re.search(r"(?<!micro )(?<!micro-)(?<!\bm-)(?<!\bm)\batx\b|mid-? ?tower|media torre|mediana torre", n):
        return "ATX"
    if re.search(r"micro-? ?atx|\bm-?atx\b|mini ?torre|mini ?tower", n):
        return "Micro ATX"
    if re.search(r"\bmini-? ?itx\b|\bitx\b", n):
        return "Mini ITX"
    return None


def rin_camion(nombre):
    """El rin de una llanta de camión: 17.5, 19.5, 22.5 o 24.5."""
    vals = set(re.findall(r"(?<![\d.])(17|19|22|24)\.5\b", _norm(nombre)))
    return f"{vals.pop()}.5" if len(vals) == 1 else None


def trapea(nombre):
    """Robot que también trapea."""
    n = _norm(nombre)
    return "Sí" if re.search(r"trapea|\bmopa|\bmop\b|friega|aspira y (trapea|friega)|2 en 1|3 en 1", n) else None


def puntadas(nombre):
    """Puntadas de una máquina de coser («37 puntadas»)."""
    vals = {int(m.group(1)) for m in re.finditer(r"\b(\d{1,4})\s*(puntadas|puntos|stitches)\b", _norm(nombre))
            if 2 <= int(m.group(1)) <= 2000}
    return next(iter(vals)) if len(vals) == 1 else None


def material_plancha(nombre):
    """Las placas de una plancha para cabello."""
    n = _norm(nombre)
    if re.search(r"\bvapor\b|steam", n):
        return "Vapor"
    if re.search(r"titanio|titanium", n):
        return "Titanio"
    if re.search(r"ceramica|ceramic|turmalina|tourmaline", n):
        return "Cerámica"
    return None


def inalambrico_cuidado(nombre):
    """Cortadora o recortadora inalámbrica (recargable). Casi ninguna dice
    «con cable», así que es un rasgo: «Sí» o nada."""
    n = _norm(nombre)
    return "Sí" if re.search(r"inalambric|recargable|cordless|\bbateria\b|sin cable|\busb\b", n) else None


def monitores_soporte(nombre):
    """Para cuántos monitores es un soporte."""
    n = _norm(nombre)
    if re.search(r"\b(triple|cuadruple|para (3|4|6|tres|cuatro|seis) (monitores|pantallas)|(3|4|6) (monitores|pantallas))\b", n):
        return "3 o más"
    if re.search(r"\b(doble|dual|para (2|dos) (monitores|pantallas)|2 (monitores|pantallas)|dos (monitores|pantallas))\b", n):
        return "2 monitores"
    if re.search(r"\b(sencillo|individual|un monitor|1 monitor|para (un|1) monitor|monitor unico)\b", n):
        return "1 monitor"
    return None


# ------------------------------------------------- joyería: de qué metal
# Oro de kilates, plata .925, chapa (baño o laminado) o acero: es lo que
# decide el precio de un collar o unos aretes. «Oro» y «plata» a secas son
# casi siempre el color de la bisutería («4 Piezas Plata», «oro rosa» de
# Swarovski): en una muestra de 25, menos de la mitad eran el metal. Por eso
# sólo cuentan con kilates o con la ley (04-oct-2026).
_PLATA_LEY = re.compile(r"\b925\b|\.925|\bs925\b|sterling|plata (de )?ley|plata esterlina|plata (pura|fina)\b")
_CHAPA = re.compile(r"\bchapa|chapad|\bbano (de |en )?(oro|plata|rodio)|\bbanad[oa]s? (en |de )?(oro|plata|rodio)"
                    r"|\blaminad|\blam\b|gold ?plated|gold ?filled|\bfilled\b|\bplated\b|\bvermeil|aleacion con oro")
_KILATES = re.compile(r"\b(10|14|18|22|24) ?(k|kt|kts|ktes|kilates|quilates)\b|\boro (solido|macizo|puro)\b")
_ACERO_JOYA = re.compile(r"acero inoxidable|\bacero\b|stainless|\btitanio\b|\btungsteno\b|\bsteel\b")


def metal_joya(nombre):
    """Plata .925, Chapa de oro, Oro (de kilates) o Acero inoxidable."""
    n = _norm(nombre)
    if _PLATA_LEY.search(n):
        return "Plata .925"
    if _CHAPA.search(n):
        return "Chapa de oro"
    if _KILATES.search(n):
        return "Oro"
    if _ACERO_JOYA.search(n):
        return "Acero inoxidable"
    return None


# ------------------------------------------------- mascotas: talla
# La talla de una cama, un arnés o un suéter («Talla M», «para perros
# pequeños», «XL»): 24-57% la dice (04-oct-2026).
_TALLA_CHICA = re.compile(r"\btalla:? ?(xxs|xs|s|ch|chica|p)\b|\b(xxs|xs)\b|\b(chic[oa]s?|pequen[oa]s?|mini|toy|small|petite)\b")
_TALLA_MEDIANA = re.compile(r"\btalla:? ?(m|med|mediana)\b|\b(median[oa]s?|medium)\b")
_TALLA_GRANDE = re.compile(r"\btalla:? ?(l|xl|xxl|xxxl|g|eg|grande)\b|\b(xl|xxl|xxxl|2xl|3xl)\b"
                           r"|\b(grandes?|large|gigantes?|extra ?grande|jumbo)\b")


def talla_mascota(nombre):
    """Chica, Mediana o Grande; None si no dice o dice más de una."""
    n = _norm(nombre)
    hits = {t for t, rx in (("Chica", _TALLA_CHICA), ("Mediana", _TALLA_MEDIANA), ("Grande", _TALLA_GRANDE)) if rx.search(n)}
    return hits.pop() if len(hits) == 1 else None


# ------------------------------------------------- muebles: material y tapizado
# Del nombre, en el vocabulario de la ficha (04-oct-2026: mesas de centro,
# escritorios, burós, repisas, taburetes... sólo se comparaban por precio y
# la ficha dice el material en menos del 10%). «Color nogal», «tipo
# mármol», «efecto madera» son el acabado, no el material; el MDF va antes
# que la madera («madera MDF» es aglomerado).
_NO_ES_MATERIAL = r"(?<!color )(?<!tono )(?<!tipo )(?<!acabado )(?<!imitacion )(?<!efecto )(?<!estilo )(?<!look )(?<!vinil )"
_MATERIAL_MUEBLE = tuple((n, re.compile(r)) for n, r in (
    ("Mármol", _NO_ES_MATERIAL + r"\b(marmol|marble)\b"),
    ("Vidrio", _NO_ES_MATERIAL + r"\b(vidrio|cristal)\b"),
    ("Ratán y mimbre", r"\bratt?an\b|\bmimbre|\bbejuco"),
    ("Aglomerado (MDF/MDP)", r"\bmdf\b|\bmdp\b|melamin|aglomerado|\bparticulas\b"),
    ("Madera", _NO_ES_MATERIAL + r"\bmaderas?\b|\bparota\b|\bteca\b|\bbambu\b|\b(pino|encino|roble|nogal|cedro) macizo"
                                 r"|solid wood"),
    ("Metal", _NO_ES_MATERIAL + r"\b(metal|metalic[oa]|acero|hierro|aluminio|forjad[oa]|herreria)\b"),
    ("Plástico", _NO_ES_MATERIAL + r"\b(plastico|polipropileno|resina|pvc|acrilico)\b"),
))
_TAPIZADO = tuple((n, re.compile(r)) for n, r in (
    ("Piel", r"\bpiel\b|\bcuero\b|vinipiel|\bvinil|\bpu\b|leather|curpiel"),
    ("Terciopelo", r"terciopelo|velvet|\bpana\b|aterciopelad"),
    ("Tela", r"\btela\b|\blino\b|poliester|chenille|boucle|textil|algodon|microfibra|\bfabric"),
))


def material_mueble(nombre):
    n = _norm(nombre)
    return next((nom for nom, rx in _MATERIAL_MUEBLE if rx.search(n)), None)


def tapizado(nombre):
    """Tela, terciopelo o piel (también la sintética) de un sofá o sillón."""
    n = _norm(nombre)
    return next((nom for nom, rx in _TAPIZADO if rx.search(n)), None)


# ------------------------------------------------- persianas y maquetas
def ancho_persiana(nombre):
    """El ancho de una persiana en cm: el que dice «ancho» o, en «140 x 220
    cm», el primero (así se anuncian: ancho por alto). 72% lo dice."""
    n = _norm(nombre)
    m = re.search(r"\b(\d{2,3})\s*(cm)?\s*(de )?(ancho|an\b)", n) or re.search(r"\bancho:?\s*(?:de\s*)?(\d{2,3})", n)
    if not m:
        m = re.search(r"\b(\d{2,3})\s*(cm)?\s*x\s*\d{2,3}\s*cm\b", n)
    if not m:
        return None
    v = int(m.group(1))
    return v if 40 <= v <= 400 else None


def escala_modelo(nombre):
    """La escala de un auto o una figura a escala («1:64», «1/18»)."""
    vals = {int(x) for x in re.findall(r"\b1\s*[:/]\s*(\d{1,3})\b", _norm(nombre)) if 4 <= int(x) <= 150}
    return f"1:{vals.pop()}" if len(vals) == 1 else None


# ------------------------------------------------- lámparas, cuadernos, cuadros
def luces_lampara(nombre):
    """Luces (focos o brazos) de un candil o una lámpara colgante."""
    vals = {int(m.group(1)) for m in re.finditer(r"\b(\d{1,2})\s*(luces|focos|brazos|lamparas|bombillas)\b", _norm(nombre))
            if 2 <= int(m.group(1)) <= 40}
    return next(iter(vals)) if len(vals) == 1 else None


def hojas_cuaderno(nombre):
    """Hojas de un cuaderno («100 hojas»); las páginas cuentan como media hoja."""
    n = _norm(nombre)
    vals = {int(m.group(1)) for m in re.finditer(r"\b(\d{2,3})\s*(hojas|h)\b", n) if 20 <= int(m.group(1)) <= 500}
    if not vals:
        vals = {int(m.group(1)) // 2 for m in re.finditer(r"\b(\d{2,3})\s*(paginas|pag)\b", n) if 40 <= int(m.group(1)) <= 1000}
    return next(iter(vals)) if len(vals) == 1 else None


def tamano_cuadro(nombre):
    """El lado más largo de un cuadro en cm («60x80cm» -> 80)."""
    n = _norm(nombre)
    m = re.search(r"\b(\d{2,3})\s*(?:cm)?\s*x\s*(\d{2,3})\s*cm\b", n)
    if not m:
        return None
    v = max(int(m.group(1)), int(m.group(2)))
    return v if 15 <= v <= 300 else None


# ------------------------------------------------- juegos de cartas
_JUEGO_CARTAS = tuple((n, re.compile(r)) for n, r in (
    ("Pokémon", r"pokemon|pikachu"), ("Yu-Gi-Oh!", r"yu-?gi-?oh|yugioh"),
    ("Magic", r"magic:? the gathering|\bmtg\b|magic gathering|\bmagic\b.*(booster|sobre|mazo|commander|draft)"),
    ("One Piece", r"one piece"), ("Dragon Ball", r"dragon ball"), ("Lorcana", r"lorcana"), ("Star Wars", r"star wars"),
    ("UNO", r"\buno\b"), ("Digimon", r"digimon"),
    ("Deportes (Panini, Topps)", r"panini|topps|futbol|soccer|\bnba\b|\bnfl\b|baseball|beisbol"),
))


def juego_cartas(nombre):
    """Qué juego o colección de cartas es (Pokémon, UNO, Magic...)."""
    n = _norm(nombre)
    return next((nom for nom, rx in _JUEGO_CARTAS if rx.search(n)), None)


# ------------------------------------------------- rines por medida
# «Rin delantero 2.15x12», «17x8 6-139», «1.85/18 pulgadas», «21"» (04-oct-2026:
# Rines sólo se comparaba por precio; 55% dice la medida).
_RIN_RX = (re.compile(r"\b\d\.\d{1,2} ?(?:x|/) ?r?(1[0-9]|2[0-4])\b"), re.compile(r"\b(1[0-9]|2[0-4]) ?x ?\d(?:\.\d{1,2})?\b"),
           re.compile(r"\brin (1[0-9]|2[0-4])\b"), re.compile(r"\b(1[0-9]|2[0-4]) ?(?:\"|pulgadas|pulg)"),
           re.compile(r"\d-(1[0-9]|2[0-4])\b"))


def rin_de_rin(nombre):
    n = _norm(nombre)
    vals = {int(m.group(1)) for rx in _RIN_RX for m in rx.finditer(n)}
    return f'{vals.pop()}"' if len(vals) == 1 else None


# ------------------------------------------------- cascos de moto
_TALLAS_CASCO = {"xs": "XS", "s": "S", "ch": "S", "m": "M", "l": "L", "g": "L", "xl": "XL", "eg": "XL", "xxl": "XXL",
                 "2xl": "XXL", "xxxl": "XXL", "3xl": "XXL"}


def talla_casco(nombre):
    """Talla de un casco («Talla L», «talla: xl»)."""
    n = _norm(nombre)
    vals = {_TALLAS_CASCO[m.group(1)] for m in re.finditer(r"\btalla:?\s*(xxxl|3xl|xxl|2xl|xl|xs|eg|ch|s|m|l|g)\b", n)}
    return vals.pop() if len(vals) == 1 else None


def certificacion_casco(nombre):
    """DOT (EE. UU.), ECE (Europa) o las dos."""
    n = _norm(nombre)
    dot, ece = bool(re.search(r"\bdot\b", n)), bool(re.search(r"\bece\b|22\.0[56]", n))
    return "DOT y ECE" if dot and ece else "ECE" if ece else "DOT" if dot else None


# ------------------------------------------------- ventiladores de PC y aspiradoras
def ventilador_mm(nombre):
    """Medida de un ventilador de gabinete (80, 92, 120, 140 mm...)."""
    vals = {int(m.group(1)) for m in re.finditer(r"\b(40|50|60|70|80|92|120|140|180|200)\s*mm\b", _norm(nombre))}
    return f"{vals.pop()} mm" if len(vals) == 1 else None


def capacidad_aspiradora(nombre):
    """Litros del tanque de una aspiradora de seco y húmedo; los galones
    se pasan a litros («12 galones» = 45 L)."""
    n = _norm(nombre)
    m = re.search(r"\b(\d{1,2}(?:\.\d)?)\s*(galones|galon|gal)\b", n)
    if m:
        v = round(float(m.group(1)) * 3.785)
        return v if 3 <= v <= 120 else None
    m = re.search(r"\b(\d{1,3})\s*(l|lt|lts|litros)\b", n)
    return int(m.group(1)) if m and 3 <= int(m.group(1)) <= 120 else None


# ------------------------------------------------- componentes de PC
# Componentes de PC no tenía ni una faceta (05-oct-2026): procesadores,
# tarjetas de video, RAM y fuentes de poder sólo se comparaban por precio.
def socket_procesador(nombre):
    """Socket de un procesador por su modelo («i5-12400» es LGA 1700,
    «Ryzen 5 7600X» AM5, «Core Ultra 7 265K» LGA 1851)."""
    n = _norm(nombre)
    s = socket_tarjeta(nombre)
    if s:
        return s
    if re.search(r"core ultra [3579] ?2\d{2}", n):
        return "LGA 1851"
    m = re.search(r"\bi[3579][- ]?(1[0-4])\d{3}", n)
    if m:
        gen = int(m.group(1))
        return "LGA 1700" if gen >= 12 else "LGA 1200"
    m = re.search(r"\bryzen [3579]\s*(?:pro\s*)?(\d)\d{3}", n)
    if m:
        return "AM5" if int(m.group(1)) >= 7 else "AM4"
    return None


def clase_procesador(nombre):
    """i3/Ryzen 3 de entrada ... i9/Ryzen 9 tope de gama."""
    n = _norm(nombre)
    m = re.search(r"\bcore\s*(?:ultra\s*)?i?([3579])\b|\bi([3579])[- ]?\d{4,5}|\bryzen\s*([3579])\b|\bcore ultra ([3579])", n)
    if not m:
        return None
    k = next(g for g in m.groups() if g)
    return {"3": "Entrada", "5": "Media", "7": "Alta", "9": "Tope"}[k]


def serie_gpu(nombre):
    n = _norm(nombre)
    m = re.search(r"\brtx\s*-?\s*([2-5])0[5-9]0", n)
    if m:
        return f"GeForce RTX {m.group(1)}0"
    m = re.search(r"\brx\s*-?\s*([5-9])\d{3}", n)
    if m:
        return f"Radeon RX {m.group(1)}000"
    if re.search(r"\bgtx\b|\bgt ?[17]\d{2,3}\b", n):
        return "GeForce GTX/GT"
    if re.search(r"\barc\s*[ab]\d{3}", n):
        return "Intel Arc"
    return None


def vram_gb(nombre):
    """Memoria de una tarjeta de video («8gb», «16G»)."""
    n = _norm(nombre)
    vals = {int(m.group(1)) for m in re.finditer(r"\b(2|3|4|6|8|10|12|16|20|24|32)\s*g(?:b)?(?![a-z0-9])", n)}
    return vals.pop() if len(vals) == 1 else None


def ram_total_gb(nombre):
    """Capacidad total de un kit de RAM («32 GB (2 x 16 GB)», «2x8gb» = 16)."""
    n = _norm(nombre)
    m = re.search(r"\b([1-8])\s*x\s*(4|8|16|24|32|48|64)\s*gb?\b", n)
    if m:
        return int(m.group(1)) * int(m.group(2))
    vals = {int(x) for x in re.findall(r"\b(4|8|16|24|32|48|64|96|128)\s*gb\b", n)}
    return max(vals) if vals and len(vals) <= 2 else None


def certificacion_fuente(nombre):
    n = _norm(nombre)
    m = re.search(r"\b(titanium|platinum|platino|gold|oro|silver|bronze|bronce)\b", n)
    if m:
        return {"titanium": "Titanium", "platinum": "Platinum", "platino": "Platinum", "gold": "Gold", "oro": "Gold",
                "silver": "Silver", "bronze": "Bronze", "bronce": "Bronze"}[m.group(1)]
    if re.search(r"80 ?\+|80 ?plus", n):
        return "80 Plus"
    return None


def potencia_fuente(nombre):
    vals = {int(m.group(1)) for m in re.finditer(r"\b(\d{3,4})\s*w\b", _norm(nombre)) if 300 <= int(m.group(1)) <= 2000}
    return vals.pop() if len(vals) == 1 else None


def sistema_capsulas(nombre):
    """Qué cápsulas usa una cafetera."""
    n = _norm(nombre)
    if re.search(r"vertuo", n):
        return "Nespresso Vertuo"
    if re.search(r"dolce gusto|dolcegusto", n):
        return "Dolce Gusto"
    if re.search(r"keurig|k-?cup|k-?mini|k-?express|k-?supreme|k-?elite", n):
        return "K-Cup (Keurig)"
    if re.search(r"\b[2-5] en 1\b|multi ?capsula|varias capsulas", n):
        return "Varias cápsulas"
    if re.search(r"nespresso", n):
        return "Nespresso Original"
    return None


def espada_motosierra(nombre):
    """Largo de la espada (barra) de una motosierra en pulgadas."""
    n = _norm(nombre)
    vals = {int(m.group(1)) for m in re.finditer(r"\b(6|8|10|12|14|16|18|20|22|24|26|28)\s*(\"|pulgadas|pulg|pul|in)(?!\w)", n)}
    return f'{vals.pop()}"' if len(vals) == 1 else None


_PESO_MARTILLO_RE = re.compile(r"(?<![\d.,])(\d{1,3}(?:\.\d{1,2})?)\s*(oz|onzas?|lbs?|libras?|kg|kilos?|g|gr|gramos)\b")
_A_KG = {"oz": 0.02835, "onza": 0.02835, "onzas": 0.02835, "lb": 0.4536, "lbs": 0.4536, "libra": 0.4536,
         "libras": 0.4536, "kg": 1, "kilo": 1, "kilos": 1, "g": 0.001, "gr": 0.001, "gramos": 0.001}


def peso_martillo(nombre):
    """Peso de la cabeza de un martillo o un mazo («Martillo Truper 16 oz»,
    «Marro 4 lb»), en kg. 57% de los martillos lo dice (04-oct-2026)."""
    vals = {round(float(m.group(1)) * _A_KG[m.group(2)], 2) for m in _PESO_MARTILLO_RE.finditer(_norm(nombre))}
    vals = {v for v in vals if 0.1 <= v <= 12}
    return next(iter(vals)) if len(vals) == 1 else None


_PUERTAS_RE = re.compile(r"\b(\d{1,2})\s*puertas?\b")


def puertas(nombre):
    """Puertas de un clóset o una alacena («Closet Madesa Venus 8 Puertas»):
    es lo que dice su tamaño, y el 67% de los roperos lo trae en el nombre."""
    vals = {int(m.group(1)) for m in _PUERTAS_RE.finditer(_norm(nombre)) if 1 <= int(m.group(1)) <= 12}
    return next(iter(vals)) if len(vals) == 1 else None


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
    cable = bool(re.search(r"\bcon cable\b|\balambric|\bjack 3\.?5|\b3\.5 ?mm\b|\busb-?c con cable\b|\bwired\b", n))
    if inal and not cable:
        return "Inalámbrico"
    if cable and not inal:
        return "Con cable"
    return None


def cancelacion_ruido(nombre):
    n = _norm(nombre)
    return "Sí" if re.search(r"cancelacion (activa )?de ruido|\banc\b|noise cancell", n) else None


# ------------------------------------------------------------- rasgos
# Lo que ANTES era una subcategoría («Bocinas Bluetooth impermeables»,
# «Cortinas blackout», «Smartwatches con llamadas») y ahora es una tarjeta de
# Compara calidad (26-sep-2026): un producto puede tener varios rasgos a la
# vez, y con subcategorías tenía que caer en una sola. Sólo se afirma lo que
# el nombre dice ("Sí"); que no lo diga no quiere decir que no lo tenga, así
# que nunca se devuelve "No".
def _rasgo(rx):
    r = re.compile(rx)
    return lambda nombre: "Sí" if r.search(_norm(nombre)) else None


# «5ATM» es siempre una clasificación de resistencia al agua (smartwatches).
_impermeable = _rasgo(r"impermeable|a prueba de agua|water ?proof|resistente al agua|\bipx?[4-8]\d?k?\b|sumergible|\b\d{1,2}\s*atm\b")
_NO_IMPERMEABLE = re.compile(r"\bno (?:es |son )?(?:resistentes? al agua|impermeables?|sumergibles?)")


def impermeable(nombre):
    """"Sí" si el nombre lo afirma; nada si lo niega ("no resistente al
    agua" también contiene "resistente al agua")."""
    return None if _NO_IMPERMEABLE.search(_norm(nombre)) else _impermeable(nombre)
blackout = _rasgo(r"black ?out|\bopac[oa]s?\b|oscurecimiento|oscurecedora|para oscurecer|oscurecen")
_RELOJ_AGUA = re.compile(r"\b\d{1,2}\s*atm\b|\b(?:30|50|100|200|300|500)\s*(?:m|metros)\b(?!\s*m)|\bwr\s?\d{2,3}\b|\b\d{1,2}\s*bar\b")


def impermeable_reloj(nombre):
    """Un reloj dice su resistencia al agua en ATM o metros («3 ATM», «100 m
    Sumergible», «WR50»), además de «resistente al agua». Sólo para relojes:
    en una cadena «50 m» es el largo (04-oct-2026: 145 relojes de Joyería
    lo decían en el nombre y no lo tenían)."""
    if _NO_IMPERMEABLE.search(_norm(nombre)):
        return None
    return impermeable(nombre) or ("Sí" if _RELOJ_AGUA.search(_norm(nombre)) else None)
polarizado = _rasgo(r"polariz")
llamadas = _rasgo(r"llamadas?\b|bluetooth call|\bcall\b")
gps = _rasgo(r"\bgps\b")
datos_moviles = _rasgo(r"\b(4g|5g|lte)\b")
doble_canasta = _rasgo(r"doble canasta|dos canastas|2 canastas|\bdual\b|doble cesta")
memory_foam = _rasgo(r"memory ?foam|viscoelastic|espuma viscoel")


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


def presion_bar(nombre):
    """Bares de la bomba de una cafetera espresso («20 bar», «3.5 Bares»).
    Debajo de 5 es la de vapor (moka eléctrica), no una espresso de bomba."""
    n = _norm(nombre)
    vals = {float(m.group(1).replace(",", ".")) for m in re.finditer(r"(?<![\d.,])(\d{1,2}(?:[.,]\d)?) ?bar(?:es|s)?\b", n)}
    vals = {int(v) if v == int(v) else v for v in vals if 1 <= v <= 25}
    return next(iter(vals)) if len(vals) == 1 else None


def jugadores(nombre):
    """Jugadores que dice el nombre de un juego de mesa («para 2 a 4
    jugadores», «2-6 Jugadores», «Más De 4 Jugadores»), con el mismo
    criterio que la ficha técnica (specs_extract.players_max_of)."""
    import specs_extract as se
    n = _norm(nombre)
    m = re.search(r"((?:mas de |\+ ?)?\d{1,2}(?: ?(?:a|-|y|o) ?\d{1,2})?(?: ?(?:o mas|\+))?) ?(?:jugadores|players|personas)\b", n)
    if not m:
        return None
    # «Más de 4» son cinco o más: el tramo de grupo grande, como «5+».
    mas = re.match(r"mas de (\d{1,2})$", m.group(1))
    if mas:
        return se.players_max_of(f"{int(mas.group(1)) + 1}+")
    return se.players_max_of(m.group(1))


def modo_clima(texto):
    """Minisplit o aire: sólo frío, o frío y calor (bomba de calor). Del
    nombre o de «Tipo de climatización» de la ficha («Frío-Calor»)."""
    n = _norm(texto)
    if re.search(r"frio[ -/y]*calor|calor[ -/y]*frio|bomba de calor|heat pump|calefaccion", n):
        return "Frío y calor"
    if re.search(r"\bsolo frio\b|\bsolo enfriamiento\b|^frio$|\bfrio solo\b", n):
        return "Solo frío"
    return None


# ----------------------------------------------- videojuegos retro, bicicletas
_PLATAFORMAS_RETRO = [
    ("Nintendo Wii U", r"\bwii ?u\b"), ("Nintendo Wii", r"\bwii\b"), ("Nintendo 3DS", r"\b3ds\b|\bn3ds\b"),
    ("Nintendo DS", r"\bnds\b|nintendo ds\b|\bds lite\b|\bdsi\b|\bds\b"),
    ("Game Boy", r"game ?boy|\bgba\b|\bgbc\b"), ("Nintendo 64", r"\bn64\b|nintendo 64"),
    ("GameCube", r"game ?cube|\bngc\b"), ("Super Nintendo", r"\bsnes\b|super nintendo|super nes"),
    ("NES", r"\bnes\b|\bfamicom\b"),
    ("PlayStation 3", r"\bps3\b|playstation ?3"), ("PlayStation 2", r"\bps2\b|playstation ?2"),
    ("PlayStation Vita", r"\bvita\b|\bpsvita\b"), ("PSP", r"\bpsp\b"),
    ("PlayStation", r"\bps1\b|\bpsx\b|\bpsone\b|playstation ?(1|one)\b|ps one"),
    ("Xbox 360", r"xbox ?360|\b360\b"), ("Xbox", r"xbox (clasico|original|classic)|\bxbox\b"),
    ("Sega", r"\bsega\b|genesis|dreamcast|saturn|mega ?drive|master system"), ("Atari", r"\batari\b"),
    ("PC", r"\bpc\b|windows|steam"),
]


def plataforma_retro(nombre):
    """Consola de un juego o accesorio retro («Perfect dark n64», «Warhawk ps3»).
    Gana la primera de la tabla, que va de lo específico a lo general («Wii U»
    antes que «Wii»). Un nombre con dos consolas distintas no se lee."""
    n = _norm(nombre)
    hay = [et for et, rx in _PLATAFORMAS_RETRO if re.search(rx, n)]
    if not hay:
        return None
    # «360/One» (Xbox 360 y Xbox One): la 360 manda; dos consolas de marcas
    # distintas, ninguna.
    marcas = {"Nintendo" if h.startswith(("Nintendo", "Game", "Super", "NES")) else
              "Sony" if h.startswith(("PlayStation", "PSP")) else
              "Microsoft" if h.startswith("Xbox") else h for h in hay}
    return hay[0] if len(marcas) == 1 else None


_RODADAS = {"10", "12", "14", "16", "18", "20", "24", "26", "27.5", "28", "29", "700"}


def rodada_titulo(nombre):
    """Rodada de una bicicleta del nombre («r20», «rodada 26», «12R»): el mismo
    formato que la ficha («R20»). Sólo si el nombre habla de una bicicleta."""
    n = _norm(nombre)
    if not re.search(r"bicicleta|\bbici\b|\bmtb\b|rodada|montana|\bcross\b|\bbmx\b", n):
        return None
    vals = set()
    for rx in (r"\brodada\s*(?:r\s*)?(\d{2}(?:\.5)?|700)\b", r"(?<![\w.])r\s?(\d{2}(?:\.5)?|700)\b(?!\s*[x/]|\s*(?:cm|mm|v|w|gb))",
               r"(?<![\w.])(\d{2}(?:\.5)?)\s?r\b"):
        for m in re.finditer(rx, n):
            if m.group(1) in _RODADAS:
                vals.add(m.group(1))
    return "R" + next(iter(vals)) if len(vals) == 1 else None


# ------------------------------------------------------------------ medidas
_MEDIDAS_RE = re.compile(
    r"(?<![\d.,x×])(\d{1,3}(?:[.,]\d{1,2})?)\s*(?:x|×|por)\s*(\d{1,3}(?:[.,]\d{1,2})?)"
    r"(?:\s*(?:x|×|por)\s*(\d{1,3}(?:[.,]\d{1,2})?))?\s*(cm|mm|m|mts?|metros?|pulgadas?|plg|pulg|in|\")(?![a-z0-9])")


def medidas(nombre):
    """«244 × 264 cm», «41 × 33 × 8 cm»: las medidas que el nombre dice con su
    unidad (cm, mm, m, pulgadas). 14 mil fichas las traen en el título y nada
    las leía (08-oct-2026). Si el nombre trae dos medidas distintas («18x8 cm /
    20x18 cm») no se elige ninguna."""
    n = _norm(nombre).replace("\u202f", " ")
    vistas = set()
    for m in _MEDIDAS_RE.finditer(n):
        nums = [g for g in m.groups()[:3] if g]
        unidad = m.group(4)
        unidad = {"cm": "cm", "mm": "mm", "m": "m", "mt": "m", "mts": "m", "metro": "m", "metros": "m"}.get(unidad, "pulgadas")
        vals = [float(x.replace(",", ".")) for x in nums]
        if unidad == "m" and max(vals) > 100:
            continue
        if unidad == "cm" and max(vals) > 600:
            continue
        if unidad == "pulgadas" and max(vals) > 200:
            continue
        txt = " × ".join(str(int(v)) if v == int(v) else str(v) for v in vals)
        vistas.add(f"{txt} {unidad}")
    return next(iter(vistas)) if len(vistas) == 1 else None
