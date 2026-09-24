#!/usr/bin/env python3
"""Mete al catálogo lo capturado en Walmart o Bodega Aurrerá, de una vez.

DE DÓNDE VIENE LO QUE ENTRA
---------------------------
Las dos tiendas sirven sus páginas solo a navegadores de verdad (PerimeterX:
cualquier script recibe "Verifica tu identidad", hasta para leer los términos
y condiciones), así que no hay importador que las lea desde el servidor. Hay
dos entradas, las dos legítimas:

  1. El JSON del marcador/extensión (scripts/extension-walmart/): la persona
     abre la tienda en su navegador y el código lee lo que la tienda ya le
     mostró. Cada producto trae id, title, price, photo, url, store y, si el
     listado lo decía, dept, listPrice, brand.
  2. El feed de productos de Admitad (export_adv_products, CSV con ";"),
     cuando el programa esté aprobado y la tienda lo ofrezca. Es el mismo
     formato que ya usa add_motorola_products.py: name, price, oldprice, url
     (el enlace de afiliado, con la url de la tienda dentro de ulp=),
     picture, vendor, available. Todavía no se probó contra un feed real de
     estas dos tiendas: la primera vez, con --dry-run.

QUÉ HACE
--------
  1. Junta los archivos, quita los ids repetidos (el marcador acumula) y lo
     que el catálogo ya tiene de esa tienda (misma url o mismo id de producto
     en la url).
  2. Lo que queda pasa por clasificar_captura_perifericos.py, que decide
     categoría y subcategoría por el título y descarta con motivo lo que no
     es un producto. El clasificador espera la clave `asin` como
     identificador; acá va el id de la tienda, que no choca con ningún ASIN
     de Amazon.

     El departamento (`dept`) NO se le pasa salvo con --usar-departamento.
     En Amazon el departamento manda sobre el título cuando nombra una
     subcategoría del catálogo, y eso funciona porque sus departamentos son
     hojas con nombres afinados. Los de Walmart son más anchos y chocan con
     subcategorías de otra categoría: "Juguetes" existe como subcategoría de
     Mascotas, y con el departamento puesto un LEGO se iba a Mascotas/Juguetes
     (medido en la prueba del 19 de septiembre de 2026: de dos decisiones por
     departamento, una mal). Las 158 reglas por título lo hacen mejor solas.
  3. Da de alta lo clasificado con las mismas guardas que
     add_amazon_standalone.py: sin precio no entra, categoría y subcategoría
     tienen que existir en data/data.json, y un precio tres veces más caro que
     lo más caro de su subcategoría se toma por dato malo.

La url se guarda tal cual viene. Cuando el programa de afiliados se apruebe
se anota el enlace en afiliados.py y aplicar_afiliados.py --tienda <id> la
envuelve; las del feed ya vienen envueltas y se respetan.

Después hay que correr la cadena de siempre (sync_subcategories, compute_facets,
compute_quality_axes, record_price_history, build_search_index,
build_marcas_index, generate_seo_pages); el script lo recuerda.

USO
---
    python3 scripts/importar_captura_tienda.py capturas/walmart-2026-09-20-1234.json
    python3 scripts/importar_captura_tienda.py capturas/bodega-aurrera-*.json --dry-run
    python3 scripts/importar_captura_tienda.py captura.json --solo-clasificar
    python3 scripts/importar_captura_tienda.py --tienda walmart_mx --feed-file feed.csv --dry-run
    python3 scripts/importar_captura_tienda.py --tienda walmart_mx --feed-url "<url del export_adv_products>"
"""
import argparse
import csv
import io
import json
import os
import re
import subprocess
import sys
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from add_amazon_standalone import FACTOR_PRECIO_ABSURDO, techos_por_subcategoria  # noqa: E402
from data_io import load_catalog, next_id, registrar_max_id, save_catalog, url_real  # noqa: E402

