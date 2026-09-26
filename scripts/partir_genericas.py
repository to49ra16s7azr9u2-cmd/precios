#!/usr/bin/env python3
"""Parte las subcategorías comodín («Accesorios», «Refacciones para X»,
«Otros») en subcategorías con el NOMBRE de la pieza o el accesorio.

POR QUÉ (25-sep-2026, noche)
----------------------------
El usuario pidió que no quede ninguna categoría «Accesorios»: que cada
parte o accesorio tenga la suya, con su nombre («Fundas para audífonos»,
«Soportes para monitor», «Guantes para moto»). Había 99 subcategorías
comodín con ~31 mil fichas, más «Para autos» y «Para motos» en Autopartes.

CÓMO
----
1. REGLAS a mano (REGLAS): lo que en una comodín es de otra categoría o
   tiene nombre conocido («Radio Android para Mazda» en Autopartes/Para
   autos es un estéreo; «Kit original ag» son resortes de suspensión).
2. CABEZA: el primer sustantivo del título, saltando marcas y palabras de
   relleno («kit», «set», «para»...). Cada cabeza con MIN_GRUPO fichas o más
   se vuelve una subcategoría: plural de la cabeza + el contexto de la
   comodín («Soporte» en «Accesorios de monitor» -> «Soportes para monitor»).
   SINONIMOS junta cabezas que son lo mismo (estuche/case -> funda).
3. RESTO: lo que no alcanza grupo propio lo pone el MODELO (bayesiano sobre
   nombres, el de detectar_mal_clasificados.py) en la subcategoría con nombre
   más parecida de la misma categoría, entrenado con las fichas que ya
   tienen subcategoría con nombre, las nuevas de este mismo reparto y los
   ejemplos verificados a mano (ejemplos_verificados.py) con más peso. El
   modelo se reentrena en cada corrida: crece con el catálogo.

--informe escribe la propuesta (subcategorías nuevas con muestra, y adónde
va el resto) para revisarla; --aplicar la guarda: mueve las fichas, quita
las comodín del manifiesto, agrega las nuevas y deja data/particion-
genericas.json con la tabla cabeza -> subcategoría, que usan las altas
siguientes y las redirecciones de 404.html.

USO
---
    python3 scripts/partir_genericas.py --informe /tmp/partir.json
    python3 scripts/partir_genericas.py --aplicar
"""
import argparse
import collections
import io
import json
import os
import random
import re
import sys
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
from data_io import load_catalog, save_catalog  # noqa: E402
from detectar_mal_clasificados import Bayes, tokens  # noqa: E402

TABLA = os.path.join(ROOT, "data", "particion-genericas.json")
CANDADO = os.path.join(ROOT, "data", "clasificacion-a-mano.json")
MIN_GRUPO = 12
MARGEN_RESTO = 7.0      # nats sobre la segunda subcategoría

# «otras» no: «Violines, mandolinas y otras cuerdas» y «Juegos retro y otras
# plataformas» ya nombran lo que tienen.
RX_GENERICA = re.compile(r"\b(accesorios?|refacciones|repuestos|partes)\b|^(otros|varios)\b|^para (autos|motos)$", re.I)
# Subcategorías que dicen «accesorios» pero ya nombran la cosa: se quedan.
NO_GENERICAS = {
    ("Electrodomésticos", "Filtros y membranas de repuesto"),
    ("Blancos y ropa de cama", "Accesorios de baño"),
    ("Ropa y accesorios", "Ropa y accesorios"),
}

