#!/usr/bin/env python3
"""Le pone subcategoría a los productos que llegaron sin ella.

POR QUÉ IMPORTA
---------------
La subcategoría es el paso 2 del recorrido del sitio: categoría -> "¿Qué
tipo buscas?" -> ranking -> comparación. En varias categorías ese paso no
servía de nada porque casi ningún producto estaba clasificado -- Blancos y
ropa de cama tenía 2,144 de 2,585 sin subcategoría (83%), Instrumentos
musicales 1,648 de 1,920 (86%), Iluminación 1,303 de 1,469 (89%). Además,
una subcategoría con menos de 30 productos no llega a tener página propia
de SEO (ver MIN_PRODUCTOS_SUBCATEGORIA en generate_seo_pages.py), así que
todas esas se quedaban sin página.

CÓMO DECIDE
-----------
Por el nombre, con reglas explícitas por categoría, y con dos frenos:

  1. GANA LA PALABRA QUE APARECE PRIMERO. Los títulos en español empiezan
     por lo que ES el producto ("Protector Lux Rogga Matrimonial + Sabanas
     Royal + Almohada"): eso es un protector, aunque nombre sábanas y
     almohada después. Sin esta regla, un combo se clasificaba por
     cualquiera de sus partes.
  2. SI EMPATAN DOS, NO SE CLASIFICA. Dos reglas distintas que enganchan en
     la misma posición no dan una respuesta, dan dos.

Y cada regla dice DÓNDE puede enganchar, porque hay dos clases distintas:

  - "cabeza": la palabra ES el producto (sábanas, lámpara de techo, disco
    duro externo). Tiene que estar al principio del título, si no se cuelan
    los accesorios: "Púa de guitarra" y "Filtro de Micrófono" no son una
    guitarra ni un micrófono, y en la primera versión de este script
    terminaban en Guitarras y en Amplificadores y micrófonos.
  - "libre": la palabra CALIFICA a un producto que ya se sabe cuál es
    ("Lavadora Whirlpool Carga Superior 20Kg", "Cafetera Oster de
    cápsulas"). Ahí el dato llega tarde en el título a propósito y exigirle
    estar al principio tiraría clasificaciones buenas.

Antes de medir la posición se le quita al título el "Juego de" / "Paquete
de" del principio, que en Blancos es la mitad del catálogo ("Juego de Funda
de Edredón..." es un edredón).

Y no se clasifica lo que arranca nombrando un accesorio ("Funda para
guitarra", "Soporte para teclado"): el accesorio no es el producto, y
meterlo en Guitarras ensucia justo la lista que alguien abre para comparar
guitarras.

Lo que ninguna regla toca se queda sin subcategoría, que es como estaba.
Nunca se inventa una subcategoría que la categoría no declare: si una regla
nombra uno que no existe, el script se planta antes de tocar nada.

USO
    python3 scripts/clasificar_subcategorias.py --dry-run
    python3 scripts/clasificar_subcategorias.py --dry-run --categorias Iluminación
    python3 scripts/clasificar_subcategorias.py
"""
import argparse
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog, texto_plano as norm, tramo_mah




# Si el título ARRANCA con esto, el producto es un accesorio de otra cosa y
# no va en la subcategoría del aparato que nombra después.
ACCESORIO_AL_FRENTE = re.compile(
    r"^(funda|estuche|maleta|bolsa|mochila|soporte|base|atril|banco|banqueta|"
    r"correa|cable|adaptador|cargador|bateria|pila|repuesto|refaccion|kit de limpieza|"
    r"protector de pantalla|mica|pua|puas|plumilla|afinador|metronomo|capo|cejilla|"
    r"filtro|boton|anillo|cartucho|cana|canas|boquilla|aceite|limpiador|"
    # Encontrados auditando la primera corrida: "Difusor trompeta para
    # driver" es una bocina, no un instrumento de viento, y "Tapa
    # amplificadora Fender" es una tapa. Iban a Viento y a Amplificadores.
    r"difusor|tapa|jarra|vaso|rack|gancho|dispensador|porta|montura|abrazadera|"
    r"espumador|conector|convertidor)\b"
)

# Y esto, en cualquier parte del título, dice que el producto es para
# mantener otro producto: "Kit desincrustante compatible con Nespresso" no
# es una cafetera de cápsulas.
CONSUMIBLE_DE_MANTENIMIENTO = re.compile(
    r"\bdesincrustante\b|\bdescalcificad|\bkit de limpieza\b|"
    r"\bpastillas de limpieza\b|\brepuesto\b"
)

