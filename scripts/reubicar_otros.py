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


# ------------------------------------------------------------------------
# Cuarta pasada (24-sep-2026, 48 en Varios y 414 sin subcategoría). Aquí
# muchas fichas estaban en la CATEGORÍA equivocada (artículos de bebé y de
# alberca en Juegos de mesa, tablas de planchar en Muebles, libros en
# inglés en cualquier lado), así que varias reglas cambian de categoría.
_MJ = ('Juegos de mesa',)
_JO = ('Joyería y bisutería',)
_MU = ('Muebles',)
_HE = ('Herramientas',)
_EL = ('Electrodomésticos',)
_VI = ('Videojuegos',)
_TODAS = ('Otros', 'Juegos de mesa', 'Muebles', 'Joyería y bisutería', 'Videojuegos', 'Herramientas')
_GRUPOS_4 = [
    # libros sueltos en cualquier categoría
    (_TODAS, r'^(?:\S+ ){0,4}(libro|el libro)\b|\bpublicacion independiente|\blibro autoeditado|\bintroduction to|\bresearch, theory|'
             r'\ba simple guide\b|\bwriting\b.{0,40}\b(routledge|research)|\bpublications international\b', ('Libros', None)),
    # Otros / Varios
    (_O, r'^(?:\S+ ){0,2}balanza', ('Cocina y comedor', 'Básculas y medidores')),
    (_O, r'\bbancos? de energia|\bbateria para magsafe', ('Baterías portátiles', None)),
    (_O, r'^(?:\S+ ){0,1}biberon', ('Juguetes y bebés', 'Biberones')),
    (_O + _HE, r'\bcaja fuerte|\bcandado biometrico', ('Herramientas', 'Cerraduras y candados')),
    (_O, r'^(?:\S+ ){0,1}cilindro \d+ ?kg', ('Herramientas', 'Gas LP')),
    (_O, r'\barmonica|\bbigote clip.?on para tuba|\bdjembe', ('Instrumentos musicales', None)),
    (_O, r'\bestuche.{0,40}\bpara (audifonos|auriculares)', ('Audífonos', 'Accesorios')),
    (_O, r'\bestuche para anteojos', ('Viajes', 'Accesorios de viaje')),
    (_O, r'\bteleprompter', ('Cámaras y fotografía', 'Accesorios')),
    (_O, r'\bteclado\b.{0,30}\b(bluetooth|inalambric)|\bkit de teclado', ('Teclados', None)),
    (_O, r'^(?:\S+ ){0,2}lana\b|\barcilla polimerica|\btela autoadhesiva para manualidades|\bherramientas de dibujo', ('Juegos de mesa', PINTAR)),
    (_O, r'\breloj despertador', ('Joyería y bisutería', 'Relojes de bolsillo y de pared')),
    (_O, r'\btapon de drenaje para refrigeradores igloo', ('Viajes', 'Camping')),
    (_O, r'\btabla colgante escalada', ('Deportes y fitness', None)),
    (_O, r'\bempunadura para telefono|\bagarre de telefono', ('Celulares', SOPORTES)),
    (_O, r'\btrituradora(s)? de (tejidos|muestras)', ('Herramientas', 'Medición')),
    # Juegos de mesa / Otros juegos
    (_MJ, r'\bbeb[ea]s?\b|\bbaby\b|\bplay space|\bcapazo|\bcaballito montable', ('Juguetes y bebés', None)),
    (_MJ, r'\bnatacion|\bflotacion|\bpistolas? de agua|\barenero|\bbolos\b|\bflying disc|\bpopdarts|\bjuego activo|\bluz roja luz verde',
     ('Juguetes y bebés', 'Juguetes para exterior')),
    (_MJ, r'\bkit de (diseccion|actividades|practica de soldadura|modelo de motor)|\btriops|\bterrario|\bpellets .{0,20}buho|\bhotel de bichos|'
          r'\bteaching stones|\bagenda visual|\btangram|\bsopa de silabas|\basociacion de imagenes|\blaberinto|\bbrain challenger|\bcilindros de encaje|'
          r'\bglobe toy|\borboot|\bdiana emocional|\btarro de recompensas|\bgorra de seguimiento eeg', ('Juegos de mesa', 'Educativos')),
    (_MJ, r'\bjuego de viaje|\bhedbanz|\bque soy\b|\btaco gato|\bmah jongg|\bshut the box|\bjuego de hilo|\bcat.?s cradle|\bequilibrio\b|'
          r'\bset de juegos \d+ en 1|\bbandeja para tarjetas|\bjuego de gato|\bdoteki|\bslang-o-matic', ('Juegos de mesa', 'De mesa clásicos')),
    (_MJ, r'\brollos (de )?(hilo|liston)|\bplay-?doh|\bplastilina|\bpegatina|\bfold-roller|\bcarton\b', ('Juegos de mesa', PINTAR)),
    (_MJ, r'\bjuego nintendo|\bnintendo switch\b', ('Videojuegos', 'Juegos Nintendo Switch')),
    (_MJ, r'\bimanes decorativos|\bpuerta y ventanas de hadas|\brueda de oracion', ('Decoración de hogar y jardín', ADORNOS)),
    (_MJ, r'\bguarderia|\bmunecas?\b|\bsupermercado|\bcasita\b', ('Juguetes y bebés', 'Muñecas')),
    # Joyería / Otros
    (_JO, r'\b(conjunto|juego|set) (de )?joyeria|\bjewelry set|\bjoyeria de \d piezas|\bset nudo de bruja|\bjuego joyeria', ('Joyería y bisutería', 'Arras y sets')),
    (_JO, r'^(?:\S+ ){0,1}(aro|arracadas?|arrancadas|violadores)\b|\bjoyas para las orejas|\bpiercing|\bperforacion de orejas', ('Joyería y bisutería', 'Aretes')),
    (_JO, r'\balicates para joyeria|\bcortadores (generic )?para joyeria|\bfranela para limpiar joyeria|\bmaquina de perforacion.{0,30}joyeria',
     ('Joyería y bisutería', 'Cuidado y herramientas')),
    (_JO, r'\banillas abiertas|\bgemas\b|\bagata\b|\bempaques de bisuteria|\bestuches para bisuteria|\btaller de joyeria|\bkit de joyeria|'
          r'\bkit de actividad sorpresa de estudio de joyeria|\bmi taller de joyeria', ('Joyería y bisutería', 'Material para bisutería')),
    (_JO, r'\bcinturon', ('Joyería y bisutería', MANCUERNILLAS)),
    (_JO, r'\bporta-?puas', ('Instrumentos musicales', 'Accesorios de guitarra')),
    (_JO, r'\bjoyeria (de fe|espiritual|religiosa)|\bfeventdepot|\bespiritualventdepot', ('Joyería y bisutería', 'Collares')),
    # Muebles / Otros y sin subcategoría
    (_MU, r'\bburro de planchar|\btabla de planchar', ('Electrodomésticos', 'Planchas')),
    (_MU, r'\btendedero|\bcesto de ropa', ('Electrodomésticos', LIMPIEZA)),
    (_MU, r'\bco?l?chon\b.{0,40}\bqueen|\bqueen\b.{0,40}\bco?l?chon', ('Muebles', 'Colchones queen size')),
    (_MU, r'\bco?l?chon\b.{0,40}\bking|\bking\b.{0,40}\bco?l?chon', ('Muebles', 'Colchones king size')),
    (_MU, r'\bnapnest|\bco?l?chon\b.{0,40}\bmatrimonial', ('Muebles', 'Colchones matrimoniales')),
    (_MU, r'\bdespensero|\bgabinete inferior|\bmueble organizador multiusos|\bgabinete de bar', ('Muebles', GABINETES)),
    (_MU, r'\bmesitas auxiliares', ('Muebles', 'Mesas auxiliares y laterales')),
    (_MU, r'\bmesitas\b.{0,40}\bcajones', ('Muebles', 'Burós')),
    (_MU, r'\bespejo cuerpo completo', ('Decoración de hogar y jardín', 'Espejos de cuerpo completo')),
    (_MU, r'\bmaceta decorativa', ('Decoración de hogar y jardín', ADORNOS)),
    (_MU, r'\bbase para monitor|\bsoporte para laptop|\bbandeja ergonomica para teclado', ('Componentes y accesorios de PC', 'Accesorios de monitor')),
    (_MU, r'\bportarrollos de bano', ('Blancos y ropa de cama', BANO)),
    (_MU, r'\bbetafpv|\bdron fpv|\btransmisor de radio', ('Drones', 'Accesorios')),
    (_MU, r'\bcorrea de cabeza vr|\bmeta quest', ('Videojuegos', 'Realidad virtual')),
    (_MU, r'\bpeluches?\b|\bpillow plush', ('Juguetes y bebés', 'Peluches')),
    (_MU, r'\bbaby bouncer|\bbright starts', ('Juguetes y bebés', 'Sillas de comer y mecedoras')),
    (_MU, r'\bcarpa infantil|\btunel exterior|\bset de gis', ('Juguetes y bebés', 'Juguetes para exterior')),
    (_MU, r'\bpatines\b', ('Deportes y fitness', None)),
    (_MU, r'\bprotector de bozal', ('Mascotas', None)),
    (_MU, r'\btable curling|\bhold.?em table|\bchess table', ('Juegos de mesa', 'De mesa clásicos')),
    (_MU, r'\bbase giratoria ateco', ('Cocina y comedor', 'Repostería y moldes')),
    # Herramientas sin subcategoría
    (_HE, r'\babocinad|\bexpansora de resorte|\bcompresion de resortes|\bguia para atornillar|\bkit tipo cartera|\btool-check|\bmango ajustable',
     ('Herramientas', 'Herramientas manuales')),
    (_HE, r'\bbomba (autocebante|rotativa)|\btornillo de purga', ('Herramientas', 'Bombas de agua')),
    (_HE, r'\bcabezal de duch|\bhansgrohe', ('Herramientas', 'Regaderas y duchas')),
    (_HE, r'\bmueble para bano', ('Muebles', MUEBLES_BANO)),
    (_HE, r'\barcon rodante', ('Herramientas', 'Organización')),
    (_HE, r'\bcaja porta ?equipaje|\bportaquipaje', ('Autos, bicicletas y motos', 'Accesorios y refacciones')),
    (_HE, r'\bpulidor|\bgorros de pulido|\bmenzerna', ('Herramientas', 'Esmeriladoras y pulidoras')),
    (_HE, r'\blaminadora|\bprensado de tabletas|\bmolino de laminacion|\bmicromotor.{0,40}joyeria|\bperforacion.{0,60}joyeria',
     ('Joyería y bisutería', 'Cuidado y herramientas')),
    (_HE, r'\bconexion presion rapida', ('Herramientas', 'Neumáticas')),
    (_HE, r'\bcadena distribucion', ('Autos, bicicletas y motos', 'Accesorios y refacciones')),
    (_HE, r'\bplaca de control.{0,40}lavadora', ('Refacciones', 'Refacciones para lavadora y secadora')),
    (_HE, r'\bmango de armario', ('Muebles', 'Herrajes y refacciones de muebles')),
    (_HE, r'\bmaquina de limpieza de suelos|\blimpiacristales', ('Electrodomésticos', LIMPIEZA)),
    # Electrodomésticos sin subcategoría
    (_EL, r'\bninja slushi|\bbebidas congeladas', ('Electrodomésticos', 'Máquinas de helados y postres')),
    (_EL, r'\bfreidora (neumatica|de aire)', ('Electrodomésticos', 'Freidoras de aire')),
    (_EL, r'\bfreidora de mesa', ('Electrodomésticos', 'Freidoras eléctricas')),
    (_EL, r'\bmini maquina (para|portatil)|\btaiyaki|\bbanderillas|\bcupcakes', ('Electrodomésticos', 'Pequeños electrodomésticos de cocina')),
    (_EL, r'\bjuice fountain|\bextractor de jugo', ('Electrodomésticos', 'Extractores de jugo')),
    (_EL, r'\bcalentador instantaneo|\brheem\b', ('Electrodomésticos', 'Calentadores de agua')),
    (_EL, r'\bfiltro (de sedimentos|para agua)', ('Electrodomésticos', 'Filtros y membranas de repuesto')),
    (_EL, r'\brecubri\w* (de )?tabletas|\bpurificador de frutas', ('Electrodomésticos', 'Otros electrodomésticos de cocina')),
    (_EL, r'\bcuidado de sombreros', ('Electrodomésticos', 'Vaporizadores de ropa')),
    # Videojuegos / Otros accesorios gamer
    (_VI, r'\bpalanca de velocidades', ('Videojuegos', 'Volantes, arcade y simuladores')),
    (_VI, r'\btarjeta de captura|\bamiibo|\bemulador|\bamplificador de audifonos', ('Videojuegos', 'Cables y adaptadores')),
    (_VI, r'\bxbox live|\btarjeta de acceso', ('Videojuegos', 'Tarjetas y suscripciones')),
    (_VI, r'\bteclado\b.{0,40}\bpara (controlador|xbox|ps5)|\bagarres para palanca|\bcobertura para palanca|\bpara palanca analogica',
     ('Videojuegos', 'Controles y gamepads')),
    (_VI, r'\bkit (de )?(\d+ )?accesorios|\bkit de inicio|\bkit powera|\bjuego de proteccion', ('Videojuegos', 'Fundas, micas y protectores')),
    (_VI, r'\bkit de herramientas.{0,30}(abrir|desmontar)', ('Videojuegos', REFACCIONES_CONSOLA)),
    (_VI, r'\bvideojuego\b.{0,60}\bps4', ('Videojuegos', 'Juegos PS4')),
    (_VI, r'-switch\b|\bswitch \(\[bonus', ('Videojuegos', 'Juegos Nintendo Switch')),
]
_POR_GRUPO += [(cats, re.compile(rx), dest) for cats, rx, dest in _GRUPOS_4]


