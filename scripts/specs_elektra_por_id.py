#!/usr/bin/env python3
"""Ficha técnica de Elektra para las fichas que no tienen ninguna.

POR QUÉ
-------
El 05-oct-2026 sólo 117 mil de 896 mil fichas (13%) tenían especificaciones,
y 157 mil de las que no tenían eran de Elektra. refresh_vtex.py ya guarda la
ficha técnica (elektra_specs.py) de lo que ve, pero el recorrido diario de
Elektra es rotativo y desde GitHub Actions la API ni contesta, así que la
mayoría nunca pasaba por ahí. Una muestra de 100 fichas al azar: la API
devolvió 82 (lo demás está agotado u oculto) y 80 de esas traían ficha
técnica, con 5-6 campos de mediana.

CÓMO
----
Se pide por id de SKU (el número final de la url, «...-1300611929/p»), de a
50 por pedido, con la misma API pública de catálogo que autoriza el
robots.txt de Elektra y el User-Agent con el que nos presentamos. Son unos
3,200 pedidos para todo el faltante, con una pausa entre uno y otro.

Dos pasos, para que un reinicio del contenedor no tire lo ya bajado:

    python3 scripts/specs_elektra_por_id.py --bajar     # -> caché JSONL, reanudable
    python3 scripts/specs_elektra_por_id.py --aplicar   # caché -> catálogo

Sólo se llena la ficha que no tiene NINGUNA especificación: la que ya trae
la de Mercado Libre u otra tienda no se toca.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from add_elektra_products import fetch_json  # noqa: E402
from data_io import load_catalog, save_catalog, url_real  # noqa: E402
from elektra_specs import specs_from  # noqa: E402

API = "https://www.elektra.mx/api/catalog_system/pub/products/search"
CACHE = "/tmp/elektra/specs_por_sku.jsonl"
LOTE = 50
_SKU = re.compile(r"-(\d+)/p$")


def sku_de(oferta):
    u = url_real(oferta.get("url") or "") or oferta.get("url") or ""
    m = _SKU.search(u)
    return m.group(1) if m else None


def faltantes(data):
    """{sku: [id de ficha]} de las fichas sin especificaciones con oferta de Elektra."""
    out = {}
    for p in data["products"]:
        if p.get("specs"):
            continue
        for o in p.get("offers") or []:
            if o.get("storeId") == "elektra":
                s = sku_de(o)
                if s:
                    out.setdefault(s, []).append(p["id"])
    return out


def leer_cache():
    vistos = {}
    if os.path.exists(CACHE):
        with open(CACHE, encoding="utf-8") as f:
            for linea in f:
                try:
                    d = json.loads(linea)
                except ValueError:
                    continue
                vistos[d["sku"]] = d.get("specs") or []
    return vistos


def bajar(skus, pausa, limite):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    hechos = leer_cache()
    pendientes = [s for s in skus if s not in hechos]
    if limite:
        pendientes = pendientes[:limite]
    print(f"SKU sin ficha: {len(skus):,}; ya en caché: {len(hechos):,}; por pedir: {len(pendientes):,}")
    con, fallidos = 0, 0
    with open(CACHE, "a", encoding="utf-8") as f:
        for i in range(0, len(pendientes), LOTE):
            lote = pendientes[i:i + LOTE]
            q = "&".join("fq=" + urllib.parse.quote(f"skuId:{s}") for s in lote)
            res = fetch_json(f"{API}?{q}&_from=0&_to={LOTE - 1}")
            if res is None:
                # No se anota: se vuelve a pedir en la próxima corrida.
                fallidos += 1
                time.sleep(pausa * 4)
                continue
            por_sku = {}
            for prod in res:
                ficha = specs_from(prod)
                for it in prod.get("items") or []:
                    por_sku[str(it.get("itemId"))] = ficha
            for s in lote:
                # Lo que la API no devuelve (agotado u oculto) también se
                # anota, vacío, para no volver a pedirlo en cada corrida.
                ficha = por_sku.get(s, [])
                con += bool(ficha)
                f.write(json.dumps({"sku": s, "specs": ficha}, ensure_ascii=False) + "\n")
            f.flush()
            n = i // LOTE + 1
            if n % 50 == 0:
                print(f"  {n:,} pedidos; {i + len(lote):,} SKU; con ficha {con:,}; fallidos {fallidos}", flush=True)
            time.sleep(pausa)
    print(f"Bajado: {len(pendientes):,} SKU, {con:,} con ficha técnica; pedidos fallidos {fallidos}")


def aplicar(data, mapa, dry_run):
    cache = leer_cache()
    por_id = {p["id"]: p for p in data["products"]}
    llenas = 0
    campos = 0
    for s, ids in mapa.items():
        ficha = cache.get(s)
        if not ficha:
            continue
        for pid in ids:
            p = por_id[pid]
            if not p.get("specs"):
                p["specs"] = ficha
                llenas += 1
                campos += len(ficha)
    con = sum(1 for p in data["products"] if p.get("specs"))
    print(f"Fichas que ganan ficha técnica: {llenas:,} ({campos:,} campos); "
          f"con especificaciones: {con:,} de {len(data['products']):,} ({con / len(data['products']):.0%})")
    if dry_run:
        print("(--dry-run: no se escribió nada)")
        return
    save_catalog(data)
    print("Guardado.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bajar", action="store_true")
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--pausa", type=float, default=0.6, help="segundos entre pedidos")
    ap.add_argument("--limite", type=int, default=0, help="sólo los primeros N SKU (prueba)")
    args = ap.parse_args()
    if not (args.bajar or args.aplicar):
        ap.error("--bajar y/o --aplicar")
    data = load_catalog()
    mapa = faltantes(data)
    if args.bajar:
        bajar(sorted(mapa), args.pausa, args.limite)
    if args.aplicar:
        aplicar(data, mapa, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
