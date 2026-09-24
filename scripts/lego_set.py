"""El número de set de una ficha LEGO y su enlace a la tienda oficial.

Mismo criterio que legoSetNumber() / legoStoreUrl() en js/app.js: si se
cambia uno, se cambia el otro (la página estática y la app pintan el mismo
botón).
"""
import re
import urllib.parse

from afiliados import SOICOS_LEGO

_NO_ES_SET = re.compile(
    r'compatible|tipo lego|estilo lego|para lego|kit de luz|kit de luces|luz led|luces led|'
    r'iluminaci|l[aá]mpara|vitrina|display case|videojuego|\bps[45]\b|xbox|nintendo|switch|playstation',
    re.I)
_CANTIDADES = re.compile(r'\b\d{3,6}\s*(piezas|pzas|pzs|pcs|pieces|pz)\b|'
                         r'\b(piezas|pzas|pzs|pcs|pieces)\s*:?\s*\d{3,6}\b', re.I)


def es_lego(product):
    nombre = product.get("name") or ""
    marca = (product.get("brand") or "").strip().lower()
    if product.get("category") == "Videojuegos" or _NO_ES_SET.search(nombre):
        return False
    return marca == "lego" or bool(re.match(r'^(\S+ ){0,3}lego\b', nombre, re.I))


def numero_set(product):
    """El número de set del título (5 dígitos primero, después 4 que no
    parezcan un año, después 6), o None."""
    if not es_lego(product):
        return None
    nombre = _CANTIDADES.sub(" ", product.get("name") or "")
    nums = re.findall(r'(?<!\d)(?<!\d[.,])(\d{4,6})(?!\d)(?![.,]\d)', nombre)
    for n in nums:
        if len(n) == 5:
            return n
    for n in nums:
        if len(n) == 4 and not re.match(r'(19|20)\d\d$', n):
            return n
    for n in nums:
        if len(n) == 6:
            return n
    return None


def url_lego_store(product):
    n = numero_set(product)
    if not n:
        return None
    return SOICOS_LEGO + urllib.parse.quote(f"https://www.lego.com/es-mx/search?q={n}", safe="")
