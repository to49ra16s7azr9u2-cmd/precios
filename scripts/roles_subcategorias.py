"""Qué papel juega cada subcategoría dentro de su categoría.

DE DÓNDE SALE LA IDEA
---------------------
De cómo ordena kakaku.com su portada de パソコン (PC). No lista sus 125
subcategorías en plano: las agrupa por papel --パソコン本体 (12, las
máquinas), 周辺機器 (64, periféricos), パーツ (18, componentes),
ドライブ・ストレージ (18), ネットワーク機器 (13)-- y por eso "la laptop más
barata" significa ahí la laptop más barata, no el cable más barato.

ComparaMEX tenía sus 966 subcategorías en plano, y se notaba en tres sitios:

  - /barato/<categoría>/ abría con el accesorio, no con el producto. Medido
    el 21 de septiembre de 2026: "el refrigerador más barato" era un filtro
    de vegetales de $199 y "el televisor más barato" un Fire Stick de $588.
    Se tapó con una guardia de atípicos (descartar lo que vale menos del 15%
    de la mediana de su subcategoría), que funciona pero es un parche: la
    pregunta no es cuánto vale, es qué es.
  - Los rankings ponían cables al lado de laptops.
  - Los chips de la página de categoría eran una lista larga sin jerarquía.

EL PAPEL ES RELATIVO A LA CATEGORÍA
-----------------------------------
No se puede sacar del nombre de la subcategoría sola: un cable es accesorio
dentro de Celulares y es EL PRODUCTO dentro de "Cargadores y adaptadores".
Lo mismo con las refacciones: en Autos son partes, y en la categoría
Refacciones son lo que se compara. Por eso esto es un mapa por categoría y
no una lista de palabras.

LOS CINCO PAPELES
-----------------
  producto    Lo que la categoría compara. Es el valor por omisión: sólo se
              listan abajo las subcategorías que NO lo son, así el archivo
              se lee de un vistazo y crecer el catálogo no obliga a tocarlo.
  accesorio   Va con el producto pero no es el producto (fundas, soportes,
              organizadores).
  parte       Va dentro del producto o lo repara (refacciones, aspas,
              almohadillas de repuesto).
  consumible  Se gasta con el uso (filtros, tinta, cuerdas, baquetas,
              brocas, desechables).
  afin        Es un producto de pleno derecho y pertenece a la categoría,
              pero no es lo que busca quien escribe su nombre. El teléfono
              alámbrico está bien puesto en Celulares y no es un celular; el
              Fire Stick está bien puesto en Televisores y no es un
              televisor. kakaku.com resuelve esto separando la categoría
              (固定電話 no cuelga de スマートフォン); acá, que el catálogo ya
              está armado, se marcan y se muestran aparte.

CÓMO SE USA
-----------
    from roles_subcategorias import rol_de
    rol_de("Televisores", "Accesorios y soportes")   -> "accesorio"
    rol_de("Televisores", "4K")                      -> "producto"
"""

PRODUCTO = "producto"
ACCESORIO = "accesorio"
PARTE = "parte"
CONSUMIBLE = "consumible"
AFIN = "afin"

