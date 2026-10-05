"""Enlace a la tienda oficial de Huawei MX (Soicos) desde la ficha de un
producto Huawei. Mismo criterio que huaweiDestino() en js/app.js.

Sólo el ENLACE, sin precio ni foto: los términos de uso de
consumer.huawei.com/mx prohíben reproducir, mostrar o guardar en «sistemas
de recabación de información» su contenido con fines comerciales sin
consentimiento escrito, igual que LEGO. Probado por el usuario el
05-oct-2026: /mx/search/?keyword=<serie> abre la búsqueda con los productos
(«mate x7» -> Mate X7, Mate X6, ...). Las páginas de modelo tienen slugs
irregulares (watch-gt6 existe, watch-gt-6 no), por eso se va a la búsqueda.

Sólo las series que vende Huawei México; un accesorio «para Huawei» (correa,
mica, cargador) o un teléfono de versión china («Enjoy 70X») no lleva enlace.
"""
import re
import urllib.parse

from afiliados import SOICOS_HUAWEI

_NO = re.compile(r'\b(para|for|compatible( con)?) huawei\b|\bcorreas?\b|\bfundas?\b|\bmica\b|\bprotector|\bcargador|'
                 r'\bcable\b|\badaptador|\bcase\b|\brepuesto|\breacondicionad|\bchina version\b|\bgen[eé]ric', re.I)
_SERIE = re.compile(
    r'\b(mate ?x\d+|mate ?\d{2}(?: (?:pro\+?|rs|pro max))?|pura ?\d{2}(?: (?:pro|ultra|pro max))?|'
    r'nova ?y\d{2}s?|nova ?\d{1,2}(?: (?:pro|ultra|se|i))?|pocket ?\d|'
    r'watch (?:gt ?runner ?\d?|gt ?\d(?: pro)?|fit ?\d(?: pro)?|fit special edition|ultimate(?: \d)?|kids ?\w+(?: pro)?|d2?|\d)|'
    r'band ?\d{1,2}|free ?buds (?:pro ?\d|se ?\d|\d+i|studio|\d)|freeclip(?: ?\d)?|freearc|'
    r'matebook (?:d ?\d{2}|x pro|\d{2})|matepad(?: (?:pro|air|se|\d{2}(?:\.\d)?))?)\b', re.I)


def es_huawei(product):
    nombre = product.get("name") or ""
    if product.get("category") == "Redes" or _NO.search(nombre):
        return False
    return bool(re.search(r'\bhuawei\b', nombre, re.I))


def destino(product):
    """URL de consumer.huawei.com/mx para la ficha, o None."""
    if not es_huawei(product):
        return None
    s = _SERIE.search(product.get("name") or "")
    if not s:
        return None
    clave = re.sub(r'\s+', ' ', s.group(1)).lower()
    return "https://consumer.huawei.com/mx/search/?keyword=" + urllib.parse.quote(clave)


def url_huawei_store(product):
    d = destino(product)
    return SOICOS_HUAWEI + urllib.parse.quote(d, safe="") if d else None
