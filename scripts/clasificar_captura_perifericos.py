#!/usr/bin/env python3
"""Clasifica una captura de Amazon de periféricos y componentes de PC.

La captura del 11-sep-2026 mezcló webcams, soportes de monitor, gabinetes,
enfriadores, RAM y la cola de la búsqueda "periféricos", que Amazon rellenó
con seguros Assurant, catéteres y espadas de utilería; la segunda tanda
trajo mini PC, all-in-one y escritorios de oficina, y la tercera Mac mini,
soportes para mini PC, un monitor portátil y una MacBook; la cuarta,
televisores; la quinta, pantallas de proyección; la sexta, lavadoras; la
séptima, aspiradoras; la octava, refrigeradores, y la novena, secadoras de
cabello. Este script la reparte entre "Componentes y accesorios de PC",
"Videojuegos / Accesorios", "Computadoras de escritorio",
"Muebles / Escritorios", "Monitores", "Laptops", "Televisores",
"Proyectores y accesorios", "Lavadoras", "Aspiradoras", "Refrigeradores" y
"Aparatos de belleza".

La captura de lavadoras llega casi entera de accesorios: de 64 anuncios,
la mayoría son fundas, pastillas de limpieza y refacciones (interruptores
de tapa, filtros de pelusa, juegos de suspensión, mangueras). El aparato
mismo son 22.

La de aspiradoras, al revés, llega casi entera de aparatos: 28 anuncios, y
solo se cuelan un kit de limpieza de ductos, un soporte para Dyson, una
licuadora y un anuncio sin título. Los dos accesorios no se descartan: el
catálogo ya tiene "Aspiradoras / Accesorios y repuestos" para ellos.

La octava sección son refrigeradores, con una cola de cuatro anuncios de
café por delante. De los 62 anuncios, 29 son el aparato (refrigeradores,
frigobares, un congelador y cinco exhibidores comerciales) y el resto son
cosas que solo dicen "refrigerador" de pasada: seis filtros de agua de
repuesto, cuatro refacciones, nueve trastes de cocina y tres desodorantes.
Cada grupo va a donde el catálogo ya los tiene: los filtros y las piezas a
"Refacciones / Refacciones para electrodomésticos", los trastes a
"Otros / Varios" (donde ya están los contenedores de alimentos y las bolsas
reutilizables) y las vitrinas de mostrador a "Equipo comercial /
Refrigeración comercial", que el catálogo separa del refrigerador vertical
de puerta de cristal ("Refrigeradores / Uso comercial").

La novena son secadoras de cabello: 100 anuncios y ningún descarte, porque
Amazon no rellenó la sección con nada ajeno. La palabra "secadora" sola no
alcanza -- la de ropa se llama igual --, así que la regla pide que el título
nombre además el pelo o lo que se le hace (rizos, frizz, difusor, iones,
turmalina), o que la marca sea de peluquería. Van a "Aparatos de belleza /
Secadoras de cabello", junto a los cepillos secadores y los
multiestilizadores que el catálogo ya tiene ahí.

Mismo criterio que las capturas anteriores: la categoría se decide por lo
que el título dice; lo que no encaja se descarta con su motivo y lo dudoso
se resuelve a mano en EXPLICITOS, nunca por parecido.
"""
import collections, io, json, re, sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import capacidad_mah

def T(s):
    s = re.sub(r'\s+', ' ', s.lower())
    # La diéresis cuenta: sin ella "desagüe" no casa con "desague".
    return s.translate(str.maketrans('áéíóúñü', 'aeiounu'))

