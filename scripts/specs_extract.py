#!/usr/bin/env python3
"""Extrae specs estructuradas (RAM, almacenamiento, pantalla, chip, GPU, etc.)
del NOMBRE de un producto, para poder ofrecer filtros de "Memoria",
"Almacenamiento", "Procesador", "Tarjeta gráfica", etc. en la interfaz.

POR QUÉ DEL NOMBRE Y NO DE product.specs
------------------------------------------
specs[] (label/value) solo existe en una minoría del catálogo -- 28% de
Celulares, 19% de Tabletas, 7% de Laptops tienen algo ahí. El resto solo
tiene el nombre libre capturado de la tienda. Cualquier filtro que dependa
SOLO de specs[] dejaría fuera a la mayoría del catálogo, así que estos
extractores leen primero specs[] (más confiable cuando existe) y si no
hay nada útil, caen al nombre.

CRITERIO: nunca adivinar. Si el nombre es ambiguo (dos números de RAM
posibles, un chip que no matchea ningún patrón conocido), la función
devuelve None para ESE campo en particular -- el producto simplemente no
aparece bajo ningún valor de ese filtro puntual, pero sigue apareciendo
en "todos". Es el mismo criterio que match_amazon_capture.py y
phone_signature.py vienen usando toda la sesión.
"""
import re

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import sin_acentos as _norm  # noqa: E402




# ---------------------------------------------------------------------
# RAM / Almacenamiento
# ---------------------------------------------------------------------
# Set para el paso "número suelto + 'G' sin 'B'" ("778G" de un chip Snapdragon,
# "256G" que Sunsky escribe sin la B). A propósito NO incluye valores chicos
# (4, 8, 16...): "Network: 4G" / "5G" son con diferencia el uso más común de
# un número chico pegado a "G" sin B en estas fichas -- convertirlos a
# "4GB"/"5GB" inventaría una capacidad de la red del teléfono. Es el mismo
# set (y el mismo motivo) que _REAL_CAPS de phone_signature.py.
_REAL_CAPS_BARE_G = {16, 32, 64, 128, 256, 512, 1024, 2048}
# Set general de "esto es una capacidad real" para cuando el número SÍ trae
# la "B" explícita ("4GB RAM") -- ahí no hay ambigüedad con la red, así que
# se permiten los valores chicos que sí usan RAM de laptop/tablet.
_REAL_CAPS = {2, 3, 4, 6, 8, 12, 16, 18, 24, 32, 36, 48, 64, 96, 128, 192, 256, 384, 512, 768, 1024, 1536, 2048, 4096}


def _cap_numbers(name):
    """Todas las capacidades ('NN gb'/'NN tb') que aparecen en el nombre,
    normalizadas a GB, junto con su posición en el texto normalizado."""
    n = _norm(name).replace("+", " + ")
    # "12+512GB", "8GB RAM+256GB ROM", "256gb 8gb ram" ya vienen con "gb"/"tb"
    # pegados casi siempre; el caso sin "b" ("778G" de un chip) se filtra
    # exigiendo que el número sea una capacidad real (y no chica, ver arriba)
    # antes de tratarlo como tal.
    n = re.sub(
        r"\b(\d{1,4})\s*g\b(?!b)",
        lambda m: m.group(1) + "gb" if int(m.group(1)) in _REAL_CAPS_BARE_G else m.group(0),
        n,
    )
    # "512 SSD", "512ssd", "128 SSD" (laptops que omiten la "GB" y confían
    # en "SSD" como unidad implícita) -- sin esto, "Core I7 ... 512 SSD +
    # 8GB" solo veía el "8GB" y lo tomaba como almacenamiento (única
    # capacidad encontrada, sin la palabra "ram" cerca), perdiendo el 512
    # real y quedándose con 8GB como si fuera el disco.
    n = re.sub(r"\b(\d{2,4})\s*(?=ssd|hdd|emmc)\b", r"\1gb ", n)
    # "128GB 6 RAM" (storage con unidad, RAM suelta sin unidad justo antes
    # de la palabra) -- sin esto solo se veía el "128gb" capturado, y como
    # "ram" cae dentro de los 20 caracteres siguientes (ver ram_storage_gb)
    # el único valor encontrado se clasificaba como RAM -- exactamente al
    # revés: 128 es el almacenamiento, 6 (el que de verdad describe "ram")
    # se perdía entero. 1-3 dígitos porque la RAM de estos equipos nunca
    # llega a 4 dígitos.
    n = re.sub(r"\b(\d{1,3})\s*(?=ram\b)", r"\1gb ", n)
    out = []
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(gb|tb)\b", n):
        num = float(m.group(1))
        if m.group(2) == "tb":
            num *= 1024
        out.append((int(num), m.start()))
    return out, n


_RAM_HINT = re.compile(r"\bram\b")


def ram_storage_gb(name):
    """(ram_gb, storage_gb), cualquiera puede ser None.

    Con 1 o 2 valores de capacidad distintos en el nombre, se aplica el
    mismo criterio ya probado en phone_signature.py: el mayor es
    almacenamiento, el menor es RAM (nunca al revés en un equipo real), y
    con un solo valor se decide por si la palabra "ram" aparece pegada.

    Con 3+ valores distintos NO se adivina cuál es cuál -- se vio en
    laptops reales un tercer número que es la capacidad MÁXIMA de
    expansión ("512GB SSD Extensiones 4TB"), no el almacenamiento
    configurado; tomar el máximo a ciegas ahí habría dicho 4TB en vez de
    los 512GB reales.
    """
    caps, n = _cap_numbers(name)
    if not caps:
        return None, None
    nums = sorted({c[0] for c in caps})
    if len(nums) == 1:
        val = nums[0]
        pos = caps[0][1]
        tail = n[pos:pos + 20]
        if _RAM_HINT.search(tail):
            return val, None
        return None, val
    if len(nums) == 2:
        return nums[0], nums[1]
    return None, None


_STORAGE_TYPE_RE = (
    ("nvme", re.compile(r"\bnvme\b")),
    ("ssd", re.compile(r"\bssd\b")),
    ("emmc", re.compile(r"\bemmc\b")),
    ("hdd", re.compile(r"\bhdd\b|\bdisco duro\b")),
)


def storage_type_of(name):
    """'ssd'/'nvme'/'emmc'/'hdd', o None si el nombre no lo dice."""
    n = _norm(name)
    for key, rx in _STORAGE_TYPE_RE:
        if rx.search(n):
            return "ssd" if key == "nvme" else key
    return None


