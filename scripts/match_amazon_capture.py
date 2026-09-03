#!/usr/bin/env python3
"""Toma lo que capturó la extensión de Chrome (ver conversación: popup.js
exporta {asin, title, price, photo, url} por producto) y para cada uno busca
el product_id que le corresponde en el catálogo de ComparaMEX -- el paso que
faltaba entre "capturé datos de Amazon" y add_amazon_offers.py.

CRITERIO DE MATCHING
---------------------
El proyecto ya probó el matching difuso por título puro en otra etapa y dio
falsos positivos a montones (dos productos con nombre parecido pero
distinto). Acá se aplica el mismo criterio conservador que en
audit_cross_store.py:

  - Si el título capturado y un candidato mencionan una capacidad
    (256GB/128GB/1TB) y NO coinciden, el candidato queda excluido aunque
    comparta muchas otras palabras -- una contradicción de capacidad es la
    señal más fuerte de que es OTRO producto.
  - Entre lo que sobrevive ese filtro, se puntúa por palabras en común
    (4+ letras, sin relleno) + bonus si coincide color y variante
    (Pro Max/Pro/Plus/Mini/Air/SE).
  - Solo se asigna automático si hay un candidato con el puntaje más alto
    de forma NO empatada y por encima de un mínimo. Cualquier otro caso
    (cero candidatos, empate, puntaje bajo) se deja para revisión manual
    con la lista de candidatos a la vista -- nunca se adivina.

USO
---
    python3 scripts/match_amazon_capture.py captura.json
    python3 scripts/match_amazon_capture.py captura.json -o resuelto.json

`captura.json` es la lista exportada por la extensión. La salida
(resuelto.json, o captura.resuelto.json si no se pasa -o) es una lista lista
para revisar y pasarle a add_amazon_offers.py: los ítems ya resueltos traen
`product_id`; los que necesitan una decisión traen `candidates` en vez de
`product_id`, para completar a mano antes de importar.
"""
import argparse
import json
import os
import re
import sys
import unicodedata
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog  # noqa: E402

STOP = {
    "para", "con", "del", "los", "las", "por", "que", "este", "esta", "color",
    "pack", "paquete", "unidades", "pulgadas", "pulg", "inch", "the", "and",
    "with", "for",
}
VARIANTS = ("pro max", "pro", "plus", "mini", "air", "se")
COLORS = (
    # "titanio natural" y "titanio del desierto" van primero y a propósito:
    # son colores DISTINTOS del iPhone Pro, y ni "natural" ni "desierto" son
    # palabras de color por sí solas -- así que sin esta entrada compuesta
    # los dos colapsaban al "titanio" genérico y se leían como el mismo
    # color (se vio un caso real: un 16 Pro Titanio del Desierto resolvió
    # solo contra un candidato Titanio Natural). "Titanio Negro"/"Titanio
    # Blanco" NO necesitan esto -- "negro"/"blanco" ya son colores por sí
    # solos más abajo en la lista, y agregarlos acá como compuestos
    # rompía la comparación contra un candidato que dice apenas "Negro"
    # sin la palabra "titanio".
    "titanio natural", "natural titanium", "titanio del desierto",
    "desert titanium",
    "negro", "black", "blanco", "white", "azul", "blue", "rosa", "pink",
    "dorado", "gold", "plata", "silver", "plateado", "plateada", "gris",
    "gray", "grey", "verde", "green", "morado", "purpura", "purple",
    "violeta", "lila", "naranja", "orange", "titanio", "titanium", "rojo",
    "red", "amarillo", "yellow", "grafito", "graphite", "medianoche",
    "media noche", "midnight", "salvia", "sage", "oro", "crema", "coral",
    "beige", "turquesa", "champan", "champán", "champagne", "perla",
    "cobre", "vino", "burgundy", "lavanda", "lavender", "cereza", "cherry",
)
# color_of() devolvía la palabra encontrada TAL CUAL, así que sinónimos
# del mismo color en idiomas/formas distintas ("violeta" vs "morado" vs
# "purple") se leían como colores DISTINTOS -- eso dejó pasar sin marcar
# contradicción un caso real: una captura en "Violeta" resolvió sola
# contra un candidato "(Black)" del catálogo porque tcol quedaba None
# (violeta no estaba siquiera en COLORS) y por lo tanto nunca se
# comparaba. Este mapa canoniza cada sinónimo a un único nombre para que
# la comparación tcol != pcol funcione entre idiomas/variantes.
COLOR_CANON = {
    "black": "negro", "white": "blanco", "blue": "azul", "pink": "rosa",
    "gold": "dorado", "silver": "plata", "gray": "gris", "grey": "gris",
    "green": "verde", "purpura": "morado", "purple": "morado",
    "violeta": "morado", "lila": "morado", "orange": "naranja",
    "titanium": "titanio", "red": "rojo", "yellow": "amarillo",
    "graphite": "grafito", "media noche": "medianoche",
    "midnight": "medianoche", "sage": "salvia",
    "natural titanium": "titanio natural",
    "desert titanium": "titanio del desierto",
    # "plateado"/"plateada" (adjetivo: "acabado plateado") no es la misma
    # palabra que "plata" (sustantivo, el color en sí) así que \bplata\b
    # nunca la encontraba -- color_of() devolvía None para "Plateado" y
    # eso DESACTIVABA por completo el chequeo de contradicción de color
    # (si ninguno de los dos lados declara color, no hay nada que
    # comparar). Se vio un caso real: un iPhone 17 Pro "Plateado"
    # resolvió solo contra un candidato "Azul profundo" porque el color
    # del título quedaba en None.
    "plateado": "plata", "plateada": "plata",
    "champagne": "champan", "champán": "champan",
    "burgundy": "vino", "lavender": "lavanda", "cherry": "cereza",
}
MIN_SCORE = 3


