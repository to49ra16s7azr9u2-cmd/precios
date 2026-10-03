#!/usr/bin/env python3
"""Recorre TODO el árbol de categorías de Elektra y deja los productos en el
formato de captura de importar_captura_tienda.py.

POR QUÉ
-------
add_elektra_products.py y add_vtex_products.py importan sólo las categorías
que tienen un mapeo a mano (CATEGORY_MAP / ELEKTRA_MAP): ~69 mil ofertas. El
feed de Soicos del programa de Elektra (10219) trae ~199 mil, así que dos
tercios del catálogo de Elektra no estaban. Acá no se mapea nada a mano: se
recorren las 896 hojas del árbol con la misma API pública de catálogo que
autoriza el robots.txt de Elektra (`/api/catalog_system/pub/products/search
?fq=*`), y la categoría del sitio la decide después el clasificador por
título de importar_captura_tienda.py, igual que con Walmart.

El enlace de afiliado no hace falta en la captura: es siempre
ad.soicos.com/-5hYi?dl=<url de elektra.mx> y se pone al salir hacia la tienda
(afiliados.url_salida, urlSalida() en js/app.js). Se guarda la url de
elektra.mx tal cual, como las 69 mil ofertas que ya hay.

QUÉ QUEDA FUERA
---------------
Los departamentos «Alimentos y Bebidas» y «Servicios», las hojas de
medicamentos, comida y bebidas (soicos_a_captura.DEPARTAMENTOS_FUERA), los
nombres de servicios y garantías (JUNK_RE de add_elektra_products) y lo que
no tiene ningún vendedor con existencia.

LÍMITE DE LA API
----------------
VTEX no pagina más allá de _from=2500. Una hoja que llega a ese tope se
vuelve a pedir partida por rangos de precio (fq=P:[a TO b]).

USO
---
    python3 scripts/elektra_arbol_a_captura.py --salida /tmp/elektra-arbol.json
    python3 scripts/elektra_arbol_a_captura.py --salida /tmp/x.json --max-hojas 5   # prueba
    python3 scripts/elektra_arbol_a_captura.py --salida /tmp/elektra-arbol.json --continuar
        # sigue desde la última hoja guardada (el recorrido entero lleva ~5 h
        # y un reinicio del contenedor lo corta)
    python3 scripts/importar_captura_tienda.py /tmp/elektra-arbol.json --dry-run
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from add_elektra_products import JUNK_RE, PAGE_SIZE, vendedor_publicable  # noqa: E402
from importar_captura_tienda import id_de_url  # noqa: E402
from soicos_a_captura import ALCOHOL_TITULO, DEPARTAMENTOS_FUERA, _NO_BEBIDA  # noqa: E402

BASE = "https://www.elektra.mx/api/catalog_system/pub"
DEPTOS_FUERA = {"alimentos y bebidas", "servicios"}
TOPE_VTEX = 2500
RANGOS = [(0, 199), (200, 499), (500, 999), (1000, 1999), (2000, 3999), (4000, 7999),
          (8000, 14999), (15000, 29999), (30000, 999999)]
PAUSA = 0.25
# Se presenta como lo que es. Con el User-Agent de Chrome que usan los demás
# importadores, Elektra contesta 403 a estas consultas (03-oct-2026).
HEADERS = {"User-Agent": "ComparaMEX/1.0 (+https://comparamex.com; comparador de precios)",
           "Accept-Language": "es-MX,es;q=0.9"}


def fetch_json(url, reintentos=3):
    for intento in range(reintentos + 1):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=40) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            if intento == reintentos:
                return None
            time.sleep(1.5 * (intento + 1))


def hojas(arbol):
    out = []

    def bajar(n, ids, nombres):
        ids, nombres = ids + [str(n["id"])], nombres + [n["name"]]
        if n.get("children"):
            for c in n["children"]:
                bajar(c, ids, nombres)
        else:
            out.append(("/".join(ids), nombres))
    for n in arbol:
        bajar(n, [], [])
    return out


def pagina(path, frm, rango=None):
    q = f"fq=C:/{path}/"
    if rango:
        q += "&fq=" + urllib.parse.quote(f"P:[{rango[0]} TO {rango[1]}]")
    time.sleep(PAUSA)
    return fetch_json(f"{BASE}/products/search?{q}&_from={frm}&_to={frm + PAGE_SIZE - 1}") or []


def recorrer(path, rango=None):
    """(productos, llegó_al_tope)."""
    out, frm = [], 0
    while frm < TOPE_VTEX:
        lote = pagina(path, frm, rango)
        out += lote
        if len(lote) < PAGE_SIZE:
            return out, False
        frm += PAGE_SIZE
    return out, True


def item_de(p, nombres):
    nombre = (p.get("productName") or "").strip()
    url = p.get("link") or ""
    if not nombre or not url.startswith("https://www.elektra.mx/"):
        return None, "sin nombre o url"
    if JUNK_RE.search(nombre):
        return None, "servicio o garantía"
    if ALCOHOL_TITULO.search(nombre) and not _NO_BEBIDA.search(nombre):
        return None, "bebida alcohólica"
    items = p.get("items") or []
    vendedor = vendedor_publicable(items[0]) if items else None
    if not vendedor:
        return None, "sin existencia"
    co = vendedor["commertialOffer"]
    pid = id_de_url(url)
    if not pid:
        return None, "sin número en la url"
    it = {"store": "elektra", "id": pid, "title": nombre, "price": co["Price"], "url": url,
          "dept": nombres[-1]}
    if co.get("ListPrice") and co["ListPrice"] > co["Price"]:
        it["listPrice"] = co["ListPrice"]
    imgs = items[0].get("images") or []
    if imgs:
        it["photo"] = imgs[0].get("imageUrl")
    if p.get("brand"):
        it["brand"] = p["brand"]
    ean = re.sub(r"\D", "", items[0].get("ean") or "")
    if 8 <= len(ean) <= 14:
        it["gtin"] = ean
    return it, None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--max-hojas", type=int, default=0, help="sólo las primeras N hojas (prueba)")
    ap.add_argument("--continuar", action="store_true",
                    help="retoma desde la última hoja guardada en <salida>.progreso")
    args = ap.parse_args()
    arbol = fetch_json(f"{BASE}/category/tree/4")
    if not arbol:
        sys.exit("no se pudo leer el árbol de categorías")
    todas = hojas(arbol)
    elegidas = [(p, n) for p, n in todas
                if n[0].strip().lower() not in DEPTOS_FUERA
                and not any(DEPARTAMENTOS_FUERA.search(x) for x in n)]
    if args.max_hojas:
        elegidas = elegidas[:args.max_hojas]
    print(f"hojas: {len(todas)}; a recorrer: {len(elegidas)}", flush=True)
    vistos, salida, fuera, desde = set(), [], {}, 0
    progreso = args.salida + ".progreso"
    if args.continuar and os.path.exists(progreso):
        with open(progreso, encoding="utf-8") as f:
            prog = json.load(f)
        if prog.get("hojas") != [p for p, _ in elegidas]:
            sys.exit("el árbol de categorías cambió desde el último corte: hay que empezar de cero")
        with open(args.salida, encoding="utf-8") as f:
            salida = json.load(f)
        vistos = {it["id"] for it in salida}
        desde = prog["hecho"]
        print(f"se retoma tras la hoja {desde}: {len(salida):,} productos ya guardados", flush=True)
    for i, (path, nombres) in enumerate(elegidas, 1):
        if i <= desde:
            continue
        productos, tope = recorrer(path)
        if tope:
            for r in RANGOS:
                extra, tope_r = recorrer(path, r)
                productos += extra
                if tope_r:
                    print(f"  aviso: {' > '.join(nombres)} sigue topada en ${r[0]}-{r[1]}", flush=True)
        for p in productos:
            it, motivo = item_de(p, nombres)
            if motivo:
                fuera[motivo] = fuera.get(motivo, 0) + 1
                continue
            if it["id"] in vistos:
                continue
            vistos.add(it["id"])
            salida.append(it)
        if i % 25 == 0 or i == len(elegidas):
            print(f"  hoja {i}/{len(elegidas)}: {len(salida):,} productos", flush=True)
            with open(args.salida + ".tmp", "w", encoding="utf-8") as f:
                json.dump(salida, f, ensure_ascii=False)
            os.replace(args.salida + ".tmp", args.salida)
            with open(progreso, "w", encoding="utf-8") as f:
                json.dump({"hecho": i, "hojas": [p for p, _ in elegidas]}, f)
    with open(args.salida, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False)
    print(f"productos distintos: {len(salida):,} -> {args.salida}")
    for m, n in sorted(fuera.items(), key=lambda x: -x[1]):
        print(f"  fuera: {m}: {n:,}")


if __name__ == "__main__":
    main()
