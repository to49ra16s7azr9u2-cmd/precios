#!/usr/bin/env python3
"""El escalón del medio: familias de subcategorías dentro de una categoría.

POR QUÉ HACE FALTA
------------------
El catálogo tiene 990 subcategorías en 57 categorías, y Muebles sola tiene 69.
La capa de roles (roles_subcategorias.py) ya separa el producto del accesorio
y de la refacción, pero adentro de «Productos» de Muebles siguen quedando unos
cincuenta chips seguidos donde «Sillas de oficina» y «Colchones king size»
cuelgan al mismo nivel. Eso no se lee.

Es el mismo problema que resuelve kakaku.com con su escalón intermedio:
パソコン no lista sus 125 subcategorías de corrido, las agrupa en ノートパソコン,
デスクトップ, PCパーツ… y recién ahí abre. Esto es ese escalón.

DE DÓNDE SALE CADA FAMILIA
--------------------------
Por dos caminos, y el orden importa:

  1. Lo que la tabla FAMILIAS diga, si la categoría está ahí. Hace falta donde
     el nombre no dice a qué familia pertenece: nada en «Llaves y dados» ni en
     «Taladros y rotomartillos» indica que una es herramienta manual y la otra
     eléctrica, y en Herramientas eso deja 39 subcategorías sueltas.

  2. Lo que quede, deducido del nombre: las subcategorías que empiezan con el
     mismo sustantivo son familia. «Sillas de oficina», «Sillas gamer» y
     «Sillas de comedor» son «Sillas»; «Ventiladores de techo», «de pedestal»
     y «de torre» son «Ventiladores». Sale gratis y acierta en Climatización,
     Mascotas y Blancos.

Las dos vías se suman, no se excluyen. La tabla sólo tiene que nombrar lo que
la deducción no ve; escribir «Cocina» en Muebles no cuesta también escribir
«Sillas», «Mesas» y «Colchones», que salen solas.

Una familia necesita al menos dos subcategorías: una sola no es un grupo, es
la subcategoría con un título encima.

QUÉ NO AGRUPA
-------------
Sólo mira las subcategorías de rol «producto». El accesorio, la refacción y el
consumible ya tienen su propio corte en roles_subcategorias.py, y meterles
familias encima sería un tercer nivel sobre un segundo que ya existe.

USO
---
    from familias_subcategorias import agrupar
    for familia, subs in agrupar(categoria, subcategorias):
        ...
    python3 scripts/familias_subcategorias.py        # revisar el resultado
"""
import collections
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roles_subcategorias import PRODUCTO, rol_de  # noqa: E402

MIN_SUBS = 2          # una sola subcategoría no hace familia
MIN_FICHAS = 120      # y una familia sin fichas tampoco: Libros deducía
                      # «Novela» y «Ciencia» con cero productos adentro
SIN_FAMILIA = None    # las que no entran en ninguna van sueltas, al final