# Lo que descalifica en cualquier parte del título.
FUERA = [
 (re.compile(r'^amazon renewed$'), 'el título no nombra ningún producto'),
 (re.compile(r'\bassurant\b'), 'seguro de daños, no es un producto'),
 (re.compile(r'\bcateter'), 'material médico, no es periférico de PC'),
 (re.compile(r'baaske medical'), 'accesorio médico sin categoría'),
 (re.compile(r'tapones auditivos'), 'protección auditiva, no reproduce audio'),
 (re.compile(r'chaleco'), 'batería para ropa calefactable'),
 (re.compile(r'18650|21700'), 'carcasa para armar, sin celdas'),
 (re.compile(r'para gafas|gafas inteligentes|rayban meta'), 'batería para un aparato concreto'),
 (re.compile(r'espada|dune ii|dientes de gusano'), 'utilería/merchandising'),
 (re.compile(r'generador portatil de linea de escaneo'), 'no se entiende qué producto es'),
 (re.compile(r'cargador portatil de bateria para swyop'), 'no se entiende qué producto es'),
 (re.compile(r'soporte (de pared )?(de|para) tv|soporte de tv rodante'),
  'soporte de TV: el catálogo no tiene esa subcategoría'),
 (re.compile(r'cubierta de tv'), 'accesorio: protector/cubierta'),
 (re.compile(r'retroiluminacion para tv'), 'tira de luces, no es el aparato'),
 # Refacciones y consumibles de lavadora. Van en FUERA (no en CABECERA)
 # porque en estos títulos la pieza se nombra donde caiga: "Kit de
 # reemplazo de eje de montaje y rodamiento de bañera para lavadora".
 (re.compile(r'interruptor de bloqueo|interruptor bloqueo|bloqueo de (la )?tapa|'
             r'filtros? de pelusa|juego suspension|barras? de suspension|'
             r'eje de montaje y rodamiento|manguera.{0,20}(drenado|desague)|'
             r'colector de pelo|temporizador de lavadora|interruptor de temporizador|'
             r'tapa giratoria|tapa de centrifugado|'
             r'resorte (para puerta|de apertura)|reductores de eje'),
  'refacción de lavadora, no es el aparato'),
 # Un paquete de dos electrodomésticos no se puede comparar contra una
 # lavadora sola: el precio es de los dos.
 (re.compile(r'lavadora.*\+.*(frigobar|refrigerador|microondas|secador|lavadora|'
             r'semi-?automatica|\d+ ?kg)|'
             r'(frigobar|refrigerador|microondas)\b.*\+.*lavadora'),
  'paquete de dos aparatos, no es un producto comparable'),
 (re.compile(r'lavadora de huevos'), 'lavadora de huevos, no lava ropa'),
 (re.compile(r'^for lavadora'), 'el título no dice qué producto es'),
 (re.compile(r'pastillas? (limpiadoras?|para limpiar|para lavar)|'
             r'tabletas de lavado|tabletas efervescentes'),
  'consumible de limpieza, no es el aparato'),
 (re.compile(r'^base para lavadora|base ajustable para refrigerador'),
  'base con ruedas, no es el aparato'),
 # No es una lavadora: una turbina que se mete en un balde con la ropa.
 (re.compile(r'(lavadora|washer).{0,40}(ultrasonic|turbo usb|turbina)|'
             r'mini lavadora de turbina|washer turbine'),
  'turbina que se mete en un recipiente, no es una lavadora'),
 # Consumibles del refri y de la cafetera: se gastan, no se comparan contra
 # el aparato. Mismo criterio que las pastillas para lavadora.
 (re.compile(r'filtros? de papel'), 'consumible, no es el aparato'),
 (re.compile(r'desodorante para refrigerador|desodorante refrigerador|'
             r'elimina los olores de tu refri'),
  'desodorante, no es el aparato'),
]
# Lo que descalifica solo si va al PRINCIPIO del título: ahí Amazon pone lo
# que el producto ES. Más adelante viene la lista de características, y ahí
# "cubierta de privacidad" describe un detalle de una webcam, "tornillos"
# lo que trae un tanque de refrigeración y "Funda para juegos" es la segunda
# mención de un gabinete mal traducido.
CABECERA = [
 # "Funda para PC" y "Carcasa para computadora" son gabinetes mal traducidos;
 # el resto de fundas y carcasas son accesorios.
 (re.compile(r'\bfunda de viaje|\bfunda (?!para pc\b)|\bestuche\b|'
             r'\bcarcasa (?!(para|de|del) (pc|computadora|ordenador)\b)|'
             r'co2crea'), 'accesorio: funda/estuche/carcasa'),
 (re.compile(r'protector (de )?pantalla|bisel ahuecado|keyboard skin|'
             r'cubierta (deslizante|de camara|camara web|webcam|universal)|webcam cover|'
             r'obturador de privacidad|tapa de privacidad'), 'accesorio: protector/cubierta'),
 # Salvo cuando el título abre nombrando el aparato: "Aspiradora de Agua,
 # Limpiador de Tapicería" es una aspiradora, y el catálogo ya trae la
 # limpiadora de tapicería Teendow C6 MAX en Aspiradoras.
 (re.compile(r'^(?!aspirador)(?=.*(?:limpiador|kit de limpieza|kit limpiador))'),
  'kit de limpieza, no es el aparato'),
 # Solo al principio: una pantalla de proyección motorizada "con control
 # remoto" lo trae de accesorio.
 (re.compile(r'control remoto'), 'control remoto de repuesto, no es el aparato'),
 (re.compile(r'bateria de repuesto|bateria for portatil|repuesto para el altavoz|'
             r'cable de repuesto|adaptadores tipo c de repuesto|thumbsticks de repuesto|'
             r'lente optica|modulo camara|pegatinas|huano switches|corepad|'
             r'modulo de de mando'), 'repuesto o pieza suelta de otro aparato'),
 (re.compile(r'\btornillo'), 'tornillería'),
 (re.compile(r'de tecla esc|keycap'), 'una tecla suelta'),
 (re.compile(r'bolsa de almacenamiento'), 'bolsa, no es el aparato'),
 # "Cubre Lavadora", "Protector Superior de Silicona": las fundas de
 # lavadora que no empiezan con la palabra "Funda".
 (re.compile(r'cubre lavadora|cubierta de lavadora|protector superior'),
  'accesorio: funda/estuche/carcasa'),
 # Una lavadora de verdad también menciona sus perillas de control, pero
 # más adelante, entre las características; el juego de repuesto las
 # nombra al principio porque es lo que se vende.
 (re.compile(r'perillas de control'), 'refacción de lavadora, no es el aparato'),
]

