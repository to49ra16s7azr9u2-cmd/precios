"""Las tiendas que corren sobre VTEX, con la misma API pública de catálogo
que Elektra, y cómo se mapea el árbol de cada una a las categorías del sitio.

POR QUÉ
-------
Elektra (70,000 productos, el 85% del catálogo) entró y se refresca todos
los días por `/api/catalog_system/pub/products/search`, la API pública del
motor VTEX. Ese motor lo usan más tiendas mexicanas: se probaron 30
dominios de retail y responden con el mismo JSON (precio, existencia por
vendedor, marca, foto, ficha técnica y EAN) Chedraui y Martí. Liverpool,
Coppel, Walmart, Sanborns, Innovasport, etc. no.

Cada tienda VTEX nueva cuesta lo que hay acá: dominio, ids de categoría y
a qué categoría del sitio va cada una. El importador
(add_vtex_products.py) y el refresco diario (refresh_vtex.py) son los
mismos para todas, Elektra incluida --add_elektra_products.py y
refresh_elektra.py siguen existiendo por sus clasificadores y por el
workflow, pero el refresco de Elektra ya pasa por acá.

QUÉ ENTRA Y QUÉ NO
------------------
Mismo criterio que se fue fijando con Elektra (ver las notas de su
CATEGORY_MAP): nada de ropa ni calzado, ni consumibles (alimentos,
papelería, perfumes, limpieza, lubricantes, suplementos), ni bolsas,
mochilas o lentes. Por eso de Chedraui no entra Supermercado, Farmacia,
Belleza, Papelería ni Moda, y de Martí --que es dos tercios ropa y
tenis-- entra solo el equipo deportivo, las bicicletas y motos y el
campismo. Tampoco entran Cocina (ollas, vajillas) ni Decoración de
Chedraui: no hay categoría del sitio donde se comparen.

CÓMO SE CLASIFICA
-----------------
Igual que en Elektra: una categoría de la tienda va o a una tupla fija
(categoría, subcategoría, icono) o a una función nombre -> tupla | None
cuando la categoría de la tienda mezcla cosas (None = no es algo que el
sitio compare; se descarta). Las funciones reutilizan las de
add_elektra_products.py, que ya conocen el vocabulario de los títulos en
español, y agregan lo que Chedraui/Martí nombran distinto.
"""
import re

from add_elektra_products import (  # noqa: E402
    CATEGORY_MAP as ELEKTRA_MAP, PRESETS as ELEKTRA_PRESETS,
    JUNK_RE, REFACCIONES_AUTO_PATHS, REFACCIONES_JUNK_RE,
    cat_audio, cat_auto_accesorios, cat_bano, cat_celulares,
    cat_climatizacion, cat_cocina, cat_computo_accesorios, cat_deportes,
    cat_electrodomesticos, cat_herr_construccion, cat_herr_manuales,
    cat_impresion, cat_juguetes, cat_material_electrico, cat_monitores_proyeccion,
    cat_muebles, cat_tabletas, cat_telefonia_accesorios, cat_tv,
    cat_videojuegos, cat_wearables, norm,
)


def _primero(name, *clasificadores):
    """El primer clasificador que reconozca el nombre."""
    for c in clasificadores:
        r = c(name)
        if r:
            return r
    return None


def con_default(clasificador, default):
    """Clasifica por nombre y, si nada engancha, cae en `default`. Solo para
    categorías de la tienda que son puras (todo lo que hay ahí ES del tipo
    del default); en las mezcladas el default sería adivinar."""
    def f(name):
        return clasificador(name) or default
    return f


def fijo(categoria, subcategoria, icono):
    return (categoria, subcategoria, icono)


# Accesorios que se cuelan en categorías "del aparato en sí".
ACCESORIO_RE = re.compile(
    r"\bfunda|\bmica\b|protector|cristal templado|vidrio templado|\bcable\b|"
    r"cargador|\bsoporte\b|\bbase\b|\bcorrea\b|estuche|\bholder\b|adaptador|"
    r"\bcase\b|\bcover\b|popsocket|\bstylus\b|\blapiz\b|\bpluma\b",
    re.I,
)


# ---------------------------------------------------------------------------
# Chedraui
# ---------------------------------------------------------------------------

def ch_computacion(name):
    n0 = norm(name)
    # "Tablet Lenovo ... +Teclado+Pluma" es una tablet, no un teclado: si el
    # título ARRANCA nombrando la tablet, el accesorio incluido no manda.
    if re.match(r"(tablet|ipad)\b", n0):
        return "Tabletas", ("Apple (iPad)" if "ipad" in n0 or "apple" in n0 else "Android"), "tablet"
    r = _primero(name, cat_tabletas, cat_impresion, cat_monitores_proyeccion, cat_computo_accesorios)
    if r:
        return r
    n = norm(name)
    gamer = "gamer" in n or "gaming" in n
    if any(k in n for k in ("laptop", "notebook", "macbook", "chromebook", "portatil")):
        return "Laptops", ("Gamer" if gamer else "Oficina"), "laptop"
    if "all in one" in n or re.search(r"\baio\b", n):
        return "Computadoras de escritorio", "All in One", "desktop"
    if "mini pc" in n:
        return "Computadoras de escritorio", "Mini PC", "desktop"
    if any(k in n for k in ("computadora", "pc gamer", "desktop", "gabinete con", "cpu ")):
        return "Computadoras de escritorio", "Torre", "desktop"
    if any(k in n for k in ("no break", "nobreak", "regulador de voltaje", "supresor de picos")) or re.search(r"\bups\b", n):
        return "Componentes y accesorios de PC", "Accesorios", "cpu"
    if any(k in n for k in ("tarjeta de video", "tarjeta grafica", "procesador", "tarjeta madre", "fuente de poder", "gabinete")):
        return "Componentes y accesorios de PC", "Componentes", "cpu"
    if "switch" in n and ("puerto" in n or "ethernet" in n or "gigabit" in n):
        return "Redes", "Switches", "wifi"
    return None


