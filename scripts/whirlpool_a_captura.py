#!/usr/bin/env python3
"""Baja las fichas de whirlpool.mx al formato que come importar_captura_tienda.py.

Es el mismo camino que Coppel (cosechar_coppel.py + coppel_a_captura.py):
en vez del categorizador propio de add_whirlpool_products.py --que es de
antes de la taxonomía actual y mandaba lo que no reconocía a "Otros"--, las
fichas pasan por el importador genérico, que clasifica con las reglas de
clasificar_captura_perifericos.py, deduplica contra el catálogo y descarta
el precio inverosímil. Después, la fusión cruzada (merge_amazon_cross_store.py
+ fusionar_vetado.py) junta cada Whirlpool con la misma lavadora en Coppel,
Elektra, Liverpool o Mercado Libre, que es lo que un comparador tiene que
hacer con una tienda de marca.

DE DÓNDE SALE
-------------
El sitemap de productos (sitemap/product-0.xml, 534 urls el 23-sep-2026) y
el JSON-LD schema.org/Product de cada ficha: nombre, marca, foto, sku y
precio en MXN. robots.txt permite todo menos cuenta, login, checkout,
búsqueda y quick-view, y el sitio no tiene protección de bots. Los pedidos
van de a uno cada ~0.4 s (el _throttle de add_whirlpool_products.py).

EL ENLACE DE AFILIADO
---------------------
Se envuelve acá con la base de afiliados.py. url_afiliado() arma
exactamente el deeplink que devuelve el generador del panel de Admitad para
"Whirlpool MX/CO" (comparado carácter por carácter el 23-sep-2026).

QUÉ SE DESCARTA ACÁ
-------------------
Las páginas de servicio (instalaciones, garantías) y lo agotado: un
comparador que ofrece un precio que no se puede pagar miente. Las
refacciones y consumibles (Affresh, filtros) SÍ entran: el clasificador los
manda a su subcategoría de accesorio, y se venden también en Amazon y
Mercado Libre, así que hay con qué compararlos.

USO
---
    python3 scripts/whirlpool_a_captura.py --salida capturas/whirlpool.json
    python3 scripts/importar_captura_tienda.py capturas/whirlpool.json --tienda whirlpool --dry-run
"""
import argparse
import datetime
import json
import os
import re
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from add_whirlpool_products import SERVICE_SLUGS, SITEMAP_URL, extract_product, fetch  # noqa: E402
from afiliados import base_de  # noqa: E402
from data_io import url_afiliado  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def urls_de_productos():
    xml = fetch(SITEMAP_URL)
    if not xml:
        sys.exit("No se pudo bajar el sitemap de productos")
    out = []
    for u in re.findall(r"<loc>([^<]+)</loc>", xml):
        slug = urllib.parse.urlparse(u).path.strip("/").rsplit("/", 1)[0].lower()
        if slug in SERVICE_SLUGS:
            continue
        out.append(u)
    return out


def modelos_de(url):
    """Los códigos de modelo del final del slug, en mayúsculas.

    whirlpool.mx no los pone en el nombre ("Lavadora 20kg Carga Superior
    Blanca Agitador") pero sí en la url (...-agitador-8mwtw2024mjm/p), y los
    combos traen dos (...-whw9910s-wer3000). Coppel, Elektra y Mercado
    Libre sí los escriben en el título, y es por ahí que la fusión cruzada
    reconoce que es la misma lavadora.
    """
    slug = urllib.parse.urlparse(url).path.strip("/")
    if slug.endswith("/p"):
        slug = slug[:-2]
    partes = slug.rsplit("/", 1)[-1].split("-")
    codigos = []
    for w in reversed(partes):
        if len(w) >= 5 and re.search(r"\d", w) and re.search(r"[a-z]", w) and not re.fullmatch(r"\d+(kg|cm|pies|l|w|btu|hp)", w):
            codigos.append(w.upper())
        else:
            break
    return list(reversed(codigos))


def id_de(url, info):
    """El sku del JSON-LD, o el código del final del slug."""
    if info.get("sku"):
        return str(info["sku"]).strip()
    slug = urllib.parse.urlparse(url).path.strip("/").rsplit("/", 1)[0]
    return slug.rsplit("-", 1)[-1]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--salida")
    ap.add_argument("--limite", type=int, default=0)
    ap.add_argument("--paralelas", type=int, default=3)
    args = ap.parse_args()

    base = base_de("whirlpool")
    urls = urls_de_productos()
    if args.limite:
        urls = urls[:args.limite]
    print(f"urls de producto: {len(urls)}")

    def leer(u):
        page = fetch(u)
        return u, (extract_product(page, u) if page else None)

    items, motivos = [], {"sin_json_ld": 0, "agotado": 0, "sin_nombre": 0}
    with ThreadPoolExecutor(max_workers=args.paralelas) as ex:
        for u, info in ex.map(leer, urls):
            if not info:
                motivos["sin_json_ld"] += 1
                continue
            if not info.get("in_stock"):
                motivos["agotado"] += 1
                continue
            if not info.get("name"):
                motivos["sin_nombre"] += 1
                continue
            foto = info.get("image")
            if isinstance(foto, list):
                foto = foto[0] if foto else None
            item = {"store": "whirlpool", "id": id_de(u, info), "title": info["name"].strip(),
                    "price": info["price"], "photo": foto,
                    "url": url_afiliado(base, u) if base else u}
            if info.get("brand"):
                item["brand"] = info["brand"]
            if info.get("gtin"):
                item["gtin"] = info["gtin"]
            modelos = modelos_de(u)
            if modelos:
                item["modelos"] = modelos
            items.append(item)

    salida = args.salida or os.path.join(
        RAIZ, "capturas", f"whirlpool-{datetime.date.today().isoformat()}-{len(items)}.json")
    os.makedirs(os.path.dirname(salida), exist_ok=True)
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    for k, v in motivos.items():
        if v:
            print(f"  descartada por {k}: {v}")
    print(f"convertidas {len(items)} -> {os.path.relpath(salida, RAIZ)}")


if __name__ == "__main__":
    main()
