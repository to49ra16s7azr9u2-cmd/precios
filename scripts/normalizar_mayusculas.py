#!/usr/bin/env python3
"""Pasa a mayúscula/minúscula normal los nombres que llegaron TODO EN MAYÚSCULAS.

POR QUÉ
-------
Elektra publica 2,241 productos así ("MOTOROLA MOTO G17 POWER 8GB 256GB LCD
6.7 PULGADAS") y Mercado Libre otros 737. En el sitio se ven como si
gritaran, y en Google el título de la ficha es ese nombre: un resultado en
mayúsculas al lado de nueve en minúsculas se lee como spam y se hace clic
menos. No es un cambio de datos, es de tipografía: el producto es el mismo.

QUÉ SE TOCA Y QUÉ NO
--------------------
Solo los nombres cuyas letras están TODAS en mayúscula (str.isupper()). Un
nombre con mezcla ("iPhone 17 256GB Libre") ya lo escribió alguien con
criterio y no se toca. Dentro de un nombre en mayúsculas, palabra por
palabra:

  - lo que lleva dígitos queda como está: 256GB, 4K, R18, PH4, GA-2100-1ACR,
    50UA7500PSA. Son códigos, y un código en minúsculas deja de encontrarse;
  - las siglas y marcas que se escriben en mayúsculas quedan así (LED, LCD,
    AMOLED, UHD, HDR, USB, HDMI, RAM, SSD, TV, PS5, BGS, LG, HP, JBL...);
  - las palabras que tienen SU forma propia van a esa forma (IPHONE -> iPhone,
    PLAYSTATION -> PlayStation, WEBOS -> webOS);
  - las preposiciones y artículos van en minúscula salvo al inicio (de, con,
    para, en, y...); las unidades también (mm, cm, w, ton);
  - todo lo demás, Capitalizado: MOTOROLA -> Motorola, PULGADAS -> Pulgadas.

Una palabra de 1 a 3 letras que no está en ninguna lista se deja en
mayúsculas: casi siempre es una sigla que no se conoce (UHP, AS, NG) y
equivocarse hacia "Uhp" es peor que dejar "UHP".

USO
    python3 scripts/normalizar_mayusculas.py --dry-run [--muestra 40]
    python3 scripts/normalizar_mayusculas.py
"""
import argparse
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog  # noqa: E402

# Minúscula salvo al inicio del nombre.
MINUSCULAS = {
    "de", "del", "la", "el", "los", "las", "y", "o", "e", "u", "a", "con",
    "sin", "para", "por", "en", "al", "un", "una", "unos", "unas", "tipo",
    "mod", "mod.", "c/", "s/", "p/",
    # unidades
    "mm", "cm", "kg", "ml", "hz", "ton", "pzas", "pza", "pz", "pcs", "km",
    # preposiciones en inglés de los títulos de juegos y películas
    "of", "the", "and", "for", "with", "to", "in", "on",
}
# Unidades de UNA letra (g, m, l, w, v) no van acá a propósito: "G SHOCK",
# "G-TIDE" o "M PRO" son nombres, no gramos ni metros.

# Palabras cortas corrientes que sí llevan su Capitalización normal. Lo que
# tenga 3 letras y no esté acá ni en SIGLAS se deja en mayúsculas.
CORTAS = {
    "PRO", "MAX", "AIR", "NEO", "FIT", "GO", "ONE", "TAB", "PAD", "POP", "ORO",
    "SET", "KIT", "TOP", "BOX", "CAR", "VAN", "LUZ", "SOL", "MAR", "RED", "GEL",
    "GAS", "PAN", "DOS", "TRES", "UNO", "MINI", "LITE", "PLUS", "NOTE", "EDGE",
    "FLIP", "FOLD", "BUDS", "WATCH", "BAND", "PLAY", "NEW", "OLD", "BIG", "MEN",
    "NIÑO", "NIÑA", "PIE", "OJO", "PEZ", "MAP", "FAN", "HUB", "CAM", "MIC",
    "AMP", "SUB", "MID", "LOW", "HOT", "ICE", "SUN", "SKY", "BAY", "ECO",
    "FUN", "JOY", "ZEN", "ART", "ROJO", "AZUL", "GRIS", "ROSA", "TE",
}
# HP es unidad (caballos) y marca; como marca va en mayúsculas cuando está
# al inicio del nombre o antes de un modelo. Lo decide _palabra().

SIGLAS = {
    "LED", "OLED", "QLED", "LCD", "AMOLED", "IPS", "UHD", "FHD", "HD", "HDR",
    "HDR10", "USB", "HDMI", "RAM", "ROM", "SSD", "HDD", "CPU", "GPU", "TV",
    "PC", "DVD", "CD", "BT", "FM", "AM", "AC", "DC", "GPS", "NFC", "LTE",
    "RGB", "ANC", "TWS", "ATV", "SUV", "UTV", "ABS", "EBS", "LPG", "PS5",
    "PS4", "PS3", "PSP", "XL", "XXL", "XS", "S", "M", "L", "II", "III",
    "IV", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "SE", "AI", "IA",
    "DJ", "MP3", "MP4", "MIDI", "UV", "IP", "LG", "JBL", "TCL", "AOC",
    "ASUS", "MSI", "BGS", "KTM", "BMW", "GMC", "RAV4", "CRV", "HRV", "MG",
    "STF", "KSR", "AWG", "NBA", "NFL", "MLB", "UFC", "F1", "TNT", "MTB",
    "BMX", "PU", "PVC", "EVA", "LP", "EP", "VHS", "SD", "CR", "MR", "FR",
    "USA", "UK", "EU", "MX", "XT", "GT", "RS", "RX", "GTX", "RTX", "AMD",
    "ARM", "MAC", "NG", "UHP", "HP",
}