def ch_movilidad(name):
    n = norm(name)
    if ACCESORIO_RE.search(n) or any(k in n for k in ("casco", "llanta", "candado", "bateria para")):
        return None
    if any(k in n for k in ("scooter", "patinete", "patin electric", "patineta electric", "monopatin")):
        return "Movilidad eléctrica", "Patinetes eléctricos", "scooter"
    if any(k in n for k in ("bicicleta", "bici ", "bicimoto", "tricicleta", "triciclo")):
        return "Movilidad eléctrica", "Bicicletas eléctricas", "scooter"
    if "moto" in n:
        return "Autos, bicicletas y motos", "Motocicletas", "car"
    return None


def deporte_interior(name):
    """cat_deportes, pero dentro de una categoría de equipo deportivo: ahí
    "bicicleta" en el nombre es una bici fija/de spinning o un accesorio para
    bici (guantes, luces), nunca una bicicleta para la calle."""
    r = cat_deportes(name)
    if r and r[0] == "Autos, bicicletas y motos":
        n = norm(name)
        if any(k in n for k in ("spinning", "estatic", "fija", "indoor")):
            return "Deportes y fitness", "Bicicletas fijas", "dumbbell"
        return "Deportes y fitness", "Otros", "dumbbell"
    return r


def ch_telefonia(name):
    n = norm(name)
    r = _primero(name, cat_wearables, cat_telefonia_accesorios)
    if r:
        return r
    if ACCESORIO_RE.search(n):
        return None
    if re.search(r"\b(celular|smartphone|iphone|telefono|galaxy [a-z]\d|redmi|motorola|xiaomi|moto g)\b", n):
        return cat_celulares(name)
    return None


def ch_tv(name):
    return cat_tv(name)


def ch_casa_inteligente(name):
    n = norm(name)
    if "camara" in n:
        return "Cámaras de seguridad", None, "security-cam"
    if "timbre" in n:
        return "Cámaras de seguridad", "Timbres inteligentes", "security-cam"
    if "cerradura" in n:
        return "Domótica y hogar inteligente", "Cerraduras inteligentes", "house"
    if any(k in n for k in ("foco", "tira led", "lampara", "bombilla")):
        return "Iluminación", "Focos inteligentes", "bulb"
    if "enchufe" in n or "contacto inteligente" in n or "clavija inteligente" in n:
        return "Domótica y hogar inteligente", "Enchufes inteligentes", "house"
    if "interruptor" in n or "apagador" in n:
        return "Domótica y hogar inteligente", "Interruptores inteligentes", "house"
    if any(k in n for k in ("echo", "alexa", "google nest", "nest mini", "bocina inteligente", "asistente")):
        return "Domótica y hogar inteligente", "Bocinas inteligentes", "house"
    if "sensor" in n:
        return "Cámaras de seguridad", "Sensores", "security-cam"
    if "alarma" in n:
        return "Cámaras de seguridad", "Alarmas", "security-cam"
    return None


_GAMER_RE = re.compile(r"xbox|playstation|\bps[45]\b|nintendo|switch|steam deck|videojuego|consola|\bjuego\b")


def ch_mundo_geek(name):
    n = norm(name)
    if "barra de luz" in n or "pila" in n or "bateria" in n:
        return None
    if _GAMER_RE.search(n) and any(k in n for k in ("accesorio", "lector de disco", "kit ", "estuche", "base de carga", "cargador")):
        return "Videojuegos", "Accesorios", "gamepad"
    r = _primero(name, cat_monitores_proyeccion, cat_computo_accesorios)
    if r:
        return r
    if ("laptop" in n or "notebook" in n) and ("gamer" in n or "gaming" in n):
        return "Laptops", "Gamer", "laptop"
    if _GAMER_RE.search(n):
        return cat_videojuegos(name)
    return None


def ch_refrigeradores(name):
    n = norm(name)
    if any(k in n for k in ("frigobar", "minibar", "mini bar", "cava", "enfriador de vino")):
        return "Refrigeradores", "Frigobares", "fridge"
    if "congelador" in n:
        return "Refrigeradores", "Congeladores", "fridge"
    if "refrigerador" in n:
        return "Refrigeradores", "Refrigeradores", "fridge"
    return None


def ch_electrodomesticos(name):
    r = cat_electrodomesticos(name)
    if r:
        return r
    n = norm(name)
    if any(k in n for k in ("hervidor", "tetera electrica", "exprimidor", "extractor", "procesador de alimentos",
                             "picadora", "molino", "yogurtera", "fuente de chocolate", "palomera",
                             "maquina de helados", "maquina de pan", "deshidratador", "grill", "crepera",
                             "fondue", "raclette", "bascula de cocina", "abrelatas electrico")):
        return "Electrodomésticos", "Pequeños electrodomésticos de cocina", "appliance"
    return None