# Contexto que se agrega al nombre de la pieza, por comodín sin «para X».
CONTEXTO = {
    ("Celulares", "Accesorios"): "para celular",
    ("Audífonos", "Accesorios"): "para audífonos",
    ("Audífonos", "Almohadillas y repuestos"): "para audífonos",
    ("Cámaras y fotografía", "Accesorios"): "para cámara",
    ("Componentes y accesorios de PC", "Accesorios"): "para PC",
    ("Componentes y accesorios de PC", "Accesorios de monitor"): "para monitor",
    ("Componentes y accesorios de PC", "Accesorios de memoria"): "para memoria",
    ("Instrumentos musicales", "Accesorios"): "para instrumentos",
    ("Instrumentos musicales", "Accesorios de guitarra"): "para guitarra",
    ("Instrumentos musicales", "Boquillas, cañas y accesorios de viento"): "para instrumentos de viento",
    ("Instrumentos musicales", "Fundas y accesorios de batería"): "para batería",
    ("Instrumentos musicales", "Bancos, soportes y accesorios de teclado"): "para teclado",
    ("Aspiradoras", "Accesorios"): "para aspiradora",
    ("Proyectores y accesorios", "Otros accesorios de proyector"): "para proyector",
    ("Proyectores y accesorios", "Accesorios"): "para proyector",
    ("Televisores", "Accesorios y soportes"): "para TV",
    ("Teclados", "Switches, keycaps y accesorios"): "para teclado",
    ("Bocinas", "Accesorios para bocinas"): "para bocinas",
    ("Tabletas", "Accesorios para tableta"): "para tableta",
    ("Autopartes", "Para autos"): "para auto",
    ("Autopartes", "Para motos"): "para moto",
    ("Autopartes", "Asientos, parrillas y accesorios de moto"): "para moto",
    ("Autos y motos", "Accesorios para auto"): "para auto",
    ("Autos y motos", "Accesorios para moto"): "para moto",
    ("Autos y motos", "Accesorios de audio para auto"): "para audio de auto",
    ("Autos y motos", "Cámaras y accesorios de llanta"): "para llanta",
    ("Energía solar", "Accesorios y limpieza de paneles solares"): "para paneles solares",
    ("Muebles", "Accesorios y organizadores de escritorio"): "de escritorio",
    ("Muebles", "Accesorios y refacciones para sillas"): "para silla",
    ("Muebles", "Accesorios y refacciones de cama"): "para cama",
    ("Muebles", "Herrajes y refacciones de muebles"): "para muebles",
    ("Herramientas", "Accesorios para herramientas eléctricas"): "para herramienta eléctrica",
    ("Herramientas", "Accesorios de multiherramienta y mototool"): "para mototool",
    ("Herramientas", "Accesorios para rotomartillo y demoledor"): "para rotomartillo",
    ("Herramientas", "Refacciones de herramientas eléctricas"): "para herramienta eléctrica",
    ("Herramientas", "Sanitarios y accesorios de baño"): "para baño",
    ("Herramientas", "Lijas y accesorios de lijado"): "para lijar",
    ("Climatización", "Refacciones de calefactor"): "para calefactor",
    ("Climatización", "Accesorios y refacciones de aire acondicionado"): "para aire acondicionado",
    ("Climatización", "Aspas y refacciones de ventilador"): "para ventilador",
    ("Cargadores y adaptadores", "Cargadores para reloj y accesorios pequeños"): "para reloj y gadgets",
    ("Blancos y ropa de cama", "Cortinas de baño y accesorios"): "para baño",
    ("Deportes y fitness", "Accesorios y ropa de yoga"): "para yoga",
    ("Electrodomésticos", "Refacciones para otros electrodomésticos"): "para electrodomésticos",
    ("Electrodomésticos", "Otros electrodomésticos de cocina"): "de cocina",
    ("Deportes y fitness", "Accesorios de fuerza"): "para pesas",
    ("Deportes y fitness", "Pelotas, redes y accesorios de ping pong"): "de ping pong",
    ("Deportes y fitness", "Pelotas y accesorios de raqueta"): "para raqueta",
    ("Deportes y fitness", "Tapones y accesorios de natación"): "para natación",
    ("Deportes y fitness", "Dardos y accesorios"): "para dardos",
    ("Deportes y fitness", "Accesorios de patinaje"): "para patinar",
    ("Deportes y fitness", "Ropa y accesorios de fútbol"): "de fútbol",
    ("Bicicletas y movilidad", "Accesorios para bicicleta"): "para bicicleta",
    ("Bicicletas y movilidad", "Refacciones y transmisión de bicicleta"): "para bicicleta",
    ("Bicicletas y movilidad", "Accesorios de movilidad eléctrica"): "para scooter eléctrico",
    ("Cámaras y fotografía", "Accesorios para drones"): "para dron",
    ("Cámaras de seguridad", "Accesorios de videovigilancia"): "para cámaras de seguridad",
    ("Domótica y hogar inteligente", "Accesorios y refacciones de cerradura"): "para cerradura",
    ("Baterías portátiles", "Accesorios y repuestos"): "para batería portátil",
    ("Cafeteras", "Accesorios para cafetera"): "para cafetera",
    ("Electrodomésticos", "Accesorios de purificador"): "para purificador",
    ("Electrodomésticos", "Accesorios y repuestos para freidora de aire"): "para freidora de aire",
    ("Electrodomésticos", "Accesorios y refacciones de máquina de coser"): "para máquina de coser",
    ("Impresión 3D", "Refacciones y accesorios"): "para impresora 3D",
    ("Impresoras", "Cabezales y refacciones de impresión"): "para impresora",
    ("Mascotas", "Tapetes y accesorios de alimentación"): "para plato de mascota",
    ("Viajes", "Accesorios de viaje"): "de viaje",
    ("Videojuegos", "Otros accesorios gamer"): "gamer",
    ("Videojuegos", "Refacciones de consolas y controles"): "para consola",
}

