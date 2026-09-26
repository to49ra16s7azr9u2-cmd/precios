#!/usr/bin/env python3
"""Saca fichas sueltas del catálogo publicado, sin perderlas.

POR QUÉ
-------
El sitio no compara medicamentos (su publicidad está regulada por COFEPRIS;
ver DEPARTAMENTOS_FUERA en soicos_a_captura.py), pero algunos entraron por la
taxonomía de su tienda como «Suplementos»: captopril, losartán, amlodipino,
Crestor... (26-sep-2026). ocultar_tiendas.py hace esto por tienda; esto lo
hace por ficha.

Esto NO borra nada: la ficha entera va a data/fichas-ocultas.json.gz con el
motivo y la fecha, y `--restaurar` la devuelve tal cual. Lo que sale del
catálogo deja de aparecer en todas partes (páginas, índices, rankings,
sitemaps), porque todo eso se arma leyendo el catálogo.

USO
---
    python3 scripts/ocultar_fichas.py --ids ids.json --motivo "medicamento" --dry-run
    python3 scripts/ocultar_fichas.py --ids ids.json --motivo "medicamento"
    python3 scripts/ocultar_fichas.py --restaurar --motivo "medicamento"   # o --ids
"""
import argparse
import datetime
import gzip
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import ROOT, load_catalog, save_catalog  # noqa: E402

ARCHIVO = os.path.join(ROOT, "data", "fichas-ocultas.json.gz")


def leer():
    if not os.path.exists(ARCHIVO):
        return {"fichas": []}
    with gzip.open(ARCHIVO, "rt", encoding="utf-8") as f:
        return json.load(f)


def guardar(d):
    tmp = ARCHIVO + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, ARCHIVO)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ids", help="JSON con la lista de ids")
    ap.add_argument("--motivo", required=True)
    ap.add_argument("--restaurar", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    ids = set(json.load(open(args.ids, encoding="utf-8"))) if args.ids else None
    archivo = leer()
    data = load_catalog()

    if args.restaurar:
        vuelven = [x for x in archivo["fichas"]
                   if x["motivo"] == args.motivo and (ids is None or x["ficha"]["id"] in ids)]
        presentes = {p["id"] for p in data["products"]}
        nuevas = [x["ficha"] for x in vuelven if x["ficha"]["id"] not in presentes]
        print(f"vuelven {len(nuevas):,} fichas (motivo «{args.motivo}»)")
        if args.dry_run:
            return
        data["products"].extend(nuevas)
        archivo["fichas"] = [x for x in archivo["fichas"] if x not in vuelven]
        save_catalog(data)
        guardar(archivo)
        return

    if not ids:
        sys.exit("falta --ids")
    salen = [p for p in data["products"] if p["id"] in ids]
    print(f"salen {len(salen):,} fichas (motivo «{args.motivo}»)")
    for p in salen[:15]:
        print(f"  {p['id']:>9}  {p['category']} / {p.get('subcategory')}  {p['name'][:60]}")
    if args.dry_run:
        return
    hoy = datetime.date.today().isoformat()
    archivo["fichas"].extend({"motivo": args.motivo, "fecha": hoy, "ficha": p} for p in salen)
    data["products"] = [p for p in data["products"] if p["id"] not in ids]
    guardar(archivo)
    save_catalog(data)
    print("Guardado.")


if __name__ == "__main__":
    main()
