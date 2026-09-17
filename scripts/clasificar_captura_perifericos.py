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
"Belleza y cuidado personal", "Electrodomésticos" y "Equipo comercial".

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
turmalina), o que la marca sea de peluquería. Van a "Belleza y cuidado personal /
Secadoras de cabello", junto a los cepillos secadores y los
multiestilizadores que el catálogo ya tiene ahí.

La décima son planchas: cuatro de ropa (dos de viaje y las dos Silver Star
de vapor por gravedad). "Plancha" sola no alcanza, porque la de pelo, la
prensa de sublimación y la de ropa se llaman igual; las reglas van de lo más
específico a lo más general y en ese orden salen los tres cepillos
alisadores ("Belleza y cuidado personal / Planchas para cabello") y la máquina de
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
 (re.compile(r'^(?:\S+ ){0,3}(mesa|soporte|manija|alfombrilla|estera|tapete|almohadilla|repuesto|funda|cubierta|teflon|lamina|guantes?|cinta|bandeja|'
             r'elemento calefactor|controlador|placa|base|hojas? de (teflon|ptfe)|papel ptfe|hojas? de transferencia|resistencia).{0,60}'
             r'(prensa (de calor|termica)|sublimacion|transferencia (termica|de calor)|cricut|easy ?press)'),
  'accesorio de prensa de calor, no es la prensa'),
 (re.compile(r'^(?:\S+ ){0,6}(cubierta|funda)s? .{0,30}impresora|dust cover.{0,30}(impresora|printer)'),
  'funda de impresora, no es la impresora'),
 # El suplemento ya NO se descarta: a pedido del usuario tiene categoría
 # propia ("Suplementos", ver la red al final de REGLAS). Antes esta lista
 # lo dejaba fuera por consumible, y de paso evitaba que "apoya la salud
 # celular" lo metiera en Celulares; de eso se encarga ahora la red, que va
 # antes que nada gracias a que el título de un suplemento lo dice claro.
 # Se conserva solo el agua de hidrógeno, que no es un suplemento sino una
 # bebida.
 (re.compile(r'tabletas? de (agua de )?hidrogeno|hidrogeno molecular'),
  'bebida (consumible)'),
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
             r'cargador(es)? .{0,30}\d{2,} (ranuras|puertos)|estacion de carga movil|'
             r'cargador(es)? (portatil )?para (celular(es)?|telefonos?),? (estacion de carga|para multiples dispositivos)|carr(o|ito) de (almacenamiento|carga)|'
             r'bolsa colgante|locker|\d{2,} ranuras|\d+ compartimentos|'
             r'(caja|organizador|nizer|estante).{0,30}(guardar|compartimentos)))'
             r'(?=.*(celulares?|telefonos?|smartphones?|tablets?|tabletas?|\bipad\b|dispositivos? (moviles?|electronicos?)|multiples dispositivos))'),
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
 # El calefactor queda fuera de esta regla: el "\d+ kW" que delata al
 # cargador de coche eléctrico también lo llevan el radiador de aceite
 # y el calefactor de invernadero, y por eso se descartaban 716 de la
 # captura de clima con el motivo de un cargador.
 (re.compile(r'^(?!.*(calefactor|calefaccion|calentador de (ambiente|invernadero|espacio|patio)|'
             r'radiador (lleno de aceite|de aceite|digital|portatil)|estufa electrica))'
             r'^(?!(?:\S+ ){0,2}(soporte|montaje|funda)\b)(?!.*(patinete|scooter|hoverboard|bicicleta electrica|e-?bike|ebike|kukirin|segway|ninebot|'
             r'dewalt|makita|milwaukee|ryobi|ridgid|craftsman|arrancador|mantenedor|jump starter|'
             r'cargador (de |para )?bater[ií]as? (de |para )?(auto|coche|carro|moto|automovil)))'
             r'(?=.*(carritos? de golf|golf cart|montacargas|carretilla elevadora|forklift|sillas? (de )?ruedas|(fuente de alimentacion|cargador de bateria).{0,40}\d{4} ?w\b|'
             r'cargador (electrico )?(de|para) (valla|cerca|cerco)|baja impedancia|'
             r'\bbarcos?\b|(uso|motor|bateria|cargador) marin[oa]|\bmarine\b|vehiculos? electricos?|coches? electricos?|autos? electricos?|cargador(es)? ev\b|\bev\b (cargador|charger|adaptador)|\bevse\b|j1772|tipo 2 iec|iec 62196|wallbox|wall box|'
             r'ccs2|\bgbt\b|\d+ ?kw\b|victron|xantrex|samlex|\bmppt\b|ciclo profundo|plomo[- ]?acido|bateria agm|\bsla\b|cargador .{0,30}lifepo4|\blipo\b|'
             r'^(?!.*(laptop|portatil|notebook|macbook|chromebook|\bdell\b|\bhp\b|lenovo|\basus\b|\bacer\b|\bmsi\b|thinkpad|inspiron|'
             r'pavilion|ideapad|vivobook|zenbook|latitude|omen|legion|surface|razer|alienware|imac|usb|tipo c|\bpd\b|\bqc\b|'
             r'magsafe|iphone|celular|telefono|smartphone|tablet|ipad|reloj|watch|mah|pilas|sobretension|supresor|regleta|multicontacto|\btomas?\b|enchufe|contacto|'
             r'interruptor|apagador|disyuntor|breaker|\brele\b|relevador|contactor|controlador ats|transferencia|temporizador|tomacorriente|termostato|dimmer|atenuador|placa de pared|modulo|cerradura|sensor|timbre))'
             r'.*(\b(3[6-9]|[4-9]\d)([.,]\d)? ?v\b|\d+ ?ah\b|\d+ ?amperios|\d+ ?v[ /,]{0,3}\d{2,}([.,]\d)? ?a\b)))'),
  'cargador de batería de vehículo o industrial, no es un cargador de consumo'),
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
 # El juguete DE MASCOTA no se descarta: Mascotas/Juguetes es una
 # subcategoría del catálogo. Esta guarda existe para la cocinita de
 # juguete y el teléfono de imitación, no para la pelota del perro -- 561
 # juguetes de perro y gato se perdían acá en la captura del 16-sep.
 (re.compile(r'^(?!.*(\bperro|\bgato\b|\bgatos\b|\bgatito|mascota|\bcachorro|\bcanino|\bfelino|'
             r'\bhamster|\bconejo\b|\bhuron\b|\bpet (toy|toys|bed)\b|\bdog (toy|toys)\b|'
             r'\bcat (toy|toys)\b))'
             # Lookahead, no coincidencia directa: con "^...(?:juguete|...)"
             # la guarda solo se aplicaba si el título EMPEZABA con la
             # palabra, y dejaba pasar todo lo que la nombra más adelante.
             r'(?=.*(\bjuguetes?\b|de imitacion|de simulacion|en miniatura|'
             r'de cocina para ninos))'),
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
 (re.compile(r'^' + ES_ROBOT_VIDRIOS + r'(?!.*(intelig|\bwifi\b|alexa|tuya|\bapp\b|smart|bluetooth))(?!.*\bcon control remoto).*control remoto'),
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
 # La persiana celular (de ventana) y la cortina se descartaban para que
 # no entraran como celular; ahora tienen su sitio en Blancos / Cortinas.
 (re.compile(r'barras? (de|para) cortina de (ducha|bano)|tubo para cortina de (bano|ducha)|cortinas? (de|para) (ducha|bano)|organizador de ducha'),
  ('Otros', 'Baño', 'box')),
 (re.compile(r'^(?!(?:\S+ ){0,3}(soportes?|barras?|rieles?|ganchos?|anillos?|argollas?|alzapanos|abrazaderas?|tubos?)\b)'
             r'(?!.*(ducha|de bano|proyeccion|proyector|\bpvc\b|de tiras|cortina de aire|motorizad|intelig|\bwifi\b|alexa|tuya))'
             r'(?=.*((persianas?|cortinas?|estor(es)?|tonos?) (verticales |plisad[ao]s? |enrollables? |opac[ao]s? )?celular|'
             r'persianas? (plisad|de panal|enrollable|vertical|romana|de madera|de aluminio|de bambu|blackout)|cortinas? (para|de) (ventana|techo|puerta|sala|recamara|cocina|bano)|nido de abeja|'
             r'bloqueador(es)? de luz|opac[ao]s? de bloqueo|^(?:\S+ ){0,3}(cortinas?|persianas?|estor(es)?)\b))'),
  ('Blancos y ropa de cama', 'Cortinas', 'pillow')),
 # Suplementos. Va PRIMERA, que es la excepción a la regla de este archivo
 # ("las redes, al final"), y hace falta explicar por qué.
 #
 # Primero se probó primera con disparadores amplios y fue un desastre: 233
 # fichas bien clasificadas se las llevó, entre ellas las cafeteras "con
 # cápsula de espresso" por "cápsula" y los cargadores "de aleación de zinc"
 # por "zinc". Se movió al final y ahí el problema fue el contrario: las
 # reglas precisas se le adelantaban y "YPENZA FF Flex 30 Tabletas |
 # Suplemento Alimenticio" entraba como tableta Android y "DIM 100 mg |
 # Suplemento Antioxidante y de Apoyo Celular" como celular -- exactamente
 # el caso que la vieja guarda de FUERA describía.
 #
 # La solución es primera PERO con disparadores que solo nombran un
 # suplemento: "suplemento", "creatina", "probiótico", "ashwagandha"... y la
 # dosis únicamente acompañada del formato ("860 mg | 30 capletas").
 # "Vitamina C", "magnesio" y "zinc" a secas quedaron fuera: son también el
 # material de un cargador y el ingrediente de una crema. Así no es una red
 # amplia arriba, es una regla precisa arriba.
 (re.compile(r'^(?!.*(\blibro\b|pasta blanda|pasta dura|\bautor\b|\bnovela\b|'
             r'\bcrema\b|\bserum\b|\bshampoo|\bchampu\b|\bjabon\b|\bmascarilla\b|'
             r'\blocion\b|\bmaquillaje\b|\bperfume\b|\bcafetera|\bcafe\b|'
             # La tableta que purifica agua y la coctelera de proteína no se
             # toman como suplemento: una es para el agua y la otra es un envase.
             r'purificacion de agua|potabiliza|\bbotella\b|\bcoctelera\b|\bshaker\b|'
             r'\bpara (perro|gato|mascota)|\bveterinari))'
             r'(?=.*(\bsuplement|\bproteina (en polvo|de suero|whey|vegetal)|\bwhey\b|'
             r'\bcreatina\b|\bprobiotic|\bprebiotic|\bmultivitamin|\bcolageno (hidrolizado|tipo)|'
             r'\bomega ?3\b|\bmelatonina\b|\bbiotina\b|\bglucosamina\b|\bcurcuma\b|'
             r'\bashwagandha\b|\bbacopa\b|\bresveratrol\b|\bnootropico\b|\bespirulina\b|'
             r'\bmoringa\b|\bchlorella\b|\bpre ?entreno\b|\bbcaa\b|\bl-?carnitina\b|'
             r'\bglutamina\b|\bcitrato de (magnesio|potasio)|\bbisglicinato\b|'
             r'\bapoyo (digestivo|inmun|articular)\b|'
             # La dosis vale si viene con el formato en el mismo título.
             r'(?=.*\b\d{2,4} ?mg\b)(?=.*\b(capsulas?|capletas?|tabletas?|gomitas?|softgels?|comprimidos?)\b)))'),
  ('Suplementos', None, 'heart-pulse')),
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
             r'(?=.*(\brizador(a)? de (pelo|cabello)|tenaza (rizadora|para rizar)|'
             r'ondulador(a)? de (pelo|cabello)))'),
  ('Belleza y cuidado personal', 'Rizadores', 'sparkle')),
 (re.compile(r'^(?!.*\bsecador)'
             r'(?=.*(cepillo alisador|alisador(a)? de (pelo|cabello)|'
             r'plancha.{0,30}(de pelo|de cabello|alisador)))'),
  ('Belleza y cuidado personal', 'Planchas para cabello', 'sparkle')),
 # Red de Belleza y cuidado personal, el departamento entero: el aparato
 # Y el cosmético. La categoría ya tenía 1,828 fichas de maquillaje entre
 # sus quince subcategorías, así que el cosmético no estrena casa, solo le
 # faltaba regla. Medido sobre la captura de 12,602 anuncios de belleza del
 # 17-sep: de 12,309 nuevos entraban 1,775 y se descartaban 10,534, entre
 # ellos 2,040 cremas y sueros, 1,203 de maquillaje, 884 aparatos faciales
 # y 712 pelucas y extensiones.
 #
 # Va después de las reglas finas de secadora, plancha y rizador (que ganan
 # por precisión) y antes de las redes de Muebles y Herramientas, que se
 # llevaban la silla de tocador y el organizador de maquillaje.
 #
 # "Rizador" pide borde de palabra: sin él, "pulve-rizador" metía las
 # pistolas de pintura, las hidrolavadoras y los fumigadores en Rizadores.
 # La misma trampa vieja que "Wilson Me-diana" y el cable "cat 6".
 (re.compile(r'^(?!.*(\bzapatos?\b|calzado|cacahuate|avellana|\bbatidora\b|pastelera|chantilly|'
             r'\bkn95\b|\bn95\b|cubrebocas|tapabocas|mascarilla (quirurgica|desechable|de tela)|'
             r'para (trastes|ropa|piso|auto|coche|carro|moto|inodoro)|limpiador de (pantalla|teclado)|'
             r'aceite (de motor|para motor|lubricante|hidraulico|de cocina|de oliva|comestible)|'
             r'gel (antibacterial|de silicona|refrigerante|balistico)|'
             r'de ambiente|\bpanal(es)?\b|ambientador|aromatizante|'
             # El aparato de clima no es un cosmético: el mini ventilador se
             # vende "para maquillaje" y el Dyson viene en color "rubor";
             # el absorbedor de humedad y el purificador dicen "fragancia".
             r'ventilador|abanico|absorbedor de humedad|deshumidificador|purificador de aire|'
             # El cepillo de dientes y la pasta dental son de Salud.
             r'\bdental\b|cepillo de dientes|enjuague bucal|irrigador|hilo dental|'
             r'\bperro|\bgato\b|mascota|veterinari|\bbebe\b|\bbebes\b|\bbaby\b|'
             r'\bimpresora\b|\bcartucho\b|\btoner\b|\btinta\b|'
             r'\bsilla\b|taburete|\bescritorio\b|organizador|\bcargador\b|\bcarrito\b|'
             r'\bsuplement|\bcapsulas? blandas\b|\btabletas?\b|\bcomprimidos?\b))'
             r'(?=.*('
             r'secadora? de (cabello|pelo)|cepillo secador|plancha (de|para) (cabello|pelo)|alaciadora|'
             r'\brizador|tenaza (de|para) (cabello|rizos)|\bdepilador|luz pulsada|cera depilatoria|'
             r'rasuradora|afeitadora|\brastrillo (de|para) afeitar\b|cortapelo|recortador de (barba|vello)|'
             r'radiofrecuencia (facial|corporal|profesional)|microagujas|microdermoabrasion|'
             r'dermapen|cavitacion|\bhifu\b|hydra ?facial|jet peel|criolipolisis|'
             r'ultrasonido (facial|corporal|de belleza)|oxigeno de hidrogeno|'
             r'mascara facial led|terapia de luz led|fototerapia facial|lifting facial|'
             r'limpiador facial (electrico|ultrasonico)|peeling ultrasonico|'
             r'vaporizador facial|sauna facial|analizador de piel|'
             r'cepillo (corporal|de cuerpo|en seco)|cepillo electrico para la espalda|'
             # La captura trae medio catálogo en inglés.
             r'\bflat iron\b|\bhair dryer\b|\bcurling iron\b|\blip plumper\b|\bbronzer\b|'
             r'\bconcealer\b|\beyeshadow\b|\bmoisturizer\b|\bcleanser\b|\bnail polish\b|'
             r'\bfacial mist\b|\bbody lotion\b|\bhair mask\b|'
             r'lampara (uv|led) (para|de) unas|torno (de|para) unas|drill (para|de) unas|'
             r'protector solar|bloqueador solar|\bfps ?\d|\bspf ?\d|\bsunscreen\b|'
             r'\bserum\b|\bs.rum\b|'
             r'crema (facial|corporal|hidratante|antiarrugas|para el cuerpo|para la cara|reparadora|nutritiva)|'
             r'crema (anti|de dia|de noche|contorno)|'
             r'limpiador facial|gel limpiador|agua micelar|\btonico facial\b|contorno de ojos|'
             r'mascarilla (facial|capilar|de hidrogel|coreana|de arcilla)|'
             r'exfoliante (facial|corporal)|\bretinol\b|\bniacinamida\b|'
             r'acido (salicilico|hialuronico|glicolico|kojico)|'
             r'\bfoundation\b|(base|paleta|kit|set|polvo) de maquillaje|maquillaje (facial|profesional|liquido)|'
             r'brocha(s)? (de|para) maquillaje|esponja de maquillaje|'
             r'\blabial\b|\blipstick\b|\brimel\b|'
             r'mascara de pesta|delineador (de ojos|liquido)|rubor (en polvo|en crema|compacto)|'
             r'sombra de ojos|paleta de sombras|'
             r'corrector de ojeras|setting spray|polvo compacto|brocha (de|para) maquillaje|'
             r'\bshampoo\b|\bchampu\b|\bacondicionador (para|de) (cabello|pelo)\b|tratamiento capilar|'
             r'tinte (para|de) (cabello|pelo)|\bkeratina\b|aceite (para|de) (cabello|pelo|barba)|'
             r'\bperfume\b|eau de (toilette|parfum)|agua de colonia|'
             r'\bdesodorante\b|antitranspirante|'
             r'\bpeluca|extensiones de (cabello|pelo)|'
             r'esmalte (de|para) unas|gel (para|de) unas|acrilico (para|de) unas|unas postizas|press ?on nails|'
             r'kit de manicura|juego de manicura|\bcortaunas\b|empujador de cuticula|lima de unas|\bpedicure\b'
             r'))'),
  ('Belleza y cuidado personal', None, 'sparkle')),
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
 # tiene en Belleza y cuidado personal, junto con los cepillos secadores y los
 # multiestilizadores (el Dyson Airwrap, el SUTRA Aero Styler 5 en 1).
 (re.compile(r'^(?=.*\bsecador)(?=.*(cabello|\bpelo\b|peinad|rizo|frizz|difusor|'
             r'alaciadora|ionic|iones|turmalina|estiliz|salon))'),
  ('Belleza y cuidado personal', 'Secadoras de cabello', 'sparkle')),
 # Cuatro marcas que solo hacen aparatos de peluquería. Cuando el título se
 # queda en "Conair Secadora 289es" o "Hot Tools Secador Silencioso 1875 W",
 # la marca es lo único que queda, y basta: la secadora de ropa la venden
 # Whirlpool, Mabe y LG, no BaByliss.
 (re.compile(r'^(?=.*\bsecador)(?=.*(conair|babyliss|remington|hot tools))'),
  ('Belleza y cuidado personal', 'Secadoras de cabello', 'sparkle')),
 # Lo que ya no puede ser otra cosa: el cepillo que seca, el título en inglés
 # y la secadora de viaje (la de ropa no viaja).
 (re.compile(r'cepillo secador|hair dryer|secador(a)? de viaje'),
  ('Belleza y cuidado personal', 'Secadoras de cabello', 'sparkle')),
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

 # ---- Captura de cocina comercial (12,112) y de domótica (12,284) ----
 # La refacción del refrigerador no es el refrigerador: el evaporador, el
 # compresor, el termostato y la junta de la puerta nombran el aparato al
 # que sirven. Iban a "Refrigeradores / Uso comercial" (1,194 en una
 # captura) o a Componentes de PC por la palabra "refrigeración".
 (re.compile(r'^(?!.*(\bpc\b|computadora|gamer|gaming|cpu\b|\baio\b|socket|\bam[45]\b|\blga\b|automotriz|para (auto|coche|carro)\b|vehiculo|camion|automovil|nevera portatil|refrigerador portatil|ventilador (portatil|de mano|usb)))'
             r'(?=.*((condensador|evaporador|\bcompresor|termostato|burlete|empaque|junta (magnetica|de puerta|de goma)|'
             r'filtro secador|motor (de|del) ventilador|ventilador de refrigeracion|sensor de temperatura|tarjeta|placa (de control|electronica)|'
             r'manija|bisagra|capacitor|relevador|arrancador|deflector|valvula de expansion|tubo capilar|'
             r'gas refrigerante|\br134a\b|\br600a\b|\br404a\b|\br410a\b|\br22\b|tira de sellado|goma de puerta).{0,60}'
             r'(refrigerador|congelador|nevera|frigorifico|refrigeracion|heladera|camara fria|vitrina|enfriador)|'
             r'refrigerador.{0,30}(ventilador de refrigeracion|condensador|evaporador|compresor|termostato)|'
             r'filtro secador|\bcompresor (embraco|tecumseh|danfoss|de refrigeracion|frigorifico|para refrigerador)|'
             r'gas refrigerante|\br134a\b|\br600a\b|\br404a\b|motor (de |para )?(refrigeracion|refrigerador|congelador|evaporador|condensador)|motor electronico.{0,40}refrigeraci|'
             r'(gozne|bisagra|herraje).{0,30}refrigera|placa de enfriamiento (para|de) (congelador|refrigerador)|(alfombrilla|tapete) anticongelante|divisor de refrigerador|separador de congelador|estante.{0,40}(para|de) (congelador|refrigerador|nevera|vitrina)|'
             r'motor (de |del )?ventilador (del |de )?(evaporador|condensador)|ventilador de repuesto|ventilador (de |para )?(frigorifico|refrigerador|congelador|nevera)|'
             r'termometro (de|para) (refrigera|congelador|nevera)|sondas? de temperatura|(motor|ventilador).{0,25}(for|para) (refrigerador|congelador|nevera)))'),
  ('Refacciones', 'Refacciones para electrodomésticos', 'gear')),
 # La cortina de tiras de PVC: la del cuarto frío va con la refrigeración
 # comercial y la del garaje con la construcción.
 (re.compile(r'(cortina|puerta|tiras?) (de |enfriadora de )?(pvc|tiras|plastico|vinilo)|tiras? de pvc|cortina de tiras'
             r'(?=.*(refrigerador|congelador|camara fria|cuarto frio|comercial|refrigeracion))'),
  ('Equipo comercial', 'Refrigeración comercial', 'snowflake')),
 (re.compile(r'(cortina|puerta|tiras?) (de |enfriadora de )?(pvc|tiras|plastico|vinilo)|tiras? de pvc|cortina de tiras'),
  ('Herramientas', 'Construcción', 'wrench')),
 # El radio de bolsillo, el inversor y la báscula tienen su sitio y no lo
 # alcanzaba ninguna regla (el radio acababa en Mobiliario por 'la mejor
 # recepción', el inversor en Herramientas, la báscula de cocina en manuales).
 (re.compile(r'^(?!.*(bocina|altavoz|para (auto|coche|carro)|estereo|\bcd\b|tocadiscos|bluetooth|speaker|parlante|\btv\b))'
             r'(?=(?:\S+ ){0,3}radios? (am|fm|portatil|de onda corta|de transistores|multibanda|de bolsillo|solar|de emergencia|retro|vintage|de mesa|digital|dab|despertador)|.*radio (am|fm)\b|.*radio.{0,30}(onda corta|transistores))'),
  ('Otros', 'Radios', 'box')),
 (re.compile(r'^(?!.*(estacion de energia|estacion electrica|generador|power station|central electrica))(?=.*(inversor(es)? de (corriente|voltaje|onda|energia)|inversor .{0,25}\d+ ?w\b|convertidor (cc|dc) a (ca|ac)|inversor (solar|senoidal|de onda)))'),
  ('Otros', 'Inversores', 'box')),
 (re.compile(r'basculas? (de bano|corporal|digital de bano|intelig|de peso corporal|para personas|de grasa corporal)|bascula.{0,30}(bluetooth|app|grasa corporal|imc)'),
  ('Salud', 'Básculas', 'heart-pulse')),
 (re.compile(r'basculas? (de cocina|digital de cocina|de precision|de bolsillo|digital de precision|para alimentos)|balanzas? (de cocina|de precision|digital)'),
  ('Cocina y comedor', 'Utensilios de cocina', 'coffee')),
 # El termostato del motor y la bomba de agua del coche nombran el
 # termostato, y la domótica no es lo suyo.
 (re.compile(r'(carcasa|conjunto) (de )?termostato|termostato (de|del|para) (motor|coche|auto|carro|vehiculo)|'
             r'termostato .{0,50}(ford|chevrolet|nissan|toyota|volkswagen|honda|mazda|\bkia\b|hyundai|\bbmw\b|audi|mercedes|jeep|dodge|volvo|subaru|\bgm\b|silverado|cummins)|'
             r'bomba de agua (para|de) (motor|auto|coche|carro|autobus|camion)|interruptor .{0,40}(puerta trasera|maletero|automovil)'),
  ('Refacciones', 'Para autos', 'gear')),
 # Domótica, por el aparato y no por "alexa": el enchufe, el apagador, la
 # cerradura con huella, el foco y la cortina inteligentes. Antes cualquier
 # cosa "compatible con Alexa" era una bocina inteligente (808 en una
 # captura) y el enchufe inteligente no encajaba en nada.
 (re.compile(r'^(?!(?:\S+ ){0,3}(cargador|cable|funda|soporte|adaptador|base|repuesto|montura|bateria|manija de repuesto|placa (de pared|frontal|decorativa))\b)'
             r'(?!.*(\bpc\b|gamer|gaming|para (auto|coche|carro|moto)\b|windows|celeron|\bintel\b|\bghz\b|\bram\b|\bssd\b|mini pc|calefactor|radiador|estufa|chimenea|calentador))'
             r'(?=.*(enchufes? intelig|contactos? (de pared )?intelig|smart plug|tomacorriente intelig|enchufes? (wifi|alexa)|regleta intelig|multicontacto intelig|'
             r'apagador(es)? intelig|interruptor(es)? (de luz |de pared |tactil |de atenuacion |inalambrico )?intelig|smart switch|'
             r'interruptor(es)? (de luz |de pared |tactil )?(wifi|zigbee|tuya)|apagador(es)? (wifi|tuya)|modulo (interruptor|rele) (wifi|intelig)|rele wifi|'
             r'atenuador intelig|dimmer intelig|pulsador de boton de interruptor|interruptor.{0,30}(tuya|alexa|zigbee)|'
             r'cerraduras?.{0,60}(intelig|electronic|digital|biometric|huella|reconocimiento facial|\bapp\b|\bwifi\b|bluetooth|tuya|contrasena|codigo|tarjeta|sin llave|keyless|teclado)|'
             r'smart lock|chapa intelig|cerrojo intelig|manijas? (de |para )?(puerta )?.{0,30}huella|bloqueo de puerta intelig|'
             r'focos? intelig|bombillas? intelig|tiras? (de )?led intelig|iluminacion intelig|lampara intelig|luz intelig|focos? (wifi|alexa|led wifi|led rgb wifi)|'
             r'philips hue|\bhue\b (bridge|white|play|go|lightstrip)|controlador (led|rgb|de tiras? led).{0,30}(wifi|intelig|alexa|tuya)|'
             r'\bhub\b.{0,25}(zigbee|domotic|intelig|alexa|tuya|matter|hogar)|puente (hue|zigbee|wifi|intelig)|\bzigbee\b|\bmatter\b|gateway (zigbee|bluetooth|wifi)|'
             r'cortinas? (motorizada|intelig|automatica|electrica)|persianas? (motorizada|intelig|automatica|electrica)|motor (para|de) cortina|riel (para|de) cortina motorizad|'
             r'sensor(es)? (de )?(movimiento|puerta|ventana|agua|fuga|humo|temperatura|presencia|inundacion|gas)[^,]{0,30}(wifi|intelig|zigbee|alexa|tuya)|'
             r'detector(es)? .{0,25}(wifi|intelig|zigbee)|valvula (de )?(bola|de agua|de gas)?.{0,30}(wifi|intelig|tuya|alexa|zigbee)|'
             r'termostatos? (intelig|wifi|programable|digital|de pared|para calefaccion|honeywell|nest)|honeywell home|'
             r'tuya smart|smart life|control(ador)? (remoto )?universal (ir |infrarrojo )?(wifi|intelig)|boton (sos|de panico) (wifi|intelig)))'),
  ('Domótica y hogar inteligente', None, 'home')),
 # Lo mismo con la palabra suelta ('lámpara de techo inteligente wifi',
 # 'toma de pared inteligente'), pero sin tocar los aparatos que tienen
 # su propia categoría y traen luz o wifi de paso.
 (re.compile(r'^(?!(?:\S+ ){0,3}(cargador|cable|funda|soporte|adaptador|base|repuesto|montura|bateria)\b)'
             r'(?!.*(ventilador|aire acondicionado|minisplit|refrigerador|lavadora|secadora|televis|\btv\b|pantalla|monitor|laptop|celular|smartphone|tablet|reloj|smartwatch|'
             r'camara|bocina|audifono|aspiradora|\brobot\b|proyector|calentador|horno|estufa|microondas|cafetera|licuadora|freidora|purificador|humidificador|impresora|'
             r'\bmouse\b|teclado (mecanico|gamer|inalambrico)|espejo|\bpc\b|gamer|gaming|para (auto|coche|carro|moto)\b|mascota|juguete|\bdron\b|pluma|linterna|'
             r'transferencia|\bats\b|trifasic|\bsmd\b|\d+ ?pines|de tiempo|temporizador|medidor|disyuntor|breaker|circuito|\bdin\b|carril|calefactor|radiador|estufa|chimenea))'
             r'(?=.*(interruptor(es)?[^,|]{0,40}intelig|apagador(es)?[^,|]{0,40}intelig|enchufes?[^,|]{0,30}intelig|tomas? (de pared|de corriente)[^,|]{0,30}intelig|'
             r'iluminacion[^,|]{0,30}intelig|lamparas?[^,|]{0,40}intelig|\bluz[^,|]{0,40}intelig|luces[^,|]{0,40}intelig|focos?[^,|]{0,40}intelig|plafon(es)?[^,|]{0,40}intelig|'
             r'bombillas?[^,|]{0,40}intelig|tiras? (de )?led[^,|]{0,40}intelig|\bgovee\b|luces? (led )?rgbic|(intelig|rfid|huella)[^,|]{0,40}cerradura|bloqueo de puerta[^,|]{0,40}intelig|'
             r'smartcode|teclado electronico sin llave|entrada sin llave|cortinas?[^,|]{0,30}(motorizad|intelig)|persianas?[^,|]{0,30}(motorizad|intelig)|'
             r'riel (de |para )?cortinas?[^,|]{0,40}(motorizad|electric|intelig)|termostato[^,|]{0,30}(wifi|intelig)|sensor(es)?[^,|]{0,40}(wifi|zigbee|tuya|intelig)))'),
  ('Domótica y hogar inteligente', None, 'home')),
 # Iluminación no tenía red: la lámpara de techo, el foco y la luz con
 # sensor para el clóset iban a Escaleras, a Roperos o a la basura.
 (re.compile(r'^(?!.*(camara|proyector|\btv\b|monitor|linterna|luz de trabajo|para (auto|coche|carro|moto|motocicleta|bicicleta|bici)\b|de (auto|coche|carro|moto)\b|\bfaros?\b|aro de luz|ring light|letrero|pantalla led|juguete|acuario|pecera|terrario|reptil|de crecimiento|para plantas|cultivo|esterilizador|para unas|de unas|secador|\bwifi\b|alexa|tuya|'
             r'ventilador|abanico|\bpc\b|difusor|aromaterapia|humidificador|bocina|altavoz|speaker|fotografia|\bvideos?\b|softbox|estudio|mascota|perro|\bgato\b|collar|casco|\bdron\b))'
             r'^(?!(?:\S+ ){0,3}(interruptor|apagador|placa|toma|enchufe|sensor|controlador|regulador|atenuador|dimmer|temporizador|soporte|base|cable|adaptador|pantalla|difusor|reloj)\b)'
             r'^(?:\S+ ){0,3}(?<!con )(?<!y )(luz|luces|lampara|lamparas|foco|focos|bombilla|bombillas|tiras? (de )?led|tiras? (de )?luz|iluminacion|plafon(es)?|candil(es)?|apliques?|arbotantes?|luminarias?|reflector(es)? led|farol(es)?|panel(es)? led|barras? de luz|luz nocturna|lampara solar|luces solares|kit de iluminacion|tubos? led|riel de iluminacion|lampara colgante|luces? colgantes?|focos? led|lamparas? de (techo|pared|piso|pie|mesa|escritorio|buro|noche))\b'),
  ('Iluminación', None, 'lightbulb')),
 # La cerradura mecánica y el candado: no eran de nadie y acababan en
 # Teclados ("con teclado"), en Roperos ("para armario") o en Componentes
 # ("de gabinete").
 (re.compile(r'^(?!.*(intelig|\bwifi\b|biometric|huella|bluetooth|\bapp\b|tuya|alexa|bicicleta|\bbici\b|\bmoto\b|maleta|equipaje|mascota|laptop|notebook|casillero|para auto|de auto|coche|volante))'
             r'(?:\S+ ){0,4}(cerraduras?|cerrojos?|candados?|chapas?|picaportes?|pasador(es)? de puerta|aldabas?|cerradura de gabinete|manijas? (de|para|con) (puerta|cerradura))\b'),
  ('Herramientas', 'Cerraduras y candados', 'wrench')),
 # Material eléctrico: el temporizador de pared, el interruptor de
 # transferencia, el disyuntor y el contacto de pared. Sin esto el
 # temporizador entraba a Componentes por "ventilador" y el botón
 # momentáneo "Auto Reset" a Autos.
 (re.compile(r'^(?!.*(\bpc\b|gamer|gaming|para (auto|coche|carro|moto)\b|bicicleta|juguete))'
             r'(?:\S+ ){0,4}(temporizador(es)? (programable|de pared|de enchufe|de riego|de luz|electrico)|'
             r'interruptores? tactiles|circuit breaker|extensor de (enchufe|toma)|tomas? (usb|de pared|de corriente|multiples?)|receptaculos?|placas? (para|de) (interruptor|apagador|contacto)|\bgfci\b|medidor de potencia|'
             r'interruptor(es)? (de paso|de \d polos?|termico|selector|giratorio|de llave|de transferencia|automatico|termomagnetico|diferencial|de circuito|de tiempo|horario|crepuscular|de flotador|de presion|de palanca|de cuchilla|'
             r'sencillo|doble|triple|de escalera|de 3 vias|de pared|de luz|con sensor|de boton|de encendido|basculante|momentaneo|de pie|de llave|de nivel|magnetico|de limite)|'
             r'controlador ats|\bats\b|disyuntor(es)?|\bbreakers?\b|contactor(es)?|\breles?\b|relevador(es)?|caja de distribucion|tablero electrico|centro de carga|pastillas? termomagnetica|'
             r'tipo carril|riel din|regleta (electrica|de conexion|de terminales)|supresor de picos|protector (contra|de) sobretension|extension electrica|'
             r'clavijas?|tomacorrientes?|contactos? (duplex|de pared|dobles?|sencillos?|con usb)|placas? (de pared|para contacto|de interruptor)|'
             r'apagador(es)? (sencillo|doble|triple|de pared|de escalera|con placa)|atenuador(es)?|\bdimmer\b|fotocelda|'
             r'timbres? (inalambrico|de puerta|para puerta|de pared|electrico)|controlador(es)? de temperatura|termostato digital|termostato programable|'
             r'boton(es)? (momentaneo|pulsador|de arranque|de paro|de emergencia)|pulsador(es)?|cable (thw|calibre|electrico|duplex)|canaleta|fusibles?|portafusibles?|'
             r'cinta aislante|conector(es)? wago|terminales electricas|voltimetro|amperimetro|medidor de (consumo|energia|voltaje)|\bwattimetro\b)\b'),
  ('Herramientas', 'Material eléctrico', 'wrench')),
 # El hub USB y la docking station: el catálogo los tenía en Monitores.
 (re.compile(r'\bhubs? usb\b|concentrador usb|usb hub|docking station|estacion de acoplamiento|base de conexion usb|adaptador multipuerto|hub (usb-?c|tipo c)'),
  ('Componentes y accesorios de PC', 'Accesorios', 'cpu')),
 # Punto de venta: la caja registradora, la terminal POS, el cajón de
 # dinero y la impresora de tickets iban a Tabletas, Celulares o AiO.
 (re.compile(r'terminal (pos|de punto de venta|de cobro|de pago|para tarjetas)|\bpos\b (terminal|todo en uno|tactil|android|de doble pantalla)|'
             r'caja registradora|cajas registradoras|cajon (de dinero|portamonedas|de efectivo|monedero)|impresora (termica )?de (tickets|recibos)|miniprinter|'
             r'impresora termica.{0,30}(58|80) ?mm|escaner de codigos? de barras|lector de codigos? de barras|lector de tarjetas|\btpv\b|'
             r'maquina expendedora|rollos? termicos?|papel termico|terminal de (cobro|pago)|\bpda\b.{0,50}(escaner|codigo de barras|colector)|colector de datos|'
             r'sistema (de )?punto de venta|mercado pago point|punto de venta'),
  ('Equipo comercial', 'Punto de venta', 'factory')),
 # Mobiliario comercial: el exhibidor, el mostrador y la recepción.
 (re.compile(r'^(?!.*(refriger|congel|vitrina|\bfrio\b|\bfria\b|celular|telefono|tablet|pastel|postres|cupcake|torta|joyeria|anillos|relojes|figuras|funko|munec|juguete|estatua|statue|adorno|decoraci|altura de mostrador|mesita|buro|de noche|antipolvo|protector|escritorio de))'
             r'(?=.*(exhibidor(es)?|estante(s)? de exhibicion|organizador(es)? (de|para) (cigarrillos|caramelos|dulces|chicles|tabaco)|'
             r'mostrador(es)? (de|para) (tienda|recepcion|caja|exhibicion|venta|cristal|vidrio|madera|negocio)|mueble mostrador|mostrador (comercial|de recepcion)|^(?:\S+ ){0,2}mostrador(es)?\b|mobiliario (de|para|para la) (recepcion|comercial|tienda|restaurante)|'
             r'(mostrador|mesa|escritorio|sillas?|sillon(es)?|sofas?|bancos?|bancas?|mobiliario|area|sala|muebles?) de recepcion|recepcion (de|para) (oficina|hotel|clinica|consultorio)|maniqui|\bgondolas?\b|\banaquel(es)?\b|\bcasilleros?\b|\btaquillas?\b|\blockers?\b|banco de barberia|silla de barbero|estacion de manicura|'
             r'estanterias? (moviles|movil|metalica (industrial|de carga)|para (almacen|bodega|tienda))|estantes? (de acero( inoxidable)?|metalicos?|de alambre|cromados?|industrial(es)?).{0,50}(niveles|garaje|almacen|bodega|lbs|kg|comercial|cocina|restaurante|nsf|pared)))'),
  ('Equipo comercial', 'Mobiliario', 'factory')),
 # Cocina industrial: el dispensador de bebidas, la máquina de hielo, la
 # freidora comercial y la mesa de trabajo de acero inoxidable.
 (re.compile(r'^(?!.*(juguete|de imitacion|para ninos|\bpc\b|gamer))'
             r'(?=.*(dispensador(es)? de (bebidas|jugo|cerveza|agua fria|cafe comercial)|maquina (comercial )?(de|para) (hacer )?(hielo|helados?|helado suave|yogur|palomitas|algodon de azucar|crepas|churros|tortillas|hot ?dogs|nieve|raspados|granizados|donas|malteadas|cafe comercial)|'
             r'trituradora de hielo|freidora (industrial|comercial|de papas)|campanas? (industrial|comercial|de extraccion industrial)|campanas? (para |de )?cocinas? (industrial|comercial)|peladora|maquina comercial (de|para)|enfriador (de|para) (vasos|bebidas|copas|latas)|enfriador rapido|mesas? (de )?(taller|trabajo|preparacion)( de cocina)? .{0,30}acero|'
             r'estufa industrial|parrilla industrial|plancha industrial|bano maria (electrico|industrial|comercial)|fermentador|amasadora|batidora industrial|laminadora|rebanadora (de carne|de embutidos|comercial|industrial)|'
             r'cortadora de (carne|embutidos|vegetales|papas)|licuadora industrial|olla (industrial|arrocera comercial)|cazos? (de acero|para carnitas|carnitero)|comal industrial|marmita|'
             r'extractor industrial|mesa de (trabajo|preparacion) de acero inoxidable|mesa de acero inoxidable|fregadero (industrial|comercial)|tarja (industrial|de acero inoxidable)|'
             r'exhibidor (de comida|caliente)|calentador de (alimentos|comida) comercial|mantenedor de calor|asador (de pollos|comercial|industrial)|tostadora comercial|'
             r'maquina (de |para )?(sellar|sellado|empacar al vacio) (comercial|industrial)|refresquera|jarra refresquera|chocomilera|cafetera (industrial|comercial|percoladora)))'),
  ('Equipo comercial', 'Cocina industrial', 'factory')),
 # El carro de servicio y el carrito de cocina: no son un auto.
 (re.compile(r'^(?!.*(bebe|\bnino|munec|juguete|\bgolf\b|herramienta|cargador|de carga|celular|\brc\b|control remoto|ventilador|para (el )?carro\b|de(l)? carro\b|coche|\bauto\b|automovil))'
             r'(?:\S+ ){0,3}(carros?|carritos?|carretilla de servicio) (de |para |con |multifuncion|utilitario|rodante|movil|auxiliar|organizador|metalico|plegable|portatil|industrial|bar\b|barra|multiusos|almacenamiento|servicio|utilidad)'
             r'(?!.*(compras|mandado|supermercado|lavanderia|ropa|playa|jardin|ninos))'),
  ('Equipo comercial', 'Carros de servicio', 'factory')),
 (re.compile(r'^(?!.*(bebe|\bnino|munec|juguete|\bgolf\b|herramienta|cargador|de carga|celular|\brc\b|control remoto|ventilador|para (el )?carro\b|de(l)? carro\b|coche|\bauto\b|automovil))'
             r'(?:\S+ ){0,3}(carros?|carritos?) (de |para |con |multifuncion|utilitario|rodante|movil|auxiliar|organizador|metalico|plegable|portatil|industrial|bar\b|barra|multiusos|almacenamiento|servicio|utilidad)'
             r'(?=.*(compras|mandado|supermercado|lavanderia|ropa|playa|jardin))'),
  ('Otros', 'Organización del hogar', 'box')),
 # Impresoras: la de sublimación va con el equipo comercial, el cabezal y
 # la tinta con los consumibles, y la de casa por su tecnología.
 (re.compile(r'^(?!.*(cabezal|tinta|papel|cubierta|funda|cover))(?=.*(impresoras? (de |para )?sublimacion|impresora.{0,40}sublimaci|sublimaci.{0,40}impresora))'),
  ('Equipo comercial', 'Impresoras de sublimación', 'factory')),
 (re.compile(r'^(?!.*(3d|etiquetadora|rotuladora|\bdymo\b|\bbrother p-?touch\b))'
             r'(?=.*(tinta (de |para )?sublimacion|papel (de |para )?sublimacion|cabezal(es)? de impresion|cabezal impresor|cabezal (epson|canon|hp)|'
             r'impresora (multifuncional|de inyeccion|de tinta|laser|ecotank|termica|fotografica|portatil|inalambrica|wifi|a color|monocromatica|de etiquetas|de fotos|de tanque)|'
             r'\becotank\b|\bpixma\b|\bdeskjet\b|\blaserjet\b|\bofficejet\b|\bimageclass\b|\bbrother (dcp|mfc|hl)-|\bepson (l\d{3,4}|et-\d|wf-\d|xp-\d)|\bcanon (g\d{4}|ts\d{4}|mg\d{4}|mx\d{3})|'
             r'multifuncional (epson|hp|canon|brother|xerox|kyocera|ricoh)|impresora (epson|hp|canon|brother|xerox|kyocera|ricoh)))'),
  ('Impresoras', None, 'printer')),
 # Plomería: el fregadero, el grifo y el lavabo. Sin la guarda, el filtro
 # para grifo seguiría en Purificadores de agua, que es donde va.
 (re.compile(r'^(?!.*(filtro|purificador|osmosis|juguete|para (auto|coche|carro)|de imitacion))'
             r'(?:\S+ ){0,2}(fregaderos?|tarjas?|grifos?|griferia|llaves? (mezcladora|monomando|de cocina|de lavabo|para fregadero)|mezcladoras? (de|para) (cocina|lavabo|bano|regadera)|monomando|regaderas?|lavabos?|inodoros?|\bwc\b|bides?|taza de bano|sanitarios?|mingitorios?)\b'),
  ('Herramientas', 'Plomería', 'wrench')),
 (re.compile(r'toallas? de cocina|secador(es)? de cocina|trapos? de cocina|panos? de cocina'),
  ('Blancos y ropa de cama', 'Toallas', 'pillow')),
 # El barril de arroz es un contenedor de cocina.
 (re.compile(r'barril(es)? (de|para) arroz|contenedor(es)? (de|para) (arroz|granos|cereal|harina)|dispensador(es)? de (arroz|cereal|granos|harina)|cubo (de|para) arroz|caja de arroz|caja (refrigerada|aislante|termica) (para|for) alimentos|hielera|cubos? (de |para )?hielo|cubitera|contenedor de hielo'),
  ('Cocina y comedor', 'Contenedores', 'kitchen')),
 # El espejo: el de maquillaje con la belleza, el de baño y el de pared
 # con la decoración.
 (re.compile(r'^(?!.*(retrovisor|\bauto\b|coche|carro|\bmoto\b|bicicleta|dental|telescopio|camara|lente|para (puerta|ventana) de|convexo|de inspeccion))'
             r'(?!.*(de bano|para bano|antivaho|retroiluminado|cuerpo entero|de pared))'
             r'(?:\S+ ){0,2}espejos?\b(?=.*(maquillaje|tocador|cosmetic|aumento|vanidad|de mano|compacto))'),
  ('Belleza y cuidado personal', 'Maquillaje', 'sparkles')),
 (re.compile(r'^(?!.*(retrovisor|\bauto\b|coche|carro|\bmoto\b|bicicleta|dental|telescopio|camara|lente|convexo|de inspeccion|de seguridad|de trafico))'
             r'(?:\S+ ){0,2}espejos?\b'),
  ('Decoración de hogar y jardín', 'Espejos', 'vase')),
 (re.compile(r'^(?!.*(refrigerador(es)?|enfriador|ventilador) (de |para )?(telefonos?|celular|movil))'
             # La refacción y el accesorio del refri no son el refri.
             r'^(?!(?:\S+ ){0,3}(cortina|evaporador|junta|termostato|motor|compresor|filtro|sensor|condensador|ventilador|rejilla|repuesto|refaccion|estante|cajon|bandeja|manija|tira|empaque|burlete|cubierta|funda|parasol|control|tarjeta|placa|puerta enfriadora|imanes?|iman|organizador|contenedor|termometro|kit|tapete|alfombrilla|lampara|foco|bombilla|bisagra|jaladera|pedal|cerradura|candado|soporte|base|rodillo|rueda|tubo|valvula|capacitor|arrancador|relevador|rele|fusible|cable|deflector|charola|cesta|canasta|divisor|separador|panel|sello|goma|puerta|tiras?)\b)'
             r'(?!.*(condensador|evaporador|compresor (embraco|tecumseh|danfoss|de refrigeracion|frigorifico|para refrigerador|rotativo|hermetico)|termostato|burlete|empaque|junta (magnetica|de puerta)|refaccion|repuesto|reemplazo|pieza de recambio|motor (de|del) ventilador|ventilador de refrigeracion|cortina|tira de sellado|tiras? de pvc|puerta enfriadora|desodorizante|purificador para|refrigerador de aire|aire acondicionado|enfriador de aire|maquina (de|para) (hacer )?helado|humidor))'
             r'(?=.*(\brefrigerador|\bfrigobar|\bnevera\b|cava de vino|enfriador de vino))'),
  ('Refrigeradores', None, 'fridge')),
 # Purificadores de agua, después de los filtros de refrigerador: los dos
 # dicen "filtro de agua" y el del refri no purifica nada, repone una
 # pieza. La subcategoría del catálogo guarda juntos el aparato y sus
 # cartuchos (los Hydrofast HF03, los JIMMY R9), así que el kit
 # mineralizador y el filtro suelto van con los equipos de ósmosis.
 # El irrigador trae "Filtro de Agua" en el título y caía en purificadores.
 (re.compile(r'irrigador (dental|bucal|oral)|water ?flosser'),
  ('Salud', 'Cuidado dental', 'heart-pulse')),
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
 # La montura de cámara: cabeza de bola, brazo mágico, placa de liberación
 # rápida, clip de manubrio "para cámara de acción". Caían en
 # Refacciones/Otros por el "tornillo de 1/4" (41 en la captura del
 # 16-sep) y esa subcategoría ni está registrada, así que
 # add_amazon_standalone.py las habría descartado en silencio.
 #
 # La montura tiene que ABRIR el título y el título tiene que nombrar una
 # cámara de verdad. La primera versión pedía las dos palabras en
 # cualquier parte y la regresión la tiró: con "adaptador" en el título y
 # "cámara" cien caracteres después entraban el adaptador de enchufe de
 # viaje, la batería de Starlink, el poste para panel solar, el tripié de
 # bocinas, un teléfono Doro y el i12Pro "cámara triple".
 (re.compile(r'^(?!.*(celular|telefono|smartphone|\btablet\b|tableta|bocina|bafle|panel(es)? solar|'
             r'\bsolar\b|enchufe|de viaje|starlink|scooter|patinete|timbre|microscopio|monitor|'
             r'\bring\b|seguridad|\bpara (silla|sofa|mesa|cama)))'
             r'^(?:\S+ ){0,3}(soporte|adaptador|montaje|cabeza de bola|cabezal de bola|brazo magico|'
             r'brazo articulado|placa de liberacion|abrazadera|monopie|kit de montaje|clip de hebilla|'
             r'marco (protector|de proteccion))\b'
             r'(?=.*(camara de accion|camara deportiva|\bgopro\b|insta ?360|dji (osmo|action)|'
             r'\btripode\b|\btripie\b|\bdslr\b|zapata (caliente|fria)|\bhero ?\d|\bakaso\b|\bsjcam\b))'),
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
             r'car ?radio|carplay|android auto|doble din|2 ?din|autoestereo|estereo (para|de) (coche|auto|carro)|bicicleta|triciclo|motocicleta|casillero|persiana|cortina|caja registradora|punto de venta|terminal (pos|de cobro|de pago)|\bpos\b|\btpv\b|colector de datos|\bpda\b|de repuesto|refaccion|reemplazo|laptop|notebook|macbook|'
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
 # Red de Juegos de mesa. El auditor de cobertura la daba en 0% con 4,147
 # fichas y sub_juego_mesa() escrito: de 300 de muestra, 197 no enganchaban
 # nada y 77 se iban a Muebles.
 #
 # "Juego de mesa" es la trampa: en español nombra el juego de tablero Y
 # el juego de MUEBLES. "Juego de Mesas Auxiliares Nido", "Juego de mesa y
 # silla infantil" y "Juego de Mesa y 2 Bancos" entraban como juegos --337
 # fichas--. Se separan por el borde de palabra ("juego de mesa\b" no casa
 # con "juego de mesaS") y porque el juego de muebles trae asientos y
 # medidas: silla, banco, "110 x 65 x 75 cm".
 #
 # "Dados" tampoco sirve de disparador: en México el dado de impacto es
 # una herramienta, y por eso el juego de dados se reconoce por el juego
 # de rol, no por la palabra suelta.
 (re.compile(
             r'^(?!.*(tablero de dardos|tablero (electronico|de control|de circuito|arduino|de anuncios)|'
             r'\bdardos?\b|mesa de (centro|comedor|noche|trabajo|billar|ping ?pong)|'
             r'juego de (sabanas|toallas|herramientas|llaves|desarmador|dados de impacto|copas|vasos|platos)|'
             r'\bdado de impacto\b|\bmatraca\b|\bsocket\b|\bmilimetric|\bpulgada\b|\bllave de impacto\b|'
             r'\bperro|\bgato\b|mascota|'
             r'\bconsola\b|\bplaystation\b|\bxbox\b|\bnintendo\b|\bsteam\b|videojuego|'
             r'\bdisfraz\b|\bpinata\b|\bglobo|'
             r'maquina (de|para) coser|\bpuzzle mat\b|tapete de goma|'
             # "Juego de mesa" es también el juego de MUEBLES: mesas auxiliares,
             # mesa nido, mesa y sillas. La silla lo delata.
             r'\bsilla|mesas? (auxiliar|de centro|nido|lateral)|\bnogal\b|\bmuebles\b|'
             r'\blibro\b|\blibros\b|'
             r'figura de accion|\bmaqueta\b|kit de montaje|'
             r'toys for children|early education|kindergarten|educativ|'
             # El juego de muebles trae medidas y asientos; el de tablero, no.
             r'mesa de actividades|\bbancos?\b|\d+ ?x ?\d+ ?x ?\d+ ?cm|\balmacenamiento\b|'
             r'\bcomedor\b|\bjardin\b|\bterraza\b|ping ?pong|\bbillar\b|futbolito|\brepuesto\b))'
             r'(?=.*('
             r'rompecabeza|\bpuzzle\b|\bpuzle\b|'
             r'juego de mesa\b|juegos de mesa\b|\bboard game\b|'
             r'\bajedrez\b|\bchess\b|\bdomino\b|\bbackgammon\b|\bdamas chinas\b|'
             r'\bnaipes\b|\bbaraja\b|cartas coleccionables|juego de cartas|\bmazo de cartas\b|'
             r'\bmonopol|\bjenga\b|\bscrabble\b|\bloteria mexicana\b|\bmemorama\b|'
             r'serpientes y escaleras|\bturista mundial\b|\bcatan\b|\bdixit\b|\bcarcassonne\b|'
             r'\bcalabozos y dragones\b|\bd&d\b|juego de rol|\bwarhammer\b|'
             r'\bbingo\b|\bmahjong\b|\bmah-?jongg\b|\btimbiriche\b|'
             r'\bpoker\b.{0,20}(fichas|set|mesa)|fichas de poker'
             r'))'),
  ('Juegos de mesa', None, 'dice')),
 # Red de Joyería y bisutería. Otra de las que el auditor de cobertura
 # (scripts/auditar_cobertura_clasificador.py) marcó en 0%: 4,760 fichas,
 # once subcategorías, sub_joyeria() escrito y ninguna regla que llegara.
 # De una muestra de 300, 295 no enganchaban NADA -- ni el "Anillo Promesa
 # Oro 14K" ni el "Reloj Casio MTP-1375D".
 #
 # Casi todas las palabras de joyería nombran otra cosa en otro lado, y
 # por eso la guarda es larga: el "collar" del perro, el "anillo" de la
 # toalla y el del reposabrazos, la "pulsera" de actividad, el "reloj de
 # pared", el anillo de retención de la caja de herramientas, la flauta
 # "de plata de ley" y el anillo calefactor de cerámica.
 #
 # El oro como COLOR no cuenta: "Laptop HP oro rosa" y "iPhone oro" son
 # 34 fichas que entraban por decir "oro". Solo cuenta con quilates
 # ("oro 14k"), chapado o plata 925.
 (re.compile(
             r'^(?!.*(\bperro|\bgato\b|\bgatos\b|mascota|\bcanino|\bfelino|\bcachorro|'
             r'smart ?watch|reloj intelig|apple watch|galaxy watch|banda de actividad|'
             # El reloj de pulsera SÍ es joyería (2,345 fichas del catálogo),
             # pero el inteligente tiene su propia categoría y va antes que
             # nada: cualquier seña de smartwatch descalifica.
             r'\bwatch\b|amazfit|\bgarmin\b|\bfitbit\b|smartband|\bsmart\b|'
             r'\bgps\b|podometro|\bspo2\b|frecuencia cardiaca|'
             r'pulsera de actividad|fitness tracker|\bmi band\b|'
             r'reloj (de pared|de mesa|de arena|despertador|checador)|\bdespertador\b|'
             r'\bmagsafe\b|magnetico para (celular|telefono)|anillo (magnetico|de piston|de goma|de sellado)|'
             r'\bo-?ring\b|\bempaque\b|\bcadena de (motosierra|bicicleta|moto|distribucion)\b|'
             r'\bherramienta|\btaladro\b|\bllave (allen|inglesa)\b|'
             r'\bdisfraz\b|\bjuguete\b|\bpeluche\b|'
             r'\btoalla|\bsilla\b|reposabrazos|reposapies|\bpinza|desarmador|'
             # El aparato que NOMBRA una joya no es una joya: los "Auriculares
             # Bluetooth con Aretes Desmontables", los "Anillos Espaciadores
             # para Bocinas de Coche", los "Altavoces de Collar" y las gafas
             # de sol con bocina. El plural importa: "\bbocina\b" no casa con
             # "bocinas" ni "\baltavoz" con "altavoces", y por eso se colaban.
             r'anillo(s)? de retencion|\bbocinas?\b|altavo(z|ces)|\bcables?\b|\bconector|\bmp3\b|'
             r'\bcargador|base de carga|\bventilador|'
             # Los "Anillos de Gimnasia" olímpicos cuelgan de una barra.
             r'gimnasi|gimnastic|\bdominadas?\b|anillos de ejercicio|'
             r'\braqueta|\btenis\b|\bdardos?\b|\bdiana\b|\bkayak\b|\bmancuerna|\bexpansor|\bmuelle|'
             r'\bmicroscopio\b|\blupa\b|\btocador\b|\btaburete\b|\bnintendo\b|\bswitch\b|wall mount|\bmontaje\b|arcilla|'
             r'auricular|audifono|\btws\b|bluetooth|\bmicrofono\b|manos libres|'
             r'manta electrica|\balmohadilla\b|'
             r'\byoga\b|\bpilates\b|\bpesas\b|\btobillo\b|\bmuneca\b|'
             r'\blaptop\b|\bnotebook\b|\bcelular\b|\btablet|'
             r'\bllave\b|anillo cerrado|'
             r'\bflauta\b|\bclarinete\b|instrumento musical|\bsaxofon|\btrompeta\b|\bguitarra\b|'
             r'\bextensible\b|correa para reloj|banda para reloj|'
             r'\bbomba\b|cama elastica|\btrampolin\b|'
             r'anillo (calefactor|calentador)|anillo intelig|smart ring|\boura\b))'
             r'(?=.*('
             r'\banillo(s)?\b|\bsortija|\barete(s)?\b|\barracada|\bbroquel|'
             r'\bcollar(es)?\b|\bgargantilla|\bpulsera(s)?\b|\bbrazalete|\besclava\b|'
             r'\bdije(s)?\b|\bcharm(s)?\b|\breloj(es)?\b|'
             r'\bjoyero\b|caja (para|de) joyas|organizador de joyas|'
             r'\barras\b|lentes de sol|gafas de sol|'
             r'\bbisuteria\b|\bjoyeria\b|'
             r'oro de \d{1,2} ?k\b|\b(10|14|18|22|24) ?k(ilates)?\b (de )?oro|oro \d{1,2}k\b|'
             r'chapa(do)? (en|de) oro|banado en oro|plata (925|esterlina|de ley)|'
             r'\bzirconia\b|\bcirconita\b'
             r'))'),
  ('Joyería y bisutería', None, 'ring')),
 # Red de Blancos y ropa de cama. Cuarta categoría con el mismo agujero
 # que Mascotas, Deportes y fitness y Belleza: diez subcategorías, 4,221
 # fichas, sub_blancos() completo... y una sola regla de categoría, la de
 # las almohadas. Medido sobre la captura de 11,431 anuncios de blancos del
 # 17-sep: de 11,354 nuevos entraban 3,975 y casi todos mal --1,202
 # protectores de colchón como Muebles/Colchones, 689 como Muebles/Camas,
 # 492 mantas eléctricas como Climatización/Calefactores-- y 6,522 se
 # descartaban.
 #
 # Va ANTES que Climatización porque la manta eléctrica es ropa de cama, no
 # un calefactor: el catálogo ya tiene "Cobijas eléctricas".
 #
 # "Almohada" pide ir en la cabeza del título, como ya hacía sub_blancos():
 # suelta, se llevaba 2,876 colchones "Restonic Matrimonial CON 2
 # ALMOHADAS" -- la almohada de regalo no convierte al colchón en blanco de
 # cama, igual que el balón de regalo no convertía al colchón en artículo
 # deportivo.
 (re.compile(r'^(?!.*(\bperro|\bgato\b|mascota|\bcanino|\bfelino|'
             r'para (auto|coche|carro|camioneta|vehiculo)|asiento de auto|'
             r'\byoga\b|\bpilates\b|\bcamping\b|\bpicnic\b|manta termica de emergencia|'
             r'inflable|\bcortauna|\btoallita|papel higienico|'
             r'\bsoldad|\bmanta de vidrio\b|fibra de vidrio|'
             # La almohada de viaje va en Maletas, la de lactancia en Bebés,
             # la de masaje es un masajeador, la de peluche un peluche y la
             # "almohada para tablet" un soporte. Y la manta del MOTOR
             # calienta un coche, no una cama.
             r'\bviaje\b|\bcervical\b|\blumbar\b|lactancia|\bbebes?\b|\bmasaje\b|'
             r'altavoz|\bbocina\b|bluetooth|\bsofa ?cama\b|\bfuton\b|silla gamer|'
             r'\btablet|\bipad\b|\bkindle\b|\bpeluche\b|\bmotor\b|\btoallero\b|'
             # La mesa calefactora japonesa (kotatsu) se vende CON edredón y
             # sigue siendo un calefactor; la manta térmica del tambor de
             # aceite calienta un bidón; las gafas de natación "7 en 1"
             # traen toalla en el paquete; y "topper" es además el adorno
             # del pastel, no solo el sobrecolchón.
             r'mesa calefactora|\btatami\b|\bkotatsu\b|'
             r'\btambor\b|\bbarril\b|\bdrum\b|'
             r'\bgafas\b|\bgoggles\b|\banteojos\b|'
             r'\bpastel\b|\bcake\b|\btorta\b|cumpleanos|'
             r'\bcompresa\b|'
             # "Topper" es también el postizo de pelo, después de haber sido
             # el adorno del pastel. Y la almohadilla térmica de alivio de
             # dolor, el masajeador con forma de almohada, las "sábanas de
             # máscara facial" y el poncho de surf no son ropa de cama.
             r'\bcabello\b|\bhair\b|\bpostizo\b|\bpeluca|'
             r'almohadilla termica|alivio de dolor|masajeador|'
             r'mascara facial|mascarilla facial|\bponcho\b|'
             r'supervivencia|\bemergencia\b|\bmylar\b|campismo))'
             # El colchón y la cabecera son Muebles; lo que los CUBRE, no. Por
             # eso "colchón" descalifica solo si ABRE el título: con la guarda
             # a tres palabras, "Protector DE COLCHÓN Acolchado" se
             # descalificaba a sí mismo y 917 protectores acababan en
             # Muebles/Colchones y Refacciones. "Colchoneta" no lleva borde de
             # palabra tras "colchon" y pasa, que es lo que queremos: un
             # topper es ropa de cama.
             r'(?!colchon(es)?\b)'
             r'(?!(?:\S+ ){0,2}(cama box|box spring|cabecera)\b)'
             r'(?=.*('
             r'protector(es)? (de |para )?colchon|cubre ?colchon|funda (de|para) colchon|sobrecolchon|'
             r'\bpillow ?top\b|\btopper\b|protector de almohada|'
             r'\bsabana|juego de sabanas|ropa de cama|funda(s)? (de|para) almohada|'
             r'\bedredon|\bcolcha\b|\bquilt\b|\bduvet\b|cubrecama|\bcobertor\b|'
             r'\bcobija|\bfrazada|manta (electrica|polar|de sherpa|de franela|para cama)|'
             r'^(?:\S+ ){0,3}almohadas?\b|'
             r'toalla(s)? (de|para) (bano|playa|cuerpo|mano)|\btoallon\b|juego de toallas|'
             r'tapete (de|para) bano|\balfombra de bano\b|'
             r'funda (para|de) (sofa|sillon|mueble)|cubre ?sofa|cubre ?sillon'
             r'))'),
  ('Blancos y ropa de cama', None, 'pillow')),
 # Red de Climatización, adelantada a propósito.
 #
 # La captura de 12,705 anuncios de clima entró casi entera en el lugar
 # equivocado: 3,420 ventiladores de techo, centrífugos industriales y
 # aires acondicionados portátiles se fueron a Componentes de PC (los caza
 # la palabra "ventilador"), 91 minisplits y ventiladores de torre a
 # Bocinas inteligentes (por decir "Alexa"), 74 deshumidificadores a
 # Roperos (por decir "closet") y 78 calentadores y purificadores a
 # Escritorios (por decir "de escritorio"). Ninguna de esas cuatro reglas
 # está mal: el aparato de clima las menciona de paso y ellas van antes.
 #
 # Por eso esta va ARRIBA y no de red al final, la misma excepción que
 # Suplementos y por el mismo motivo: no se apoya en palabras anchas sino
 # en el sustantivo que ABRE el título. Un componente de PC no se anuncia
 # como "Ventilador de techo" ni "Minisplit", y el que sí lo hace
 # ("Ventilador Corsair iCue QL140 RGB") lleva alguna de las palabras de
 # la guarda. La subcategoría la pone sub_clima.
 (re.compile(r'^(?!.*(\bcpu\b|procesador|gabinete|\bpc\b|\bitx\b|socket|\bam[45]\b|\blga\b|'
             r'disipador|\bargb\b|\brgb\b|\bpwm\b|noctua|chasis|tarjeta grafica|\bgpu\b|placa base|'
             r'base (enfriadora|enfriador|enfriamiento|refrigerante)|sin ventilador|'
             r'ps[45]\b|playstation|xbox|steam deck|consola|nintendo|\bdock\b|'
             r'holograma|holografic|publicida|plumero|soldadora|motor rc|'
             r'(para|de) camara|radiador de motor|\boem\b|\brele\b|'
             # El ventilador de gabinete se vende por su medida en milímetros
             # y muchos no dicen "PC" ni "RGB" en el título: "Acteck Ventilador
             # POLAR EG VG120 120mm 1700RPM Molex", "NZXT F120Q Ventilador 120
             # mm". Las medidas son las de la industria; el ventilador de
             # habitación se anuncia en pulgadas.
             r'\b(80|92|120|140|200|240|280|360) ?mm\b|'
             r'ventilador de refrigeracion de radiador|radiador compatible|'
             r'\brv\b|camion|camper|caravana|motorhome|tablero|autobus|remolque|'
             r'para (auto|coche|carro|automovil|vehiculo|moto)|desempanador|'
             r'calentador de agua|boiler|calenton|purificador de agua|'
             r'milwaukee|dewalt|ridgid|makita|ryobi|\bm1[28]\b|'
             r'(para|de) (celular|telefono|movil|laptop|portatil de)))'
             # Estas otras solo descalifican si llegan TEMPRANO. El anuncio de
             # un deshumidificador o de un purificador LEVOIT nombra al final
             # "caspa de mascotas" y "olor de perro", y con la guarda suelta se
             # perdían enteros; el sillón de masaje con calefacción, en cambio,
             # abre diciendo lo que es.
             r'(?!.{0,55}(masaje|reclinable|sillon|\bsofa\b|colchon|freidora|'
             r'perro|\bgato\b|mascota|(para|de) camara))'
             # La pieza suelta no es el aparato: el resistor, el embrague y
             # la cubierta del ventilador son refacciones, y "Luz LED para
             # Ventilador de Techo" es iluminación. "luz" pide preposición
             # detrás para no llevarse "minka-aire, luz Wave, Ventilador de techo".
             r'(?!(?:\S+ ){0,2}(interruptor|embrague|compresor|motor|aspas?|difusor|capacitor|'
             r'termostato|rejilla|repuesto|soporte|filtro|mando|control(ador)?|resistor|cubierta|secador)\b)'
             r'(?!(?:\S+ ){0,2}(luz|luces|kit) (led )?(de|para)\b)'
             r'(?:(?:\S+ ){0,4}(ventilador(es)?|abanico|aire acondicionado|acondicionador(es)? de aire|'
             r'minisplit|mini split|climatizador(es)?|enfriador (de aire|evaporativo)|'
             r'calefactor(es)?|deshumidificador(es)?|deshumificador|humidificador(es)?|'
             r'purificador(es)? (de )?aire|radiador (lleno de aceite|de aceite)|'
             r'calentador(es)? (de ambiente|de pared|de patio|de espacio|de interiores|de habitacion|'
             r'de escritorio|electrico|ceramico|infrarrojo|de cuarzo|halogeno|de torre))\b'
             # Estas nombran el aparato aunque lleguen tarde en el título.
             r'|(?=.*(ventilador(es)? de techo|ceiling fan|minisplit|mini split|abanico de techo|'
             r'aire acondicionado|acondicionador de aire)))'),
  ('Climatización', None, 'snowflake')),
 # La bocina, con las cuatro maneras de nombrarla que usa esta captura:
 # "bocina", "bafle", "altavoz/altavoces" y la máquina de cantar karaoke,
 # que el catálogo ya tiene entre las bocinas.
 (re.compile(r'\becho (pop|dot|show|studio|hub)\b|amazon echo|google nest|homepod|'
             r'\bnest (audio|mini|hub)\b|bocina intelig|altavoz intelig'),
  ('Domótica y hogar inteligente', 'Bocinas inteligentes', 'speaker')),
 (re.compile(r'cerradura (inteligente|electronica|digital|biometrica)|smart lock'),
  ('Domótica y hogar inteligente', 'Cerraduras inteligentes', 'lock')),
 # Solo la almohada de cama: la de viaje va en Maletas y la de bebé en
 # Bebés, y las dos se llaman almohada.
 (re.compile(r'^(?!.*(viaje|cuello|cervical|masaj|bebe|lactancia|embarazo|inflable))'
             # "Colchón Matrimonial Monaco+ Almohada+ Protector+ Sábanas" es
             # un colchón con almohada de regalo: el colchón abre el título y
             # la almohada llega tercera, dentro de las tres palabras que esta
             # regla mira.
             r'(?!colchon(es)?\b)'
             r'(?:\S+ ){0,3}almohadas?\b'),
  ('Blancos y ropa de cama', 'Almohadas', 'pillow')),
 (re.compile(r'^(?!(?:\S+ ){0,2}(cables? (auxiliar|usb|micro|divisor|de carga|tipo c|hdmi)|cargador|estante|antena|banda|soporte|funda)\b)'
             r'(?=.*(bocina|bafle|altavo(z|ces)|maquina de cantar|\bspeaker\b|barra de sonido|sound ?bar|sistema activo estereo|\bsonos\b|'
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
             r'(?=.*(silla|sofa|sillon|escritorio|mesa|cama|colchon))'
             # ... y no la montura de cámara con "tornillo de 1/4" que
             # menciona de paso una mesa o el sillín de la bici.
             r'(?!.*(\bcamara|\bgopro\b|insta ?360|\btripode\b|\btripie\b|\bdslr\b|zapata caliente|\b1/4))'),
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
             # El accesorio que se vende POR el teléfono: "anillo magnético
             # compatible con iPhone 15 14 13", "obturador remoto para iPhone",
             # "bloque de pared para Samsung Galaxy S24". La regla de arriba
             # pide marca y modelo cerca de un color o unos GB, y "compatible
             # con iPhone 15 ... negro" lo cumple igual que el iPhone. Un
             # teléfono de verdad nunca dice "para iPhone" ni "compatible con
             # Galaxy"; los combos de tienda dicen "con bocina", no "para".
             # El teléfono tiene que ser el objeto directo del "para": con 25
             # caracteres de holgura, "Fabricado para Estados Unidos por
             # Motorola" convertía un Moto G en accesorio (y de ahí a
             # Motocicletas), y "para Personas Mayores ... Teléfono" tiraba un
             # teléfono básico. Medido en la regresión: 6 teléfonos perdidos.
             r'(?!.*\b(para|compatible (con|for|with)|for|fits?) (el |la |los |las |tu |su |mi |un |una )?'
             r'(iphone|celular(es)?|telefonos? (celular|movil|inteligente)|smartphones?|samsung|galaxy|xiaomi|'
             r'redmi|motorola|huawei|android|movil(es)?)\b)'
             r'(?!.*(anillo|ring holder|ring stand|obturador|palo (de )?selfie|gamepad|mando de juego|'
             r'unidad flash|enchufes? de pared|bloque de pared|laser|impresora|proyector))'
             r'(?=.*(\bcelular(es)?\b|smartphone|\bsmart ?phone\b|'
             r'telefono (inteligente|celular|movil|desbloqueado|resistente|robusto|android)|'
             r'telefonos inteligentes|movil inteligente|dual sim|dual nano|desbloqueado|liberado|'
             r'\d+ ?gb ram|\d+ ?gb ?\+ ?\d+ ?gb|\d+ ?\+ ?\d+ ?gb|\bram\b.{0,15}\brom\b|'
             r'\b(flip|smart|cell|feature) ?phone\b|'
             r'(samsung galaxy|galaxy [asmzf]\d|xiaomi|redmi|\bpoco\b|motorola|\bmoto ?[ge]\d|'
             r'\boppo\b|\bvivo\b|realme|\bhonor\b|huawei|\bzte\b|nokia|\btcl\b|oneplus|infinix|\btecno\b|'
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
 # Guarda de mascotas: la "Cama refrescante para perros", la "Alfombrilla
 # Refrescante para Mascotas" y la "casa de refrigeración para gatos"
 # enganchaban acá por "refrigeración"/"enfriamiento" y entraban como
 # componentes de PC -- 595 en la captura de mascotas del 16-sep. Ningún
 # componente de computadora se vende "para perro".
 # Lo que sobra del aparato de clima tampoco es un componente de PC: la
 # aspa de repuesto del ventilador de techo y el "minka-aire, luz Wave,
 # Ventilador de techo" no los toma la red de Climatización (una es pieza
 # suelta y la otra abre nombrando la luz) y acababan acá.
 (re.compile(r'^(?!.*(ventilador(es)? de techo|aspas? (de|para) ventilador|minisplit|mini split|'
             r'aire acondicionado|acondicionador de aire|ventilador (centrifugo|axial|industrial)))'
             r'^(?!(?:\S+ ){0,3}(cerradura|mesa|interruptor|temporizador|termostato|cortina|puerta|parasol|funda|maquina|estante|carro|carrito|gabinete de (cocina|bano)|isla|cojin|asiento|motor|gozne|bisagra|contenedor|cubo|placa de enfriamiento|hielera|caja)\b)'
             r'^(?!.*(\bperro|\bgato\b|\bgatos\b|\bgatito|mascota|\bcanino|\bfelino|\bcachorro))'
             # Lookahead, no coincidencia directa: con "^...(?:ventilador|...)"
             # la regla solo valía si el título EMPEZABA con la palabra, y
             # 205 componentes bien clasificados ("Barito - Ventilador de
             # Cintura Portátil") se quedaban sin categoría.
             r'(?=.*(?:ventilador|enfriador|enfriamiento|cooler|disipador|\baio\b|refrigeraci|refrigeradora|'
             r'pasta (termica|de grasa)|grasa termica|compuesto termico|fuente de poder|'
             r'fuente de alimentacion|tarjeta grafica|filtro de (malla|polvo)|'
             r'hub de ventilador|cable (de extension de alimentacion|rgb)|neon difuso|'
             r'tanque de agua|reservorio|indicador flujo|boton de encendido|'
             r'placa adaptadora|\bsata\b|pcie|\bpc fan\b|noctua|kit de actualizaci.n pantalla|'
             r'gabinete (para |de |del )?(pc|computadora|ordenador|gamer|gaming|atx|itx|torre|cpu)|gabinete.{0,40}\b(atx|itx|rgb|gamer|gaming|cristal templado|vidrio templado|ventiladores)\b|carcasa (para|de|del) (pc|computadora|ordenador)|funda para pc|'
             r'caja (modular|para pc)|chasis para pc|pc case|torre media|mid-tower|'
             r'almohadilla decorativa|para placa base|placa madre))'), COMP),
 # "Teclado" en español es el de la computadora Y el musical, y esta regla
 # se llevaba los dos: en la captura de 6,387 anuncios de instrumentos, 153
 # fichas -- melódicas, pianos digitales, kalimbas, kazoos, controladores
 # MIDI y hasta bancos de piano -- entraban como periférico de PC. Lo
 # musical lo recoge la red de Instrumentos musicales del final.
 (re.compile(r'^(?!.*(melodica|pianica|kalimba|\bkazoo\b|instrumento musical|'
             r'\bmidi\b|\bpiano|\bmusical\b|sintetizador|\borgano\b|\bpianika\b|'
             r'banco (de|para) (piano|teclado)|banqueta|melodic|cerradura|cerrojo|chapa|candado|caja fuerte|manija|picaporte|control de acceso|caja registradora|punto de venta|\bpos\b|'
             # Con el lookahead, "teclado" en cualquier parte alcanza, y eso
             # trae lo que solo lo NOMBRA: el "Cargador Micro-USB para Kindle
             # Paperwhite, Oasis, teclado, táctil" (es el modelo Kindle
             # Keyboard) y el monitor que viene en combo con teclado y mouse.
             # "\btablet" no: el "Teclado inalámbrico con touchpad para tablet"
             # es un teclado, y la guarda se llevaba 16 de ellos.
             # Ni "\bpulgadas\b": el propio teclado de tableta dice su medida
             # ("Teclado Microsoft Surface Pro para 11/10 pulgadas") y la
             # guarda se llevaba doce. El monitor que viene en combo se
             # reconoce por lo que es monitor, no por las pulgadas.
             r'\bcargador\b|\badaptador\b|\bmonitor\b|\bfhd\b|full hd|1920 ?x ?1080|'
             # Solo el MUEBLE: "escritorio" a secas devolvía a Muebles el "Teclado
             # Inalámbrico 2.4G ... Diseño De Escritorio", que es un teclado.
             r'(escritorio|mesa) (ejecutiv|industrial|de pie|para computadora|de oficina|de trabajo|gamer|con cajon)|'
             r'convertidor de escritorio|bandeja (para|de) teclado|\brecepcion\b|'
             r'\bips\b|\bhz\b|\bkindle\b))'
             # Lookahead, no coincidencia directa. Con "^(?!guarda)(teclado|
             # keyboard)" la palabra tenía que estar en la POSICIÓN 0 y solo
             # entraba lo que ABRE con "Teclado": el "Corsair K55 Core TKL
             # Teclado Gaming" y el "LOFREE Flow2 Teclado mecánico" se
             # quedaban sin categoría. Es el mismo tropiezo del ancla ^ que
             # ya se corrigió en la guarda de juguetes y en la regla de
             # componentes de PC; este era el tercero, y medido contra el
             # catálogo dejaba Teclados en 18% de acierto.
             r'(?=.*(teclado|keyboard))'), ('Teclados', None, 'keyboard')),
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
             # Tercera pasada, sobre la captura de 13,373 anuncios: 301 títulos
             # decían literalmente "instrumento de viento" sin nombrar cuál, y
             # los metales y las flautas del mundo (trompa, fliscorno, suona,
             # xun, dizi, pan pipes) eran 106 más. El tocadiscos entra acá
             # porque Instrumentos musicales ya tiene su subcategoría
             # ("Tornamesas"), que hasta ahora no la alcanzaba ninguna regla.
             r'instrumentos? (de )?viento|\btrompa\b|corno (frances|ingles)|'
             r'french horn|\bbugle\b|fliscorno|\btuba\b|\beufonio\b|\bsuona\b|'
             r'\bsheng\b|\bxun\b|\bdizi\b|bansuri|pan ?pipes?|panpipe|'
             r'\bpiccolo\b|flautin|\bgaita\b|cornamusa|\bcucurbita\b|\bbawu\b|'
             # El tocadiscos NO entra acá aunque "Tornamesas" exista como
             # subcategoría: probado, se llevaba los reproductores de vinilo
             # retro --que son equipo de audio de sala, no un instrumento-- y
             # encima sub_instrumento los mandaba a Amplificadores, porque esa
             # rama va antes que la de Tornamesas. Una tornamesa de DJ de
             # verdad ya la reclama una regla anterior.
             r'instrumentos? musical))'),
  ('Instrumentos musicales', None, 'guitar')),
 # Y esta segunda las AMBIGUAS: "batería" es también la pila, "tambor" el de
 # la lavadora, "platillo" un plato, "cuerdas" una soga, "bajo" una
 # preposición. Exigen además una palabra del mundo musical en el título, y
 # por eso van después: cualquier regla más precisa (Baterías portátiles,
 # Lavadoras, Autos) ya se llevó lo suyo mucho antes.
 (re.compile(r'^(?!.*(de juguete|para (muneca|barbie)|\bmaqueta\b))'
             r'(?=.*(\bbateria|\btambor|\bplatillo|\bcuerdas?\b|\bbajo\b|\bpercusion|'
             # "amplificador" y "pedal" se probaron como disparadores y hubo
             # que sacarlos: los repetidores de WiFi se venden como
             # "amplificador de señal ... doble banda", y "banda" ya estaba en
             # la lista de contexto de abajo -- 40 extensores de red acababan
             # en Instrumentos musicales. El amplificador de guitarra lo
             # recoge igual la red, por la palabra "guitarra" o "bajo".
             r'\bafinador\b|\batril\b|\bpartitura|\bviola\b))'
             r'(?=.*(musical|instrumento|orquesta|\bbanda\b|percusion|'
             r'guitarra|\bpiano\b|\bmidi\b|conciert|\bmusica\b|baterista|'
             r'\bbaqueta|\btarola\b|\bhi-?hat\b|\bcharles\b|\bbombo\b|'
             # El contexto también viene en inglés (media tienda de cuerdas y
             # parches se vende con el título original) y en la marca, cuando
             # esa marca no fabrica otra cosa: Fender no hace lavadoras. Se
             # excluyen a propósito las que sí (Yamaha, Roland, Pearl, Dunlop),
             # porque ahí la marca no dice nada sobre qué es el producto.
             r'\bguitar\b|\bbass\b|\bdrum\b|\bcymbal\b|\bsnare\b|\bstrings?\b|'
             r'\bfret|\bukulele\b|\bukelele\b|\bsaxofon|\btrompeta|\bviolin|'
             # Ni Remo ni Shure, aunque solo hagan cosas de música: "remo" es
             # también el de la tabla de remo (un propulsor de surf con
             # "batería" acabó en Baterías), y Shure pone su nombre en la
             # tapa de la pila de su transmisor, que es un repuesto.
             r'addario|ernie ball|\bfender\b|\bgibson\b|ibanez|squier|epiphone|'
             r'\btama\b|sabian|zildjian|\bevans\b|\bmeinl\b|\bludwig\b|'
             r'\bsonor\b|\bmapex\b|gretsch|\bkorg\b))'),
  ('Instrumentos musicales', None, 'guitar')),
 # Cámaras y almacenamiento, de red y por la misma razón que Instrumentos:
 # las dos categorías existían con sus subcategorías y sus repartidores,
 # pero ninguna regla general llegaba hasta ellas. Medido sobre la captura
 # de 12,683 anuncios del 16-sep: de 8,952 "no encaja", 4,328 decían
 # "cámara" (de acción, videocámara, instantánea, mirrorless, DJI Osmo,
 # Insta360, Akaso) y ~2,500 eran memorias USB, tarjetas y discos.
 #
 # Las dos piden el término EN LA CABEZA del título (primeras cinco
 # palabras). La primera versión lo buscaba en cualquier parte y la
 # regresión la tiró: la PC gamer "con SSD de 256 GB" era almacenamiento,
 # el OPPO Find X9 "cámara de 200 MP" y un Moto G eran cámaras compactas,
 # el kit NVR "con HDD" un disco interno, el dron "con cámara 4K" una
 # cámara. Lo que se vende ES lo que abre el título.
 (re.compile(r'^(?!.*(camara (de seguridad|ip|web|espia|oculta|para (auto|coche|carro)|trasera|de reversa|de vigilancia|'
             r'termica|termografica|endoscop|de microscopio|para (celular|telefono|smartphone)|ptz|corporal para policia)|'
             r'webcam|vigilancia|\bcctv\b|dashcam|\bptz\b|videoconferencia|\bndi\b|\bpoe\b|\bnvr\b|\bdvr\b|'
             r'\bdomo\b|monitor de bebe|baby monitor|\bdron|\bdrone|microscopio|endoscopio|\bfunda|estuche|\bbolsa|'
             r'mochila|tripie|tripode|\bfiltro|\bcorrea|protector de pantalla|\bmica\b|cargador|bateria|'
             r'tarjeta (de memoria|sd)|\bpara gopro|\bpara dji|\bpara insta|\bpara camara|accesorios? (para|de) (camara|gopro|dji)|'
             r'\bcaja\b|\bkit de (limpieza|accesorios)|de juguete|para nino|luz (de|para) (video|camara)|monitor de camara|'
             r'\bpegamento|adhesivo|\bvisor\b|'
             # Lo que la regresión 7 dejó pasar: la cámara de seguridad que no
             # dice "de seguridad" (Ring, timbre, exteriores, visión nocturna,
             # detección de movimiento), la de marcha atrás, la del monitor
             # de bebé y la impresora Instax.
             r'seguridad|\btimbre|exteriores|vision nocturna|deteccion de movimiento|marcha atras|retrovisor|'
             r'monitor de video|para bebe|\bbebe\b|\bnanny|\balexa\b|aplicacion para (telefono|celular)|\bapp\b|'
             r'smart cam|impresora|hi-print|\blab\b|\bwifi\b.{0,25}(app|remot|nube|cloud)|de carga\b|'
             r'de inspeccion|serpiente|boroscop|serguridad|\bexterior\b|interior|\b2pcs\b|\b4pcs\b))'
             r'^(?:\S+ ){0,5}(camara|videocamara|camcorder|filmadora|\binstax\b|polaroid|\bgopro\b|insta ?360|'
             r'dji (osmo|pocket|action)|\bakaso\b|\bsjcam\b|mirrorless|\bdslr\b|sony (alpha|zv-?|a\d{4})|canon (eos|powershot)|'
             r'nikon (z|d\d{3,4}|coolpix)|fujifilm (x-?[thse]|x100|gfx)|panasonic lumix|\blumix\b|olympus om|\bom system)\b'),
  ('Cámaras y fotografía', None, 'camera')),
 (re.compile(r'^(?!.*(memoria ram|\bddr\d|sodimm|\budimm\b|lector de tarjeta|\badaptador\b|\bcable\b|\bfunda|'
             r'estuche|carcasa|\benclosure\b|gabinete (para|de) disco|\bdock\b|base para disco|soporte|montura|'
             r'\bpc\b|computadora|laptop|\bportatil\b|chromebook|\bgamer\b|\bryzen\b|\bintel\b|\bcore i\d|'
             r'\bnvr\b|\bdvr\b|\bkit\b|camara|reproductor|escaner|\bradio\b|tablet|monitor|pantalla|'
             r'punto de acceso|access point|\bwnap|prosafe|'
             r'\bpara (camara|celular|telefono|switch|ps[45]|xbox)|de juguete))'
             r'^(?:\S+ ){0,5}(memoria usb|unidad(es)? flash|\bpendrive|usb flash|flash drive|memoria flash|'
             r'tarjeta (de memoria|micro ?sd|sd\b|sdxc|sdhc|cfexpress)|micro ?sdxc|micro ?sdhc|memoria micro ?sd|'
             r'disco duro|\bhdd\b|\bssd\b|unidad de estado solido|\bnvme\b|\bnas\b|'
             r'sandisk|kingston|\blexar\b|\badata\b|\bseagate\b|western digital|\bwd\b|toshiba canvio|'
             r'samsung (evo|pro|t7|t9|870|980|990)|\bcrucial\b|\bpny\b)\b'),
  ('Almacenamiento', None, 'storage')),
 # Mascotas, de red y ANTES que Herramientas, Vehículos y Muebles. La
 # categoría existe con ocho subcategorías y no tenía NINGUNA regla que la
 # alcanzara. Medido sobre la captura de 11,451 anuncios del 16-sep: de
 # 11,433 nuevos se daban de alta 3,993 y casi todos mal -- 2,358 camas
 # para perro entraban como Muebles/Camas, 279 rampas y escaleras para
 # mascota como Herramientas/Escaleras, y otras 400 como roperos, mesas,
 # sofás y colchones. Las 6,749 restantes se descartaban.
 #
 # Red de Deportes y fitness, el mismo agujero que tenía Mascotas: la
 # categoría existe con dieciocho subcategorías y 2,994 fichas, y NINGUNA
 # regla de categoría la alcanzaba. Medido sobre la captura de 12,398
 # anuncios de gimnasio del 16-sep: de 12,018 nuevos entraban 1,913, y de
 # esos 498 como Muebles/Sillas, 251 como Muebles/Mesas de centro y 198
 # como Bicicletas. Los otros 10,105 se descartaban enteros, entre ellos
 # 3,674 aparatos de gimnasio y 2,506 artículos de deporte.
 #
 # Los disparadores nombran el aparato, nunca el deporte a secas: "fútbol"
 # suelto está en un proyector "Diseño Fútbol 360°" y en un peluche;
 # "camping" está en la silla, el ventilador y la lavadora portátil (y de
 # todos modos el campismo vive en Viajes/Camping, que ya tiene 249);
 # "dardos" está en los lanzadores Nerf; "TRX" es también una bicicleta
 # Veloci; "spinning" es además el carrete de pesca.
 (re.compile(r'^(?!.*(de juguete|para ni.o|didactic|\bmaqueta\b|\bnerf\b|lanzador|'
             r'balon de (gas|oxigeno|butano)|gato hidraulico|'
             r'llavero|\bpegatina|\bsticker|calcomania|\bposter\b|'
             r'\bplayera\b|\bcamiseta\b|\bpantalon|\blegging|\bsudadera\b|'
             r'\bperro|\bgato\b|mascota|soldad|'
             r'para (auto|coche|carro|automovil)|parachoques|'
             r'\btambor\b|\bbateria\b|proyector|ventilador|calefactor|lavadora|'
             r'panel solar|estacion de energia|linterna|\bsilla\b|\bcolchon\b|'
             r'audifono|auricular|headphone|\bmp3\b|'
             r'\bcuenco\b|campana de mano|percusion|meditacion|\bchakra\b|'
             r'\bpesca\b|fishing|cana de pescar|'
             r'\bcelular|\btelefono\b|\blaptop\b|\bconsola\b|videojuego))'
             # La bicicleta de calle vive en Autos: el casco "para bicicleta,
             # patineta o patines" y el cojín de sillín son suyos. La fija y
             # la de spinning no, que son aparatos de gimnasio.
             r'(?!.{0,45}\bbicicletas?\b(?! ?(fija|estatica|de spinning|recumbent)))'
             r'(?=.*('
             r'mancuerna|kettlebell|pesa rusa|disco olimpico|barra olimpica|barra z\b|'
             r'\bdominadas?\b|pull ?up bar|'
             r'\babdominales?\b|ab wheel|rueda para abdominal|tabla de flexiones|push ?up board|'
             r'polea(s)? (gym|de gimnasio|para ejercicio|de cable)|sistema de poleas|lat pulldown|'
             r'accesorios? (de|para) polea|'
             r'banco (de|para) (ejercicio|pesas|abdominales)|banco fitness|banco multiposicion|'
             r'caminadora|trotadora|\beliptica\b|escaladora|maquina de remo|rowing machine|'
             r'bicicleta (fija|estatica|de spinning)|spinning|ciclo indoor|'
             r'multigimnasio|multiestacion|home gym|gimnasio (en casa|multifuncional|completo)|'
             r'banda(s)? (de|elastica de) resistencia|liga(s)? de ejercicio|power loops|'
             r'tapete (de|para) (yoga|ejercicio|pilates)|colchoneta (de|para) (yoga|ejercicio|gimnasia)|'
             r'\byoga\b|\bpilates\b|'
             r'\bbalon\b|pelota (de|para) (futbol|basquet|voleibol|yoga|pilates|ejercicio)|'
             r'raqueta (de|para) (tenis|padel|badminton|squash|ping)|ping ?pong|tenis de mesa|'
             r'\bbadminton\b|\bpadel\b|\bsquash\b|'
             r'tablero de dardos|juego de dardos|dardos de (acero|punta|aluminio)|\bdiana\b|'
             r'\bboxeo\b|costal de box|guantes de box|taekwondo|protector bucal|'
             r'patin(es|eta)\b|\bpatineta\b|\bskate\b|monopatin|'
             r'\bnatacion\b|goggles de nadar|aletas? de buceo|\bsnorkel\b|\bkayak\b|'
             r'paddle ?(board|surf)|stand up paddle|'
             r'\bvoleibol\b|\bvolleyball\b|balon de futbol|pelota de futbol|porteria de futbol|'
             r'\bespinilleras?\b|'
             r'rodillera|\bcodera|tobillera|munequera|faja (lumbar|deportiva|de levantamiento)|'
             r'cuerda para saltar|jump rope|salto de cuerda|'
             r'suspension trainer|entrenador de suspension|'
             r'ejercitador de (agarre|pecho|brazos|manos)|entrenador de fuerza de agarre|'
             r'\bcrossfit\b|\bhalterofilia\b|\bsentadillas?\b|'
             # Los anillos olímpicos son aparato de gimnasio, no joyería.
             r'anillos (de|para) (gimnasia|ejercicio)|anillos gimnastic|gimnasia olimpica'
             r'))'),
  ('Deportes y fitness', None, 'dumbbell')),
 # Se excluye el gato HIDRÁULICO, que es una herramienta de auto, y la
 # puerta "para gato" de una casa, que es ferretería.
 (re.compile(r'^(?!.*(gato (hidraulico|de piso|de botella|tipo patin)|perro caliente|'
             r'\bhot ?dog\b|pinza de gato|gato mecanico|'
             # La cámara que vigila a la mascota es una cámara de seguridad:
             # se vende como "cámara para mascotas y bebés" y entraba acá.
             r'\bcamara|\bvigilancia\b|monitor de bebe|\bcctv\b|\bnvr\b|\bdvr\b|'
             r'ojo de pez|esnorquel|\bbuceo\b))'
             # La mascota tiene que nombrarse TEMPRANO (primeros ~55
             # caracteres): si aparece al final es una mención de paso. Medido:
             # el camión "articulado gato" (Caterpillar traducido), la "alarma
             # de ladridos de perro" que es una alarma, el sensor Zigbee "apto
             # para mascotas" y el soplador de coches que además sirve para
             # "depilación de mascotas" entraban todos como productos de
             # mascota. Lo que SÍ es para la mascota lo dice al principio:
             # "Cama para perros", "Cuencos para Perros y Gatos".
             r'(?=^.{0,55}?(\bperro|\bperros\b|\bgato\b|\bgatos\b|\bgatito|mascota|\bcanino|\bfelino|'
             r'\bcachorro|\bhuron\b|\bconejo\b|\bhamster|\bloro\b|\bpericos?\b|'
             # Sin "pez"/"peces" sueltos: "ojo de pez" es un tipo de lente.
             r'\bacuario\b|\bpecera\b|\bjaula (para|de) (ave|pajaro|conejo|hamster)|'
             r'\bcatnip\b|\bcroqueta|\barenero\b|arena (para|de) gato|rascador (para|de) gato|'
             # "PET" a secas es el plástico: "flejes de PP/PET" son máquinas
             # de embalaje, no cosas de mascotas. Y "cat" a secas es el cable
             # "cat 6" y el teléfono "CAT S48c". Los dos piden contexto.
             r'\bveterinari|\bpet (bed|toy|toys|door|bowl|carrier|crate|house|supplies|grooming|food)\b|'
             r'\bpets? (supplies|products|store)\b|\bdog (bed|toy|toys|house|crate|bowl|food|leash)\b|'
             r'\bcat (bed|toy|toys|tree|litter|food|door|scratch)\b))'),
  ('Mascotas', None, 'paw')),
 # Herramientas, también de red y por la misma razón que Muebles: un
 # montón de aparatos nombran una herramienta de paso ("organizador para
 # taladro", "batería para atornillador"). Lo que ninguna otra regla
 # reclama y nombra una herramienta, es una herramienta.
 (re.compile(r'^(?!.*(de juguete|para nino|didactic|\bmaqueta\b|compresor de aire acondicionado|inversor de corriente|bascula (de bano|corporal|de cocina|de precision|de bolsillo)|balanza de cocina))'
             r'(?=.*(herramienta|taladro|rotomartillo|esmeriladora|soldador|'
             r'soldadura|escalera|andamio|\bbroca|\blija\b|desarmador|'
             r'destornillador|\bpinzas?\b|\bllave (allen|hexagonal|inglesa|perica|mixta)|'
             r'martillo|\bcincel\b|grabado(r|ra)? ?laser|multimetro|\bvernier\b|'
             r'flexometro|seguridad industrial|casco de seguridad|'
             r'guantes de (trabajo|seguridad|corte)|gas l\.?p\.?|plomeria|'
             r'jardineria|podadora|motosierra|desbrozadora|cortasetos|'
             r'compresor de aire|neumatica|\bcemento\b|revolvedora|carretilla))'),
  ('Herramientas', None, 'wrench')),
 # Cochecitos y sillas de auto de bebé, ANTES que Vehículos y que Muebles.
 # En español la carriola se llama "silla de paseo" y la silla de auto,
 # "asiento para coche": la primera enganchaba la red de Muebles ("silla")
 # y la segunda la de Vehículos ("coche"). Medido sobre la captura de
 # 12,621 anuncios del 16-sep: 1,568 carriolas entraron como Muebles/Sillas
 # y otro tanto de sistemas de viaje como Autos.
 (re.compile(r'^(?!.*(de juguete|para (muneca|barbie)|\bmaqueta\b|a escala|'
             # El accesorio PARA la carriola no es la carriola: el espejo de
             # bebé "para carriola", la mosquitera, el soporte de tablet que
             # sirve "para cama, carriola, avión".
             r'(espejo|soporte|funda|bolsa|organizador|manubrio|mosquitera|protector|'
             r'cubre|sombrilla|\bred\b|gancho|portavaso|colchoneta|forro|accesorio)'
             r'.{0,45}(carriola|cochecito)|para (la )?(carriola|cochecito)))'
             r'(?=.*(\bcarriola|cochecito (de|para) bebe|silla de paseo|travel system|'
             r'sistema de viaje|\bportabebe|asiento (para|de) (coche|auto|carro) (infantil|de bebe|para bebe)|'
             r'autoasiento|\bcar seat\b|silla (de|para) auto (infantil|de bebe|para bebe)|'
             r'\bbebe\b.{0,25}(carriola|cochecito|asiento de seguridad)))'),
  ('Juguetes y bebés', None, 'toy')),
 # Maquetas y coches a escala, también antes que Vehículos: "Set 50
 # Miniaturas Coche 1:100 para Maquetas" y "Modelo de coche a escala 1/18"
 # son juguetes de colección, no autos.
 # "miniatura" a secas se probó y hubo que sacarlo: el "Mini Micrófono ...
 # Miniatura Para Celular", la "Caja de Circuito Miniatura" de un panel
 # solar y la "Radio Miniatura de Banda Completa" son aparatos de verdad.
 # Ahora la miniatura tiene que venir con la escala o con la maqueta.
 (re.compile(r'^(?!.*(refaccion|repuesto|herramienta))'
             r'(?=.*(\bmaqueta|modelismo|escala 1 ?[:/] ?\d|a escala \d|\bdie-?cast\b|'
             r'fundido a presion|modelo (de|a) escala|\bdiorama\b|'
             r'kit de (modelo|montaje) (a escala|de simulacion)|'
             r'miniatura(s)?\b(?=.*(escala|maqueta|diorama|coleccion|\b1 ?[:/] ?\d))|'
             r'rompecabezas 3d|puzzle 3d))'),
  ('Juguetes y bebés', 'Maquetas', 'toy')),
 # Vehículos, de red por la misma razón que Muebles y Herramientas: la
 # categoría tenía nueve subcategorías y ninguna regla que la alcanzara, así
 # que una captura de autos y bicis entraba al 16% -- 7,568 de 10,162 anuncios
 # caían en "no encaja", casi todos accesorio y refacción.
 (re.compile(r'^(?!.*(de juguete|para (muneca|barbie)|\bmaqueta\b|'
             r'control remoto.{0,15}escala|montable para nino|'
             r'carr(o|ito)s? (de|para) (servicio|cocina|almacenamiento|bar|te|postres|helados|comida|bebidas|limpieza|lavanderia|compras|mandado|supermercado|libros|utilidad|herramientas|carga|mano|jardin)|'
             r'carr(o|ito)s? (rodante|multifuncion|utilitario|auxiliar|movil|organizador|plegable|metalico|con ruedas)|auto ?reset|inodoro|\bbide\b))'
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
             r'\btaburete|\bbanca\b|\bvitrina|\bcredenza|\blitera|'
             r'\bisla de cocina|\balacena|\bgabinete (de|para) (cocina|bano)|\baparador|\botomana|\bpuff?\b|'
             r'\bbanco (de|para) (bar|cocina|comedor|entrada|zapatos|almacenamiento|jardin|exterior|madera|ninos|plastico|acero|metal)|banco (tapizado|otomano|plegable|infantil|escalon|nube|con almacenamiento)|\bbanquito|\bbanqueta|'
             r'\bconsola (de entrada|para (sala|recibidor|pasillo))|\bestanteria\b|\btocador\b|mueble(s)? (de|para) (cocina|bano|tv|television|sala|entrada)|gabinete de audio|estante de audio|rack de audio))'),
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
 "B00X76H980": ("TIMCO", 'Belleza y cuidado personal', 'Secadoras de cabello', 'sparkle'),
 "B0D7FJKP3R": ("JULIET", 'Belleza y cuidado personal', 'Secadoras de cabello', 'sparkle'),
 # El One-Step Volumizer es el cepillo secador de Revlon; su título nunca dice
 # "secador". El catálogo ya guarda el multiestilizador Magic Styler y el
 # cepillo Izutech Toro entre las secadoras de cabello.
 "B09B2XF75X": ("REVLON", 'Belleza y cuidado personal', 'Secadoras de cabello', 'sparkle'),
 # El kit de Lizze empieza por la plancha y la secadora va de añadido: va con
 # los kits de plancha del catálogo ("Kit Plancha 450° + Rizador + Peine").
 "B0G3BH7RN2": ("LIZZE", 'Belleza y cuidado personal', 'Planchas para cabello', 'sparkle'),
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
 "B0GFJYK5C4": (None, 'Belleza y cuidado personal', 'Planchas para cabello', 'sparkle'),
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
    r'\b(proteccion|protector(a|es)?|funda|estuche|kit de|camara|mica|cubierta|pegatina|correa|controlador(es)?|chatpad|teclado|grips?|almohadillas?|'
    r'audifonos?|headset|diadema|tarjeta|libro|guia (oficial|de estrategia)|hacking|'
    r'control(es|ler|lers)?|mando|joy.?con|gamepad|volante|palanca|arcade stick|'
    r'grip|empunadura|soporte|base de carga|dock|stand|wall mount|'
    r'montaje de pared|cargador|cable|adaptador|bateria|pila|'
    r'boton(es)?|abxy|thumbstick|joystick|gatillo|'
    r'protector|mica|skin|calcomania|sticker|ventilador|enfriador|'
    r'tarjeta (micro ?sd|de memoria)|memoria micro ?sd|'
    r'repuesto|reemplazo|replacement|kit de (limpieza|reparacion|herramientas)|'
    r'charger|battery|button|holder|mount|case|cover|carrying)\b')

