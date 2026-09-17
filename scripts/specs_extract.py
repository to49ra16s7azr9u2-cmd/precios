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
    # 720p y 1280x800 (WXGA) son los proyectores de entrada.
    ("HD", re.compile(r"\bhd\b|\b1366\s*x\s*768\b|\b1280\s*x\s*720\b|\b720p\b|\b1280\s*x\s*800\b|\bwxga\b")),
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
    ("De pilas", re.compile(r"\bpilas?\b|baterias? recargables?|battery charger|cargador de bateria")),
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


# Lo que va después de "compatible con" es con qué FUNCIONA el producto, no
# lo que ES. Sin recortarlo, un "CUKTECH Cargador GAN USB C 100W, Cargador de
# Pared de 3 Puertos ... Compatible con MacBook Pro, iPhone 17/16/15" salía
# como "Para laptop" por la palabra MacBook, cuando el propio nombre dice
# "de Pared" dos veces. Se corta solo en "compatible con/para" y no en el
# "para" suelto, que muchas veces sí dice qué es el producto ("Cargador para
# laptop"). Sobre los cargadores que ya hay en el catálogo no cambia ni uno:
# es para los que entren de acá en adelante.
_COMPATIBILIDAD = re.compile(r"\b(?:compatible|compatibles|apto|apta|aptos|aptas)\s+(?:con|para)\b")


def charger_type_of(name):
    """Tipo de cargador según el nombre, o None si no se puede decir."""
    n = _COMPATIBILIDAD.split(_norm(name), 1)[0]
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


# ---------- Hogar: electrodomésticos, bocinas, audífonos, muebles ----------
#
# Mismo criterio que el resto del archivo: cada función lee UN dato que la
# tienda escribió (en el nombre o en el valor de una spec) y devuelve None
# cuando el texto no lo dice o lo dice dos veces distinto. El rango
# plausible lo pone quien llama, porque "1500 W" es normal en un calefactor
# y absurdo en una bocina de escritorio.

# "1,200 W", "1.200 W" (separador de miles) y "800 watts"/"1000 vatios".
_HOME_WATTS_RE = re.compile(
    r"(?<![\d.,])(\d{1,2}[.,]\d{3}|\d{1,5}(?:\.\d)?)\s*(?:w\b|watts?\b|vatios\b)"
)


def power_watts(text, lo, hi):
    """Potencia en watts dentro de [lo, hi], o None. Dos potencias
    distintas en el mismo texto ("motor 1200 W, calentador 800 W") no se
    resuelven."""
    n = _norm(text or "")
    vals = set()
    for m in _HOME_WATTS_RE.finditer(n):
        raw = m.group(1)
        if re.fullmatch(r"\d{1,2}[.,]\d{3}", raw):
            raw = raw.replace(".", "").replace(",", "")
        try:
            v = float(raw)
        except ValueError:
            continue
        if lo <= v <= hi:
            vals.add(v)
    if len(vals) != 1:
        return None
    v = next(iter(vals))
    return int(v) if v == int(v) else v


# "6 L", "7.5 lts", "1,5 litros". Excluye "L/min" (caudal de un calentador
# de paso) y "105 L x 75 Al" (el largo de un mueble).
_LITERS_RE = re.compile(
    r"(?<![\d.,])(\d{1,3}(?:[.,]\d{1,2})?)\s*(?:l\b|lts?\b|litros?\b)(?!\s*/|\s*x\b)"
)
_QUARTS_RE = re.compile(r"(?<![\d.,])(\d{1,2}(?:[.,]\d{1,2})?)\s*(?:qt\b|quarts?\b|cuartos?\b)")
_CUBIC_FT_RE = re.compile(r"(?<![\d.,])(\d(?:[.,]\d{1,2})?)\s*(?:pies|ft|cu\s?ft|p3|cuft)")