def norm(s):
    # Separar transiciones minúscula->mayúscula ANTES de pasar todo a
    # minúsculas -- varios títulos capturados vienen con palabras pegadas
    # por un salto de línea que se perdió al leer la página ("EsimMorado",
    # "128GBNegroDesbloqueado"). Sin este split, "\bmorado\b" no encuentra
    # límite de palabra dentro de "esimmorado" y el color desaparece sin
    # aviso -- eso fue lo que dejó pasar una coincidencia con la variante
    # equivocada de color en la corrida real de esta captura.
    #
    # OJO: "iPhone" en sí mismo es una transición minúscula->mayúscula
    # ("i" + "Phone") -- sin esta excepción, el split de arriba rompe
    # "iphone" en "i phone" y con eso deja de encontrar el ancla que usan
    # generation_of/VARIANT_RE, lo cual fue MUCHO peor que el bug que se
    # quería arreglar (varias generaciones distintas volvieron a
    # confirmarse solas). Se normaliza el nombre de marca primero para que
    # no le quede ninguna transición de mayúscula que partir.
    s = re.sub(r"iphone", "iphone", s or "", flags=re.IGNORECASE)
    s = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", s)
    # "128GBNegro": GB y la palabra siguiente quedan mayúscula-mayúscula, así
    # que el split de arriba no lo separa -- y sin el espacio, capacities()
    # no encuentra el límite de palabra que necesita después de "gb"/"tb" y
    # la capacidad del propio título capturado desaparece (se vio un caso
    # real: un 128GB así resolvió solo contra un candidato de 256GB porque
    # ya no había nada con qué contradecirlo).
    s = re.sub(r"(\d+\s*(?:gb|tb))(?=[a-zA-Z])", r"\1 ", s, flags=re.IGNORECASE)
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def words(s):
    return {t for t in re.split(r"[^a-z]+", norm(s)) if len(t) >= 4} - STOP


