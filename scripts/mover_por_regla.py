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


def _tramo_mah_mover(tn):
    """Tramo de capacidad para el power bank que se mueve desde Cargadores.
    Sin cifra, el tramo más común del catálogo."""
    m = re.search(r'(\d{4,6}) ?mah|\b(\d{1,2}) ?ah\b', tn)
    if not m:
        return 'Hasta 10,000 mAh'
    n = int(m.group(1)) if m.group(1) else int(m.group(2)) * 1000
    return 'Hasta 10,000 mAh' if n <= 10000 else ('10,000 a 20,000 mAh' if n <= 20000 else 'Más de 20,000 mAh')


def tramo_mah(tn):
    m = re.search(r'(\d{1,3}[.,]?\d{3}|\d{4,6})\s*m ?ah', tn)
    if not m:
        return None
    n = int(m.group(1).replace('.', '').replace(',', ''))
    return 'Hasta 10,000 mAh' if n <= 10000 else ('10,000 a 20,000 mAh' if n <= 20000 else 'Más de 20,000 mAh')


# (categoría origen, regex que debe cumplir, regex que NO debe cumplir o None,
#  categoría destino, subcategoría destino o función(tn) -> sub|None)
AUTOS_BALDE = {'Autos'}

# Lotes con nombre (auditar_subcategorias_tienda.py): cada lote se prueba y se
# aplica solo con --lote, y además entra en REGLAS para las corridas completas.
LOTES = {}