# Palabras que no son la pieza: se saltan al buscar la cabeza.
RELLENO = {
    "kit", "set", "juego", "par", "pares", "paquete", "pack", "piezas", "pieza", "pzas", "pzs", "pz", "pza", "pcs",
    "de", "del", "x", "nuevo", "nueva", "nuevos", "original", "originales", "para", "con", "el", "la", "los", "las",
    "un", "una", "mini", "super", "pro", "premium", "universal", "repuesto", "repuestos", "refaccion", "refacciones",
    "accesorio", "accesorios", "compatible", "compatibles", "reemplazo", "generico", "generica", "oem", "and", "for",
    "the", "with", "venta", "internacional", "unidades", "uds", "profesional", "portatil", "multifuncional", "y",
    "color", "negro", "negra", "blanco", "blanca", "grande", "pequeno", "pequena", "doble", "alta", "calidad",
    "ajustable", "electrico", "electrica", "digital", "inalambrico", "inalambrica", "tipo", "modelo", "estilo", "en",
    "por", "sin", "a", "al",
}
# Cabezas que son lo mismo: la de la izquierda se nombra como la de la derecha.
SINONIMOS = {
    "estuche": "funda", "case": "funda", "carcasa": "funda", "cubierta": "funda", "cubre": "funda",
    "mando": "control", "controlador": "control", "altavoz": "bocina", "altavoces": "bocina",
    "reposamuneca": "reposamuñecas", "organizadore": "organizador", "calentadore": "calentador",
    "trapeador": "mopa", "trapo": "mopa", "fregona": "mopa", "pano": "mopa", "trapeadore": "mopa",
    "conectore": "conector", "soport": "soporte", "cabl": "cable", "chaqueta": "chamarra", "guant": "guante",
    "estant": "estante", "luc": "luz", "led": "luz", "foco": "luz", "peladora": "pelador", "tetera": "hervidor",
    "aspirador": "aspiradora", "earpad": "almohadilla", "concentrador": "hub", "docking": "hub",
    "estacion": "hub", "interruptore": "switch", "interruptor": "switch", "tecla": "keycap",
    "botella": "gato", "torre": "gato", "bolso": "bolsa", "plumilla": "pua", "capo": "cejilla",
}