# Las categorías donde el nombre de la subcategoría no dice de qué familia es.
# El orden de las familias es el orden en que se muestran: primero lo que más
# se compra.
FAMILIAS = {
    "Herramientas": [
        ("Herramienta eléctrica", [
            "Taladros y rotomartillos", "Atornilladores", "Sierras",
            "Esmeriladoras y pulidoras", "Lijadoras",
            "Routers, fresadoras y multiherramientas",
            "Pistolas de calor, engrapadoras y clavadoras",
            "Herramientas de banco", "Herramientas eléctricas",
            "Baterías y cargadores de herramienta", "Grabado láser"]),
        ("Herramienta manual", [
            "Llaves y dados", "Desarmadores y puntas", "Pinzas y alicates",
            "Martillos, cinceles y mazos", "Herramientas de corte manual",
            "Prensas y sujeción", "Herramientas manuales",
            "Juegos de herramientas"]),
        ("Plomería y baño", [
            "Plomería", "Grifos y monomandos", "Regaderas y duchas",
            "Tarjas y fregaderos", "Bombas de agua", "Tuberías y conexiones",
            "Sanitarios y accesorios de baño"]),
        ("Instalación eléctrica", [
            "Apagadores y contactos", "Placas y tapas eléctricas",
            "Generadores", "Soldadura"]),
        ("Jardín y exterior", [
            "Jardinería", "Podadoras y cortacésped", "Hidrolavadoras"]),
        ("Aire comprimido", [
            "Neumáticas", "Compresores y herramienta neumática",
            "Flejadoras y empacadoras"]),
        ("Medición y seguridad", [
            "Medición", "Seguridad industrial", "Cerraduras y candados"]),
        ("Obra y taller", [
            "Construcción", "Escaleras", "Organización", "Gas LP"]),
    ],
    "Electrodomésticos": [
        ("Cocción", [
            "Estufas", "Hornos", "Microondas", "Parrillas y planchas eléctricas",
            "Wafleras, sandwicheras y creperas", "Tostadoras",
            "Arroceras y ollas multiusos", "Vaporeras y hervidores de huevos",
            "Máquinas de pan y pasta"]),
        ("Freidoras", [
            "Freidoras de aire", "Freidoras de aire hasta 3 L",
            "Freidoras de aire de 3.5 a 5 L", "Freidoras de aire de 5.5 a 7 L",
            "Freidoras de aire de 8 L o más",
            "Freidoras de aire de doble canasta", "Freidoras eléctricas",
            "Hornos freidora y multifunción"]),
        ("Preparación de alimentos", [
            "Licuadoras", "Batidoras y amasadoras", "Extractores de jugo",
            "Molinos y procesadores", "Máquinas de helados y postres",
            "Máquinas de palomitas y snacks",
            "Pequeños electrodomésticos de cocina",
            "Otros electrodomésticos de cocina"]),
        ("Agua y purificación", [
            "Purificadores bajo tarja", "Purificadores de grifo y encimera",
            "Ósmosis inversa", "Destiladores e ionizadores",
            "Jarras y botellas con filtro",
            "Ablandadores y filtros de casa completa",
            "Dispensadores de agua", "Purificadores de agua",
            "Calentadores de agua"]),
        ("Limpieza y ropa", [
            "Planchas", "Vaporizadores de ropa", "Lavavajillas",
            "Robots limpiacristales", "Máquinas de coser"]),
    ],
    "Refacciones": [
        ("Para auto", [
            "Para autos", "Frenos", "Carrocería, espejos y molduras",
            "Sistema eléctrico y sensores", "Faros y luces",
            "Motor y transmisión", "Filtros y aceites",
            "Suspensión y dirección", "Escape", "Bujías y encendido",
            "Motores", "Bombas", "Limpiaparabrisas", "Interior y tapicería",
            "Llaves y cerraduras de auto"]),
        ("Para moto", [
            "Para motos", "Carenados, plásticos y tanques", "Luces de moto",
            "Manubrios, espejos y controles", "Eléctrico y baterías de moto",
            "Motor, carburación y escape de moto",
            "Asientos, parrillas y accesorios de moto",
            "Suspensión y dirección de moto", "Frenos de moto",
            "Cadenas, sprockets y transmisión", "Llantas y cámaras de moto",
            "Filtros y aceites de moto"]),
        ("Para electrodomésticos", [
            "Refacciones para refrigerador", "Refacciones para aspiradora y robot",
            "Refacciones para otros electrodomésticos",
            "Refacciones para lavadora y secadora",
            "Refacciones para electrodomésticos",
            "Refacciones para freidora de aire",
            "Refacciones para licuadora y batidora",
            "Refacciones para plancha y vaporizador",
            "Refacciones para cafetera", "Refacciones para microondas",
            "Refacciones para estufa y horno", "Enfriamiento y climatización",
            "Refacciones para aire acondicionado y ventilador",
            "Refacciones para bocinas y audio"]),
        ("Para movilidad eléctrica", [
            "Para patinetas eléctricas", "Para bicicletas eléctricas"]),
    ],
    "Monitores": [
        ("Por tamaño", [
            "Hasta 22 pulgadas", "23 a 25 pulgadas", "27 pulgadas",
            "28 a 34 pulgadas", "35 pulgadas o más"]),
        ("Por uso", [
            "Gaming", "Monitores 4K y profesionales", "Ultrawide y curvos",
            "Táctiles e industriales", "Portátiles"]),
    ],
    "Bocinas": [
        ("Bluetooth y portátiles", [
            "Bocinas Bluetooth", "Bocinas Bluetooth compactas (hasta 20 W)",
            "Bocinas Bluetooth medianas (20 a 60 W)",
            "Bocinas Bluetooth potentes (60 W o más)",
            "Bocinas Bluetooth impermeables", "Bocinas con luces LED",
            "Bocinas Bluetooth con radio, USB y micrófono",
            "Mini bocinas y de llavero"]),
        ("Para la casa", [
            "Barras de sonido", "De estantería y Hi-Fi", "Subwoofers",
            "Empotrables y de exterior", "Radios y reproductores",
            "Amplificadores y receptores", "Para PC y escritorio"]),
        ("Sonido profesional", ["Bafles y audio profesional",
                                "De fiesta y karaoke"]),
    ],
    "Blancos y ropa de cama": [
        ("Cama", [
            "Sábanas", "Sábanas individuales", "Sábanas matrimoniales",
            "Sábanas queen size", "Sábanas king size",
            "Sábanas para cuna y bebé", "Fundas de almohada",
            "Fundas nórdicas y de edredón", "Almohadas", "Edredones",
            "Cobijas"]),
        ("Protección de colchón", [
            "Protectores de colchón", "Protectores de colchón impermeables",
            "Protectores de colchón acolchados", "Toppers y sobrecolchones",
            "Protectores de almohada", "Protectores para cuna"]),
        ("Calor eléctrico", [
            "Cobijas eléctricas", "Cobijas eléctricas individuales",
            "Cobijas eléctricas matrimoniales",
            "Cobijas eléctricas queen y king",
            "Mantas eléctricas USB y portátiles",
            "Chales y mantas eléctricas para regazo",
            "Almohadillas y cojines térmicos"]),
        ("Baño", [
            "Toallas", "Toallas de baño", "Toallas de manos y faciales",
            "Juegos de toallas", "Toallas de playa y alberca",
            "Batas y toallas con capucha", "Tapetes de baño"]),
        ("Resto de la casa", [
            "Cortinas", "Fundas para muebles", "Toallas de cocina y paños",
            "Toallas de microfibra y deportivas"]),
    ],
    "Iluminación": [
        ("De techo", [
            "Lámparas colgantes", "Candiles y arañas",
            "Plafones y lámparas de sobreponer", "Rieles y spots",
            "Empotrada", "Ventiladores con luz"]),
        ("De pie y de mesa", [
            "Lámparas de piso", "Lámparas de escritorio", "Lámparas de pared"]),
        ("Exterior e industrial", [
            "Exterior", "Lámparas de techo para exterior",
            "Lámparas industriales y de nave", "Lámparas de emergencia"]),
        ("Decorativa y de efecto", ["Tiras LED", "Decorativa", "Escenario"]),
    ],
    "Climatización": [
        ("Enfriar", [
            "Minisplit", "Aires acondicionados", "Aires acondicionados portátiles",
            "Aires acondicionados de ventana",
            "Aires acondicionados para auto y RV", "Mini enfriadores personales",
            "Climatizadores evaporativos"]),
        ("Calidad del aire", [
            "Purificadores de aire", "Deshumidificadores", "Humidificadores",
            "Extractores y ventilación"]),
    ],
    "Teclados": [
        ("Mecánicos", [
            "Mecánicos", "Mecánicos 60% y compactos", "Mecánicos 65% y 75%",
            "Mecánicos TKL (80%)", "Mecánicos tamaño completo",
            "Mecánicos inalámbricos"]),
        ("De membrana y oficina", [
            "Membrana", "Inalámbricos", "Combos con mouse", "Numéricos",
            "Ergonómicos"]),
    ],
    "Joyería y bisutería": [
        ("Relojes", [
            "Relojes", "Relojes para hombre", "Relojes para mujer",
            "Relojes infantiles", "Relojes deportivos y digitales",
            "Relojes de bolsillo y de pared"]),
        ("Joyería", [
            "Aretes", "Collares", "Pulseras", "Anillos", "Dijes y charms",
            "Arras y sets"]),
    ],
    # Mascotas deduce solas «Jaulas», «Camas», «Comederos» y «Juguetes»; acá
    # van las que quedan, agrupadas por lo que el dueño va a hacer con ellas.
    "Mascotas": [
        ("Descanso y refugio", [
            "Cuevas, iglús y tiendas para mascotas",
            "Cojines y mantas para mascotas", "Casas para mascotas",
            "Rascadores y torres"]),
        ("Alimentación", [
            "Platos y tazones para mascotas", "Fuentes y dispensadores de agua",
            "Tapetes y accesorios de alimentación", "Bebederos"]),
        ("Paseo y adiestramiento", [
            "Transportadoras", "Correas", "Adiestramiento",
            "Puertas para mascotas", "Ropa y accesorios"]),
        ("Higiene", ["Areneros", "Higiene y limpieza"]),
    ],
    "Cocina y comedor": [
        ("Beber", [
            "Termos y botellas térmicas", "Botellas de agua",
            "Vasos térmicos y de viaje", "Tazas", "Vasos y copas",
            "Jarras y dispensadores de bebidas",
            "Botellas de vidrio y plástico", "Bar y coctelería"]),
        ("Cocinar", [
            "Ollas de presión", "Ollas y cacerolas", "Sartenes y comales",
            "Baterías de cocina", "Repostería y moldes",
            "Utensilios de cocina", "Cuchillos y tablas",
            "Básculas y medidores"]),
        ("Servir la mesa", ["Platos y bowls", "Vajillas", "Cubiertos"]),
        ("Guardar", [
            "Contenedores herméticos", "Tarros y frascos",
            "Loncheras y termos para alimentos", "Organización de cocina"]),
    ],
    # Domótica deduce «Cerraduras», «Interruptores», «Enchufes» y «Lámparas»
    # por separado, y son cuatro trozos de dos cosas: lo que abre y lo que
    # enciende. La tabla los junta.
    "Domótica y hogar inteligente": [
        ("Cerraduras y candados", [
            "Cerraduras con huella digital", "Cerraduras con teclado y código",
            "Cerraduras Wi-Fi y con app", "Cerraduras de puerta inteligentes",
            "Cerraduras para gabinete y casillero",
            "Cerraduras para puerta de vidrio y corrediza",
            "Candados inteligentes", "Cerraduras inteligentes"]),
        ("Interruptores y enchufes", [
            "Enchufes inteligentes", "Interruptores Wi-Fi",
            "Interruptores Zigbee, Matter y Thread",
            "Dimmers y reguladores inteligentes",
            "Módulos y relés inteligentes",
            "Interruptores y botones inalámbricos",
            "Breakers y protectores inteligentes",
            "Enchufes y contactos inteligentes",
            "Interruptores táctiles y de escena",
            "Interruptores inteligentes"]),
        ("Iluminación", [
            "Focos inteligentes", "Tiras LED inteligentes",
            "Lámparas y plafones inteligentes",
            "Luces inteligentes de exterior y solares",
            "Paneles y luces decorativas inteligentes",
            "Controladores e interruptores de luz",
            "Lámparas de escritorio y noche inteligentes",
            "Iluminación inteligente"]),
        ("Control y sensores", [
            "Bocinas inteligentes", "Hubs", "Cortinas motorizadas",
            "Sensores", "Termostatos"]),
    ],
    "Cargadores y adaptadores": [
        ("Cargadores de pared", [
            "Cargadores de pared hasta 20 W", "Cargadores de pared de 25 a 45 W",
            "Cargadores de pared de 65 W o más", "Cargadores de pared con cable",
            "Cargadores multipuerto y estaciones de carga", "De pared"]),
        ("Inalámbricos", ["Inalámbrico", "Base de carga",
                          "Cargadores para reloj y accesorios pequeños"]),
        ("Para otros aparatos", [
            "De auto", "Para laptop", "De pilas", "Para herramientas",
            "Adaptador de corriente"]),
    ],
    # Muebles deduce solas «Sillas», «Mesas», «Escritorios», «Colchones»,
    # «Sofás» y «Camas»; acá sólo van las que el nombre no junta.
    "Muebles": [
        ("Comedor", [
            "Mesas de comedor", "Mesas de comedor extensibles",
            "Mesas de comedor para exterior", "Juegos de comedor",
            "Bancas de comedor", "Antecomedores y mesas de cocina",
            "Mesas altas y de bar"]),
        ("Cocina", [
            "Cocinas integrales", "Alacenas y gabinetes de cocina",
            "Muebles de cocina", "Carros e islas de cocina",
            "Encimeras y cubiertas"]),
        ("Dormitorio", [
            "Bases de cama y box", "Cabeceras", "Literas",
            "Camas individuales", "Camas matrimoniales", "Camas queen y king",
            "Camas infantiles", "Camas plegables y catres", "Camas"]),
        ("Almacenamiento", [
            "Roperos", "Libreros", "Repisas", "Zapateras", "Percheros",
            "Burós"]),
    ],
    "Belleza y cuidado personal": [
        ("Maquillaje", [
            "Bases y correctores", "Labiales", "Polvos, rubores y bronceadores",
            "Sombras y delineadores", "Máscaras de pestañas y cejas",
            "Maquillaje", "Paletas y sets de maquillaje",
            "Primers y fijadores", "Pestañas postizas", "Brochas y esponjas",
            "Organizadores de maquillaje"]),
        ("Cuidado facial", [
            "Cremas y sérums faciales", "Mascarillas faciales",
            "Limpiadores y tónicos", "Exfoliantes y peelings",
            "Contorno de ojos y labios", "Dispositivos de cuidado facial",
            "Faciales", "Cuidado facial masculino", "Protección solar"]),
        ("Cabello", [
            "Secadoras de cabello", "Planchas para cabello", "Rizadores",
            "Extensiones de cabello", "Pelucas", "Cuidado del cabello",
            "Estilizadores"]),
        ("Afeitado y depilación", ["Rasuradoras", "Depilación"]),
        ("Uñas", ["Uñas", "Manicure"]),
        ("Cuerpo y spa", [
            "Corporales", "Masajeadores", "Vaporizadores y equipo de spa",
            "Perfumes", "Cuidado personal"]),
    ],
    "Deportes y fitness": [
        ("Fuerza", [
            "Mancuernas", "Sets de pesas", "Pesas", "Kettlebells",
            "Barras y discos", "Bancos y racks", "Equipo de gimnasio",
            "Máquinas multifuncionales y poleas", "Máquinas de abdominales",
            "Pesas de tobillo y chalecos con peso",
            "Barras de dominadas y calistenia"]),
        ("Cardio", ["Bicicletas fijas", "Máquinas de cardio"]),
        ("Entrenamiento funcional", [
            "Bandas de resistencia", "Yoga", "Tablas y balance",
            "Protección y soportes"]),
        ("Deportes de equipo", ["Balones", "Voleibol", "Fútbol"]),
        ("Raqueta y precisión", ["Raquetas", "Ping pong", "Dardos"]),
        ("Agua y exterior", [
            "Natación", "Deportes acuáticos", "Patines y patinetas",
            "Campismo"]),
    ],
    "Juguetes y bebés": [
        ("Juguetes", [
            "Muñecas", "Figuras de acción", "Peluches",
            "Bloques de construcción", "Maquetas", "Juguetes educativos",
            "Juguetes musicales", "Juguetes para bebé", "Vehículos de juguete",
            "Vehículos a control remoto", "Juegos arcade",
            "Juguetes para exterior", "Trampolines", "Montables",
            "Triciclos"]),
        ("Paseo y transporte", [
            "Carriolas", "Sillas de auto", "Portabebés y canguros",
            "Andaderas"]),
        ("Alimentación", [
            "Alimentación y lactancia", "Biberones", "Chupones y mordederas",
            "Sillas de comer y mecedoras"]),
        ("Higiene y cuidado", [
            "Pañales y cambio", "Baño e higiene del bebé",
            "Cuidado y salud del bebé", "Ropa y calzado de bebé"]),
        ("Dormir y seguridad", [
            "Cunas", "Corrales", "Seguridad para bebé", "Monitores de bebé",
            "Bebés"]),
    ],
    "Instrumentos musicales": [
        ("Cuerdas", [
            "Guitarras eléctricas", "Guitarras acústicas",
            "Guitarras electroacústicas", "Guitarras clásicas", "Bajos",
            "Ukuleles", "Violines, mandolinas y otras cuerdas"]),
        ("Percusión", [
            "Percusión", "Baterías acústicas", "Baterías electrónicas",
            "Baterías", "Platillos", "Tarolas y cajas"]),
        ("Viento", [
            "Saxofones", "Trompetas, trombones y metales",
            "Clarinetes y oboes", "Flautas traversas", "Armónicas y melódicas",
            "Ocarinas, silbatos y flautas dulces",
            "Instrumentos de viento digitales", "Viento"]),
        ("Teclados", [
            "Pianos digitales", "Teclados electrónicos",
            "Sintetizadores y controladores MIDI", "Acordeones",
            "Órganos y otros teclados"]),
        ("Amplificación y efectos", [
            "Amplificadores de guitarra y bajo", "Amplificadores",
            "Pedales y efectos"]),
    ],
}