RX_VJ_CONSOLA = re.compile(r'^(?:\S+ ){0,4}(consola|console)\b|'
                           r'(consola|console)\b.{0,20}(nintendo|playstation|xbox)')
# Lo que acompaña a la plataforma cuando el título es el APARATO y no un
# juego para él: "PS5 Slim 1TB", "Switch OLED Blanca", "Xbox Series S
# Digital". "Ps4 Batman" o "Pragmata (Nintendo Switch 2)" no traen nada de
# esto y son juegos aunque la plataforma vaya al principio.
RX_VJ_HARDWARE = re.compile(r'\b(oled|lite|slim|pro|digital|\d+ ?(gb|tb)|ssd|bundle|paquete|blanc[ao]|negr[ao]|'
                            r'reacondicionad|nuev[ao]|sellad|edicion (estandar|digital|standard)|standard edition|'
                            r'portatil|handheld|\bgen\b|generacion|mando incluido|con (1|2|dos) (control|mando))')
RX_VJ_JUEGO = re.compile(r'\((nintendo switch( 2)?|switch( 2)?|ps[345]|playstation ?[345]|xbox[^)]*)\)|'
                         r'- (nintendo switch( 2)?|switch 2|ps[345]|playstation ?[345]|xbox (series|one))\s*$|'
                         r'para (nintendo )?switch( 2)?\s*$|\b(edition|edicion (deluxe|coleccionista|collector|definitiva|completa)|'
                         r'remastered|remake|collection|\bgoty\b|game of the year|juego (de|para) (nintendo|switch|ps[45]|playstation|xbox))\b')


