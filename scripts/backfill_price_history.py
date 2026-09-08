#!/usr/bin/env python3
"""Rellena data/hist/ con los precios que quedaron en el historial de git.

El refresco diario sobreescribía el precio, pero cada corrida dejaba un
commit con data/cat/*.json: ahí está, sin querer, el precio de cada día desde
que el catálogo se empezó a versionar. Es todo el pasado que se puede
recuperar --antes de eso no existe-- y hay que sacarlo UNA vez, antes de que
el historial de git se poede o se reescriba.

De cada día se toma el ÚLTIMO commit que tocó data/cat/, que es el estado con
el que quedó el sitio ese día.

USO
    python3 scripts/backfill_price_history.py --dry-run
    python3 scripts/backfill_price_history.py
"""
import argparse
import collections
import datetime
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import ROOT, load_catalog
from record_price_history import (
    dia_de, limpiar_huerfanos, registrar, ubicacion_actual,
)


# La partición anterior a data/cat/: data/products-1.json, -2, -3...
PARTICION_VIEJA = re.compile(r"data/products-\d+\.json$")


def git(*args):
    return subprocess.run(
        ["git", "-C", ROOT, *args], capture_output=True, text=True, check=True
    ).stdout


def commits_por_dia():
    """[(fecha, sha)] -- el último commit de cada día que tocó el catálogo.

    Se miran las dos particiones: data/cat/ (la actual, por categoría) y
    data/products-N.json (la anterior, ciega por conteo). Los primeros días
    del catálogo están solo en la vieja, y son días que no se pueden
    recuperar de ninguna otra parte.
    """
    salida = git("log", "--format=%H %ad", "--date=short", "--",
                 "data/cat/", "data/products-1.json")
    ultimo = {}
    for linea in salida.splitlines():
        sha, fecha = linea.split(None, 1)
        # git log viene del más nuevo al más viejo, así que el primero que se
        # ve de cada día ES el último de ese día.
        ultimo.setdefault(fecha.strip(), sha)
    return sorted((datetime.date.fromisoformat(f), sha) for f, sha in ultimo.items())


def productos_en(sha):
    """Los productos del catálogo tal como estaban en ese commit.

    Se leen solo las shards de data/cat: traen category, offers y
    colorVariants, que es todo lo que necesita el registrador. No hace falta
    data/det (ahí van url y ficha técnica, nada de precios).
    """
    archivos = [
        n for n in git("ls-tree", "-r", "--name-only", sha, "data/").split()
        if n.endswith(".json") and (
            n.startswith("data/cat/") or PARTICION_VIEJA.match(n)
        )
    ]
    productos = []
    for nombre in archivos:
        try:
            productos.extend(json.loads(git("show", f"{sha}:{nombre}")))
        except (subprocess.CalledProcessError, ValueError):
            continue
    return productos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = load_catalog()
    donde = ubicacion_actual(data["products"])
    if not args.dry_run:
        limpiar_huerfanos(donde)

    dias = commits_por_dia()
    print(f"Días con datos en git: {len(dias)} "
          f"({dias[0][0]} a {dias[-1][0]})" if dias else "Sin commits de data/cat")

    total = collections.Counter()
    for fecha, sha in dias:
        productos = productos_en(sha)
        # Sin podar: se recorre de más viejo a más nuevo y podar contra la
        # fecha de un día viejo borraría lo que aún no se anotó.
        st = registrar(productos, fecha, donde, args.dry_run, podar_viejo=False)
        total.update(st)
        print(f"  {fecha} {sha[:9]}  {len(productos):,} productos  "
              f"+{st['puntos']:,} puntos  ({st['ignorados']:,} ya no existen)")

    print(f"\nTotal: {total['puntos']:,} puntos, {total['series_nuevas']:,} series")
    if args.dry_run:
        print("(--dry-run: no se escribió nada)")


if __name__ == "__main__":
    main()