def capacities(s):
    n = norm(s).replace("-", " ")
    # ", ?" entre el número y la unidad (no solo espacio): Amazon a veces
    # aplana el selector de variantes (color/RAM/almacenamiento) DENTRO
    # del título como una lista separada por comas -- "(Negro, 512, GB,
    # GB, 16)" en vez de "512GB" -- y sin tolerar la coma ahí capacities()
    # no encontraba NADA, así que un 512GB se auto-confirmaba sin
    # contradicción contra un candidato de 256GB. Se vio un caso real.
    caps = set(re.findall(r"(\d+)\s*,?\s*(gb|tb)\b", n))
    # Algunos anuncios escriben "128G" en vez de "128GB" -- pero una "G"
    # suelta también es como se escribe la generación de red ("4G", "5G"),
    # así que solo cuenta como almacenamiento cuando el número tiene 2+
    # dígitos: ningún almacenamiento real es de 1-9 GB, y no existe una red
    # "64G". Sin este piso, "128G" se perdía por completo -- se vio un caso
    # real de un 64GB capturado resolviendo solo contra un candidato de
    # 128G porque no había nada con qué contradecirlo.
    caps |= {(num, "gb") for num in re.findall(r"\b(\d{2,4})g\b", n)}
    if not caps:
        return caps
    # Los celulares que no son iPhone suelen anunciar RAM y almacenamiento
    # juntos ("4GB+8GB(Boost)+64GB", "8GB RAM 256GB ROM") -- sin este
    # recorte, la CIFRA DE RAM de un candidato coincidía por casualidad con
    # la de RAM del título capturado aunque el ALMACENAMIENTO real fuera
    # distinto (64GB vs 128GB, ambos con "4GB" de RAM), y como alcanza con
    # que haya AL MENOS una coincidencia para no descartar el candidato,
    # la contradicción de capacidad real quedaba sin detectar. El
    # almacenamiento es prácticamente siempre el número más grande de la
    # lista (ninguna RAM real iguala o supera el almacenamiento del mismo
    # equipo), así que sólo ese cuenta.
    def _gb(t):
        return int(t[0]) * (1024 if t[1] == "tb" else 1)
    return {max(caps, key=_gb)}


def generation_of(s):
    # El número de generación ("14", "15", "16e", "17"...) es el dato que MÁS
    # importa para no confundir un iPhone con otro -- y words() lo descarta
    # por completo, porque el regex de tokenización trata los dígitos como
    # separadores. Sin esto, "iPhone 14" y "iPhone 15 Pro" comparten tantas
    # palabras (apple/iphone/gb/color/...) que el puntaje los daba por
    # iguales; así fue como salieron auto-confirmados varios pares de
    # generación distinta en la primera corrida real.
    # Los modelos con nombre en vez de número (X, XR, XS, XS Max) no traen
    # NINGÚN dígito de generación -- sin este caso aparte, generation_of()
    # devolvía None para un "iPhone XR" tal como para uno sin generación
    # reconocible, así que el hard-exclude de generación (tg != pg) nunca
    # se activaba entre ellos y un numerado, y "iPhone XR" resolvió solo
    # contra "iPhone 12" (modelos completamente distintos) en una corrida
    # real. Se anclan como su propio "número" de generación (xr/xs/xsmax/x)
    # para que sigan siendo comparables entre sí y contra los numerados.
    m = re.search(r"iphone\s*(xs\s*max|xr|xs|x)\b", norm(s))
    if m:
        return re.sub(r"\s+", "", m.group(1))
    m = re.search(r"iphone\s*(\d{1,2})\s*(e)?\b", norm(s))
    if not m:
        return None
    return m.group(1) + (m.group(2) or "")


# Palabras que, si aparecen en el título capturado, TIENEN que aparecer
# también en el nombre del candidato -- si no, se descarta sin más vueltas.
# "iphone" ya cumplía este rol de entrada; se generaliza acá porque sin
# esto un Huawei se confirmó solo contra un Samsung, y otro contra un par
# de audífonos, en una corrida real con celulares que no son iPhone.
# "xiaomi"/"moto" quedan afuera a propósito: varios anuncios reales de
# catálogo (y de Amazon) nombran la línea ("Poco X8 Pro", "Motorola Edge
# 60") sin repetir la marca completa, y exigirla ahí habría descartado
# coincidencias correctas.
BRAND_WORDS = {
    "iphone", "samsung", "motorola", "huawei", "oppo", "realme", "redmi",
    "poco",
}

