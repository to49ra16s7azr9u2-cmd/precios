#!/usr/bin/env python3
"""Firma estructurada de un celular a partir de su nombre.

La idea: dos fichas son el MISMO producto solo si coinciden en TODOS los
atributos que distinguen una variante de otra -- marca, línea/modelo,
almacenamiento, RAM, color, compañía y si trae regalo/combo. Si alguno de
esos atributos NO se puede leer del nombre, la firma queda incompleta y la
ficha NO se fusiona con nadie: no se puede confirmar que sea la misma
variante, y ese es exactamente el error que hay que evitar.
"""
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from match_amazon_capture import color_of  # noqa: E402  -- canoniza sinónimos de color


def _norm(s):
    s = unicodedata.normalize("NFD", (s or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()


# ---- compañía -------------------------------------------------------
CARRIERS = (
    ("att", r"\bat&t\b|\batt\b"),
    ("telcel", r"\btelcel\b"),
    ("movistar", r"\bmovistar\b"),
    ("unefon", r"\bunefon\b"),
    ("libre", r"\blibre\b|\bdesbloqueado\b|\bdesbloqueada\b|\bunlocked\b"),
)


def carrier_of(name):
    n = _norm(name)
    for key, rx in CARRIERS:
        if re.search(rx, n):
            return key
    return None  # no declarado


# ---- regalo / combo -------------------------------------------------
# El REGALO concreto importa, no solo que haya regalo: Elektra publica el
# mismo teléfono "con Audífonos y Bocina" y "con Audífonos y Smartwatch"
# como dos productos con precios distintos. Con un bool los agrupaba a los
# dos (se vio en 7 grupos de la primera prueba), así que se compara el
# CONJUNTO de accesorios mencionados.
GIFT_WORDS = (
    ("audifonos", r"aud[ií]fonos|earbuds|\bbuds\b"),
    ("smartwatch", r"smartwatch|\bwatch\b|reloj"),
    ("bocina", r"bocina|speaker|sound"),
    ("adaptador", r"adaptador"),
    ("protector", r"protector|mica|funda|case"),
    ("powerbank", r"power ?bank|bater[ií]a externa|xpocket|pocket"),
    ("juegos", r"\bjuegos\b"),
)
BUNDLE_RE = re.compile(
    r"\bcombo\b|\bbundle\b|\bde regalo\b|\bcon aud[ií]fonos\b|\bcon smartwatch\b|"
    r"\bmas \d+ juegos\b|\+",
    re.IGNORECASE,
)


def bundle_of(name):
    """Conjunto (ordenado) de accesorios de regalo; () si no trae ninguno.

    Incluye los colores que aparecen DESPUÉS del primer accesorio: el mismo
    teléfono "con Smartwatch Filwans GTR Plata" y "... GTR Negro" son dos
    publicaciones distintas (el regalo no es el mismo) y sin esto quedaban
    en el mismo grupo, porque el color que lee color_of() es el del
    teléfono (el primero del nombre), no el del accesorio.
    """
    n = _norm(name)
    hits = [(m.start(), k) for k, rx in GIFT_WORDS
            for m in [re.search(rx, n)] if m]
    gifts = tuple(sorted(k for _, k in hits))
    if gifts:
        first = min(pos for pos, _ in hits)
        tail_colors = tuple(sorted({
            c for c in re.findall(r"[a-z]+", n[first:]) if color_of(c)
        }))
        return gifts + tail_colors
    # "Combo"/"Bundle" sin decir qué trae: se marca aparte, no como "sin regalo"
    if re.search(r"\bcombo\b|\bbundle\b|\bde regalo\b", n):
        return ("_sin_detallar",)
    return ()


# ---- eSIM / SIM física ----------------------------------------------
# Un iPhone "sólo eSIM" es un SKU distinto del que trae bandeja de SIM
# (Apple los vende por separado y el catálogo los distingue en el nombre).
# Sin esto se fusionaban ~20 pares "X" con "X - Sólo eSIM".
ESIM_RE = re.compile(r"s[oó]lo\s*e-?sim|\be-?sim\b", re.IGNORECASE)


def esim_of(name):
    return bool(ESIM_RE.search(_norm(name)))


# ---- red 4G / 5G ----------------------------------------------------
# El Galaxy A17 existe en versión 4G y 5G: son equipos distintos con
# precio distinto. Si el nombre no lo declara, queda en None y no se
# fusiona con ninguno de los dos (no se puede confirmar cuál es).
def network_of(name):
    n = _norm(name)
    has5 = bool(re.search(r"\b5\s?g\b", n))
    has4 = bool(re.search(r"\b4\s?g\b|\blte\b", n))
    if has5 and not has4:
        return "5g"
    if has4 and not has5:
        return "4g"
    if has5 and has4:
        return "5g"  # "4G LTE / 5G" -> es 5G
    return None


# ---- condición ------------------------------------------------------
def condition_of(name):
    n = _norm(name)
    if re.search(r"reacondicionado premium|premium reacondicionado", n):
        return "reacond_premium"
    if re.search(r"reacondicionad|renovad|restaurad|seminuevo|refurbish|\brfb\b", n):
        return "reacond"
    m = re.search(r"\bgrado\s*(a\+|a|b|c)\b", n)
    if m:
        return "grado_" + m.group(1)
    return "nuevo"


# ---- almacenamiento y RAM -------------------------------------------
_REAL_CAPS = {16, 32, 64, 128, 256, 512, 1024, 2048}
# "8+256GB", "8GB RAM 256GB", "256gb 8gb ram", "12GB+512GB", "4+64GB"
def _caps(name):
    n = _norm(name).replace("+", " + ")
    out = []
    # Varias fichas escriben la capacidad sin la "B": "12+256G", "8G RAM+256G
    # ROM", "Galaxy S25 Ultra 256G". Solo se aceptan valores que son
    # capacidades reales (potencias de dos): "5G"/"4G" son la RED, y
    # "Snapdragon 778G"/"782G" son el PROCESADOR -- con un piso numérico
    # simple, esos chips entraban como "778 GB" y cambiaban la capacidad de
    # 26 fichas de Sunsky.
    n = re.sub(r"\b(\d{2,})\s*g\b(?!b)", lambda m: m.group(1) + "gb"
               if int(m.group(1)) in _REAL_CAPS else m.group(0), n)
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(gb|tb)\b", n):
        num = float(m.group(1))
        if m.group(2) == "tb":
            num *= 1024
        out.append((int(num), m.start()))
    return out, n


RAM_HINT = re.compile(r"\bram\b")


def storage_ram_of(name):
    """Devuelve (almacenamiento_gb, ram_gb). Cualquiera puede ser None.

    Regla simple y robusta contra los formatos que aparecen de verdad:
    de todos los números "NgB" del nombre, el MAYOR es el almacenamiento y
    el MENOR la RAM (una RAM nunca supera al almacenamiento en estos
    equipos). Con un solo número, es almacenamiento salvo que la palabra
    "ram" esté pegada a él.
    """
    caps, n = _caps(name)
    if not caps:
        return None, None
    nums = sorted({c[0] for c in caps})
    if len(nums) == 1:
        val = nums[0]
        # "8GB RAM" a secas -> es RAM, no almacenamiento
        pos = caps[0][1]
        tail = n[pos:pos + 20]
        if RAM_HINT.search(tail):
            return None, val
        return val, None
    # "16GB: 8GB+8GB" (RAM extendida) y similares: el mayor manda como ROM
    return max(nums), min(nums)


# ---- marca / modelo -------------------------------------------------
FILLER = {
    "celular", "celulares", "smartphone", "telefono", "movil", "phone", "dual",
    "sim", "5g", "4g", "lte", "nfc", "ram", "rom", "gb", "tb", "pantalla",
    "camara", "bateria", "mah", "pulgadas", "android", "color", "con", "de",
    "la", "el", "y", "para", "version", "global", "nacional", "esim", "psim",
    "solo", "hd", "fhd", "amoled", "oled", "lcd", "hz", "mp", "mpx", "core",
    "octa", "procesador", "carga", "rapida", "resistencia", "agua", "polvo",
    "smarphone", "unidades", "cellular_phone", "internacional", "inteligente",
    "desbloqueado", "desbloqueada", "unlocked", "libre", "reacondicionado",
    "reacondicionada", "premium", "renovado", "grado", "seminuevo", "bundle",
    "combo", "regalo", "audifonos", "smartwatch", "watch", "earbuds", "buds",
    "bocina", "w", "nits", "fps", "ip", "ai", "ia", "plus_bundle",
}
MODEL_STOP_RE = re.compile(
    r"\b(pantalla|camara|bateria|procesador|snapdragon|dimensity|mediatek|helio|"
    r"kirin|unisoc|exynos|tensor|carga|resistencia|android|hyperos|magicos|coloros|"
    r"harmonyos|originos|con capacidad|hasta|chip|"
    # marcadores en inglés: las fichas de Sunsky vienen con descripción larga
    # en inglés ("..., Screen Fingerprint, 6.55 inch MagicOS ..."), y sin
    # cortar ahí el "modelo" terminaba siendo puro texto de specs compartido
    # entre equipos distintos -- fue lo que agrupó un Honor 500 con un Honor
    # 300 y un Magic 7 Lite con un Magic 8 Lite en la primera prueba.
    r"screen fingerprint|side fingerprint|in-screen|face id|"
    r"inch|camera|cameras|battery|network|fingerprint)\b"
)


def model_of(name, brand):
    n = _norm(name)
    # corta en el primer marcador de "ficha técnica"
    m = MODEL_STOP_RE.search(n)
    if m:
        n = n[:m.start()]
    # "Pro+" / "Note 15 Pro+" es OTRO equipo que "Pro" a secas: el "+" se
    # conserva como palabra ("plus") en vez de borrarlo con el resto de la
    # puntuación -- borrarlo agrupó un Redmi Note 15 Pro con un Note 15 Pro+
    # en la primera prueba. Solo cuenta el "+" pegado a una palabra
    # (Pro+, Note+), no el de "8+256GB" ni el de "64GB + 3GB Ram" (ahí el
    # "+" separa RAM de almacenamiento). Permitir el espacio antes del "+",
    # o no excluir "gb"/"tb" pegados, metía la palabra inventada "plus" en
    # el modelo y partía en dos el par de Honor Play10 (Elektra + Amazon)
    # que justamente había que unir.
    # Un "+" es parte del modelo cuando lo precede una PALABRA ("Pro+",
    # "Note 14 Pro + 5G", que Elektra escribe con espacio), y es un simple
    # separador cuando lo precede una capacidad ("12GB+512GB", "64GB + 3GB
    # Ram", "(8+16)"). El patrón exige que la palabra empiece en un límite
    # de palabra, así que el "gb" de "64gb" no cuenta como palabra.
    n = re.sub(r"\b([a-z]+)\s*\+", lambda m: m.group(1) + " plus", n)
    n = re.sub(r"[(),:;/|\"'+.-]", " ", n)
    b = _norm(brand)
    toks = []
    for t in n.split():
        if not t:
            continue
        if t == b or t in b.split():
            continue
        # OJO: un número SUELTO se conserva -- en muchas marcas el modelo ES
        # un número (Honor 300/400/500/600, Nothing Phone 3a). Tirarlos hizo
        # que "Honor 500" y "Honor 300" quedaran con el mismo modelo en la
        # primera prueba. Solo se descartan los números que traen unidad
        # pegada (capacidad/specs) o los decimales (pulgadas de pantalla).
        if re.fullmatch(r"\d+(gb|tb|mah|mpx|mp|w|hz|nits|fps|ghz)", t):
            continue
        if re.fullmatch(r"\d+\.\d+\w*", t):
            continue
        if t in FILLER:
            continue
        if color_of(t):  # es una palabra de color
            continue
        toks.append(t)
    # normaliza "magic8" -> "magic 8", "note14" -> "note 14", "x7d" queda
    joined = " ".join(toks)
    joined = re.sub(r"([a-z])(\d)", r"\1 \2", joined)
    joined = re.sub(r"(\d)([a-z])\b", r"\1 \2", joined)
    joined = re.sub(r"\s+", " ", joined).strip()
    return joined or None


def signature(product):
    name = product.get("name") or ""
    brand = (product.get("brand") or "").strip()
    if not brand:
        return None
    storage, ram = storage_ram_of(name)
    color = color_of(name)
    model = model_of(name, brand)
    carrier = carrier_of(name)
    # Firma INCOMPLETA -> no se fusiona con nadie.
    if not (model and storage and color):
        return None
    return (
        brand.lower(),
        model,
        storage,
        ram,                    # None cuenta como "no declarado" y separa grupos
        color,
        carrier,                # None cuenta como "no declarado" y separa grupos
        bundle_of(name),        # accesorios de regalo concretos
        condition_of(name),
        esim_of(name),
        network_of(name),       # None cuenta como "no declarado" y separa grupos
    )
