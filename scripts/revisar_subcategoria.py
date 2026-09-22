#!/usr/bin/env python3
"""El expediente de una subcategoría: todas las señales en una pantalla.

PARA QUÉ
--------
Recorrer las 996 subcategorías una por una, en orden, hasta la última. Cada
señal de las que ya existen (la cabecera del título, el dominio de Mercado
Libre, el bayes, el precio, el rol) vive en su propio script y hay que
correrlos por separado y cruzar la salida a mano. Esto los junta para UNA
subcategoría, que es la unidad en la que se revisa.

QUÉ MIRA
--------
  1. Tamaño, peso en su categoría, rol y familia.
  2. De qué está hecha: las cabeceras de título más frecuentes. Si una
     cabecera nombra a OTRA subcategoría de la misma categoría, se marca.
  3. El dominio de Mercado Libre dominante y las fichas cuyo dominio manda
     a otro lado.
  4. Lo que el bayes explica mejor con otra subcategoría.
  5. Precio: mediana, y las fichas por debajo del 15% de la mediana, que casi
     siempre son un accesorio o una pieza colada entre los productos. Es lo
     que vio el usuario en Baterías portátiles: un módulo de $19 encabezando
     la lista al ordenar por precio.
  6. Sustantivos de accesorio en una subcategoría de rol producto.

Cada hallazgo sale con su destino propuesto y una confianza, y --salida
escribe el JSON que come aplicar_movimientos.py, agrupado por destino, para
aplicar lo revisado.

EL RECORRIDO
------------
--lista imprime todas las subcategorías en el orden del recorrido (por
categoría y tamaño) con una marca de las ya revisadas. La revisión se anota
en data/revision-subcategorias.json con --hecha, y así el recorrido se
puede retomar en otra sesión por donde iba.

USO
---
    python3 scripts/revisar_subcategoria.py --lista
    python3 scripts/revisar_subcategoria.py "Muebles" "Sillas de oficina"
    python3 scripts/revisar_subcategoria.py "Muebles" "Sillas de oficina" --salida /tmp/m.json
    python3 scripts/revisar_subcategoria.py "Muebles" "Sillas de oficina" --hecha "nota"
"""
import argparse
import collections
import datetime
import io
import json
import os
import re
import statistics
import sys
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import load_catalog  # noqa: E402
from roles_subcategorias import rol_de, PRODUCTO  # noqa: E402
from familias_subcategorias import agrupar  # noqa: E402
from proponer_corte import cabecera, token_propio, T  # noqa: E402

RAIZ = os.path.dirname(AQUI)
BITACORA = os.path.join(RAIZ, "data", "revision-subcategorias.json")
DOMINIOS = os.path.join(RAIZ, "data", "ml-dominios-producto.json")

# Sustantivos que, abriendo el título en una subcategoría de producto, casi
# siempre son un accesorio o una pieza y no el producto.
ACCESORIO = re.compile(
    r"^(?:\S+ ){0,2}(funda|estuche|cable|cargador|adaptador|soporte|base|repuesto|"
    r"reemplazo|refaccion|kit de (limpieza|reparacion|mantenimiento)|filtro|"
    r"protector|mica|correa|bolsa|tapa|cubierta|pano|panos|cepillo|bateria de repuesto|"
    r"control remoto|pieza|piezas|manual|tornillo|tornillos|junta|empaque|"
    r"organizador|gancho|clip|pegatina|sticker|calcomania)\b")
PISO_PRECIO = 0.15      # por debajo de esta fracción de la mediana, sospechoso
MARGEN_BAYES = 12.0


def precio_min(p):
    ps = [o.get("price") for o in (p.get("offers") or []) if isinstance(o.get("price"), (int, float)) and o.get("price") > 0]
    return min(ps) if ps else None


def cargar_bitacora():
    if os.path.exists(BITACORA):
        with io.open(BITACORA, encoding="utf-8") as f:
            return json.load(f)
    return {}


def orden_recorrido(data, cuenta):
    """[(categoría, subcategoría)] en el orden del recorrido: por categoría,
    y dentro de cada una de mayor a menor."""
    salida = []
    for c in data["categories"]:
        subs = [s["id"] for s in (c.get("subcategories") or [])]
        subs.sort(key=lambda s: -cuenta[(c["id"], s)])
        salida.extend((c["id"], s) for s in subs)
    return salida


