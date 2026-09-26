#!/usr/bin/env python3
"""Las subcategorías de miles de fichas, partidas por lo que se elige (26-sep-2026).

POR QUÉ
-------
Fuera de Autopartes (ver subcategorias_autopartes_finas.py) quedaban cajones
de miles de fichas donde conviven productos que nadie compara entre sí,
contados el 26-sep-2026:

  * Llantas para auto (25,594) y para camioneta (16,793): se compran por RIN.
    Quien busca una 205/55 R16 no quiere ver las de rin 14 ni las de 20.
  * Calzado / Tenis (15,713): 8,070 dicen «hombre» y 3,338 «mujer».
  * Autos y motos / Tapetes, fundas y parasoles (9,369): 5,274 cubrevolantes
    y 3,900 juegos de cubreasientos; tapetes, 1,458.
  * Muebles / Cabeceras (7,942): 2,739 son box + cabecera (la cama entera).
  * Belleza / Perfumes (7,911): dama 958 + mujer 711, caballero 742 + hombre
    689, unisex 518, además de sets y body mist.
  * Juguetes / Figuras de acción (6,735): 3,401 Funko, que ya tienen su
    subcategoría («Funko y coleccionables»).
  * Blancos / Edredones (6,423): colchas y cobertores (1,438), coordinados
    con sábanas, rellenos (duvet).

Como en Autopartes, lo que ninguna regla reconoce se queda en la
subcategoría vieja con el mismo nombre y la misma url.

CÓMO SE APLICA
--------------
  * A lo nuevo: DIVISIONES entra en OLA2 (subcategorias_tres_niveles.py) y el
    clasificador lo aplica con afinar_ola2().
  * A lo que ya está: este script con --aplicar (también en regenerar_sitio.sh).
  * Familias: cada subcategoría nueva va en la familia de la vieja
    (familias_subcategorias.py).

USO
---
    python3 scripts/subcategorias_divisiones.py            # informe
    python3 scripts/subcategorias_divisiones.py --aplicar
"""
import argparse
import collections
import os
import random
import re
import sys
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)


def T(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s)


def _por_regla(ramas):
    """Repartidor de reglas: gana la que el título nombra primero; en empate,
    la primera de la lista."""
    cs = [(s, re.compile(rx)) for s, rx in ramas]

    def f(tn):
        mejor = None
        for sub, rx in cs:
            m = rx.search(tn)
            if m and (mejor is None or m.start() < mejor[0]):
                mejor = (m.start(), sub)
        return mejor[1] if mejor else None
    return f


# ------------------------------------------------------------------ llantas
# El rin sale de la medida: «205/55 r16», «205 55 r16», «p225/60r17»,
# «31x10.50r15», «11r22.5», «265/70zr17».
_RIN = re.compile(r"(?:\d{3}[ /-]\d{2} ?z? ?r ?f? ?|\d{2}x\d{1,2}\.\d{2} ?(?:r|-) ?|\b\d{2} ?r ?|\b\d{3} ?r ?)"
                  r"(1[2-9]|2[0-6])(\.5)?c?(?!\d)")


def rin(tn):
    m = _RIN.search(tn)
    if not m:
        m = re.search(r"\brin (1[2-9]|2[0-6])\b", tn)
        return (int(m.group(1)), False) if m else (None, False)
    return int(m.group(1)), bool(m.group(2))


LLANTAS_AUTO = ["Llantas para auto rin 13 y 14", "Llantas para auto rin 15", "Llantas para auto rin 16",
                "Llantas para auto rin 17", "Llantas para auto rin 18", "Llantas para auto rin 19 o más"]


def llanta_auto(tn):
    r, _ = rin(tn)
    if r is None:
        return None
    if r <= 14:
        return LLANTAS_AUTO[0]
    if r >= 19:
        return LLANTAS_AUTO[5]
    return {15: LLANTAS_AUTO[1], 16: LLANTAS_AUTO[2], 17: LLANTAS_AUTO[3], 18: LLANTAS_AUTO[4]}[r]


LLANTAS_SUV = ["Llantas para camioneta rin 15 y 16", "Llantas para camioneta rin 17",
               "Llantas para camioneta rin 18", "Llantas para camioneta rin 20 o más",
               "Llantas para camión (rin 17.5 a 24.5)"]


def llanta_suv(tn):
    r, media = rin(tn)
    if r is None:
        return None
    if media:                       # 17.5, 19.5, 22.5, 24.5: de camión
        return LLANTAS_SUV[4] if r >= 17 else None
    if r <= 16:
        return LLANTAS_SUV[0]
    if r == 17:
        return LLANTAS_SUV[1]
    if r in (18, 19):
        return LLANTAS_SUV[2]
    return LLANTAS_SUV[3]


# ------------------------------------------------------------------- reglas
_HOMBRE = r"\bhombres?\b|\bcaballeros?\b|\bmasculin|\bmen'?s?\b|\bhomme\b|\bpour homme\b|\bfor men\b|\bhim\b|\bvaron"
_MUJER = r"\bmujer(es)?\b|\bdamas?\b|\bfemenin|\bwomen'?s?\b|\bwns\b|\bfemme\b|\bpour femme\b|\bfor women\b|\bher\b|\blady\b"