REGLAS = [
    # --- Lotes del 21 de septiembre de 2026 -----------------------------
    # Segunda tanda de la auditoría estadística (margen 14). De 2,289
    # señalados van los grupos donde el modelo tiene razón al leerlos; se
    # dejan fuera los que acierta la clasificación actual y falla el modelo
    # ("Laptop de 17.3 pulgadas" está bien en 17" o más, y el modelo la
    # quería en 15"; la silla gamer está bien donde está).

    # El tocadiscos y el fonógrafo no son una bocina Bluetooth.
    # El "no": las patas de goma y los cables de un tocadiscos también lo
    # nombran, y son accesorios.
    ('Bocinas', r'tocadiscos|fonografo|reproductor de vinilo|vinilo vintage|'
     r'\bgramofono\b|tornamesa',
     r'^(?:\S+ ){0,3}(patas?|pata|base|soporte|cable|funda|aguja|capsula|'
     r'almohadilla|kit|adaptador|tapete|correa)\b',
     'Bocinas', 'Radios y reproductores', ['Bocinas Bluetooth']),

    # El altavoz de estantería de dos o tres vías es Hi-Fi, no portátil.
    ('Bocinas', r'de estanteria|bookshelf|(dos|tres|2|3) vias|\bhi-?fi\b|'
     r'monitor de estudio',
     # Las de auto también son «de 2 vías» (Kicker, Soundstream 4x6 pulg).
     r'^(?:\S+ ){0,3}(patas?|base|soporte|cable|funda|rejilla|kit|'
     r'adaptador|almohadilla)\b|\bautos?\b|carro|coche|kicker|soundstream|\d ?pulg|inteligente',
     'Bocinas', 'De estantería y Hi-Fi', ['Bocinas Bluetooth']),

    # El aire portátil de ruedas no es un minisplit (que va en la pared).
    ('Climatización', r'\bportatil(es)?\b.{0,40}\b\d{4,5} ?btu|'
     r'aire acondicionado portatil|unidad de ca portatil', None,
     'Climatización', 'Aires acondicionados portátiles', ['Minisplit']),

    # La batería compatible ES una batería, aunque diga "compatible con".
    ('Herramientas', r'^(?:\S+ ){0,4}bateria\b|bateria (compacta|de iones|de litio|'
     r'recargable).{0,30}(milwaukee|dewalt|makita|bosch|ryobi|truper)', None,
     'Herramientas', 'Baterías y cargadores de herramienta',
     ['Refacciones de herramientas eléctricas']),

    # El sensor y el empaque del refrigerador tenían subcategoría propia.
    ('Refacciones', r'refrigerador|nevera|congelador|frigorific', None,
     'Refacciones', 'Refacciones para refrigerador',
     ['Refacciones para otros electrodomésticos']),

    # El gabinete y la alacena de cocina dentro del cajón "Otros".
    ('Muebles', r'gabinete (inferior|superior|bajo|alto|de cocina)|alacena|'
     r'despensero|mueble de cocina|modulo de cocina', None,
     'Muebles', 'Muebles de cocina', ['Otros', 'Varios']),

    # La mesa plegable de pared no es una mesa de comedor extensible.
    ('Muebles', r'plegable de pared|abatible de pared|que ahorra espacio.{0,20}pared', None,
     'Muebles', 'Mesas plegables y multiusos', ['Mesas de comedor extensibles']),

    # Salidos de aprender_subcategoria.py --auditar: un bayes ingenuo
    # entrenado con las fichas YA clasificadas de cada categoría señala las
    # que su propia subcategoría explica mucho peor que otra. No es un
    # oráculo (marca de más), así que de sus 780 señalados van sólo los
    # grupos donde el error es evidente al leerlos.

    # 53 fichas. La flejadora --la máquina que pone el fleje a una caja--
    # cayó en "Baterías y cargadores de herramienta" por decir "a batería"
    # y en "Soldadura" por decir "máquina". Tiene subcategoría propia.
    ('Herramientas', r'flejadora|flejado|zunchadora|empacadora de fleje|'
     r'maquina de fleje', None,
     'Herramientas', 'Flejadoras y empacadoras',
     ['Baterías y cargadores de herramienta', 'Soldadura', 'Herramientas eléctricas']),

    # 32. El banco de pesas y el rack de sentadillas tienen su subcategoría;
    # estaban repartidos entre mancuernas, abdominales y "equipo de gimnasio"
    # porque el título nombra las pesas que se usan encima.
    ('Deportes y fitness',
     r'^(?:\S+ ){0,3}(banco|bancos|rack|racks|estante|soporte|jaula|'
     r'taburete de entrenamiento)\b.{0,40}'
     r'(pesas|mancuernas|sentadilla|press|banca|gimnasio|barra)|'
     r'press de banca|banco (ajustable|plegable|olimpico|de gimnasio)', None,
     'Deportes y fitness', 'Bancos y racks',
     ['Mancuernas', 'Máquinas de abdominales', 'Accesorios de fuerza',
      'Equipo de gimnasio', 'Pesas', 'Barras y discos']),

    # 11. El triciclo de tres ruedas para adulto estaba entre los accesorios
    # de bicicleta.
    ('Autos, bicicletas y motos',
     r'triciclo|tres ruedas|3 ruedas|bicicleta de carga|\bcargo bike\b', None,
     'Autos, bicicletas y motos', 'Triciclos y bicicletas de carga',
     ['Accesorios para bicicleta', 'Accesorios y refacciones']),

    # 10. "Ventilador sin aspas" fue a parar a la subcategoría de las aspas
    # de repuesto, que es lo contrario de lo que es.
    ('Climatización',
     r'sin aspas|bladeless|ventilador (portatil|de mano|personal|recargable|'
     r'de camping|usb)\b', None,
     'Climatización', 'Ventiladores portátiles y de mano',
     ['Aspas y refacciones de ventilador']),

    # 10. Audífonos enteros dentro de "Almohadillas y repuestos".
    ('Audífonos',
     r'^(?:\S+ ){0,3}audifonos?\b.{0,50}(inalambric|bluetooth|in ?ear|tws)|'
     r'^(?:\S+ ){0,3}(earbuds?|auriculares) (inalambric|bluetooth|tws)', None,
     'Audífonos', 'Earbuds inalámbricos', ['Almohadillas y repuestos']),

    # 6. El calefactor entero dentro de sus propias refacciones.
    ('Climatización',
     r'^(?:\S+ ){0,3}(calefactor|calentador de (espacio|ambiente|cuarto))\b'
     r'.{0,40}(ceramic|de aire|con termostato|con control)', None,
     'Climatización', 'Calefactores cerámicos y de aire', ['Refacciones de calefactor']),

    # 6. Cobijas eléctricas enteras dentro de "Repuestos y controles".
    ('Blancos y ropa de cama',
     r'^(?:\S+ ){0,3}(cobija|manta|frazada|colcha)\b.{0,40}'
     r'(electric|termica|calefactable|con calor)', None,
     'Blancos y ropa de cama', 'Cobijas eléctricas',
     ['Repuestos y controles de cobija eléctrica']),

    # Cortes que faltaban, al estilo de kakaku.com: parte 掃除機 en
    # スティック / ハンディ / キャニスター / ロボット y スーツケース por
    # "機内持ち込み可否". Acá "Portátiles" juntaba la aspiradora de mano con
    # la de escoba (750 fichas, el 61% de la categoría) y "Maletas" juntaba
    # la de cabina, la documentada y la mochila de viaje (852, el 80%).
    # El orden importa: primero lo específico, después lo general.

    ('Aspiradoras', r'\bde escoba\b|\bvertical(es)?\b|\bstick\b|escoba inalambrica',
     None, 'Aspiradoras', 'De escoba', ['Portátiles']),
    ('Aspiradoras', r'\bde mano\b|\bhandheld\b|para auto|de coche|portatil de mano',
     None, 'Aspiradoras', 'De mano', ['Portátiles']),

    # Una mochila de viaje no es una maleta: es lo primero que hay que
    # sacar, porque si no el corte por tamaño mezcla peras con manzanas.
    ('Viajes', r'^\W*(mochila|bolsa|neceser|maleta deportiva|bolso|'
     r'organizador|porta ?traje|cangurera|rinonera)',
     None, 'Viajes', 'Mochilas y bolsas de viaje', ['Maletas']),
    ('Viajes', r'\b(set|juego|kit) de \d? ?maletas|set de maletas|'
     r'\b[234] ?piezas\b|juego de maletas',
     None, 'Viajes', 'Sets de maletas', ['Maletas']),
    ('Viajes', r'\bcabina\b|carry ?on|equipaje de mano|\bde mano\b|'
     r'\b(1[6-9]|20|21)\s*(?:"|pulg|pulgadas|in\b)',
     None, 'Viajes', 'Maletas de cabina', ['Maletas']),
    ('Viajes', r'\b(2[4-9]|3[0-2])\s*(?:"|pulg|pulgadas|in\b)|\bgrande\b|'
     r'\bdocumentad|\b(8[0-9]|9[0-9]|1\d\d)\s*l\b',
     None, 'Viajes', 'Maletas grandes', ['Maletas']),

    # Auditoría de taxonomía: subcategorías con nombre de MARCA, el mismo
    # concepto repetido en dos categorías, y una categoría fantasma.

    # "Drones / DJI" era una subcategoría con nombre de marca --que es
    # justo lo que no se hace-- y encima no tenía drones DJI adentro: son
    # accesorios PARA drones (megáfono, soporte de tableta para el control).
    ('Drones', r'.', None, 'Drones', 'Accesorios', ['DJI']),

    # "Juegos de mesa / Woodestic" también era una marca. Lo que vende son
    # juegos de madera de puntería (crokinole, shuffleboard), que es un tipo
    # de juego, no un fabricante.
    ('Juegos de mesa', r'.', None, 'Juegos de mesa', 'De mesa clásicos', ['Woodestic']),

    # "Bicicletas eléctricas" estaba en dos categorías. En Autos lo que hay
    # son PIEZAS de e-bike (controladores, corte de freno), no bicicletas;
    # las bicicletas enteras están en Movilidad eléctrica.
    ('Autos, bicicletas y motos',
     r'controller|controlador|corte de freno|\bkit\b|conversion|display|'
     r'acelerador|throttle|\bbms\b|celda|motor de rueda|\bcableado\b',
     None, 'Refacciones', 'Para bicicletas eléctricas', ['Bicicletas eléctricas']),
    ('Autos, bicicletas y motos', r'.', None,
     'Movilidad eléctrica', 'Bicicletas eléctricas', ['Bicicletas eléctricas']),

    # Todo el audio de auto vive en Autos (coaxiales, componentes,
    # tweeters, subwoofers, amplificadores, estéreos). "Bocinas para auto"
    # tenía además una copia dentro de Bocinas, partida en dos el mismo
    # catálogo.
    ('Bocinas', r'.', None,
     'Autos, bicicletas y motos', 'Bocinas para auto', ['Bocinas para auto']),

    # Generadores repetido en Herramientas y en Otros. Se juntan donde ya
    # están los compresores y las hidrolavadoras.
    ('Otros', r'.', None, 'Herramientas', 'Generadores', ['Generadores']),

    # Un foco inteligente es domótica; en Iluminación quedaba la copia chica.
    ('Iluminación', r'.', None,
     'Domótica y hogar inteligente', 'Focos inteligentes', ['Focos inteligentes']),

    # La categoría "Fitness" tenía ocho fichas repartidas en Grande /
    # Mediana / Pequeña, y existe "Deportes y fitness" con treinta
    # subcategorías de verdad. No era una categoría: era un resto de una
    # importación vieja, con su página publicada y casi nada adentro.
    ('Fitness', r'cinta de correr|caminadora|remadora|eliptica|spinning|'
     r'bicicleta (fija|de spinning)', None,
     'Deportes y fitness', 'Máquinas de cardio'),
    ('Fitness', r'disco|mancuerna|\bbarra\b|\bpesa', None,
     'Deportes y fitness', 'Barras y discos'),
    ('Fitness', r'cinturon|rodillera|muneque|coderas?|soporte lumbar|faja', None,
     'Deportes y fitness', 'Protección y soportes'),
    ('Fitness', r'rodillo|foam roller|masaje|cuerda (para )?saltar|saltar', None,
     'Deportes y fitness', 'Accesorios de fuerza'),
    ('Fitness', r'.', None, 'Deportes y fitness', 'Otros'),

    # El topper es ropa de cama, no un mueble.
    ('Muebles', r'.', None,
     'Blancos y ropa de cama', 'Toppers y sobrecolchones', ['Toppers y sobrecolchones']),

    # Salieron de una auditoría nueva: buscar la ficha que está en una
    # subcategoría de PRODUCTO (ver roles_subcategorias.py) pero cuyo
    # nombre ARRANCA nombrando un accesorio, una parte o un consumible --
    # descartando el caso en que la categoría o la subcategoría ya se
    # llaman así, porque un cargador dentro de "Cargadores y adaptadores"
    # está en su casa. Dio 4,319 fichas en 382 subcategorías; acá van las
    # que tienen un destino que ya existe.

    # El filtro de repuesto no es el purificador. 245 fichas en
    # "Purificadores bajo tarja" y 82 en "Ósmosis inversa" abrían diciendo
    # "Filtro de agua…" y competían con el sistema entero.
    ('Electrodomésticos',
     r'^(?:\S+ ){0,2}(filtro|membrana|cartucho)s?\b',
     r'purificador (de agua )?(bajo|con filtro)|sistema de (osmosis|filtracion)|'
     r'^(?:\S+ ){0,3}(purificador|sistema|equipo)\b',
     'Electrodomésticos', 'Filtros y membranas de repuesto',
     ['Purificadores bajo tarja', 'Ósmosis inversa', 'Purificadores de agua',
      'Purificadores de grifo y encimera']),

    # La funda y el cable de la batería portátil no son la batería.
    ('Baterías portátiles',
     r'^(?:\S+ ){0,2}(funda|estuche|carcasa|bolsa|cable|adaptador|soporte)s?\b',
     r'power ?bank|banco de energia|bateria portatil|\d+ ?mah\b',
     'Baterías portátiles', 'Accesorios y repuestos',
     ['Hasta 10,000 mAh', '10,000 a 20,000 mAh', 'Más de 20,000 mAh']),

    # La funda del estuche de los earbuds no es un par de audífonos. 210
    # fichas repartidas entre "Earbuds inalámbricos" y "Earbuds con cable".
    # Para esto hubo que darle a la categoría una subcategoría "Accesorios",
    # que no tenía: sin destino, la auditoría sólo podía señalar.
    ('Audífonos',
     r'^\W*(funda|estuche|carcasa|bolsa para|soporte|gancho|mosqueton|'
     r'almohadilla|espuma|adaptador|clip de|correa para|cable para|'
     r'kit de (limpieza|estuche)|repuesto)s?\b',
     r'(audifono|auricular|earbud|diadema|headset|headphone)s? '
     r'(inalambric|bluetooth|con cable|deportiv|gamer|tws)',
     'Audífonos', 'Accesorios',
     ['Earbuds inalámbricos', 'Earbuds con cable', 'Earbuds de cuello',
      'Earbuds deportivos', 'Earbuds para niños', 'Earbuds con cancelación de ruido',
      'Diadema con cable', 'Diadema inalámbrica', 'Diadema con cancelación de ruido',
      'De oído abierto', 'Gamer']),

    # Lo mismo con el reloj: el soporte y el bumper no son el smartwatch.
    ('Relojes inteligentes',
     r'^\W*(funda|estuche|carcasa|bumper|mica|protector de pantalla|soporte|'
     r'base de carga|cargador para|cable para|correa|extensible|'
     r'pulsera de repuesto)s?\b',
     r'\b(smartwatch|smart watch|reloj inteligente|banda de actividad)\b.{0,30}'
     r'(amoled|gps|llamadas|bluetooth|pantalla)',
     'Relojes inteligentes', 'Accesorios'),

    # El cable SATA y el filtro antipolvo de la caja no son un componente
    # con el que se compare una tarjeta madre.
    ('Componentes y accesorios de PC',
     r'^(?:\S+ ){0,2}(cable|filtro|tornillo|adaptador|soporte|funda)s?\b',
     r'tarjeta (madre|grafica|de video)|procesador|fuente de poder|disipador',
     'Componentes y accesorios de PC', 'Accesorios',
     ['Componentes']),

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
    # Un combo «Pantalla ... con/+ barra de sonido» es un televisor con regalo,
    # no una barra (26-sep-2026: 9 combos LG OLED habían ido a Barras).
    ('Televisores', r'barra de sonido|\bsoundbar\b', r'^(combo )?(pantalla|smart ?tv|tv\b|televis)',
     'Bocinas', 'Barras de sonido'),
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
     r'rompecabezas|puzzle|juego de mesa|juego de cartas', 'Juguetes y bebés', 'Juguetes para exterior'),
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
                       r'resbaladilla|columpio|casa de juegos', None, 'Juguetes y bebés', 'Juguetes para exterior',
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
     'Juguetes y bebés', 'Juguetes para exterior', {None}),
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

    ('Instrumentos musicales', r'maquina (de )?burbujas', None, 'Iluminación', 'Escenario', {None}),
    ('Redes', r'distribuidor de alimentacion|\bdcdu\b', None,
     'Herramientas', 'Material eléctrico', {None}),
    ('Electrodomésticos', r'navaja plegable|\bschrade\b', None,
     'Herramientas', 'Herramientas de corte manual', {None}),
    ('Electrodomésticos', r'purificador(es)? de aire(?!.{0,15}cocina)', None,
     'Climatización', 'Purificadores de aire', {None}),

    # Cargadores, Almacenamiento y Suplementos (21-sep): el power bank tiene
    # categoría propia, la RAM es componente y la guía es un libro.
    ('Cargadores y adaptadores',
     r'banco de (energia|poder)|power ?bank|powerbank|bateria (portatil|externa)|'
     r'\bstash mini\b|\bmophie\b.{0,20}mah|\d{4,6} ?mah',
     r'cargador de pared|\bcable\b de datos$', 'Baterías portátiles',
     lambda tn: _tramo_mah_mover(tn), {None}),
    ('Almacenamiento', r'memoria ddr[2345]?\b', None,
     'Componentes y accesorios de PC', 'RAM DDR3 y anteriores', {None}),
    ('Suplementos', r'gran guia de la suplementacion|manual definitivo', None,
     'Libros', 'Salud y nutrición', {None}),

    # Audífonos (21-sep): el celular que regala audífonos, la funda de
    # tableta y el teclado Yamaha no son audífonos.
    ('Audífonos', r'\b\d+gb \d+ ?gb\b|\bmovistar\b.{0,25}audifonos|honor x7d|oppo a58', None,
     'Celulares', 'Android', {None}),
    ('Audífonos', r'bolsa para tablet|funda de transporte para ipad', None,
     'Tabletas', 'Accesorios para tableta', {None}),
    ('Televisores', r'tableta grafica|\bxppen\b', None,
     'Tabletas', 'Tabletas de dibujo y escritura', {None}),
    ('Televisores', r'protector de sobretensiones', None, 'Herramientas', 'Material eléctrico', {None}),
    ('Televisores', r'sistemas? de iluminacion de television', None, 'Iluminación', 'Escenario', {None}),
    # CCTV: la caja de conexiones, el balún y el transceptor son material
    # eléctrico; la central de intercomunicación es de Domótica.
    ('Cámaras de seguridad',
     r'caja de conexiones|\bpfa\d{3}|transceptor|\bpfm\d{3}|extensor video|\bbalu[nm]\b|'
     r'antivandalica|medidor de luz|monitor led \d',
     None, 'Herramientas', 'Material eléctrico', {None}),
    ('Cámaras de seguridad', r'centrales de voz|intercomunicacion', None,
     'Domótica y hogar inteligente', 'Sensores', {None}),
    ('Audífonos', r'soporte de pared para ps5|\bplayvital\b', None,
     'Videojuegos', 'Otros accesorios gamer', {None}),
    ('Audífonos', r'hubs splitter|panel frontal de auriculares', None,
     'Componentes y accesorios de PC', 'Accesorios', {None}),
    ('Audífonos', r'paquete de teclado premium|\b\d{2} teclas\b', None,
     'Instrumentos musicales', 'Teclados', {None}),
    ('Audífonos', r'preamplificador de microfono|mezclador de auriculares', None,
     'Instrumentos musicales', 'Micrófonos', {None}),

    # Belleza y Baterías portátiles (21-sep): el libro de Scrum, el kit de
    # cuidado del bebé y el cargador de herramienta no son del rubro.
    ('Belleza y cuidado personal', r'para scrum\b|libro impreso con espiral', None,
     'Libros', 'Negocios y finanzas', {None}),
    ('Belleza y cuidado personal',
     r'\bpanal\b|dermatitis del panal|\bmordedor|denticion|balsamo.{0,15}pezones|'
     r'spray para extraccion|\bbaby\b|\bkids\b|pediatric|\binfantino\b|'
     r'kit de cuidado para bebe|oxido de zinc',
     None, 'Juguetes y bebés', 'Bebés', {None}),
    ('Belleza y cuidado personal', r'cepillo de dientes', None, 'Salud', 'Cuidado dental', {None}),
    ('Baterías portátiles', r'cargador de litio.{0,20}\bryobi\b|\bbpl-?\d|cortadores de cables', None,
     'Herramientas', 'Baterías y cargadores de herramienta', {None}),
    ('Baterías portátiles', r'\bmouse\b inalambrico', None, 'Mouse', 'Inalámbricos', {None}),
    ('Baterías portátiles', r'radio portatil', None, 'Bocinas', 'Radios y reproductores', {None}),
    ('Baterías portátiles', r'calentador de bateria', None, 'Climatización', 'Calefactores', {None}),

    # Televisores y Lavadoras: la mitad de lo que colgaba de ahí era el
    # accesorio de otra categoría (21-sep).
    ('Televisores', r'auriculares? (inalambricos? )?(para|digitales para)|\bavantree\b|\bsennheiser\b|'
     r'solidcom|altavoz de tv inalambrico.{0,40}audicion',
     None, 'Audífonos', 'Diadema inalámbrica', {None}),
    ('Televisores', r'mueble para tv|repisas? flotantes?|estante elevador', None,
     'Muebles', 'Mesas para TV y consolas', {None}),
    ('Televisores', r'tableta grafica|\bxppen\b', None, 'Tabletas', 'Tabletas de dibujo', {None}),
    ('Televisores', r'sports production|logbook|complete guide to live', None,
     'Libros', 'Técnicos y profesionales', {None}),
    ('Televisores', r'barras? de luz rgbic|\bgovee\b', None, 'Iluminación', 'Tiras LED', {None}),
    ('Televisores', r'amplificador wifi|repetidor inalambrico', None, 'Redes', 'Repetidores', {None}),
    ('Televisores', r'juguete interactivo para perro|wobble wag', None,
     'Mascotas', 'Juguetes para perro', {None}),
    ('Televisores', r'altavoz de piso|\bmaxxbass\b|q acoustics', None, 'Bocinas', 'Bocinas Bluetooth', {None}),
    ('Lavadoras', r'bano de pies|masaje.{0,20}pies', None,
     'Belleza y cuidado personal', 'Cuidado personal', {None}),
    ('Lavadoras', r'fregadora de (pisos|suelos)', None, 'Aspiradoras', 'Limpiadoras de pisos', {None}),
    ('Lavadoras', r'estantes? (de almacenamiento )?para lavadora|mini estantes para lavadora|'
     r'elevadores de (mesa|cama)',
     None, 'Muebles', 'Repisas', {None}),
    ('Lavadoras', r'tapete (de microfibra|frio)|tapetes? refrescante', None,
     'Mascotas', 'Tapetes y accesorios de alimentación', {None}),
    ('Lavadoras', r'cable para secadora', None, 'Refacciones', 'Refacciones para lavadora y secadora', {None}),
    ('Lavadoras', r'ahorro de electricidad|protector de sobretensiones|\bgfci\b|enchufe de reemplazo', None,
     'Herramientas', 'Material eléctrico', {None}),
    ('Lavadoras', r'alfombras? (absorbente|de bano)|protector de colchon|compresa caliente|'
     r'almohadilla termica',
     None, 'Blancos y ropa de cama', 'Tapetes de baño', {None}),
    ('Lavadoras', r'purificador(es)? de aire', None, 'Climatización', 'Purificadores de aire', {None}),
    ('Lavadoras', r'platillos de bateria|tuercas de ala', None,
     'Instrumentos musicales', 'Baterías', {None}),

    # Iluminación: la placa ciega y la extensión de uso rudo son material
    # eléctrico, y el foco inteligente es de Domótica (21-sep).
    ('Iluminación',
     r'placas? (ciega|de \d ?modulo|de \d+ modulos)|\blugano\b|'
     r'extension uso rudo|adaptador clavija|\bclavija\b',
     r'intelig|wifi|smart|tuya|alexa', 'Herramientas', 'Material eléctrico', {None}),
    ('Iluminación', r'smart led bulb|foco intelig|\bnexxt\b.{0,20}smart', None,
     'Domótica y hogar inteligente', 'Focos inteligentes', {None}),

    # Herramientas: la báscula de cocina y el batidor no son herramienta.
    ('Herramientas', r'\bbascula\b|\bbalanzas?\b|juego de pesas de escala', None,
     'Cocina y comedor', 'Básculas y medidores', {None}),
    ('Herramientas', r'\bbatidor\b|herramienta multiusos de cocina', None,
     'Cocina y comedor', 'Utensilios de cocina', {None}),
    ('Herramientas', r'lente de camara trasera|maniqui|modelo de anatomia|'
     r'herramientas de dibujo|figures de dibujo',
     None, 'Otros', 'Varios', {None}),
    ('Herramientas', r'maquina de prensado en caliente|prensa de calor', None,
     'Equipo comercial', 'Prensas de calor', {None}),

    # Mascotas: el equipo veterinario, el humidificador con forma de gato y
    # el esmalte "ojo de gato" (21-sep). Ninguno es un producto de mascota.
    ('Mascotas',
     r'oximetro|monitor.{0,30}(frecuencia cardiaca|presion arterial)|detector de pulso|'
     r'ultrasonido veterinario|equipo veterinario|uso veterinario',
     None, 'Salud', 'Equipo de monitoreo médico', {None}),
    ('Mascotas', r'\bbascula\b|\bb\?scula\b', None, 'Salud', 'Básculas', {None}),
    ('Mascotas', r'humidificador', None, 'Climatización', 'Humidificadores', {None}),
    ('Mascotas', r'esmalte en gel|\bbeetles\b.{0,25}esmalte', None,
     'Belleza y cuidado personal', 'Uñas', {None}),
    ('Mascotas', r'silla infantil|taburete infantil|silla montessori|set mesa cuadrada con silla', None,
     'Muebles', 'Sillas infantiles', {None}),
    ('Mascotas', r'feather flag|\bbandera\b', None, 'Otros', 'Varios', {None}),

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
     'Drones', 'FPV', {None}),
    ('Autos, bicicletas y motos', r'fuente de alimentacion dc', None,
     'Herramientas', 'Material eléctrico', {None}),
    ('Autos, bicicletas y motos', r'adaptador (for )?coaxial|\bsma-tnc\b|\brg316\b', None,
     'Redes', 'Access points', {None}),
    ('Autos, bicicletas y motos', r'radio portatil', None, 'Bocinas', 'Radios y reproductores', {None}),
    ('Autos, bicicletas y motos', r'\bdylf-?\d+|sensor de impacto|prensa jack|medidor de fuerza', None,
     'Herramientas', 'Medición', {None}),
    ('Autos, bicicletas y motos', r'juego de \d+ platos|juegos para exteriores', None,
     'Otros', 'Varios', {None}),
    ('Autos, bicicletas y motos', r'\bprinsel\b|vehiculo motocross', None,
     'Juguetes y bebés', 'Vehículos de juguete', {None}),
    ('Herramientas', r'soporte universal para vasos', None, 'Otros', 'Varios', {None}),
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
    # El mousepad suelto es de Mouse; el combo que lo incluye no.
    ('Teclados', r'alfombrilla|mouse ?pad|tapete para mouse',
     r'\bcombo\b|\bkit\b.{0,25}teclado|teclado.{0,25}\bkit\b', 'Mouse', 'Oficina', {None}),
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
     r'mata ?m[o]?squitos|antimosquitos|exterminador de insectos|atrapa m[o]?squitos|'
     r'trampa.{0,15}m[o]?squitos',
     None, 'Otros', 'Varios', {None}),
    # Blancos y Mascotas (21-sep): la caja zapatera, el futbolín y la cortina
    # a prueba de gatos no son ropa de cama ni producto de mascota.
    ('Blancos y ropa de cama', r'cajas? (absorbentes de humedad|zapateras)|cajas? organizadora', None,
     'Otros', 'Organización del hogar', {None}),
    ('Blancos y ropa de cama', r'\bfutbolin\b', None,
     'Juegos de mesa', 'De mesa clásicos', {None}),
    ('Blancos y ropa de cama',
     r'orejeras antiruido|proteccion auditiva|juego de \d+ platos|\blanas? light\b|\bberroco\b',
     None, 'Otros', 'Varios', {None}),
    ('Blancos y ropa de cama', r'cinta para extensiones|extensiones de cabello', None,
     'Belleza y cuidado personal', 'Extensiones de cabello', {None}),
    ('Mascotas', r'cortinas? opacas|cortinas?.{0,30}a prueba de gatos', None,
     'Blancos y ropa de cama', 'Cortinas', {None}),
    ('Mascotas', r'alfombra de bano|alfombra de gato.{0,30}bano', None,
     'Blancos y ropa de cama', 'Tapetes de baño', {None}),
    ('Mascotas', r'mobiliario de escritorio|resina sintetica.{0,30}decoracion', None,
     'Decoración de hogar y jardín', 'Espejos', {None}),
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
    # ---- Ronda del 26-sep-2026 (colisiones de palabras y comodines) ----
    # «RAM 1500» es una camioneta, no memoria: refacciones de auto que
    # cayeron en Componentes de PC por la palabra.
    ('Componentes y accesorios de PC',
     r'\bram (700|1500|2500|3500|4500|5500)\b|promaster|\bdodge\b|sprinter|windstar|plymouth|\bmercury\b|\bv6\b|\bv8\b',
     None, 'Autopartes',
     lambda tn: 'Enfriamiento y climatización' if re.search(r'enfria|condensador|radiador|tubo de', tn)
     else 'Motor y transmisión'),
    ('Celulares', r'manija|tapa batea', None, 'Autopartes', 'Carrocería, espejos y molduras'),
    # Hieleras y bolsas térmicas no son refrigeradores.
    ('Refrigeradores', r'^(\S+ ){0,3}(bolsa|mochila|lonchera)\b|\blunch\b', r'para refrigerador',
     'Cocina y comedor', 'Loncheras y termos para alimentos'),
    ('Refrigeradores', r'hielera|\bcooler\b', r'para refrigerador|refrigerador con',
     'Deportes y fitness', 'Campismo'),
    # Focos de auto (H11, 9006, T10...) en Iluminación de la casa.
    ('Iluminación',
     r'^(\S+ ){0,3}(focos?|bombillas?|kit de (faros|focos|luces)|luces led)\b.{0,60}'
     r'\b(h1|h3|h4|h7|h8|h9|h11|h13|h16|9003|9004|9005|9006|9007|9012|880|881|hb3|hb4|d1s|d2s|d3s|d4s|'
     r't10|t15|194|921|1156|1157|3157|7440|7443|ba15s|ba15d)\b|antiniebla|canbus|'
     r'^(\S+ ){0,3}(focos?|bombillas?|faros?)\b.{0,40}para (auto|coche|carro|moto|camioneta)',
     r'\bfarol\b|lampara de pared|colgante|e27|e26', 'Autopartes', 'Faros y luces'),
    ('Belleza y cuidado personal', r'parabrisas', None, 'Autos y motos', 'Tapetes, fundas y parasoles'),
    ('Relojes inteligentes', r'^(\S+ ){0,2}(correa|pulsera de repuesto|malla)\b', r'^(reloj|smartwatch|banda inteligente)',
     'Relojes inteligentes', 'Correas y extensibles', {'Bandas de actividad', 'Smartwatches'}),
    # Cables sueltos en los cargadores de pared.
    ('Cargadores y adaptadores', r'^(\S+ ){0,1}cable\b',
     r'cargador (de pared|con cable)|\bcubo\b|adaptador de corriente|\+ ?cable|con cable|cabezal|\bkit\b',
     'Cargadores y adaptadores',
     lambda tn: 'Cables multiconector' if re.search(r'\b[23] en 1\b|multi', tn)
     else 'Cables Lightning' if 'lightning' in tn
     else 'Cables micro USB' if re.search(r'micro ?usb', tn)
     else 'Cables USB-C' if re.search(r'tipo ?-?c|usb ?-?c|type ?-?c', tn) else 'Cable',
     {'De pared', 'Cargadores de pared de 25 a 45 W', 'Cargadores de pared de 65 W o más',
      'Cargadores de pared hasta 20 W'}),
    # Micas para el celular Moto G (Motorola) en Motocicletas.
    ('Autos y motos', r'hidrogel|protector de pantalla|\bmoto (g|e|edge)\s?\d|\bmotorola\b', r'\bcasco',
     'Celulares', lambda tn: 'Micas para celular' if re.search(r'mica|hidrogel|pantalla|cristal|vidrio', tn)
     else 'Protectores para celular', {'Motocicletas', 'Accesorios para moto'}),
    # «Autos» era un cajón: carritos de juguete, montables, sillas de bebé...
    ('Autos y motos', r'hot wheels|matchbox|jada|bburago|burago|maisto|majorette|welly|greenlight|'
     r'escala 1[:/]\d+|\b1[:/](18|24|32|43|64)\b|a escala|diecast|fundido', None,
     'Juguetes', 'Vehículos de juguete', {'Autos'}),
    ('Autos y motos', r'montable|(carro|coche|camioneta|auto) electric[oa] (para ni|infantil)|bumper car|'
     r'scooter.{0,30}ni(n|ñ)os', r'silla|asiento|motor de|bateria de repuesto',
     'Juguetes', 'Montables', {'Autos'}),
    ('Autos y motos', r'\brc\b|control remoto|2\.4 ?ghz|radio ?control', r'alarma|arranque|restaurador|epicentro|servo tester',
     'Juguetes', 'Vehículos a control remoto', {'Autos'}),
    ('Autos y motos', r'silla(s)? (de|para) auto|asiento (de|para) (coche|auto) (infantil|para bebe)|autoasiento|'
     r'uppababy|chicco|graco|britax|cybex|maxi-?cosi', None, 'Bebés', 'Sillas de auto', {'Autos'}),
    ('Autos y motos', r'inversor|arrancador|cargador de bateria', None,
     'Autos y motos', 'Arrancadores y cargadores de batería', {'Autos'}),
    ('Autos y motos', r'transmisor|\bfm\b|altavoces|audiobahn|estereo', r'alarma',
     'Autos y motos', 'Accesorios de audio para auto', {'Autos'}),
    ('Autos y motos', r'pulidora|almohadillas? (de pulido|de lana|para (lijar|pulir|pulidora))|shampoo|\bcera\b|'
     r'cera liquida|liquido (limpia|para limpiar)|limpia|microfibra|abrillantador|clay bar',
     None, 'Autos y motos', 'Limpieza y cuidado del auto', {'Autos'}),
    ('Autos y motos', r'alarma|organizador|bandeja|ambientador|aromatizante|funda', None,
     'Autos y motos', 'Accesorios para auto', {'Autos'}),
    # ---- Sin subcategoría (26-sep-2026) ----
    ('Autopartes', r'^engrane|^engranes', None, 'Autopartes', 'Motor y transmisión', {None}),
    ('Autopartes', r'^conector|sensor|arnes', None, 'Autopartes', 'Sistema eléctrico y sensores', {None}),
    ('Autopartes', r'^valvula|balancin|junta|bendix', None, 'Autopartes', 'Motor y transmisión', {None}),
    ('Autos y motos', r'\bllantas?\b', r'bicicleta|carretilla|moto\b|motocicleta',
     'Autos y motos',
     lambda tn: ola2._auto_o_camioneta(tn, 'Llantas para auto'), {None}),
    ('Autos y motos', r'^guantes', None, 'Autos y motos', 'Guantes para moto', {None}),
    ('Autos y motos', r'^medio', None, 'Autos y motos', 'Medios rangos y bocinas profesionales', {None}),
    ('Mascotas', r'jersey|bandanas?|impermeable|\bcapa\b|chamarra|\bpants\b|sudadera|playera|sueter|vestido|disfraz',
     r'libro', 'Mascotas', 'Ropa para mascotas', {None}),
    ('Mascotas', r'alimento|croqueta|hill.?s|pedigree|churu|snack|premios?|golosina|whiskas|purina|pro plan|nupec',
     r'libro|comedero|plato|dispensador', 'Mascotas', 'Alimento y premios', {None}),
    ('Mascotas', r'^cadena|collar|pechera|arnes', r'libro', 'Mascotas', 'Correas', {None}),
    ('Mascotas', r'corta ?pelo|cepillo|peine|shampoo|champu|quita ?pelo|removedor|toallitas|cortau(n|ñ)as', r'libro',
     'Mascotas', 'Higiene y limpieza', {None}),
    ('Autos y motos', r'^(\S+ ){0,3}llantas? .{0,25}(bicicleta|\bbici\b|\bmtb\b)|llanta.{0,40}\b(700 ?x ?\d{2}|2[0679](\.5)? ?x ?[12]\.\d)',
     r'motocicleta|palanca|desmontar', 'Bicicletas y movilidad', 'Llantas para bicicleta'),
    # ---- Lo que quedaba en «Autos y motos / Autos» (26-sep-2026, segunda pasada) ----
    ('Autos y motos', r'stroller|carriola', None, 'Bebés', 'Carriolas', AUTOS_BALDE),
    ('Autos y motos', r'silla para bebe|auto silla|booster|base de asiento infantil|adaptador (de asiento|peg perego)|'
     r'bucklebee|hebilla release|asiento de coche (y cochecito|bugaboo)|coche de bebe|camara .{0,25}bebe|back seat baby|'
     r'tiny traveler|pata de apoyo para asiento|carrito de viaje para asiento|mochila (de viaje )?para asiento|'
     r'asientos de coche de bebes|doona|evenflo', None, 'Bebés', 'Sillas de auto', AUTOS_BALDE),
    ('Autos y motos', r'step ?2|cozy coupe|coche de empuje|cruiser|buggy electrico|go kart|carro electrico|'
     r'camioneta electrica|drift trike|montable|carro buggy', None, 'Juguetes', 'Montables', AUTOS_BALDE),
    ('Autos y motos', r'mando a distancia|teledirigido|control remoto|a control\b|doble control|servo tester|\bfpv\b',
     r'restaurador|epicentro', 'Juguetes', 'Vehículos a control remoto', AUTOS_BALDE),
    ('Autos y motos', r'bloques|building|bricks|\blego\b|city f1|speed champions|\bloz\b|armable|diybee|modelo de montaje',
     None, 'Juguetes', 'Bloques de construcción', AUTOS_BALDE),
    ('Autos y motos', r'juguete|\btoys?\b|playset|pinypon|playmobil|paw patrol|barbie|spidey|marvel|star wars|mandalorian|'
     r'monster (truck|jam)|fisher-price|tonka|transformable|friccion|inercial|coleccion|replica|'
     r'coche de (policia|bomberos|carreras)|camion (de policia|de remolque|portajuguetes|volquete|shinesignal)|'
     r'vehiculo (excavador|volquete|spin master|monster|razor|teledirigido)|super wings|hot ?wheels|hw collector|'
     r'green toys|\bpista\b|figuras? de accion|lionel|mcfarlane|batimovil|bburago|coche lab\.?g|coche (esmaltado|mamut)|'
     r'todo terreno giratorio|coche arana|mecanicos qaba|carro (marvel|fisher|monster|clasico|todo ?terreno)|'
     r'camioneta (toy|todo terreno wuundentoy|lori)|auto (de dinosaurio|de friccion|marvel|frjv|deportivo ford)|'
     r'auto de carreras wuundentoy|vehiculos coches|vehiculos monster|juego con forma de coche', None,
     'Juguetes', 'Vehículos de juguete', AUTOS_BALDE),
    ('Autos y motos', r'grand theft auto', None, 'Videojuegos', 'Juegos retro y otras plataformas', AUTOS_BALDE),
    ('Autos y motos', r'baston (de seguridad|para volante)|antirrobo|antirobo|inmovilizador|obd2? port lock|'
     r'localizador|rastreador|gps tracker|tkstar|rastreo|monitor de voz', None,
     'Autos y motos', 'Accesorios para auto', AUTOS_BALDE),
    ('Autos y motos', r'^camara|\bdvr\b|reversa|respaldo|dashcam|auto-vox|radar mount|navegador gps|garmin', None,
     'Autos y motos', 'Dashcams y cámaras', AUTOS_BALDE),
    ('Autos y motos', r'bocinas?|altavoz|parlantes|crossover|stereo|epicentro|driver de graves|set de medios|'
     r'sistema de (audio|mejora)|audio (para|de) coche|handsfree|planchas a prueba de sonido|amortiguacion de sonido',
     r'farbin', 'Autos y motos', 'Accesorios de audio para auto', AUTOS_BALDE),
    ('Autos y motos', r'\bjacks?\b|torres? (para )?auto|torre auto|torres para automovil|gato hidraulico|tijera|'
     r'wheel dolly|llave (de )?cruz|probador|\bobd|scanner|diagnostic|detector de fugas|endoscope|manometro|'
     r'extractor tipo pitman|prensa de rotulas|saca golpes|abolladuras|embudo de refrigerante|junta universal|'
     r'universal joint|air compressor|air pump', None, 'Autos y motos', 'Gatos y herramientas para auto', AUTOS_BALDE),
    ('Autos y motos', r'liquido (de|para) frenos', None, 'Autopartes', 'Frenos', AUTOS_BALDE),
    ('Autos y motos', r'headlight|headlamp|faros?\b|lampara de coche|bombillas? led|minibombillas|\bbulb|'
     r'luz reguladora|lampara led redonda', None, 'Autopartes', 'Faros y luces', AUTOS_BALDE),
    ('Autos y motos', r'radiator|condenser|turbocharger|water pump|exhaust|sensor de flujo|steering wheel switch|'
     r'ball head|grille|bumper|aleron|mounting fixed bracket|motor de caja|clips? (de|para) (coche|retencion)|'
     r'remaches|sujetadores para coche|kit de clips|surtido de clips|valvula de neumatico|tapones de valvula|'
     r'tapa de vastago', None, 'Autopartes', 'Carrocería, espejos y molduras', AUTOS_BALDE),
    ('Autos y motos', r'pulid|pulimento|ceramic|sellador|restaurador de plasticos|restauracion|shampoo|\bcera\b|'
     r'\bwash\b|lavar|lavado|hidrolavado|detalles|scuff|\bpads\b|discos de pulido|espuma colorante|'
     r'removedor de adhesivos|plumero|cepillo|guante lavar|\bfoam\b|nu finish|black restorer|tonyin|vonixx|'
     r'carbrite|raspadores de nieve', None, 'Autos y motos', 'Limpieza y cuidado del auto', AUTOS_BALDE),
    ('Autos y motos', r'aroma|aromatiz|difusor|california scents|ambientador', None,
     'Autos y motos', 'Aromatizantes para auto', AUTOS_BALDE),
    ('Autos y motos', r'sunshade|parasol|visera', None, 'Autos y motos', 'Tapetes, fundas y parasoles', AUTOS_BALDE),
    ('Autos y motos', r'toldo|carpa|roof tent|parking shed|canopy|awning', None,
     'Jardín y exterior', 'Sombrillas, toldos y carpas', AUTOS_BALDE),
    ('Autos y motos', r'basura|organizador|ganchos|monedero|bandeja|consola|reposabrazos|portaplaca|marco de matricula|'
     r'license plate|panel de toma|amarres|cinturones de seguridad|hebilla .{0,20}cinturon|revestimientos de suelo|'
     r'alfombrilla para coche|adorno|colgante|bling|pelicula', None,
     'Autos y motos', 'Accesorios para auto', AUTOS_BALDE),
    ('Autos y motos', r'cargador (auto )?bateria|cargador bateria|inverter|inversor', None,
     'Autos y motos', 'Arrancadores y cargadores de batería', AUTOS_BALDE),
    ('Autos y motos', r'fiambrera|lonchera electrica|rice cooker', None,
     'Cocina y comedor', 'Loncheras y termos para alimentos', AUTOS_BALDE),
    # ---- Sin subcategoría, tercera pasada (26-sep-2026) ----
    ('Blancos y ropa de cama', r'^(\S+ ){0,2}cortinas? (de )?(regadera|bano|ducha)|shower curtain', None,
     'Blancos y ropa de cama', 'Cortinas para baño', {None}),
    ('Blancos y ropa de cama', r'^(\S+ ){0,2}cortinas?\b', r'regadera|bano|ducha|flecos',
     'Decoración de hogar y jardín', 'Cortinas', {None}),
    ('Blancos y ropa de cama', r'^(\S+ ){0,2}(edredon|colcha|cobertor|duvet)', None,
     'Blancos y ropa de cama', 'Edredones', {None}),
    ('Blancos y ropa de cama', r'^(\S+ ){0,2}(cobija|frazada|manta)\b', r'electric', 'Blancos y ropa de cama', 'Cobijas', {None}),
    ('Blancos y ropa de cama', r'^(\S+ ){0,2}tapete', None, 'Blancos y ropa de cama', 'Tapetes de baño', {None}),
    ('Blancos y ropa de cama', r'^(\S+ ){0,2}toallas?\b', None, 'Blancos y ropa de cama', 'Toallas', {None}),
    ('Blancos y ropa de cama', r'^(\S+ ){0,2}(sabanas?|juego de sabanas)\b', None, 'Blancos y ropa de cama', 'Sábanas', {None}),
    ('Blancos y ropa de cama', r'^(\S+ ){0,2}almohadas?\b', None, 'Blancos y ropa de cama', 'Almohadas', {None}),
    ('Mascotas', r'\bgato (para|hidraulico|de patin|tipo|de botella)|prensa hidraulica|mikel|surtek|truper|urrea', None,
     'Autos y motos', 'Gatos y herramientas para auto', {None}),
    ('Mascotas', r'casa de campana', None, 'Deportes y fitness', 'Campismo', {None}),
    ('Mascotas', r'editorial|lectorum|tapa blanda|ediciones|\blibro\b|\b97[89]\d{10}\b', None,
     'Libros', 'Hogar, manualidades y mascotas', {None}),
    ('Bocinas', r'^(combo )?(pantalla|smart ?tv|televis)', None, 'Televisores',
     lambda tn: (lambda m: None if not m else '70 pulgadas o más' if int(m.group(1)) >= 70
                 else '58 a 65 pulgadas' if int(m.group(1)) >= 58 else '50 a 55 pulgadas' if int(m.group(1)) >= 50
                 else None)(re.search(r'\b(\d{2}) ?(pulgadas|")', tn)), {'Barras de sonido'}),
    # ---- Por sustantivo de arranque (26-sep-2026) ----
    ('Decoración de hogar y jardín', r'^(par de )?espejos? .{0,40}\b(19[5-9]\d|20[0-3]\d)\b|espejo lateral|retrovisor', None,
     'Autopartes', 'Carrocería, espejos y molduras'),
    ('Herramientas', r'^(par de )?(manijas?|chapas?) (de )?(puerta )?(exterior|interior)?.{0,40}\b(19[5-9]\d|20[0-3]\d)\b', None,
     'Autopartes', 'Carrocería, espejos y molduras'),
    ('Componentes y accesorios de PC', r'^condensador de enfriamiento|condensador .{0,30}\b(19[5-9]\d|20[0-3]\d)\b', None,
     'Autopartes', 'Enfriamiento y climatización'),
    ('Audífonos', r'^(combo )?smartwatch|^reloj inteligente', None, 'Relojes inteligentes', 'Smartwatches'),
    ('Electrodomésticos', r'^repuesto de lona|lona (para )?toldo', None, 'Jardín y exterior', 'Sombrillas, toldos y carpas'),
    # ---- Piezas de AUTO en subcategorías de MOTO (26-sep-2026) ----
    # Venían de la comodín «Para motos» de una tienda y de «206 cc» leído como
    # cilindrada (ver RX_AUTO_MARCA en reglas_nuevas.py).
    ('Autopartes', r'\b(chevrolet|ford|nissan|volkswagen|vw|toyota|dodge|chrysler|jeep|kia|hyundai|mazda|bmw|audi|mercedes|'
     r'gmc|mercury|lincoln|buick|cadillac|pontiac|plymouth|seat|renault|peugeot|mitsubishi|subaru|isuzu|acura|infiniti|'
     r'lexus|volvo|fiat|ram|tsuru|sentra|jetta|aveo|tiida)\b|\b[vl]\d \d\.\dl\b|\b\d\.\dl\b|\bsedan\b|\bpickup\b',
     r'\b(motos?|motocicletas?|motoneta|italika|cuatrimoto|scooter|harley|vento|dinamo|bajaj|ktm|ducati|carabela)\b',
     'Autopartes',
     lambda tn: 'Frenos' if re.search(r'freno|balata|cilindro (de )?rueda|mangueta|rondana|caliper|disco', tn)
     else 'Suspensión y dirección' if re.search(r'cubre ?polvo|macheta|flecha|homocinetica|camber|rotula|terminal|'
                                                r'horquilla|buje|varilla|flector|amortiguador|direccion|tuerca|brazo', tn)
     else 'Motor y transmisión' if re.search(r'chicote|clutch|tensor|soporte (de )?motor|banda|junta|empaque', tn)
     else 'Enfriamiento y climatización' if re.search(r'anticongelante|radiador|enfria|termostato', tn)
     else 'Faros y luces' if re.search(r'calavera|faro|cuarto|luz', tn)
     else 'Limpiaparabrisas' if re.search(r'limpiaparabrisas|pluma', tn)
     else 'Ruedas para auto' if re.search(r'\brin(es)?\b', tn)
     else 'Sistema eléctrico y sensores' if re.search(r'velocimetro|sensor|cable|switch', tn)
     else 'Carrocería, espejos y molduras' if re.search(r'espejo|moldura|manija|puerta|cubierta|tapa', tn)
     else 'Para autos',
     {'Frenos de moto', 'Cadenas, sprockets y transmisión', 'Luces de moto', 'Carenados, plásticos y tanques',
      'Motor, carburación y escape de moto', 'Eléctrico y baterías de moto', 'Manubrios, espejos y controles',
      'Suspensión y dirección de moto', 'Asientos, parrillas y accesorios de moto', 'Filtros y aceites de moto',
      'Para motos', 'Varillas para moto'}),
    ('Joyería y bisutería', r'^reloj inteligente|smartwatch', None, 'Relojes inteligentes', 'Smartwatches'),
    ('Viajes', r'^catre|campismo|casa de campana', None, 'Deportes y fitness', 'Campismo'),
    ('Autos y motos', r'^moto (sound|buds)', None, 'Audífonos', 'Earbuds inalámbricos'),
    ('Autos y motos', r'^moto watch', None, 'Relojes inteligentes', 'Smartwatches'),
    ('Autopartes', r'patinete|scooter electric|bicicleta electrica|e-?bike|monopatin', r'\bmoto',
     'Bicicletas y movilidad', lambda tn: 'Para bicicletas eléctricas' if re.search(r'bicicleta|e-?bike', tn) else 'Para patinetas eléctricas'),
    # ---- Controles remotos entre los aparatos (26-sep-2026) ----
    ('Televisores', r'^(\S+ ){0,1}control (para|remoto|universal)|^mando (para|a distancia)', r'\bcon control',
     'Televisores', 'Controles para TV'),
    ('Climatización', r'^(\S+ ){0,1}control (para|remoto|universal|minisplit|mini split)|^mando', r'\bcon control',
     'Climatización', 'Controles para aire acondicionado'),
    ('Proyectores y accesorios', r'^control (para|remoto|universal)', r'\bcon control',
     'Proyectores y accesorios', 'Controles para proyector'),
    # ---- Llantas por medida (26-sep-2026): «225/45 r17» es de auto, no de
    # camioneta; «275/35zr20 michelin pilot» es de auto, no de moto; «165/60
    # r14» no es de bicicleta. Ver MEDIDA_AUTO en subcategorias_finas_ola2.py.
    ('Autos y motos', r'llanta|neumatico', None, 'Autos y motos',
     lambda tn: ola2.sub_llanta(tn) if ola2.sub_llanta(tn) in ('Llantas para auto', 'Llantas para camioneta y SUV',
                                                              'Llantas para moto') else None,
     {'Llantas para auto', 'Llantas para camioneta y SUV', 'Llantas para moto', 'Llantas'}),
    ('Bicicletas y movilidad', r'llanta|neumatico', None, 'Autos y motos',
     lambda tn: ola2.sub_llanta(tn) if ola2.sub_llanta(tn) in ('Llantas para auto', 'Llantas para camioneta y SUV') else None,
     {'Llantas para bicicleta'}),
    # ---- Televisores por pulgadas (26-sep-2026): 129 en el tramo equivocado
    # («Pantalla hisense 75"» en 50 a 55).
    ('Televisores', r'\b\d{2} ?(pulgadas|pulg|plg|"|\'\'|”|¨)', r'^(soporte|control|base|mueble|funda|protector)',
     'Televisores',
     lambda tn: (lambda m: None if not m else (lambda x: 'Hasta 32 pulgadas' if x <= 32 else '40 a 43 pulgadas' if 40 <= x <= 43
                 else '50 a 55 pulgadas' if 50 <= x <= 55 else '58 a 65 pulgadas' if 58 <= x <= 65
                 else '70 pulgadas o más' if x >= 70 else None)(int(m.group(1))))(
         re.search(r'\b(\d{2}) ?(?:pulgadas|pulg|plg|"|\'\'|”|¨)', tn)),
     {'Hasta 32 pulgadas', '40 a 43 pulgadas', '50 a 55 pulgadas', '58 a 65 pulgadas', '70 pulgadas o más'}),
    ('Laptops', r'trampolin', None, 'Juguetes', 'Trampolines'),
]


