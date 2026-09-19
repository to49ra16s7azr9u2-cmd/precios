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
import subcategorias_finas_ola2 as ola2  # noqa: E402

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


TRABAJOS = [
    ("Suplementos", None, fino.SUPLEMENTOS, lambda p: fino.sub_suplemento_fino(T(p.get("name"))), None),
    ("Cocina y comedor", None, fino.COCINA, lambda p: fino.sub_cocina_fino(T(p.get("name"))), None),
    ("Libros", None, fino.LIBROS, lambda p: fino.sub_libro_fino(texto_libro(p), p.get("subcategory")), None),
]
for _cat, _viejas, _lista, _f, _resto in ola2.OLA2:
    TRABAJOS.append((_cat, _viejas, _lista,
                     (lambda f: lambda p: f(T(p.get("name")), p.get("subcategory")))(_f), _resto))


def repartir(fichas, cat, f, icono, dry, viejas=None, muestras=None):
    """Reasigna subcategoría e icono; devuelve (cambiadas, conteo por sub).
    Con `viejas` solo toca las fichas que están en esas subcategorías."""
    cambiadas = 0
    conteo = collections.Counter()
    for p in fichas:
        if p.get("category") != cat:
            continue
        if viejas is not None and p.get("subcategory") not in viejas:
            continue
        nueva = f(p)
        if nueva is None and viejas is not None:
            # El reparto parcial no debe dejar sin subcategoría lo que no
            # reconoce: se queda donde estaba.
            nueva = p.get("subcategory")
        if muestras is not None and len(muestras[nueva]) < 4:
            muestras[nueva].append((p.get("name") or "")[:95])
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
    ap.add_argument("--muestras", action="store_true", help="imprime 4 nombres por subcategoría")
    ap.add_argument("--limpiar-vacias", action="store_true", help="quita de data.categories las subcategorías sin fichas")
    args = ap.parse_args()
    ap_cats = {t[0] for t in TRABAJOS}
    cats = list(ap_cats) if args.todas else args.categoria
    if not cats and not args.limpiar_vacias:
        ap.error("--categoria o --todas")
    for c in cats:
        if c not in ap_cats:
            ap.error(f"sin repartidor fino: {c}")
    trabajos = [t for t in TRABAJOS if t[0] in cats]

    data = load_catalog()
    ocultas = json.load(open(OCULTAS, encoding="utf-8")) if os.path.exists(OCULTAS) else None
    cat_by_id = {c["id"]: c for c in data["categories"]}

    for cat, viejas, lista, f0, resto in trabajos:
        f = (lambda p: f0(p) or resto) if resto else f0
        c = cat_by_id[cat]
        icono_cat = c.get("icon") or "box"
        icono = {(cat, None): icono_cat}
        for sub in lista:
            icono[(cat, sub)] = icono_cat
        # las viejas conservan el suyo por si alguna sobrevive
        for s in c.get("subcategories") or []:
            icono.setdefault((cat, s["id"]), s.get("icon") or icono_cat)

        muestras = collections.defaultdict(list) if args.muestras else None
        n1, conteo = repartir(data["products"], cat, f, icono, args.dry_run, viejas, muestras)
        n2, conteo_oc = (0, collections.Counter())
        if ocultas:
            n2, conteo_oc = repartir(ocultas["productos"], cat, f, icono, args.dry_run, viejas)
        total = sum(conteo.values())
        print(f"### {cat}{' (' + ', '.join(viejas) + ')' if viejas else ''}: catálogo {total} fichas ({n1} cambian), ocultas {sum(conteo_oc.values())} ({n2} cambian)")
        for sub in lista + [None]:
            if conteo[sub] or conteo_oc[sub]:
                print(f"   {conteo[sub]:6d} {conteo_oc[sub]:6d}  {sub}")
                for m in (muestras or {}).get(sub, []):
                    print(f"                    {m}")
        sobran = [s for s in conteo if s and s not in lista]
        if sobran:
            print("   FUERA DE LA LISTA:", sobran)

        # Lista nueva de subcategorías: las finas en orden, y las viejas
        # solo si les queda alguna ficha visible.
        # Cuántas fichas quedan en cada subcategoría vieja tras el reparto
        # (las que no se tocaron siguen contando).
        quedan = collections.Counter(p.get("subcategory") for p in data["products"] if p.get("category") == cat)
        if not args.dry_run:
            pass
        else:
            for k, v in conteo.items():
                quedan[k] += v
            for v_ in (viejas or []):
                quedan[v_] = 0 if viejas else quedan[v_]
        nuevas = [{"id": sub, "name": sub, "icon": icono_cat} for sub in lista if conteo[sub] or conteo_oc[sub]]
        ya = {n["id"] for n in nuevas}
        sobreviven = []
        for s_ in (c.get("subcategories") or []):
            if s_["id"] in ya:
                continue
            # Una subcategoría vieja sin fichas ya no tiene sentido en la
            # lista, sea de las que este reparto absorbió o no.
            if not quedan.get(s_["id"]):
                continue
            sobreviven.append(s_)
        if viejas is not None:
            # la lista fina se inserta donde estaba la primera vieja
            idx = next((i for i, s_ in enumerate(c.get("subcategories") or []) if s_["id"] in viejas), len(sobreviven))
            lista_final = sobreviven[:idx] + nuevas + sobreviven[idx:]
        else:
            lista_final = nuevas + sobreviven
        if not args.dry_run:
            c["subcategories"] = lista_final
        print(f"   subcategorías en data.categories: {len(nuevas)} finas + {len(sobreviven)} que siguen")

    if args.limpiar_vacias:
        usadas = collections.Counter((p.get("category"), p.get("subcategory")) for p in data["products"])
        # Las fichas de tiendas ocultas cuentan: al restaurarlas necesitan
        # su subcategoría en la lista (Libros entero está oculto hoy).
        for p in (ocultas or {}).get("productos", []):
            usadas[(p.get("category"), p.get("subcategory"))] += 1
        for c in data["categories"]:
            antes = len(c.get("subcategories") or [])
            c["subcategories"] = [s_ for s_ in (c.get("subcategories") or []) if usadas.get((c["id"], s_["id"]))]
            if len(c["subcategories"]) != antes:
                print(f"   {c['id']}: {antes - len(c['subcategories'])} subcategorías vacías fuera de la lista")
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
