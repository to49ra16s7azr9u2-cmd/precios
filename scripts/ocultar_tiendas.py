#!/usr/bin/env python3
"""Saca del catálogo publicado las ofertas de una tienda, sin perderlas.

POR QUÉ
-------
Los términos de uso de varias tiendas prohíben reproducir su contenido
fuera del uso personal y no comercial, o directamente prohíben la
extracción automática (Refacciones Originales nombra "robot, araña,
scraping... herramientas de inteligencia artificial"). Mientras no haya una
autorización por escrito -- normalmente, entrar a su programa de afiliados
-- esas ofertas no deben verse en el sitio.

Esto NO borra nada: mueve lo afectado a data/tiendas-ocultas.json, de donde
`--restaurar` lo devuelve tal cual el día que llegue el permiso. Lo que sale
del catálogo deja de aparecer en todas partes sin tocar ningún otro script:
las páginas estáticas, los índices de búsqueda y de marcas, los rankings y
los sitemaps se arman leyendo el catálogo.

QUÉ PASA CON CADA FICHA
-----------------------
  - Si la ficha tiene ofertas de otras tiendas, pierde solo la de esta y se
    queda (con un vendedor menos).
  - Si esa era su única oferta, la ficha entera se guarda en el archivo y
    sale del catálogo: una ficha sin oferta no es comparable ni se puede
    publicar.

USO
---
    python3 scripts/ocultar_tiendas.py --tienda gandhi --dry-run
    python3 scripts/ocultar_tiendas.py --tienda gandhi --tienda doto
    python3 scripts/ocultar_tiendas.py --restaurar --tienda gandhi
    python3 scripts/ocultar_tiendas.py --listar
"""
import argparse
import gzip
import io
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
from data_io import load_catalog, save_catalog  # noqa: E402

# Comprimido (24-sep-2026): el sitio no lo lee y en JSON plano eran 33 MB
# publicados con cada página. gzip con mtime=0 para que el mismo contenido
# dé el mismo archivo (y no un cambio en git en cada corrida).
ARCHIVO = os.path.join(ROOT, "data", "tiendas-ocultas.json.gz")


def leer():
    if not os.path.exists(ARCHIVO):
        return {"tiendas": {}, "productos": [], "ofertas": []}
    with gzip.open(ARCHIVO, "rt", encoding="utf-8") as f:
        return json.load(f)


def guardar(d):
    with gzip.GzipFile(ARCHIVO, "wb", mtime=0) as g, io.TextIOWrapper(g, encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def ofertas_de(producto):
    """Todas las listas de ofertas de una ficha: la suya y las de sus variantes."""
    yield producto.get("offers") or []
    for v in producto.get("colorVariants") or []:
        yield v.get("offers") or []


def tiene_ofertas(producto):
    return any(lista for lista in ofertas_de(producto))


def ocultar(data, tiendas, motivo):
    guardado = leer()
    fuera_productos, fuera_ofertas = [], []
    quedan = []
    for p in data["products"]:
        sacadas = []
        for lista in ofertas_de(p):
            for o in list(lista):
                if o.get("storeId") in tiendas:
                    lista.remove(o)
                    sacadas.append(o)
        if not sacadas:
            quedan.append(p)
            continue
        if tiene_ofertas(p):
            quedan.append(p)
            fuera_ofertas.extend({"productId": p["id"], "offer": o} for o in sacadas)
        else:
            # Se guarda la ficha con sus ofertas de vuelta, para poder
            # restaurarla idéntica.
            entera = dict(p)
            entera["offers"] = (entera.get("offers") or []) + [o for o in sacadas if o.get("storeId") in tiendas]
            fuera_productos.append(entera)
    data["products"] = quedan
    data["stores"] = [s for s in (data.get("stores") or []) if s["id"] not in tiendas]
    guardado["productos"].extend(fuera_productos)
    guardado["ofertas"].extend(fuera_ofertas)
    for t in tiendas:
        guardado["tiendas"][t] = motivo
    return guardado, fuera_productos, fuera_ofertas


def restaurar(data, tiendas):
    guardado = leer()
    por_id = {p["id"]: p for p in data["products"]}
    vueltas_p, vueltas_o = 0, 0
    quedan_p, quedan_o = [], []
    for p in guardado.get("productos", []):
        if any(o.get("storeId") in tiendas for lista in ofertas_de(p) for o in lista):
            data["products"].append(p)
            por_id[p["id"]] = p
            vueltas_p += 1
        else:
            quedan_p.append(p)
    for e in guardado.get("ofertas", []):
        o = e["offer"]
        p = por_id.get(e["productId"])
        if p is not None and o.get("storeId") in tiendas:
            p.setdefault("offers", []).append(o)
            vueltas_o += 1
        else:
            quedan_o.append(e)
    guardado["productos"], guardado["ofertas"] = quedan_p, quedan_o
    for t in tiendas:
        guardado.get("tiendas", {}).pop(t, None)
    return guardado, vueltas_p, vueltas_o


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tienda", action="append", default=[], help="storeId (se puede repetir)")
    ap.add_argument("--motivo", default="sin autorización por escrito de la tienda",
                    help="por qué se oculta; queda anotado en el archivo")
    ap.add_argument("--restaurar", action="store_true", help="devolver al catálogo lo guardado")
    ap.add_argument("--listar", action="store_true", help="qué hay guardado")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.listar:
        g = leer()
        print(f"{ARCHIVO}")
        for t, m in sorted(g.get("tiendas", {}).items()):
            print(f"  {t}: {m}")
        print(f"  fichas guardadas: {len(g.get('productos', [])):,}   ofertas sueltas: {len(g.get('ofertas', [])):,}")
        return
    if not args.tienda:
        ap.error("se necesita --tienda")
    tiendas = set(args.tienda)

    data = load_catalog()
    antes = len(data["products"])
    if args.restaurar:
        guardado, vp, vo = restaurar(data, tiendas)
        print(f"Restauradas {vp:,} fichas y {vo:,} ofertas de {', '.join(sorted(tiendas))}")
    else:
        guardado, fp, fo = ocultar(data, tiendas, args.motivo)
        print(f"Tiendas ocultadas: {', '.join(sorted(tiendas))}")
        print(f"  fichas que salen del catálogo (era su única oferta): {len(fp):,}")
        print(f"  ofertas quitadas de fichas que se quedan:            {len(fo):,}")
    print(f"  catálogo: {antes:,} -> {len(data['products']):,} fichas")
    if args.dry_run:
        print("\n(--dry-run: no se escribió nada)")
        return
    guardar(guardado)
    save_catalog(data)
    print(f"\nGuardado. Lo oculto vive en {os.path.relpath(ARCHIVO, ROOT)} y vuelve con --restaurar.")
    print("Ahora hay que regenerar: sync_subcategories, compute_facets, compute_quality_axes, "
          "build_search_index, build_marcas_index, generate_seo_pages.")


if __name__ == "__main__":
    main()
