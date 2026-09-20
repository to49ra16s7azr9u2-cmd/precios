#!/usr/bin/env python3
"""Arma grupos de movimiento (el JSON que lee aplicar_movimientos.py) a
partir de reglas explícitas: categoría de origen + expresión sobre el
título -> categoría y subcategoría de destino.

POR QUÉ
-------
Tras repartir las fichas sin subcategoría (19-sep-2026) lo que queda sin
subcategoría es, en su mayoría, ficha con la CATEGORÍA equivocada por la
taxonomía de su tienda: walkie-talkies en Audífonos, instrumental dental y
de belleza en Herramientas, placas y apagadores comunes en Domótica,
correas de reloj en Relojes inteligentes, cabezas móviles de escenario en
Instrumentos, teclados musicales en Teclados. El auditor por acuerdo
(modelo + reglas) no las alcanza porque el clasificador de capturas no
tiene regla de categoría para todas, y el modelo solo propone destinos
dentro de lo que ya vio. Acá se nombran una por una, con su regla, y se
aplican con la misma bitácora que los demás movimientos.

USO
---
    python3 scripts/mover_por_regla.py --salida /tmp/mover_reglas.json      # informa y escribe
    python3 scripts/aplicar_movimientos.py /tmp/mover_reglas.json --todos --motivo "..."
"""
import argparse
import collections
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import load_catalog  # noqa: E402
from subcategorias_finas import sub_cocina_fino  # noqa: E402
import subcategorias_finas_ola2 as ola2  # noqa: E402


def T(s):
    s = re.sub(r'\s+', ' ', (s or '').lower())
    return s.translate(str.maketrans('áéíóúñü', 'aeiounu'))


def tramo_mah(tn):
    m = re.search(r'(\d{1,3}[.,]?\d{3}|\d{4,6})\s*m ?ah', tn)
    if not m:
        return None
    n = int(m.group(1).replace('.', '').replace(',', ''))
    return 'Hasta 10,000 mAh' if n <= 10000 else ('10,000 a 20,000 mAh' if n <= 20000 else 'Más de 20,000 mAh')