def ch_lavado(name):
    n = norm(name)
    if "lavasecadora" in n:
        return "Lavadoras", "Lavasecadoras", "washer"
    if "centro de lavado" in n:
        return "Lavadoras", "Centros de lavado", "washer"
    if "secadora" in n and "pelo" not in n and "cabello" not in n:
        return "Lavadoras", "Secadoras", "washer"
    if "lavadora" in n:
        if "semiautomatica" in n or "doble tina" in n:
            return "Lavadoras", "Semiautomáticas", "washer"
        if "carga frontal" in n:
            return "Lavadoras", "Carga frontal", "washer"
        if "carga superior" in n:
            return "Lavadoras", "Carga superior", "washer"
        return "Lavadoras", None, "washer"
    if "centrifugadora" in n or "exprimidora de ropa" in n:
        return "Lavadoras", None, "washer"
    return None


def ch_climatizacion(name):
    r = cat_climatizacion(name)
    if r:
        return r
    n = norm(name)
    if "humificador" in n or "difusor de aromas" in n:  # así lo escribe la tienda
        return "Climatización", "Humidificadores", "snowflake"
    if "enfriador de aire" in n or "cooler evaporativo" in n:
        return "Climatización", "Climatizadores evaporativos", "snowflake"
    if "calentador" in n and "agua" not in n:
        return "Climatización", "Calefactores", "snowflake"
    return None


def ch_agua(name):
    n = norm(name)
    if "purificador" in n or "filtro de agua" in n:
        return "Electrodomésticos", "Purificadores de agua", "appliance"
    if "dispensador" in n or "despachador" in n or "enfriador de agua" in n:
        return "Electrodomésticos", "Otros", "appliance"
    return None


def ch_planchado(name):
    n = norm(name)
    if "vaporizador" in n or "vaporera de ropa" in n:
        return "Electrodomésticos", "Vaporizadores de ropa", "appliance"
    if "plancha" in n and "cabello" not in n and "pelo" not in n:
        return "Electrodomésticos", "Planchas", "appliance"
    if "burro de planchar" in n or "mesa de planchar" in n:
        return "Otros", "Organización del hogar", "box"
    return None


def ch_recamara(name):
    n = norm(name)
    if "almohada" in n:
        return "Blancos y ropa de cama", "Almohadas", "pillow"
    if any(k in n for k in ("edredon", "cobertor", "duvet", "colcha")):
        return "Blancos y ropa de cama", "Edredones", "pillow"
    if "sabana" in n:
        return "Blancos y ropa de cama", "Sábanas", "pillow"
    if "protector de colchon" in n or "cubrecolchon" in n or "cubre colchon" in n:
        return "Blancos y ropa de cama", "Protectores de colchón", "pillow"
    if "cobija" in n or "frazada" in n or "manta" in n:
        return "Blancos y ropa de cama", "Cobijas eléctricas" if "electric" in n else "Edredones", "pillow"
    if "cortina" in n:
        return "Blancos y ropa de cama", "Cortinas", "pillow"
    return None


def ch_mejoras(name):
    r = _primero(name, cat_herr_manuales, cat_material_electrico, cat_herr_construccion)
    if r:
        return r
    n = norm(name)
    if any(k in n for k in ("taladro", "rotomartillo", "sierra", "esmeril", "pulidora", "lijadora",
                             "caladora", "atornillador", "cortadora", "router de madera", "pistola de calor",
                             "hidrolavadora", "compresor")):
        return "Herramientas", "Herramientas eléctricas", "wrench"
    if "escalera" in n:
        return "Herramientas", "Escaleras", "wrench"
    if any(k in n for k in ("llave de paso", "valvula", "tuberia", "conector de", "tinaco", "bomba de agua", "calentador de agua")):
        if "calentador" in n:
            return "Electrodomésticos", "Calentadores de agua", "appliance"
        return "Herramientas", "Plomería", "wrench"
    if "regadera" in n:
        return "Otros", "Baño", "box"
    return None


def ch_patio(name):
    n = norm(name)
    if any(k in n for k in ("podadora", "desbrozadora", "motosierra", "sopladora", "hidrolavadora",
                             "tijera de podar", "tijeras de podar", "manguera", "aspersor", "pala",
                             "rastrillo", "carretilla", "cortasetos", "orilladora", "azadon", "machete")):
        return "Herramientas", "Jardinería", "wrench"
    if "asador" in n or "parrilla de carbon" in n or "ahumador" in n:
        return "Decoración de hogar y jardín", "Asadores", "vase"
    if any(k in n for k in ("mesa", "silla", "sillon", "camastro", "sombrilla", "toldo", "gazebo", "hamaca")):
        return "Muebles", "Otros", "sofa"
    return None


