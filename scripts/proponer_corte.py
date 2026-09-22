#!/usr/bin/env python3
"""Propone solo por dónde partir los cajones grandes del catálogo.

POR QUÉ
-------
Los cortes de «Componentes», «Muebles de cocina» y «Plomería» salieron bien,
pero los elegí yo mirando la lista de subcategorías grandes, y las palabras
del corte las escribí a mano. Eso no escala y depende de que a alguien se le
ocurra mirar. Esto lo hace el catálogo.

CÓMO
----
Lo que kakaku separa es el TIPO de producto, y en español el tipo se dice al
principio del título: «Gabinete Pc Gamer Thermaltake», «Fuente de Poder
Cooler Master», «Cocina Integral Kessa». Así que de cada ficha del cajón se
saca su sustantivo de cabecera —la primera palabra con contenido, ya quitada
la marca— y se cuenta.

Si un cajón de 2,000 fichas resulta que son 700 «gabinete», 400 «fuente» y
300 «ventilador», ese cajón tiene tres productos adentro y hay que partirlo.
Si son 2,000 fichas con 800 cabeceras distintas, ninguna con peso, entonces
es un cajón legítimamente variado y se deja en paz.

QUÉ NO HACE
-----------
No parte por marca. La marca se quita del título antes de mirar (viene en la
ficha) y además se descartan las cabeceras que coinciden con una marca
conocida del catálogo: «Truper» no es un tipo de producto.

Tampoco aplica nada. Escribe la propuesta y ahí para: el nombre de la
subcategoría nueva y la regla que la llena los decide una persona leyendo
esto, que es donde el juicio sí hace falta.

USO
---
    python3 scripts/proponer_corte.py
    python3 scripts/proponer_corte.py --min-cajon 400 --min-grupo 60
    python3 scripts/proponer_corte.py --categoria Herramientas --detalle
"""
import argparse
import collections
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog  # noqa: E402

# Palabras que pueden abrir un título sin nombrar el producto.
ARRANQUES = {
    "nuevo", "nueva", "original", "gran", "super", "mini", "max", "pro",
    "premium", "profesional", "kit", "set", "juego", "paquete", "pack",
    "combo", "par", "caja", "bolsa", "lote", "oferta", "envio", "gratis",
    "venta", "internacional", "importado", "genuino", "universal", "alta",
    "gama", "linea", "serie", "modelo", "tipo", "marca", "color", "negro",
    "blanco", "azul", "rojo", "gris", "verde", "rosa", "plata", "dorado",
    "para", "con", "sin", "por", "del", "las", "los", "una", "uno", "the",
    "and", "de", "el", "la", "y", "a", "en", "x", "pza", "pzas", "piezas",
    "pieza", "unidad", "unidades", "grande", "chico", "pequeno", "mediano",
}
# Sufijos de plural que se recortan para que «gabinetes» y «gabinete» cuenten
# juntos. Es burdo a propósito: sólo tiene que agrupar, no conjugar.
def _sing(w):
    if len(w) > 5 and w.endswith("es"):
        return w[:-2]
    if len(w) > 4 and w.endswith("s"):
        return w[:-1]
    return w


