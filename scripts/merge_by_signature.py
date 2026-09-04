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
from data_io import load_catalog, save_catalog  # noqa: E402
from phone_signature import signature  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def id_num(product):
    m = re.match(r"p(\d+)$", product.get("id", ""))
    return int(m.group(1)) if m else 10**9


def mergeable_groups(products):
    groups = defaultdict(list)
    for p in products:
        if p.get("category") != "Celulares":
            continue
        sig = signature(p)
        if sig is None:
            continue  # firma incompleta -> no se fusiona con nadie
        groups[sig].append(p)
    return [sorted(ps, key=id_num) for ps in groups.values() if len(ps) > 1]


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