def ch_juguetes(name):
    r = cat_juguetes(name)
    if r:
        return r
    n = norm(name)
    if any(k in n for k in ("muneca", "barbie", "pony", "bebe llorones", "nenuco")):
        return "Juguetes y bebés", "Muñecas", "toy"
    if any(k in n for k in ("lego", "mega bloks", "bloques", "armable", "construccion")):
        return "Juguetes y bebés", "Bloques de construcción", "toy"
    if "peluche" in n:
        return "Juguetes y bebés", "Peluches", "toy"
    if any(k in n for k in ("figura", "coleccionable", "funko", "dinosaurio", "transformers", "hot wheels")):
        return "Juguetes y bebés", "Figuras de acción", "toy"
    if "rompecabezas" in n or "puzzle" in n:
        return "Juegos de mesa", "Rompecabezas", "dice"
    if any(k in n for k in ("juego de mesa", "cartas", "monopoly", "jenga", "loteria", "domino", "ajedrez")):
        return "Juegos de mesa", "Ajedrez" if "ajedrez" in n else "Otros juegos", "dice"
    if "control remoto" in n or "radiocontrol" in n or "radio control" in n or re.search(r"\brc\b", n):
        return "Juguetes y bebés", "Vehículos a control remoto", "toy"
    if any(k in n for k in ("triciclo", "montable", "scooter", "patineta", "patines", "bicicleta")):
        return "Juguetes y bebés", "Triciclos" if "triciclo" in n else "Montables", "toy"
    if any(k in n for k in ("didactico", "educativo", "aprendizaje", "plastilina", "manualidad", "ciencia", "experimento")):
        return "Juguetes y bebés", "Juguetes educativos", "toy"
    if any(k in n for k in ("piano", "guitarra", "tambor", "xilofono", "musical")):
        return "Juguetes y bebés", "Juguetes musicales", "toy"
    if any(k in n for k in ("lanzador", "nerf", "pistola de agua", "burbujas", "alberca", "resbaladilla", "columpio")):
        return "Juguetes y bebés", "Juguetes para exterior", "toy"
    return None


def ch_acuaticos(name):
    r = cat_juguetes(name)
    if r:
        return r
    n = norm(name)
    if any(k in n for k in ("salvavidas", "flotador", "chaleco", "alberca")):
        return "Juguetes y bebés", "Juguetes para exterior", "toy"
    if any(k in n for k in ("goggle", "gogle", "visor", "aleta", "snorkel", "tabla", "gorro de natacion")):
        return "Deportes y fitness", "Otros", "dumbbell"
    return None


def ch_ciclismo(name):
    r = cat_deportes(name)
    if r:
        return r
    n = norm(name)
    if "bicicleta" in n and "electric" in n:
        return "Movilidad eléctrica", "Bicicletas eléctricas", "scooter"
    if "bicicleta" in n:
        return "Autos, bicicletas y motos", "Bicicletas", "car"
    if any(k in n for k in ("casco", "rodillera", "codera", "protector", "candado")):
        return "Deportes y fitness", "Otros", "dumbbell"
    return None


def ch_colectivos(name):
    n = norm(name)
    if "balon" in n or "pelota" in n:
        return "Deportes y fitness", "Voleibol" if "voleibol" in n or "volleyball" in n else "Balones", "dumbbell"
    if any(k in n for k in ("porteria", "red de", "canasta", "tablero", "aro de basquet", "conos", "silbato", "espinillera", "guante")):
        return "Deportes y fitness", "Otros", "dumbbell"
    return None


def ch_otros_deportes(name):
    r = cat_deportes(name)
    if r:
        return r
    n = norm(name)
    if any(k in n for k in ("raqueta", "tenis de mesa", "ping pong", "badminton", "gallito")):
        return "Deportes y fitness", "Ping pong" if "ping pong" in n or "tenis de mesa" in n else "Otros", "dumbbell"
    if any(k in n for k in ("box", "vendas", "careta", "protector bucal")):
        return "Deportes y fitness", "Boxeo", "dumbbell"
    return None


def ch_motos(name):
    n = norm(name)
    r = cat_auto_accesorios(name)
    if r:
        return r
    if any(k in n for k in ("motoneta", "motocicleta", "moto ", "scooter")) and not ACCESORIO_RE.search(n):
        return "Autos, bicicletas y motos", "Motocicletas", "car"
    return None


def ch_refacciones_auto(name):
    n = norm(name)
    if "acumulador" in n or "bateria" in n:
        return "Autos, bicicletas y motos", "Baterías para auto", "car"
    if any(k in n for k in ("gato hidraulico", "llave", "desarmador", "pinza", "juego de herramientas", "caja de herramientas", "torquimetro")):
        return "Herramientas", "Herramientas manuales", "wrench"
    if any(k in n for k in ("cables para pasar corriente", "cargador de bateria", "arrancador", "compresor")):
        return "Autos, bicicletas y motos", "Autos", "car"
    return "Refacciones", "Para autos", "gear"


def ch_seguridad_auto(name):
    n = norm(name)
    r = cat_auto_accesorios(name)
    if r:
        return r
    if any(k in n for k in ("alarma", "bloqueador", "candado", "baston", "camara de reversa", "dash cam", "dashcam", "sensor de reversa")):
        return "Autos, bicicletas y motos", "Autos", "car"
    return None


