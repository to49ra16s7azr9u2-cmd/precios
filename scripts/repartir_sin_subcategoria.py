#!/usr/bin/env python3
"""Reparte las fichas que se quedaron sin subcategoría o en una "Otros".

QUÉ SE ENCONTRÓ AL MEDIR
------------------------
15,386 fichas (6.4% del catálogo) no tienen subcategoría o están en una
subcategoría comodín ("Otros", "Varios", "Otros juegos"). Mirándolas, el
problema en buena parte NO es que falte la subcategoría: es que la
CATEGORÍA está mal, y por eso ningún repartidor de subcategoría puede
acertar.

  - "Honor X7d 8GB 256GB + Audifonos 119 De Regalo" está en Audífonos: es
    un teléfono con audífonos de regalo. Así 1,369 fichas.
  - "HP 14 Computadora portátil para Estudiantes" está en Otros.
  - "Bobina de Encendido Morimoto AMP XB" (una bobina de auto) y "Balasto
    MAD OWL 7R 230W" (un balastro de luz de escenario) están en Iluminación.
  - "Luz LED PAR Blizzard Lighting" está en Instrumentos musicales.

CÓMO SE REPARTE
---------------
No se escriben reglas nuevas en paralelo: se usan los repartidores de
subcategoría del clasificador de capturas
(clasificar_captura_perifericos.py), probados contra 16 capturas y ~75,000
anuncios.

Y se llaman DIRECTAMENTE, con el repartidor de la categoría que la ficha ya
tiene. La primera versión pasaba la ficha por el clasificador entero, como
si fuera un anuncio de una captura, y así solo resolvió 23: el clasificador
empieza por decidir la CATEGORÍA a partir del título, y un "MÓDEM NETGEAR
CM600 DOCSIS 3.0" no engancha ninguna regla de categoría, se descarta con
"no encaja en ninguna categoría" y nunca llega a sub_red(). Pero acá la
categoría NO hay que adivinarla: ya está en la ficha, puesta por la
taxonomía de su tienda. Lo único que falta es la subcategoría.

Y se aplica con frenos, porque ese clasificador fue calibrado sobre
títulos de Amazon y acá entran títulos de ocho tiendas:

  1. NO se cambia de categoría. Se probó y sale mal: la categoría que ya
     tiene la ficha viene de la taxonomía de su tienda, y el clasificador
     --que adivina por palabras sueltas-- propuso mandar "Mesa Sensorial 2
     en 1", "Juego Mesa Equilibrio" y las expansiones de Dixit a
     Muebles/Mesas de centro por la palabra "mesa"; los ventiladores de
     techo a Componentes de PC por "ventilador"; y los microscopios de
     reparación a Celulares por "teléfono". 1,624 movimientos, casi todos
     malos. Acá solo se RELLENA la subcategoría, dentro de la categoría que
     la ficha ya tiene.
  2. La subcategoría propuesta tiene que estar registrada en data.json.
     add_amazon_standalone.py descarta en silencio los pares que no lo
     están, y acá pasaría lo mismo pero peor: la ficha quedaría en una
     subcategoría sin página.
  3. Nunca se mueve a una subcategoría comodín: sacar una ficha de
     "sin subcategoría" para meterla en "Otros" no resuelve nada.
  4. Las fichas que el clasificador descarta (FUERA) se quedan como están y
     se listan: son las que hay que mirar a mano.

Sin --aplicar solo informa y deja el detalle en
data/reparto-subcategorias-<fecha>.tsv.
"""
import argparse
import collections
import datetime
import io
import json
import os
import re
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import load_catalog, save_catalog  # noqa: E402

CLASIFICADOR = os.path.join(AQUI, "clasificar_captura_perifericos.py")

# Subcategorías que no dicen nada: ni se toman como origen bueno ni se
# aceptan como destino.
# "Otros accesorios gamer" entra acá aunque sea una subcategoría fina:
# las fichas que Mercado Libre trae ya con ella nunca pasaron por el
# repartidor, y la mayoría son controles, fundas o cables que sí tienen
# subcategoría propia. Como destino sigue vetada, así que lo que no se
# reconoce se queda donde está.
# "Baterías", "Viento" y "Amplificadores" son los cajones de Instrumentos
# musicales (y solo de ahí: ningún otro rubro usa esos nombres), de cuando la
# categoría se repartía en familias y no en instrumentos. Entran acá para que
# el refinador los abra igual que a "Otros".
COMODIN = {"Otros", "Varios", "Otro", "Otros juegos", "Otro calzado", "Otros accesorios gamer",
           "Baterías", "Viento", "Amplificadores"}