# {categoría: {subcategoría: papel}}. Lo que no está acá es "producto".
ROLES = {
    "Celulares": {
        "Accesorios para celular": ACCESORIO,
        "Teléfonos fijos": AFIN,
    },
    "Baterías portátiles (power bank)": {
        "Accesorios y repuestos": ACCESORIO,
    },
    "Tabletas": {
        # Las pizarras LCD de escritura son un producto, pero no son una
        # tableta: kakaku.com separa 電子メモ de タブレット.
        "Tabletas de dibujo y escritura": AFIN,
        "Accesorios para tableta": ACCESORIO,
    },
    "Bocinas": {
        "Accesorios para bocinas": ACCESORIO,
    },
    "Audífonos y auriculares": {
        "Almohadillas y repuestos": PARTE,
    },
    "Teclados": {
        "Switches, keycaps y accesorios": ACCESORIO,
    },
    # Ojo: en esta categoría la memoria RAM y los componentes SON el
    # producto; lo que sobra son los accesorios DE esos componentes.
    "Componentes y accesorios de PC": {
        "Refacciones para laptop": PARTE,
        "Accesorios": ACCESORIO,
        "Accesorios de memoria": ACCESORIO,
        "Accesorios de monitor": ACCESORIO,
    },
    "Televisores": {
        "Accesorios de TV": ACCESORIO,
        "Accesorios y soportes": ACCESORIO,
        "Dispositivos de streaming": AFIN,
    },
    # Las pantallas de proyección se quedan como producto: en esta categoría
    # se comparan igual que el proyector, y el nombre de la categoría las
    # incluye ("Proyectores y accesorios").
    "Proyectores y accesorios": {
        "Accesorios": ACCESORIO,
        "Otros accesorios de proyector": ACCESORIO,
        "Soportes para proyector": ACCESORIO,
        "Lámparas de proyector": CONSUMIBLE,
    },
    "Aspiradoras": {
        "Accesorios": ACCESORIO,
    },
    "Electrodomésticos": {
        "Accesorios y refacciones de máquina de coser": PARTE,
        "Accesorios de purificador": ACCESORIO,
        "Accesorios y repuestos para freidora de aire": ACCESORIO,
        "Filtros para regadera": CONSUMIBLE,
        "Filtros para refrigerador y cafetera": CONSUMIBLE,
        "Filtros y membranas de repuesto": CONSUMIBLE,
        # Affresh y las toallitas de la tienda de marca (23-sep).
        "Limpiadores para electrodomésticos": CONSUMIBLE,
    },
    # Los controles y volantes se quedan como producto: la gente los compara
    # entre sí ("control de PS5 más barato"), no son un extra de la consola.
    "Videojuegos": {
        "Cables y adaptadores": ACCESORIO,
        "Cargadores, bases y soportes": ACCESORIO,
        "Fundas, micas y protectores": ACCESORIO,
        "Otros accesorios gamer": ACCESORIO,
        "Tarjetas y suscripciones": CONSUMIBLE,
    },
    "Muebles": {
        "Accesorios y refacciones para sillas": PARTE,
        "Herrajes y refacciones de muebles": PARTE,
        "Accesorios y organizadores de escritorio": ACCESORIO,
        "Fundas y accesorios para sofá": ACCESORIO,
        "Accesorios y refacciones de cama": PARTE,
    },
    # Brocas, discos y hojas se marcan consumible: son lo que se gasta al
    # usar la herramienta, y con ellos arriba "la herramienta más barata"
    # cuesta $38 y es un disco de corte.
    "Herramientas": {
        "Baterías y cargadores de herramienta": ACCESORIO,
        "Accesorios de multiherramienta y mototool": ACCESORIO,
        "Accesorios para herramientas eléctricas": ACCESORIO,
        "Accesorios para rotomartillo y demoledor": ACCESORIO,
        "Lijas y accesorios de lijado": ACCESORIO,
        "Refacciones de herramientas eléctricas": PARTE,
        "Material eléctrico": PARTE,
        "Brocas": CONSUMIBLE,
        "Discos de corte y desbaste": CONSUMIBLE,
        "Hojas y cuchillas de sierra": CONSUMIBLE,
        "Puntas y dados de impacto": CONSUMIBLE,
    },
    "Autos, bicicletas y motos": {
        "Tapetes, fundas y parasoles": ACCESORIO,
        "Limpieza y cuidado del auto": CONSUMIBLE,
        # El audio de auto y las cámaras son productos, pero no son el auto
        # ni la bicicleta: "el auto más barato" no es una bocina de $265.
        "Bocinas para auto": AFIN,
        "Bocinas de 4 a 5.25 pulgadas": AFIN,
        "Bocinas coaxiales de 6.5 pulgadas": AFIN,
        "Bocinas coaxiales 6x9 y 6x8": AFIN,
        "Bocinas de componentes": AFIN,
        "Bocinas marinas y para moto": AFIN,
        "Medios rangos y bocinas profesionales": AFIN,
        "Tweeters": AFIN,
        "Subwoofers para auto": AFIN,
        "Amplificadores para auto": AFIN,
        "Estéreos para auto": AFIN,
        "Dashcams y cámaras": AFIN,
        "Accesorios de audio para auto": ACCESORIO,
        "Accesorios para bicicleta": ACCESORIO,
        "Accesorios para moto": ACCESORIO,
        "Accesorios y refacciones": PARTE,
        "Bolsas, canastas y portabultos": ACCESORIO,
        "Bombas e infladores": ACCESORIO,
        "Candados para bicicleta": ACCESORIO,
        "Cascos para moto": ACCESORIO,
        "Cascos y protección para ciclismo": ACCESORIO,
        "Ciclocomputadoras y soportes para celular": ACCESORIO,
        "Herramientas y mantenimiento de bicicleta": ACCESORIO,
        "Luces para bicicleta": ACCESORIO,
        "Portabicicletas y soportes": ACCESORIO,
        "Ropa y calzado de ciclismo": ACCESORIO,
        "Cámaras y accesorios de llanta": PARTE,
        "Pedales, manubrios y puños": PARTE,
        "Refacciones y transmisión de bicicleta": PARTE,
        "Rines": PARTE,
        "Sillines y asientos": PARTE,
        "Llantas": PARTE,
        "Llantas para auto": PARTE,
        "Llantas para bicicleta": PARTE,
        "Llantas para camioneta y SUV": PARTE,
        "Llantas para carretilla y equipo": PARTE,
        "Llantas para moto": PARTE,
        "Baterías para auto": PARTE,
    },
    # Refacciones entera es la categoría de las partes: acá la parte ES el
    # producto que se compara, así que no lleva ninguna marca.
    "Otros": {
        "Soportes para dispositivos": ACCESORIO,
        "Accesorios y limpieza de paneles solares": ACCESORIO,
    },
    "Drones": {
        "Accesorios": ACCESORIO,
    },
    "Cafeteras": {
        "Accesorios para cafetera": ACCESORIO,
    },
    "Cámaras de seguridad": {
        "Accesorios de videovigilancia": ACCESORIO,
    },
    "Impresoras": {
        "Cartuchos de tinta": CONSUMIBLE,
        "Tóner": CONSUMIBLE,
        "Cabezales y refacciones de impresión": PARTE,
        "Consumibles": CONSUMIBLE,
    },
    "Instrumentos musicales": {
        # Un micrófono es un producto, pero no es un instrumento musical.
        "Micrófonos": AFIN,
        "Producción de audio": AFIN,
        "Tornamesas": AFIN,
        "Accesorios": ACCESORIO,
        "Accesorios de guitarra": ACCESORIO,
        "Bancos, soportes y accesorios de teclado": ACCESORIO,
        "Boquillas, cañas y accesorios de viento": ACCESORIO,
        "Fundas, soportes y atriles": ACCESORIO,
        "Fundas y accesorios de batería": ACCESORIO,
        "Pads de práctica": ACCESORIO,
        "Pedales y herrajes de batería": PARTE,
        "Baquetas y escobillas": CONSUMIBLE,
        "Cuerdas de guitarra y bajo": CONSUMIBLE,
        "Parches": CONSUMIBLE,
    },
    # Los lentes se quedan como producto: son de lo más comparado de la
    # categoría y kakaku les da categoría propia (レンズ).
    "Cámaras y fotografía": {
        "Filtros y parasoles": ACCESORIO,
        "Trípodes y soportes": ACCESORIO,
        "Baterías y cargadores de cámara": ACCESORIO,
        "Accesorios": ACCESORIO,
    },
    "Impresión 3D": {
        "Accesorios": ACCESORIO,
        "Filamentos": CONSUMIBLE,
    },
    "Movilidad eléctrica": {
        "Accesorios": ACCESORIO,
    },
    "Climatización": {
        "Accesorios y refacciones de aire acondicionado": PARTE,
        "Aspas y refacciones de ventilador": PARTE,
        "Refacciones de calefactor": PARTE,
    },
    "Deportes y fitness": {
        "Accesorios de fuerza": ACCESORIO,
    },
    "Joyería y bisutería": {
        "Cajas y estuches para relojes": ACCESORIO,
        "Correas y extensibles": ACCESORIO,
        "Cuidado y herramientas": ACCESORIO,
        "Joyeros": ACCESORIO,
        "Material para bisutería": CONSUMIBLE,
    },
    "Blancos y ropa de cama": {
        "Repuestos y controles de cobija eléctrica": PARTE,
    },
    "Domótica y hogar inteligente": {
        "Accesorios y refacciones de cerradura": PARTE,
    },
    "Cocina y comedor": {
        "Desechables": CONSUMIBLE,
        "Limpieza de cocina": CONSUMIBLE,
    },
}

