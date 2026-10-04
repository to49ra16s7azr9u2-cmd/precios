#!/usr/bin/env python3
"""Cambia por la foto vigente las fotos de una tienda que ya no existen,
usando una captura reciente de esa misma tienda (04-oct-2026).

EL PROBLEMA
-----------
Elektra (VTEX) vuelve a subir las imágenes de sus productos y la url vieja
deja de existir: /arquivos/ids/31013070/... da 404 y la nueva es otro id.
El refresco diario es el que debía ir al día, pero llevaba semanas sin
correr para Elektra (403 por el User-Agent, y después la regla del 50% de
cobertura; ver refresh_vtex.py). Medido el 04-oct: de las 64 mil fichas
viejas de Elektra, 15,255 tenían una foto distinta en la captura del árbol
de ese día, y en una muestra la vieja daba 404 en el 100% y la nueva 200 en
el 100%. En el sitio eran filas «sin foto» (la ilustración de la categoría).

QUÉ HACE
--------
Para cada ficha con una oferta de la tienda de la captura (por el número de
producto de la url, id_de_url, y si no por la url), si la captura trae una
foto con otro id de asset que la que tiene la ficha:
  - la foto de la oferta de esa tienda pasa a ser la de la captura;
  - la foto de la ficha también, pero sólo si era de esa misma tienda (una
    ficha con la foto de Mercado Libre o de Coppel no se toca) y la ficha no
    tiene colores (cada color trae su foto).

USO
---
    python3 scripts/actualizar_fotos_captura.py /tmp/elektra/elektra-arbol.json --dry-run
    python3 scripts/actualizar_fotos_captura.py /tmp/elektra/elektra-arbol.json
"""
import argparse
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog, url_real  # noqa: E402
from importar_captura_tienda import id_de_url  # noqa: E402

_ASSET = re.compile(r"/arquivos/ids/(\d+)")


def clave_foto(u):
    """El id del asset de VTEX (lo que cambia cuando la tienda la vuelve a
    subir); para otras urls, la url sin parámetros."""
    m = _ASSET.search(u or "")
    return m.group(1) if m else (u or "").split("?")[0]


def host(u):
    m = re.match(r"https?://([^/]+)/", u or "")
    return m.group(1) if m else ""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("captura")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    with open(args.captura, encoding="utf-8") as f:
        captura = json.load(f)
    tiendas = {it.get("store") for it in captura}
    if len(tiendas) != 1:
        sys.exit(f"la captura debe ser de una sola tienda: {sorted(map(str, tiendas))}")
    tienda = tiendas.pop()
    por_id = {it["id"]: it for it in captura if it.get("photo")}
    por_url = {it["url"]: it for it in captura if it.get("photo")}
    hosts_tienda = {host(it["photo"]) for it in captura if it.get("photo")}
    data = load_catalog()
    est = collections.Counter()
    ejemplos = []
    for p in data["products"]:
        ofertas = list(p.get("offers") or [])
        for v in p.get("colorVariants") or []:
            ofertas += v.get("offers") or []
        for o in ofertas:
            if o.get("storeId") != tienda or not o.get("url"):
                continue
            real = url_real(o["url"]) or o["url"]
            it = por_id.get(id_de_url(real)) or por_url.get(real)
            if not it:
                continue
            nueva = it["photo"]
            if o.get("photo") and clave_foto(o["photo"]) != clave_foto(nueva):
                o["photo"] = nueva
                est["foto de la oferta"] += 1
            # Con colores, cada oferta es de un color con su foto: la de la
            # ficha no se cambia por la del primer color que aparezca.
            if p.get("photo") and not p.get("colorVariants") and host(p["photo"]) in hosts_tienda \
                    and clave_foto(p["photo"]) != clave_foto(nueva):
                if len(ejemplos) < 8:
                    ejemplos.append((p["id"], p["photo"][:90], nueva[:90]))
                p["photo"] = nueva
                est["foto de la ficha"] += 1
            break
    print(f"{tienda}: {dict(est)}")
    for e in ejemplos:
        print("   ", *e)
    if args.dry_run:
        print("(--dry-run: no se escribió nada)")
        return 0
    if est:
        save_catalog(data)
        print("Guardado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