def liters_of(text, lo, hi, quarts=False, cubic_feet=False):
    """Capacidad en litros dentro de [lo, hi], o None. Con quarts=True
    acepta "6 cuartos"/"8qt" (freidoras de aire, 0.946 L cada uno) y con
    cubic_feet=True "1.1 pies cúbicos" (microondas, 28.3 L cada uno)."""
    n = _norm(text or "").replace(",", ".")
    vals = set()
    for m in _LITERS_RE.finditer(n):
        vals.add(float(m.group(1)))
    if not vals and quarts:
        for m in _QUARTS_RE.finditer(n):
            vals.add(round(float(m.group(1)) * 0.946, 1))
    if not vals and cubic_feet:
        for m in _CUBIC_FT_RE.finditer(n):
            vals.add(round(float(m.group(1)) * 28.3))
    vals = {v for v in vals if lo <= v <= hi}
    if len(vals) != 1:
        return None
    v = next(iter(vals))
    return int(v) if v == int(v) else v


_CUPS_RE = re.compile(r"(?<![\d.,])(\d{1,3})\s*(?:tazas?\b|tz\b)")


def cups_of(text):
    """Tazas de una cafetera (1-200), o None."""
    n = _norm(text or "")
    vals = {int(m.group(1)) for m in _CUPS_RE.finditer(n)}
    vals = {v for v in vals if 1 <= v <= 200}
    return next(iter(vals)) if len(vals) == 1 else None


_SERVICES_RE = re.compile(r"(?<![\d.,])(\d{1,2}(?:[.,]5)?)\s*servicios?\b")


def services_of(text, lo, hi):
    """Servicios (regaderas de un calentador, cubiertos de un
    lavavajillas). Acepta el número solo, como lo escribe la ficha ("1.5"),
    o "2 servicios" dentro del nombre."""
    n = _norm(text or "").strip().replace(",", ".")
    if re.fullmatch(r"\d{1,2}(?:\.\d)?", n):
        vals = {float(n)}
    else:
        vals = {float(m.group(1)) for m in _SERVICES_RE.finditer(n)}
    vals = {v for v in vals if lo <= v <= hi}
    if len(vals) != 1:
        return None
    v = next(iter(vals))
    return int(v) if v == int(v) else v


# "20 horas", "24h", "6.5 hrs". "60 Hz" y "2.4 GHz" no entran: la h no
# termina palabra.
_HOURS_RE = re.compile(r"(?<![\d.,])(\d{1,3}(?:[.,]\d)?)\s*(?:h\b|hrs?\b|horas?\b)")


def battery_hours_of(text):
    """Horas de batería (1-150), o None. Dos cifras distintas ("8 h con
    ANC, 12 h sin") no se resuelven."""
    n = _norm(text or "").replace(",", ".")
    vals = {float(m.group(1)) for m in _HOURS_RE.finditer(n)}
    vals = {v for v in vals if 1 <= v <= 150}
    if len(vals) != 1:
        return None
    v = next(iter(vals))
    return int(v) if v == int(v) else v


_CM_RE = re.compile(r"(?<![\d.,])(\d{2,3})\s*cms?\b")
_INCH_RE = re.compile(r"(?<![\d.,])(\d{2}(?:\.\d)?)\s*(?:\"|''|pulgadas|pulg\b|in\b)")


_HOOD_LARGO_RE = re.compile(r"largo:\s*(\d{2}(?:\.\d)?)")


def hood_width_cm(text):
    """Ancho de una campana de cocina en cm (40-150), o None. La ficha lo da
    a veces en pulgadas: "30" a secas, o 'Alto:19.6", Largo:29.9", ...'
    donde el ancho de la campana es el "Largo"; 76 cm es una de 30"."""
    n = _norm(text or "").strip()
    if re.fullmatch(r"\d{2}(?:\.\d{1,2})?", n):
        vals = {round(float(n) * 2.54)}
    elif _HOOD_LARGO_RE.search(n):
        vals = {round(float(_HOOD_LARGO_RE.search(n).group(1)) * 2.54)}
    else:
        vals = {int(m.group(1)) for m in _CM_RE.finditer(n)}
        if not vals:
            vals = {round(float(m.group(1)) * 2.54) for m in _INCH_RE.finditer(n)}
    vals = {v for v in vals if 40 <= v <= 150}
    return next(iter(vals)) if len(vals) == 1 else None