# "Juego de sábanas" es sábanas; "Paquete de 6 focos" son focos. Se le quita
# al título ese arranque antes de medir en qué palabra engancha cada regla.
PREFIJO_DE_CONJUNTO = re.compile(
    r"^(juego|juegos|set|paquete|pack|kit|combo|caja|par)\s+(de\s+)?(\d+\s+)?"
)

# Un token que parece número de modelo ("PSRE383SET", "X10"): letras Y
# dígitos. Muchos títulos arrancan con marca y modelo antes de decir qué es
# la cosa ("Yamaha PSRE383SET Teclado digital de 61 teclas"), y sin saltarlos
# el sustantivo del producto cae fuera de la ventana.
MODELO = re.compile(r"^[a-z0-9]*[a-z][a-z0-9]*\d[a-z0-9]*$")

# Hasta qué palabra puede enganchar una regla de "cabeza". Dos: la primera
# es el sustantivo del producto y la segunda cubre "disco duro", "tira led",
# "lampara de techo" (que engancha como frase desde la palabra 0).
VENTANA_CABEZA = 2

# Ámbitos de una regla:
#   CABEZA   la palabra ES el producto -> tiene que estar al principio.
#   LIBRE    la palabra lo CALIFICA -> puede estar en cualquier parte.
#   RESIDUAL red de seguridad de la categoría -> solo si NINGUNA otra
#            enganchó. Sin esto, un residual gana por posición: "PC HP 800
#            G4 Mini" enganchaba "pc" en la palabra 0 y "mini" en la 3, así
#            que 9 mini PCs terminaban en Torre / Escritorio.
CABEZA, LIBRE, RESIDUAL = "cabeza", "libre", "residual"