# (categoría, comodín) -> [(regex sobre el título normalizado, (cat, sub))]: lo
# que se decide antes que la cabeza. «AUTOPARTE» = Autopartes por la pieza.
AUTOPARTE = ("Autopartes", None)
REGLAS = {
    ("Autopartes", "Para autos"): [
        (r"^kit (original|deportivo) ag\b|\bresortes?\b", ("Autopartes", "Suspensión y dirección")),
        (r"\b(radio|estereo|android|carplay|car ?play|unidad principal|pantalla tactil)\b", ("Autos y motos", "Estéreos para auto")),
        (r"\bcamara (de )?(estacionamiento|reversa|trasera)\b", ("Autopartes", "Sistema eléctrico y sensores")),
        (r"^bocinas?\b", ("Autos y motos", "Bocinas para auto")),
        (r"^gatos?\b", ("Autos y motos", "Gatos y herramientas para auto")),
    ],
    ("Autos y motos", "Accesorios para auto"): [
        (r"^(\S+ ){0,1}gatos?\b|\bllave de cruz\b|\bextractor\b", ("Autos y motos", "Gatos y herramientas para auto")),
        (r"^(\S+ ){0,2}(amortiguador|espejo|resorte|balata|bujia|filtro|faro|calavera|barra estabilizadora)", AUTOPARTE),
        (r"^(\S+ ){0,2}(compresor|inflador|bomba de aire)\b", ("Autos y motos", "Compresores e infladores")),
        (r"\baromatizante", ("Autos y motos", "Aromatizantes para auto")),
        (r"\b(soporte|porta ?celular|holder)\b.{0,30}\b(celular|telefono|movil|smartphone)", ("Autos y motos", "Soportes para celular de auto")),
        (r"^(\S+ ){0,2}(tapete|funda|cojin|cubreasiento|cubre asiento|parasol|protector de asiento)", ("Autos y motos", "Tapetes, fundas y parasoles")),
        (r"^(\S+ ){0,2}aceites?\b", AUTOPARTE),
        (r"^(\S+ ){0,2}(pulidora|cera|shampoo|abrillantador|microfibra|limpiador)\b", ("Autos y motos", "Limpieza y cuidado del auto")),
        (r"^(\S+ ){0,2}(luces|luz|tiras? led|focos? led)\b", ("Autos y motos", "Luces LED para auto")),
    ],
    ("Autos y motos", "Accesorios para moto"): [
        (r"^(\S+ ){0,2}(guantes?)\b", ("Autos y motos", "Guantes para moto")),
        (r"^(\S+ ){0,2}(chamarra|chaqueta|impermeable|pantalon|botas?)\b", ("Autos y motos", "Ropa para motociclista")),
        (r"^(\S+ ){0,2}(faros?|direccional(es)?|focos?|luz|luces|stop|calavera)\b", ("Autopartes", "Luces de moto")),
        (r"^(\S+ ){0,2}(espejos?|manubrio|puno|maneta|slider|parabrisas?|escape|cilindro|palanca)\b", AUTOPARTE),
        (r"^(\S+ ){0,2}(alforjas?|baul|maleta|caja|mochila|bolsa|organizador)\b", ("Autos y motos", "Baúles, alforjas y bolsas para moto")),
        (r"^(\S+ ){0,2}(funda|cubre ?moto|cubierta|lona)\b", ("Autos y motos", "Fundas para moto")),
    ],
    ("Autopartes", "Para motos"): [(r".", AUTOPARTE)],
    # El líquido de frenos Pentosin caía en «Micas y accesorios para casco» y la
    # cabeza «freno» inventaba «Frenos para casco» (53 fichas, 26-sep-2026).
    ("Autos y motos", "Micas y accesorios para casco"): [
        (r"liquido de frenos|\bfrenos?\b", ("Autopartes", "Frenos")),
    ],
    ("Autopartes", "Asientos, parrillas y accesorios de moto"): [
        (r"\b(asiento|respaldo|cojin)\b", ("Autopartes", "Asientos y respaldos de moto")),
        (r"\b(parrilla|portaequipaje|alforja|baul)\b", ("Autopartes", "Parrillas y portaequipajes de moto")),
    ],
    ("Instrumentos musicales", "Accesorios de guitarra"): [
        (r"^(\S+ ){0,2}(guqin|erhu|pipa|guzheng|laud|sitar|bouzouki|banjo)\b", ("Instrumentos musicales", "Violines, mandolinas y otras cuerdas")),
        (r"^libro", ("Libros", "Música y cine")),
    ],
}