# El orden importa: "silla gamer de oficina" es gamer, "silla plegable de
# camping" es plegable. Comedor y oficina van al final porque son las
# palabras que más se cuelan en nombres de otros tipos.
_CHAIR_TYPES = (
    ("Gamer", re.compile(r"\bgamer\b|\bgaming\b|videojuegos")),
    ("Mecedora", re.compile(r"mecedora")),
    ("Alta / bar", re.compile(r"\bbar\b|periquera|\bbanco alto\b")),
    ("Plegable", re.compile(r"\bplegable\b|\bcamping\b|\bplaya\b")),
    ("Sillón", re.compile(r"\bsillon\b|reclinable|\bpuff\b")),
    ("Comedor", re.compile(r"\bcomedor\b")),
    ("Oficina", re.compile(r"\boficina\b|ejecutiv|ergonomic|\bescritorio\b|multipostura")),
)


def chair_type_of(name):
    """Tipo de silla según el nombre, o None si no dice ninguno."""
    n = _norm(name or "")
    for label, rx in _CHAIR_TYPES:
        if rx.search(n):
            return label
    return None


_MULTI_RE = re.compile(
    r"multifuncional|todo en uno|all[- ]in[- ]one|escanea|imprime.{0,15}copia|"
    r"\b3 en 1\b|copiadora|\bmfp\b|\bmfc\b|\bdcp\b"
)


def multifunction_of(name, scans_spec=None):
    """"Multifuncional" si imprime, copia y escanea; "Solo impresión" si la
    ficha dice que no escanea; None si no se sabe."""
    if _MULTI_RE.search(_norm(name or "")):
        return "Multifuncional"
    v = _norm(scans_spec or "").strip()
    if re.match(r"s[i]\b", v):
        return "Multifuncional"
    if re.match(r"no\b", v) and not re.match(r"no (especificado|aplica)", v):
        return "Solo impresión"
    return None


# ---------------------------------------------------------------------
# Genéricos: el dato que decide la compra en las categorías que no tenían
# ninguno (juguetes, herramientas, maletas, mascotas, deportes...). Cada
# función lee UN dato de un texto -- el valor de una spec o el nombre -- y
# devuelve None si no está o está dos veces distinto. El rango plausible lo
# pone quien llama, igual que en el resto del archivo: 20 kg es una
# mancuerna y 150 kg es lo que aguanta una silla.
# ---------------------------------------------------------------------
def _uno(vals):
    """El único valor del conjunto, entero si lo es; None si hay cero o
    varios distintos."""
    if len(vals) != 1:
        return None
    v = next(iter(vals))
    return int(v) if isinstance(v, float) and v == int(v) else v


def _num(s):
    return float(s.replace(",", "."))


_KG_RE = re.compile(r"(?<![\d.,])(\d{1,4}(?:[.,]\d{1,2})?)\s*(kg|kgs|kilos?|kilogramos?|lbs?|libras?)\b")


def kg_of(text, lo, hi):
    """Kilos dentro de [lo, hi]; las libras se convierten (0.4536)."""
    vals = set()
    for m in _KG_RE.finditer(_norm(text or "")):
        v = _num(m.group(1))
        if m.group(2).startswith("l"):
            v = round(v * 0.4536, 1)
        if lo <= v <= hi:
            vals.add(v)
    return _uno(vals)


_VOLT_RE = re.compile(r"(?<![\d.,])(\d{1,3}(?:[.,]\d)?)\s*v(?:olts?|oltios)?\b")


