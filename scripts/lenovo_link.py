"""Enlace a la tienda oficial de Lenovo MX (Soicos) desde la ficha de un
producto Lenovo. Mismo criterio que lenovoStoreUrl() en js/app.js.

Sólo el ENLACE, sin precio: los términos de uso de lenovo.com prohíben usar
procesos automáticos (robots, arañas, scripts) para acceder o recolectar su
información, y el programa de Soicos no entrega un feed. Probado por el
usuario el 24-sep-2026:
  /mx/es/p/<número de parte>   abre la página del producto
  /mx/es/search?text=<texto>   abre la búsqueda (por número o por serie)
Los números de parte que terminan en «US» son modelos de Estados Unidos que
lenovo.com/mx no vende: a esos se les da la búsqueda por serie.
"""
import re
import urllib.parse

from afiliados import SOICOS_LENOVO

_NO = re.compile(r'compatible|\bpara (lenovo|thinkpad|ideapad|legion|yoga)\b|\bfunda|\bmica\b|\bcargador|\bbateria para|'
                 r'\bprotector|\bcarcasa|\brepuesto|\breemplazo|\bteclado para|\bpantalla para', re.I)
_PARTE = re.compile(r'\b(\d{2}[A-Z0-9]{2}\d{4}[A-Z]{2}|\d{2}[A-Z0-9]{2}[A-Z0-9]{6})\b', re.I)
_SERIE = re.compile(
    r'\b(ideapad(?: (?:slim|flex|gaming|pro|duet))?(?: \d{1,2}i?)?|thinkpad(?: [a-z]\d{1,2}[a-z]?)?|legion(?: (?:pro|slim|go|tower))?(?: \d{1,2}i?)?|'
    r'yoga(?: (?:slim|pro|book|tab))?(?: \d{1,2}i?)?|thinkbook(?: \d{2}s?)?|loq(?: \d{2}i?)?|ideacentre(?: aio)?(?: \d)?|thinkcentre(?: [a-z]\d{2}[a-z]?)?|'
    r'thinkvision(?: [a-z]\d{2}[a-z]?-?\d{0,2})?|tab (?:m|p|k)\d{1,2}(?: plus)?|legion go(?: s)?|chromebook(?: duet)?|v1[45](?= g\d| gen|\b))\b', re.I)


def es_lenovo(product):
    nombre = product.get("name") or ""
    marca = (product.get("brand") or "").strip().lower()
    if _NO.search(nombre):
        return False
    return marca == "lenovo" or bool(re.match(r'^(\S+ ){0,2}lenovo\b', nombre, re.I))


def destino(product):
    """URL de lenovo.com/mx para la ficha, o None."""
    if not es_lenovo(product):
        return None
    nombre = product.get("name") or ""
    for m in _PARTE.finditer(nombre):
        parte = m.group(1).upper()
        if re.search(r'\d', parte[4:]) and not parte.endswith("US"):
            return f"https://www.lenovo.com/mx/es/p/{parte}"
    s = _SERIE.search(nombre)
    if s:
        return "https://www.lenovo.com/mx/es/search?text=" + urllib.parse.quote(s.group(1))
    return None


def url_lenovo_store(product):
    d = destino(product)
    return SOICOS_LENOVO + urllib.parse.quote(d, safe="") if d else None
