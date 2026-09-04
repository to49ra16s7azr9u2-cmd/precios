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
}
_STORAGE_RANGE = {
    "Celulares": (4, 2048),    # 2TB ya es un buque insignia excepcional
    "Laptops": (4, 8192),      # 8TB cubre workstations reales (RAID/NVMe dobles)
    "Tabletas": (4, 2048),
}


def _in_range(val, ranges, category):
    if val is None:
        return None
    lo, hi = ranges[category]
    return val if lo <= val <= hi else None


def _screen_in(category, name, spec_map):
    val = None
    if "pantalla" in spec_map:
        val = se.screen_size_in(spec_map["pantalla"])
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
    ram = _gb_of(spec_map["memoria ram"]) if "memoria ram" in spec_map else None
    storage = None
    for lbl in ("almacenamiento", "capacidad"):
        if lbl in spec_map:
            storage = _gb_of(spec_map[lbl])
            break
    if ram is not None or storage is not None:
        if ram is None or storage is not None:
            # si falta uno de los dos, se completa con el nombre pero sin
            # pisar el que ya vino confirmado por specs[]
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


def facets_for(product):
    category = product.get("category")
    if category not in ("Celulares", "Laptops", "Tabletas"):
        return None
    name = product.get("name", "")
    brand = product.get("brand")
    spec_map = _spec_map(product)

    ram, storage = _ram_storage(category, name, spec_map)
    ram = _in_range(ram, _RAM_RANGE, category)
    storage = _in_range(storage, _STORAGE_RANGE, category)
    f = {}
    if ram is not None:
        f["ram_gb"] = ram
    if storage is not None:
        f["storage_gb"] = storage
    storage_type = se.storage_type_of(name)
    if storage_type:
        f["storage_type"] = storage_type
    screen = _screen_in(category, name, spec_map)
    if screen is not None:
        f["screen_in"] = screen
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
        batt = se.battery_mah(name)
        if batt:
            f["battery_mah"] = batt

    if category == "Laptops":
        cpu = _cpu(name, spec_map, brand)
        if cpu:
            f["cpu_family"] = cpu
        gpu = se.gpu_of(name)
        if gpu:
            f["gpu"] = gpu
        os_ = se.os_of(name)
        if os_:
            f["os"] = os_

    return f or None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cat = load_catalog()
    products = cat["products"]

    per_field = Counter()
    per_cat_total = Counter()
    changed = 0
    for p in products:
        f = facets_for(p)
        if f is None:
            if p.get("category") in ("Celulares", "Laptops", "Tabletas"):
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
    for cat_name in ("Celulares", "Laptops", "Tabletas"):
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