# ---------------------------------------------------------------------
# Pantalla: tamaño en pulgadas y frecuencia de refresco
# ---------------------------------------------------------------------
# "6.7 pulgadas", "15.6\"", "14 inch", "16.2\"" -- exige una unidad explícita
# para no capturar un decimal cualquiera de la ficha (precio, versión de
# Android, etc.).
# El decimal permite 1 O 2 dígitos: "6.7 inch" y "6.59 inch" son igual de
# comunes en las fichas de Sunsky -- con solo 1 dígito permitido, "6.59
# inch" no matcheaba nada (el "9" sobrante rompía el límite de palabra
# justo antes de "inch").
#
# La unidad va en DOS expresiones a propósito:
#
#   1. _SCREEN_UNIT_RE: comillas y palabras. Antes esto era una sola
#      expresión terminada en \b, y ese \b se aplicaba a TODA la
#      alternación -- o sea también a la comilla. Después de un `"` (que no
#      es carácter de palabra) solo hay límite de palabra si viene una letra
#      pegada, así que 15.6" FHD no matcheaba y 15.6"FHD sí: la forma más
#      común de escribir el tamaño quedaba fuera. Se veía en los conteos --
#      Laptops tenía 134 de 1,429 productos con pulgadas; con la comilla
#      arreglada son 908. El \b queda solo en las alternativas de palabra,
#      que sí lo necesitan (para que "inch" no matchee dentro de otra
#      palabra).
#   2. _SCREEN_IN_RE: el sufijo "in" pegado al número ("15.6in"). Va aparte
#      porque NO puede aceptar espacio antes: "8 in 1" (kits y laptops
#      convertibles escritos en inglés) daría 8 pulgadas de la nada. Pegado
#      al número, "15.6in" no tiene otra lectura.
#
# El (?<![\d.,]) del arranque corta el número por la izquierda: sin él,
# "Galaxy Tab S10 FE 109\"" matcheaba los dos últimos dígitos de 109 y dejaba
# una tablet de 9 pulgadas.
_SCREEN_NUM = r"(?<![\d.,])(\d{1,2}(?:[.,]\d{1,2})?)"
_SCREEN_UNIT_RE = re.compile(
    _SCREEN_NUM + r"\s*(?:\"|''|”|″|pulgadas?\b|pulg\.?|inch(?:es)?\b)"
)
_SCREEN_IN_RE = re.compile(_SCREEN_NUM + r"in\b")


def screen_size_in(name):
    """Tamaño de pantalla en pulgadas (float), o None.

    Rango 3–20": fuera de eso es casi siempre otra cosa (un precio, un
    modelo de RAM tipo "8" pulgadas no existe, una resolución mal
    puntuada). Si hay más de un tamaño distinto mencionado (raro, pero
    pasa en combos "laptop + tablet"), no se adivina cuál es el del
    equipo principal.
    """
    n = _norm(name).replace(",", ".")
    sizes = set()
    for rx in (_SCREEN_UNIT_RE, _SCREEN_IN_RE):
        for m in rx.finditer(n):
            try:
                v = float(m.group(1))
            except ValueError:
                continue
            if 3.0 <= v <= 20.0:
                sizes.add(v)
    if len(sizes) == 1:
        return next(iter(sizes))
    return None


_REFRESH_RE = re.compile(r"\b(60|90|120|144|165|180|240)\s*hz\b")


def refresh_hz(name):
    n = _norm(name)
    vals = {int(m.group(1)) for m in _REFRESH_RE.finditer(n)}
    if len(vals) == 1:
        return next(iter(vals))
    return None


# ---------------------------------------------------------------------
# Red: 4G / 5G (celulares y tablets)
# ---------------------------------------------------------------------
def network_gen(name):
    n = _norm(name)
    has5 = re.search(r"\b5g\b", n) is not None
    has4 = re.search(r"\b4g\b|\blte\b", n) is not None
    if has5:
        return "5g"
    if has4:
        return "4g"
    return None


# ---------------------------------------------------------------------
# Chipset (celulares y tablets): se intenta primero el MODELO EXACTO
# ("Snapdragon 8 Elite Gen 5", "Dimensity 9400e") y solo si el nombre no
# trae el número específico se cae a la FAMILIA ("Snapdragon", "Dimensity")
# -- nunca se inventa el número si no está.
_CHIPSET_FAMILIES = (
    ("Apple", re.compile(r"\bapple\s*a\d{2}\b|\bbionic\b")),
    ("Snapdragon", re.compile(r"\bsnapdragon\b|\bsnap\s*dragon\b|\bqualcomm\b")),
    ("Dimensity", re.compile(r"\bdimensity\b")),
    ("Exynos", re.compile(r"\bexynos\b")),
    ("Kirin", re.compile(r"\bkirin\b")),
    ("Tensor", re.compile(r"\bgoogle tensor\b|\btensor g\d\b")),
    ("Unisoc", re.compile(r"\bunisoc\b|\bspreadtrum\b")),
    ("Helio", re.compile(r"\bhelio\b")),
)

# "Snapdragon 8 Elite Gen 5" / "Snapdragon 8 Gen 3" / "Snapdragon 7+ Gen 3"
# / "Snapdragon 8 Elite" -- el número de serie es obligatorio (1-2 dígitos,
# "+" opcional), "Elite" y "Gen N" son opcionales e independientes.
_SNAPDRAGON_CODE_RE = re.compile(
    r"\bsnap\s*dragon\s+(\d{1,2}\+?)(\s*elite)?(\s*gen\s*\d)?\b"
)
_DIMENSITY_CODE_RE = re.compile(r"\bdimensity\s*(\d{3,4}\+?[a-z]?)\b")
_EXYNOS_CODE_RE = re.compile(r"\bexynos\s*(\d{3,4}[a-z]?)\b")
_KIRIN_CODE_RE = re.compile(r"\bkirin\s*(\d{3,4}[a-z]?)\b")
_TENSOR_CODE_RE = re.compile(r"\btensor\s*(g\d)\b")
_HELIO_CODE_RE = re.compile(r"\bhelio\s*([a-z]\d{2,3}[a-z]?)\b")
_UNISOC_CODE_RE = re.compile(r"\b(ums\d{3,4}[a-z]?|t\d{3}[a-z]?)\b")
_CHIPSET_APPLE_CODE_RE = re.compile(r"\ba(1[0-9]|2[0-9])(x|z)?\s*(pro)?\b")


def _fmt_snapdragon(m):
    parts = [f"Snapdragon {m.group(1)}"]
    if m.group(2):
        parts.append("Elite")
    if m.group(3):
        gen_digit = re.search(r"\d", m.group(3)).group(0)
        parts.append(f"Gen {gen_digit}")
    return " ".join(parts)


def chipset_family(name):
    n = _norm(name)

    m = _SNAPDRAGON_CODE_RE.search(n)
    if m:
        return _fmt_snapdragon(m)
    m = _DIMENSITY_CODE_RE.search(n)
    if m:
        return f"Dimensity {m.group(1)}"
    m = _EXYNOS_CODE_RE.search(n)
    if m:
        return f"Exynos {m.group(1)}"
    m = _KIRIN_CODE_RE.search(n)
    if m:
        return f"Kirin {m.group(1)}"
    m = _TENSOR_CODE_RE.search(n)
    if m:
        return f"Tensor {m.group(1).upper()}"
    m = _HELIO_CODE_RE.search(n)
    if m:
        return f"Helio {m.group(1).upper()}"
    if re.search(r"\bunisoc\b|\bspreadtrum\b", n):
        m = _UNISOC_CODE_RE.search(n)
        if m:
            return f"Unisoc {m.group(1).upper()}"
    if re.search(r"\bapple\s*a\d{2}\b|\bbionic\b", n):
        m = _CHIPSET_APPLE_CODE_RE.search(n)
        if m:
            suffix = m.group(2).upper() if m.group(2) else ""
            return f"Apple A{m.group(1)}{suffix}" + (" Pro" if m.group(3) else "")

    for label, rx in _CHIPSET_FAMILIES:
        if rx.search(n):
            return label
    return None