# (categoría origen, regex que debe cumplir, regex que NO debe cumplir o None,
#  categoría destino, subcategoría destino o función(tn) -> sub|None)
REGLAS = [
    ('Audífonos', r'walkie|talkie|\bradios?\b(?! ?control)|onda corta|reproductor (mp3|de cd|de musica)|discman|intercomunicador',
     r'^(?:\S+ ){0,2}(auricular|audifono|headset|earbud|headphone)|radio fm|for iphone|mp3 player|conduccion osea|open ?ear',
     'Bocinas', 'Radios y reproductores'),
    ('Audífonos', r'^(?:\S+ )?microfono', r'diadema con microfono|con microfono|auricular|audifonos? con', 'Instrumentos musicales', 'Micrófonos'),
    ('Herramientas', r'\bdental|\bbucal|articulador', None, 'Belleza y cuidado personal', 'Cuidado personal'),
    ('Herramientas', r'manicura|pedicura|\bunas\b|nail (art|drill|lamp|tips)|\bnails\b', r'aerografo|pulverizador de pintura', 'Belleza y cuidado personal', 'Uñas'),
    ('Herramientas', r'\bfacial|guasha|gua sha|analizador de (piel|cabello)|cuero cabelludo|celulitis|drenaje linfatico|escultura corporal|esculpir corporal',
     None, 'Belleza y cuidado personal', 'Dispositivos de cuidado facial'),
    ('Herramientas', r'\bcabello\b|\bbarba\b|\bbarber|\bbigote\b|peinar|extensiones de cabello|\bpelo\b|peluquer', r'lija|sierra|taladro', 'Belleza y cuidado personal', 'Cuidado del cabello'),
    ('Herramientas', r'maquillaje|corrector|paleta de crema', None, 'Belleza y cuidado personal', 'Maquillaje'),
    ('Herramientas', r'\bobd ?2\b|\bobd ?ii\b|escaner automotriz|diagnostico automotriz', None, 'Autos, bicicletas y motos', 'Accesorios y refacciones'),
    ('Herramientas', r'masaje|masajeador|rodillo de masaje|spiky ball', None, 'Belleza y cuidado personal', 'Masajeadores'),
    ('Herramientas', r'agarres? (para|de) gym|agarraderas|para gym\b|para gimnasio', None, 'Deportes y fitness', 'Accesorios de fuerza'),
    ('Domótica y hogar inteligente', r'apagador|tapa ciega|placa (armada|ciega|cristal|valo|solaris|lugano|flat|slim|dimmer|de (acero|aluminio|plastico|nylon|cristal|pared)|con \d|\d|cubre)|'
     r'(\d|con|dos|tres) (contactos?|interruptores?|apagadores?|modulos?)\b|cubierta para interruptor|tapa para placa|placa cubre',
     r'intelig|wifi|wi-fi|tuya|zigbee|alexa|smart|matter|\bapp\b|magnetic|shelly|sonoff|\bwiz\b|connected',
     'Herramientas', 'Material eléctrico'),
    ('Domótica y hogar inteligente', r'letrero|\bneon\b', r'intelig|wifi|smart|tuya|alexa|\bapp\b|rgbic|govee|tira', 'Iluminación', 'Decorativa'),
    ('Domótica y hogar inteligente', r'adaptador (universal )?de (viaje|enchufe)|adaptador de enchufe|enchufe (europeo|americano)|convertidor a tierra',
     r'control remoto|\bfoco\b|intelig', 'Cargadores y adaptadores', 'Adaptador de corriente'),
    ('Domótica y hogar inteligente', r'kit.{0,25}camaras|\bcctv\b|\bdahua\b|\bhikvision\b|\bnvr\b|\bdvr\b', None, 'Cámaras de seguridad', 'Kits de vigilancia'),
    ('Relojes inteligentes', r'\bcorreas?\b|extensible|pulsera (de|elastica|para|deportiva)|banda (de|para) reloj',
     r'apple watch|galaxy watch|smart ?watch|mi band|fitbit|garmin|huawei watch|amazfit|smart|whoop|pixel watch|xiaomi',
     'Joyería y bisutería', 'Correas y extensibles'),
    ('Instrumentos musicales', r'cabeza (movil|robotica)|cabezas moviles|\bpar ?led\b|\bpar ?\d{2,3}\b|estrobo|\bdmx\b|\bbeam\b|\bwash\b|barra led|maquina de humo|liquido.{0,10}humo|canon de luces|elevacion.{0,20}iluminacion|\bwasher\b|luces led (par|rgb)|kit home party|\bgobo\b',
     r'cuerdas|strings', 'Iluminación', 'Escenario'),
    ('Teclados', r'\b(25|32|37|49|54|61|76|88) teclas\b|casiotone|\bpsr|\byamaha\b|\bcasio\b|\balesis\b|\bpiano\b|\bkboard\b|\bkosmos\b|\bkorg\b|\broland\b|teclado (musical|digital|infantil)',
     r'mecanic|gamer|gaming|\busb\b|qwerty|espanol|\bpc\b|computadora|juego|membrana|touchpad|bluetooth|inalambric|2\.4 ?g|para (mac|windows|ipad|tablet)', 'Instrumentos musicales', 'Teclados electrónicos'),
    ('Cargadores y adaptadores', r'power ?bank|banco de energia|bateria (externa|portatil)|powerbank', None, 'Baterías portátiles', tramo_mah),
    ('Baterías portátiles', r'arrancador|jump ?starter', None, 'Autos, bicicletas y motos', 'Baterías para auto'),
    ('Juegos de mesa', r'play-?doh|\bslime\b|plastilina|kit de ciencia|pegatinas|stickers|arena sensorial|cuaderno de actividades|libro de (pegatinas|actividades)',
     None, 'Juguetes y bebés', 'Juguetes educativos'),
    ('Iluminación', r'interruptor termomagnetico|placa armada|extension domestica|\bapagador|\bcontacto\b|pastilla termo', r'intelig|wifi', 'Herramientas', 'Material eléctrico'),
    ('Cámaras y fotografía', r'protector (de )?lente.{0,40}(iphone|samsung|galaxy|pixel|xiaomi|celular|smartphone)|mica.{0,20}camara.{0,30}(iphone|galaxy|pixel)',
     None, 'Celulares', 'Accesorios'),
    ('Televisores', r'^(?:\S+ ){0,3}(auriculares|audifonos)', None, 'Audífonos', 'Diadema inalámbrica'),
    ('Televisores', r'barra de sonido|\bsoundbar\b', None, 'Bocinas', 'Barras de sonido'),
    ('Mascotas', r'carriola.{0,25}\bbebe\b|para bebe\b', r'perro|gato|mascota', 'Juguetes y bebés', 'Carriolas'),
    # "Otros / Varios" es en buena parte cocina y mesa (Elektra manda ahí
    # tablas, vajilla, moldes, especieros): la subcategoría fina la decide
    # el mismo repartidor de Cocina y comedor, y lo que no reconoce no se
    # mueve.
    ('Otros', r'cuchillo|tabla (de|para) (cortar|picar)|tablas? de cortar|vajilla|\bplato|\bvaso|\btaza|\btermo|botella|'
              r'\bjarra|especi(a|ero)|escurridor|bandeja|charola|cubiert(os|eria)|\bmolde|reposteria|fondant|'
              r'\bcuenco|\bbowl\b|salero|pimentero|\bsarten|\bolla|cacerola|plancha de hierro|hierro fundido|'
              r'\bcomal|tequilero|\bcopa|\bjarro|\btarro|frasco|tapas? para conservas|conservas|contenedor(es)? (de|para) (alimentos|comida)|'
              r'recipiente|tupper|hermetic|lonchera|\brallador|\bpelador|\bcolador|\bbatidor\b|\bespatula|'
              r'\bcucharon|\bpinzas? de cocina|\bmandolina\b|cortador|espiralizador|molinillo|molino de (especias|pimienta|cafe|sal)|'
              r'\bmortero|\bbascula de cocina|\bcoctel|\bshaker\b|\bhielera\b|\bdesechable|bolsas de papel|servilleta|'
              r'\bmantel|posavasos|dispensador de aceite|aceitera|vinagrera|\bazucarera|\btetera|\bcafetera de prensa|\bprensa francesa|'
              r'\bcantimplora|termica|organizador (de |para )?(cocina|especias|fregadero|refrigerador|latas|cubiertos)|estante para especias|'
              r'rejillas? de coccion|\bwok\b|\bvaporera\b|\btortillero|\bsalsera|\bensaladera|\bfrutero|\bpanera|'
              r'limpieza de (cafetera|cocina)|tabletas de limpieza|descalcificador',
     r'parrilla|asador|\bcarbon\b|para mascotas|para perros|para gatos|\bbano\b|celular|telefono|camara|'
     r'\bsilla|\bsoporte|\bcoche\b|\bauto\b|tablet|ipad|\bbuffet\b|catering|calentador|\bportavasos\b',
     'Cocina y comedor', lambda tn: sub_cocina_fino(tn) or 'Utensilios de cocina', (None, 'Varios', 'Organización del hogar')),
    ('Otros', r'\basador\b|parrilla.{0,20}(carbon|gas|electrica)|\bbbq\b|\bahumado\b|churrasco|'
              r'tabla de charcuteria|\bcharcuteria\b',
     r'cobertura|funda|cubierta', 'Cocina y comedor', 'Utensilios de cocina', (None, 'Varios')),
    ('Juegos de mesa', r'piscina|acuatico|\bplaya\b|\bbalon\b|\balberca\b|water ?football|aros de buceo|resbaladilla|columpio|tobogan',
     r'rompecabezas|puzzle|juego de mesa|juego de cartas', 'Juguetes y bebés', 'Juegos de exterior'),
    ('Juegos de mesa', r'kit de (arte|manualidades|ciencia|cristales|cultivo|experimentos)|manualidades|estampilla|tatuajes|alcancia|engranajes|'
                       r'modelo (anatomico|de flor|del cuerpo|de cerebro|de esqueleto)|\besqueleto\b|\bosmo\b|set de juego de (limpieza|cocina|te|doctor)|'
                       r'\bplay-?doh\b|\bslime\b|plastilina|\bcrayola\b|pegatinas|\bstickers\b|cuaderno de actividades|libro de (pegatinas|actividades|colorear)|'
                       r'arena (sensorial|cinetica|magica)|\bmontessori\b|juguete sensorial|\bfelt fun\b|\bskillmatics\b|para colorear|\bpintura\b',
     r'rompecabezas|puzzle|juego de mesa|juego de cartas|tarjetas', 'Juguetes y bebés', 'Juguetes educativos'),
    ('Juegos de mesa', r'\bpeluche|\bmuneca|\bfigura\b|\bfiguras\b|\bfunko\b|\bplaymobil\b|\blego\b|bloques',
     r'juego de cartas|card game|juego de mesa|expansion|funkoverse|\btcg\b|rompecabezas|puzzle', 'Juguetes y bebés', lambda tn: 'Peluches' if 'peluche' in tn else ('Muñecas' if 'muneca' in tn else ('Bloques de construcción' if re.search(r'lego|bloques', tn) else 'Figuras de acción'))),
    ('Instrumentos musicales', r'\blasers?\b.{0,25}(rg|rgb|dj|alienpro|steelpro|verde|rojo|fiesta)|luces? (led )?(dj|de fiesta|robotica)|cabezas? (movil|robotica)',
     None, 'Iluminación', 'Escenario'),
    ('Herramientas', r'bomba (de aire |de pie |de piso )?(para|de) (bicicleta|bici)|foot pump.{0,30}bicicleta|inflador (para|de) (bicicleta|bici)|bomba de aire',
     r'compresor|acuario|pecera', 'Autos, bicicletas y motos', 'Bombas e infladores'),
    ('Herramientas', r'taburete|\bsilla\b|\bbanco\b (de|para) (taller|trabajo|garaje)|banco rodante', r'banco de trabajo con|prensa|escalera|escalon|peldano|fregadero|\bcarro\b|carrito', 'Muebles', 'Taburetes y bancos'),
    ('Herramientas', r'\blibrero\b|bookshelf|estante organizador.{0,30}(sala|cocina|bano|hogar)|estanteria de almacenamiento para (cocina|bano)', None, 'Muebles', 'Libreros'),
    # --- Quinta tanda: lo que no es un audífono ---
    # El teléfono que regala audífonos: la tienda lo deja en Audífonos y se
    # reconoce por el modelo, no por la palabra "celular".
    ('Audífonos', r'galaxy (s|a|z)\d{1,2}|\biphone 1[3-9]\b|redmi (note )?\d|\bpoco [xfm]\d|'
                  r'moto (g|e)\d{1,2}|\bhonor \d{2,3}|\bzte blade\b',
     r'\bfunda\b|\bmica\b|\bcable\b|\bcargador\b|\bprotector\b|compatible con|\bpara \b',
     'Celulares', lambda tn: 'iPhone' if 'iphone' in tn else 'Android', (None,)),
    ('Audífonos', r'\bvr\b|realidad virtual|valve index|meta quest', None, 'Videojuegos', 'Realidad virtual', (None,)),
    ('Audífonos', r'^(?:\S+ ){0,3}tablet\b|tablet con windows', None, 'Tabletas', 'Tabletas Windows y rugged', (None,)),
    ('Audífonos', r'bolsa para tablet|funda de transporte para ipad', None, 'Tabletas', 'Fundas y teclados', (None,)),
    ('Audífonos', r'smartwatch y audifonos|active pack', None, 'Relojes inteligentes', 'Smartwatches', (None,)),
    ('Audífonos', r'bateria para audifonos|\bpr44\b|tamano 675', None, 'Cargadores y adaptadores', 'De pilas', (None,)),
    ('Audífonos', r'amplificador de auriculares.{0,25}guitarra|enchufe de guitarra', None,
     'Instrumentos musicales', 'Amplificadores de guitarra y bajo', (None,)),
    ('Audífonos', r'tablero de clavijas|almacenamiento lateral de escritorio', None, 'Otros', 'Organización del hogar', (None,)),
    # --- Cuarta tanda: lo que Mercado Libre dejó en Herramientas ---
    ('Herramientas', r'divisores? de estante|organizador (de )?(utensilios|menaje)|bandeja cubiertos|'
                     r'organizador\b.{0,20}cocina', None, 'Cocina y comedor', 'Organización de cocina', (None,)),
    ('Herramientas', r'bomba.{0,25}bicicleta|ruedas de entrenamiento|porton trasero.{0,25}bicicleta|'
                     r'reparacion bicicletas|\bciclismo\b', None, 'Autos, bicicletas y motos',
     'Accesorios para bicicleta', (None,)),
    ('Herramientas', r'\balforjas?\b', None, 'Autos, bicicletas y motos', 'Accesorios para moto', (None,)),
    ('Herramientas', r'estanteria|\bestante\b.{0,20}niveles|\blibrero\b', r'herramienta|garaje|cochera|taller',
     'Muebles', 'Libreros', (None,)),
    ('Herramientas', r'soporte de motocicleta|para motocicleta|tanque de combustible|\bmoto\b',
     None, 'Autos, bicicletas y motos', 'Accesorios para moto', (None,)),
    ('Herramientas', r'bicicleta de equilibrio|\bstrider\b', None, 'Autos, bicicletas y motos',
     'Bicicletas sin pedales y balance', (None,)),
    ('Herramientas', r'tocadiscos|\bstylus\b|\bvinilos?\b', None, 'Instrumentos musicales', 'Tornamesas', (None,)),
    ('Herramientas', r'interdental|cuidado oral|\bdental\b', None, 'Belleza y cuidado personal', 'Cuidado personal', (None,)),
    ('Herramientas', r'\bcornhole\b|juego de lanzamiento', None, 'Juegos de mesa', 'De fiesta', (None,)),
    ('Herramientas', r'cama elastica|\btrampolin\b', None, 'Juguetes y bebés', 'Trampolines', (None,)),
    ('Herramientas', r'molino de harina|molino de (granos|maiz)', None, 'Cocina y comedor', 'Utensilios de cocina', (None,)),
    ('Herramientas', r'paneles? solares?', r'\btaladro\b|\bsierra\b', 'Otros',
     'Accesorios y limpieza de paneles solares', (None,)),
    ('Herramientas', r'^(?:\S+ ){0,3}ventilador\b', None, 'Climatización', 'Ventiladores de piso e industriales', (None,)),
    # --- Tercera tanda (20-sep, tarde) ---
    ('Audífonos', r'^(?:\S+ ){0,2}radios? (fm|am|portatil|de bolsillo|recargable)', None,
     'Bocinas', 'Radios y reproductores', (None,)),
    ('Audífonos', r'detector de ruido|probador de sonido|\bestetoscopio\b', None, 'Herramientas', 'Medición', (None,)),
    ('Audífonos', r'traje de bano|kit de natacion|\bgoggles?\b', None, 'Deportes y fitness', 'Natación', (None,)),
    ('Audífonos', r'ventilador.{0,25}(xbox|consola|ps5)', None, 'Videojuegos', 'Cargadores, bases y soportes', (None,)),
    ('Audífonos', r'tapon(es)? para (los )?oidos|proteccion auditiva|orejeras de seguridad|para trabajadores de la construccion',
     None, 'Herramientas', 'Seguridad industrial', (None,)),
    ('Baterías portátiles', r'herramienta de prensado|crimpado hidraulico|abrazadera hidraulica|prensado de bateria',
     None, 'Herramientas', 'Herramientas manuales', (None,)),
    ('Baterías portátiles', r'^(?:\S+ ){0,3}(mini )?ventilador', None, 'Climatización', 'Ventiladores portátiles y de mano', (None,)),
    ('Baterías portátiles', r'\blinterna\b', None, 'Iluminación', 'Lámparas de emergencia', (None,)),
    ('Baterías portátiles', r'cortadora de cesped|podadora|desbrozadora', None, 'Herramientas', 'Jardinería', (None,)),
    ('Baterías portátiles', r'\bgarmin\b|smart ?watch|reloj intelig', None, 'Relojes inteligentes', 'Smartwatches', (None,)),
    ('Baterías portátiles', r'monitor de bebe|baby monitor', None, 'Juguetes y bebés', 'Monitores de bebé', (None,)),
    ('Baterías portátiles', r'\bhubs?\b.{0,20}usb|adaptador(es)? de puerto', None, 'Cargadores y adaptadores', 'Cable', (None,)),
    ('Baterías portátiles', r'(pilas|baterias) recargables (de litio )?(aaa|aa)\b|paquete de \d+ (pilas|baterias)',
     None, 'Cargadores y adaptadores', 'De pilas', (None,)),
    ('Baterías portátiles', r'central electrica|estacion de energia|power station|generador portatil',
     None, 'Otros', 'Estaciones de energía', (None,)),
    # --- Segunda tanda, con lo que trajo la ronda de Mercado Libre ---
    ('Instrumentos musicales', r'maquina de (burbujas|nieve|humo)|liquido (de |para )?humo|snowcraft|'
                               r'\btruss\b|braguero|slip cover', None, 'Iluminación', 'Escenario', (None,)),
    ('Cámaras y fotografía', r'camara (ip|de seguridad|trampa|floodlight)|\btimbre\b|night owl|'
                             r'videovigilancia|\bnvr\b|\bdvr\b', None, 'Cámaras de seguridad',
     lambda tn: 'Timbres inteligentes' if 'timbre' in tn else ('Cámaras exteriores' if re.search(r'exterior|floodlight|trampa|intemperie', tn) else 'Cámaras interiores'), (None,)),
    ('Cámaras y fotografía', r'camara (trasera|de reversa|de vision trasera)|espejo retrovisor|para bicicleta',
     None, 'Autos, bicicletas y motos', 'Dashcams y cámaras', (None,)),
    ('Domótica y hogar inteligente', r'\brouter\b|\bmesh\b|repetidor wifi', None, 'Redes', 'Routers', (None,)),
    ('Domótica y hogar inteligente', r'controlador.{0,25}(movil|bluetooth)|\b8bitdo\b|\bgamepad\b',
     None, 'Videojuegos', 'Controles y gamepads', (None,)),
    ('Domótica y hogar inteligente', r'sistema de camaras|camaras? de seguridad|\bnvr\b|\bdvr\b',
     None, 'Cámaras de seguridad', 'Kits de vigilancia', (None,)),
    ('Mascotas', r'\bunas\b|esmalte de unas|ojos? de gato.{0,20}(gel|unas)|imanes.{0,20}unas',
     r'cortaunas|corta unas', 'Belleza y cuidado personal', 'Uñas', (None,)),
    ('Juegos de mesa', r'\bcarpa\b|tienda (de juego|infantil)|castillo para|piedras de paso|\bscooter\b|'
                       r'resbaladilla|columpio|casa de juegos', None, 'Juguetes y bebés', 'Juegos de exterior',
     (None, 'Otros juegos')),
    ('Juegos de mesa', r'set de actividades|kit (de )?(casa|diy|cientifico|de ciencia)|manualidades|'
                       r'pizarras? magnetica|\bsticker|aviones de papel|lace and trace|melissa & doug|'
                       r'\bdidax\b|edxeducation|para dibujar|\bplastilina\b|\bteching\b',
     None, 'Juguetes y bebés', 'Juguetes educativos', (None, 'Otros juegos')),
    ('Videojuegos', r'gaming headset|\bheadsets?\b|\barctis\b|blackshark|\bkraken\b|\bcloud (ii|alpha)\b',
     r'\bsoporte\b|\bstand\b|\bgancho\b|\bbase\b|almohadilla|\bfunda\b', 'Audífonos', 'Gamer',
     (None, 'Otros accesorios gamer')),
    ('Videojuegos', r'^(?:\S+ ){0,3}microfono\b', None, 'Instrumentos musicales', 'Micrófonos', (None, 'Otros accesorios gamer')),
    ('Videojuegos', r'palancas? de (freno|embrague)|para motocicletas', None, 'Autos, bicicletas y motos',
     'Accesorios para moto', (None, 'Otros accesorios gamer')),
    # --- Fichas que la tienda dejó en la categoría equivocada (20-sep) ---
    ('Audífonos', r'^(?:\S+ ){0,3}(tocadiscos|turntable)', None, 'Instrumentos musicales', 'Tornamesas', (None,)),
    ('Audífonos', r'reposacabezas|monitor.{0,25}(coche|auto)', None, 'Autos, bicicletas y motos', 'Estéreos para auto', (None,)),
    ('Audífonos', r'^(?:\S+ ){0,3}(dac|amplificador|interfaz de audio|mezclador|mezcladora)\b',
     None, 'Instrumentos musicales', 'Producción de audio', (None,)),
    ('Videojuegos', r'^(?:\S+ ){0,3}(audifonos?|auriculares|headsets?|diadema)\b|\bstereo headset\b',
     r'\bsoporte\b|\bbase\b|\bgancho\b|amplificador|\bfunda\b|\bcable\b|almohadilla',
     'Audífonos', 'Gamer', (None, 'Otros accesorios gamer')),
    ('Videojuegos', r'baston para auto|bloqueo antirrobo', None, 'Autos, bicicletas y motos', 'Accesorios y refacciones', (None, 'Otros accesorios gamer')),
    ('Otros', r'computadora portatil|\blaptop\b|\bnotebook\b', r'soporte|funda|mochila|base|cargador|adaptador',
     'Laptops', lambda tn: ola2.sub_laptop(tn, None) or 'Laptops de 15" y 16"', (None, 'Varios')),
    # La cámara entera va a "Cámaras de acción"; el palo, el soporte o la
    # funda son accesorio aunque nombren la marca.
    ('Otros', r'insta ?360|\bgopro\b|camara de accion', None, 'Cámaras y fotografía',
     lambda tn: 'Accesorios' if re.match(r'^(?:\S+ ){0,6}(palo|selfie|tripode|tripie|soporte|montaje|brazo|abrazadera|clamp|mount|adaptador|funda|estuche|bolsa|correa|bateria|cargador|filtro|kit)\b', tn) else 'Cámaras de acción',
     (None, 'Varios')),
    ('Otros', r'\bbicicleta\b|cuadro de bicicleta|\bciclismo\b', None, 'Autos, bicicletas y motos', 'Accesorios para bicicleta', (None, 'Varios')),
    ('Otros', r'armor all|limpiador.{0,20}(vidrios|parabrisas|auto|coche)', None, 'Autos, bicicletas y motos', 'Accesorios y refacciones', (None, 'Varios')),
    ('Otros', r'kit de supervivencia|tienda de campana|casa de campana|sleeping bag|bolsa de dormir|'
              r'mesa de playa|silla de playa|\bacampar\b',
     r'panel solar|estacion de energia|power ?bank|cargador', 'Deportes y fitness', 'Campismo', (None, 'Varios')),
    ('Baterías portátiles', r'bateria de (coche|auto|carro)|plomo-?acido|pinzas? de bateria|'
                            r'correas? para transporte de bateria|cargador de bateria.{0,30}(12 ?v|24 ?v|amperios)',
     None, 'Autos, bicicletas y motos', 'Baterías para auto', (None, 'Hasta 10,000 mAh', '10,000 a 20,000 mAh', 'Más de 20,000 mAh')),
    ('Baterías portátiles', r'\bajedrez\b', None, 'Juegos de mesa', 'Ajedrez', (None,)),
    ('Baterías portátiles', r'barra de luces|estroboscopic|luz de emergencia', None, 'Iluminación', 'Lámparas de emergencia', (None,)),
    ('Baterías portátiles', r'\bmatamoscas\b|raqueta.{0,20}insectos', None, 'Otros', 'Varios', (None,)),
    ('Teclados', r'\bmazas\b|\bmallets\b|percusion', None, 'Instrumentos musicales', 'Percusión', (None,)),
    ('Teclados', r'mezclador(a)? de audio|\bmixer\b', None, 'Instrumentos musicales', 'Producción de audio', (None,)),
    ('Teclados', r'terminal de venta|punto de venta', None, 'Equipo comercial', 'Punto de venta', (None,)),
    ('Teclados', r'keyboard for .{0,25}(laptop|hp|dell|lenovo)|laptops with|touchpad keyboard|\bfor 15-|\bfor 14-',
     None, 'Componentes y accesorios de PC', 'Accesorios', (None,)),
    ('Televisores', r'\baltavoc(es|z)\b|\bbocinas?\b', r'repuesto|de repuesto',
     'Bocinas', lambda tn: 'Barras de sonido' if 'barra' in tn else 'De estantería y Hi-Fi', (None,)),
    ('Televisores', r'repetidor.{0,20}(wifi|red)|extensor de (red|wifi)', None, 'Redes', 'Repetidores', (None,)),
    ('Televisores', r'unidad flash|memoria usb', None, 'Almacenamiento', 'Memorias USB', (None,)),
    ('Televisores', r'lente (de camara|sin espejo)', None, 'Cámaras y fotografía', 'Lentes', (None,)),
    ('Televisores', r'jaulas? para perro|casa for mascotas', None, 'Mascotas', 'Jaulas para perro', (None,)),
    ('Muebles', r'pedicure chair|silla de pedicura|nail salon|spa pedicure', None, 'Belleza y cuidado personal', 'Mobiliario para salón', (None, 'Otros')),
    ('Muebles', r'skateboard seat|patineta electrica|electric skateboard', None, 'Movilidad eléctrica', 'Accesorios', (None, 'Otros')),
    ('Muebles', r'^(?:\S+ ){0,2}(sandalias?|chanclas?|zapat(os|illas)|tenis)\b', r'zapatera|mueble|organizador|estante|taburete|banco|\bmesa\b|sensor|cambiador', 'Calzado', lambda tn: 'Sandalias' if re.search(r'sandalia|chancla', tn) else ('Tenis' if 'tenis' in tn else 'Zapatos de vestir')),

    # ---- Instrumentos musicales (20-sep). Lo que queda sin subcategoría en
    # el rubro es, en su mayoría, equipo de escenario, juguete o adorno que
    # entró ahí porque la tienda lo vende junto con los instrumentos. Casi
    # todas se limitan a las fichas SIN subcategoría (última tupla) para no
    # tocar lo que ya está colocado.
    ('Instrumentos musicales',
     r'maquina de (humo|niebla|burbujas)|camara de humo|liquido.{0,25}(humo|burbujas)|'
     r'galon liquido|generador de burbujas|\bnebula\d|\bcosmo-\d|\bghost-\d|'
     r'canones? par\b|\bwashers?\b|\bstrobe\b|\bderby\b|jelly movil|mini spot|mini planet|'
     r'\balienpro\b|\bsteelpro\b|blizzard lighting|esferas? de cristal|\bdiscoball\b|'
     r'soporte.{0,25}hamburguesa|hamburguesa \d|pinza.{0,30}iluminacion|'
     r'soporte universal para luces|\blaser\b',
     r'\bpedal\b|\bguitarra\b|microfono', 'Iluminación', 'Escenario', {None}),
    ('Instrumentos musicales',
     r'\botamatone\b|instrumentos? musicales? (para (ninos|bebes)|infantil)|'
     r'instrumentos musicales de madera para ninos|juego de (musica|instrumentos musicales)|'
     r'kit de instrumentos musicales|\bmake a melody\b|\bpeppa pig\b|'
     r'campanas de computadora|juguete de musica|piezas de instrumentos musicales para ni',
     None, 'Juguetes y bebés', 'Juguetes musicales', {None}),
    ('Instrumentos musicales', r'juego (de )?loteria|juego didactico', None,
     'Juguetes y bebés', 'Juguetes educativos', {None}),
    ('Instrumentos musicales', r'casa de munecas|\bbook nook\b|miniaturas?\b.{0,30}munecas', None,
     'Juguetes y bebés', 'Maquetas', {None}),
    ('Instrumentos musicales', r'bloques de construccion', None,
     'Juguetes y bebés', 'Bloques de construcción', {None}),
    ('Instrumentos musicales', r'\bdijes?\b|\bcharms?\b|colgantes para (collares|pulseras)', None,
     'Joyería y bisutería', 'Dijes y charms', {None}),
    ('Instrumentos musicales',
     r'adornos? de instrumento|decoraciones 2d|acrilico (rosa|2d)|adornos de navidad|'
     r'plantillas de notas|decoracion de pared|guirnalda de fiesta|pancarta de feliz cumpleanos',
     None, 'Otros', 'Varios', {None}),
    ('Instrumentos musicales', r'\bbafle\b|\bstagepro\b|elite system|medio grave colgante', None,
     'Bocinas', 'Accesorios para bocinas', {None}),
    ('Instrumentos musicales',
     r'convertidor de salida de linea|control de graves|\bskar audio\b|\baudiocontrol\b|\blc2i\b',
     None, 'Autos, bicicletas y motos', 'Accesorios de audio para auto', {None}),
    ('Instrumentos musicales', r'unidad flash usb|memoria usb|\bpendrive\b', None,
     'Almacenamiento', 'Memorias USB', {None}),
    ('Instrumentos musicales', r'\bpolipasto\b|\bgarrucha\b', None,
     'Herramientas', 'Herramientas manuales', {None}),
    ('Instrumentos musicales', r'\bcargador\b.{0,40}m ?ah|\d{4,6} ?m ?ah', None,
     'Baterías portátiles', tramo_mah, {None}),
    ('Instrumentos musicales', r'libro para colorear', None, 'Libros', 'Infantil', {None}),
    ('Instrumentos musicales', r'libro publicado', None, 'Libros', 'Música y cine', {None}),
    ('Instrumentos musicales', r'\bfox 40\b|silbato.{0,30}(arbitro|deportiv)', None,
     'Deportes y fitness', 'Otros', None),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--salida', required=True)
    ap.add_argument('--muestras', type=int, default=3)
    args = ap.parse_args()
    data = load_catalog()
    reg = {c['id']: {s['id'] for s in (c.get('subcategories') or [])} for c in data['categories']}
    grupos = collections.defaultdict(list)
    muestras = collections.defaultdict(list)
    for p in data['products']:
        tn = T(p.get('name'))
        for regla in REGLAS:
            cat, si, no, cat2, sub2 = regla[:5]
            subs = regla[5] if len(regla) > 5 else None   # subcategorías de origen a las que se limita
            if p.get('category') != cat or not re.search(si, tn) or (no and re.search(no, tn)):
                continue
            if subs is not None and p.get('subcategory') not in subs:
                continue
            s2 = sub2(tn) if callable(sub2) else sub2
            if not s2 or s2 not in reg.get(cat2, ()):
                break
            k = f"{cat} | {p.get('subcategory')} | {cat2} | {s2}"
            grupos[k].append(p['id'])
            if len(muestras[k]) < args.muestras:
                muestras[k].append((p.get('name') or '')[:100])
            break
    for k, ids in sorted(grupos.items(), key=lambda kv: -len(kv[1])):
        print(f"{len(ids):5d}  {k}")
        for m in muestras[k]:
            print(f"           {m}")
    print(f"\nTotal: {sum(len(v) for v in grupos.values())} fichas en {len(grupos)} grupos -> {args.salida}")
    json.dump(grupos, open(args.salida, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)


if __name__ == '__main__':
    main()
