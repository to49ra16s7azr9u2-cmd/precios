#!/usr/bin/env python3
"""Fusiona fichas de celular que son el MISMO equipo aunque el nombre esté
escrito distinto en cada tienda.

POR QUÉ HACE FALTA ADEMÁS DE merge_cross_store.py
--------------------------------------------------
merge_cross_store.py exige que el nombre normalizado sea IDÉNTICO. Entre
tiendas eso no pasa casi nunca:

    Mercado Libre  "Honor Magic 8 Lite 8gb Ram 256gb Dorado Dual Sim Dorado"
    Elektra        "MAGIC 8 LITE 256GB RAM 8GB COLOR DORADO"
    Elektra        "Honor Play10 3GB RAM 64GB ROM Morado Estelar"
    Amazon         "Honor Play10 Smartphone 64GB + 3GB Ram Morado Estelar"

Son el mismo teléfono y el sitio los mostraba como fichas sueltas, así que
no había comparación de precios -- justo lo contrario de para lo que existe
el sitio. El usuario lo reportó viendo 217 resultados de "honor" sin
consolidar y sin ver a Amazon en los equipos donde sí se había cargado.

CÓMO SE DECIDE QUE SON EL MISMO
-------------------------------
Por FIRMA ESTRUCTURADA (ver scripts/phone_signature.py), no por parecido
de texto: marca + línea/modelo + almacenamiento + RAM + color + compañía +
regalo concreto + condición + eSIM + red (4G/5G). Todos tienen que
coincidir.

Un atributo que el nombre NO declara NO se da por bueno: cuenta como valor
propio y separa el grupo. Por eso un "Galaxy A17 4G" nunca se fusiona con
un "Galaxy A17" a secas (existe también el A17 5G, que es otro equipo), ni
un iPhone "sólo eSIM" con el de SIM física, ni un "con Audífonos y Bocina"
con un "con Audífonos y Smartwatch". Si falta modelo, capacidad o color, la
ficha directamente no se fusiona con nadie.

QUÉ FICHA SOBREVIVE
-------------------
La de id más bajo (la más vieja, la que probablemente ya esté indexada),
igual que merge_cross_store.py. Se queda con TODAS las ofertas del grupo
(deduplicadas por url) y hereda foto/specs si le faltaban.

USO
---
    python3 scripts/merge_by_signature.py --dry-run
    python3 scripts/merge_by_signature.py
"""
import argparse
import os
import re
import shutil
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import id_num, load_catalog, save_catalog  # noqa: E402
from phone_signature import signature  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))




# El apellido del acabado ("Azul neblina", "Azul claro") es la parte del
# color que a veces distingue dos equipos y a veces es la misma cosa dicha
# de dos formas. Leyendo UN nombre no hay manera de saber cuál de los dos
# casos es; leyendo el CATÁLOGO ENTERO, sí:
#
#   iPhone 17, azul  -> el único apellido que aparece es "neblina" (y su
#                       traducción "Mist"). Si no hay un segundo azul, el
#                       "Azul" a secas de otra tienda no puede ser otro:
#                       es el mismo, escrito corto.
#   Galaxy S25 FE, azul -> aparecen "marino", "claro" y "oscuro". Con dos o
#                       más azules reales conviviendo, un "Azul" pelado es
#                       AMBIGUO: no se sabe cuál de ellos es, así que no se
#                       fusiona con ninguno.
#
# Se mira por (marca, modelo) y no por firma completa a propósito: la
# paleta la define el modelo, no la capacidad ni la compañía. Que el
# catálogo tenga el "Azul Claro" en 128 GB y el "Azul Marino" en 512 GB ya
# prueba que el modelo tiene dos azules.
def _palette(products):
    """(marca, modelo, color_base) -> conjunto de apellidos vistos."""
    pal = defaultdict(set)
    for p in products:
        if p.get("category") != "Celulares":
            continue
        sig = signature(p)
        if sig is None:
            continue
        brand, model, _, _, (base, quals), *_ = sig
        if quals:
            pal[(brand, model, base)].update(quals)
    return pal