REGLAS += [
    # «Carda copa» es un cepillo de alambre para esmeril, no una copa.
    ('Cocina y comedor', r'^carda|\bcarda (copa|circular|de alambre)', None, 'Herramientas', 'Esmeriladoras y pulidoras'),
    # Blusas con estampado de gatos no son para gatos.
    ('Mascotas', r'^(playera|blusa|sudadera|camiseta|vestido)\b.{0,60}\b(mujer|dama|hombre|unisex|nina|nino)\b', r'para (perro|gato|mascota)',
     'Ropa y accesorios', 'Blusas y tops'),
]

# ---- Libros fuera de Libros (26-sep-2026) ----
# 521 libros estaban en otras categorías porque su título nombra un objeto:
# «La historia contada en televisión» (Televisores), «El anillo del
# nibelungo» (Joyería), «El martillo de las brujas» (Herramientas). Un ISBN
# o «editorial / tapa blanda / autor» dicen que es un libro, se llame como
# se llame.
from subcategorias_finas import sub_libro_fino  # noqa: E402
_RX_LIBRO = (r'\b97[89]\d{10}\b|\beditorial\b|\btapa (blanda|dura)\b|\bpasta (blanda|dura)\b|\bautor\b|'
             r'\bediciones\b|^libro\b')
_NO_LIBRO = (r'para colorear con|cuaderno|agenda|libreta|separador|estante|atril|porta ?libros|lampara|funda|'
             r'soporte|reproductor|lector|librero|repisa|perfume|eau de|parfum|\ben blanco\b|'
             # Kits de «Running Press Mini Ediciones», tazas «collage editorial»,
             # la lotería de «Gallo Editor», el Echo Pop «Ediciones del Mundial»
             # y martillos «con tapa blanda» (26-sep-2026).
             r'running press|mini ediciones|ediciones mini|\btazas?\b|echo pop|spec ops|\bloteria\b|'
             r'martillo perforador|\bjuego de disc golf')


def _genero(tn):
    g = sub_libro_fino(tn)
    if g:
        return g
    if re.search(r'\bnin[oa]s\b|infantil|cuento|scholastic|disney|peppa|paw patrol|para colorear|bebe', tn):
        return 'Infantil'
    return 'Novela contemporánea'


try:
    _cats_manifiesto = [c['id'] for c in json.load(open(os.path.join(os.path.dirname(AQUI), 'data', 'data.json'),
                                                          encoding='utf-8'))['categories']]
except Exception:  # noqa: BLE001
    _cats_manifiesto = []
# «Cambio de luz» es el interruptor de columna del auto (Cardic, Total Parts),
# no una lámpara: 1,209 en Iluminación / Decorativa (26-sep-2026).
REGLAS += [('Iluminación', r'^cambio de luz\b', None, 'Autopartes', 'Faros y luces')]
REGLAS += [(c, _RX_LIBRO, _NO_LIBRO, 'Libros', _genero) for c in _cats_manifiesto if c != 'Libros']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--salida', required=True)
    ap.add_argument('--muestras', type=int, default=3)
    ap.add_argument('--lote', help='sólo las reglas de LOTES[nombre] (auditoría por subcategoría)')
    args = ap.parse_args()
    if args.lote == 'todos':
        reglas = [r for lote in LOTES.values() for r in lote]
    else:
        reglas = LOTES[args.lote] if args.lote else REGLAS
    data = load_catalog()
    reg = {c['id']: {s['id'] for s in (c.get('subcategories') or [])} for c in data['categories']}
    # Candado (data/clasificacion-a-mano.json): una ficha que sigue donde la
    # dejó una decisión a mano o un movimiento ya aplicado no la vuelve a
    # mover una regla. Sin esto la revisión ficha por ficha de la auditoría
    # WB se deshacía en la siguiente corrida (unos balancines de Audi S3
    # volvían a «Motor ... de moto» por una regla de motos).
    ruta_candado = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'clasificacion-a-mano.json')
    candado = json.load(open(ruta_candado, encoding='utf-8')) if os.path.exists(ruta_candado) else {}
    grupos = collections.defaultdict(list)
    muestras = collections.defaultdict(list)
    for p in data['products']:
        fijo = candado.get(p['id'])
        if fijo and fijo[0] == p.get('category') and (fijo[1] or None) == (p.get('subcategory') or None):
            continue
        tn = T(p.get('name'))
        for regla in reglas:
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


# ---- Cola sin subcategoría (26-sep-2026, tercera pasada) ----
# Lo último sin subcategoría es, casi todo, ficha en la CATEGORÍA equivocada
# porque el título nombra un animal o un vehículo: «Perro apestoso» (libro),
# aretes de gatito, rompecabezas de gatos, carritos de juguete en Autos y
# motos, «literatura» en Muebles. Sólo se tocan las que no tienen
# subcategoría (o están en «Otros»): las demás ya pasaron por su regla.
_SIN = {None}
_SIN_U_OTROS = {None, 'Otros', 'Varios'}
_EDITORIAL = (r'\b(macmillan|alfaomega|zenith|planeta|larousse|booket|tusquets|nordica libros|koral book|b4u publishing|'
              r'gato sueco|fontamara|textofilia|gustavo gili|vr editoras|diaz de santos|az editora|elefanta|'
              r'castillo a macmillan|molino|varios autores|tomo books|pearson|mcgraw hill|random house|hachette|akal|'
              r'alianza|anagrama|salamandra|sexto piso|fce|siglo xxi|urano|oceano|santillana|norma|edelvives|'
              r'kalandraka|ekare|sm ediciones|debolsillo|penguin|harpercollins|scholastic|editores?|editora)\b|'
              r', de [a-z]+ [a-z]+|, (dura|blanda)\b|\b(dura|blanda)$|/ pd\.?$')
def _genero_mascotas(tn):
    # Los libros que caían en Mascotas son, sobre todo, infantiles («Perro
    # apestoso», «Patrulla de cachorros») o de animales.
    if re.search(r'castillo|macmillan|cuento|patrulla|gato sueco|ekare|kalandraka|infantil', tn):
        return 'Infantil'
    return sub_libro_fino(tn) or 'Hogar, manualidades y mascotas'


_NO_LIB2 = _NO_LIBRO + r'|rompecabezas|peluche|llavero|arete|pendiente|taza|cerveza|\bgin\b|tamagotchi'
REGLAS += [
    ('Mascotas', _EDITORIAL, _NO_LIB2, 'Libros', _genero_mascotas, _SIN),
    ('Muebles', r'literatura|literarios|escritos|\bmesalina\b', _NO_LIB2, 'Libros', _genero, _SIN_U_OTROS),
    ('Autos y motos', _EDITORIAL, _NO_LIB2, 'Libros', _genero, _SIN),
    ('Mascotas', r'\b(aretes?|pendientes|earring(cat|dog)\d*)\b', None, 'Joyería y bisutería', 'Aretes', _SIN),
    ('Mascotas', r'\bllavero', None, 'Joyería y bisutería', 'Llaveros', _SIN),
    ('Mascotas', r'^rompecabezas', None, 'Juegos de mesa', 'Rompecabezas', _SIN),
    ('Mascotas', r'\btazas?\b', r'para (perro|gato|mascota)', 'Cocina y comedor', 'Tazas', _SIN),
    ('Mascotas', r'^(libreta|cuaderno|agenda)', None, 'Papelería y oficina', 'Libretas y agendas', _SIN),
    ('Mascotas', r'^(sacapuntas|clips|lapicera|crayones|colibrix|divisores de libros|pizarron|gomas en forma)|^ooy',
     None, 'Papelería y oficina', 'Útiles escolares', _SIN),
    ('Mascotas', r'\bcarda\b|cardina|deslanador|desenredador|peinado y autolimpieza|cortadora de mascotas|'
                 r'corte pelo canina|secador .{0,40}mascotas|aseo y cepillado|\btalco\b|colonia .{0,20}perro|'
                 r'espuma .{0,30}bano seco|antipulgas|pack higiene|refrescante de aliento|veteribac|antiseptica|'
                 r'dispensador de bolsas|bolsas para perro|baglife|alfombra sanitaria|\barena\b|bandeja esquinera|'
                 r'pill coat|bano para perros', None, 'Mascotas', 'Higiene y limpieza', _SIN),
    ('Mascotas', r'repelente|zakese|ahuyentador|entrenador|canine calm|calmante', r'moscas para caballos',
     'Mascotas', 'Adiestramiento', _SIN),
    ('Mascotas', r'\b(cachorro|adulto) \d+ ?kg|comida (para )?mascotas|maka receta|balu cachorro|alpha cachorro|'
                 r'perfect sense', r'kit', 'Mascotas', 'Alimento para perro', _SIN),
    ('Mascotas', r'botana|carnaza|golosinas|refresco para perro|pasto de trigo|mezcla para pastel', r'dispensador|camara',
     'Mascotas', 'Premios y snacks para mascotas', _SIN),
    ('Mascotas', r'vitaminas|suplemento|condroprotector|colageno|tabletas masticables|probioticos|omega ?3|omegapet|'
                 r'apoyo urinario|soporte piel|lifestages|lion.?s mane|carbodetox|dolodog|derma care|congestion nasal',
     None, 'Mascotas', 'Alimento y premios', _SIN),
    ('Mascotas', r'transportadora|carriers?\b|portabebes|bolsa de viaje .{0,30}mascotas|bolso portatil .{0,30}mascota|'
                 r'carrito (para|multiusos) .{0,20}mascotas|caja p/mascotas', None, 'Mascotas', 'Transportadoras', _SIN),
    ('Mascotas', r'mueble .{0,15}gato|mueble para gato|kitty sill', None, 'Mascotas', 'Rascadores y torres', _SIN),
    ('Mascotas', r'cat bed|tent igloo|soft mat|\bcama\b', None, 'Mascotas', 'Camas', _SIN),
    ('Mascotas', r'filtros? .{0,30}fuentes?|fuentes carbon|despachador de agua', None,
     'Mascotas', 'Fuentes y dispensadores de agua', _SIN),
    ('Mascotas', r'cable de amarre|estaca para', None, 'Mascotas', 'Correas', _SIN),
    ('Mascotas', r'mordedera .{0,20}perro|trixie|bola .{0,20}perro|chupete para perro|lickimat|flotadores para perros|'
                 r'juguete', r'kidz|musical', 'Mascotas', 'Juguetes para perro', _SIN),
    ('Mascotas', r'lactancia|pezon de lactancia', None, 'Mascotas', 'Comederos', _SIN),
    ('Mascotas', r'doggie door', None, 'Mascotas', 'Puertas para mascotas', _SIN),
    ('Mascotas', r'etiquetas identificacion', None, 'Mascotas', 'Collares para mascotas', _SIN),
    ('Mascotas', r'camisas .{0,20}perros', None, 'Mascotas', 'Ropa para mascotas', _SIN),
    ('Mascotas', r'escalera (redlemon )?para perro|soporte triangular para perros|silla de coche elevadora|barreras para perros',
     None, 'Mascotas', 'Corrales y rejas para mascotas', _SIN),
    ('Mascotas', r'bascula (veterinaria|digital)', None, 'Mascotas', 'Higiene y limpieza', _SIN),
    ('Mascotas', r'peluche|lamaze|\bgund\b|aurora world|pelucheria|titi 15 cm', r'para perro', 'Juguetes', 'Peluches', _SIN),
    ('Mascotas', r'play-?doh|set de juego|melissa & doug|set veterinario|set mascota play|shinymals|l\.o\.l|tamagotchi',
     None, 'Juguetes', 'Juguetes educativos', _SIN),
    ('Mascotas', r'^vehiculo', None, 'Juguetes', 'Vehículos de juguete', _SIN),
    ('Mascotas', r'^gato (automotriz|botella|hidraulico)', None, 'Autos y motos', 'Gatos hidráulicos para auto', _SIN),
    ('Mascotas', r'escultura|estatua|adorno para mesa|velas en forma|portallaves|alcancia|imanes', None,
     'Decoración de hogar y jardín', 'Figuras y adornos', _SIN),
    ('Mascotas', r'^inflable .{0,20}(halloween|navidad)', None, 'Decoración de hogar y jardín', 'Navidad y temporada', _SIN),
    ('Mascotas', r'vinil decorativo', None, 'Decoración de hogar y jardín', 'Vinil decorativo', _SIN),
    ('Mascotas', r'^(set \d+ bolsas|cartera|monedero)', None, 'Bolsas y mochilas', 'Carteras y monederos', _SIN),
    ('Mascotas', r'^(diadema|donas de pelo)', None, 'Belleza y cuidado personal', 'Cuidado del cabello', _SIN),
    # Autos y motos sin subcategoría
    ('Autos y motos', r'^(\S+ ){0,2}llantas?\d', r'bicicleta|carretilla|moto\b|motocicleta', 'Autos y motos',
     lambda tn: ola2._auto_o_camioneta(re.sub(r'(llantas?)(\d)', r'\1 \2', tn), 'Llantas para auto'), _SIN),
    ('Autos y motos', r'^vehiculos?\b|batimovil|bburago|hot ?wheels|camion de bomberos', r'emergencia|torreta',
     'Juguetes', 'Vehículos de juguete', _SIN),
    ('Autos y motos', r'altavo(z|ces)|alta voz|set de medios|\bmedios? rango', None, 'Autos y motos',
     'Bocinas para auto', _SIN),
    ('Autos y motos', r'meguiar|cera liquida|pulido|removedor de oxidacion|shampoo para auto', None, 'Autos y motos',
     'Limpieza y cuidado del auto', _SIN),
    ('Autos y motos', r'^llavero', None, 'Joyería y bisutería', 'Llaveros', _SIN),
    ('Autos y motos', r'compresor|inflador', None, 'Autos y motos', 'Compresores e infladores', _SIN),
    ('Autos y motos', r'^pulidora', None, 'Herramientas', 'Esmeriladoras y pulidoras', _SIN),
    ('Autos y motos', r'^lona\b', None, 'Herramientas', 'Construcción', _SIN),
    ('Autos y motos', r'torreta|estrobo', None, 'Autos y motos', 'Luces LED para auto', _SIN),
    ('Autos y motos', r'pintura en aerosol', None, 'Autos y motos', 'Limpieza y cuidado del auto', _SIN),
    # Muebles «Otros»
    ('Muebles', r'^espejo', None, 'Decoración de hogar y jardín', 'Espejos decorativos de pared', _SIN_U_OTROS),
    ('Muebles', r'^piso autoadhesivo', None, 'Herramientas', 'Construcción', _SIN_U_OTROS),
    ('Muebles', r'carro de bar', None, 'Muebles', 'Mesas de cama y con ruedas', _SIN_U_OTROS),
    ('Muebles', r'baul|caja de almacenamiento|organizacion plegable', r'guillotina', 'Muebles', 'Repisas', _SIN_U_OTROS),
    ('Muebles', r'comoda', r'mujer|hombre|sudadera|filipina|pantalon|blusa|playera', 'Muebles', 'Cómodas y cajoneras', _SIN_U_OTROS),
    ('Muebles', r'casillero|locker', None, 'Muebles', 'Roperos', _SIN_U_OTROS),
    ('Muebles', r'mesa ?decorativa|mesa auxiliar', None, 'Muebles', 'Mesas auxiliares y laterales', _SIN_U_OTROS),
    ('Muebles', r'banqueta', None, 'Muebles', 'Taburetes y bancos', _SIN_U_OTROS),
    # Belleza sin subcategoría
    ('Belleza y cuidado personal', r'^(\d+ )?(pcs |piezas |paquete \d+ )?(mini )?pinzas? (para|de) (cabello|metal)|pinza para cabello|'
     r'pinzas para cabello', None, 'Belleza y cuidado personal', 'Cuidado del cabello', _SIN),
    ('Belleza y cuidado personal', r'pestanas', None, 'Belleza y cuidado personal', 'Pestañas postizas', _SIN),
    ('Belleza y cuidado personal', r'^acondi?cionador', None, 'Belleza y cuidado personal', 'Acondicionadores', _SIN),
    ('Belleza y cuidado personal', r'\bsuero\b', None, 'Belleza y cuidado personal', 'Sérums faciales', _SIN),
    ('Belleza y cuidado personal', r'aceite esencial', None, 'Belleza y cuidado personal',
     'Aceites esenciales y de masaje', _SIN),
    ('Belleza y cuidado personal', r'recortadora|clipper', None, 'Belleza y cuidado personal', 'Cortadoras de cabello', _SIN),
    ('Belleza y cuidado personal', r'leave in|tratamiento reparador|vitamino color', None, 'Belleza y cuidado personal',
     'Tratamientos y mascarillas capilares', _SIN),
    ('Belleza y cuidado personal', r'toalla de microfibra|hair towel', None, 'Belleza y cuidado personal',
     'Cuidado del cabello', _SIN),
    ('Belleza y cuidado personal', r'electrolitos', None, 'Suplementos', 'Electrolitos y minerales', _SIN),
    ('Belleza y cuidado personal', r'^marcadores', None, 'Papelería y oficina', 'Arte y dibujo', _SIN),
    ('Belleza y cuidado personal', r'^mascara .{0,40}halloween', None, 'Juguetes', 'Disfraces', _SIN),
    ('Belleza y cuidado personal', r'cejas', None, 'Belleza y cuidado personal', 'Máscaras de pestañas y cejas', _SIN),
    # Suplementos sin subcategoría: la función fina ya existente, y los arneses
    # «suplementarios» de Italika son autoparte de moto.
    ('Suplementos', r'arnes suplementario', None, 'Autopartes', 'Eléctrico y baterías de moto', _SIN),
    ('Suplementos', r'.', None, 'Suplementos',
     lambda tn: sub_suplemento_fino(tn) or ('Herbolaria y superalimentos' if re.search(
         r'raiz|hierba|herbal|extracto|semilla|hawthorn|vitex|chaste|melon|clorofila|spirulina|ganoderma|maitake|'
         r'mushroom|hongos|oregano|malvavisco|solanum|carbon (vegetal|activado)|shilajit', tn) else None), _SIN),
    # Libros sin subcategoría: género por título; si no se sabe, novela.
    ('Libros', r'.', None, 'Libros', _genero, _SIN),
    # Juguetes sin subcategoría
    ('Juguetes', r'^vehiculos?|^auto\b|^carro\b|^pista', None, 'Juguetes', 'Vehículos de juguete', _SIN),
    ('Juguetes', r'^figura', None, 'Juguetes', 'Figuras de acción', _SIN),
    # Iluminación sin subcategoría
    ('Iluminación', r'^lamparas? (de )?(techo|colgante)', None, 'Iluminación', 'Lámparas colgantes', _SIN),
    ('Iluminación', r'^proyector', None, 'Iluminación', 'Proyectores de luz y efectos', _SIN),
    ('Iluminación', r'^lamparas? solar', None, 'Iluminación', 'Lámparas solares', _SIN),
    ('Iluminación', r'faroles?', None, 'Iluminación', 'Decorativa', _SIN),
    ('Iluminación', r'^focos?\b', None, 'Iluminación', 'Focos', _SIN),
    # Cámaras sin subcategoría: casi todas son cámaras de vigilancia.
    ('Cámaras y fotografía', r'^camara .{0,60}(seguridad|vigilancia|wifi|ip\b|espia|bombilla|foco|exterior|interior)',
     None, 'Cámaras de seguridad',
     lambda tn: ('Cámaras espía' if 'espia' in tn else 'Cámaras PTZ' if re.search(r'\bptz\b', tn)
                 else 'Cámaras exteriores' if re.search(r'exterior|intemperie|solar|\bbala\b', tn) else 'Cámaras interiores'),
     _SIN),
]

