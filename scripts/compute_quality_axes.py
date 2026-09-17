#!/usr/bin/env python3
"""Arma los ejes de "Compara calidad" para todas las subcategorías que
tengan con qué, y los deja en data/quality-axes.json.

POR QUÉ UN ARCHIVO Y NO MÁS JAVASCRIPT
--------------------------------------
QUALITY_AXES en js/app.js tiene los ejes escritos a mano para unas treinta
categorías: cada uno con su corte pensado y su línea de uso. Escribir así
las trescientas y pico subcategorías restantes no escala, y además los
cortes buenos dependen de lo que hay en el catálogo hoy (la mediana de
watts de una herramienta cambia cuando entran 500 taladros). Este script
lee el catálogo, mira qué campo de facets tiene cada subcategoría, y arma
los ejes con la misma regla que los de mano:

  - el corte es siempre UN campo que la tienda publicó, y la tarjeta dice
    cuál es ("Hasta 800 W");
  - los tres tramos salen de la distribución real (terciles redondeados a
    números legibles), no de un ideal;
  - un campo que no reparte (el 90% cae en un solo tramo) no sirve para
    elegir y se descarta;
  - la línea de uso orienta sobre el RANGO, no afirma nada de cada
    producto.

Lo que está a mano en app.js gana: este archivo solo llena los huecos.
qualityAxes() en app.js busca primero en QUALITY_AXES y después acá, con
la clave "Categoría/Subcategoría" y, si no hay, "Categoría".

FORMATO
-------
    {"Deportes y fitness/Pesas": {"intro": "...", "axes": [
        {"key": "level", "label": "Peso", "field": "weight_kg",
         "criterion": "en kilos", "ramp": true,
         "tiers": [{"id": "ligeras", "name": "Ligeras", "use": "...",
                    "spec": "Hasta 5 kg", "max": 5}, ...]}]}}

Un tramo numérico cumple  min < v <= max  (el que falte no acota); uno
de texto lleva "values" con los valores que le pertenecen.

USO
---
    python3 scripts/compute_quality_axes.py            # escribe el JSON
    python3 scripts/compute_quality_axes.py --dry-run  # solo el resumen
"""
import argparse
import collections
import io
import json
import math
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog  # noqa: E402

SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "quality-axes.json")
APP_JS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "js", "app.js")

MIN_FICHAS = 30        # subcategorías más chicas no llevan bloque
MIN_COBERTURA = 0.20   # el campo tiene que estar en 1 de cada 5 fichas
MIN_CON_DATO = 12
MAX_DOMINANTE = 0.85   # si un tramo se lleva más que esto, el eje no reparte
MIN_TRAMO = 0.06       # cada tramo con al menos el 6% (o se funde)

# Orden de preferencia: lo que decide la compra antes que lo descriptivo.
PRIORIDAD = [
    "power_w", "charger_w", "liters", "engine_cc", "range_km", "battery_ah", "weight_kg",
    "load_kg", "size_in", "screen_in", "length_cm", "length_m", "lumens", "battery_mah", "camera_mp",
    "resolution", "focal_mm", "storage_gb", "ram_gb", "dpi", "ports", "wifi_std", "thread_count",
    "pieces", "ball_no", "glove_oz", "thickness_mm", "players_max", "age_min",
    "speeds", "volt", "helmet_type", "size_label", "breed_size", "pet_stage",
    "bike_type", "filament", "tool_type", "rim_size", "wheel_size", "platform", "gender",
    "stone", "material", "water_resistant", "sport", "volume_ml",
]

# Donde el orden general no es el de la compra: en una bicicleta el tipo y
# la rodada van antes que la edad.
PRIORIDAD_ESPECIFICA = {
    "Autos, bicicletas y motos/Bicicletas": ["bike_type", "wheel_size", "speeds", "age_min"],
    "Juguetes y bebés/Peluches": ["length_cm", "age_min"],
    "Videojuegos/Consolas": ["platform", "storage_gb"],
    "Cámaras y fotografía/Cámaras de acción": ["camera_mp", "battery_mah"],
    "Mascotas/Bebederos": ["liters", "breed_size"],
    "Redes/Routers": ["wifi_std", "ports"], "Redes/Repetidores": ["wifi_std"], "Redes/Switches": ["ports", "wifi_std"],
    "Juegos de mesa": ["players_max", "age_min"],
}