def sub_videojuego(tn):
    """Consolas / Software / Accesorios, por dónde cae la plataforma."""
    if RX_VJ_ACCESORIO.search(tn):
        return 'Accesorios'
    # "Juego Xbox 360 Lego The Movie" y "Planet Coaster: Console Edition"
    # nombran la consola, pero son el juego.
    if re.match(r'^(?:\S+ ){0,3}(video ?)?juegos?\b', tn) or 'console edition' in tn:
        return 'Software'
    # Un juego se delata solo: la plataforma entre paréntesis, al final tras
    # un guion, o "edition/remastered"; salvo que el título abra con la
    # consola ("Consola PS5 Edición Digital").
    if RX_VJ_JUEGO.search(tn) and not re.match(r'^(?:\S+ ){0,2}consola', tn):
        return 'Software'
    if RX_VJ_CONSOLA.search(tn):
        return 'Consolas'
    m = RX_VJ_PLATAFORMA.search(tn)
    if not m:
        return None
    # La plataforma en las primeras palabras es el aparato SOLO si la
    # acompaña algo de hardware (OLED, 1TB, Slim, blanca...); si no, es un
    # juego que abre con su plataforma ("Ps4 Batman: Arkham Collection").
    if len(tn[:m.start()].split()) <= 2:
        return 'Consolas' if RX_VJ_HARDWARE.search(tn[m.end():m.end() + 60]) else 'Software'
    return 'Software'


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
        (r'isla de cocina|mueble(s)? (de|para) cocina|gabinete (de|para) (cocina|bano)|\balacena|barra de (cafe|desayuno)|'
         r'estante para (panadero|microondas)|\bdespensa\b|carrito de cocina|vinoteca|gabinete de vino|mueble bar', 'Muebles de cocina'),
        (r'\bcolchon|box spring|\bsomier\b', 'Colchones'),
        (r'\b(buro|mesita de noche|mesa de noche|mesa de luz)\b', 'Burós'),
        (r'\b(litera|cabecera|base de cama|cama|camas)\b', 'Camas'),
        (r'\b(sofa ?cama|sofa|sofas|sillon|loveseat|futon)\b', 'Sofás'),
        (r'\b(zapateras?|zapateros?)\b', 'Zapateras'),
        (r'\b(percheros?|paragueros?|burro de ropa)\b', 'Percheros'),
        (r'\b(roperos?|armarios?|closets?|comodas?|vitrinas?|credenzas?|cajoneras?|aparadores?|tocador(es)?)\b', 'Roperos'),
        (r'\b(libreros?|estanterias?|estantes? para libros)\b', 'Libreros'),
        (r'\b(repisas?|entrepanos?)\b', 'Repisas'),
        (r'mesa de (billar|ping ?pong|futbolito|juego|poker)', 'Mesas de juego'),
        (r'\bescritorios?\b', 'Escritorios'),
        (r'\bsillas? (de|para) comedor|\bbancos? (de|para) comedor', 'Sillas'),
        (r'\b(comedor|antecomedor)\b', 'Mesas de comedor'),
        (r'mesa (de centro|auxiliar|lateral|de sala|de cafe)', 'Mesas de centro'),
        # "Mesa alta de bar", "Mesa de cocina para desayunador", "juego de
        # mesa de comedor de 4 piezas": la mesa de comer aunque "comedor"
        # llegue después de "mesa".
        (r'\bmesas?\b.{0,45}\b(comedor|cocina|de bar|desayunador|alta|de cafeteria|de restaurante)\b', 'Mesas de comedor'),
        (r'\b(sillas?|bancos?|taburetes?|butacas?|bancas?|banquitos?|puff?s?|otomanas?)\b', 'Sillas'),
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
                 r'\berhu\b|\bguqin\b|guzheng|\bkoto\b|\bsitar\b|\bcitara\b|'
                 r'\blira\b|\blyre\b|\bharp\b', tn): return 'Cuerdas'
    if re.search(r'saxofon|trompeta|flauta|clarinete|trombon|\btuba\b|armonica|oboe|'
                 r'\bfagot\b|\bcorno\b|\btrompa\b|corneta|melodica|\bpianica\b|'
                 r'\bkazoo\b|ocarina|didgeridoo|\bgaita\b|\bquena\b|zampo|flautin|'
                 r'\bflugel|\bcornamusa\b|bombardino|\bshofar\b|\bhulusi\b|sousafon|'
                 r'\bcuerno\b|\bmelodion\b|\bpiano de viento\b|'
                 # Los que la red nueva trae y aquí no tenían rama: 301 fichas
                 # dicen "instrumento de viento" sin nombrar cuál, y los del
                 # resto del mundo (suona, sheng, xun, dizi, bansuri, bawu)
                 # caían sin subcategoría, que es quedarse fuera de su página.
                 r'instrumentos? (de )?viento|\bsuona\b|\bsheng\b|\bxun\b|\bdizi\b|'
                 r'bansuri|pan ?pipes?|panpipe|\bpiccolo\b|\bbawu\b|\bcucurbita\b|'
                 r'fliscorno|\beufonio\b|french horn|\bbugle\b', tn): return 'Viento'
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
                 r'\bdiapason\b|tenedor de afinacion|cable midi|\bperilla\b|'
                 # Al final de todo, que es donde no molesta: un juego de
                 # cuerdas sueltas (media tienda de D'Addario) no nombra
                 # ningún instrumento y se quedaba sin subcategoría. Acá abajo
                 # solo alcanza a lo que ninguna rama anterior reclamó, así
                 # que "guitarra con cuerdas de repuesto" sigue en Guitarras.
                 r'\bcuerdas?\b|drum ?stick', tn): return 'Accesorios'
    return None