# ---- Errores sistemáticos de la muestra de 100 (26-sep-2026) ----
# De 10,639 fichas que el modelo marca, a mano: 43/100 mal puestas. Las
# familias que se repiten van por regla (el modelo solo acierta el destino
# ~30% de las veces, así que no se le hace caso a ciegas).
def _tenis(tn):
    if re.search(r'^botas?\b|botas? de combate', tn):
        return 'Botas'
    if re.search(r'bebe|\bninos?\b|\bninas?\b|infantil|12-21|\bjr\b|\binf\b|\bk\b', tn):
        return 'Tenis para niños'
    if re.search(r'\bmujer\b|\bdama\b', tn):
        return 'Tenis para mujer'
    if re.search(r'\bhombre\b|caballero', tn):
        return 'Tenis para hombre'
    return 'Tenis'


_MOTO_MARCAS = r'bajaj|pulsar|vento|italika|\bdm ?\d{3}|\bft ?\d{3}|yamaha|suzuki gn|\bmoto\b|motocicleta|\bcc\b|screamer'
_ESPEJO_AUTO = (r'^(\(\d+\) )?(par de |juego |set )?espejos?\b.{0,80}\b(izq|der|izquierdo|derecho|piloto|pasajero|'
                r's/control|c/control|electrico|manual|retrovisor|lateral)\b|^espejo generica|^juego espejos')
REGLAS += [
    ('Deportes y fitness', r'^(tacos|taquetes|tachon(es)?|tachos?)\b|^pirma brasil', None,
     'Deportes y fitness', 'Tachones de fútbol'),
    ('Deportes y fitness', r'^(tenis|calzado|botas? de combate)\b|bubble gummers.{0,20}tenis|^tenis ',
     r'raqueta|pelota|mesa|\bred\b|bola', 'Calzado', _tenis),
    ('Deportes y fitness', r'^mochila\b', r'bebe|cabeza', 'Bolsas y mochilas', 'Mochilas'),
    ('Decoración de hogar y jardín', _ESPEJO_AUTO, r'bano|tocador|maquillaje|cuerpo completo|pared|bebe',
     'Autopartes', lambda tn: 'Manubrios, espejos y controles' if re.search(_MOTO_MARCAS, tn)
     else 'Carrocería, espejos y molduras'),
    ('Refrigeradores', r'palanca|bomba de agua|linea de agua|\bpin de|arnes|valvula|pestillo|empaque|termostato|'
                       r'repuesto|refaccion|bisagra|\boem\b|protector de (sobretension|voltaje)|marco magnetico|'
                       r'para (puerta de )?refrigerador',
     r'^refrigerador(?!.*(palanca|valvula|pestillo))|mini nevera|frigobar', 'Electrodomésticos', 'Filtros para refrigerador y cafetera'),
    ('Refrigeradores', r'bloques? de hielo|paquete de hielo|hielo reutilizable', None, 'Cocina y comedor',
     'Loncheras y termos para alimentos'),
    ('Refrigeradores', r'mini nevera|nevera compacta|frigobar|mini refrigerador', None, 'Refrigeradores', 'Frigobares',
     {'Top mount', 'Bottom freezer', 'Una puerta'}),
    ('Proyectores y accesorios', r'proyector (de |led )?(logotipos?|luz|estrellas|nebulosa|historias|figuras|galaxia|aurora)|'
                                 r'star shower|lampara de estrellas|\bgobo\b|moonlite|storytime|frases intercambiables|'
                                 r'con proyector (nebulosa|de estrellas)|puntero laser|proyector navideno',
     r'video|hdmi|1080|4k|lumenes ansi|wifi', 'Iluminación', 'Proyectores de luz y efectos'),
    ('Joyería y bisutería', r'anillos? para cortinas', None, 'Decoración de hogar y jardín', 'Cortinas'),
    ('Joyería y bisutería', r'opresor de anillos|juego de anillos de cobre|para anillos de cobre|remache y anillo|tuberia pex', None,
     'Herramientas', 'Herramientas manuales'),
    ('Joyería y bisutería', r'anillos? para moto', None, 'Autopartes', 'Motor, carburación y escape de moto'),
    ('Joyería y bisutería', r'anillos? para pestanas', None, 'Belleza y cuidado personal', 'Pestañas postizas'),
    ('Joyería y bisutería', r'anillo de cocina', None, 'Cocina y comedor', 'Utensilios de cocina'),
    ('Laptops', r'^(computadora|pc|completo|cpu)\b.{0,80}\bmonitor\b|^pc (intel|amd)', r'para laptop|funda|mochila',
     'Computadoras de escritorio', 'Torres de casa y oficina'),
    ('Celulares', r'lenovo m\d{3}|thinkcentre|optiplex|elitedesk|prodesk', None,
     'Computadoras de escritorio', 'Reacondicionadas'),
    ('Juguetes', r'roman fashion', None, 'Ropa y accesorios',
     lambda tn: 'Pantalones y jeans' if re.search(r'pants|pantalon|jogger', tn) else 'Chamarras y suéteres'),
]

# ---- Libros de Walmart/Bodega por editorial (26-sep-2026) ----
# Walmart escribe el libro con la editorial pegada al título y sin «libro»:
# «Cien años de soledad diana mexico gabriel garcia marquez». El clasificador
# leía la palabra suelta: «diana» -> tableros de dardos (264 libros), «luz»
# -> Iluminación, «perfume» -> Perfumes, «anillos» -> Joyería. Una editorial
# conocida en el título dice que es un libro.
_EDITORIAL_FUERTE = (r'\b(booket|seix barral|alfaguara|debolsillo|trillas|paraninfo|gedisa|picarona|leetra|vr editoras|'
                     r'anagrama|tusquets( editores)?|grijalbo|random house|paidos|paidotribo|libro de bolsillo|'
                     r'1ra edicion|planeta (mexico|mexicana|junior|infantil|comic|de libros)|hachette literatura|'
                     r'diana mexico|editorial (diana|oceano|porrua|critica|planeta)|castillo a macmillan|montena|'
                     r'nube de tinta|panini manga|ivrea|kamite|fondo de cultura economica|siglo xxi editores|'
                     r'ediciones sm|kalandraka|ekare|limusa|titania libro|martinez roca|bonilla artigas|a buen paso|'
                     r'silver dolphin|pikids)\b|/ pd\.?$')
_NO_LIBRO_PRODUCTO = (r'\b(led|luces|focos?|sabanas?|funda|peluche|rompecabezas|juguete|croqueta|alimento|termo|'
                      r'set de|cable|bocina|audifonos|tenis|playera)\b|\d+ ?(cm|ml|w|pzas?|piezas|kg)\b')
REGLAS += [(c, _EDITORIAL_FUERTE, _NO_LIBRO_PRODUCTO, 'Libros', _genero) for c in _cats_manifiesto if c != 'Libros']
def _genero_diana(tn):
    # Diana es, sobre todo, sello de autoayuda (y el de García Márquez en México).
    if 'garcia marquez' in tn:
        return 'Clásicos'
    return sub_libro_fino(tn) or 'Autoayuda y desarrollo personal'


REGLAS += [('Deportes y fitness', r'^(buro|portaluna)\b', None, 'Muebles',
            lambda tn: 'Burós' if tn.startswith('buro') else 'Tocadores'),
           ('Deportes y fitness', r'.\bdiana( mexico| planeta)? [a-z]|, diana\b|^diana princesa',
            r'dardos?|tablero|electronica|diana de|tiro|^(paquete|cuadro|arco)\b|nuez$', 'Libros', _genero_diana)]

# ---- Walmart/Bodega: familias mal puestas de la muestra de 400 (26-sep-2026) ----
REGLAS += [
    # «Acuario» es una marca de impermeabilizante: 353 cubetas en Mascotas.
    ('Mascotas', r'impermeabilizante|acriterm|acuaflex|^pintura|sellador|^cubeta', None, 'Herramientas', 'Construcción'),
    # Disfraces de Disfraces Tudi y compañía en Bloques de construcción y Muñecas.
    ('Juguetes', r'^disfra(z|ces)\b|disfraces tudi|\bt\d disfraces\b|- disfraz de', r'peluche|muneca|figura|con disfraz',
     'Juguetes', 'Disfraces'),
    ('Ropa y accesorios', r'^disfra(z|ces)\b|disfraces tudi', None, 'Juguetes', 'Disfraces'),
    ('Autos y motos', r'liquido de frenos', None, 'Autopartes', 'Frenos'),
    ('Laptops', r'^procesador (intel|amd)|^procesador de escritorio', None, 'Componentes y accesorios de PC', 'Procesadores'),
    ('Celulares', r'^procesador (intel|amd)', None, 'Componentes y accesorios de PC', 'Procesadores'),
    ('Muebles', r'silla (de )?(ruedas|electrica|para ducha|de traslado|emergencia)|stairpro|freno de silla de ruedas',
     None, 'Salud', 'Movilidad y apoyo'),
    ('Muebles', r'^(colchon(eta)?|alfombrilla|almohada|masajeador)\b.{0,50}masaj', r'sillon|reposet|silla|base de cama|cama electrica',
     'Belleza y cuidado personal', 'Masajeadores'),
]

# ---- Auditoría de Walmart/Bodega por subcategoría, lote 1 (26-sep-2026) ----
# auditar_subcategorias_tienda.py: fichas cuya palabra de arranque es rara en
# su subcategoría. De los primeros 110 grupos revisados a mano, estos son los
# errores de verdad (el resto, p. ej. «Base para faro» en Faros, está bien).
_AP_TODAS = None
LOTES['wb1'] = [
    # Autopartes en subcategorías «sumidero» (Bujías y encendido, Enfriamiento,
    # Carenados de moto) por el reparto fino.
    ('Autopartes', r'^(\d+ )?rin(es)?\b', r'tambor|\bmoto|vento|italika|nitrox|ryder|honda (gl|cg)|\b[1-3]\.\d+ ?x ?1[78]\b',
     'Autos y motos', 'Rines'),
    ('Autopartes', r'^(\d+-)?porta ?diodos', None, 'Autopartes', 'Alternadores y marchas',
     {s for s in ['Enfriamiento y climatización', 'Bujías y encendido', 'Sistema eléctrico y sensores']}),
    ('Autopartes', r'^gomas? (de )?(varilla|barra) estabilizadora', None, 'Autopartes', 'Bujes y gomas de suspensión',
     {'Enfriamiento y climatización', 'Bujías y encendido', 'Motor y transmisión'}),
    ('Autopartes', r'^cubre ?polvos?\b.{0,60}(lado caja|lado rueda|flecha|homocinetica)', None, 'Autopartes',
     'Flechas y juntas homocinéticas', {'Enfriamiento y climatización', 'Bujías y encendido', 'Motor y transmisión',
                                        'Faros y luces'}),
    ('Autopartes', r'sellos? del tubo (de )?aire acondicionado', None, 'Autopartes', 'Enfriamiento y climatización',
     {'Bujías y encendido', 'Motor y transmisión'}),
    ('Autopartes', r'^tolva', r'\bmoto\b|italika|vort', 'Autopartes', 'Tolvas, salpicaderas y loderas',
     {'Carenados, plásticos y tanques'}),
    ('Autopartes', r'^rejilla defensa|^anti ?impacto', r'\bmoto\b|italika', 'Autopartes', 'Defensas, fascias y parrillas',
     {'Carenados, plásticos y tanques'}),
    ('Autopartes', r'^pinon \(?vvt|^solenoide (de )?(tiempo variable|vvt)', None, 'Autopartes',
     'Válvulas, punterías y árbol de levas', {'Bujías y encendido', 'Enfriamiento y climatización', 'Para autos', 'Motor y transmisión'}),
    ('Autopartes', r'^engrane de arbol|^guia de tiempo|^componentes de tiempo', None, 'Autopartes',
     'Cadenas y kits de distribución', {'Enfriamiento y climatización', 'Poleas y tensores', 'Bujías y encendido'}),
    ('Autopartes', r'^regulador (de )?presion (de )?combustible', None, 'Autopartes', 'Inyectores y carburadores',
     {'Filtros y aceites'}),
    ('Autopartes', r'^brazo (de )?(control|lateral|tensor)', None, 'Autopartes', 'Horquillas y brazos de suspensión',
     {'Faros y luces', 'Enfriamiento y climatización', 'Bujías y encendido', 'Frenos'}),
    ('Autopartes', r'^tapa batea|^tapon oem de panel de piso', None, 'Autopartes', 'Carrocería, espejos y molduras',
     {'Faros y luces', 'Bujías y encendido'}),
    ('Autopartes', r'^placa (para )?ajuste de caster', None, 'Autopartes', 'Suspensión y dirección', {'Frenos'}),
    ('Autopartes', r'^soporte para motor \d+ ?(lb|kg|ton)', None, 'Autos y motos', 'Gatos y herramientas para auto'),
    ('Autopartes', r'^(\d+-)?resistencia\b', r'bomba|gasolina|combustible', 'Autopartes', 'Enfriamiento y climatización',
     {'Bujías y encendido'}),
    ('Autos y motos', r'cerraduras? .{0,40}\bmoto', r'cadena|antirrobo|bicicleta', 'Autopartes', 'Eléctrico y baterías de moto', {'Motocicletas'}),
    # Muebles
    ('Muebles', r'^cabecera\b', None, 'Muebles', 'Cabeceras',
     {'Colchones king size', 'Colchones queen size', 'Colchones matrimoniales', 'Colchones individuales', 'Colchones',
      'Bases de cama y box'}),
    ('Muebles', r'^base,? (matrimonial|queen|king|individual)|^base box', None, 'Muebles', 'Bases de cama y box',
     {'Colchones king size', 'Colchones queen size', 'Colchones matrimoniales', 'Colchones individuales', 'Colchones'}),
    ('Muebles', r'^(set de \d+ )?bancos?\b', None, 'Muebles', 'Taburetes y bancos', {'Sillas de comedor'}),
    ('Muebles', r'^tapete', None, 'Decoración de hogar y jardín', 'Tapetes y alfombras', {'Sillas de comedor'}),
    ('Muebles', r'^mantel', None, 'Cocina y comedor', 'Manteles y caminos de mesa', {'Mesas de centro', 'Mesas de comedor'}),
    ('Muebles', r'^cesto', None, 'Muebles', 'Organizadores y almacenamiento', {'Roperos'}),
    # Belleza
    ('Belleza y cuidado personal', r'^balsamo labial', None, 'Belleza y cuidado personal', 'Bálsamos labiales',
     {'Protección solar', 'Cremas y sérums faciales'}),
    ('Belleza y cuidado personal', r'^acondicionador', None, 'Belleza y cuidado personal', 'Acondicionadores',
     {'Cremas y sérums faciales'}),
    ('Belleza y cuidado personal', r'^vela', None, 'Limpieza y hogar', 'Aromatizantes y velas', {'Corporales'}),
    ('Relojes inteligentes', r'^banda\b|^correa', None, 'Relojes inteligentes', 'Correas y extensibles', {'Smartwatches'}),
    # Iluminación
    ('Iluminación', r'^espejo', None, 'Decoración de hogar y jardín',
     lambda tn: 'Espejos de baño con luz' if re.search(r'\bbano\b|touch|dimmer|\d{2} ?cm', tn) else 'Espejos de tocador y maquillaje',
     {'Decorativa'}),
    ('Iluminación', r'^\d* ?faros? tipo barra|estrobo', None, 'Autos y motos', 'Luces LED para auto', {'Focos'}),
    ('Iluminación', r'^reflector', None, 'Iluminación', 'Reflectores', {'Focos'}),
    ('Electrodomésticos', r'^sarten', None, 'Cocina y comedor', 'Sartenes y comales', {'Wafleras, sandwicheras y creperas'}),
    # Herramientas
    ('Herramientas', r'^(\d+ ?pzs )?(juego de )?dados?\b', None, 'Herramientas', 'Dados, matracas y autocles', {'Juegos de herramientas'}),
    ('Herramientas', r'^generador', None, 'Herramientas', 'Generadores', {'Jardinería'}),
    ('Herramientas', r'^podadora', None, 'Herramientas', 'Podadoras y cortacésped', {'Jardinería'}),
    ('Herramientas', r'^multicontacto', None, 'Cargadores y adaptadores', 'Regletas y multicontactos',
     {'Apagadores y contactos'}),
    # Otros
    ('Joyería y bisutería', r'^pulsera', None, 'Joyería y bisutería', 'Pulseras', {'Collares'}),
    ('Juegos de mesa', r'^tapete', r'porta rompecabezas', 'Bebés', 'Juguetes para bebé', {'Rompecabezas'}),
    ('Juguetes', r'^sandalia', None, 'Calzado', 'Sandalias', {'Muñecas'}),
    ('Juguetes', r'loungefly|mini backpack', None, 'Bolsas y mochilas',
     lambda tn: 'Carteras y monederos' if 'wallet' in tn else 'Cangureras y bolsos cruzados' if 'crossbody' in tn else 'Mochilas',
     {'Figuras de acción'}),
    ('Mascotas', r'^placa de identificacion', None, 'Mascotas', 'Collares para mascotas', {'Ropa para mascotas'}),
    ('Bocinas', r'^subwoofer', None, 'Bocinas', 'Subwoofers', {'Bafles y audio profesional'}),
]
REGLAS += LOTES['wb1']