PC   = 'Componentes y accesorios de PC'
VJ   = ('Videojuegos', 'Accesorios', 'gamepad')
PERI = (PC, 'Periféricos y accesorios', 'cpu')
COMP = (PC, 'Componentes', 'cpu')

REGLAS = [
 # Lavadoras antes que todo: lo que queda después de quitar fundas,
 # pastillas y refacciones es el aparato. Incluye la centrifugadora suelta,
 # que el catálogo ya trae (Koblenz SCK-60, HKPRO HK-37) sin subcategoría
 # porque su título tampoco dice "secadora".
 (re.compile(r'\blavadora|\blava\w*secadora|\bcentrifugadora'), ('Lavadoras', None, 'washer')),
 # Aspiradoras: el título siempre nombra el aparato ("aspiradora", "aspirador",
 # "robot aspirador", "shop vac"). La licuadora que Amazon metió en la sección
 # se va a su categoría de siempre, no a Aspiradoras.
 (re.compile(r'\blicuadora'), ('Electrodomésticos', 'Licuadoras y extractores', 'appliance')),
 (re.compile(r'\baspirador|shop vac|wet/?dry shop'), ('Aspiradoras', None, 'vacuum')),
 # Secadoras de cabello. "Secadora" a secas es ambigua -- la de ropa se llama
 # igual -- así que el título tiene que nombrar además el pelo o lo que se le
 # hace: rizos, frizz, difusor, iones, turmalina, peinado. El catálogo las
 # tiene en Aparatos de belleza, junto con los cepillos secadores y los
 # multiestilizadores (el Dyson Airwrap, el SUTRA Aero Styler 5 en 1).
 (re.compile(r'^(?=.*\bsecador)(?=.*(cabello|\bpelo\b|peinad|rizo|frizz|difusor|'
             r'alaciadora|ionic|iones|turmalina|estiliz|salon))'),
  ('Aparatos de belleza', 'Secadoras de cabello', 'sparkle')),
 # Cuatro marcas que solo hacen aparatos de peluquería. Cuando el título se
 # queda en "Conair Secadora 289es" o "Hot Tools Secador Silencioso 1875 W",
 # la marca es lo único que queda, y basta: la secadora de ropa la venden
 # Whirlpool, Mabe y LG, no BaByliss.
 (re.compile(r'^(?=.*\bsecador)(?=.*(conair|babyliss|remington|hot tools))'),
  ('Aparatos de belleza', 'Secadoras de cabello', 'sparkle')),
 # Lo que ya no puede ser otra cosa: el cepillo que seca, el título en inglés
 # y la secadora de viaje (la de ropa no viaja).
 (re.compile(r'cepillo secador|hair dryer|secador(a)? de viaje'),
  ('Aparatos de belleza', 'Secadoras de cabello', 'sparkle')),
 # Refrigeradores. Antes del aparato van las piezas y los trastes que también
 # dicen "refrigerador": si no, un filtro de agua de repuesto acaba de refri.
 # Los seis filtros de la captura abren el título con la palabra "Filtro".
 (re.compile(r'^filtro\b.{0,60}refrigerador'),
  ('Refacciones', 'Refacciones para electrodomésticos', 'gear')),
 # Piezas sueltas: el relé del compresor, el cable de corriente, la tapa del
 # cajón y la bomba que alimenta la línea de agua del refri.
 (re.compile(r'rele de arranque|cable de alimentacion de refrigerador|'
             r'^tapa cajon|dispensador automatico para refrigerador'),
  ('Refacciones', 'Refacciones para electrodomésticos', 'gear')),
 # Trastes de cocina que se venden "para el refri". El catálogo ya tiene los
 # contenedores de alimentos y las bolsas reutilizables en Otros / Varios.
 (re.compile(r'organizador(es)? (de|para) (refrigerador|nevera)|'
             r'contenedores? para refrigerador|soporte para huevos|'
             r'organizadores antideslizantes para latas|bolsas de aluminio|'
             r'forro para estantes|revestimientos? (de gabinete|antideslizantes)'),
  ('Otros', 'Varios', 'box')),
 # La vitrina de mostrador es equipo de negocio y el refrigerador vertical de
 # puerta de cristal es un refri de uso comercial: el catálogo los separa así
 # ("Vitrina Refrigerada Sobre Mostrador Rtw100l" contra "Refrigerador
 # Exhibidor Rhino de 415.6 L"). La vitrina va antes porque varias también
 # se anuncian como "Exhibidor Comercial".
 (re.compile(r'vitrina (refrigerada|fria)'),
  ('Equipo comercial', 'Refrigeración comercial', 'snowflake')),
 (re.compile(r'\brefrigerador|\bfrigobar|\bnevera\b|cava de vino|enfriador de vino'),
  ('Refrigeradores', None, 'fridge')),
 (re.compile(r'freidora de aire'), ('Electrodomésticos', 'Freidoras de aire', 'appliance')),
 (re.compile(r'hervidor|tetera electrica'),
  ('Electrodomésticos', 'Pequeños electrodomésticos de cocina', 'appliance')),
 (re.compile(r'computadora escritorio (completa|amd|intel)|pc gamer factor'),
  ('Computadoras de escritorio', 'Torre / Escritorio', 'desktop')),
 # Solo si "laptop" abre el título: "power bank para laptop" y "soporte para
 # monitor y laptop" la nombran como destino, no como producto.
 (re.compile(r'^laptop\b|macbook (pro|air)'), ('Laptops', None, 'laptop')),
 # Pantallas de proyección antes que las TV: también se venden como
 # "Pantalla 100 pulgadas", pero dicen proyección/proyector, "lienzo",
 # "eléctrica" (la que se enrolla con motor) o traen trípode. Un proyector
 # propiamente dicho abre el título con esa palabra.
 (re.compile(r'proyec(cion|tor)|lienzo de proyec|pantalla electrica|'
             r'pantalla de 16:9|projector screen'),
  ('Proyectores y accesorios', 'Pantallas de proyección', 'projector')),
 (re.compile(r'^(?:\S+ ){0,2}proyector'), ('Proyectores y accesorios', 'Proyectores', 'projector')),
 # Televisores: "pantalla NN pulgadas" es como Amazon México nombra una TV;
 # "Pantalla 4K" de un mini PC no cae porque pide dos dígitos y pulgadas.
 (re.compile(r'smart tv|televisor|television|roku tv|crystal uhd|'
             r'pantalla (led )?\d{2}(\.\d)? ?(pulgadas|"|”)|\d{2}" (hd|4k) tv'),
  ('Televisores', None, 'tv')),
 # Antes que los videojuegos: el monitor portátil enumera "PS5, Xbox, Switch"
 # como lo que se le puede conectar.
 (re.compile(r'monitor portatil'), ('Monitores', 'Portátiles', 'monitor')),
 (re.compile(r'switch ?2|steam ?deck|rog ally|legion go|msi claw|freno de mano|handbrake|'
             r'consola de juegos|\bps5\b|mando bdm|gun grip|golf|juego de interruptor|'
             r'interruptor ns|base portatil ns'), VJ),
 (re.compile(r'webcam|camara web|camara de computadora|camara para pc|lifecam|facecam|'
             r'\bkiyo\b|streamcam|\bbrio\b|sistema de camara para sala|'
             r'sistema de videoconferencia|camara usb hdmi|camara de alta velocidad|'
             r'camara hdmi ptz|obsbot'), (PC, 'Webcams', 'cpu')),
 # "monitor" va antes que los componentes para que "Soporte de escritorio
 # para un monitor" no caiga en muebles; el único componente que dice
 # "monitor" (la pantalla de un AIO) está en EXPLICITOS.
 (re.compile(r'monitor'), (PC, 'Accesorios de monitor', 'cpu')),
 # Muebles: el escritorio sobre el que va la computadora, no la computadora.
 # Solo si la palabra abre el título: "RAM de escritorio" y "PC de escritorio"
 # la usan como adjetivo.
 (re.compile(r'^(?:\S+ ){0,2}escritorio (para|de|minimalista|con|gamer|diseno)|computadora de pie'),
  ('Muebles', 'Escritorios', 'sofa')),
 # Después de webcams y soportes: "para iMac" es un soporte, "Intel NUC" es
 # una placa VESA y el sistema Yealink es "todo en uno" pero es una cámara.
 (re.compile(r'all[- ]in[- ]one|\baio desktop|todo en uno|\bimac\b|omnistudio|proone|'
             r'panel industrial'),
  ('Computadoras de escritorio', 'All in One', 'desktop')),
 # Lo que se le cuelga a un mini PC va antes que el mini PC: soportes de
 # escritorio/VESA y la base dock del Mac mini son periféricos.
 (re.compile(r'^(?:\S+ ){0,2}(mini-?soporte|soporte)\b.*(mini pc|mac[- ]mini|miniordenador)|'
             r'soporte vesa|dock station|estacion de acoplamiento|docking'), PERI),
 (re.compile(r'mini pc|mac mini|mini ordenador|thinkcentre tiny|micro pc'),
  ('Computadoras de escritorio', 'Mini PC', 'desktop')),
 # La RAM va después de las computadoras completas: un mini PC "16GB DDR4"
 # no es un módulo de memoria.
 (re.compile(r'memoria ram|\bram\b|sodimm|udimm|ddr[45]|modulo de memoria'),
  (PC, 'Memoria RAM', 'cpu')),
 (re.compile(r'ventilador|enfriador|enfriamiento|cooler|disipador|\baio\b|refrigeraci|refrigeradora|'
             r'pasta (termica|de grasa)|grasa termica|compuesto termico|fuente de poder|'
             r'fuente de alimentacion|tarjeta grafica|filtro de (malla|polvo)|'
             r'hub de ventilador|cable (de extension de alimentacion|rgb)|neon difuso|'
             r'tanque de agua|reservorio|indicador flujo|boton de encendido|'
             r'placa adaptadora|\bsata\b|pcie|\bpc fan\b|noctua|kit de actualizaci.n pantalla|'
             r'gabinete|carcasa (para|de|del) (pc|computadora|ordenador)|funda para pc|'
             r'caja (modular|para pc)|chasis para pc|pc case|torre media|mid-tower|'
             r'almohadilla decorativa|para placa base|placa madre'), COMP),
 (re.compile(r'teclado|keyboard'), ('Teclados', None, 'keyboard')),
 (re.compile(r'\bmouse\b|\braton\b|\bratones\b'), ('Mouse', None, 'mouse')),
 (re.compile(r'bocina|bafle|altavoz'), ('Bocinas', None, 'speaker')),
 (re.compile(r'audifonos'), ('Audífonos', None, 'headphones')),
 (re.compile(r'power ?bank|bateria portatil|banco de energia|cargador portatil'),
  ('Baterías portátiles', None, 'battery')),
]

