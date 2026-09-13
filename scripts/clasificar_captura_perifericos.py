#!/usr/bin/env python3
"""Clasifica una captura de Amazon de periféricos y componentes de PC.

La captura del 11-sep-2026 mezcló webcams, soportes de monitor, gabinetes,
enfriadores, RAM y la cola de la búsqueda "periféricos", que Amazon rellenó
con seguros Assurant, catéteres y espadas de utilería; la segunda tanda
trajo mini PC, all-in-one y escritorios de oficina, y la tercera Mac mini,
soportes para mini PC, un monitor portátil y una MacBook; la cuarta,
televisores; la quinta, pantallas de proyección; la sexta, lavadoras; la
séptima, aspiradoras; la octava, refrigeradores; la novena, secadoras de
cabello; la décima, planchas; la undécima, robots limpiacristales, y la
duodécima, freidoras de aire; la decimotercera, licuadoras, y la
decimocuarta, purificadores de agua. Este
script la reparte entre "Componentes y accesorios de PC",
"Videojuegos / Accesorios", "Computadoras de escritorio",
"Muebles / Escritorios", "Monitores", "Laptops", "Televisores",
"Proyectores y accesorios", "Lavadoras", "Aspiradoras", "Refrigeradores",
"Aparatos de belleza", "Electrodomésticos" y "Equipo comercial".

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

La décima son planchas: cuatro de ropa (dos de viaje y las dos Silver Star
de vapor por gravedad). "Plancha" sola no alcanza, porque la de pelo, la
prensa de sublimación y la de ropa se llaman igual; las reglas van de lo más
específico a lo más general y en ese orden salen los tres cepillos
alisadores ("Aparatos de belleza / Planchas y rizadores") y la máquina de
sublimación 8 en 1 ("Equipo comercial / Sublimación y prensas").

La undécima son robots limpiacristales: 47 anuncios y 35 aparatos. El
catálogo ya tenía la subcategoría con diez fichas (Liectroux, FMART,
Teendow), así que solo faltaban las reglas. Esta sección obligó a dos
cambios en FUERA: el robot dice "limpiador" y "control remoto" en el mismo
título que el aparato, y las dos reglas que cazan esas palabras --escritas
para accesorios de otras secciones-- se llevaban la sección entera antes de
llegar a REGLAS.

La duodécima son freidoras de aire: 39 anuncios y 30 aparatos. El catálogo
ya tenía la subcategoría con 190 fichas, pero la regla pedía la frase exacta
"freidora de aire" y con eso se le escapaban seis: Cuisinart escribe
"Freidora Aire" sin el "de", T-Fal la llama "Horno Freidor", Ninja la vende
por capacidad ("Freidora de 4 cuartos") y varias marcas usan el inglés. Los
nueve descartes son lo que se mete dentro del aparato: seis moldes y
bandejas de silicona y tres paquetes de papel desechable. Todos nombran
"freidora de aire" en el título, así que hizo falta una guarda en FUERA, que
corre antes que REGLAS. El único título que no nombra la fritura, el "Ninja
Crispi Pro - Sistema de cocción de vidrio", se resolvió a mano en
EXPLICITOS.

La decimotercera son licuadoras: 92 anuncios, de los que solo 55 son la
licuadora. Veintiocho son piezas -- cuchillas, aspas, vasos y juntas -- que
dicen "licuadora" en el título porque es la máquina a la que le entran; van
a "Refacciones / Refacciones para electrodomésticos", donde el catálogo ya
guarda una cuchilla de Ninja (p530). Separarlas costó una regla de tres
condiciones a la vez, porque cada palabra suelta se lleva por delante a una
licuadora de verdad: la SIGNA se anuncia "Con Vaso" y una portátil de 800 ml
presume "6 Cuchillas". La regla del aparato también hubo que abrirla: la
subcategoría se llama "Licuadoras y extractores", pero pedía la palabra
"licuadora", y con eso se le escapaban los catorce extractores de jugos, de
nutrientes y de prensado en frío que no la dicen. Los ocho descartes son
seis latas de cereal Nestum, un anuncio sin título y una prensa de papas de
palanca que Amazon llama "exprimidor". La batidora de pedestal se fue a
"Pequeños electrodomésticos de cocina", donde el catálogo tiene treinta.

La decimocuarta son purificadores de agua: nueve anuncios. Cinco son el
equipo o su cartucho y van a "Electrodomésticos / Purificadores de agua",
donde el catálogo ya guarda juntos el aparato y sus repuestos (los Hydrofast
HF03, los filtros JIMMY R9). Dos son filtros de refrigerador y van a
Refacciones con los otros seis que ya entraron: el de LG venía en inglés
("Refrigerator Water Filter") y por eso se le escapaba a la regla, que pedía
que el título abriera con "Filtro". Los dos descartes son tratamientos
químicos para el tinaco que se venden por litros tratados o por meses de
duración: se dosifican y se acaban, como las pastillas de lavadora.

La decimoquinta es la sección de pequeños electrodomésticos de cocina, la
más revuelta de todas: 344 anuncios y solo 194 son un aparato. Ciento
treinta y nueve van a "Pequeños electrodomésticos de cocina", que es donde el
catálogo ya guarda las ollas, arroceras, tostadores, wafleras,
sandwicheras, creperas y básculas; el resto se reparte entre licuadoras,
parrillas de inducción y de quemadores (a "Estufas y hornos", con la
"Parrilla Eléctrica de 24 IN 4 quemadores" que ya estaba), tres
microondas, siete freidoras de aire, diez refacciones, tres aparatos
industriales y una cafetera. Los 150 descartes son todo lo que Amazon
pone alrededor del aparato: 43 seguros de Assurant, 40 fundas y
cubiertas, 19 bandejas con ruedas para moverlo por la barra, 18 estantes
y organizadores, 14 baterías de cocina y cubiertos, cuatro elevadores de
gabinete, cinco juguetes y dos combos de varios aparatos con un solo
precio. Hicieron falta guardas nuevas en FUERA para cada familia, porque
todas nombran el aparato en el título ("Funda para tostador", "Bandeja
deslizante para licuadora"). Tres se resolvieron a mano: la Chefman
"Freidora digital multifuncional" nunca dice "aire", y el NutriBullet
"Batidora" y el Ninja "Sistema de Cocina" son licuadoras de vaso. La regla
de "parrilla" tuvo que pedir apellido (eléctrica, panini, raclette),
porque un filtro de PC se vende con "parrillas de filtro de ventilador".
También entra la parrilla panini de Chefman de la primera captura, que
hasta hoy no tenía regla que la reconociera.

La decimosexta no es una sección sino toda la tienda de un tirón: 2,160
anuncios que van de las pilas portátiles a las máquinas de coser, pasando
por bocinas, audífonos, teclados, ratones, webcams, brazos de monitor,
refrigeración de PC, mini PCs, televisores, pantallas de proyección,
lavadoras, aspiradoras, secadoras de pelo, planchas, robots
limpiacristales, freidoras, licuadoras, purificadores, refrigeradores y
la cocina entera. Mil setecientos cincuenta y cinco son un producto y
405 no; de los que entran, 1,724 ya estaban en el catálogo y solo 18 son
fichas nuevas: las máquinas de coser, que el catálogo guardaba desde hacía
tiempo en su propia subcategoría pero que ninguna regla sabía reconocer.

Lo que se quedaba fuera por falta de regla eran ochenta y cinco anuncios,
y en el repaso resultaron ser siempre lo mismo: el producto se nombra en
un idioma o con una palabra que las reglas no tenían. Media captura dice
"auriculares" donde el catálogo dice "audífonos", y las marcas grandes
venden "Buds" y "headphones" sin traducir; "altavoz" estaba, pero
"altavoces" no; Sonos vende un "Wireless Speaker" a secas. Se ensancharon
las dos reglas de audio con esas formas y se les puso delante la de las
bocinas de coche, porque el catálogo nunca las guarda en Bocinas sino en
"Audio y multimedia para auto" -- cincuenta y cinco fichas contra ninguna
-- y se reconocen por cómo se venden: coaxiales, de 6x9, de rango medio o
diciendo "para auto".

El otro grupo eran palabras que significan dos cosas distintas. "Monitor"
en audio no es una pantalla: las Edifier R1000T4 son "Bocinas Monitores
Tipo Estudio", los KZ EDX Pro son "Audífonos con Monitor Dentro del oído"
y el Phenyx Pro es un "Sistema de monitoreo in-Ear", y los tres acababan
en Accesorios de monitor, que es donde van los brazos y las bases de
pantalla; ahora el audio se decide antes. "MacBook Pro" no siempre es una
laptop: cinco power banks, un cargador de pared, un cable y un mouse lo
nombraban como lo que cargan o a lo que se conectan, así que la palabra
pide abrir el título igual que ya lo pedía "laptop". "GDDR5" no es "DDR5":
una tarjeta gráfica estaba fichada como módulo de memoria RAM. "Proyector"
delante de "pantalla" es el aparato y detrás es el destino, y con eso el
AOC portátil dejó de ser una pantalla de proyección. Y "PS5" o "Xbox" en
un título no lo vuelven un accesorio de videojuegos: el teclado HyperX
Alloy Core y dos ratones Corsair los listan entre lo que aceptan, así que
la regla de videojuegos ahora deja pasar a lo que dice "teclado" o
"mouse".

Familias nuevas, todas con su lugar ya hecho en el catálogo y ninguna
regla que llegara a él: las máquinas de coser y sus piezas (prensatelas,
bobinas, porta-carretes y la mesa de extensión, que van a Refacciones como
las cuchillas de licuadora), la estación de energía de 110 V (la DJI Power
1000, la EcoFlow DELTA 3, las DaranEner), las baterías de cámara de Tilta,
el cargador de pared, el cable suelto, el micrófono de solapa, la
impresora 3D, la terminal de cobro y el celular cuando el título es marca
y modelo y nada más. Esa última regla tuvo que descartar de una vez los
Buds, los Watch y las Tab, que empiezan igual y no son teléfonos, y
también las baterías, que Samsung anuncia como "Galaxy Magnetic Wireless
5000mAh".

Los 405 descartes no traen nada nuevo: 78 seguros de Assurant, 74 fundas,
56 anuncios cuyo título es la palabra "Amazon Renewed" y nada más, 24
refacciones de lavadora, 19 bandejas con ruedas, 18 muebles, 16
utensilios de mano, 12 repuestos de otro aparato y 12 paquetes de dos
electrodomésticos con un solo precio. Solo hicieron falta cuatro guardas
nuevas: el embudo dosificador y el cajón de la cafetera espresso, las
perlas de perfume de la ropa, el escurridor del fregadero y los dos
títulos que son el nombre de una línea de producto y nada más. Cinco se
resolvieron a mano: Razer y SteelSeries bautizan sus periféricos y dan por
sabido lo que son (el Pro Click V2, el Viper V3 Pro, el Basilisk Mobile y
el Apex Pro Gen 3), y el SoundPEATS Air6 trae la funda en el título, que
era justo lo que lo descartaba.

Al pasar todas las capturas por las reglas nuevas, 69 fichas que ya
estaban en el catálogo salían con otra etiqueta, y solo se movieron las
24 que cambian de categoría. Las otras 45 eran el clasificador perdiendo
detalle, no ganándolo: 38 audífonos cuya ficha ya dice "Earbuds
inalámbricos" o "Diadema con cable" salen sin subcategoría porque
sub_audio solo la deduce cuando el título nombra a la vez la forma y la
conexión, y lo mismo les pasa a cuatro bocinas, dos lavadoras de carga
superior y un MacBook Pro. Una subcategoría concreta no se cambia por
None: ahí la ficha sabe más que la regla.

Las 24 que sí se movieron son las que el clasificador afina. Siete kits
Tilta de baterías NP-FZ100 y DMW-BLK22 estaban en "Cargadores" y son
accesorios de cámara. Cuatro estaciones de energía (DaranEner, DJI
Power, MARBERO) se juntan con las otras 74 en "Otros / Energía portátil
y paneles solares", que es donde el catálogo ya las guardaba;
por eso esa regla apunta ahí y no a una subcategoría nueva. Tres bancos
de batería y un cargador portátil que se anunciaban de otra forma vuelven
a "Baterías portátiles". El Sonos Era 300 va con los asistentes
inteligentes, un altavoz de conferencia va a "Bocinas", y el resto son
una tarjeta gráfica GDDR5 que estaba en "Memoria RAM", el Apex Pro Gen 3
a "Mecánicos", el Pro Click V2 a "Oficina", el KATAR PRO XT a "Gaming",
el sistema de monitoreo in-ear de Phenyx Pro a Audífonos y dos
alfombrillas a Mouse, que es donde el catálogo guarda las otras 34.

Tres reglas se corrigieron por el camino. La de escritorios buscaba
"computadora de pie" sin cerrar la palabra, así que "alfombrilla de
computadora de piel" entraba en Muebles; ahora la palabra se cierra y hay
una regla propia para los tapetes que no nombran el mouse. La de power
banks leía "2400mAh Batería" dentro de "Bocina Bluetooth, Barra de
Sonido" y se llevaba dos bocinas; ahora descarta de entrada cualquier
título que diga bocina, altavoz o barra de sonido. Y la de bocinas se
llevaba el Echo Pop, así que los Echo, los Nest y lo que diga Alexa se
desvían antes a domótica.

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
# Un robot limpiacristales nombra en el mismo título el aparato y dos cosas
# que en cualquier otra sección delatan un accesorio: "limpiador" y "control
# remoto". Sin esta guarda, las dos reglas de FUERA que las cazan se llevarían
# la sección entera antes de que REGLAS pueda verla.
ES_ROBOT_VIDRIOS = (r'(?!.*\brobot\b.{0,40}(limpiacristales|limpiavidrios|'
                    r'ventana|vidrio|cristal))')

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
 # Lo que se vende alrededor de la cafetera espresso: el embudo que encaja
 # en el portafiltro de 54 mm y el cajón donde se golpea la pastilla usada.
 (re.compile(r'embudo dosificador|caja de cafe espresso|cubo para cafe|'
             r'knock ?box'),
  'accesorio de cafetera, no es la cafetera'),
 # El perfumante de la ropa es del mismo estante que la lavadora, pero se
 # gasta y se repone, como las pastillas.
 (re.compile(r'perlas de perfume|suavizante de telas'),
  'consumible de lavandería, no es el aparato'),
 # El escurridor del fregadero no se enchufa.
 (re.compile(r'cesta escurridora|colador de alimentos|escurridor de'),
  'utensilio manual, no es un electrodoméstico'),
 # Dos títulos que son el nombre de una línea de producto y nada más.
 (re.compile(r'^steren preferencias$|^amazon basics$'),
  'el título no dice qué producto es'),
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
 # Lo que se mete DENTRO de la freidora. Todos nombran "freidora de aire" en
 # el título, así que sin esta guarda entrarían a la sección del aparato:
 # el papel se gasta como los filtros de la cafetera, y los moldes y las
 # bandejas de silicona son accesorios, no la freidora.
 (re.compile(r'papel.{0,30}(freidora|air fryer)|forro de papel|'
             r'revestimiento de papel'),
  'papel desechable, no es el aparato'),
 (re.compile(r'(moldes?|bandejas?|olla|accesorios?|kit accesorios)'
             r'.{0,40}(de silicona|silicon|para freidora|para air fryer)|'
             r'silicona (moldes|para freidora)|de silicona para freidora'),
  'accesorio de silicona, no es el aparato'),
 # Cola de la sección de licuadoras: Amazon cuela seis latas de cereal
 # Nestum entre los extractores porque se prepara con licuadora. Es comida.
 (re.compile(r'\bnestum\b|cereal (infantil|para bebes)'),
  'cereal infantil, no es un aparato'),
 # El "exprimidor" de tooloflife es una prensa de papas de palanca: no
 # tiene motor ni enchufe. El catálogo no tiene utensilios manuales.
 (re.compile(r'prensa de papas|exprimidor de verduras'),
  'utensilio manual, no es un electrodoméstico'),
 # Tratamientos para el tinaco: se dosifican y se acaban. El TECHNOSAR se
 # vende por litros tratados ("5000-10000 L") y el dual por paquete de
 # cuatro con duración de seis meses; ninguno es un aparato que comparar.
 # Mismo criterio que las pastillas de lavadora y los filtros de café.
 (re.compile(r'antisarro|desinfectante.{0,30}(tinaco|agua)|'
             r'suavizador de agua'),
  'tratamiento químico del agua, no es el aparato'),
 # Sección de pequeños electrodomésticos de cocina. Amazon mezcla con los
 # aparatos todo lo que se pone debajo, encima o alrededor de ellos: las
 # bandejas con ruedas para moverlos por la barra, los deslizadores
 # adhesivos, el elevador de gabinete para la batidora de pie, los estantes
 # para el microondas y los enrolladores de cable. Nada de eso se enchufa.
 (re.compile(r'bandeja (deslizante|rodante)|estera deslizante|'
             r'alfombrilla de bambu|slider de bambu|deslizadores|'
             r'lanzadores autoadhesivos|ruedas de electrodomesticos|'
             r'tapete para fregadero'),
  'bandeja o tapete para mover el aparato, no es el aparato'),
 (re.compile(r'elevador (de electrodomesticos|mezclador|de mezclador)|'
             r'mezclador elevador|aparato elevador'),
  'elevador de gabinete, no es el aparato'),
 (re.compile(r'estante (para|de) microondas|estante extensible|'
             r'soporte (para|de) (mini refrigerador|microondas)|'
             r'cajones extraibles|muebles? para cocina|barra de cafe|'
             r'organizador(es)? de cables (adhesivo|mejorados|'
             r'para electrodomesticos)|organizador\s?para debajo|'
             r'organizador con ganchos'),
  'mueble u organizador, no es el aparato'),
 # Trastes sin motor: baterías de cocina, juegos de ollas, cubiertos y los
 # cortadores de palanca. El catálogo no tiene utensilios manuales.
 (re.compile(r'bateria de cocina|juego de (ollas|cubiertos|\d+ sartenes)|'
             r'conjunto de ollas|sartenes antiadherentes|cubiertos de acero|'
             r'cortador de (curry|verduras)|picador de verduras|'
             r'molde de arroz|platillo volador|para estufa de gas'),
  'utensilio manual, no es un electrodoméstico'),
 (re.compile(r'\bjuguetes?\b|de imitacion|de simulacion|en miniatura|'
             r'de cocina para ninos'),
  'juguete, no es un aparato'),
 # Un combo de dos o tres aparatos con un solo precio no se compara contra
 # ninguno de ellos suelto. Mismo criterio que la lavadora con frigobar.
 (re.compile(r'combo dulce|combinacion de electrodomesticos'),
  'paquete de varios aparatos, no es un producto comparable'),
 # Fundas y cubiertas que no abren el título con la palabra "Funda":
 # "10 cubiertas antipolvo desechables", "Batidora antipolvo para batidora"
 # (una funda mal traducida), "Juego de fundas con tema de frutas" y las
 # piezas de repuesto de la Thermomix, que no está en el catálogo.
 (re.compile(r'cubiertas? (antipolvo|de proteccion|transparentes)|'
             r'tostador cubierta|batidora antipolvo|juego de fundas|'
             r'fundas faciles|protector de visualizacion|thermomix|'
             r'\btm[67]\b|cubiertas? (para|contra) (tostador|licuadora|'
             r'panificadora|rebanar|el polvo|electrodomesticos)|'
             r'cubierta (cortadora|protectora)|tapas? de silicona para|'
             r'tapas de licuadora|batidora de pollo|'
             r'protector de electrodomesticos'),
  'accesorio: funda/estuche/carcasa'),
]
# Lo que descalifica solo si va al PRINCIPIO del título: ahí Amazon pone lo
# que el producto ES. Más adelante viene la lista de características, y ahí
# "cubierta de privacidad" describe un detalle de una webcam, "tornillos"
# lo que trae un tanque de refrigeración y "Funda para juegos" es la segunda
# mención de un gabinete mal traducido.
CABECERA = [
 # "Funda para PC" y "Carcasa para computadora" son gabinetes mal traducidos;
 # el resto de fundas y carcasas son accesorios.
 (re.compile(r'\bfunda de viaje|\bfundas? (?!para pc\b)|\bestuche\b|'
             r'\bcarcasa (?!(para|de|del) (pc|computadora|ordenador)\b)|'
             r'co2crea'), 'accesorio: funda/estuche/carcasa'),
 (re.compile(r'protector (de )?pantalla|bisel ahuecado|keyboard skin|'
             r'cubierta (deslizante|de camara|camara web|webcam|universal)|webcam cover|'
             r'obturador de privacidad|tapa de privacidad'), 'accesorio: protector/cubierta'),
 # Salvo cuando el título abre nombrando el aparato: "Aspiradora de Agua,
 # Limpiador de Tapicería" es una aspiradora, y el catálogo ya trae la
 # limpiadora de tapicería Teendow C6 MAX en Aspiradoras.
 (re.compile(r'^' + ES_ROBOT_VIDRIOS +
             r'(?!aspirador)(?=.*(?:limpiador|kit de limpieza|kit limpiador))'),
  'kit de limpieza, no es el aparato'),
 # Solo al principio: una pantalla de proyección motorizada "con control
 # remoto" lo trae de accesorio.
 (re.compile(r'^' + ES_ROBOT_VIDRIOS + r'.*control remoto'),
  'control remoto de repuesto, no es el aparato'),
 (re.compile(r'bateria de repuesto|bateria for portatil|repuesto para el altavoz|'
             r'cable de repuesto|adaptadores tipo c de repuesto|thumbsticks de repuesto|'
             r'lente optica|modulo camara|pegatinas|huano switches|corepad|'
             r'modulo de de mando'), 'repuesto o pieza suelta de otro aparato'),
 # Se gasta y se repone; no se compara contra el robot, igual que los
 # desodorantes de refrigerador y las pastillas de lavadora.
 (re.compile(r'quita gotas|limpia vidrio cromo'),
  'químico de limpieza, no es el aparato'),
 (re.compile(r'\btornillo'), 'tornillería'),
 # Solo al principio: el kit de vasos de NutriBullet trae "cepillo de
 # limpieza" de añadido y es una refacción.
 (re.compile(r'^cepillo de limpieza'), 'accesorio de limpieza, no es el aparato'),
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
 # Limpieza de ventanas. Va antes que Lavadoras y que Aspiradoras porque
 # estos títulos se describen a sí mismos con las dos palabras: hay un
 # "Robot limpiacristales, aspiradora Inteligente de 2600 Pa" y hasta un
 # "Robot limpiacristales ... Lavadora eléctrica robótica para Cristales".
 # Ninguno limpia pisos ni lava ropa.
 #
 # Primero las herramientas de mano: el juego de tres piezas con atomizador
 # dice "limpiacristales de ventana" y si no se resuelve acá se iría con los
 # robots. No tiene motor; va con el trapeador y la cubeta, en Otros.
 (re.compile(r'herramientas de limpieza de ventanas'), ('Otros', 'Varios', 'box')),
 (re.compile(r'\brobot\b.{0,40}(limpiacristales|limpiavidrios|'
             r'limpiador de ventanas|limpieza de ventanas)|'
             r'\blimpiacristales\b|\blimpiavidrios\b'),
  ('Electrodomésticos', 'Robots limpiacristales', 'appliance')),

 # Planchas. "Plancha" sola no alcanza: la de pelo, la prensa de sublimación
 # y la de ropa se llaman igual, así que el orden decide y va de lo más
 # específico a lo más general.
 #
 # La de pelo pide "alisador" o "plancha de pelo/cabello" -- no basta con
 # "cepillo ... de cabello", que es el cepillo secador. Y si el título nombra
 # un secador en cualquier parte, no entra: los kits "5 en 1" y "7 en 1" que
 # abren con "Secador de Cabello" y listan "Boquillas + Cepillo + Rizador de
 # Pelo" son multiestilizadores, y el catálogo los tiene en Secadoras de
 # cabello junto al Dyson Airwrap.
 (re.compile(r'^(?!.*\bsecador)'
             r'(?=.*(cepillo alisador|alisador(a)? de (pelo|cabello)|'
             r'plancha.{0,30}(de pelo|de cabello|alisador|rizador)|'
             r'rizador de (pelo|cabello)))'),
  ('Aparatos de belleza', 'Planchas y rizadores', 'sparkle')),
 # La prensa de calor pide nombrarse como máquina o prensa: "Impresora ...
 # Para Planchas Sublimación", que el catálogo tiene en Impresoras, no es
 # una prensa sino la impresora que le carga el papel.
 (re.compile(r'maquina de sublimacion|prensa de calor|prensa termica'),
  ('Equipo comercial', 'Sublimación y prensas', 'factory')),
 # La de ropa, al final. Antes que el vaporizador porque el catálogo ya
 # resolvió así el empate: las "Plancha Vapor Vertical" están en Planchas,
 # y en Vaporizadores solo lo que se anuncia como vaporizador.
 (re.compile(r'\bplancha\b.{0,30}(de vapor|a vapor|de viaje|para ropa|'
             r'de ropa|vertical)|plancha vapor'),
  ('Electrodomésticos', 'Planchas', 'appliance')),
 (re.compile(r'vaporizador (de|para) ropa|vaporizador.{0,25}\bropa\b'),
  ('Electrodomésticos', 'Vaporizadores de ropa', 'appliance')),

 # Lavadoras antes que todo: lo que queda después de quitar fundas,
 # pastillas y refacciones es el aparato. Incluye la centrifugadora suelta,
 # que el catálogo ya trae (Koblenz SCK-60, HKPRO HK-37) sin subcategoría
 # porque su título tampoco dice "secadora".
 (re.compile(r'\blavadora|\blava\w*secadora|\bcentrifugadora'), ('Lavadoras', None, 'washer')),
 # Aspiradoras: el título siempre nombra el aparato ("aspiradora", "aspirador",
 # "robot aspirador", "shop vac"). La licuadora que Amazon metió en la sección
 # se va a su categoría de siempre, no a Aspiradoras.
 # Las piezas van antes que el aparato: veintiocho anuncios de esta captura
 # son cuchillas, vasos y juntas que dicen "licuadora" en el título. El
 # catálogo ya tiene el precedente (p530, "Short 6-blade Blender Blade
 # Replacement for Ninja TB301") en Refacciones para electrodomésticos.
 # Hacen falta las tres condiciones a la vez -- el aparato, la pieza y la
 # palabra "repuesto" -- porque cualquiera de ellas suelta se lleva por
 # delante a una licuadora de verdad: la SIGNA se anuncia "Con Vaso" y la
 # portátil de 800 ml presume "6 Cuchillas".
 (re.compile(r'^(?=.*(licuadora|blender|nutribullet|nutri\b|'
             r'extractor|exprimidor))'
             r'(?=.*(repuesto|recambio|reemplazo))'
             r'(?=.*(cuchilla|aspa|hoja|vaso|taza|junta|pieza|'
             r'anillo de sellado|base de))'),
  ('Refacciones', 'Refacciones para electrodomésticos', 'gear')),
 # Cuatro nombres que ya son la pieza y no necesitan decir "repuesto":
 # ninguna licuadora entera se anuncia como "cuchilla extractora" ni como
 # "vaso de licuadora".
 (re.compile(r'cuchilla (extractora|cruzada|inferior|de licuadora)|'
             r'hojas? extractora|vasos? de licuadora|base de cuchilla|'
             r'sellos? de silicona para licuadora'),
  ('Refacciones', 'Refacciones para electrodomésticos', 'gear')),
 # El aparato. Junto a "licuadora" van las cuatro maneras de nombrar lo
 # mismo que usa la sección: extractor de jugos, extractor de nutrientes,
 # exprimidor eléctrico y prensado en frío. La subcategoría se llama
 # "Licuadoras y extractores" justamente por eso.
 (re.compile(r'\blicuadora|extractor(a|es)? de (jugo|nutrientes)|'
             r'\bexprimidor|prensado en frio|masticacion lenta'),
  ('Electrodomésticos', 'Licuadoras y extractores', 'appliance')),
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
 (re.compile(r'^filtro\b.{0,60}refrigerador|refrigerator water filter'),
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
             r'recipientes de vidrio hermetico|'
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
 # Purificadores de agua, después de los filtros de refrigerador: los dos
 # dicen "filtro de agua" y el del refri no purifica nada, repone una
 # pieza. La subcategoría del catálogo guarda juntos el aparato y sus
 # cartuchos (los Hydrofast HF03, los JIMMY R9), así que el kit
 # mineralizador y el filtro suelto van con los equipos de ósmosis.
 (re.compile(r'purificador(a|es)? de agua|purificadora de agua|'
             r'osmosis inversa|filtracion de agua|filtro de agua|'
             r'botella purificadora'),
  ('Electrodomésticos', 'Purificadores de agua', 'appliance')),
 # Máquinas de coser. El catálogo ya tiene la subcategoría con cincuenta y
 # cinco fichas, pero ninguna regla la alcanzaba: hasta hoy las dieciséis
 # máquinas de la captura caían en "no encaja". Primero las piezas, que
 # nombran la máquina igual que las cuchillas nombran la licuadora: el
 # prensatelas, la bobina, el porta-carrete y la mesa de extensión que se le
 # acopla al brazo. Después el aparato, en sus tres nombres: "máquina de
 # coser", la overlock que sobrehila y la recta de chapa.
 (re.compile(r'prensatelas|bobinas? (de aluminio|para maquina|vacias)|'
             r'soporte para (carrete|hilo)|mesa de (extension|expansion)'),
  ('Refacciones', 'Refacciones para electrodomésticos', 'gear')),
 (re.compile(r'maquina de coser|maquina overlock|\boverlock\b|'
             r'maquina.{0,20}sobrehilado|\bsewing\b'),
  ('Electrodomésticos', 'Máquinas de coser', 'appliance')),
 # Cocina: primero las piezas sueltas, que nombran el aparato al que le
 # entran ("Microinterruptor Para Horno Microondas", "Botón de Interruptor
 # para Olla a Presión", "Perilla del Eje de Repuesto ... freidora de
 # aire"); si no, acabarían en la sección del aparato.
 (re.compile(r'micro ?interruptor|interruptor de puerta|'
             r'boton de interruptor|manguera de repuesto|^repuesto\b|'
             r'anillos de sellado|disco de formas|'
             r'perillas? (del eje|de repuesto)|cable de alimentacion universal'),
  ('Refacciones', 'Refacciones para electrodomésticos', 'gear')),
 # Seis maneras de nombrar el mismo aparato: Cuisinart escribe "Freidora
 # Aire" sin el "de", T-Fal lo llama "Horno Freidor", Ninja lo vende por
 # capacidad ("Freidora de 4 cuartos") y varias marcas usan el inglés.
 (re.compile(r'freidora de aire|freidora aire|air ?fryer|horno freidor|'
             r'freidora de \d+ cuartos|'
             r'freidora electrica.{0,60}sin aceite'),
  ('Electrodomésticos', 'Freidoras de aire', 'appliance')),
 # Batidora de pedestal: el catálogo tiene treinta en Pequeños
 # electrodomésticos de cocina, ninguna entre las licuadoras.
 (re.compile(r'batidora de (pedestal|pie)|batidora planetaria'),
  ('Electrodomésticos', 'Pequeños electrodomésticos de cocina',
   'appliance')),
 # La GRAVITA abre "Cafetera Tetera Eléctrica Hervidor": es un hervidor.
 (re.compile(r'hervidor|\btetera\b'),
  ('Electrodomésticos', 'Pequeños electrodomésticos de cocina', 'appliance')),
 # El horno de microondas va antes que los demás aparatos porque el Chefman
 # "horno tostador de freidora de aire" ya se fue arriba con las freidoras.
 (re.compile(r'\bmicroondas\b'),
  ('Electrodomésticos', 'Microondas', 'appliance')),
 # Lo que sustituye a la estufa: las parrillas de inducción y las de
 # quemadores, sean portátiles o empotrables. El catálogo las guarda en
 # "Estufas y hornos" ("Parrilla Eléctrica de 24 IN 4 quemadores").
 # Antes que la parrilla de mesa, que no tiene quemadores.
 (re.compile(r'parrilla (electrica )?de induccion|estufa de induccion|'
             r'\d+ quemador|quemadores|parrilla electrica empotrable|'
             r'cocina electrica (portatil|de ceramica)|de un solo quemador'),
  ('Electrodomésticos', 'Estufas y hornos', 'appliance')),
 # Lo industrial y lo comercial va con el equipo de negocio: la plancha de
 # encimera de 17 pulgadas, la máquina de 25 hot cakes y la waflera Waring.
 (re.compile(r'\b(industrial|commercial)\b(?=.*(hot cakes|waffle|parrilla))|'
             r'plancha.{0,40}industrial'),
  ('Equipo comercial', 'Cocina industrial', 'factory')),
 # El resto de la sección: todo lo que se enchufa en la barra de la cocina
 # y el catálogo guarda en "Pequeños electrodomésticos de cocina" (ollas,
 # arroceras, tostadores, wafleras, sandwicheras, creperas, básculas, las
 # Ninja SLUSHi). "Máquina de/para" vale solo con lo que hace, porque la
 # "Máquina de coser" y la "Máquina de hielo" son otra cosa... salvo que
 # la máquina de hielo de barra también vive aquí.
 (re.compile(r'olla (a presion|de presion|de coccion|electrica|arrocera|'
             r'de huevos?)|multicooker|arrocera|vaporera|arroz y grano|'
             r'tostador|toaster|waf+lera|waffle|gofre|gofrar|'
             r'sandwichera|panini|sandwiches|crepera|raclette|'
             r'parrilla (electrica|panini|raclette|de interior|y plancha)|'
             r'plancha (electrica|de ceramica)|sarten electric|'
             r'electric sarten|asador|batidora|amasadora|'
             r'mezclador (clasico|electrico)|picador electrico|'
             r'mini chopper|sistema de cocina|food prep|'
             r'bascula.{0,30}(cocina|alimentos)|b.scula digital de cocina|'
             r'palomit|castella|pastelitos|pastelero|magdalenas|'
             r'hot cakes|maquina (de|para) (pan|desayuno|malteadas)|'
             r'slushi|granizados|ice maker|maquina de hielo|'
             r'freidora electrica|deshidratador'),
  ('Electrodomésticos', 'Pequeños electrodomésticos de cocina',
   'appliance')),
 # La cafetera de verdad, después del hervidor: sub_cafetera() reparte
 # entre las subcategorías del catálogo por lo que dice el título.
 (re.compile(r'\bcafetera'), ('Cafeteras', None, 'coffee')),
 # Energía portátil, en tres escalones y en este orden.
 #
 # Primero la batería de cámara, que no es ninguno de los otros dos: las
 # ocho estaciones de carga Tilta y el hub del X3 cargan celdas NP-FZ100,
 # LP-E6 y DMW-BLK22, y el catálogo guarda esas piezas en Accesorios de
 # cámaras. Tilta, además, solo fabrica accesorios de cámara: su brazo
 # articulado entra por la marca.
 (re.compile(r'\btilta\b|np-?fz100|lp-?e6|dmw-?blk|bateria (para|de) camara|'
             r'hub de cargador de bateria'),
  ('Cámaras y fotografía', 'Accesorios', 'camera')),
 # Después la estación de energía, que es el aparato con toma de corriente
 # de 110 V: la DJI Power 1000, la EcoFlow DELTA 3 y las DaranEner. El
 # catálogo tiene la subcategoría desde hace tiempo.
 (re.compile(r'estacion de energia|central electrica portatil|'
             r'\bpower station\b'),
  ('Otros', 'Energía portátil y paneles solares', 'battery')),
 # Y al final la batería portátil, que sube hasta aquí desde el final de
 # REGLAS. Tenía que adelantarse: la MARBERO y la MR. GADGETS se anuncian
 # como "fuente de alimentación" y se iban con las fuentes de poder de PC,
 # y cinco power banks "para MacBook Pro" se iban a Laptops. Junto a "power
 # bank" van las cinco maneras de decir lo mismo que trae la captura:
 # batería externa, magnética, inalámbrica, MagSafe y powerstation.
 (re.compile(r'^(?!.*(bocina|barra de sonido|soundbar|altavo))'
             r'(?=.*(power ?bank|powerbank|bateria portatil|banco de energia|'
             r'cargador(es)? portatil|bateria externa|power ?station|'
             r'bateria (magnetica|inalambrica|magsafe)|\d+ ?mah bateria|'
             r'cargador inalambrico portatil))'),
  ('Baterías portátiles', None, 'battery')),
 # El cargador de pared y el cable, que la captura trae sueltos y hasta hoy
 # no tenían regla: el pack GAN de 140 W de DJI, el CUKTECH de 65 W, el
 # cubo de 20 W y el cable Lightning de UGREEN.
 (re.compile(r'cargador (de pared|de corriente|de casa)|'
             r'cargador.{0,25}\bgan\b|\bgan\b.{0,25}cargador|'
             r'cargador (usb ?c |tipo c )?\d+ ?w\b|cubo de carga|carga rapida cubo|'
             r'pack de carga'),
  ('Cargadores y adaptadores', 'De pared', 'plug')),
 (re.compile(r'^(?:\S+ ){0,2}cable (alargador|usb|lightning|convertidor|de impresora)|'
             r'lightning cable|cable mfi'),
  ('Cargadores y adaptadores', 'Cable', 'plug')),
 # La impresora 3D y la terminal de cobro, una de cada una en la captura y
 # las dos con su lugar hecho en el catálogo.
 (re.compile(r'impresora 3d'), ('Impresión 3D', 'Impresoras', 'printer')),
 (re.compile(r'terminal para tarjetas|mercado pago point|punto de venta'),
  ('Equipo comercial', 'Punto de venta', 'factory')),
 # El celular, cuando el título es solo marca y modelo. Pide abrir con la
 # marca y descarta de una vez los Buds, los Watch y las Tab, que empiezan
 # igual y no son teléfonos.
 (re.compile(r'^(samsung galaxy|apple iphone|galaxy z fold)'
             r'(?!.*\b(buds|watch|tab|book|fit|ring)\b)'
             r'(?!.*(bateria|power ?bank|cargador|funda|\bcase\b))'),
  ('Celulares', None, 'phone')),
 # El soporte de celular no es el celular: el catálogo lo tiene en Varios.
 (re.compile(r'^soporte para celular|base para celular'),
  ('Otros', 'Varios', 'box')),
 (re.compile(r'computadora escritorio (completa|amd|intel)|pc gamer factor'),
  ('Computadoras de escritorio', 'Torre / Escritorio', 'desktop')),
 # Solo si "laptop" abre el título: "power bank para laptop" y "soporte para
 # monitor y laptop" la nombran como destino, no como producto.
 # "macbook" también pide abrir el título: seis power banks, un cargador de
 # pared, un cable y un mouse de esta captura lo nombran como lo que cargan
 # o a lo que se conectan ("Cargador de Laptop Portátil para MacBook Pro").
 (re.compile(r'^laptop\b|^(?:\S+ ){0,3}macbook (pro|air)'), ('Laptops', None, 'laptop')),
 # El proyector va primero, pero solo cuando la palabra es la primera o la
 # segunda del título: el "AOC Proyector portátil 4K" es el aparato y la
 # "Pantalla de Proyector con Trípode" nombra al proyector como destino, y
 # ahí "proyector" ya es la tercera palabra.
 (re.compile(r'^(?:\S+ )?proyector\b(?!.*pantalla)'),
  ('Proyectores y accesorios', 'Proyectores', 'projector')),
 # Pantallas de proyección antes que las TV: también se venden como
 # "Pantalla 100 pulgadas", pero dicen proyección/proyector, "lienzo",
 # "eléctrica" (la que se enrolla con motor) o traen trípode.
 (re.compile(r'proyec(cion|tor)|lienzo de proyec|pantalla electrica|'
             r'pantalla de 16:9|projector screen'),
  ('Proyectores y accesorios', 'Pantallas de proyección', 'projector')),
 # Televisores: "pantalla NN pulgadas" es como Amazon México nombra una TV;
 # "Pantalla 4K" de un mini PC no cae porque pide dos dígitos y pulgadas.
 (re.compile(r'smart tv|televisor|television|roku tv|crystal uhd|'
             r'pantalla (led )?\d{2}(\.\d)? ?(pulgadas|"|”)|\d{2}" (hd|4k) tv'),
  ('Televisores', None, 'tv')),
 # Antes que los videojuegos: el monitor portátil enumera "PS5, Xbox, Switch"
 # como lo que se le puede conectar.
 (re.compile(r'monitor portatil'), ('Monitores', 'Portátiles', 'monitor')),
 # Los videojuegos dejan pasar al teclado y al mouse: el HyperX Alloy Core
 # y los dos ratones Corsair listan "PS5" y "Xbox" entre lo que aceptan, y
 # con eso se iban a Accesorios de videojuegos. Un título que dice "teclado"
 # o "mouse" es un teclado o un mouse, conecte donde conecte, y los dos
 # tienen su regla al final de REGLAS.
 (re.compile(r'^(?!.*(teclado|\bmouse\b|\braton\b))'
             r'(?=.*(switch ?2|steam ?deck|rog ally|legion go|msi claw|freno de mano|handbrake|'
             r'consola de juegos|\bps5\b|mando bdm|gun grip|golf|juego de interruptor|'
             r'interruptor ns|base portatil ns))'), VJ),
 (re.compile(r'webcam|camara web|camara de computadora|camara para pc|lifecam|facecam|'
             r'\bkiyo\b|streamcam|\bbrio\b|sistema de camara para sala|'
             r'sistema de videoconferencia|camara usb hdmi|camara de alta velocidad|'
             r'camara hdmi ptz|obsbot'), (PC, 'Webcams', 'cpu')),
 # El audio va antes que "monitor", porque en audio esa palabra significa
 # otra cosa: las Edifier R1000T4 son "Bocinas Monitores Tipo Estudio", los
 # KZ EDX Pro son "Audífonos con Monitor Dentro del oído" y el Phenyx Pro es
 # un "Sistema de monitoreo in-Ear". Los tres acababan en Accesorios de
 # monitor, que es donde van los brazos y las bases de pantalla.
 #
 # Las bocinas de coche primero: el catálogo nunca las guarda en Bocinas
 # sino en "Audio y multimedia para auto" (cincuenta y cinco fichas contra
 # ninguna), y se reconocen por cómo se venden -- coaxiales, de 6x9, de dos
 # o tres vías, de rango medio, o diciendo "para auto".
 (re.compile(r'\bcoaxial|\b6 ?x ?9\b|(rango medio|medio rango)|'
             r'bocinas? (para|de) auto|autoestereo|car audio|'
             r'altavoces de componentes'),
  ('Autos, bicicletas y motos', 'Audio y multimedia para auto', 'speaker')),
 # La bocina, con las cuatro maneras de nombrarla que usa esta captura:
 # "bocina", "bafle", "altavoz/altavoces" y la máquina de cantar karaoke,
 # que el catálogo ya tiene entre las bocinas.
 (re.compile(r'\becho (pop|dot|show|studio|hub)\b|\balexa\b|google nest|'
             r'\bnest (audio|mini|hub)\b|bocina intelig|altavoz intelig'),
  ('Domótica y hogar inteligente', 'Bocinas y asistentes inteligentes', 'speaker')),
 (re.compile(r'bocina|bafle|altavo(z|ces)|maquina de cantar|\bspeaker\b|'
             r'monitores? (de |tipo )?estudio'),
  ('Bocinas', None, 'speaker')),
 # Audífonos: "audífonos" es la palabra del catálogo, pero media captura
 # dice "auriculares", y las marcas grandes venden "Buds" y "headphones"
 # sin traducir. "Diadema" sola no basta -- también es una vincha -- así
 # que pide cable, micrófono o inalámbrico al lado.
 (re.compile(r'audifonos|auriculares|\bearbuds?\b|\bbuds\b|headphones|'
             r'\bin[- ]?ear\b|monitoreo in[- ]?ear|'
             r'\bdiadema\b.{0,30}(cable|microfono|inalambric)'),
  ('Audífonos', None, 'headphones')),
 # El micrófono suelto es de la sección de instrumentos, que es donde el
 # catálogo guarda los doce de solapa y los inalámbricos.
 (re.compile(r'microfono (inalambrico|de solapa|condensador|lavalier)|'
             r'kit de microfono'),
  ('Instrumentos musicales', 'Amplificadores y micrófonos', 'mic')),
 # "monitor" va antes que los componentes para que "Soporte de escritorio
 # para un monitor" no caiga en muebles; el único componente que dice
 # "monitor" (la pantalla de un AIO) está en EXPLICITOS.
 (re.compile(r'monitor'), (PC, 'Accesorios de monitor', 'cpu')),
 # Muebles: el escritorio sobre el que va la computadora, no la computadora.
 # Solo si la palabra abre el título: "RAM de escritorio" y "PC de escritorio"
 # la usan como adjetivo.
 (re.compile(r'(?!.*\bmouse\b)(alfombrilla|tapete) (de|para) (computadora|escritorio|teclado)|\bdesk ?(mat|pad)\b'),
  (PC, 'Periféricos y accesorios', 'mouse')),
 (re.compile(r'^(?:\S+ ){0,2}escritorio (para|de|minimalista|con|gamer|diseno)|computadora de pie\b'),
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
 (re.compile(r'memoria ram|\bram\b|sodimm|udimm|\bddr[45]|modulo de memoria'),
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
]

# Anuncios que ninguna regla decide bien; cada uno leído a mano.
EXPLICITOS = {
 # Decimosexta captura. Cinco anuncios cuyo título es marca y modelo y
 # nada más: Razer y SteelSeries bautizan sus periféricos y dan por
 # sabido lo que son. Los cuatro primeros son ratones y teclados de
 # catálogo; el SoundPEATS trae la funda en el título y por eso lo
 # descartaba la guarda de fundas, pero lo que se vende son los audífonos.
 "B0F72VH42N": ("RAZER", 'Mouse', 'Oficina', 'mouse'),
 "B0DSCV9HGJ": ("RAZER", 'Mouse', 'Gaming', 'mouse'),
 "B0F85WRNZG": ("RAZER", 'Mouse', 'Gaming', 'mouse'),
 "B0D4RKYZJ5": ("STEELSERIES", 'Teclados', 'Mecánicos', 'keyboard'),
 "B0GX5167M8": ("SOUNDPEATS", 'Audífonos', 'Earbuds inalámbricos', 'headphones'),
 # Cocina, decimoquinta captura. La Chefman "Freidora digital
 # multifuncional + asador, deshidratador" es una freidora de aire con
 # rosticero, pero el título nunca dice "aire". El NutriBullet se anuncia
 # como "Batidora" y el Ninja CrushBOSS como "Sistema de Cocina": los dos
 # son licuadoras de vaso, con el resto de NutriBullet y Ninja.
 "B08DL8WH9V": ("CHEFMAN", 'Electrodomésticos', 'Freidoras de aire', 'appliance'),
 "B012T634SM": ("NUTRIBULLET", 'Electrodomésticos', 'Licuadoras y extractores', 'appliance'),
 "B0HD9M1PVH": ("NINJA", 'Electrodomésticos', 'Licuadoras y extractores', 'appliance'),
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
 # Dice las cuatro cosas: "Cepillo Alisador De Cabello, Plancha Inalámbrica
 # De Peine Caliente, Cepillo Secador De Inalámbrico, Cepillo Rizador". Abre
 # nombrando el alisador y la plancha, que es lo que se vende; el "secador"
 # aparece de paso y por él la regla de arriba lo dejaría fuera.
 "B0GFJYK5C4": (None, 'Aparatos de belleza', 'Planchas y rizadores', 'sparkle'),
 # Se anuncia como "Robot de Limpieza de Ventanas" pero el resto del título
 # dice lo que es: "Limpiador de Vidrios Eléctrico de Mano, 2000Pa, con
 # Batería Recargable, Hoja de Escobilla de Goma de 11 Pulgadas para Puertas
 # de Ducha". No trepa el vidrio solo: es una aspiradora de mano con jalador.
 "B0HBPKT3KS": ("FTVOGUE", 'Aspiradoras', 'Inalámbricas y de mano', 'vacuum'),
 # El único título de la sección que no nombra la fritura: "Ninja Crispi Pro
 # - Sistema de cocción de vidrio | Bone | AS101LG". Es el hermano mayor del
 # Crispi y del Crispi DualZone, que en esta misma tanda sí se anuncian como
 # "Freidora de aire de vidrio". Se decide a mano, no por parecido de regla.
 "B0FPPP568C": ("NINJA", 'Electrodomésticos', 'Freidoras de aire', 'appliance'),
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
 # Los dos de la sección de licuadoras que el título deja a medias.
 # "NutriBullet Blender Combo Easy Twist Blade" no es la licuadora Combo:
 # a 473 pesos y 2.3 kg es la cuchilla de rosca que se le cambia, y va con
 # las otras veintisiete piezas.
 "B0846LSYDJ": ("NUTRIBULLET", 'Refacciones',
                'Refacciones para electrodomésticos', 'gear'),
 # La Oster ActiFit+ es una licuadora personal de 1200 W con tres vasos
 # portátiles, pero su título nunca dice "licuadora" ni "extractor".
 "B07PDSW3TJ": ("OSTER", 'Electrodomésticos',
                'Licuadoras y extractores', 'appliance'),
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
# Las cinco marcas que se nombran en las secciones de planchas y de limpieza
# de ventanas. El resto de los robots se anuncia sin marca: el título es una
# lista de características, y así quedan también los diez que el catálogo ya
# tenía sin marca.
MARCAS += ["FMART", "HOBOT", "SUPERTRUST", "NEWBEALER", "SILVER STAR"]
MARCAS += ["COMFEE", "POWERXL", "BOGNER", "KITCHENAID", "GREENPAN", "DASH",
           "CUISINART", "NINJA", "HUKËN", "CECOTEC", "T-FAL", "INSTANT POT",
           "GOURMIA", "OSTER", "ELITE GOURMET", "YOGONEV"]
# Las marcas de la sección de pequeños electrodomésticos de cocina. "Bella"
# y "Nostalgia" son marcas aunque parezcan palabras sueltas: abren el
# título con guion ("Bella - Olla de cocción lenta").
MARCAS += ["UNCANNY BRANDS", "HAMILTON BEACH", "TAURUS", "RAGANET",
           "RAGABASICS", "REDLEMON", "BELLA", "NOSTALGIA", "SIGNA", "EUROGAR",
           "PARIS HILTON", "SANRIO", "SELECT BRANDS", "HOLSTEIN HOUSEWARES",
           "MOSS & STONE", "AROMA HOUSEWARES", "KARINEAR", "IQ TECH",
           "HOTSPOT", "AEKA", "WJTNG", "FINYQBET", "ULTREAN", "SUGARWHISK",
           "CASA LITUS", "GRAVITA", "NUTRIBULLET", "WARING", "BENE CASA",
           "HOLSTEIN", "ZEPTER", "MAGIC BULLET"]

ALIAS = {"THERMALRLGHT": "THERMALRIGHT", "WHITE-WESTINGHOUSE": "WHITE WESTINGHOUSE",
         "KÄRCHER": "KARCHER", "HUKËN": "HUKEN"}

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

def sub_cafetera(tn):
    if re.search(r'capsula', tn): return 'De cápsulas'
    if re.search(r'espresso|expreso|\d+ bares', tn):
        return 'Espresso automáticas y semiautomáticas'
    if re.search(r'portatil|de viaje', tn): return 'Portátiles'
    if re.search(r'molinillo|molino de cafe', tn): return 'Molinillos de café'
    return None

def sub_celular(tn):
    return 'iPhone' if 'iphone' in tn else 'Android'


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
    elif cat == 'Cafeteras': sub = sub_cafetera(tn)
    elif cat == 'Celulares': sub = sub_celular(tn)
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