def volts_of(text, lo, hi):
    vals = {_num(m.group(1)) for m in _VOLT_RE.finditer(_norm(text or ""))}
    return _uno({v for v in vals if lo <= v <= hi})


_INCHES_RE = re.compile(r"(?<![\d.,])(\d{1,3}(?:[.,]\d)?)\s*(?:\"|''|”|″|pulgadas?\b|pulg\b|in\b)")


def inches_of(text, lo, hi):
    vals = {_num(m.group(1)) for m in _INCHES_RE.finditer(_norm(text or ""))}
    return _uno({v for v in vals if lo <= v <= hi})


_TALLAS = (
    (re.compile(r"\b(xxl|2xl|3xl|xxg|extra extra grande)\b"), "Extra grande"),
    (re.compile(r"\b(xl|xg|extra grande|x-large|xlarge)\b"), "Extra grande"),
    (re.compile(r"\b(xs|xch|extra chica|x-small)\b"), "Chica"),
    (re.compile(r"\b(l|g|grande|large)\b"), "Grande"),
    (re.compile(r"\b(m|med|mediana|mediano|medium)\b"), "Mediana"),
    (re.compile(r"\b(s|ch|chica|chico|pequena|pequeno|small)\b"), "Chica"),
)


def size_label_of(text, bare=False):
    """Talla normalizada a Chica/Mediana/Grande/Extra grande. En un nombre
    la letra suelta ("L") es un modelo con la misma frecuencia que una
    talla, así que ahí se exige la palabra "talla" delante; en el valor de
    una spec (bare=True) la letra sola vale."""
    n = _norm(text or "")
    if not bare:
        m = re.search(r"\btalla\s+([a-z\- ]{1,20})", n)
        if not m:
            return None
        n = m.group(1)
    hits = {lbl for rx, lbl in _TALLAS if rx.search(n)}
    return next(iter(hits)) if len(hits) == 1 else None


_DIM_RE = re.compile(r"^\s*(\d{1,4}(?:[.,]\d{1,3})?)\s*(mm|cm|m)\b")


def first_dimension_cm(text, lo, hi):
    """El primer número de "1.2 m x 0.6 m x 0.75 m" (el largo, L), en cm."""
    m = _DIM_RE.match(_norm(text or ""))
    if not m:
        return None
    v = _num(m.group(1))
    v = v * 100 if m.group(2) == "m" else v / 10 if m.group(2) == "mm" else v
    v = round(v)
    return v if lo <= v <= hi else None


_LEN_CM_RE = re.compile(r"(?<![\d.,])(\d{1,3}(?:[.,]\d)?)\s*cm\b")
_DIMS_X_RE = re.compile(r"(\d{1,3}(?:[.,]\d)?)\s*(?:x|\*)\s*(\d{1,3}(?:[.,]\d)?)(?:\s*(?:x|\*)\s*(\d{1,3}(?:[.,]\d)?))?\s*cm\b")


def length_cm_of(text, lo, hi):
    """Tamaño en cm de un peluche o una figura. Con medidas "30 x 20 cm"
    se queda la mayor, que es la que se ve."""
    n = _norm(text or "")
    m = _DIMS_X_RE.search(n)
    if m:
        v = max(_num(g) for g in m.groups() if g)
        return v if lo <= v <= hi else None
    vals = {_num(m.group(1)) for m in _LEN_CM_RE.finditer(n)}
    return _uno({v for v in vals if lo <= v <= hi})


def water_resistant_of(text):
    n = _norm(text or "").strip()
    if not n:
        return None
    if re.search(r"\bip[x]?\d|\d\s*atm\b|\d+\s*m(etros)?\b|\bwater ?proof\b|\bresistente\b(?!.*\bno\b)|^si\b|^s[ií]$|\bsumergible\b", n) \
            and not re.match(r"^no\b", n):
        return "Sí"
    if re.match(r"^(no|non|n/a|ninguna)\b", n):
        return "No"
    return None


