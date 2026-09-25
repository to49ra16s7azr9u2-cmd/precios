#!/usr/bin/env python3
"""Reorganización de categorías del 25-sep-2026.

POR QUÉ
-------
Con Walmart y Bodega Aurrerá el catálogo pasó de 470 mil a 1.1 millones de
fichas y la lista de categorías dejó de corresponder a lo que hay:
«Refacciones» eran 350 mil fichas y casi todas de auto; Calzado, Libros,
Ropa y Papelería existían pero vacías, y 270 mil fichas de Walmart/Bodega se
quedaban afuera por no tener dónde caer (zapatos, libros, autopartes, ropa,
bolsas, jardín, papelería). El usuario aprobó el plan completo:

  1. Autopartes, sacada de Refacciones (las refacciones de electrodomésticos
     pasan a Electrodomésticos).
  2. Calzado.       3. Libros.        4. Ropa y accesorios.
  5. Bolsas y mochilas, Jardín y exterior, Papelería y oficina.
  6. Subcategorías nuevas (cojines, tapetes, Funko, fiestas, disfraces,
     perfumes, alimento para mascotas...).
  7. Bebés, separada de «Juguetes y bebés» (que queda como Juguetes); Drones
     a Cámaras y fotografía; Movilidad eléctrica a Autos; Fitness (vacía)
     fuera.

QUÉ HAY ACÁ
-----------
- destino(cat, sub): adónde va HOY una (categoría, subcategoría) vieja. La
  aplican decidir() del clasificador y save_catalog() de data_io, así que
  cualquier camino de alta que todavía diga «Refacciones» o «Drones» termina
  en la categoría nueva.
- CATEGORIAS_NUEVAS: las categorías que se crean, con icono y subcategorías.
- SUBS_NUEVAS: subcategorías nuevas en categorías que ya existían.
- REDIRECCIONES: slug viejo de categoría -> slug nuevo, para 404.html.
- main(): con --aplicar actualiza data/data.json, mueve las fichas por
  destino() y pasa el candado manual (data/clasificacion-a-mano.json) a los
  nombres nuevos.

USO
---
    python3 scripts/reorganizar_categorias.py            # informe
    python3 scripts/reorganizar_categorias.py --aplicar
"""
import argparse
import collections
import io
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(AQUI)

AUTOPARTES = "Autopartes"
BEBES = "Bebés"
JUGUETES = "Juguetes"
BOLSAS = "Bolsas y mochilas"
JARDIN = "Jardín y exterior"

# Subcategorías de Refacciones que son de electrodomésticos: pasan a
# Electrodomésticos con el mismo nombre (y papel de «parte», ver
# roles_subcategorias.py). Todo lo demás de Refacciones es de auto, moto o
# movilidad eléctrica: Autopartes.
REFACCIONES_ELECTRO = {
    "Refacciones para lavadora y secadora", "Refacciones para refrigerador",
    "Refacciones para estufa y horno", "Refacciones para licuadora y batidora",
    "Refacciones para aspiradora y robot", "Refacciones para cafetera",
    "Refacciones para freidora de aire", "Refacciones para microondas",
    "Refacciones para aire acondicionado y ventilador",
    "Refacciones para plancha y vaporizador", "Refacciones para bocinas y audio",
    "Refacciones para otros electrodomésticos", "Refacciones para electrodomésticos",
}

# «Juguetes y bebés» se parte en dos. Lo de estas familias es de Bebés.
SUBS_BEBES = [
    "Carriolas", "Sillas de auto", "Portabebés y canguros", "Andaderas",
    "Alimentación y lactancia", "Biberones", "Chupones y mordederas",
    "Sillas de comer y mecedoras", "Pañales y cambio", "Baño e higiene del bebé",
    "Cuidado y salud del bebé", "Ropa y calzado de bebé", "Cunas", "Corrales",
    "Seguridad para bebé", "Monitores de bebé", "Juguetes para bebé",
]

DRONES_A = {"Accesorios": "Accesorios para drones"}          # el resto -> «Drones»
MOVILIDAD_A = {
    "Scooters para adultos": "Scooters eléctricos",
    "Scooters para niños": "Scooters eléctricos",
    "Bicicletas eléctricas plegables y urbanas": "Bicicletas eléctricas",
    "Bicicletas eléctricas de montaña": "Bicicletas eléctricas",
    "Hoverboards, patinetas y monociclos": "Hoverboards y patinetas eléctricas",
    "Accesorios": "Accesorios de movilidad eléctrica",
}
DECORACION_A_JARDIN = {"Asadores": "Asadores y parrillas", "Albercas y spa": "Albercas e inflables"}