def dominios_por_ficha(products):
    if not os.path.exists(DOMINIOS):
        return {}
    from dominios_ml import ids_del_catalogo
    with io.open(DOMINIOS, encoding="utf-8") as f:
        dom = json.load(f)
    return {pid: dom[m] for pid, m in ids_del_catalogo(products).items() if dom.get(m)}


def expediente(data, cat, sub, marcas, args):
    products = data["products"]
    items = [p for p in products if p.get("category") == cat and p.get("subcategory") == sub]
    en_cat = [p for p in products if p.get("category") == cat]
    subs_cat = [s["id"] for s in next(c for c in data["categories"] if c["id"] == cat)["subcategories"]]
    cuenta_cat = collections.Counter(p.get("subcategory") for p in en_cat)
    rol = rol_de(cat, sub)
    fam = next((f for f, ms in agrupar(cat, subs_cat, cuenta_cat) if sub in ms), None)
    hallazgos = collections.defaultdict(list)   # destino -> [(conf, id, nombre, señal)]

    print(f"══ {cat} / {sub}")
    print(f"   {len(items):,} fichas ({len(items)/max(len(en_cat),1):.0%} de {cat}) · rol {rol} · familia {fam or '—'}")
    if not items:
        return hallazgos

    # 2. cabeceras
    propio = token_propio(data).get(cat, {})
    mias = {w for w in re.split(r"[^a-z0-9]+", T(sub)) if len(w) >= 4}
    # Si el título nombra a la CATEGORÍA, la cabecera no decide: «Teléfono
    # celular Samsung Galaxy A16» abre con «teléfono», que dentro de Celulares
    # nombra a «Teléfonos fijos», pero el «celular» de al lado dice que no.
    # Sin este freno, Android proponía mandar 140 smartphones a fijos.
    de_cat = {w[:-1] if w.endswith("s") else w
              for w in re.split(r"[^a-z0-9]+", T(cat)) if len(w) >= 5}
    rx_cat = re.compile(r"\b(" + "|".join(re.escape(w) for w in de_cat) + r")") if de_cat else None
    cab = collections.Counter()
    cab_de = {}
    for p in items:
        h = cabecera(p["name"], p.get("brand"), marcas)
        if h:
            cab[h] += 1
            cab_de[p["id"]] = h
    print("   cabeceras:", ", ".join(f"{h} {n}" for h, n in cab.most_common(10)))
    for h, n in cab.most_common(40):
        destino = propio.get(h)
        if destino and destino != sub and h not in mias and n >= 2:
            for p in items:
                if cab_de.get(p["id"]) == h:
                    if rx_cat and rx_cat.search(T(p["name"])):
                        continue
                    hallazgos[(cat, destino)].append(("cabecera", p["id"], p["name"]))

    # 3. dominios
    doms = args.doms
    if doms:
        cd = collections.Counter(doms.get(p["id"]) for p in items if doms.get(p["id"]))
        if cd:
            dm, n = cd.most_common(1)[0]
            print(f"   dominio ML: {dm} {n}/{sum(cd.values())}" +
                  (f"; otros: {', '.join(f'{k} {v}' for k, v in cd.most_common(4)[1:])}" if len(cd) > 1 else ""))
            # dónde cae cada dominio en el resto del catálogo
            mandato = collections.defaultdict(collections.Counter)
            for p in products:
                x = doms.get(p["id"])
                if x and p.get("category") == cat and p.get("subcategory"):
                    mandato[x][p["subcategory"]] += 1
            for p in items:
                x = doms.get(p["id"])
                if not x or x == dm:
                    continue
                c = mandato[x]
                tot = sum(c.values())
                if tot >= 8:
                    dest, k = c.most_common(1)[0]
                    if dest != sub and k / tot >= 0.8:
                        hallazgos[(cat, dest)].append(("dominio " + x, p["id"], p["name"]))

    # 4. bayes
    if args.modelo is not None:
        for p in items:
            puntos = args.modelo.puntajes(p["name"])
            if len(puntos) < 2:
                continue
            mejor_lp, mejor = puntos[0]
            suyo = next((lp for lp, s in puntos if s == sub), None)
            if suyo is not None and mejor != sub and mejor_lp - suyo >= MARGEN_BAYES:
                hallazgos[(cat, mejor)].append((f"bayes +{mejor_lp - suyo:.0f}", p["id"], p["name"]))

    # 5. precio
    precios = [(precio_min(p), p) for p in items]
    precios = [(pr, p) for pr, p in precios if pr]
    if len(precios) >= 8:
        med = statistics.median(pr for pr, _p in precios)
        bajos = [(pr, p) for pr, p in precios if pr < med * PISO_PRECIO]
        precios.sort(key=lambda t: t[0])
        print(f"   precio: mediana ${med:,.0f} · más baratos: " +
              " | ".join(f"${pr:,.0f} {p['name'][:28]}" for pr, p in precios[:3]))
        if bajos:
            print(f"   por debajo del {PISO_PRECIO:.0%} de la mediana: {len(bajos)}")
            for pr, p in bajos[:6]:
                print(f"       ${pr:>8,.0f}  {p['name'][:64]}")

    # 6. accesorio en rol producto
    if rol == PRODUCTO:
        acc = [p for p in items if ACCESORIO.search(T(p["name"]))]
        if acc:
            print(f"   abren con sustantivo de accesorio: {len(acc)}")
            for p in acc[:6]:
                print(f"       {p['name'][:70]}")

    # resumen de hallazgos
    if hallazgos:
        print("   ── propuestas:")
        for (c2, s2), lst in sorted(hallazgos.items(), key=lambda kv: -len(kv[1])):
            señales = collections.Counter(x[0].split()[0] for x in lst)
            print(f"   {len(lst):>4}  -> {c2} / {s2}   [{', '.join(f'{k} {v}' for k, v in señales.items())}]")
            for _s, _i, nombre in lst[:args.muestras]:
                print(f"             {nombre[:66]}")
    else:
        print("   sin propuestas")
    return hallazgos


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("categoria", nargs="?")
    ap.add_argument("subcategoria", nargs="?")
    ap.add_argument("--lista", action="store_true", help="el orden del recorrido, con las ya revisadas marcadas")
    ap.add_argument("--siguiente", type=int, default=0, help="expedientes de las N siguientes sin revisar")
    ap.add_argument("--salida", help="JSON de movimientos con las propuestas")
    ap.add_argument("--hecha", metavar="NOTA", help="anotar la subcategoría como revisada")
    ap.add_argument("--sin-bayes", action="store_true")
    ap.add_argument("--muestras", type=int, default=2)
    args = ap.parse_args()

    data = load_catalog()
    cuenta = collections.Counter((p.get("category"), p.get("subcategory")) for p in data["products"])
    bit = cargar_bitacora()
    orden = orden_recorrido(data, cuenta)

    if args.lista:
        hechas = 0
        for i, (c, s) in enumerate(orden, 1):
            k = f"{c} | {s}"
            marca = "✓" if k in bit else " "
            hechas += k in bit
            print(f"{marca} {i:>4}  {cuenta[(c, s)]:>6,}  {c} / {s}")
        print(f"\n{hechas} revisadas de {len(orden)}")
        return 0

    if args.hecha is not None:
        if not (args.categoria and args.subcategoria):
            print("--hecha necesita categoría y subcategoría", file=sys.stderr)
            return 1
        bit[f"{args.categoria} | {args.subcategoria}"] = {
            "fecha": datetime.date.today().isoformat(), "nota": args.hecha}
        with io.open(BITACORA, "w", encoding="utf-8") as f:
            json.dump(bit, f, ensure_ascii=False, indent=1)
        print(f"anotada. {len(bit)} revisadas de {len(orden)}")
        return 0

    marcas = {T(p["brand"]) for p in data["products"] if p.get("brand")}
    marcas |= {w for m in list(marcas) for w in m.split() if len(w) > 3}
    args.doms = dominios_por_ficha(data["products"])
    args.modelo = None

    objetivo = []
    if args.siguiente:
        objetivo = [(c, s) for c, s in orden if f"{c} | {s}" not in bit][:args.siguiente]
    elif args.categoria and args.subcategoria:
        objetivo = [(args.categoria, args.subcategoria)]
    else:
        ap.print_help()
        return 1

    if not args.sin_bayes:
        import aprender_subcategoria as apr
        modelos = apr.construir(data["products"])

    todos = collections.defaultdict(list)
    for c, s in objetivo:
        args.modelo = None if args.sin_bayes else (modelos.get(c, (None,))[0])
        h = expediente(data, c, s, marcas, args)
        for (c2, s2), lst in h.items():
            todos[f"{c} | {s} | {c2} | {s2}"].extend(i for _sig, i, _n in lst)
        print()
    if args.salida:
        with io.open(args.salida, "w", encoding="utf-8") as f:
            json.dump({k: sorted(set(v)) for k, v in todos.items()}, f, ensure_ascii=False, indent=0)
        print(f"-> {args.salida} ({len(todos)} grupos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
