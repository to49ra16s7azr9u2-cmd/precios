#!/usr/bin/env python3
"""Deportes y fitness por deporte: primero el deporte, después el equipo.

POR QUÉ
-------
Deportes y fitness estaba cortada por TIPO DE EQUIPO: «Balones» juntaba el
balón de fútbol con el de básquetbol y el de voleibol, «Raquetas» la de
tenis con la de pádel y la de bádminton, «Protección y soportes» la
espinillera con el protector bucal. Quien busca algo para jugar fútbol
tenía que pasar por tres subcategorías distintas y filtrar en cada una.

Así no ordena nadie una tienda de deportes, ni kakaku.com: スポーツ abre
por deporte (サッカー・フットサル, バスケットボール, テニス...) y recién
adentro de cada deporte por equipo (サッカーボール, スパイク,
すね当て...). Pedido explícito del usuario: «スポーツで分けてから、道具の
種類で分ける（サッカー→ボール）».

CÓMO QUEDA
----------
El deporte es la FAMILIA (el escalón del medio de
familias_subcategorias.py) y el equipo es la SUBCATEGORÍA. La tabla
FAMILIAS de abajo es la fuente de verdad de las dos cosas: el orden de las
familias, qué subcategorías tiene cada una y en qué orden se muestran.

El gimnasio, el cardio y el yoga no son deportes, pero son las tres
secciones más grandes de la categoría y así las separa también kakaku
(フィットネス・トレーニング). Los deportes con pocas fichas (fútbol
americano, béisbol, golf) van como una sola subcategoría con el nombre del
deporte, dentro de «Otros deportes».

USO
---
    from deportes_por_deporte import reclasificar
    nueva = reclasificar(nombre, subcategoria_actual)

El clasificador de capturas (clasificar_captura_perifericos.py) lo llama al
final, así que lo que se importe de ahora en adelante ya entra por deporte.

    python3 scripts/deportes_por_deporte.py --dry-run   # ver el reparto
    python3 scripts/deportes_por_deporte.py             # aplicarlo
"""
import argparse
import collections
import datetime
import json
import os
import re
import sys
import unicodedata

CATEGORIA = "Deportes y fitness"

FAMILIAS = [
    ("Gimnasio y pesas", [
        "Mancuernas", "Kettlebells", "Barras y discos", "Sets de pesas",
        "Pesas de tobillo y chalecos con peso", "Balones medicinales",
        "Bancos y racks", "Máquinas multifuncionales y poleas",
        "Máquinas de abdominales", "Barras de dominadas y calistenia",
        "Bandas de resistencia", "Accesorios de fuerza", "Equipo de gimnasio"]),
    ("Cardio", [
        "Caminadoras", "Bicicletas fijas", "Elípticas", "Remadoras",
        "Escaladoras y steppers", "Cuerdas para saltar",
        "Otros aparatos de cardio"]),
    ("Yoga y pilates", [
        "Tapetes de yoga", "Bloques, correas y ruedas de yoga",
        "Pelotas y aros de pilates", "Rodillos de espuma y masaje",
        "Tablas y balance", "Accesorios y ropa de yoga"]),
    ("Fútbol", [
        "Balones de fútbol", "Porterías y redes de fútbol", "Espinilleras",
        "Guantes de portero", "Entrenamiento de fútbol",
        "Ropa y accesorios de fútbol"]),
    ("Básquetbol", ["Balones de básquetbol", "Tableros y canastas"]),
    ("Voleibol", [
        "Balones de voleibol", "Redes de voleibol",
        "Rodilleras y mangas de voleibol"]),
    ("Tenis, pádel y bádminton", [
        "Raquetas de tenis", "Raquetas de pádel", "Bádminton",
        "Pelotas y accesorios de raqueta"]),
    ("Ping pong", [
        "Mesas de ping pong", "Raquetas de ping pong",
        "Pelotas, redes y accesorios de ping pong"]),
    ("Boxeo y artes marciales", [
        "Guantes de box", "Costales, peras y entrenadores",
        "Protección, vendas y artes marciales"]),
    ("Natación", [
        "Goggles de natación", "Gorros de natación",
        "Trajes de baño deportivos", "Aletas, tablas y entrenamiento de natación",
        "Tapones y accesorios de natación"]),
    ("Deportes acuáticos", [
        "Paddle, surf y kayak", "Snorkel y buceo",
        "Chalecos, bolsas secas y accesorios acuáticos"]),
    ("Patinaje", [
        "Patines en línea", "Patines de 4 ruedas", "Patinetas y scooters",
        "Protección para patinar", "Accesorios de patinaje"]),
    ("Dardos", ["Dardos y accesorios", "Tableros de dardos"]),
    ("Protección y recuperación", [
        "Rodilleras, muñequeras y soportes", "Protectores bucales"]),
    ("Otros deportes", [
        "Fútbol americano", "Béisbol y softbol", "Golf", "Campismo",
        "Otros deportes"]),
]
SUBCATEGORIAS = [s for _, subs in FAMILIAS for s in subs]
FAMILIA_DE = {s: f for f, subs in FAMILIAS for s in subs}

