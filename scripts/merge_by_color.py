#!/usr/bin/env python3
"""Junta en UNA ficha los productos que son el mismo equipo en otro color.

EL PROBLEMA
-----------
La lista mostraba el mismo teléfono cinco veces seguidas:

    iPhone 17 256GB Libre Blanco     $19,999
    iPhone 17 256GB Negro Medianoche $17,099
    iPhone 17 256GB Libre Azul       ...
    iPhone 17 256GB Libre Lavanda    ...
    iPhone 17 256GB Libre Verde      ...

Son el mismo producto. Quien busca un iPhone 17 de 256 GB quiere ver UNA
ficha con el precio más bajo y elegir el color adentro, no cinco fichas
que compiten entre sí y esconden cuál es realmente el más barato.

QUÉ SE CONSIDERA "EL MISMO EQUIPO"
----------------------------------
La firma estructurada de phone_signature.py SIN el color: marca, modelo,
almacenamiento, RAM, compañía, regalo, condición, eSIM y red tienen que
coincidir. O sea que NO se juntan (y está bien que no):

    - un 256 GB con un 512 GB
    - un nuevo con un reacondicionado
    - un "sólo eSIM" con uno de SIM física  <- pedido expreso del usuario
    - un Telcel con uno libre
    - uno con audífonos de regalo con uno sin regalo

Si a una ficha le falta el modelo, la capacidad o el color, la firma queda
incompleta y esa ficha no se junta con nadie.

CÓMO QUEDA LA FICHA
-------------------
Cada color pasa a ser una entrada de `colorVariants` CON SUS PROPIAS
OFERTAS, así que un color de Elektra y otro de Mercado Libre conviven sin
que uno herede la tienda del otro:

    colorVariants: [
      {"color": "Azul marino", "offers": [ ...ofertas de ese color... ]},
      {"color": "Blanco",      "offers": [ ... ]},
    ]

El nombre del color es el COMPLETO ("Azul marino", "Azul hielo"), no el
color base: el Galaxy S25 FE tiene dos azules distintos y en la lista de
variantes tienen que poder distinguirse.

Sobrevive la ficha de id más bajo (la más vieja, la que probablemente ya
esté indexada), igual que en merge_cross_store.py y merge_by_signature.py.
product.offers queda con las ofertas de la variante más barata, para que
cualquier lector viejo que mire product.offers directamente siga viendo un
precio razonable.

USO
---
    python3 scripts/merge_by_color.py --dry-run
    python3 scripts/merge_by_color.py
"""
import argparse
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog  # noqa: E402
from phone_signature import color_full_of, signature  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Por ahora solo Celulares: phone_signature.py está construido y probado
# para teléfonos (capacidad, RAM, compañía, eSIM). Aplicarlo a un sillón o
# a una licuadora leería "modelo" donde no hay.
CATEGORIES = ("Celulares",)


def id_num(product):
    m = re.match(r"p(\d+)$", product.get("id", ""))
    return int(m.group(1)) if m else 10**9


def color_parts(product):
    """(color base, apellidos) del nombre, o (None, ()) si no dice color."""
    base, quals = color_full_of(product.get("name", ""))
    if not base:
        return None, ()
    # Los apellidos que YA están dentro del color base sobran: color_of
    # devuelve "titanio del desierto" como base y ("desierto", "titanio")
    # como apellidos, y concatenarlos daba "Titanio del desierto desierto
    # titanio".
    limpios = tuple(q for q in (quals or ()) if q not in base)
    return base, limpios


def color_label(product):
    """Nombre para mostrar del color ("Azul marino"), no solo el base."""
    base, quals = color_parts(product)
    if not base:
        return None
    etiqueta = base if not quals else f"{base} {' '.join(quals)}"
    return etiqueta[:1].upper() + etiqueta[1:]