def sub_iluminacion(tn):
    if re.search(r'tira (led|de luz)|cinta led|\bstrip\b', tn): return 'Tiras LED'
    if re.search(r'foco intelig|bombilla intelig|\bwifi\b.{0,15}foco|foco.{0,15}\bwifi\b|'
                 r'foco.{0,20}(alexa|google)', tn): return 'Focos inteligentes'
    if re.search(r'\bfoco\b|bombilla|\bled\b.{0,10}\bw\b|luminaria', tn): return 'Focos'
    if re.search(r'lampara de (escritorio|mesa|buro)|de escritorio', tn): return 'Lámparas de escritorio'
    if re.search(r'lampara (de )?(techo|colgante)|luces? colgantes?|colgante|candil|plafon|arana|araña|empotra', tn): return 'Lámparas de techo'
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
    # ... salvo que el vehículo ABRA el título. "Bicicleta de Montaña Rodada
    # 29 ... Cuadro de Aluminio" es una bicicleta entera y caía en
    # "Accesorios para bicicleta" por la palabra "cuadro", que ahí es una
    # ficha técnica y no el producto. El sillín, en cambio, abre con
    # "Sillín", así que la regla de piezas lo sigue agarrando.
    # Sin holgura ninguna: el vehículo tiene que ser la PRIMERA palabra. Con
    # una de holgura entraba "Soporte Bici" (un soporte) y con dos, "Radios
    # de bicicleta" (los rayos de la rueda). Lo que se quiere rescatar acá
    # es la bicicleta entera, que siempre abre el título con su nombre.
    if re.match(r'^(bicicleta|bici|triciclo)\b', tn):
        return 'Bicicletas'
    if re.match(r'^(motocicleta|motoneta|scooter de gasolina)\b', tn):
        return 'Motocicletas'
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
                 r'funda para (auto|volante|asiento)|cubre ?volante|\bcojin|'
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
    # El accesorio DEL aparato no es el aparato: "Cargador de 18 V ... para
    # Echo Show 21" no es una bocina inteligente.
    if re.match(r'^(?:\S+ ){0,3}(cargador|cable|funda|soporte|adaptador|base|repuesto|montura|bateria)\b', tn):
        return None
    if re.search(r'enchufes? intelig|contactos? (de pared )?intelig|smart plug|tomacorriente intelig|enchufes? (wifi|alexa)|regleta intelig|multicontacto intelig', tn):
        return 'Enchufes inteligentes'
    if re.search(r'apagador(es)? intelig|interruptor(es)? (de luz |de pared |tactil |de atenuacion |inalambrico )?intelig|smart switch|'
                 r'interruptor(es)? (de luz |de pared |tactil )?(wifi|zigbee|tuya)|apagador(es)? (wifi|tuya)|modulo (interruptor|rele)|rele wifi|'
                 r'atenuador intelig|dimmer intelig|pulsador de boton|interruptor.{0,30}(tuya|alexa|zigbee|wifi)', tn):
        return 'Interruptores inteligentes'
    if re.search(r'cerradura|chapa intelig|smart lock|cerrojo|manija.{0,30}huella|bloqueo de puerta|\block\b', tn): return 'Cerraduras inteligentes'
    if re.search(r'cortina|persiana', tn): return 'Cortinas motorizadas'
    if re.search(r'termostato|honeywell home', tn): return 'Termostatos'
    if re.match(r'^(?:\S+ ){0,1}(sensor|detector|valvula)', tn): return 'Sensores'
    if re.search(r'\bhub\b|puente|bridge|gateway|centro de control|control(ador)? (remoto )?universal', tn): return 'Hubs'
    if re.search(r'focos?|bombillas?|tiras? (de )?led|iluminacion|lampara|\bluz\b|\bluces\b|philips hue|\bhue\b|controlador (led|rgb)', tn):
        return 'Iluminación inteligente'
    # "Amazon Echo Pop", "Asistente de Voz Echo Show 8": 493 fichas de la
    # categoría son el Echo y no lo agarraba nada, porque la regla pedía
    # "echo dot" exacto. El Show y el Hub llevan pantalla pero se usan como
    # bocina, que es como los vende Amazon.
    if re.search(r'sensor|detector|valvula|timbre', tn): return 'Sensores'
    if re.search(r'\bzigbee\b|\bmatter\b', tn): return 'Hubs'
    if re.search(r'bocina intelig|altavoz intelig|google (home|nest)|\becho (dot|pop|show|studio)\b|amazon echo|homepod|asistente de voz', tn): return 'Bocinas inteligentes'
    if re.search(r'\bhub\b|puente|bridge|zigbee|centro de control', tn): return 'Hubs'
    if re.search(r'cortina|persiana', tn): return 'Cortinas motorizadas'
    if re.search(r'sensor|detector|timbre intelig|videoportero', tn): return 'Sensores'
    if re.search(r'termostato', tn): return 'Termostatos'
    return None