CHEDRAUI_MAP = {
    # Tecnología
    "8/801": fijo("Instrumentos musicales", None, "guitar"),
    "8/802": ch_movilidad,
    "8/804": ch_computacion,
    "8/805": ch_tv,
    "8/806": ch_telefonia,
    "8/807": cat_audio,
    "8/808": ch_casa_inteligente,
    "8/810": ch_mundo_geek,
    # Electrodomésticos y línea blanca
    "13/1301": ch_refrigeradores,
    "13/1302": ch_electrodomesticos,
    "13/1303": cat_cocina,
    "13/1304": cat_electrodomesticos,   # solo "aspiradora ..." engancha; los accesorios no
    "13/1305": ch_lavado,
    "13/1306": ch_climatizacion,
    "13/1307": ch_agua,
    "13/1308": ch_planchado,
    "13/1309": ch_climatizacion,
    "13/1310": ch_climatizacion,
    # Hogar y jardín (Cocina 7/701 y Decoración 7/707 se dejan fuera a
    # propósito: ollas, vajillas y adornos no tienen categoría donde
    # compararse en el sitio)
    "7/703": cat_bano,
    "7/706": cat_muebles,
    "7/712": ch_patio,
    "7/717": ch_recamara,
    "7/718": ch_mejoras,
    # Juguetería: categorías puras, con default por tipo
    "10/1003": con_default(ch_juguetes, ("Juguetes y bebés", "Muñecas", "toy")),
    "10/1004": con_default(ch_juguetes, ("Juguetes y bebés", "Juguetes educativos", "toy")),
    "10/1005": con_default(ch_juguetes, ("Juguetes y bebés", "Figuras de acción", "toy")),
    "10/1009": con_default(ch_juguetes, ("Juguetes y bebés", "Bloques de construcción", "toy")),
    "10/1010": con_default(ch_juguetes, ("Juegos de mesa", "Otros juegos", "dice")),
    "10/1011": con_default(ch_juguetes, ("Juguetes y bebés", "Juguetes para exterior", "toy")),
    "10/1013": con_default(ch_juguetes, ("Juguetes y bebés", "Otros", "toy")),
    "10/1014": con_default(ch_juguetes, ("Juguetes y bebés", "Bebés", "toy")),
    "10/1015": con_default(ch_juguetes, ("Juguetes y bebés", "Peluches", "toy")),
    # Deportes
    "15/1501": fijo("Viajes", "Camping", "suitcase"),
    "15/1502": ch_acuaticos,
    "15/1503": ch_ciclismo,
    "15/1504": con_default(deporte_interior, ("Deportes y fitness", "Otros", "dumbbell")),
    "15/1505": ch_colectivos,
    "15/1506": ch_otros_deportes,
    "15/1508": fijo("Viajes", "Maletas", "suitcase"),
    # Automóviles y motos (Limpieza 16/1602 y Lubricantes 16/1604 son
    # consumibles: fuera)
    "16/1601": cat_auto_accesorios,
    "16/1603": fijo("Autos, bicicletas y motos", "Llantas", "car"),
    "16/1605": ch_motos,
    "16/1606": ch_refacciones_auto,
    "16/1607": ch_seguridad_auto,
}

CHEDRAUI_PRESETS = {
    "tecnologia": [p for p in CHEDRAUI_MAP if p.startswith("8/")],
    "electrodomesticos": [p for p in CHEDRAUI_MAP if p.startswith("13/")],
    "hogar": [p for p in CHEDRAUI_MAP if p.startswith("7/")],
    "jugueteria": [p for p in CHEDRAUI_MAP if p.startswith("10/")],
    "deportes": [p for p in CHEDRAUI_MAP if p.startswith("15/")],
    "autos": [p for p in CHEDRAUI_MAP if p.startswith("16/")],
}
CHEDRAUI_PRESETS["todo"] = list(CHEDRAUI_MAP)


# ---------------------------------------------------------------------------
# Martí
# ---------------------------------------------------------------------------

def mt_relojes(name):
    n = norm(name)
    if any(k in n for k in ("gps", "smart", "garmin", "polar", "suunto", "coros", "amazfit", "fitbit", "apple watch", "galaxy watch")):
        return "Relojes inteligentes", "Smartwatches", "watch"
    if ACCESORIO_RE.search(n):
        return None
    return "Joyería y bisutería", "Relojes", "ring"


def mt_bicicletas(name):
    n = norm(name)
    if ACCESORIO_RE.search(n):
        return None
    if "electric" in n:
        return "Movilidad eléctrica", "Bicicletas eléctricas", "scooter"
    if "bicicleta" in n or "bici " in n or re.search(r"\brodada\b|\br\d\d\b", n):
        return "Autos, bicicletas y motos", "Bicicletas", "car"
    return None


def mt_rodantes(name):
    """Patines, patinetas y scooters: eléctricos a Movilidad, el resto a deportes."""
    return deporte_interior(name) or ("Deportes y fitness", "Otros", "dumbbell")


DEPORTE_OTROS = ("Deportes y fitness", "Otros", "dumbbell")
PESAS = ("Deportes y fitness", "Pesas", "dumbbell")
CAMPING = ("Viajes", "Camping", "suitcase")