def breed_size_of(text):
    n = _norm(text or "")
    if re.search(r"todas|todos|cualquier", n):
        return "Todas las razas"
    hits = set()
    if re.search(r"\b(chic[oa]|pequen[oa]|mini|toy|small)\b", n): hits.add("Chica")
    if re.search(r"\b(median[oa]|medium)\b", n): hits.add("Mediana")
    if re.search(r"\b(grande|large|gigante)\b", n): hits.add("Grande")
    return next(iter(hits)) if len(hits) == 1 else None


def pet_stage_of(text):
    n = _norm(text or "")
    cach = bool(re.search(r"cachorr|puppy|kitten|gatito", n))
    adul = bool(re.search(r"adult", n))
    sen = bool(re.search(r"senior|mayor|viej", n))
    if re.search(r"todas|todos|cualquier|1-10", n) or sum([cach, adul, sen]) > 1:
        return "Todas las etapas"
    if cach: return "Cachorro"
    if adul: return "Adulto"
    if sen: return "Senior"
    return None


def thread_count_of(text):
    n = _norm(text or "")
    vals = {int(m.group(1)) for m in re.finditer(r"(?<!\d)(\d{2,4})(?!\d)", n)}
    return _uno({v for v in vals if 50 <= v <= 2000})


def speeds_of(text):
    n = _norm(text or "").strip()
    vals = {int(m.group(1)) for m in re.finditer(r"(?<!\d)(\d{1,2})(?!\d)", n)}
    return _uno({v for v in vals if 1 <= v <= 40})


_PLATAFORMAS_SPEC = (
    (re.compile(r"switch\s*2"), "Nintendo Switch 2"),
    (re.compile(r"switch"), "Nintendo Switch"),
    (re.compile(r"ps\s*5|playstation\s*5"), "PlayStation 5"),
    (re.compile(r"ps\s*4|playstation\s*4"), "PlayStation 4"),
    (re.compile(r"series\s*[xs]"), "Xbox Series X|S"),
    (re.compile(r"xbox\s*one"), "Xbox One"),
)


def platform_spec_of(text):
    """La consola tal como la escribe la ficha; "Xbox" a secas no dice
    cuál y se descarta."""
    n = _norm(text or "")
    for rx, lbl in _PLATAFORMAS_SPEC:
        if rx.search(n):
            return lbl
    return None


_MATERIALES = (
    (re.compile(r"chapa|banado|gold ?filled|plated"), "Chapa de oro"),
    (re.compile(r"\boro\b|\bgold\b|\b1[048]\s?k\b|\b14k\b"), "Oro"),
    (re.compile(r"\bplata\b|\bsilver\b|s925|\b925\b"), "Plata"),
    (re.compile(r"acero inox|inoxidable|stainless"), "Acero inoxidable"),
    (re.compile(r"\bacero\b"), "Acero"),
    (re.compile(r"\bmdp\b|\bmdf\b|aglomerad|melamin|particula"), "Aglomerado (MDF/MDP)"),
    (re.compile(r"madera|\bpino\b|caoba|roble|nogal|bambu|ratan|mimbre"), "Madera"),
    (re.compile(r"piel sintetica|vinipiel|sintetic|\bpu\b|polipiel|imitacion piel"), "Piel sintética"),
    (re.compile(r"\bpiel\b|\bcuero\b|\bleather\b"), "Piel"),
    (re.compile(r"microfibra"), "Microfibra"),
    (re.compile(r"algodon.*(poliester|polyester)|(poliester|polyester).*algodon"), "Algodón y poliéster"),
    (re.compile(r"algodon|cotton"), "Algodón"),
    (re.compile(r"poliester|polyester|nylon|nailon|lycra|spandex"), "Poliéster"),
    (re.compile(r"\btela\b|lino\b|terciopelo|velvet|tejid"), "Tela"),
    (re.compile(r"aluminio"), "Aluminio"),
    (re.compile(r"vidrio|cristal|glass"), "Vidrio"),
    (re.compile(r"ceramic|porcelana"), "Cerámica"),
    (re.compile(r"silicon"), "Silicona"),
    (re.compile(r"plastic|\babs\b|polipropileno|\bpvc\b|polietileno|\bpp\b|resina"), "Plástico"),
    (re.compile(r"\bmetal|hierro|zinc|laton|latón|bronce|cobre|aleacion"), "Metal"),
)