# ---------------------------------------------------------------------
# Modelo (celulares): SOLO para las marcas donde el nombre de línea de
# producto sigue un patrón lo bastante regular para extraerlo sin
# adivinar -- Apple (iPhone), Samsung (Galaxy S/A/Z) y el ecosistema
# Xiaomi (Xiaomi/Redmi/POCO). Para el comprador, "iPhone 15" o "Galaxy
# S24" dice mucho más que el chip que trae adentro (a diferencia de
# Android donde Snapdragon/Dimensity sí es un criterio de compra) -- de
# ahí que este filtro exista aparte de chipset_family, no en su lugar.
# Cada marca se activa solo si `brand` coincide (gate explícito, igual
# que Apple Silicon en cpu_family) para no arriesgar falsos cruces entre
# marcas con números de modelo parecidos.
# ---------------------------------------------------------------------
def _squash(s):
    """Quita TODOS los espacios internos -- normaliza "pro max"/"pro  max"/
    "promax" (variantes de espaciado que la propia tienda mezcla) a una
    sola forma antes de buscarla en los diccionarios de formato de abajo."""
    return re.sub(r"\s+", "", s.strip())


_IPHONE_MODEL_RE = re.compile(
    r"\biphone\s*(x[rs]?|se|air|\d{1,2}e?)\s*(pro\s*max|pro|plus|mini)?\b"
)
_IPHONE_SUFFIX_FMT = {"promax": "Pro Max", "pro": "Pro", "plus": "Plus", "mini": "Mini"}


def _iphone_model(name):
    n = _norm(name)
    m = _IPHONE_MODEL_RE.search(n)
    if not m:
        return None
    base, suffix = m.group(1), m.group(2)
    if base in ("x", "xr", "xs"):
        base = base.upper()
    elif base == "se":
        base = "SE"
    elif base == "air":
        base = "Air"
    label = f"iPhone {base}"
    if suffix:
        label += " " + _IPHONE_SUFFIX_FMT[_squash(suffix)]
    return label


_GALAXY_NOTE_RE = re.compile(r"\bnote\s*(\d{1,2})\b")
_GALAXY_Z_RE = re.compile(r"\b(?:z\s*)?(fold|flip)\s*(\d{1,2})?\b")
_GALAXY_S_RE = re.compile(r"\bs(\d{1,2})(e)?\s*(ultra|\+|plus|fe\s*dual|fe)?\b")
_GALAXY_A_RE = re.compile(r"\ba(\d{2})(e)?\b")
_GALAXY_J_RE = re.compile(r"\bj(\d{1,2})\b")
_GALAXY_S_SUFFIX_FMT = {"ultra": "Ultra", "+": "+", "plus": "+", "fedual": "FE Dual", "fe": "FE"}


def _galaxy_model(name):
    n = _norm(name)
    m = _GALAXY_NOTE_RE.search(n)
    if m:
        return f"Galaxy Note {m.group(1)}"
    # "z" es opcional -- varias fichas escriben "Galaxy Flip 4" sin la Z,
    # pero "fold"/"flip" seguido de número solo existe en la línea
    # plegable de Samsung, así que igual identifica el modelo sin
    # ambigüedad.
    m = _GALAXY_Z_RE.search(n)
    if m:
        line = m.group(1).capitalize()
        return f"Galaxy Z {line}" + (f" {m.group(2)}" if m.group(2) else "")
    m = _GALAXY_S_RE.search(n)
    if m:
        num, e, variant = m.group(1), m.group(2), m.group(3)
        label = f"Galaxy S{num}" + ("e" if e else "")
        if variant:
            label += " " + _GALAXY_S_SUFFIX_FMT[_squash(variant)]
        return label
    m = _GALAXY_A_RE.search(n)
    if m:
        return f"Galaxy A{m.group(1)}" + ("e" if m.group(2) else "")
    m = _GALAXY_J_RE.search(n)
    if m:
        return f"Galaxy J{m.group(1)}"
    return None


_REDMI_TURBO_RE = re.compile(r"\bredmi\s*turbo\s*(\d{1,2})\s*(max|pro)?\b")
_REDMI_NOTE_RE = re.compile(r"\bredmi\s*note\s*(\d{1,2})(s)?\s*(pro\s*max|pro\s*plus|pro\+|pro|plus)?\b")
_REDMI_K_RE = re.compile(r"\bredmi\s*k(\d{1,2})(s)?\s*(pro\s*max|pro)?\b")
_REDMI_A_RE = re.compile(r"\bredmi\s*a(\d{1,2})\s*(pro)?\b")
_REDMI_BARE_RE = re.compile(r"\bredmi\s*(\d{1,2})(c)?\s*(pro)?\b")
_POCO_RE = re.compile(r"\bpoco\s*([xmcf])(\d{1,2})(s)?\s*(pro\s*max|ultra|pro)?\b")
_XIAOMI_CIVI_RE = re.compile(r"\bcivi\s*(\d{1,2})\s*(pro|ultra)?\b")
_XIAOMI_BARE_RE = re.compile(r"\bxiaomi\s*(\d{1,2})([st])?\s*(ultra|pro\s*max|pro|max)?\b")
_NOTE_SUFFIX_FMT = {"promax": "Pro Max", "proplus": "Pro+", "pro+": "Pro+", "pro": "Pro", "plus": "Plus"}
_K_SUFFIX_FMT = {"promax": "Pro Max", "pro": "Pro"}
_POCO_SUFFIX_FMT = {"promax": "Pro Max", "ultra": "Ultra", "pro": "Pro"}
_XIAOMI_SUFFIX_FMT = {"ultra": "Ultra", "promax": "Pro Max", "pro": "Pro", "max": "Max"}