# ---- Auditoría WB, lote 2 (26-sep-2026): grupos 0-130 de la segunda vuelta ----
_MOTO_SUB = {'Motor, carburación y escape de moto', 'Suspensión y dirección de moto', 'Carenados, plásticos y tanques'}
LOTES['wb2'] = [
    ('Autopartes', r'^tapon (de )?(bloque|carter)', None, 'Autopartes', 'Tapones, cárter y tapas de motor',
     {'Bujías y encendido', 'Motor y transmisión'}),
    ('Autopartes', r'^soporte (de )?goma de escape', None, 'Autopartes', 'Escape', {'Enfriamiento y climatización'}),
    ('Autopartes', r'^bases? de amortiguador', r'\bmoto\b|italika', 'Autopartes', 'Bases y cubrepolvos de amortiguador', _MOTO_SUB),
    ('Autopartes', r'^soporte (de )?motor', r'\bmoto\b|italika|\bcc\b', 'Autopartes', 'Soportes de motor y transmisión', _MOTO_SUB),
    ('Autopartes', r'^soporte (de )?cabina', None, 'Autopartes', 'Soportes de motor y transmisión', {'Motor y transmisión'}),
    ('Autopartes', r'^deposito (de )?anticongelante', None, 'Autopartes', 'Depósitos de anticongelante', {'Motor y transmisión'}),
    ('Autopartes', r'^tubo (de )?calefaccion|^manguera (de )?calefaccion', None, 'Autopartes', 'Mangueras y tubos de enfriamiento',
     {'Motor y transmisión'}),
    ('Autopartes', r'^toma (conector )?(de )?(calefaccion|agua)', None, 'Autopartes', 'Tomas de agua y termostatos',
     {'Motor y transmisión'}),
    # Refacciones de moto en «Motocicletas» (la moto entera)
    ('Autos y motos', r'^(manija|palanca) (de )?(clutch|freno)', None, 'Autopartes', 'Manubrios, espejos y controles', {'Motocicletas'}),
    ('Autos y motos', r'^porta ?placa', None, 'Autopartes', 'Carenados, plásticos y tanques', {'Motocicletas'}),
    ('Autos y motos', r'^retene?s?\b', None, 'Autopartes',
     lambda tn: 'Motor, carburación y escape de moto' if 'motor' in tn else 'Suspensión y dirección de moto', {'Motocicletas'}),
    ('Autos y motos', r'^jersey', None, 'Autos y motos', 'Ropa para motociclista', {'Motocicletas'}),
    ('Iluminación', r'^faros? led .{0,40}(diurna|auto|coche)|ledriving', None, 'Autos y motos', 'Luces LED para auto', {'Focos'}),
    ('Iluminación', r'^tubo led', None, 'Iluminación', 'Tubos LED y fluorescentes', {'Plafones y lámparas de sobreponer'}),
    ('Iluminación', r'^lentes? lupa .{0,40}pestanas', None, 'Belleza y cuidado personal', 'Pestañas postizas', {'Decorativa'}),
    # Herramientas
    ('Herramientas', r'^tubo poliducto', None, 'Herramientas', 'Material eléctrico', {'Llaves y dados'}),
    ('Herramientas', r'^brocha', None, 'Herramientas', 'Construcción', {'Desarmadores y puntas'}),
    ('Herramientas', r'^pijas?\b', None, 'Herramientas', 'Construcción', {'Brocas'}),
    ('Herramientas', r'^cadena (galvanizada|de acero|grado)', None, 'Herramientas', 'Construcción', {'Jardinería'}),
    ('Herramientas', r'^bandas? (de )?lija', None, 'Herramientas', 'Lijas y accesorios de lijado', {'Lijadoras'}),
    # Muebles
    ('Muebles', r'^cajonera', r'\bburos?\b', 'Muebles', 'Cómodas y cajoneras', {'Sillas de comedor', 'Mesas de comedor'}),
    ('Muebles', r'^(set de \d+ )?buros?\b', None, 'Muebles', 'Burós', {'Sillas de comedor'}),
    ('Muebles', r'^love[ -]?(seat|chaise)', None, 'Muebles', 'Love seats', {'Sofás seccionales y esquineros', 'Sillones y reclinables'}),
    ('Muebles', r'^sala \d', None, 'Muebles', 'Salas completas', {'Taburetes y bancos'}),
    ('Muebles', r'^box (queen|king|matrimonial|individual)', None, 'Muebles', 'Bases de cama y box',
     {'Colchones king size', 'Colchones queen size', 'Colchones matrimoniales', 'Colchones individuales'}),
    ('Muebles', r'^soporte (para )?laptop', None, 'Muebles', 'Accesorios y organizadores de escritorio', {'Sillas de oficina'}),
    # Otros
    ('Computadoras de escritorio', r'^disipador', None, 'Componentes y accesorios de PC', 'Disipadores de CPU', {'PC gamer'}),
    ('Deportes y fitness', r'^porteria', None, 'Deportes y fitness', 'Porterías y redes de fútbol', {'Balones de fútbol'}),
    ('Bebés', r'^triciclo', None, 'Juguetes', 'Triciclos', {'Carriolas'}),
    ('Juguetes', r'^cuatrimoto a gasolina', None, 'Autos y motos', 'Cuatrimotos', {'Montables'}),
    ('Juguetes', r'^pop keychain', None, 'Juguetes', 'Funko y coleccionables', {'Figuras de acción'}),
    ('Cocina y comedor', r'^molde', None, 'Cocina y comedor', 'Repostería y moldes', {'Sartenes y comales'}),
    ('Belleza y cuidado personal', r'^sombra', None, 'Belleza y cuidado personal', 'Sombras y delineadores', {'Bases y correctores'}),
    ('Belleza y cuidado personal', r'^iluminador', None, 'Belleza y cuidado personal', 'Polvos, rubores y bronceadores',
     {'Bases y correctores'}),
    ('Belleza y cuidado personal', r'^tonico de aseo|hair tonic|grooming tonic', None, 'Belleza y cuidado personal',
     'Cuidado del cabello', {'Cremas y sérums faciales'}),
    ('Audífonos', r'^tapones? (para )?(los )?oidos', None, 'Salud', 'Salud'),
]
REGLAS += LOTES['wb2']

# ---- Auditoría WB, lote 3 (26-sep-2026): grupos 100-370 de la tercera vuelta ----
# «Vento» es marca de motos Y el sedán de Volkswagen: las piezas del Vento de
# VW (tensor, depósito, cofre, terminal, moldura) caían en subcategorías de
# moto. Se reconocen por «volkswagen», el motor («l4 1.6l») o la marca de la
# pieza de auto (tong yang, syd, dai, depo, k-nadian).
_AUTO_NO_MOTO = r'volkswagen|\bl4\b|\bv6\b|tong yang|\bsyd\b|\bdai\b|\bdepo\b|k-?nadian|soportes star|generica'
_SUB_MOTO = {'Motor, carburación y escape de moto', 'Suspensión y dirección de moto', 'Carenados, plásticos y tanques',
             'Luces de moto'}
_AP_SUMIDERO = {'Bujías y encendido', 'Enfriamiento y climatización', 'Motor y transmisión', 'Frenos', 'Faros y luces',
                'Para autos', 'Sistema eléctrico y sensores', 'Suspensión y dirección'}
LOTES['wb3'] = [
    # extensiones de los lotes 1 y 2
    ('Autopartes', r'^solenoide (de )?(tiempo variable|vvt)|^pinon (walker )?\(?vvt', None, 'Autopartes',
     'Válvulas, punterías y árbol de levas', _AP_SUMIDERO),
    ('Autopartes', r'^(par de |juego de )?cubre ?polvos?\b.{0,60}(lado caja|lado rueda|flecha|homocinetica)', None,
     'Autopartes', 'Flechas y juntas homocinéticas', _AP_SUMIDERO),
    ('Autopartes', r'^cubre ?polvos? macheta .{0,20}direccion', None, 'Autopartes', 'Coples, varillas y cajas de dirección',
     _AP_SUMIDERO),
    ('Autopartes', r'^junta lado rueda', None, 'Autopartes', 'Flechas y juntas homocinéticas', _AP_SUMIDERO),
    ('Autopartes', r'^anti ?impacto', r'\bmoto\b|italika', 'Autopartes', 'Defensas, fascias y parrillas', _AP_SUMIDERO),
    ('Autopartes', r'^bases? (de )?amortiguador', r'\bmoto\b|italika', 'Autopartes', 'Bases y cubrepolvos de amortiguador',
     _SUB_MOTO),
    ('Autopartes', r'^toma (de )?agua', None, 'Autopartes', 'Tomas de agua y termostatos', _AP_SUMIDERO),
    ('Autopartes', r'^(1-)?regulador\b', r'presion|combustible|gasolina', 'Autopartes', 'Alternadores y marchas',
     {'Motor y transmisión', 'Bujías y encendido', 'Sistema eléctrico y sensores'}),
    ('Autopartes', r'^soporte (de )?aire acondicionado', None, 'Autopartes', 'Enfriamiento y climatización',
     {'Motor y transmisión', 'Bujías y encendido'}),
    ('Autopartes', r'^cubre ?pedales', None, 'Autopartes', 'Interior y tapicería', _AP_SUMIDERO),
    ('Autopartes', r'^soporte (de )?barra (tensora|de torsion|torsion|estabilizadora)', None, 'Autopartes',
     'Suspensión y dirección', _AP_SUMIDERO - {'Suspensión y dirección'}),
    ('Autopartes', r'^goma (de )?multiple', None, 'Autopartes', 'Empaques, juntas y retenes', _AP_SUMIDERO),
    ('Autopartes', r'^mazas?\b', None, 'Autopartes', 'Baleros y mazas de rueda', _AP_SUMIDERO),
    ('Autopartes', r'^kit (de )?distribucion', None, 'Autopartes', 'Cadenas y kits de distribución', _AP_SUMIDERO),
    ('Autopartes', r'^tapon (de )?rueda', None, 'Autos y motos', 'Tapones para llanta', _AP_SUMIDERO),
    ('Autopartes', r'^tapa lateral .{0,40}(set|suzuki|honda|italika|moto|cgl|en 125)', None, 'Autopartes',
     'Carenados, plásticos y tanques', _AP_SUMIDERO),
    ('Autopartes', r'^repuesto .{0,40}(fluval|hagen|acuario|pecera)', None, 'Mascotas', 'Acuarios y terrarios'),
    ('Autopartes', r'^resortes? deportivos? .{0,20}para auto', None, 'Autopartes', 'Resortes y muelles', _SUB_MOTO),
    ('Autopartes', r'^gomas? (para )?tirantes', None, 'Autopartes', 'Bujes y gomas de suspensión', _SUB_MOTO),
    # piezas del Vento de VW en subcategorías de moto
    ('Autopartes', r'^tensor', None, 'Autopartes', 'Poleas y tensores', _SUB_MOTO),
    ('Autopartes', r'^terminal', _NO_MOTO := r'\bmoto\b|italika', 'Autopartes', 'Terminales de dirección', _SUB_MOTO),
    ('Autopartes', r'^deposito', r'\bmoto\b|italika', 'Autopartes', 'Depósitos de anticongelante', _SUB_MOTO),
    ('Autopartes', r'^cofre', r'\bmoto\b|italika', 'Autopartes', 'Cofres, puertas y bisagras', _SUB_MOTO),
    ('Autopartes', r'^moldura', r'\bmoto\b|italika', 'Autopartes', 'Molduras y emblemas', _SUB_MOTO),
    ('Autopartes', r'^cuarto\b.{0,60}(' + _AUTO_NO_MOTO + ')', None, 'Autopartes', 'Cuartos y direccionales', _SUB_MOTO),
    ('Autopartes', r'^direccionales? .{0,40}(led )?.{0,20}(\bst\b|\bit\b|moto|italika|at 110)', None, 'Autopartes',
     'Luces de moto', {'Cuartos y direccionales'}),
    # Motocicletas (la moto entera) con refacciones y accesorios
    ('Autos y motos', r'^\W*porta ?placa', None, 'Autopartes', 'Carenados, plásticos y tanques', {'Motocicletas'}),
    ('Autos y motos', r'^liga elastica|^pulpo', None, 'Autos y motos', 'Accesorios para moto', {'Motocicletas'}),
    ('Autos y motos', r'^baleros?\b', None, 'Autopartes', 'Suspensión y dirección de moto', {'Motocicletas'}),
    ('Autos y motos', r'^balancin', None, 'Autopartes', 'Motor, carburación y escape de moto', {'Motocicletas'}),
    ('Autos y motos', r'^pulidora', None, 'Autos y motos', 'Limpieza y cuidado del auto', {'Motocicletas'}),
    ('Autos y motos', r'^calavera', None, 'Autopartes', 'Luces de moto', {'Motocicletas'}),
    ('Autos y motos', r'^banda (de )?accesorios', None, 'Autopartes', 'Bandas', {'Estéreos para auto'}),
    ('Autos y motos', r'^\d* ?tapones? polveras?', None, 'Autos y motos', 'Tapones para llanta', {'Rines'}),
    ('Autos y motos', r'^lentes? ', None, 'Joyería y bisutería', 'Lentes de sol', {'Cascos para moto'}),
    ('Autos y motos', r'giftpack|majorette', None, 'Juguetes', 'Vehículos de juguete', {'Accesorios para auto'}),
    # Muebles
    ('Muebles', r'soporte dorsolumbar|soporte de espalda', None, 'Salud', 'Movilidad y apoyo', {'Sillas de oficina'}),
    ('Muebles', r'^base para (productos )?calientes', None, 'Cocina y comedor', 'Utensilios de cocina', {'Mesas de centro'}),
    ('Muebles', r'^soporte angular|^bisagra', None, 'Muebles', 'Herrajes y refacciones de muebles'),
    ('Muebles', r'^lambrin|^piso (spc|autoadhesivo|laminado|vinilico)', None, 'Herramientas', 'Construcción'),
    ('Muebles', r'^litera', None, 'Muebles', 'Literas', {'Bases de cama y box'}),
    ('Muebles', r'^(base )?soporte (para )?(laptop|tableta)', None, 'Muebles', 'Accesorios y organizadores de escritorio',
     {'Sillas de oficina'}),
    ('Muebles', r'^sala (\d|con \d)', None, 'Muebles', 'Salas completas', {'Taburetes y bancos'}),
    ('Muebles', r'^(set de \d+ |juego de )?buros?\b', None, 'Muebles', 'Burós', {'Mesas de comedor', 'Mesas auxiliares y laterales'}),
    ('Muebles', r'^antecomedor', None, 'Muebles', 'Antecomedores y mesas de cocina', {'Juegos de comedor'}),
    ('Muebles', r'^(kit de cocina|madesa gabinete de cocina completa)', None, 'Muebles', 'Cocinas integrales',
     {'Alacenas y gabinetes de cocina'}),
    ('Muebles', r'^andador', None, 'Salud', 'Andaderas, bastones y muletas', {'Taburetes y bancos'}),
    ('Muebles', r'^hamaca', None, 'Muebles', 'Mecedoras y colgantes', {'Sillas plegables y de camping'}),
    ('Muebles', r'^cabecera\b', None, 'Muebles', 'Cabeceras', {'Sillones y reclinables'}),
    ('Muebles', r'^vela\b', None, 'Limpieza y hogar', 'Aromatizantes y velas', {'Sillones y reclinables'}),
    ('Muebles', r'^(kit \d+ )?cestos?\b', None, 'Muebles', 'Organizadores y almacenamiento', {'Roperos'}),
    ('Muebles', r'^soporte (fijo )?(de pared )?para tv', None, 'Televisores', 'Soportes para TV', {'Mesas de centro'}),
    # Cocina / electrodomésticos
    ('Cocina y comedor', r'^maceta', None, 'Jardín y exterior', 'Macetas y jardineras', {'Platos y bowls'}),
    ('Cocina y comedor', r'^cazo', None, 'Cocina y comedor', 'Ollas y cacerolas', {'Sartenes y comales'}),
    ('Electrodomésticos', r'^vaporizador', None, 'Electrodomésticos', 'Vaporizadores de ropa', {'Planchas'}),
    ('Electrodomésticos', r'^budinera|^arrocera .{0,30}aluminio', r'electric', 'Cocina y comedor', 'Ollas y cacerolas',
     {'Arroceras y ollas multiusos'}),
    ('Electrodomésticos', r'^tetera silbante', None, 'Cocina y comedor', 'Utensilios de cocina', {'Estufas'}),
    ('Electrodomésticos', r'^contenedor', None, 'Cocina y comedor', 'Contenedores herméticos', {'Microondas'}),
    ('Electrodomésticos', r'^bascula', None, 'Salud',
     lambda tn: None if re.search(r'alimento|cocina', tn) else 'Básculas', {'Estufas'}),
    ('Electrodomésticos', r'^bascula .{0,30}(alimento|cocina)', None, 'Cocina y comedor', 'Básculas y medidores', {'Estufas'}),
    ('Electrodomésticos', r'^sarten', None, 'Cocina y comedor', 'Sartenes y comales', {'Pequeños electrodomésticos de cocina'}),
    ('Cafeteras', r'^juego \d+ tazas|^tazas', None, 'Cocina y comedor', 'Juegos de tazas'),
    ('Refrigeradores', r'^enfriador (de )?vinos', None, 'Refrigeradores', 'Cavas de vino', {'Frigobares'}),
    # Herramientas
    ('Herramientas', r'^motobomba', None, 'Herramientas', 'Bombas de agua', {'Plomería', 'Jardinería', 'Mangueras y riego'}),
    ('Herramientas', r'^porta ?vaso', None, 'Herramientas', 'Sanitarios y accesorios de baño', {'Regaderas y duchas'}),
    ('Herramientas', r'^cautin', None, 'Herramientas', 'Cautines y estaciones de soldar', {'Juegos de herramientas'}),
    ('Herramientas', r'^(juego )?sierras? de barril', None, 'Herramientas', 'Sierras de copa y cortacírculos', {'Brocas'}),
    ('Herramientas', r'^bisagra', None, 'Muebles', 'Herrajes y refacciones de muebles', {'Regaderas y duchas', 'Brocas'}),
    ('Herramientas', r'^esmeril', None, 'Herramientas', 'Esmeriladoras y pulidoras', {'Taladros y rotomartillos'}),
    ('Herramientas', r'^pluma hidraulica|herramienta (de )?desmontaje .{0,20}resorte', None, 'Autos y motos',
     'Gatos y herramientas para auto', {'Herramientas manuales', 'Compresores y herramienta neumática'}),
    ('Herramientas', r'^inyector de grasa', None, 'Herramientas', 'Herramientas manuales', {'Jardinería'}),
    ('Herramientas', r'^molino (para granos|electrico)', None, 'Electrodomésticos', 'Molinos y procesadores', {'Jardinería'}),
    ('Herramientas', r'^cadena (plastica|pulida)', None, 'Herramientas', 'Construcción', {'Organizadores de herramientas', 'Llaves y dados'}),
    ('Herramientas', r'^guia de acero .{0,20}cable', None, 'Herramientas', 'Material eléctrico', {'Jardinería'}),
    ('Herramientas', r'^hilo de construccion', None, 'Herramientas', 'Construcción', {'Jardinería'}),
    ('Herramientas', r'^timbre', None, 'Herramientas', 'Timbres', {'Placas y tapas eléctricas'}),
    ('Herramientas', r'^bandas? (de )?lija', None, 'Herramientas', 'Lijas y accesorios de lijado', {'Brocas'}),
    # Iluminación
    ('Iluminación', r'^tubo (led|t8|t5)', None, 'Iluminación', 'Tubos LED y fluorescentes', {'Plafones y lámparas de sobreponer'}),
    ('Iluminación', r'^letrero', None, 'Iluminación', 'Letreros y neón', {'Tiras LED'}),
    ('Iluminación', r'^reflector', None, 'Iluminación', 'Reflectores', {'Plafones y lámparas de sobreponer'}),
    ('Iluminación', r'^proyector (de )?estrellas', None, 'Iluminación', 'Proyectores de luz y efectos', {'Lámparas de escritorio'}),
    ('Iluminación', r'^tira (flexible )?(de )?led', None, 'Iluminación', 'Tiras LED', {'Focos'}),
    ('Iluminación', r'(vehiculo|\bauto|patrulla|ambulancia|torreta|12 ?v\b).{0,80}estrobo|estrobo.{0,80}(vehiculo|12 ?v\b|12-24 ?v)|tunelight',
     r'\bdj\b|fiesta|escenario|dmx', 'Autos y motos', 'Luces LED para auto', {'Escenario'}),
    ('Iluminación', r'^bases? para luces auxiliares', None, 'Autos y motos', 'Luces LED para auto', {'Decorativa'}),
    # Belleza
    ('Belleza y cuidado personal', r'^multiestilizador', None, 'Belleza y cuidado personal', 'Estilizadores', {'Secadoras de cabello'}),
    ('Belleza y cuidado personal', r'^delineador', None, 'Belleza y cuidado personal', 'Sombras y delineadores', {'Bases y correctores'}),
    ('Belleza y cuidado personal', r'^polvo', None, 'Belleza y cuidado personal', 'Polvos, rubores y bronceadores', {'Correctores'}),
    # Otros
    ('Relojes inteligentes', r'^smartwatch', None, 'Relojes inteligentes', 'Smartwatches', {'Correas y extensibles'}),
    ('Componentes y accesorios de PC', r'^placa base|^tarjeta madre', None, 'Componentes y accesorios de PC', 'Tarjetas madre',
     {'RAM DDR4 para PC de escritorio', 'RAM DDR5 para PC de escritorio'}),
    ('Cargadores y adaptadores', r'^hub\b', None, 'Componentes y accesorios de PC', 'Hubs y docks para PC',
     {'Cargadores multipuerto y estaciones de carga'}),
    ('Juguetes', r'^funko', None, 'Juguetes', 'Funko y coleccionables', {'Bloques de construcción'}),
    ('Juguetes', r'^tapete', None, 'Bebés', 'Juguetes para bebé', {'Figuras de acción'}),
    ('Blancos y ropa de cama', r'^cojin', None, 'Decoración de hogar y jardín', 'Cojines', {'Edredones'}),
    ('Blancos y ropa de cama', r'^(juego de )?baberos?', None, 'Bebés', 'Alimentación y lactancia'),
    ('Instrumentos musicales', r'^masajeador', None, 'Belleza y cuidado personal', 'Masajeadores'),
    ('Bicicletas y movilidad', r'^scooter', None, 'Deportes y fitness', 'Patinetas y scooters', {'Triciclos y bicicletas de carga'}),
    ('Celulares', r'^estabilizador', None, 'Cámaras y fotografía', 'Trípodes y soportes'),
    ('Mascotas', r'^pigmento', None, 'Herramientas', 'Construcción', {'Acuarios y terrarios'}),
    ('Mascotas', r'^arenero', None, 'Mascotas', 'Areneros', {'Higiene y limpieza'}),
    ('Bebés', r'^baberos?', None, 'Bebés', 'Alimentación y lactancia', {'Carriolas'}),
    ('Bebés', r'^chupon', None, 'Bebés', 'Chupones y mordederas', {'Carriolas'}),
    ('Joyería y bisutería', r'^pulso\b', None, 'Joyería y bisutería', 'Pulseras', {'Anillos'}),
    ('Joyería y bisutería', r'^pendientes', None, 'Joyería y bisutería', 'Aretes', {'Collares'}),
    ('Deportes y fitness', r'^(set \d+ )?porterias?', None, 'Deportes y fitness', 'Porterías y redes de fútbol', {'Balones de fútbol'}),
]
REGLAS += LOTES['wb3']

