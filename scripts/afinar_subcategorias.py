#!/usr/bin/env python3
"""Reparte una categoría entera en las subcategorías finas de
subcategorias_finas.py y deja la lista de data.categories acorde.

POR QUÉ
-------
"Vitaminas y minerales", "Botellas y termos" o "Literatura y novela" eran
cajones demasiado grandes: quien busca magnesio, un vaso térmico o un
thriller no encuentra nada útil en una subcategoría de 1,700 fichas. Las
subcategorías finas se definen en subcategorias_finas.py (nutriente, uso y
tipo, género); este script las aplica a lo que ya está en el catálogo Y a
las fichas de tiendas ocultas (data/tiendas-ocultas.json), para que al
restaurarlas lleguen ya repartidas.

Además de reasignar la subcategoría (y el icono, como aplicar_movimientos)
reescribe data.categories[cat].subcategories con la lista fina en el orden
del módulo; las subcategorías viejas que se quedan sin fichas desaparecen
de la lista y las que aún tienen alguna (no debería pasar) se conservan al
final.

USO
---
    python3 scripts/afinar_subcategorias.py --categoria Suplementos --dry-run
    python3 scripts/afinar_subcategorias.py --todas
"""
import argparse
import collections
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import load_catalog, save_catalog  # noqa: E402
import subcategorias_finas as fino  # noqa: E402

OCULTAS = os.path.join(AQUI, "..", "data", "tiendas-ocultas.json")

# Palabras de marketing que Gandhi mete en el subtítulo (PIM_H1) de todos
# los libros: "Un viaje literario", "obra maestra", "clásico indispensable".
# Sin quitarlas, la mitad del catálogo sería "Viajes" o "Clásicos".
RX_CLICHE = re.compile(
    r'\b(un )?viaje (literario|epico|intimo|profundo|visual|apasionante|inesperado|desgarrador|'
    r'inolvidable|emotivo|fascinante|por|al|a traves|hacia)\b.{0,25}|obra maestra|'
    r'clasico (indispensable|radical|para|de siempre|moderno)|al corazon de|en el corazon de|'
    r'tesoro|imprescindible|inolvidable|legado|en (tu|nuestra) libreria|joya literaria|conquista mundos')


def T(s):
    s = re.sub(r'\s+', ' ', (s or '').lower())
    return s.translate(str.maketrans('áéíóúñü', 'aeiounu'))


def specs_de(p):
    out = {}
    for s in (p.get("specs") or []):
        if isinstance(s, dict) and "label" in s:
            out[s["label"]] = str(s.get("value") or "")
    return out


def texto_libro(p):
    sp = specs_de(p)
    h1 = RX_CLICHE.sub('', T(sp.get("PIM_H1", "")))
    return T(p.get("name") or "") + " | " + h1


CATEGORIAS = {
    "Suplementos": (fino.SUPLEMENTOS, lambda p: fino.sub_suplemento_fino(T(p.get("name")))),
    "Cocina y comedor": (fino.COCINA, lambda p: fino.sub_cocina_fino(T(p.get("name")))),
    "Libros": (fino.LIBROS, lambda p: fino.sub_libro_fino(texto_libro(p), p.get("subcategory"))),
}


def repartir(fichas, cat, f, icono, dry):
    """Reasigna subcategoría e icono; devuelve (cambiadas, conteo por sub)."""
    cambiadas = 0
    conteo = collections.Counter()
    for p in fichas:
        if p.get("category") != cat:
            continue
        nueva = f(p)
        conteo[nueva] += 1
        if nueva != p.get("subcategory"):
            cambiadas += 1
            if not dry:
                p["subcategory"] = nueva
        if not dry:
            ic = icono.get((cat, nueva)) or icono.get((cat, None))
            if ic:
                p["image"] = ic
    return cambiadas, conteo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--categoria", action="append", default=[])
    ap.add_argument("--todas", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    cats = list(CATEGORIAS) if args.todas else args.categoria
    if not cats:
        ap.error("--categoria o --todas")
    for c in cats:
        if c not in CATEGORIAS:
            ap.error(f"sin repartidor fino: {c}")

    data = load_catalog()
    ocultas = json.load(open(OCULTAS, encoding="utf-8")) if os.path.exists(OCULTAS) else None
    cat_by_id = {c["id"]: c for c in data["categories"]}

    for cat in cats:
        lista, f = CATEGORIAS[cat]
        c = cat_by_id[cat]
        icono_cat = c.get("icon") or "box"
        icono = {(cat, None): icono_cat}
        for sub in lista:
            icono[(cat, sub)] = icono_cat
        # las viejas conservan el suyo por si alguna sobrevive
        for s in c.get("subcategories") or []:
            icono.setdefault((cat, s["id"]), s.get("icon") or icono_cat)

        n1, conteo = repartir(data["products"], cat, f, icono, args.dry_run)
        n2, conteo_oc = (0, collections.Counter())
        if ocultas:
            n2, conteo_oc = repartir(ocultas["productos"], cat, f, icono, args.dry_run)
        total = sum(conteo.values())
        print(f"### {cat}: catálogo {total} fichas ({n1} cambian), ocultas {sum(conteo_oc.values())} ({n2} cambian)")
        for sub in lista + [None]:
            if conteo[sub] or conteo_oc[sub]:
                print(f"   {conteo[sub]:6d} {conteo_oc[sub]:6d}  {sub}")
        sobran = [s for s in conteo if s and s not in lista]
        if sobran:
            print("   FUERA DE LA LISTA:", sobran)

        # Lista nueva de subcategorías: las finas en orden, y las viejas
        # solo si les queda alguna ficha visible.
        viejas = [s for s in (c.get("subcategories") or []) if s["id"] not in lista and conteo.get(s["id"])]
        nuevas = [{"id": sub, "name": sub, "icon": icono_cat} for sub in lista if conteo[sub] or conteo_oc[sub]]
        if not args.dry_run:
            c["subcategories"] = nuevas + viejas
        print(f"   subcategorías en data.categories: {len(nuevas)} finas + {len(viejas)} viejas")

    if args.dry_run:
        print("(dry-run: nada guardado)")
        return
    save_catalog(data)
    if ocultas:
        with open(OCULTAS, "w", encoding="utf-8") as fh:
            json.dump(ocultas, fh, ensure_ascii=False)
    print("Guardado. Ahora: sync_subcategories, compute_facets, compute_quality_axes, build_search_index, build_marcas_index, generate_seo_pages.")


if __name__ == "__main__":
    main()