# Las piezas y accesorios que pueden dar nombre a una subcategoría: cabeza ->
# (nombre, si lleva el contexto de la comodín). Una cabeza que no está acá
# («verticales», «gamer», una marca) no se vuelve subcategoría: su ficha va
# al resto. Salió de las cabezas de las 97 comodín, revisadas a mano.
PIEZAS = {
    "bateria": ("Baterías", True), "bolsa": ("Bolsas", True), "cargador": ("Cargadores", True),
    "cepillo": ("Cepillos", True), "filtro": ("Filtros", True), "manguera": ("Mangueras", True),
    "almohadilla": ("Almohadillas", True), "cilindro": ("Cilindros", True), "engrane": ("Engranes", True),
    "palanca": ("Palancas", True), "pedal": ("Pedales", True), "soporte": ("Soportes", True),
    "varilla": ("Varillas", True), "eje": ("Ejes", True), "posapie": ("Reposapiés", True),
    "reposapie": ("Reposapiés", True), "anillo": ("Anillos", True), "asiento": ("Asientos", True),
    "barra": ("Barras", True), "compresor": ("Compresores", True), "escape": ("Escapes", True),
    "funda": ("Fundas", True), "organizador": ("Organizadores", True), "portaequipaje": ("Portaequipajes", True),
    "protector": ("Protectores", True), "tapon": ("Tapones", True), "valvula": ("Válvulas", True),
    "inflador": ("Infladores", True), "cuadro": ("Cuadros", True), "freno": ("Frenos", True),
    "cortina": ("Cortinas", True), "forro": ("Forros", True), "gancho": ("Ganchos", True),
    "cable": ("Cables", True), "cuchara": ("Cucharas", True), "adaptador": ("Adaptadores", True),
    "correa": ("Correas", True), "mica": ("Micas", True), "control": ("Controles", True),
    "deflector": ("Deflectores", True), "elemento": ("Resistencias", True), "nucleo": ("Núcleos", True),
    "tubo": ("Tubos", True), "base": ("Bases", True), "brazo": ("Brazos", True),
    "conmutador": ("Conmutadores KVM", True), "elevador": ("Elevadores", True), "hub": ("Hubs y docks", True),
    "binocular": ("Binoculares", False), "tripode": ("Trípodes", True), "tapa": ("Tapas", True),
    "cinturon": ("Cinturones", True), "ejercitador": ("Ejercitadores", False), "toalla": ("Toallas", True),
    "zapato": ("Zapatos acuáticos", False), "pelota": ("Pelotas", True), "punta": ("Puntas", True),
    "tarjeta": ("Tarjetas", True), "caja": ("Cajas", True), "alfombrilla": ("Alfombrillas", True),
    "bascula": ("Básculas de cocina", False), "clip": ("Clips", True), "cuchilla": ("Cuchillas", True),
    "deshidratador": ("Deshidratadores de alimentos", False), "divisor": ("Divisores", True),
    "estante": ("Estantes", True), "evaporador": ("Evaporadores", True), "hervidor": ("Hervidores y teteras", False),
    "limpiacristal": ("Limpiacristales", True), "manija": ("Manijas", True), "mopa": ("Mopas y paños", True),
    "motor": ("Motores", True), "placa": ("Placas", True), "sensor": ("Sensores", True),
    "separador": ("Separadores", True), "solucion": ("Soluciones de limpieza", True), "sonda": ("Sondas", True),
    "termostato": ("Termostatos", True), "conector": ("Conectores", True), "herramienta": ("Herramientas", True),
    "maquina": ("Máquinas de limpieza", True), "pertiga": ("Pértigas", True), "robot": ("Robots", True),
    "cortador": ("Cortadores", True), "inodoro": ("Inodoros", False), "lavabo": ("Lavabos", False),
    "letrero": ("Letreros para baño", False), "lija": ("Lijas", False), "sanitario": ("Sanitarios", False),
    "cabezal": ("Cabezales", True), "afinador": ("Afinadores", True), "alfombra": ("Alfombras", True),
    "boquilla": ("Boquillas", True), "cana": ("Cañas", True), "clavija": ("Clavijas", True),
    "pastilla": ("Pastillas", True), "puente": ("Puentes", True), "pua": ("Púas", True),
    "microfono": ("Micrófonos", True), "bandeja": ("Bandejas", True), "pata": ("Patas", True),
    "teclado": ("Teclados", True), "switch": ("Switches", True), "keycap": ("Keycaps", True),
    "pelador": ("Peladores", False), "guante": ("Guantes", True), "cadena": ("Cadenas", True),
    "rueda": ("Ruedas", True), "rin": ("Rines", True), "timbre": ("Timbres", True), "bocina": ("Bocinas", True),
    "calentador": ("Calentadores", True), "aspa": ("Aspas", True), "lente": ("Lentes", True),
    "ventilador": ("Ventiladores", True), "pantalla": ("Pantallas", True), "estuche": ("Fundas", True),
    "cuerda": ("Cuerdas", True), "metronomo": ("Metrónomos", False), "cojin": ("Cojines", True),
    "tapete": ("Tapetes", True), "pomo": ("Jaladeras y pomos", False), "jaladera": ("Jaladeras y pomos", False),
    "bata": ("Batas", True), "visor": ("Visores", True), "overgrip": ("Grips", True), "grip": ("Grips", True),
    "red": ("Redes", True), "dardo": ("Dardos", False), "diafragma": ("Diafragmas", True), "rejilla": ("Rejillas", True),
    "cesta": ("Cestas", True), "parrilla": ("Parrillas", True), "cartucho": ("Cartuchos", True),
    "mando": ("Controles", True), "llanta": ("Llantas", True), "camara": ("Cámaras", True),
    "gato": ("Gatos hidráulicos", True), "jack": ("Gatos hidráulicos", True), "bolso": ("Bolsas", True),
    "capo": ("Cejillas", True), "cejilla": ("Cejillas", True), "diadema": ("Diademas", True),
}


