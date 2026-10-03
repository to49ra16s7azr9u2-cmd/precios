#!/usr/bin/env python3
"""Deja la captura del feed de Elektra (Soicos, programa 10219) lista para
importar_captura_tienda.py.

Dos cambios sobre lo que sale de soicos_a_captura.py:

  1. La url se guarda SIN el deeplink (la de elektra.mx que va dentro de
     dl=). Las 68 mil ofertas de Elektra que ya hay se guardan así:
     refresh_vtex.py, merge_same_store.py y split_elektra_variants.py
     comparan esa url, y el deeplink se pone al salir hacia la tienda
     (afiliados.url_salida y urlSalida() en js/app.js).
  2. El id pasa a ser el número de producto de Elektra que va al final de la
     url, no el id interno de Soicos: es con ese número que
     importar_captura_tienda.conocidos() reconoce lo que ya está.

USO
---
    python3 scripts/preparar_captura_elektra.py captura-elektra.json(.gz) --salida /tmp/elektra.json
    python3 scripts/importar_captura_tienda.py /tmp/elektra.json --dry-run
    python3 scripts/importar_captura_tienda.py /tmp/elektra.json
"""
import argparse
import collections
import gzip
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import url_real  # noqa: E402
from importar_captura_tienda import id_de_url  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("captura")
    ap.add_argument("--salida", required=True)
    args = ap.parse_args()
    abrir = gzip.open if args.captura.endswith(".gz") else open
    with abrir(args.captura, "rt", encoding="utf-8") as f:
        items = json.load(f)
    out, motivos, vistos = [], collections.Counter(), set()
    for it in items:
        url = url_real(it.get("url")) or it.get("url") or ""
        if not url.startswith("https://www.elektra.mx/"):
            motivos["url que no es de elektra.mx"] += 1
            continue
        pid = id_de_url(url)
        if not pid:
            motivos["sin número de producto en la url"] += 1
            continue
        if pid in vistos:
            motivos["repetido en el feed"] += 1
            continue
        vistos.add(pid)
        out.append(dict(it, store="elektra", id=pid, url=url))
    with open(args.salida, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"feed: {len(items):,} -> listos: {len(out):,} en {args.salida}")
    for m, n in motivos.most_common():
        print(f"  fuera: {m}: {n:,}")


if __name__ == "__main__":
    main()
