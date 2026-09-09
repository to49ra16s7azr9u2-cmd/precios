#!/usr/bin/env python3
"""Guarda y reaplica los precios de una corrida, por url de oferta.

PARA QUÉ
--------
La corrida diaria tarda ~2 h y termina commiteando el catálogo entero. Si
mientras tanto alguien pushó a main, el rebase choca: los archivos de
data/cat son una sola línea de JSON cada uno, así que dos cambios en la
misma categoría NUNCA se pueden juntar solos, y el commit de precios se
pierde entero (pasó las tres corridas programadas que hubo).

Con esto la corrida no tiene que perderse: antes de publicar guarda los
precios que consiguió, y si el rebase choca, se parte del main de verdad y
se le vuelven a aplicar. Es un merge honesto y acotado, no un "gana el
mío": se identifica cada precio por la URL de su oferta, así que

  - un producto que main borró (una fusión, por ejemplo) NO vuelve,
  - una oferta que main quitó no se resucita,
  - un precio que main cambió a mano se pisa con el de la tienda, que es
    justo lo que la corrida fue a buscar.

USO
    python3 scripts/precios_de_ofertas.py --guardar /tmp/precios.json
    python3 scripts/precios_de_ofertas.py --aplicar /tmp/precios.json
    python3 scripts/precios_de_ofertas.py --aplicar /tmp/precios.json --dry-run
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog


# Lo que se guarda de cada oferta. El precio es lo que la corrida fue a
# buscar; el stock cambia con él y sin él la ficha diría "en stock" de algo
# que la tienda ya marcó agotado.
CAMPOS = ("price", "listPrice", "stock")


def ofertas_de(product):
    """Todas las ofertas del producto, incluidas las de las variantes."""
    for o in product.get("offers") or []:
        yield o
    for v in product.get("colorVariants") or []:
        for o in v.get("offers") or []:
            yield o
        if v.get("price") is not None and v.get("url"):
            yield v


def guardar(ruta):
    data = load_catalog()
    salida = {}
    n = 0
    ambiguas = 0
    for p in data["products"]:
        por_url = {}
        for o in ofertas_de(p):
            url = o.get("url")
            if not url or o.get("price") is None:
                continue
            valores = {c: o[c] for c in CAMPOS if o.get(c) is not None}
            if url in por_url and por_url[url] != valores:
                # La misma publicación anotada dos veces con precios
                # distintos (pasa en un par de productos fusionados por
                # color). No se sabe cuál es el bueno, así que no se guarda
                # ninguno en vez de reaplicar uno al azar sobre el otro.
                por_url[url] = None
                continue
            por_url[url] = valores
        limpio = {u: v for u, v in por_url.items() if v is not None}
        ambiguas += len(por_url) - len(limpio)
        n += len(limpio)
        if limpio:
            salida[p["id"]] = limpio
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False)
    os.replace(tmp, ruta)
    print(f"Guardados {n:,} precios de {len(salida):,} productos en {ruta}")
    if ambiguas:
        print(f"  ({ambiguas} urls con dos precios distintos en la misma ficha, "
              "no se guardan)")


def aplicar(ruta, dry_run=False):
    with open(ruta, encoding="utf-8") as f:
        guardados = json.load(f)
    data = load_catalog()
    aplicados = iguales = 0
    productos_tocados = set()
    for p in data["products"]:
        por_url = guardados.get(p["id"])
        if not por_url:
            continue
        for o in ofertas_de(p):
            valores = por_url.get(o.get("url"))
            if not valores:
                continue
            if all(o.get(c) == v for c, v in valores.items()):
                iguales += 1
                continue
            o.update(valores)
            aplicados += 1
            productos_tocados.add(p["id"])
    faltan = len(guardados) - sum(1 for p in data["products"] if p["id"] in guardados)
    print(f"Precios reaplicados: {aplicados:,} en {len(productos_tocados):,} productos "
          f"({iguales:,} ya estaban igual)")
    print(f"Productos del archivo que ya no están en el catálogo: {faltan:,} "
          "(no se resucitan)")
    if dry_run:
        print("(--dry-run: no se escribió nada)")
        return
    if aplicados:
        save_catalog(data)
        print("Catálogo guardado.")


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--guardar", metavar="ARCHIVO")
    g.add_argument("--aplicar", metavar="ARCHIVO")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.guardar:
        guardar(args.guardar)
    else:
        aplicar(args.aplicar, args.dry_run)


if __name__ == "__main__":
    main()