# Anuncios que ninguna regla decide bien; cada uno leído a mano.
EXPLICITOS = {
 # El título abre como kit de limpieza y por eso CABECERA lo tira, pero lo
 # que se vende es la boquilla que se le pone a la aspiradora para limpiar
 # el ducto de la secadora. El catálogo ya tiene dónde ponerlo.
 "B0H512VSLK": (None, 'Aspiradoras', 'Accesorios y repuestos', 'vacuum'),
 # Cola de la sección de café. El catálogo ya guarda el knock box de Ninja
 # ("Knock Box Ninja Luxe Café XSKKNOCKBOX") entre las espresso, así que el
 # cubo de posos y el embudo de 54 mm van con él; no hay subcategoría de
 # accesorios de cafetera.
 "B0BZZCRMP5": (None, 'Cafeteras', 'Espresso automáticas y semiautomáticas', 'coffee'),
 "B0GTZJZZ1H": (None, 'Cafeteras', 'Espresso automáticas y semiautomáticas', 'coffee'),
 # Central eléctrica de 245 Wh: misma cosa que la DJI Power 1000 V2 y las dos
 # DaranEner de esta misma captura, que ya están en Estación de energía.
 "B0DB1S36YP": ("EF ECOFLOW", 'Cargadores y adaptadores', 'Estación de energía', 'charger'),
 # Tarja de cocina: el catálogo las tiene en plomería, con los fregaderos
 # tipo vasija y el fregadero comercial BWE.
 "B0FJ8ZDP95": (None, 'Herramientas', 'Plomería y gas LP', 'wrench'),
 # Cava de 8 botellas: las cavas chicas del catálogo (GW8XDBB2 de 8, MW6XDBB
 # de 6) están entre los frigobares; las de 33 botellas para arriba, no.
 "B07Q8ZP8HC": ("AVERA", 'Refrigeradores', 'Frigobares y mini refrigeradores', 'fridge'),
 # Sección de secadoras de cabello. Cuatro títulos que no dicen de qué secan
 # o qué es lo principal del paquete, resueltos a mano:
 # Timco y JULIET venden secadoras de pelo -- Timco aparece tres veces más en
 # esta misma captura, siempre con "Secadora de Cabello" --, y 700 y 1800 W
 # plegables es lo que pesa una de viaje, no una de ropa.
 "B00X76H980": ("TIMCO", 'Aparatos de belleza', 'Secadoras de cabello', 'sparkle'),
 "B0D7FJKP3R": ("JULIET", 'Aparatos de belleza', 'Secadoras de cabello', 'sparkle'),
 # El One-Step Volumizer es el cepillo secador de Revlon; su título nunca dice
 # "secador". El catálogo ya guarda el multiestilizador Magic Styler y el
 # cepillo Izutech Toro entre las secadoras de cabello.
 "B09B2XF75X": ("REVLON", 'Aparatos de belleza', 'Secadoras de cabello', 'sparkle'),
 # El kit de Lizze empieza por la plancha y la secadora va de añadido: va con
 # los kits de plancha del catálogo ("Kit Plancha 450° + Rizador + Peine").
 "B0G3BH7RN2": ("LIZZE", 'Aparatos de belleza', 'Planchas y rizadores', 'sparkle'),
 # Karcher VC3, WD3 y KWD1: el título no dice de qué tipo son, pero el catálogo
 # ya trae estos mismos modelos ("Karcher De Tanque Vc3", "Karcher Agua Polvo
 # Sopladora Wd2", "Karcher Wdl1 Solidos Y Liquidos") en el cajón de tanque.
 "B0D212FFVF": ("KARCHER", 'Aspiradoras', 'Industriales y de tanque', 'vacuum'),
 "B0B45DV64T": ("KARCHER", 'Aspiradoras', 'Industriales y de tanque', 'vacuum'),
 "B0BWG91V1T": ("KARCHER", 'Aspiradoras', 'Industriales y de tanque', 'vacuum'),
 "B0FGDYJJQQ": ("XTREME PC GAMING", 'Computadoras de escritorio', 'Torre / Escritorio', 'desktop'),
 "B0GM3C1186": ("PRIDE GAMING", 'Computadoras de escritorio', 'Torre / Escritorio', 'desktop'),
 "B0CWV9NFZX": ("HUAWEI", 'Celulares', 'Android', 'phone'),
 # Pedal USB: no es teclado ni mouse aunque el título nombre a los dos.
 "B0BQN2VLDV": ("ZERODIS",) + PERI,
 # Docks y hubs de StarTech: van fuera de la PC, así que periférico.
 "B008YT59Q4": ("STARTECH",) + PERI, "B0764GBNX2": ("STARTECH",) + PERI,
 "B078PLPSTV": ("STARTECH",) + PERI, "B074FZRFF7": ("STARTECH",) + PERI,
 # Tarjeta PCIe de puertos serie: va dentro del gabinete.
 "B06XSKGB64": ("STARTECH",) + COMP,
 # Adaptador USB a puerto paralelo de 36 pines (impresoras viejas).
 "B0FCFW6Q1S": (None,) + PERI,
 # Cables internos: al header USB de la placa base y a un disco SATA.
 "B0H8GSPZM2": (None,) + COMP, "B0CCWQ67JT": (None,) + COMP,
 "B0GLHZP868": (None,) + COMP,
 # Cables y adaptadores USB sueltos: mismo destino que el cable UGREEN de la
 # captura anterior.
 "B0HFSNXRL9": (None, 'Cargadores y adaptadores', 'Cable', 'charger'),
 "B07T68S27D": ("GAZECHIMP", 'Cargadores y adaptadores', 'Cable', 'charger'),
 "B0HCDKQJF1": (None, 'Cargadores y adaptadores', 'Cable', 'charger'),
 "B0GL1MHJF8": (None, 'Cargadores y adaptadores', 'Cable', 'charger'),
 # Soportes verticales para laptop y micrófono de 3.5 mm para PC.
 "B0DB5PWRFH": (None,) + PERI, "B0DB5KW2LB": (None,) + PERI,
 "B0D5N9MBCZ": (None,) + PERI,
 # Docks para consolas portátiles.
 "B0CKYVVPMH": (None,) + VJ, "B0FXVRJCGJ": (None,) + VJ, "B0H7RVGNZ8": (None,) + VJ,
 "B0FK532LYS": (None,) + VJ,  # ventilador para Switch 2
 "B0DYJ58GYP": (None,) + COMP,  # pantalla para un enfriador AIO; dice "monitor"
 "B08X4Y7GM6": ("MOUNT-IT!",) + PERI,  # soporte para mini PC; dice "detrás de un monitor"
 "B0H9F4B5C5": (None,) + VJ, "B0HHMN8HP1": (None,) + VJ, "B0BTYKSNZQ": (None,) + VJ,
 "B09MJWBY63": ("EXTREMERATE",) + VJ,
}