# (subcategoría, patrón). El orden acá no decide nada: decide en qué
# posición del nombre engancha cada uno (ver el módulo de arriba).
REGLAS = {
    "Blancos y ropa de cama": [
        ("Sábanas", r"\bsabana|\bjuego de cama\b|\bropa de cama\b", CABEZA),
        ("Edredones y cobertores", r"\bedredon|\bcobertor|\bcolcha\b|\bcolchas\b|\bquilt\b|\bduvet\b|\bcubrecama\b|\bmanta\b|\bcobija\b|\bfrazada\b", CABEZA),
        ("Almohadas", r"\balmohada", CABEZA),
        ("Protectores de colchón", r"\bprotector\b|\bcubrecolchon\b|\bcubre colchon\b", CABEZA),
        ("Toallas", r"\btoalla", CABEZA),
        ("Tapetes de baño", r"\btapete de bano\b|\btapetes de bano\b", CABEZA),
        ("Cortinas", r"\bcortina", CABEZA),
        ("Fundas para muebles", r"\bfunda para (sofa|sillon|mueble)|\bcubresofa\b", CABEZA),
        # Califica a la cobija, así que puede llegar tarde en el título.
        ("Cobijas eléctricas", r"\b(cobija|manta|frazada) electrica\b", LIBRE),
    ],
    "Instrumentos musicales": [
        ("Guitarras", r"\bguitarra\b|\bguitarras\b|\bguitarra (electrica|acustica|clasica)\b|\bbajo electrico\b|\bukulele\b|\bcharango\b|\brequinto\b", CABEZA),
        ("Teclados y pianos", r"\bteclado\b|\bteclados\b|\bpiano\b|\bpianos\b|\bsintetizador\b|\borgano\b", CABEZA),
        ("Baterías", r"\bbateria acustica\b|\bbateria electronica\b|\bplatillo|\btarola\b|\bredoblante\b|\btimbales\b|\bbombo\b", CABEZA),
        ("Cuerdas", r"\bcuerdas\b|\bencordado\b", CABEZA),
        ("Amplificadores y micrófonos", r"\bamplificador|\bmicrofono|\bmicrofonos\b", CABEZA),
        ("Viento", r"\btrompeta\b|\barmonica\b|\bsaxofon\b|\bflauta\b|\bclarinete\b|\btrombon\b|\btuba\b|\bcorneta\b", CABEZA),
        ("DJ y producción", r"\bcontrolador (dj|midi)\b|\bmezcladora\b|\bmixer\b|\binterfaz de audio\b|\btornamesa\b", CABEZA),
    ],
    "Iluminación": [
        ("Tiras LED", r"\btira led\b|\btiras led\b|\btira de led\b", CABEZA),
        ("Lámparas de escritorio", r"\blampara de escritorio\b|\blampara de mesa\b|\blampara de buro\b", CABEZA),
        ("Lámparas de techo y pie", r"\blampara de techo\b|\blampara de piso\b|\blampara de pie\b|\bcandil\b|\bplafon\b|\bluminario de techo\b|\barbotante\b", CABEZA),
        ("Lámparas de emergencia", r"\blampara de emergencia\b|\bluz de emergencia\b|\blinterna\b", CABEZA),
        ("Iluminación industrial y exterior", r"\breflector\b|\breflectores\b|\bluminario\b|\blampara solar\b|\bcampana led\b|\bpanel led\b", CABEZA),
        ("Focos inteligentes", r"\bfoco inteligente\b|\bfocos inteligentes\b|\bfoco smart\b|\bfoco wifi\b", CABEZA),
    ],
    "Almacenamiento": [
        ("Externo", r"\b(disco duro|disco|ssd|unidad) externo\b|\bdisco duro portatil\b|\bexterno\b", LIBRE),
        ("Interno", r"\b(disco duro|disco|ssd|unidad) interno\b|\bnvme\b|\bsata\b|\binterno\b", LIBRE),
        ("Memorias y tarjetas", r"\bmemoria (usb|flash|micro|sd)\b|\btarjeta (sd|micro|de memoria)\b|\bmicrosd\b|\bflash drive\b|\busb flash\b|\bpendrive\b|\bmemoria usb\b", CABEZA),
        ("NAS y red", r"\bnas\b|\balmacenamiento en red\b", LIBRE),
    ],
    "Cafeteras": [
        ("De cápsulas", r"\bcapsula|\bkeurig\b|\bnespresso\b|\bdolce gusto\b|\bk cup\b", LIBRE),
        ("Molinillos de café", r"\bmolino\b|\bmolinillo\b|\bmoledor\b", CABEZA),
        # 30 tazas para arriba. Con \d{2,3} entraban las de 12 y 15 tazas,
        # que son cafeteras de casa: 29 quedaron marcadas como comerciales.
        # "percoladora" tampoco alcanza sola (las hay de casa).
        ("Uso comercial", r"\bcomercial\b|\bindustrial\b|\b2 grupos\b|\b([3-9]\d|[1-9]\d{2}) tazas\b", LIBRE),
        ("Portátiles", r"\bportatil\b|\bde viaje\b|\bitaliana\b|\bmoka\b|\bprensa francesa\b", LIBRE),
        ("Espresso automáticas y semiautomáticas", r"\bespresso\b|\bexpreso\b|\bsemiautomatica\b", LIBRE),
    ],
    "Computadoras de escritorio": [
        ("All in One", r"\ball in one\b|\baio\b|\bimac\b|\btodo en uno\b", LIBRE),
        # "mini" a secas también: así se venden ("HP 800 G4 Mini", "Lenovo
        # ThinkCentre Tiny"). SFF/USFF NO entran acá a propósito: son
        # gabinetes de torre chicos, no mini PCs, y son 30 equipos.
        ("Mini PC", r"\bmini\b|\bminipc\b|\btiny\b|\bnuc\b", LIBRE),
        # Red de seguridad: una computadora de escritorio que no es
        # all-in-one ni mini es, por definición, de torre. RESIDUAL, así que
        # solo entra si las dos de arriba no engancharon.
        ("Torre / Escritorio", r"\b(pc|computadora|desktop|gamer|gaming|torre|cpu|workstation)\b", RESIDUAL),
    ],
    "Lavadoras": [
        ("Lavasecadoras", r"\blavasecadora", CABEZA),
        ("Centros de lavado", r"\bcentro de lavado\b", CABEZA),
        ("Secadoras", r"\bsecadora", CABEZA),
        ("Semiautomáticas", r"\bsemiautomatica|\bsemi automatica|\bdoble tina\b|\b2 tinas\b|\bdos tinas\b", LIBRE),
        ("Carga frontal", r"\bcarga frontal\b", LIBRE),
        ("Carga superior", r"\bcarga superior\b|\bagitador\b|\bimpulsor\b", LIBRE),
    ],
    "Cámaras y fotografía": [
        ("Cámaras de acción", r"\bgopro\b|\bcamara de accion\b|\baction cam\b|\binsta360\b|\bosmo action\b", LIBRE),
        ("Instantáneas", r"\binstax\b|\binstantanea|\bpolaroid\b", LIBRE),
        ("Videocámaras", r"\bvideocamara|\bhandycam\b|\bcamcorder\b", CABEZA),
        ("Mirrorless y réflex", r"\bmirrorless\b|\breflex\b|\bdslr\b|\bsin espejo\b", LIBRE),
        ("Lentes y accesorios", r"\blente\b|\blentes\b|\bobjetivo\b|\bteleobjetivo\b", CABEZA),
    ],
}