# Qué repartidor le toca a cada categoría. Es el mismo reparto que hace el
# clasificador de capturas al final de su main; acá se replica el mapa
# porque la categoría no se adivina, se lee de la ficha.
REPARTIDORES = {
    "Bocinas": "sub_bocina", "Monitores": "sub_monitor", "Laptops": "sub_laptop",
    "Teclados": "sub_teclado", "Mouse": "sub_mouse", "Televisores": "sub_tv",
    "Audífonos": "sub_audio", "Lavadoras": "sub_lavadora", "Aspiradoras": "sub_aspiradora",
    "Refrigeradores": "sub_refri", "Cafeteras": "sub_cafetera", "Celulares": "sub_celular",
    "Tabletas": "sub_tableta", "Videojuegos": "sub_videojuego", "Muebles": "sub_mueble",
    "Herramientas": "sub_herramienta", "Juegos de mesa": "sub_juego_mesa",
    "Instrumentos musicales": "sub_instrumento", "Iluminación": "sub_iluminacion",
    "Autos, bicicletas y motos": "sub_vehiculo", "Domótica y hogar inteligente": "sub_domotica",
    "Cámaras y fotografía": "sub_camara", "Almacenamiento": "sub_almacenamiento",
    "Redes": "sub_red", "Climatización": "sub_clima", "Mascotas": "sub_mascota",
    "Cámaras de seguridad": "sub_vigilancia", "Juguetes y bebés": "sub_juguete",
    "Deportes y fitness": "sub_deporte", "Joyería y bisutería": "sub_joyeria",
    "Belleza y cuidado personal": "sub_belleza",
    "Impresoras": "sub_impresora", "Computadoras de escritorio": "sub_escritorio",
    "Blancos y ropa de cama": "sub_blancos", "Relojes inteligentes": "sub_reloj",
    "Suplementos": "sub_suplemento_fino", "Cocina y comedor": "sub_cocina_fino",
    "Baterías portátiles": "sub_bateria_tramo",
    "Cargadores y adaptadores": "sub_cargador", "Electrodomésticos": "sub_electro",
    "Drones": "sub_dron", "Equipo comercial": "sub_comercial", "Viajes": "sub_viaje",
    "Impresión 3D": "sub_impresion3d", "Movilidad eléctrica": "sub_movilidad",
    "Proyectores y accesorios": "sub_proyector", "Otros": "sub_otros",
}


def cargar_repartidores():
    """Saca del clasificador sus funciones sub_*.

    Es un script (lee sys.argv al importarse), así que se ejecuta con argv y
    __file__ puestos a mano sobre una captura vacía, igual que en
    reparar_celulares.py.
    """
    vacia = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    json.dump([], vacia)
    vacia.close()
    salida = vacia.name + ".alta.json"
    argv, stdout = sys.argv, sys.stdout
    sys.argv = ["clasificar", vacia.name, salida]
    sys.stdout = io.StringIO()
    try:
        g = {"__name__": "__main__", "__file__": CLASIFICADOR}
        exec(compile(open(CLASIFICADOR, encoding="utf-8").read(), CLASIFICADOR, "exec"), g)
    finally:
        sys.argv, sys.stdout = argv, stdout
        for f in (vacia.name, salida):
            if os.path.exists(f):
                os.unlink(f)
    # Baterías portátiles se reparte por tramo de mAh, no por un sub_*. Lo
    # que no trae mAh en el título y tampoco es un power bank (la funda, el
    # módulo de carga, la tapa del compartimento, el cable con batería) cae
    # en "Accesorios y repuestos": el rubro solo tenía los tres tramos de
    # capacidad y esas fichas se quedaban sin ningún lugar donde ir.
    def _bateria_tramo(tn):
        t = g["tramo"](g["capacidad_mah"](tn))
        if t:
            return t
        if re.search(r"\bfundas?\b|\bcarcasas?\b|\bcubiertas?\b|\btapas?\b|\bcajas?\b|\bestuches?\b|"
                     r"\bshell\b|\bconvertidora|usb c to usb|extension de la garantia|"
                     r"\bmodulo\b|\bpcba?\b|\bplaca\b|\btarjeta de carga\b|\bsoporte\b|"
                     r"\bcable\b|\badaptador\b|\brepuesto\b|\breemplazo\b|\bprotector(es)?\b|"
                     r"\beliminador(es)?\b|\bconvertidor\b|\bbolsa\b|\bcargador de (bateria|pilas)\b|"
                     r"\bcompatible con\b|\bpara \w+ para \w+\b", tn):
            return "Accesorios y repuestos"
        return None
    g["sub_bateria_tramo"] = _bateria_tramo
    return g