MARCAS = ["CUKTECH","INIU","DEWALT","1 HORA","SELECT SOUND","AIWA","STF","LOGITECH",
 "RAZER","STYLOS","HUAWEI","TIMETEC","ADATA","ODYPC","TEAM GROUP","CRYFOKT","OBSBOT",
 "MTQ","EMEET","UGREEN","LENOVO","STEREN","DELL","ZZCP","ELGATO","ATOLLA","YOIDESU",
 "POLY","NIVEOLI","HP","ASHATA","CYBER ACOUSTICS","GOTOTOP","NEXIGO","YEALINK","SVPRO",
 "FOMAKO","MICROSOFT","MSI","WALI","REDLEMON","MOUNTUP","DAWNTREES","GIANOTTER","HUANUO",
 "MOUNT-IT!","FENGE","VIVO","HUMANCENTRIC","YUNSEITY","AVLT","NB NORTH BAYOU","ZENSUKYE",
 "STARTECH","ZERODIS","EJOYOUS","TBEST","LICAEVEY","ALIPIS","EIMSOAH","AMONIDA","YINHING",
 "THERMALRIGHT","THERMALRLGHT","THERMALTAKE","DARKFLASH","CORSAIR","XTREME PC GAMING",
 "GEOMETRIC FUTURE","LIAN LI","ASIAHORSE","BE QUIET!","HYTE","VETROO","ANTEC","APEVIA",
 "JONSBO","HYXN","NOCTUA","GAMDIAS","RUIX","GAME FACTOR","FOIFKIN","SANPYL","YEYIAN",
 "PRIDE GAMING","NACEB","HEJHNCII","MAVIS LAVEN","ASIXXSIX","HITEFU","LUQEEG","RICHER-R",
 "DKE","GAZECHIMP","KAMRUI","GETORLI","HP","ACER","LENOVO","ASUS",
 "TOPLIVING","UTILIA","SEDETA","JETECH","TORRAS","TOCOL","EXTREMERATE","ESTINK","TANGXI","LOOP",
 "SONY","SAMSUNG","APPLE","XIAOMI","ANKER","AMAZON BASICS","LETTURE","UPLAYTECK",
 "AOOSTAR","CHUWI","BEELINK","ECS","ARZOPA","PUTORSEN","AFOOYO","FASGEAR",
 "LG","HISENSE","JVC","WESTINGHOUSE","CHIQ","TCL","SANSUI","DAEWOO",
 "IMADEMEXICO","VEVOR","XGIMI","RACK & PACK","RACEGT","NIERBO","PYLE","MECCANIXITY",
 "ZUNATE","YOSOO HEALTH GEAR","HUANYINGBJB","VOOPVOR",
 "MIDEA","DACE","MABE","KOBLENZ","WHIRLPOOL","AUCMA","MIRAGE",
 "WHITE WESTINGHOUSE","WHITE-WESTINGHOUSE","SUPER DEAL","EASY","WINIA","DAEWOO",
 "ACROS","PANASONIC","GUTSTARK","GIANTEX","MEDIMALL","COSTWAY","ZYNKEZ","PATAKU",
 "ERIVESS","ZENY","SERENELIFE","PUCHEN","POCREATION","TOPINCN","AYNEFY","HAOFY",
 "ZJCHAO","JTLB","KIMISS","LUOCUTE","ARAMOX","FILFEEL","KADIMENDIUM","HOMSFOU"]