# "Combo 2 Motorola Moto G06 4-256GB Verde-Verde" es un PAQUETE DE 2
# EQUIPOS (mismo modelo, un color por unidad -- de ahí el color repetido
# tras el guion) a un precio que ya es el de las dos unidades juntas, no
# el de una sola. Una captura de Amazon de una sola unidad (siempre lo
# que se ve en estas capturas) nunca debería auto-confirmarse contra
# esto: el precio y hasta la cantidad de equipos no coinciden aunque
# marca/modelo/color/capacidad sí. Detectado por la firma de nombre que
# usa Elektra para estos paquetes -- "N-NNNGB" con la RAM SIN "GB" propio
# pegada por guion a la capacidad SÍ con "GB" -- que no aparece en
# ningún nombre de equipo individual del catálogo (esos siempre escriben
# "4GB 128GB"/"4GB RAM 128GB", nunca "4-128GB").
MULTI_UNIT_PACK_RE = re.compile(r"\bcombo\s*\d+\b.*\b\d{1,2}-\d{2,4}gb\b", re.IGNORECASE)

# "Desbloqueado" en el título capturado es una afirmación positiva de que
# el equipo NO está atado a ninguna compañía -- un candidato con AT&T/
# Telcel/Movistar explícito en el nombre lo contradice directamente
# (Libre/Otro no, esos sí son compatibles con "desbloqueado"). Se vio un
# caso real: "Motorola Moto Edge 50 ... Desbloqueado" resolvió solo
# contra un candidato "... AT&T Verde" porque nada comparaba esto.
UNLOCKED_HINT_RE = re.compile(r"\bdesbloqueado\b|\bdesbloqueada\b|\bunlocked\b", re.IGNORECASE)
LOCKED_CARRIER_RE = re.compile(r"\b(AT&T|Telcel|Movistar)\b", re.IGNORECASE)

# Número/línea de modelo para las marcas más comunes en las capturas de
# Amazon, con el mismo criterio que generation_of() para iPhone: ancla
# justo después de la línea del producto (Galaxy S/A/Z, Redmi Note, Poco,
# Edge, Pura, Reno/Find X, GT/Neo de realme) en vez de comparar dígitos
# sueltos, que words() ya descarta como separadores. Calibrado contra
# nombres reales del catálogo (ver `python3 -c "...grep Galaxy S2..."` en
# el historial) -- p.ej. "Galaxy S25 Ultra" vs "Galaxy S25 Edge" vs
# "Galaxy S25 FE" son tres equipos distintos con el mismo número base.
# Cada clave del resultado lleva el nombre de marca como prefijo para que
# nunca choque con el de otra marca (el "A17" de Samsung no es el mismo
# equipo que un hipotético "A17" de otra marca).
def _plus(s):
    # "S25+" y "S25 Plus" son el mismo sufijo escrito distinto -- normaliza
    # antes de armar la clave. Importante: un grupo que puede terminar en
    # "+" no puede llevar un \b después en el regex ("+" no es \w, así que
    # si lo que sigue es un espacio o el final del string tampoco lo es,
    # \b no encuentra límite y el grupo completo no matchea -- se vio pasar
    # esto real con "Redmi Note 15 Pro+" y "Galaxy S25+", que sin este
    # arreglo colapsaban a la misma clave que la versión sin "+"/"Pro").
    return (s or "").replace("+", "plus")