def _xiaomi_model(name):
    n = _norm(name)

    m = _REDMI_TURBO_RE.search(n)
    if m:
        label = f"Redmi Turbo {m.group(1)}"
        if m.group(2):
            label += " " + m.group(2).capitalize()
        return label

    m = _REDMI_NOTE_RE.search(n)
    if m:
        label = f"Redmi Note {m.group(1)}" + ("S" if m.group(2) else "")
        if m.group(3):
            label += " " + _NOTE_SUFFIX_FMT[_squash(m.group(3))]
        return label

    m = _REDMI_K_RE.search(n)
    if m:
        label = f"Redmi K{m.group(1)}" + ("S" if m.group(2) else "")
        if m.group(3):
            label += " " + _K_SUFFIX_FMT[_squash(m.group(3))]
        return label

    m = _REDMI_A_RE.search(n)
    if m:
        return f"Redmi A{m.group(1)}" + (" Pro" if m.group(2) else "")

    m = _POCO_RE.search(n)
    if m:
        letter, num, s_suffix, variant = m.group(1), m.group(2), m.group(3), m.group(4)
        label = f"POCO {letter.upper()}{num}" + ("s" if s_suffix else "")
        if variant:
            label += " " + _POCO_SUFFIX_FMT[_squash(variant)]
        return label

    m = _REDMI_BARE_RE.search(n)
    if m:
        label = f"Redmi {m.group(1)}" + ("C" if m.group(2) else "")
        if m.group(3):
            label += " Pro"
        return label

    m = _XIAOMI_CIVI_RE.search(n)
    if m:
        label = f"Xiaomi Civi {m.group(1)}"
        if m.group(2):
            label += " " + m.group(2).capitalize()
        return label

    m = _XIAOMI_BARE_RE.search(n)
    if m:
        label = f"Xiaomi {m.group(1)}" + (m.group(2).upper() if m.group(2) else "")
        if m.group(3):
            label += " " + _XIAOMI_SUFFIX_FMT[_squash(m.group(3))]
        return label
    return None


def model_name(name, brand):
    """Modelo exacto (línea de producto) o None -- ver comentario arriba
    de por qué solo estas 3 marcas."""
    b = _norm(brand or "")
    if b == "apple":
        return _iphone_model(name)
    if b == "samsung":
        return _galaxy_model(name)
    if b in ("xiaomi", "poco", "redmi"):
        return _xiaomi_model(name)
    return None


# ---------------------------------------------------------------------
# Cámara principal (MP) y batería (mAh) -- celulares/tablets
# ---------------------------------------------------------------------
# El número más ALTO de "NNmp"/"NN mpx" es casi siempre la cámara
# principal (las secundarias/macro/profundidad son menores) -- "50MP+2MP"
# -> 50. Con un techo de 250 se descarta ruido tipo "108MP" mal escrito
# junto a specs de otra cosa (no se ha visto en la práctica, pero es una
# cámara real de gama alta hoy, así que el techo se deja holgado).
_CAMERA_RE = re.compile(r"\b(\d{1,3})\s*mp(?:x)?\b")


def camera_mp(name):
    n = _norm(name)
    vals = [int(m.group(1)) for m in _CAMERA_RE.finditer(n)]
    vals = [v for v in vals if 2 <= v <= 250]
    return max(vals) if vals else None


_BATTERY_RE = re.compile(r"\b(\d{3,5})\s*mah\b")


def battery_mah(name):
    n = _norm(name)
    vals = {int(m.group(1)) for m in _BATTERY_RE.finditer(n)}
    vals = {v for v in vals if 1000 <= v <= 15000}
    if len(vals) == 1:
        return next(iter(vals))
    return None


# ---------------------------------------------------------------------
# Laptops: marca+familia de CPU
# ---------------------------------------------------------------------
_CPU_FAMILIES = (
    # Apple Silicon primero: "Apple M4" no debe caer en ningún patrón Intel/AMD.
    ("Apple M", re.compile(r"\bapple\s*(m\d)\b|\bchip\s*(m\d)\b(?!\s*pro)")),
    ("Apple M Pro/Max", re.compile(r"\bm\d\s*(pro|max|ultra)\b")),
    ("Intel Core Ultra", re.compile(r"\bcore\s*ultra\s*[3579x]?\b|\bultra\s*[3579]\s*\d{2,3}[a-z]?\b")),
    ("Intel Core i9", re.compile(r"\bi9[\s-]?\d{3,5}[a-z]*\b|\bcore\s*i9\b")),
    ("Intel Core i7", re.compile(r"\bi7[\s-]?\d{3,5}[a-z]*\b|\bcore\s*i7\b")),
    ("Intel Core i5", re.compile(r"\bi5[\s-]?\d{3,5}[a-z]*\b|\bcore\s*i5\b")),
    ("Intel Core i3", re.compile(r"\bi3[\s-]?\d{3,5}[a-z]*\b|\bcore\s*i3\b")),
    ("Intel Core (3/5/7)", re.compile(r"\bintel\s*core\s*[357]\b(?!\s*i)")),
    ("Intel Celeron/Pentium", re.compile(r"\bceleron\b|\bpentium\b")),
    ("Intel N-series", re.compile(r"\bn\d{3,4}\b")),
    ("AMD Ryzen 9", re.compile(r"\bryzen\s*9\b|\br9[\s-]?\d{3,4}\w*\b")),
    ("AMD Ryzen 7", re.compile(r"\bryzen\s*7\b|\br7[\s-]?\d{3,4}\w*\b")),
    ("AMD Ryzen 5", re.compile(r"\bryzen\s*5\b|\br5[\s-]?\d{3,4}\w*\b")),
    ("AMD Ryzen 3", re.compile(r"\bryzen\s*3\b|\br3[\s-]?\d{3,4}\w*\b")),
    ("AMD Ryzen AI", re.compile(r"\bryzen\s*ai\b")),
    ("AMD Athlon", re.compile(r"\bathlon\b")),
    ("Qualcomm Snapdragon X", re.compile(r"\bsnapdragon\s*x\b")),
    ("MediaTek Kompanio", re.compile(r"\bkompanio\b")),
)


_APPLE_BARE_M_RE = re.compile(r"\bm([1-5])\s*(pro|max|ultra)?\b")
# La línea "MacBook Neo" (vista repetidas veces en capturas de Amazon esta
# sesión) usa el chip A-series de iPhone/iPad, no el M-series de MacBook --
# "Chip A16 Pro de Apple", "Chip A18 Pro". Sin este patrón quedaban sin CPU
# detectado a pesar de que el nombre sí lo dice.
_APPLE_A_SERIES_RE = re.compile(r"\ba(1[5-9]|2[0-9])\s*(pro)?\b")

# Modelo EXACTO de CPU cuando el nombre lo trae -- "i5-13420H", "Ryzen 7
# 7735HS", "Core Ultra 7 155H" -- antes de caer a la familia sola ("Core
# i5", "Ryzen 7"). El código real de Intel/AMD siempre son 3-5 dígitos
# pegados directamente (un solo espacio o guion) a la marca de familia;
# eso además excluye, sin buscarlo a propósito, a los marcadores de
# generación en español tipo "10a Gen"/"11ª generación", que nunca traen
# ese patrón exacto.
_INTEL_IX_CODE_RE = re.compile(r"\bi([3579])[\s-](\d{4,5}[a-z]{0,3})\b")
_INTEL_ULTRA_CODE_RE = re.compile(r"\bultra\s*([3579])?[\s-]*(\d{3}[a-z]{0,2})\b")
_RYZEN_CODE_RE = re.compile(r"\bryzen\s*([3579])(\s*pro)?[\s-]*(\d{3,4}[a-z]{0,3})\b")