MARCAS += ["CRAFTSMAN","SHARK","KARCHER","KÄRCHER","ROBOROCK","BISSELL","EUREKA",
 "TRUPER","BLACK+DECKER","VEVOR","TRENT","MASTERBLEND"]
MARCAS += ["KIROGILY","WAVYTALK","REMINGTON","BOMIDI","SENDOWTEK","CHARLEMAIN","REVLON",
 "CONAIR","BABYLISSPRO","BABYLISS","RAYI","BELLISSIMA ITALIA","PHILIPS","HOT TOOLS",
 "BLUELANDER","OSOJI","TAIFF","DORISILK","DREAME","UNIORANGE","CIVEYA","LECOMELY",
 "TIMCO","YUNIR","VENTUS","LIZZE","AIMA BEAUTY","JULIET"]
MARCAS += ["CHEFMAN","EF ECOFLOW","ELECTACTIC","FEELFUNN","RCA","ROVSUN","FRIGIDAIRE",
 "RHINO","AVERA","ASTROAI","CROWNFUL","BIGKING","SIMPLE DELUXE","U CHEF","JOMA",
 "AUSEIN","INGEQUIS","VANTISAN","STANHOME","SEENTECH","WHIRLPOOL"]

# "Kärcher" y "Karcher" son la misma marca: marca() pasa a mayúsculas pero no
# quita acentos, así que hay que nombrar las dos.
ALIAS = {"THERMALRLGHT": "THERMALRIGHT", "WHITE-WESTINGHOUSE": "WHITE WESTINGHOUSE",
         "KÄRCHER": "KARCHER"}