# (categoría, subcategoría vieja, [finas en orden], repartidor(tn) -> fina | None)
DIVISIONES = [
    ("Autos y motos", "Llantas para auto", LLANTAS_AUTO, llanta_auto),
    ("Autos y motos", "Llantas para camioneta y SUV", LLANTAS_SUV, llanta_suv),
    ("Calzado", "Tenis", ["Tenis para hombre", "Tenis para mujer"], _por_regla([
        # unisex o para los dos: se queda en «Tenis».
        ("Tenis", r"\bunisex\b|\bhombre y mujer\b|\bmujer y hombre\b|\bdama y caballero\b"),
        ("Tenis para hombre", _HOMBRE),
        ("Tenis para mujer", _MUJER),
    ])),
    ("Belleza y cuidado personal", "Perfumes",
     ["Perfumes para mujer", "Perfumes para hombre", "Perfumes unisex", "Sets de perfume", "Body mist y splash"],
     _por_regla([
         ("Sets de perfume", r"^(\S+ ){0,2}(set|estuche|kit|coffret)\b|\bset de regalo\b|\bgift set\b"),
         ("Body mist y splash", r"\bbody mist\b|\bbody splash\b|\bsplash\b|\bmist\b|\bbruma\b"),
         ("Perfumes unisex", r"\bunisex\b|\bhombre y mujer\b|\bmujer y hombre\b|\bdama y caballero\b"),
         ("Perfumes para hombre", _HOMBRE),
         ("Perfumes para mujer", _MUJER),
     ])),
    ("Autos y motos", "Tapetes, fundas y parasoles",
     ["Cubrevolantes", "Cubreasientos para auto", "Tapetes para auto"], _por_regla([
         ("Cubrevolantes", r"\bcubre ?volantes?\b|\bfundas? (de |para )?volante"),
         ("Cubreasientos para auto", r"\bcubre ?asientos?\b|\bfundas? (de |para )?asientos?\b"),
         ("Tapetes para auto", r"\btapetes?\b|\balfombrillas?\b"),
     ])),
    ("Muebles", "Cabeceras", ["Box con cabecera"], _por_regla([
        ("Box con cabecera", r"\bbox\b|\bbase (de |para )?cama\b|\bmarco de cama\b|\bcama (individual|matrimonial|queen|king)"
                             r".{0,30}\bcon cabecera"),
    ])),
    ("Juguetes", "Figuras de acción", ["Funko y coleccionables", "Figuras de colección a escala"], _por_regla([
        ("Funko y coleccionables", r"\bfunko\b|\bpop!? ?(vinyl|vinilo)?\b(?=.{0,40}\b(pop|funko)\b)|\bpocket pop\b"),
        ("Figuras de colección a escala", r"\bhot toys\b|\b1/(4|6|12)\b|\bsixth scale\b|\bescala 1|\bneca\b|\bmcfarlane\b|"
                                          r"\bfiguarts\b|\bbanpresto\b|\bsuper7\b|\bmezco\b|\bsh ?figuarts\b|\bstatue\b|\bestatua\b"),
    ])),
    ("Blancos y ropa de cama", "Edredones",
     ["Colchas y cobertores", "Coordinados y juegos de edredón", "Rellenos de edredón (duvet)"], _por_regla([
         ("Rellenos de edredón (duvet)", r"\brellenos?\b|\binserto\b|\bduvet\b(?!.{0,15}\bcover)"),
         ("Coordinados y juegos de edredón", r"\bcoordinados?\b|\+ ?sabanas|\bcon sabanas\b|\bjuego de (edredon|cama)|"
                                              r"\bset de (edredon|cama)|\bcon fundas\b"),
         ("Colchas y cobertores", r"\bcolchas?\b|\bcobertor(es)?\b|\bedrecolcha\b|\bcubrecamas?\b"),
     ])),
]

# ---------------------------------------------------------------------------
# Segunda ronda (26-sep-2026): las demás categorías, subcategoría por
# subcategoría (las de 1,200 fichas o más). Se revisó cada una por el
# sustantivo de sus títulos; las que ya eran un solo tipo de producto
# (juegos de PS4, cocinas integrales, colchones por medida...) se dejaron.
# Donde la pieza ya tiene subcategoría en la categoría (las colgantes que
# estaban en Plafones, los muebles de baño en Alacenas) se devuelve esa.
def _R(*ramas):
    return _por_regla(list(ramas))