MARTI_MAP = {
    # Accesorios: solo el equipo deportivo (gorras, calcetas, cinturones,
    # mochilas, bolsas, lentes, termos, navajas, etc. quedan fuera)
    "82/119": con_default(ch_colectivos, ("Deportes y fitness", "Balones", "dumbbell")),
    "82/126": con_default(deporte_interior, DEPORTE_OTROS),  # guantes (box, portero, béisbol, ciclismo)
    "82/127": DEPORTE_OTROS,                                  # manoplas
    "82/131": con_default(ch_otros_deportes, DEPORTE_OTROS),  # raquetas
    "82/128": con_default(ch_otros_deportes, DEPORTE_OTROS),  # paletas
    "82/121": DEPORTE_OTROS,                                  # bats
    "82/125": DEPORTE_OTROS, "82/135": DEPORTE_OTROS, "82/118": DEPORTE_OTROS,  # goggles, visores, aletas
    "82/133": DEPORTE_OTROS, "82/134": DEPORTE_OTROS, "82/228": DEPORTE_OTROS,  # snorkels, tablas, gorras de natación
    "82/84": DEPORTE_OTROS, "82/89": DEPORTE_OTROS, "82/90": DEPORTE_OTROS,     # espinilleras, caretas, cascos
    "82/96": DEPORTE_OTROS, "82/224": DEPORTE_OTROS, "82/94": DEPORTE_OTROS,    # rodilleras, coderas, bucales
    "82/92": DEPORTE_OTROS, "82/88": DEPORTE_OTROS, "82/87": DEPORTE_OTROS,     # muñequeras, tobilleras, vendas
    "82/83": ("Deportes y fitness", "Boxeo", "dumbbell"),   # conchas
    "82/175": PESAS, "82/171": PESAS, "82/120": PESAS, "82/174": PESAS, "82/138": PESAS,  # pesas, discos, barras, ligas, bandas
    "82/172": PESAS,                                                            # ejercitadores
    "82/170": ("Deportes y fitness", "Yoga", "dumbbell"),            # tapetes
    "82/150": DEPORTE_OTROS,                                                    # cuerdas
    "82/100": CAMPING, "82/223": CAMPING, "82/105": CAMPING, "82/382": CAMPING, "82/332": CAMPING,
    "82/144": ("Viajes", "Maletas", "suitcase"),
    "82/199": ("Salud", "Básculas", "heart-pulse"),
    "82/236": cat_audio,
    "82/391": mt_relojes,
    "82/377": ("Belleza y cuidado personal", "Masajeadores", "sparkle"),
    "82/146": ("Cámaras y fotografía", "Accesorios", "camera"),                # binoculares
    "82/154": None,  # portacelulares: accesorio
    # Equipamiento
    "8/9": con_default(deporte_interior, ("Deportes y fitness", "Equipo de gimnasio", "dumbbell")),
    "8/149": ("Deportes y fitness", "Boxeo", "dumbbell"),   # costales
    "8/368": ("Deportes y fitness", "Boxeo", "dumbbell"),   # peras
    "8/188": DEPORTE_OTROS,                                                     # kayaks
    "8/293": ("Deportes y fitness", "Ping pong", "dumbbell"),
    "8/292": DEPORTE_OTROS, "8/309": DEPORTE_OTROS, "8/335": DEPORTE_OTROS,     # tableros, mesas, asientos
    "8/399": PESAS, "8/402": PESAS, "8/380": PESAS,                             # mancuernas, bloques, racks
    "8/158": ("Autos, bicicletas y motos", "Autos", "car"),                    # porta bicicletas
    # Movilidad
    "413/435": mt_bicicletas,
    "413/436": ch_motos,
    "413/437": mt_rodantes, "413/438": mt_rodantes, "413/439": mt_rodantes,
    "413/440": ("Juguetes y bebés", "Montables", "toy"),
    "413/441": ("Juguetes y bebés", "Montables", "toy"),
    # Entretenimiento
    "412/433": ("Cámaras y fotografía", "Accesorios", "camera"),               # telescopios
    "412/434": ("Juguetes y bebés", "Trampolines", "toy"),
    "412/432": ("Juguetes y bebés", "Juguetes para exterior", "toy"),
}
MARTI_MAP = {k: v for k, v in MARTI_MAP.items() if v is not None}

MARTI_PRESETS = {
    "accesorios": [p for p in MARTI_MAP if p.startswith("82/")],
    "equipamiento": [p for p in MARTI_MAP if p.startswith("8/")],
    "movilidad": [p for p in MARTI_MAP if p.startswith("413/")],
    "entretenimiento": [p for p in MARTI_MAP if p.startswith("412/")],
}
MARTI_PRESETS["todo"] = list(MARTI_MAP)


# ---------------------------------------------------------------------------
# Juguetrón (juguetron.mx): juguetería, todo el árbol es juguete
# ---------------------------------------------------------------------------
# El árbol tiene dos mitades: las categorías de tipo de juguete (2..15) y
# un montón de nodos de LICENCIA (Lego, Marvel, Star Wars, Disney...) que
# repiten los mismos productos agrupados por marca. Solo se recorren las
# primeras: entrar por las licencias traería los mismos ids otra vez y
# add_vtex_products ya descarta duplicados, pero serían miles de
# peticiones para nada.

def jt_creatividad(name):
    """La rama "Creatividad y Arte" mezcla el set de manualidades con el
    llavero y la libreta de la misma licencia. Solo entra lo que es un
    juguete: lo demás es papelería o baratija, que el sitio no compara."""
    n = norm(name)
    if any(k in n for k in ("maquillaje", "belleza", "uñas", "unas postizas", "esmalte",
                            "llavero", "libreta", "cuaderno", "pluma", "lapiz", "boligrafo",
                            "sticker", "calcomania", "mochila", "bolsa", "cartuchera")):
        return None
    if "rompecabezas" in n or "puzzle" in n:
        return "Juegos de mesa", None, "toy"
    if any(k in n for k in ("masa", "play-doh", "plastilina", "slime", "arena magica")):
        return "Juguetes y bebés", "Juguetes educativos", "toy"
    if any(k in n for k in ("pintura", "pinta", "dibujo", "acuarela", "crayon", "gis",
                            "manualidad", "kit de", "set de", "ciencia", "experimento",
                            "microscopio", "telescopio")):
        return "Juguetes y bebés", "Juguetes educativos", "toy"
    return None