# Lo que dice cada campo: etiqueta de la fila, criterio, unidad y los tres
# nombres/usos genéricos de menor a mayor. Los específicos por subcategoría
# van en USOS y ganan.
CAMPOS = {
    "power_w": dict(label="Potencia", criterion="en watts", unit=" W",
                    nombres=("Baja", "Media", "Alta"),
                    usos=("Trabajos ligeros y uso ocasional", "Uso de todos los días", "Uso rudo o continuo")),
    "charger_w": dict(label="Carga", criterion="en watts de salida", unit=" W",
                      nombres=("Lenta", "Rápida", "Muy rápida"),
                      usos=("Teléfono y audífonos", "Carga rápida de teléfono y tablet", "Laptop, o varios equipos a la vez")),
    "liters": dict(label="Capacidad", criterion="en litros", unit=" L",
                   nombres=("Chica", "Mediana", "Grande"),
                   usos=("Una o dos personas", "Para la familia", "Reuniones o uso intensivo")),
    "engine_cc": dict(label="Cilindrada", criterion="en centímetros cúbicos", unit=" cc",
                      nombres=("Chica", "Mediana", "Grande"),
                      usos=("Ciudad y trámites", "Carretera ocasional", "Viajes largos y potencia")),
    "range_km": dict(label="Autonomía", criterion="en km por carga", unit=" km",
                     nombres=("Corta", "Media", "Larga"),
                     usos=("Trayectos cortos", "Ida y vuelta al trabajo", "Todo el día sin cargar")),
    "weight_kg": dict(label="Peso", criterion="en kilos", unit=" kg",
                      nombres=("Ligeras", "Medias", "Pesadas"),
                      usos=("Para empezar y tonificar", "Fuerza general", "Fuerza avanzada")),
    "load_kg": dict(label="Carga máxima", criterion="en kilos que aguanta", unit=" kg",
                    nombres=("Ligera", "Media", "Reforzada"),
                    usos=("Uso ocasional", "Uso diario", "Uso intensivo o más peso")),
    "size_in": dict(label="Tamaño", criterion="en pulgadas", unit='"',
                    nombres=("Chico", "Mediano", "Grande"),
                    usos=("El más compacto", "El tamaño más común", "El más grande")),
    "screen_in": dict(label="Tamaño", criterion="por pantalla", unit='"',
                      nombres=("Chica", "Mediana", "Grande"),
                      usos=("Para un cuarto chico", "El tamaño más común", "Sala y cine en casa")),
    "length_cm": dict(label="Tamaño", criterion="por largo en cm", unit=" cm",
                      nombres=("Chico", "Mediano", "Grande"),
                      usos=("Cabe en cualquier lugar", "El tamaño más común", "Ocupa más espacio")),
    "battery_mah": dict(label="Batería", criterion="en mAh", unit=" mAh",
                        nombres=("Chica", "Mediana", "Grande"),
                        usos=("Uso ligero", "Un día completo", "Varios días sin cargar")),
    "camera_mp": dict(label="Resolución", criterion="en megapixeles", unit=" MP",
                      nombres=("Básica", "Media", "Alta"),
                      usos=("Para ver en pantalla chica", "Fotos nítidas de diario", "Detalle para imprimir o recortar")),
    "storage_gb": dict(label="Almacenamiento", criterion="en GB", unit=" GB",
                       nombres=("Básico", "Intermedio", "Alto"),
                       usos=("Pocos juegos a la vez", "Varios juegos instalados", "Toda la biblioteca")),
    "thread_count": dict(label="Hilos", criterion="por hilos por pulgada", unit=" hilos",
                         nombres=("Frescas", "Suaves", "De hotel"),
                         usos=("Ligeras y frescas", "Más tupidas y suaves", "Tacto de hotel")),
    "pieces": dict(label="Piezas", criterion="por número de piezas", unit=" piezas",
                   nombres=("Pocas", "Medias", "Muchas"),
                   usos=("Para empezar o para niños", "Una tarde entera", "Un reto largo")),
    "volume_ml": dict(label="Contenido", criterion="en mililitros", unit=" ml",
                      nombres=("Chico", "Mediano", "Grande"),
                      usos=("Para probar o para viajar", "Uso de diario", "Rinde meses")),
    "speeds": dict(label="Velocidades", criterion="de la bicicleta", unit="",
                   nombres=("Sin cambios", "Pocas", "Muchas"),
                   usos=("Ciudad plana y niños", "Cerros suaves", "Montaña y ruta")),
    "battery_ah": dict(label="Batería", criterion="en amperes-hora", unit=" Ah",
                       nombres=("Chica", "Mediana", "Grande"),
                       usos=("Trayectos cortos", "Uso de diario", "Más autonomía")),
    "length_m": dict(label="Largo", criterion="en metros", unit=" m",
                     nombres=("Corta", "Mediana", "Larga"),
                     usos=("Un mueble o un marco", "Una pared", "Un cuarto entero")),
    "lumens": dict(label="Luz", criterion="en lúmenes", unit=" lm",
                   nombres=("Suave", "Media", "Potente"),
                   usos=("Ambiente y buró", "Cuarto o cocina", "Exterior y naves")),
    "ram_gb": dict(label="Memoria", criterion="en GB", unit=" GB",
                   nombres=("Básica", "Intermedia", "Alta"),
                   usos=("Oficina y navegar", "Varias apps y juegos", "Edición y estaciones de trabajo")),
    "dpi": dict(label="Sensibilidad", criterion="en DPI", unit=" DPI",
                nombres=("Básica", "Media", "Alta"),
                usos=("Oficina y navegar", "Juegos casuales", "Juegos competitivos y pantallas grandes")),
    "ports": dict(label="Puertos", criterion="por número de puertos", unit=" puertos",
                  nombres=("Pocos", "Medios", "Muchos"),
                  usos=("Un escritorio o una sala", "Casa u oficina chica", "Oficina o rack")),
    "focal_mm": dict(label="Focal", criterion="en milímetros", unit=" mm",
                     nombres=("Gran angular", "Normal", "Teleobjetivo"),
                     usos=("Paisaje, arquitectura e interiores", "Retrato y calle", "Deporte, fauna y lejos")),
    "glove_oz": dict(label="Peso", criterion="en onzas", unit=" oz",
                     nombres=("Ligeros", "Medios", "Pesados"),
                     usos=("Niños y saco", "Entrenamiento general", "Sparring y protección")),
    "thickness_mm": dict(label="Grosor", criterion="en milímetros", unit=" mm",
                         nombres=("Delgado", "Medio", "Grueso"),
                         usos=("Equilibrio y viajes", "El grosor más común", "Rodillas y suelo duro")),
    # Categóricos: la etiqueta y, si hay, un uso por valor.
    "helmet_type": dict(label="Tipo", criterion="de casco", ramp=False, valores={
        "Integral": "Cerrado, el que más protege", "Cerrado": "Cerrado, el que más protege",
        "Abatible": "Se abre por delante", "Jet": "Sin mentonera, para ciudad", "Abierto": "Sin mentonera, para ciudad",
        "Cross": "Para terracería", "3/4": "Cubre la nuca, no la barbilla", "Doble Propósito": "Ciudad y terracería"}),
    "size_label": dict(label="Talla", criterion="según la ficha", orden=["Chica", "Mediana", "Grande", "Extra grande"]),
    "breed_size": dict(label="Raza", criterion="por tamaño del perro", ramp=False,
                       orden=["Chica", "Mediana", "Grande", "Todas las razas"],
                       valores={"Chica": "Hasta 10 kg", "Mediana": "10 a 25 kg", "Grande": "Más de 25 kg",
                                "Todas las razas": "Sirve para cualquier tamaño"}),
    "pet_stage": dict(label="Etapa", criterion="de vida de la mascota", ramp=False,
                      orden=["Cachorro", "Adulto", "Senior", "Todas las etapas"],
                      valores={"Cachorro": "Los primeros meses", "Adulto": "La etapa más larga",
                               "Senior": "Mascotas mayores", "Todas las etapas": "Sirve a cualquier edad"}),
    "bike_type": dict(label="Tipo", criterion="de bicicleta", ramp=False, valores={
        "Montaña": "Terracería y cerro", "Urbana": "Ciudad y trayectos cortos", "Ruta": "Asfalto y velocidad",
        "Infantiles": "Para niños", "Eléctricas": "Con motor"}),
    "tool_type": dict(label="Tipo", criterion="de herramienta", ramp=False),
    "rim_size": dict(label="Rin", criterion="por medida", ordinal=True),
    "wheel_size": dict(label="Rodada", criterion="por medida", ordinal=True),
    "platform": dict(label="Consola", criterion="a la que pertenece", ramp=False,
                     orden=["Nintendo Switch 2", "Nintendo Switch", "PlayStation 5", "PlayStation 4", "Xbox Series X|S", "Xbox One"]),
    "gender": dict(label="Para quién", criterion="según la ficha", ramp=False,
                   orden=["Hombre", "Mujer", "Unisex", "Niño", "Niña"]),
    "stone": dict(label="Piedra", criterion="según la ficha", ramp=False,
                  orden=["Sin piedra", "Zirconia", "Cristal", "Perla", "Moissanita", "Diamante"]),
    "material": dict(label="Material", criterion="según la ficha", ramp=False),
    "water_resistant": dict(label="Resistencia al agua", criterion="según la ficha", ramp=False,
                            orden=["Sí", "No"],
                            valores={"Sí": "Aguanta lluvia, sudor o regadera", "No": "Mantener seco"}),
    "sport": dict(label="Deporte", criterion="según la ficha", ramp=False),
    "filament": dict(label="Material", criterion="del filamento", ramp=False, valores={
        "PLA": "El más fácil de imprimir", "PLA+": "PLA más resistente", "PETG": "Resistente y algo flexible",
        "ABS": "Aguanta calor, pide cama caliente", "TPU": "Flexible", "ASA": "Para exterior", "Nylon": "Muy resistente"}),
    "wifi_std": dict(label="Wi-Fi", criterion="por generación",
                     orden=["Wi-Fi 4", "Wi-Fi 5", "Wi-Fi 6", "Wi-Fi 6E", "Wi-Fi 7"],
                     valores={"Wi-Fi 4": "Básico, para pocos equipos", "Wi-Fi 5": "Suficiente para streaming",
                              "Wi-Fi 6": "Muchos equipos a la vez", "Wi-Fi 6E": "Banda de 6 GHz, sin interferencia",
                              "Wi-Fi 7": "La generación más nueva"}),
    "resolution": dict(label="Resolución", criterion="de la imagen",
                       orden=["HD", "HD+", "FHD", "WFHD", "QHD", "UWQHD", "DQHD", "4K UHD", "8K UHD"],
                       valores={"HD": "Para videollamadas básicas", "FHD": "Nítida, la más común",
                                "QHD": "Más detalle que Full HD", "4K UHD": "El máximo detalle"}),
}

