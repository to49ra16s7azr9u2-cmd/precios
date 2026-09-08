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
# Categorías con facets calculados. Es la misma lista que decide dónde se
# muestra el bloque "Compara calidad" del sitio (SPECS_BANNER_CATEGORIES en
# js/app.js): una categoría entra acá cuando de sus nombres se puede sacar
# un atributo REAL, no cuando nos gustaría tenerlo.
FACET_CATEGORIES = (
    "Celulares", "Laptops", "Tabletas", "Monitores",
    "Televisores", "Videojuegos", "Lavadoras", "Refrigeradores",
    "Blancos y ropa de cama", "Muebles",
    "Computadoras de escritorio", "Almacenamiento", "Climatización",
    "Refacciones", "Herramientas", "Bocinas",
    "Autos, bicicletas y motos", "Electrodomésticos", "Joyería y bisutería",
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
    ("Electrodomésticos", "Estufas y hornos", "emplea", "fuel"),
    ("Joyería y bisutería", "Relojes", "genero", "gender", "_gender"),
    ("Videojuegos", "Software", "clasificacion", "age_rating", "_age"),
    ("Electrodomésticos", "Estufas y hornos", "numero de quemadores", "burners", "_burners"),
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


def facets_for(product):
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
        if f is None:
            if p.get("category") in FACET_CATEGORIES:
                per_cat_total[p["category"]] += 1
            continue
        per_cat_total[p["category"]] += 1
        for k in f:
            per_field[(p["category"], k)] += 1
        if p.get("facets") != f:
            changed += 1
        if not args.dry_run:
            p["facets"] = f

    print("Cobertura por campo:")
    for cat_name in FACET_CATEGORIES:
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
