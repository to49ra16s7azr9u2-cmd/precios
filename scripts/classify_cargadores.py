#!/usr/bin/env python3
"""Re-parte "Cargadores y adaptadores" por el tipo de cargador que es.

POR QUÉ
-------
La categoría estaba partida en "Cargadores" (391) y "Adaptadores" (69).
Eso no ayuda a elegir: un cargador de auto, uno inalámbrico, una batería
externa y una estación de energía caían todos en "Cargadores", que es
decir "esta categoría" otra vez. Quien entra ya sabe que busca un
cargador; lo que no sabe es cuál de todos.

La subcategoría pasa a ser DÓNDE se enchufa y para qué (ver
charger_type_of en specs_extract.py, que lo lee del nombre): de pared, de
auto, inalámbrico, para laptop, batería externa, cable, base de carga,
adaptador de corriente, de pilas y estación de energía.

Lo que no se puede clasificar queda en "Otros": son cargadores de aparatos
puntuales (una rasuradora Philips, una cámara Canon) y reguladores de
voltaje, que no forman un grupo con nombre propio. Inventarles uno sería
peor que dejarlos juntos y decirlo.

Después de correr esto conviene correr sync_subcategories.py, que registra
las subcategorías nuevas en data.categories -- sin eso la interfaz no las
ofrece. Este script además BORRA de esa lista las subcategorías de esta
categoría que se quedaron sin productos.

USO
---
    python3 scripts/classify_cargadores.py --dry-run
    python3 scripts/classify_cargadores.py
"""
import argparse
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import (capacidad_mah, load_catalog,  # noqa: E402
                     save_catalog, sin_acentos as _norm, tramo_mah)
from specs_extract import charger_type_of  # noqa: E402

CATEGORIA = "Cargadores y adaptadores"
RESIDUAL = "Otros"
POWER_BANKS = "Baterías portátiles"

# Un power bank NO es un cargador: tiene su propia batería y existe la
# categoría aparte, con sus tramos de mAh. Tenerlos en las dos hacía que la
# portada mostrara dos categorías con la misma foto y el mismo producto
# adentro, que fue justo lo que notó el usuario.
#
# "Cargador portátil" a secas no alcanza para moverlo: en México se le dice
# así también a un cargador de viaje chico. Hace falta que se declare como
# batería (power bank / batería externa) o que diga su capacidad en mAh.
_PB_FUERTE = re.compile(r"power ?bank|bateria externa|pila portatil|bateria portatil")
# Accesorios PARA power banks y cargadores DE baterías de aparatos, que no
# son power banks. Ojo con "cable": un power bank "con 4 cables integrados"
# sigue siendo un power bank, así que la palabra sola no descarta nada.
# "pila" a secas NO descalifica: en México "pila portátil" es como se le dice
# a un power bank, y así quedaban fuera cuatro de cada diez capturas de Amazon
# ("1 Hora Power Bank 20000mAh ... Pila Portatil"). Lo que descalifica es
# cargar pilas AA/AAA, que es otro aparato.
_PB_NO = re.compile(r"load resistor|\btester\b|estuche|funda|soporte para|"
                    r"cargador de bateria|cargador de baterias|"
                    r"cargador de pilas|pilas? (?:aa|aaa|recargables|alcalinas|c\b|d\b)|"
                    r"\b(?:aa|aaa)\b.{0,20}\bpilas?\b")