DIVISIONES += [
    # ---- Herramientas
    ("Herramientas", "Llaves y dados",
     ["Dados, matracas y autocles", "Llaves combinadas y españolas", "Llaves Allen y Torx", "Llaves ajustables y stilson"],
     _R(("Dados, matracas y autocles", r"\bdados?\b|\bmatracas?\b|\bautocle|\bmaneral|\bbarra de fuerza"),
        ("Llaves Allen y Torx", r"\ballen\b|\btorx\b|\bhexagonal(es)?\b"),
        ("Llaves ajustables y stilson", r"\bajustable|\bperica\b|\bstilson|\binglesa\b|\bpara tubo\b"),
        ("Llaves combinadas y españolas", r"\bcombinadas?\b|\bespanolas?\b|\bmixtas?\b|\bestriadas?\b|\bde boca\b|\bmatraca combinada"))),
    ("Herramientas", "Brocas",
     ["Brocas para concreto y SDS", "Brocas para metal", "Brocas para madera", "Sierras de copa y cortacírculos",
      "Machuelos y tarrajas"],
     _R(("Sierras de copa y cortacírculos", r"\bsierras? (de )?copa|\bcortacirculos|\bbimetalic|\bhole ?saw"),
        ("Machuelos y tarrajas", r"\bmachuelos?\b|\btarrajas?\b|\btaps?\b"),
        ("Brocas para concreto y SDS", r"\bconcreto\b|\bsds\b|\bmamposteria|\brotomartillo"),
        ("Brocas para metal", r"\bmetal(es)?\b|\bhss\b|\bcobalto|\bacero\b.{0,20}\bbroca|\bescalonada"),
        ("Brocas para madera", r"\bmadera\b|\bpala\b|\bforstner|\bplana\b"))),
    ("Herramientas", "Jardinería",
     ["Motosierras", "Desbrozadoras y desmalezadoras", "Mangueras y riego", "Sopladoras", "Fumigadoras y pulverizadores",
      "Tijeras de podar y cortasetos"],
     _R(("Motosierras", r"\bmotosierras?\b"),
        ("Desbrozadoras y desmalezadoras", r"\bdesbrozadoras?\b|\bdesmalezadoras?\b|\borilladoras?\b"),
        ("Sopladoras", r"\bsopladora|\bsoplador(es)?\b"),
        ("Fumigadoras y pulverizadores", r"\bfumigador|\baspersoras?\b|\bmochila (de )?fumigar|\bpulverizador(es)? (de|para) (jardin|presion|mochila)"),
        ("Tijeras de podar y cortasetos", r"\btijeras?\b|\bcortasetos|\bpodadoras? de mano|\bserrucho de poda"),
        ("Mangueras y riego", r"\bmangueras?\b|\baspersor(es)?\b|\briego\b|\bpistola de riego|\bcarrete"))),
    ("Herramientas", "Cerraduras y candados", ["Candados", "Cerraduras y chapas de puerta"],
     _R(("Candados", r"\bcandados?\b"),
        ("Cerraduras y chapas de puerta", r"\bcerraduras?\b|\bchapas?\b|\bcerrojos?\b|\bpomos?\b|\bmanijas? (de|para) puerta"))),
    ("Herramientas", "Desarmadores y puntas", ["Juegos de desarmadores", "Puntas para atornillar"],
     _R(("Juegos de desarmadores", r"\bjuegos?\b|\bset\b|\bkit\b|\d+ ?(piezas|pzas|pz)\b"),
        ("Puntas para atornillar", r"^(\S+ ){0,2}puntas?\b|\bbits?\b"))),
    ("Herramientas", "Pinzas y alicates",
     ["Pinzas de presión", "Pinzas de corte", "Pinzas de electricista y ponchadoras", "Pinzas de punta"],
     _R(("Pinzas de presión", r"\bpresion\b|\bperro\b|\bvise ?grip"),
        ("Pinzas de electricista y ponchadoras", r"\belectricista|\bponchadora|\bpelacables|\bpeladora|\bcrimp"),
        ("Pinzas de corte", r"^(\S+ ){0,4}(pinzas?|alicates?)\b.{0,25}\b(corte|diagonal)|\bcortafrio|\bcortadora de cable"),
        ("Pinzas de punta", r"\bpunta\b|\bmicro ?punta"))),
    ("Herramientas", "Taladros y rotomartillos", ["Rotomartillos", "Taladros inalámbricos"],
     _R(("Atornilladores", r"^(\S+ ){0,1}(atornillador(es)?|llaves? de impacto)\b"),
        ("Rotomartillos", r"\brotomartillos?\b|\bsds\b|\bmartillo perforador"),
        ("Taladros inalámbricos", r"\binalambric|\ba bateria\b|\b(12|18|20|40) ?v\b|\bbrushless"))),
    ("Herramientas", "Soldadura",
     ["Soldadoras", "Caretas y cascos para soldar", "Cautines y estaciones de soldar", "Consumibles de soldadura"],
     _R(("Caretas y cascos para soldar", r"\bcaretas?\b|\bcascos?\b"),
        ("Cautines y estaciones de soldar", r"\bcautin|\bestacion(es)? de (soldadura|soldar|retrabajo)|\bsoldador (electrico|tipo lapiz|de lapiz)|"
                                            r"\bpistola (de )?soldar"),
        ("Consumibles de soldadura", r"\balambres?\b|\bvarillas?\b|\belectrodos?\b|\bestano\b|\bfundente"),
        ("Soldadoras", r"\bsoldadoras?\b|\bmaquina (de|para) soldar|\binversora|\binverter|\bmig\b|\btig\b"))),
    ("Herramientas", "Medición",
     ["Multímetros y probadores", "Cintas métricas y flexómetros", "Niveles", "Calibradores y vernier", "Escuadras y reglas",
      "Material eléctrico"],
     _R(("Multímetros y probadores", r"\bmultimetros?\b|\bprobador|\bdetector de voltaje|\bamperimetr|\btester\b"),
        ("Cintas métricas y flexómetros", r"\bflexometro|\bcintas? (metrica|de medir|de medicion)|\bodometro"),
        ("Niveles", r"^(\S+ ){0,2}nivel(es)?\b|\bnivel laser"),
        ("Calibradores y vernier", r"\bcalibrador|\bvernier|\bmicrometro|\bpie de rey"),
        ("Escuadras y reglas", r"\bescuadras?\b|\breglas?\b|\bescalimetro|\btransportador"),
        ("Material eléctrico", r"^cables?\b|\bthw\b|\buso rudo\b"))),
    ("Herramientas", "Material eléctrico",
     ["Timbres", "Cables y extensiones eléctricas", "Apagadores y contactos", "Interruptores, breakers y fusibles"],
     _R(("Timbres", r"\btimbres?\b"),
        ("Interruptores, breakers y fusibles", r"\bdisyuntor|\bbreaker|\btermomagnetic|\bcentro de carga|\bfusibles?\b|\bsupresor"),
        ("Apagadores y contactos", r"\bclavijas?\b|\bcontactos?\b|\breceptaculo|\bmulticontacto|\btomas? de corriente|\bapagador"),
        ("Cables y extensiones eléctricas", r"\bcables?\b|\bextension(es)?\b|\balambres?\b"))),
    ("Herramientas", "Regaderas y duchas", ["Brazos y manerales de regadera", "Grifos y monomandos"],
     _R(("Grifos y monomandos", r"^(\S+ ){0,1}(mezcladora|monomando|llave (de|para) (lavabo|fregadero))\b"),
        ("Brazos y manerales de regadera", r"^(\S+ ){0,2}(brazos?|manerales?|chapeton)\b"))),
    ("Herramientas", "Organizadores de herramientas",
     ["Cajas de herramientas", "Bolsas y cinturones portaherramientas", "Gabinetes y carros de herramientas"],
     _R(("Gabinetes y carros de herramientas", r"\bgabinetes?\b|\bcarros?\b|\bcarritos?\b|\bestantes?\b|\bcajonera"),
        ("Bolsas y cinturones portaherramientas", r"\bbolsas?\b|\bcinturon|\bmochilas?\b|\blona\b|\bmandil|\bportaherramientas"),
        ("Cajas de herramientas", r"\bcajas?\b|\bmaletas?\b|\bmaletin"))),
    # ---- Belleza
    ("Belleza y cuidado personal", "Cremas y sérums faciales", ["Sérums faciales", "Cremas faciales", "Aceites faciales"],
     _R(("Sérums faciales", r"\bserums?\b|\bsueros?\b|\bampolletas?\b|\besencia\b"),
        ("Cremas faciales", r"\bcremas?\b|\bcream\b|\bhidratante\b|\bmoisturizer|\bemulsion"),
        ("Aceites faciales", r"^(\S+ ){0,2}aceites?\b|\bfacial oil"))),
    ("Belleza y cuidado personal", "Cuidado del cabello",
     ["Shampoo", "Acondicionadores", "Tratamientos y mascarillas capilares", "Ceras, geles y fijadores", "Tintes para cabello"],
     _R(("Tintes para cabello", r"\btintes?\b|\bcoloracion|\bdecolorante|\bpeinado de color|\bcanas\b"),
        ("Shampoo", r"\bshampoo|\bchampu|\bchampoo"),
        ("Acondicionadores", r"\bacondicionador"),
        ("Ceras, geles y fijadores", r"\bceras?\b|\bgel(es)?\b|\bpomadas?\b|\bfijador|\blaca\b|\bspray (fijador|para peinar)|\bmousse"),
        ("Tratamientos y mascarillas capilares", r"\bmascarillas?\b|\btratamiento|\baceites?\b|\bserum|\bampolleta|\bkeratina|\bolaplex|\btonico"))),
    ("Belleza y cuidado personal", "Corporales",
     ["Aceites esenciales y de masaje", "Cremas y lociones corporales", "Exfoliantes corporales", "Desodorantes",
      "Jabones y geles de baño"],
     _R(("Desodorantes", r"\bdesodorante|\bantitranspirante"),
        ("Exfoliantes corporales", r"\bexfoliante|\bscrub\b"),
        ("Jabones y geles de baño", r"\bjabon|\bgel de (ducha|bano)|\bbody wash|\bshower gel"),
        ("Aceites esenciales y de masaje", r"\baceites?\b"),
        ("Cremas y lociones corporales", r"\bcremas?\b|\blocion|\blotion|\bmanteca|\bbody butter|\bhidratante corporal"))),
    ("Belleza y cuidado personal", "Rasuradoras",
     ["Recortadoras de barba", "Cortadoras de cabello", "Afeitadoras eléctricas", "Rastrillos y navajas",
      "Cremas y bálsamos para afeitar"],
     _R(("Cremas y bálsamos para afeitar", r"^(\S+ ){0,2}(cremas?|gel|balsamo|aceite|espuma|cera|locion)\b"),
        ("Rastrillos y navajas", r"\brastrillos?\b|\bnavajas?\b|\bhojas de afeitar|\bcuchillas? de repuesto"),
        ("Cortadoras de cabello", r"\bcortadora|\bcortapelo|\bclipper|\bmaquina (de|para) cortar|\bmaquinilla (de|para) cortar"),
        ("Recortadoras de barba", r"\brecortador|\btrimmer|\bbarba\b"),
        ("Afeitadoras eléctricas", r"\bafeitadora|\brasuradora|\bshaver"))),
    ("Belleza y cuidado personal", "Labiales",
     ["Brillos labiales (gloss)", "Bálsamos labiales", "Delineadores de labios", "Tintas y labiales líquidos"],
     _R(("Delineadores de labios", r"\bdelineador|\blapiz (labial|de labios)|\blip liner"),
        ("Bálsamos labiales", r"\bbalsamos?\b|\blip balm|\bprotector labial"),
        ("Brillos labiales (gloss)", r"\bbrillos?\b|\bgloss\b|\blip oil|\baceite (labial|para labios)"),
        ("Tintas y labiales líquidos", r"\btintas?\b|\btintes?\b|\bliquido\b"))),
    ("Belleza y cuidado personal", "Bases y correctores", ["Correctores", "Bases de maquillaje"],
     _R(("Correctores", r"\bcorrector|\bconcealer"),
        ("Bases de maquillaje", r"\bbases?\b|\bfoundation"))),
    # ---- Joyería
    ("Joyería y bisutería", "Anillos", ["Anillos de compromiso", "Argollas de matrimonio", "Anillos de promesa"],
     _R(("Anillos de compromiso", r"\bcompromiso|\bsolitario"),
        ("Argollas de matrimonio", r"\bargollas?\b|\bmatrimonio|\bboda\b|\bchurumbela"),
        ("Anillos de promesa", r"\bpromesa"))),
    ("Joyería y bisutería", "Aretes", ["Arracadas", "Broqueles"],
     _R(("Arracadas", r"\barracadas?\b|\bhuggies?\b"), ("Broqueles", r"\bbroquel(es)?\b|\btopos?\b"))),
    ("Joyería y bisutería", "Collares", ["Cadenas", "Rosarios y medallas religiosas"],
     _R(("Rosarios y medallas religiosas", r"\brosarios?\b|\bmedallas?\b|\bescapulario|\bvirgen\b|\bsan (benito|judas)"),
        ("Cadenas", r"^(\S+ ){0,1}cadenas?\b|\bcadena (torzal|cubana|rolo|gucci|singapur|figaro|italiana)"))),
    ("Joyería y bisutería", "Dijes y charms", ["Charms"], _R(("Charms", r"\bcharms?\b"))),
    ("Joyería y bisutería", "Relojes para hombre", ["Relojes de buceo", "Cronógrafos", "Relojes automáticos"],
     _R(("Relojes automáticos", r"\bautomatico|\bautomatic\b|\bmecanico\b"),
        ("Relojes de buceo", r"\bdiver\b|\bbuceo\b|\bsubmariner"),
        ("Cronógrafos", r"\bcronografo|\bchronograph"))),
    ("Joyería y bisutería", "Lentes de sol", ["Lentes de sol polarizados"],
     _R(("Lentes de sol polarizados", r"\bpolariz"))),
    # ---- Iluminación
    ("Iluminación", "Plafones y lámparas de sobreponer",
     ["Lámparas colgantes", "Candiles y arañas", "Empotrada", "Rieles y spots"],
     _R(("Lámparas colgantes", r"\bcolgantes?\b|\bsuspendid"),
        ("Candiles y arañas", r"\bcandil(es)?\b|\barana\b|\bchandelier"),
        ("Rieles y spots", r"\briel(es)?\b|\bspots?\b"),
        ("Empotrada", r"\bempotrabl|\bempotrad"))),
    ("Iluminación", "Decorativa", ["Luces navideñas y guirnaldas", "Proyectores de luz y efectos", "Letreros y neón"],
     _R(("Luces navideñas y guirnaldas", r"\bnavid|\bserie de luces|^series?\b|\bguirnalda|\bcortina de luces|\barbol\b|\besferas\b"),
        ("Proyectores de luz y efectos", r"\bproyector|\bgalaxia|\bestrellas\b|\bbola de (luz|disco)|\brgb\b"),
        ("Letreros y neón", r"\bletreros?\b|\bneon\b"))),
    ("Iluminación", "Focos", ["Focos dicroicos (GU10 y MR16)", "Tubos LED y fluorescentes", "Focos vintage y de filamento"],
     _R(("Focos dicroicos (GU10 y MR16)", r"\bgu ?10\b|\bmr ?16\b|\bdicroic"),
        ("Tubos LED y fluorescentes", r"\btubos?\b|\bt8\b|\bt5\b|\bfluorescente"),
        ("Focos vintage y de filamento", r"\bvintage\b|\bfilamento|\bedison\b"))),
    ("Iluminación", "Exterior", ["Lámparas solares", "Reflectores", "Series y guirnaldas de exterior"],
     _R(("Lámparas solares", r"\bsolar(es)?\b"),
        ("Reflectores", r"\breflector(es)?\b"),
        ("Series y guirnaldas de exterior", r"\bseries?\b|\bguirnalda|\besferas\b|\bmanguera (de )?luz|\bcadena de luces"))),
    # ---- Muebles
    ("Muebles", "Roperos", ["Clósets de tela y portátiles", "Cómodas y cajoneras", "Tocadores"],
     _R(("Clósets de tela y portátiles", r"\btela\b|\bplegable|\bportatil|\barmable de tela|\bnon ?woven"),
        ("Cómodas y cajoneras", r"\bcomodas?\b|\bcajoneras?\b"),
        ("Tocadores", r"\btocador"))),
    ("Muebles", "Alacenas y gabinetes de cocina", ["Muebles de baño", "Cocinas integrales"],
     _R(("Muebles de baño", r"\bbano\b|\blavabo|\blavamanos|\bovalin|\bbotiquin"),
        ("Cocinas integrales", r"\bcocina integral|\bintegral\b"))),
    ("Muebles", "Sillones y reclinables",
     ["Love seats", "Sillones reclinables", "Salas completas", "Puffs y otomanas", "Mecedoras y colgantes"],
     _R(("Puffs y otomanas", r"^(\S+ ){0,1}puff?s?\b|\botomana|\bottoman"),
        ("Mecedoras y colgantes", r"\bmecedora|\bcolgante"),
        ("Love seats", r"\blove ?seat|\b2 plazas\b"),
        ("Salas completas", r"^salas?\b|\bjuego de sala|\bsala (modular|en l|esquinera|3 ?2 ?1)"),
        ("Sillones reclinables", r"\breclinable|\breposet"))),
    ("Muebles", "Sillas de oficina", ["Sillas ergonómicas", "Sillas ejecutivas"],
     _R(("Sillas ergonómicas", r"\bergonomic|\bmalla\b|\bmesh\b"),
        ("Sillas ejecutivas", r"\bejecutiva|\bpiel\b|\bcuero\b|\bdirector"))),
    # ---- Cocina
    ("Cocina y comedor", "Vasos y copas", ["Copas", "Vasos tequileros y caballitos"],
     _R(("Vasos tequileros y caballitos", r"\btequileros?\b|\bcaballitos?\b|\bshots?\b"),
        ("Copas", r"^(\S+ ){0,3}copas?\b(?!.{0,20}mundial)"))),
    ("Cocina y comedor", "Tazas", ["Juegos de tazas"], _R(("Juegos de tazas", r"^duo\b|\bjuego de \d+ tazas|\bset de \d+ tazas|^\d+ tazas|\btazas\b"))),
    ("Cocina y comedor", "Termos y botellas térmicas", ["Botellas de agua"], _R(("Botellas de agua", r"^(\S+ ){0,1}botellas?\b"))),
    ("Cocina y comedor", "Sartenes y comales", ["Juegos de sartenes", "Comales y planchas"],
     _R(("Juegos de sartenes", r"\bjuego de \d? ?sartenes|\bset de \d? ?sartenes|^\d+ sartenes|\bsartenes\b"),
        ("Comales y planchas", r"\bcomal(es)?\b|\bplancha\b|\bparrilla\b"))),
    ("Cocina y comedor", "Cuchillos y tablas", ["Juegos de cuchillos", "Tablas para picar", "Afiladores de cuchillos"],
     _R(("Afiladores de cuchillos", r"\bafilador"),
        ("Tablas para picar", r"^(\S+ ){0,1}tablas?\b"),
        ("Juegos de cuchillos", r"\bjuego de cuchillos|\bset de cuchillos|^cuchillos\b|\bcuchillos .{0,20}\d+ ?(pzas|piezas)|\bbloque"))),
    # ---- Electrodomésticos
    ("Electrodomésticos", "Campanas de cocina", ["Combos de campana y parrilla"],
     _R(("Combos de campana y parrilla", r"^(tri)?combo\b|\b\+ ?parrilla|\bcon parrilla|\by parrilla"))),
    ("Electrodomésticos", "Estufas", ["Parrillas de gas", "Parrillas de inducción y eléctricas"],
     _R(("Parrillas de inducción y eléctricas", r"\binduccion|\bvitroceramic|\bparrilla electrica"),
        ("Parrillas de gas", r"^(\S+ ){0,1}parrillas?\b"))),
    # ---- Mascotas
    ("Mascotas", "Juguetes para perro",
     ["Pelotas y lanzadores para perro", "Mordederas y masticables", "Peluches para perro", "Ropa para mascotas"],
     _R(("Ropa para mascotas", r"^(\S+ ){0,1}(jersey|chamarra|traje|sueter|sudadera|abrigo|playera|disfraz)\b"),
        ("Pelotas y lanzadores para perro", r"\bpelotas?\b|\blanzador"),
        ("Mordederas y masticables", r"\bmasticable|\bmordedera|\bhueso|\bcuerdas?\b|\bnylabone|\bbenebone"),
        ("Peluches para perro", r"\bpeluche"))),
    ("Mascotas", "Correas", ["Collares para mascotas", "Arneses y pecheras", "Correas retráctiles"],
     _R(("Arneses y pecheras", r"\barnes(es)?\b|\bpecheras?\b"),
        ("Correas retráctiles", r"\bretractil"),
        ("Collares para mascotas", r"^(\S+ ){0,3}collar(es)?\b"))),
    ("Mascotas", "Ropa para mascotas", ["Disfraces para mascotas", "Impermeables y abrigos para mascotas"],
     _R(("Disfraces para mascotas", r"\bdisfraz|\bhalloween"),
        ("Impermeables y abrigos para mascotas", r"\bimpermeable|\babrigo|\bchamarra|\bsueter|\bsudadera|\bcapa\b|\bchaleco"))),
    ("Mascotas", "Alimento y premios", ["Premios y snacks para mascotas", "Alimento para perro", "Alimento para gato"],
     _R(("Premios y snacks para mascotas", r"\bpremios?\b|\bsnacks?\b|\bgalletas?\b|\bchurus?\b|\bdentastix|\bbocadillo"),
        ("Alimento para gato", r"\bgatos?\b|\bgatitos?\b|\bfelin|\bcat\b|\bkitten|\bgatina|\bwhiskas|\bminino"),
        ("Alimento para perro", r"\bperros?\b|\bcachorro|\bcanin|\bdog\b|\bpuppy|\bpedigree|\bdog chow"))),
    ("Mascotas", "Camas para perro", ["Camas ortopédicas para perro"],
     _R(("Camas ortopédicas para perro", r"\bortopedic|\bviscoelast|\bmemory"))),
    # ---- Autos y motos
    ("Autos y motos", "Cascos para moto",
     ["Cascos abatibles", "Cascos integrales", "Cascos abiertos", "Micas y accesorios para casco"],
     _R(("Micas y accesorios para casco", r"^(\S+ ){0,1}(micas?|visor|pinlock|liquido|intercomunicador|cuernos|adorno|orejas)\b"),
        ("Cascos abatibles", r"\babatible|\bmodular\b"),
        ("Cascos abiertos", r"\babiertos?\b|\b3/4\b|\bjet\b|\bopen face|\bmedio casco"),
        ("Cascos integrales", r"\bintegral(es)?\b|\bcerrado\b|\bfull face|\bcross\b|\bmotocross"))),
    ("Autos y motos", "Motocicletas", ["Guantes para moto", "Ropa para motociclista", "Cuatrimotos"],
     _R(("Guantes para moto", r"^(\S+ ){0,1}guantes?\b"),
        ("Ropa para motociclista", r"^(\S+ ){0,1}(pantalon|chamarra|chaqueta|impermeable|chaleco|sudadera)\b"),
        ("Cuatrimotos", r"\bcuatrimotos?\b|\batv\b|\butv\b|\brazer\b"))),
    # ---- Otros
    ("Relojes inteligentes", "Correas y extensibles",
     ["Correas para Apple Watch", "Correas para Galaxy Watch", "Correas para Huawei, Xiaomi y Amazfit"],
     _R(("Correas para Apple Watch", r"\bapple watch|\biwatch"),
        ("Correas para Galaxy Watch", r"\bgalaxy watch|\bsamsung"),
        ("Correas para Huawei, Xiaomi y Amazfit", r"\bhuawei|\bxiaomi|\bmi band|\bamazfit|\bredmi"))),
    ("Videojuegos", "Controles y gamepads",
     ["Controles para PlayStation", "Controles para Xbox", "Controles para Nintendo Switch", "Controles para PC y celular"],
     _R(("Controles para PlayStation", r"\bps5\b|\bps4\b|\bplaystation|\bdualsense|\bdualshock"),
        ("Controles para Xbox", r"\bxbox"),
        ("Controles para Nintendo Switch", r"\bswitch\b|\bjoy ?-?con|\bnintendo"),
        ("Controles para PC y celular", r"\bpc\b|\bandroid|\bcelular|\bmovil|\biphone|\bsteam"))),
    ("Celulares", "Soportes y agarraderas", ["PopSockets y agarraderas", "Tripiés y palos selfie"],
     _R(("Tripiés y palos selfie", r"\btripode|\btripie|\bpalo (de )?selfie|\bselfie stick|\bmonopie"),
        ("PopSockets y agarraderas", r"\bpopsockets?\b|\bpopgrip|\bgrip\b|\bagarre|\bempunadura|\banillo"))),
    ("Celulares", "Reacondicionados", ["iPhone reacondicionados"],
     _R(("iPhone reacondicionados", r"\biphone|\bapple\b"))),
    ("Componentes y accesorios de PC", "Enfriamiento y ventiladores",
     ["Enfriamiento líquido", "Disipadores de CPU", "Ventiladores para gabinete", "Pasta térmica"],
     _R(("Pasta térmica", r"\bpasta termica|\bthermal (paste|pad)|\bcompuesto termico"),
        ("Enfriamiento líquido", r"\bliquid|\baio\b|\bwater ?cool"),
        ("Disipadores de CPU", r"\bdisipador|\bcpu cooler|\bcooler (de|para) cpu|\bair cooler"),
        ("Ventiladores para gabinete", r"\bventilador(es)?\b|\bfans?\b|\bargb\b|\bpwm\b"))),
    ("Audífonos", "Earbuds inalámbricos", ["Earbuds con cancelación de ruido"],
     _R(("Earbuds con cancelación de ruido", r"\bcancelacion|\banc\b|\bnoise cancel"))),
    ("Instrumentos musicales", "Micrófonos",
     ["Micrófonos inalámbricos", "Micrófonos de condensador y USB", "Micrófonos lavalier"],
     _R(("Micrófonos lavalier", r"\blavalier|\bsolapa|\bcorbata"),
        ("Micrófonos inalámbricos", r"\binalambric|\buhf\b|\bvhf\b"),
        ("Micrófonos de condensador y USB", r"\bcondensador|\busb\b|\bstreaming|\bpodcast"))),
    ("Blancos y ropa de cama", "Cobijas", ["Cobertores", "Frazadas y mantas"],
     _R(("Cobertores", r"^(\S+ ){0,1}cobertor"), ("Frazadas y mantas", r"^(\S+ ){0,1}(frazada|manta)s?\b"))),
    ("Blancos y ropa de cama", "Almohadas",
     ["Almohadas de memory foam", "Almohadas de lactancia y embarazo", "Almohadas cervicales y ortopédicas"],
     _R(("Almohadas de lactancia y embarazo", r"\blactancia|\bembarazo|\bmaternidad"),
        ("Almohadas cervicales y ortopédicas", r"\bcervical|\bortopedic"),
        ("Almohadas de memory foam", r"\bmemory|\bviscoelast|\bfoam\b"))),
    ("Bebés", "Carriolas", ["Sistemas de viaje", "Carriolas bastón"],
     _R(("Sistemas de viaje", r"\bsistema de viaje|\btravel system|\bcon portabebe"),
        ("Carriolas bastón", r"\bbaston\b|\bumbrella|\bparaguas"))),
    ("Calzado", "Botas", ["Botas de trabajo", "Botas vaqueras", "Botas de motociclista", "Botines"],
     _R(("Botas", r"\bfutbol\b|\btachones\b|\bsoccer\b"),
        ("Botas de trabajo", r"\bworkland|\btrabajo\b|\bindustrial|\bcasquillo|\bseguridad\b|\bdielectric"),
        ("Botas vaqueras", r"\bvaquer|\broper\b|\bwestern|\bexotic"),
        ("Botas de motociclista", r"\bbiker\b|\bmotociclista|\bmoto\b"),
        ("Botines", r"^(\S+ ){0,1}botin(es)?\b(?!.{0,30}\b(futbol|tachones|soccer))"))),
    ("Calzado", "Tenis para niños", ["Tenis para niña", "Tenis para niño"],
     _R(("Tenis para niña", r"\bninas?\b|\bgirls?\b"), ("Tenis para niño", r"\bnino\b|\bboys?\b"))),
    ("Deportes y fitness", "Balones de fútbol", ["Tachones de fútbol", "Guantes de portero"],
     _R(("Tachones de fútbol", r"^(\S+ ){0,1}(tachones|taquetes|tacos)\b|\bcalzado de futbol"),
        ("Guantes de portero", r"^(\S+ ){0,1}guantes? (de )?portero"))),
    ("Deportes y fitness", "Rodilleras, muñequeras y soportes",
     ["Fajas lumbares", "Rodilleras", "Tobilleras", "Coderas y muñequeras", "Correctores de postura"],
     _R(("Fajas lumbares", r"^(\S+ ){0,1}fajas?\b|\blumbar"),
        ("Correctores de postura", r"\bcorrector"),
        ("Rodilleras", r"\brodilleras?\b"),
        ("Tobilleras", r"\btobilleras?\b"),
        ("Coderas y muñequeras", r"\bcoderas?\b|\bmunequeras?\b"))),
    # «Otros deportes» eran sobre todo fajas y correctores (449 fichas, 205
    # empiezan con «faja»): van a las subcategorías que salen de Rodilleras.
    ("Deportes y fitness", "Otros deportes", ["Fajas lumbares", "Correctores de postura", "Tachones de fútbol"],
     _R(("Fajas lumbares", r"^(\S+ ){0,1}fajas?\b|\bfaja lumbar|\bcinturon (de )?soporte lumbar"),
        ("Correctores de postura", r"\bcorrector(es)? de postura|^corrector"),
        ("Tachones de fútbol", r"^(\S+ ){0,1}(tachones|taquetes|tacos)\b"))),
    ("Juegos de mesa", "De mesa clásicos", ["Dominó", "Lotería y bingo"],
     _R(("Dominó", r"\bdomino"), ("Lotería y bingo", r"\bloteria|\bbingo"))),
    ("Decoración de hogar y jardín", "Cortinas", ["Persianas", "Cortinas blackout"],
     _R(("Persianas", r"\bpersianas?\b|\benrollable"), ("Cortinas blackout", r"\bblackout|\bopacas?\b|\btermic"))),
]