_MODEL_PATTERNS = {
    "samsung": (
        (re.compile(r"galaxy\s*s\s*(\d{2})\s*(\+|plus|ultra|edge|fe)?"),
         lambda m: "s" + m.group(1) + _plus(m.group(2))),
        (re.compile(r"galaxy\s*z\s*(fold|flip)\s*(\d{1,2})\s*(ultra)?\b"),
         lambda m: "z" + m.group(1) + m.group(2) + (m.group(3) or "")),
        (re.compile(r"galaxy\s*a\s*(\d{2})(\+)?"),
         lambda m: "a" + m.group(1) + _plus(m.group(2))),
    ),
    "redmi": (
        (re.compile(r"redmi\s*note\s*(\d{1,2})\s*(pro)?\s*(\+)?"),
         lambda m: "note" + m.group(1) + (m.group(2) or "") + _plus(m.group(3))),
        (re.compile(r"redmi\s*(\d{1,2}[a-z]?)\b"),
         lambda m: "redmi" + m.group(1)),
    ),
    "poco": (
        (re.compile(r"poco\s*([a-z])\s*(\d{1,2})\s*(pro|ultra)?\b"),
         lambda m: m.group(1) + m.group(2) + (m.group(3) or "")),
    ),
    "motorola": (
        (re.compile(r"edge\s*(\d{2})\s*(fusion|pro|neo)?\b"),
         lambda m: "edge" + m.group(1) + (m.group(2) or "")),
        # "Power" es una variante real del G-series (más batería), no una
        # forma distinta de nombrar el mismo equipo -- se vio pasar un "Moto
        # G15" (base) resolviendo solo contra un "Moto G15 Power" sin que
        # nada marcara la diferencia.
        (re.compile(r"\bg\s*(\d{2,3})\s*(power)?\b"),
         lambda m: "g" + m.group(1) + (m.group(2) or "")),
    ),
    "huawei": (
        (re.compile(r"pura\s*(\d{2})(s)?\s*(pro\s*max|pro|ultra)?\b"),
         lambda m: "pura" + m.group(1) + (m.group(2) or "") + re.sub(r"\s+", "", m.group(3) or "")),
    ),
    "oppo": (
        (re.compile(r"find\s*x\s*(\d{1,2})(s)?\s*(pro|ultra)?\b"),
         lambda m: "findx" + m.group(1) + (m.group(2) or "") + (m.group(3) or "")),
        (re.compile(r"reno\s*(\d{1,2})([a-z])?\s*(pro\+?|ultra)?"),
         lambda m: "reno" + m.group(1) + (m.group(2) or "") + _plus(m.group(3))),
        # "Pro" es un equipo distinto del "A6" base (precio y specs
        # distintos), no una forma alternativa de nombrar el mismo -- sin
        # capturarlo acá, model_of("OPPO A6 Pro...") y model_of("OPPO A6...")
        # devolvían la misma clave ("oppo:a6") y un merge/otro_libre podía
        # confirmar como "iguales" un A6 Pro contra un A6 sin Pro.
        (re.compile(r"\ba(\d{1,2})([a-z])?\s*(pro)?\b"),
         lambda m: "a" + m.group(1) + (m.group(2) or "") + (m.group(3) or "")),
    ),
    "realme": (
        (re.compile(r"(gt|neo)\s*(\d{1,2})\s*(pro\+?|pro|ultra|se|t)?"),
         lambda m: m.group(1) + m.group(2) + _plus(m.group(3))),
        (re.compile(r"\bp\s*(\d{1,2})\b"), lambda m: "p" + m.group(1)),
        (re.compile(r"\bv\s*(\d{1,2})\b"), lambda m: "v" + m.group(1)),
        (re.compile(r"\bc\s*(\d{1,2})\b"), lambda m: "c" + m.group(1)),
    ),
}


def model_of(s):
    n = norm(s)
    for brand, patterns in _MODEL_PATTERNS.items():
        if brand not in n:
            continue
        for rx, keyfn in patterns:
            m = rx.search(n)
            if m:
                return f"{brand}:{keyfn(m)}"
    return None


VARIANT_RE = re.compile(
    r"iphone\s*(?:\d{1,2}e?)?\s*(" + "|".join(re.escape(v) for v in VARIANTS) + r")\b"
)


def variant_of(s):
    # Tiene que anclarse justo después de "iphone" (como aparece siempre en
    # un título/nombre real: "iPhone 17 Pro Max", "iPhone Air"...), y no
    # buscar la palabra suelta en cualquier parte del texto. Dos bugs reales
    # que dio esa versión más simple:
    #   - "se" como substring aparece dentro de "disenado", "trasera", etc.
    #     (arreglado antes con \b, pero \b solo no alcanza)
    #   - "Chip A19 Pro" aparece en la descripción de CUALQUIER iPhone de
    #     gama alta, incluido el iPhone Air -- así que "pro" suelto se
    #     detectaba como si el propio teléfono fuera el modelo Pro.
    m = VARIANT_RE.search(norm(s))
    return m.group(1) if m else None