def sub_deporte(tn):
    """Reparte Deportes y fitness."""
    if re.search(r'^(?:\S+ ){0,3}(pesa|mancuerna|disco olimpico|barra olimpica|kettlebell)', tn): return 'Pesas'
    if re.search(r'bicicleta (fija|estatica|de spinning)|spinning|ciclo indoor', tn): return 'Bicicletas fijas'
    if re.search(r'\bbalon\b|pelota de (futbol|basquet|voleibol)', tn): return 'Balones'
    if re.search(r'patin(es|eta)?\b|patineta|skate|scooter para nino', tn): return 'Patines y patinetas'
    if re.search(r'\byoga\b|pilates|tapete de ejercicio|colchoneta', tn): return 'Yoga'
    if re.search(r'\bboxeo\b|costal de box|guantes de box', tn): return 'Boxeo'
    if re.search(r'raqueta|\btenis de mesa\b|badminton|\bpadel\b|squash', tn): return 'Raquetas'
    if re.search(r'ping ?pong|mesa de tenis de mesa', tn): return 'Ping pong'
    # "diana" con bordes: sin ellos, "Wilson Mediana" era un juego de dardos.
    if re.search(r'\bdardos?\b|\bdiana\b|tablero de dardos', tn): return 'Dardos'
    if re.search(r'\bvoleibol\b|\bvolleyball\b', tn): return 'Voleibol'
    if re.search(r'\bfutbol\b|\bsoccer\b|porteria|guante(s)? (de )?portero', tn): return 'Fútbol'
    if re.search(r'natacion|alberca|goggles de nadar|traje de bano deportivo|\baleta(s)? de buceo\b', tn):
        return 'Natación'
    # Sin "\bsup\b": el guión del número de parte hace de borde de palabra y
    # el guante de portero "SUP-D1GLV-3" entraba como tabla de paddle.
    if re.search(r'kayak|paddle ?(board|surf)|stand up paddle|buceo|\bsurf\b|snorkel', tn):
        return 'Deportes acuáticos'
    if re.search(r'banda(s)? (de|elastica)? ?resistencia|liga de ejercicio', tn): return 'Bandas de resistencia'
    if re.search(r'campismo|camping|casa de campana|sleeping bag|bolsa de dormir', tn): return 'Campismo'
    if re.search(r'rodillera|codera|tobillera|muneque|faja|soporte (lumbar|deportivo)', tn):
        return 'Protección y soportes'
    # Lo que la captura de 12,398 dejaba sin repartir (2,693 fichas) era
    # casi todo aparato de gimnasio con otro nombre: la polea, la barra de
    # dominadas, el banco, la escaladora y la tabla de flexiones.
    if re.search(r'caminadora|trotadora|eliptica|escaladora|maquina de remo|remo (de|para) ejercicio|'
                 r'multigimnasio|multiestacion|banco (de|para) (ejercicio|pesas|abdominales)|'
                 r'banco fitness|banco multiposicion|gimnasio|home gym|'
                 r'\bdominadas?\b|pull ?up bar|\babdominales?\b|ab wheel|rueda para abdominal|'
                 r'tabla de flexiones|push ?up board|polea|lat pulldown|'
                 r'suspension trainer|entrenador de suspension|'
                 r'ejercitador de (agarre|pecho|brazos|manos)|entrenador de fuerza de agarre|'
                 r'\bcrossfit\b|\bsentadillas?\b', tn):
        return 'Equipo de gimnasio'
    return None