# Los nombres bonitos, para los encabezados de grupo de la página de
# categoría (el equivalente a パソコン本体 / 周辺機器 / パーツ).
TITULOS = {
    PRODUCTO: "Productos",
    AFIN: "Relacionados",
    ACCESORIO: "Accesorios",
    PARTE: "Refacciones y partes",
    CONSUMIBLE: "Consumibles",
}

ORDEN = [PRODUCTO, AFIN, ACCESORIO, PARTE, CONSUMIBLE]


# Una subcategoría llamada exactamente "Accesorios" es un accesorio en
# cualquier categoría: no hay caso donde una categoría se llame así. Vale la
# pena tenerlo como regla y no como 9 entradas repetidas, sobre todo porque
# cada categoría nueva que estrene la suya la hereda sin que nadie tenga que
# acordarse. Es el mismo nombre que ya usa SUBCATEGORIAS_OPT_IN en
# generate_seo_pages.py, web_summary.py y js/app.js.
POR_NOMBRE = {"Accesorios": ACCESORIO}


# Tres categorías tienen un id distinto de su nombre, y ROLES está escrito
# con el nombre. Casi todos los que preguntan pasan p["category"], que es el
# id, así que sin este puente los papeles de Audífonos y de Baterías
# portátiles nunca se aplicaban (medido el 23 de septiembre de 2026: sus
# repuestos seguían compitiendo en los rankings). Se acepta cualquiera de
# los dos.
ALIAS_CATEGORIA = {
    "Audífonos": "Audífonos y auriculares",
    "Baterías portátiles": "Baterías portátiles (power bank)",
    "Redes": "Redes y WiFi",
}


from subcategorias_tres_niveles import ROLES_TRES_NIVELES  # noqa: E402
for _cat, _roles in ROLES_TRES_NIVELES.items():
    _clave = _cat if _cat in ROLES else ALIAS_CATEGORIA.get(_cat, _cat)
    ROLES.setdefault(_clave, {}).update(_roles)


import reubicar_otros as _ro  # noqa: E402
ROLES.setdefault(_ro.SOLAR, {}).update(_ro.ROLES_SOLAR)
for _cat, _roles in _ro.ROLES_NUEVAS.items():
    ROLES.setdefault(_cat, {}).update({s: {'accesorio': ACCESORIO, 'afin': AFIN}[r] for s, r in _roles.items()})


def rol_de(categoria, subcategoria):
    """El papel de esa subcategoría dentro de esa categoría (id o nombre)."""
    if not subcategoria:
        return PRODUCTO
    roles = ROLES.get(categoria) or ROLES.get(ALIAS_CATEGORIA.get(categoria), {})
    explicito = roles.get(subcategoria)
    if explicito:
        return explicito
    return POR_NOMBRE.get(subcategoria, PRODUCTO)


def es_producto(categoria, subcategoria):
    return rol_de(categoria, subcategoria) == PRODUCTO
