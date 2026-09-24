#!/usr/bin/env python3
"""Vacía la categoría «Otros»: cada grupo va a donde se compara (24-sep-2026).

POR QUÉ
-------
«Otros» tenía 7,845 fichas, y casi ninguna era «otra cosa»: eran grupos
claros sin casa propia. Los popsockets y soportes de coche (2,809) son
accesorios de celular; las estaciones de energía (477) son el tramo alto de
las baterías portátiles; los paneles, inversores, kits y controladores
solares (2,052) son una categoría entera que kakaku tiene aparte; las
cortinas de baño son blancos; los walkie-talkies son radios de dos vías.
En «Otros» nadie los encontraba navegando, y cada «lo más barato de Otros»
comparaba un panel solar con una cortina.

Sólo «Varios» sigue siendo de verdad varios: eso lo decide el modelo del
catálogo con los vecinos (clasificar_otros.py), ficha por ficha.

La tabla la usan el clasificador (lo que entra nuevo; ver decidir() en
clasificar_captura_perifericos.py) y clasificar_otros.py (lo que ya está).
"""
import re

SOLAR = 'Energía solar'
SUBS_SOLAR = ['Paneles solares', 'Cargadores solares portátiles', 'Kits solares y controladores de carga',
              'Inversores', 'Accesorios y limpieza de paneles solares', 'Luces y ventiladores solares',
              'Bombas y calentadores solares']

SOPORTES = 'Soportes y agarraderas'
BANO = 'Cortinas de baño y accesorios'
ORGANIZACION = 'Organizadores y almacenamiento'
CUADROS = 'Cuadros y decoración de pared'
PLAGAS = 'Control de plagas y mosquitos'
RADIOS_DOS_VIAS = 'Radios de dos vías'

# Subcategorías nuevas en categorías que ya existían: (categoría, sub, icono)
NUEVAS = [
    ('Celulares', SOPORTES, 'phone'),
    ('Celulares', RADIOS_DOS_VIAS, 'phone'),
    ('Blancos y ropa de cama', BANO, 'pillow'),
    ('Muebles', ORGANIZACION, 'sofa'),
    ('Decoración de hogar y jardín', CUADROS, 'box'),
    ('Electrodomésticos', PLAGAS, 'appliance'),
]
# Rol en roles_subcategorias.py
ROLES_NUEVAS = {'Celulares': {SOPORTES: 'accesorio', RADIOS_DOS_VIAS: 'afin'}}

# Agarraderas y anillos de celular (Popsockets): el título empieza muchas
# veces por «Teléfono celular grip…» o «Smartphone Popsockets…» y la regla de
# teléfonos se los quedaba (Celulares/Android, y de ahí a la lista de los
# Resistentes). Lo usan la DEFINICIÓN del clasificador y clasificar_otros.py.
AGARRE = re.compile(r'\bpopsockets?\b|\bpop ?grip\b|\bpop socket\b|'
                    r'^(?=.*\b(celular|telefono|smartphone|phone|movil|magsafe|iphone|samsung)\b)'
                    r'(?!.*\b(pinzas?|alicates?|tenazas?|llave|herramienta|raqueta|bate|palo|volante|manubrio)\b)'
                    r'(?:\S+ ){0,3}grip\b|\bagarraderas? (para|de) (celular|telefono|smartphone|movil)|'
                    r'\banillos? (para|de) (celular|telefono|smartphone)')
_ARRANCADOR = re.compile(r'\barrancador|\bjump ?starter|\bbooster\b|\barranque\b|\bpasa ?corriente')
_PANEL = re.compile(r'^(?:\S+ ){0,4}(panel|paneles|maleta|veliz)\b.{0,30}\bsolar')
_PLOMERIA = re.compile(r'\bregadera|\bmonomando|\bgrifo|\bmezcladora|\bllave (de|para) (lavabo|tina|regadera)|\bsalida (de )?tina|\bducha (de|con) (mano|telefono)|\bcabezal')
_WALKIE = re.compile(r'walkie|\bgmrs\b|\bfrs\b|\bpoc\b|\bbidireccional|\bdos vias\b|\buhf\b|\bvhf\b|\bbaofeng|\bretevis|\bmidland|\bmotorola (talkabout|t\d)|\bradio(s)? (de|para) (comunicacion|largo alcance)|\bauricular(es)? (para|de) radio')
_RADIO_AM = re.compile(r'\bam\b.{0,5}\bfm\b|\bam/fm|\bonda corta|\bsw\b|\bradio (portatil|de bolsillo|de emergencia|despertador|solar|de manivela)|\bnoaa\b')