# Un aparato que declara la capacidad de SU batería no es un power bank. Un
# celular ("OPPO A6x Desbloqueado, 128GB+4GB, Pantalla 6.75\" 120 Hz, Batería
# de Larga Duración (6100 mAh)") entra en cualquier búsqueda de "baterías
# portátiles" y, mirando solo el mAh, terminaba en el tramo "Hasta 10,000 mAh".
# Lo que lo delata es lo que un power bank NO tiene: pulgadas de pantalla,
# hercios, RAM+almacenamiento, o decirse teléfono. "Pantalla" a secas no
# cuenta: muchos power banks traen una pantallita con el porcentaje.
_APARATO_CON_BATERIA = re.compile(
    r'pantalla\s*(?:de\s*)?\d+(?:[.,]\d+)?\s*(?:"|\x27\x27|pulgada)'
    r"|\d+\s*gb\s*\+\s*\d+\s*gb|\d+\s*gb\s*ram|\bram\b\s*\d+\s*gb"
    r"|\d+\s*hz\b|desbloqueado|dual\s*sim|\besim\b"
    r"|camara de \d+\s*mp|\d+\s*mp\b"
)
# A propósito NO están celular / teléfono / laptop / tablet: un power bank los
# nombra todo el tiempo para decir a qué le sirve ("Cargador Portátil para
# Celular 5000 mAh", "AsperX Power Bank para Laptop"). Lo que queda son datos
# que solo tiene el aparato: pulgadas de pantalla, hercios, RAM+almacenamiento,
# megapíxeles, desbloqueado / dual SIM.


def es_power_bank(nombre):
    n = _norm(nombre)
    if _PB_NO.search(n):
        return False
    # Antes que nada: si es un aparato con batería propia, no es un power bank
    # -- ni siquiera si además dice "power bank" en el título de otra cosa.
    if _APARATO_CON_BATERIA.search(n) and not _PB_FUERTE.search(n):
        return False
    if _PB_FUERTE.search(n):
        return True
    # Declarar capacidad en mAh es declararse batería: lo que almacena carga
    # es un power bank, no un cargador. Los que cargan la batería de OTRO
    # aparato (pilas AA, la de una consola) ya quedaron fuera arriba.
    return capacidad_mah(n) is not None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = load_catalog()
    productos = [p for p in data["products"] if p.get("category") == CATEGORIA]
    antes = Counter(p.get("subcategory") for p in productos)

    # Primero se sacan los power banks: no son cargadores.
    mudados = []
    for p in list(productos):
        if not es_power_bank(p.get("name", "")):
            continue
        p["category"] = POWER_BANKS
        p["subcategory"] = tramo_mah(p.get("name", ""))
        p["image"] = "battery"
        mudados.append(p["name"][:52])
        productos.remove(p)
    print(f"Movidos a {POWER_BANKS}: {len(mudados)}")
    for n in mudados[:12]:
        print(f"   {n}")
    if len(mudados) > 12:
        print(f"   ... y {len(mudados) - 12} más")
    print()
    cambios = 0
    for p in productos:
        nueva = charger_type_of(p.get("name", "")) or RESIDUAL
        if p.get("subcategory") != nueva:
            p["subcategory"] = nueva
            cambios += 1
    despues = Counter(p.get("subcategory") for p in productos)

    print(f"Productos en {CATEGORIA}: {len(productos)}")
    print(f"  reclasificados: {cambios}")
    print(f"\n  antes:   {dict(antes)}")
    print("\n  después:")
    for k, v in despues.most_common():
        print(f"     {k:26} {v}")
    sin = despues.get(RESIDUAL, 0)
    print(f"\n  sin tipo reconocible: {sin} ({100 * sin // max(1, len(productos))}%)")

    # Las subcategorías viejas quedan huérfanas en data.categories: la
    # interfaz las seguiría ofreciendo con cero resultados.
    vivas = set(despues)
    huerfanas = []
    for c in data["categories"]:
        if c.get("name") != CATEGORIA:
            continue
        subs = c.get("subcategories") or []
        quedan = [s for s in subs if s.get("name") in vivas]
        huerfanas = [s["name"] for s in subs if s.get("name") not in vivas]
        c["subcategories"] = quedan
    if huerfanas:
        print(f"  subcategorías sin productos, quitadas de la lista: {huerfanas}")

    if args.dry_run:
        print("\n(--dry-run: no se escribió nada)")
        return
    save_catalog(data)
    print("\nGuardado. Correr después: python3 scripts/sync_subcategories.py")


if __name__ == "__main__":
    main()