def sub_belleza(tn):
    """Reparte Belleza y cuidado personal.

    El aparato va antes que el cosmético porque lo nombra de paso: la
    "plancha para cabello con aceite de argán" es una plancha, y el
    "vaporizador facial" no es una crema. Dentro del cosmético, lo capilar
    antes que lo facial ("mascarilla capilar" contra "mascarilla facial") y
    el maquillaje antes que la crema ("crema base de maquillaje").
    """
    if re.search(r'secadora? de (cabello|pelo)|cepillo secador', tn): return 'Secadoras de cabello'
    if re.search(r'plancha (de|para) (cabello|pelo)|alaciadora', tn): return 'Planchas para cabello'
    if re.search(r'\brizador|tenaza (de|para) (cabello|rizos)|ondulador', tn): return 'Rizadores'
    if re.search(r'\bdepilador|luz pulsada|cera depilatoria|depilacion laser', tn): return 'Depilación'
    if re.search(r'rasuradora|afeitadora|rastrillo (de|para) afeitar|cortapelo|'
                 r'recortador de (barba|vello)', tn): return 'Rasuradoras'
    if re.search(r'\bpeluca', tn): return 'Pelucas'
    if re.search(r'extensiones de (cabello|pelo)', tn): return 'Extensiones de cabello'
    if re.search(r'esmalte (de|para) unas|gel (para|de) unas|acrilico (para|de) unas|'
                 r'unas postizas|press ?on nails|lampara (uv|led) (para|de) unas|'
                 r'torno (de|para) unas|drill (para|de) unas', tn): return 'Uñas'
    if re.search(r'kit de manicura|juego de manicura|\bcortaunas\b|empujador de cuticula|'
                 r'lima de unas|\bpedicure\b|tijeras (de|para) cuticula', tn): return 'Manicure'
    if re.search(r'silla (de|para) (salon|barbero|estilista)|carrito de belleza|'
                 r'mostrador de recepcion|lavacabezas|camilla (de|para) (masaje|spa)', tn):
        return 'Mobiliario para salón'
    if re.search(r'masajeador|pistola de masaje', tn): return 'Masajeadores'
    # El aparato de cabina (HIFU, radiofrecuencia, hidrafacial) es facial o
    # corporal según lo que dice tratar; por defecto, facial.
    if re.search(r'radiofrecuencia corporal|cavitacion|criolipolisis|ultrasonido corporal|'
                 r'moldeado corporal|body sculpt|cepillo (corporal|de cuerpo|en seco)|'
                 r'\bbody lotion\b|locion corporal', tn): return 'Corporales'
    if re.search(r'\bhifu\b|hydra ?facial|jet peel|oxigeno de hidrogeno|mascara facial led|'
                 r'terapia de luz led|fototerapia facial|lifting facial|analizador de piel|'
                 r'radiofrecuencia (facial|profesional)|microagujas|microdermoabrasion|dermapen|'
                 r'peeling ultrasonico|limpiador facial|vaporizador facial|sauna facial|'
                 r'\bfacial mist\b|\bcleanser\b|\bmoisturizer\b', tn): return 'Faciales'
    if re.search(r'protector solar|bloqueador solar|\bfps ?\d|\bspf ?\d|\bsunscreen\b', tn):
        return 'Protección solar'
    if re.search(r'\bperfume\b|eau de (toilette|parfum)|agua de colonia', tn):
        return 'Perfumes'
    if re.search(r'\bhair mask\b|\bhair dryer\b', tn): return 'Secadoras de cabello' if 'dryer' in tn else 'Cuidado del cabello'
    if re.search(r'\bflat iron\b', tn): return 'Planchas para cabello'
    if re.search(r'\bcurling iron\b', tn): return 'Rizadores'
    if re.search(r'\bnail polish\b', tn): return 'Uñas'
    if re.search(r'\bshampoo\b|\bchampu\b|acondicionador (para|de) (cabello|pelo)|'
                 r'tratamiento capilar|mascarilla capilar|tinte (para|de) (cabello|pelo)|'
                 r'\bkeratina\b|aceite (para|de) (cabello|pelo)', tn): return 'Cuidado del cabello'
    if re.search(r'\bmaquillaje\b|\bfoundation\b|\blabial\b|\blipstick\b|\brimel\b|'
                 r'mascara de pesta|delineador (de ojos|liquido)|\brubor\b|sombra de ojos|'
                 r'paleta de sombras|corrector de ojeras|setting spray|polvo compacto|'
                 r'brocha (de|para) maquillaje|\bbronzer\b|\bconcealer\b|\beyeshadow\b|'
                 r'\blip plumper\b', tn): return 'Maquillaje'
    if re.search(r'crema (corporal|para el cuerpo)|locion corporal|\bdesodorante\b|'
                 r'antitranspirante|gel de bano|aceite (corporal|de barba|para barba)|'
                 r'exfoliante corporal', tn): return 'Corporales'
    if re.search(r'\bserum\b|crema|limpiador facial|gel limpiador|agua micelar|tonico facial|'
                 r'contorno de ojos|mascarilla|exfoliante|\bretinol\b|\bniacinamida\b|'
                 r'acido (salicilico|hialuronico|glicolico|kojico)|facial', tn): return 'Faciales'
    return None


