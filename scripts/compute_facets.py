#!/usr/bin/env python3
"""Calcula el objeto `facets` de cada producto de Celulares/Laptops/Tabletas
y lo guarda en el catálogo, para alimentar los filtros de "Memoria",
"Almacenamiento", "Procesador", "Tarjeta gráfica", etc. de la interfaz.

Las funciones de extracción puras viven en specs_extract.py (solo toman
texto/marca, sin conocer specs[] ni la categoría). Este script es la capa
que sí conoce el catálogo:

  1. Cuando el producto trae specs[] con una etiqueta reconocida (p.ej.
     "Memoria RAM: 8 GB", "Procesador: Apple A16 Bionic"), ese valor ya
     viene desambiguado por la propia etiqueta -- no hay que adivinar si
     un número es RAM o almacenamiento, la tienda ya lo dijo. Se usa ESE
     valor en vez del nombre cuando existe.
  2. Si no hay specs[] útil para ese campo, se cae al nombre (mismas
     funciones de specs_extract.py que ya se probaron contra el catálogo).
  3. Se aplica un rango de pulgadas de pantalla plausible POR CATEGORÍA
     (un celular normal no mide 12", una laptop no mide 3.3") -- este
     filtro de cordura es justo lo que specs_extract.py NO puede hacer por
     sí solo porque no conoce la categoría del producto.

Uso:
  python3 scripts/compute_facets.py --dry-run   # solo reporta conteos
  python3 scripts/compute_facets.py              # aplica y guarda
"""
import argparse
import re
import sys
import unicodedata
from collections import Counter

sys.path.insert(0, "scripts")
from data_io import load_catalog, save_catalog
import specs_extract as se