# storeId -> cómo se registra en data.json (stores) la primera vez que entra
# un producto suyo. El id walmart_mx ya lo usaban js/app.js (LIVE_API_CONFIG)
# e icons/stores/walmart_mx.png, por eso no es "walmart" a secas.
TIENDAS = {
    "walmart_mx": {
        "dominios": ("walmart.com.mx",),
        "store": {"id": "walmart_mx", "name": "Walmart", "hubRegion": None, "color": "#0071CE",
                  "logo": "WM", "logoImg": "icons/stores/walmart_mx.png", "typicalShippingDays": [2, 7]},
    },
    "bodega_aurrera": {
        "dominios": ("bodegaaurrera.com.mx",),
        "store": {"id": "bodega_aurrera", "name": "Bodega Aurrerá", "hubRegion": None, "color": "#1E8E3E",
                  "logo": "BA", "typicalShippingDays": [2, 7]},
    },
    # Coppel no se captura con el navegador como las dos de arriba: sus
    # fichas se leen del sitemap que publica (ver coppel_sitemap.py) y
    # coppel_a_captura.py las deja en este mismo formato. Lo que aporta
    # entrar por acá son las guardas que ya están escritas -- deduplicado
    # contra el catálogo, clasificación por título y techo de precio por
    # subcategoría -- en vez de un importador propio que las repita.
    # Lenovo entra por el feed de Admitad ("Mexico Main"), no por captura:
    # el feed ya trae la url convertida en deeplink, así que no hace falta
    # envolverla después con aplicar_afiliados.py.
    "lenovo": {
        "dominios": ("lenovo.com",),
        "store": {"id": "lenovo", "name": "Lenovo", "hubRegion": None, "color": "#E1140A",
                  "logo": "LN", "typicalShippingDays": [4, 12]},
    },
    # Whirlpool entra por el sitemap y el JSON-LD de sus fichas (ver
    # whirlpool_a_captura.py), igual que Coppel: el importador pone la
    # clasificación y las guardas.
    "whirlpool": {
        "dominios": ("whirlpool.mx",),
        "store": {"id": "whirlpool", "name": "Whirlpool", "hubRegion": None, "color": "#7B0028",
                  "logo": "WP", "typicalShippingDays": [5, 12], "logoImg": "icons/stores/whirlpool.png"},
    },
    # Sam's Club entra por el feed de Soicos (ver soicos_a_captura.py): las
    # urls ya vienen como deeplink de afiliado.
    "sams_mx": {
        "dominios": ("sams.com.mx",),
        "store": {"id": "sams_mx", "name": "Sam's Club", "hubRegion": None, "color": "#0067A0",
                  "logo": "SC", "typicalShippingDays": [2, 7]},
    },
    # Reuse: celulares, tabletas y laptops reacondicionados (feed de Soicos).
    "reuse_mx": {
        "dominios": ("reuse.mx",),
        "store": {"id": "reuse_mx", "name": "Reuse", "hubRegion": None, "color": "#00A676",
                  "logo": "RU", "typicalShippingDays": [2, 6]},
    },
    # Sephora: belleza y perfumes (feed de Soicos). Entra sólo a fichas que
    # ya existen (emparejar_feed.py), igual que Walmart y Bodega Aurrerá.
    "sephora_mx": {
        "dominios": ("sephora.com.mx",),
        "store": {"id": "sephora_mx", "name": "Sephora", "hubRegion": None, "color": "#000000",
                  "logo": "SE", "typicalShippingDays": [2, 6]},
    },
    "coppel": {
        "dominios": ("coppel.com",),
        "store": {"id": "coppel", "name": "Coppel", "hubRegion": None, "color": "#FFD100",
                  "logo": "CP", "typicalShippingDays": [3, 10]},
    },
}

RX_ID_URL = re.compile(r"/ip/(?:[^/?#]+/)*?(\d{6,})(?:[/?#]|$)")
# Coppel numera distinto, y de dos maneras: /pdp/<slug>-pm-<id> es lo que
# vende la tienda y /pdp/<slug>-mkp-<id> lo que venden terceros en su
# marketplace. El tipo queda pegado al id (ver coppel_sitemap.id_de).
RX_ID_COPPEL = re.compile(r"/pdp/[^?#]*-(pm|mkp)-(\d+)(?:[/?#]|$)")