# «Varios» (24-sep, segunda pasada): los grupos que se ven a simple vista.
# Lo que no cae en ninguno lo decide clasificar_restantes.py con el modelo.
_VARIOS = [
    (re.compile(r'^(?:\S+ ){0,3}(cuadros?|canvas|lienzos?|poster|posters|laminas? decorativas?)\b|'
                r'\bdecoracion (de|para) pared|\bimpresion (en lienzo|artistica)|\barte de pared'),
     ('Decoración de hogar y jardín', CUADROS)),
    (re.compile(r'mata ?mosquitos?|atrapa ?mosquitos?|\bmosquit|\binsectos?\b|\bmoscas?\b|\bplagas?\b|'
                r'\brepelente|\bcucarachas?|\btrampas? (para|de) (ratas?|ratones|moscas|insectos)'),
     ('Electrodomésticos', PLAGAS)),
    (re.compile(r'\beisco\b|\bmatraz|\bprobeta|\bvaso de precipitado|\bmicroscopio|\btubos? de (ensayo|espectro)|'
                r'\bespectro\b|\blaboratorio|\bbureta|\bpipeta|\bdetector (de metales|emf)|\bmedidor emf'),
     ('Herramientas', 'Medición')),
    (re.compile(r'\bselfie|\btripie|\btripode|\baro de luz|\baro de led|\bestabilizador|\bgimbal'),
     ('Cámaras y fotografía', 'Trípodes y soportes')),
    (re.compile(r'porta ?celular|soporte (para|de) (celular|telefono|iphone|movil)|\bventosa magnetica|'
                r'soporte de carga.{0,30}magsafe'),
     ('Celulares', SOPORTES)),
]


def reubicar_varios(tn):
    """(categoría, sub) para un «Otros / Varios» que cae en un grupo claro, o None."""
    for rx, destino in _VARIOS:
        if rx.search(tn):
            return destino
    return None


def reubicar(cat, sub, tn):
    """(categoría, subcategoría) donde va una ficha que hoy está en
    («Otros», sub), o None si se queda (sólo «Varios»). `tn` es el título
    normalizado (minúsculas, sin acentos)."""
    if cat != 'Otros' or sub is None:
        return None
    if sub == 'Varios':
        return reubicar_varios(tn)
    if sub in SUBS_SOLAR:
        return (SOLAR, sub)
    if sub == 'Estaciones de energía':
        if _ARRANCADOR.search(tn):
            return ('Autos, bicicletas y motos', 'Accesorios y refacciones')
        if _PANEL.search(tn):
            return (SOLAR, 'Paneles solares')
        return ('Baterías portátiles', 'Estaciones de energía')
    if sub == 'Soportes para dispositivos':
        return ('Celulares', SOPORTES)
    if sub == 'Baño':
        if _PLOMERIA.search(tn):
            return ('Herramientas', None)   # el repartidor de Herramientas elige (Plomería)
        return ('Blancos y ropa de cama', BANO)
    if sub == 'Organización del hogar':
        return ('Muebles', ORGANIZACION)
    if sub == 'Radios':
        if _WALKIE.search(tn):
            return ('Celulares', RADIOS_DOS_VIAS)
        if _RADIO_AM.search(tn):
            return ('Bocinas', 'Radios y reproductores')
        return ('Celulares', RADIOS_DOS_VIAS)
    return None


ICONO = {SOLAR: 'sun', 'Baterías portátiles': 'battery', 'Celulares': 'phone', 'Blancos y ropa de cama': 'pillow',
         'Muebles': 'sofa', 'Bocinas': 'speaker', 'Herramientas': 'wrench', 'Autos, bicicletas y motos': 'car'}

# La categoría nueva, con su escalón del medio (familias_subcategorias.py).
FAMILIAS_SOLAR = [
    ('Generación y almacenamiento', ['Paneles solares', 'Cargadores solares portátiles',
                                     'Kits solares y controladores de carga', 'Inversores']),
    ('Aparatos solares', ['Luces y ventiladores solares', 'Bombas y calentadores solares']),
]
ROLES_SOLAR = {'Accesorios y limpieza de paneles solares': 'accesorio'}
# Las subcategorías nuevas entran en la familia que ya tenía su categoría.
FAMILIAS_AGREGAR = {
    'Blancos y ropa de cama': ('Baño', BANO),
    'Muebles': ('Almacenamiento', ORGANIZACION),
    'Celulares': ('Teléfonos sencillos', RADIOS_DOS_VIAS),
}


# ------------------------------------------------------------------------
# Grupos que el modelo no podía colocar porque les faltaba subcategoría
# (24-sep-2026, segunda pasada sobre lo que quedó sin subcategoría: el
# modelo sin margen mandaba el mueble de baño a «Alacenas de cocina» y el
# aparador a «Escritorios de oficina»). Se aplican a lo que está sin
# subcategoría o en un comodín, y al alta (decidir()).
MUEBLES_BANO = 'Muebles de baño'
APARADORES = 'Aparadores y bufeteros'
GABINETES = 'Gabinetes de almacenamiento'
CAVAS = 'Cavas y porta botellas'
PINTAR = 'Manualidades y pintar por números'
REFACCIONES_CONSOLA = 'Refacciones de consolas y controles'
ADORNOS = 'Figuras y adornos'
NUEVAS += [
    ('Muebles', MUEBLES_BANO, 'sofa'), ('Muebles', APARADORES, 'sofa'), ('Muebles', GABINETES, 'sofa'),
    ('Muebles', CAVAS, 'sofa'), ('Juegos de mesa', PINTAR, 'dice'), ('Decoración de hogar y jardín', ADORNOS, 'box'), ('Videojuegos', REFACCIONES_CONSOLA, 'gamepad'),
]
ROLES_NUEVAS.setdefault('Videojuegos', {})[REFACCIONES_CONSOLA] = 'accesorio'
FAMILIAS_AGREGAR_VARIAS = {
    'Muebles': [('Almacenamiento', MUEBLES_BANO), ('Almacenamiento', APARADORES), ('Almacenamiento', GABINETES),
                ('Almacenamiento', CAVAS)],
}

