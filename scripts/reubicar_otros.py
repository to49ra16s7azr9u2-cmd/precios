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


# ------------------------------------------------------------------------
# Tercera pasada (24-sep-2026, a pedido del usuario: «残りもルールを加えて減
# らしてください»): lo que quedaba en Varios y sin subcategoría, leído título
# por título y agrupado. Van DESPUÉS de las de arriba y sólo tocan lo que
# está en «Otros», sin subcategoría o en un comodín.
LIMPIEZA = 'Limpieza del hogar y lavandería'
ALBERCAS = 'Albercas y spa'
DELANTALES = 'Delantales y guantes de cocina'
LLAVEROS = 'Llaveros'
BROCHES = 'Broches y prendedores'
CARTERAS = 'Carteras y billeteras'
MANCUERNILLAS = 'Mancuernillas y accesorios de hombre'
TIARAS = 'Tiaras y accesorios para el cabello'
CAMARAS_CONSOLA = 'Cámaras para consola'
ANTIESTRES = 'Juguetes antiestrés'
NUEVAS += [
    ('Electrodomésticos', LIMPIEZA, 'appliance'), ('Decoración de hogar y jardín', ALBERCAS, 'box'),
    ('Cocina y comedor', DELANTALES, 'kitchen'), ('Joyería y bisutería', LLAVEROS, 'gem'),
    ('Joyería y bisutería', BROCHES, 'gem'), ('Joyería y bisutería', CARTERAS, 'gem'),
    ('Joyería y bisutería', MANCUERNILLAS, 'gem'), ('Joyería y bisutería', TIARAS, 'gem'),
    ('Videojuegos', CAMARAS_CONSOLA, 'gamepad'), ('Juguetes y bebés', ANTIESTRES, 'toy'),
]
ROLES_NUEVAS['Videojuegos'][CAMARAS_CONSOLA] = 'accesorio'

