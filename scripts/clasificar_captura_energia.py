#!/usr/bin/env python3
"""Clasifica una captura de Amazon de baterías/power banks para darla de alta.

Convierte el JSON crudo de la captura (asin, title, price, photo, url) en el
formato que espera add_amazon_standalone.py, agregando marca, categoría,
subcategoría e ilustración.

POR QUÉ HACE FALTA CLASIFICAR Y NO METER TODO EN "BATERÍAS PORTÁTILES"
----------------------------------------------------------------------
Una búsqueda de "baterías portátiles" en Amazon devuelve tres cosas
distintas mezcladas, y solo una es un power bank:

  - Power bank de bolsillo: se mide en mAh y carga un celular.
  - Estación de energía: se mide en Wh (la DJI Power 1000 Mini son 1008 Wh),
    pesa kilos y se usa en campamento u obra. Va a
    "Cargadores y adaptadores / Estación de energía".
  - Cargador o arrancador de batería de auto: el NOCO GENIUS10 carga una
    batería de plomo de 6V/12V y el NOCO Boost GB40 arranca un motor. No
    cargan un teléfono: van a "Autos, bicicletas y motos".

Mezclarlas rompe el filtro por capacidad (una estación de 1008 Wh no tiene
tramo de mAh) y pone un arrancador de coche de $3,000 en el ranking de power
banks.

USO
    python3 scripts/clasificar_captura_energia.py captura.json salida.json
    python3 scripts/add_amazon_standalone.py salida.json --dry-run
"""
import sys, re, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from classify_cargadores import es_power_bank, tramo_mah, _norm

# Una estación de energía se mide en Wh y no cabe en un bolsillo.
_ESTACION = re.compile(r"estacion de energia|central electrica|\d{3,5}\s*wh\b|"
                       r"power ?station|para exteriores|campamento|acampar|generador")
# Arrancar un auto o cargar su batería de plomo es otro producto.
_AUTO = re.compile(r"arrancador|jump ?start|booster de|cargador de bateria|"
                   r"bateria de auto|6v\s*/\s*12v|desulfatador|pasar corriente")

MARCAS = ["INIU", "UGREEN", "ANKER", "CUKTECH", "DJI", "NOCO", "ASPERX",
          "TONEOF", "BELOSIN", "BASEUS", "XIAOMI", "SAMSUNG", "1 HORA", "1HORA"]


def marca(titulo):
    n = _norm(titulo)
    for m in MARCAS:
        if _norm(m) in n:
            return "1 HORA" if m in ("1 HORA", "1HORA") else m
    return "GENERICO"


def clasificar(titulo):
    """(categoria, subcategoria, ilustracion). categoria None = sin decidir."""
    n = _norm(titulo)
    if _AUTO.search(n):
        return "Autos, bicicletas y motos", "Baterías y arranque", "car"
    if _ESTACION.search(n):
        return "Cargadores y adaptadores", "Estación de energía", "battery"
    if es_power_bank(titulo):
        # Sin mAh declarado no se inventa un tramo: queda sin subcategoría,
        # que es un estado que la categoría ya tiene.
        return "Baterías portátiles", tramo_mah(titulo), "battery"
    return None, None, "battery"


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    datos = json.load(open(sys.argv[1], encoding="utf-8"))
    salida, sin_clasificar, sin_precio = [], [], []
    for d in datos:
        cat, sub, img = clasificar(d["title"])
        if cat is None:
            sin_clasificar.append(d)
        if d.get("price") is None:
            sin_precio.append(d)
        salida.append({**d, "brand": marca(d["title"]), "category": cat,
                       "subcategory": sub, "image": img})
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=1)

    import collections
    print(f"Clasificados: {len(salida)}")
    for k, v in collections.Counter((d["category"], d["subcategory"]) for d in salida).most_common():
        print(f"  {v:>3}  {k[0]} / {k[1]}")
    if sin_clasificar:
        print(f"\nSIN CLASIFICAR ({len(sin_clasificar)}) -- revisar a mano:")
        for d in sin_clasificar:
            print(f"  {d['asin']}  {d['title'][:76]}")
    if sin_precio:
        print(f"\nSIN PRECIO ({len(sin_precio)}) -- add_amazon_standalone.py los salta:")
        for d in sin_precio:
            print(f"  {d['asin']}  {d['title'][:76]}")


if __name__ == "__main__":
    main()