# ---- Auditoría WB, lote 4 (26-sep-2026): grupos 250-520 (de 4 a 6 fichas) ----
_P = r'^(\(\d+\) |\d+[-/] ?)?'   # «(1) soporte...», «1-regulador», «1/ brazo»
_AP_TODO = _AP_SUMIDERO | _SUB_MOTO | {'Escape', 'Cuartos y direccionales', 'Filtros y aceites'}
LOTES['wb4'] = [
    # Autopartes
    ('Autopartes', _P + r'soporte (de )?barra (tensora|de torsion|torsion|estabilizadora)', None, 'Autopartes',
     'Suspensión y dirección', _AP_TODO - {'Suspensión y dirección'}),
    ('Autopartes', _P + r'soporte (de )?brazo', None, 'Autopartes', 'Suspensión y dirección', _AP_TODO - {'Suspensión y dirección'}),
    ('Autopartes', _P + r'(tubo|manguera) (de )?(enfriamiento )?calefaccion', None, 'Autopartes',
     'Mangueras y tubos de enfriamiento', _AP_TODO),
    ('Autopartes', _P + r'resistencia\b', r'bomba|gasolina|combustible', 'Autopartes', 'Enfriamiento y climatización',
     {'Motor y transmisión'}),
    ('Autopartes', _P + r'guia de tiempo', None, 'Autopartes', 'Cadenas y kits de distribución', _AP_TODO),
    ('Autopartes', _P + r'soporte (de )?goma de escape', None, 'Autopartes', 'Escape', _AP_TODO - {'Escape'}),
    ('Autopartes', _P + r'toma (de )?agua', None, 'Autopartes', 'Tomas de agua y termostatos', _SUB_MOTO),
    ('Autopartes', _P + r'rotula', r'\bmoto\b|italika', 'Autopartes', 'Rótulas', _SUB_MOTO),
    ('Autopartes', _P + r'tapon (de )?llenado (de )?aceite', None, 'Autopartes', 'Tapones, cárter y tapas de motor',
     {'Filtros y aceites'}),
    ('Autopartes', _P + r'gomas? (de )?caja (de )?direccion', None, 'Autopartes', 'Coples, varillas y cajas de dirección', _AP_TODO),
    ('Autopartes', _P + r'laina .{0,20}caster', None, 'Autopartes', 'Suspensión y dirección', _AP_TODO),
    ('Autopartes', _P + r'compresor \w+ \d+ ?lt', None, 'Herramientas', 'Compresores y herramienta neumática'),
    ('Autopartes', _P + r'valvula .{0,20}marcha minima', None, 'Autopartes', 'Válvulas IAC y de marcha mínima', _AP_TODO),
    ('Autopartes', _P + r'balancin', None, 'Autopartes', 'Motor, carburación y escape de moto',
     {'Válvulas, punterías y árbol de levas', 'Carenados, plásticos y tanques'}),
    ('Autopartes', _P + r'motor (de )?elevacion (de )?ventana', None, 'Autopartes', 'Elevadores y cristales', _AP_TODO),
    ('Autopartes', _P + r'direccionales? .{0,40}(set|yh|ybr|\bit\b|\bst\b)', None, 'Autopartes', 'Luces de moto',
     {'Cuartos y direccionales'}),
    ('Autopartes', _P + r'moto ?bomba', None, 'Herramientas', 'Bombas de agua'),
    ('Autopartes', _P + r'tope (de )?rebote', None, 'Autopartes', 'Bases y cubrepolvos de amortiguador', _AP_TODO),
    ('Autopartes', _P + r'guia (trasera )?(de )?(fascia|defensa)', None, 'Autopartes', 'Defensas, fascias y parrillas', _AP_TODO),
    ('Autopartes', _P + r'aleron|contrachapa', None, 'Autopartes', 'Carrocería, espejos y molduras', _AP_TODO),
    ('Autopartes', _P + r'brazo aux', None, 'Autopartes', 'Coples, varillas y cajas de dirección', _AP_TODO),
    # Motocicletas / llantas de moto
    ('Autos y motos', r'^bases? adaptador(es)? de manubrio|puños|^jgo par punos', None, 'Autopartes', 'Manubrios, espejos y controles',
     {'Motocicletas'}),
    ('Autos y motos', r'^banda para moto|^gomas? de sprocket', None, 'Autopartes', 'Cadenas, sprockets y transmisión', {'Motocicletas'}),
    ('Autos y motos', r'^tapas? laterales', None, 'Autopartes', 'Carenados, plásticos y tanques', {'Motocicletas'}),
    ('Autos y motos', r'^defensa slider', None, 'Autopartes', 'Asientos, parrillas y accesorios de moto', {'Motocicletas'}),
    ('Autos y motos', r'^scooter', None, 'Deportes y fitness', 'Patinetas y scooters', {'Motocicletas'}),
    ('Autos y motos', r'^kit de palanca desmontar', None, 'Autos y motos', 'Cámaras y accesorios de llanta', {'Llantas para moto'}),
    ('Autos y motos', r'^ambientador', None, 'Autos y motos', 'Aromatizantes para auto', {'Accesorios para auto'}),
    ('Autos y motos', r'^sudadera', None, 'Autos y motos', 'Ropa para motociclista', {'Cascos para moto'}),
    ('Autos y motos', r'^buje separador', None, 'Autopartes', 'Suspensión y dirección de moto', {'Rines'}),
    ('Autos y motos', r'^amplificador', None, 'Autos y motos', 'Amplificadores para auto', {'Subwoofers para auto'}),
    # Herramientas
    ('Herramientas', r'^esmeriladora', None, 'Herramientas', 'Esmeriladoras y pulidoras', {'Baterías y cargadores de herramienta', 'Motosierras'}),
    ('Herramientas', r'^sierra sable', None, 'Herramientas', 'Sierras', {'Neumáticas'}),
    ('Herramientas', r'^cautin', None, 'Herramientas', 'Cautines y estaciones de soldar', {'Desarmadores y puntas'}),
    ('Herramientas', r'^sanitario', None, 'Herramientas', 'Sanitarios', {'Juegos de herramientas'}),
    ('Herramientas', r'^(enrutador|router) (madera|industrial)', None, 'Herramientas', 'Routers, fresadoras y multiherramientas',
     {'Routers, fresadoras y multiherramientas', 'Taladros y rotomartillos'}),
    ('Herramientas', r'^pintex|esmalte alquidalico', None, 'Herramientas', 'Construcción'),
    ('Herramientas', r'^generador', r'espuma', 'Herramientas', 'Generadores', {'Hidrolavadoras'}),
    ('Herramientas', r'^lentes? para soldar', None, 'Herramientas', 'Caretas y cascos para soldar', {'Soldadura'}),
    ('Herramientas', r'^molino (para granos|electrico|pulverizador)', None, 'Electrodomésticos', 'Molinos y procesadores', {'Jardinería'}),
    ('Herramientas', r'^puntas? para atornillar', None, 'Herramientas', 'Puntas para atornillar', {'Brocas'}),
    ('Herramientas', r'^sierra carburo', None, 'Herramientas', 'Hojas y cuchillas de sierra', {'Brocas'}),
    ('Herramientas', r'^clavija', r'madera', 'Herramientas', 'Apagadores y contactos', {'Juegos de herramientas'}),
    ('Herramientas', r'^electrodo', None, 'Herramientas', 'Consumibles de soldadura', {'Bolsas y cinturones portaherramientas'}),
    ('Herramientas', r'^banda (de |para )?(lija|lijadora)', None, 'Herramientas', 'Lijas y accesorios de lijado', {'Lijadoras', 'Brocas'}),
    ('Herramientas', r'^gato de botella', None, 'Autos y motos', 'Gatos hidráulicos para auto', {'Seguridad industrial'}),
    ('Herramientas', r'^cadena tipo', None, 'Herramientas', 'Construcción', {'Jardinería'}),
    ('Herramientas', r'^juego dados? con punta', None, 'Herramientas', 'Dados, matracas y autocles', {'Juegos de herramientas'}),
    ('Iluminación', r'^generador', None, 'Herramientas', 'Generadores', {'Decorativa'}),
    ('Iluminación', r'^lentes? (luz )?anti-? ?azul', None, 'Joyería y bisutería', 'Lentes oftálmicos y de lectura', {'Decorativa'}),
    # Muebles, cocina, bebés, etc.
    ('Muebles', r'^puerta plegable', None, 'Herramientas', 'Construcción', {'Sillas de oficina'}),
    ('Muebles', r'^set \d+ bancos?', None, 'Muebles', 'Taburetes y bancos', {'Sillas de comedor'}),
    ('Muebles', r'^set \d+ piezas mantel|^mantel', None, 'Cocina y comedor', 'Manteles y caminos de mesa', {'Mesas de centro'}),
    ('Electrodomésticos', r'^cacerola', None, 'Cocina y comedor', 'Ollas y cacerolas', {'Arroceras y ollas multiusos'}),
    ('Electrodomésticos', r'^tetera', r'electrica', 'Cocina y comedor', 'Utensilios de cocina', {'Estufas'}),
    ('Cargadores y adaptadores', r'^zapato postoperatorio', None, 'Salud', 'Movilidad y apoyo'),
    ('Cafeteras', r'^(set|juego) \d+ tazas', None, 'Cocina y comedor', 'Juegos de tazas'),
    ('Refrigeradores', r'^enfriador portatil', None, 'Deportes y fitness', 'Campismo', {'Frigobares'}),
    ('Bebés', r'^autoasiento', None, 'Bebés', 'Sillas de auto', {'Portabebés y canguros'}),
    ('Bebés', r'^corral', None, 'Bebés', 'Corrales', {'Carriolas'}),
    ('Blancos y ropa de cama', r'toallas? con capucha .{0,20}bebe', None, 'Bebés', 'Baño e higiene del bebé'),
    ('Blancos y ropa de cama', r'panaleros?', None, 'Bebés', 'Ropa y calzado de bebé', {'Cobijas'}),
    ('Deportes y fitness', r'^sillon puff', None, 'Muebles', 'Puffs y otomanas', {'Balones de fútbol'}),
    ('Deportes y fitness', r'^visor (para )?buceo', None, 'Deportes y fitness', 'Snorkel y buceo', {'Balones de fútbol'}),
    ('Deportes y fitness', r'^\d+ porterias?', None, 'Deportes y fitness', 'Porterías y redes de fútbol', {'Balones de fútbol'}),
    ('Cámaras y fotografía', r'^drone?s?\b', None, 'Cámaras y fotografía', 'Drones', {'Cámaras de acción'}),
    ('Cámaras y fotografía', r'^lentes? de sol', None, 'Joyería y bisutería', 'Lentes de sol'),
    ('Joyería y bisutería', r'^lentes? de sol', None, 'Joyería y bisutería', 'Lentes de sol', {'Relojes para hombre', 'Relojes'}),
    ('Joyería y bisutería', r'^pulso\b', None, 'Joyería y bisutería', 'Pulseras', {'Collares'}),
    ('Joyería y bisutería', r'^pulsera\b', r'aretes', 'Joyería y bisutería', 'Pulseras', {'Cadenas', 'Aretes'}),
    ('Joyería y bisutería', r'^(par )?tobilleras con peso', None, 'Deportes y fitness', 'Pesas de tobillo y chalecos con peso'),
    ('Juguetes', r'^(fm )?lapicera', None, 'Papelería y oficina', 'Útiles escolares'),
    ('Mascotas', r'^collarin cervical', None, 'Salud', 'Movilidad y apoyo'),
    ('Mascotas', r'^kit de pintura acrilica', None, 'Papelería y oficina', 'Arte y dibujo'),
    ('Mascotas', r'^placa de identificacion', None, 'Mascotas', 'Collares para mascotas', {'Juguetes para perro'}),
    ('Componentes y accesorios de PC', r'^mother ?(board)?\b', None, 'Componentes y accesorios de PC', 'Tarjetas madre',
     {'RAM DDR4 para PC de escritorio', 'RAM DDR5 para PC de escritorio'}),
    ('Audífonos', r'^tapones? (para |de )?(los )?oidos', None, 'Salud', 'Salud'),
    ('Belleza y cuidado personal', r'^bruma corporal', None, 'Belleza y cuidado personal', 'Corporales', {'Cremas faciales'}),
    ('Belleza y cuidado personal', r'^tenaza', None, 'Belleza y cuidado personal', 'Rizadores', {'Planchas para cabello'}),
    ('Belleza y cuidado personal', r'^pintex', None, 'Herramientas', 'Construcción'),
]
REGLAS += LOTES['wb4']

# ---- Auditoría WB, lote 5 (26-sep-2026): grupos nuevos 0-168 (de 3 a 4 fichas) ----
LOTES['wb5'] = [
    ('Electrodomésticos', r'^sarten electrica', None, 'Electrodomésticos', 'Parrillas y planchas eléctricas', {'Lavavajillas'}),
    ('Electrodomésticos', r'^jarra', r'electric', 'Cocina y comedor', 'Jarras y dispensadores de bebidas',
     {'Pequeños electrodomésticos de cocina'}),
    ('Electrodomésticos', r'^prensa manual', None, 'Cocina y comedor', 'Utensilios de cocina', {'Extractores de jugo'}),
    ('Deportes y fitness', r'^caminadora', None, 'Deportes y fitness', 'Caminadoras', {'Máquinas multifuncionales y poleas'}),
    ('Deportes y fitness', r'^banco ajustable', None, 'Deportes y fitness', 'Bancos y racks', {'Bandas de resistencia'}),
    ('Deportes y fitness', r'^(anillo|aro) de pilates', None, 'Deportes y fitness', 'Pelotas y aros de pilates', {'Bandas de resistencia'}),
    ('Deportes y fitness', r'^(\d+ ?pzs )?pulseras?', None, 'Joyería y bisutería', 'Pulseras', {'Mancuernas'}),
    ('Muebles', r'^cantina', None, 'Muebles', 'Aparadores y bufeteros', {'Sillas de comedor'}),
    ('Cocina y comedor', r'^tequilero', None, 'Cocina y comedor', 'Vasos tequileros y caballitos', {'Utensilios de cocina'}),
    ('Cocina y comedor', r'^base para pastel', None, 'Cocina y comedor', 'Repostería y moldes', {'Vasos y copas'}),
    ('Cocina y comedor', r'^(juego )?budineras?', None, 'Cocina y comedor', 'Ollas y cacerolas', {'Sartenes y comales'}),
    ('Cocina y comedor', r'^prensa francesa', None, 'Cafeteras', 'Manuales', {'Termos y botellas térmicas'}),
    ('Cargadores y adaptadores', r'^hub\b', None, 'Componentes y accesorios de PC', 'Hubs y docks para PC', {'Cables USB-C'}),
    ('Cargadores y adaptadores', r'^mesita de noche', None, 'Muebles', 'Burós'),
    ('Belleza y cuidado personal', r'^velas?\b', None, 'Limpieza y hogar', 'Aromatizantes y velas', {'Depilación'}),
    ('Belleza y cuidado personal', r'^tonyin|lavado y proteccion de auto', None, 'Autos y motos', 'Limpieza y cuidado del auto'),
    ('Belleza y cuidado personal', r'^esmalte', None, 'Belleza y cuidado personal', 'Uñas', {'Labiales'}),
    ('Belleza y cuidado personal', r'^acondicionador', None, 'Belleza y cuidado personal', 'Acondicionadores', {'Cremas faciales'}),
    ('Bebés', r'canguros? .{0,20}(bebe|portabebe)|mochila ergonomica porta ?bebe', None, 'Bebés', 'Portabebés y canguros', {'Carriolas'}),
    ('Bebés', r'^chupetes?', r'tetina', 'Bebés', 'Chupones y mordederas', {'Alimentación y lactancia', 'Biberones'}),
    ('Bolsas y mochilas', r'^cosmetiquera', None, 'Bolsas y mochilas', 'Cosmetiqueras y neceseres', {'Mochilas para laptop'}),
    ('Climatización', r'^enfriador (de ventilador )?para (computadora|laptop)', None, 'Componentes y accesorios de PC',
     'Enfriamiento y ventiladores', {'Ventiladores portátiles y de mano'}),
    ('Climatización', r'^calefactor', None, 'Climatización', 'Calefactores cerámicos y de aire', {'Ventiladores portátiles y de mano'}),
    ('Laptops', r'^cpu\b', None, 'Computadoras de escritorio',
     lambda tn: 'Reacondicionadas' if 'reacondicionad' in tn else 'Torres de casa y oficina'),
    ('Iluminación', r'^faros? de lupa|luces led auxiliares', None, 'Autos y motos', 'Luces LED para auto', {'Proyectores de luz y efectos'}),
    ('Bocinas', r'^estereo moto', None, 'Autos y motos', 'Bocinas marinas y para moto'),
    ('Bocinas', r'^subwoofer', None, 'Bocinas', 'Subwoofers', {'De estantería y Hi-Fi'}),
    ('Aspiradoras', r'^lijadora', None, 'Herramientas', 'Lijadoras'),
    ('Proyectores y accesorios', r'brazo movil musical .{0,20}cuna|movil musical .{0,20}cuna', None, 'Bebés', 'Juguetes para bebé'),
    ('Celulares', r'^timbre', None, 'Herramientas', 'Timbres', {'Android'}),
    ('Celulares', r'^amplificador de senal', None, 'Redes', 'Repetidores', {'Android'}),
    ('Joyería y bisutería', r'^timex reloj|^reloj .{0,30}para ninos', None, 'Joyería y bisutería', 'Relojes infantiles', {'Correas para reloj'}),
    ('Joyería y bisutería', r'^disfraz', None, 'Juguetes', 'Disfraces'),
    ('Mascotas', r'^tapete sanitario', None, 'Mascotas', 'Higiene y limpieza', {'Acuarios y terrarios'}),
    ('Mascotas', r'^conejo \d+ ?cm|nici', r'para (perro|gato)', 'Juguetes', 'Peluches', {None}),
    ('Mascotas', r'^rastrillo .{0,40}(perro|gato|mascota)', None, 'Mascotas', 'Higiene y limpieza', {None}),
]
REGLAS += LOTES['wb5']