# Las subcategorías de gimnasio que ya estaban cortadas por tipo de aparato
# y no tienen deporte que separar: se quedan como están, salvo lo que la
# regla de abajo saque explícitamente (el balón medicinal, la cuerda para
# saltar). Una banda de resistencia "para yoga y pilates" sigue siendo
# banda de resistencia.
YA_POR_TIPO = {
    "Mancuernas", "Kettlebells", "Barras y discos", "Sets de pesas",
    "Pesas de tobillo y chalecos con peso", "Bancos y racks",
    "Máquinas multifuncionales y poleas", "Máquinas de abdominales",
    "Barras de dominadas y calistenia", "Bandas de resistencia",
    "Accesorios de fuerza", "Equipo de gimnasio", "Bicicletas fijas",
}


def T(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def _r(rx):
    return re.compile(rx)


# --- Deporte ---------------------------------------------------------------
# El orden importa: tenis de mesa antes que tenis, fútbol americano antes que
# fútbol, pádel antes que tenis (la cinta "para pádel y tenis" es de pádel).
DEPORTES = [
    ("pingpong", _r(r"ping ?-?pong|tenis de mesa|table tennis|\bpong\b")),
    ("americano", _r(r"futbol americano|\bnfl\b|tochito|american football")),
    ("box", _r(r"\bbox(eo|ing)?\b|\bcostal(es)?\b|\bmma\b|muay|kick ?box|"
               r"guantes? (de |para )?box|saco de (box|boxeo)|punching|\bpaos\b|"
               r"manoplas? de box|vendas? (de |para )?(box|boxeo|mano)|envolturas de mano|"
               r"cleto reyes|everlast|\brdx\b|fire sports|maquina de boxeo|pera de (box|velocidad)")),
    ("marciales", _r(r"karate|taekwondo|\bjudo\b|jiu ?-?jitsu|artes marciales|kimono|dobok|"
                     r"nunchaku|\bkendo\b|capoeira")),
    ("dardos", _r(r"\bdardos?\b|\bdarts?\b|dartboard|tablero de dardos|red dragon|winmau")),
    ("patinaje", _r(r"\bpatin(es)?\b|patineta|skate|longboard|scooter|monopatin|hoverboard|"
                    r"rollerblade|roller ?derby|penny board")),
    ("padel", _r(r"\bpadel\b|pickleball")),
    ("badminton", _r(r"badminton|\bgallitos?\b|\bvolantes? de pluma")),
    ("tenis", _r(r"\btenis\b|\btennis\b")),
    ("voleibol", _r(r"volei|voley|volley|voleibol|mikasa|molten")),
    ("basquet", _r(r"basquet|basket|baloncesto|\bnba\b|canasta de (basquet|baloncesto)")),
    ("beisbol", _r(r"beisbol|baseball|softbol|softball|\bmanopla\b(?! de box)|\bbates?\b de")),
    ("golf", _r(r"\bgolf\b")),
    ("futbol", _r(r"\bfutbol\b|\bfootball\b|\bsoc+er\b|\bsoocer\b|porteri|espinillera|guantes? (de )?portero|"
                  r"\bjersey\b|seleccion (mexicana|nacional)|"
                  r"\btachones\b|\bfifa\b|\bportero\b")),
    ("natacion", _r(r"natacion|\bnadar\b|\bnado\b|\bswim|goggles?|gafas de (natacion|nadar)|"
                    r"gorr[oa]s? (de )?(natacion|silicona|nadar|piscina)|traje de bano|banador|"
                    r"pull buoy|pinza nasal|tapones? (para )?(los )?oidos|speedo|\bnadador")),
    ("acuaticos", _r(r"kayak|paddle ?board|stand up paddle|\bsup\b(?!-)|\bsurf|snorkel|esnorquel|"
                     r"buceo|chaleco salvavidas|salvavidas|wakeboard|esqui acuatico|bolsa seca|"
                     r"dry bag|cressi|aztron")),
    ("yoga", _r(r"\byoga\b|pilates|fitball|foam roller|rodillo de espuma|esterilla|yogamat")),
    ("camp", _r(r"campismo|camping|acampar|casa de campana|tienda de campana|saco de dormir|"
                r"sleeping bag|colchon(eta)? (inflable|autoinflable|autohinchable)|"
                r"estufa (de |para )?(camping|acampar)|supervivencia|lifestraw|filtro de agua (portatil|personal)")),
    ("otros", _r(r"hockey|rugby|gimnasia ritmica|escalada|tiro con arco|arqueria|esgrima|"
                 r"atletismo|jabalina|cricket|lacrosse|frisbee|petanca|boliche|bowling")),
]

BALON = _r(r"\bbalon(es)?\b|\bpelotas?\b|\bball\b|minibalon|\bbalones\b")


def _deporte(t):
    for nombre, rx in DEPORTES:
        if rx.search(t):
            return nombre
    return None


# --- Equipo dentro de cada deporte ----------------------------------------
def _futbol(t):
    if re.search(r"espinillera|shin ?guard", t):
        return "Espinilleras"
    if re.search(r"\bguantes?\b|portero|goalkeeper", t) and not re.search(r"jersey|playera", t):
        return "Guantes de portero"
    if re.search(r"porteri|\bredes?\b(?! social)|\barcos? de futbol|\bgoal\b|miniporteria", t):
        return "Porterías y redes de fútbol"
    if BALON.search(t) and not re.search(r"globos?|mochila|bolsa|balonera|red para balones|inflador|bomba", t):
        return "Balones de fútbol"
    if re.search(r"\bconos?\b|escalera (de )?(agilidad|entrenamiento|velocidad)|paracaidas|\bvallas?\b|"
                 r"aros? de agilidad|entrenamiento|entrenador|rebot|cinturon|tablero tactico|"
                 r"pizarra|silbato|marcador", t):
        return "Entrenamiento de fútbol"
    return "Ropa y accesorios de fútbol"


def _basquet(t):
    aro = re.search(r"tablero|canasta|\baros?\b|red (de|para)|backboard|hoop", t)
    if BALON.search(t) and not aro:
        return "Balones de básquetbol"
    if aro:
        return "Tableros y canastas"
    return "Otros deportes"


def _voleibol(t):
    if re.search(r"rodillera|mangas?\b|codera|arm ?sleeve", t):
        return "Rodilleras y mangas de voleibol"
    if re.search(r"\bred(es)?\b|\bnet\b|poste|antena|lineas? de (limite|cancha)|cancha", t) and not BALON.search(t.split(" con ")[0]):
        return "Redes de voleibol"
    return "Balones de voleibol"


def _raqueta(t, deporte):
    # La raqueta nombrada al principio es la raqueta, aunque después diga
    # "preencordada" o "con bolsa"; el grip "para raqueta de tenis" no.
    principal = re.search(r"^(?:\S+ ){0,4}(juego de |set de |kit de )?(raquetas?|palas?)\b", t)
    if not principal and re.search(r"overgrip|\bgrips?\b|cinta de agarre|empunadura|anillo de agarre|mochila|bolsa|"
                                   r"calibrador|tensor|raquetero|encordadora|cuerdas? (para|de) raqueta", t):
        return "Pelotas y accesorios de raqueta"
    es_raqueta = re.search(r"raquetas?|\bpalas?\b(?! de nieve)|\bracket|\bracquet", t) and not re.search(
        r"overgrip|grip|cinta|funda|bolsa|mochila|raquetero|protector|cuerdas? para raqueta|encordado", t)
    if deporte == "badminton":
        return "Bádminton"
    if es_raqueta and deporte == "padel":
        return "Raquetas de pádel"
    if es_raqueta and deporte == "tenis":
        return "Raquetas de tenis"
    return "Pelotas y accesorios de raqueta"


def _pingpong(t):
    # "tenis de mesa" es el nombre del deporte, no la mesa: sin quitarlo, la
    # raqueta, el robot y la bolsa "de tenis de mesa" caían en Mesas.
    sin_deporte = re.sub(r"tenis de mesa|table tennis", " ", t)
    if re.search(r"robot|maquina|sacador|bolsa|funda (de|para) raqueta|estuche", t):
        return "Pelotas, redes y accesorios de ping pong"
    if re.search(r"\bmesas?\b|\btable\b", sin_deporte) and not re.search(
            r"pelotas? de|ajustable a cualquier mesa|para (cualquier )?mesa|de puerta|puerta", sin_deporte):
        return "Mesas de ping pong"
    if re.search(r"raquetas?|\bpalas?\b|paletas?|paddles?|\bgoma\b|madera de|hoja de goma|mango", t):
        return "Raquetas de ping pong"
    return "Pelotas, redes y accesorios de ping pong"


def _box(t, deporte):
    if deporte == "marciales" or re.search(r"vendas?|envolturas|guantes interiores", t):
        return "Protección, vendas y artes marciales"
    if re.search(r"\bguantes?\b|\bgloves?\b", t) and not re.search(r"bucal|careta|cabezal|paos|manopla|mitones", t):
        return "Guantes de box"
    if re.search(r"costal|saco|bolsa (de |para )?(boxeo|box|pesada)|\bpera\b|punching|maquina de boxeo|"
                 r"reflej|pelota de boxeo|dummy|muneco|columna|soporte (de|para) (costal|saco)|"
                 r"entrenador de boxeo|boxeo (musical|inteligente)|\bbag\b", t):
        return "Costales, peras y entrenadores"
    return "Protección, vendas y artes marciales"


def _natacion(t):
    if re.search(r"goggles?|gafas|anteojos|lentes (de|para) (natacion|nadar)", t):
        return "Goggles de natación"
    if re.search(r"\bgorr[oa]s?\b|\bcap\b", t):
        return "Gorros de natación"
    if re.search(r"traje de bano|trajes de bano|banador|bikini|swimsuit|jammer|trunks|\bbrief\b|"
                 r"una pieza|enterizo|shorts?|bermudas?|rash ?guard|licra|proteccion solar upf|camisa de manga larga", t):
        return "Trajes de baño deportivos"
    if re.search(r"aletas?|tabla|pull buoy|paletas?|\bpalas?\b|snorkel|esnorquel|tubo de respiracion|"
                 r"cinturon|correa de natacion|entrenador|boya|mancuernas? (de agua|acuatic)|"
                 r"pesas? (de agua|acuatic)|fulcrum|brazada|flotador|chaleco", t):
        return "Aletas, tablas y entrenamiento de natación"
    return "Tapones y accesorios de natación"


def _acuaticos(t):
    if re.search(r"snorkel|esnorquel|buceo|mascara|visor|aletas?|regulador|tanque de buceo|"
                 r"cressi|scuba|seascooter", t):
        return "Snorkel y buceo"
    if re.search(r"tabla|paddle|\bsup\b|surf|kayak|\bremos?\b|canoa|bomba (de |para )?(sup|aire|kayak)|"
                 r"\bvela\b|aleron|wakeboard|esqui acuatico|body ?board", t):
        return "Paddle, surf y kayak"
    return "Chalecos, bolsas secas y accesorios acuáticos"


def _patinaje(t):
    if re.search(r"\bcasco|rodillera|codera|muneque|protecc?ion|protector", t) and not re.search(
            r"patines (en linea|de \d|ajustables)|patines para", t.split(" con ")[0]):
        return "Protección para patinar"
    if re.search(r"patineta|skate ?board|longboard|penny|cruiser|monopatin|scooter|hoverboard|"
                 r"tabla de skate|\bdeck\b|swing", t) and not re.search(r"patines", t):
        return "Patinetas y scooters"
    if re.search(r"rodamiento|balero|\bruedas? (de |para )?(repuesto|patin)|bearing|multiherramienta|ejes? de patineta|trucks?|lija|"
                 r"bolsa|mochila|soporte (de pared|para patineta)|colgador|llave|agujeta|\bfreno|"
                 r"tablas de dedo|fingerboard|tech deck", t):
        return "Accesorios de patinaje"
    if re.search(r"en linea|en lineas|inline|in-line|rollerblade|freeskate|macroblade|\bblades?\b", t):
        return "Patines en línea"
    if re.search(r"patin", t):
        return "Patines de 4 ruedas"
    return "Patinetas y scooters"


def _yoga(t):
    if re.search(r"bandas?|gomas? elastic|ligas?|cuerda elastica|cinta de resistencia|tubos? de resistencia|"
                 r"barra de pilates|kit (de )?pilates|resistencia", t) and not re.search(r"tapete|esterilla|\bmat\b", t):
        return "Bandas de resistencia"
    if re.search(r"discos? deslizantes?|sliders?|placa deslizante", t):
        return "Accesorios de fuerza"
    if re.search(r"estante|rack|organizador de gimnasio", t):
        return "Equipo de gimnasio"
    if re.search(r"zapatos? (de |para )?agua|calzado (para |de )?agua|aquashoes", t):
        return "Chalecos, bolsas secas y accesorios acuáticos"
    if re.search(r"rodillo|foam roller|\broller\b|masaje|masajeador|pistola", t):
        return "Rodillos de espuma y masaje"
    if re.search(r"tapete|esterilla|\bmat\b|colchoneta|yogamat|alfombr", t) and not re.search(
            r"bolsa|porta ?(esterilla|tapete)|estante|correa para (tapete|esterilla)|toalla", t):
        return "Tapetes de yoga"
    if re.search(r"bloques?|ladrillo|correas?|cinta de yoga|\bstrap\b|rueda de yoga|yoga wheel", t):
        return "Bloques, correas y ruedas de yoga"
    if re.search(r"mancuerna|pesas? hexagonal|dumbbell", t):
        return "Mancuernas"
    if re.search(r"barra (de ejercicio )?ponderada|anillo de (peso|potencia)|pesas? de mano", t):
        return "Accesorios de fuerza"
    if re.search(r"pelota|balon|fitball|\bball\b|aro de pilates|anillo de pilates|\baro\b|\bring\b|"
                 r"reformer|cadillac|cama de pilates", t):
        return "Pelotas y aros de pilates"
    if re.search(r"tabla de equilibrio|balance|bosu|disco de equilibrio|cojin de equilibrio|"
                 r"equilibrio|balancin", t):
        return "Tablas y balance"
    return "Accesorios y ropa de yoga"


def _cardio(t):
    if re.search(r"bicicleta|spinning|recumbent", t) and not re.search(r"eliptica", t):
        return "Bicicletas fijas"
    if re.search(r"caminadora|trotadora|cinta (de |para )?correr|treadmill|walking pad|banda (para |de )?caminadora", t):
        return "Caminadoras"
    if re.search(r"eliptic|elliptical|spacewalk", t):
        return "Elípticas"
    if re.search(r"remadora|\bremo\b|rowing|\brower", t):
        return "Remadoras"
    if re.search(r"escalador|stepper|\bstep\b|escalera", t):
        return "Escaladoras y steppers"
    return "Otros aparatos de cardio"


def _dardos(t):
    if re.search(r"tablero|\bdiana\b|dartboard|electronic|gabinete|cabinet|blanco de dardos", t) and not re.search(
            r"^(set|juego) de dardos|dardos (de|con) (punta|tungsteno|acero)", t):
        return "Tableros de dardos"
    return "Dardos y accesorios"


def _soportes(t):
    if re.search(r"bucal|mouthguard|mouth guard", t):
        return "Protectores bucales"
    return "Rodilleras, muñequeras y soportes"


def reclasificar(nombre, sub):
    """La subcategoría nueva de una ficha de Deportes y fitness."""
    t = T(nombre)
    if sub in SUBCATEGORIAS and sub not in YA_POR_TIPO and sub != "Otros deportes":
        return sub  # ya repartida

    # Lo que se saca de las subcategorías de gimnasio por lo que ES, no por
    # el deporte que menciona de paso.
    if re.search(r"balon medicinal|medicine ball|slam ?ball|wall ?ball|pelota medicinal|"
                 r"balon (de )?(peso|lastre)|mancuerna de goma medicine", t):
        return "Balones medicinales"
    if re.search(r"cuerdas? (de |para )?(saltar|brincar|salto)|jump ?rope|speed rope|comba\b|"
                 r"\bcuerda\b.{0,25}\b(salto|saltar)\b|cuerda .{0,25}(comfort handle|entrenamiento)", t):
        return "Cuerdas para saltar"
    if sub in YA_POR_TIPO:
        return sub
    if sub == "Pesas":
        if re.search(r"mancuerna|dumbbell", t):
            return "Mancuernas"
        if re.search(r"kettlebell|pesa rusa", t):
            return "Kettlebells"
        if re.search(r"tobiller|chaleco|munequera", t):
            return "Pesas de tobillo y chalecos con peso"
        if re.search(r"\bdisco|barra", t):
            return "Barras y discos"
        return "Sets de pesas"
    if sub == "Máquinas de cardio":
        return _cardio(t)

    # Un protector bucal es de protección aunque diga "fútbol, rugby y box".
    if re.search(r"protector(es)? bucal|bucal (deportivo|para)|mouthguard", t):
        return "Protectores bucales"
    if re.search(r"barra (de )?dominadas|pull ?-?up bar", t):
        return "Barras de dominadas y calistenia"
    # La rodillera, la tobillera y la muñequera son de cualquier deporte
    # aunque la marca diga "Basquetbol" o "NBA"; las de voleibol (con manga)
    # sí se quedan en voleibol.
    if re.search(r"rodillera|tobillera|munequera|codera|\bsoportes? (de|para) (rodilla|tobillo|muneca)|"
                 r"compresion", t) and not re.search(r"volei|voley|volley|voleibol|patin|skate|casco", t):
        return "Rodilleras, muñequeras y soportes"
    if re.search(r"\bplatos? (de )?entrenamiento|\bconos?\b|escalera (de )?(entrenamiento|agilidad|velocidad)|"
                 r"silbato|whistle", t):
        return "Entrenamiento de fútbol"

    d = _deporte(t)
    if d == "futbol":
        return _futbol(t)
    if d == "basquet":
        return _basquet(t)
    if d == "voleibol":
        return _voleibol(t)
    if d in ("tenis", "padel", "badminton"):
        return _raqueta(t, d)
    if d == "pingpong":
        return _pingpong(t)
    if d in ("box", "marciales"):
        return _box(t, d)
    if d == "natacion":
        return _natacion(t)
    if d == "acuaticos":
        return _acuaticos(t)
    if d == "patinaje":
        return _patinaje(t)
    if d == "yoga":
        return _yoga(t)
    if d == "dardos":
        return _dardos(t)
    if d == "americano":
        return "Fútbol americano"
    if d == "beisbol":
        return "Béisbol y softbol"
    if d == "golf":
        return "Golf"
    if d == "camp":
        return "Campismo"
    if d == "otros":
        return "Otros deportes"

    # Sin deporte en el nombre: decide lo que la ficha ya era.
    por_sub = {
        "Balones": lambda: ("Ropa y accesorios de fútbol" if re.search(r"mochila|bolsa|balonera|red para balones", t)
                            else "Accesorios de fuerza" if re.search(r"guantes?", t)
                            else "Balones de fútbol" if re.search(r"\bno\.? ?[345]\b|#\s?[345]\b|numero [345]|"
                                                              r"tamano [345]|talla [345]", t)
                            else "Balones de básquetbol" if re.search(r"#\s?[67]\b|no\.? ?[67]\b|numero [67]", t)
                            else "Pelotas y aros de pilates" if re.search(r"ejercicio|gimnasia|estabilidad|embarazo", t)
                            else "Balones de fútbol" if re.search(r"\bbalon", t)
                            else "Otros deportes"),
        "Voleibol": lambda: _voleibol(t),
        "Fútbol": lambda: _futbol(t),
        "Raquetas": lambda: _raqueta(t, "tenis"),
        "Ping pong": lambda: _pingpong(t),
        "Boxeo": lambda: _box(t, "box"),
        "Yoga": lambda: _yoga(t),
        "Natación": lambda: _natacion(t),
        "Deportes acuáticos": lambda: _acuaticos(t),
        "Patines y patinetas": lambda: _patinaje(t),
        "Dardos": lambda: _dardos(t),
        "Protección y soportes": lambda: _soportes(t),
        "Tablas y balance": lambda: "Tablas y balance",
        "Campismo": lambda: "Campismo",
    }
    if sub in por_sub:
        return por_sub[sub]()
    return "Otros deportes"


def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from data_io import load_catalog, save_catalog

    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--muestra", help="archivo donde escribir una muestra por subcategoría")
    args = ap.parse_args()

    data = load_catalog()
    cat = next(c for c in data["categories"] if c["id"] == CATEGORIA)
    grupos = collections.Counter()
    ejemplos = collections.defaultdict(list)
    cuenta = collections.Counter()
    for p in data["products"]:
        if p.get("category") != CATEGORIA:
            continue
        vieja = p.get("subcategory")
        nueva = reclasificar(p.get("name"), vieja)
        cuenta[nueva] += 1
        ejemplos[nueva].append(f"[{vieja}] {p.get('name', '')[:90]}")
        if nueva != vieja:
            grupos[f"{CATEGORIA} | {vieja} | {CATEGORIA} | {nueva}"] += 1
            if not args.dry_run:
                p["subcategory"] = nueva

    for f, subs in FAMILIAS:
        print(f"## {f}: {sum(cuenta[s] for s in subs):,}")
        for s in subs:
            print(f"   {cuenta[s]:>6,}  {s}")
    print(f"movidas: {sum(grupos.values()):,}")

    if args.muestra:
        import random
        random.seed(0)
        with open(args.muestra, "w", encoding="utf-8") as fh:
            for s in SUBCATEGORIAS:
                L = ejemplos.get(s, [])
                fh.write(f"### {s} ({len(L)})\n")
                for x in random.sample(L, min(30, len(L))):
                    fh.write(f"    {x}\n")
    if args.dry_run:
        return

    iconos = {s["id"]: s.get("icon") for s in cat.get("subcategories") or []}
    icono_def = next(iter(iconos.values()), "dumbbell") or "dumbbell"
    cat["subcategories"] = [
        {"id": s, "name": s, "icon": iconos.get(s) or icono_def} for s in SUBCATEGORIAS
    ]
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "movimientos-aplicados.json")
    with open(ruta, encoding="utf-8") as fh:
        bitacora = json.load(fh)
    bitacora.append({
        "fecha": datetime.date.today().isoformat(),
        "origen": "deportes_por_deporte.py",
        "motivo": "Deportes y fitness por deporte y después por equipo (pedido del usuario, estilo kakaku)",
        "grupos": dict(grupos),
    })
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(bitacora, fh, ensure_ascii=False, indent=1)
    save_catalog(data)
    print("Guardado.")


if __name__ == "__main__":
    main()