def T(s):
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def es_generica(cat, sub):
    return bool(sub) and (cat, sub) not in NO_GENERICAS and bool(RX_GENERICA.search(sub))


def contexto(cat, sub):
    if (cat, sub) in CONTEXTO:
        return CONTEXTO[(cat, sub)]
    m = re.search(r"\b(para|de) (.+)$", sub)
    if m and not re.search(r"accesorio|refacci|repuest", m.group(2), re.I):
        return f"{m.group(1)} {m.group(2)}"
    return ""


def singular(w, vocab):
    if w in SINONIMOS:
        return SINONIMOS[w]
    if w.endswith("ces") and len(w) > 4:
        return w[:-3] + "z"
    if w.endswith("es") and len(w) > 4 and vocab.get(w[:-2], 0) >= vocab.get(w[:-1], 0) and vocab.get(w[:-2], 0) > 0:
        w = w[:-2]
    elif w.endswith("s") and len(w) > 3 and not w.endswith("ss"):
        w = w[:-1]
    return SINONIMOS.get(w, w)


PLURALES = {"robot": "robots", "hub": "hubs", "switch": "switches", "kit": "kits", "clip": "clips",
            "keycap": "keycaps", "control": "controles", "adaptador": "adaptadores"}
ACENTO = str.maketrans("áéíóú", "aeiou")


def plural(w):
    if w in PLURALES:
        return PLURALES[w]
    if len(w) > 2 and w[-2] in "áéíóú" and w[-1] in "ns":
        return w.translate(ACENTO) + "es"
    if w.endswith(("s", "x")):
        return w
    if w.endswith("z"):
        return w[:-1] + "ces"
    if w[-1] in "aeiouáéó":
        return w + "s"
    if w.endswith("ón"):
        return w[:-2] + "ones"
    return w + "es"