def collapse_labels(labels):
    """etiqueta cruda -> etiqueta canónica, colapsando las formas de escribir
    el MISMO color.

    Trabaja sobre las ETIQUETAS y no sobre los productos porque las fichas
    ya fusionadas por color traen sus variantes con el nombre escrito por
    Mercado Libre ("Naranja", "Naranja cósmico", "Naranja cósmico titanio"),
    y ahí no hay producto al que preguntarle.
    """
    por_base = defaultdict(list)
    sueltas = {}
    for raw in labels:
        base, quals = color_full_of(raw)
        if not base:
            sueltas[raw] = raw
            continue
        limpios = tuple(q for q in (quals or ()) if q not in base)
        por_base[base].append((raw, limpios))
    out = dict(sueltas)
    for base, miembros in por_base.items():
        # Se agrupa por INCLUSIÓN, no por igualdad: "Naranja", "Naranja
        # cósmico" y "Naranja cósmico titanio" son apellidos anidados -- la
        # misma pintura descrita con más o menos detalle -- y el iPhone 17
        # Pro tiene un solo naranja. En cambio "Azul marino" y "Azul hielo"
        # son conjuntos DISJUNTOS: dos azules reales del Galaxy S25 FE, y
        # esos sí se quedan separados.
        cadenas = []  # cada cadena: [(raw, quals), ...] compatibles entre sí
        # De MÁS específico a menos: así las cadenas de cada acabado real se
        # forman primero y el nombre pelado llega al final, cuando ya puede
        # ver que encaja en dos y quedarse aparte. Al revés, el pelado creaba
        # la primera cadena y se llevaba puesto al primer acabado que
        # apareciera ("Azul" terminaba etiquetado "Azul marino").
        for raw, quals in sorted(miembros, key=lambda m: -len(m[1])):
            compatibles = [c for c in cadenas
                           if all(set(q) <= set(quals) or set(quals) <= set(q) for _, q in c)]
            # Compatible con DOS cadenas a la vez = ambiguo: un "Azul" pelado
            # cuando el equipo tiene "Azul marino" y "Azul hielo" no dice
            # cuál de los dos es, así que se queda como su propia variante en
            # vez de meterlo en una a dedo.
            if len(compatibles) == 1:
                compatibles[0].append((raw, quals))
            else:
                cadenas.append([(raw, quals)])
        for cadena in cadenas:
            mejor = max((r for r, _ in cadena), key=len)
            for raw, _ in cadena:
                out[raw] = mejor
    return out


def collapse_colors(productos):
    """id de producto -> etiqueta de color, colapsando las formas de escribir
    el MISMO color.

    Dentro de un grupo, "Naranja" y "Naranja cósmico" son el mismo color del
    iPhone 17 Pro escrito de dos formas: solo existe un naranja. Pero "Azul
    marino" y "Azul hielo" del Galaxy S25 FE son DOS azules reales. La regla
    es la misma que usa merge_by_signature.py: con un solo apellido para ese
    color base, el apellido no distingue nada y se colapsa; con dos o más,
    cada uno es su propia variante y el que viene sin apellido queda aparte
    porque no se sabe cuál es.
    """
    por_base = defaultdict(list)
    for p in productos:
        base, quals = color_parts(p)
        if base:
            por_base[base].append((p, quals))
    etiquetas = {}
    for base, miembros in por_base.items():
        con_apellido = {q for _, q in miembros if q}
        if len(con_apellido) <= 1:
            # Un solo apellido (o ninguno): todos son el mismo color. Se usa
            # la forma más descriptiva que haya aparecido.
            mejor = max((color_label(p) for p, _ in miembros), key=len)
            for p, _ in miembros:
                etiquetas[p["id"]] = mejor
        else:
            for p, _ in miembros:
                etiquetas[p["id"]] = color_label(p)
    return etiquetas


def variants_of(product, etiqueta=None):
    """Variantes de color de una ficha, ya en el formato nuevo.

    Una ficha que YA venía fusionada por color (colorVariants del formato
    viejo de Mercado Libre, con price/url/sellers sueltos en la variante)
    se convierte acá: cada una de esas variantes era, en los hechos, una
    oferta de Mercado Libre.
    """
    viejas = product.get("colorVariants") or []
    if viejas and not any("offers" in v for v in viejas):
        out = []
        for v in viejas:
            oferta = {"storeId": "mercadolibre", "price": v.get("price"), "url": v.get("url")}
            for campo in ("shippingFee", "sellerCount", "lowestPrice", "sellers", "photo"):
                if v.get(campo) is not None:
                    oferta[campo] = v[campo]
            out.append({"color": v.get("color") or etiqueta or color_label(product), "offers": [oferta]})
        return out
    if viejas:
        return viejas
    return [{"color": etiqueta or color_label(product), "offers": product.get("offers") or []}]