PROPIAS = {
    "IPHONE": "iPhone", "IPAD": "iPad", "IPOD": "iPod", "IMAC": "iMac",
    "MACBOOK": "MacBook", "AIRPODS": "AirPods", "AIRTAG": "AirTag",
    "PLAYSTATION": "PlayStation", "XBOX": "Xbox", "WEBOS": "webOS",
    "IOS": "iOS", "MACOS": "macOS", "YOUTUBE": "YouTube", "WIFI": "WiFi",
    "WI-FI": "Wi-Fi", "BLUETOOTH": "Bluetooth", "MAGSAFE": "MagSafe",
    "GALAXY": "Galaxy", "REDMI": "Redmi", "POCO": "POCO", "JBL": "JBL",
    "SMARTWATCH": "Smartwatch", "SMART": "Smart", "TCL": "TCL", "OPPO": "OPPO",
    "VIVO": "vivo", "ZTE": "ZTE", "HONOR": "HONOR", "REALME": "realme",
    "ONEPLUS": "OnePlus", "NUBIA": "nubia", "INFINIX": "Infinix",
    "TECNO": "TECNO", "HISENSE": "Hisense", "AIWA": "Aiwa", "PANASONIC": "Panasonic",
    "MAKITA": "Makita", "DEWALT": "DeWalt", "TRUPER": "Truper", "PRETUL": "Pretul",
    "STANLEY": "Stanley", "URREA": "Urrea", "AKSI": "Aksi", "SURTEK": "Surtek",
    "CASIO": "Casio", "CITIZEN": "Citizen", "SEIKO": "Seiko", "TIMEX": "Timex",
    "KUMHO": "Kumho", "MICHELIN": "Michelin", "BRIDGESTONE": "Bridgestone",
    "GOODYEAR": "Goodyear", "PIRELLI": "Pirelli", "FIRESTONE": "Firestone",
    "TRANSWELL": "Transwell", "NINTENDO": "Nintendo", "SWITCH": "Switch",
    "SAMSUNG": "Samsung", "MOTOROLA": "Motorola", "XIAOMI": "Xiaomi",
    "HUAWEI": "Huawei", "SONY": "Sony", "APPLE": "Apple", "LENOVO": "Lenovo",
    "ACER": "Acer", "DELL": "Dell", "LOGITECH": "Logitech", "RAZER": "Razer",
    "HYPERX": "HyperX", "STEELSERIES": "SteelSeries", "WHIRLPOOL": "Whirlpool",
    "MABE": "Mabe", "TEKA": "Teka", "BEHRINGER": "Behringer", "YAMAHA": "Yamaha",
    "FENDER": "Fender", "GIBSON": "Gibson", "PUMA": "Puma", "NIKE": "Nike",
    "ADIDAS": "adidas", "MARVEL": "Marvel", "DISNEY": "Disney", "LEGO": "LEGO",
    "BARBIE": "Barbie", "MATTEL": "Mattel", "HASBRO": "Hasbro",
}

_TIENE_DIGITO = re.compile(r"\d")


def _palabra(w, primera):
    """Una palabra (sin espacios) de un nombre todo en mayúsculas."""
    if not w:
        return w
    if _TIENE_DIGITO.search(w):
        return w
    # Puntuación pegada: "(NEGRO)", "HEXAGONAL," -> se procesa el núcleo.
    m = re.match(r"^([^\wÁÉÍÓÚÑÜ]*)(.*?)([^\wÁÉÍÓÚÑÜ]*)$", w)
    pre, nucleo, post = m.group(1), m.group(2), m.group(3)
    if not nucleo:
        return w
    if nucleo in PROPIAS:
        return pre + PROPIAS[nucleo] + post
    if nucleo in SIGLAS:
        return pre + nucleo + post
    if nucleo in CORTAS:
        return pre + nucleo.capitalize() + post
    low = nucleo.lower()
    if low in MINUSCULAS and not primera:
        return pre + low + post
    if low in MINUSCULAS and primera:
        return pre + low.capitalize() + post
    # Compuestas con guion o barra: cada parte por su lado ("ECO-DRIVE").
    if "-" in nucleo or "/" in nucleo or "+" in nucleo:
        sep = "-" if "-" in nucleo else ("/" if "/" in nucleo else "+")
        return pre + sep.join(_palabra(x, primera) for x in nucleo.split(sep)) + post
    if len(nucleo) <= 3:
        return w  # sigla desconocida: mejor UHP que Uhp
    return pre + low.capitalize() + post


def normalizar(nombre):
    if not nombre or not nombre.isupper():
        return nombre
    partes = nombre.split(" ")
    out = []
    primera = True
    for w in partes:
        out.append(_palabra(w, primera))
        if w.strip():
            primera = False
    return " ".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--muestra", type=int, default=30)
    args = ap.parse_args()
    data = load_catalog()
    cambios = []
    for p in data["products"]:
        n = p.get("name") or ""
        nuevo = normalizar(n)
        if nuevo != n:
            cambios.append((p, n, nuevo))
    print(f"Nombres todo en mayúsculas: {len(cambios)}")
    random.seed(11)
    for p, n, nuevo in random.sample(cambios, min(args.muestra, len(cambios))):
        print(f"  {n[:70]}\n    -> {nuevo[:70]}")
    if args.dry_run:
        print("\n(--dry-run: no se escribió nada)")
        return
    for p, _, nuevo in cambios:
        p["name"] = nuevo
    save_catalog(data)
    print(f"\nGuardado: {len(cambios)} nombres normalizados.")


if __name__ == "__main__":
    main()