def jt_aire_libre(name):
    n = norm(name)
    if "bicicleta" in n or "triciclo" in n:
        return "Juguetes y bebés", "Triciclos" if "triciclo" in n else "Otros", "toy"
    if "patin" in n or "scooter" in n or "patineta" in n:
        return "Juguetes y bebés", "Montables", "toy"
    if "balon" in n or "pelota" in n:
        return "Deportes y fitness", "Balones", "dumbbell"
    if "alberca" in n or "inflable" in n or "casa de juego" in n or "resbaladilla" in n:
        return "Juguetes y bebés", "Juguetes para exterior", "toy"
    return "Juguetes y bebés", "Juguetes para exterior", "toy"


def jt_gadgets(name):
    n = norm(name)
    if "radio control" in n or "radiocontrol" in n or "dron" in n:
        return "Juguetes y bebés", "Vehículos a control remoto", "toy"
    return "Juguetes y bebés", "Otros", "toy"


def jt_bebes(name):
    n = norm(name)
    if "carriola" in n:
        return "Juguetes y bebés", "Carriolas", "toy"
    if "montable" in n or "andadera" in n:
        return "Juguetes y bebés", "Montables", "toy"
    if "peluche" in n or "abrazable" in n:
        return "Juguetes y bebés", "Peluches", "toy"
    return "Juguetes y bebés", "Bebés", "toy"


JUGUETRON_MAP = {
    "2": jt_creatividad,
    "3": fijo("Juegos de mesa", None, "toy"),
    "4": fijo("Juguetes y bebés", "Bloques de construcción", "toy"),
    "5": jt_gadgets,
    "6": fijo("Juguetes y bebés", "Juguetes educativos", "toy"),
    "9": jt_bebes,
    "10": fijo("Juguetes y bebés", "Figuras de acción", "toy"),
    "11": jt_aire_libre,
    "12": fijo("Juguetes y bebés", "Muñecas", "toy"),
    "13": fijo("Juguetes y bebés", "Vehículos a control remoto", "toy"),
    "14": fijo("Juguetes y bebés", "Juguetes para exterior", "toy"),
    "15": fijo("Juguetes y bebés", "Peluches", "toy"),
}

JUGUETRON_PRESETS = {"todo": list(JUGUETRON_MAP)}


# ---------------------------------------------------------------------------
# Miniso (miniso.com.mx): variedades; entra lo que el sitio ya compara
# ---------------------------------------------------------------------------
# De su árbol quedan fuera Moda (6), Salud y Belleza (5), Papelería (9),
# Snacks (408), Viajes (12: casi todo bolsas y neceseres) y Temporada (10),
# por el mismo criterio que rige a Chedraui: ropa, cosméticos, consumibles
# y bolsas no tienen dónde compararse acá.

def mn_hogar(name):
    n = norm(name)
    if "lampara" in n or "luz led" in n:
        return "Iluminación", "Lámparas de escritorio", "bulb"
    if "cojin" in n or "manta" in n or "cobija" in n or "almohada" in n:
        return "Blancos y ropa de cama", "Almohadas" if "almohada" in n else "Cobijas", "pillow"
    if "organizador" in n or "caja" in n or "cesto" in n or "canasta" in n:
        return "Otros", "Organización del hogar", "box"
    if "espejo" in n or "cortina de bano" in n or "jabonera" in n or "cepillo de dientes" in n:
        return cat_bano(name)
    return None


def mn_tecnologia(name):
    n = norm(name)
    if "bocina" in n or "altavoz" in n:
        return "Bocinas", None, "speaker"
    if "audifono" in n or "auricular" in n:
        return "Audífonos", None, "headphones"
    if "cable" in n:
        return "Cargadores y adaptadores", "Cable", "plug"
    if "cargador" in n or "adaptador" in n:
        return "Cargadores y adaptadores", "De pared", "plug"
    if "power bank" in n or "bateria portatil" in n:
        return "Baterías portátiles", None, "battery"
    if "mouse" in n or "teclado" in n or "mousepad" in n:
        return cat_computo_accesorios(name)
    return cat_telefonia_accesorios(name)


MINISO_MAP = {
    "4/38": mn_hogar,
    "4/47": cat_bano,
    "4/53": mn_hogar,
    "4/409": fijo("Otros", "Organización del hogar", "box"),
    "4/427": fijo("Iluminación", "Lámparas de escritorio", "bulb"),
    "8": cat_juguetes,
    "11": mn_tecnologia,
    "54": fijo("Mascotas", None, "paw"),
    "49/58": None,   # vasos y termos: consumo, sin categoría donde comparar
}
MINISO_MAP = {k: v for k, v in MINISO_MAP.items() if v is not None}
MINISO_PRESETS = {"todo": list(MINISO_MAP)}