def cpu_family(name, brand=None):
    """`brand`, si se pasa, solo se usa para permitir los patrones de Apple
    Silicon SUELTOS (sin la palabra "Apple" ni "chip" antes) -- "MacBook
    Air 13 M5 16GB..." no trae ninguna de esas dos palabras. Fuera de
    Apple no se activan esos patrones: un "M5" suelto en cualquier otra
    marca es demasiado ambiguo (existió una línea real "Intel Core M5"
    hace años) para adivinarlo solo por el número.
    """
    n = _norm(name)
    if brand and _norm(brand) == "apple":
        m = _APPLE_BARE_M_RE.search(n)
        if m:
            return "Apple M" if not m.group(2) else "Apple M Pro/Max"
        if _APPLE_A_SERIES_RE.search(n):
            return "Apple A-series"

    m = _INTEL_IX_CODE_RE.search(n)
    if m:
        return f"Intel Core i{m.group(1)}-{m.group(2).upper()}"
    m = _INTEL_ULTRA_CODE_RE.search(n)
    if m and "core ultra" in n:
        tier = f"{m.group(1)} " if m.group(1) else ""
        return f"Intel Core Ultra {tier}{m.group(2).upper()}"
    m = _RYZEN_CODE_RE.search(n)
    if m:
        pro = " PRO" if m.group(2) else ""
        return f"AMD Ryzen {m.group(1)}{pro} {m.group(3).upper()}"

    for label, rx in _CPU_FAMILIES:
        if rx.search(n):
            return label
    return None


# ---------------------------------------------------------------------
# Laptops: GPU -- discreta (marca + serie) o integrada
# ---------------------------------------------------------------------
# Modelo EXACTO cuando el número está en el nombre ("RTX 4060", "GTX 1650
# Ti", "Radeon RX 7600S") -- las familias de abajo son solo el fallback
# cuando la ficha menciona la marca sin el número específico.
_RTX_CODE_RE = re.compile(r"\brtx\s*(5[0-9]{3}|4[0-9]{3}|3[0-9]{3}|2[0-9]{3})\s*(ti)?\b")
_GTX_CODE_RE = re.compile(r"\bgtx\s*(1[0-9]{3}|9[0-9]{2})\s*(ti)?\b")
_RADEON_RX_CODE_RE = re.compile(r"\bradeon\s*rx\s*(\d{3,4}[a-z]?)\b")
_RADEON_IGPU_CODE_RE = re.compile(r"\bradeon\s*(780m|760m|740m|680m|660m)\b")
_ARC_CODE_RE = re.compile(r"\barc\s*(\d{3}[a-z]?)\b")

_GPU_DISCRETE = (
    ("NVIDIA Quadro/RTX Pro", re.compile(r"\bquadro\b|\brtx\s*pro\b")),
    ("NVIDIA (otra)", re.compile(r"\bnvidia\b|\bgeforce\b")),
    ("AMD Radeon (dedicada)", re.compile(r"\bradeon\s*rx\b")),
)
_GPU_INTEGRATED = (
    ("AMD Radeon (integrada)", re.compile(r"\bradeon\s*(?:780m|760m|740m|680m|660m|graphics)\b")),
    ("Intel Arc", re.compile(r"\bintel\s*arc\b|\barc\s*\d{3}[a-z]?\b|\barc\s*graphics\b")),
    ("Intel Iris Xe", re.compile(r"\biris\s*xe\b")),
    ("Intel UHD", re.compile(r"\buhd\s*graphics\b")),
    ("Qualcomm Adreno", re.compile(r"\badreno\b")),
    ("Apple GPU integrada", re.compile(r"\bapple\s*m\d\b")),
)


def gpu_of(name):
    """Devuelve una etiqueta de GPU o None. Primero se intenta el modelo
    EXACTO (RTX/GTX/Radeon RX/Radeon integrada/Arc con su número), luego
    los patrones de GPU DISCRETA sin número específico -- son los que de
    verdad importan para un comprador que filtra por esto -- y solo si no
    hay ninguna mención de GPU dedicada se cae a los patrones de
    integrada. Nunca se asume "integrada" por default cuando el nombre
    simplemente no menciona ninguna GPU: eso sería inventar un dato que
    la ficha no trae.
    """
    n = _norm(name)

    m = _RTX_CODE_RE.search(n)
    if m:
        return f"NVIDIA RTX {m.group(1)}" + (" Ti" if m.group(2) else "")
    m = _GTX_CODE_RE.search(n)
    if m:
        return f"NVIDIA GTX {m.group(1)}" + (" Ti" if m.group(2) else "")
    m = _RADEON_RX_CODE_RE.search(n)
    if m:
        return f"AMD Radeon RX {m.group(1).upper()}"

    for label, rx in _GPU_DISCRETE:
        if rx.search(n):
            return label

    m = _RADEON_IGPU_CODE_RE.search(n)
    if m:
        return f"AMD Radeon {m.group(1).upper()}"
    m = _ARC_CODE_RE.search(n)
    if m:
        return f"Intel Arc {m.group(1).upper()}"

    for label, rx in _GPU_INTEGRATED:
        if rx.search(n):
            return label
    return None


# ---------------------------------------------------------------------
# Laptops: sistema operativo
# ---------------------------------------------------------------------
_OS_PATTERNS = (
    ("macOS", re.compile(r"\bmacos\b|\bmac os\b")),
    ("ChromeOS", re.compile(r"\bchrome\s*os\b|\bchromebook\b|\bcromado os\b")),
    ("Windows 11", re.compile(r"\bwindows\s*11\b|\bwin\s*11\b|\bw11\b")),
    ("Windows 10", re.compile(r"\bwindows\s*10\b|\bwin\s*10\b|\bw10\b")),
    ("Linux", re.compile(r"\blinux\b|\bubuntu\b")),
)


def os_of(name):
    n = _norm(name)
    for label, rx in _OS_PATTERNS:
        if rx.search(n):
            return label
    return None


# ---------------------------------------------------------------------
# Monitores: tipo de panel y resolución
# ---------------------------------------------------------------------
# OLED antes que IPS/VA/TN -- "QD-OLED"/"WOLED" son variantes de OLED, y un
# monitor OLED nunca es TAMBIÉN IPS/VA/TN (son tecnologías de panel
# excluyentes), así que el primer match que aparezca es el correcto.
_PANEL_TYPE_PATTERNS = (
    ("OLED", re.compile(r"\boled\b|\bqd-oled\b|\bwoled\b")),
    ("IPS", re.compile(r"\bips\b")),
    ("VA", re.compile(r"\bva\b")),
    ("TN", re.compile(r"\btn\b")),
)


def panel_type(name):
    n = _norm(name)
    for label, rx in _PANEL_TYPE_PATTERNS:
        if rx.search(n):
            return label
    return None