# Campos que solo son una decisión de compra en algunas categorías: el
# material de un mueble o una joya sí, el de una licuadora no.
CAMPO_SOLO_EN = {
    "material": {"Muebles", "Joyería y bisutería", "Blancos y ropa de cama", "Instrumentos musicales",
                 "Viajes", "Otros", "Decoración de hogar y jardín", "Juguetes y bebés", "Mascotas",
                 "Belleza y cuidado personal/Mobiliario para salón"},
    "water_resistant": {"Relojes inteligentes", "Audífonos", "Bocinas", "Joyería y bisutería",
                        "Salud y belleza", "Cámaras y fotografía"},
    "volume_ml": {"Otros", "Salud y belleza", "Belleza y cuidado personal", "Juguetes y bebés"},
}

# Tramos fijos: acá los cortes no salen de la distribución sino de cómo se
# habla del producto (nadie busca un juego "de 2.7 jugadores").
FIJOS = {
    "age_min": ("Edad", "recomendada", [
        ("bebes", "Bebés", "Desde el nacimiento", "0 a 2 años", None, 2),
        ("ninos", "Niños", "Preescolar y primaria", "3 a 7 años", 2, 7),
        ("grandes", "Grandes", "De 8 a 12 años", "8 a 12 años", 7, 12),
        ("adultos", "Jóvenes y adultos", "De 13 en adelante", "13 años o más", 12, None)]),
    "players_max": ("Jugadores", "que caben", [
        ("solo", "Solitario", "Para jugar solo", "1 jugador", None, 1),
        ("dos", "Para dos", "En pareja o uno contra uno", "2 jugadores", 1, 2),
        ("chico", "Grupo chico", "Familia o cuatro amigos", "3 a 4 jugadores", 2, 4),
        ("grande", "Grupo grande", "Fiestas y reuniones", "5 o más", 4, None)]),
    "volt": ("Alimentación", "por voltaje", [
        ("bat12", "Batería chica", "Ligeras, para la casa", "Hasta 12 V", None, 14),
        ("bat20", "Batería 18–20 V", "El estándar inalámbrico", "18 a 24 V", 14, 30),
        ("bat36", "Batería grande", "Inalámbricas de uso rudo", "36 V o más", 30, 100),
        ("cable", "De cable", "Enchufe de casa", "110 a 127 V", 100, 150),
        ("cable220", "De 220 V", "Instalación de 220 V", "220 V", 150, None)]),
    "ball_no": ("Número", "del balón", [
        ("n3", "No. 3", "Niños chicos", "No. 3", None, 3),
        ("n4", "No. 4", "Juvenil", "No. 4", 3, 4),
        ("n5", "No. 5", "Adultos, medida oficial de futbol", "No. 5", 4, 5),
        ("n6", "No. 6", "Basquetbol femenil", "No. 6", 5, 6),
        ("n7", "No. 7", "Basquetbol varonil y futbol americano", "No. 7", 6, None)]),
}
# Los de voltaje y balón no van de menos a más en el sentido de "mejor".
FIJOS_SIN_RAMPA = {"volt", "ball_no"}