# Palabras que no pueden ser la cabeza de una familia.
_VACIAS = {"de", "para", "y", "con", "en", "del", "la", "el", "los", "las",
           "otros", "otras", "otro", "otra", "a", "por", "sin", "e"}


def _plano(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def _cabeza(nombre):
    """El sustantivo con el que abre el nombre de la subcategoría."""
    for w in re.split(r"[^a-z0-9]+", _plano(nombre)):
        if w and len(w) > 2 and w not in _VACIAS:
            return w
    return None


# Cabezas que son una unidad de medida, no un producto: «23 a 25 pulgadas» y
# «27 pulgadas» son una familia de verdad, pero llamarla «Pulgadas» no dice
# nada. Lo que las junta es el tamaño.
_UNIDADES = {"pulgadas", "pulgada", "litros", "watts", "plazas", "mah",
             "kilos", "metros"}


def _titulo(cabeza, nombres):
    """El nombre de la familia deducida.

    Es el prefijo de palabras que comparten TODOS los nombres del grupo, no
    sólo la primera: «Aires acondicionados portátiles», «de ventana» y «para
    auto y RV» comparten «Aires acondicionados», y llamar a esa familia
    «Aires» a secas quedaba raro. Si no comparten más que la cabeza, se usa la
    cabeza tal como está escrita en el nombre más corto.
    """
    if cabeza in _UNIDADES:
        return "Por tamaño"
    palabras = [re.split(r"\s+", n.strip()) for n in nombres]
    comun = []
    for i in range(min(len(p) for p in palabras)):
        w = palabras[0][i]
        if all(_plano(p[i]) == _plano(w) for p in palabras):
            comun.append(w)
        else:
            break
    if comun:
        return " ".join(comun).rstrip(" ,")
    corto = min(nombres, key=len)
    primera = re.split(r"[^\wÁÉÍÓÚÜÑáéíóúüñ]+", corto)[0]
    return primera if _plano(primera) == cabeza else cabeza.capitalize()


def agrupar(categoria, subcategorias, cuenta=None):
    """[(familia | None, [subcategorías])] en el orden en que se muestran.

    `subcategorias` son los nombres; `cuenta` es un dict opcional
    {subcategoría: fichas} que se usa para ordenar las familias deducidas por
    tamaño. Las que no entran en ninguna familia salen al final con
    familia None, que el que dibuja muestra sin encabezado.
    """
    quedan = [s for s in subcategorias if rol_de(categoria, s) == PRODUCTO]
    otras = [s for s in subcategorias if rol_de(categoria, s) != PRODUCTO]
    if not quedan:
        return [(SIN_FAMILIA, list(subcategorias))]

    salida, usadas = [], set()
    presentes = set(quedan)
    # La tabla va primero y la deducción DESPUÉS, sobre lo que la tabla no
    # reclamó. Al principio la tabla reemplazaba a la deducción, y entonces
    # escribir una familia nueva en una categoría obligaba a escribirlas
    # todas: agregar «Cocina» a Muebles hacía desaparecer «Sillas»,
    # «Colchones» y «Mesas», que salían solas y estaban bien.
    for familia, miembros in FAMILIAS.get(categoria, []):
        hay = [m for m in miembros if m in presentes]
        if len(hay) >= MIN_SUBS:
            salida.append((familia, hay))
            usadas.update(hay)

    porcabeza = collections.defaultdict(list)
    for x in quedan:
        if x in usadas:
            continue
        c = _cabeza(x)
        if c:
            porcabeza[c].append(x)
    grupos = [(c, v) for c, v in porcabeza.items() if len(v) >= MIN_SUBS]
    if cuenta:
        grupos.sort(key=lambda kv: -sum(cuenta.get(x, 0) for x in kv[1]))
    else:
        grupos.sort(key=lambda kv: -len(kv[1]))
    for c, v in grupos:
        if cuenta and sum(cuenta.get(x, 0) for x in v) < MIN_FICHAS:
            continue
        salida.append((_titulo(c, v), v))
        usadas.update(v)

    sueltas = [s for s in quedan if s not in usadas] + otras
    if sueltas:
        salida.append((SIN_FAMILIA, sueltas))
    return salida


def familia_de(categoria, subcategoria, subcategorias):
    """La familia de esa subcategoría, o None si va suelta."""
    for familia, miembros in agrupar(categoria, subcategorias):
        if subcategoria in miembros:
            return familia
    return None


def main():
    from data_io import load_catalog
    data = load_catalog()
    cuenta = collections.Counter(
        (p.get("category"), p.get("subcategory")) for p in data["products"])
    for c in data["categories"]:
        subs = [s["id"] for s in (c.get("subcategories") or [])]
        if len(subs) < 8:
            continue
        por_sub = {s: cuenta[(c["id"], s)] for s in subs}
        grupos = agrupar(c["id"], subs, por_sub)
        con = [g for g in grupos if g[0]]
        if not con:
            continue
        de_tabla = " (tabla)" if c["id"] in FAMILIAS else " (deducidas)"
        print(f"=== {c['id']}: {len(con)} familias{de_tabla}")
        for familia, miembros in grupos:
            n = sum(por_sub.get(m, 0) for m in miembros)
            etq = familia or "· sueltas"
            print(f"   {n:>6,}  {etq:<26} {len(miembros):>2} subcategorías")
    return 0


if __name__ == "__main__":
    sys.exit(main())