def id_de_url(url):
    """El id de producto que va al final de la url, según la tienda."""
    u = url_real(url) or url or ""
    m = RX_ID_URL.search(u)
    if m:
        return m.group(1)
    m = RX_ID_COPPEL.search(u)
    return f"{m.group(1)}{m.group(2)}" if m else None


def tienda_de_url(url):
    u = (url_real(url) or url or "").lower()
    for sid, t in TIENDAS.items():
        if any(d in u for d in t["dominios"]):
            return sid
    return None


def precio(raw):
    if raw in (None, "", 0, "0"):
        return None
    try:
        v = float(str(raw).replace(",", "").replace("$", "").strip())
    except ValueError:
        return None
    return v if v > 0 else None


# ---------------------------------------------------------------------------
# Entradas
# ---------------------------------------------------------------------------
def items_de_captura(rutas, tienda):
    out = []
    for ruta in rutas:
        for it in json.load(io.open(ruta, encoding="utf-8")):
            sid = it.get("store") or tienda or tienda_de_url(it.get("url"))
            pid = str(it.get("id") or id_de_url(it.get("url")) or "").strip()
            if sid not in TIENDAS or not pid or not it.get("title") or not it.get("url"):
                continue
            item = {"store": sid, "id": pid, "title": it["title"].strip(), "price": precio(it.get("price")),
                    "photo": it.get("photo") or None, "url": it["url"]}
            for k in ("dept", "brand", "listPrice", "agotado", "sponsored", "gtin",
                      "shippingFee", "freeShippingFromMXN", "internacional",
                      "marketplace"):
                if it.get(k):
                    item[k] = it[k]
            out.append(item)
    return out