# Las funciones de DIVISIONES reciben sólo el título; OLA2 pasa (tn, sub_vieja).
def _para_ola2(fn, vieja):
    def f(tn, sub_vieja):
        r = fn(tn)
        return None if r == vieja else r
    return f


TRES_NIVELES_DIVISIONES = [(cat, [vieja], [vieja] + finas, _para_ola2(fn, vieja), None)
                           for cat, vieja, finas, fn in DIVISIONES]

# Subcategorías nuevas que caen en una que ya existía en otra parte de la
# categoría: su familia es la de esa, no la de la vieja.
YA_EXISTEN = {
    ("Juguetes", "Funko y coleccionables"),
    ("Herramientas", "Atornilladores"), ("Herramientas", "Grifos y monomandos"),
    ("Audífonos", "Earbuds con cancelación de ruido"), ("Autos y motos", "Guantes para moto"),
    ("Autos y motos", "Ropa para motociclista"), ("Cocina y comedor", "Botellas de agua"),
    ("Deportes y fitness", "Guantes de portero"), ("Herramientas", "Apagadores y contactos"),
    ("Herramientas", "Material eléctrico"), ("Iluminación", "Candiles y arañas"), ("Iluminación", "Empotrada"),
    ("Iluminación", "Lámparas colgantes"), ("Iluminación", "Rieles y spots"),
    ("Joyería y bisutería", "Relojes para hombre"), ("Joyería y bisutería", "Relojes para mujer"),
    ("Mascotas", "Ropa para mascotas"), ("Muebles", "Cocinas integrales"), ("Muebles", "Mecedoras y colgantes"),
    ("Muebles", "Muebles de baño"), ("Muebles", "Puffs y otomanas"), ("Muebles", "Taburetes y bancos"),
}