def destino(cat, sub):
    """(cat, sub) de hoy para una (cat, sub) posiblemente vieja."""
    if cat == "Refacciones":
        if sub in REFACCIONES_ELECTRO:
            return "Electrodomésticos", sub
        return AUTOPARTES, sub
    if cat == "Juguetes y bebés":
        return (BEBES if sub in SUBS_BEBES else JUGUETES), sub
    if cat == "Drones":
        return "Cámaras y fotografía", DRONES_A.get(sub, "Drones")
    if cat == "Movilidad eléctrica":
        return "Autos, bicicletas y motos", MOVILIDAD_A.get(sub, "Accesorios de movilidad eléctrica")
    if cat == "Decoración de hogar y jardín" and sub in DECORACION_A_JARDIN:
        return JARDIN, DECORACION_A_JARDIN[sub]
    if cat == "Fitness":
        return "Deportes y fitness", None
    return cat, sub


# Categorías que se crean (id = nombre). Las de Refacciones/Juguetes heredan
# sus subcategorías al migrar; acá van las que no existían en ningún lado.
CATEGORIAS_NUEVAS = {
    AUTOPARTES: ("gear", []),
    BEBES: ("pillow", []),
    JUGUETES: ("toy", ["Funko y coleccionables", "Artículos para fiestas", "Disfraces"]),
    BOLSAS: ("bag", ["Mochilas", "Mochilas para laptop", "Bolsas para mujer", "Carteras y monederos",
                     "Cangureras y bolsos cruzados", "Cosmetiqueras y neceseres"]),
    JARDIN: ("leaf", ["Macetas y jardineras", "Plantas artificiales", "Riego y mangueras",
                      "Albercas e inflables", "Asadores y parrillas", "Sombrillas, toldos y carpas",
                      "Decoración de jardín"]),
}

# Subcategorías nuevas en categorías que ya existían.
SUBS_NUEVAS = {
    "Calzado": ["Tenis", "Tenis para niños", "Zapatos de vestir", "Zapatos casuales", "Botas",
                "Sandalias", "Pantuflas", "Calzado de seguridad"],
    "Ropa y accesorios": ["Blusas y tops", "Camisas", "Pantalones y jeans", "Shorts y bermudas",
                          "Chamarras y suéteres", "Sudaderas", "Gorras y sombreros", "Calcetines",
                          "Trajes de baño", "Paraguas", "Ropa de niños"],
    "Papelería y oficina": ["Arte y dibujo", "Papel y sobres", "Útiles escolares",
                            "Artículos de oficina", "Etiquetadoras y rotuladoras", "Embalaje",
                            "Libretas y agendas"],
    "Decoración de hogar y jardín": ["Cojines", "Tapetes y alfombras", "Relojes de pared",
                                     "Floreros y centros de mesa", "Portarretratos",
                                     "Vinil decorativo", "Navidad y temporada"],
    "Mascotas": ["Alimento para mascotas"],
    "Cámaras y fotografía": ["Drones", "Accesorios para drones"],
    "Autos, bicicletas y motos": ["Scooters eléctricos", "Bicicletas eléctricas",
                                  "Hoverboards y patinetas eléctricas",
                                  "Accesorios de movilidad eléctrica"],
    "Blancos y ropa de cama": ["Accesorios de baño"],
    "Joyería y bisutería": ["Lentes oftálmicos y de lectura"],
}

CATEGORIAS_QUE_SE_VAN = {"Refacciones", "Juguetes y bebés", "Drones", "Movilidad eléctrica", "Fitness"}

# slug de categoría viejo -> nuevo (404.html). Las subcategorías conservan
# su slug salvo en las que se fusionaron, que van a la raíz de la nueva.
REDIRECCIONES = {
    "refacciones": "autopartes",
    "juguetes-y-bebes": "juguetes",
    "drones": "camaras-y-fotografia",
    "movilidad-electrica": "autos-bicicletas-y-motos",
    "fitness": "deportes-y-fitness",
}


def _sub(nombre, icono):
    return {"id": nombre, "name": nombre, "icon": icono}


