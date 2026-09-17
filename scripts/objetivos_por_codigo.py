#!/usr/bin/env python3
"""Arma la lista de consultas a Mercado Libre POR CÓDIGO DE MODELO para las
fichas de una sola tienda que no tienen con quién fusionarse.

POR QUÉ
-------
merge_amazon_cross_store.py --todas-las-tiendas (17-sep-2026) dejó 38,913
fichas con este motivo: "ningún producto de otra tienda con ese código".
No es que la fusión falle: es que el otro vendedor no está en el catálogo.
ml_discover.py trae productos por subcategoría y por marca, y así ya se
agotó (15,990 combinaciones). Lo que falta es preguntarle a Mercado Libre
por el código exacto ("aw65rkq", "8x214a6") dentro del dominio de esa
categoría: una consulta por ficha huérfana, que devuelve el mismo producto
o nada.

Los códigos salen de merge_amazon_cross_store.codigos() / codigos_pegados(),
que ya excluyen medidas y especificaciones ("128gb", "1080p"). Un código es
huérfano si ninguna ficha de OTRA tienda lo tiene. El dominio sale de las
líneas "Cat / Sub -> MLM-... (...)" que imprime ml_discover.py; se pasan
uno o más logs con --logs. Sin dominio confirmado la ficha se salta:
/catalog del Worker exige ?domain= y adivinarlo es lo que el propio
ml_discover.py aprendió a no hacer.

La salida es un targets.json para add_products.py. Lo que entre se fusiona
después con merge_amazon_cross_store.py --dry-run --informe y
fusionar_vetado.py --aplicar (NUNCA sin el filtro: ver ese script).

USO
---
    python3 scripts/objetivos_por_codigo.py --logs /tmp/claude-0/cap/ml3-*.raw /tmp/claude-0/cap/ml4-*.raw \
        --salida /tmp/claude-0/cap/targets_codigos.json
"""
import argparse
import collections
import glob
import json
import re
import sys

sys.path.insert(0, "scripts")
from data_io import load_catalog  # noqa: E402
import merge_amazon_cross_store as m  # noqa: E402

LINEA = re.compile(r'\s+(.+?) / (.+?) -> (MLM-[A-Z0-9_]+) \((.*?), (\d+) conocidos, (\d+)%\)')


def dominios_de(logs):
    por_sub, por_cat = {}, collections.defaultdict(collections.Counter)
    for patron in logs:
        for f in glob.glob(patron):
            for ln in open(f, encoding="utf-8", errors="ignore"):
                mm = LINEA.match(ln)
                if mm:
                    cat, sub, dom = mm.group(1), mm.group(2), mm.group(3)
                    por_sub.setdefault((cat, sub), dom)
                    por_cat[cat][dom] += 1
    return por_sub, por_cat


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", nargs="+", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--max", type=int, default=8)
    args = ap.parse_args()

    por_sub, por_cat = dominios_de(args.logs)
    P = load_catalog()["products"]
    idx = collections.defaultdict(set)
    for p in P:
        for c in m.codigos(p.get("name") or "") | m.codigos_pegados(p.get("name") or ""):
            for t in m.tiendas_de(p):
                idx[c].add(t)

    targets, sin_dom, fichas = {}, collections.Counter(), 0
    for p in P:
        if not m.es_origen(p, False):
            continue
        tiendas = m.tiendas_de(p)
        if "mercadolibre" in tiendas:
            continue
        cods = m.codigos(p.get("name") or "") | m.codigos_pegados(p.get("name") or "")
        huer = [c for c in cods if idx[c] <= tiendas]
        if not huer:
            continue
        cat, sub = p.get("category"), p.get("subcategory")
        dom = por_sub.get((cat, sub)) or (por_cat[cat].most_common(1)[0][0] if por_cat.get(cat) else None)
        if not dom:
            sin_dom[cat] += 1
            continue
        code = max(huer, key=len)
        targets.setdefault((dom, code), {"domain": dom, "q": code, "cat": cat, "sub": None,
                                         "max": args.max, "pages": 1, "icon": p.get("image") or "box"})
        fichas += 1
    json.dump(list(targets.values()), open(args.salida, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"dominios confirmados: {len(por_sub)} subcategorías, {len(por_cat)} categorías")
    print(f"fichas huérfanas con dominio: {fichas:,}   consultas (dominio, código): {len(targets):,}")
    print("sin dominio confirmado:", ", ".join(f"{c} {n}" for c, n in sin_dom.most_common(10)))


if __name__ == "__main__":
    main()