_O = ('Otros',)
_GRUPOS_3 = [
    # ---- Otros / Varios: cocina
    (_O, r'\bdelantal|\boven mitt|\bmanopla|\bprotectores de calor|\bguantes (para|de) (barbacoa|horno|cocina)', ('Cocina y comedor', DELANTALES)),
    (_O, r'\bbateria (de cocina|talent)|^(?:\S+ ){0,2}(jgo|juego) ekco', ('Cocina y comedor', 'Baterías de cocina')),
    (_O, r'\balmacenamiento de alimentos|\bsoportes? para huevos|\bdispensadores? de cereales|\bcaja bento|\bsouper cubes|'
         r'\bglad mini|\bcesta ovalada', ('Cocina y comedor', 'Contenedores herméticos')),
    (_O, r'\bbowls?\b|\bjuego de te\b|\btea for one|\bfuente para servir|\bsalvamantel|\bposavasos|\bset de sushi', ('Cocina y comedor', 'Platos y bowls')),
    (_O, r'\bcuberteria|\bcubiertos\b|\bpalillos .{0,20}metal', ('Cocina y comedor', 'Cubiertos')),
    (_O, r'\bdecantador|\bwhisky|\bcoctel|\bcocktail|\bmartini|\bbarril de envejecimiento|\bcoravin|\benfriador de latas|\bbar caddy|'
         r'\blineas de cerveza|\bbolsas? (de|para) vino|\balfombrilla de barra', ('Cocina y comedor', 'Bar y coctelería')),
    (_O, r'\bhornear|\bdecoracion de pasteles|\bbase giratoria|\bprensa de galletas|\bcajas? .{0,30}pasteles|\bmolde', ('Cocina y comedor', 'Repostería y moldes')),
    (_O, r'^(?:\S+ ){0,2}(bolsas?|popotes?|pajillas?|palitos|palillos agitadores|pinchos|brochetas?|tenedores|envoltura|envases?|'
         r'tapones para bebidas|saco de patata|juego de \d+ bolsas|pantallas de limpieza)\b', ('Cocina y comedor', 'Desechables')),
    (_O, r'\bprensa de ajo|\bcentrifug\w* de ensaladas|\bdesgranador|\bdeshuesador|\bcest[ao]s? (de|para) vapor|\bvapor de bambu|'
         r'\binserto para vapor|\bjuego de vapor|\bpala (de|para) pizza|\bcortapizzas|\bmolinos? de sal|\btamiz|\binfusor|\babre ?latas|'
         r'\bcucharilla|\bherramienta de huevo|\bremovedor de membrana|\bpesas de fermentacion|\bfermenter|\bgerminacion|'
         r'\btostonera|\btrompo\b|\bmaquina de pasta|\bsoplete|\bcepillo removedor|\blimpiador de pajillas|\bcalentador de mantequilla|'
         r'\bcubo para palomitas|\bcaja de recetas|\bcarpeta de recetas|\blibro de recetas|\bfundas de silicona|\bsoporte para (goteo|toalla de papel)|'
         r'\bbol de vidrio', ('Cocina y comedor', 'Utensilios de cocina')),
    (_O, r'^(?:\S+ ){0,2}tijeras', ('Herramientas', 'Herramientas de corte manual')),
    (_O, r'^(?:\S+ ){0,1}arrocera', ('Electrodomésticos', 'Arroceras y ollas multiusos')),
    (_O, r'\bmolino electrico para cafe', ('Electrodomésticos', 'Molinos y procesadores')),
    (_O, r'\bplanchas? (cozeer|grimate|\d+ ?cm)|\bprensa para plancha|\bplancha blackstone|\bbolsa de transporte para plancha|'
         r'\bdrenaje de grasa|\bencendedor(es)? (de carbon|tipo chimenea|de fuego)|\bkit de encendedor|\bflavorizer|\bflameengine|'
         r'\bparrilla de barbacoa', ('Decoración de hogar y jardín', 'Asadores')),
    # ---- limpieza, lavandería, albercas
    (('Otros', 'Mascotas'), r'\b(manchas|olores)\b.{0,40}\bmascotas|\bmascotas\b.{0,40}\b(manchas|olores)|\btoallitas para mascotas',
     ('Mascotas', 'Higiene y limpieza')),
    (('Otros', 'Decoración de hogar y jardín', 'Herramientas'), r'\bpiscinas?\b|\balbercas?\b|\bspa\b|\bcloro\b|\bclorador|\bpool\b|\bjacuzzi',
     ('Decoración de hogar y jardín', ALBERCAS)),
    (_O, r'\bdetergente|\bquitamanchas|\bremovedor de manchas|\blimpiador|\blimpiadora|\blimpia lavadoras|\bdesodoriz|\bambientador|'
         r'\btrapeador|\bfregadora|\batrapa ?pelusas?|\bbolas de lana|\blavanderia|\blaundry|\btoallitas|\bcera protectora|\bespuma limpiador|'
         r'\bsuavizante|\bpolvo de limpieza|\besterilizador|\bdesodorante adhesivo|\bgancho de almacenamiento',
     ('Electrodomésticos', LIMPIEZA)),
    # ---- celular
    (_O + ('Celulares',), r'\benfriador (para|de) (celular|telefono)|\bcooler para celular|\brefrigeradores? de telefonos|'
                          r'\bventilador (de )?refrigeracion celul|\btelefono retro|\bauricular retro|\bretroring|\blocalizador|'
                          r'\btarjeta de seguimiento|\bdispositivo de seguimiento|\btraductor', ('Celulares', 'Accesorios')),
    (_O + ('Celulares',), r'\banillo magnetico|\bring snap|\bhalolock|\bmagnetic smart holder|\bsoporte magnetico|\bsteelie|\bsalpicadero|'
                          r'\bporta vasos para auto.{0,40}telefono', ('Celulares', SOPORTES)),
    # ---- decoración, coleccionables
    (('Otros', 'Joyería y bisutería', 'Juegos de mesa'),
     r'\bcaja de musica|\breplica|\bestatua|\bplantilla\b|\bbanner\b|\bguirnalda|\bfeather flag|\bdecoracion de halloween|'
     r'\bchapado en oro de 24|\bcoleccionable fanattik|\bamuleto coleccionable|\blingote|\bbillete coleccionable|\bmarco de fotos',
     ('Decoración de hogar y jardín', ADORNOS)),
    (('Otros', 'Muebles'), r'\bposteres?|\bcarteles?\b|\bdecoracion de aula', ('Decoración de hogar y jardín', CUADROS)),
    (('Otros', 'Joyería y bisutería', 'Juegos de mesa'), r'^(?:\S+ ){0,4}llaveros?\b', ('Joyería y bisutería', LLAVEROS)),
    # ---- herramientas, camping, suplementos
    (_O, r'\bmedidor de voltaje|\bprobador de (bateria|valor)|\bcamara termica|\bmodelo de anatomia', ('Herramientas', 'Medición')),
    (_O, r'\bpiedra de (aplanado|afilar)|\bafilador|\bpulidor de cuero|\bcigar cutter', ('Herramientas', 'Herramientas de corte manual')),
    (_O, r'\bherramienta de apertura de electronica|\bespatulas', ('Herramientas', 'Herramientas manuales')),
    (_O, r'\bbrujula|\bplancha de camping|\bsupervivencia', ('Viajes', 'Camping')),
    (_O, r'\bimmunocal|\bglutation', ('Suplementos', 'Sistema inmune')),
    (_O, r'\bestuche (rigido )?para (audifonos|auriculares)', ('Audífonos', 'Accesorios')),
    # ---- Juegos de mesa / Otros juegos
    (('Juegos de mesa',), r'\bgeodas?|\bfosiles|\bkit de (ciencia|optica|quimica)|\boptica laser|\bgalton|\bdoppler|\beisco|\bnumberblocks|'
                          r'\bmathlink|\blearning|\beducativ|\btabla magnetica|\bcartel de emociones|\bmaravillas del mundo|\bpulidora de piedras',
     ('Juegos de mesa', 'Educativos')),
    (('Juegos de mesa',), r'\barcilla|\bslime|\brainbow loom|\bligas\b|\brollos de (hilo|liston)|\bmagic water|\brinconcito de libros|\bkit diy|'
                          r'\bcasa de juego de fieltro|\bset de gis', ('Juegos de mesa', PINTAR)),
    (('Juegos de mesa',), r'\bdespedida de soltera|\bfiesta\b|\bglobos', ('Juegos de mesa', 'De fiesta')),
    (('Juegos de mesa',), r'\bgodtear|\barkham|\bwargame|\bminiaturas de mesa|\bsenor de los anillos: duel', ('Juegos de mesa', 'De estrategia')),
    (('Juegos de mesa',), r'\bjuegos? de mesa|\bbananagrams|\bbaloncesto de mesa|\bmini hoop|\bcurling|\bdisc golf|\blanzamiento de anillos|'
                          r'\bbillar|\bmesa multijuego|\btumble|\bdaruma|\bcanicas|\bbolas magneticas|\bjuego de viajero|\bpeg\b|\bjuego de ensamble|'
                          r'\bjuego de tiro|\bjuegos para exteriores', ('Juegos de mesa', 'De mesa clásicos')),
    (('Juegos de mesa',), r'\bbeyblade|\bminiverse|\bmini coleccionables', ('Juguetes y bebés', 'Figuras de acción')),
    (('Juegos de mesa',), r'\bbarquitos de bano|\bbomba de agua .{0,20}ballena', ('Juguetes y bebés', 'Baño e higiene del bebé')),
    # ---- Joyería / Otros
    (('Joyería y bisutería',), r'\bmisterio\b|\brosario|\brelicario|\bcrucifijo|\breligios|\bcatolic|\bjoyeria de fe\b|\bsan (judas|benito)',
     ('Joyería y bisutería', 'Collares')),
    (('Joyería y bisutería',), r'\bbroche|\bbrooch|\bprendedor', ('Joyería y bisutería', BROCHES)),
    (('Joyería y bisutería', 'Otros'), r'\bbilletera|\bcartera (para|de) (hombre|mujer)|\btarjetero', ('Joyería y bisutería', CARTERAS)),
    (('Joyería y bisutería',), r'\bmancuernillas|\bgemelos|\bbow tie|\bcorbata|\bpisacorbata', ('Joyería y bisutería', MANCUERNILLAS)),
    (('Joyería y bisutería',), r'\bdiadema|\bcorona\b|\btiara|\btocado|\bheaddress|\bcrown\b|\bhair ', ('Joyería y bisutería', TIARAS)),
    (('Joyería y bisutería',), r'\bcuentas\b|\bbeads\b|\balambre|\bgrapa remache|\bkit de bisuteria|\bcordon para cuello|\bextensor de joyeria|'
                               r'\bmoissanite|\bloose\b|\bconnector jewelry|\bjibbitz|\bmaquina de joyeria', ('Joyería y bisutería', 'Material para bisutería')),
    (('Joyería y bisutería',), r'\bpano para pulir|\blimpiador(as)? para joyas|\bsoluciones limpiadoras|\bjewelry shield', ('Joyería y bisutería', 'Cuidado y herramientas')),
    (('Joyería y bisutería',), r'\bexpositor|\bmarco flotante|\bestuche para anteojos', ('Joyería y bisutería', 'Joyeros')),
    # ---- Videojuegos / Otros accesorios gamer
    (('Videojuegos',), r'\bmemory stick|\btarjeta (de )?memoria|\btarjeta expansion', ('Almacenamiento', 'Tarjetas SD y otras')),
    (('Videojuegos',), r'\bcamara\b', ('Videojuegos', CAMARAS_CONSOLA)),
    (('Videojuegos',), r'\bgatillos|\bdedales|\bkit de direccion', ('Videojuegos', 'Controles y gamepads')),
    (('Videojuegos',), r'\bpantalla (lcd|tactil)|\breplacement|\brepair|\breparacion|\bbutton|\bboton|\bscrew|\baltavoces internos|\bparts\b|'
                       r'\bkit de prueba|\balmohadillas|\bpadz\b', ('Videojuegos', REFACCIONES_CONSOLA)),
    (('Videojuegos',), r'\bwall mount|\bmount\b|\bsoporte', ('Videojuegos', 'Cargadores, bases y soportes')),
    (('Videojuegos',), r'\bkit de accesorios|\bbundle|\bkit de proteccion|\bcover\b|\bfunda|\bprotection|\bmochila|\bbackpack|\bmaleta|\bestuche|\bsticker',
     ('Videojuegos', 'Fundas, micas y protectores')),
    # ---- Herramientas / Electrodomésticos / Muebles / Juguetes / Cargadores sin subcategoría
    (('Herramientas',), r'\bducha|\bdesague|\bkohler', ('Herramientas', 'Regaderas y duchas')),
    (('Herramientas',), r'\blavadora a presion|\bhidrolavadora', ('Herramientas', 'Hidrolavadoras')),
    (('Herramientas',), r'\bbanco (de herramientas|modelo)|\bcarro de herramientas', ('Herramientas', 'Organización')),
    (('Herramientas',), r'\bbarredora|\bmaleza|\bcesped', ('Herramientas', 'Jardinería')),
    (('Herramientas',), r'\blija|\blijado|\bcinturon de papel', ('Herramientas', 'Lijas y accesorios de lijado')),
    (('Herramientas',), r'\bbomba (dosificadora|peristaltica)|\bmarshall equipment', ('Herramientas', 'Bombas de agua')),
    (('Herramientas',), r'\bengrasadora', ('Herramientas', 'Herramientas manuales')),
    (('Herramientas',), r'\bcargo box|\bcaja de techo', ('Autos, bicicletas y motos', 'Accesorios y refacciones')),
    (('Herramientas', 'Electrodomésticos'), r'\bmaquina de (mini )?donas', ('Electrodomésticos', 'Pequeños electrodomésticos de cocina')),
    (('Electrodomésticos',), r'\bwaffl|\bpanqueques|\bcorn dog|\btortillas', ('Electrodomésticos', 'Wafleras, sandwicheras y creperas')),
    (('Electrodomésticos',), r'\bcalentador(es)? de agua|\btermotanque|\bcorriente domestica', ('Electrodomésticos', 'Calentadores de agua')),
    (('Electrodomésticos',), r'\bfiltr\w* de agua|\bfiltrador de agua', ('Electrodomésticos', 'Filtros y membranas de repuesto')),
    (('Electrodomésticos',), r'\bpurificador de (aire|humo)|\bfiltros purificadores de aire', ('Climatización', 'Purificadores de aire')),
    (('Electrodomésticos',), r'\bpurificador para refrigerador', ('Electrodomésticos', 'Accesorios de purificador')),
    (('Electrodomésticos',), r'\bmaquina de hielo|\bmezclador de alimentos|\bextractor multifuncional', ('Electrodomésticos', 'Pequeños electrodomésticos de cocina')),
    (('Electrodomésticos', 'Juguetes y bebés'), r'\bhorno de microondas|\bmicroondas', ('Electrodomésticos', 'Microondas')),
    (('Muebles',), r'\bmesitas? de noche', ('Muebles', 'Burós')),
    (('Muebles',), r'\bliteras?\b', ('Muebles', 'Literas')),
    (('Muebles',), r'^(?:\S+ ){0,1}sala\b', ('Muebles', 'Sofás de 2 y 3 plazas')),
    (('Muebles',), r'\bestantes y buffeteras', ('Muebles', APARADORES)),
    (('Muebles',), r'\bmueble mostrador', ('Muebles', GABINETES)),
    (('Muebles',), r'\bcajones de almacenamiento|\bcarrito auxiliar', ('Muebles', ORGANIZACION)),
    (('Muebles',), r'\bhamaca', ('Muebles', 'Mecedoras y colgantes')),
    (('Juguetes y bebés',), r'\bproyector de fotos|\bllavero de camara|\bcamara (de|para) (viaje|campamento)', ('Juguetes y bebés', 'Juguetes educativos')),
    (('Juguetes y bebés',), r'\bantiestres|\bfidget', ('Juguetes y bebés', ANTIESTRES)),
    (('Juguetes y bebés',), r'\bcocina juguete|\bmi cocina\b|\bjuguete.{0,20}cocina|\bhorno freidora', ('Juguetes y bebés', 'Juguetes educativos')),
    (('Cargadores y adaptadores',), r'\bbateria (de vuelo|.{0,30}\b(dji|drone|mavic))|\bdrones?\b', ('Drones', 'Accesorios')),
    (('Cargadores y adaptadores',), r'\bpower ?bank|\bbateria (externa|portatil)|\bbanco de energia|\bcargador portatil \d', ('Baterías portátiles', None)),
    (('Cargadores y adaptadores',), r'\baudifonos|\bauricuares|\bauriculares', ('Audífonos', None)),
    (('Cargadores y adaptadores',), r'\bapple watch|\breloj(es)? solar', ('Relojes inteligentes', 'Fundas, cargadores y protectores')),
]
_POR_GRUPO += [(cats, re.compile(rx), dest) for cats, rx, dest in _GRUPOS_3]
FAMILIAS_AGREGAR_VARIAS.setdefault('Electrodomésticos', []).append(('Limpieza y ropa', LIMPIEZA))
FAMILIAS_AGREGAR_VARIAS.setdefault('Cocina y comedor', []).append(('Cocinar', DELANTALES))