_COLOR_RE = re.compile(r"\b(" + "|".join(re.escape(c) for c in COLORS) + r")\b")
# "titanio"/"titanium" SUELTO (sin "natural"/"del desierto" pegado) no es un
# color en sí, es el prefijo que Apple usa para nombrar el acabado real:
# "Titanio Negro", "Titanio Azul" -- el color que importa para comparar es
# "negro"/"azul", no "titanio". Antes de que color_of() mirara la POSICIÓN
# en el texto, esto funcionaba por accidente (la tupla COLORS tiene
# "negro"/"azul" antes que "titanio", así que ganaban igual sin importar
# dónde aparecía cada uno). Al pasar a "el que aparece más a la izquierda"
# se rompió: "titanio" aparece ANTES que "negro" en el texto, así que
# empezó a devolver el prefijo genérico en vez del acabado real -- un
# "iPhone 15 Pro 128GB Titanio Negro" resolvía contra una ficha genérica
# "iPhone 15 Pro (128 GB) - Titanio" (sin acabado específico) en vez de
# mandarse a revisión manual por color no confirmado, exactamente el tipo
# de match que resolve() está diseñado para rechazar.
_BARE_TITANIO = {"titanio", "titanium"}
_COLOR_RE_NO_BARE_TITANIO = re.compile(
    r"\b(" + "|".join(re.escape(c) for c in COLORS if c not in _BARE_TITANIO) + r")\b"
)


def color_of(s):
    # Antes esto recorría COLORS en su orden fijo y devolvía el primer color
    # que matcheara EN CUALQUIER PARTE del texto -- no el que aparece
    # primero en el texto. Un título como "...Naranja con FreeBuds Pro 5
    # Blanco" (el color del regalo mencionado DESPUÉS del color real del
    # equipo) devolvía "blanco" en vez de "naranja" simplemente porque
    # "blanco" está antes que "naranja" en la tupla COLORS, sin relación
    # con dónde aparece cada uno en el título. Ahora se arma un solo regex
    # con todos los colores y se toma el que aparece MÁS A LA IZQUIERDA en
    # el texto -- los compuestos ("titanio natural") siguen ganándole a su
    # prefijo ("titanio") cuando empiezan en la misma posición porque
    # siguen listados primero en COLORS (el orden de alternancia del regex
    # es el desempate cuando dos matchean en el mismo punto de inicio).
    #
    # "titanio" suelto se prueba en una SEGUNDA pasada, solo si ningún otro
    # color aparece en el texto -- así "Titanio Negro" da "negro" (el
    # acabado real) y un "... - Titanio" sin nada más sigue dando "titanio"
    # (ver _BARE_TITANIO arriba).
    n = norm(s)
    m = _COLOR_RE_NO_BARE_TITANIO.search(n)
    if not m:
        m = _COLOR_RE.search(n)
    if not m:
        return None
    c = m.group(1)
    return COLOR_CANON.get(c, c)