def nuevas_por_vieja():
    """{(categoría, vieja): [finas nuevas]} para sumarlas a la familia de la vieja."""
    out = collections.defaultdict(list)
    vistas = set()   # una subcategoría nueva va sólo con la PRIMERA que la crea
    for cat, vieja, finas, _ in DIVISIONES:
        for f in finas:
            if (cat, f) in YA_EXISTEN or (cat, f) in vistas:
                continue
            vistas.add((cat, f))
            out[(cat, vieja)].append(f)
    return out


def main():
    from data_io import load_catalog, save_catalog
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--muestras", type=int, default=4)
    args = ap.parse_args()
    data = load_catalog()
    por_clave = {(c, v): (finas, fn) for c, v, finas, fn in DIVISIONES}
    cambios, quedan = collections.Counter(), collections.Counter()
    ejemplos = collections.defaultdict(list)
    for p in data["products"]:
        k = (p.get("category"), p.get("subcategory"))
        if k not in por_clave:
            continue
        tn = T(p.get("name"))
        nueva = por_clave[k][1](tn)
        if not nueva or nueva == k[1]:
            quedan[k] += 1
            continue
        # Encadenadas: «Relojes» -> «Relojes para hombre» -> «Relojes de buceo».
        for _ in range(3):
            sig = por_clave.get((k[0], nueva))
            siguiente = sig[1](tn) if sig else None
            if not siguiente or siguiente == nueva:
                break
            nueva = siguiente
        cambios[k + (nueva,)] += 1
        ejemplos[k + (nueva,)].append(p.get("name") or "")
        if args.aplicar:
            p["subcategory"] = nueva
    random.seed(5)
    for k in por_clave:
        print(f"\n=== {k[0]} / {k[1]}: se quedan {quedan[k]:,}")
        for kk, n in sorted(cambios.items(), key=lambda x: -x[1]):
            if kk[:2] != k:
                continue
            print(f"   {n:7,}  {kk[2]}")
            for e in random.sample(ejemplos[kk], min(args.muestras, len(ejemplos[kk]))):
                print(f"              {e[:90]}")
    print(f"\nTotal: {sum(cambios.values()):,} fichas a su subcategoría fina")
    if args.aplicar and cambios:
        for cat_id, vieja, finas, _ in DIVISIONES:
            cat = next((c for c in data["categories"] if c["id"] == cat_id), None)
            if not cat:
                continue
            subs = cat.setdefault("subcategories", [])
            existentes = {s["id"] for s in subs}
            base = next((s for s in subs if s["id"] == vieja), {})
            i = next((j for j, s in enumerate(subs) if s["id"] == vieja), len(subs) - 1)
            for f in finas:
                if f not in existentes:
                    i += 1
                    subs.insert(i, {"id": f, "name": f, "icon": base.get("icon") or cat.get("icon")})
                    existentes.add(f)
        save_catalog(data)
        print("Guardado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
