#!/usr/bin/env python3
"""Rellena data/hist/ con los precios que quedaron en el historial de git.

El refresco diario sobreescribía el precio, pero cada corrida dejaba un
commit con data/cat/*.json: ahí está, sin querer, el precio de cada día desde
que el catálogo se empezó a versionar. Es todo el pasado que se puede
recuperar --antes de eso no existe-- y hay que sacarlo UNA vez, antes de que
el historial de git se poede o se reescriba.

De cada día se toma el ÚLTIMO commit que tocó data/cat/, que es el estado con
el que quedó el sitio ese día.

SOLO SIRVE CONTRA UN HISTORIAL VACÍO. Los días se replayean del más viejo al
más nuevo y anotar() compara contra el ÚLTIMO punto de la serie, así que
correrlo sobre un data/hist ya poblado le pega los días viejos DETRÁS de los
nuevos y deja las series desordenadas (28 mil puntos fuera de lugar por día
replayeado, medido). Por eso hay que pedir --rehacer explícitamente: borra
data/hist y lo reconstruye entero.

USO
    python3 scripts/backfill_price_history.py --dry-run
    python3 scripts/backfill_price_history.py            # solo si está vacío
    python3 scripts/backfill_price_history.py --rehacer   # borra y reconstruye
"""
import argparse
import collections
import datetime
import json
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import ROOT, load_catalog
from record_price_history import (
    HIST_DIR, dia_de, limpiar_huerfanos, registrar, ubicacion_actual,
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

    Las shards de data/cat traen category, offers y colorVariants. Y hace
    falta también data/det: ahí viven los `sellers`, y el precio que el sitio
    muestra es el del vendedor más barato cuando la publicación abre en filas
    por vendedor (ver _precio_mostrado en record_price_history.py). Sin
    pegarlos de vuelta, un día recuperado de git quedaría medido con otra
    vara que los días nuevos.
    """
    nombres = git("ls-tree", "-r", "--name-only", sha, "data/").split()
    archivos = [
        n for n in nombres
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

    # {id: {"sellers": {"0": [...], ...}}} -> de vuelta a cada oferta, igual
    # que hace load_catalog() con el catálogo de hoy.
    detalles = {}
    for nombre in nombres:
        if not (nombre.startswith("data/det/") and nombre.endswith(".json")):
            continue
        try:
            detalles.update(json.loads(git("show", f"{sha}:{nombre}")))
        except (subprocess.CalledProcessError, ValueError):
            continue
    if detalles:
        for p in productos:
            por_indice = (detalles.get(p["id"]) or {}).get("sellers") or {}
            ofertas = p.get("offers") or []
            for idx, valor in por_indice.items():
                i = int(idx)
                if i < len(ofertas):
                    ofertas[i]["sellers"] = valor
    return productos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--rehacer", action="store_true",
                    help="borra data/hist y lo reconstruye entero desde git")
    args = ap.parse_args()

    hist_dir = os.path.join(ROOT, HIST_DIR)
    ya_hay = os.path.isdir(hist_dir) and any(
        n.endswith(".json") for n in os.listdir(hist_dir)
    )
    if ya_hay and not args.dry_run:
        if not args.rehacer:
            print(f"{HIST_DIR} ya tiene datos. Replayear los días encima "
                  "desordenaría las series (ver el encabezado del archivo). "
                  "Usa --rehacer para borrarlo y reconstruirlo.")
            return 1
        shutil.rmtree(hist_dir)
        print(f"{HIST_DIR} borrado: se reconstruye desde cero.")

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
        if ya_hay:
            print("OJO: data/hist ya tiene datos, así que estos '+puntos' son "
                  "los que se pegarían DETRÁS de los días ya anotados. Para "
                  "reconstruir de verdad hace falta --rehacer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
