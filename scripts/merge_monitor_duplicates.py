#!/usr/bin/env python3
"""Fusiona fichas de MONITOR que son el mismo equipo cargado dos veces.

POR QUÉ NO LO RESUELVE merge_by_signature.py
--------------------------------------------
Ese script fusiona por firma estructurada, pero la firma está construida
para CELULARES (marca + línea + almacenamiento + RAM + color + compañía +
regalo + eSIM + red). Un monitor no tiene casi ninguno de esos atributos:
lo que lo identifica es el código de modelo, las pulgadas, la resolución y
la frecuencia. Escribir esa segunda firma completa es un trabajo aparte;
mientras tanto estos nueve pares quedaban partidos, y partidos duelen:
el MISMO monitor aparecía dos veces en la lista, con dos precios
distintos, y en ninguna de las dos fichas se veía la comparación entre
tiendas -- que es exactamente para lo que existe el sitio.

CÓMO SE ELIGIERON
-----------------
Detección: mismo código de modelo (token con letra Y dígito, descartando
los que son especificaciones escritas como token -- 200hz, 1920x1080,
0.5ms), misma marca, y pulgadas iguales o no declaradas en una de las dos.
Después se revisó UNA POR UNA contra resolución, frecuencia, tipo de panel
y curvatura: ningún par tiene un dato que se contradiga; donde uno de los
dos no trae el dato, simplemente falta, no discrepa.

    par                        pulgadas   resolución  Hz     panel
    XPG RIFT R24F2             23.8       FHD         120    IPS
    Acteck Captive Brite CB185 18.5       HD          60     TN
    Acteck Captive Brite CB195 19.5       HD          60     TN
    Acteck Captive Vivid SP215 21.5       FHD         75     VA
    Acteck Captive Vivid SP245 24.5       FHD         75     IPS
    Xiaomi A22i                21.5       FHD         --     VA
    Xiaomi A24i 2026           23.8/24    FHD         144    IPS
    BenQ GW2791                27         FHD         100    IPS
    Dell SE2426H               23.8/24    FHD         144    IPS

(23.8" y 24" son el mismo panel: 24" es la medida comercial.)

EL QUE NO ENTRA
---------------
XZEAL XST-570-1 quedó AFUERA a propósito, y es el motivo por el que esta
lista se revisó a mano en vez de aplicarse automática: p48915 es el BLANCO
y p124995 el NEGRO. Mismo código de modelo, mismas pulgadas, misma
resolución -- y aun así son dos productos distintos. Fusionarlos habría
puesto el precio del negro ($1,731) en la ficha del blanco ($3,999).

USO
---
    python3 scripts/merge_monitor_duplicates.py --dry-run
    python3 scripts/merge_monitor_duplicates.py
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (etiqueta, id que sobrevive, id que se absorbe). Sobrevive el id más bajo
# -- el más viejo, el que probablemente ya esté indexado en buscadores --,
# igual que en merge_cross_store.py y merge_by_signature.py.
PAIRS = [
    ("XPG RIFT R24F2", "p49066", "p49075"),
    ("Acteck Captive Brite CB185", "p49015", "p124924"),
    ("Acteck Captive Brite CB195", "p49118", "p49132"),
    ("Acteck Captive Vivid SP215", "p49138", "p124864"),
    ("Acteck Captive Vivid SP245", "p49093", "p49111"),
    ("Xiaomi A22i", "p48976", "p124865"),
    ("Xiaomi A24i 2026", "p29763", "p124891"),
    ("BenQ GW2791", "p31724", "p124970"),
    ("Dell SE2426H", "p26981", "p124874"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = load_catalog()
    by_id = {p["id"]: p for p in data["products"]}

    drop = set()
    for label, keep_id, drop_id in PAIRS:
        keep, gone = by_id.get(keep_id), by_id.get(drop_id)
        if not keep or not gone:
            # Ya fusionado en una corrida anterior: no es un error, es que
            # este script se puede volver a correr sin romper nada.
            print(f"  {label}: {keep_id}/{drop_id} -- ya no están los dos, se salta")
            continue
        if keep.get("category") != "Monitores" or gone.get("category") != "Monitores":
            print(f"  {label}: ALGUNO NO ES MONITOR, se salta", file=sys.stderr)
            continue
        seen = {o.get("url") for o in keep.setdefault("offers", [])}
        moved = 0
        for o in gone.get("offers") or []:
            if o.get("url") in seen:
                continue
            keep["offers"].append(o)
            seen.add(o.get("url"))
            moved += 1
        if not keep.get("photo") and gone.get("photo"):
            keep["photo"] = gone["photo"]
        if not keep.get("specs") and gone.get("specs"):
            keep["specs"] = gone["specs"]
        drop.add(drop_id)
        stores = sorted({o.get("storeId") for o in keep["offers"]})
        print(f"  {label}: {drop_id} -> {keep_id} (+{moved} oferta(s); queda con {stores})")

    if args.dry_run:
        print(f"\n(--dry-run: se fusionarían {len(drop)} fichas, no se escribió nada)")
        return
    if not drop:
        print("\nNada que fusionar.")
        return

    data["products"] = [p for p in data["products"] if p["id"] not in drop]
    save_catalog(data)
    print(f"\nFichas fusionadas: {len(drop)}; catálogo: {len(data['products'])} productos")

    # La página estática de la ficha que desaparece queda huérfana:
    # generate_seo_pages.py solo escribe las de los productos actuales,
    # nunca borra las de los que dejaron de existir.
    removed = 0
    for pid in drop:
        path = os.path.join(ROOT, "producto", f"{pid}.html")
        if os.path.exists(path):
            os.remove(path)
            removed += 1
    print(f"Páginas estáticas huérfanas eliminadas: {removed}")


if __name__ == "__main__":
    main()