# ---- Auditoría WB, lote 6 (26-sep-2026): grupos nuevos 169-330 (3 fichas) ----
LOTES['wb6'] = [
    # Herramientas
    ('Herramientas', r'^(kit )?hidrolavadora', None, 'Herramientas', 'Hidrolavadoras', {'Baterías y cargadores de herramienta'}),
    ('Herramientas', r'^atornillador', None, 'Herramientas', 'Atornilladores', {'Baterías y cargadores de herramienta'}),
    ('Herramientas', r'^sierra (para madera|circular|caladora)', None, 'Herramientas', 'Sierras', {'Brocas para madera', 'Brocas'}),
    ('Herramientas', r'^remachadora', None, 'Herramientas', 'Herramientas manuales', {'Llaves y dados'}),
    ('Herramientas', r'^cortadora de pasto', None, 'Herramientas', 'Podadoras y cortacésped', {'Jardinería'}),
    ('Herramientas', r'^bandas? grano', None, 'Herramientas', 'Lijas y accesorios de lijado', {'Cajas de herramientas'}),
    ('Herramientas', r'^corta ?azulejos', None, 'Herramientas', 'Herramientas de corte manual', {'Brocas'}),
    ('Herramientas', r'^cautin', None, 'Herramientas', 'Cautines y estaciones de soldar', {'Puntas para atornillar'}),
    ('Herramientas', r'^cople .{0,20}(laton|npt|macho|hembra)', None, 'Herramientas', 'Tuberías y conexiones', {'Jardinería'}),
    ('Herramientas', r'^carrete de pesca', None, 'Deportes y fitness', 'Pesca'),
    ('Herramientas', r'^(kit de )?cinceles? sds', None, 'Herramientas', 'Accesorios para rotomartillo y demoledor', {'Rotomartillos'}),
    ('Herramientas', r'^generador', r'espuma|vapor|ozono', 'Herramientas', 'Generadores', {'Compresores y herramienta neumática'}),
    ('Herramientas', r'^pluma hidraulica', None, 'Autos y motos', 'Gatos y herramientas para auto', {'Llaves y dados', 'Jardinería'}),
    # Electrodomésticos / cocina
    ('Electrodomésticos', r'^crepera electrica', None, 'Electrodomésticos', 'Wafleras, sandwicheras y creperas', {'Planchas'}),
    ('Electrodomésticos', r'^microondas', None, 'Electrodomésticos', 'Microondas', {'Campanas de cocina'}),
    ('Electrodomésticos', r'^plancha (de )?hierro fundido', None, 'Cocina y comedor', 'Comales y planchas', {'Estufas'}),
    ('Cocina y comedor', r'^balon\b', None, 'Deportes y fitness', 'Balones de fútbol', {'Vasos y copas'}),
    ('Cocina y comedor', r'^cava\b.{0,40}(mueble|bar|botellas)', None, 'Muebles', 'Cavas y porta botellas', {'Organización de cocina'}),
    ('Cocina y comedor', r'^(set de )?manteles', None, 'Cocina y comedor', 'Manteles y caminos de mesa', {'Vajillas'}),
    ('Cocina y comedor', r'^molde', None, 'Cocina y comedor', 'Repostería y moldes', {'Utensilios de cocina'}),
    ('Cocina y comedor', r'^empaque .{0,20}tanque', None, 'Herramientas', 'Sanitarios y accesorios de baño', {'Tazas'}),
    ('Cocina y comedor', r'^tetera electrica', None, 'Electrodomésticos', 'Hervidores y teteras eléctricas',
     {'Jarras y dispensadores de bebidas'}),
    # Autos y motos / autopartes
    ('Autos y motos', r'^cojin', None, 'Salud', 'Salud', {'Llantas para auto'}),
    ('Autos y motos', r'^switch (de )?encendido', None, 'Autopartes', 'Eléctrico y baterías de moto', {'Motocicletas'}),
    ('Autos y motos', r'^toma coaxial', None, 'Herramientas', 'Apagadores y contactos', {'Accesorios para auto'}),
    ('Autos y motos', r'^faro delantero', None, 'Autopartes', 'Luces de moto', {'Motocicletas'}),
    ('Autos y motos', r'^bandanas?', None, 'Autos y motos', 'Ropa para motociclista', {'Motocicletas'}),
    ('Autos y motos', r'^moto-?tool', None, 'Herramientas', 'Neumáticas', {'Llantas para moto'}),
    ('Autopartes', r'^vaso con aspas', None, 'Electrodomésticos', 'Licuadoras'),
    ('Autopartes', _P + r'(juego )?gomas? (para )?barra', None, 'Autopartes', 'Bujes y gomas de suspensión', _AP_TODO),
    ('Autopartes', _P + r'regulador (de )?presion (de )?combustible', None, 'Autopartes', 'Inyectores y carburadores', _AP_TODO),
    ('Autopartes', _P + r'montaje de amortiguadores', r'\bmoto\b|italika', 'Autopartes', 'Bases y cubrepolvos de amortiguador', _SUB_MOTO),
    ('Autopartes', _P + r'frente para', None, 'Autopartes', 'Defensas, fascias y parrillas', _AP_TODO),
    ('Autopartes', _P + r'(par de )?coples? .{0,10}direccion', None, 'Autopartes', 'Coples, varillas y cajas de dirección', _AP_TODO),
    ('Autopartes', _P + r'junta lado rueda', None, 'Autopartes', 'Flechas y juntas homocinéticas', _SUB_MOTO),
    ('Autopartes', _P + r'deposito limpiaparabrisas', None, 'Autopartes', 'Limpiaparabrisas', {'Para motos'} | _SUB_MOTO),
    ('Autopartes', _P + r'(kit \d+ )?tapones de rin', None, 'Autos y motos', 'Tapones para llanta'),
    ('Autopartes', _P + r'alternador', None, 'Autopartes', 'Alternadores y marchas', {'Motor y transmisión'}),
    ('Autopartes', _P + r'espejo (retrovisor|electrico)', r'\bmoto\b|bebe', 'Autopartes', 'Espejos laterales',
     {'Motor y transmisión', 'Faros'}),
    ('Autopartes', _P + r'terminal (exterior|interior)', None, 'Autopartes', 'Terminales de dirección', {'Motor y transmisión'}),
    # Deportes, juguetes, ropa
    ('Deportes y fitness', r'^caminadora', None, 'Deportes y fitness', 'Caminadoras', {'Cuerdas para saltar'}),
    ('Deportes y fitness', r'^(paquete de \d+ )?shorts?', None, 'Ropa y accesorios', 'Shorts y bermudas', {'Rodilleras, muñequeras y soportes'}),
    ('Juguetes', r'^pista', r'canicas', 'Juguetes', 'Vehículos de juguete', {'Bloques de construcción'}),
    ('Juguetes', r'^vaso entrenador', None, 'Bebés', 'Alimentación y lactancia', {'Figuras de acción'}),
    ('Ropa y accesorios', r'^sueter', None, 'Ropa y accesorios', 'Chamarras y suéteres', {'Playeras'}),
    # Componentes
    ('Componentes y accesorios de PC', r'^cava', None, 'Refrigeradores', 'Cavas de vino'),
    ('Componentes y accesorios de PC', r'^kit pestanas', None, 'Belleza y cuidado personal', 'Pestañas postizas'),
    ('Componentes y accesorios de PC', r'^t\.? ?madre', None, 'Componentes y accesorios de PC', 'Tarjetas madre',
     {'RAM DDR4 para PC de escritorio', 'RAM DDR5 para PC de escritorio'}),
    ('Componentes y accesorios de PC', r'^fuente\b', None, 'Componentes y accesorios de PC', 'Fuentes de poder', {'Gabinetes'}),
    ('Componentes y accesorios de PC', r'^vornado|circulador de aire', None, 'Climatización', 'Ventiladores de mesa y clip'),
    # Muebles
    ('Muebles', r'^vinil decorativo', None, 'Decoración de hogar y jardín', 'Vinil decorativo'),
    ('Muebles', r'^cocina \d', None, 'Muebles', 'Cocinas integrales', {'Sillas de comedor'}),
    ('Muebles', r'^set \d+ buros?', None, 'Muebles', 'Burós', {'Repisas'}),
    ('Muebles', r'^porta ?pasaporte', None, 'Viajes', 'Accesorios de viaje'),
    ('Muebles', r'^bouncer', None, 'Bebés', 'Sillas de comer y mecedoras'),
    ('Muebles', r'^caminos? (de )?mesa', None, 'Cocina y comedor', 'Manteles y caminos de mesa', {'Mesas de centro'}),
    ('Muebles', r'^banco\b', None, 'Muebles', 'Taburetes y bancos', {'Sillones y reclinables', 'Sillas de exterior'}),
    ('Muebles', r'^sombrilla', None, 'Jardín y exterior', 'Sombrillas, toldos y carpas', {'Sillas plegables y de camping'}),
    ('Muebles', r'^cestos?\b', None, 'Muebles', 'Organizadores y almacenamiento', {'Sillas plegables y de camping', 'Taburetes y bancos'}),
]
REGLAS += LOTES['wb6']

# ---- Auditoría WB, lote 7 (26-sep-2026): grupos pendientes 0-198 (2 y 3 fichas) ----
LOTES['wb7'] = [
    ('Bebés', r'^chupetes?', r'tetina', 'Bebés', 'Chupones y mordederas', {'Carriolas'}),
    ('Cocina y comedor', r'^\d+ tequileros', None, 'Cocina y comedor', 'Vasos tequileros y caballitos', {'Bar y coctelería'}),
    ('Refrigeradores', r'^recipientes? (de )?almacenamiento', None, 'Cocina y comedor', 'Contenedores herméticos'),
    ('Belleza y cuidado personal', r'^set de \d+ labiales', None, 'Belleza y cuidado personal', 'Tintas y labiales líquidos',
     {'Polvos, rubores y bronceadores'}),
    ('Belleza y cuidado personal', r'^liquido para pantallas', None, 'Limpieza y hogar', 'Limpiadores y desinfectantes'),
    ('Decoración de hogar y jardín', r'candados? (para )?cortina', None, 'Herramientas', 'Candados', {'Cortinas'}),
    ('Cargadores y adaptadores', r'^hub\b', None, 'Componentes y accesorios de PC', 'Hubs y docks para PC', {'De pared'}),
    ('Televisores', r'^roku (ultra|express|streaming)|reproductor (de )?streaming', r'\btv\b|control', 'Televisores', 'Dispositivos de streaming'),
    ('Videojuegos', r'^xbxone', None, 'Videojuegos', 'Juegos Xbox', {'Juegos PS4'}),
    ('Iluminación', r'^espejo', None, 'Decoración de hogar y jardín', 'Espejos de baño con luz', {'Lámparas de pared'}),
    ('Iluminación', r'^calefactor', None, 'Climatización', 'Calefactores infrarrojos y de cuarzo', {'Focos'}),
    ('Iluminación', r'^relevador', None, 'Autopartes', 'Luces de moto'),
    ('Juegos de mesa', r'^piso (foamy|rompecabezas)', None, 'Bebés', 'Juguetes para bebé', {'Rompecabezas'}),
    ('Blancos y ropa de cama', r'^pano (de )?limpieza', None, 'Limpieza y hogar', 'Limpiadores y desinfectantes'),
    ('Blancos y ropa de cama', r'^hamaca', None, 'Muebles', 'Mecedoras y colgantes'),
    ('Blancos y ropa de cama', r'^toallita .{0,40}(chiqui|bebe)', None, 'Bebés', 'Baño e higiene del bebé', {'Cobijas'}),
    ('Bocinas', r'^proyector', None, 'Proyectores y accesorios', 'Proyectores', {'Barras de sonido'}),
    ('Bicicletas y movilidad', r'^set de juego barbie', None, 'Juguetes', 'Muñecas'),
    ('Bicicletas y movilidad', r'^gorra', None, 'Ropa y accesorios', 'Gorras y sombreros'),
    ('Equipo comercial', r'^\d+ candados', None, 'Herramientas', 'Candados'),
    ('Monitores', r'^oximetro', None, 'Salud', 'Oxímetros'),
    ('Celulares', r'^pulsera', None, 'Joyería y bisutería', 'Pulseras'),
    ('Celulares', r'^abridor de tarros', None, 'Cocina y comedor', 'Utensilios de cocina'),
    # Herramientas
    ('Herramientas', r'^(combo )?prensa hidraulica', None, 'Herramientas', 'Herramientas de banco', {'Seguridad industrial'}),
    ('Herramientas', r'^engrapadora', r'hojas', 'Herramientas', 'Pistolas de calor, engrapadoras y clavadoras', {'Neumáticas'}),
    ('Herramientas', r'^esmeriladora', None, 'Herramientas', 'Esmeriladoras y pulidoras', {'Cables y extensiones eléctricas'}),
    ('Herramientas', r'^lijadora', None, 'Herramientas', 'Lijadoras', {'Juegos de herramientas'}),
    ('Herramientas', r'^regleta|^supresor de picos', None, 'Cargadores y adaptadores', 'Regletas y multicontactos',
     {'Material eléctrico', 'Juegos de herramientas'}),
    ('Herramientas', r'^(combo )?plotter', None, 'Herramientas', 'Grabado láser', {'Taladros y rotomartillos'}),
    ('Herramientas', r'^tonyin', None, 'Autos y motos', 'Limpieza y cuidado del auto'),
    ('Herramientas', r'fusibles automotri|fusibles coche', None, 'Autopartes', 'Bulbos, interruptores y relevadores'),
    ('Herramientas', r'^porta ?fusible', None, 'Autopartes', 'Bulbos, interruptores y relevadores',
     {'Interruptores, breakers y fusibles'}),
    ('Herramientas', r'^kit soldador', None, 'Herramientas', 'Soldadoras', {'Caretas y cascos para soldar'}),
    ('Herramientas', r'^escuadra', None, 'Herramientas', 'Escuadras y reglas', {'Desarmadores y puntas'}),
    ('Herramientas', r'^guia jalacable', None, 'Herramientas', 'Material eléctrico', {'Brocas'}),
    ('Herramientas', r'^enchufe (de paso )?rj45', None, 'Redes', 'Cables y adaptadores de red'),
    ('Herramientas', r'^hidrolavadora', None, 'Herramientas', 'Hidrolavadoras', {'Jardinería'}),
    ('Herramientas', r'^clavija', r'madera', 'Herramientas', 'Apagadores y contactos', {'Prensas y sujeción'}),
]
REGLAS += LOTES['wb7']

# ---- Auditoría WB, lote 8 (26-sep-2026): grupos pendientes 199-298 (2 fichas) ----
LOTES['wb8'] = [
    # Herramientas
    ('Herramientas', r'^placa (toma|decorativa|ciega|para (apagador|contacto|modulo))', None, 'Herramientas',
     'Placas y tapas eléctricas', {'Material eléctrico'}),
    ('Herramientas', r'quita ?grapas', None, 'Autos y motos', 'Gatos y herramientas para auto',
     {'Pistolas de calor, engrapadoras y clavadoras'}),
    ('Herramientas', r'^sierra de arco', None, 'Herramientas', 'Herramientas de corte manual', {'Brocas para metal'}),
    ('Herramientas', r'^sierras? (corta ?circulo|perforadora)', None, 'Herramientas', 'Sierras de copa y cortacírculos', {'Brocas para metal'}),
    ('Herramientas', r'^sierra', r'corta ?circulo|perforadora', 'Herramientas', 'Sierras', {'Brocas para metal', 'Baterías y cargadores de herramienta'}),
    ('Herramientas', r'^(combo )?(mini)?esmeriladora', None, 'Herramientas', 'Esmeriladoras y pulidoras',
     {'Cintas métricas y flexómetros', 'Taladros y rotomartillos'}),
    ('Herramientas', r'^cortadora .{0,30}(marmol|azulejo|porcelanato)', None, 'Herramientas', 'Sierras', {'Brocas'}),
    ('Herramientas', r'^bandas? de lija', None, 'Herramientas', 'Lijas y accesorios de lijado', {'Discos de corte y desbaste'}),
    ('Herramientas', r'^lijadora', None, 'Herramientas', 'Lijadoras', {'Esmeriladoras y pulidoras'}),
    ('Herramientas', r'^pinzas?\b', None, 'Herramientas', 'Pinzas y alicates', {'Mangueras y riego'}),
    ('Herramientas', r'^esatto .{0,40}lavabo', None, 'Herramientas', 'Lavabos', {'Llaves y dados'}),
    ('Herramientas', r'^puerta de (chapa|madera|tambor)', r'cerradura|pestillo', 'Herramientas', 'Construcción',
     {'Cerraduras y chapas de puerta'}),
    ('Herramientas', r'^tarja', None, 'Herramientas', 'Tarjas y fregaderos', {'Medición'}),
    ('Herramientas', r'^timbre', None, 'Herramientas', 'Timbres', {'Baterías y cargadores de herramienta'}),
    ('Herramientas', r'^router', None, 'Herramientas', 'Routers, fresadoras y multiherramientas', {'Brocas para madera'}),
    ('Herramientas', r'^switch de presion', None, 'Herramientas', 'Bombas de agua', {'Jardinería'}),
    ('Herramientas', r'^quemador', None, 'Herramientas', 'Gas LP', {'Jardinería'}),
    ('Herramientas', r'^generador de nitrogeno', None, 'Autos y motos', 'Gatos y herramientas para auto', {'Medición'}),
    ('Herramientas', r'^matraca neumatica', None, 'Herramientas', 'Neumáticas', {'Juegos de herramientas'}),
    ('Herramientas', r'^soporte (de plastico |magnetico )?para dados', None, 'Herramientas', 'Organizadores de herramientas',
     {'Dados, matracas y autocles'}),
    ('Herramientas', r'^lanza (de |para )?hidrolav', None, 'Herramientas', 'Hidrolavadoras', {'Juegos de herramientas'}),
    ('Herramientas', r'^lanza para fumigador', None, 'Herramientas', 'Fumigadoras y pulverizadores', {'Juegos de herramientas'}),
    ('Herramientas', r'^plug rj ?45', None, 'Redes', 'Cables y adaptadores de red', {'Pinzas y alicates'}),
    ('Herramientas', r'alicates? (de|para) bomba de agua', None, 'Herramientas', 'Pinzas y alicates', {'Bombas de agua', 'Plomería'}),
    ('Herramientas', _P + r'(\d+ pzs )?codo', None, 'Herramientas', 'Tuberías y conexiones', {'Llaves y dados'}),
    ('Herramientas', r'^impermeabilizante', None, 'Herramientas', 'Construcción', {'Llaves y dados'}),
    ('Herramientas', r'^bisagra', None, 'Muebles', 'Herrajes y refacciones de muebles', {'Llaves y dados'}),
    ('Herramientas', r'^brocha', r'canina|perro|mascota|cunero', 'Herramientas', 'Construcción', {'Martillos, cinceles y mazos'}),
    ('Herramientas', r'^(\d+ )?(buje|flecha)\b.{0,80}\b(fs ?\d+|shindaiwa|desbrozadora)', None, 'Herramientas',
     'Desbrozadoras y desmalezadoras', {'Jardinería'}),
    ('Herramientas', r'^escuadra', None, 'Herramientas', 'Escuadras y reglas', {'Llaves y dados'}),
    ('Herramientas', r'^tira de impulso con flexometros', None, 'Herramientas', 'Cintas métricas y flexómetros', {'Llaves y dados'}),
    ('Herramientas', r'^tira de impulso con extensiones', None, 'Herramientas', 'Cables y extensiones eléctricas', {'Llaves y dados'}),
    ('Herramientas', r'^coladera', None, 'Herramientas', 'Plomería', {'Cerraduras y candados'}),
    ('Herramientas', r'^regulador', None, 'Cargadores y adaptadores', 'Regletas y multicontactos', {'Apagadores y contactos'}),
    ('Herramientas', r'^porta ?rollo', None, 'Herramientas', 'Sanitarios y accesorios de baño', {'Soldadura'}),
    ('Herramientas', r'^cespol', None, 'Herramientas', 'Plomería', {'Candados'}),
    ('Herramientas', r'onguard', None, 'Bicicletas y movilidad', 'Candados para bicicleta', {'Candados'}),
    # Deportes
    ('Deportes y fitness', r'^set de pesas', None, 'Deportes y fitness', 'Sets de pesas', {'Máquinas multifuncionales y poleas'}),
    ('Deportes y fitness', r'^set de \d+ pesas rusas', None, 'Deportes y fitness', 'Kettlebells', {'Bancos y racks'}),
    ('Deportes y fitness', r'^pesas discos', None, 'Deportes y fitness', 'Barras y discos', {'Bancos y racks'}),
    ('Deportes y fitness', r'^cuerda (de batalla|de azote)', None, 'Deportes y fitness', 'Accesorios de fuerza', {'Otros deportes'}),
    ('Deportes y fitness', r'^kit de costal', None, 'Deportes y fitness', 'Costales, peras y entrenadores', {'Guantes de box'}),
    ('Deportes y fitness', r'^tapa codera', None, 'Autopartes', 'Interior y tapicería'),
    ('Deportes y fitness', r'pastillas? (de )?limpieza.{0,30}(retenedor|dentadura)', None, 'Salud', 'Cuidado dental'),
    ('Deportes y fitness', r'^tacos? (puma|adidas|nike|under armour)', None, 'Deportes y fitness', 'Tachones de fútbol', {'Otros deportes'}),
    ('Deportes y fitness', r'^flechas?\b', None, 'Deportes y fitness', 'Otros deportes', {'Balones de fútbol'}),
    ('Deportes y fitness', r'^cuerda (de )?alpinismo', None, 'Deportes y fitness', 'Campismo'),
    ('Deportes y fitness', r'^tabla de equilibrio', None, 'Deportes y fitness', 'Tablas y balance', {'Bandas de resistencia'}),
    ('Deportes y fitness', r'^espinilleras?', None, 'Deportes y fitness', 'Espinilleras', {'Balones de fútbol'}),
    ('Deportes y fitness', r'^cartera', None, 'Bolsas y mochilas', 'Carteras y monederos', {'Patinetas y scooters'}),
    # Autos y motos
    ('Autos y motos', r'^tapon (de tanque )?(de )?gasolina', None, 'Autopartes', 'Carenados, plásticos y tanques', {'Motocicletas'}),
    ('Autos y motos', r'^balero', None, 'Autopartes', 'Baleros y mazas de rueda', {'Estéreos para auto'}),
    ('Autos y motos', r'^tapete', None, 'Autos y motos', 'Tapetes para auto', {'Estéreos para auto'}),
    ('Autos y motos', r'^soporte (de )?motor', None, 'Autopartes', 'Soportes de motor y transmisión', {'Estéreos para auto'}),
    ('Autos y motos', r'^espejo retrovisor', r'carplay|camara', 'Autopartes', 'Espejos laterales', {'Estéreos para auto'}),
    ('Autos y motos', r'^amplificador', r'valvulas|110 ?v', 'Autos y motos', 'Amplificadores para auto', {'Estéreos para auto'}),
    ('Autos y motos', r'^bujes? (de )?horquilla', None, 'Autopartes', 'Suspensión y dirección de moto', {'Motocicletas'}),
    ('Autos y motos', r'^bujes? de arranque', None, 'Autopartes', 'Motor, carburación y escape de moto', {'Motocicletas'}),
    ('Autos y motos', r'^(juego de )?valvulas?', None, 'Autopartes', 'Motor, carburación y escape de moto', {'Motocicletas'}),
    ('Autos y motos', r'^palanca', None, 'Autopartes', 'Palancas para moto', {'Motocicletas'}),
    ('Autos y motos', r'^\d* ?resortes? de parador', None, 'Autopartes', 'Soportes para moto', {'Motocicletas'}),
    ('Autos y motos', r'^candado', None, 'Autos y motos', 'Accesorios para moto', {'Motocicletas'}),
    ('Autos y motos', r'^lentes', None, 'Autos y motos', 'Accesorios para moto', {'Motocicletas'}),
    ('Autos y motos', r'^monopatin', None, 'Deportes y fitness', 'Patinetas y scooters', {'Motocicletas'}),
    ('Autos y motos', r'^garmin drivesmart|navegador gps', None, 'Autos y motos', 'Accesorios para auto', {'Dashcams y cámaras'}),
    ('Autos y motos', r'^toma coaxial', None, 'Herramientas', 'Placas y tapas eléctricas'),
    ('Autos y motos', r'^jersey ciclista', None, 'Bicicletas y movilidad', 'Ropa y calzado de ciclismo', {'Cascos para moto'}),
    ('Autos y motos', r'^(camisa|chamarra|jersey)', None, 'Autos y motos', 'Ropa para motociclista', {'Cascos para moto'}),
    ('Autos y motos', r'^prensa hidraulica', None, 'Herramientas', 'Herramientas de banco', {'Gatos y herramientas para auto'}),
    # Cámaras y joyería
    ('Cámaras y fotografía', r'^drone', None, 'Cámaras y fotografía', 'Drones', {'Accesorios'}),
    ('Cámaras y fotografía', r'^timbre', None, 'Cámaras de seguridad', 'Timbres inteligentes', {'Lentes'}),
    ('Cámaras y fotografía', r'^osmo mobile', None, 'Celulares', 'Tripiés y palos selfie', {'Cámaras de acción'}),
    ('Joyería y bisutería', r'^(set \d+ )?exhibidor', None, 'Joyería y bisutería', 'Joyeros', {'Collares'}),
]
REGLAS += LOTES['wb8']

