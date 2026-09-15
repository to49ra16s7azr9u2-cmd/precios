#!/usr/bin/env python3
"""Le pone subcategoría a los productos que ya están en el catálogo y se
quedaron sin ella, en las categorías cuyo desempate se escribió después.

POR QUÉ
-------
Las reglas que deciden la subcategoría viven en clasificar_captura_perifericos.py
y corren SOLO cuando entra una captura nueva. Lo que ya estaba guardado no se
vuelve a mirar, así que cada vez que se escribe un desempate nuevo queda un
escalón: los productos viejos se quedan con la subcategoría vacía y los nuevos
no. Al escribir sub_bocina, sub_audio, sub_laptop y sub_monitor quedaron así
1,802 bocinas, 3,702 audífonos, 158 laptops y los monitores anteriores a la
captura de septiembre.

Eso se nota en el sitio: el bloque "¿Qué tipo buscas?" reparte mal (una
subcategoría con 40 productos al lado de una categoría con 8,000 sin repartir),
y una subcategoría con menos de 30 productos no llega a tener página propia de
SEO (MIN_PRODUCTOS_SUBCATEGORIA en generate_seo_pages.py).

CÓMO
----
Reusa las mismas funciones que la captura, importadas del clasificador, para
que haya una sola definición de qué es una bocina chica o un audífono de
diadema. No inventa reglas nuevas acá: si las de allá cambian, esto cambia con
ellas.

Solo TOCA lo que está vacío. Un producto que ya tiene subcategoría se queda como
está, aunque la regla diría otra cosa: puede haberla puesto una persona a mano
o una regla más específica, y pisarla sería perder ese trabajo. Para eso está
--recategorizar, que sí la recalcula, y que no se usa en la corrida diaria.

Las funciones se niegan ante la duda y devuelven None; eso se respeta. Un
audífono que no dice si es de diadema o de botón se queda sin subcategoría,
igual que cuando entra por captura.

USO
---
    python3 scripts/subcategorias_perifericos.py --dry-run
    python3 scripts/subcategorias_perifericos.py
    python3 scripts/subcategorias_perifericos.py --solo Bocinas --solo Audífonos
"""
import argparse
import collections
import importlib.util
import os
import sys
import unicodedata
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))


def _cargar_clasificador():
    """Importa clasificar_captura_perifericos.py hasta antes de su main.

    El módulo no está pensado para importarse: al final lee sys.argv[1] y
    escribe un archivo. Se compila solo la parte de arriba (reglas y funciones)
    y se ejecuta eso, que es lo único que hace falta.
    """
    ruta = os.path.join(AQUI, "clasificar_captura_perifericos.py")
    with open(ruta, encoding="utf-8") as f:
        fuente = f.read()
    corte = fuente.index("\ncaptura = json.load")
    mod = {"__file__": ruta, "__name__": "clasificador_parcial"}
    exec(compile(fuente[:corte], ruta, "exec"), mod)  # noqa: S102
    return mod


# Categoría del catálogo -> nombre de la función que la reparte. Solo las que
# tienen un desempate escrito: el resto se queda como está.
DESPACHO = {
    "Bocinas": "sub_bocina",
    "Audífonos": "sub_audio",
    "Laptops": "sub_laptop",
    "Monitores": "sub_monitor",
    "Teclados": "sub_teclado",
    "Mouse": "sub_mouse",
    "Televisores": "sub_tv",
    "Lavadoras": "sub_lavadora",
    "Aspiradoras": "sub_aspiradora",
    "Refrigeradores": "sub_refri",
    "Cafeteras": "sub_cafetera",
    "Celulares": "sub_celular",
    "Tabletas": "sub_tableta",
    "Videojuegos": "sub_videojuego",
    "Muebles": "sub_mueble",
    "Juegos de mesa": "sub_juego_mesa",
    "Instrumentos musicales": "sub_instrumento",
    "Iluminación": "sub_iluminacion",
    "Autos, bicicletas y motos": "sub_vehiculo",
    "Domótica y hogar inteligente": "sub_domotica",
    "Cámaras y fotografía": "sub_camara",
    "Herramientas": "sub_herramienta",
}


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="no escribe, solo cuenta")
    ap.add_argument("--recategorizar", action="store_true",
                    help="recalcula también los que YA tienen subcategoría (no usar a diario)")
    ap.add_argument("--solo", action="append", default=[],
                    help="limita a estas categorías (se puede repetir)")
    args = ap.parse_args()

    mod = _cargar_clasificador()
    data = load_catalog()

    # Las subcategorías que el índice reconoce hoy, por categoría: si una
    # función devuelve algo que no está ahí, no se aplica -- inventar una
    # subcategoría suelta la deja invisible en los filtros (ver
    # sync_subcategories.py, que existe justo porque eso pasó).
    validas = {c["id"]: {s["id"] for s in (c.get("subcategories") or [])}
               for c in data["categories"]}

    objetivo = {c: f for c, f in DESPACHO.items()
                if not args.solo or c in args.solo}
    desconocidas = [c for c in args.solo if c not in DESPACHO]
    if desconocidas:
        print("sin regla escrita, se ignoran:", ", ".join(desconocidas))

    puestas = collections.Counter()
    fuera_del_indice = collections.Counter()
    sin_respuesta = collections.Counter()
    tocados = 0

    for p in data["products"]:
        cat = p.get("category")
        fn = objetivo.get(cat)
        if not fn:
            continue
        if p.get("subcategory") and not args.recategorizar:
            continue
        sub = mod[fn](norm(p.get("name") or ""))
        if not sub:
            sin_respuesta[cat] += 1
            continue
        if sub not in validas.get(cat, set()):
            fuera_del_indice[(cat, sub)] += 1
            continue
        if sub == p.get("subcategory"):
            continue
        p["subcategory"] = sub
        puestas[(cat, sub)] += 1
        tocados += 1

    for (cat, sub), n in sorted(puestas.items(), key=lambda k: -k[1]):
        print(f"  {n:6}  {cat} / {sub}")
    print(f"\nproductos con subcategoría nueva: {tocados}")
    if fuera_del_indice:
        print("\nla regla propuso una subcategoría que el índice no tiene "
              "(no se aplicó; correr sync_subcategories.py si debe existir):")
        for (cat, sub), n in fuera_del_indice.most_common():
            print(f"  {n:6}  {cat} / {sub}")
    print("\nsiguen sin subcategoría (la regla se negó ante la duda):")
    for cat, n in sin_respuesta.most_common():
        print(f"  {n:6}  {cat}")

    if args.dry_run:
        print("\n--dry-run: no se escribió nada")
        return
    if not tocados:
        print("\nnada que escribir")
        return
    save_catalog(data)
    print("\nGuardado.")


if __name__ == "__main__":
    main()