def T(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


# Una medida no es un tipo de producto. «256gb», «1500w», «4k», «27pulgadas»
# abrían títulos enteros de Celulares y Monitores y salían propuestos como si
# fueran productos distintos.
MEDIDA = re.compile(r"^\d|\d(gb|tb|mb|kg|ml|cm|mm|pulg|w|v|hz|mah|lt|l)$|^\d+[a-z]{0,4}$")


def cabecera(nombre, marca, marcas):
    """La primera palabra con contenido del título, sin marca. None si no hay."""
    t = T(nombre)
    if marca:
        t = t.replace(T(marca), " ")
    for w in re.split(r"[^a-z0-9]+", t):
        if len(w) < 4 or w in ARRANQUES:
            continue
        if any(ch.isdigit() for ch in w) or MEDIDA.match(w):
            continue
        if w in marcas:          # «Truper» no es un tipo de producto
            continue
        return _sing(w)
    return None


def token_propio(data):
    """{categoría: {palabra: subcategoría}} con las palabras que nombran a UNA
    sola subcategoría de esa categoría.

    «cama» nombra sólo a «Camas» dentro de Mascotas, así que una ficha que
    empieza con «cama» y está en «Casas para mascotas» está en el cajón de al
    lado. «perro», en cambio, aparece en ocho subcategorías de Mascotas y no
    dice nada: esas se descartan.
    """
    out = {}
    for c in data["categories"]:
        cuenta = collections.Counter()
        dueño = {}
        for sub in (c.get("subcategories") or []):
            for w in re.split(r"[^a-z0-9]+", T(sub["id"])):
                if len(w) < 4 or w in ARRANQUES:
                    continue
                w = _sing(w)
                cuenta[w] += 1
                dueño[w] = sub["id"]
        out[c["id"]] = {w: dueño[w] for w, n in cuenta.items() if n == 1}
    return out


def misubicadas(data, marcas, min_grupo, techo):
    """Fichas cuya cabecera nombra a otra subcategoría de su propia categoría.

    La cabecera sola no alcanza, y el porqué se ve en Monitores: «Monitor
    Curvo de 27"» en «Gaming» tiene por cabecera «monitor», que dentro de
    Monitores nombra sólo a «Monitores 4K y profesionales», y de ahí salían
    1,836 monitores gamer acusados de estar mal. Pero «monitor» es el
    sustantivo de FAMILIA: lo son todos los de la categoría, así que no
    distingue nada.

    El freno es pedir que la cabecera sea MINORITARIA en su categoría. «bomba»
    es el 1% de Herramientas y por eso dice algo cuando aparece en Plomería;
    «monitor» es el 70% de Monitores y no dice nada. El umbral es --techo.

    (Se probó antes cruzarlo con el bayes de aprender_subcategoria.py y no
    sirve: ese modelo aprende de las etiquetas que esto audita, así que
    repite el statu quo y ni siquiera considera un destino con pocos
    ejemplos. Dio cero en todo el catálogo.)
    """
    propio = token_propio(data)
    # Cuán común es cada cabecera dentro de su categoría.
    por_cat = collections.defaultdict(collections.Counter)
    cabezas = {}
    for p in data["products"]:
        cat = p.get("category")
        if not cat:
            continue
        h = cabecera(p["name"], p.get("brand"), marcas)
        cabezas[p["id"]] = h
        if h:
            por_cat[cat][h] += 1
    grupos = collections.defaultdict(list)
    muestras = collections.defaultdict(list)
    for p in data["products"]:
        cat, sub = p.get("category"), p.get("subcategory")
        if not cat or not sub:
            continue
        h = cabezas.get(p["id"])
        if not h:
            continue
        cuantas = sum(por_cat[cat].values())
        if not cuantas or por_cat[cat][h] / cuantas > techo:
            continue
        destino = propio.get(cat, {}).get(h)
        if not destino or destino == sub:
            continue
        # Si la cabecera también nombra al cajón donde está, no hay conflicto.
        if h in {_sing(w) for w in re.split(r"[^a-z0-9]+", T(sub)) if len(w) >= 4}:
            continue
        k = f"{cat} | {sub} | {cat} | {destino}"
        grupos[k].append(p["id"])
        if len(muestras[k]) < 2:
            muestras[k].append(p["name"][:66])
    return ({k: v for k, v in grupos.items() if len(v) >= min_grupo}, muestras)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--min-cajon", type=int, default=300,
                    help="fichas mínimas para mirar un cajón (%(default)s)")
    ap.add_argument("--min-grupo", type=int, default=50,
                    help="fichas mínimas de una cabecera para proponerla (%(default)s)")
    ap.add_argument("--min-grupos", type=int, default=2,
                    help="cabeceras que tienen que alcanzar el mínimo (%(default)s)")
    ap.add_argument("--categoria")
    ap.add_argument("--detalle", action="store_true", help="ejemplos de cada grupo")
    ap.add_argument("--limite", type=int, default=30)
    ap.add_argument("--misubicadas", action="store_true",
                    help="fichas cuya cabecera nombra a otra subcategoría que YA existe")
    ap.add_argument("--techo", type=float, default=0.05,
                    help="proporción máxima de la cabecera dentro de su categoría "
                         "para que diga algo (%(default)s)")
    ap.add_argument("--salida", help="con --misubicadas, JSON para aplicar_movimientos.py")
    args = ap.parse_args()

    data = load_catalog()
    marcas = {T(p["brand"]) for p in data["products"] if p.get("brand")}
    marcas |= {w for m in list(marcas) for w in m.split() if len(w) > 3}
    # Los nombres de las subcategorías que ya existen no son un corte nuevo.
    propias = collections.defaultdict(set)
    for c in data["categories"]:
        for s in (c.get("subcategories") or []):
            for w in re.split(r"[^a-z0-9]+", T(s["id"])):
                if len(w) >= 4:
                    propias[c["id"]].add(_sing(w))

    if args.misubicadas:
        grupos, muestras = misubicadas(data, marcas, args.min_grupo, args.techo)
        total = sum(len(v) for v in grupos.values())
        print(f"fichas cuya cabecera minoritaria (<= {args.techo:.0%} de su "
              f"categoría) nombra a otra subcategoría existente "
              f"(grupos de {args.min_grupo}+): {total:,}\n")
        for k, ids in sorted(grupos.items(), key=lambda kv: -len(kv[1]))[:args.limite]:
            print(f"  {len(ids):>5}  {k}")
            for m in muestras[k]:
                print(f"           {m}")
        if args.salida:
            import json
            with open(args.salida, "w", encoding="utf-8") as f:
                json.dump(grupos, f, ensure_ascii=False, indent=0)
            print(f"\n-> {args.salida} ({len(grupos)} grupos)")
        return 0

    cajones = collections.defaultdict(list)
    for p in data["products"]:
        cat, sub = p.get("category"), p.get("subcategory")
        if sub and (not args.categoria or cat == args.categoria):
            cajones[(cat, sub)].append(p)

    propuestas = []
    for (cat, sub), items in cajones.items():
        if len(items) < args.min_cajon:
            continue
        c = collections.Counter()
        ejemplos = collections.defaultdict(list)
        for p in items:
            h = cabecera(p["name"], p.get("brand"), marcas)
            if not h:
                continue
            c[h] += 1
            if len(ejemplos[h]) < 2:
                ejemplos[h].append(p["name"][:62])
        # Una cabecera que ya nombra a ESTA subcategoría no es un corte: en
        # «Sábanas king size» casi todas las fichas empiezan con «sábanas».
        mias = {w for w in re.split(r"[^a-z0-9]+", T(sub) + " " + T(cat)) if len(w) >= 4}
        mias = {_sing(w) for w in mias}
        grupos = [(h, n) for h, n in c.most_common()
                  if n >= args.min_grupo and h not in mias]
        if len(grupos) < args.min_grupos:
            continue
        cubre = sum(n for _h, n in grupos) / len(items)
        propuestas.append((cubre * sum(n for _h, n in grupos), cubre, cat, sub,
                           len(items), grupos, ejemplos))

    propuestas.sort(reverse=True)
    print(f"cajones de {args.min_cajon}+ fichas con {args.min_grupos}+ tipos "
          f"de {args.min_grupo}+ adentro: {len(propuestas)}\n")
    for _peso, cubre, cat, sub, n, grupos, ejemplos in propuestas[:args.limite]:
        nuevo = [h for h, _k in grupos if h not in propias[cat]]
        marca_nuevo = "  *" if nuevo else ""
        print(f"  {n:>6,}  {cat} / {sub}   ({cubre:.0%} del cajón en {len(grupos)} tipos){marca_nuevo}")
        for h, k in grupos[:8]:
            señal = " (ya es subcategoría)" if h in propias[cat] else ""
            print(f"          {k:>5}  {h}{señal}")
            if args.detalle:
                for e in ejemplos[h]:
                    print(f"                   {e}")
    print("\n  * = trae al menos un tipo que todavía no es subcategoría de esa categoría")
    return 0


if __name__ == "__main__":
    sys.exit(main())
