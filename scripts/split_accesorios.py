#!/usr/bin/env python3
"""Manda a "Accesorios y repuestos" los productos que son SOLO una pieza.

EL PROBLEMA
-----------
"Aspiradoras — del más barato al más caro" abría con un kit de mopas de $257,
unos paños de mopa de $317 y unos cepillos de $335. Ninguna de las tres es una
aspiradora: son repuestos que se compran cuando ya se tiene una. Quien entra a
comparar aspiradoras no puede comparar nada en las primeras tres filas.

CÓMO SE DECIDE
--------------
Por el SUSTANTIVO DE CABEZA del nombre, no por si la palabra aparece en algún
lado. "Filtro HEPA para aspiradora JIGOO" es un filtro; "Aspiradora inalámbrica
LEVOIT con filtro HEPA" es una aspiradora, y las dos tienen la palabra
"filtro". Se saltean las cantidades de adelante ("2 paños...", "Pack de 4
filtros...", "Kit de mopa...") para llegar al sustantivo real.

Quedan fuera a propósito las palabras demasiado generales -- kit, juego, set,
papel -- porque nombran productos por derecho propio ("Juego de mesa", "Kit
Aspiradora Koblenz WD-9 + Bolsa") y marcarlas se llevaba puestos cientos de
productos legítimos. Otras (soporte, cargador, base, funda, cable, adaptador)
solo cuentan como pieza si el nombre dice PARA QUÉ aparato son: "Soporte para
Aspiradora Dyson V15" es un accesorio, "Base de carga" a secas es un producto.

OJO con esa segunda regla: NO se puede aplicar a una categoría donde esos
sustantivos SON el producto. En "Cargadores y adaptadores", "Cargador para
Kukirin G2" es exactamente lo que la categoría vende. Por eso el script pide
las categorías explícitamente y arranca solo con Aspiradoras.

QUÉ PASA DESPUÉS
----------------
Van a la subcategoría "Accesorios y repuestos" de SU MISMA categoría, no a otro
lado: un filtro de aspiradora pertenece a aspiradoras. Esa subcategoría es de
las que NO entran en el listado por defecto (ver SUBCATEGORIAS_OPT_IN en
js/app.js y en generate_seo_pages.py): aparecen al elegirla, al buscarlas por
nombre y en su propia página, pero no ensucian el ranking de la categoría.

USO
    python3 scripts/split_accesorios.py --dry-run
    python3 scripts/split_accesorios.py --categorias Aspiradoras
    python3 scripts/split_accesorios.py --contar     # cuántos hay por categoría
"""
import argparse
import os
import re
import sys
import unicodedata
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog

SUBCATEGORIA = "Accesorios y repuestos"

# Cantidades y envoltorios que van ANTES del sustantivo real.
_PREFIJOS = re.compile(
    r"^(?:\d+\s*(?:uds?|unidades?|pzas?|piezas?|pack|pcs)\s+|\d+[a-z]*\s+"
    r"|pack\s+de\s+\d*\s*|paquete\s+de\s+\d*\s*|juego\s+de\s+\d*\s*"
    r"|kit\s+de\s+\d*\s*|set\s+de\s+\d*\s*|par\s+de\s+\d*\s*|x\d+\s+)+"
)

# Sustantivos que, en cabeza, nombran una pieza y no un aparato.
_PIEZAS = {
    "mopa", "mopas", "pano", "panos", "trapo", "trapos",
    "filtro", "filtros", "bolsa", "bolsas", "cepillo", "cepillos",
    "rodillo", "rodillos", "manguera", "mangueras", "boquilla", "boquillas",
    "cabezal", "cabezales", "bateria", "baterias",
    "repuesto", "repuestos", "recambio", "recambios", "refaccion", "refacciones",
    "accesorio", "accesorios", "deposito", "depositos", "contenedor", "contenedores",
    "cartucho", "cartuchos", "toner", "tinta", "tintas",
    "correa", "correas", "banda", "bandas", "tapa", "tapas",
    "cubierta", "cubiertas", "tubo", "tubos", "extension", "extensiones",
    "eje", "ejes", "cinta", "cintas", "pieza", "piezas",
}

# Sustantivos que son pieza SOLO si el nombre dice para qué aparato son. Un
# "soporte" o un "cargador" es un producto por derecho propio (un soporte de
# monitor, un cargador de pared); "Soporte para Aspiradora Dyson V15" no.
_PIEZAS_SI_ES_PARA = {
    "soporte", "soportes", "cargador", "cargadores", "base", "bases",
    "funda", "fundas", "protector", "protectores", "estuche", "estuches",
    "cable", "cables", "adaptador", "adaptadores",
}
_DICE_PARA_QUE = re.compile(r"\b(para|compatible con|repuesto de)\b")


def _normalizar(texto):
    t = unicodedata.normalize("NFKD", (texto or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]", " ", t)


def sustantivo_de_cabeza(nombre):
    t = _PREFIJOS.sub("", _normalizar(nombre).strip())
    for palabra in t.split():
        if len(palabra) >= 3:
            return palabra
    return ""


def es_solo_una_pieza(nombre):
    cabeza = sustantivo_de_cabeza(nombre)
    if cabeza in _PIEZAS:
        return True
    return cabeza in _PIEZAS_SI_ES_PARA and bool(_DICE_PARA_QUE.search(_normalizar(nombre)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--contar", action="store_true",
                    help="solo mostrar cuántos hay por categoría, sin tocar nada")
    ap.add_argument("--categorias", nargs="*", default=["Aspiradoras"],
                    help='categorías a procesar (por nombre). "todas" para el catálogo entero.')
    args = ap.parse_args()

    data = load_catalog()
    productos = data["products"]

    if args.contar:
        c = Counter(p["category"] for p in productos if es_solo_una_pieza(p["name"]))
        print(f"Productos que son solo una pieza: {sum(c.values()):,}")
        for cat, n in c.most_common():
            print(f"  {n:>5,}  {cat}")
        return

    objetivo = None if args.categorias == ["todas"] else set(args.categorias)
    movidos, por_cat = [], Counter()
    for p in productos:
        if objetivo is not None and p["category"] not in objetivo:
            continue
        if p.get("subcategory") == SUBCATEGORIA or not es_solo_una_pieza(p["name"]):
            continue
        movidos.append((p["category"], p.get("subcategory"), p["name"]))
        por_cat[p["category"]] += 1
        p["subcategory"] = SUBCATEGORIA

    print(f"Movidos a \"{SUBCATEGORIA}\": {len(movidos):,}")
    for cat, n in por_cat.most_common():
        print(f"  {n:>5,}  {cat}")
    for cat, antes, nombre in movidos[:15]:
        print(f"     [{cat} / {antes}] {nombre[:70]}")
    if len(movidos) > 15:
        print(f"     ... y {len(movidos) - 15:,} más")

    # La subcategoría tiene que existir en la taxonomía o el filtro no la lista.
    for cat in data["categories"]:
        if por_cat.get(cat["id"]):
            subs = cat.setdefault("subcategories", [])
            if not any(s["id"] == SUBCATEGORIA for s in subs):
                subs.append({"id": SUBCATEGORIA, "name": SUBCATEGORIA})
                print(f'  + subcategoría nueva en {cat["name"]}')

    if args.dry_run:
        print("\n(--dry-run: no se escribió nada)")
        return
    if movidos:
        save_catalog(data)
        print("\nGuardado.")


if __name__ == "__main__":
    main()