def material_of(text):
    """El material principal, normalizado a una lista corta. El primero
    que engancha manda: "latón en chapa de oro" es chapa, no latón."""
    n = _norm(text or "")
    if not n or re.match(r"^(no aplica|n/a|no|0|-|\.)$", n.strip()):
        return None
    for rx, lbl in _MATERIALES:
        if rx.search(n):
            return lbl
    return None


def stone_of(text):
    n = _norm(text or "").strip()
    if not n:
        return None
    if re.search(r"zircon|circon|\bcz\b", n): return "Zirconia"
    if re.search(r"diamant", n): return "Diamante"
    if re.search(r"moissan", n): return "Moissanita"
    if re.search(r"perla", n): return "Perla"
    if re.search(r"cristal|swarov", n): return "Cristal"
    if re.search(r"^(0|no|ninguna|sin piedra|no tiene|no contiene|no aplica|n/a)\b", n): return "Sin piedra"
    return None


_MP_RE = re.compile(r"(?<![\d.,])(\d{1,3}(?:\.\d)?)\s*(?:mp\b|megapix)")


def megapixels_of(text, lo, hi):
    n = _norm(text or "").strip()
    vals = {_num(m.group(1)) for m in _MP_RE.finditer(n)}
    if not vals and re.fullmatch(r"\d{1,3}(?:\.\d)?", n):
        vals = {_num(n)}
    return _uno({v for v in vals if lo <= v <= hi})


_BALL_RE = re.compile(r"(?:\bno\.?\s*|#\s*|\bnumero\s*|\bn°\s*|\bnum\.?\s*)([3-7])\b")


def ball_number_of(text):
    vals = {int(m.group(1)) for m in _BALL_RE.finditer(_norm(text or ""))}
    return _uno(vals)


_PIECES_RE = re.compile(r"(?<![\d.,])(\d{1,3}(?:[.,]\d{3})|\d{1,5})\s*(?:piezas?\b|pzas?\b|pzs?\b|pcs\b|pieces?\b|pc\b)")


def pieces_of(text, lo, hi):
    vals = set()
    for m in _PIECES_RE.finditer(_norm(text or "")):
        raw = m.group(1)
        v = int(raw.replace(".", "").replace(",", ""))
        if lo <= v <= hi:
            vals.add(v)
    return _uno(vals)


_ML_RE = re.compile(r"(?<![\d.,])(\d{1,4}(?:[.,]\d)?)\s*(?:ml\b|mililitros?\b)")


def ml_of(text, lo, hi):
    vals = {_num(m.group(1)) for m in _ML_RE.finditer(_norm(text or ""))}
    return _uno({v for v in vals if lo <= v <= hi})


_KM_RE = re.compile(r"(?<![\d.,])(\d{2,3})\s*km\b(?!\s*/?\s*h)")


def range_km_of(text, lo, hi):
    """Autonomía en km. "50 km/h" es velocidad y no entra."""
    vals = {int(m.group(1)) for m in _KM_RE.finditer(_norm(text or ""))}
    return _uno({v for v in vals if lo <= v <= hi})


_CC_RE = re.compile(r"(?<![\d.,])(\d{2,4})\s*cc\b")


def engine_cc_of(text, lo, hi):
    vals = {int(m.group(1)) for m in _CC_RE.finditer(_norm(text or ""))}
    return _uno({v for v in vals if lo <= v <= hi})


_MAH_RE = re.compile(r"(?<![\d.,])(\d{1,3}(?:[.,]\d{3})|\d{3,6})\s*mah\b")


