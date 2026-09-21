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
from subcategorias_finas import sub_cocina_fino, sub_suplemento_fino  # noqa: E402
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
    # El "no" pedía que el título no dijera "auricular" en ninguna parte, y
    # el micrófono de podcast anuncia su salida para auriculares: ahora solo
    # se salva el que ABRE nombrando el audífono.
    ('Audífonos', r'^(?:\S+ )?microfono',
     r'^(?:\S+ ){0,3}(auricular|audifono|headset|diadema)|diadema con microfono|audifonos? con|'
     r'microfono desmontable|reemplazo de microfono|\bcon audifonos\b|\by audifonos\b|'
     r'de repuesto para (auriculares|audifonos)|repuesto para auriculares',
     'Instrumentos musicales', 'Micrófonos'),
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
     r'(\d|con|dos|tres) (contactos?|interruptores?|apagadores?|modulos?)\b|cubierta para interruptor|tapa para placa|placa cubre|'
     # La placa y el apagador de catálogo eléctrico se nombran por su línea
     # y su marca, no por la palabra "placa ciega": Leviton, Volteck, Aksi,
     # iGoto, Lutron. Son material eléctrico, no domótica.
     r'placas? (duplex|dup\b|inox|contacto|interruptor|redonda|termoplastica|quickport|nylon|acero|lucek|con toma|de baquelita|plastic|economica)|'
     r'\bplacas?\b.{0,30}(leviton|volteck|voltech|aksi|igoto|lutron|quickport|termoplastic|baquelita|standard)|'
     r'(leviton|aksi|volteck|voltech|igoto) placas?\b|'
     r'interruptor(es)? (electrico|de escalera|escalera|combinacion|palanca|sencillo|vertical|unipolar)|'
     r'tapa (decora|lisa|leviton)|tapa \w+ intemperie|'
     r'\bclavija\b|adaptador aterrizado|contrachapa de placa',
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

    # ---- Juguetes y bebés (20-sep)
    ('Juguetes y bebés', r'remolque de bicicleta|portabebes? (individual|doble)', None,
     'Autos, bicicletas y motos', 'Asientos infantiles y remolques', {None}),

    # ---- Baterías portátiles (20-sep). El rubro junta el power bank con
    # todo lo que dice "portátil" y "batería" en el título: la batería de
    # repuesto de una laptop, el cargador de pilas de una cámara, la tapa
    # del compartimento. Cada regla se limita a las fichas sin subcategoría.
    ('Baterías portátiles', r'\bauriculares?\b|\baudifonos?\b|quietcomfort|\bwh-1000|sonido oseo', None,
     'Audífonos', 'Diadema con cancelación de ruido', {None}),
    ('Baterías portátiles',
     r'camara (espia|oculta|de accion|de ninera)|\bosmo pocket\b|\bgopro\b|ultra hd \d+mp|'
     r'cubierta de la (puerta de la )?bateria de la camara|puerta de bateria|'
     r'\bnp-?(6l|fv5|fw50|f970)\b|speedlite|bateria.{0,20}(flash|camara)',
     None, 'Cámaras y fotografía', 'Accesorios', {None}),
    ('Baterías portátiles', r'\brouter\b|punto de acceso wifi|hotspot|\b4g lte\b|modem wifi', None,
     'Redes', 'Routers', {None}),
    ('Baterías portátiles', r'panel(es)? solar|cargador solar|banco de energia solar|celulas solares', None,
     'Otros', 'Cargadores solares portátiles', {None}),
    ('Baterías portátiles', r'\bproyector\b', None, 'Proyectores y accesorios', 'Proyectores', {None}),
    ('Baterías portátiles', r'\bmouse\b', None, 'Mouse', 'Mouse inalámbrico', {None}),
    ('Baterías portátiles', r'extensor de (visualizacion|monitor)|triple extensor', None,
     'Monitores', 'Monitores portátiles', {None}),
    ('Baterías portátiles',
     r'^(?:\S+ ){0,6}cables? (usb|de datos|de carga|puente)|\bcable\b.{0,30}(usb c a usb|240w|xh2\.54|xt60)',
     None, 'Cargadores y adaptadores', 'Cable', {None}),
    ('Baterías portátiles',
     r'cargador inalambrico|\bqi2|\bmagsafe\b|estacion de carga|\bmaggo\b|base de braun|'
     r'cargador de (cepillo|bateria) de dientes',
     None, 'Cargadores y adaptadores', 'Base de carga', {None}),
    ('Baterías portátiles',
     r'bateria portatil.{0,40}(hp|dell|msi|macbook|toshiba|elitebook|envy|precision|satellite)|'
     r'compatible con (hp|dell|msi|macbook|panasonic)|\bab06xl\b|\bbty-m6h\b|\bvh08\b|\ba1383\b|'
     r'cargador portatil de 65 w para toshiba',
     None, 'Refacciones', 'Refacciones para otros electrodomésticos', {None}),

    # ---- Herramientas, segunda tanda (20-sep). "Herramienta" es la palabra
    # que más se usa de relleno en los títulos de Mercado Libre ("herramienta
    # de entrenamiento", "herramienta de belleza", "herramientas profesionales
    # de diseño de sonido"), y el rubro se llenó de cosas que no son una
    # herramienta. Todas se limitan a las fichas sin subcategoría.
    ('Herramientas',
     r'\bsintetizador\b|teoria musical|\bmaracas\b|limpiar cuerdas|herramienta de acordes|'
     r'ajuste de bastidor|gong mallet|\bcarillon|pedal de efectos|guitar strings?|'
     r'chakra sound|barras? de resonantes',
     None, 'Instrumentos musicales', 'Accesorios', {None}),
    ('Herramientas',
     r'limpieza (de )?camara|sensor (ccd|cmos)|lupa sensor|cabeza de bola',
     None, 'Cámaras y fotografía', 'Accesorios', {None}),
    ('Herramientas',
     r'soporte de montaje de disco duro|tarjetas? de memoria micro sd|soporte de expansion de \d discos',
     None, 'Almacenamiento', 'Tarjetas de memoria', {None}),
    ('Herramientas', r'tubo acustico', None, 'Audífonos', 'Earbuds con cable', {None}),
    ('Herramientas',
     r'radio de coche|car radio|reproductor multimedia compatible for|restauracion de faros|'
     r'esponja para pulido|arrancador de salto|bocinas? de trompeta',
     None, 'Autos, bicicletas y motos', 'Accesorios y refacciones', {None}),
    ('Herramientas',
     r'\bgolf\b|\bdardos\b|pelotas de tenis|supervivencia|\bbrujula\b|gimnasia ritmica|'
     r'bloques de yoga|estirador de piernas|fuerza para antebrazo|equipo de ejercicio|'
     r'bascula de pesca|organizador de equipos de gimnasio',
     None, 'Deportes y fitness', 'Otros', {None}),
    ('Herramientas',
     r'cuticula|removedor de piel|dreadlocks|diagnostico de la piel|\bfascia\b|'
     r'cortapelos|cera para (el vello|eliminar el vello)|\bloofah\b|\blufa\b|'
     r'esterilizacion para herramientas|tarro de desinfeccion|botellas de limpieza de pestanas',
     None, 'Belleza y cuidado personal', 'Cuidado personal', {None}),
    ('Herramientas', r'irrigador|ortodoncia|\bbrackets\b', None,
     'Belleza y cuidado personal', 'Cuidado personal', {None}),
    ('Herramientas',
     r'composicion corporal|bascula.{0,30}(peso corporal|medir la altura|440)|analizador ultrasonico',
     None, 'Salud', 'Básculas', {None}),
    ('Herramientas',
     r'aire acondicionado|refrigerante|deshumidificad|deshdificador|fugas de (ca|aire)',
     None, 'Climatización', 'Accesorios y refacciones de aire acondicionado', {None}),
    ('Herramientas', r'estanteria|carro con ruedas cocina|carrito de bebidas', None,
     'Muebles', 'Libreros', {None}),
    ('Herramientas', r'castillo hinchable|casa de rebote|ruleta de premios|rueda de la fortuna', None,
     'Juguetes y bebés', 'Juegos de exterior', {None}),
    ('Herramientas', r'ruedas dedicadas para carriola de mascotas|caseta de exterior', None,
     'Mascotas', 'Casas para mascotas', {None}),
    ('Herramientas', r'reposacabezas thule|respaldo de carriola', None,
     'Juguetes y bebés', 'Carriolas', {None}),
    ('Herramientas', r'salud mental|practica clinica|herramientas psicologicas', None,
     'Libros', 'Psicología', {None}),
    ('Herramientas', r'bolso frontal para scooter', None,
     'Movilidad eléctrica', 'Accesorios', {None}),
    ('Herramientas', r'soporte magnetico para starlink', None, 'Redes', 'Routers', {None}),

    # ---- Celulares (20-sep). Sin restringir a las fichas sin subcategoría,
    # a diferencia del resto: acá el problema es justamente que TIENEN una
    # (el despachador daba 'Android' por hecho), así que limitarlas a las
    # vacías no movería ninguna.
    # ---- Celulares (20-sep). El rubro daba 'Android' por hecho a todo lo
    # que entraba, así que el micrófono, el masajeador, el protector de
    # colchón y el juguete para perro aparecían como teléfonos en la lista
    # (y en la de "más baratos", que es la que abre la categoría, salían
    # todos primeros). El despachador ya los deja sin subcategoría; acá van
    # a su rubro.
    ('Celulares', r'^(?:\S+ ){0,3}(microfono|dji mic)|lavalier|microfono de solapa',
     r'\bcelular\b|\btelefono\b|smartphone|\bgalaxy\b|\biphone\b|\bmoto \w|\bredmi\b|feature phone|rugged phone|\bdual sim\b|\bdesbloqueado\b|\bram\b', 'Instrumentos musicales', 'Micrófonos'),
    ('Celulares',
     r'^(?:\S+ ){0,4}(auriculares?|earbuds?|earphones?|headphones?|headset|audifonos?|tws|'
     r'enco|true wireless)\b',
     r'\bcelular\b|\btelefono\b|smartphone|\bgalaxy\b|\biphone\b|\bmoto \w|\bredmi\b|feature phone|rugged phone|\bdual sim\b|\bdesbloqueado\b|\bram\b', 'Audífonos', 'Earbuds inalámbricos'),
    ('Celulares', r'masajeador|liberador(es)? (de musculos|fasciales)|fascia|rodillo masajeador', None,
     'Salud', 'Salud'),
    ('Celulares', r'baumanometro|presion arterial', None, 'Salud', 'Equipo de monitoreo médico'),
    ('Celulares', r'cepillo de dientes|pasta de dientes', None, 'Salud', 'Cuidado dental'),
    ('Celulares',
     r'incontinencia|protector(a)? de colchon|colchon impermeable|almohadillas? de cama|'
     r'sabanas impermeables|almohadillas? (protectora|absorbente)',
     None, 'Salud', 'Salud'),
    ('Celulares', r'cobija electrica|manta termica|alfombrillas? de calefaccion', None,
     'Otros', 'Varios'),
    ('Celulares', r'silla reclinable', None, 'Muebles', 'Sillones y reclinables'),
    ('Celulares', r'reposabrazos', None, 'Muebles', 'Accesorios y organizadores de escritorio'),
    ('Celulares', r'^(?:\S+ ){0,3}llaveros?\b', None, 'Otros', 'Varios'),
    ('Celulares', r'masticar|chirrido de peluche', None, 'Mascotas', 'Juguetes para perro'),
    ('Celulares', r'caja conmemorativa de mascotas', None, 'Mascotas', 'Higiene y limpieza'),
    ('Celulares', r'unidades? (de memoria )?flash|memory stick', None,
     'Almacenamiento', 'Memorias USB'),
    ('Celulares', r'action cam|super clamp', None, 'Cámaras y fotografía', 'Accesorios'),
    ('Celulares', r'pastillas de guitarra', None, 'Instrumentos musicales', 'Accesorios de guitarra'),
    ('Celulares', r'tabletas? profesionales? de dibujo', None, 'Tabletas', 'Tabletas de dibujo'),
    ('Celulares', r'punto de acceso wifi|\benrutador\b', r'rugged phone|\btelefono resistente\b',
     'Redes', 'Routers'),
    ('Celulares', r'controlador (inteligente )?led', None, 'Iluminación', 'Tiras LED'),
    ('Celulares', r'almohadilla calefactora de pantalla|maquina laser|separadora', None,
     'Herramientas', 'Accesorios para herramientas eléctricas'),
    ('Celulares', r'^(?:\S+ ){0,3}(taza|vaso)\b', None, 'Cocina y comedor', 'Tazas'),

    # ---- Auditoría de despachadores (20-sep). "Tableta" es la pantalla y la
    # forma farmacéutica: 113 cajas de suplementos estaban listadas como
    # tabletas Android. No se limita a las fichas sin subcategoría porque el
    # problema es justamente que tienen una.
    ('Tabletas',
     r'\b\d+(\.\d+)? ?mg\b|\bcomprimidos?\b|\bgrageas?\b|caja con \d+ tabletas|'
     r'suplemento alimenticio',
     r'\bram\b|\brom\b|\bgb\b|\bpulgadas\b|\bandroid\b|\bwifi\b',
     'Suplementos', lambda tn: sub_suplemento_fino(tn) or 'Herbolaria y superalimentos'),
    # El repuesto del refrigerador se busca en Refacciones, no entre los
    # refrigeradores: el despachador ya lo deja sin subcategoría.
    ('Refrigeradores',
     r'\btapon(es)?\b|\btermometro\b|\btermistor\b|\bsensor\b|\bfoco\b|\bsonda\b|'
     r'medidor de temperatura|indicador de temperatura|\bempaque\b|\bbisagra\b|'
     r'barra divisoria|filtro de agua',
     # El refrigerador entero también anuncia su "Smart Sensor": si el título
     # abre nombrando el aparato, no es refacción.
     r'^(?:\S+ ){0,4}(refrigerador|refrigeradora|frigobar|congelador|minibar|nevera)\b|\bpies cubicos\b',
     'Refacciones', 'Refacciones para refrigerador'),

    # ---- Piezas y accesorios que estaban como producto terminado (20-sep).
    # Todas piden que la palabra ABRA el título: la ficha técnica de un
    # monitor dice "antirreflejo" y la de una bocina "bobina de voz", así que
    # sin el ancla se llevaban el producto terminado.
    ('Bocinas',
     r'^(?:\S+ ){0,4}(bobina de voz|voice coil|cono de (papel|altavoz)|papel de cono|'
     r'tubo de graves|caja de (conexiones|terminales)|binding post|esquinero|'
     r'diafragma)\b|rejilla (para|de) (bocina|altavoz|woofer|subwoofer)',
     r'\bbluetooth\b|\bkaraoke\b|\bpasivas?\b|\bhi-?fi\b', 'Bocinas', 'Accesorios para bocinas'),
    ('Monitores',
     r'^(?:\S+ ){0,4}(funda|cubierta|protector(es)?|filtro|pelicula|mica|soporte|brazo|'
     r'adaptador|cable|convertidor|limpiador|antipolvo)\b|monitor de nailon para polvo',
     r'\b(fhd|qhd|uhd|ips|hz|ms|1920|2560|3840)\b',
     'Componentes y accesorios de PC', 'Accesorios de monitor'),
    ('Laptops',
     r'^(?:\S+ ){0,4}(concentrador|hub|adaptador(a)?|convertidor|soporte|base|funda|'
     r'maletin|mochila|cargador|cable|conector|protector|pelicula|mica|limpiador|'
     r'enfriador)\b|\bm\.?2 ngff\b|\bmsata\b|so-?dimm a desktop|dimm memory.{0,20}connector',
     r'\b(core i[3579]|ryzen|celeron|intel|amd)\b.{0,40}\b(ram|ssd|gb)\b',
     'Componentes y accesorios de PC', 'Accesorios'),

    # ---- Audífonos (20-sep). "Audífono" es el auricular Y el aparato para
    # oír: los cargadores Starkey, las pilas HearClear y los transductores de
    # audiómetro son productos médicos. Y el rubro junta además el teléfono
    # que viene "+ audífonos de regalo".
    ('Audífonos',
     r'\bstarkey\b|hearclear|baterias para audifonos|\baudiometro\b|\btdh39\b|\bdd45\b|'
     r'conversation enhancing|\bbte\b|para personas mayores.{0,30}audifono',
     None, 'Salud', 'Salud', {None}),
    ('Audífonos', r'^(?:\S+ ){0,3}(honor|oppo|samsung galaxy|xiaomi redmi|motorola)\b.{0,40}\bgb\b',
     None, 'Celulares', 'Android', {None}),
    ('Audífonos', r'posee \d auriculares.{0,20}agenda', None, 'Celulares', 'Teléfonos fijos', {None}),
    ('Audífonos', r'^(?:\S+ ){0,3}(bolsa|funda) para tablet', None, 'Tabletas', 'Accesorios para tableta', {None}),
    ('Audífonos', r'cane creek|\bzs44\b|\bzs56\b', None,
     'Autos, bicicletas y motos', 'Refacciones y transmisión de bicicleta', {None}),
    ('Audífonos', r'auriculares falso|para disfraz', None, 'Otros', 'Varios', {None}),
    ('Audífonos', r'^(?:\S+ ){0,3}(teclado|amplificador|pedal|bateria de silicona|guitarra)\b|'
     r'\bomnichord\b|\bblackstar\b|\bamplug\b|liberlive|steinberg ur\d|fonografo',
     None, 'Instrumentos musicales', 'Accesorios', {None}),
    ('Audífonos', r'^(?:\S+ ){0,3}microfono\b|\bfifine\b|\bjyx\b|preamplificador de microfono',
     # El audífono con micrófono sigue siendo un audífono, y el micrófono de
     # repuesto de un headset es un repuesto de audífono.
     r'\baudifono|\bauricular|\bheadset\b|\bdiadema\b|\breemplazo\b|\bg7\d{2}\b',
     'Instrumentos musicales', 'Micrófonos', {None}),
    ('Audífonos', r'wall mount de pared ps5|ventilador de refrigeracion rgb.{0,20}xbox|para consola xbox',
     None, 'Videojuegos', 'Otros accesorios gamer', {None}),
    ('Audífonos', r'^(?:\S+ ){0,4}(mini )?radio (digital )?fm|receptor de radio portatil',
     None, 'Bocinas', 'Radios y reproductores', {None}),
    ('Audífonos', r'kit de soldadura', None, 'Herramientas', 'Soldadura', {None}),
    ('Audífonos', r'kit de audio portero', None, 'Domótica y hogar inteligente', 'Videoporteros', {None}),
    ('Audífonos', r'compatible con dji', None, 'Drones', 'Accesorios', {None}),

    # ---- Domótica y Cámaras (20-sep). Los dos rubros juntan lo que la
    # tienda etiquetó "smart" o "cámara" sin más: relés industriales,
    # controles de aire, mandos de videojuego, cámaras de coche.
    ('Domótica y hogar inteligente',
     r'\bdh48s\b|rele programable|\bioLogik\b|\bmoxa\b|\branco\b|\bxr06cx\b|'
     r'controlador (electronico )?de temperatura|controlador.{0,15}cnc|\bgrbl\b',
     None, 'Herramientas', 'Material eléctrico', {None}),
    ('Domótica y hogar inteligente', r'^control(ador)? (para )?aire ac\b|control para aire',
     None, 'Climatización', 'Accesorios y refacciones de aire acondicionado', {None}),
    ('Domótica y hogar inteligente',
     r'control(ador)? (inalambrico )?de (videojuegos|juego)|\bgamesir\b|\bretro-?bit\b|'
     r'caja de botones sim-?panel|\bserafim\b',
     None, 'Videojuegos', 'Otros accesorios gamer', {None}),
    ('Domótica y hogar inteligente',
     r'camara (wifi|de monitoreo|oculta|de seguridad|inteligente)|camara.{0,20}(interior|exterior)',
     None, 'Cámaras de seguridad', 'Cámaras interiores', {None}),
    ('Domótica y hogar inteligente', r'sistema de intrusion|\bhoneywell v\d{2}', None,
     'Cámaras de seguridad', 'Alarmas', {None}),
    ('Domótica y hogar inteligente', r'convertidor hdmi|muro de video|\bhdmi\b.{0,25}(1080p|4k)', None,
     'Televisores', 'Accesorios y soportes', {None}),
    ('Domótica y hogar inteligente', r'fire tv\b|\bchromecast\b|\bstreaming stick\b|efecto espejo a tv|\bmiracast\b', None,
     'Televisores', 'Accesorios y soportes', {None}),
    # El interruptor de vacío de 10 kV se anuncia "inteligente" y por eso se
    # escapaba del filtro de material eléctrico: va por su cuenta.
    ('Domótica y hogar inteligente', r'interruptor de (demarcacion|vacio)|\b\d+ ?kv\b|seccionador', None,
     'Herramientas', 'Material eléctrico', {None}),
    ('Domótica y hogar inteligente', r'cinta led|tira led', None, 'Iluminación', 'Tiras LED', {None}),
    ('Domótica y hogar inteligente', r'difusor de aceites|humidificador aroma', None,
     'Belleza y cuidado personal', 'Cuidado personal', {None}),
    ('Domótica y hogar inteligente', r'manija de puerta|\bkwikset\b(?!.{0,20}intelig)', None,
     'Herramientas', 'Cerraduras y candados', {None}),

    # Autos: el coche de juguete y el libro de motos (21-sep). El de
    # juguete se reconoce por la escala, la marca y el "para niños".
    ('Autos, bicicletas y motos',
     r'\bmaisto\b|\bcaterpillar\b|cat ?toys|paw patrol|\btamiya\b|picassotiles|'
     r'\b1:\d{1,3}\b|fundido a troquel|die ?cast|pista de (carros|autos)|'
     r'vehiculo de ingenieria|camion (portador|transportador) de dinosaurios|'
     r'calendario de adviento|mini machines|mini vehiculos|vehiculo de paseo|'
     r'bloques de construccion|para dioramas',
     None, 'Juguetes y bebés', 'Vehículos de juguete', {None}),
    ('Autos, bicicletas y motos',
     r'^motocicletas?$|^motocicletas y ciclomotores$|motocicletas em figuras|'
     r'manutencao de motocicletas|zen e arte|hell\'s angels|conduccion deportiva|'
     r'reparacion de motocicletas|cube books|motocicletas motor y caja',
     None, 'Libros', 'Técnicos y profesionales', {None}),
    ('Autos, bicicletas y motos', r'tarjeta de memoria\b', None,
     'Almacenamiento', 'Tarjetas de memoria', {None}),
    ('Autos, bicicletas y motos', r'camara fpv|\bruncam\b|\bsiyi\b|cardan.{0,20}zoom', None,
     'Drones', 'Cámaras y gimbals', {None}),
    ('Autos, bicicletas y motos', r'raquetas? de tenis', None, 'Deportes y fitness', 'Raquetas', {None}),
    ('Autos, bicicletas y motos', r'cobija electrica|manta electrica', None,
     'Blancos y ropa de cama', 'Cobijas eléctricas', {None}),

    # Blancos y ropa de cama: el colchón, la cabecera y el sofá infantil
    # tienen categoría propia en Muebles (21-sep).
    ('Blancos y ropa de cama', r'colchon.{0,25}(cuna|cochecito|bebe)|colchon de cuna', None,
     'Muebles', 'Colchones infantiles y de cuna', {None}),
    ('Blancos y ropa de cama',
     r'^(?:\S+ ){0,3}colchon\b|colchon (de latex|organico|ecologico|plegable|hibrido)',
     r'funda|protector|topper|sobrecolchon', 'Muebles', 'Colchones', {None}),
    ('Blancos y ropa de cama', r'sofa plegable|sillon infantil', None,
     'Muebles', 'Sofás infantiles', {None}),
    ('Blancos y ropa de cama', r'^(?:\S+ ){0,2}respaldo\b|\bcabecera\b', None,
     'Muebles', 'Cabeceras', {None}),
    ('Blancos y ropa de cama', r'night ?guard|protector (bucal|dental)|rechinar los dientes', None,
     'Salud', 'Cuidado dental', {None}),
    ('Blancos y ropa de cama', r'pistola masajeadora|\btheragun\b|masajeador', None,
     'Belleza y cuidado personal', 'Masajeadores', {None}),

    # Decoración solo tiene Espejos y Asadores: el interruptor industrial y
    # la lámpara que cayeron ahí pertenecen a otra categoría (21-sep).
    ('Decoración de hogar y jardín',
     r'^(?:\S+ ){0,3}(interruptor|apagador|boton de encendido)|\bkcd1\b|\bla38\b',
     r'\bespejo|\btocador\b', 'Herramientas', 'Material eléctrico', {None}),
    ('Decoración de hogar y jardín', r'aplique de pared|barra de luz led|tira de pared', r'\bespejo',
     'Iluminación', 'Lámparas de pared', {None}),
    ('Decoración de hogar y jardín', r'lampara (de )?escritorio', r'\bespejo',
     'Iluminación', 'Lámparas de escritorio', {None}),
    # Componentes y accesorios de PC: el disco y la PC armada tienen
    # categoría propia y no una subcategoría de componente.
    ('Componentes y accesorios de PC', r'\bnas de escritorio\b|\bnas\b.{0,25}bahias', None,
     'Almacenamiento', 'NAS', {None}),
    ('Componentes y accesorios de PC', r'\bpc gamer\b|computadora (de escritorio )?armada', None,
     'Computadoras de escritorio', 'Torre', {None}),
    ('Componentes y accesorios de PC', r'\bssd\b|\bnvme\b|disco duro|unidad de estado solido',
     r'\bpc gamer\b|\bnas\b', 'Almacenamiento',
     # Los ids de Almacenamiento no son los nombres: 'SSD' e 'Interno'.
     lambda tn: 'SSD' if re.search(r'\bssd\b|\bnvme\b|estado solido', tn) else 'Interno',
     {None}),

    # Lo que la tienda colgó de Cámaras sin serlo (21-sep): el comedero con
    # cámara, la cámara de aire del scooter y el escáner de piel de salón.
    ('Cámaras y fotografía', r'\bcomedero\b|alimentador automatico|dispensador de comida', None,
     'Mascotas', 'Comederos automáticos', {None}),
    ('Cámaras y fotografía',
     r'camara reforzada|camara.{0,35}(scooter|patin electrico)|valvula de neumatico|'
     r'neumatico sin camara',
     None, 'Refacciones', 'Para patinetas eléctricas', {None}),
    ('Cámaras y fotografía', r'analizador facial|iriscopio|cuero cabelludo|escaner de piel', None,
     'Belleza y cuidado personal', 'Dispositivos de cuidado facial', {None}),
    ('Cámaras y fotografía',
     r'camaras? interiores?|camara wifi solar|kit inalambrico con zoom|\bring 2\b',
     r'camara de accion|gopro', 'Cámaras de seguridad', 'Cámaras interiores', {None}),
    ('Cámaras y fotografía', r'\bblader\b.{0,30}balon|camara.{0,15}latex.{0,20}balon', None,
     'Deportes y fitness', 'Balones', {None}),
    ('Cámaras y fotografía',
     r'camara de (salpicadero|tablero|respaldo|reversa)|camara salpicadero|\bdash ?cam\b|camara.{0,20}retrovisor|'
     r'\bthinkware\b|\bfitcamx\b|\bauto-?vox\b|\bcrimestopper\b|\balpine hce\b|\bmufu\b|'
     r'cobertura para mando de llave',
     None, 'Autos, bicicletas y motos', 'Dashcams y cámaras', {None}),
    ('Cámaras y fotografía',
     r'\bring\b.{0,25}(cam|spotlight|exterior|interior)|\bblink\b (outdoor|indoor|mini)|'
     r'camara (de )?(rastreo|caza|vigilancia|espia|falsa)|\btactacam\b|\bmoultrie\b|'
     r'yellowstone\.ai|camara domo|\bcamara ip\b|camara.{0,20}(para exteriores|para interior)|'
     r'detector de camara oculta|foco led inteligente camara',
     None, 'Cámaras de seguridad', 'Cámaras exteriores', {None}),
    ('Cámaras y fotografía',
     r'\bmicroscopio\b|camara intraoral|camara de inspeccion|\bendoscop|boroscopio',
     None, 'Herramientas', 'Medición', {None}),

    # ---- Mascotas y Teclados (20-sep).
    ('Mascotas', r'^(?:\S+ ){0,3}(yo,? el gato|el gato que)|seguridad alimentaria|salud publica veterinaria',
     None, 'Libros', 'Hogar, manualidades y mascotas', {None}),
    ('Mascotas', r'world cup|\bfifa\b|figuras coleccionables', None,
     'Juguetes y bebés', 'Figuras de acción', {None}),
    ('Mascotas', r'camara de seguridad|camara de mascotas|\bnoorio\b', None,
     'Cámaras de seguridad', 'Cámaras interiores', {None}),
    ('Mascotas', r'dobladora|\bplegadora\b', None, 'Herramientas', 'Construcción', {None}),
    ('Teclados', r'keyboard (for|with backlight).{0,30}laptop|top cover with|para laptops?\b', None,
     'Componentes y accesorios de PC', 'Accesorios', {None}),
    ('Teclados', r'alfombrilla|mouse ?pad|tapete para mouse', None, 'Mouse', 'Oficina', {None}),
    ('Teclados', r'pedal (sustain|de expresion|sostenido)|teclado electronico lexibook', None,
     'Instrumentos musicales', 'Bancos, soportes y accesorios de teclado', {None}),
    ('Teclados', r'\bviking pro\b|2 in 1 tablet laptop', None, 'Tabletas', 'Tabletas Windows y rugged', {None}),

    # ---- Segunda tanda de Domótica y Cámaras (20-sep).
    ('Domótica y hogar inteligente',
     r'\baiphone\b|\bisonas\b|global cache|\bbrainboxes\b|kb electronics|\batosa\b|\barduino\b|'
     r'inserto (decorativo|pasacables)|panel de pared para garaje|fibra optica|'
     r'placa controladora|modulo de seguridad',
     None, 'Herramientas', 'Material eléctrico', {None}),
    ('Domótica y hogar inteligente', r'\bbascula\b|body scale', None, 'Salud', 'Básculas', {None}),
    ('Domótica y hogar inteligente',
     r'serie navidena|manguera led|starlight headliner|\bfriendship lamp\b',
     None, 'Iluminación', 'Decorativa', {None}),
    ('Domótica y hogar inteligente',
     r'\bpuk grip\b|control (inalambrico )?iine|grip ergonomico para juegos',
     None, 'Videojuegos', 'Otros accesorios gamer', {None}),
    ('Domótica y hogar inteligente', r'\beufy\b.{0,20}(llavero|quick arm)|panel solar.{0,10}ring',
     None, 'Cámaras de seguridad', 'Otros', {None}),
    ('Domótica y hogar inteligente', r'dispositivo de seguimiento|localizador xiaomi|\btag\b.{0,8}1pz',
     None, 'Otros', 'Varios', {None}),

    ('Cámaras y fotografía',
     r'\bring\b.{0,20}(plug|2k|interiores?)|\bblink\b|\bchamberlain\b|\bmyq\b|\baosu\b|'
     r'\bseco-?larm\b|\blicaevey\b|\bsq11\b|xiaomi (mi home|camara para exterior)|'
     r'camara (inalambrica )?(pequena )?para (el hogar|oficina)',
     None, 'Cámaras de seguridad', 'Cámaras interiores', {None}),
    ('Cámaras y fotografía', r'\bshure\b.{0,20}(blx|sistema inalambrico)|sistema inalambrico de microfono',
     None, 'Instrumentos musicales', 'Micrófonos', {None}),
    ('Cámaras y fotografía', r'\bbabycam\b|monitor de video inalambrico en el vehiculo', None,
     'Juguetes y bebés', 'Monitores de bebé', {None}),
    ('Cámaras y fotografía', r'para acuarios y terrarios|camara para mascotas', None,
     'Mascotas', 'Acuarios y terrarios', {None}),

    # ---- Iluminación y Autos (20-sep).
    ('Iluminación', r'bobina de encendido|\bmorimoto\b', None,
     'Autos, bicicletas y motos', 'Accesorios y refacciones', {None}),
    ('Iluminación', r'tubo de espectro|\beisco\b', None, 'Otros', 'Varios', {None}),
    ('Iluminación', r'flotadores iluminados|\bthill\b', None, 'Deportes y fitness', 'Otros', {None}),
    ('Iluminación', r'mezcladora de audio', None, 'Instrumentos musicales', 'Producción de audio', {None}),
    ('Iluminación', r'\bestevez\b|valvula (de union |final )?anti-?retorno|rejilla plastica', None,
     'Herramientas', 'Plomería', {None}),
    ('Iluminación',
     r'mata ?mosquitos|antimosquitos|exterminador de insectos|atrapa mosquitos|trampa.{0,15}mosquitos',
     None, 'Otros', 'Varios', {None}),
    ('Autos, bicicletas y motos',
     r'^(?:\S+ ){0,3}(top 10x10|motocicletas en accion)|manual.{0,20}motocicletas|'
     r'electricidad (y electronica )?(de|para) motocicletas|reparacion mecanica de motocicletas|'
     r'mantenimiento y servicio profesional de motocicletas|comportamiento dinamico|'
     r'\bspanish edition\b|manuales tecnicos profesionales',
     None, 'Libros', 'Técnicos y profesionales', {None}),
    ('Autos, bicicletas y motos', r'hot wheels|pista.{0,20}(lavado de autos|carreras)', None,
     'Juguetes y bebés', 'Vehículos de juguete', {None}),
    ('Autos, bicicletas y motos',
     r'cabina de pintura|maquina de lavado de autos|barrera de estacionamiento|\bbolardo\b|'
     r'adaptador de pistola de lavado',
     None, 'Herramientas', 'Hidrolavadoras', {None}),
    # Lo que la tienda colgó de Cocina y comedor sin serlo: la cortina de
    # baño con sus ganchos, la bufetera de bufet y la bolsa de cuadro.
    ('Cocina y comedor', r'cortinas? de ducha|cortinas? de bano|ganchos? para cortina',
     None, 'Blancos y ropa de cama', 'Cortinas', {None}),
    ('Cocina y comedor', r'\bchafer\b|\bbufetera\b|\bchafing\b|mesa (caliente|termica) (de|para) bufet',
     None, 'Equipo comercial', 'Cocina industrial', {None}),
    ('Cocina y comedor', r'bolsas? (para |de )?bicicleta|bolsa bicicleta',
     None, 'Autos, bicicletas y motos', 'Bolsas, canastas y portabultos', {None}),
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
            # La ficha "sin subcategoría" viene de dos formas, None y cadena
            # vacía, según por dónde entró al catálogo. Comparar contra {None}
            # a secas dejaba fuera a las vacías, y con ellas a familias
            # enteras (los relés DH48S, que son siete fichas iguales).
            if subs is not None and (p.get('subcategory') or None) not in subs:
                continue
            s2 = sub2(tn) if callable(sub2) else sub2
            if not s2 or s2 not in reg.get(cat2, ()):
                break
            # Mover una ficha a donde ya está no es un movimiento: la regla
            # de piezas de bocina alcanzaba también a las que ya estaban en
            # "Accesorios para bocinas", y esas 50 llenaban el informe y el
            # grupo que se aplicaba, tapando los movimientos de verdad.
            if cat2 == cat and s2 == (p.get('subcategory') or None):
                break
            # aplicar_movimientos normaliza la subcategoría vacía a "None":
            # sin esto la clave decía "" y ningún producto casaba.
            k = f"{cat} | {p.get('subcategory') or None} | {cat2} | {s2}"
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