# ---------------------------------------------------------------------------
# Gandhi (gandhi.com.mx): libros
# ---------------------------------------------------------------------------
# Gandhi obliga a una decisión: el sitio no tiene categoría de Libros. Se
# agrega, porque el libro es el producto que MEJOR se compara de todo el
# catálogo -- el ISBN es el mismo en todas las tiendas, así que dos ofertas
# del mismo libro son el mismo objeto sin necesidad de firma ni de adivinar.
# Es lo contrario de lo que pasa con los electrodomésticos.
#
# Ebooks (2) y Audiolibros (3) quedan fuera: son licencias, no objetos, y no
# se comparan por precio entre tiendas de la misma manera. Los nodos de
# Colegio (261) son listas escolares, no catálogo.

def gd_accesorios(name):
    n = norm(name)
    if "juego" in n or "rompecabezas" in n or "puzzle" in n:
        return "Juegos de mesa", None, "toy"
    if "funda" in n or "cubierta" in n:
        return None
    return None


GANDHI_MAP = {
    "1/12": fijo("Libros", "Literatura y novela", "book"),
    "1/13": fijo("Libros", "Juvenil", "book"),
    "1/14": fijo("Libros", "Literatura y novela", "book"),
    "1/15": fijo("Libros", "Cómic y manga", "book"),
    "1/16": fijo("Libros", "Infantil", "book"),
    "1/17": fijo("Libros", "No ficción", "book"),
    "1/18": fijo("Libros", "Ciencia", "book"),
    "1/19": fijo("Libros", "Estilo de vida", "book"),
    "1/20": fijo("Libros", "Arte", "book"),
    "1/21": fijo("Libros", "Gastronomía", "book"),
    "1/22": fijo("Libros", "Especializados", "book"),
    "253/254": fijo("Tabletas", "Lectores electrónicos", "tablet"),
    "4/201": gd_accesorios,
}
GANDHI_MAP = {k: v for k, v in GANDHI_MAP.items() if v is not None}
GANDHI_PRESETS = {
    "libros": [p for p in GANDHI_MAP if p.startswith("1/")],
    "todo": list(GANDHI_MAP),
}


# ---------------------------------------------------------------------------
# Registro
# ---------------------------------------------------------------------------

TIENDAS = {
    "elektra": {
        "nombre": "Elektra",
        "dominio": "www.elektra.mx",
        "categorias": ELEKTRA_MAP,
        "presets": ELEKTRA_PRESETS,
        "refacciones_auto": REFACCIONES_AUTO_PATHS,
        # Entrada en data.json -> stores (la que ya existe se respeta).
        "store": {"id": "elektra", "name": "Elektra", "hubRegion": None,
                  "color": "#E30613", "logo": "EL", "typicalShippingDays": [3, 10]},
    },
    "chedraui": {
        "nombre": "Chedraui",
        "dominio": "www.chedraui.com.mx",
        "categorias": CHEDRAUI_MAP,
        "presets": CHEDRAUI_PRESETS,
        "refacciones_auto": {"16/1606"},
        "store": {"id": "chedraui", "name": "Chedraui", "hubRegion": None,
                  "color": "#F47920", "logo": "CH", "typicalShippingDays": [3, 10]},
    },
    "marti": {
        "nombre": "Martí",
        "dominio": "www.marti.mx",
        "categorias": MARTI_MAP,
        "presets": MARTI_PRESETS,
        "refacciones_auto": set(),
        "store": {"id": "marti", "name": "Martí", "hubRegion": None,
                  "color": "#D31F2A", "logo": "MT", "typicalShippingDays": [3, 8]},
    },
    "juguetron": {
        "nombre": "Juguetrón",
        "dominio": "www.juguetron.mx",
        "categorias": JUGUETRON_MAP,
        "presets": JUGUETRON_PRESETS,
        "refacciones_auto": set(),
        "store": {"id": "juguetron", "name": "Juguetrón", "hubRegion": None,
                  "color": "#00A3E0", "logo": "JT", "typicalShippingDays": [3, 8]},
    },
    "miniso": {
        "nombre": "Miniso",
        "dominio": "www.miniso.com.mx",
        "categorias": MINISO_MAP,
        "presets": MINISO_PRESETS,
        "refacciones_auto": set(),
        "store": {"id": "miniso", "name": "Miniso", "hubRegion": None,
                  "color": "#E60012", "logo": "MN", "typicalShippingDays": [3, 8]},
    },
    "gandhi": {
        "nombre": "Gandhi",
        "dominio": "www.gandhi.com.mx",
        "categorias": GANDHI_MAP,
        "presets": GANDHI_PRESETS,
        "refacciones_auto": set(),
        "store": {"id": "gandhi", "name": "Gandhi", "hubRegion": None,
                  "color": "#F5A800", "logo": "GA", "typicalShippingDays": [2, 7]},
    },
}

# Para quien solo necesita saber si una tienda es VTEX (record_price_history).
TIENDAS_VTEX = frozenset(TIENDAS)


def search_url(store_id):
    return f"https://{TIENDAS[store_id]['dominio']}/api/catalog_system/pub/products/search"


def junk_re_de(store_id, path):
    """El filtro de nombres que aplica a esta categoría de esta tienda: las
    de refacciones de auto solo filtran servicios (ver add_elektra_products)."""
    if path in TIENDAS[store_id]["refacciones_auto"]:
        return REFACCIONES_JUNK_RE
    return JUNK_RE


def resolver(mapping, name):
    """(categoría, subcategoría, icono) para un nombre, según el mapeo de la
    categoría de la tienda (tupla fija o clasificador), o None."""
    if callable(mapping):
        return mapping(name)
    return mapping