def mah_of(text, lo, hi):
    vals = set()
    for m in _MAH_RE.finditer(_norm(text or "")):
        v = int(m.group(1).replace(".", "").replace(",", ""))
        if lo <= v <= hi:
            vals.add(v)
    return _uno(vals)


def age_years_of(text):
    """Edad mínima en años a partir de "3 años en adelante", "14+", "8 años
    y más", "0-1 año", "Bebé", "Adulto". "Niños" a secas no dice cuántos."""
    n = _norm(text or "").strip()
    if not n or re.match(r"^(n/a|no aplica|-)$", n):
        return None
    if re.search(r"\bbebe|\bmeses\b|recien nacid|0\s*(-|a)\s*\d|^0\b", n):
        return 0
    if re.search(r"adult|\b1[8-9]\+|\b18\b", n):
        return 18
    if re.search(r"todas las edades|todo publico|todas", n):
        return 0
    m = re.search(r"(\d{1,2})\s*(\+|anos|ano\b|years|y mas|mas|en adelante|-|a\b)", n)
    if not m:
        m = re.search(r"^\+?(\d{1,2})$", n)
    if not m:
        return None
    v = int(m.group(1))
    return v if 0 <= v <= 18 else None


def players_max_of(text):
    """Jugadores que caben: el máximo cuando hay rango ("2 a 4" -> 4), 99
    cuando la ficha deja el tope abierto ("2 o más", "Varios")."""
    n = _norm(text or "").strip()
    if not n or re.match(r"^(n/a|no aplica|-|0)$", n):
        return None
    nums = [int(x) for x in re.findall(r"\d{1,2}", n)]
    abierto = bool(re.search(r"\+|o mas|en adelante|varios|multijugador|ilimitad", n))
    if abierto:
        return 99
    nums = [x for x in nums if 1 <= x <= 30]
    return max(nums) if nums else None


# Más genéricos, para las subcategorías que quedaban sin un solo dato.
_GB_RE = re.compile(r"(?<![\d.,])(\d{1,4})\s*gb\b")


def gb_of(text, lo, hi):
    """Gigabytes sueltos ("16GB DDR5"). Un kit "2x16GB" trae dos cifras y
    no se resuelve."""
    vals = {int(m.group(1)) for m in _GB_RE.finditer(_norm(text or ""))}
    return _uno({v for v in vals if lo <= v <= hi})


_OZ_RE = re.compile(r"(?<![\d.,])(\d{1,2})\s*oz\b")


def oz_of(text, lo, hi):
    vals = {int(m.group(1)) for m in _OZ_RE.finditer(_norm(text or ""))}
    return _uno({v for v in vals if lo <= v <= hi})


_MM_RE = re.compile(r"(?<![\d.,])(\d{1,3}(?:[.,]\d)?)\s*mm\b")


def mm_of(text, lo, hi):
    vals = {_num(m.group(1)) for m in _MM_RE.finditer(_norm(text or ""))}
    return _uno({v for v in vals if lo <= v <= hi})


_FOCAL_RE = re.compile(r"(?<![\d.,])(\d{1,3})(?:\s*-\s*(\d{1,3}))?\s*mm\b")


def focal_mm_of(text):
    """Distancia focal de un lente: el primer número de "18-55mm" (el gran
    angular es lo que se elige) o el único de "50mm". Rango 8-800."""
    n = _norm(text or "")
    vals = set()
    for m in _FOCAL_RE.finditer(n):
        v = int(m.group(1))
        if 8 <= v <= 800:
            vals.add(v)
    return _uno(vals)


_FILAMENTOS = (
    (re.compile(r"\bpla\s*\+|\bpla\+"), "PLA+"),
    (re.compile(r"\bpla\b"), "PLA"),
    (re.compile(r"\bpetg\b"), "PETG"),
    (re.compile(r"\babs\b"), "ABS"),
    (re.compile(r"\btpu\b"), "TPU"),
    (re.compile(r"\basa\b"), "ASA"),
    (re.compile(r"\bnylon\b|\bnailon\b"), "Nylon"),
)