def sub_joyeria(tn):
    """Reparte Joyería y bisutería. El material suelto va primero: un
    paquete de "dijes para pulsera" es material, no una pulsera."""
    if re.search(r'^(?:\S+ ){0,3}(kit|paquete|lote|set) de (dijes|cuentas|abalorios|hilo|mostacilla)', tn):
        return 'Material para bisutería'
    if re.search(r'\bjoyero\b|caja (para|de) joyas|organizador de joyas', tn): return 'Joyeros'
    if re.search(r'\barras\b|set de novia', tn): return 'Arras y sets'
    if re.search(r'lentes de sol|gafas de sol', tn): return 'Lentes de sol'
    if re.search(r'^(?:\S+ ){0,3}(reloj|relojes)\b', tn): return 'Relojes'
    if re.search(r'^(?:\S+ ){0,3}(arete|aretes|arracada|broquel)', tn): return 'Aretes'
    if re.search(r'^(?:\S+ ){0,3}(collar|gargantilla|cadena)', tn): return 'Collares'
    if re.search(r'^(?:\S+ ){0,3}(pulsera|brazalete|esclava)', tn): return 'Pulseras'
    if re.search(r'^(?:\S+ ){0,3}(anillo|anillos|sortija)', tn): return 'Anillos'
    if re.search(r'\bdije\b|\bdijes\b|\bcharm', tn): return 'Dijes y charms'
    if re.search(r'limpiador de joyas|pano de pulido|herramienta de joyeria', tn):
        return 'Cuidado y herramientas'
    return None


def sub_impresora(tn):
    """Reparte Impresoras. El consumible primero: el cartucho y el tóner
    nombran la impresora para la que sirven."""
    if re.search(r'cartucho|\btoner\b|\btinta\b|papel (fotografico|bond|de sublimacion|para sublimacion|sublimar)|cinta de impresion|\bdrum\b|cabezal',
                 tn) and not re.match(r'^(?:\S+ ){0,3}impresora', tn):
        return 'Consumibles'
    if re.search(r'fotografica|de fotos|instantanea|selphy|\bivy\b|kodak dock|liene', tn): return 'Fotográficas'
    if re.search(r'\blaser\b|laserjet', tn): return 'Láser'
    if re.search(r'termica|\bthermal\b|etiquetas|tickets|punto de venta', tn): return 'Térmica'
    if re.search(r'inyeccion|inkjet|deskjet|ecotank|\bofficejet\b|pixma|multifuncional', tn):
        return 'Inyección de tinta'
    return None


def sub_escritorio(tn):
    """Reparte Computadoras de escritorio."""
    # Todo esto solo si abre el título: los módulos de RAM de Timetec dicen
    # "para iMac All-in-One" al final y no son computadoras. Una AIO de
    # verdad lo dice temprano ("HP All-in-One 24", "Panel PC Industrial
    # All-in-One", "Apple 2024 iMac").
    if re.match(r'^(?:\S+ ){0,4}(all[- ]?in[- ]?one|aio|todo en uno|imac)\b', tn):
        return 'All in One'
    if re.search(r'mini ?pc|\bnuc\b|micro pc|tiny|mini computadora', tn): return 'Mini PC'
    if re.search(r'\btorre\b|\bdesktop\b|gabinete|sobremesa|\bsff\b|computadora de escritorio', tn):
        return 'Torre'
    return None


def sub_blancos(tn):
    """Reparte Blancos y ropa de cama."""
    if re.search(r'^(?:\S+ ){0,3}(sabana|juego de cama|ropa de cama|funda de almohada)', tn): return 'Sábanas'
    if re.search(r'^(?:\S+ ){0,3}(edredon|colcha|quilt|duvet|cubrecama)', tn): return 'Edredones'
    if re.search(r'(cobija|manta|frazada) electrica', tn): return 'Cobijas eléctricas'
    if re.search(r'^(?:\S+ ){0,3}(cobija|manta|frazada|cobertor)', tn): return 'Cobijas'
    if re.search(r'^(?:\S+ ){0,3}(protector|cubrecolchon)|protector (de|para) colchon|'
                 r'cubre ?colchon|\btopper\b|sobrecolchon|\bpillow ?top\b|'
                 r'protector(es)? (de |para )?colchon', tn):
        return 'Protectores de colchón'
    if re.search(r'^(?:\S+ ){0,3}almohada', tn): return 'Almohadas'
    if re.search(r'^(?:\S+ ){0,3}(toalla|toallas)|toalla(s)? (de|para) (bano|playa|cuerpo|mano)|'
                 r'\btoallon\b|juego de toallas', tn): return 'Toallas'
    if re.search(r'tapete(s)? (de|para) bano|alfombra (de|para) bano', tn): return 'Tapetes de baño'
    if re.search(r'^(?:\S+ ){0,3}(cortina|cortinas)', tn): return 'Cortinas'
    if re.search(r'funda (para|de) (sofa|sillon|sillones|mueble)|cubre ?(sofa|sillon|sillones)',
                 tn): return 'Fundas para muebles'
    return None


def sub_reloj(tn):
    """Reparte Relojes inteligentes."""
    if re.search(r'banda de actividad|pulsera de actividad|\bmi band\b|fitness tracker|\bband \d', tn):
        return 'Bandas de actividad'
    if re.search(r'smart ?watch|reloj intelig|apple watch|galaxy watch|\bwatch\b', tn): return 'Smartwatches'
    return None