def _norm_label(s):
    s = unicodedata.normalize("NFD", (s or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()


_GB_VALUE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(gb|tb)\b", re.I)


def _gb_of(value):
    """Un solo valor 'NN GB'/'NN TB' ya desambiguado por su propia
    etiqueta (specs[] "Almacenamiento"/"Memoria RAM"/"Capacidad") -- no
    hay que decidir cuál es cuál, la etiqueta ya lo dice."""
    m = _GB_VALUE_RE.search(value or "")
    if not m:
        return None
    num = float(m.group(1).replace(",", "."))
    if m.group(2).lower() == "tb":
        num *= 1024
    return int(num)


def _spec_map(product):
    out = {}
    for s in product.get("specs") or []:
        lbl = _norm_label(s.get("label"))
        val = s.get("value")
        if lbl and val:
            out.setdefault(lbl, val)
    return out


# Rango de pulgadas plausible por categoría -- fuera de rango se descarta
# (no se adivina "cuál de los dos números es el bueno", se tira el dato).
# Celulares: un plegable tipo libro (Mate XT, Fold) sí llega a ~10-11" en
# la etiqueta de pantalla interior -- de ahí el rango ampliado cuando el
# nombre trae una palabra de plegable.
# Categorías con facets PROPIOS (RAM, pulgadas, BTU, kilos de carga...):
# una categoría entra acá cuando de sus nombres se puede sacar un atributo
# REAL, no cuando nos gustaría tenerlo. El resto del catálogo no se queda
# sin nada: los campos genéricos de SPEC_GENERALES y NOMBRE_GENERALES (más
# abajo) se leen en todas las categorías, y son los que alimentan "Compara
# calidad" donde no hay eje escrito a mano (scripts/compute_quality_axes.py).
FACET_CATEGORIES = (
    "Celulares", "Laptops", "Tabletas", "Monitores",
    "Televisores", "Videojuegos", "Lavadoras", "Refrigeradores",
    "Blancos y ropa de cama", "Muebles",
    "Computadoras de escritorio", "Almacenamiento", "Climatización",
    "Refacciones", "Herramientas", "Bocinas",
    "Autos, bicicletas y motos", "Electrodomésticos", "Joyería y bisutería",
    "Cargadores y adaptadores",
    # Hogar: lo que decide la compra es UN dato (tazas, litros, watts,
    # horas de batería) y las tiendas lo escriben en el nombre o la ficha.
    "Proyectores y accesorios", "Aspiradoras", "Cafeteras", "Audífonos",
    "Impresoras",
)

_FOLDABLE_RE = re.compile(r"\bplegable\b|\bfold\b|\bflip\b")
_SCREEN_RANGE = {
    "Celulares": (3.0, 7.5),
    "Celulares_foldable": (3.0, 11.0),
    "Laptops": (9.0, 19.0),
    "Tabletas": (6.0, 16.0),
}

# Mismo criterio que el rango de pantalla: un valor de RAM/almacenamiento
# fuera de lo que existe de verdad en el mercado no se "corrige" -- se
# descarta (None). Aparece sobre todo en dos casos reales del catálogo:
# specs[] con un error de captura de la tienda ("Memoria RAM: 256 GB" en
# un iPhone -- la tienda copió el almacenamiento en el campo de RAM) y
# títulos con anuncios de almacenamiento inflados tipo spam ("4GB RAM
# 112TB" en laptops de $6,000 que en la vida real traen 128GB eMMC).
# Los topes son generosos a propósito (el equipo real más caro del
# catálogo, no un promedio) para no descartar nada legítimo.
_RAM_RANGE = {
    "Celulares": (1, 24),      # ROG Phone 9 (24GB) es el flagship real más alto visto
    "Laptops": (2, 128),       # ASUS ROG Flow Z13 / ProArt con memoria unificada de 128GB
    "Tabletas": (1, 32),
    # Una torre acepta más módulos que cualquier laptop: 256GB es una
    # estación de trabajo real, no un error de captura.
    "Computadoras de escritorio": (2, 256),
}
_STORAGE_RANGE = {
    "Celulares": (4, 2048),    # 2TB ya es un buque insignia excepcional
    "Laptops": (4, 8192),      # 8TB cubre workstations reales (RAID/NVMe dobles)
    "Tabletas": (4, 2048),
    "Computadoras de escritorio": (4, 16384),
}


def _in_range(val, ranges, category):
    if val is None:
        return None
    lo, hi = ranges[category]
    return val if lo <= val <= hi else None


def _screen_in(category, name, spec_map):
    val = None
    # "tamaño de la pantalla" es como lo llama la ficha técnica de Elektra.
    for lbl in ("pantalla", "tamano de la pantalla"):
        if lbl in spec_map:
            val = se.screen_size_in(spec_map[lbl])
            if val is not None:
                break
    if val is None:
        val = se.screen_size_in(name)
    if val is None:
        return None
    lo, hi = _SCREEN_RANGE[category]
    if category == "Celulares" and _FOLDABLE_RE.search(se._norm(name)):
        lo, hi = _SCREEN_RANGE["Celulares_foldable"]
    if lo <= val <= hi:
        return val
    return None


def _ram_storage(category, name, spec_map):
    # Caso más confiable: la tienda separó RAM y Almacenamiento en dos
    # campos propios -- no hay ambigüedad alguna que resolver.
    ram = None
    for lbl in ("memoria ram", "ram"):
        if lbl in spec_map:
            ram = _gb_of(spec_map[lbl])
            break
    storage = None
    # "disco duro" y "capacidad de almacenamiento" los trae la ficha técnica
    # de Elektra (ver elektra_specs.py); "memoria interna" es como llama
    # Elektra al almacenamiento de un celular.
    for lbl in ("almacenamiento", "capacidad de almacenamiento", "disco duro",
                "memoria interna", "capacidad"):
        if lbl in spec_map:
            storage = _gb_of(spec_map[lbl])
            break
    if ram is not None or storage is not None:
        # Lo que la ficha no diga se completa con el nombre, sin pisar lo que
        # sí vino confirmado por specs[].
        #
        # La condición de antes ("if ram is None or storage is not None")
        # dejaba fuera justo el caso de una ficha que declara la RAM y no el
        # almacenamiento: devolvía (ram, None) sin mirar el nombre. Empezó a
        # doler al importar las fichas de Elektra, donde las torres traen
        # "Memoria RAM" pero el almacenamiento se llama "Disco Duro": la
        # cobertura de storage_gb en Computadoras de escritorio se desplomó
        # de 94% a 29%.
        if ram is None or storage is None:
            n_ram, n_storage = se.ram_storage_gb(name)
            if ram is None:
                ram = n_ram
            if storage is None:
                storage = n_storage
        return ram, storage
    # Campo combinado "RAM + Almacenamiento": "12 GB + 512 GB" -- el
    # orden de la etiqueta ya dice cuál es cuál, se lee posicional en vez
    # de usar el criterio "el mayor es almacenamiento" (que aquí no hace
    # falta adivinar).
    if "ram + almacenamiento" in spec_map:
        nums = _GB_VALUE_RE.findall(spec_map["ram + almacenamiento"])
        if len(nums) == 2:
            def _to_gb(n, unit):
                v = float(n.replace(",", "."))
                return int(v * 1024) if unit.lower() == "tb" else int(v)
            return _to_gb(*nums[0]), _to_gb(*nums[1])
    return se.ram_storage_gb(name)


def _chipset(category, name, spec_map, brand):
    if "procesador" in spec_map:
        val = se.chipset_family(spec_map["procesador"])
        if val:
            return val
    return se.chipset_family(name)


def _cpu(name, spec_map, brand):
    if "procesador" in spec_map:
        val = se.cpu_family(spec_map["procesador"], brand)
        if val:
            return val
    return se.cpu_family(name, brand)


def _camera(spec_map, name):
    if "camara principal" in spec_map:
        val = se.camera_mp(spec_map["camara principal"])
        if val:
            return val
    return se.camera_mp(name)


def _network(spec_map, name):
    if "conectividad" in spec_map:
        val = se.network_gen(spec_map["conectividad"])
        if val:
            return val
    return se.network_gen(name)


# "DS 150" y "DS150" son el mismo modelo escrito de dos formas. Se agrupan
# por el nombre sin espacios y se muestra la grafía que la tienda usa más
# veces -- que hay que contar sobre el catálogo entero, así que se arma en
# main() antes de recalcular nada.
_COMPAT_CANON = {}


def _compat_key(modelo):
    return re.sub(r"\s+", "", (modelo or "")).upper()


def build_compat_canon(products):
    conteo = {}
    for p in products:
        if p.get("category") != "Refacciones":
            continue
        compat = _spec_map(p).get("compatibilidad")
        if not compat:
            continue
        for m in se.compat_of(compat)[0]:
            conteo.setdefault(_compat_key(m), {}).setdefault(m, 0)
            conteo[_compat_key(m)][m] += 1
    _COMPAT_CANON.clear()
    for clave, grafias in conteo.items():
        _COMPAT_CANON[clave] = max(grafias.items(), key=lambda kv: (kv[1], -len(kv[0])))[0]
    return len(_COMPAT_CANON)


# Facetas que la ficha técnica ya declara y que solo hay que copiar. Nacen
# de un barrido del catálogo buscando (categoría, etiqueta) con al menos 35%
# de cobertura y entre 2 y 12 valores distintos -- o sea, campos que la
# tienda llena de forma consistente y que enumeran, no texto libre.
#
#   (categoría, subcategoría o None, etiqueta, campo de la faceta)
SPEC_DIRECTAS = (
    # La firmeza es la segunda pregunta de un colchón, después de la medida.
    ("Muebles", "Colchones", "nivel de firmeza", "firmness"),
    # Para un ventilador, el tipo manda sobre las pulgadas: uno de techo y
    # uno de escritorio no se comparan aunque midan lo mismo. Y la tienda lo
    # declara en el 78% contra el 43% que se leía del nombre.
    ("Climatización", "Ventiladores", "tipo de ventilador", "fan_type"),
    # Herramientas es la categoría más grande sin una sola faceta (7,243).
    ("Herramientas", None, "tipo de herramienta", "tool_type"),
    ("Bocinas", None, "numero de bocinas", "speaker_count"),
    # Medida de la llanta y de la rueda: la primera pregunta al comprar
    # cualquiera de las dos, y la tienda las escribe siempre igual (R14,
    # R16, R26, R29...).
    ("Autos, bicicletas y motos", "Llantas", "rin", "rim_size"),
    ("Autos, bicicletas y motos", None, "rodada", "wheel_size"),
    # Con qué funciona la estufa: gas LP, natural o electricidad. Cambia si
    # se puede instalar en la casa, no es un detalle de ficha.
    ("Electrodomésticos", "Estufas", "emplea", "fuel"),
    ("Electrodomésticos", "Hornos", "emplea", "fuel"),
    # Calentador y calefactor: mismo dato, misma etiqueta, misma razón.
    ("Electrodomésticos", "Calentadores de agua", "emplea", "fuel"),
    ("Climatización", "Calefactores", "emplea", "fuel"),
    # Instantáneo, de paso o de depósito: cambia la instalación y el gasto.
    ("Electrodomésticos", "Calentadores de agua", "tipo de boiler", "heater_type"),
    ("Joyería y bisutería", "Relojes", "genero", "gender", "_gender"),
    ("Videojuegos", "Software", "clasificacion", "age_rating", "_age"),
    ("Electrodomésticos", "Estufas", "numero de quemadores", "burners", "_burners"),
)


# La clasificación por edad mezcla DOS sistemas y el mismo código significa
# cosas opuestas en cada uno: "C Adultos +18" es 18+ en el sistema mexicano
# y "C Infancia Temprana" es la EC de la ESRB, o sea preescolar. Normalizar
# por la letra pondría los juegos de adultos junto a los de niños -- el
# error más caro posible en este filtro.
#
# Por eso la tabla es EXPLÍCITA, valor por valor, y lo que no está en ella
# no se clasifica: quedan fuera los 119 "C" a secas (no se sabe de qué
# sistema es), los 26 "A 18 Años en adelante" (la A es "todo público": el
# valor se contradice solo) y los "RP" sin clasificar.
_EDADES = {
    "a": "Todo público",
    "e todas las edades": "Todo público",
    "c infancia temprana": "Todo público",
    "e10 10 años en adelante": "10 años o más",
    "b": "12 años o más",
    "b 12 años en adelante": "12 años o más",
    "t 13 años en adelante": "13 años o más",
    "b 15 años en adelante": "15 años o más",
    "m 17 años en adelante": "17 años o más",
    "c adultos +18": "18 años o más",
}

_GENEROS = {"caballero": "Hombre", "hombre": "Hombre", "dama": "Mujer",
            "mujer": "Mujer", "unisex": "Unisex", "niño": "Niño", "niña": "Niña"}


# Las claves de las dos tablas se escriben con acentos para que se lean,
# pero _norm_label() los quita ("años" -> "anos"): sin pasar las claves por
# la misma función, solo acertaban las que no llevaban ninguno -- y de las
# diez clasificaciones por edad entraban tres.
_EDADES = {_norm_label(k): v for k, v in _EDADES.items()}
_GENEROS = {_norm_label(k): v for k, v in _GENEROS.items()}


def _age(valor):
    return _EDADES.get(_norm_label(valor))


def _gender(valor):
    return _GENEROS.get(_norm_label(valor))


def _burners(valor):
    """Solo el número, y solo si es uno solo y plausible. La tienda escribe
    "4", "5 quemadores", "4 zonas de inducción" y también "NA" o "5,5"."""
    nums = re.findall(r"\d+", valor or "")
    if len(nums) != 1:
        return None
    n = int(nums[0])
    return str(n) if 1 <= n <= 8 else None


def _spec_directa(product, spec_map, f):
    cat, sub = product.get("category"), product.get("subcategory")
    for regla in SPEC_DIRECTAS:
        c, s_, etiqueta, campo = regla[:4]
        if c != cat or (s_ is not None and s_ != sub):
            continue
        val = spec_map.get(etiqueta)
        if not val:
            continue
        # Quinta posición opcional: el nombre de la función que normaliza el
        # valor. Sin ella se copia tal cual.
        if len(regla) > 4:
            val = globals()[regla[4]](val)
        if val:
            f[campo] = val


def _primero(fn, *fuentes):
    """fn(texto) sobre la primera fuente que devuelva algo. Las fuentes van
    en orden de confianza: el valor de la spec (ya etiquetado) antes que el
    nombre (hay que interpretarlo)."""
    for src in fuentes:
        if not src:
            continue
        v = fn(src)
        if v is not None:
            return v
    return None


def _hogar_facets(product, name, spec_map, f):
    """Facetas de las categorías del hogar (electrodomésticos, bocinas,
    audífonos, cafeteras...). Un campo por decisión de compra, leído de la
    ficha y si no del nombre; el rango plausible es por categoría porque
    1,500 W es normal en un calefactor y absurdo en una bocina."""
    category, sub = product.get("category"), product.get("subcategory")
    watts = spec_map.get("potencia en watts")
    if category == "Proyectores y accesorios" and sub == "Proyectores":
        r = _primero(se.resolution_of, spec_map.get("calidad de la imagen"),
                     spec_map.get("resolucion"), name)
        if r:
            f["resolution"] = r
    elif category == "Aspiradoras":
        w = _primero(lambda t: se.power_watts(t, 50, 3000), watts, name)
        if w is not None:
            f["power_w"] = w
    elif category == "Cafeteras":
        tazas = spec_map.get("capacidad en tazas", "").strip()
        cups = int(tazas) if re.fullmatch(r"\d{1,3}", tazas) else None
        if cups is None:
            cups = _primero(se.cups_of, spec_map.get("capacidad"), name)
        if cups:
            f["cups"] = cups
    elif category == "Audífonos":
        h = _primero(se.battery_hours_of, spec_map.get("duracion de la bateria"), name)
        if h is not None:
            f["battery_h"] = h
    elif category == "Impresoras" and sub != "Consumibles":
        mf = se.multifunction_of(name, spec_map.get("escanea"))
        if mf:
            f["multifunction"] = mf
    elif category == "Bocinas":
        w = _primero(lambda t: se.power_watts(t, 1, 3000), watts, name)
        if w is not None:
            f["power_w"] = w
        h = _primero(se.battery_hours_of, spec_map.get("duracion de la bateria"), name)
        if h is not None:
            f["battery_h"] = h
    elif category == "Climatización" and sub == "Calefactores":
        w = _primero(lambda t: se.power_watts(t, 100, 10000), watts, name)
        if w is not None:
            f["power_w"] = w
    elif category == "Muebles" and sub == "Sillas":
        tipo = se.chair_type_of(name)
        if tipo:
            f["chair_type"] = tipo
    elif category == "Electrodomésticos":
        if sub == "Campanas de cocina":
            cm = _primero(se.hood_width_cm, name, spec_map.get("tamano en pulgadas"))
            if cm is not None:
                f["hood_cm"] = cm
        elif sub == "Microondas":
            litros = _primero(lambda t: se.liters_of(t, 10, 60, cubic_feet=True),
                              spec_map.get("capacidad en litros"), spec_map.get("capacidad"),
                              spec_map.get("capacidad en pies"), name)
            if litros is not None:
                f["liters"] = litros
        elif sub == "Freidoras de aire":
            litros = _primero(lambda t: se.liters_of(t, 1, 60, quarts=True),
                              spec_map.get("capacidad"), name)
            if litros is not None:
                f["liters"] = litros
        elif sub in ("Licuadoras", "Extractores de jugo"):
            w = _primero(lambda t: se.power_watts(t, 100, 3000), watts, name)
            if w is not None:
                f["power_w"] = w
        elif sub == "Calentadores de agua":
            n = _primero(lambda t: se.services_of(t, 0.5, 20),
                         spec_map.get("numero de servicios"), name)
            if n is not None:
                f["services"] = n
        elif sub == "Lavavajillas":
            n = _primero(lambda t: se.services_of(t, 4, 20),
                         spec_map.get("numero de servicios"), name)
            if n is not None:
                f["services"] = n


# ---------------------------------------------------------------------
# Genéricos: un dato por decisión de compra en las categorías que no tenían
# ninguno (juguetes, herramientas, maletas, mascotas, deportes, joyería...).
# Es lo que alimenta "Compara calidad" en todas las subcategorías: sin un
# campo con datos no hay tarjetas que mostrar.
#
# Dos fuentes, en este orden: la ficha de la tienda (SPEC_GENERALES: una
# etiqueta -> un campo, con su normalizador) y el nombre (NOMBRE_GENERALES:
# por categoría o subcategoría, con el rango plausible). Ninguna pisa un
# campo que la rama propia de la categoría ya llenó.
# ---------------------------------------------------------------------
SPEC_GENERALES = (
    ("edad recomendada", "age_min", se.age_years_of),
    ("numero de jugadores", "players_max", se.players_max_of),
    ("capacidad de carga", "load_kg", lambda v: se.kg_of(v, 1, 2000)),
    ("potencia en watts", "power_w", lambda v: se.power_watts(v, 1, 30000)),
    ("voltaje", "volt", lambda v: se.volts_of(v, 3, 480)),
    ("voltaje de salida", "volt", lambda v: se.volts_of(v, 1, 480)),
    ("pulgadas", "size_in", lambda v: se.inches_of(v, 8, 120)),
    ("tamano en pulgadas", "size_in", lambda v: se.inches_of(v, 3, 120)),
    ("tamano", "size_in", lambda v: se.inches_of(v, 8, 120)),
    ("tamano", "size_label", lambda v: se.size_label_of(v, bare=True)),
    ("talla del casco", "size_label", lambda v: se.size_label_of(v, bare=True)),
    ("talla", "size_label", lambda v: se.size_label_of(v, bare=True)),
    ("tipo de casco", "helmet_type", lambda v: v.strip().title() if v.strip() else None),
    # Solo en muebles: en blancos y utensilios "dimensiones" es la caja.
    ("dimensiones (l x al x an)", "length_cm", lambda v: se.first_dimension_cm(v, 20, 400),
     ("Muebles", "Decoración de hogar y jardín", "Equipo comercial")),
    ("resistencia al agua", "water_resistant", se.water_resistant_of),
    ("tamano de la raza", "breed_size", se.breed_size_of),
    ("etapa de vida de la mascota", "pet_stage", se.pet_stage_of),
    ("deporte", "sport", lambda v: v.strip().title() if v.strip() and v.strip().lower() not in ("recreativo", "no aplica") else None),
    ("numero de hilos", "thread_count", se.thread_count_of),
    ("velocidades", "speeds", se.speeds_of),
    ("tipo de bicicletas", "bike_type", lambda v: v.strip().title() if v.strip() else None),
    ("consola", "platform", se.platform_spec_of),
    ("material", "material", se.material_of),
    ("tipo de piedra", "stone", se.stone_of),
    ("megapixeles", "camera_mp", lambda v: se.megapixels_of(v, 1, 200)),
    ("capacidad en litros", "liters", lambda v: se.liters_of(v, 0.1, 2000)),
    ("genero", "gender", _gender),
    ("capacidad de bateria (mah)", "battery_mah", lambda v: se.mah_of(v, 100, 100000)),
)

# (categoría, subcategoría o None) -> [(campo, función(nombre))]. El rango
# va en la función porque "1500 W" es una secadora de pelo y también un
# panel solar grande.
def _w(lo, hi):
    return lambda t: se.power_watts(t, lo, hi)


NOMBRE_GENERALES = {
    ("Herramientas", None): [("power_w", _w(50, 5000)), ("volt", lambda t: se.volts_of(t, 3, 240))],
    ("Movilidad eléctrica", None): [("power_w", _w(100, 8000)), ("range_km", lambda t: se.range_km_of(t, 10, 300)),
                                    ("battery_ah", lambda t: se.ah_of(t, 2, 100)), ("volt", lambda t: se.volts_of(t, 12, 120))],
    ("Autos, bicicletas y motos", "Bocinas para auto"): [("power_w", _w(10, 20000)), ("size_in", lambda t: se.inches_of(t, 3, 21))],
    ("Autos, bicicletas y motos", "Amplificadores para auto"): [("power_w", _w(10, 20000))],
    ("Autos, bicicletas y motos", "Estéreos para auto"): [("size_in", lambda t: se.inches_of(t, 4, 13)), ("power_w", _w(10, 500))],
    ("Autos, bicicletas y motos", "Motocicletas"): [("engine_cc", lambda t: se.engine_cc_of(t, 49, 2500)), ("power_w", _w(200, 20000))],
    ("Autos, bicicletas y motos", "Cascos para moto"): [("size_label", se.size_label_of)],
    ("Autos, bicicletas y motos", "Baterías para auto"): [("volt", lambda t: se.volts_of(t, 6, 48))],
    ("Instrumentos musicales", "Amplificadores"): [("power_w", _w(5, 5000))],
    ("Iluminación", None): [("power_w", _w(1, 600))],
    ("Domótica y hogar inteligente", "Iluminación inteligente"): [("power_w", _w(1, 200))],
    ("Belleza y cuidado personal", "Secadoras de cabello"): [("power_w", _w(300, 3500))],
    ("Belleza y cuidado personal", "Planchas para cabello"): [("power_w", _w(10, 500))],
    ("Otros", "Generadores"): [("power_w", _w(300, 30000))],
    ("Otros", "Inversores"): [("power_w", _w(50, 20000))],
    ("Otros", "Paneles solares"): [("power_w", _w(5, 1000))],
    ("Otros", "Estaciones de energía"): [("power_w", _w(100, 10000))],
    ("Otros", "Radios"): [("power_w", _w(1, 300))],
    ("Otros", "Varios"): [("volume_ml", lambda t: se.ml_of(t, 10, 5000))],
    ("Electrodomésticos", "Pequeños electrodomésticos de cocina"): [("power_w", _w(100, 3000)), ("liters", lambda t: se.liters_of(t, 0.3, 60, quarts=True))],
    ("Electrodomésticos", "Planchas"): [("power_w", _w(500, 3500))],
    ("Electrodomésticos", "Hornos"): [("liters", lambda t: se.liters_of(t, 5, 150)), ("power_w", _w(500, 6000))],
    ("Electrodomésticos", "Máquinas de coser"): [("power_w", _w(20, 300))],
    ("Climatización", "Purificadores de aire"): [("power_w", _w(3, 500))],
    ("Climatización", "Humidificadores"): [("liters", lambda t: se.liters_of(t, 0.3, 30)), ("power_w", _w(3, 500))],
    ("Climatización", "Deshumidificadores"): [("liters", lambda t: se.liters_of(t, 1, 100)), ("power_w", _w(20, 1500))],
    ("Climatización", "Climatizadores evaporativos"): [("liters", lambda t: se.liters_of(t, 3, 150))],
    ("Equipo comercial", None): [("power_w", _w(100, 30000)), ("liters", lambda t: se.liters_of(t, 5, 3000))],
    ("Refrigeradores", "Frigobares"): [("liters", lambda t: se.liters_of(t, 15, 300))],
    ("Refrigeradores", "Uso comercial"): [("liters", lambda t: se.liters_of(t, 50, 3000))],
    ("Baterías portátiles", None): [("charger_w", se.charger_watts)],
    ("Deportes y fitness", "Pesas"): [("weight_kg", lambda t: se.kg_of(t, 0.5, 300))],
    ("Deportes y fitness", "Balones"): [("ball_no", se.ball_number_of)],
    ("Deportes y fitness", "Voleibol"): [("ball_no", se.ball_number_of)],
    ("Deportes y fitness", "Bicicletas fijas"): [("load_kg", lambda t: se.kg_of(t, 50, 300))],
    ("Salud", "Básculas"): [("load_kg", lambda t: se.kg_of(t, 50, 1000))],
    ("Salud", "Cuidado del cabello"): [("volume_ml", lambda t: se.ml_of(t, 10, 5000))],
    ("Salud", "Cuidado personal"): [("volume_ml", lambda t: se.ml_of(t, 10, 5000))],
    ("Salud", "Depilación"): [("volume_ml", lambda t: se.ml_of(t, 10, 5000))],
    ("Belleza y cuidado personal", "Maquillaje"): [("volume_ml", lambda t: se.ml_of(t, 1, 2000))],
    ("Juguetes y bebés", "Biberones"): [("volume_ml", lambda t: se.ml_of(t, 30, 500))],
    ("Juguetes y bebés", "Peluches"): [("length_cm", lambda t: se.length_cm_of(t, 8, 250))],
    ("Juguetes y bebés", "Figuras de acción"): [("length_cm", lambda t: se.length_cm_of(t, 4, 120))],
    ("Juguetes y bebés", "Bloques de construcción"): [("pieces", lambda t: se.pieces_of(t, 10, 20000))],
    ("Juguetes y bebés", "Montables"): [("volt", lambda t: se.volts_of(t, 6, 48))],
    ("Juegos de mesa", "Rompecabezas"): [("pieces", lambda t: se.pieces_of(t, 20, 60000))],
    ("Cámaras y fotografía", None): [("camera_mp", lambda t: se.megapixels_of(t, 2, 200))],
    ("Cámaras de seguridad", None): [("camera_mp", lambda t: se.megapixels_of(t, 1, 24))],
    ("Videojuegos", "Consolas"): [("storage_gb", se.drive_capacity_gb)],
    ("Proyectores y accesorios", "Pantallas de proyección"): [("screen_in", lambda t: se.inches_of(t, 40, 400))],
    ("Decoración de hogar y jardín", "Asadores"): [("size_in", lambda t: se.inches_of(t, 12, 80))],
    ("Mascotas", "Bebederos"): [("liters", lambda t: se.liters_of(t, 0.3, 30))],
    ("Cargadores y adaptadores", "De pilas"): [("volt", lambda t: se.volts_of(t, 1, 48))],
    ("Viajes", "Maletas"): [("size_in", lambda t: se.inches_of(t, 14, 34))],
    ("Autos, bicicletas y motos", "Baterías para auto"): [("battery_ah", lambda t: se.ah_of(t, 2, 300))],
    ("Deportes y fitness", "Boxeo"): [("glove_oz", lambda t: se.oz_of(t, 4, 20))],
    ("Deportes y fitness", "Yoga"): [("thickness_mm", lambda t: se.mm_of(t, 2, 30))],
    ("Impresión 3D", "Filamentos"): [("filament", se.filament_of)],
    ("Redes", None): [("wifi_std", se.wifi_std_of), ("ports", se.ports_of)],
    ("Mouse", None): [("dpi", se.dpi_of)],
    ("Componentes y accesorios de PC", "Memoria RAM"): [("ram_gb", lambda t: se.gb_of(t, 2, 256))],
    ("Componentes y accesorios de PC", "Webcams"): [("resolution", se.resolution_of)],
    ("Componentes y accesorios de PC", "Accesorios de monitor"): [("size_in", lambda t: se.inches_of(t, 13, 75))],
    ("Cámaras de seguridad", None): [("resolution", se.resolution_of)],
    ("Cámaras y fotografía", "Lentes"): [("focal_mm", se.focal_mm_of)],
    ("Iluminación", "Tiras LED"): [("length_m", lambda t: se.meters_of(t, 1, 50))],
    ("Iluminación", None): [("lumens", lambda t: se.lumens_of(t, 50, 50000))],
}


# "kind": el tipo de producto que decide la compra en las subcategorías
# donde ninguna cifra lo hace -- en Guitarras la pregunta es si es
# eléctrica o acústica, en Cerraduras cómo se abre, en Jaulas para qué
# animal. Una tabla por subcategoría, de lo específico (el accesorio, que
# casi siempre nombra al instrumento) a lo general. Solo se admiten
# tablas que en el catálogo cubren 35%+ y no dejan el 85% en un valor.
_TIPOS_CRUDOS = {
 ("Instrumentos musicales","Guitarras"): [("Cuerdas y accesorios", r"\bcuerdas?\b|\bpuas?\b|\bcapo\b|correa|afinador|cejilla|pastilla|\bfunda\b|\bcable\b|\bpedal\b|amplificador|\bstand\b|soporte"),("Bajo", r"\bbajo electrico\b|\bbajo\b.{0,15}cuerdas|\bbass\b"),("Eléctrica", r"electrica|\belectric\b"),("Clásica", r"clasica|criolla|nylon"),("Acústica", r"acustica|electroacustica"),("Ukelele", r"ukelele|ukulele"),("Otros de cuerda", r"banjo|mandolina|violin|\blaud\b|charango|\bviola\b|\barpa\b")],
 ("Instrumentos musicales","Viento"): [("Accesorios", r"\bboquilla|\bcanas?\b|lubricante|\bfunda\b|\bestuche\b|atril|\bcorrea\b|abrazadera|limpiador"),("Saxofón", r"saxofon|\bsaxo\b|\bsax\b"),("Trompeta", r"trompeta|corneta"),("Flauta", r"flauta"),("Clarinete", r"clarinete"),("Trombón", r"trombon"),("Armónica", r"armonica"),("Otros de viento", r"tuba|oboe|fagot|melodica|\bpianica\b")],
 ("Instrumentos musicales","Baterías"): [("Baquetas y accesorios", r"baquetas?|\bparche|\bfunda\b|\bbanco\b|\bpedal\b|\batril\b|llave de afinacion|\bsoporte\b|\bherraje|\bstand\b"),("Electrónica", r"electronica|\bpads?\b|\bmodulo\b|\bmesh\b"),("Platillos", r"platillo|\bhi ?hat\b|\bcrash\b|\bride\b|\bsplash\b"),("Cajón y percusión", r"\bcajon\b|bongo|conga|\bdjembe\b|pandereta|\btimbal|\bcabasa\b|\bmaracas\b"),("Acústica", r"acustica|\bbateria\b")],
 ("Instrumentos musicales","Cuerdas"): [("Guitarra acústica", r"acustica|folk|\bnylon\b|clasica"),("Guitarra eléctrica", r"electrica"),("Bajo", r"\bbajo\b|\bbass\b"),("Violín y similares", r"violin|\bviola\b|cello|violonchelo|contrabajo"),("Ukelele", r"ukelele|ukulele"),("Otros", r"banjo|mandolina|\barpa\b|charango")],
 ("Instrumentos musicales","Percusión"): [("Accesorios", r"baquetas?|\bfunda\b|\bsoporte\b|\batril\b|\bparche"),("Cajón", r"\bcajon\b"),("Congas y bongós", r"conga|bongo|\btimbal"),("Djembé y étnica", r"djembe|\bdarbuka\b|\bhandpan\b|\btambor\b"),("Pandereta y menor", r"pandereta|\bmaracas\b|\bcabasa\b|\bclaves\b|\bguiro\b|triangulo|\bcascabel"),("Xilófono y metalófono", r"xilofono|metalofono|glockenspiel|\bmarimba\b")],
 ("Domótica y hogar inteligente","Cerraduras inteligentes"): [("Huella dactilar", r"huella"),("Reconocimiento facial", r"facial|reconocimiento de rostro"),("Con teclado", r"teclado|contrasena|codigo|\bpin\b|keypad"),("Con tarjeta", r"tarjeta|\brfid\b"),("Por aplicación", r"\bapp\b|aplicacion|\bwifi\b|bluetooth|tuya|\bremot")],
 ("Domótica y hogar inteligente","Interruptores inteligentes"): [("Wi-Fi", r"\bwifi\b|wi-?fi"),("Zigbee o Matter", r"zigbee|\bmatter\b|\bthread\b"),("Con control remoto", r"control remoto|inalambric|\brf\b|433"),("Táctil", r"tactil|\btouch\b")],
 ("Mascotas","Jaulas y corrales"): [("Para perro", r"\bperro|\bcanin|\bcachorro"),("Para gato", r"\bgato|\bgatito|\bfelin"),("Para aves", r"\bave|\bpajaro|\bloro|periquito|canario"),("Para roedores", r"hamster|conejo|cuyo|\bcobayo|\bhuron|chinchilla"),("Para reptiles", r"reptil|tortuga|iguana|terrario")],
 ("Mascotas","Comederos"): [("Para perro", r"\bperro|\bcanin|\bcachorro"),("Para gato", r"\bgato|\bgatito|\bfelin"),("Para aves", r"\bave|\bpajaro|\bloro|periquito|canario|colibri"),("Para roedores", r"hamster|conejo|cuyo|\bcobayo|\bhuron")],
 ("Mascotas","Camas"): [("Para perro", r"\bperro|\bcanin|\bcachorro"),("Para gato", r"\bgato|\bgatito|\bfelin"),("Para roedores", r"hamster|conejo|\bhuron")],
 ("Mascotas","Casas para mascotas"): [("Para perro", r"\bperro|\bcanin|\bcachorro|caseta"),("Para gato", r"\bgato|\bgatito|\bfelin|rascador"),("Para aves", r"\bave|\bpajaro|\bloro"),("Para roedores", r"hamster|conejo|\bhuron|chinchilla")],
 ("Mascotas","Juguetes"): [("Para perro", r"\bperro|\bcanin|\bcachorro|mordedor"),("Para gato", r"\bgato|\bgatito|\bfelin|rascador|catnip"),("Para aves", r"\bave|\bpajaro|\bloro"),("Para roedores", r"hamster|conejo|\bhuron|rueda de ejercicio")],
 ("Mascotas","Puertas para mascotas"): [("Para perro", r"\bperro|\bcanin|\bcachorro"),("Para gato", r"\bgato|\bgatito|\bfelin"),("Con microchip o sensor", r"microchip|sensor|intelig|\bchip\b")],
 ("Autos, bicicletas y motos","Bicicletas"): [("Accesorios", r"\bsillin|\bmanillar|\bpedal|\bcadena|\bcasco\b|\bcandado\b|\bbomba\b|portabici|guardabarro|\bcanasti|\bhorquilla|\bllanta|\bcamara\b|\bfreno|\bpinon|\bcuadro\b|\brayos?\b|velocimetro"),("Eléctrica", r"electrica|\be-?bike\b"),("Montaña", r"montana|\bmtb\b|todo terreno"),("Infantil", r"infantil|\bnino|\bnina|rodada 1[268]|rodada 20|\btriciclo"),("Ruta o urbana", r"\bruta\b|carretera|\bgravel\b|\bfixie\b|urbana|\bcity\b|plegable"),("Fija", r"\bfija\b|estatica|spinning")],
 ("Autos, bicicletas y motos","Baterías para auto"): [("Para auto", r"\bauto\b|\bcoche\b|\bcarro\b|automovil|camioneta"),("Para moto", r"\bmoto\b|motocicleta"),("Cargador o accesorio", r"cargador|mantenedor|arrancador|cables? pasa|\bpinzas\b")],
 ("Deportes y fitness","Equipo de gimnasio"): [("Accesorios", r"\bguantes\b|\bcinturon\b|\bcuerda\b|\bbanda|\bcorrea\b|\bagarre|\bmuneque|\brodiller"),("Banco y soportes", r"\bbanco\b|\bsoporte\b|\brack\b|\btorre\b|\bestante"),("Máquinas", r"\bmaquina\b|\bmultigimnasio\b|\bpolea\b|\bprensa\b|\bremo\b|\beliptica\b|\bcaminadora\b|\bescaladora\b"),("Peso libre", r"\bmancuerna|\bbarra\b|\bdisco|\bpesas?\b|kettlebell"),("Calistenia", r"\bdominadas\b|\bparalelas\b|\bbarra fija\b|\banillas\b|\bfondos\b|\babdominal")],
 ("Deportes y fitness","Yoga"): [("Tapetes", r"\btapete|colchoneta|\bmat\b"),("Bloques y cinturones", r"\bbloque|\bladrillo|\bcinturon|\bcorrea\b|\bstrap\b"),("Ruedas y rodillos", r"\brueda\b|\brodillo\b|\bfoam\b"),("Hamacas y columpios", r"\bhamaca\b|\bcolumpio\b|aereo"),("Pelotas", r"\bpelota|\bbalon\b|\bfitball\b")],
 ("Deportes y fitness","Boxeo"): [("Guantes", r"\bguantes?\b"),("Costales y soportes", r"\bcostal|\bsaco\b|\bpera\b|\bsoporte\b|\bbase\b"),("Protecciones", r"\bcareta\b|\bcasco\b|\bbucal\b|\bespinillera|\bconchilla|\bpeto\b|\bvendas?\b"),("Manoplas y paos", r"\bmanopla|\bpao\b|\bfocos?\b|\bmitts\b")],
 ("Belleza y cuidado personal","Rasuradoras"): [("Para barba", r"\bbarba\b|\brostro\b|facial|\bpatilla"),("Para cabello", r"\bcabello\b|\bpelo\b|\bcorte\b|\bmaquina de cortar\b|\bclipper\b"),("Corporal o depilación", r"\bcorporal\b|\bcuerpo\b|\bdepila|\bingle\b|\bpiernas\b|\baxila"),("Repuestos y accesorios", r"\brepuesto|\bcuchilla|\bcabezal|\bpeine\b|\baceite\b|\bcargador\b")],
 ("Otros","Soportes para dispositivos"): [("Para celular", r"celular|telefono|smartphone|\bmovil\b"),("Para tablet", r"tablet|tableta|\bipad\b"),("Para laptop", r"laptop|portatil|notebook|macbook"),("Para monitor o TV", r"monitor|\btv\b|television|pantalla"),("Para auto", r"\bauto\b|\bcoche\b|\bcarro\b|\brejilla\b|\bparabrisas\b|\bsalpicadero\b")],
 ("Teclados","Mecánicos"): [("Con cable", r"\bcable\b|alambric|\busb\b(?!.*inalambric)"),("Inalámbrico", r"inalambric|bluetooth|\b2\.4 ?g\b|\bwireless\b"),("Teclado numérico o compacto", r"\b60%|\b65%|\b75%|\btkl\b|compacto|numerico|\bnumpad\b"),("Accesorios", r"\bkeycaps?\b|\bswitch|\bteclas\b|\bmunequera\b|\blubricante\b|\bcable coiled\b")],
 ("Iluminación","Lámparas de techo"): [("Colgante", r"colgante|\bpendant\b|\bcolgantes\b"),("Plafón", r"\bplafon|\bplafones\b|\bempotra|\bsobreponer\b"),("Candil o araña", r"\bcandil|\barana\b|chandelier"),("Riel o track", r"\briel\b|\btrack\b|\bspot\b")],
 ("Equipo comercial","Punto de venta"): [("Terminal o caja registradora", r"terminal|caja registradora|\btpv\b|\bpos\b"),("Impresora de tickets", r"impresora|miniprinter|\btickets?\b|\brecibos?\b"),("Lector de códigos", r"lector|escaner|codigo de barras|\bscanner\b"),("Cajón de dinero", r"\bcajon\b|portamonedas|\befectivo\b"),("Consumibles", r"\brollos?\b|papel termico|\bcinta\b|\betiquetas\b")],
 ("Equipo comercial","Carros de servicio"): [("De acero inoxidable", r"acero inoxidable|\binox\b"),("De plástico", r"\bplastico\b|\bpolimero\b|\bresina\b"),("De madera", r"\bmadera\b|\bbambu\b"),("De metal o alambre", r"\bmetal\b|\balambre\b|\bhierro\b|\bacero\b")],
 ("Belleza y cuidado personal","Faciales"): [("Limpieza", r"limpiador|\bjabon\b|\bgel\b|\bespuma\b|desmaquill|\btonico\b|\bagua micelar\b"),("Hidratación", r"crema|hidratant|\bserum\b|\bgotas\b|\baceite\b|\bbalsamo\b"),("Mascarillas", r"mascarilla|\bparches?\b|\bpatch\b"),("Aparatos", r"\bmasajeador\b|\bcepillo\b|\bdispositivo\b|\blimpiadora\b|\bmicrocorriente\b|\bled\b"),("Protector solar", r"protector solar|\bspf\b|\bfps\b|bloqueador")],
 ("Belleza y cuidado personal","Corporales"): [("Cremas y lociones", r"crema|locion|hidratant|\bmanteca\b|\bbalsamo\b"),("Exfoliantes", r"exfoliant|\bscrub\b|\bsal\b"),("Jabones y geles", r"\bjabon\b|\bgel de bano\b|\bshower\b|\bespuma\b"),("Aceites", r"\baceite\b|\boleo\b"),("Aparatos", r"\bmasajeador\b|\bcepillo\b|\bdispositivo\b")],
 ("Autos, bicicletas y motos","Accesorios para bicicleta"): [("Luces y seguridad", r"\bluz\b|\bluces\b|\bcandado\b|\bcasco\b|\btimbre\b|\breflej"),("Transporte y carga", r"portabici|\bcanasti|\balforja|\bparrilla\b|\bremolque\b"),("Herramienta y mantenimiento", r"\bbomba\b|\bherramienta|\bmultiusos\b|\blubricante\b|\bparche"),("Comodidad", r"\bsillin|\bpuno|\bguantes\b|\basiento\b|\bfunda\b"),("Computadoras y soportes", r"velocimetro|ciclocomputadora|\bsoporte\b|\bporta ?celular\b")],
 ("Autos, bicicletas y motos","Accesorios y refacciones"): [("Interior", r"\btapete|\bfunda\b|\bvolante\b|\basiento\b|\borganizador\b|\bcubre"),("Exterior", r"\bespejo|\bfaro|\bparrilla\b|\bcubierta\b|\bloderas?\b|\bemblema\b|\bmolduras?\b"),("Mecánica", r"\bfiltro\b|\baceite\b|\bbalata|\bbujia|\bamortiguador|\bbanda\b|\bbomba\b"),("Herramienta y emergencia", r"\bgato\b|\bllave de cruz\b|\bcables? pasa|\bextintor\b|\btriangulo\b|\bcompresor\b"),("Audio y electrónica", r"\bcamara\b|\bdash ?cam\b|\bsensor\b|\balarma\b|\bantena\b|\bcargador\b")],
}

TIPOS = {k: [(et, re.compile(rx)) for et, rx in v] for k, v in _TIPOS_CRUDOS.items()}


# Campos que en esa subcategoría dicen otra cosa: el "material" de un
# colchón es el de su box de madera.
NO_GENERALES = {("Muebles", "Colchones"): {"material"}}


def _generales(product, name, spec_map, f):
    cat, sub = product.get("category"), product.get("subcategory")
    fuera = NO_GENERALES.get((cat, sub), ())
    for regla in SPEC_GENERALES:
        etiqueta, campo, fn = regla[:3]
        if campo in f or campo in fuera:
            continue
        if len(regla) > 3 and cat not in regla[3]:
            continue
        val = spec_map.get(etiqueta)
        if not val:
            continue
        try:
            v = fn(val)
        except (ValueError, AttributeError):
            v = None
        if v is not None:
            f[campo] = v
    reglas = NOMBRE_GENERALES.get((cat, sub), []) + NOMBRE_GENERALES.get((cat, None), [])
    for campo, fn in reglas:
        if campo in f or campo in fuera:
            continue
        v = fn(name)
        if v is not None:
            f[campo] = v
    tabla = TIPOS.get((cat, sub))
    if tabla and "kind" not in f:
        v = se.kind_of(name, tabla)
        if v is not None:
            f["kind"] = v


def facets_for(product):
    """Los facets propios de la categoría (abajo) y, encima, los genéricos
    que cualquier categoría puede tener. Ninguno de los dos pisa al otro."""
    f = _facets_propias(product) or {}
    _generales(product, product.get("name", ""), _spec_map(product), f)
    return f or None


def _facets_propias(product):
    category = product.get("category")
    if category not in FACET_CATEGORIES:
        return None
    name = product.get("name", "")
    brand = product.get("brand")
    spec_map = _spec_map(product)

    f = {}
    # Los campos que la tienda declara tal cual se copian ANTES de las ramas
    # propias de cada categoría: varias de ellas devuelven ahí mismo (Muebles
    # es una), así que si esto fuera más abajo no llegaría nunca.
    _spec_directa(product, spec_map, f)
    _hogar_facets(product, name, spec_map, f)

    if category in ("Proyectores y accesorios", "Aspiradoras", "Cafeteras",
                    "Audífonos", "Impresoras"):
        return f or None

    if category == "Monitores":
        # Los monitores no tienen RAM/almacenamiento/tipo de almacenamiento
        # que filtrar, y el tamaño de pantalla sigue una convención de
        # nombre distinta a la de celulares/laptops/tabletas (número
        # SUELTO justo después de "Monitor", ver monitor_screen_in) -- de
        # ahí que este bloque no reuse _screen_in()/_SCREEN_RANGE.
        screen = se.monitor_screen_in(name)
        if screen is not None:
            f["screen_in"] = screen
        refresh = se.refresh_hz(name)
        if refresh:
            f["refresh_hz"] = refresh
        resolution = se.resolution_of(name)
        if resolution:
            f["resolution"] = resolution
        panel = se.panel_type(name)
        if panel:
            f["panel_type"] = panel
        if se.is_curved(name):
            f["curved"] = True
        return f or None

    if category in ("Blancos y ropa de cama", "Muebles"):
        # La medida de cama es el dato que decide la compra en colchones,
        # bases y ropa de cama, y el único que se puede leer del nombre con
        # confianza en estas dos categorías. En el resto de Muebles
        # (escritorios, libreros...) simplemente no aparece y el producto
        # queda sin facet, como corresponde.
        medida = None
        for lbl in ("tamano de colchon", "tamano"):
            if lbl in spec_map:
                medida = se.bed_size_of(spec_map[lbl])
                if medida:
                    break
        if not medida:
            medida = se.bed_size_of(name)
        if medida:
            f["bed_size"] = medida
        return f or None

    if category == "Televisores":
        # Los televisores no comparten casi nada con celulares/laptops: lo
        # que importa es cuántas pulgadas y qué resolución. El tamaño usa su
        # propio extractor porque el rango es otro (24"-110") y la
        # convención del nombre también ("Pantalla 55 Pulgadas ...").
        screen = se.tv_screen_in(name)
        if screen is not None:
            f["screen_in"] = screen
        resolution = se.resolution_of(name)
        if resolution:
            f["resolution"] = resolution
        return f or None

    if category == "Videojuegos":
        plataforma = se.platform_of(name)
        if plataforma:
            f["platform"] = plataforma
        return f or None

    if category == "Lavadoras":
        # La ficha técnica lo declara; el nombre hay que interpretarlo.
        kg = None
        for lbl in ("capacidad de carga lavadora (kg)", "capacidad de carga"):
            if lbl in spec_map:
                kg = se.wash_capacity_kg(spec_map[lbl])
                if kg is not None:
                    break
        if kg is None:
            kg = se.wash_capacity_kg(name)
        if kg is not None:
            f["wash_kg"] = kg
        return f or None

    if category == "Refrigeradores":
        ft3 = None
        if "capacidad en pies" in spec_map:
            ft3 = se.fridge_capacity_ft3(spec_map["capacidad en pies"] + " pies")
        if ft3 is None:
            ft3 = se.fridge_capacity_ft3(name)
        if ft3 is not None:
            f["fridge_ft3"] = ft3
        return f or None

    # Los campos que la tienda declara tal cual valen para cualquier
    # categoría de la tabla; se aplican antes de las ramas propias.
    _spec_directa(product, spec_map, f)

    # Categorías cuyas facetas salen ENTERAS de la ficha técnica: no tienen
    # nada que leerle al nombre, así que devuelven acá mismo en vez de caer
    # en la lógica de RAM/almacenamiento de más abajo.
    if category in ("Herramientas", "Bocinas", "Autos, bicicletas y motos",
                    "Electrodomésticos", "Joyería y bisutería"):
        return f or None

    if category == "Refacciones":
        # Con qué moto/coche es compatible y de qué años. Solo del formato
        # con viñeta de la ficha de Elektra; ver compat_of() para por qué el
        # resto no se toca.
        compat = spec_map.get("compatibilidad")
        if compat:
            modelos, anios = se.compat_of(compat)
            modelos = [_COMPAT_CANON.get(_compat_key(m), m) for m in modelos]
            if modelos:
                f["compat_model"] = sorted(set(modelos))
            if anios:
                f["compat_year"] = anios
        return f or None

    if category == "Cargadores y adaptadores":
        # El tipo ya es la subcategoría (ver classify_cargadores.py); acá
        # solo la potencia, que es lo otro que decide: 20 W cargan un
        # teléfono y 65 W una laptop.
        w = se.charger_watts(name)
        if w is not None:
            f["charger_w"] = w
        return f or None

    if category == "Almacenamiento":
        # La capacidad ES la compra acá. El tipo (SSD, disco duro, USB,
        # microSD) se lee del nombre con el mismo extractor que ya usan
        # laptops y tabletas.
        cap = se.drive_capacity_gb(name)
        if cap is not None:
            f["drive_gb"] = cap
        tipo = se.storage_type_of(name)
        if tipo:
            f["storage_type"] = tipo
        return f or None

    if category == "Climatización":
        # Dos subcategorías con un dato legible y ninguna relación entre
        # sí: el minisplit se compra por BTU y el ventilador por pulgadas
        # de aspa. El resto (purificadores, humidificadores) no dice nada
        # comparable en el nombre y se queda sin facet.
        sub = product.get("subcategory")
        if sub == "Aires acondicionados":
            btu = se.ac_btu(name)
            if btu is not None:
                f["ac_btu"] = btu
        elif sub == "Ventiladores":
            pulg = se.fan_size_in(name)
            if pulg is not None:
                f["fan_in"] = pulg
        return f or None

    ram, storage = _ram_storage(category, name, spec_map)
    ram = _in_range(ram, _RAM_RANGE, category)
    storage = _in_range(storage, _STORAGE_RANGE, category)
    if ram is not None:
        f["ram_gb"] = ram
    if storage is not None:
        f["storage_gb"] = storage
    storage_type = se.storage_type_of(name)
    if storage_type:
        f["storage_type"] = storage_type
    if category != "Computadoras de escritorio":
        screen = _screen_in(category, name, spec_map)
        if screen is not None:
            f["screen_in"] = screen
    # Una torre no tiene frecuencia de actualización: los dos aciertos que
    # daba acá venían de paquetes que incluyen monitor, y el dato quedaba
    # colgado del gabinete.
    if category != "Computadoras de escritorio":
        refresh = se.refresh_hz(name)
        if refresh:
            f["refresh_hz"] = refresh

    if category in ("Celulares", "Tabletas"):
        net = _network(spec_map, name)
        if net:
            f["network_gen"] = net
        chip = _chipset(category, name, spec_map, brand)
        if chip:
            f["chipset_family"] = chip
        cam = _camera(spec_map, name)
        if cam:
            f["camera_mp"] = cam
        batt = None
        if "capacidad de bateria (mah)" in spec_map:
            batt = se.battery_mah(spec_map["capacidad de bateria (mah)"] + " mAh")
        if batt is None:
            batt = se.battery_mah(name)
        if batt:
            f["battery_mah"] = batt

    if category == "Celulares":
        # Solo celulares: "iPhone 15"/"Galaxy S24"/"Redmi Note 14 Pro" le
        # dice al comprador mucho más que el chip que trae adentro. No se
        # extiende a Tabletas -- el nombre de línea de iPad/Galaxy Tab/
        # Redmi Pad sigue un patrón totalmente distinto al de sus
        # celulares homónimos, y model_name() asume la convención de
        # nombres de teléfono de cada marca.
        model = se.model_name(name, brand)
        if model:
            f["model_name"] = model

    # El procesador, la gráfica y el sistema operativo se leen igual en una
    # torre que en una laptop: son las mismas familias de piezas y los
    # mismos nombres comerciales.
    if category in ("Laptops", "Computadoras de escritorio"):
        cpu = _cpu(name, spec_map, brand)
        if cpu:
            f["cpu_family"] = cpu
        gpu = se.gpu_of(name)
        if gpu:
            f["gpu"] = gpu
        # La ficha técnica lo declara en el 66% de las laptops; del nombre
        # se leía en el 36%.
        os_ = se.os_of(spec_map.get("sistema operativo") or "") or se.os_of(name)
        if os_:
            f["os"] = os_

    return f or None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cat = load_catalog()
    products = cat["products"]

    n = build_compat_canon(products)
    if n:
        print(f"Modelos compatibles distintos en Refacciones: {n}")

    per_field = Counter()
    per_cat_total = Counter()
    changed = 0
    for p in products:
        f = facets_for(p)
        per_cat_total[p["category"]] += 1
        if f is None:
            # Sin facets ahora: los que tuviera son de otra categoría o de
            # una ficha que ya no dice eso, y se sueltan.
            if p.get("facets"):
                changed += 1
                if not args.dry_run:
                    del p["facets"]
            continue
        for k in f:
            per_field[(p["category"], k)] += 1
        if p.get("facets") != f:
            changed += 1
        if not args.dry_run:
            p["facets"] = f

    print("Cobertura por campo:")
    for cat_name in sorted(per_cat_total):
        total = per_cat_total[cat_name]
        print(f"  {cat_name} (n={total}):")
        for (c, k), n in sorted(per_field.items()):
            if c == cat_name:
                print(f"    {k}: {n} ({100*n/total:.0f}%)")
    print(f"\nproductos con al menos 1 facet nuevo/cambiado: {changed}")

    if args.dry_run:
        print("\n(dry-run, no se guardó nada)")
        return

    save_catalog(cat)
    print("\nGuardado.")


if __name__ == "__main__":
    main()
