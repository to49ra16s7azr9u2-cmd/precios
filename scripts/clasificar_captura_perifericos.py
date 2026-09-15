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
catálogo ya tiene "Aspiradoras / Accesorios" para ellos.

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
alisadores ("Aparatos de belleza / Planchas para cabello") y la máquina de
sublimación 8 en 1 ("Equipo comercial / Prensas de calor").

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
subcategoría se llama "Licuadoras", pero pedía la palabra
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
parrillas de inducción y de quemadores (a "Estufas", con la
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
"Bocinas para auto" -- cincuenta y cinco fichas contra ninguna
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

La decimoséptima vuelve a ser la tienda entera, 2,274 anuncios, y solo
114 no estaban en la anterior: la sección de microondas y la de
lavavajillas. Cincuenta y cinco son un aparato (41 microondas, ocho
lavavajillas, dos interruptores de puerta, y sueltos un enfriador de
aire, una cerradura inteligente, un irrigador dental y una almohada) y
51 entran como fichas nuevas; los otros cuatro no traían precio. Los
microondas ya tenían regla. Los lavavajillas no, aunque el catálogo
guarda 37 en su propia subcategoría, y sin regla caían donde caía
cualquier otra palabra del título: tres en Componentes de PC por
"ventilador de secado", uno en Lavadoras por "lavadora de tazas". La
regla nueva pide que el lavavajillas abra el título o lleve apellido
("de encimera", "de 13 cubiertos"), y no la palabra suelta, porque la
palabra suelta es "apto para lavavajillas" en la olla de cocción lenta,
la freidora y el mini picador, que con la primera versión de la regla se
iban los cinco a Lavavajillas.

Los 59 descartes son la sección de lavavajillas casi entera: 31
consumibles y accesorios (detergente, sal, abrillantador, el imán de
limpio/sucio, canastillas, la manguera de drenaje), seis "mini
lavavajillas" que son un balde con chorro o un limpiador ultrasónico de
tazas y se distinguen porque dicen USB, recargable o plegable y nunca
cuántos programas tienen, nueve utensilios de microondas (cocedores de
huevo, tapas, la repisa de pared), cinco estantes, dos juegos de
recipientes de vidrio y el rollo de papel pergamino. Cascade y Finish
venden detergente sin decir para qué, así que se descartan por la marca.

Cuatro reglas viejas se corrigieron. La de freidoras se llevaba el
"Horno Microondas Air Fryer 3 en 1" de Cuisinart, que es un microondas
y el catálogo guarda cuatro iguales en Microondas; la guarda pide "horno
microondas" y no "microondas" a secas porque la Ninja Crispi dice que
sus recipientes van al microondas. La de purificadores de agua se
llevaba el irrigador dental por el "Filtro de Agua" del título; ahora el
irrigador se decide antes y va a Cuidado dental, junto a los cepillos
eléctricos, y las dos fichas de Waterpik y Aquasonic que estaban en
Cuidado personal se mueven con él. La de refrigeración de PC se llevaba
el enfriador de aire VORTEX, que es un climatizador evaporativo y tiene
17 iguales en Climatización; la regla nueva descarta lo que diga CPU,
procesador o socket, que es como se anuncian los Thermalright. Y la que
descarta controles remotos de repuesto leía "con control remoto" en
cualquier aparato que lo trae de fábrica; ahora "con control remoto" no
cuenta.

Desde la decimoséptima el marcador de captura (captura_amazon.html) sabe
recorrer departamentos, y cada anuncio llega con el nombre del
departamento donde Amazon lo tenía ("dept"). Cuando ese nombre coincide
con una subcategoría del catálogo ("Microondas", "Lavavajillas",
"Licuadoras") se usa tal cual y no se adivina por el título: Amazon ya
hizo ese trabajo. Cuando coincide solo con una categoría ("Electrodomésticos")
sirve de red para lo que ninguna regla reconoce. Las guardas de FUERA y
CABECERA van antes en los dos casos, porque en el departamento de
microondas también están los cocedores de huevo.

La decimoctava es la primera que llega de la extensión de Chrome y la
primera de una sola búsqueda: "celulares", 12,164 anuncios, 11,767 que
el catálogo no tenía. Tres de cada cuatro no son teléfonos: 7,370
casilleros, armarios y estaciones de carga con ranuras para guardar los
celulares de un aula (nombran "celulares" en cada título y sin la guarda
caían en gabinetes de PC), 531 persianas "celulares" de ventana (las de
panal, que Amazon traduce así), y después fundas, correas, tarjetas SIM,
lápices ópticos, aros de luz y herramientas de reparación, cada cosa con
su motivo en FUERA. Lo que sí es teléfono se reparte en tres reglas. La
primera lee la ficha técnica en el título ("8GB RAM", "128GB+8GB",
"teléfono inteligente resistente", "botones grandes para adultos
mayores") y va antes que las bocinas, los proyectores y los audífonos,
porque un celular de obra menciona su proyector y un Infinix viene en
kit con sus audífonos; solo se aparta si el título abre con el accesorio
o nombra otro aparato que también se vende por gigas (laptop, tablet,
mini PC, TV box, estéreo de coche). La segunda es marca y modelo al
principio ("Motorola Edge 70 Fusion", "Samsung S26 Ultra 256GB",
"OnePlus 15R Mint Breeze"), con la lista de marcas que Amazon México
vende. La tercera es la red: "celular", "smartphone", "dual SIM" o
"liberado" en cualquier parte, con la lista larga de guardas que
distingue el teléfono de lo que se vende "para" el teléfono.

El teléfono básico (de tapa, de botones grandes, 2G, para personas
mayores) estrena subcategoría, Básicos: no es Android y mentir con la
subcategoría era peor que dejarla vacía. La marca del celular se lee
también cuando abre el título aunque no esté en MARCAS ("vivo", "honor"
y "cat" son palabras corrientes en cualquier otra categoría). Los
soportes, trípodes, palos de selfie y ventiladores de celular van a
Otros/Varios, que es donde el catálogo los tiene; el cargador de coche
estrena De auto; el de pared se aparta cuando dice inalámbrico, Qi,
MagSafe o solar para que caiga en su regla.

La decimonovena es la búsqueda de "cargador": 7,948 anuncios, 7,815
nuevos. La palabra es la más ambigua del catálogo. Dos de cada tres
anuncios no son un cargador de consumo: 1,520 son cargadores de batería
de carrito de golf, montacargas, silla de ruedas, lancha o vehículo
eléctrico, y fuentes industriales de 36 a 96 V; otros 627 son
refacciones de maquinaria pesada, porque en español "cargador de
ruedas" es la pala mecánica y Amazon vende sus inyectores, bombas
hidráulicas y turbocompresores con esa palabra en el título. Los dos
grupos se descartan con su motivo, con guardas para que no se lleven un
cargador de laptop de 20 V ni uno de coche de 65 W.

Lo que sí es cargador se reparte por la subcategoría que ya tenía el
catálogo, que hasta ahora casi nadie usaba: De pared (1,031), Para
laptop (la marca de la laptop o la punta de 4.5 mm en el título),
Inalámbrico (Qi, MagSafe, almohadilla), De auto (encendedor), Base de
carga, Adaptador de corriente, De pilas, Cable, y Otros para lo que
dice cargador y no cae en ninguna. Y lo que se carga pero tiene cajón
propio sale de Cargadores: la batería y el arrancador de auto van a
Baterías para auto, la batería de taladro a Accesorios para
herramientas eléctricas, el cargador del patinete y el de la bicicleta
eléctrica a sus refacciones, el de la afeitadora o la caminadora a
Refacciones para electrodomésticos, el de la cámara a Accesorios de
cámaras y el del dron a Accesorios de drones.

La vigésima es "batería portátil": 11,992 anuncios, 11,508 nuevos. La
palabra tiene tres sentidos en español y Amazon devuelve los tres. Uno
es el power bank, que es lo que se buscaba. Otro es el instrumento: la
captura trae 361 tarolas, baquetas, pedales de bombo, almohadillas de
práctica y hasta la tarima donde se monta, y "batería portátil de 12
pulgadas" no es un cargador; la regla de Instrumentos va antes que
todas para que no acabe en power banks. El tercero es el paquete de
celdas de litio de 12 o 24 V medido en amperios-hora (para autocaravana,
panel solar o antena satelital): no tiene salida USB, no se mide en mAh
y el catálogo no tiene dónde ponerlo, así que se descarta con su motivo.

"Portátil" tiene el mismo problema: es el adjetivo y también la laptop.
La regla de Laptops se adelanta a la de Memoria RAM porque "LG gram 17,
32 GB LPDDR5" y "Lenovo V15, 8GB DDR5" nombran su memoria en el título
y se iban a módulos sueltos; pide pulgadas o procesador, y descarta lo
que abre con mouse, teclado, funda o mochila.

Lo demás que la búsqueda trae a batería va a la categoría que le toca y
que el catálogo ya tenía: 1,353 flejadoras eléctricas (la herramienta
que cierra el fleje de una tarima, casi todas el mismo anuncio repetido)
a Herramientas eléctricas; 412 cortacéspedes, motosierras, sopladoras y
tijeras de podar a Jardinería; 652 arrancadores de coche a Baterías para
auto; 236 ventiladores portátiles a Ventiladores; 431 estaciones de
energía a las suyas; y las linternas y luces de trabajo a Lámparas de
emergencia.

La vigesimoprimera es "laptop": 3,577 anuncios y la más limpia de las
tres de esta tanda, porque la palabra solo significa una cosa. Entran
2,585 fichas, 2,132 de oficina y 195 gamer, que es como parte el
catálogo y que hasta hoy no se decidía: las laptops entraban sin
subcategoría. La gamer se reconoce por lo que dice de sí misma (gamer,
gaming, ROG, TUF, Legion, Nitro, Victus) o por la GPU dedicada y los
144 Hz de pantalla.

La regla de Laptops pasa a abrir REGLAS. Su ficha técnica pisaba media
docena de categorías: "webcam con obturador de privacidad" mandaba 339
laptops a Webcams, "16GB RAM 512GB SSD" mandaba 208 a Memoria RAM, "8 GB
+ 256 GB" mandaba 151 a Celulares y "Pantalla 15.6"" mandaba 31 a
Televisores. Puesta primero, las cuatro cosas se arreglan solas. Lo que
se vende alrededor de la laptop se aparta por el principio del título
(funda, mochila, soporte, dock, cargador) o por la guarda (pantalla LCD
de repuesto, back cover, bisagras), y cada uno tiene su regla más abajo.
La guarda también aparta el all-in-one y el monitor portátil, que dicen
las mismas pulgadas y el mismo procesador.

La vigesimosegunda es "tablet": 7,980 anuncios. La regla de Tabletas sube
al principio de REGLAS, al lado de la de Laptops y por la misma razón:
su ficha técnica la mandaba a Memoria RAM ("16GB RAM 128GB ROM", 265
casos), a Celulares ("8 GB de RAM, solo wifi", 256) y al all-in-one
("panel táctil todo en uno", 138). Pero la tableta necesita una guarda
que la laptop no: media tienda se anuncia como "compatible con iPhone,
iPad y tablets", así que la palabra tiene que salir en las primeras
seis del título y no vale en cualquier parte. Sin eso, la regla se
llevaba audífonos, power banks y cables por la lista de compatibilidad.
El armario de carga de tabletas (el de las aulas) se descarta con los
casilleros de celulares, que ya tenían regla.

La vigesimotercera es "monitor": 12,691 anuncios y el error más grande
que tenía el clasificador. La regla de accesorios de monitor pedía solo
que el título dijera "monitor", así que 7,562 monitores de verdad
entraban como accesorios: la categoría Monitores no crecía y Accesorios
de monitor se llenaba de pantallas. Ahora hay dos reglas. La de
accesorios pide que el título nombre el accesorio (brazo, soporte,
base, elevador, filtro de privacidad, barra de luz, placa VESA), y la
de Monitores abre REGLAS junto a Laptops y Tabletas.

La de Monitores pide la palabra en las primeras doce del título, porque
la marca y el modelo van antes ("MSI Pro MP275W E2 27\" IPS 1920 x 1080
(FHD) Monitor de Oficina"), más una seña de pantalla: pulgadas, FHD,
QHD, 4K, los hercios, el tipo de panel o el conector. Y aparta por la
guarda lo que dice "monitor" sin serlo: el monitor de bebé, el de
signos vitales, el de calidad del aire, el de estudio (que es una
bocina y el catálogo guarda en Bocinas), el de reposacabezas de coche y
la tableta gráfica. "VESA" no puede estar en esa guarda: un monitor de
verdad presume su montaje VESA, y ponerlo ahí tiraba justo los buenos.

Monitores estrena sus tres subcategorías, que existían y estaban casi
vacías: Portátiles (el que se lleva en la mochila, incluido el extensor
de pantalla de laptop), Gaming (lo dice el título, o pasa de 120 Hz) y
Oficina para el resto.

La vigesimocuarta es "bocina": 12,134 anuncios. Aquí la regla de la
bocina ya estaba bien; lo que faltaba era el reparto. Bocinas tenía
cuatro subcategorías desde hace tiempo (Pequeña, Mediana, Grande y
Barras de sonido) y 1,802 fichas sin ninguna, porque nunca se escribió
el desempate. Ahora sub_bocina lo decide con lo que el título trae de
verdad: la barra de sonido lo dice en el nombre, y para el tamaño la
seña más honesta son los watts, que salen en 1,917 de los anuncios. De
100 W para arriba es la torre o el bafle de fiesta; hasta 15 W es la
portátil de bolsillo; en medio queda todo lo demás. Cuando no hay
watts se decide por cómo se vende: "torre de sonido", "bafle
profesional", "boombox" y los conos de 12 pulgadas o más son grandes;
"mini", "clip", "de ducha" y "de llavero" son chicas.

Lo que rodea a la bocina sale de la categoría. El soporte de piso, la
pata de aislamiento y la rejilla se descartan con su motivo (eran 18
fichas ya en el catálogo que estaban como bocinas). El cable de altavoz
y el SpeakOn van a Cable. El driver suelto, el cono y la bobina de voz
se descartan: son la pieza de dentro, para reparar o para armar una
caja. Y la bocina de coche se reconoce mejor: antes pedía "bocina para
auto" y ahora también vale "altavoces de coche", el tweeter y el
altavoz de agudos cuando abren el título, y los componentes. El
"diafragma" no puede ir suelto en esa lista: los audífonos in-ear
presumen su diafragma dinámico y se iban todos.

La vigesimoquinta es "audífonos": 6,317 anuncios. Como con las bocinas,
la regla estaba bien y lo que fallaba era el reparto. sub_audio pedía
que el título dijera la forma (diadema o in-ear) y la conexión (cable o
bluetooth), y devolvía None si faltaba cualquiera de las dos o si
aparecían las dos: de 4,729 audífonos, 4,260 se quedaban sin
subcategoría.

Ahora reconoce las dos cosas como las nombra la tienda. Para la forma:
circumaural, supraaural, "sobre la oreja", de copa, orejeras, headset,
casco y conducción ósea son diadema; intraural, intrauditivo, de botón,
earbuds, TWS, gancho de oreja, banda para el cuello y semi-in-ear son
de botón. Y las familias de modelo que dicen la forma sin decirla: los
WF y los IE de Sennheiser son de botón, los WH, los HD, los ATH-M y los
QuietComfort son de diadema. Cuando la forma sale dos veces (un
"headset" que también dice in-ear) gana la que aparece antes en el
título, que es la que nombra el producto; cuando el inalámbrico
menciona su cable auxiliar, gana el bluetooth, que es como se usa. Con
eso pasan de 469 a 2,030 fichas con subcategoría.

Los 3,124 que siguen sin ella son los que de verdad no dicen la forma
("Auriculares Bluetooth 5.3 con micrófono"). Adivinar que son de botón
porque la mayoría lo es sería inventar, y el catálogo prefiere el hueco.

Aparte, la regla de Audífonos ya no se lleva lo que se le pone al
audífono: las almohadillas y las puntas de repuesto, la espuma, el
estuche, y el escritorio que trae "gancho para auriculares" en la
descripción.

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

# "Apto para lavavajillas", "lavable en lavavajillas", "dishwasher safe":
# habla de una pieza del aparato, no de un lavavajillas. Lo comparten las
# reglas de lavavajillas de FUERA y de REGLAS, porque una olla de cocción
# lenta y una freidora lo dicen en el título.
NO_APTO_LAVAVAJILLAS = (r'(?!.*(apt[oa]s? para|lavables? en|seguros? para|lavar en|'
                        r'lavan en|lavarse en).{0,4}(lavavajillas|lavaplatos)|'
                        r'.*dishwasher[- ]safe)')

FUERA = [
 # Un suplemento que promete "apoya la salud celular" caía en Celulares por
 # esa palabra. Es consumible, que es lo que esta lista deja fuera.
 (re.compile(r'tabletas? de (agua de )?hidrogeno|hidrogeno molecular|'
             r'\b(tabletas?|pastillas?|capsulas?) .{0,30}(antioxidantes|'
             r'suplemento|vitamin)'), 'suplemento (consumible)'),
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
 # La búsqueda de "celulares" en Amazon trae 4,300 casilleros: armarios,
 # gabinetes y estaciones de carga con ranuras para guardar los teléfonos
 # de un aula o una oficina. Nombran "celulares" en cada título y sin esta
 # guarda caían en gabinetes de PC.
 (re.compile(r'^(?!.*(monitor|laptop|\d[\d.,]* ?mah|power ?bank))'
             r'(?=.*(gabinete|armario(s)? de carga|armario|casillero|taquilla|caja fuerte|'
             r'caja (de |para )(almacenamiento|seguridad|bloqueo|guardar)|closet|organizador|'
             r'estacion(es)? de carga.{0,80}(aula|oficina|escuela|escolar|clase|evento|publico|segur|bloqueo|cerradura|candado|'
             r'\d{2,} (puertos|ranuras|dispositivos|telefonos|celulares)|multiples (dispositivos|telefonos|celulares))|'
             r'cargador(es)? .{0,30}\d{2,} (ranuras|puertos)|cerradura|candado|estacion de carga movil|'
             r'cargador(es)? (portatil )?para (celular(es)?|telefonos?),? (estacion de carga|para multiples dispositivos)|carr(o|ito) de (almacenamiento|carga)|'
             r'bolsa colgante|locker|\d{2,} ranuras|\d+ compartimentos|'
             r'(caja|organizador|nizer|estante).{0,30}(guardar|compartimentos)))'
             r'(?=.*(celular|telefono|movil|dispositivo|smartphone|tablets?|tabletas?|\bipad\b))'),
  'casillero o estación de carga para guardar celulares, no es un celular'),
 # El soporte, la pata de aislamiento y la rejilla son lo que se le pone
 # a la bocina, no la bocina.
 (re.compile(r'^(?:\S+ ){0,4}(soportes?|bases?|patas?|almohadillas?|aisladores?|rejillas?|parrillas?|montajes?)\b'
             r'.{0,40}(altavo|bocina|parlante|speaker|subwoofer)|'
             r'(altavo(z|ces)|bocinas?|parlantes?).{0,30}(soporte de (pared|piso|techo)|patas de aislamiento)'),
  'soporte o accesorio de bocina, no es la bocina'),
 # El driver suelto, el cono y la bobina son la pieza de dentro de una
 # bocina, no la bocina: se compran para reparar o para armar una caja.
 (re.compile(r'^(?:\S+ ){0,3}(woofer|subwoofer|tweeter|driver) \S+ (de repuesto|sin caja|para gabinete)|'
             r'\bwoofer speaker\b|kit de reparacion de (altavo|bocina)|cono de (altavo|bocina)|'
             r'diafragma (de |para )(repuesto|altavo|bocina|compresion|driver)|(altavo|bocina).{0,20}diafragma de repuesto'),
  'refacción de bocina, no es la bocina'),
 # La búsqueda de "cargador" trae refacciones de maquinaria pesada
 # ("cargador de ruedas" es la pala mecánica), cargadores de batería de
 # carritos de golf, montacargas, lanchas y vehículos eléctricos, y
 # fuentes industriales de 36 a 96 V. Nada de eso es un cargador de
 # consumo; la guarda deja pasar lo que nombra una laptop, un USB o un
 # celular, y lo que ya tiene cajón propio (patinete, herramienta,
 # batería de auto).
 (re.compile(r'inyector de combustible|bomba (hidraulica|de engranajes|de inyeccion)|cargador(a|es|as)? de (ruedas|orugas)|'
             r'silenciador \d|pastillas de freno|parachoques|(para|compatible con) caterpillar|caterpillar cat \d|komatsu|bobcat|\bvolvo l\d|kit de carrocer|'
             r'cargadora? (frontal|de cadenas)|\bjohn deere\b|turbocompresor|valvula (hidraulica|de control|solenoide)|bomba de (combustible|piston)|'
             r'brazo de control|unidad de control del motor|elevador de carga|plataforma (de )?elevaci|carro hidraulico|ciguenal|'
             r'cremallera de direccion|\bculata\b|alternador de \d+ ?v|monorrail|hitachi \(?zw'),
  'refacción de maquinaria pesada ("cargador de ruedas"), no es un cargador'),
 # El paquete de celdas de litio de 12 o 24 V con capacidad en Ah
 # (para autocaravana, panel solar, antena satelital o carrito de
 # limpieza) no es una batería portátil: no tiene salida USB ni se
 # mide en mAh, y el catálogo no tiene dónde ponerlo.
 (re.compile(r'^(?!.*(\d+ ?mah|\busb\b|power ?bank|celular|telefono|laptop|portatil de \d|tipo c))'
             r'(?=.*bateria)(?=.*\b\d+ ?v\b)(?=.*\b\d+([.,]\d+)? ?ah\b)'),
  'paquete de celdas de litio por amperios-hora, no es una batería portátil'),
 (re.compile(r'^(?!(?:\S+ ){0,2}(soporte|montaje|funda)\b)(?!.*(patinete|scooter|hoverboard|bicicleta electrica|e-?bike|ebike|kukirin|segway|ninebot|'
             r'dewalt|makita|milwaukee|ryobi|ridgid|craftsman|arrancador|mantenedor|jump starter|'
             r'cargador (de |para )?bater[ií]as? (de |para )?(auto|coche|carro|moto|automovil)))'
             r'(?=.*(carritos? de golf|golf cart|montacargas|carretilla elevadora|forklift|sillas? (de )?ruedas|(fuente de alimentacion|cargador de bateria).{0,40}\d{4} ?w\b|'
             r'cargador (electrico )?(de|para) (valla|cerca|cerco)|baja impedancia|'
             r'\bbarcos?\b|(uso|motor|bateria|cargador) marin[oa]|\bmarine\b|vehiculos? electricos?|coches? electricos?|autos? electricos?|cargador(es)? ev\b|\bev\b (cargador|charger|adaptador)|\bevse\b|j1772|tipo 2 iec|iec 62196|wallbox|wall box|'
             r'ccs2|\bgbt\b|\d+ ?kw\b|victron|xantrex|samlex|\bmppt\b|ciclo profundo|plomo[- ]?acido|bateria agm|\bsla\b|cargador .{0,30}lifepo4|\blipo\b|'
             r'^(?!.*(laptop|portatil|notebook|macbook|chromebook|\bdell\b|\bhp\b|lenovo|\basus\b|\bacer\b|\bmsi\b|thinkpad|inspiron|'
             r'pavilion|ideapad|vivobook|zenbook|latitude|omen|legion|surface|razer|alienware|imac|usb|tipo c|\bpd\b|\bqc\b|'
             r'magsafe|iphone|celular|telefono|smartphone|tablet|ipad|reloj|watch|mah|pilas))'
             r'.*(\b(3[6-9]|[4-9]\d)([.,]\d)? ?v\b|\d+ ?ah\b|\d+ ?amperios|\d+ ?v[ /,]{0,3}\d{2,}([.,]\d)? ?a\b)))'),
  'cargador de batería de vehículo o industrial, no es un cargador de consumo'),
 (re.compile(r'(persianas?|cortinas?|estor(es)?|tonos?) (verticales |plisad[ao]s? |enrollables? |opac[ao]s? )?celular|'
             r'persianas? (plisad|de panal|enrollable)|cortinas? (para|de) (ventana|techo|puerta)|nido de abeja|'
             r'bloqueador(es)? de luz|opac[ao]s? de bloqueo'),
  'persiana celular (de ventana), no es un teléfono'),
 (re.compile(r'bolsas? faraday|bloqueador de senal|luz .{0,25}(para|de) selfie|aro de luz.{0,30}(celular|telefono|selfie|tiktok)|luz de relleno (led|para|de)|'
             r'telefono (simulado|falso)|senuelo|telefono (de audio y video|vintage).{0,60}bodas|pegatinas?.{0,30}senal|refuerzo de antena|'
             r'estabilizador (facial|para celular|de mano)|\bgimbal\b|toallitas|lens wipes|limpiador de pantalla|'
             r'herramienta para separar|separar pantallas|calentador de pantalla|spudger|'
             r'pantalla (lcd|amoled|oled).{0,40}(repuesto|reemplazo|reparacion|ensamble)|piezas de reparacion|'
             r'modelo de exposicion|telefono de exposicion|\bdummy\b|otterbox|spigen|symmetry series|defender series|'
             r'tabla de bolsillos?|\d+ bolsillos'),
  'accesorio, refacción o exhibidor de celular, no es el celular'),
 (re.compile(r'correas?( \S+){0,2} (para|de) (el )?(celular|telefono|muneca)|cordon (para|de) (el )?(celular|telefono)|'
             r'colgante para celular|cinturon (de|para) correr|brazalete|'
             r'bolsa (de|para) (correr|brazo)|rinonera'),
  'accesorio para llevar el celular, no es el celular'),
 (re.compile(r'destornillador|desarmador|kit de (herramientas|reparacion)|ventosa para pantalla|'
             r'espatula (de apertura|para abrir)'),
  'herramienta de reparación, no es el celular'),
 (re.compile(r'^(?!.*(\d[\d.,]* ?mah|power ?bank|portatil|inalambric|magsafe))'
             r'(bateria|pila) .{0,40}(de repuesto|de reemplazo|interna|compatible con|'
             r'para (samsung|iphone|xiaomi|motorola|huawei|lg|galaxy|redmi|moto\b|celular|telefono))|'
             r'bateria (de repuesto|de reemplazo|interna|original) (para|compatible)'),
  'batería de repuesto, no es el celular'),
 (re.compile(r'tarjeta sim\b|chip (telcel|at&t|movistar|unefon|bait)|bandeja (de |para )?sim|'
             r'adaptador (de )?sim|(extractor|expulsor|eyector|extraccion) (de )?(sim|chip)|'
             r'(pin|aguja).{0,20}sim\b|nano sim a micro|sim (fisica|prepago)|chip (prepago|con internet)'),
  'tarjeta SIM o refacción, no es el celular'),
 (re.compile(r'^(?!.*moto g stylus)(?=.*(lapiz (optico|stylus|capacitivo|para pantalla|tactil|de pantalla)|'
             r'stylus pen|touchscreen stylus|^lapiz\b))'),
  'lápiz óptico, no es el celular'),
 (re.compile(r'lentes? (de|para) (camara de )?(telefono|celular|movil|smartphone)|kit de lentes?|'
             r'filtro (de lente|nd|cpl|magnetico|polarizador).{0,40}(telefono|celular)|calcomania'),
  'accesorio de cámara para celular, no es el celular'),
 # Lo que se vende alrededor del lavavajillas y no es el lavavajillas: el
 # detergente, la sal, el abrillantador, el imán de limpio/sucio, la
 # canastilla y la manguera. Se nombran donde caigan ("Finish Jet Dry -
 # Asistente de enjuague para lavavajillas"), así que van en FUERA. La
 # guarda del principio es para el aparato que dice "apto para
 # lavavajillas" de sus piezas: ese sí es el aparato.
 (re.compile(r'^' + NO_APTO_LAVAVAJILLAS +
             r'(?=.*(lavavajillas|lavaplatos|lavatrastes|dishwasher))'
             r'(?=.*(detergente (para|de|lavavajillas|en polvo|liquido|automatico)|'
             r'dishwasher (detergent|pods|rinse)|\bsal (para|regeneradora)\b|'
             r'(asistente|agente) de enjuague|rinse aid|abrillantador|ambientador|'
             r'\biman\b|letrero magnetico|clean dirty|indicador de suciedad|'
             r'canastilla|cesta (inferior|de reparacion|de repuesto)|conjunto de cesta|'
             r'reparacion de escurreplatos|manguera de drenaje|adaptador de manguera|'
             r'kit de instalacion))'),
  'consumible o accesorio de lavavajillas, no es el aparato'),
 # Los "mini lavavajillas" de pila: un balde con chorro, una cubeta plegable
 # o un limpiador ultrasónico de tazas. No lavan una vajilla; el
 # lavavajillas de verdad se distingue porque dice cuántos programas tiene.
 (re.compile(r'^' + NO_APTO_LAVAVAJILLAS + r'(?=.*(lavavajillas|lavaplatos))'
             r'(?=.*(\busb\b|recargable|ultras|plegable|colapsable|cubeta|'
             r'de fregadero|limpiador (automatico|de alta presion)|lavadora de tazas))'),
  'lavador de tazas de fregadero, no es un lavavajillas'),
 # Lo que se mete en el microondas o se le cuelga encima, no el microondas.
 (re.compile(r'cocedor (de )?huevos|escalfador|tapas? (para|de) microondas|'
             r'tapa microonda|tapas de silicona|soporte de pared para microondas|'
             r'repisa (para|de|horno de) microondas|cubierta para microondas'),
  'utensilio para microondas, no es el aparato'),
 # Solo cuando el recipiente ES el producto (abre el título): la Ninja
 # Crispi es una freidora "con 2 recipientes de vidrio".
 (re.compile(r'^(?:\S+ ){0,4}(contenedores?|recipientes?|toppers?)\b'
             r'.*(vidrio|alimentos|hermetic|meal prep)'),
  'recipientes para alimentos, no es un aparato'),
 (re.compile(r'papel (pergamino|encerado|para hornear|aluminio)|parchment paper'),
  'consumible de cocina, no es un aparato'),
 # El detergente que no dice para qué es: Cascade y Finish solo hacen eso.
 (re.compile(r'^(detergente|abrillantador|platinum actionpacs|cascade|finish)\b'),
  'consumible de limpieza, no es el aparato'),
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
 (re.compile(r'\bfunda de viaje|\bfundas? (?!para pc\b)|\bestuche\b|\bcase (para|for)\b|^(?:\S+ ){1,3}for .{0,40}\bcase\b|\bcase\b \(compatible|'
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
 # remoto" lo trae de accesorio. Y "con control remoto" nunca es el
 # control: el enfriador de aire VORTEX lo dice en la palabra 7 y es un
 # enfriador de aire.
 (re.compile(r'^' + ES_ROBOT_VIDRIOS + r'(?!.*\bcon control remoto).*control remoto'),
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
PERI = (PC, 'Accesorios', 'cpu')
COMP = (PC, 'Componentes', 'cpu')

REGLAS = [
 # La laptop abre REGLAS. Es la primera regla de todas porque su ficha
 # técnica pisa media docena de categorías: "webcam con obturador" la
 # mandaba a Webcams, "16GB RAM 512GB SSD" a Memoria RAM, "8 GB + 256
 # GB" a Celulares y "Pantalla 15.6"" a Televisores. Lo que se vende
 # alrededor de la laptop (funda, mochila, soporte, dock, pantalla de
 # repuesto, cubierta) se aparta por el principio del título o por la
 # guarda, y cada uno tiene su regla más abajo.
 #
 # Antes decía: la laptop antes que la RAM: "LG gram 17, 32 GB LPDDR5" y "Lenovo V15,
 # 8GB DDR5, 256GB SSD" nombran su memoria en el título y se iban a
 # Memoria RAM. Un módulo suelto no dice pulgadas ni trae procesador.
 (re.compile(r'^(?!(?:\S+ ){0,3}(mouse|raton|teclado|combo|funda|maletin|mochila|soporte|base|cargador|adaptador|cable|bocina|altavoz|audifonos|webcam|hub|docking|dock|bolsa|estuche|backpack|porta ?laptop|set de viaje|pantalla|lcd|panel|cubierta|cover|adhesivos?|tornillos?|bisagra|ventilador|enfriador|memoria|disco|\bssd\b|\bram\b|bateria|pila|protector|mica|limpiador|'
             r'juego de|kit de|paquete de|par de|extensor|monitor|impresora|proyector|escaner|silla|escritorio|lampara)\b)'
             r'(?!.*(sodimm|udimm|modulo de memoria|solo memoria|kit de memoria|(para|compatible con|de repuesto para) (laptop|notebook|macbook)\b|mini telefono|telefono inteligente|smartphone|\bcelular(es)?\b|dual sim|back cover|bottom cover|lcd (display|screen|panel)|display panel|nexiq|diesel laptops|\baio\b|all[- ]in[- ]one|todo en uno|desktop|de escritorio|\bimac\b|mini pc|lavadora|proyecc|monitor portatil|extensor de pantalla|\btarola\b|baqueta|bombo|platillo|reproductor de dvd|para bateria|de bateria\b|flejad|\bestufa|\bhorno\b|horno de pizza|\bquemador|\bparrilla\b|plancha (de |a )?vapor|\bfreidora|licuadora|\bcampana\b|purificador|filtro de agua|vaporizador|cafetera|\bmicroondas\b|lavavajillas|aspiradora|calentador de agua|deshumidificador|humidificador|maquina de coser|\binodoro\b|\bregadera\b))'
             r'(?=.*(\blaptops?\b|\bnotebooks?\b|\bportatil(es)?\b|macbook|chromebook|ultrabook|omnibook|\bgram\b\s?\d|thinkpad|ideapad|'
             r'vivobook|zenbook|inspiron|latitude|pavilion|elitebook|probook|aspire|\bnitro\b|predator|omen|legion|'
             r'victus|swift|yoga \d|thinkbook|travelmate|modern \d|katana|cyborg|\btuf gaming\b|rog (zephyrus|strix|flow)))'
             r'(?=.*(\d{2}([.,]\d)? ?(pulgadas|")|\bfhd\b|\bwqxga\b|\bwuxga\b|intel (core|ultra|celeron|n\d)|ryzen|'
             r'\bi[3579]-?\d|snapdragon x|win(dows)? 1[01]|chrome ?os|mediatek|\bm[1-5] (pro|max|chip)?|chip m[1-5]|\bssd\b|\bemmc\b|\d+ ?gb de ram|\bcpu\b|microsoft (365|office)|ultra ?(ligero|delgado|thin)))'),
  ('Laptops', None, 'laptop')),
 # La tableta sube junto a la laptop, por la misma razón: su ficha
 # técnica la mandaba a Memoria RAM ("16GB RAM 128GB ROM", 265 casos),
 # a Celulares ("8 GB de RAM, solo wifi", 256) y al all-in-one ("panel
 # táctil todo en uno"). Lo que se vende para la tableta (funda, lápiz,
 # teclado, soporte) se aparta por el principio del título, y el panel
 # industrial y el monitor de reposacabezas por la guarda.
 (re.compile(r'^(?!(?:\S+ ){0,3}(funda|\bcase\b|protector|mica|soporte|base|lapiz|stylus|teclado|keyboard|cargador|'
             r'cable|adaptador|\bmouse\b|raton|audifono|bocina|estuche|bolsa|mochila|brazo|pantalla|cristal|vidrio|'
             r'juego de|kit de|paquete de|par de|silla|mesa|escritorio|monitor)\b)'
             r'(?!.*(funda (para|de|compatible)|\bcase (para|for)\b|protector de pantalla|mica|cristal templado|'
             r'soporte (para|de|magnetico|universal|plegable)|'
             r'lapiz optico|stylus pen|(para|con|compatible con|y) (ipad|tablet|mac)\b|para (celulares|telefonos)|'
             r'panel (industrial|pc)|todo en uno|all[- ]in[- ]one|reposacabezas|para (coche|auto|carro)|'
             r'drawing (tablet|monitor)|tableta (grafica|digitalizadora|de dibujo)|monitor tactil|tabletas? (de |para )?(purificacion|potabilizacion|cloro|limpieza|lavavajillas|efervescentes|desinfec)|purificacion de agua|tabletas? (de |para )?\w+ (de |para )?agua|pastillas))'
             r'(?!.*(power ?bank|banco de energia|bateria (externa|portatil)|audifono|auricular|earbud|'
             r'\bcable\b|cargador|hub |concentrador|\bdock\b))'
             r'(?=^(?:\S+ ){0,6}(\btablets?\b|\btabletas?\b|\bipad\b|galaxy tab\b|matepad|redmi pad|idea ?tab|'
             r'poco pad|surface pro|\bpad (\d|pro|mini|se)\b))'),
  ('Tabletas', None, 'tablet')),
 # El monitor, tercera de las tres que abren REGLAS. Sin ella la palabra
 # "monitor" caía en Accesorios de monitor y la búsqueda entera (12,691
 # anuncios) se iba ahí. Pide que el título abra con el monitor o su
 # marca, y aparta lo que solo lo menciona: el soporte, el brazo, la
 # laptop "con monitor externo", el monitor de bebé y el de signos
 # vitales, que no son pantallas de computadora.
 (re.compile(r'^(?!(?:\S+ ){0,3}(soporte|brazo|base|montaje|riser|elevador|funda|\bcase\b|protector|filtro|'
             r'cable|adaptador|divisor|\bkvm\b|barra|visera|parasol|limpiador|juego de|kit de|'
             r'paquete de|par de)\b)'
             r'(?!.*((placa|adaptador|soporte) vesa|monitor (de )?(bebe|beb|signos|presion|ritmo|glucosa|cardiaco|fetal|ambiental|'
             r'calidad del aire|temperatura|humedad|co2|energia|red|actividad)|baby monitor|videovigilancia|'
             r'reposacabezas|para (coche|auto|carro)|todo en uno|all[- ]in[- ]one|\baio\b|'
             r'monitores? (de |tipo )?estudio|monitor de audio|drawing (tablet|monitor)|tableta (grafica|digitalizadora)|(soporte|brazo|base|montaje|riser|elevador|peana) (de |para )(monitor|pantalla)|(funda|estuche|maletin|mochila|cable|adaptador|divisor|filtro de privacidad|barra de luz) (para |de )(monitor|pantalla)|bocinas? de (repisa|columna|libreria)|altavoz de (columna|repisa)|monitor audio\b))'
             r'(?=^(?:\S+ ){0,12}\bmonitor(es)?\b|^(?:\S+ ){0,4}(extensor de (pantalla|tela)|pantalla portatil|segunda pantalla)|'
             r'^(?:\S+ ){0,3}(pantalla|display) (para |de )?(pc|computadora|gamer|gaming))'
             r'(?=.*(\d{2}([.,]\d)? ?(pulgadas|\"|inch|in\b)|\bfhd\b|full hd|\bqhd\b|\buhd\b|\b[24]k\b|1920|2560|3840|'
             r'1080 ?p|1440 ?p|2160 ?p|\bhdr\b|pantalla (tactil|adicional|extra)|'
             r'\d{2,3} ?hz|\bips\b|\bva\b|\btn\b|\boled\b|curvo|\bhdmi\b|displayport|\bvga\b))'),
  ('Monitores', None, 'monitor')),
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
 # Con una captura profunda la subcategoría se llenó de lo que rodea al
 # robot: la solución de 1 l "compatible con ECOVACS Winbot", el paquete de
 # doce paños, y el jalador de goma que se llama "limpiacristales manual" y
 # no tiene motor. Los consumibles no se comparan acá y el jalador va con el
 # trapeador, en Otros; el resto de las piezas, a Refacciones.
 (re.compile(r'\blimpiacristales\b.{0,40}\b(manual|raspador|rasqueta|de goma)\b|'
             r'\b(jalador|escurridor|espatula|raspador|rasqueta) (de (goma|silicona) )?'
             r'(para )?(vidrio|cristal|ventana|mampara)'),
  ('Otros', 'Varios', 'box')),
 (re.compile(r'(?=.*(limpiacristales|limpiavidrios|winbot|hobot))'
             r'(?=.*(\bsolucion\b|\blimpiador liquido\b|detergente|'
             r'\btrapo|\bpano|toallitas?|almohadillas?|\bfiltros?\b|'
             r'\bcable de seguridad\b|bateria de repuesto|'
             r'(paquete|juego|kit|set) de \d+|\d+ unidades|'
             r'\brepuesto|\breemplazo|\baccesorios?\b))'),
  ('Refacciones', 'Refacciones para electrodomésticos', 'gear')),
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
             r'(?=.*(rizador(a)? de (pelo|cabello)|tenaza (rizadora|para rizar)|'
             r'ondulador(a)? de (pelo|cabello)))'),
  ('Aparatos de belleza', 'Rizadores', 'sparkle')),
 (re.compile(r'^(?!.*\bsecador)'
             r'(?=.*(cepillo alisador|alisador(a)? de (pelo|cabello)|'
             r'plancha.{0,30}(de pelo|de cabello|alisador)))'),
  ('Aparatos de belleza', 'Planchas para cabello', 'sparkle')),
 # La prensa de calor pide nombrarse como máquina o prensa: "Impresora ...
 # Para Planchas Sublimación", que el catálogo tiene en Impresoras, no es
 # una prensa sino la impresora que le carga el papel.
 (re.compile(r'maquina de sublimacion|prensa de calor|prensa termica'),
  ('Equipo comercial', 'Prensas de calor', 'factory')),
 # La de ropa, al final. Antes que el vaporizador porque el catálogo ya
 # resolvió así el empate: las "Plancha Vapor Vertical" están en Planchas,
 # y en Vaporizadores solo lo que se anuncia como vaporizador.
 # Antes del aparato, lo que lo acompaña: la almohadilla de planchado que
 # se cuelga, la funda de la tabla y la suela antiadherente de repuesto.
 (re.compile(r'(?=.*(plancha|planchado|vaporizador))'
             r'(?=.*(almohadilla|funda (de|para) (la )?tabla|'
             r'cubierta (de|para) (la )?tabla|suela (antiadherente|de repuesto)|'
             r'tabla de planchar\b(?!.*\bcon vaporizador\b)))'),
  ('Refacciones', 'Refacciones para electrodomésticos', 'gear')),
 (re.compile(r'\bplancha\b.{0,30}(de vapor|a vapor|de viaje|para ropa|'
             r'de ropa|vertical)|plancha vapor'),
  ('Electrodomésticos', 'Planchas', 'appliance')),
 (re.compile(r'vaporizador (de|para) ropa|vaporizador.{0,40}\bropa\b'),
  ('Electrodomésticos', 'Vaporizadores de ropa', 'appliance')),
 # Tres subcategorías que el catálogo ya tenía y a las que no llegaba
 # ninguna regla, como pasó antes con Máquinas de coser. Las campanas
 # terminaban en "Componentes y accesorios de PC" porque el título dice
 # "ventilador" y esa regla es la que lo caza; por eso van antes.
 (re.compile(r'\bcampana\b.{0,30}(extractora|de cocina|para cocina|de pared|'
             r'bajo alacena|de isla)|campana extractora|extractor de (humo|cocina)|'
             r'\bcampana\b.{0,40}\bcocina\b'),
  ('Electrodomésticos', 'Campanas de cocina', 'appliance')),
 # El calentador de agua de la casa, no el de ambiente (ese es Climatización)
 # ni el eléctrico de la regadera, que el catálogo guarda con las regaderas.
 (re.compile(r'^(?!.*(calentador (de )?(ambiente|espacios|patio|piscina|alberca)|'
             r'calefactor|hervidor|tetera|\btaza\b|para (formula|biberon|bebe)|'
             r'calientabiberones|de viaje|\bcaja\b|\bsoporte\b|termostato|'
             r'\banodo\b|\bresistencia\b|valvula de (alivio|seguridad)))'
             r'(?=.*(calentador de agua|boiler\b|calentador de paso|'
             r'calentador de deposito|calentador solar|termotanque))'),
  ('Electrodomésticos', 'Calentadores de agua', 'appliance')),
 # El horno que se empotra o se pone en la barra. La freidora de aire ya se
 # resolvió arriba, y el horno de microondas tiene su propia subcategoría.
 (re.compile(r'^(?!.*(horno (de )?microondas|freidora|air ?fryer|'
             r'horno (de secado|dental|de laboratorio|para pintura)))'
             r'(?=.*(\bhorno\b.{0,30}(electrico|de gas|empotrable|de conveccion|'
             r'tostador|de pizza|de piso|de pared)|horno de pizza|'
             r'\bhorno tostador\b|horno electrico|horno empotrable))'),
  ('Electrodomésticos', 'Hornos', 'appliance')),

 # Lavadoras antes que todo: lo que queda después de quitar fundas,
 # pastillas y refacciones es el aparato. Incluye la centrifugadora suelta,
 # que el catálogo ya trae (Koblenz SCK-60, HKPRO HK-37) sin subcategoría
 # porque su título tampoco dice "secadora".
 # Antes que la lavadora: el de encimera se anuncia como "Lavadora de
 # tazas" y el catálogo guarda 37 en su propia subcategoría. Tiene que
 # nombrarlo en las primeras palabras o con su apellido ("de encimera",
 # "de 13 cubiertos"): la palabra suelta al final es "apto para
 # lavavajillas" de otro aparato.
 (re.compile(r'^' + NO_APTO_LAVAVAJILLAS +
             r'(?:(?:\S+ ){0,5}(?:mini )?(lavavajillas|lavaplatos|lavatrastes)\b|'
             r'.*(lavavajillas|lavaplatos) (portatil|de encimera|para encimera|de mesa|'
             r'compact|integrable|empotrable|de \d+ (cubiertos|servicios)))'),
  ('Electrodomésticos', 'Lavavajillas', 'appliance')),
 # La lavadora de ropa, y solo esa. La palabra la usan tres cosas más que
 # no lavan ropa y que tienen su lugar en otra parte: la hidrolavadora
 # ("lavadora a presión", que es herramienta de jardín y ya tiene regla más
 # abajo), la lavadora de huevos y la de coches. Y la refacción -- la
 # tarjeta, la bomba de drenaje, las escobillas del motor -- que nombra la
 # lavadora para decir a cuál le queda.
 (re.compile(r'^(?!.*(a presion|hidrolavadora|\bpsi\b|\bgpm\b|de huevos|karcher|'
             r'tarjeta (para|de) lavadora|escobillas|bomba de drenaje|'
             r'(repuesto|refaccion|reemplazo|compatible con) .{0,30}lavadora|'
             r'lavadora .{0,20}(de repuesto|compatible)))'
             r'(?=.*(\blavadora|\blava\w*secadora|\bcentrifugadora))'),
  ('Lavadoras', None, 'washer')),
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
 # "Licuadoras" justamente por eso.
 (re.compile(r'extractor(a|es)? de (jugo|nutrientes)|'
             r'\bexprimidor|prensado en frio|masticacion lenta'),
  ('Electrodomésticos', 'Extractores de jugo', 'appliance')),
 (re.compile(r'\blicuadora'), ('Electrodomésticos', 'Licuadoras', 'appliance')),
 # Botellas térmicas: Amazon traduce "vacuum insulated" como "aislada al
 # aspiradora", y con eso 46 botellas de agua de una captura cayeron en
 # Aspiradoras. Va antes que Aspiradoras a propósito. "termo" solo cuando
 # no es el calentador de agua ("termo eléctrico").
 (re.compile(r'\bbotellas? (?:de|para) agua\b|aislad[ao]s? al aspirador|\bcantimplora|'
             r'\btermos?\b(?!\s*(?:electrico|el\u00e9ctrico|de agua|de gas))'),
  ('Cocina y comedor', 'Botellas y termos', 'coffee')),
 (re.compile(r'(?!.*(viaje|\btsa\b|aseo))'
             r'((estante|organizador|soporte|rack|porta ?botellas?|pinzas?|clip).{0,40}\bbotellas?\b|'
             r'\bbotellero|organizador de (cocina|especias|tapas)|porta ?vasos)'),
  ('Cocina y comedor', 'Organización de cocina', 'coffee')),
 # El resto de la cocina de mesa de esa misma captura: frascos, botellas de
 # vidrio o plástico para jugo/leche/aceite/salsas, vasos y tazas, y lo que
 # los organiza o limpia. Quedan fuera a propósito los envases de viaje/aseo
 # (no son cocina) y los de laboratorio, tinta y pegamento.
 (re.compile(r'(?!.*(viaje|\btsa\b|aseo|cosmet|champu|shampoo|reactivo|laboratorio|boticario|'
             r'cuentagotas|\btinta|pegamento|rociador|spray|atomizador|perfume|esencial|'
             r'mascota|perro|gato|biberon|bebe\b|purificador|filtro))'
             r'(botellas? (de |para )?(vidrio|plastico|pet\b|jugo|leche|aceite|salsa|condimento|'
             r'vino|licor|cerveza|kombucha|kefir|agua mineral|almacenamiento)|'
             r'botellas? (exprimibles?|hermeticas?|reutilizables?|vacias?|con tapa)|'
             r'\bfrascos? (de vidrio|hermetic|con tapa|para conserva)|'
             r'dispensador(es)? (de|para) (aceite|salsa|condimento|vinagre|jabon de cocina)|'
             r'\btarros? de vidrio|recipientes? hermetic|contenedor(es)? (de|para) (alimentos|comida)|'
             r'\btuppers?\b|tupperware|\bcaballitos? de plastico)'),
  ('Cocina y comedor', 'Contenedores', 'coffee')),
 (re.compile(r'cepillos? .{0,25}botellas?|vertedor(es)? (de|para) botellas?|abridor(es)? de botellas?|'
             r'destapador(es)?|sacacorchos|descorchador'),
  ('Cocina y comedor', 'Utensilios de cocina', 'coffee')),
 (re.compile(r'(?!.*(licuadora|batidora|aspirador|mezclador|1080p|4k|\bdvr\b|camara|wifi|espia))'
             r'(\bvasos? (termicos?|de vidrio|de acero|de cristal|para (cerveza|vino|agua|cafe|whisky))|'
             r'\btazas? (termicas?|de cafe|de ceramica|para cafe|de te)|\btermo para cafe|\btumblers?\b|'
             r'\bcopas? (de vino|de cristal|de vidrio|para vino)|\bshots? de vidrio|\bjarras? (de vidrio|de cristal|para agua))'),
  ('Cocina y comedor', 'Vasos y tazas', 'coffee')),
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
 (re.compile(r'^(?!.*(refrigerador(es)?|enfriador|ventilador) (de |para )?(telefonos?|celular|movil))'
             r'(?=.*(\brefrigerador|\bfrigobar|\bnevera\b|cava de vino|enfriador de vino))'),
  ('Refrigeradores', None, 'fridge')),
 # Purificadores de agua, después de los filtros de refrigerador: los dos
 # dicen "filtro de agua" y el del refri no purifica nada, repone una
 # pieza. La subcategoría del catálogo guarda juntos el aparato y sus
 # cartuchos (los Hydrofast HF03, los JIMMY R9), así que el kit
 # mineralizador y el filtro suelto van con los equipos de ósmosis.
 # El irrigador trae "Filtro de Agua" en el título y caía en purificadores.
 (re.compile(r'irrigador (dental|bucal|oral)|water ?flosser'),
  ('Salud y belleza', 'Cuidado dental', 'heart-pulse')),
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
 # Salvo el "Horno Microondas Air Fryer 3 en 1": ese es un microondas con
 # función de freír, y el catálogo guarda los cuatro que tiene en
 # Microondas. La guarda pide "horno microondas" y no "microondas" a secas
 # porque la Ninja Crispi dice que sus recipientes van al microondas.
 # Lo que se le pone adentro o encima a la freidora, que en una captura
 # profunda es más que las freidoras mismas: la cesta de reemplazo, la bolsa
 # de transporte de la Ninja Crispi, los forros de papel y las rejillas.
 (re.compile(r'(?=.*(freidora de aire|freidora aire|air ?fryer))'
             r'(?=.*(\bcesta\b.{0,25}(de (reemplazo|repuesto)|(for|para) freidora)|'
             r'\bbandeja\b.{0,25}(for|para) (freidora|hornear)|bolsa de transporte|'
             r'\bforros?\b|papel (para|de) horneado|moldes? de silicona|'
             r'\brejilla|accesorios? para|\brecetario\b|libro de recetas|'
             r'(reemplazo|repuesto) (de|para)\b|compatible (with|con) \w+ ?for))'),
  ('Refacciones', 'Refacciones para electrodomésticos', 'gear')),
 # La freidora de aceite se llama igual y no es lo mismo: va con los
 # pequeños electrodomésticos de cocina, donde el catálogo ya tiene las suyas.
 (re.compile(r'^(?!.*(freidora de aire|freidora aire|air ?fryer))'
             r'(?=.*(freidora (profunda|de aceite|de grasa)|freidora electrica de \d))'),
  ('Electrodomésticos', 'Pequeños electrodomésticos de cocina', 'appliance')),
 (re.compile(r'^(?!.*(horno (de )?microondas|microondas (air|con freidora)))'
             r'(?=.*(freidora de aire|freidora aire|air ?fryer|horno freidor|'
             r'freidora de \d+ cuartos|'
             r'freidora electrica.{0,60}sin aceite))'),
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
 # "Estufas" ("Parrilla Eléctrica de 24 IN 4 quemadores").
 # Antes que la parrilla de mesa, que no tiene quemadores.
 (re.compile(r'parrilla (electrica )?de induccion|estufa de induccion|'
             r'\d+ quemador|quemadores|parrilla electrica empotrable|'
             r'cocina electrica (portatil|de ceramica)|de un solo quemador'),
  ('Electrodomésticos', 'Estufas', 'appliance')),
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
 # "Batería" en español también es el instrumento, y la búsqueda de
 # baterías portátiles trae tarolas, baquetas, pedales de bombo,
 # almohadillas de entrenamiento y hasta la tarima donde se monta. Va
 # antes que todo lo demás para que "batería portátil de 12 pulgadas"
 # no acabe en power banks ni en laptops.
 (re.compile(r'^(?!.*(\d+ ?mah|power ?bank|litio|recargable de \d|celda|tilta|\bnp-|\ben-el|\blp-e|dmw-|estacion de carga|camara|\bv-mount\b))'
             r'(?=.*(bateria (electronica|acustica|musical|infantil|de practica|para principiantes)|'
             r'(juego|kit|set) de bateria|bateria de \d piezas|'
             r'\btarola\b|\bbaqueta|pedal (de|doble) bombo|pedal de bombo|platillos?( de| para)? (bateria|charles|hi-?hat)|'
             r'(almohadillas?|pad(s)?) de (entrenamiento|practica).{0,20}bateria|banco (de|para) bateria|'
             r'(asiento|trono) (de|para) bateria|(anillos?|amortiguador(es)?) silenciador(es)? .{0,20}(bateria|tarola)|'
             r'afinador de (bateria|tarola)|parche (de|para) (tarola|bombo|tom)|'
             r'plataforma (portatil )?para bateria))'),
  ('Instrumentos musicales', 'Baterías', 'mic')),
 # La batería de bicicleta eléctrica y la de patinete: son refacciones,
 # no power banks, aunque digan "batería de litio portátil".
 (re.compile(r'^(?!.*(power ?bank|banco de energia))'
             r'(?=.*((bateria|celda).{0,60}(bicicleta electrica|e-?bike|ebike|triciclo electrico)|'
             r'(bicicleta electrica|e-?bike|ebike).{0,40}bateria|'
             r'bateria .{0,40}(portaequipaje|montaje en rack|rack trasero|anderson)))'),
  ('Refacciones', 'Para bicicletas eléctricas', 'gear')),
 # Primero la batería de cámara, que no es ninguno de los otros dos: las
 # ocho estaciones de carga Tilta y el hub del X3 cargan celdas NP-FZ100,
 # LP-E6 y DMW-BLK22, y el catálogo guarda esas piezas en Accesorios de
 # cámaras. Tilta, además, solo fabrica accesorios de cámara: su brazo
 # articulado entra por la marca.
 (re.compile(r'^(?!.*(power ?bank|\b([5-9]\d{3}|\d{5,}) ?mah|\d{2},\d{3} ?mah))'
             r'(?=.*(\btilta\b|np-?fz100|lp-?e6|dmw-?blk|bateria (para|de) camara|'
             r'hub de cargador de bateria|\ben-el\d|\bnp-(f\d|fw|bx|fm)|\blp-e\d|\bnb-\d+l|\bdmw-bl|\bblx-?1|\bbln-?1|\bbls-?5|'
             r'(bateria|cargador)s?.{0,40}(nikon|canon|sony (alpha|np-)|fujifilm|olympus|gopro|insta360|smallrig)|'
             r'cargador de baterias? (para|de) camaras?))'),
  ('Cámaras y fotografía', 'Accesorios', 'camera')),
 (re.compile(r'^(?!.*(estacion de energia|power station|osmo|pocket))(?=.*((cargador|bateria)s?.{0,40}(\bdji\b|\bdrones?\b|\bdron\b|mavic|phantom \d|avata)|'
             r'(\bdji\b|\bdrones?\b|\bdron\b|mavic).{0,40}(cargador|bateria)))'),
  ('Drones', 'Accesorios', 'drone')),
 # Después la estación de energía, que es el aparato con toma de corriente
 # de 110 V: la DJI Power 1000, la EcoFlow DELTA 3 y las DaranEner. El
 # catálogo tiene la subcategoría desde hace tiempo.
 (re.compile(r'estacion de energia|estacion electrica|generador solar|central electrica portatil|'
             r'\bpower station\b'),
  ('Otros', 'Estaciones de energía', 'battery')),
 # Y al final la batería portátil, que sube hasta aquí desde el final de
 # REGLAS. Tenía que adelantarse: la MARBERO y la MR. GADGETS se anuncian
 # como "fuente de alimentación" y se iban con las fuentes de poder de PC,
 # y cinco power banks "para MacBook Pro" se iban a Laptops. Junto a "power
 # bank" van las cinco maneras de decir lo mismo que trae la captura:
 # batería externa, magnética, inalámbrica, MagSafe y powerstation.
 (re.compile(r'^(?!.*(bocina|barra de sonido|soundbar|altavo|\bev\b|nivel [12]|vehiculo|'
             r'carrito|golf|encendedor|lir\d|celda de boton|^(?!.*mah).*panel solar|celula solar|celda solar|almohadilla|'
             r'\bdiy\b|caja (de|para) (bateria|banco de energia|powerbank|pilas)|soporte de bateria|sin celdas|'
             r'probador|comprobador|medidor de (voltaje|bateria)|analizador|cortacesped|pulverizador|nebulizador|'
             r'tijeras|silla (de )?ruedas|\d{2} ?v ?max|stanley|dewalt|makita|milwaukee|ryobi))'
             r'(?=.*(power ?bank|powerbank|bateria portatil|banco de energia|'
             r'cargador(es)? portatil(?!.{0,80}(legion|thinkpad|inspiron|pavilion|ideapad|vivobook|zenbook|latitude|omen|precision \d|aspire|elitebook|probook|chromebook|macbook|laptop|notebook|reloj|\bwatch\b|auto electrico|tipo 2))|'
             r'bateria externa|power ?station|'
             r'bateria (magnetica|inalambrica|magsafe)|\d+ ?mah bateria|'
             r'cargador inalambrico portatil))'),
  ('Baterías portátiles', None, 'battery')),
 # El cargador de pared y el cable, que la captura trae sueltos y hasta hoy
 # no tenían regla: el pack GAN de 140 W de DJI, el CUKTECH de 65 W, el
 # cubo de 20 W y el cable Lightning de UGREEN.
 # El celular, cuando el título es solo marca y modelo. Pide abrir con la
 # marca y descarta de una vez los Buds, los Watch y las Tab, que empiezan
 # igual y no son teléfonos.
 (re.compile(r'^(samsung (galaxy )?(note ?\d{1,2}\b|[asmzf]\d{1,2}\b)|apple iphone|iphone \d+|galaxy (z fold|z flip|[asmz]\d{1,2}\b)|'
             r'motorola (edge|moto|razr|g\d+)|moto (edge|g|e|razr)\b|one ?plus (\d+|nord|open)|'
             r'huawei (nova|mate|pura|p\d+)|honor (magic|x\d+|\d+|play)|xiaomi (\d+|redmi|poco|mi \d+)|'
             r'redmi (note|\d+|a\d+)|poco [cfmx]\d+|realme (\d+|c\d+|gt|narzo|note)|oppo (a\d+|reno|find)|'
             r'vivo ([vyx]\d+)|zte (blade|axon|nubia)|nubia|tecno (spark|camon|pova|phantom)|'
             r'infinix (hot|note|smart|zero|gt)|nokia [cg]\d+|google pixel|pixel \d+|bmobile|lanix (ilium|alpha|x\d+)|'
             r'blu ([a-z]\d+|joy|studio|view)|sony xperia|nothing phone|cmf phone|alcatel \d+|tcl \d0)'
             r'(?!.*\b(buds|watch|tab|book|fit|ring|band|pad|tv|choice)\b)'
             r'(?!.*(bateria|power ?bank|cargador|cable|funda|\bcase\b|carcasa|protector|mica|soporte|correa|'
             r'repuesto|display|pantalla lcd|lente|vidrio|cristal|adaptador|auricular|audifono))'),
  ('Celulares', None, 'phone')),
 # El celular con la ficha técnica en el título (RAM y ROM, "8GB+256GB",
 # "teléfono inteligente resistente", "botones grandes para adultos
 # mayores"): la señal es tan fuerte que no importa que después mencione
 # el altavoz, el proyector, la mica o la microSD que trae de regalo. Va
 # antes que las bocinas, los proyectores y los audífonos por eso mismo;
 # solo se aparta si el título abre con el accesorio o nombra otro aparato
 # que también se vende por gigas (laptop, tablet, mini PC, TV box).
 (re.compile(r'^(?!(?:\S+ ){0,2}(funda|mica|protector|\bcase\b|carcasa|cargador|cable|bateria|pila|soporte|'
             r'tripie|tripode|lente|kit de|audifonos|auriculares|bocina|altavoz|teclado|\bmouse\b|monitor|proyector|camara|'
             r'estuche|bolsa|brazalete|correa|adaptador|memoria|tarjeta)\b)'
             r'(?!.*((funda|mica|protector|carcasa|cristal templado|vidrio templado) (para|compatible|de|transparente|rigid|antigolpes|silicona)|'
             r'car ?radio|carplay|android auto|doble din|2 ?din|autoestereo|estereo (para|de) (coche|auto|carro)|bicicleta|triciclo|motocicleta|casillero|persiana|cortina|de repuesto|refaccion|reemplazo|laptop|notebook|macbook|'
             r'chromebook|mini pc|\bpc\b|\btablet\b|tableta|\bipad\b|\bpad\b|router|modem|consola|\bretro\b|'
             r'\btv\b|television|\bssd\b|memoria usb|\bwatch\b|smartwatch|reloj|camara (de seguridad|ip|web)|'
             r'\bdron\b|estereo|\bdin\b|carplay|android auto|para (auto|coche|carro)|pantalla (lcd|amoled|oled).{0,30}(repuesto|reemplazo|reparacion)))'
             r'(?=.*(\d+ ?gb (de )?ram|\bram\b.{0,15}\brom\b|\brom\b.{0,15}\bram\b|\d+ ?gb ?\+ ?\d+ ?gb|'
             r'\d+ ?\+ ?\d+ ?gb\b|\d+ ?gb ?[/_] ?\d+ ?gb|\d+ ?gb, ?\d+ ?gb\b|dual sim|\bandroid \d+(\.\d+)?\b|'
             r'\b(4|6|8|12|16|24) ?\+ ?(64|128|256|512|1024)\b|desbloqueado de fabrica|(celular|telefono|smartphone|movil) (android )?(desbloqueado|senior)|'
             r'a prueba de golpes.{0,60}(mil-std|ip6[89])|(mil-std|ip6[89]).{0,60}a prueba de golpes|'
             r'(celular|telefono|smartphone|movil) (robusto|resistente|inteligente|basico|de tapa|con tapa)|'
             r'telefono inteligente|smartphone|(personas|adultos) mayores|botones? grandes?|boton sos|\bsenior\b|'
             r'\b(flip|cell|feature) ?phone\b|telefono (celular|movil) (2g|3g|4g|desbloqueado)))'),
  ('Celulares', None, 'phone')),
 # La búsqueda de "cargador" trae de todo lo que se carga. Lo que tiene
 # cajón fuera de Cargadores va primero: la batería de auto y su
 # cargador/arrancador, la batería y el cargador de herramienta
 # eléctrica, el cargador del patinete y de la bicicleta eléctrica, y el
 # eliminador de repuesto de una afeitadora o una caminadora.
 (re.compile(r'cargador (de |para )?bater[ií]as? (de |para )?(auto|coche|carro|moto|automovil|12 ?v|6/12 ?v|12/24 ?v)|'
             r'\bmantenedor\b|battery tender|arrancador|jump starter|booster de bateria|'
             r'cargador (de |para )?bater[ií]as?.{0,40}(6/12 ?v|12 ?v|amperimetro|pinzas)'),
  ('Autos, bicicletas y motos', 'Baterías para auto', 'car')),
 (re.compile(r'^(?!.*(lavadora a presion|hidrolavadora|soplador|motosierra|podadora|cortacesped|desbrozadora|tijeras de podar|pulverizador|aspiradora))'
             r'(?=.*(\b(dewalt|makita|milwaukee|ryobi|ridgid|craftsman|worx|einhell|greenworks|metabo|hilti|kobalt|porter-?cable|skil)\b.{0,60}(bateria|cargador)|'
             r'(bateria|cargador).{0,60}\b(dewalt|makita|milwaukee|ryobi|ridgid|craftsman|worx|einhell|greenworks|metabo|hilti|kobalt|skil)\b|'
             r'bosch (gxs|gba|gal|gaa)|black ?(\+|&|and|y) ?decker.{0,40}(bateria|cargador)|driver de impacto|taladro (inalambrico|percutor|atornillador|electrico)|bateria (para|de) taladro|'
             r'herramientas? (inalambrica|electrica)|\b(18|20|40) ?v (max|xr|lxt|onepwr|power ?share)|\bm18\b|\blxt\b|'
             r'kit de (inicio|arranque).{0,30}bateria|bateria (portatil |de repuesto )?(de |para )?\d{2} ?v ?(max|ion de litio)|\b\d{2} ?v max\b|\b(stanley|dewalt|makita|milwaukee|ryobi|ridgid|craftsman|worx|einhell|greenworks|metabo|hilti|kobalt|skil|bauer|hart)\b.{0,40}\b\d+[.,]?\d* ?a(h)?\b))'),
  ('Herramientas', 'Accesorios para herramientas eléctricas', 'wrench')),
 (re.compile(r'(cargador|bateria).{0,60}(patinete|scooter|hoverboard|kukirin|segway|ninebot)|(patinete|scooter|hoverboard).{0,60}(cargador|bateria)'),
  ('Refacciones', 'Para patinetas eléctricas', 'gear')),
 (re.compile(r'(cargador|bateria).{0,60}(bicicleta electrica|e-?bike|ebike)|(bicicleta electrica|e-?bike|ebike).{0,60}(cargador|bateria)'),
  ('Refacciones', 'Para bicicletas eléctricas', 'gear')),
 (re.compile(r'(cargador|adaptador|fuente de alimentacion|eliminador).{0,60}(para|compatible con|de) .{0,40}(afeitadora|norelco|one ?blade|masaje|masajeador|'
             r'caminadora|eliptica|rowing|\bremo\b|nordictrack|peloton|bicicleta estatica|humidificador|purificador|maquina de coser|licuadora|mosquito|walkie|resmed|cpap|'
             r'\bbose\b|sonos|\bjbl\b|\bbeats\b|barra de sonido|altavoz|bocina|concentrador de oxigeno|inogen)'),
  ('Refacciones', 'Refacciones para electrodomésticos', 'gear')),
 # Y los cargadores de consumo, por subcategoría del catálogo: el de auto
 # (encendedor), el de pilas AA, el de laptop (punta o marca de laptop en
 # el título), el de pared (USB, tipo C, GaN, watts), el inalámbrico, la
 # base o estación de carga, el adaptador de corriente de un aparato y el
 # cable. Lo que dice "cargador" y no cae en ninguno queda en Otros, al
 # final de REGLAS.
 (re.compile(r'cargador(es)? (de|para) (el )?(coche|auto|carro|automovil|vehiculo)|cargador vehicular|car charger|'
             r'encendedor de cigarrillos|divisor de enchufe para encendedor|pared/auto|pared y auto|'
             r'cargador(es)?.{0,30}\b(auto|coche|carro)\b'),
  ('Cargadores y adaptadores', 'De auto', 'plug')),
 (re.compile(r'cargador (de |para )?(pilas|baterias) (aa|aaa|recargables|nimh|18650|9 ?v|de boton|lir|cr)|cargador de pilas|'
             r'cargador universal de pilas|\b(aa|aaa)\b.{0,40}cargador|\b18650\b|cargador .{0,20}\b(aa|aaa)\b|'
             r'(baterias?|pilas?) recargables? (aa|aaa|c|d)\b.{0,40}cargador|cargador .{0,60}(baterias?|pilas?) recargables?\b|pilas recargables (aa|aaa)'),
  ('Cargadores y adaptadores', 'De pilas', 'plug')),
 (re.compile(r'^(?!.*(celular|telefono|smartphone).{0,30}(\d+ ?gb|dual sim))'
             r'(?!.*(\bmouse\b|raton|teclado|audifono|auricular|\breloj\b|smartwatch|bocina|altavoz).*(cargador|carga inalambrica|base de carga))'
             r'(?=.*(cargador inalambrico|carga inalambrica|\bqi2?\b|magsafe.{0,20}cargador|cargador (rapido )?magsafe|wireless charger|almohadilla de carga|cargador magnetico|'
             r'cargador magnetico (para|iphone|3 en 1|2 en 1)|estacion de carga (inalambrica|magnetica)))'),
  ('Cargadores y adaptadores', 'Inalámbrico', 'plug')),
 (re.compile(r'^(?!.*(casillero|armario|gabinete|cerradura|\d{2,} (puertos|ranuras)|\bgan\b|\d{3} ?w\b|\d puertos|multipuerto|\bev\b|\d+ ?kw|\bmouse\b|raton|teclado|audifono|auricular|reloj|watch|bocina|altavoz|aspiradora|robot|camara|dron|control|mando|consola))'
             r'(?=.*(base de carga|estacion de carga|dock de carga|soporte de carga|charging (dock|station|stand)|cargador de escritorio|base cargadora))'),
  ('Cargadores y adaptadores', 'Base de carga', 'plug')),
 (re.compile(r'^(?!.*(iphone|samsung|celular|telefono|smartphone|airpods|ipad|tablet|\bgan\b|multipuerto|\d puertos))'
             r'(?=.*((cargador|adaptador).{0,80}(laptop|portatil(es)?|notebook|macbook|chromebook|\bdell\b|\bhp\b|lenovo|\basus\b|\bacer\b|\bmsi\b|'
             r'thinkpad|inspiron|pavilion|ideapad|vivobook|zenbook|latitude|omen|legion|surface|razer|alienware|gigabyte|precision \d|\bxps\b|'
             r'elitebook|probook|aspire|nitro|predator)|(adaptador|cargador) de (ca|corriente|alimentacion).{0,60}(laptop|portatil|notebook)|'
             r'punta \(?(de )?\d|punta (cuadrada|delgada|redonda)|'
             r'(\bdell\b|\bhp\b|lenovo|\basus\b|\bacer\b|\bmsi\b|inspiron|thinkpad|surface|\brog\b|strix|\btuf\b).{0,60}(cargador|adaptador|\bpsu\b)))'),
  ('Cargadores y adaptadores', 'Para laptop', 'plug')),
 (re.compile(r'^(?!.*(wireless|inalambric|\bqi\b|magsafe|solar|pilas|reloj|watch|soporte|elevador|brazo|enfriador|ventilador))'
             r'(?=.*(cargador(es)? (de pared|de corriente|de casa|usb|tipo c|usb ?c|rapido|carga rapida|multisalida|dual|doble|de \d+ ?w|'
             r'original|con cable|combo|de viaje|de red|electrico)|\bcharger\b|'
             r'cargador(es)? (para|compatible con) (iphone|samsung|celular|telefono|smartphone|android|ipad|tablet|apple|xiaomi|motorola|huawei|oppo|honor)|'
             r'\d+ ?w (usb-?c |tipo c |rapido )?(charger|cargador)|'
             r'cargador.{0,25}\bgan\b|\bgan\b.{0,25}cargador|'
             r'cargador (usb ?c |tipo c )?\d+ ?w\b|cubo de carga|carga rapida cubo|bloque de carga|'
             r'pack de carga|kit de cargador|quick charge|power delivery|\bqc ?3|multicontacto|power adapter|bloque de carga(dor)?|adaptador(es)? de carga( rapida)?.{0,20}puertos|'
             r'estacion de carga.{0,40}(\d puertos|usb|\bgan\b|\d+ ?w\b)|carga-dor|'
             r'adaptador de (corriente|carga) (usb|pd|de \d+ ?w|tipo c|usb-?c)|adaptador de corriente.{0,20}\d+ ?w\b|'
             r'cargador.{0,30}(puertos?|salidas)|cargador.{0,30}\d+ ?(w|a)\b.{0,30}(usb|tipo c|puerto)))'),
  ('Cargadores y adaptadores', 'De pared', 'plug')),
 (re.compile(r'^(?!.*(ventilador|\bpwm\b|argb|\brgb\b|gabinete))(?:\S+ ){0,3}cable (alargador|usb|lightning|tipo c|usb-?c|de carga|cargador|magnetico|trenzado|convertidor|de impresora|divisor|auxiliar|micro ?usb|hdmi|de datos|de nailon|de nylon)|'
             r'lightning cable|cable mfi'),
  ('Cargadores y adaptadores', 'Cable', 'plug')),
 # La impresora 3D y la terminal de cobro, una de cada una en la captura y
 # las dos con su lugar hecho en el catálogo.
 (re.compile(r'impresora 3d'), ('Impresión 3D', 'Impresoras', 'printer')),
 (re.compile(r'terminal para tarjetas|mercado pago point|punto de venta'),
  ('Equipo comercial', 'Punto de venta', 'factory')),
 # El soporte de celular no es el celular: el catálogo lo tiene en Varios.
 # El ventilador que se pega atrás para jugar ("Refrigeradores de
 # teléfonos móviles") va al mismo cajón, antes que los refrigeradores.
 (re.compile(r'^(?!.*(altavoz|bocina|speaker|parlante|lampara|cargador inalambrico|power ?bank|laptop|computadora|macbook|monitor))'
             r'(?=.*(soportes? (magnetico |universal |plegable |retractil |de |para )*(el )?(telefono|celular|movil|smartphone|iphone)|'
             r'soportes?.{0,60}(para |de |y )(el |tu |varios |multiples )?(telefono|celular|movil|smartphone|iphone|tablet|ipad)|'
             r'montaje de telefono|base para celular|tripie (para|de) (el )?(celular|telefono|movil|smartphone)|'
             r'tripode.{0,30}(celular|telefono|movil|selfie)|palo (de )?selfie|'
             r'anillo (soporte|magnetico)|porta ?celular|auricular (de telefono )?retro|telefono retro con bluetooth|'
             r'(refrigerador(es)?|enfriador|ventilador) (de |para )?(telefonos?|celular(es)?|moviles?)\b))'),
  ('Otros', 'Varios', 'box')),
 (re.compile(r'panel(es)? solar'), ('Otros', 'Paneles solares', 'battery')),
 (re.compile(r'^(?!.*(80 ?plus|\batx\b|\bsfx\b|modular|gabinete|\bpc\b|gamer))'
             r'(?=.*(adaptador de corriente|eliminador|adaptador (de )?(ca|ac)\b|adaptador ac/dc|fuente de (alimentacion|poder).{0,30}\d+ ?v\b|cable de alimentacion.{0,30}\d+ ?v\b|adaptador de cargador))'),
  ('Cargadores y adaptadores', 'Adaptador de corriente', 'plug')),
 (re.compile(r'adaptador(es)? (otg|tipo c|usb-?c|usb|de viaje|universal)|convertidor .{0,20}otg|cable otg'),
  ('Cargadores y adaptadores', 'Otros', 'plug')),
 (re.compile(r'computadora escritorio (completa|amd|intel)|pc gamer factor'),
  ('Computadoras de escritorio', 'Torre', 'desktop')),
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
 # Los videojuegos dejan pasar al teclado y al mouse: el HyperX Alloy Core
 # y los dos ratones Corsair listan "PS5" y "Xbox" entre lo que aceptan, y
 # con eso se iban a Accesorios de videojuegos. Un título que dice "teclado"
 # o "mouse" es un teclado o un mouse, conecte donde conecte, y los dos
 # tienen su regla al final de REGLAS.
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
 # sino en "Bocinas para auto" (cincuenta y cinco fichas contra
 # ninguna), y se reconocen por cómo se venden -- coaxiales, de 6x9, de dos
 # o tres vías, de rango medio, o diciendo "para auto".
 # El cable de altavoz y el driver suelto no son la bocina: uno es cable
 # y el otro la pieza que va dentro de una caja que hay que construir.
 (re.compile(r'^(?:\S+ ){0,3}cables? (de |para )?(altavo|bocina|parlante|speaker)|cable speakon|'
             r'(altavo(z|ces)|bocinas?) internos? (de repuesto|izquierd|derech)|'
             r'(altavo(z|ces)|bocinas?) de repuesto (para|compatible)'),
  ('Cargadores y adaptadores', 'Cable', 'plug')),
 (re.compile(r'\bcoaxial|\b6 ?x ?9\b|(rango medio|medio rango)|'
             r'(bocinas?|altavo(z|ces)|parlantes?|tweeters?|woofers?) (para|de) (auto|coche|carro|automovil|vehiculo)|'
             r'autoestereo|car audio|\bdoor speakers?\b|^(?:\S+ ){0,4}(altavoz de agudos|\btweeters?\b|super bullet)|'
             r'altavo(z|ces) (de )?componentes?|bocinas? (de )?componentes?|\bcomponent speakers?\b'),
  ('Autos, bicicletas y motos', 'Bocinas para auto', 'speaker')),
 # La bocina, con las cuatro maneras de nombrarla que usa esta captura:
 # "bocina", "bafle", "altavoz/altavoces" y la máquina de cantar karaoke,
 # que el catálogo ya tiene entre las bocinas.
 (re.compile(r'\becho (pop|dot|show|studio|hub)\b|\balexa\b|google nest|'
             r'\bnest (audio|mini|hub)\b|bocina intelig|altavoz intelig'),
  ('Domótica y hogar inteligente', 'Bocinas inteligentes', 'speaker')),
 (re.compile(r'cerradura (inteligente|electronica|digital|biometrica)|smart lock'),
  ('Domótica y hogar inteligente', 'Cerraduras inteligentes', 'lock')),
 # Solo la almohada de cama: la de viaje va en Maletas y la de bebé en
 # Bebés, y las dos se llaman almohada.
 (re.compile(r'^(?!.*(viaje|cuello|cervical|masaj|bebe|lactancia|embarazo|inflable))'
             r'(?:\S+ ){0,3}almohadas?\b'),
  ('Blancos y ropa de cama', 'Almohadas', 'pillow')),
 (re.compile(r'^(?!(?:\S+ ){0,2}(cables? (auxiliar|usb|micro|divisor|de carga|tipo c|hdmi)|cargador|estante|antena|banda|soporte|funda)\b)'
             r'(?=.*(bocina|bafle|altavo(z|ces)|maquina de cantar|\bspeaker\b|'
             r'monitores? (de |tipo )?estudio))'),
  ('Bocinas', None, 'speaker')),
 # Audífonos: "audífonos" es la palabra del catálogo, pero media captura
 # dice "auriculares", y las marcas grandes venden "Buds" y "headphones"
 # sin traducir. "Diadema" sola no basta -- también es una vincha -- así
 # que pide cable, micrófono o inalámbrico al lado.
 (re.compile(r'^(?!(?:\S+ ){0,3}(soporte|cables? (auxiliar|usb|micro|divisor|de carga|tipo c|hdmi)|estante|gafas|lentes|'
             r'mesa|escritorio|silla|mueble|organizador|gancho|percha|almohadilla|espuma|repuesto|puntas?|'
             r'adaptador|estuche|funda|bolsa)\b)'
             r'(?!.*(gancho para (auriculares|audifonos)|puntas? para (audifonos|auriculares)|'
             r'almohadillas? (de repuesto )?para (audifonos|auriculares)|espuma de repuesto))'
             r'(?=.*(audifonos|auriculares|\bearbuds?\b|\bbuds\b|headphones|'
             r'\bin[- ]?ear\b|monitoreo in[- ]?ear|'
             r'\bdiadema\b.{0,30}(cable|microfono|inalambric)))'),
  ('Audífonos', None, 'headphones')),
 # Videojuegos va DESPUÉS de monitores, bocinas y audífonos a propósito. El
 # accesorio gamer nombra la consola para decir con qué anda ("Razer Kraken
 # para PS5", "monitor gamer compatible con Xbox"), así que si esta regla
 # corriera antes se los llevaría a todos. Y al revés: sacarlos de acá con una
 # guarda los perdía, porque su propia regla tampoco los enganchaba y caían en
 # "no encaja". El orden resuelve las dos cosas -- cada categoría se queda con
 # lo suyo, y lo que ninguna reclama sigue teniendo a Videojuegos de red.
 (re.compile(r'^(?!.*(teclado gamer|\bmouse\b|\braton\b|\bmonitor\b|\bsilla\b|'
             r'escritorio|smart tv|televisor|\bproyector|\bimpresora))'
             r'(?=.*(nintendo switch|switch ?2|switch oled|switch lite|'
             r'playstation ?[345]|\bps[345]\b|playstation portal|'
             r'xbox series [xs]|xbox one|xbox 360|\bxbox\b|'
             r'steam ?deck|rog ally|legion go|msi claw|\bwii u\b|\bwii\b|'
             r'nintendo 3ds|\bpsp\b|ps vita|game ?boy|consola de juegos|'
             r'freno de mano|handbrake|mando bdm|gun grip|'
             r'juego de interruptor|interruptor ns|base portatil ns))'), VJ),
 # El micrófono suelto es de la sección de instrumentos, que es donde el
 # catálogo guarda los doce de solapa y los inalámbricos.
 (re.compile(r'microfono (inalambrico|de solapa|condensador|lavalier)|'
             r'kit de microfono'),
  ('Instrumentos musicales', 'Micrófonos', 'mic')),
 # Accesorios de monitor: el brazo, la base, el soporte VESA, la barra de
 # luz y el filtro de privacidad. Antes bastaba con que el título dijera
 # "monitor", y por eso la búsqueda de monitores metía 7,562 monitores
 # de verdad en accesorios. Ahora hay que nombrar el accesorio.
 (re.compile(r'(brazo|soporte|base|montaje|riser|elevador|peana|adaptador vesa|placa vesa)\b.{0,40}(monitor|pantalla)|'
             r'(?<!de )monitor(es)? (con|para) (brazo|soporte|base|montaje|riser|elevador|peana)\b|'
             r'(barra de luz|luz de pantalla|screen ?bar|filtro de privacidad|protector de pantalla|'
             r'visera|parasol|limpiador de pantalla|calibrador de color)\b.{0,40}(monitor|pantalla)|'
             r'\bvesa\b|kvm\b|divisor (hdmi|displayport|dp)|cable (hdmi|displayport|dvi|vga)'),
  (PC, 'Accesorios de monitor', 'cpu')),
 # Muebles: el escritorio sobre el que va la computadora, no la computadora.
 # Solo si la palabra abre el título: "RAM de escritorio" y "PC de escritorio"
 # la usan como adjetivo.
 (re.compile(r'(?!.*\bmouse\b)(alfombrilla|tapete) (de|para) (computadora|escritorio|teclado)|\bdesk ?(mat|pad)\b'),
  (PC, 'Accesorios', 'mouse')),
 # Lo que NO es el mueble aunque lo nombre: la rueda de repuesto de la silla,
 # el pasacables del escritorio, la funda del sofá.
 (re.compile(r'\b(ruedas? (giratorias?|de repuesto|para)|rodaja|garruch|'
             r'organizador de cables|pasacables|\bojal\b|'
             r'tornillo|tuerca|perno|herraje|bisagra|riel(es)? de cajon|'
             r'(funda|forro|cubierta|protector) (para|de) (sofa|sillon|silla|colchon|mesa)|'
             r'pata(s)? de (repuesto|mesa|silla)|kit de (montaje|reparacion))\b'
             r'(?=.*(silla|sofa|sillon|escritorio|mesa|cama|colchon))'),
  ('Refacciones', 'Otros', 'gear')),
 # Después de webcams y soportes: "para iMac" es un soporte, "Intel NUC" es
 # una placa VESA y el sistema Yealink es "todo en uno" pero es una cámara.
 (re.compile(r'^(?!.*(sodimm|udimm|modulo de memoria|adaptador|cargador|fuente|red electrica))(?=.*(all[- ]in[- ]one|\baio desktop|todo en uno|\bimac\b|omnistudio|proone|'
             r'panel industrial))'),
  ('Computadoras de escritorio', 'All in One', 'desktop')),
 # Lo que se le cuelga a un mini PC va antes que el mini PC: soportes de
 # escritorio/VESA y la base dock del Mac mini son periféricos.
 (re.compile(r'^(?:\S+ ){0,2}(mini-?soporte|soporte)\b.*(mini pc|mac[- ]mini|miniordenador)|'
             r'soporte vesa|dock station|estacion de acoplamiento|docking'), PERI),
 (re.compile(r'mini pc|mac mini|mini ordenador|thinkcentre tiny|micro pc'),
  ('Computadoras de escritorio', 'Mini PC', 'desktop')),
 # La RAM va después de las computadoras completas: un mini PC "16GB DDR4"
 # no es un módulo de memoria.
 # La tableta y el celular van antes que la memoria RAM: "8GB RAM + 256GB"
 # es como se vende un teléfono, y "Xiaomi Redmi 9C 64GB 3GB RAM" caía en
 # módulos de memoria. La tableta primero, porque "iPad desbloqueado" y
 # "Galaxy Tab" cumplen las señas del celular.
 (re.compile(r'^(?!.*(funda|\bcase\b|protector|mica|cristal templado|soporte (para|de|magnetico|universal|plegable)|'
             r'^(?:\S+ ){0,2}cargador\b|cargador (de pared|inalambrico|portatil|de auto|solar|para (celular|telefono|iphone))|'
             r'^(?:\S+ ){0,2}cable\b|casillero|armario|gabinete|caja|estacion de carga|persiana|cortina|'
             r'bateria (de repuesto|interna|para)|lapiz|stylus pen|tarjeta sim|\btablet\b|\bipad\b|matepad|'
             r'smart ?watch|\bwatch\b|reloj|buds\b|audifono|auricular|airpods|tripie|tripode|control remoto|'
             r'\blente\b|filtro|adaptador|memoria usb|tf card|microsd|\bssd\b|kit de|repuesto|'
             r'pantalla (lcd|amoled|oled).{0,30}(repuesto|reemplazo|reparacion)|display|'
             r'refaccion|\btv\b|television|smart tv|qled|\buhd\b|roku|monitor|laptop|notebook|macbook|imac|\bbook\b|'
             r'proyector|bocina|altavoz|camara de seguridad|scooter|patinete|aspiradora|robot|\bband\b|\bfit\b|'
             r'\bring\b|router|modem|consola|\bmouse\b|\bpc\b|escritorio|impresora|refrigerador|lavadora|'
             r'secadora|microondas|estufa|horno|nest\b|chromecast|toallitas|brazalete|cordon|correa|soporte|'
             r'\bddr[345]\b|sodimm|\budimm\b|\brdimm\b|\bdimm\b|pc[34]-\d|modulo de memoria|memoria dram|''magic keyboard|teclado (para|magic|inalambrico|mecanico|bluetooth|touchpad|plegable|retroiluminado|numerico)|teclado y (raton|mouse)|\bmouse\b|\braton\b|combinacion de raton|core ultra|\bi[3579]-\d{4}|ryzen [3579]\b|\btssd\b|sobremesa|torre desktop|digital piano|cascos? over-?ear|driver de camara))'
             r'(?=.*(\bcelular(es)?\b|smartphone|\bsmart ?phone\b|'
             r'telefono (inteligente|celular|movil|desbloqueado|resistente|robusto|android)|'
             r'telefonos inteligentes|movil inteligente|dual sim|dual nano|desbloqueado|liberado|'
             r'\d+ ?gb ram|\d+ ?gb ?\+ ?\d+ ?gb|\d+ ?\+ ?\d+ ?gb|\bram\b.{0,15}\brom\b|'
             r'\b(flip|smart|cell|feature) ?phone\b|'
             r'(samsung galaxy|galaxy [asmzf]\d|xiaomi|redmi|\bpoco\b|motorola|\bmoto ?[ge]\d|'
             r'\boppo\b|\bvivo\b|realme|\bhonor\b|huawei|\bzte\b|nokia|\btcl\b|oneplus|infinix|tecno|'
             r'google pixel|pixel \d|iphone|nubia|alcatel|lanix|bmobile|blackview|doogee|ulefone|'
             r'oukitel|cubot|umidigi|fossibot|kyocera|cat phones|crosscall|\bblu\b|hotwav|\bagm\b|'
             r'nothing phone|xperia|blackberry|\bhtc\b)'
             r'.{0,60}\b(5g|4g|lte|\d+ ?gb|android|desbloqueado|liberado|nacional|negro|azul|blanco|gris|verde|'
             r'rosa|morado|dorado|plata|rojo|amarillo|naranja|edge \d|nova \d|magic ?\d|reno ?\d|note ?\d|'
             r'redmi \d|poco [cfmx]\d|pixel \d|xperia|axon|blade|nord|find x|\ba\d{2}\b|\bs\d{2}\b)\b))'),
  ('Celulares', None, 'phone')),
 (re.compile(r'^(?!.*(correa|funda|protector|cargador|cable|smartphone \+|\+ (reloj|smartwatch)|mica))'
             r'(?=.*(smart ?watch|reloj inteligente|galaxy watch|apple watch|\bwatch (s|gt|fit)\d?\b))'),
  ('Relojes inteligentes', 'Smartwatches', 'watch')),
 # El ventilador y el calentador de batería no son componentes de PC: el
 # catálogo los tiene en Climatización desde que entraron los de torre.
 (re.compile(r'^(?!.*(\bcpu\b|procesador|gabinete|\bpc\b|\bitx\b|socket|disipador|radiador|argb|\bpwm\b|chasis))'
             r'(?=.*(ventilador(es)? (portatil|de mano|recargable|de camping|de cuello|de piso|de mesa|de torre|nebuliza|de carriola)|'
             r'mini ventilador|ventilador.{0,30}(bateria|\d+ ?mah)|abanico (portatil|recargable|de mano)))'),
  ('Climatización', 'Ventiladores', 'snowflake')),
 (re.compile(r'^(?!.*(\bcpu\b|procesador|\bpc\b|gabinete|para auto|desempanador))'
             r'(?=.*(calefactor|calentador de ambiente|estufa electrica portatil))'),
  ('Climatización', 'Calefactores', 'snowflake')),
 # La hidrolavadora a batería y la sopladora: herramienta de jardín, no
 # lavadora de ropa ni electrodoméstico de cocina.
 (re.compile(r'^(?!.*(ropa|prendas|lavadora de ropa))'
             r'(?=.*(hidrolavadora|lavadora a presion|lavadoras a presion|lavadora de (coche|auto|carro)|'
             r'lavado a chorro|jet wash|pressure washer|\d+ ?psi\b|pistola de agua|\bpsi\b.{0,30}(inalambric|bateria)|'
             r'soplador(a)? de (hojas|nieve)|motosierra|desbrozadora|podadora|cortasetos|pala para nieve|cortacesped|cortacespedes|tijeras de podar|pulverizador(a)?|nebulizador (frio|ulv)|fumigador|aspersor|sierra de poda|'
             r'engrasadora|cortador de cable|cabrestante|polipasto|montacargas? electrico portatil))'),
  ('Herramientas', 'Jardinería', 'wrench')),
 # La flejadora (la herramienta que cierra el fleje de una tarima) es
 # eléctrica, no de soldadura: dice "de soldadura" porque suelda el
 # fleje de PET. Son 1,275 en la captura, casi todas el mismo anuncio
 # repetido por vendedores distintos, y van con las herramientas
 # eléctricas porque eso es lo que son.
 (re.compile(r'maquina flejadora|flejadora (electrica|portatil|automatica)|maquina de flejado|'
             r'herramienta flejadora|empacadora electrica'),
  ('Herramientas', 'Herramientas eléctricas', 'wrench')),
 (re.compile(r'soldadora a bateria|soldadora inalambrica|kit de soldadura|cautin'),
  ('Herramientas', 'Soldadura', 'wrench')),
 # Linternas, luces de trabajo y lámparas recargables: el catálogo las
 # guarda en Iluminación, que ya tiene las de emergencia y las de exterior.
 (re.compile(r'^(?!.*(camara|proyector|aro de luz|tira led|\btv\b|monitor))'
             r'^(?!(?:\S+ ){0,3}(banda|correa|pulsera|cinta|bolsa|soporte)\b)'
             r'(?=.*(\blinterna\b|luz de trabajo|luces de inundacion|reflector led|lampara de campamento|'
             r'lampara recargable|luz de lectura|farol(a)? (led|solar|recargable)|luz de emergencia|lampara de emergencia))'),
  ('Iluminación', 'Lámparas de emergencia', 'bulb')),
 (re.compile(r'memoria ram|\bram\b|sodimm|udimm|\bddr[45]|modulo de memoria'),
  (PC, 'Memoria RAM', 'cpu')),
 # El enfriador de aire de la sala, no el del procesador. El catálogo
 # tiene 17 en Climatizadores evaporativos.
 (re.compile(r'^(?!.*(\bcpu\b|procesador|\bpc\b|\bitx\b|socket|\bam[45]\b|\blga\b))'
             r'(?=.*(enfriador de aire|climatizador evaporativo|enfriador evaporativo))'),
  ('Climatización', 'Climatizadores evaporativos', 'snowflake')),
 (re.compile(r'ventilador|enfriador|enfriamiento|cooler|disipador|\baio\b|refrigeraci|refrigeradora|'
             r'pasta (termica|de grasa)|grasa termica|compuesto termico|fuente de poder|'
             r'fuente de alimentacion|tarjeta grafica|filtro de (malla|polvo)|'
             r'hub de ventilador|cable (de extension de alimentacion|rgb)|neon difuso|'
             r'tanque de agua|reservorio|indicador flujo|boton de encendido|'
             r'placa adaptadora|\bsata\b|pcie|\bpc fan\b|noctua|kit de actualizaci.n pantalla|'
             r'gabinete|carcasa (para|de|del) (pc|computadora|ordenador)|funda para pc|'
             r'caja (modular|para pc)|chasis para pc|pc case|torre media|mid-tower|'
             r'almohadilla decorativa|para placa base|placa madre'), COMP),
 # "Teclado" en español es el de la computadora Y el musical, y esta regla
 # se llevaba los dos: en la captura de 6,387 anuncios de instrumentos, 153
 # fichas -- melódicas, pianos digitales, kalimbas, kazoos, controladores
 # MIDI y hasta bancos de piano -- entraban como periférico de PC. Lo
 # musical lo recoge la red de Instrumentos musicales del final.
 (re.compile(r'^(?!.*(melodica|pianica|kalimba|\bkazoo\b|instrumento musical|'
             r'\bmidi\b|\bpiano|\bmusical\b|sintetizador|\borgano\b|\bpianika\b|'
             r'banco (de|para) (piano|teclado)|banqueta|melodic))'
             r'(teclado|keyboard)'), ('Teclados', None, 'keyboard')),
 (re.compile(r'\bmouse\b|\braton\b|\bratones\b'), ('Mouse', None, 'mouse')),
 # Lo que dice "cargador" y no cayó en ninguna subcategoría: el del reloj
 # inteligente, el de la cámara vieja, el genérico "para Samsung". Al
 # final de REGLAS para que cualquier regla más precisa gane antes.
 (re.compile(r'^(?:\S+ ){0,3}cargador(es)?\b|cargador (para|compatible con|de reloj|magnetico|generico)'),
  ('Cargadores y adaptadores', 'Otros', 'plug')),
 # Instrumentos musicales, de red al final por la misma razón que Muebles,
 # Herramientas y Vehículos: la categoría tenía doce subcategorías y ninguna
 # regla general que la alcanzara -- solo dos muy puntuales (las baterías y
 # los micrófonos). Medido sobre la captura de 6,387 anuncios de
 # instrumentos: 4,799 caían en "no encaja en ninguna categoría", y entre
 # ellos 729 saxofones, 443 clarinetes, 386 tambores, 299 guitarras, 228
 # trombones y 216 flautas.
 #
 # Van DOS reglas y no una a propósito. Esta primera lista solo tiene
 # palabras que en español no nombran otra cosa.
 (re.compile(r'^(?!.*(de juguete|para (muneca|barbie)|\bmaqueta\b|'
             r'disfraz|\bpinata\b))'
             r'(?=.*(guitarra|ukulele|\bbanjo\b|mandolina|charango|requinto|\bjarana\b|'
             r'violin|violonchelo|\bcello\b|contrabajo|\barpa\b|\berhu\b|\bguqin\b|guzheng|'
             r'saxofon|trompeta|\bflauta|clarinete|trombon|armonica|\boboe\b|\bfagot\b|'
             r'corneta|melodica|\bpianica\b|\bkazoo\b|ocarina|didgeridoo|\bquena\b|zampo|'
             r'\bpandere|\bpandero\b|\bmaraca|xilofono|glockenspiel|metalofono|'
             r'\bcencerro\b|\bguiro\b|castanuela|kalimba|\bhandpan\b|\bagogo\b|\bcabasa\b|'
             r'cuenco (cantante|tibetano)|\bbongo|\bconga\b|\btimbal|redoblante|\btarola\b|'
             r'acordeon|sintetizador|\bmetronomo\b|capotraste|\bcejilla\b|\bbaqueta|'
             r'piano (digital|electrico|de cola|vertical|de pulgar|de dedo)|'
             # Segunda pasada, sobre lo que seguía cayendo en "no encaja":
             # "ukelele" se escribe de las dos formas en México, el bombardino
             # aparecía 40 veces, y los parches y platillos de batería son
             # media tienda de percusión (Remo, Evans, Sabian, Paiste).
             r'ukelele|bombardino|\bdjembe\b|\bshofar\b|\bhulusi\b|sousafon|'
             r'\bvibrafono\b|\bmarimba\b|\bsitar\b|\bbanjolele\b|\bcuatro\b venezolano|'
             r'parche (de |para )?(caja|tom|bombo|tarola|resonante|bateria)|'
             r'\bplatillo|\bcuencos? (cantante|tibetano|de cristal)|\bkashaka\b|'
             r'\baslatua|miniteclado|\bmelodion\b|\bcabaza\b|\bwaterphone\b|'
             r'\bmazos? de (vibrafono|marimba|xilofono|timbal)|\bdiapason\b|'
             r'instrumentos? musical))'),
  ('Instrumentos musicales', None, 'guitar')),
 # Y esta segunda las AMBIGUAS: "batería" es también la pila, "tambor" el de
 # la lavadora, "platillo" un plato, "cuerdas" una soga, "bajo" una
 # preposición. Exigen además una palabra del mundo musical en el título, y
 # por eso van después: cualquier regla más precisa (Baterías portátiles,
 # Lavadoras, Autos) ya se llevó lo suyo mucho antes.
 (re.compile(r'^(?!.*(de juguete|para (muneca|barbie)|\bmaqueta\b))'
             r'(?=.*(\bbateria|\btambor|\bplatillo|\bcuerdas\b|\bbajo\b|\bpercusion|'
             r'\bafinador\b|\batril\b|\bpartitura))'
             r'(?=.*(musical|instrumento|orquesta|\bbanda\b|percusion|'
             r'guitarra|\bpiano\b|\bmidi\b|conciert|\bmusica\b|baterista|'
             r'\bbaqueta|\btarola\b|\bhi-?hat\b|\bcharles\b|\bbombo\b))'),
  ('Instrumentos musicales', None, 'guitar')),
 # Herramientas, también de red y por la misma razón que Muebles: un
 # montón de aparatos nombran una herramienta de paso ("organizador para
 # taladro", "batería para atornillador"). Lo que ninguna otra regla
 # reclama y nombra una herramienta, es una herramienta.
 (re.compile(r'^(?!.*(de juguete|para nino|didactic|\bmaqueta\b))'
             r'(?=.*(herramienta|taladro|rotomartillo|esmeriladora|soldador|\n'
             r'soldadura|escalera|andamio|\\bbroca|\\blija\\b|desarmador|\n'
             r'destornillador|\\bpinza|\\bllave (allen|hexagonal|inglesa|perica|mixta)|\n'
             r'martillo|\\bcincel\\b|grabado(r|ra)? ?laser|multimetro|\\bvernier\\b|\n'
             r'flexometro|seguridad industrial|casco de seguridad|\n'
             r'guantes de (trabajo|seguridad|corte)|gas l\\.?p\\.?|plomeria|\n'
             r'jardineria|podadora|motosierra|desbrozadora|cortasetos|\n'
             r'compresor de aire|neumatica|\\bcemento\\b|revolvedora|carretilla))'),
  ('Herramientas', None, 'wrench')),
 # Vehículos, de red por la misma razón que Muebles y Herramientas: la
 # categoría tenía nueve subcategorías y ninguna regla que la alcanzara, así
 # que una captura de autos y bicis entraba al 16% -- 7,568 de 10,162 anuncios
 # caían en "no encaja", casi todos accesorio y refacción.
 (re.compile(r'^(?!.*(de juguete|para (muneca|barbie)|\bmaqueta\b|'
             r'control remoto.{0,15}escala|montable para nino))'
             r'(?=.*(\bbicicleta|\bbici\b|ciclismo|\btriciclo|\bmotocicleta|\bmoto\b|'
             r'\bautomovil|\bvehiculo|\bauto\b|\bcoche\b|\bcarro\b|camioneta|'
             r'\bllanta|neumatico|autoestereo|estereo (para|de) (auto|coche|carro)|'
             r'car ?radio|carplay|android auto|dash ?cam|casco (de|para) (moto|ciclismo)|'
             r'\bsillin\b|manillar|portabicicleta|arrancador de bateria))'),
  ('Autos, bicicletas y motos', None, 'car')),
 # Muebles va AL FINAL de REGLAS, de red. Un título de mueble nombra el
 # mueble y nada más, pero un montón de aparatos lo nombran de paso:
 # "cargador para silla de ruedas", "ventilador para cama", "teléfono de
 # mesa". Con la regla arriba se llevaba todos esos (104 en la regresión).
 # Abajo, cada categoría se queda primero con lo suyo y lo que ninguna
 # reclama y nombra un mueble, es un mueble.
 # "Ventilador de escritorio" es un ventilador y "lámpara de mesa" una
 # lámpara: ahí el mueble solo dice dónde se pone el aparato. Esas reglas
 # corren después, así que sin esta guarda Muebles se las llevaba (27
 # ventiladores terminaron de escritorio antes de agregarla).
 (re.compile(r'^(?!.*(silla (de ruedas|de bebe|para auto|alta|periquera)|'
             r'mesa de planchar|tabla de planchar|casa de munecas|'
             r'para (muneca|barbie|casa de munecas)|maqueta|'
             r'(ventilador|abanico|calefactor|lampara|purificador|humidificador|'
             r'difusor|reloj|espejo|estufa|parrilla|horno|proyector|monitor|'
             r'impresora|telefono|radio|television|pantalla|bocina|caja fuerte)'
             r' (de|para) (escritorio|mesa|buro|cama)))'
             r'(?=.*(\bsilla|\bsillon|\bsofa|\bescritorio|\bmesa|\bmesita|'
             r'\bcama\b|\bcolchon|\blibrero|\brepisa|\bburo\b|\bzapater|'
             r'\bperchero|\bropero|\barmario|\bcloset|\bcomoda|\bcomedor|'
             r'\btaburete|\bbanca\b|\bvitrina|\bcredenza|\blitera))'),
  ('Muebles', None, 'sofa')),
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
 "B012T634SM": ("NUTRIBULLET", 'Electrodomésticos', 'Licuadoras', 'appliance'),
 "B0HD9M1PVH": ("NINJA", 'Electrodomésticos', 'Licuadoras', 'appliance'),
 # El título abre como kit de limpieza y por eso CABECERA lo tira, pero lo
 # que se vende es la boquilla que se le pone a la aspiradora para limpiar
 # el ducto de la secadora. El catálogo ya tiene dónde ponerlo.
 "B0H512VSLK": (None, 'Aspiradoras', 'Accesorios', 'vacuum'),
 # Cola de la sección de café. El catálogo ya guarda el knock box de Ninja
 # ("Knock Box Ninja Luxe Café XSKKNOCKBOX") entre las espresso, así que el
 # cubo de posos y el embudo de 54 mm van con él; no hay subcategoría de
 # accesorios de cafetera.
 "B0BZZCRMP5": (None, 'Cafeteras', 'Espresso', 'coffee'),
 "B0GTZJZZ1H": (None, 'Cafeteras', 'Espresso', 'coffee'),
 # Central eléctrica de 245 Wh: misma cosa que la DJI Power 1000 V2 y las dos
 # DaranEner de esta misma captura, que ya están en Estaciones de energía.
 "B0DB1S36YP": ("EF ECOFLOW", 'Otros', 'Estaciones de energía', 'battery'),
 # Tarja de cocina: el catálogo las tiene en plomería, con los fregaderos
 # tipo vasija y el fregadero comercial BWE.
 "B0FJ8ZDP95": (None, 'Herramientas', 'Plomería', 'wrench'),
 # Cava de 8 botellas: las cavas chicas del catálogo (GW8XDBB2 de 8, MW6XDBB
 # de 6) están entre los frigobares; las de 33 botellas para arriba, no.
 "B07Q8ZP8HC": ("AVERA", 'Refrigeradores', 'Frigobares', 'fridge'),
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
 "B0G3BH7RN2": ("LIZZE", 'Aparatos de belleza', 'Planchas para cabello', 'sparkle'),
 # Karcher VC3, WD3 y KWD1: el título no dice de qué tipo son, pero el catálogo
 # ya trae estos mismos modelos ("Karcher De Tanque Vc3", "Karcher Agua Polvo
 # Sopladora Wd2", "Karcher Wdl1 Solidos Y Liquidos") en el cajón de tanque.
 "B0D212FFVF": ("KARCHER", 'Aspiradoras', 'De tanque', 'vacuum'),
 "B0B45DV64T": ("KARCHER", 'Aspiradoras', 'De tanque', 'vacuum'),
 "B0BWG91V1T": ("KARCHER", 'Aspiradoras', 'De tanque', 'vacuum'),
 "B0FGDYJJQQ": ("XTREME PC GAMING", 'Computadoras de escritorio', 'Torre', 'desktop'),
 "B0GM3C1186": ("PRIDE GAMING", 'Computadoras de escritorio', 'Torre', 'desktop'),
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
 "B0GFJYK5C4": (None, 'Aparatos de belleza', 'Planchas para cabello', 'sparkle'),
 # Se anuncia como "Robot de Limpieza de Ventanas" pero el resto del título
 # dice lo que es: "Limpiador de Vidrios Eléctrico de Mano, 2000Pa, con
 # Batería Recargable, Hoja de Escobilla de Goma de 11 Pulgadas para Puertas
 # de Ducha". No trepa el vidrio solo: es una aspiradora de mano con jalador.
 "B0HBPKT3KS": ("FTVOGUE", 'Aspiradoras', 'Portátiles', 'vacuum'),
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
                'Licuadoras', 'appliance'),
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

# Las de la captura de microondas y lavavajillas. "GE" son dos letras, pero
# marca() exige que no la rodeen letras ni números, así que "GEL" no entra.
# Marcas de celular que no son una palabra corriente (las que sí -- Vivo,
# Honor, Cat -- van en MARCAS_CELULAR, solo al principio del título).
MARCAS += ["OPPO", "REALME", "ZTE", "NOKIA", "ONEPLUS", "INFINIX", "TECNO", "MOTOROLA",
           "REDMI", "POCO", "ALCATEL", "LANIX", "BMOBILE", "NUBIA", "CUBOT", "DOOGEE",
           "UMIDIGI", "ULEFONE", "OUKITEL", "BLACKVIEW", "KYOCERA", "CROSSCALL", "HOTWAV"]
MARCAS += ["TEKA", "GE", "GALANZ", "TOSHIBA", "BREVILLE", "SHARP", "AIRMSEN",
           "MYSMILE", "VORTEX"]

ALIAS = {"REDMI": "XIAOMI", "POCO": "XIAOMI", "THERMALRLGHT": "THERMALRIGHT", "WHITE-WESTINGHOUSE": "WHITE WESTINGHOUSE",
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

# Videojuegos: la consola, el juego y el accesorio se nombran con la MISMA
# palabra ("Xbox Series X" aparece en los tres), así que la palabra no alcanza.
# Lo que los separa es DÓNDE está la plataforma en el título:
#
#   "Nintendo Switch 2 - Versión Nacional"          -> al principio: es la consola
#   "Dragon Age: The Veilguard - Xbox Series X"     -> al final: es el juego
#   "Cable de alimentación para Playstation 4"      -> hay una pieza: es accesorio
#
# El accesorio manda sobre los otros dos porque un control para Switch nombra
# la consola igual que la consola misma.
RX_VJ_PLATAFORMA = re.compile(
    r'\b(nintendo switch|switch ?2|switch oled|switch lite|'
    r'playstation ?[345]|ps[345]\b|playstation portal|'
    r'xbox series [xs]|xbox one|xbox 360|xbox\b|'
    r'steam ?deck|rog ally|legion go|msi claw|'
    r'wii u\b|wii\b|nintendo 3ds|psp\b|ps vita|game ?boy)')

RX_VJ_ACCESORIO = re.compile(
    r'\b(control(es|ler|lers)?|mando|joy ?con|gamepad|volante|palanca|arcade stick|'
    r'grip|empunadura|soporte|base de carga|dock|stand|wall mount|'
    r'montaje de pared|cargador|cable|adaptador|bateria|pila|'
    r'boton(es)?|abxy|thumbstick|joystick|gatillo|'
    r'protector|mica|skin|calcomania|sticker|ventilador|enfriador|'
    r'tarjeta (micro ?sd|de memoria)|memoria micro ?sd|'
    r'repuesto|reemplazo|replacement|kit de (limpieza|reparacion|herramientas)|'
    r'charger|battery|button|holder|mount|case|cover|carrying)\b')

RX_VJ_CONSOLA = re.compile(r'^(?:\S+ ){0,4}(consola|console)\b|'
                           r'(consola|console)\b.{0,20}(nintendo|playstation|xbox)')


def sub_videojuego(tn):
    """Consolas / Software / Accesorios, por dónde cae la plataforma."""
    if RX_VJ_ACCESORIO.search(tn):
        return 'Accesorios'
    if RX_VJ_CONSOLA.search(tn):
        return 'Consolas'
    m = RX_VJ_PLATAFORMA.search(tn)
    if not m:
        return None
    # La plataforma en las primeras palabras es el aparato; más atrás es la
    # coletilla que dice para qué consola es el juego.
    return 'Consolas' if len(tn[:m.start()].split()) <= 2 else 'Software'


# Muebles. La categoría tenía quince subcategorías y una sola regla, la de
# escritorios, así que una captura de muebles entraba al 14%: de 12,373
# anuncios, 9,857 caían en "no encaja" -- sillas, sofás, mesas y camas
# enteras. Acá se reparte igual que en Videojuegos, con un desempate propio.
#
# Primero lo que NO es el mueble aunque lo nombre: la rueda de repuesto de la
# silla, el organizador de cables del escritorio, la funda del sofá. Después
# el mueble, de lo específico a lo general, porque los títulos encadenan
# varios ("mesita de noche de 2 niveles, buró blanco, mesita auxiliar").
RX_MUEBLE_PIEZA = re.compile(
    r'\b(ruedas? (giratorias?|de repuesto|para)|rodaja|garruch|'
    r'organizador de cables|pasacables|ojal|'
    r'tornillo|tuerca|perno|herraje|bisagra|riel(es)? de cajon|'
    r'(funda|forro|cubierta|protector) (para|de) (sofa|sillon|silla|colchon|mesa)|'
    r'cojin|almohadon|respaldo de repuesto|pata(s)? de (repuesto|mesa|silla)|'
    r'kit de (montaje|reparacion)|refaccion|reemplazo)\b')

RX_MUEBLE = re.compile(
    r'\b(silla|sillas|sillon|sofa|sofas|loveseat|futon|puff|banco|taburete|'
    r'butaca|escritorio|mesa|mesita|mesas|comedor|antecomedor|'
    r'cama|camas|litera|colchon|box spring|somier|'
    r'librero|estanteria|estante|repisa|buro|zapatera|zapatero|'
    r'perchero|paraguero|ropero|armario|closet|comoda|'
    r'recamara|vitrina|credenza|barra de bar|banca)\b')


def sub_mueble(tn):
    """Reparte Muebles por el PRIMER mueble que nombra el título.

    Los títulos encadenan varios ("Escritorio para computadora con buró y
    repisa", "mesita de noche de 2 niveles, buró blanco"): lo que se vende es
    lo que va primero, y lo de atrás describe lo que trae. Con una lista de
    prioridad fija el escritorio con buró terminaba en Burós.
    """
    candidatos = [
        (r'\bcolchon|box spring|\bsomier\b', 'Colchones'),
        (r'\b(buro|mesita de noche|mesa de noche|mesa de luz)\b', 'Burós'),
        (r'\b(litera|cabecera|base de cama|cama|camas)\b', 'Camas'),
        (r'\b(sofa ?cama|sofa|sofas|sillon|loveseat|futon)\b', 'Sofás'),
        (r'\b(zapatera|zapatero)\b', 'Zapateras'),
        (r'\b(perchero|paraguero|burro de ropa)\b', 'Percheros'),
        (r'\b(ropero|armario|closet|comoda|vitrina|credenza)\b', 'Roperos'),
        (r'\b(librero|estanteria|estante para libros)\b', 'Libreros'),
        (r'\b(repisa|entrepano)\b', 'Repisas'),
        (r'mesa de (billar|ping ?pong|futbolito|juego|poker)', 'Mesas de juego'),
        (r'\bescritorio\b', 'Escritorios'),
        (r'\bsillas? (de|para) comedor|\bbancos? (de|para) comedor', 'Sillas'),
        (r'\b(comedor|antecomedor)\b', 'Mesas de comedor'),
        (r'mesa (de centro|auxiliar|lateral|de sala|de cafe)', 'Mesas de centro'),
        (r'\b(silla|sillas|banco|taburete|butaca|banca)\b', 'Sillas'),
        (r'\b(mesa|mesas|mesita)\b', 'Mesas de centro'),
        (r'\bestante\b', 'Repisas'),
    ]
    mejor = None
    for patron, sub in candidatos:
        m = re.search(patron, tn)
        if m and (mejor is None or m.start() < mejor[0]):
            mejor = (m.start(), sub)
    return mejor[1] if mejor else 'Otros'


# Categorías que tenían subcategorías declaradas pero ninguna función que las
# repartiera: el producto entraba con la categoría bien y la subcategoría
# vacía. Eran 7,000 fichas repartidas en nueve categorías.

def sub_juego_mesa(tn):
    if re.search(r'rompecabeza|\bpuzzle\b|\bpuzle\b', tn): return 'Rompecabezas'
    if re.search(r'\bajedrez\b|\bchess\b', tn): return 'Ajedrez'
    if re.search(r'woodestic', tn): return 'Woodestic'
    if re.search(r'\bdomino\b|\bbackgammon\b|\bdamas\b|\bgo\b(?= )', tn): return 'Clásicos'
    if re.search(r'cartas|\bnaipes\b|\bbaraja\b|\buno\b|\bpoker\b|mazo\b', tn): return 'De cartas'
    if re.search(r'\brol\b|calabozos|dragones|\bd&d\b|\bdados\b|miniatura', tn): return 'De rol y dados'
    if re.search(r'\bloteria\b|\bmemorama\b|serpientes y escaleras|\bturista\b|'
                 r'\bmonopol|\bjenga\b|\bscrabble\b|\bbasta\b', tn): return 'De mesa clásicos'
    return 'Otros juegos'


def sub_instrumento(tn):
    # El orden de siempre (el instrumento primero, los accesorios al final)
    # se conserva tal cual: cambiarlo movería de subcategoría fichas que ya
    # están en el catálogo. Lo que se agrega son las familias que faltaban,
    # dentro de la rama que les corresponde.
    if re.search(r'guitarra|\bbajo\b|ukulele|ukelele|\bbanjo\b|banjolele|mandolina|'
                 r'charango|requinto|\bjarana\b|\blaud\b', tn): return 'Guitarras'
    # Percusión de mano y de placas ANTES que Baterías: una pandereta o un
    # xilófono no son un kit de batería, y la rama de abajo se los llevaba
    # por la palabra "percusion" que casi todos traen en el título.
    if re.search(r'\bpandere|\bpandero\b|\bmaraca|xilofono|glockenspiel|metalofono|'
                 r'\bcencerro\b|\bguiro\b|\bclaves\b|castanuela|\btriangulo\b|'
                 r'\bshaker\b|kalimba|\bhandpan\b|tongue drum|cuenco (cantante|tibetano)|'
                 r'\bsonaja|cascabel|\bchocalho\b|\bagogo\b|\bcaba[sz]a\b|vibraslap|'
                 r'campanas? de viento|carillon|\bdjembe\b|\bkashaka\b|\baslatua|'
                 r'\bvibrafono\b|\bmarimba\b|\bwaterphone\b|campanas? de mano|'
                 r'cuencos? (cantante|tibetano|de cristal)|tazon de cristal', tn): return 'Percusión'
    if re.search(r'bateria|tambor|\bcajon\b|percusion|platillo|conga|\bbongo|'
                 r'\bredoblante\b|\btarola\b|\bbombo\b|\bbaqueta|\btimbal|\bparche\b|\bcharles\b|hi-?hat', tn): return 'Baterías'
    if re.search(r'violin|violonchelo|\bcello\b|contrabajo|\bviola\b|\barpa\b|'
                 r'\berhu\b|\bguqin\b|guzheng|\bkoto\b|\bsitar\b|\bcitara\b', tn): return 'Cuerdas'
    if re.search(r'saxofon|trompeta|flauta|clarinete|trombon|\btuba\b|armonica|oboe|'
                 r'\bfagot\b|\bcorno\b|\btrompa\b|corneta|melodica|\bpianica\b|'
                 r'\bkazoo\b|ocarina|didgeridoo|\bgaita\b|\bquena\b|zampo|flautin|'
                 r'\bflugel|\bcornamusa\b|bombardino|\bshofar\b|\bhulusi\b|sousafon|'
                 r'\bcuerno\b|\bmelodion\b|\bpiano de viento\b', tn): return 'Viento'
    if re.search(r'microfono', tn): return 'Micrófonos'
    if re.search(r'interfaz de audio|mezcladora|mixer|monitor de estudio|'
                 r'controlador midi|\bdaw\b|preamp', tn): return 'Producción de audio'
    if re.search(r'teclado|piano|sintetizador|organo|acordeon|melodion', tn): return 'Teclados'
    if re.search(r'amplificador|\bamp\b|combo de guitarra', tn): return 'Amplificadores'
    if re.search(r'tornamesa|tocadiscos|turntable', tn): return 'Tornamesas'
    if re.search(r'\bpedal(es)? (de|para)? ?(efecto|distorsion|reverb|delay|wah|loop)|'
                 r'pedalera|\bmultiefecto', tn): return 'Efectos y pedales'
    if re.search(r'atril|funda|estuche|correa|cuerdas de repuesto|afinador|'
                 r'capotraste|puas?\b|banqueta|\bboquilla\b|\bcanas?\b|colofonia|'
                 r'\bresina\b|pastilla (de|para)|\bpickup\b|parche (de|para)|'
                 r'soporte (de|para)|banco (de|para) (piano|teclado|bateria)|'
                 r'metronomo|\bpartitura|aceite (de|para) (valvula|llave)|'
                 r'\bdiapason\b|tenedor de afinacion|cable midi|\bperilla\b', tn): return 'Accesorios'
    return None


def sub_iluminacion(tn):
    if re.search(r'tira (led|de luz)|cinta led|\bstrip\b', tn): return 'Tiras LED'
    if re.search(r'foco intelig|bombilla intelig|\bwifi\b.{0,15}foco|foco.{0,15}\bwifi\b|'
                 r'foco.{0,20}(alexa|google)', tn): return 'Focos inteligentes'
    if re.search(r'\bfoco\b|bombilla|\bled\b.{0,10}\bw\b|luminaria', tn): return 'Focos'
    if re.search(r'lampara de (escritorio|mesa|buro)|de escritorio', tn): return 'Lámparas de escritorio'
    if re.search(r'lampara de (techo|colgante)|candil|plafon|araña', tn): return 'Lámparas de techo'
    if re.search(r'lampara de (pared|muro)|arbotante|aplique', tn): return 'Lámparas de pared'
    if re.search(r'lampara de (piso|pie)', tn): return 'Lámparas de piso'
    if re.search(r'emergencia|linterna|recargable.{0,15}apagon', tn): return 'Lámparas de emergencia'
    if re.search(r'exterior|jardin|solar|reflector|\bposte\b', tn): return 'Exterior'
    if re.search(r'\blampara\b|\bluz\b|\bluces\b', tn): return 'Decorativa'
    return None


def sub_vehiculo(tn):
    """Reparte Autos, bicicletas y motos.

    Lo PRIMERO es la pieza, no el vehículo: un sillín para bicicleta nombra la
    bicicleta igual que la bicicleta, y una captura de esta categoría trae
    sobre todo accesorio y refacción. Con el vehículo arriba, el sillín, el
    escape y la dashcam entraban como "Bicicletas", "Motocicletas" y "Autos".
    """
    if re.search(r'\b(casco|guantes de moto|chamarra de moto)\b', tn):
        return 'Cascos para moto'
    if re.search(r'dash ?cam|camara (para|de) (auto|carro|coche|tablero)|camara de reversa', tn):
        return 'Dashcams y cámaras'
    if re.search(r'\bllanta|neumatico|\brin\b|\brines\b', tn):
        return 'Llantas'
    if re.search(r'bateria (para|de) (auto|coche|carro)|acumulador|arrancador', tn):
        return 'Baterías para auto'
    if re.search(r'estereo|autoestereo|radio (para|de) (auto|carro)|carplay|android auto|'
                 r'car ?radio|doble din|2 ?din', tn):
        return 'Estéreos para auto'
    if re.search(r'bocina.{0,20}(auto|carro)|\bwoofer\b|subwoofer', tn):
        return 'Bocinas para auto'
    if re.search(r'amplificador', tn):
        return 'Amplificadores para auto'
    if re.search(r'\b(sillin|manillar|pedal|cadena|pinon|cesta|canastilla|'
                 r'guardabarro|cuadro|horquilla|timbre|bomba de aire|candado|'
                 r'portabicicleta|alforja|velocimetro|ciclocomputadora|'
                 r'desviador|manubrio de bici)\b', tn):
        return 'Accesorios para bicicleta'
    if re.search(r'\b(escape|silenciador|carenado|estribo|baul|maletero|puno)\b', tn):
        return 'Accesorios para moto'
    if re.search(r'aceite|filtro|balata|amortiguador|bujia|limpiaparabrisas|'
                 r'gato hidraulico|cables? pasa corriente|visera|tapete|'
                 r'funda para (auto|volante|asiento)|cubre ?volante|'
                 r'refaccion|repuesto|\bespejo\b|\bsoporte\b', tn):
        return 'Accesorios y refacciones'
    # Y recién ahora el vehículo entero.
    if re.search(r'\bmotocicleta\b|\bmoto\b|scooter de gasolina', tn):
        return 'Motocicletas'
    if re.search(r'\bbicicleta|\bbici\b|\bmtb\b|ciclismo|\btriciclo\b', tn):
        return 'Bicicletas'
    if re.search(r'\bauto\b|\bcoche\b|\bcarro\b|camioneta|\bautomovil\b', tn):
        return 'Autos'
    return None


def sub_domotica(tn):
    if re.search(r'enchufe intelig|contacto intelig|smart plug', tn): return 'Enchufes inteligentes'
    if re.search(r'apagador intelig|interruptor intelig|smart switch', tn): return 'Interruptores inteligentes'
    if re.search(r'cerradura|chapa intelig|smart lock', tn): return 'Cerraduras inteligentes'
    if re.search(r'foco intelig|tira led|iluminacion intelig|bombilla intelig', tn): return 'Iluminación inteligente'
    if re.search(r'bocina intelig|alexa|google (home|nest)|echo dot|homepod', tn): return 'Bocinas inteligentes'
    if re.search(r'\bhub\b|puente|bridge|zigbee|centro de control', tn): return 'Hubs'
    if re.search(r'cortina|persiana', tn): return 'Cortinas motorizadas'
    if re.search(r'sensor|detector|timbre intelig|videoportero', tn): return 'Sensores'
    if re.search(r'termostato', tn): return 'Termostatos'
    return None


def sub_camara(tn):
    if re.search(r'gopro|camara de accion|action cam|insta ?360', tn): return 'Cámaras de acción'
    if re.search(r'instantanea|instax|polaroid', tn): return 'Instantáneas'
    if re.search(r'videocamara|camcorder|filmadora', tn): return 'Videocámaras'
    if re.search(r'mirrorless|sin espejo|\balpha\b|\bzv-?e\b|\bx-?t\d', tn): return 'Mirrorless'
    if re.search(r'reflex|\bdslr\b|\beos\b.{0,10}\d|\bd\d{3,4}\b', tn): return 'Réflex'
    if re.search(r'\blente\b|\bobjetivo\b|\bmm f/|teleobjetivo|gran angular', tn): return 'Lentes'
    if re.search(r'tripie|tripode|estabilizador|gimbal|flash|filtro|correa|'
                 r'bolsa|mochila|bateria|cargador|tarjeta', tn): return 'Accesorios'
    if re.search(r'drone|dron\b', tn): return 'Accesorios'
    return None


def sub_herramienta(tn):
    """Reparte Herramientas. La categoría tenía quince subcategorías y las
    reglas solo alcanzaban a tres, así que una captura de ferretería entraba
    al 17%: de 4,227 anuncios, 2,985 caían en "no encaja"."""
    if re.search(r'grabado(r|ra)? ?laser|\blaser\b.{0,20}(grabar|grabado|cortar)|'
                 r'maquina de grabado|\bcnc\b', tn):
        return 'Grabado láser'
    if re.search(r'soldadur|soldador|soldadora|estano|electrodo|\bmig\b|\btig\b|\bmma\b|'
                 r'careta de soldar|inversora', tn):
        return 'Soldadura'
    if re.search(r'escalera|andamio|banco de trabajo|plataforma de trabajo', tn):
        return 'Escaleras'
    if re.search(r'casco|guantes de (trabajo|seguridad|corte)|chaleco reflejante|'
                 r'lentes de seguridad|googles de seguridad|tapones auditivos|'
                 r'arnes de seguridad|botas de seguridad|mascarilla|respirador|'
                 r'seguridad industrial|epp\b', tn):
        return 'Seguridad industrial'
    if re.search(r'\bgas l\.?p\.?\b|gas lp|regulador de gas|manguera de gas|'
                 r'cilindro de gas|tanque de gas', tn):
        return 'Gas LP'
    if re.search(r'plomeria|llave de paso|\bcespol\b|coflex|tuberia|\bpvc\b|'
                 r'destapacanos|manguera de jardin|conexion hidraulica|'
                 r'\bniple\b|\bcodo\b.{0,12}(pvc|cobre)', tn):
        return 'Plomería'
    if re.search(r'multimetro|\bvernier\b|calibrador|flexometro|cinta metrica|'
                 r'nivel laser|distanciometro|medidor|termometro infrarrojo|'
                 r'\bescuadra\b|micrometro', tn):
        return 'Medición'
    if re.search(r'cable (electrico|thw|calibre)|\bcontacto\b|apagador|pastilla|'
                 r'centro de carga|caja de conexion|conector electrico|'
                 r'material electrico|canaleta|\bcinta de aislar\b', tn):
        return 'Material eléctrico'
    if re.search(r'neumatic|\baire comprimido\b|compresor de aire|pistola de aire|'
                 r'\bimpacto\b.{0,15}neumatic', tn):
        return 'Neumáticas'
    if re.search(r'jardin|podadora|desbrozadora|motosierra|cortasetos|'
                 r'\bmanguera\b|aspersor|tijeras de podar|soplador de hojas', tn):
        return 'Jardinería'
    if re.search(r'cemento|revolvedora|carretilla|cimbra|varilla|\bblock\b|'
                 r'construccion|\bllana\b|cuchara de albanil', tn):
        return 'Construcción'
    if re.search(r'caja de herramientas|organizador de herramientas|'
                 r'\bgabinete\b.{0,15}herramienta|maletin de herramientas|'
                 r'panel de herramientas|\bcarro de herramientas\b', tn):
        return 'Organización'
    if re.search(r'\bbroca|\bdisco de (corte|desbaste)|\blija\b|puntas? de (atornillador|desarmador)|'
                 r'\bsierra caladora hoja|accesorios? para (taladro|rotomartillo)|'
                 r'\bmandril\b|adaptador de brocas', tn):
        return 'Accesorios para herramientas eléctricas'
    if re.search(r'taladro|rotomartillo|esmeriladora|sierra|lijadora|pulidora|'
                 r'router\b|cepillo electrico|atornillador (electrico|inalambrico)|'
                 r'\bcaladora\b|ingletadora|\bfresadora\b|hidrolavadora', tn):
        return 'Herramientas eléctricas'
    if re.search(r'\bllave\b|\bpinza|\bdesarmador|destornillador|martillo|'
                 r'\bcincel\b|\blima\b|\bsegueta\b|\bprensa\b|\bgato\b|'
                 r'juego de dados|matraca|\bhexagonal\b|\ballen\b|herramienta manual', tn):
        return 'Herramientas manuales'
    return None


def sub_bocina(tn):
    """Barras de sonido, Grande, Pequeña o Mediana, que es como parte el
    catálogo. La barra lo dice en el nombre. Para el tamaño la seña más
    honesta que trae el título son los watts: de 100 W para arriba es la
    torre o el bafle de fiesta, hasta 15 W es la portátil de bolsillo, y
    en medio queda todo lo demás. Cuando no hay watts se decide por cómo
    se vende: "torre", "profesional" y "boombox" son grandes; "mini",
    "clip" y "de ducha" son chicas."""
    if re.search(r'barra de sonido|\bsound ?bar\b|teatro en casa|home theater|\bhtib\b', tn):
        return 'Barras de sonido'
    m = re.search(r'(\d{2,4})\s?w(?:atts?)?\b', tn)
    w = int(m.group(1)) if m else None
    if re.search(r'torre de sonido|bafle (profesional|amplificado|de \d{2})|altavoz de torre|'
                 r'\bboombox\b|party ?(speaker|box)|karaoke.{0,20}(profesional|\d{3} ?w)|'
                 r'\b(1[2-9]|2\d)\s?(pulgadas|")|\bpa\b system|linea de arreglo', tn):
        return 'Grande'
    if re.search(r'\bmini\b|\bclip\b|llavero|de ducha|de bolsillo|portatil pequen|'
                 r'\b[1-5]\s?(pulgadas|")', tn):
        return 'Pequeña'
    if w is not None:
        if w >= 100: return 'Grande'
        if w <= 15: return 'Pequeña'
        return 'Mediana'
    return 'Mediana'

def sub_monitor(tn):
    """Gaming, Portátiles u Oficina. El portátil se lleva la pantalla en la
    mochila (lo dice el título o es un extensor de laptop); el gamer se
    anuncia como tal o pasa de 100 Hz, que es el corte que usa el
    catálogo. Lo demás es de oficina."""
    if re.search(r'monitor portatil|portatil.{0,20}monitor|extensor de pantalla|pantalla portatil|'
                 r'monitor (usb-?c )?de viaje|segunda pantalla portatil', tn):
        return 'Portátiles'
    if re.search(r'\bgamer\b|\bgaming\b|ultragear|odyssey|\brog\b|\btuf\b|predator|nitro|'
                 r'mobiuz|\baorus\b|\bagon\b|\bg-?sync\b|freesync premium|'
                 r'\b(1[2-9]\d|[2-9]\d\d) ?hz\b', tn):
        return 'Gaming'
    return 'Oficina'

def sub_laptop(tn):
    """Gamer u Oficina, que es como parte el catálogo. La gamer se anuncia
    como tal: lo dice en el nombre, o trae GPU dedicada (RTX, GTX, Radeon
    RX) o una pantalla de más de 120 Hz. Lo demás es de oficina."""
    if re.search(r'\bgamer\b|\bgaming\b|\brtx ?\d|\bgtx ?\d|radeon rx ?\d|\brog\b|\btuf\b|predator|nitro \d|'
                 r'legion|victus|katana|cyborg|omen|\balienware\b|raider|stealth|zephyrus|\d{3} ?hz|'
                 r'\b(1[4-9]\d|[2-9]\d\d) ?hz\b', tn):
        return 'Gamer'
    return 'Oficina'

def sub_teclado(tn):
    """El catálogo solo distinguía mecánico y membrana, y así 1,378 teclados se
    quedaban sin repartir. El combo con mouse, el ergonómico partido y el
    numérico son productos distintos, no variantes del mismo."""
    if re.search(r'\bcombo\b.{0,25}(mouse|raton)|teclado y (mouse|raton)|'
                 r'(mouse|raton) y teclado|kit de teclado y', tn):
        return 'Combos con mouse'
    if re.search(r'teclado numerico|\bnumpad\b|pad numerico', tn):
        return 'Numéricos'
    if re.search(r'ergonomic|dividido|partido|split', tn):
        return 'Ergonómicos'
    if re.search(r'mecanic', tn):
        return 'Mecánicos'
    if 'membrana' in tn:
        return 'Membrana'
    if re.search(r'inalambric|bluetooth|wireless|2\.4 ?ghz', tn):
        return 'Inalámbricos'
    return None

def sub_tv(tn):
    if re.search(r'\b4k\b|qled|uhd|qned|oled|miniled|mini-led', tn): return '4K'
    if re.search(r'full hd|\bfhd\b|\bhd\b|1080p|720p', tn): return 'HD'
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
    # La mini lavadora de cubeta, la plegable de viaje y la manual de pedal no
    # son ni de carga superior ni frontal: son otro aparato, y el catálogo
    # tenía 1,770 lavadoras sin repartir en buena parte por esto.
    if re.search(r'\bmini lavadora|lavadora (mini|portatil|plegable|manual|de mano|de cubeta)|'
                 r'lavadora.{0,25}(portatil|plegable|de viaje|sin electricidad|no electrica)|'
                 r'lavadora de pedal', tn):
        return 'Portátiles'
    # Automática de tamaño normal que no dice por dónde se carga. Se nombra por
    # lo que sí afirma, en vez de adivinar la puerta.
    if re.search(r'\bautomatica\b|\d{1,2} ?kg\b|\d{1,2} ?kilos', tn):
        return 'Automáticas'
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
        return 'Accesorios'
    if re.search(r'robot aspirador|aspiradora robot|robot aspirador?a', tn):
        return 'Robots aspiradores'
    # Tanque, taller y agua/polvo: la Karcher VC3 y la shop vac del catálogo
    # ya están aquí, y la Koblenz "Canister" es lo mismo con otro nombre.
    if re.search(r'canister|de tanque|shop vac|seco *[-y]* *(humedo|mojado)|'
                 r'humedo/?seco|seco/?humedo|agua y polvo|solidos y liquidos|'
                 r'galones|wet/?dry|sopladora', tn):
        return 'De tanque'
    # El resto es la aspiradora de casa. El catálogo mete aquí también las de
    # cable (Atrix ERGO Lite, SIPPON vertical), así que el nombre de la
    # subcategoría se queda corto pero la convención ya está tomada.
    return 'Portátiles'

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
        return 'Frigobares'
    return 'Refrigeradores'

def sub_cafetera(tn):
    if re.search(r'capsula', tn): return 'De cápsulas'
    if re.search(r'espresso|expreso|\d+ bares', tn):
        return 'Espresso'
    if re.search(r'portatil|de viaje', tn): return 'Portátiles'
    if re.search(r'molinillo|molino de cafe', tn): return 'Molinillos de café'
    # Las que no llevan bomba ni cápsula: la prensa francesa, el sifón, el
    # vertidor y la de frío. Son un grupo grande y se vendían sin repartir.
    if re.search(r'prensa francesa|french press|\bsifon\b|cold ?brew|'
                 r'vertidor|pour ?over|\bchemex\b|\bv60\b|cafetera italiana|'
                 r'\bmoka\b|greca', tn):
        return 'Manuales'
    if re.search(r'goteo|drip|\d{1,2} tazas|programable|percoladora', tn):
        return 'De goteo'
    return None

def sub_celular(tn):
    if 'iphone' in tn: return 'iPhone'
    if re.search(r'resistente|rugged|robusto|todoterreno|\bip6[89]\b|a prueba de (golpes|agua)', tn): return 'Resistentes'
    # El teléfono básico (de tapa, de botones grandes, 2G) no es Android:
    # tiene su propia subcategoría.
    if re.search(r'\b[23]g\b|botones? grandes?|(personas|adultos) mayores|\bsenior\b|abatible|(flip|feature) ?phone|'
                 r'(de|con) tapa\b|rotary|telefono (celular |movil )?basico|celular basico|boton sos|\bsos\b|'
                 r'(pantalla (de )?)?\b[12][.,]\d+ ?(pulgadas|")|unlocked phone', tn): return 'Básicos'
    return 'Android'

def sub_tableta(tn):
    return 'Apple' if 'ipad' in tn else 'Android'

# La marca del celular cuando abre el título y no está en MARCAS: "vivo" y
# "honor" son palabras corrientes ("en vivo", "honor a") y no pueden entrar
# a la lista general, pero al principio del nombre de un celular son la marca.
MARCAS_CELULAR = re.compile(r'\b(vivo|oppo|realme|honor|xiaomi|redmi|poco|motorola|moto|samsung|huawei|zte|nokia|tcl|'
                            r'oneplus|infinix|tecno|google|apple|iphone|nubia|alcatel|lanix|bmobile|blackview|doogee|'
                            r'ulefone|oukitel|cubot|umidigi|fossibot|kyocera|blu|hotwav|agm|cat|nothing|sony|'
                            r'blackberry|htc|lg|asus|zebra|hisense)\b')
def marca_celular(tn):
    m = MARCAS_CELULAR.search(tn[:50])
    if not m: return None
    return {'redmi': 'XIAOMI', 'poco': 'XIAOMI', 'moto': 'MOTOROLA', 'iphone': 'APPLE',
            'cat': 'CAT PHONES'}.get(m.group(1), m.group(1).upper())


# Las dos maneras de nombrar la forma del audífono que usa la tienda, más
# las familias de modelo que la dicen sin decirla: los Sony WF y los IE de
# Sennheiser son de botón, los WH y los HD son de diadema. "Auriculares
# inalámbricos" a secas no dice la forma y se queda sin subcategoría: el
# catálogo prefiere el hueco a la mentira.
RX_DIADEMA = re.compile(r'diadema|over[- ]ear|on[- ]ear|circumaural|supra ?a?ural|de copa|orejeras|'
                        r'sobre (la )?(oreja|el oido)|alrededor de (la )?oreja|encima de la oreja|'
                        r'over the ear|around[- ]ear|\bgamer\b.{0,20}(microfono|mic\b)|'
                        r'\bheadphones?\b|\bheadset\b|\bcascos?\b|\bvincha\b|banda para la cabeza|'
                        r'conduccion osea|bone conduction|\bwh-?\d|\bhd ?[2-9]\d{2}\b|\bath-m\d|\bdt ?\d{3}\b|'
                        r'\bqc ?\d{2}\b|quietcomfort|\bmomentum \d|\bxm[3-6]\b|crusher|hesh')
RX_EARBUD  = re.compile(r'in[- ]ear|earbuds?\b|\btws\b|true wireless|intraura|intraaura|intraudit|'
                        r'de boton\b|\bbotones?\b(?!.*grandes)|earphones?\b|\bairpods?\b|\bbuds\b|'
                        r'intrauricular|monitor(es)? in ?ear|\biem\b|\bcanalphone|'
                        r'banda para el cuello|neckband|de cuello|\bwf-?\d|\bie ?\d{3}\b|\bse ?\d{3}\b|'
                        r'\bfreebuds\b|\bgalaxy buds\b|\bpods\b|gancho (para|de) (la )?oreja|clip de oreja|ear ?hook|'
                        r'\bsemi-?in-?ear\b|auriculares? de boton')
RX_INAL    = re.compile(r'inalambric|bluetooth|wireless|\btws\b|2\.4 ?ghz')
RX_CABLE   = re.compile(r'con cable|alambric|\b3\.5 ?mm\b|\bjack\b|cableado|\bwired\b|'
                        r'conector (usb|tipo c|usb-?c|lightning)')

def sub_audio(tn):
    """Diadema o Earbuds, con cable o inalámbricos, que son las cuatro
    subcategorías del catálogo. Cuando la forma sale dos veces (un
    "headset" que también dice "in-ear") gana la que aparezca antes en el
    título, que es la que nombra el producto. Cuando no sale ninguna, o
    cuando no se sabe si lleva cable, se devuelve None: media tienda se
    anuncia como "Auriculares Bluetooth" a secas y adivinar la forma sería
    inventar."""
    # Dos formatos que el catálogo no tenía y que no son ni diadema ni botón:
    # el de oído abierto (clip sobre la oreja, conducción ósea) y el de
    # gaming, que se vende como categoría propia y casi siempre trae micrófono.
    if re.search(r'open[- ]?ear|oido abierto|de clip\b|con clip\b|clip \w*oreja|'
                 r'conduccion osea|bone conduction', tn):
        return 'De oído abierto'
    if re.search(r'\bgamer\b|\bgaming\b|para juegos|para gaming|\bheadset\b.{0,30}(juego|gamer)|'
                 r'\bquantum\b|\bkraken\b|\bcloud (ii|alpha|stinger)\b|\barctis\b|'
                 r'\brog (delta|cetra)\b|\bblackshark\b', tn):
        return 'Gamer'
    d = RX_DIADEMA.search(tn)
    e = RX_EARBUD.search(tn)
    if d and e:
        diadema = d.start() < e.start()
    elif d or e:
        diadema = bool(d)
    else:
        # "Auriculares inalámbricos" a secas: hoy el formato que se vende así,
        # sin decir la forma, es el de botón -- la diadema SIEMPRE se nombra
        # ("diadema", "over-ear", "headset"), porque es su argumento de venta.
        # Antes esto devolvía None y dejaba 3,739 audífonos sin repartir.
        # Sin forma declarada: el bluetooth manda sobre la mención del cable
        # (casi siempre es el cable de carga, no de audio). Lo que se vende
        # así, sin decir la forma, es el de botón: la diadema se nombra
        # siempre porque es su argumento de venta.
        if RX_INAL.search(tn):
            return 'Earbuds inalámbricos'
        if RX_CABLE.search(tn):
            return 'Earbuds con cable'
        return None
    inal, cable = bool(RX_INAL.search(tn)), bool(RX_CABLE.search(tn))
    if not inal and not cable:
        # Forma conocida y conexión no: hoy lo que no aclara es inalámbrico,
        # porque el de cable lo dice para diferenciarse.
        return 'Diadema inalámbrica' if diadema else 'Earbuds inalámbricos'
    if inal == cable:
        # Un inalámbrico que además trae cable auxiliar dice las dos cosas;
        # gana el bluetooth, que es lo que define cómo se usa.
        if inal and re.search(r'bluetooth|inalambric|wireless|\btws\b', tn): inal, cable = True, False
        else: return None
    return (('Diadema' if diadema else 'Earbuds') + ' ' +
            (('inalámbrica' if diadema else 'inalámbricos') if inal else 'con cable'))

def pistas_de_departamento():
    """{nombre normalizado -> (categoría, subcategoría, icono)} sacado del
    catálogo: cada subcategoría cuyo nombre es único entre categorías, y
    cada categoría a secas (subcategoría None). El icono es el que más usan
    sus fichas, o el de la categoría si todavía no tiene ninguna."""
    from data_io import load_catalog
    data = load_catalog()
    iconos = collections.Counter()
    for p in data['products']:
        iconos[(p['category'], p.get('subcategory'), p.get('image'))] += 1
    def icono(cat, sub, defecto):
        c = [(n, i) for (k, s, i), n in iconos.items() if k == cat and (sub is None or s == sub) and i]
        return max(c)[1] if c else defecto
    pistas, repetidas = {}, set()
    for c in data['categories']:
        for s in c.get('subcategories') or []:
            k = T(s['name'])
            if k in pistas: repetidas.add(k)
            pistas[k] = (c['id'], s['id'], icono(c['id'], s['id'], s.get('icon') or c.get('icon')))
    for k in repetidas: del pistas[k]
    for c in data['categories']:
        for k in {T(c['name']), T(c['id'])}:
            pistas.setdefault(k, (c['id'], None, icono(c['id'], None, c.get('icon'))))
    return pistas

captura = json.load(io.open(sys.argv[1], encoding='utf-8'))
PISTAS = pistas_de_departamento() if any(it.get('dept') for it in captura) else {}
por_dept = 0
alta, fuera = [], []
for it in captura:
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
    # El departamento de Amazon manda cuando nombra una subcategoría del
    # catálogo; si solo nombra la categoría, es la red para lo que ninguna
    # regla reconoce.
    pista = PISTAS.get(T(it.get('dept') or ''))
    hit = pista if pista and pista[1] else next((v for rx, v in REGLAS if rx.search(tn)), None)
    if not hit and pista: hit = pista
    if not hit:
        fuera.append((it, 'no encaja en ninguna categoría')); continue
    cat, sub, img = hit
    if hit is pista:
        por_dept += 1
    elif cat == 'Baterías portátiles': sub = tramo(capacidad_mah(it['title']))
    elif cat == 'Bocinas': sub = sub_bocina(tn)
    elif cat == 'Monitores': sub = sub_monitor(tn)
    elif cat == 'Laptops': sub = sub_laptop(tn)
    elif cat == 'Teclados': sub = sub_teclado(tn)
    elif cat == 'Mouse': sub = sub_mouse(tn)
    elif cat == 'Televisores': sub = sub_tv(tn)
    elif cat == 'Audífonos': sub = sub_audio(tn)
    elif cat == 'Lavadoras': sub = sub_lavadora(tn)
    elif cat == 'Aspiradoras': sub = sub_aspiradora(tn)
    elif cat == 'Refrigeradores': sub = sub_refri(tn)
    elif cat == 'Cafeteras': sub = sub_cafetera(tn)
    elif cat == 'Celulares': sub = sub_celular(tn)
    elif cat == 'Tabletas': sub = sub_tableta(tn)
    elif cat == 'Videojuegos': sub = sub_videojuego(tn)
    elif cat == 'Muebles': sub = sub_mueble(tn)
    elif cat == 'Herramientas': sub = sub_herramienta(tn)
    elif cat == 'Juegos de mesa': sub = sub_juego_mesa(tn)
    elif cat == 'Instrumentos musicales': sub = sub_instrumento(tn)
    elif cat == 'Iluminación': sub = sub_iluminacion(tn)
    elif cat == 'Autos, bicicletas y motos': sub = sub_vehiculo(tn)
    elif cat == 'Domótica y hogar inteligente': sub = sub_domotica(tn)
    elif cat == 'Cámaras y fotografía': sub = sub_camara(tn)
    mk = marca(it['title'])
    if cat == 'Celulares' and not mk: mk = marca_celular(tn)
    alta.append({**base, 'brand': mk, 'category': cat,
                 'subcategory': sub, 'image': img})

json.dump(alta, io.open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'ALTA: {len(alta)}   FUERA: {len(fuera)}   sin precio (no se dan de alta): '
      f'{sum(1 for a in alta if a["price"] is None)}'
      + (f'   por departamento de Amazon: {por_dept}' if por_dept else '') + '\n')
for k, n in collections.Counter((a['category'], a['subcategory']) for a in alta).most_common():
    print(f'  {n:4}  {k[0]} / {k[1]}')
print('\nsin marca:', sum(1 for a in alta if not a['brand']))
print('\n--- descartados ---')
for k, n in collections.Counter(m for _, m in fuera).most_common():
    print(f'  {n:4}  {k}')
print()
for it, m in fuera:
    print(f'  [{m[:30]:30}] {it["asin"]} {it["title"][:75]}')