# ------------------------------------------------------------------------
# Quinta pasada (24-sep-2026): las ~240 que seguían sin clasificar, leídas
# título por título. Muchas estaban en una categoría equivocada que ninguna
# regla de arriba miraba (colchones en Blancos, calentadores de biberón en
# Climatización, peluches para perro y libros en Mascotas...), por eso casi
# todas son «cualquier categoría» (None): por_grupo sólo toca lo que está
# en «Otros», sin subcategoría o en un comodín.
#
# Libros con su género: van ANTES que todo (la regla de libros de la cuarta
# pasada no les daba subcategoría y el repartidor de Libros no encontraba
# una, así que se quedaban donde estaban).
_LIBROS_5 = [
    (None, r'\bbodily autonomy|\bwomen.?s writing', ('Libros', 'Filosofía y ensayo')),
    (None, r'\bcreative writing and wellbeing', ('Libros', 'Psicología')),
    (None, r'\bmy period my power', ('Libros', 'Salud y bienestar')),
    (None, r'\blibro completo de solitario', ('Libros', 'Hogar, manualidades y mascotas')),
    (None, r'\blibro de imagenes de cachorros|\bel gato que (amaba los libros|venia del cielo)|^yo, el gato$', ('Libros', 'Infantil')),
    (None, r'\bhacking the xbox', ('Libros', 'Técnicos y profesionales')),
    (None, r'\bprovidence \(tides of fortune\)', ('Libros', 'Fantasía')),
    (None, r'\bwarrior of my own', ('Libros', 'Autoayuda y desarrollo personal')),
    (None, r'\blibro dutton decadence', ('Libros', 'Novela romántica')),
]
_BEBE = 'Juguetes y bebés'
_GRUPOS_5 = [
    # colchones y protectores fuera de Muebles
    (None, r'\bcolchon impermeable', ('Blancos y ropa de cama', 'Protectores de colchón impermeables')),
    (None, r'\bcolchon acolchado|\bcolchon utopia bedding acolchado', ('Blancos y ropa de cama', 'Protectores de colchón acolchados')),
    (None, r'\bcolchon (de cuna|para corral)', ('Muebles', 'Colchones infantiles y de cuna')),
    (None, r'\bcolchon viscoelastico.{0,60}\b(doble|matrimonial)', ('Muebles', 'Colchones matrimoniales')),
    (None, r'\b(alfombra )?cambiador(a)?\b.{0,40}\b(panal|impermeable)|^(?:\S+ ){0,1}cambiador colchon', (_BEBE, 'Pañales y cambio')),
    (None, r'\bropa para cama\b.{0,30}\bmuneca', (_BEBE, 'Muñecas')),
    (None, r'^tapete de mesa', ('Cocina y comedor', 'Manteles y caminos de mesa')),
    # bebés
    (None, r'\bcalentador (portatil )?de biberon', (_BEBE, 'Alimentación y lactancia')),
    (None, r'\bmedicion del tamano de bridas', (_BEBE, 'Alimentación y lactancia')),
    (None, r'\bcolumpio electrico\b.{0,30}\bbebe', (_BEBE, 'Sillas de comer y mecedoras')),
    (None, r'\bmamadera\b', (_BEBE, 'Biberones')),
    (None, r'\bpolvo para bebes|\bmustela baby', (_BEBE, 'Baño e higiene del bebé')),
    (None, r'\bbaby trend\b.{0,40}\bcapazo', (_BEBE, 'Carriolas')),
    (None, r'\bplay space\b|\bcorral\b.{0,20}\bpaneles', (_BEBE, 'Corrales')),
    (None, r'\bstroll .?n trike', (_BEBE, 'Triciclos')),
    (None, r'\bjuego de instrumentos musicales\b.{0,30}\bninos|\bmusical instrument toy|\bteclado electrico\b.{0,40}\bninos', (_BEBE, 'Juguetes musicales')),
    (None, r'^playmobil\b|\bpop funko|\bfunko pop', (_BEBE, 'Figuras de acción')),
    (None, r'\bcasa de campana infantil', (_BEBE, 'Juguetes para exterior')),
    (None, r'\bcompatible con lego\b', (_BEBE, 'Bloques de construcción')),
    # mascotas
    (None, r'\bpeluche\b.{0,50}\bpara (perro|mascotas)|\bpeluche (pesado )?para (perro|mascotas)', ('Mascotas', 'Juguetes para perro')),
    (None, r'\bpuerta\b.{0,40}\bpara mascotas', ('Mascotas', 'Puertas para mascotas')),
    # salud y cuidado personal
    (None, r'\bnebulizador compresor', ('Salud', 'Nebulizadores')),
    (None, r'\bcepillos? de dientes plegables|\besmerilado dental', ('Salud', 'Cuidado dental')),
    (None, r'\bgel corporal', ('Belleza y cuidado personal', 'Corporales')),
    (None, r'\bgel nail lamp|\blampara (uv )?de unas|\breposabrazos para unas', ('Belleza y cuidado personal', 'Uñas')),
    (None, r'\bcepillo de joyas', ('Joyería y bisutería', 'Cuidado y herramientas')),
    # climatización
    (None, r'\bcirculador de aire industrial', ('Climatización', 'Ventiladores de piso e industriales')),
    (None, r'\balfombrillas? de calefaccion usb', ('Blancos y ropa de cama', 'Mantas eléctricas USB y portátiles')),
    # muebles
    (None, r'\bcarro de (bebidas|cocina)|\bcarro de bebidas', ('Muebles', 'Carros e islas de cocina')),
    (None, r'^mueble multimedia', ('Muebles', 'Mesas para TV y consolas')),
    (None, r'\bde 2 cuerpos\b.{0,20}\btela', ('Muebles', 'Sofás de 2 y 3 plazas')),
    (None, r'\bdescansa ?pies|\breposapies?\b', ('Muebles', 'Puffs y otomanas')),
    (None, r'^gabinete multifuncional', ('Muebles', 'Gabinetes de almacenamiento')),
    (None, r'\bhinge\b', ('Muebles', 'Herrajes y refacciones de muebles')),
    (None, r'duerme comodamente con esta almohada', ('Blancos y ropa de cama', 'Almohadas')),
    # domótica
    (('Domótica y hogar inteligente',), r'\binterruptor regulador|\batenuador\b', ('Domótica y hogar inteligente', 'Dimmers y reguladores inteligentes')),
    (None, r'\bcalendario digital inteligente|\bhogar inteligente panel de control', ('Domótica y hogar inteligente', 'Hubs')),
    (None, r'\btuya\b.{0,40}\binterruptor', ('Domótica y hogar inteligente', 'Módulos y relés inteligentes')),
    (None, r'^philips hue\b.{0,20}\bcable colgante', ('Domótica y hogar inteligente', 'Lámparas y plafones inteligentes')),
    # teclados
    (None, r'^kit\b.{0,40}\bteclado\b.{0,60}\bmouse|\bteclado inalambrico con mouse', ('Teclados', 'Combos con mouse')),
    (('Teclados',), r'\bteclado iluminado\b.{0,40}\bcon cable', ('Teclados', 'Membrana')),
    # autos y refacciones
    (None, r'\baltavoces frontales\b.{0,40}\b5\.25|\bbocinas traseras\b.{0,40}\b5\.25', ('Autos, bicicletas y motos', 'Bocinas de 4 a 5.25 pulgadas')),
    (None, r'^bocina italika', ('Autos, bicicletas y motos', 'Accesorios para moto')),
    (None, r'\bbocina electrica para (ford|gm)|\bbocina de sirena antirrobo', ('Autos, bicicletas y motos', 'Accesorios y refacciones')),
    (None, r'^camara (llanta|para bicicleta)\b', ('Autos, bicicletas y motos', 'Cámaras y accesorios de llanta')),
    (None, r'\bbomba de refrigeracion del compresor de aire acondicionado', ('Refacciones', 'Enfriamiento y climatización')),
    (None, r'\bbocinas marinas', ('Autos, bicicletas y motos', 'Bocinas marinas y para moto')),
    # computación
    (None, r'\bsynology diskstation|\bkit diy nas', ('Almacenamiento', 'NAS')),
    (None, r'\bssd nvme\b', ('Almacenamiento', 'SSD NVMe M.2')),
    (None, r'^ventilador de refrigeracion\b.{0,20}\bpara asus', ('Componentes y accesorios de PC', 'Enfriamiento y ventiladores')),
    (None, r'\bmonitor intrauditivo|\biem\b', ('Audífonos', 'Earbuds con cable')),
    # cocina
    (None, r'^(?:\S+ ){0,1}jarra de agua|^juego de jarra de agua|\bdispensador de cafe\b.{0,30}\b\d+ ?l\b', ('Cocina y comedor', 'Jarras y dispensadores de bebidas')),
    (None, r'^(set de \d+ )?tablas? para (picar|cortar)', ('Cocina y comedor', 'Cuchillos y tablas')),
    (None, r'\bcajas transparentes\b.{0,40}\bpasteles', ('Cocina y comedor', 'Repostería y moldes')),
    (None, r'\bpiezas medidoras', ('Cocina y comedor', 'Básculas y medidores')),
    (None, r'^lunch box\b', ('Cocina y comedor', 'Loncheras y termos para alimentos')),
    (None, r'^secadora de ropa portatil', ('Electrodomésticos', LIMPIEZA)),
    (None, r'\baccesorio cafeteras superautomaticas|\bpara cafeteras jura', ('Cafeteras', 'Accesorios para cafetera')),
    # varios
    (None, r'\btablas de pizarra', ('Papelería y oficina', 'Pizarrones')),
    (None, r'^adaptador t power 12v', ('Cargadores y adaptadores', 'Adaptador de corriente')),
    (None, r'^panel solar de \d+ ?w', ('Energía solar', 'Paneles solares')),
    (None, r'\bprensado en caliente\b.{0,30}\bsublimacion', ('Equipo comercial', 'Prensas de calor')),
    (None, r'\bvolteador de paginas', ('Instrumentos musicales', 'Accesorios')),
    (None, r'\beslabon doble\b.{0,30}\bpandora', ('Joyería y bisutería', 'Dijes y charms')),
    (None, r'^crossbody coach', ('Joyería y bisutería', 'Carteras y billeteras')),
    (None, r'\bconjunto millenia\b|\bjoyeria cristal para mujer', ('Joyería y bisutería', 'Arras y sets')),
    (None, r'^reloj despertador\b', ('Joyería y bisutería', 'Relojes de bolsillo y de pared')),
    (None, r'\blampara(s)? redondas de papel', ('Iluminación', 'Decorativa')),
]
_POR_GRUPO = ([(cats, re.compile(rx), dest) for cats, rx, dest in _LIBROS_5] + _POR_GRUPO
              + [(cats, re.compile(rx), dest) for cats, rx, dest in _GRUPOS_5])