def cabeza(nombre, marcas, vocab, minusc, evitar=()):
    """La primera palabra que nombra la cosa. Una palabra que casi nunca
    aparece en minúscula dentro de otros títulos es una marca («Guyker»,
    «D'Addario», «Thomastik»): se salta, igual que la que repite el contexto
    («Monitor» en «Accesorios de monitor»)."""
    for w in re.findall(r"[a-z]+", T(nombre)):
        if w in RELLENO or len(w) < 3 or w in marcas or w in evitar:
            continue
        s = singular(w, vocab)
        if minusc.get(w, 0) + minusc.get(s, 0) < 3 or s in evitar:
            continue
        return s
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--informe")
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    import clasificar_captura_perifericos as C
    import reglas_nuevas as R
    import ejemplos_verificados as EV

    candado = json.load(io.open(CANDADO, encoding="utf-8")) if os.path.exists(CANDADO) else {}
    data = load_catalog()
    cats = {c["id"]: c for c in data["categories"]}
    genericas = {(c["id"], s["id"]) for c in data["categories"] for s in c.get("subcategories") or []
                 if es_generica(c["id"], s["id"])}

    # Vocabulario (para singularizar) y marcas (para saltarlas).
    vocab = collections.Counter()
    marcas_n = collections.Counter()
    formas = collections.defaultdict(collections.Counter)   # palabra sin acento -> forma con acento
    minusc = collections.Counter()   # veces que la palabra va en minúscula y no al principio
    for p in data["products"]:
        if (p["category"], p.get("subcategory")) in genericas:
            ws = re.findall(r"[A-Za-zÁÉÍÓÚÑÜáéíóúñü]+", p.get("name") or "")
            for i, w in enumerate(ws):
                formas[T(w)][w.lower()] += 1
                vocab[T(w)] += 1
                if i > 0 and w.islower():
                    minusc[T(w)] += 1
        if p.get("brand"):
            marcas_n[T(p["brand"]).strip()] += 1
    marcas = {m for m, n in marcas_n.items() if n >= 3 and " " not in m and len(m) >= 3} - {
        "cable", "funda", "soporte", "control", "filtro", "bolsa", "cargador"}

    def mostrar(w):
        f = formas.get(w)
        base = f.most_common(1)[0][0] if f else w
        return base

    # 1. Reglas y cabezas.
    propuesta = {}          # pid -> (cat, sub, via)
    grupos = collections.defaultdict(list)   # (cat, generica, cabeza) -> [p]
    for p in data["products"]:
        k = (p["category"], p.get("subcategory"))
        if k not in genericas or p["id"] in candado:
            continue
        tn = C.T(p.get("name") or "")
        hecho = False
        for rx, dest in REGLAS.get(k, []):
            if re.search(rx, tn):
                if dest == AUTOPARTE:
                    s = R.sub_autoparte(tn)
                    if not s:
                        continue
                    dest = ("Autopartes", s)
                propuesta[p["id"]] = (dest[0], dest[1], "regla")
                hecho = True
                break
        if not hecho:
            evitar = set(re.findall(r"[a-z]+", T(contexto(*k)))) - {"para", "de"}
            evitar |= {singular(w, vocab) for w in evitar}
            grupos[(k[0], k[1], cabeza(p.get("name"), marcas, vocab, minusc, evitar))].append(p)

    nuevas = collections.defaultdict(set)     # cat -> subs nuevas
    tabla = collections.defaultdict(dict)     # "cat|generica" -> {cabeza: sub}
    resto = []
    for (cat, gen, cab), ps in grupos.items():
        if cab in PIEZAS and len(ps) >= MIN_GRUPO:
            ctx = contexto(cat, gen)
            vis, con_ctx = PIEZAS[cab]
            nombre = vis + (f" {ctx}" if ctx and con_ctx else "")
            nuevas[cat].add(nombre)
            tabla[f"{cat}|{gen}"][cab] = nombre
            for p in ps:
                propuesta[p["id"]] = (cat, nombre, "cabeza")
        else:
            resto.extend(ps)
    for pid, (cat, sub, via) in propuesta.items():
        if via == "regla":
            nuevas[cat].add(sub)

    # 2. El resto, por el modelo de subcategorías de su categoría.
    modelos = collections.defaultdict(Bayes)
    por_id = {p["id"]: p for p in data["products"]}
    for p in data["products"]:
        k = (p["category"], p.get("subcategory"))
        if p["id"] in propuesta:
            cat, sub, _ = propuesta[p["id"]]
            modelos[cat].entrenar(sub, tokens(p.get("name")))
        elif k[1] and k not in genericas:
            modelos[k[0]].entrenar(k[1], tokens(p.get("name")))
    for ej in EV.cargar():
        if ej.get("sub") and not es_generica(ej["cat"], ej["sub"]):
            for _ in range(EV.PESO):
                modelos[ej["cat"]].entrenar(ej["sub"], tokens(ej["nombre"]))
    for m in modelos.values():
        m.preparar()
    # Las hermanas: las subcategorías que salieron de la misma comodín. El
    # resto va a la más parecida de ellas; si la comodín no dio ninguna, a
    # la más parecida de toda la categoría.
    hermanas = collections.defaultdict(set)
    for pid, (c, s, v) in propuesta.items():
        q = por_id[pid]
        if c == q["category"]:
            hermanas[(q["category"], q.get("subcategory"))].add(s)
    sin_modelo = 0
    for p in resto:
        m = modelos.get(p["category"])
        pts = m.puntajes(tokens(p.get("name"))) if m and m.doc else {}
        pts = {s: v for s, v in pts.items() if not es_generica(p["category"], s)}
        hs = hermanas.get((p["category"], p.get("subcategory")))
        if hs and len(hs) >= 3 and any(s in pts for s in hs):
            pts = {s: v for s, v in pts.items() if s in hs}
        # Solo con margen claro sobre la segunda: si no, la ficha se queda
        # donde está hasta que las reglas o el modelo (que crece con cada
        # revisión) la sepan poner.
        orden = sorted(pts.values(), reverse=True)
        if len(orden) > 1 and orden[0] - orden[1] < MARGEN_RESTO:
            sin_modelo += 1
            continue
        if not pts:
            sin_modelo += 1
            continue
        propuesta[p["id"]] = (p["category"], max(pts, key=pts.get), "modelo")

    # Informe.
    cuenta = collections.Counter((por_id[pid]["category"], por_id[pid].get("subcategory"), c, s, v)
                                 for pid, (c, s, v) in propuesta.items())
    random.seed(25)
    rep = collections.defaultdict(lambda: collections.defaultdict(list))
    for pid, (c, s, v) in propuesta.items():
        p = por_id[pid]
        rep[f"{p['category']} / {p.get('subcategory')}"][f"{v}: {c} / {s}"].append(p["name"][:80])
    salida = {}
    for gen, dests in sorted(rep.items(), key=lambda kv: -sum(len(x) for x in kv[1].values())):
        salida[gen] = {d: {"n": len(ns), "ej": random.sample(ns, min(3, len(ns)))}
                       for d, ns in sorted(dests.items(), key=lambda kv: -len(kv[1]))}
    total = len(propuesta)
    vias = collections.Counter(v for _c, _s, v in propuesta.values())
    print(f"Comodín: {len(genericas)} subcategorías; fichas repartidas {total:,} "
          f"(regla {vias['regla']:,}, cabeza {vias['cabeza']:,}, modelo {vias['modelo']:,}); "
          f"sin destino {sin_modelo:,}; subcategorías nuevas {sum(len(v) for v in nuevas.values()):,}")
    if args.informe:
        with io.open(args.informe, "w", encoding="utf-8") as f:
            json.dump(salida, f, ensure_ascii=False, indent=1)
    if not args.aplicar:
        return

    origen = {pid: (por_id[pid]["category"], por_id[pid].get("subcategory")) for pid in propuesta}
    for pid, (c, s, _v) in propuesta.items():
        p = por_id[pid]
        p["category"], p["subcategory"] = c, s
    # Las que ya existían antes de esta partición (Minisplit, Robots
    # aspiradores...): una ficha de «Accesorios» que resultó ser un aparato va
    # a su subcategoría de producto, y esa subcategoría NO es hija de la
    # comodín -- si se anotaba como hija, heredaba el papel «accesorio» y el
    # aparato dejaba de contar como producto (26-sep-2026: 60 subcategorías
    # de producto marcadas como accesorio o parte).
    existentes = {(c["id"], x["id"]) for c in data["categories"] for x in c["subcategories"]}
    for cat, subs in nuevas.items():
        c = cats[cat]
        for s in sorted(subs):
            if not any(x["id"] == s for x in c["subcategories"]):
                c["subcategories"].append({"id": s, "name": s, "icon": c.get("icon")})
    quedan = collections.Counter((p["category"], p.get("subcategory")) for p in data["products"])
    for c in data["categories"]:
        c["subcategories"] = [s for s in c["subcategories"]
                              if not (es_generica(c["id"], s["id"]) and not quedan[(c["id"], s["id"])])]
    hijas = collections.defaultdict(set)
    for pid, (c, s, _v) in propuesta.items():
        q = origen[pid]
        if c == q[0] and (c, s) not in existentes:
            hijas[f"{q[0]}|{q[1]}"].add(s)
    # Corre en cada regeneración: lo de antes se conserva y se le suma lo nuevo.
    previo = json.load(io.open(TABLA, encoding="utf-8")) if os.path.exists(TABLA) else {}
    for k, v in (previo.get("hijas") or {}).items():
        hijas[k].update(v)
    for k, v in (previo.get("tabla") or {}).items():
        tabla[k] = {**v, **tabla.get(k, {})}
    comodines = set(previo.get("comodines") or []) | {f"{c}|{s}" for c, s in genericas}
    with io.open(TABLA, "w", encoding="utf-8") as f:
        json.dump({"tabla": tabla, "comodines": sorted(comodines),
                   "hijas": {k: sorted(v) for k, v in hijas.items()}}, f,
                  ensure_ascii=False, indent=1, sort_keys=True)
    save_catalog(data)
    print("Guardado.")


if __name__ == "__main__":
    main()