# Correcciones: subcategorías que están puestas y que se sabe que están
# MAL, con la prueba en el propio nombre. No es "reclasificar todo": cada
# entrada dice de qué subcategoría, a cuál, y con qué patrón. Solo corren
# con --corregir.
#
# La de Celulares viene de add_elektra_products.py, que tenía la categoría
# de teléfonos de Elektra mapeada a ("Celulares", "Android") fijo: 177
# iPhones quedaron etiquetados Android, o sea fuera del filtro "iPhone" que
# es justo el que alguien abre para compararlos. El importador ya decide
# bien (ver cat_celulares); esto arregla los que ya estaban cargados.
CORRECCIONES = {
    "Celulares": [("Android", "iPhone", r"\biphone\b")],
}

CORRECCIONES_COMPILADAS = {
    cat: [(desde, hacia, re.compile(pat)) for desde, hacia, pat in reglas]
    for cat, reglas in CORRECCIONES.items()
}


# Baterías portátiles no se parte por palabras sino por la medida del título,
# y esa lectura (con separador de miles y todo) vive en data_io: la comparte
# con classify_cargadores.py, que manda ahí los power banks que encuentra
# entre los cargadores.
REGLAS_ESPECIALES = {"Baterías portátiles": tramo_mah}

COMPILADAS = {
    cat: [(sub, re.compile(pat), ambito) for sub, pat, ambito in reglas]
    for cat, reglas in REGLAS.items()
}


def recortar_encabezado(n, marca):
    """Quita del principio lo que no dice QUÉ es el producto.

    Tres cosas: el arranque de conjunto ("Juego de sábanas" es sábanas), la
    marca ("Yamaha Teclado...") y los números de modelo ("Yamaha PSRE383SET
    Teclado..."). Sin esto el sustantivo del producto cae fuera de la
    ventana de las reglas de cabeza y se pierden clasificaciones buenas.
    """
    palabras_marca = set(norm(marca).split())
    while True:
        recortado = PREFIJO_DE_CONJUNTO.sub("", n, count=1)
        if recortado != n:
            n = recortado
            continue
        cabeza = n.split(" ", 1)
        primera = cabeza[0]
        # Una letra suelta es parte del modelo partido por el guion
        # ("Roland E-X10" queda como "e x10"), no el nombre del producto.
        if primera and (primera in palabras_marca or MODELO.match(primera)
                        or len(primera) == 1):
            n = cabeza[1] if len(cabeza) > 1 else ""
            continue
        return n