# ------------------------------------------------------------------------
# «Limpieza y hogar» (24-sep-2026): con los feeds de Walmart, Bodega Aurrerá
# y Sam's entra todo lo que no es comida (a pedido del usuario: «基本的に食
# 品以外は取り込んでいきましょう»), y los consumibles de la casa no tenían
# dónde caer (un detergente a «Blancos», un insecticida a «Electrodomésticos»).
LIMPIEZA_HOGAR = 'Limpieza y hogar'
SUBS_LIMPIEZA_HOGAR = ['Detergentes y suavizantes', 'Limpiadores y desinfectantes', 'Papel higiénico y servilletas',
                       'Bolsas de basura y desechables', 'Aromatizantes y velas', 'Insecticidas y repelentes']
ICONO[LIMPIEZA_HOGAR] = 'house'
FAMILIAS_LIMPIEZA_HOGAR = [
    ('Lavandería', ['Detergentes y suavizantes']),
    ('Limpieza de la casa', ['Limpiadores y desinfectantes', 'Insecticidas y repelentes']),
    ('Papel y desechables', ['Papel higiénico y servilletas', 'Bolsas de basura y desechables']),
    ('Ambiente', ['Aromatizantes y velas']),
]
# En esta categoría el consumible ES el producto: todas quedan con el rol
# por defecto («producto»), para que encabecen su orden por precio.
ROLES_LIMPIEZA_HOGAR = {}