def sub_suplemento(tn):
    """Reparte Suplementos. El deportivo primero: la proteína y la creatina
    también son vitaminas para quien las busca, pero se compran por eso."""
    if re.search(r'\bproteina\b|\bwhey\b|\bcaseina\b|\bprotein\b', tn): return 'Proteínas'
    if re.search(r'\bcreatina\b|\bpre ?entreno\b|\bbcaa\b|\bl-?carnitina\b|\boxido nitrico\b|'
                 r'\bglutamina\b|ganador de peso', tn): return 'Deportivos'
    if re.search(r'\bprobiotic|\bprebiotic|\bmicrobiota\b|lactobacillus|\binulina\b', tn):
        return 'Probióticos'
    if re.search(r'\bcolageno\b', tn): return 'Colágeno'
    if re.search(r'\bomega ?3\b|aceite de (pescado|krill|linaza|coco|onagra)|\bmct\b', tn):
        return 'Omega y aceites'
    if re.search(r'\bcurcuma\b|\bashwagandha\b|\bbacopa\b|\bresveratrol\b|\bespirulina\b|'
                 r'\balcachofa\b|\btoronjil\b|\bvaleriana\b|\bmoringa\b|\bginkgo\b|\bginseng\b|'
                 r'\bherbol|\bextracto de (planta|hierba)|\bnootropico\b', tn): return 'Herbolaria'
    if re.search(r'control de peso|quema ?grasa|adelgaz|\bsaciante\b|\bdetox\b|reduce medidas', tn):
        return 'Control de peso'
    if re.search(r'\bvitamina|\bmultivitamin|\bmagnesio\b|\bzinc\b|\bhierro\b|\bcalcio\b|'
                 r'\bmelatonina\b|\bbiotina\b|\bglucosamina\b|\bcolina\b|\bpotasio\b|\bselenio\b|'
                 r'\bmineral', tn): return 'Vitaminas y minerales'
    return None


def sub_red(tn):
    """Reparte Redes. Estas cuatro cosas se nombran siempre y no se pisan
    entre sí; el orden solo importa para el repetidor, que muchas veces se
    vende como "router extensor"."""
    if re.search(r'\brepetidor|extensor|\bextender\b|amplificador de senal wifi|\bmesh\b|red en malla', tn):
        return 'Repetidores'
    if re.search(r'\bmodem\b|\bdocsis\b|\bont\b|\bgpon\b', tn): return 'Módems'
    if re.search(r'\bswitch\b|conmutador', tn): return 'Switches'
    if re.search(r'access ?point|punto de acceso|\bap\b wifi', tn): return 'Access points'
    if re.search(r'\brouter\b|\bruteador\b|enrutador', tn): return 'Routers'
    return None


def sub_clima(tn):
    """Reparte Climatización.

    Manda lo que ABRE el título. El ventilador iba al final --el aire
    acondicionado y el purificador lo nombran de paso-- y eso hacía que el
    "Ventilador de mano de niebla ... con humidificador" fuera un
    humidificador y el "Ventilador portátil ... enfriador de aire sin
    aspas" un climatizador evaporativo. Los dos son ventiladores que
    mencionan una función. El aire acondicionado de cuello, que abre con
    "Aire Acondicionado", sigue cayendo donde debe.
    """
    if re.match(r'^(?:\S+ ){0,3}(ventilador|abanico)\b', tn):
        return 'Ventiladores'
    if re.search(r'aire acondicionado|acondicionador(es)? de aire|minisplit|mini ?split|'
                 r'\binverter\b.{0,20}(frio|calor)|\d+ ?btu\b', tn):
        return 'Aires acondicionados'
    if re.search(r'purificador(es)? (de )?aire|filtro hepa', tn): return 'Purificadores de aire'
    if re.search(r'deshumidificador|deshumificador', tn): return 'Deshumidificadores'
    if re.search(r'humidificador|vaporizador de ambiente|difusor de aroma', tn): return 'Humidificadores'
    if re.search(r'calefactor|calentador (de ambiente|de pared|de patio|de espacio|de interiores|'
                 r'de habitacion|de escritorio|electrico|ceramico|infrarrojo|de cuarzo|halogeno)|'
                 r'\bcalefaccion\b|chimenea electrica|radiador (lleno de aceite|de aceite)|calefactable', tn):
        return 'Calefactores'
    if re.search(r'climatizador|enfriador (de aire|evaporativo)|cooler evaporativo', tn):
        return 'Climatizadores evaporativos'
    if re.search(r'ventilador|\bfan\b', tn): return 'Ventiladores'
    return None


def sub_mascota(tn):
    """Reparte Mascotas.

    Media captura de mascotas viene con el título en inglés ("dog squeaky
    toys", "wool dog toy", "pet bed"), así que cada rama lleva también sus
    palabras en inglés.
    """
    if re.search(r'\bpuerta|\bgatera\b|\bpet door\b|\bdog door\b', tn): return 'Puertas para mascotas'
    if re.search(r'rascador|arbol (para|de) gato|torre (para|de) gato|\bcat tree\b|'
                 r'\bscratch(er|ing)\b|poste rascador', tn): return 'Rascadores y torres'
    if re.search(r'\bjaula|\bcorral\b|\bcerca (para|de) (perro|mascota)|valla (para|de) (perro|mascota)|'
                 r'\bperrera\b|\bcrate\b|\bkennel\b|\bplaypen\b', tn): return 'Jaulas y corrales'
    if re.search(r'\bcepillo|\bshampoo\b|\bchampu\b|cortaunas|\btoallita|\bpanal|'
                 r'bolsa(s)? (para|de) (heces|desecho|popo)|recogedor|\bgrooming\b|quita ?pelo|'
                 r'\bdesenredante|\bcortapelo', tn): return 'Higiene y limpieza'
    if re.search(r'\bropa\b|\bchaleco|\bsueter|\bimpermeable (para|de) (perro|mascota)|disfraz|'
                 r'\bbotas\b|\bzapatos\b|\bbandana\b|\bmonos?\b para perro', tn):
        return 'Ropa y accesorios'
    if re.search(r'\badiestr|entrenamiento (para|de) (perro|mascota)|\bclicker\b|collar antiladrido|'
                 r'valla invisible|\btraining\b (pad|collar)', tn): return 'Adiestramiento'
    if re.search(r'\barenero|\barena para gato|caja de arena|\blitter box\b', tn): return 'Areneros'
    if re.search(r'transportadora|jaula de viaje|canil|kennel|mochila (para|de) (perro|gato|mascota)', tn):
        return 'Transportadoras'
    if re.search(r'comedero|plato (para|de) (perro|gato|mascota)|dispensador de alimento', tn):
        return 'Comederos'
    if re.search(r'bebedero|fuente de agua (para|de) (perro|gato|mascota)', tn): return 'Bebederos'
    if re.search(r'\bcorrea|\bpechera|\barnes\b|\bcollar\b', tn): return 'Correas'
    if re.search(r'casa (para|de) (perro|gato|mascota)|caseta|rascador|torre para gato', tn):
        return 'Casas para mascotas'
    if re.search(r'\bcama\b|colchoneta|cojin (para|de) (perro|gato|mascota)|\bpet bed\b|'
                 r'\bdog bed\b|\bnido\b|tapete|alfombrilla|almohadilla', tn): return 'Camas'
    if re.search(r'juguete|pelota|\bkong\b|\bcatnip\b|hueso|mordedor|rat[oó]n de peluche|'
                 r'\btoy(s)?\b|squeaky|\bchew\b|\bfetch\b|disco volador|\bfrisbee\b|varita|'
                 r'alfombra olfativa|\bsnuffle\b|\btunel\b', tn):
        return 'Juguetes'
    return None


def sub_vigilancia(tn):
    """Reparte Cámaras de seguridad.

    El timbre y la cerradura van ANTES que la cámara: los dos traen cámara y
    la nombran en el título ("Videotimbre E340, Cámara Dual 2K").
    """
    if re.search(r'\btimbre|videotimbre|video ?doorbell|doorbell', tn): return 'Timbres inteligentes'
    if re.search(r'cerradura|chapa intelig|smart lock', tn): return 'Cerraduras inteligentes'
    if re.search(r'\balarma|sirena|antirrobo', tn): return 'Alarmas'
    if re.search(r'\bsensor|detector de (movimiento|humo|apertura)', tn): return 'Sensores'
    if re.search(r'\bkit\b|\bnvr\b|\bdvr\b|\d ?canales|juego de \d camaras|\d camaras\b', tn):
        return 'Kits de vigilancia'
    if re.search(r'\bptz\b|motorizada|zoom optico \d+x|seguimiento automatico', tn): return 'Cámaras PTZ'
    if re.search(r'espia|oculta|camuflaj|\bmini camara\b|llavero', tn): return 'Cámaras espía'
    if re.search(r'exterior|intemperie|\bip6[5-8]\b|impermeable|solar', tn): return 'Cámaras exteriores'
    if re.search(r'interior|\bbebe\b|mascota|\bindoor\b', tn): return 'Cámaras interiores'
    if re.search(r'camara', tn): return 'Cámaras interiores'
    return None


def sub_juguete(tn):
    """Reparte Juguetes y bebés.

    Lo de bebé (carriola, silla de auto, cuna) va primero: son productos
    caros y bien nombrados, y varios dicen además "juguete" o "juego".
    """
    # El "travel system" trae carriola Y silla de auto; se cataloga como
    # carriola, que es como lo busca quien lo compra.
    if re.search(r'carriola|cochecito (de|para) bebe|\bstroller\b|silla de paseo|'
                 r'travel system|sistema de viaje', tn): return 'Carriolas'
    if re.search(r'silla (de|para) auto|autoasiento|\bcar seat\b|'
                 r'asiento (para|de) (coche|auto|carro) (infantil|de bebe|para bebe)', tn):
        return 'Sillas de auto'
    if re.search(r'\bcuna\b|moises|\bcorral\b', tn): return 'Cunas'
    if re.search(r'andadera|caminadora de bebe', tn): return 'Andaderas'
    if re.search(r'biberon|mamila|chupon|esterilizador de biberon', tn): return 'Biberones'
    if re.search(r'monitor (de|para) bebe|baby monitor', tn): return 'Monitores de bebé'
    if re.search(r'trampolin|brincolin', tn): return 'Trampolines'
    if re.search(r'triciclo', tn): return 'Triciclos'
    if re.search(r'montable|correpasillos|carro montable', tn): return 'Montables'
    if re.search(r'\bmaqueta|modelismo|escala 1 ?[:/] ?\d|\bdie-?cast\b|fundido a presion|'
                 r'rompecabezas 3d|puzzle 3d|\bdiorama\b', tn): return 'Maquetas'
    if re.search(r'figura de accion|\bfunko\b|\bmarvel\b|\bdc\b comics|transformers', tn):
        return 'Figuras de acción'
    if re.search(r'bloques|\blego\b|\bmega bloks\b|construccion', tn): return 'Bloques de construcción'
    if re.search(r'\bmuneca|\bbarbie\b|\bnenuco\b|\bbebote\b', tn): return 'Muñecas'
    if re.search(r'peluche|\bplush\b', tn): return 'Peluches'
    if re.search(r'control remoto|radiocontrol|\brc\b\b', tn): return 'Vehículos a control remoto'
    if re.search(r'\bcarrito|\bcamion\b|monster truck|hot ?wheels|pista de carreras', tn):
        return 'Vehículos de juguete'
    if re.search(r'educativo|didactic|\bstem\b|aprendizaje|montessori', tn): return 'Juguetes educativos'
    if re.search(r'juego (de|para) exterior|resbaladilla|columpio|casita de jardin|alberca', tn):
        return 'Juegos de exterior'
    if re.search(r'arcade|maquinita', tn): return 'Juegos arcade'
    if re.search(r'instrumento|tambor|xilofono|piano de juguete', tn): return 'Juguetes musicales'
    return None


def sub_camara(tn):
    # El cargador o la batería que abren el título son accesorio aunque
    # nombren la cámara (el cargador Panasonic "para Lumix" caía en
    # Mirrorless): solo en la cabeza, para no tocar la cámara "con batería
    # extra".
    if re.search(r'^(?:\S+ ){0,5}(cargador|bateria|baterias|estacion de carga|puerta de bateria|paquete de \d+ baterias|'
                 r'soporte|adaptador|montaje|kit de montaje|cabeza de bola|cabezal|brazo|placa|abrazadera|monopie|'
                 r'marco|clip|tether|lanyard|correa)\b', tn): return 'Accesorios'
    if re.search(r'gopro|camara (de )?accion|action cam|insta ?360|\bsjcam\b|\bakaso\b|dji (osmo|action)', tn): return 'Cámaras de acción'
    if re.search(r'instantanea|instax|polaroid', tn): return 'Instantáneas'
    if re.search(r'videocamara|camcorder|filmadora', tn): return 'Videocámaras'
    if re.search(r'mirrorless|sin espejo|\balpha\b|\bzv-?e\b|\bx-?[the]\d|\bx100\b|\bgfx\b|\blumix\b|om system|\bom-?\d\b', tn): return 'Mirrorless'
    if re.search(r'reflex|\bdslr\b|\beos\b.{0,10}\d|\bd\d{3,4}\b', tn): return 'Réflex'
    # "lente" a secas se llevaba la cámara térmica ("lente de germanio"), el
    # domo IP y la grabadora láser: la subcategoría es para el objetivo
    # intercambiable, que dice su focal o su montura.
    if re.search(r'(lente|objetivo) .{0,30}(\bmm\b|f/|canon|nikon|sony|fujifilm|sigma|tamron|\bef\b|\brf\b|\bz\b)|'
                 r'teleobjetivo|(lente|objetivo) gran angular', tn): return 'Lentes'
    if re.search(r'tripie|tripode|estabilizador|gimbal|flash|filtro|correa|'
                 r'bolsa|mochila|bateria|cargador|tarjeta', tn): return 'Accesorios'
    if re.search(r'drone|dron\b', tn): return 'Accesorios'
    # La compacta es la que no es ninguna de las anteriores y se vende como
    # "cámara digital" a secas (365 fichas de la captura del 16-sep caían
    # sin subcategoría). Va al final de todo: puesta antes de Accesorios se
    # llevaba la "batería para cámara digital".
    if re.search(r'camara (digital|compacta|de fotos|fotografica|4k|para vlog|de vlog|deportiva|corporal|montada)|'
                 r'mini camara|\bvlog', tn): return 'Compactas'
    return None


def sub_almacenamiento(tn):
    if re.search(r'\bnas\b', tn): return 'NAS'
    if re.search(r'tarjeta|micro ?sd|sdxc|sdhc|cfexpress|\bsd card', tn): return 'Tarjetas de memoria'
    if re.search(r'memoria usb|unidad(es)? flash|pendrive|usb flash|flash drive|memoria flash|datatraveler|'
                 r'\bstick\b|usb (2\.0|3\.[0-2]|tipo c|type-?c)', tn): return 'Memorias USB'
    if re.search(r'externo|portatil|my passport|\belements\b|canvio|\bt7\b|\bt9\b|\bexpansion\b', tn): return 'Externo'
    if re.search(r'\bssd\b|nvme|m\.2|estado solido', tn): return 'SSD'
    if re.search(r'disco duro|\bhdd\b|\bsata\b|\bsas\b|\bst\d{4,}[a-z]*\b|\b\d+ ?tb\b', tn): return 'Interno'
    if re.search(r'\busb\b|ironkey|cruzer|\bdt\d+', tn): return 'Memorias USB'
    return None


def sub_herramienta(tn):
    """Reparte Herramientas. La categoría tenía quince subcategorías y las
    reglas solo alcanzaban a tres, así que una captura de ferretería entraba
    al 17%: de 4,227 anuncios, 2,985 caían en "no encaja"."""
    if re.search(r'cerradura|cerrojo|candado|\bchapa\b|picaporte', tn):
        return 'Cerraduras y candados'
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
                 r'panel de herramientas|\bcarr(o|ito)s? .{0,40}herramientas|carr(o|ito)s? (utilitario|de servicio|rodante|de plastico)', tn):
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
                            r'oneplus|infinix|\btecno\b|google|apple|iphone|nubia|alcatel|lanix|bmobile|blackview|doogee|'
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
# Se probó agregar "\bbt\b", "anc" y "cancelación de ruido" para rescatar
# los títulos que llevan la conexión en la sigla ("Jbl Tune 530 Bt"), y la
# regresión lo tiró: la cancelación activa SÍ existe con cable --Jabra
# Evolve2 40, EPOS Impact 860, Dell Pro WH5024 son diademas ANC con
# cable-- y 72 fichas bien clasificadas se volvieron inalámbricas o se
# quedaron sin clasificar. La sigla suelta no alcanza para afirmar.
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
    elif cat == 'Herramientas': sub = sub_herramienta(tn) or sub
    elif cat == 'Juegos de mesa': sub = sub_juego_mesa(tn)
    elif cat == 'Instrumentos musicales': sub = sub_instrumento(tn)
    elif cat == 'Iluminación': sub = sub_iluminacion(tn)
    elif cat == 'Autos, bicicletas y motos': sub = sub_vehiculo(tn)
    elif cat == 'Domótica y hogar inteligente': sub = sub_domotica(tn)
    # Los repartidores nuevos van con "or sub": solo AGREGAN subcategoría,
    # nunca borran la que la regla de categoría ya había puesto. Sin eso,
    # sub_escritorio() devolvía None para "Panel PC Industrial All-in-One" y
    # para el iMac --41 fichas-- y les quitaba el "All in One" que ya
    # tenían. Los repartidores viejos se dejan como estaban: su
    # comportamiento está calibrado contra las 16 capturas.
    elif cat == 'Suplementos': sub = sub_suplemento(tn) or sub
    elif cat == 'Redes': sub = sub_red(tn) or sub
    elif cat == 'Climatización': sub = sub_clima(tn) or sub
    elif cat == 'Belleza y cuidado personal': sub = sub_belleza(tn) or sub
    elif cat == 'Mascotas': sub = sub_mascota(tn) or sub
    elif cat == 'Cámaras de seguridad': sub = sub_vigilancia(tn) or sub
    elif cat == 'Juguetes y bebés': sub = sub_juguete(tn) or sub
    elif cat == 'Deportes y fitness': sub = sub_deporte(tn) or sub
    elif cat == 'Joyería y bisutería': sub = sub_joyeria(tn) or sub
    elif cat == 'Impresoras': sub = sub_impresora(tn) or sub
    elif cat == 'Computadoras de escritorio': sub = sub_escritorio(tn) or sub
    elif cat == 'Blancos y ropa de cama': sub = sub_blancos(tn) or sub
    elif cat == 'Relojes inteligentes': sub = sub_reloj(tn) or sub
    elif cat == 'Cámaras y fotografía': sub = sub_camara(tn)
    elif cat == 'Almacenamiento': sub = sub_almacenamiento(tn)
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
