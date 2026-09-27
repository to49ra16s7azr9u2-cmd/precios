"""Subcategorías que se juntaron con otra (revisión del árbol, 26-sep-2026).

POR QUÉ
-------
Medido sobre el catálogo (vecinos por nombre, 40 fichas de cada
subcategoría): había pares que el nombre del producto no separa porque son
LO MISMO con dos nombres («Charms» y «Dijes y charms», «Cobertores» y «Colchas
y cobertores», «Hervidores y teteras» y «... eléctricas»), o subcategorías
de 0 a 30 fichas que repiten a una hermana más grande («Cañas para
instrumentos de viento» junto a «Boquillas, cañas y accesorios de viento»).
Con dos lugares para lo mismo, cada alta cae en uno u otro al azar y
cualquier lista queda incompleta: el error lo produce el árbol, no el
clasificador.

UNIR: (categoría, subcategoría vieja) -> (categoría, subcategoría que queda).
La aplica reorganizar_categorias.destino(), así que cualquier camino de alta
o regla que todavía diga el nombre viejo termina en el nuevo, y
unificar_subcategorias.py --aplicar quita la vieja del manifiesto y deja su
url redirigiendo (data/redirecciones.json).
"""

UNIR = {
    # Lo mismo con dos nombres
    ("Electrodomésticos", "Hervidores y teteras eléctricas"): ("Electrodomésticos", "Hervidores y teteras"),
    ("Blancos y ropa de cama", "Cobertores"): ("Blancos y ropa de cama", "Colchas y cobertores"),
    ("Joyería y bisutería", "Charms"): ("Joyería y bisutería", "Dijes y charms"),
    ("Muebles", "Fundas para sofá"): ("Muebles", "Fundas y accesorios para sofá"),
    ("Muebles", "Accesorios y organizadores de escritorio"): ("Muebles", "Organizadores de escritorio"),
    ("Muebles", "Mesas para laptop y de cama"): ("Muebles", "Mesas de cama y con ruedas"),
    ("Domótica y hogar inteligente", "Enchufes y contactos inteligentes"): ("Domótica y hogar inteligente", "Enchufes inteligentes"),
    ("Domótica y hogar inteligente", "Cerraduras inteligentes"): ("Domótica y hogar inteligente", "Cerraduras de puerta inteligentes"),
    ("Audífonos", "Almohadillas para audífonos"): ("Audífonos", "Almohadillas y repuestos"),
    ("Cámaras y fotografía", "Baterías para cámara"): ("Cámaras y fotografía", "Baterías y cargadores de cámara"),
    ("Autos y motos", "Cámaras para llanta"): ("Autos y motos", "Cámaras y accesorios de llanta"),
    ("Climatización", "Aspas para ventilador"): ("Climatización", "Aspas y refacciones de ventilador"),
    ("Equipo comercial", "Terminales punto de venta"): ("Equipo comercial", "Punto de venta"),
    ("Electrodomésticos", "Básculas de cocina"): ("Cocina y comedor", "Básculas y medidores"),
    ("Lavadoras", "Lavadoras de carga frontal"): ("Lavadoras", "Carga frontal"),
    ("Almacenamiento", "Memorias USB por mayoreo"): ("Almacenamiento", "Memorias USB"),
    ("Iluminación", "Lámparas de techo para exterior"): ("Iluminación", "Exterior"),
    ("Herramientas", "Lijas"): ("Herramientas", "Lijas y accesorios de lijado"),
    ("Herramientas", "Sanitarios"): ("Herramientas", "Sanitarios y accesorios de baño"),
    ("Herramientas", "Inodoros"): ("Herramientas", "Sanitarios y accesorios de baño"),
    ("Blancos y ropa de cama", "Toallas"): ("Blancos y ropa de cama", "Toallas de baño"),
    ("Blancos y ropa de cama", "Accesorios de baño"): ("Blancos y ropa de cama", "Cortinas para baño"),
    ("Blancos y ropa de cama", "Cortinas de baño y accesorios"): ("Blancos y ropa de cama", "Cortinas para baño"),
    ("Celulares", "Soportes para celular"): ("Celulares", "Soportes y agarraderas"),
    ("Proyectores y accesorios", "Accesorios"): ("Proyectores y accesorios", "Otros accesorios de proyector"),
    ("Proyectores y accesorios", "Pantallas para proyector"): ("Proyectores y accesorios", "Pantallas de proyección"),
    # Refacciones de electrodoméstico partidas de más
    ("Electrodomésticos", "Refacciones para electrodomésticos"): ("Electrodomésticos", "Refacciones para otros electrodomésticos"),
    ("Electrodomésticos", "Refacciones para plancha y vaporizador"): ("Electrodomésticos", "Refacciones para otros electrodomésticos"),
    ("Electrodomésticos", "Refacciones para freidora de aire"): ("Electrodomésticos", "Accesorios y repuestos para freidora de aire"),
    # Accesorios de viento, teclado y batería: 0 a 26 fichas cada una
    ("Instrumentos musicales", "Cañas para instrumentos de viento"): ("Instrumentos musicales", "Boquillas, cañas y accesorios de viento"),
    ("Instrumentos musicales", "Boquillas para instrumentos de viento"): ("Instrumentos musicales", "Boquillas, cañas y accesorios de viento"),
    ("Instrumentos musicales", "Almohadillas para instrumentos de viento"): ("Instrumentos musicales", "Boquillas, cañas y accesorios de viento"),
    ("Instrumentos musicales", "Soportes para instrumentos de viento"): ("Instrumentos musicales", "Boquillas, cañas y accesorios de viento"),
    ("Instrumentos musicales", "Soportes para teclado"): ("Instrumentos musicales", "Bancos, soportes y accesorios de teclado"),
    ("Instrumentos musicales", "Alfombras para batería"): ("Instrumentos musicales", "Fundas y accesorios de batería"),
    ("Instrumentos musicales", "Alfombrillas para batería"): ("Instrumentos musicales", "Fundas y accesorios de batería"),
    # Refacciones de calefactor: seis subcategorías para 4 fichas
    ("Climatización", "Núcleos para calefactor"): ("Climatización", "Refacciones de calefactor"),
    ("Climatización", "Tubos para calefactor"): ("Climatización", "Refacciones de calefactor"),
    ("Climatización", "Resistencias para calefactor"): ("Climatización", "Refacciones de calefactor"),
    ("Climatización", "Calentadores para calefactor"): ("Climatización", "Refacciones de calefactor"),
    # Accesorios de paneles solares: ocho subcategorías para 18 fichas
    **{("Energía solar", s): ("Energía solar", "Accesorios y limpieza de paneles solares") for s in (
        "Cables para paneles solares", "Cepillos para paneles solares", "Conectores para paneles solares",
        "Herramientas para paneles solares", "Máquinas de limpieza para paneles solares",
        "Pértigas para paneles solares", "Robots para paneles solares", "Soportes para paneles solares")},
    # Deportes: subcategorías vacías que repiten a una hermana
    ("Deportes y fitness", "Rodilleras"): ("Deportes y fitness", "Rodilleras, muñequeras y soportes"),
    ("Deportes y fitness", "Tobilleras"): ("Deportes y fitness", "Rodilleras, muñequeras y soportes"),
    ("Deportes y fitness", "Coderas y muñequeras"): ("Deportes y fitness", "Rodilleras, muñequeras y soportes"),
    ("Deportes y fitness", "Soportes"): ("Deportes y fitness", "Rodilleras, muñequeras y soportes"),
    ("Deportes y fitness", "Pelotas para raqueta"): ("Deportes y fitness", "Pelotas y accesorios de raqueta"),
    ("Deportes y fitness", "Tapones para natación"): ("Deportes y fitness", "Tapones y accesorios de natación"),
    ("Deportes y fitness", "Barras"): ("Deportes y fitness", "Barras y discos"),
    ("Deportes y fitness", "Barras para pesas"): ("Deportes y fitness", "Barras y discos"),
    ("Deportes y fitness", "Cuerdas"): ("Deportes y fitness", "Cuerdas para saltar"),
    **{("Deportes y fitness", s): ("Deportes y fitness", "Accesorios de fuerza") for s in (
        "Cinturones", "Cinturones para pesas", "Guantes para pesas", "Correas para pesas",
        "Cuerdas para pesas", "Ejercitadores")},
    ("Deportes y fitness", "Ejes para dardos"): ("Deportes y fitness", "Dardos y accesorios"),
    ("Deportes y fitness", "Puntas para dardos"): ("Deportes y fitness", "Dardos y accesorios"),
    ("Deportes y fitness", "Toallas para yoga"): ("Deportes y fitness", "Accesorios y ropa de yoga"),
    ("Deportes y fitness", "Toallas para natación"): ("Deportes y fitness", "Accesorios y ropa de yoga"),
    ("Deportes y fitness", "Cuadros para yoga"): ("Deportes y fitness", "Bloques, correas y ruedas de yoga"),
    # Ping pong: pelotas, redes y raquetas eran tres listas de 26 a 40 fichas
    # que se confundían entre sí (ida y vuelta de 38%)
    **{("Deportes y fitness", s): ("Deportes y fitness", "Raquetas, pelotas y accesorios de ping pong") for s in (
        "Raquetas de ping pong", "Pelotas, redes y accesorios de ping pong", "Pelotas de ping pong",
        "Bolsas de ping pong", "Robots de ping pong")},
    # Duplicados de dos hermanas: lo que el nombre ubica en la otra lo mueve
    # antes unificar_subcategorias.ATRIBUTOS («sérum», «corrector», «candado»)
    ("Belleza y cuidado personal", "Cremas y sérums faciales"): ("Belleza y cuidado personal", "Cremas faciales"),
    ("Belleza y cuidado personal", "Bases y correctores"): ("Belleza y cuidado personal", "Bases de maquillaje"),
    ("Electrodomésticos", "Filtros para refrigerador y cafetera"): ("Electrodomésticos", "Filtros y membranas de repuesto"),
    ("Herramientas", "Cerraduras y candados"): ("Herramientas", "Cerraduras y chapas de puerta"),
    # Divisiones que el nombre del producto no dice: «niña» o «niño» casi
    # nunca está en el título, y la mitad caía en «Tenis para niños».
    ("Calzado", "Tenis para niña"): ("Calzado", "Tenis para niños"),
    ("Calzado", "Tenis para niño"): ("Calzado", "Tenis para niños"),
    ("Blancos y ropa de cama", "Cobijas eléctricas individuales"): ("Blancos y ropa de cama", "Cobijas eléctricas"),
    ("Blancos y ropa de cama", "Cobijas eléctricas matrimoniales"): ("Blancos y ropa de cama", "Cobijas eléctricas"),
    ("Blancos y ropa de cama", "Cobijas eléctricas queen y king"): ("Blancos y ropa de cama", "Cobijas eléctricas"),

    # RASGOS COMO SUBCATEGORÍA -> TARJETAS DE COMPARA CALIDAD (aprobado el
    # 26-sep). «Impermeable», «con llamadas», «blackout» no son un tipo de
    # producto sino algo que el producto tiene, y puede tener varios a la vez:
    # una bocina potente e impermeable tenía que caer en UNA de las dos listas
    # y faltaba en la otra. Ahora el tipo es la subcategoría y el rasgo es una
    # tarjeta que filtra (specs_titulo.py lo lee del nombre,
    # compute_quality_axes.py arma la tarjeta).
    **{("Bocinas", s): ("Bocinas", "Bocinas Bluetooth") for s in (
        "Bocinas Bluetooth compactas (hasta 20 W)", "Bocinas Bluetooth medianas (20 a 60 W)",
        "Bocinas Bluetooth potentes (60 W o más)", "Bocinas Bluetooth impermeables")},
    ("Audífonos", "Earbuds con cancelación de ruido"): ("Audífonos", "Earbuds inalámbricos"),
    ("Audífonos", "Diadema con cancelación de ruido"): ("Audífonos", "Diadema inalámbrica"),
    ("Decoración de hogar y jardín", "Cortinas blackout"): ("Decoración de hogar y jardín", "Cortinas"),
    ("Joyería y bisutería", "Lentes de sol polarizados"): ("Joyería y bisutería", "Lentes de sol"),
    ("Joyería y bisutería", "Relojes para hombre"): ("Joyería y bisutería", "Relojes"),
    ("Joyería y bisutería", "Relojes para mujer"): ("Joyería y bisutería", "Relojes"),
    ("Relojes inteligentes", "Smartwatches con llamadas"): ("Relojes inteligentes", "Smartwatches"),
    ("Relojes inteligentes", "Smartwatches deportivos y con GPS"): ("Relojes inteligentes", "Smartwatches"),
    ("Tabletas", "Tabletas Android con 4G o 5G"): ("Tabletas", "Tabletas Android"),
    ("Electrodomésticos", "Freidoras de aire de doble canasta"): ("Electrodomésticos", "Freidoras de aire"),
    ("Blancos y ropa de cama", "Protectores de colchón impermeables"): ("Blancos y ropa de cama", "Protectores de colchón"),
    ("Blancos y ropa de cama", "Protectores de colchón acolchados"): ("Blancos y ropa de cama", "Protectores de colchón"),
    ("Blancos y ropa de cama", "Almohadas de memory foam"): ("Blancos y ropa de cama", "Almohadas"),
    ("Teclados", "Mecánicos inalámbricos"): ("Teclados", "Mecánicos"),
    ("Teclados", "Inalámbricos"): ("Teclados", "Membrana"),
    # Medidas que cruzan con un tipo: un monitor gamer de 27" iba a «27
    # pulgadas» o a «Gaming»; una laptop gamer de 15" igual; una batería
    # MagSafe de 10,000 mAh igual. La medida pasa a la tarjeta de tamaño o
    # capacidad (ya existían: screen_in, charger_w, battery_mah) y la
    # subcategoría queda para el tipo.
    **{("Monitores", s): ("Monitores", "Para casa y oficina") for s in (
        "Hasta 22 pulgadas", "23 a 25 pulgadas", "27 pulgadas", "28 a 34 pulgadas", "35 pulgadas o más")},
    **{("Laptops", s): ("Laptops", "Para casa y oficina") for s in (
        'Ultraligeras (13" y 14")', 'Laptops de 15" y 16"', 'Laptops de 17" o más')},
    **{("Baterías portátiles", s): ("Baterías portátiles", "De uso diario") for s in (
        "Hasta 10,000 mAh", "10,000 a 20,000 mAh", "Más de 20,000 mAh")},
    **{("Cargadores y adaptadores", s): ("Cargadores y adaptadores", "De pared") for s in (
        "Cargadores de pared hasta 20 W", "Cargadores de pared de 25 a 45 W", "Cargadores de pared de 65 W o más",
        "Cargadores de pared con cable")},
}
