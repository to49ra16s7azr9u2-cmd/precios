#!/usr/bin/env python3
"""Aplica al catálogo los movimientos de categoría/subcategoría que proponen
auditar_subcategorias.py o detectar_mal_clasificados.py (su --salida).

El JSON es {"cat | sub | cat2 | sub2": [ids]}. Se mueven los grupos que se
pidan (--grupo, repetible; --todos para todos; --min para los de cierto
tamaño) menos los vetados (--vetar), y cada ficha movida toma el icono de su
subcategoría nueva. No se toca nada más de la ficha.

Los grupos aplicados quedan anotados en data/movimientos-aplicados.json con
la fecha, para saber después qué se movió y por qué.

USO
---
    python3 scripts/aplicar_movimientos.py mover.json --todos --dry-run
    python3 scripts/aplicar_movimientos.py mover.json --todos --min 10 --vetar "Refacciones | Refacciones para electrodomésticos | Electrodomésticos | Freidoras de aire"
    python3 scripts/aplicar_movimientos.py mover.json --grupo "Muebles | Sillas | Deportes y fitness | Pesas"
"""
import argparse
import collections
import datetime
import io
import json
import os
import re
import sys
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
from data_io import load_catalog, save_catalog  # noqa: E402

BITACORA = os.path.join(ROOT, "data", "movimientos-aplicados.json")
# Las fichas movidas por una persona, una por una: reaplicar_reglas.py no las
# devuelve adonde las mandaría una regla (la decisión a mano manda).
CANDADO = os.path.join(ROOT, "data", "clasificacion-a-mano.json")


def plano(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("json")
    ap.add_argument("--grupo", action="append", default=[], help="clave 'cat | sub | cat2 | sub2' (repetible)")
    ap.add_argument("--todos", action="store_true")
    ap.add_argument("--min", type=int, default=1, help="con --todos, grupos menores se saltan")
    ap.add_argument("--vetar", action="append", default=[], help="grupos que NO se aplican")
    ap.add_argument("--plan", help="JSON con [{grupo, filtro?, excluir?}, ...]: varios grupos con su filtro en una sola pasada")
    ap.add_argument("--filtro", help="regex (sin acentos, minúsculas): solo se mueven las fichas cuyo nombre lo cumple")
    ap.add_argument("--excluir", help="regex (sin acentos, minúsculas): las fichas cuyo nombre lo cumple no se mueven")
    ap.add_argument("--motivo", default="", help="nota para la bitácora")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    grupos = json.load(io.open(args.json, encoding="utf-8"))
    vetados = set(args.vetar)
    # Filtro por grupo: el de --plan si lo trae, si no el general de --filtro/--excluir.
    filtros = {}
    elegidos = []
    if args.plan:
        for e in json.load(io.open(args.plan, encoding="utf-8")):
            k = e["grupo"]
            if k not in grupos:
                print(f"  AVISO: el plan pide un grupo que no está en el JSON: {k}")
                continue
            elegidos.append(k)
            filtros[k] = (re.compile(e["filtro"]) if e.get("filtro") else None,
                          re.compile(e["excluir"]) if e.get("excluir") else None)
    for k, ids in grupos.items():
        if k in vetados or k in filtros:
            continue
        if args.todos and len(ids) >= args.min:
            elegidos.append(k)
        elif k in args.grupo:
            elegidos.append(k)
    if not elegidos:
        sys.exit("ningún grupo elegido")

    rx_filtro = re.compile(args.filtro) if args.filtro else None
    rx_excluir = re.compile(args.excluir) if args.excluir else None

    data = load_catalog()
    prods = {p["id"]: p for p in data["products"]}
    icono = {}
    for c in data["categories"]:
        icono[(c["id"], None)] = c.get("icon")
        for s in c.get("subcategories") or []:
            icono[(c["id"], s["id"])] = s.get("icon") or c.get("icon")
    subs_de = {c["id"]: {s["id"] for s in (c.get("subcategories") or [])} for c in data["categories"]}

    movidas = collections.Counter()
    saltadas = 0
    a_mano = json.load(io.open(CANDADO, encoding="utf-8")) if os.path.exists(CANDADO) else {}
    for k in elegidos:
        partes = [x.strip() for x in k.split("|")]
        if len(partes) != 4:
            continue
        cat2, sub2 = partes[2], (None if partes[3] == "None" else partes[3])
        if cat2 not in subs_de or (sub2 and sub2 not in subs_de[cat2]):
            print(f"  SALTADO grupo con destino desconocido: {k}")
            continue
        for pid in grupos[k]:
            p = prods.get(pid)
            if not p or p.get("category") != partes[0] or (p.get("subcategory") or "None") != partes[1]:
                saltadas += 1   # ya se movió o ya no está
                continue
            nombre = plano(p.get("name"))
            f_in, f_out = filtros.get(k, (rx_filtro, rx_excluir))
            if f_in and not f_in.search(nombre):
                continue
            if f_out and f_out.search(nombre):
                continue
            p["category"], p["subcategory"] = cat2, sub2
            a_mano[pid] = [cat2, sub2]
            ic = icono.get((cat2, sub2)) or icono.get((cat2, None))
            if ic:
                p["image"] = ic
            movidas[k] += 1

    for k, n in sorted(movidas.items(), key=lambda kv: -kv[1]):
        print(f"{n:5}  {k}")
    print(f"\nmovidas: {sum(movidas.values()):,} en {len(movidas)} grupos   saltadas (ya no estaban ahí): {saltadas}")
    if args.dry_run:
        print("(--dry-run: no se guardó nada)")
        return
    if not movidas:
        return
    save_catalog(data)
    bit = json.load(io.open(BITACORA, encoding="utf-8")) if os.path.exists(BITACORA) else []
    bit.append({"fecha": datetime.date.today().isoformat(), "origen": os.path.basename(args.json), "motivo": args.motivo,
                "grupos": {k: n for k, n in movidas.items()}})
    json.dump(bit, io.open(BITACORA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(a_mano, io.open(CANDADO, "w", encoding="utf-8"), ensure_ascii=False, sort_keys=True,
              separators=(",", ":"))
    print(f"Guardado. Bitácora: {os.path.relpath(BITACORA, ROOT)}")
    print("Ahora: sync_subcategories, compute_facets, compute_quality_axes, build_search_index, build_marcas_index, generate_seo_pages.")


if __name__ == "__main__":
    main()
