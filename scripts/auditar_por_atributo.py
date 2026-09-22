#!/usr/bin/env python3
"""Deja que la ficha técnica opine sobre la subcategoría, sin reglas a mano.

LA IDEA
-------
rescatar_por_spec.py buscaba un patrón escrito a mano dentro del valor de una
spec. Funcionó, pero hay que escribir cada caso. Esto es lo mismo generalizado:
NINGÚN par se escribe a mano, todos se aprenden del catálogo.

Un par (etiqueta, valor) de la ficha técnica es una afirmación de la tienda
sobre el producto: «Consola = Nintendo Switch», «Tamaño de Colchón = King
Size», «Tipo de Herramienta = Brocas y Juego de Dados». Si dentro de una
categoría casi todas las fichas que traen ese par están en la misma
subcategoría, el par manda sobre esa subcategoría. Y entonces las pocas que
traen el par y están en otra parte son sospechosas.

Es el mismo razonamiento de auditar_por_dominio.py, con el dato que pone la
tienda en vez del que pone Mercado Libre, y sirve para las 106,460 fichas que
traen ficha técnica, vengan de donde vengan.

POR QUÉ NO SE DESBOCA
---------------------
Tres frenos, y los tres se miden, no se suponen:
  * el par tiene que aparecer en --min-fichas fichas de esa categoría;
  * de ésas, --acuerdo o más tienen que coincidir en una subcategoría;
  * el valor tiene que decir algo: los "0", "N/A", "No aplica", "Sí"/"No" y
    los valores larguísimos (descripciones disfrazadas de spec) se tiran;
  * y la etiqueta tiene que PARTIR la categoría, es decir mandar a dos
    subcategorías distintas según el valor. Sin esto se cuela «material =
    plástico -> Consumibles» en Impresoras, que no dice que la ficha sea un
    cartucho: dice que los cartuchos son de plástico.
El mandato vale sólo DENTRO de su categoría: «Capacidad = 1 TB» manda en
Almacenamiento y no tiene nada que decir en Herramientas.

SÓLO SACA DEL BALDE
-------------------
Por omisión sólo se propone un destino que sea el REFINAMIENTO del balde donde
está la ficha: «Relojes» -> «Relojes para hombre», «Sábanas» -> «Sábanas queen
size». Es una prueba de forma, sin listas a mano, y sale de mirar en qué acierta
y en qué falla el método.

Acierta cuando la subcategoría de hoy es un balde genérico al que le falta
justo el dato que trae la ficha técnica. Falla cuando la subcategoría de hoy
mide OTRO eje: un Galaxy S22 reacondicionado trae «sistema operativo =
android», pero está en «Reacondicionados» a propósito y ahí se queda; un
control de Xbox trae «consola = Xbox» y no por eso es un juego. Pedir que el
destino empiece con el nombre del balde deja pasar lo primero y frena lo
segundo. Con --todo-destino se ve todo, para revisar a mano.

USO
---
    python3 scripts/auditar_por_atributo.py --mandato
    python3 scripts/auditar_por_atributo.py --salida /tmp/mover.json
    python3 scripts/auditar_por_atributo.py --categoria Videojuegos --acuerdo 0.95
"""
import argparse
import collections
import io
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog  # noqa: E402

# Valores que no dicen nada del producto.
VACIO = re.compile(r"^(0|no|si|s[ií]|n/?a|na|ninguno|no aplica|otro|otros|varios|"
                   r"por definir|sin especificar|-+|\.+)$")
# Etiquetas que describen el envoltorio, no el producto.
ETIQUETAS_FUERA = {
    "garantia con proveedor", "contenido del empaque", "modelo", "color",
    "peso", "dimensiones (l x al x an)", "marca", "sku", "codigo",
}
LARGO_MAX = 40   # un valor más largo que esto es una descripción, no un atributo