_POR_GRUPO = [
    # (categorías donde aplica o None = cualquiera, regex, (categoría, sub))
    (('Muebles', 'Otros'), r'\bmuebles? (para|de) (bano|lavabo)|\blavabo flotante|\bgabinete de bano|\bbotiquin|\bmueble bajo lavabo',
     ('Muebles', MUEBLES_BANO)),
    (('Muebles', 'Otros'), r'\baparador|\bbufetero|\btrinchador|\bcredenza|\bbuffet\b', ('Muebles', APARADORES)),
    (('Muebles', 'Otros'), r'\bgabinetes? (bajo|superior|alto|metalico|de almacenamiento|para garaje|de garaje)|\bgabinete\b.{0,40}\bgaraje',
     ('Muebles', GABINETES)),
    (('Muebles', 'Otros'), r'\bcavas?\b|\bporta ?botellas|\bvinoteca|\bbotellero', ('Muebles', CAVAS)),
    (('Muebles',), r'^(?:\S+ ){0,2}salas? (esquinera|modular|en l|seccional)|\bsofa (seccional|esquinero)',
     ('Muebles', 'Sofás seccionales y esquineros')),
    (('Muebles',), r'\bchaise|\blounge\b|\bdivan\b', ('Muebles', 'Sillones y reclinables')),
    (('Muebles',), r'\bbase (electrica|ajustable)|\bbase de cama', ('Muebles', 'Bases de cama y box')),
    (('Muebles', 'Otros'), r'^(?:\S+ ){0,3}organizador', ('Muebles', ORGANIZACION)),
    (('Juegos de mesa',), r'\blienzo|\bpintar por numeros?|\bpinta por numeros?|\bpintura por numeros?|\bmanualidad',
     ('Juegos de mesa', PINTAR)),
    (('Videojuegos',), r'\b(reemplazo|repuesto|refaccion)\b|\bplaca (de circuito|base)|\bcarcasa de repuesto|\bjoystick de repuesto|\bbotones de repuesto',
     ('Videojuegos', REFACCIONES_CONSOLA)),
    (('Joyería y bisutería',), r'^(?:\S+ ){0,3}(cajas?|joyeros?|exhibidor(es)?|organizador(es)?|estuche)\b', ('Joyería y bisutería', 'Joyeros')),
    (('Cargadores y adaptadores', 'Otros'), r'(power ?bank|bateria (portatil|externa)|banco de energia)(?=.*\b\d[\d.,]* ?mah\b)',
     ('Baterías portátiles', None)),
    (None, r'^(?:\S+ ){0,2}(kit[- ])?cilindros?\b.{0,40}\b(kg|gas|regulador)|\btanque de gas|\bregulador (de|para) gas',
     ('Herramientas', 'Gas LP')),
    (('Otros',), r'^(?:\S+ ){0,3}bolsas? (de|para) (basura|almuerzo|sellado|snack|pan|congelar|alimentos)|\brollos de sellado',
     ('Cocina y comedor', 'Desechables')),
    (('Otros',), r'\bpaellera|\bcomal\b', ('Cocina y comedor', 'Sartenes y comales')),
    (('Otros',), r'^(?:\S+ ){0,2}bascula', ('Cocina y comedor', 'Básculas y medidores')),
    (('Blancos y ropa de cama',), r'\bcolchon (termico|electrico)|\bcalefaccion', ('Blancos y ropa de cama', 'Cobijas eléctricas')),
    (('Otros',), r'\bparrillas?\b|\basador|\bahumador|\bbbq\b|\bgrill\b|\bvirutas? de madera', ('Decoración de hogar y jardín', 'Asadores')),
    (('Otros',), r'\bminiatura|\bfigura decorativa|\badorno|\bsnow globe|\bbola de (cristal|nieve)|\bestatuilla|\bescultura',
     ('Decoración de hogar y jardín', ADORNOS)),
    (('Otros',), r'^(?:\S+ ){0,2}(navaja|cortaplumas|cuchilla multiusos)', ('Herramientas', 'Herramientas de corte manual')),
]
_POR_GRUPO = [(cats, re.compile(rx), dest) for cats, rx, dest in _POR_GRUPO]


def por_grupo(cat, tn):
    """(categoría, sub) para una ficha sin subcategoría (o en «Otros»/comodín)
    que cae en uno de los grupos de arriba, o None. Sub None = que el
    repartidor de la categoría destino elija."""
    for cats, rx, dest in _POR_GRUPO:
        if (cats is None or cat in cats) and rx.search(tn):
            return dest
    return None