def subcategoria_de(categoria, nombre, marca=""):
    """(subcategoría, motivo) -- subcategoría None si no se puede decidir."""
    n = norm(nombre)
    especial = REGLAS_ESPECIALES.get(categoria)
    if especial:
        return especial(n), "medida"
    n = recortar_encabezado(n, marca)
    if ACCESORIO_AL_FRENTE.match(n):
        return None, "accesorio"
    if CONSUMIBLE_DE_MANTENIMIENTO.search(n):
        return None, "consumible"
    reglas = COMPILADAS.get(categoria)
    if not reglas:
        return None, "sin reglas"
    mejor, empate, residual = None, False, None
    for sub, rx, ambito in reglas:
        m = rx.search(n)
        if not m:
            continue
        if ambito == RESIDUAL:
            residual = sub
            continue
        if ambito == CABEZA and n[:m.start()].count(" ") >= VENTANA_CABEZA:
            # La palabra ES el producto, pero llega demasiado tarde: el
            # producto es otra cosa que la nombra ("Púa de guitarra").
            continue
        if mejor is None or m.start() < mejor[1]:
            mejor, empate = (sub, m.start()), False
        elif m.start() == mejor[1] and sub != mejor[0]:
            empate = True
    if mejor is None:
        if residual:
            return residual, "residual"
        return None, "ninguna regla"
    if empate:
        return None, "empate"
    return mejor[0], "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--categorias", nargs="*", help="solo estas categorías")
    ap.add_argument("--corregir", action="store_true",
                    help="además, arregla las subcategorías de CORRECCIONES")
    ap.add_argument("--muestra", type=int, default=6,
                    help="cuántos ejemplos imprimir por subcategoría")
    args = ap.parse_args()

    data = load_catalog()
    declaradas = {c["id"]: {s["id"] for s in c.get("subcategories", [])}
                  for c in data["categories"]}

    # Ninguna regla puede nombrar una subcategoría que la categoría no tiene.
    errores = []
    for cat, reglas in REGLAS.items():
        if cat not in declaradas:
            errores.append(f"{cat}: la categoría no existe")
            continue
        for sub, _, _ambito in reglas:  # noqa: B007
            if sub not in declaradas[cat]:
                errores.append(f"{cat}: no declara la subcategoría {sub!r}")
    for cat, fn in REGLAS_ESPECIALES.items():
        for sub in ("Hasta 10,000 mAh", "10,000 a 20,000 mAh", "Más de 20,000 mAh"):
            if cat in declaradas and sub not in declaradas[cat]:
                errores.append(f"{cat}: no declara la subcategoría {sub!r}")
    if errores:
        print("Reglas que no cuadran con el catálogo:")
        for e in errores:
            print("  -", e)
        return 1

    objetivo = set(args.categorias) if args.categorias else (
        set(REGLAS) | set(REGLAS_ESPECIALES))
    puestas = collections.Counter()
    motivos = collections.Counter()
    ejemplos = collections.defaultdict(list)
    sin_tocar = collections.defaultdict(list)

    for p in data["products"]:
        if p["category"] not in objetivo or p.get("subcategory"):
            continue
        sub, motivo = subcategoria_de(p["category"], p["name"], p.get("brand", ""))
        if sub is None:
            motivos[(p["category"], motivo)] += 1
            if len(sin_tocar[p["category"]]) < args.muestra:
                sin_tocar[p["category"]].append(f"[{motivo}] {p['name'][:66]}")
            continue
        puestas[(p["category"], sub)] += 1
        if len(ejemplos[(p["category"], sub)]) < args.muestra:
            ejemplos[(p["category"], sub)].append(p["name"][:66])
        if not args.dry_run:
            p["subcategory"] = sub

    for cat in sorted(objetivo):
        filas = [(s, n) for (c, s), n in puestas.items() if c == cat]
        if not filas and cat not in sin_tocar:
            continue
        quedan = sum(n for (c, _), n in motivos.items() if c == cat)
        print(f"\n=== {cat}: clasificados {sum(n for _, n in filas):,}, "
              f"quedan sin subcategoría {quedan:,}")
        for sub, n in sorted(filas, key=lambda x: -x[1]):
            print(f"   {n:6,}  {sub}")
            for e in ejemplos[(cat, sub)][:2]:
                print(f"           {e}")
        detalle = [(m, n) for (c, m), n in motivos.items() if c == cat]
        if detalle:
            print("   sin clasificar por:",
                  ", ".join(f"{m} {n:,}" for m, n in sorted(detalle, key=lambda x: -x[1])))
            for e in sin_tocar[cat][:3]:
                print("          ", e)

    corregidos = collections.Counter()
    if args.corregir:
        # Las subcategorías que salen de una MEDIDA del nombre (los tramos de
        # mAh) se recalculan siempre, tengan o no una puesta: son una función
        # del título, así que si no coinciden es que alguna quedó de una
        # versión anterior de la regla. Pasó con el corte de los 10,000
        # justos, que antes caía en el tramo de arriba.
        for p in data["products"]:
            medir = REGLAS_ESPECIALES.get(p["category"])
            if not medir:
                continue
            nueva = medir(norm(p["name"]))
            if not nueva or nueva == p.get("subcategory"):
                continue
            if nueva not in declaradas[p["category"]]:
                continue
            corregidos[(p["category"], p.get("subcategory"), nueva)] += 1
            if not args.dry_run:
                p["subcategory"] = nueva

        for p in data["products"]:
            for desde, hacia, rx in CORRECCIONES_COMPILADAS.get(p["category"], []):
                if p.get("subcategory") != desde or not rx.search(norm(p["name"])):
                    continue
                if hacia not in declaradas[p["category"]]:
                    print(f"AVISO: {p['category']} no declara {hacia!r}, se omite")
                    break
                corregidos[(p["category"], desde, hacia)] += 1
                if not args.dry_run:
                    p["subcategory"] = hacia
                break
        for (cat, desde, hacia), n in corregidos.most_common():
            print(f"\nCorregidos en {cat}: {n:,} de {desde!r} a {hacia!r}")

    total = sum(puestas.values()) + sum(corregidos.values())
    print(f"\nTotal clasificados: {sum(puestas.values()):,}"
          + (f", corregidos: {sum(corregidos.values()):,}" if args.corregir else ""))
    if args.dry_run:
        print("(--dry-run: no se escribió nada)")
        return 0
    if total:
        save_catalog(data)
        print("Catálogo guardado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
