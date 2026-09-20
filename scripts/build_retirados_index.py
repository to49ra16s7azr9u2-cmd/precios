#!/usr/bin/env python3
"""Índice de las fichas que NO tienen página, para que el 404 sepa qué eran.

POR QUÉ
-------
El catálogo publica ficha solo cuando hay dos o más tiendas vendiendo: con
una sola no hay nada que comparar. Pero la url de una ficha que bajó del
mínimo ya está indexada, y quien llega desde Google se encontraba con un
"esta página no existe" genérico.

Escribir una página de despedida para cada una son 197 mil archivos HTML,
doce veces lo que hoy publica el sitio, y eso deshace justamente lo que se
ganó al publicar solo las fichas comparables. En vez de eso se escribe un
índice partido en trozos: el 404 mira la url, calcula qué trozo le toca,
baja ese trozo solo (unos 120 KB) y arma la página de despedida ahí mismo,
con el nombre del producto y el enlace a su categoría.

Los ids son "p" + un número corrido, así que el trozo se calcula sin
tablas: numero // TAMANO.
"""
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
from data_io import load_catalog  # noqa: E402

TAMANO = 2000
SALIDA = os.path.join(ROOT, "data", "retirados")
MIN_OFERTAS_PARA_PAGINA = 2
RX_ID = re.compile(r"^p(\d+)$")


def slugify(texto):
    from generate_seo_pages import slugify as _s
    return _s(texto)


def main():
    data = load_catalog()
    cats = [c["name"] for c in data["categories"]]
    idx_cat = {c["id"]: i for i, c in enumerate(data["categories"])}
    trozos = {}
    sin_numero = 0
    for p in data["products"]:
        if len(p.get("offers") or []) >= MIN_OFERTAS_PARA_PAGINA:
            continue
        m = RX_ID.match(p["id"])
        if not m:
            sin_numero += 1
            continue
        n = int(m.group(1)) // TAMANO
        # [nombre, índice de categoría, subcategoría]. La subcategoría va
        # con su nombre y no con un índice: no hay una lista global de
        # subcategorías y repetir el texto cuesta poco una vez comprimido.
        # El nombre va recortado: con 70 caracteres se reconoce el producto
        # ("Banco De Ejercicio Multifuncional Gimnasio Multiposiciones") y el
        # índice entero pesa un tercio de lo que pesaría con los nombres
        # completos, que en esta tienda llegan a 200 caracteres de relleno.
        nombre = (p.get("name") or "").strip()
        if len(nombre) > 70:
            nombre = nombre[:69].rstrip() + "…"
        trozos.setdefault(n, {})[p["id"]] = [
            nombre, idx_cat.get(p.get("category"), -1), p.get("subcategory") or ""
        ]

    os.makedirs(SALIDA, exist_ok=True)
    viejos = {f for f in os.listdir(SALIDA) if f.endswith(".json")}
    escritos = 0
    for n, mapa in trozos.items():
        ruta = os.path.join(SALIDA, f"{n}.json")
        nuevo = json.dumps(mapa, ensure_ascii=False, separators=(",", ":"))
        viejos.discard(f"{n}.json")
        if os.path.exists(ruta):
            with open(ruta, encoding="utf-8") as f:
                if f.read() == nuevo:
                    continue
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(nuevo)
        escritos += 1
    for sobra in viejos:
        os.remove(os.path.join(SALIDA, sobra))

    meta = {"tamano": TAMANO, "categorias": cats,
            "slugs": [slugify(c) for c in cats]}
    ruta_meta = os.path.join(SALIDA, "meta.json")
    with open(ruta_meta, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, separators=(",", ":"))

    total = sum(len(v) for v in trozos.values())
    peso = sum(os.path.getsize(os.path.join(SALIDA, f))
               for f in os.listdir(SALIDA)) / 1024 / 1024
    print(f"Fichas sin página indexadas: {total:,} en {len(trozos)} trozos "
          f"({peso:.1f} MB, {escritos} reescritos)")
    if sin_numero:
        print(f"  ids sin número (sin trozo): {sin_numero:,}")


if __name__ == "__main__":
    main()