def leer_feed(feed_url, feed_file):
    if feed_file:
        text = io.open(feed_file, encoding="utf-8-sig").read()
    else:
        req = urllib.request.Request(feed_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            text = r.read().decode("utf-8-sig")
    primera = text.split("\n", 1)[0]
    sep = ";" if primera.count(";") >= primera.count(",") else ","
    return list(csv.DictReader(io.StringIO(text), delimiter=sep))


def items_de_feed(rows, tienda, contadores):
    """Las columnas del export_adv_products de Admitad, al mismo formato que
    el marcador. Lo que no está disponible no entra."""
    out = []
    for row in rows:
        if (row.get("available") or "true").strip().lower() not in ("true", "1", "yes", "si", "sí"):
            contadores["no_disponible"] += 1
            continue
        url = (row.get("url") or "").strip()
        title = (row.get("name") or row.get("nombre_producto") or "").strip()
        pid = id_de_url(url) or (row.get("id") or row.get("article") or "").strip()
        if not url or not title or not pid:
            contadores["sin_datos"] += 1
            continue
        # La columna de la foto no se llama igual en todos los feeds de
        # Admitad: el de Walmart la trae como "picture" y el de Lenovo como
        # "image". Se miran las dos antes de dar la ficha por sin foto.
        foto = (row.get("picture") or row.get("image") or "").strip() or None
        item = {"store": tienda, "id": pid, "title": title, "price": precio(row.get("price")),
                "photo": foto, "url": url}
        old = precio(row.get("oldprice"))
        if old and item["price"] and old > item["price"]:
            item["listPrice"] = old
        # "None" en texto es lo que escribe Admitad cuando el anunciante no
        # declaró marca. Sin esto queda una marca llamada None, con su página
        # y todo.
        vendor = (row.get("vendor") or "").strip()
        if vendor and vendor.lower() not in ("none", "null", "n/a", "-"):
            item["brand"] = vendor
        if row.get("categoryId"):
            item["dept"] = row["categoryId"].strip().split("/")[-1].strip()
        out.append(item)
    return out


# ---------------------------------------------------------------------------
# Lo que el catálogo ya tiene
# ---------------------------------------------------------------------------
def conocidos(products):
    """{(storeId, id de producto)} y {url real} de las ofertas de estas tiendas."""
    ids, urls = set(), set()
    for p in products:
        offers = list(p.get("offers") or [])
        for v in p.get("colorVariants") or []:
            offers += list(v.get("offers") or [])
        for o in offers:
            if o.get("storeId") not in TIENDAS or not o.get("url"):
                continue
            urls.add(url_real(o["url"]) or o["url"])
            pid = id_de_url(o["url"])
            if pid:
                ids.add((o["storeId"], pid))
    return ids, urls


# ---------------------------------------------------------------------------
# Alta
# ---------------------------------------------------------------------------
def dar_de_alta(data, clasificados, originales):
    """Mete en `data` las fichas nuevas. Devuelve (creados, saltados)."""
    cat_ids = {c["id"]: {s["id"] for s in (c.get("subcategories") or [])} for c in data["categories"]}
    techos = techos_por_subcategoria(data["products"])
    nid = next_id(data["products"], data)
    creados, saltados = [], []
    for it in clasificados:
        orig = originales.get(it["asin"])
        if not orig:
            saltados.append((it.get("title", "?"), "no está en la captura original"))
            continue
        if it.get("price") in (None, "", 0):
            saltados.append((it["title"], "sin precio"))
            continue
        if orig.get("agotado"):
            saltados.append((it["title"], "agotado en la tienda"))
            continue
        cat, sub = it.get("category"), it.get("subcategory")
        if cat not in cat_ids:
            saltados.append((it["title"], f"categoría desconocida: {cat}"))
            continue
        if sub and sub not in cat_ids[cat]:
            # Igual que en add_amazon_standalone.py: una subcategoría nueva del
            # clasificador hay que registrarla en data/data.json antes.
            saltados.append((it["title"], f"subcategoría desconocida: {cat}/{sub}"))
            continue
        techo = techos.get((cat, sub))
        if techo and it["price"] > techo * FACTOR_PRECIO_ABSURDO:
            saltados.append((it["title"], f"precio inverosímil: ${it['price']:,.2f} cuando lo más caro de "
                                          f"{cat}/{sub} es ${techo:,.2f}"))
            continue
        offer = {"storeId": orig["store"], "price": it["price"], "stock": "in_stock", "url": orig["url"]}
        if orig.get("listPrice") and orig["listPrice"] > it["price"]:
            offer["listPrice"] = orig["listPrice"]
        # Envío y quién vende, cuando la captura los trae (ver
        # coppel_a_captura.py). shippingFee=0 es "gratis confirmado por la
        # tienda", que es lo que la UI ya sabe leer; el resto son datos que
        # la ficha muestra al lado del precio.
        for k in ("shippingFee", "freeShippingFromMXN", "internacional", "marketplace"):
            if orig.get(k) is not None:
                offer[k] = orig[k]
        product = {
            "id": f"p{nid}",
            "name": it["title"],
            "brand": it.get("brand") or orig.get("brand") or "",
            "category": cat,
            "subcategory": sub,
            "image": it.get("image") or "box",
            "specs": [],
            "offers": [offer],
        }
        if it.get("photo") or orig.get("photo"):
            product["photo"] = it.get("photo") or orig.get("photo")
        # El GTIN del feed (Soicos lo trae para parte de Walmart): es lo que
        # mejor empareja con la misma ficha en otra tienda.
        if orig.get("gtin"):
            product["gtin"] = orig["gtin"]
        data["products"].append(product)
        creados.append(product)
        nid += 1
    if creados:
        registrar_max_id(data, nid - 1)
        stores = data.setdefault("stores", [])
        for sid in {p["offers"][0]["storeId"] for p in creados}:
            if not any(s["id"] == sid for s in stores):
                stores.append(dict(TIENDAS[sid]["store"]))
    return creados, saltados


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("capturas", nargs="*", help="JSON del marcador (uno o varios)")
    ap.add_argument("--tienda", choices=sorted(TIENDAS), help="storeId; obligatorio con --feed-*, "
                                                              "opcional con capturas (cada producto trae el suyo)")
    ap.add_argument("--feed-file", help="feed de Admitad (export_adv_products) ya bajado")
    ap.add_argument("--feed-url", help="url del feed de Admitad")
    ap.add_argument("--dry-run", action="store_true", help="todo menos el alta")
    ap.add_argument("--solo-clasificar", action="store_true", help="clasificar y parar; deja <captura>.alta.json")
    ap.add_argument("--usar-departamento", action="store_true",
                    help="dejar que el departamento de la tienda mande sobre el título (ver arriba por qué no)")
    args = ap.parse_args()
    if (args.feed_file or args.feed_url) and not args.tienda:
        ap.error("con --feed-file/--feed-url hace falta --tienda")
    if not args.capturas and not (args.feed_file or args.feed_url):
        ap.error("se necesita una captura o un feed")

    contadores = {"no_disponible": 0, "sin_datos": 0}
    items = items_de_captura(args.capturas, args.tienda) if args.capturas else []
    if args.feed_file or args.feed_url:
        rows = leer_feed(args.feed_url, args.feed_file)
        print(f"Filas en el feed: {len(rows)}")
        items += items_de_feed(rows, args.tienda, contadores)
        print(f"  no disponibles: {contadores['no_disponible']}   sin url/nombre/id: {contadores['sin_datos']}")

    # 1. desduplicar y quitar lo que ya está
    vistos, unicos = set(), []
    for it in items:
        k = (it["store"], it["id"])
        if k in vistos:
            continue
        vistos.add(k)
        unicos.append(it)
    print(f"Capturados: {len(unicos)} productos distintos")
    if not unicos:
        return
    data = load_catalog()
    ids, urls = conocidos(data["products"])
    nuevos = [it for it in unicos if (it["store"], it["id"]) not in ids and (url_real(it["url"]) or it["url"]) not in urls]
    print(f"Ya en el catálogo: {len(unicos) - len(nuevos)}   nuevos: {len(nuevos)}")
    if not nuevos:
        return

    # 2. clasificar (el clasificador identifica por `asin`: va el id de la tienda)
    base = os.path.splitext(args.capturas[0] if args.capturas else (args.feed_file or f"feed-{args.tienda}"))[0]
    ruta_nuevos, ruta_alta = base + ".nuevos.json", base + ".alta.json"
    para_clasificar = [{"asin": it["id"], "title": it["title"], "price": it["price"], "photo": it.get("photo"),
                        "url": it["url"], **({"dept": it["dept"]} if args.usar_departamento and it.get("dept") else {})}
                       for it in nuevos]
    json.dump(para_clasificar, io.open(ruta_nuevos, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n== clasificar_captura_perifericos.py ({len(nuevos)} productos) ==")
    env = {**os.environ, "PYTHONPATH": AQUI}
    r = subprocess.run([sys.executable, os.path.join(AQUI, "clasificar_captura_perifericos.py"), ruta_nuevos, ruta_alta], env=env)
    if r.returncode:
        sys.exit("el clasificador falló")
    os.remove(ruta_nuevos)
    clasificados = json.load(io.open(ruta_alta, encoding="utf-8"))
    if args.solo_clasificar:
        print(f"\nClasificados en {ruta_alta}. Revísalo y vuelve a correr sin --solo-clasificar.")
        return
    if not clasificados:
        os.remove(ruta_alta)
        print("\nNada que dar de alta.")
        return

    # 3. alta
    originales = {it["id"]: it for it in nuevos}
    creados, saltados = dar_de_alta(data, clasificados, originales)
    for name, why in saltados:
        print(f"  SALTADO  {name[:64]:64} {why}")
    print(f"\nAltas: {len(creados)}   saltados: {len(saltados)}")
    for p in creados[:40]:
        print(f"  {p['id']:9} {p['offers'][0]['storeId']:14} {p['category']}/{p['subcategory']}  ${p['offers'][0]['price']:>10,.2f}  {p['name'][:52]}")
    if len(creados) > 40:
        print(f"  ... y {len(creados) - 40} más")
    if args.dry_run:
        print("\n(--dry-run: no se guardó nada; el JSON clasificado queda en " + ruta_alta + ")")
        return
    if not creados:
        os.remove(ruta_alta)
        print("\nNada que guardar.")
        return
    save_catalog(data)
    os.remove(ruta_alta)
    print(f"\nGuardado. Catálogo: {len(data['products'])} productos")
    print("Ahora la cadena de siempre: sync_subcategories, compute_facets, compute_quality_axes, "
          "record_price_history, build_search_index, build_marcas_index, generate_seo_pages.")


if __name__ == "__main__":
    main()
