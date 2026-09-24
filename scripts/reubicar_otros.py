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
RADIOS_DOS_VIAS = 'Radios de dos vías'

# Subcategorías nuevas en categorías que ya existían: (categoría, sub, icono)
NUEVAS = [
    ('Celulares', SOPORTES, 'phone'),
    ('Celulares', RADIOS_DOS_VIAS, 'phone'),
    ('Blancos y ropa de cama', BANO, 'pillow'),
    ('Muebles', ORGANIZACION, 'sofa'),
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


def reubicar(cat, sub, tn):
    """(categoría, subcategoría) donde va una ficha que hoy está en
    («Otros», sub), o None si se queda (sólo «Varios»). `tn` es el título
    normalizado (minúsculas, sin acentos)."""
    if cat != 'Otros' or sub in (None, 'Varios'):
        return None
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