def marca(t):
    cab = t[:45].upper()
    hits = [m for m in MARCAS
            if re.search(r'(?<![A-Z0-9])' + re.escape(m) + r'(?![A-Z0-9!])', cab)]
    if not hits: return None
    return ALIAS.get(max(hits, key=len), max(hits, key=len))

def tramo(mah):
    if mah is None: return None
    if mah <= 10000: return 'Hasta 10,000 mAh'
    if mah <= 20000: return '10,000 a 20,000 mAh'
    return 'Más de 20,000 mAh'

def sub_teclado(tn):
    return 'Mecánicos' if re.search(r'mecanic', tn) else 'Membrana' if 'membrana' in tn else None

def sub_tv(tn):
    if re.search(r'\b4k\b|qled|uhd|qned|oled|miniled|mini-led', tn): return '4K y QLED'
    if re.search(r'full hd|\bfhd\b|\bhd\b|1080p|720p', tn): return 'Full HD y HD'
    return None

def sub_mouse(tn):
    if re.search(r'gamer|gaming|para juegos?|de juegos?|esports', tn): return 'Gaming'
    if re.search(r'vertical|trackball', tn): return 'Ergonómicos'
    return 'Oficina'

def sub_lavadora(tn):
    # El orden es el que manda: una lavasecadora de "carga frontal" es
    # lavasecadora, y una "doble tina, carga superior" es semiautomática --
    # doble tina ya significa que el centrifugado va aparte.
    # Una centrifugadora suelta no es de carga superior ni frontal: solo
    # exprime, y "carga superior" describe por dónde se mete la ropa. El
    # catálogo ya las trae sin subcategoría (Koblenz SCK-60, HKPRO HK-37).
    if 'centrifugadora' in tn and not re.search(r'\blavadora', tn): return None
    # Amazon escribe "Lavadasecadora" tan seguido como "Lavasecadora".
    if re.search(r'lava\w*secadora|lava ?y ?seca', tn): return 'Lavasecadoras'
    if re.search(r'centro de lavado', tn): return 'Centros de lavado'
    if re.search(r'doble tina|dos tinas|2 tinas|semi[- ]?automatic[ao]', tn): return 'Semiautomáticas'
    if re.search(r'carga frontal', tn): return 'Carga frontal'
    if re.search(r'carga superior', tn): return 'Carga superior'
    if re.search(r'^secadora', tn): return 'Secadoras'
    return None