# Nombres y usos específicos: (clave, campo) -> (nombres, usos). Cuando el
# genérico ("Baja/Media/Alta potencia") no dice para qué sirve.
USOS = {
    ("Herramientas/Herramientas eléctricas", "power_w"): (("Ligera", "Media", "Alta"),
        ("Taladros y lijadoras chicas, uso en casa", "Taller y trabajos frecuentes", "Rotomartillos, sierras y esmeriles grandes")),
    ("Herramientas", "power_w"): (("Ligera", "Media", "Alta"),
        ("Uso en casa", "Taller y trabajos frecuentes", "Uso rudo o profesional")),
    ("Autos, bicicletas y motos/Bocinas para auto", "power_w"): (("Suave", "Media", "Fuerte"),
        ("Para oír música con claridad", "Más presencia y bajos", "Para que se oiga desde afuera")),
    ("Autos, bicicletas y motos/Bocinas para auto", "size_in"): (("Chica", "Mediana", "Grande"),
        ("Tweeters y puertas chicas", "La medida más común", "Woofers y subwoofers")),
    ("Autos, bicicletas y motos/Amplificadores para auto", "power_w"): (("Suave", "Media", "Fuerte"),
        ("Para mejorar el estéreo de fábrica", "Bocinas y un subwoofer", "Subwoofers grandes y competencia")),
    ("Movilidad eléctrica/Patinetes eléctricos", "power_w"): (("Suave", "Media", "Fuerte"),
        ("Plano y trayectos cortos", "Subidas suaves y más velocidad", "Cerros y dos personas")),
    ("Movilidad eléctrica/Bicicletas eléctricas", "power_w"): (("Suave", "Media", "Fuerte"),
        ("Ayuda al pedaleo en plano", "Subidas suaves", "Cerros y carga")),
    ("Iluminación", "power_w"): (("Suave", "Media", "Potente"),
        ("Ambiente, buró y decoración", "Cuarto, cocina y oficina", "Exterior, patio y naves")),
    ("Iluminación/Exterior", "power_w"): (("Suave", "Media", "Potente"),
        ("Jardín y pasillo", "Cochera y fachada", "Estacionamiento y nave")),
    ("Viajes/Maletas", "size_in"): (("Cabina", "Mediana", "Grande"),
        ("Va en el avión contigo", "Documentada, una semana", "Viaje largo o para dos")),
    ("Juguetes y bebés/Peluches", "length_cm"): (("Chico", "Mediano", "Grande"),
        ("De bolsillo o llavero", "Para abrazar", "Para la cama")),
    ("Juguetes y bebés/Figuras de acción", "length_cm"): (("Chica", "Mediana", "Grande"),
        ("Para colección en repisa", "La escala más común", "Para exhibir")),
    ("Muebles/Escritorios", "length_cm"): (("Chico", "Mediano", "Grande"),
        ("Para una laptop", "Monitor y espacio para escribir", "Dos monitores o dos personas")),
    ("Otros/Generadores", "power_w"): (("Chico", "Mediano", "Grande"),
        ("Luces, teléfono y refrigerador", "Casa chica en un apagón", "Local, taller o casa entera")),
    ("Otros/Paneles solares", "power_w"): (("Chico", "Mediano", "Grande"),
        ("Cargar teléfono y luces", "Estación de energía o cabaña", "Instalación de casa")),
    ("Otros/Estaciones de energía", "power_w"): (("Chica", "Mediana", "Grande"),
        ("Teléfono, laptop y luces", "Refrigerador y herramientas", "Casa en un apagón")),
    ("Otros/Inversores", "power_w"): (("Chico", "Mediano", "Grande"),
        ("Laptop y teléfono", "Televisión y herramientas chicas", "Refrigerador y equipos grandes")),
    ("Belleza y cuidado personal/Secadoras de cabello", "power_w"): (("Suave", "Media", "Potente"),
        ("Cabello corto o de viaje", "Uso de diario", "Cabello largo o grueso, secado rápido")),
    ("Cámaras y fotografía", "camera_mp"): (("Básica", "Media", "Alta"),
        ("Para redes y pantalla", "Fotos nítidas de diario", "Para imprimir en grande o recortar")),
    ("Videojuegos/Consolas", "storage_gb"): (("Básico", "Intermedio", "Alto"),
        ("Pocos juegos instalados", "Varios juegos a la vez", "Toda la biblioteca")),
    ("Juegos de mesa/Rompecabezas", "pieces"): (("Pocas", "Medias", "Muchas"),
        ("Para niños o una tarde", "Un fin de semana", "Un reto largo")),
    ("Juguetes y bebés/Bloques de construcción", "pieces"): (("Pocos", "Medios", "Muchos"),
        ("Para empezar", "Un modelo completo", "Sets grandes de colección")),
    ("Autos, bicicletas y motos/Motocicletas", "engine_cc"): (("Chica", "Mediana", "Grande"),
        ("Ciudad y trámites", "Carretera ocasional", "Viajes largos")),
    ("Refrigeradores/Frigobares", "liters"): (("Chico", "Mediano", "Grande"),
        ("Bebidas en la oficina", "Cuarto o estudio", "Casi un refrigerador chico")),
    ("Electrodomésticos/Hornos", "liters"): (("Chico", "Mediano", "Grande"),
        ("Tostar y calentar", "Cocina de todos los días", "Pavo y charolas grandes")),
    ("Electrodomésticos/Pequeños electrodomésticos de cocina", "liters"): (("Chico", "Mediano", "Grande"),
        ("Una o dos porciones", "Para la familia", "Reuniones")),
    ("Electrodomésticos/Pequeños electrodomésticos de cocina", "power_w"): (("Baja", "Media", "Alta"),
        ("Batir y mezclar", "Cocinar de diario", "Calentar rápido y uso continuo")),
    ("Instrumentos musicales/Amplificadores", "power_w"): (("Para practicar", "Para ensayar", "Para tocar en vivo"),
        ("En casa, sin molestar", "Sala de ensayo", "Escenario y bocinas grandes")),
    ("Baterías portátiles", "charger_w"): (("Lenta", "Rápida", "Muy rápida"),
        ("Teléfono y audífonos", "Carga rápida de teléfono y tablet", "Laptop o varios equipos")),
    ("Deportes y fitness/Pesas", "weight_kg"): (("Ligeras", "Medias", "Pesadas"),
        ("Para empezar y tonificar", "Fuerza general", "Fuerza avanzada")),
    ("Salud y belleza/Básculas", "load_kg"): (("Estándar", "Reforzada", "Alta capacidad"),
        ("Hasta 150 kg", "Más margen", "Uso clínico o de carga")),
    ("Deportes y fitness/Equipo de gimnasio", "load_kg"): (("Ligera", "Media", "Reforzada"),
        ("Uso ocasional en casa", "Uso diario", "Uso rudo o personas de más peso")),
    ("Mascotas/Bebederos", "liters"): (("Chico", "Mediano", "Grande"),
        ("Gato o perro chico", "Perro mediano", "Varios animales o perro grande")),
    ("Proyectores y accesorios/Pantallas de proyección", "screen_in"): (("Chica", "Mediana", "Grande"),
        ("Recámara u oficina", "Sala", "Cine en casa o salón")),
    ("Blancos y ropa de cama/Sábanas", "thread_count"): (("Frescas", "Suaves", "De hotel"),
        ("Ligeras, para el calor", "Más tupidas y suaves", "Tacto de hotel")),
}