def candidates_for(item, products):
    title = item.get("title") or ""
    tw = words(title)
    if not tw:
        return []
    tc = capacities(title)
    tv = variant_of(title)
    tcol = color_of(title)
    tg = generation_of(title)
    tm = model_of(title)
    t_brands = BRAND_WORDS & tw
    t_unlocked = bool(UNLOCKED_HINT_RE.search(title))

    scored = []
    for p in products:
        pw = words(p["name"])
        overlap = tw & pw
        if not overlap:
            continue
        if t_unlocked and LOCKED_CARRIER_RE.search(p["name"]):
            continue
        # Si el título capturado trae una palabra de marca (iphone, samsung,
        # motorola...), el candidato tiene que traerla también -- si no, se
        # descarta sin más vueltas. Sin este chequeo, un "iPhone XR" resolvió
        # solo contra un iPad de la misma capacidad y color, y en otra
        # corrida real un Huawei resolvió solo contra un Samsung, y otro
        # contra un par de audífonos: nada en el puntaje exigía que el
        # candidato fuera siquiera de la misma marca, porque la marca en sí
        # no es una de las cosas que se comparan a propósito (capacidad,
        # generación, variante, color) y una palabra ausente de un lado no
        # resta puntos, solo deja de sumarlos.
        if t_brands and not (t_brands & pw):
            continue
        pc = capacities(p["name"])
        if tc and pc and not (tc & pc):
            continue  # contradicción de capacidad: descartado sin más vueltas
        pg = generation_of(p["name"])
        if tg and pg and tg != pg:
            continue  # contradicción de generación (14 vs 15 Pro, 16 vs 16e, ...): descartado
        pm = model_of(p["name"])
        if tm and pm and tm != pm:
            continue  # contradicción de línea/número de modelo (Galaxy S25 vs S25
            # Edge, Redmi Note 14 vs Note 15, Pura 70 vs Pura 90s...): mismo
            # criterio que la generación de iPhone -- son equipos distintos.
        pcol = color_of(p["name"])
        if tcol and pcol and tcol != pcol:
            continue  # contradicción de color: descartado (a diferencia de capacidad y
            # generación, el color a veces se corrige con un bonus más abajo,
            # pero un choque directo -- grafito vs azul -- es tan mal candidato
            # como una capacidad distinta: se vio un caso real donde ganaba por
            # el bonus de variante a pesar del color equivocado)
        pv = variant_of(p["name"])
        if tv != pv:
            continue  # Pro Max, Pro, Plus, Mini, Air, SE y "base" (ninguno de esos)
            # son equipos DISTINTOS con precio distinto, no una diferencia de
            # redacción -- mismo criterio que capacidad/generación/color. Un
            # nombre de catálogo bien armado dice "Pro" cuando lo es y no lo
            # dice cuando no lo es (y lo mismo vale para el título capturado),
            # así que si no coinciden ninguno de los dos es el otro -- se vio
            # un caso real donde un "iPhone 15" base ganaba por pura suerte de
            # palabras contra un "iPhone 15 Plus" en el catálogo.
        score = len(overlap)
        if tv and pv:
            score += 2
        if tcol and pcol and tcol == pcol:
            score += 1
        if tc and pc and (tc & pc):
            score += 2
        if tg and pg and tg == pg:
            score += 2
        if tm and pm and tm == pm:
            score += 2
        scored.append((score, p))
    scored.sort(key=lambda sp: -sp[0])
    return scored