# Del más específico al más genérico -- "4K"/"UWQHD"/"DQHD" son también
# técnicamente "HD", así que si "HD" (el patrón más suelto) se probara
# primero se comería todo lo demás. Cada patrón exige su propia palabra
# clave o su propia resolución en píxeles (nunca solo "ancho x alto"
# suelto, que podría ser cualquier otra cosa en la ficha).
_RESOLUTION_PATTERNS = (
    # 8K va primero: su ficha casi siempre dice también "UHD", así que con
    # 4K delante todo televisor 8K se leía como 4K.
    ("8K UHD", re.compile(r"\b8k\b|\b7680\s*x\s*4320\b")),
    ("4K UHD", re.compile(r"\b4k\b|\buhd\b|\b3840\s*x\s*2160\b")),
    ("DQHD", re.compile(r"\bdqhd\b|\b5120\s*x\s*1440\b")),
    ("UWQHD", re.compile(r"\buwqhd\b|\b3440\s*x\s*1440\b")),
    ("QHD", re.compile(r"\bqhd\b|\bwqhd\b|\bquad\s*hd\b|\b2560\s*x\s*1440\b|\b2k\b")),
    ("WFHD", re.compile(r"\bwfhd\b")),
    ("FHD", re.compile(r"\bfhd\b|\bfull\s*hd\b|\b1920\s*x\s*1080\b|\b1080p\b")),
    ("WSXGA+", re.compile(r"\bwsxga\+?\b|\b1680\s*x\s*1050\b")),
    ("HD+", re.compile(r"\bhd\+\b|\b1440\s*x\s*900\b")),
    ("HD", re.compile(r"\bhd\b|\b1366\s*x\s*768\b|\b1280\s*x\s*720\b")),
)


def resolution_of(name):
    n = _norm(name)
    for label, rx in _RESOLUTION_PATTERNS:
        if rx.search(n):
            return label
    return None


# screen_size_in() (arriba) exige una unidad explícita ("/pulgadas/inch) --
# conservador para celulares/laptops, pero en Monitores la convención más
# común es "Monitor {N} Marca Modelo" con el número SUELTO justo después
# de la palabra "Monitor", sin unidad. Acotado a Monitores nomás (no se
# toca screen_size_in, que sigue siendo lo que usan las demás categorías):
# exige que el número esté a lo sumo a 25 caracteres de "monitor" Y dentro
# del rango real de un monitor (14"-55") para no adivinar con un código de
# modelo o una frecuencia cualquiera. Excluye explícitamente "NN cm" --
# unas pocas fichas dan el tamaño en centímetros, no pulgadas, y sin este
# descarte "48 cm" (en realidad ~19") se leía como un monitor de 48".
_MONITOR_BARE_SIZE_RE = re.compile(r"\bmonitor(?:es)?\b[^0-9]{0,25}?(\d{2}(?:[.,]\d)?)\b(?!\s*cm\b)")


def monitor_screen_in(name):
    explicit = screen_size_in(name)
    if explicit is not None:
        return explicit
    n = _norm(name).replace(",", ".")
    m = _MONITOR_BARE_SIZE_RE.search(n)
    if m:
        try:
            v = float(m.group(1))
        except ValueError:
            return None
        if 14.0 <= v <= 55.0:
            return v
    return None


_CURVED_RE = re.compile(r"\bcurv[ao]\b|\bcurved\b|\b\d{3,4}r\b")


def is_curved(name):
    """True si el nombre dice explícitamente que es curvo, None si no dice
    nada (nunca False -- un monitor plano normalmente no se anuncia como
    "no curvo", así que la ausencia de la palabra no confirma que sea
    plano)."""
    n = _norm(name)
    return True if _CURVED_RE.search(n) else None


# ---------------------------------------------------------------------
# Televisores
# ---------------------------------------------------------------------
# Misma situación que en Monitores: la convención de la categoría es
# "Pantalla 55 Pulgadas ..." o "Smart TV 43 ...", muchas veces con el
# número suelto. Se acota a un rango real de televisor (24"-110") y se
# exige que el número esté cerca de la palabra que lo introduce, para no
# confundirlo con un código de modelo o los Hz.
_TV_BARE_SIZE_RE = re.compile(
    r"\b(?:pantalla|televisor(?:es)?|smart\s*tv|tv|led|qled|oled)\b[^0-9]{0,18}?"
    r"(\d{2,3}(?:[.,]\d)?)\b(?!\s*(?:cm|hz|w|v)\b)"
)


# screen_size_in() corta en 20" (es para celulares, tablets y laptops), así
# que un televisor de 75" no pasaba por ahí: la unidad explícita se vuelve a
# buscar acá con el rango de la categoría.
_TV_UNIT_SIZE_RE = re.compile(
    r"(?<![\d.,])(\d{2,3}(?:[.,]\d)?)\s*(?:\"|''|”|″|pulgadas?\b|pulg\.?|inch(?:es)?\b)"
)


# "Soporte para TV de 32 a 70 pulgadas": solo el segundo número trae la
# unidad, así que se leía como un televisor de 70". Un rango describe qué
# tamaños ACEPTA un accesorio, no el tamaño de un televisor.
_TV_RANGE_RE = re.compile(r"\bde\s*\d{2,3}\s*(?:\"|pulgadas?|pulg)?\s*a\s*\d{2,3}\b")


def tv_screen_in(name):
    """Pulgadas de un televisor, o None."""
    n = _norm(name).replace(",", ".")
    if _TV_RANGE_RE.search(n):
        return None
    tallas = set()
    for m in _TV_UNIT_SIZE_RE.finditer(n):
        try:
            v = float(m.group(1))
        except ValueError:
            continue
        if 24.0 <= v <= 110.0:
            tallas.add(v)
    if len(tallas) == 1:
        return next(iter(tallas))
    if tallas:
        return None  # dos tamaños distintos en el nombre: no se adivina
    m = _TV_BARE_SIZE_RE.search(n)
    if m:
        try:
            v = float(m.group(1))
        except ValueError:
            return None
        if 24.0 <= v <= 110.0:
            return v
    return None


# ---------------------------------------------------------------------
# Videojuegos: la consola para la que es el juego
# ---------------------------------------------------------------------
# El orden importa: "Nintendo Switch 2" tiene que probarse antes que
# "Nintendo Switch", y "Xbox Series" antes que "Xbox One", porque el
# nombre más corto es prefijo del más largo.
_PLATFORM_PATTERNS = (
    ("Nintendo Switch 2", re.compile(r"\bnintendo\s*switch\s*2\b|\bswitch\s*2\b")),
    ("Nintendo Switch", re.compile(r"\bnintendo\s*switch\b|\bswitch\b")),
    ("PlayStation 5", re.compile(r"\bps\s*5\b|\bplaystation\s*5\b")),
    ("PlayStation 4", re.compile(r"\bps\s*4\b|\bplaystation\s*4\b")),
    ("Xbox Series X|S", re.compile(r"\bxbox\s*series\b")),
    ("Xbox One", re.compile(r"\bxbox\s*one\b")),
    ("PC", re.compile(r"\bpara\s*pc\b|\bpc\s*digital\b|\bsteam\b")),
)