# ---- Auditoría WB, lote 9 (26-sep-2026): grupos pendientes 299-399 (2 fichas) ----
# Causas: marcas que parecen palabras de la categoría («Casa del Anillo»,
# «El Gato» = Elgato, «Acuario Lomas», Gerber «gatito») y títulos de Walmart
# con dos productos pegados («Base para portabebé caldigit thunderbolt»).
LOTES['wb9'] = [
    # Joyería
    ('Joyería y bisutería', r'^bascula', None, 'Joyería y bisutería', 'Cuidado y herramientas', {'Relojes deportivos y digitales'}),
    ('Joyería y bisutería', r'^juego de punteria', None, 'Juguetes', 'Juguetes para exterior', {'Arras y sets'}),
    ('Joyería y bisutería', r'^(set de \d+ )?joyeros?\b', None, 'Joyería y bisutería', 'Joyeros', {'Arras y sets'}),
    ('Joyería y bisutería', r'^toallero', None, 'Herramientas', 'Sanitarios y accesorios de baño', {'Anillos'}),
    ('Joyería y bisutería', r'^medalla', None, 'Joyería y bisutería', 'Rosarios y medallas religiosas', {'Anillos'}),
    ('Joyería y bisutería', r'^estribo corrector', None, 'Salud', 'Movilidad y apoyo', {'Anillos'}),
    ('Joyería y bisutería', r'^vehiculo', None, 'Juguetes', 'Vehículos a control remoto', {'Pulseras'}),
    ('Joyería y bisutería', r'piedras acrilicas', None, 'Joyería y bisutería', 'Material para bisutería', {'Pulseras'}),
    ('Joyería y bisutería', r'^bandas (elegantes|tipo extensibles)', None, 'Joyería y bisutería', 'Correas para reloj', {'Aretes'}),
    ('Joyería y bisutería', r'^tiara', None, 'Joyería y bisutería', 'Broches y prendedores', {'Dijes y charms'}),
    ('Joyería y bisutería', r'dulceros', None, 'Juguetes', 'Artículos para fiestas', {'Dijes y charms'}),
    ('Joyería y bisutería', r'^pluma', None, 'Papelería y oficina', 'Escritura', {'Pulseras'}),
    # Juguetes
    ('Juguetes', r'\bfunko\b', None, 'Juguetes', 'Funko y coleccionables', {'Muñecas'}),
    ('Juguetes', r'^platos de fiesta', None, 'Juguetes', 'Artículos para fiestas', {'Bloques de construcción'}),
    ('Juguetes', r'decoracion.{0,30}fiesta|fiesta.{0,40}(decoracion|globos)|globos decoraciones', None, 'Juguetes',
     'Artículos para fiestas', {'Bloques de construcción'}),
    ('Juguetes', r'^andadera', None, 'Bebés', 'Andaderas', {'Vehículos de juguete'}),
    ('Juguetes', r'^lanzador', None, 'Juguetes', 'Juguetes para exterior', {'Bloques de construcción'}),
    ('Juguetes', r'^chupete', None, 'Bebés', 'Chupones y mordederas', {'Peluches'}),
    ('Juguetes', r'^juego de manualidades', None, 'Juegos de mesa', 'Manualidades y pintar por números', {'Peluches'}),
    # Bebés
    ('Bebés', r'^gerber traje de bano', None, 'Bebés', 'Ropa y calzado de bebé', {'Juguetes para bebé'}),
    ('Bebés', r'caldigit|thunderbolt', None, 'Componentes y accesorios de PC', 'Hubs y docks para PC', {'Portabebés y canguros'}),
    ('Bebés', r'^base para portabebes? para coche', None, 'Bebés', 'Sillas de auto', {'Portabebés y canguros'}),
    ('Bebés', r'^andadera', None, 'Bebés', 'Andaderas', {'Carriolas'}),
    ('Bebés', r'^(pack \d+ )?biberon', None, 'Bebés', 'Biberones', {'Carriolas', 'Alimentación y lactancia'}),
    # Mascotas
    ('Mascotas', r'^arena', None, 'Mascotas', 'Areneros', {'Juguetes para gato'}),
    ('Mascotas', r'^brazo (para |de )?microfono', None, 'Instrumentos musicales', 'Producción de audio'),
    ('Mascotas', r'^gerber', None, 'Bebés', 'Baño e higiene del bebé'),
    ('Mascotas', r'^cubre asiento', None, 'Mascotas', 'Transportadoras', {'Ropa para mascotas'}),
    ('Mascotas', r'^mascretta (tazon|tapete)', None, 'Mascotas', 'Platos y tazones para mascotas', {'Alimento para perro'}),
    ('Mascotas', r'^vela', None, 'Limpieza y hogar', 'Aromatizantes y velas', {'Areneros'}),
    ('Mascotas', r'^maceta', None, 'Jardín y exterior', 'Macetas y jardineras', {'Areneros'}),
    ('Mascotas', r'^casa (transparente|de valla|plegable)', None, 'Mascotas', 'Corrales y rejas para mascotas',
     {None, 'Jaulas para perro'}),
    ('Mascotas', r'^casa (para|de) (interior|perro|gato)', None, 'Mascotas', 'Casas para mascotas', {None, 'Jaulas para perro'}),
    ('Mascotas', r'^tabla de bambu', None, 'Cocina y comedor', 'Tablas para picar', {'Platos y tazones para mascotas'}),
    ('Mascotas', r'^gorra', None, 'Ropa y accesorios', 'Gorras y sombreros', {None}),
    ('Mascotas', r'^transportadora', None, 'Mascotas', 'Transportadoras', {'Ropa para mascotas'}),
    ('Mascotas', r'^vinil', None, 'Decoración de hogar y jardín', 'Vinil decorativo', {'Ropa para mascotas'}),
    ('Mascotas', r'^carrito .{0,30}mascota', None, 'Mascotas', 'Transportadoras', {None}),
    ('Mascotas', r'^bandanas?', None, 'Mascotas', 'Ropa para mascotas', {'Disfraces para mascotas'}),
    ('Mascotas', r'^cuenco', None, 'Mascotas', 'Platos y tazones para mascotas', {'Camas elevadas y colchonetas'}),
    ('Mascotas', r'^faja', None, 'Herramientas', 'Seguridad industrial', {'Correas'}),
    ('Mascotas', r'^repuesto pasto', None, 'Mascotas', 'Higiene y limpieza', {None}),
    # Papelería y electrodomésticos
    ('Papelería y oficina', r'^engrapadora', None, 'Papelería y oficina', 'Artículos de oficina', {'Organización'}),
    ('Electrodomésticos', r'^kit de repuestos?', None, 'Electrodomésticos', 'Filtros y membranas de repuesto',
     {'Purificadores bajo tarja'}),
    ('Electrodomésticos', r'^sarten', None, 'Cocina y comedor', 'Sartenes y comales', {'Estufas'}),
    ('Electrodomésticos', r'air fryer (toaster )?(smart )?oven|oven combo', r'accessory|accesorio', 'Electrodomésticos',
     'Hornos freidora y multifunción', {'Freidoras de aire'}),
    ('Electrodomésticos', r'^\d+ platos', None, 'Cocina y comedor', 'Platos y bowls', {'Pequeños electrodomésticos de cocina'}),
]
REGLAS += LOTES['wb9']

# ---- Auditoría WB, lote 10 (26-sep-2026): electrodomésticos, cocina, muebles y autopartes ----
LOTES['wb10'] = [
    # Electrodomésticos
    ('Electrodomésticos', r'^(mini )?plancha', None, 'Electrodomésticos', 'Planchas', {'Máquinas de coser'}),
    ('Electrodomésticos', r'^olla de coccion lenta', None, 'Electrodomésticos', 'Arroceras y ollas multiusos', {'Hornos'}),
    ('Electrodomésticos', r'^jarra electrica', None, 'Electrodomésticos', 'Hervidores y teteras eléctricas', {'Licuadoras'}),
    ('Electrodomésticos', r'^(mini )?procesador', None, 'Electrodomésticos', 'Molinos y procesadores', {'Extractores de jugo'}),
    ('Electrodomésticos', r'^aspas?\b', None, 'Electrodomésticos', 'Refacciones para licuadora y batidora', {'Licuadoras'}),
    ('Electrodomésticos', r'^sombrilla', None, 'Ropa y accesorios', 'Paraguas', {'Filtros y membranas de repuesto'}),
    ('Electrodomésticos', r'^comic', None, 'Libros', 'Cómics y novela gráfica', {'Wafleras, sandwicheras y creperas'}),
    ('Electrodomésticos', r'^comal', None, 'Cocina y comedor', 'Comales y planchas', {'Estufas'}),
    ('Electrodomésticos', r'^lapicera', None, 'Papelería y oficina', 'Útiles escolares', {'Pequeños electrodomésticos de cocina'}),
    ('Electrodomésticos', r'^regulador de voltaje', None, 'Cargadores y adaptadores', 'Regletas y multicontactos',
     {'Filtros para refrigerador y cafetera'}),
    # Cocina y comedor
    ('Cocina y comedor', r'^juego de cocina', r'juguete|ninos?|ninas?|infantil', 'Cocina y comedor', 'Baterías de cocina',
     {'Utensilios de cocina'}),
    ('Cocina y comedor', r'^plancha para termos', None, 'Equipo comercial', 'Prensas de calor', {'Termos y botellas térmicas'}),
    ('Cocina y comedor', r'^(\d+ )?moldes?\b', None, 'Cocina y comedor', 'Repostería y moldes', {'Platos y bowls', 'Ollas y cacerolas'}),
    ('Cocina y comedor', r'^manteles?', None, 'Cocina y comedor', 'Manteles y caminos de mesa', {'Utensilios de cocina'}),
    ('Cocina y comedor', r'molinos? (de sal|pimentero)|^molinillos? de sal', None, 'Cocina y comedor', 'Utensilios de cocina',
     {'Platos y bowls'}),
    ('Cocina y comedor', r'^porta (c-\d+ )?anfora', None, 'Bicicletas y movilidad', 'Accesorios para bicicleta', {'Botellas de agua'}),
    ('Cocina y comedor', r'^(porta hielo|molde)', None, 'Cocina y comedor', 'Repostería y moldes', {'Botellas de vidrio y plástico'}),
    ('Cocina y comedor', r'taza de vidrio', None, 'Cocina y comedor', 'Tazas', {'Contenedores herméticos'}),
    ('Cocina y comedor', r'^(juego de )?biberon', None, 'Bebés', 'Biberones', {'Botellas de vidrio y plástico'}),
    ('Cocina y comedor', r'^prensa francesa', None, 'Cafeteras', 'Manuales', {'Ollas y cacerolas'}),
    # Muebles
    ('Muebles', r'^centro de juego inflable', None, 'Jardín y exterior', 'Albercas e inflables', {'Mesas de centro'}),
    ('Muebles', r'^set (de )?\d+ buros', None, 'Muebles', 'Burós', {'Sillones y reclinables', 'Colchones matrimoniales'}),
    ('Muebles', r'^cantina', None, 'Muebles', 'Mesas altas y de bar', {'Mesas de comedor', 'Taburetes y bancos'}),
    ('Muebles', r'^andador', None, 'Salud', 'Andaderas, bastones y muletas', {'Sillas de oficina', 'Sillas plegables y de camping'}),
    ('Muebles', r'^set sala', None, 'Muebles', 'Salas completas', {'Sillones reclinables'}),
    ('Muebles', r'^base (individual )?kessa', None, 'Muebles', 'Bases de cama y box', {'Sillones y reclinables'}),
    ('Muebles', r'^sala (exterior|jardin)', None, 'Muebles', 'Sillas de exterior', {'Sillas plegables y de camping'}),
    ('Muebles', r'^bancos?\b', None, 'Muebles', 'Taburetes y bancos', {'Mesas de centro', 'Sillas de oficina'}),
    ('Muebles', r'cocina integral', None, 'Muebles', 'Cocinas integrales', {'Roperos'}),
    ('Muebles', r'^base para sombrilla', None, 'Jardín y exterior', 'Sombrillas, toldos y carpas', {'Sillas plegables y de camping'}),
    ('Muebles', r'^litera', None, 'Muebles', 'Literas', {'Cabeceras'}),
    ('Muebles', r'^portarrollos', None, 'Cocina y comedor', 'Organización de cocina', {'Alacenas y gabinetes de cocina'}),
    ('Muebles', r'^piston', None, 'Muebles', 'Accesorios y refacciones para sillas', {'Sillas de oficina'}),
    ('Muebles', r'^"?base soporte laptop', None, 'Muebles', 'Mesas para laptop y de cama', {'Sillas ergonómicas'}),
    ('Muebles', r'^espejo', None, 'Decoración de hogar y jardín', 'Espejos de cuerpo completo', {'Sillas de comedor'}),
    ('Muebles', r'^vela', None, 'Limpieza y hogar', 'Aromatizantes y velas', {'Sofás cama'}),
    ('Muebles', r'^"?especiero', None, 'Cocina y comedor', 'Organización de cocina', {'Alacenas y gabinetes de cocina'}),
    ('Muebles', r'^base plegable', None, 'Muebles', 'Bases de cama y box', {'Camas plegables y catres'}),
    ('Muebles', r'^isla', None, 'Muebles', 'Carros e islas de cocina', {'Alacenas y gabinetes de cocina'}),
    ('Muebles', r'^zapatera', None, 'Muebles', 'Zapateras', {'Repisas'}),
    ('Muebles', r'almohadas? (de )?(viaje|camping)', None, 'Viajes', 'Accesorios de viaje', {'Sillas plegables y de camping'}),
    ('Muebles', r'para globos', None, 'Juguetes', 'Artículos para fiestas', {'Mesas auxiliares y laterales'}),
    ('Muebles', r'^manteles?', None, 'Cocina y comedor', 'Manteles y caminos de mesa', {'Mesas de comedor para exterior'}),
    ('Muebles', r'^cajonera', None, 'Muebles', 'Cómodas y cajoneras', {'Colchones matrimoniales'}),
    ('Muebles', r'arbol (de )?navidad', None, 'Decoración de hogar y jardín', 'Navidad y temporada', {'Mesas auxiliares y laterales'}),
    # Autopartes
    ('Autopartes', r'^plato opresor', None, 'Autopartes', 'Clutch y embrague', {'Motor y transmisión'}),
    ('Autopartes', r'llave de cadena', None, 'Herramientas', 'Llaves ajustables y stilson', {'Llaves y cerraduras de auto'}),
    ('Autopartes', r'^hule amortiguador engrane', None, 'Autopartes', 'Cadenas, sprockets y transmisión',
     {'Suspensión y dirección', 'Amortiguadores'}),
    ('Autopartes', r'^(condensador de enfriamiento|marco de radiador)', None, 'Autopartes', 'Radiadores y condensadores',
     {'Motor, carburación y escape de moto'}),
    ('Autopartes', r'^solenoide tiempo variable', None, 'Autopartes', 'Válvulas, punterías y árbol de levas',
     {'Terminales de dirección'}),
    ('Autopartes', r'caster.{0,3}camber', None, 'Autopartes', 'Suspensión y dirección', {'Motor y transmisión'}),
    ('Autopartes', r'^tapa de (gasolina|motor)', None, 'Autopartes', 'Tapones, cárter y tapas de motor', {'Enfriamiento y climatización'}),
    ('Autopartes', r'^toma (de )?agua', None, 'Autopartes', 'Tomas de agua y termostatos', {'Sensores de temperatura'}),
    ('Autopartes', r'^bisel', None, 'Autopartes', 'Faros', {'Bujías y encendido'}),
    ('Autopartes', r'^horquilla oscilante', None, 'Autopartes', 'Suspensión y dirección de moto', {'Suspensión y dirección'}),
    ('Autopartes', r'bicicleta', None, 'Bicicletas y movilidad', 'Accesorios para bicicleta', {'Claxon'}),
    ('Autopartes', r'hueso para caja de velocidades', None, 'Autopartes', 'Motor y transmisión', {'Para autos'}),
    ('Autopartes', r'^jgo (\d+ )?amortiguadores', None, 'Autopartes', 'Amortiguadores', {'Suspensión y dirección'}),
    ('Autopartes', r'^brazos? (lateral|toledo)', None, 'Autopartes', 'Horquillas y brazos de suspensión',
     {'Carenados, plásticos y tanques'}),
    ('Autopartes', r'^soporte (de )?faro', r'chevy|karparts|\d\d-\d\d', 'Autopartes', 'Luces de moto', {'Faros'}),
    ('Autopartes', r'^jaladera', None, 'Autopartes', 'Manijas y chapas', {'Faros y luces', 'Frenos'}),
    ('Autopartes', r'^maza (rueda|trasera|delantera)', r'honda (gl|cg|cgl)|italika|\(\d\d-\d\d\)', 'Autopartes',
     'Baleros y mazas de rueda', {'Suspensión y dirección'}),
    ('Autopartes', r'^puerta', None, 'Autopartes', 'Cofres, puertas y bisagras', {'Carenados, plásticos y tanques'}),
    ('Autopartes', r'^kit distribucion', None, 'Autopartes', 'Cadenas y kits de distribución', {'Bandas'}),
]
REGLAS += LOTES['wb10']

# ---- Auditoría WB, lote 11 (26-sep-2026): autopartes, belleza, climatización y varios ----
# Causas: palabras del título leídas como tipo de producto («spf» en un
# subwoofer DB Drive, «secado rápido» en un esmalte, «cargador ergonómico» en
# una cangurera, «tv box» como televisor).
LOTES['wb11'] = [
    ('Autopartes', _P + r'tapon grasera', None, 'Autopartes', 'Baleros y mazas de rueda', {'Frenos'}),
    ('Autopartes', r'pluma limpiaparabrisas', None, 'Autopartes', 'Limpiaparabrisas', {'Motor y transmisión'}),
    ('Autopartes', r'^(juego de )?coderas?\b', None, 'Autopartes', 'Interior y tapicería',
     {'Para autos', 'Carrocería, espejos y molduras'}),
    ('Componentes y accesorios de PC', r'^yeti', None, 'Deportes y fitness', 'Campismo', {'Enfriamiento y ventiladores'}),
    ('Belleza y cuidado personal', r'^hilo liston', None, 'Juguetes', 'Artículos para fiestas', {'Rizadores'}),
    ('Belleza y cuidado personal', r'^subwoofer', None, 'Autos y motos', 'Subwoofers para auto', {'Protección solar'}),
    ('Belleza y cuidado personal', r'^brillo de labios', None, 'Belleza y cuidado personal', 'Brillos labiales (gloss)',
     {'Protección solar'}),
    ('Belleza y cuidado personal', r'^brocha', None, 'Belleza y cuidado personal', 'Brochas y esponjas', {'Protección solar'}),
    ('Belleza y cuidado personal', r'^(pack \d+ )?delineador', None, 'Belleza y cuidado personal', 'Sombras y delineadores',
     {'Cremas y sérums faciales'}),
    ('Belleza y cuidado personal', r'^esmalte', None, 'Belleza y cuidado personal', 'Uñas', {'Secadoras de cabello'}),
    ('Belleza y cuidado personal', r'velas de soya|^kit \d+ velas', None, 'Limpieza y hogar', 'Aromatizantes y velas',
     {'Sets de perfume'}),
    ('Belleza y cuidado personal', r'^marcadores', None, 'Papelería y oficina', 'Arte y dibujo', {'Uñas'}),
    ('Climatización', r'^soplador', None, 'Climatización', 'Extractores y ventilación', {'Calefactores cerámicos y de aire'}),
    ('Climatización', r'^secador de manos', None, 'Herramientas', 'Sanitarios y accesorios de baño', {'Purificadores de aire'}),
    ('Calzado', r'^zapatos acuaticos', None, 'Deportes y fitness', 'Zapatos acuáticos', {'Tenis para niña'}),
    ('Libros', r'power rangers.{0,40}(cover|boom)', None, 'Libros', 'Cómics y novela gráfica', {'Novela contemporánea'}),
    ('Audífonos', r'^kit smartwatch', None, 'Relojes inteligentes', 'Smartwatches', {'Earbuds inalámbricos'}),
    ('Audífonos', r'^pilas', None, 'Cargadores y adaptadores', 'De pilas', {'Earbuds inalámbricos'}),
    ('Decoración de hogar y jardín', r'^esatto', None, 'Muebles', 'Muebles de baño', {'Espejos decorativos de pared'}),
    ('Decoración de hogar y jardín', r'sp connect|montaje de radar', None, 'Autos y motos', 'Accesorios para moto',
     {'Espejos decorativos de pared'}),
    ('Jardín y exterior', r'^fumigador', None, 'Herramientas', 'Fumigadoras y pulverizadores', {'Riego y mangueras'}),
    ('Cafeteras', r'^mini termo', None, 'Cocina y comedor', 'Termos y botellas térmicas', {'Espresso'}),
    ('Cargadores y adaptadores', r'^cangurera porta ?bebes', None, 'Bebés', 'Portabebés y canguros', {'De pared'}),
    ('Limpieza y hogar', r'^tonyin', None, 'Autos y motos', 'Limpieza y cuidado del auto', {'Limpiadores y desinfectantes'}),
    ('Limpieza y hogar', r'^(ms )?shampoo insecticida', None, 'Mascotas', 'Higiene y limpieza', {'Insecticidas y repelentes'}),
    ('Televisores', r'^(xiaomi )?tv box\b', None, 'Televisores', 'Dispositivos de streaming'),
]
REGLAS += LOTES['wb11']

# ---- Auditoría WB, lote 12 (26-sep-2026): cabezas que se repitieron en la
# revisión ficha por ficha (grupos de 1). Dentro de Herramientas el comodín
# de la tienda caía en cualquier subcategoría; el nombre de la pieza decide.
_H_TODAS = None   # cualquier subcategoría de Herramientas
LOTES['wb12'] = [
    ('Herramientas', _P + r'(despachador|dispensador) (automatico )?de jabon|^porta ?jabon|^toallero|^percha .{0,20}pared|^manija .{0,25}\bwc\b',
     None, 'Herramientas', 'Sanitarios y accesorios de baño', _H_TODAS),
    ('Herramientas', _P + r'(pack de \d+ )?soporte (reforzado )?(para )?lavabo', None, 'Herramientas', 'Lavabos', _H_TODAS),
    ('Herramientas', r'^piedra (para )?esmeril', None, 'Herramientas', 'Discos de corte y desbaste', _H_TODAS),
    ('Herramientas', r'^(pack \d+ )?brochas?\b', r'maquillaje|facial|dental|barba|canina|perro|mascota|cunero', 'Herramientas', 'Construcción', _H_TODAS),
    ('Herramientas', r'^rastrillo (afeitar|con cabezal)', None, 'Belleza y cuidado personal', 'Rasuradoras', _H_TODAS),
    ('Herramientas', r'^marcadores? (permanentes?|de doble punta)|sharpie', None, 'Papelería y oficina', 'Escritura', _H_TODAS),
    ('Herramientas', r'^(pack de \d+ )?lijas?\b', r'lijadora', 'Herramientas', 'Lijas y accesorios de lijado', _H_TODAS),
    ('Herramientas', r'^timbre', r'para bicicleta', 'Herramientas', 'Timbres', _H_TODAS),
    ('Herramientas', r'^hidrolavadora', r'repuesto|pistola|lanza|manguera|boquilla', 'Herramientas', 'Hidrolavadoras', _H_TODAS),
    ('Herramientas', r'^(combo )?(mini)?esmeriladora', r'neumatic|disco|repuesto|carbon', 'Herramientas', 'Esmeriladoras y pulidoras', _H_TODAS),
    ('Herramientas', r'^pulidora', r'neumatic|repuesto|bonete|disco', 'Herramientas', 'Esmeriladoras y pulidoras', _H_TODAS),
    ('Herramientas', r'^fumigadora?\b', r'empaque|repuesto|anillo|lanza|boquilla', 'Herramientas', 'Fumigadoras y pulverizadores', _H_TODAS),
    ('Herramientas', r'^soplador(a)? (de hojas|recargable|compacto|inalambric)', None, 'Herramientas', 'Sopladoras', _H_TODAS),
    ('Herramientas', r'^motosierra', r'repuesto|cadena|espada|tapa|careta|hierro fundido|afilador|guia', 'Herramientas', 'Motosierras', _H_TODAS),
    ('Herramientas', r'^rotomartillo|^martillo (perforador|demoledor)', r'\+|combo|repuesto|broca', 'Herramientas', 'Rotomartillos', _H_TODAS),
    ('Herramientas', r'^generador (de corriente|electrico|inverter)', None, 'Herramientas', 'Generadores', _H_TODAS),
    ('Herramientas', r'^(juego de )?(\d+ )?dados? (de impacto|en pulgadas|con puntas|hexagonales|\d)', r'tarraja', 'Herramientas',
     'Dados, matracas y autocles', _H_TODAS),
]
REGLAS += LOTES['wb12']


if __name__ == '__main__':
    main()