INTROS = {
    "Juegos de mesa": "Elige por cuántos van a jugar y de qué edad, no por la ficha técnica.",
    "Juguetes y bebés": "Elige por la edad de quien lo va a usar.",
    "Viajes/Maletas": "Elige por el viaje que vas a hacer: la de cabina va contigo en el avión.",
    "Deportes y fitness/Pesas": "Elige por dónde estás: se empieza ligero y se sube.",
    "Herramientas/Herramientas eléctricas": "Elige por el trabajo que le vas a dar y si la quieres con o sin cable.",
    "Autos, bicicletas y motos/Cascos para moto": "Empieza por el tipo y tu talla: un casco flojo no protege.",
    "Mascotas": "Elige por el tamaño y la edad de tu mascota.",
    "Iluminación": "Elige por dónde va a ir la luz, no por la ficha técnica.",
    "Movilidad eléctrica": "Elige por tu trayecto: distancia y subidas.",
    "Joyería y bisutería": "Elige por el material y la piedra: es lo que se ve y lo que dura.",
}


def norm(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", norm(s)).strip("-")
    return s or "x"


def redondo(v, hacia):
    """Un corte legible: dos cifras significativas (1,600 W, 45 kg, 6.5 L),
    y de mil para arriba múltiplos de 50."""
    if v <= 0:
        return v
    mag = 10 ** math.floor(math.log10(v))
    if v < 1:
        paso = 0.05
    elif v < 5:
        paso = 0.1
    elif v < 10:
        paso = 0.5
    elif v < 1000:
        paso = mag / 10
    else:
        paso = mag / 20
    f = math.ceil if hacia == "arriba" else math.floor
    r = f(v / paso + 1e-9) * paso
    r = round(r, 2)
    return int(r) if float(r).is_integer() else r


def fmt(v, unit):
    if isinstance(v, float) and not v.is_integer():
        s = f"{v:.1f}"
    else:
        s = f"{int(v):,}".replace(",", ",")
    return s + unit


def tramos_numericos(vals, campo, nombres, usos):
    """Tres tramos por terciles redondeados; None si el campo no reparte."""
    s = sorted(vals)
    n = len(s)
    distintos = sorted(set(s))
    unit = CAMPOS[campo]["unit"]
    if len(distintos) <= 5:
        # Pocos valores distintos (18", 22", 24"): una tarjeta por valor.
        tiers = []
        for v in distintos:
            cnt = s.count(v)
            if cnt / n < MIN_TRAMO:
                continue
            tiers.append({"id": slug(f"v{v}"), "name": fmt(v, unit), "use": "", "spec": fmt(v, unit), "values": [v]})
        if len(tiers) < 2 or max(s.count(float(t["values"][0])) for t in tiers) / n > MAX_DOMINANTE:
            return None
        return tiers
    for a, b in ((0.33, 0.66), (0.25, 0.75), (0.4, 0.8)):
        c1 = redondo(s[int(n * a)], "abajo")
        c2 = redondo(s[int(n * b)], "abajo")
        if c1 <= s[0] or c2 <= c1 or c2 >= s[-1] or c2 < c1 * 1.15:
            continue
        partes = [sum(1 for v in s if v <= c1), sum(1 for v in s if c1 < v <= c2), sum(1 for v in s if v > c2)]
        if min(partes) / n < MIN_TRAMO or max(partes) / n > MAX_DOMINANTE:
            continue
        entero = all(float(v).is_integer() for v in (c1, c2))
        desde = (c1 + 1) if entero else c1
        return [
            {"id": slug(nombres[0]), "name": nombres[0], "use": usos[0], "spec": f"Hasta {fmt(c1, unit)}", "max": c1},
            {"id": slug(nombres[1]), "name": nombres[1], "use": usos[1],
             "spec": (f"{fmt(desde, unit)} a {fmt(c2, unit)}" if entero else f"Más de {fmt(c1, unit)}, hasta {fmt(c2, unit)}"),
             "min": c1, "max": c2},
            {"id": slug(nombres[2]), "name": nombres[2], "use": usos[2], "spec": f"Más de {fmt(c2, unit)}", "min": c2},
        ]
    return None


def tramos_fijos(vals, campo):
    label, criterion, defs = FIJOS[campo]
    n = len(vals)
    tiers = []
    for tid, name, use, spec, lo, hi in defs:
        cnt = sum(1 for v in vals if (lo is None or v > lo) and (hi is None or v <= hi))
        if cnt == 0:
            continue
        t = {"id": tid, "name": name, "use": use, "spec": spec, "_n": cnt}
        if lo is not None: t["min"] = lo
        if hi is not None: t["max"] = hi
        tiers.append(t)
    if len(tiers) < 2 or max(t["_n"] for t in tiers) / n > MAX_DOMINANTE:
        return None
    for t in tiers:
        del t["_n"]
    return tiers


def tramos_categoricos(vals, campo):
    cfg = CAMPOS[campo]
    n = len(vals)
    cnt = collections.Counter(str(v) for v in vals)
    if cfg.get("orden"):
        orden = [v for v in cfg["orden"] if v in cnt] + sorted(v for v in cnt if v not in cfg["orden"])
    elif cfg.get("ordinal"):
        orden = sorted(cnt, key=lambda v: float(re.sub(r"[^\d.]", "", v) or 0))
    else:
        orden = [v for v, _ in cnt.most_common()]
    orden = [v for v in orden if cnt[v] / n >= MIN_TRAMO][:6]
    if len(orden) < 2 or cnt[orden[0]] / n > MAX_DOMINANTE and len(orden) < 3:
        return None
    if max(cnt[v] for v in orden) / n > MAX_DOMINANTE:
        return None
    usos = cfg.get("valores", {})
    return [{"id": slug(v), "name": v, "use": usos.get(v, ""), "spec": v, "values": [v]} for v in orden]


def eje(clave, campo, vals):
    cfg = CAMPOS.get(campo)
    if campo in FIJOS:
        label, criterion, _ = FIJOS[campo]
        tiers = tramos_fijos(vals, campo)
        ramp = campo not in FIJOS_SIN_RAMPA
    elif cfg and "unit" in cfg:
        nombres, usos = cfg["nombres"], cfg["usos"]
        esp = USOS.get((clave, campo)) or USOS.get((clave.split("/")[0], campo))
        if esp:
            nombres, usos = esp
        label, criterion = cfg["label"], cfg["criterion"]
        tiers = tramos_numericos(vals, campo, nombres, usos)
        ramp = True
    elif cfg:
        label, criterion = cfg["label"], cfg["criterion"]
        tiers = tramos_categoricos(vals, campo)
        # Solo se colorea de menos a más lo que tiene un orden (talla, rin).
        ramp = bool(cfg.get("ramp", True)) and (bool(cfg.get("orden")) or bool(cfg.get("ordinal")))
    else:
        return None
    if not tiers:
        return None
    return {"label": label, "field": campo, "criterion": criterion, "ramp": ramp, "tiers": tiers}


def claves_a_mano():
    """Las claves que ya tienen eje escrito en js/app.js: esas no se tocan."""
    try:
        js = io.open(APP_JS, encoding="utf-8").read()
    except OSError:
        return set()
    blk = js[js.index("const QUALITY_AXES = {"):js.index("const QUALITY_INTRO = {")]
    return set(re.findall(r'^\s{4}"?([^"\n:]+?)"?:\s*\[', blk, re.M))


def armar(products, a_mano):
    grupos = collections.defaultdict(list)
    for p in products:
        grupos[(p["category"], p.get("subcategory"))].append(p)
    por_cat = collections.defaultdict(list)
    for (cat, sub), ps in grupos.items():
        por_cat[cat].extend(ps)
    claves = [(f"{cat}/{sub}", ps) for (cat, sub), ps in grupos.items() if sub] + \
             [(cat, ps) for cat, ps in por_cat.items()]
    salida, resumen = {}, []
    cats_con_sub_a_mano = {k.split("/")[0] for k in a_mano if "/" in k}
    for clave, ps in claves:
        if clave in a_mano or len(ps) < MIN_FICHAS:
            continue
        cat = clave.split("/")[0]
        # Lo escrito a mano manda en toda su categoría: un eje de categoría
        # (Celulares por almacenamiento) vale para sus subcategorías y no
        # se sustituye por uno generado; y donde hay subcategorías a mano
        # (Electrodomésticos) la vista de categoría no lleva eje generado.
        if cat in a_mano:
            continue
        if "/" not in clave and cat in cats_con_sub_a_mano:
            continue
        # Un producto entra en un campo si su facet trae ese dato.
        por_campo = collections.defaultdict(list)
        for p in ps:
            for k, v in (p.get("facets") or {}).items():
                if v is None or isinstance(v, (list, dict, bool)):
                    continue
                por_campo[k].append(v)
        axes = []
        orden = PRIORIDAD_ESPECIFICA.get(clave) or PRIORIDAD_ESPECIFICA.get(cat)
        campos = (orden + [c for c in PRIORIDAD if c not in orden]) if orden else PRIORIDAD
        for campo in campos:
            vals = por_campo.get(campo)
            if not vals or len(vals) < MIN_CON_DATO or len(vals) / len(ps) < MIN_COBERTURA:
                continue
            if campo in CAMPO_SOLO_EN and cat not in CAMPO_SOLO_EN[campo] and clave not in CAMPO_SOLO_EN[campo]:
                continue
            if campo in FIJOS or "unit" in CAMPOS.get(campo, {}):
                nums = [v for v in vals if isinstance(v, (int, float))]
                if len(nums) < len(vals) * 0.9:
                    continue
                vals = nums
            e = eje(clave, campo, vals)
            if not e:
                continue
            e["key"] = "level" if not axes else "size"
            axes.append(e)
            if len(axes) == 2:
                break
        if not axes:
            continue
        intro = INTROS.get(clave) or INTROS.get(cat)
        salida[clave] = {"axes": axes}
        if intro:
            salida[clave]["intro"] = intro
        resumen.append((clave, len(ps), axes, por_campo))
    return salida, resumen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    data = load_catalog()
    a_mano = claves_a_mano()
    salida, resumen = armar(data["products"], a_mano)
    subs_total = len({(p["category"], p.get("subcategory")) for p in data["products"] if p.get("subcategory")})
    con_bloque = {k for k in salida if "/" in k} | {k for k in a_mano if "/" in k}
    cats_con = {k for k in salida if "/" not in k} | {k for k in a_mano if "/" not in k}
    cubiertas = 0
    for (cat, sub) in {(p["category"], p.get("subcategory")) for p in data["products"] if p.get("subcategory")}:
        if f"{cat}/{sub}" in con_bloque or cat in cats_con:
            cubiertas += 1
    print(f"Ejes generados: {len(salida)} claves ({sum(1 for k in salida if '/' in k)} subcategorías, "
          f"{sum(1 for k in salida if '/' not in k)} categorías). A mano en app.js: {len(a_mano)}.")
    print(f"Subcategorías con bloque (a mano o generado, propio o de su categoría): {cubiertas} de {subs_total}\n")
    for clave, n, axes, por_campo in sorted(resumen, key=lambda r: -r[1]):
        print(f"== {clave}  (n={n})")
        for e in axes:
            cob = len(por_campo[e["field"]]) / n
            tr = " | ".join(f"{t['name']} [{t['spec']}]" for t in e["tiers"])
            print(f"   {e['key']:5} {e['label']} · {e['field']} ({cob:.0%}): {tr}")
    if args.dry_run:
        print("\n(dry-run: no se escribió nada)")
        return
    with io.open(SALIDA, "w", encoding="utf-8") as fh:
        json.dump(salida, fh, ensure_ascii=False, indent=1)
    print(f"\nEscrito {os.path.relpath(SALIDA)} ({len(salida)} claves)")


if __name__ == "__main__":
    main()