def platform_of(name):
    """Consola a la que pertenece el juego, o None si el nombre no la dice.

    Si el nombre menciona DOS consolas distintas no se elige ninguna: pasa
    en los packs y en los accesorios "compatible con PS4/PS5", y quedarse
    con la primera sería inventar para cuál es.
    """
    n = _norm(name)
    hits = [label for label, rx in _PLATFORM_PATTERNS if rx.search(n)]
    if not hits:
        return None
    # "Nintendo Switch 2" matchea también el patrón de "Nintendo Switch":
    # eso no es ambigüedad, es el mismo juego escrito una vez, y se queda el
    # más específico (el primero de la lista).
    #
    # Dos consolas que NO son una prefijo de la otra sí son ambigüedad real:
    # "compatible PS4 y PS5" no dice para cuál es. Con una regla por familia
    # ("PlayStation" para las dos) esto devolvía PS5 a ciegas.
    if len(hits) > 1:
        base = hits[0]
        if not all(h == base or base.startswith(h) or h.startswith(base) for h in hits):
            return None
    return hits[0]


# ---------------------------------------------------------------------
# Lavadoras y refrigeradores: capacidad
# ---------------------------------------------------------------------
_WASH_KG_RE = re.compile(r"(\d{1,2}(?:[.,]\d)?)\s*(?:kg|kilos?)\b")
_FRIDGE_FT_RE = re.compile(r"(\d{1,2}(?:[.,]\d)?)\s*(?:pies|p3|ft3|pies\s*c[uú]bicos)\b")


def wash_capacity_kg(name):
    """Carga de una lavadora en kg, o None. Rango 5-30: por debajo es un
    peso de envío o un accesorio, por arriba es una lavadora industrial que
    no comparte estante con las del catálogo."""
    n = _norm(name).replace(",", ".")
    vals = set()
    for m in _WASH_KG_RE.finditer(n):
        try:
            v = float(m.group(1))
        except ValueError:
            continue
        if 5.0 <= v <= 30.0:
            vals.add(v)
    return next(iter(vals)) if len(vals) == 1 else None


def fridge_capacity_ft3(name):
    """Capacidad de un refrigerador en pies cúbicos, o None. Rango 3-35."""
    n = _norm(name).replace(",", ".")
    vals = set()
    for m in _FRIDGE_FT_RE.finditer(n):
        try:
            v = float(m.group(1))
        except ValueError:
            continue
        if 3.0 <= v <= 35.0:
            vals.add(v)
    return next(iter(vals)) if len(vals) == 1 else None


# ---------------------------------------------------------------------
# Medida de cama (colchones, bases, sábanas, edredones)
# ---------------------------------------------------------------------
# Es LA pregunta de la categoría: unas sábanas queen no sirven en una cama
# matrimonial. Las tiendas mexicanas usan indistintamente el nombre local y
# el de EE.UU. para la misma medida, así que se canonizan: twin=individual,
# full=matrimonial. "California King" se deja aparte de "King" porque es
# otra medida real (más larga y menos ancha).
_BED_SIZE_PATTERNS = (
    ("California King", re.compile(r"\bcalifornia\s*king\b|\bcal\.?\s*king\b")),
    ("King", re.compile(r"\bking\b")),
    ("Queen", re.compile(r"\bqueen\b")),
    ("Matrimonial", re.compile(r"\bmatrimonial\b|\bfull\s*size\b|\bcama\s*full\b")),
    ("Individual", re.compile(r"\bindividual\b|\btwin\b")),
)


def bed_size_of(name):
    """Medida de cama, o None si el nombre no la dice o dice más de una.

    Un anuncio que menciona DOS medidas ("disponible en individual y
    matrimonial", o un paquete) no se clasifica: elegir una sería inventar
    cuál se está vendiendo. "California King" contiene "King", y eso no es
    ambigüedad -- es la medida más específica, que gana por ir primero.
    """
    n = _norm(name)
    hits = [label for label, rx in _BED_SIZE_PATTERNS if rx.search(n)]
    if not hits:
        return None
    if len(hits) > 1:
        # Único solapamiento legítimo: "California King" dispara también
        # "King". Cualquier otro par son dos medidas distintas de verdad.
        if set(hits) == {"California King", "King"}:
            return "California King"
        return None
    return hits[0]


# ---------------------------------------------------------------------
# Aire acondicionado: capacidad de enfriamiento
# ---------------------------------------------------------------------
# La pregunta al comprar un minisplit es cuántos BTU necesita el cuarto, y
# en México se anuncia de dos formas para el MISMO equipo: en BTU ("12,000
# BTU") o en toneladas de refrigeración ("1 Tonelada", "1.5 Ton", "1T").
# La equivalencia no es una estimación nuestra: 1 tonelada de refrigeración
# son 12,000 BTU/h por definición, y las fichas de los fabricantes usan las
# dos etiquetas de forma intercambiable.
#
# Se prefiere el BTU explícito cuando está; la tonelada es el respaldo. Con
# eso la categoría pasa de 24% a 89% de nombres con capacidad legible.
_AC_BTU_RE = re.compile(r"(?<![\d.,])(\d{1,3}(?:[.,\s]\d{3})|\d{4,6})\s*btus?\b")
_AC_TON_RE = re.compile(r"(?<![\d.,])(\d(?:[.,]\d)?)\s*(?:toneladas?\b|tons?\b|t\b)")


def ac_btu(name):
    """Capacidad de enfriamiento en BTU/h, o None.

    Rango 5,000-60,000: por debajo es un ventilador o un accesorio, por
    arriba es equipo industrial que no comparte estante con el minisplit
    de una casa. Dos capacidades distintas en el mismo nombre no se
    resuelven -- elegir una sería inventar cuál se vende.
    """
    n = _norm(name)
    vals = set()
    for m in _AC_BTU_RE.finditer(n):
        try:
            v = int(re.sub(r"[.,\s]", "", m.group(1)))
        except ValueError:
            continue
        if 5000 <= v <= 60000:
            vals.add(v)
    if len(vals) == 1:
        return next(iter(vals))
    if vals:
        return None
    for m in _AC_TON_RE.finditer(n):
        try:
            v = int(float(m.group(1).replace(",", ".")) * 12000)
        except ValueError:
            continue
        if 5000 <= v <= 60000:
            vals.add(v)
    return next(iter(vals)) if len(vals) == 1 else None


# ---------------------------------------------------------------------
# Ventiladores: medida del aspa
# ---------------------------------------------------------------------
# Es la medida con la que se venden y con la que el comprador decide: un
# extractor de baño de 6" y un ventilador de techo de 52" son el mismo
# renglón de catálogo y no se comparan entre sí.
_FAN_IN_RE = re.compile(
    r"(?<![\d./-])(\d{1,2})\s*(?:\"|''|”|″|pulgadas?\b|pulg\.?)")


def fan_size_in(name):
    """Pulgadas de un ventilador, o None. Rango 4-60.

    El guardia de la izquierda descarta las fracciones de ferretería
    ("1-1/4\"" de un anillo de aire), donde el número que precede a las
    comillas es el denominador, no la medida del aspa.
    """
    n = _norm(name)
    vals = set()
    for m in _FAN_IN_RE.finditer(n):
        v = int(m.group(1))
        if 4 <= v <= 60:
            vals.add(v)
    return next(iter(vals)) if len(vals) == 1 else None