def variant_min_price(variant):
    precios = [o.get("price") for o in (variant.get("offers") or []) if o.get("price")]
    return min(precios) if precios else float("inf")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = load_catalog()
    grupos = defaultdict(list)
    for p in data["products"]:
        if p.get("category") not in CATEGORIES:
            continue
        sig = signature(p)
        if not sig:
            continue  # firma incompleta -> no se junta con nadie
        brand, model, storage, ram, _color, carrier, bundle, cond, esim, net = sig
        grupos[(brand, model, storage, ram, carrier, bundle, cond, esim, net)].append(p)

    fusionables = []
    for clave, ps in grupos.items():
        if len(ps) < 2:
            continue
        etiquetas = collapse_colors(ps)
        colores = set(etiquetas.values())
        # Dos fichas del mismo color no son "el mismo equipo en otro color":
        # eso es un duplicado y lo resuelve merge_by_signature.py.
        if len(colores) < 2:
            continue
        fusionables.append(sorted(ps, key=id_num))

    drop = set()
    resumen = []
    for ps in fusionables:
        principal = ps[0]
        etiquetas = collapse_colors(ps)
        crudas = []
        for p in ps:
            for v in variants_of(p, etiquetas.get(p["id"])):
                if v.get("color") and v.get("offers"):
                    crudas.append(v)
        canon = collapse_labels({v["color"] for v in crudas})
        variantes = []
        for v in crudas:
            etiqueta = canon.get(v["color"], v["color"])
            clave = etiqueta.lower()
            previa = next((x for x in variantes if x["color"].lower() == clave), None)
            if previa:
                # Mismo color repetido entre dos fichas: se suman las ofertas
                # en una sola variante en vez de listar el color dos veces.
                urls = {o.get("url") for o in previa["offers"]}
                previa["offers"].extend(o for o in v["offers"] if o.get("url") not in urls)
            else:
                variantes.append({"color": etiqueta, "offers": list(v["offers"])})
        for p in ps:
            if p is not principal:
                drop.add(p["id"])
                if not principal.get("photo") and p.get("photo"):
                    principal["photo"] = p["photo"]
                if not principal.get("specs") and p.get("specs"):
                    principal["specs"] = p["specs"]
        if len(variantes) < 2:
            continue
        variantes.sort(key=variant_min_price)
        principal["colorVariants"] = variantes
        # product.offers se queda con las de la variante más barata: es lo
        # que ve cualquier lector viejo que no sepa de colorVariants.
        principal["offers"] = list(variantes[0]["offers"])
        resumen.append((principal["id"], principal["name"], [v["color"] for v in variantes]))

    print(f"Grupos fusionables (mismo equipo, distinto color): {len(resumen)}")
    print(f"Fichas absorbidas: {len(drop)}")
    for pid, name, colores in resumen[:25]:
        print(f"   {pid:9} {name[:52]:52} <- {', '.join(colores)[:60]}")
    if len(resumen) > 25:
        print(f"   ... y {len(resumen) - 25} grupos más")

    if args.dry_run:
        print("\n(--dry-run: no se escribió nada)")
        return
    if not drop:
        print("\nNada que fusionar.")
        return
    data["products"] = [p for p in data["products"] if p["id"] not in drop]
    save_catalog(data)
    print(f"\nGuardado. Catálogo: {len(data['products'])} productos")

    removed = 0
    for pid in drop:
        path = os.path.join(ROOT, "producto", f"{pid}.html")
        if os.path.exists(path):
            os.remove(path)
            removed += 1
        d = os.path.join(ROOT, "producto", pid)
        if os.path.isdir(d):
            for f in os.listdir(d):
                os.remove(os.path.join(d, f))
            os.rmdir(d)
            removed += 1
    print(f"Páginas estáticas huérfanas eliminadas: {removed}")


if __name__ == "__main__":
    main()