def T(s):
    s = unicodedata.normalize("NFKD", (s or "").strip().lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def pares_de(p):
    """{(etiqueta, valor) normalizados} que valen la pena mirar."""
    out = set()
    for s in (p.get("specs") or []):
        etq, val = T(s.get("label")), T(str(s.get("value")))
        if not etq or not val or etq in ETIQUETAS_FUERA:
            continue
        if len(val) > LARGO_MAX or VACIO.match(val):
            continue
        out.add((etq, val))
    return out


def mandatos(products, min_fichas, acuerdo):
    """{(categoría, etiqueta, valor): (subcategoría, acuerdos, total)}"""
    por_par = collections.defaultdict(collections.Counter)
    for p in products:
        cat, sub = p.get("category"), p.get("subcategory")
        if not cat or not sub:
            continue
        for etq, val in pares_de(p):
            por_par[(cat, etq, val)][sub] += 1
    crudos = {}
    for clave, c in por_par.items():
        total = sum(c.values())
        if total < min_fichas:
            continue
        sub, n = c.most_common(1)[0]
        if n / total >= acuerdo:
            crudos[clave] = (sub, n, total)

    # Una etiqueta sólo manda si PARTE la categoría: si «material» apunta a
    # Consumibles y a nada más, no está distinguiendo impresoras de cartuchos,
    # está reflejando que los cartuchos son de plástico. «consola», en cambio,
    # manda a Juegos Xbox con un valor y a Juegos PS5 con otro: eso sí parte.
    destinos = collections.defaultdict(set)
    for (cat, etq, _val), (sub, _n, _t) in crudos.items():
        destinos[(cat, etq)].add(sub)
    return {k: v for k, v in crudos.items() if len(destinos[(k[0], k[1])]) >= 2}


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--min-fichas", type=int, default=25)
    ap.add_argument("--acuerdo", type=float, default=0.90)
    ap.add_argument("--min-grupo", type=int, default=4)
    ap.add_argument("--categoria", help="mirar sólo esta categoría")
    ap.add_argument("--todo-destino", dest="solo_refinamiento", action="store_false",
                    help="admitir cualquier destino, no sólo el refinamiento del balde")
    ap.add_argument("--mandato", action="store_true", help="listar los pares que mandan")
    ap.add_argument("--salida", help="JSON de movimientos para aplicar_movimientos.py")
    ap.add_argument("--limite", type=int, default=45)
    args = ap.parse_args()

    data = load_catalog()
    productos = [p for p in data["products"]
                 if not args.categoria or p.get("category") == args.categoria]
    manda = mandatos(productos, args.min_fichas, args.acuerdo)
    print(f"pares (etiqueta, valor) con mandato: {len(manda):,}   "
          f"(>={args.min_fichas} fichas, >={args.acuerdo:.0%} de acuerdo)\n")

    if args.mandato:
        for (cat, etq, val), (sub, n, total) in sorted(
                manda.items(), key=lambda kv: -kv[1][2])[:args.limite]:
            print(f"  {total:>5}  {cat} · «{etq}» = «{val[:24]}»  -> {sub}  ({n/total:.0%})")
        return 0

    # Una ficha se acusa sólo si TODOS sus pares con mandato apuntan al mismo
    # destino: si se contradicen entre ellos, el atributo no está decidiendo.
    grupos = collections.defaultdict(list)
    nombres = {}
    for p in productos:
        cat, sub = p.get("category"), p.get("subcategory")
        if not cat or not sub:
            continue
        destinos = {manda[(cat, e, v)][0] for e, v in pares_de(p)
                    if (cat, e, v) in manda}
        if len(destinos) != 1:
            continue
        destino = destinos.pop()
        if destino == sub:
            continue
        if args.solo_refinamiento and not T(destino).startswith(T(sub) + " "):
            continue
        grupos[f"{cat} | {sub} | {cat} | {destino}"].append(p["id"])
        nombres[p["id"]] = p["name"]

    orden = sorted(grupos.items(), key=lambda kv: -len(kv[1]))
    total = sum(len(v) for _k, v in orden if len(v) >= args.min_grupo)
    print(f"fichas que la ficha técnica contradice (grupos de {args.min_grupo}+): {total:,}\n")
    for clave, ids in orden[:args.limite]:
        if len(ids) < args.min_grupo:
            break
        print(f"  {len(ids):>5}  {clave}")
        for pid in ids[:2]:
            print(f"           {nombres[pid][:68]}")

    if args.salida:
        salida = {k: v for k, v in grupos.items() if len(v) >= args.min_grupo}
        with io.open(args.salida, "w", encoding="utf-8") as f:
            json.dump(salida, f, ensure_ascii=False, indent=1)
        print(f"\n-> {args.salida} ({len(salida)} grupos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
