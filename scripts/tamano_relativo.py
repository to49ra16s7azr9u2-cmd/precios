"""Tamaño RELATIVO de cada ficha dentro de su subcategoría, para el buscador.

POR QUÉ
-------
Quien escribe «mochila grande» o «peluche chico» no pide la palabra «grande»:
pide lo que es grande PARA ESA CLASE de producto (una mochila de 40 L, un
peluche de 80 cm). Buscarla literalmente deja fuera casi todo, porque el
nombre casi nunca dice «grande»; lo que sí dice, o la ficha técnica, es la
medida. Acá se convierte esa medida en un número comparable: el percentil
(0-9) de la ficha entre las de su subcategoría.

QUÉ MIDE
--------
Por subcategoría se elige UNA medida: la primera de CLAVES (de lo más físico
a lo menos) que traen al menos el 25% de sus fichas (10% si ninguna llega).
Valores sin unidad común no se mezclan entre subcategorías: el percentil es
siempre contra las fichas de la misma subcategoría.

El nombre manda sobre la medida: «grande», «gigante», «jumbo», «maxi» ->
9; «chico», «pequeño», «compacto», «mini» -> 0.

SALIDA
------
resultado = {num: dígito 0-9}; las fichas sin medida ni palabra no aparecen
(el buscador no las toca). build_buscador.py lo escribe en data/buscar/z/.
"""
import collections
import re
import unicodedata

# De lo más «físico» a lo menos. dims_cm es la mayor dimensión de «26 × 18 × 21 cm»
# (de la faceta dims, o de un «60x40x30 cm» en el nombre).
CLAVES = ("screen_in", "size_in", "length_cm", "frame_cm", "dims_cm", "blind_cm", "pan_cm", "hood_cm", "fan_in",
          "bar_in", "liters", "fridge_ft3", "wash_kg", "volume_ml", "length_m", "weight_kg", "load_kg", "pieces",
          "bed_size", "size_label")

MIN_COBERTURA = 0.25
MIN_COBERTURA_BAJA = 0.10
MIN_FICHAS = 15

_ORDINAL = {
    "bed_size": {"individual": 1, "twin": 1, "semi individual": 1, "matrimonial": 2, "full": 2, "doble": 2,
                 "queen": 3, "queen size": 3, "king": 4, "king size": 4, "california king": 5},
    "size_label": {"xxs": 0, "extra chica": 0, "extra chico": 0, "xs": 0, "chica": 1, "chico": 1, "ch": 1, "s": 1,
                   "pequena": 1, "pequeno": 1, "mediana": 2, "mediano": 2, "m": 2, "grande": 3, "g": 3, "l": 3,
                   "extra grande": 4, "xg": 4, "xl": 4, "xxl": 5, "xxg": 5, "3xl": 5, "jumbo": 5},
}

GRANDE_RE = re.compile(r"\b(grande|gigante|jumbo|maxi|xxl|extra grande|king size)\b")
CHICO_RE = re.compile(r"\b(chic[oa]|pequen[oa]|compact[oa]|mini|chiquit[oa]|portatil de bolsillo)\b")
_DIMS_RE = re.compile(r"(\d{1,4}(?:[.,]\d{1,2})?)\s*(?:x|×|\*)\s*(\d{1,4}(?:[.,]\d{1,2})?)"
                      r"(?:\s*(?:x|×|\*)\s*(\d{1,4}(?:[.,]\d{1,2})?))?\s*(cm|mm|m)\b")


def _norm(s):
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def _num(x):
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        return float(x)
    try:
        return float(str(x).replace(",", "."))
    except ValueError:
        return None


def _dims_cm(texto):
    m = _DIMS_RE.search(_norm(texto))
    if not m:
        return None
    vals = [float(g.replace(",", ".")) for g in m.groups()[:3] if g]
    f = {"cm": 1.0, "mm": 0.1, "m": 100.0}[m.group(4)]
    v = max(vals) * f
    return v if 1 <= v <= 600 else None


def candidatas(p):
    """{clave: valor numérico} de la ficha, solo con las claves de CLAVES."""
    f = p.get("facets") or {}
    out = {}
    for k in CLAVES:
        if k == "dims_cm":
            v = _dims_cm(f.get("dims")) if f.get("dims") else None
            if v is None:
                v = _dims_cm(p.get("name"))
        elif k in _ORDINAL:
            raw = f.get(k)
            raw = raw[0] if isinstance(raw, list) and raw else raw
            v = _ORDINAL[k].get(_norm(str(raw)).strip()) if raw else None
        else:
            raw = f.get(k)
            raw = max(raw) if isinstance(raw, list) and raw and all(_num(x) is not None for x in raw) else raw
            v = _num(raw) if raw is not None else None
        if v is not None and v >= 0:
            out[k] = v
    return out


def evidencia_de_nombre(nombre):
    n = _norm(nombre)
    if GRANDE_RE.search(n):
        return 9
    if CHICO_RE.search(n):
        return 0
    return None


class Calculador:
    def __init__(self):
        self.por_sub = collections.defaultdict(list)   # (cat, sub) -> [(num, candidatas)]
        self.evidencia = {}                             # num -> 0 | 9

    def recoger(self, num, cat, sub, p):
        self.por_sub[(cat, sub)].append((num, candidatas(p)))
        e = evidencia_de_nombre(p.get("name"))
        if e is not None:
            self.evidencia[num] = e

    def calcular(self):
        res = {}
        for (cat, sub), fichas in self.por_sub.items():
            n = len(fichas)
            cuenta = collections.Counter(k for _, c in fichas for k in c)
            clave = None
            if n >= MIN_FICHAS:
                for k in CLAVES:
                    if cuenta[k] >= max(MIN_FICHAS, n * MIN_COBERTURA) and \
                            len({c[k] for _, c in fichas if k in c}) >= 3:
                        clave = k
                        break
                if clave is None:
                    mejor = max(CLAVES, key=lambda k: cuenta[k])
                    if cuenta[mejor] >= max(30, n * MIN_COBERTURA_BAJA) and \
                            len({c[mejor] for _, c in fichas if mejor in c}) >= 3:
                        clave = mejor
            if clave:
                vals = sorted(c[clave] for _, c in fichas if clave in c)
                m = len(vals)
                # percentil con empates al medio: no deja a todas las fichas
                # de un mismo valor en el extremo.
                import bisect
                for num, c in fichas:
                    if clave not in c:
                        continue
                    lo = bisect.bisect_left(vals, c[clave])
                    hi = bisect.bisect_right(vals, c[clave])
                    pct = (lo + hi) / 2 / m
                    res[num] = min(9, int(pct * 10))
        for num, e in self.evidencia.items():
            res[num] = e
        return res