def icono_de(data):
    icono = {}
    for c in data["categories"]:
        icono[(c["id"], None)] = c.get("icon")
        for s in c.get("subcategories") or []:
            icono[(c["id"], s["id"])] = s.get("icon") or c.get("icon")
    return icono


def registradas(data):
    return {c["id"]: {s["id"] for s in (c.get("subcategories") or [])}
            for c in data["categories"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--categorias", nargs="*", help="solo estas categorías")
    args = ap.parse_args()

    data = load_catalog()
    reg = registradas(data)
    objetivo = [p for p in data["products"]
                if (not p.get("subcategory") or p.get("subcategory") in COMODIN)
                and (not args.categorias or p["category"] in args.categorias)]
    print(f"Fichas sin subcategoría o en comodín: {len(objetivo):,}")

    g = cargar_repartidores()
    T = g["T"]
    afinar = g["afinar_ola2"]
    icono = icono_de(data)
    cuenta = collections.Counter()
    destinos = collections.Counter()
    sin_repartidor = collections.Counter()
    lineas = []
    for p in objetivo:
        cat = p["category"]
        de = f"{cat}/{p.get('subcategory')}"
        nombre_fn = REPARTIDORES.get(cat)
        if not nombre_fn:
            cuenta["la categoría no tiene repartidor"] += 1
            sin_repartidor[cat] += 1
            continue
        tn = T(p["name"])
        sub = g[nombre_fn](tn)
        # Las subcategorías finas (olas 2-5) se aplican encima, igual que
        # hace el clasificador de capturas al final de su main.
        sub = afinar(cat, sub, tn) if sub else afinar(cat, p.get("subcategory"), tn)
        if sub in COMODIN or sub == p.get("subcategory"):
            sub = None
        if not sub:
            cuenta["el repartidor no se decide"] += 1
            lineas.append(f"SIN SUB\t{p['id']}\t{de}\t\t\t{p['name'][:100]}")
            continue
        if sub not in reg.get(cat, ()):
            cuenta["subcategoría no registrada"] += 1
            lineas.append(f"NO REGISTRADA\t{p['id']}\t{de}\t{cat}/{sub}\t\t{p['name'][:100]}")
            continue
        cuenta["SUBCATEGORÍA"] += 1
        destinos[("SUBCATEGORÍA", cat, sub)] += 1
        lineas.append(f"SUBCATEGORÍA\t{p['id']}\t{de}\t{cat}/{sub}\t\t{p['name'][:100]}")
        if args.aplicar:
            p["subcategory"] = sub
            ic = icono.get((cat, sub)) or icono.get((cat, None))
            if ic:
                p["image"] = ic

    hoy = datetime.date.today().isoformat()
    ruta = os.path.join(AQUI, "..", "data", f"reparto-subcategorias-{hoy}.tsv")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("accion\tid\tde\ta\tmotivo\tnombre\n" + "\n".join(sorted(lineas)) + "\n")
    for k, n in cuenta.most_common():
        print(f"  {n:6,}  {k}")
    if sin_repartidor:
        print("\nCategorías sin repartidor:")
        for k, n in sin_repartidor.most_common(12):
            print(f"  {n:6,}  {k}")
    print("\nDestinos (top 25):")
    for (a, c, s), n in destinos.most_common(25):
        print(f"  {n:5,}  {a:13s} -> {c} / {s}")
    print(f"\nDetalle en {os.path.relpath(ruta, os.getcwd())}")
    if args.aplicar:
        save_catalog(data)
        print("Catálogo guardado.")
    else:
        print("(sin --aplicar no se escribió nada)")


if __name__ == "__main__":
    main()