def reorganizar_manifiesto(manifest):
    """Aplica la reorganización a manifest['categories'] (en su lugar)."""
    cats = manifest["categories"]
    por_id = {c["id"]: c for c in cats}
    # 1. Categorías nuevas, al lado de la que las origina.
    orden = [c["id"] for c in cats]
    for cid, (icono, subs) in CATEGORIAS_NUEVAS.items():
        if cid not in por_id:
            c = {"id": cid, "name": cid, "icon": icono, "subcategories": []}
            por_id[cid] = c
            cats.append(c)
    # 2. Subcategorías que se mudan con sus fichas.
    for c in list(cats):
        if c["id"] not in CATEGORIAS_QUE_SE_VAN and c["id"] != "Decoración de hogar y jardín":
            continue
        for s in c.get("subcategories") or []:
            ncat, nsub = destino(c["id"], s["id"])
            if ncat == c["id"] or not nsub:
                continue
            dest = por_id[ncat]
            if not any(x["id"] == nsub for x in dest["subcategories"]):
                dest["subcategories"].append(_sub(nsub, dest.get("icon") or s.get("icon")))
    # 3. Subcategorías nuevas.
    for cid, (icono, subs) in CATEGORIAS_NUEVAS.items():
        for n in subs:
            if not any(x["id"] == n for x in por_id[cid]["subcategories"]):
                por_id[cid]["subcategories"].append(_sub(n, icono))
    for cid, subs in SUBS_NUEVAS.items():
        c = por_id[cid]
        for n in subs:
            if not any(x["id"] == n for x in c["subcategories"]):
                c["subcategories"].append(_sub(n, c.get("icon")))
    # 4. Decoración ya no lleva Asadores ni Albercas; fuera las categorías viejas.
    deco = por_id.get("Decoración de hogar y jardín")
    if deco:
        deco["subcategories"] = [s for s in deco["subcategories"] if s["id"] not in DECORACION_A_JARDIN]
    manifest["categories"] = [c for c in cats if c["id"] not in CATEGORIAS_QUE_SE_VAN]
    # Orden: cada nueva detrás de la que la origina, para que Inicio no las
    # tire al final.
    detras = {AUTOPARTES: "Autos, bicicletas y motos", JUGUETES: "Juegos de mesa", BEBES: JUGUETES,
              BOLSAS: "Viajes", JARDIN: "Decoración de hogar y jardín"}
    lista = [c for c in manifest["categories"] if c["id"] not in detras]
    for nueva, ancla in detras.items():
        c = por_id[nueva]
        ids = [x["id"] for x in lista]
        lista.insert(ids.index(ancla) + 1 if ancla in ids else len(lista), c)
    manifest["categories"] = lista


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()
    sys.path.insert(0, AQUI)
    from data_io import load_catalog, save_catalog

    data = load_catalog()
    movidas = collections.Counter()
    for p in data["products"]:
        cat, sub = p.get("category"), p.get("subcategory")
        ncat, nsub = destino(cat, sub)
        if (ncat, nsub) != (cat, sub):
            movidas[(cat, ncat)] += 1
            p["category"], p["subcategory"] = ncat, nsub
    for (a, b), n in movidas.most_common():
        print(f"  {n:8,}  {a} -> {b}")
    print(f"Fichas movidas: {sum(movidas.values()):,}")

    candado = os.path.join(ROOT, "data", "clasificacion-a-mano.json")
    cambios_candado = 0
    if os.path.exists(candado):
        with io.open(candado, encoding="utf-8") as f:
            lock = json.load(f)
        for pid, v in lock.items():
            if isinstance(v, dict) and v.get("category"):
                ncat, nsub = destino(v["category"], v.get("subcategory"))
                if (ncat, nsub) != (v["category"], v.get("subcategory")):
                    v["category"], v["subcategory"] = ncat, nsub
                    cambios_candado += 1
            elif isinstance(v, list) and len(v) >= 1:
                ncat, nsub = destino(v[0], v[1] if len(v) > 1 else None)
                if (ncat, nsub) != (v[0], v[1] if len(v) > 1 else None):
                    v[:2] = [ncat, nsub]
                    cambios_candado += 1
        print(f"Candado manual: {cambios_candado:,} entradas pasadas a los nombres nuevos")

    if not args.aplicar:
        print("(sin --aplicar: no se guardó nada)")
        return
    reorganizar_manifiesto(data)
    save_catalog(data)
    if os.path.exists(candado):
        with io.open(candado, "w", encoding="utf-8") as f:
            json.dump(lock, f, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    print("Guardado.")


if __name__ == "__main__":
    main()


# Familias (el escalón del medio, ver familias_subcategorias.py) de las
# categorías nuevas, y las que se suman a categorías que ya tenían.
FAMILIAS_NUEVAS = {
    AUTOPARTES: [
        ("Para auto", [
            "Para autos", "Frenos", "Carrocería, espejos y molduras", "Sistema eléctrico y sensores",
            "Faros y luces", "Motor y transmisión", "Filtros y aceites", "Suspensión y dirección", "Escape",
            "Bujías y encendido", "Motores", "Bombas", "Limpiaparabrisas", "Interior y tapicería",
            "Llaves y cerraduras de auto", "Enfriamiento y climatización"]),
        ("Para moto", [
            "Para motos", "Carenados, plásticos y tanques", "Luces de moto", "Manubrios, espejos y controles",
            "Eléctrico y baterías de moto", "Motor, carburación y escape de moto",
            "Asientos, parrillas y accesorios de moto", "Suspensión y dirección de moto", "Frenos de moto",
            "Cadenas, sprockets y transmisión", "Llantas y cámaras de moto", "Filtros y aceites de moto"]),
        ("Para movilidad eléctrica", ["Para patinetas eléctricas", "Para bicicletas eléctricas"]),
    ],
    BEBES: [
        ("Paseo y transporte", ["Carriolas", "Sillas de auto", "Portabebés y canguros", "Andaderas"]),
        ("Alimentación", ["Alimentación y lactancia", "Biberones", "Chupones y mordederas",
                          "Sillas de comer y mecedoras"]),
        ("Higiene y cuidado", ["Pañales y cambio", "Baño e higiene del bebé", "Cuidado y salud del bebé",
                               "Ropa y calzado de bebé"]),
        ("Dormir, seguridad y juego", ["Cunas", "Corrales", "Seguridad para bebé", "Monitores de bebé",
                                       "Juguetes para bebé"]),
    ],
    JUGUETES: [
        ("Juguetes", ["Muñecas", "Figuras de acción", "Peluches", "Bloques de construcción", "Maquetas",
                      "Juguetes educativos", "Juguetes musicales", "Vehículos de juguete",
                      "Vehículos a control remoto", "Juegos arcade"]),
        ("Al aire libre", ["Juguetes para exterior", "Trampolines", "Montables", "Triciclos"]),
        ("Coleccionables y fiestas", ["Funko y coleccionables", "Artículos para fiestas", "Disfraces"]),
    ],
    "Calzado": [
        ("Tenis", ["Tenis", "Tenis para niños"]),
        ("Zapatos", ["Zapatos de vestir", "Zapatos casuales", "Calzado de seguridad"]),
        ("Botas y sandalias", ["Botas", "Sandalias", "Pantuflas"]),
    ],
    "Ropa y accesorios": [
        ("Ropa", ["Playeras", "Blusas y tops", "Camisas", "Pantalones y jeans", "Shorts y bermudas", "Vestidos",
                  "Faldas", "Chamarras y suéteres", "Sudaderas", "Ropa deportiva", "Trajes de baño",
                  "Ropa de niños"]),
        ("Ropa interior y dormir", ["Ropa interior", "Pijamas", "Calcetines"]),
        ("Accesorios", ["Gorras y sombreros", "Paraguas"]),
    ],
    BOLSAS: [
        ("Mochilas", ["Mochilas", "Mochilas para laptop"]),
        ("Bolsas y carteras", ["Bolsas para mujer", "Carteras y monederos", "Cangureras y bolsos cruzados",
                               "Cosmetiqueras y neceseres"]),
    ],
    JARDIN: [
        ("Plantas y macetas", ["Macetas y jardineras", "Plantas artificiales", "Decoración de jardín"]),
        ("Riego y albercas", ["Riego y mangueras", "Albercas e inflables"]),
        ("Asadores y sombra", ["Asadores y parrillas", "Sombrillas, toldos y carpas"]),
    ],
    "Papelería y oficina": [
        ("Escolar", ["Cuadernos", "Útiles escolares", "Escritura", "Mochilas", "Calculadoras"]),
        ("Oficina", ["Artículos de oficina", "Organización", "Papel y sobres", "Libretas y agendas",
                     "Etiquetadoras y rotuladoras", "Embalaje", "Pizarrones"]),
        ("Arte", ["Arte y dibujo"]),
    ],
}
FAMILIAS_AGREGAR = {
    "Electrodomésticos": [("Refacciones", sorted(REFACCIONES_ELECTRO))],
    "Cámaras y fotografía": [("Drones", ["Drones", "Accesorios para drones"])],
    "Autos, bicicletas y motos": [("Movilidad eléctrica", ["Scooters eléctricos", "Bicicletas eléctricas",
                                                          "Hoverboards y patinetas eléctricas",
                                                          "Accesorios de movilidad eléctrica"])],
}