# ---------------------------------------------------------------------
# Almacenamiento (SSD, discos duros, USB, microSD): capacidad
# ---------------------------------------------------------------------
# En esta categoría la capacidad ES la compra. Se reusa el lector de
# ram_storage_gb() para las unidades pero NO su heurística de "el mayor de
# dos números es el almacenamiento": acá no hay RAM que separar, hay una
# sola capacidad, y dos capacidades distintas en un nombre son un paquete
# ("SSD 512GB + funda 64GB") que no se clasifica.
_DRIVE_CAP_RE = re.compile(r"(?<![\d.,])(\d{1,5})\s*(gb|tb)\b")


def drive_capacity_gb(name):
    """Capacidad de una unidad de almacenamiento en GB, o None.

    Rango 1 GB - 32 TB: por debajo no existe como producto y por arriba
    es un arreglo de servidor, no un disco de estante.
    """
    n = _norm(name)
    vals = set()
    for m in _DRIVE_CAP_RE.finditer(n):
        v = int(m.group(1))
        if m.group(2) == "tb":
            v *= 1024
        if 1 <= v <= 32768:
            vals.add(v)
    return next(iter(vals)) if len(vals) == 1 else None


# ---------------------------------------------------------------------
# Refacciones: con qué modelo y de qué años es compatible
# ---------------------------------------------------------------------
# La ficha técnica de Elektra trae "Compatibilidad", y en 1,592 de las
# 3,323 refacciones que la declaran viene en un formato legible a máquina:
#
#     • VORT-X 250 2022,2023,2024 • RT200 2020,2021
#
# viñeta, modelo, y los años en que ese modelo lo lleva. Son las dos
# preguntas de la categoría: "¿le queda a mi moto?" y "¿de qué año?".
#
# El resto de los valores NO se toca: 223 dicen "Generico"/"Universal" (no
# es un modelo) y 1,508 son prosa ("Diseñado para usar con aceite Mobil 1",
# "Consulte la descripción para detalles de compatibilidad", "Acura MDX y
# otros SUVs asiáticos"). Sacar un modelo de ahí sería adivinar, y una
# refacción que no le queda al coche es justo el error que no se puede
# cometer.
_COMPAT_RE = re.compile(
    r"•\s*([A-Z0-9][A-Z0-9\- ]*?)\s+((?:\d{4})(?:\s*,\s*\d{4})*)")


def compat_of(text):
    """(modelos, años) de un campo "Compatibilidad", o ([], []).

    Los modelos vienen tal como los escribe la tienda; unificar "DS 150" con
    "DS150" necesita ver el catálogo entero y se hace en compute_facets.py.
    """
    modelos, anios = [], []
    for modelo, años in _COMPAT_RE.findall(text or ""):
        m = re.sub(r"\s+", " ", modelo).strip()
        if m and m not in modelos:
            modelos.append(m)
        for a in re.findall(r"\d{4}", años):
            if 1990 <= int(a) <= 2030 and a not in anios:
                anios.append(a)
    return modelos, sorted(anios)


# ---------------------------------------------------------------------
# Cargadores: de qué tipo es y cuántos watts entrega
# ---------------------------------------------------------------------
# La categoría venía partida en "Cargadores" (391) y "Adaptadores" (69),
# que no ayuda a elegir: un cargador de auto, uno inalámbrico y una
# estación de energía caían todos en el mismo cajón. Lo que separa de
# verdad es DÓNDE se enchufa y para qué, y eso el nombre sí lo dice.
#
# El orden importa y no es alfabético: se pregunta primero por lo más
# específico.
#
# No hay tipo "power bank": una batería externa NO es un cargador y tiene
# su propia categoría, con sus tramos de mAh. classify_cargadores.py las
# saca de acá antes de clasificar el resto.
_CARGADOR_TIPOS = (
    ("Estación de energía", re.compile(r"estacion de energia|power station|generador solar")),
    ("De pilas y baterías", re.compile(r"\bpilas?\b|baterias? recargables?|battery charger|cargador de bateria")),
    ("De auto", re.compile(r"\bauto\b|\bcoche\b|encendedor|vehicul|car charger|manillar|\bmoto\b|\b12v\b")),
    ("Inalámbrico", re.compile(r"inalambric|magsafe|\bqi2?\b|magnetic|induccion")),
    ("Para laptop", re.compile(r"\blaptop\b|\bnotebook\b|macbook")),
    ("Base de carga", re.compile(r"base de carga|base cargadora|\bdock\b|estacion de carga|soporte de carga")),
    # Ojo con "cable": la palabra aparece dos veces más seguido como lo que
    # el cargador TRAE que como lo que el producto ES ("Belkin Cargador
    # Pared 30w Usb-c Con Cable", "Cargador 65w Gan + Cable Usb-c"). Con la
    # palabra suelta, 30 de los 41 productos de esta subcategoría no eran
    # cables sino cargadores -- el Belkin decía "Pared" en el nombre y aun
    # así no aparecía en "De pared". Cuenta solo cuando es el sustantivo del
    # producto, o sea antes de que el nombre empiece a enumerar lo que
    # incluye. Es el mismo criterio de cabeza de nombre que usa
    # clasificar_subcategorias.py con VENTANA_CABEZA.
    ("Cable", re.compile(r"^(?:(?!\b(?:con|sin|incluye|mas|y)\b|\+).)*"
                         r"\b(?:cable|cordon)\b")),
    ("Adaptador de corriente", re.compile(
        r"adaptador de corriente|clavij|\bviaje\b|convertidor|transformador|eliminador|"
        r"fuente de (poder|alimentacion)|power supply|adapter for")),
    # Último y a propósito: un "Cargador USB-C de 65 W con 4 puertos" no
    # dice "pared" en ninguna parte, pero es exactamente eso. Solo llega
    # acá lo que ninguna regla más específica reclamó.
    ("De pared", re.compile(
        r"\bpared\b|\bmuro\b|\bwall\b|enchufe|contacto|tomacorriente|multicontacto|"
        r"usb|\bpd\b|\bgan\b|tipo ?c|type-?c|quick charge|\bqc3|puertos?\b|\bw\b")),
)


def charger_type_of(name):
    """Tipo de cargador según el nombre, o None si no se puede decir."""
    n = _norm(name)
    for etiqueta, rx in _CARGADOR_TIPOS:
        if rx.search(n):
            return etiqueta
    return None


_WATTS_RE = re.compile(r"(?<![\d.,])(\d{1,4}(?:\.\d)?)\s*w\b")


def charger_watts(name):
    """Potencia en watts, o None. Rango 3-3,000: por debajo no existe como
    cargador y por arriba es una estación de energía declarando su
    capacidad de salida, no la carga de un equipo.

    Dos potencias distintas en el mismo nombre ("65W PD, 20W USB-A") no se
    resuelven: cuál es "la" potencia del cargador es justo lo ambiguo.
    """
    n = _norm(name)
    vals = set()
    for m in _WATTS_RE.finditer(n):
        try:
            v = float(m.group(1))
        except ValueError:
            continue
        if 3 <= v <= 3000:
            vals.add(v)
    if len(vals) != 1:
        return None
    v = next(iter(vals))
    return int(v) if v == int(v) else v