def _tiendas(product):
    return {o.get("storeId") for o in (product.get("offers") or [])}


def _una_tienda_los_separa(miembros):
    """¿Alguna tienda vende dos del grupo con apellido de color distinto?

    El colapso del apellido de arriba supone que el "Azul" pelado y el
    "Azul Marino" son la misma cosa dicha corto y largo. Cuando los dos
    nombres salen de LA MISMA tienda eso no se sostiene: una tienda no
    publica el mismo equipo dos veces con dos nombres de color distintos,
    los publica porque son dos colores. Se vio en Elektra con un "SAMSUNG
    GALAXY S25 FE 512GB/8RAM AZUL MARINO + BUDS" y un "... AZUL + BUDS":
    el catálogo había perdido los otros azules del modelo (claro y oscuro,
    los que cita el comentario de arriba), así que quedaba un solo apellido
    y la regla los daba por el mismo equipo.
    """
    por_tienda = defaultdict(set)
    for producto, apellidos in miembros:
        for tienda in _tiendas(producto):
            por_tienda[tienda].add(apellidos)
    return any(len(vistos) > 1 for vistos in por_tienda.values())


def mergeable_groups(products):
    pal = _palette(products)
    groups = defaultdict(list)
    for p in products:
        if p.get("category") != "Celulares":
            continue
        sig = signature(p)
        if sig is None:
            continue  # firma incompleta -> no se fusiona con nadie
        brand, model, storage, ram, (base, quals), *rest = sig
        # Con UN solo apellido para ese color en todo el modelo, el apellido
        # no distingue nada: se normaliza a None para que "Azul neblina" y
        # "Azul" caigan en el mismo grupo. Con dos o más, se conserva tal
        # cual y cada uno se queda en su grupo -- incluido el "Azul" pelado,
        # que no se fusiona con ninguno porque no se sabe cuál es.
        apellidos = quals
        if len(pal.get((brand, model, base), ())) == 1:
            quals = None
        key = (brand, model, storage, ram, (base, quals), *rest)
        groups[key].append((p, apellidos))
    return [sorted((p for p, _ in ms), key=id_num)
            for ms in groups.values()
            if len(ms) > 1 and not _una_tienda_los_separa(ms)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = load_catalog()
    groups = mergeable_groups(data["products"])

    print(f"Grupos fusionables (misma firma, nombre distinto): {len(groups)}")
    for ps in groups:
        stores = sorted({o.get("storeId") for p in ps for o in (p.get("offers") or [])})
        print(f"\n  {stores}")
        for p in ps:
            print(f"    {p['id']:<10} {p['name'][:76]}")
    if not groups:
        return
    if args.dry_run:
        print("\n(sin --dry-run se aplica)")
        return

    drop_ids = set()
    for ps in groups:
        primary = ps[0]
        seen = {o.get("url") for o in primary.setdefault("offers", [])}
        for p in ps[1:]:
            for o in p.get("offers") or []:
                if o.get("url") in seen:
                    continue
                primary["offers"].append(o)
                seen.add(o.get("url"))
            if not primary.get("photo") and p.get("photo"):
                primary["photo"] = p["photo"]
            if not primary.get("specs") and p.get("specs"):
                primary["specs"] = p["specs"]
            drop_ids.add(p["id"])

    data["products"] = [p for p in data["products"] if p["id"] not in drop_ids]
    save_catalog(data)
    print(f"\nProductos fusionados y eliminados: {len(drop_ids)}")
    print(f"Catálogo: {len(data['products'])} productos")

    # La página estática del producto que desaparece queda huérfana:
    # generate_seo_pages.py solo escribe las de los productos actuales,
    # nunca borra las de los que dejaron de existir.
    removed = 0
    for pid in drop_ids:
        d = os.path.join(ROOT, "producto", pid)
        if os.path.isdir(d):
            shutil.rmtree(d)
            removed += 1
    print(f"Páginas estáticas huérfanas eliminadas: {removed}")


if __name__ == "__main__":
    main()