def resolve(item, products):
    title = item.get("title") or ""
    scored = candidates_for(item, products)
    if not scored:
        return None, []
    top_score = scored[0][0]
    tied = [p for s, p in scored if s == top_score]
    tw = words(title)
    if "iphone" in tw:
        pass  # generation_of()/VARIANT_RE cubren iPhone -- protección de sobra.
    elif model_of(title):
        pass  # una de las marcas con línea/número de modelo reconocido
        # (Samsung, Redmi/Poco, Motorola, Huawei, OPPO, realme) Y el título
        # capturado trae un número de modelo que se pudo extraer -- misma
        # garantía que generation_of() le da a iPhone.
    else:
        # Ni "iphone" ni un número de modelo reconocido para ninguna marca
        # con chequeo propio. Sin eso, lo único que queda es overlap de
        # palabras + capacidad + color, que resultó insuficiente en una
        # corrida real: un Huawei se confirmó solo contra un Samsung, otro
        # contra unos audífonos, y varios pares Galaxy/Redmi/Pura con
        # número de modelo distinto (S23+ vs S24+, Note 14 vs Note 15,
        # Pura 70 vs Pura 90s) se dieron por iguales -- antes de que
        # existiera model_of(). Esto incluye marcas/formatos que
        # model_of() no reconoce todavía (títulos raros, marcas chicas):
        # van a revisión manual sin excepción, igual que antes.
        return None, scored[:5]
    if len(tied) == 1 and top_score >= MIN_SCORE:
        match = tied[0]
        tcol = color_of(item.get("title") or "")
        pcol = color_of(match["name"])
        if tcol and not pcol:
            # El título capturado trae color pero el nombre del candidato no
            # menciona ninguno -- no hay forma de confirmar que sea el mismo
            # color, y un nombre "genérico" así le gana por overlap de
            # palabras a cualquier variante de color real del mismo modelo
            # (se vio un caso real: dos capturas de colores distintos
            # resolviendo las DOS al mismo producto sin color declarado).
            # Mejor mandar a revisión manual que asumir.
            return None, scored[:5]
        tm = model_of(title)
        if tm and not model_of(match["name"]):
            # Mismo problema que el color, pero con la marca/número de
            # modelo: candidates_for() solo descarta por contradicción de
            # modelo cuando LOS DOS lados tienen uno reconocido -- si el
            # candidato no tiene ninguno (nombre en otro formato, o
            # directamente OTRO tipo de producto), no hay nada que lo
            # excluya y puede ganar por overlap de palabras nomás. Se vio
            # un caso real: un "Galaxy A34" (celular) resolvió solo contra
            # una "Galaxy Tab A11+" (tablet) porque la tablet no matcheaba
            # ningún patrón de modelo y por lo tanto no había contradicción
            # que detectar.
            return None, scored[:5]
        tc = capacities(title)
        if tc and not capacities(match["name"]):
            # Mismo problema otra vez, ahora con la capacidad: el título
            # capturado trae "512GB" pero el candidato -- a veces un
            # anuncio-combo con parlante y audífonos de regalo, o
            # directamente un sub-modelo distinto ("G15" vs "G15 Power")
            # que no repite la capacidad en su propio nombre -- no
            # menciona ninguna, así que no hay contradicción que detectar
            # y puede ganar por overlap de palabras nomás.
            return None, scored[:5]
        if MULTI_UNIT_PACK_RE.search(match["name"]) and not MULTI_UNIT_PACK_RE.search(title):
            # El candidato es un paquete de varias unidades (ver
            # MULTI_UNIT_PACK_RE) pero la captura es de una sola unidad --
            # se vio un caso real: "Motorola Moto G06 4+256gb Dual Sim
            # Verde" (una unidad) resolvió solo contra "Combo 2 Motorola
            # Moto G06 4-256GB Verde-Verde" (dos unidades, precio del
            # paquete) porque marca/modelo/color/capacidad coincidían sin
            # que nada chequeara la cantidad de equipos.
            return None, scored[:5]
        return match, scored[:5]
    return None, scored[:5]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--output")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        captured = json.load(f)

    data = load_catalog()
    products = data["products"]

    out = []
    auto, review = 0, 0
    for item in captured:
        asin = item.get("asin")
        if not asin:
            continue
        match, top5 = resolve(item, products)
        row = {"asin": asin, "price": item.get("price"), "photo": item.get("photo")}
        if match:
            row["product_id"] = match["id"]
            row["_matched_name"] = match["name"]  # informativo, add_amazon_offers.py lo ignora
            print(f"  OK  {asin}  '{item.get('title', '')[:45]}'")
            print(f"        -> {match['id']}  {match['name'][:55]}")
            auto += 1
        else:
            row["candidates"] = [
                {"product_id": p["id"], "name": p["name"], "score": s} for s, p in top5
            ]
            print(f"  ??  {asin}  '{item.get('title', '')[:45]}'  ({len(top5)} candidatos, revisar a mano)")
            for s, p in top5:
                print(f"        [{s:>2}] {p['id']}  {p['name'][:55]}")
            review += 1
        out.append(row)

    out_path = args.output or (os.path.splitext(args.input)[0] + ".resuelto.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"\nResueltos automáticamente: {auto}   Necesitan revisión manual: {review}")
    print(f"Escrito: {out_path}")
    if review:
        print("Completá 'product_id' en los que quedaron con 'candidates' antes de "
              "pasarle el archivo a add_amazon_offers.py.")


if __name__ == "__main__":
    main()