def sub_aspiradora(tn):
    # El orden es el que manda. Un accesorio primero: el soporte y el kit de
    # ductos también dicen "aspiradora", pero lo que se vende es la pieza.
    if re.search(r'^(kit|filtro|bolsa|cepillo|bateria|cargador|manguera|'
                 r'\d+ ?(piezas?|unidades?|pack))\b|'
                 # "VEVOR - Soporte de aspiradora": la marca va delante, así que
                 # estas van sin ancla.
                 r'soporte (de|para) aspirador|accesorio de aspiradora|'
                 r'repuesto para aspiradora', tn):
        return 'Accesorios y repuestos'
    if re.search(r'robot aspirador|aspiradora robot|robot aspirador?a', tn):
        return 'Robots aspiradores'
    # Tanque, taller y agua/polvo: la Karcher VC3 y la shop vac del catálogo
    # ya están aquí, y la Koblenz "Canister" es lo mismo con otro nombre.
    if re.search(r'canister|de tanque|shop vac|seco *[-y]* *(humedo|mojado)|'
                 r'humedo/?seco|seco/?humedo|agua y polvo|solidos y liquidos|'
                 r'galones|wet/?dry|sopladora', tn):
        return 'Industriales y de tanque'
    # El resto es la aspiradora de casa. El catálogo mete aquí también las de
    # cable (Atrix ERGO Lite, SIPPON vertical), así que el nombre de la
    # subcategoría se queda corto pero la convención ya está tomada.
    return 'Inalámbricas y de mano'

def sub_refri(tn):
    # El orden manda. Primero el uso comercial: el exhibidor vertical de
    # puerta de cristal es grande, pero no es el refri de una casa.
    if re.search(r'exhibidor|comercial|refrigerador vertical', tn): return 'Uso comercial'
    if re.search(r'nevera/congelador|congelador (vertical|horizontal)|^congelador', tn):
        return 'Congeladores'
    # Frigobar es lo que el título diga que es, no lo que digan los litros:
    # "mini", "compacto", "personal", "portátil", "de encimera". El de vinos
    # de 24 pulgadas dice "Incorporado/Autoportante", así que no cae aquí.
    if re.search(r'\bmini\b|frigobar|compact[ao]|personal|portatil|de encimera|'
                 r'refrigerador de bebidas', tn):
        return 'Frigobares y mini refrigeradores'
    return 'Refrigeradores'

def sub_audio(tn):
    diadema = bool(re.search(r'diadema|over[- ]ear|on[- ]ear', tn))
    earbud = bool(re.search(r'in[- ]ear|earbud|tws|true wireless', tn))
    inal = bool(re.search(r'inalambric|bluetooth|wireless', tn))
    cable = bool(re.search(r'con cable|alambric|3\.5 ?mm', tn))
    if diadema == earbud or inal == cable: return None
    return (('Diadema' if diadema else 'Earbuds') + ' ' +
            (('inalámbrica' if diadema else 'inalámbricos') if inal else 'con cable'))

alta, fuera = [], []
for it in json.load(io.open(sys.argv[1], encoding='utf-8')):
    tn = T(it['title'])
    base = {k: it[k] for k in ('asin','title','price','photo','url')}
    if it['asin'] in EXPLICITOS:
        mk, cat, sub, img = EXPLICITOS[it['asin']]
        alta.append({**base, 'brand': mk, 'category': cat, 'subcategory': sub, 'image': img})
        continue
    motivo = (next((m for rx, m in FUERA if rx.search(tn)), None)
              or next((m for rx, m in CABECERA if rx.search(tn[:55])), None))
    if motivo:
        fuera.append((it, motivo)); continue
    hit = next((v for rx, v in REGLAS if rx.search(tn)), None)
    if not hit:
        fuera.append((it, 'no encaja en ninguna categoría')); continue
    cat, sub, img = hit
    if cat == 'Baterías portátiles': sub = tramo(capacidad_mah(it['title']))
    elif cat == 'Teclados': sub = sub_teclado(tn)
    elif cat == 'Mouse': sub = sub_mouse(tn)
    elif cat == 'Televisores': sub = sub_tv(tn)
    elif cat == 'Audífonos': sub = sub_audio(tn)
    elif cat == 'Lavadoras': sub = sub_lavadora(tn)
    elif cat == 'Aspiradoras': sub = sub_aspiradora(tn)
    elif cat == 'Refrigeradores': sub = sub_refri(tn)
    alta.append({**base, 'brand': marca(it['title']), 'category': cat,
                 'subcategory': sub, 'image': img})

json.dump(alta, io.open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'ALTA: {len(alta)}   FUERA: {len(fuera)}   sin precio (no se dan de alta): '
      f'{sum(1 for a in alta if a["price"] is None)}\n')
for k, n in collections.Counter((a['category'], a['subcategory']) for a in alta).most_common():
    print(f'  {n:4}  {k[0]} / {k[1]}')
print('\nsin marca:', sum(1 for a in alta if not a['brand']))
print('\n--- descartados ---')
for k, n in collections.Counter(m for _, m in fuera).most_common():
    print(f'  {n:4}  {k}')
print()
for it, m in fuera:
    print(f'  [{m[:30]:30}] {it["asin"]} {it["title"][:75]}')