def filament_of(text):
    n = _norm(text or "")
    hits = {lbl for rx, lbl in _FILAMENTOS if rx.search(n)}
    hits.discard("PLA") if "PLA+" in hits else None
    return next(iter(hits)) if len(hits) == 1 else None


_PORTS_RE = re.compile(r"(?<![\d.,])(\d{1,2})\s*(?:puertos?|ports?|bocas)\b")


def ports_of(text):
    vals = {int(m.group(1)) for m in _PORTS_RE.finditer(_norm(text or ""))}
    return _uno({v for v in vals if 2 <= v <= 64})


_WIFI_STD = (
    (re.compile(r"wi-?fi\s*7\b|\bbe\d{3,5}\b|802\.11be"), "Wi-Fi 7"),
    (re.compile(r"wi-?fi\s*6e\b|\baxe\d{3,5}\b"), "Wi-Fi 6E"),
    (re.compile(r"wi-?fi\s*6\b|\bax\d{3,5}\b|802\.11ax"), "Wi-Fi 6"),
    (re.compile(r"wi-?fi\s*5\b|\bac\d{3,4}\b|802\.11ac"), "Wi-Fi 5"),
    (re.compile(r"wi-?fi\s*4\b|\bn\d{3}\b|802\.11n"), "Wi-Fi 4"),
)


def wifi_std_of(text):
    """Generación de Wi-Fi por su nombre (Wi-Fi 6) o por la clase de
    velocidad (AX3000 es Wi-Fi 6, AC1200 es Wi-Fi 5)."""
    n = _norm(text or "")
    for rx, lbl in _WIFI_STD:
        if rx.search(n):
            return lbl
    return None


_DPI_RE = re.compile(r"(?<![\d.,])(\d{1,3}(?:[.,]\d{3})|\d{3,6})\s*dpi\b")


def dpi_of(text):
    vals = set()
    for m in _DPI_RE.finditer(_norm(text or "")):
        v = int(m.group(1).replace(".", "").replace(",", ""))
        if 400 <= v <= 60000:
            vals.add(v)
    return _uno(vals)


_METERS_RE = re.compile(r"(?<![\d.,])(\d{1,2}(?:[.,]\d)?)\s*(?:m\b(?!m)|metros?\b|mts?\b)")


def meters_of(text, lo, hi):
    vals = {_num(m.group(1)) for m in _METERS_RE.finditer(_norm(text or ""))}
    return _uno({v for v in vals if lo <= v <= hi})


_LUMENS_RE = re.compile(r"(?<![\d.,])(\d{1,3}(?:[.,]\d{3})|\d{2,6})\s*(?:lm\b|lumen(?:es)?\b)")


def lumens_of(text, lo, hi):
    vals = set()
    for m in _LUMENS_RE.finditer(_norm(text or "")):
        v = int(m.group(1).replace(".", "").replace(",", ""))
        if lo <= v <= hi:
            vals.add(v)
    return _uno(vals)


_AH_RE = re.compile(r"(?<![\d.,])(\d{1,3}(?:[.,]\d{1,2})?)\s*ah\b")


def ah_of(text, lo, hi):
    """Amperes-hora de una batería ("48V 20Ah", "12V 7Ah")."""
    vals = {_num(m.group(1)) for m in _AH_RE.finditer(_norm(text or ""))}
    return _uno({v for v in vals if lo <= v <= hi})


def kind_of(text, tabla):
    """El tipo de producto según una tabla [(etiqueta, regex)] aplicada al
    nombre normalizado: la primera fila que casa gana, así que la tabla va
    de lo más específico (el accesorio) a lo general (el instrumento)."""
    n = _norm(text or "")
    for etiqueta, rx in tabla:
        if rx.search(n):
            return etiqueta
    return None
