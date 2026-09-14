#!/usr/bin/env python3
"""Agrega al catálogo los productos de una tienda Shopify o WooCommerce
(ver tiendas_json.py).

Es el gemelo de add_vtex_products.py para la otra plataforma que se repite
entre las tiendas mexicanas. Las dos rutas que lee son públicas y paginadas:

    Shopify       /products.json?limit=250&page=N
    WooCommerce   /wp-json/wc/store/products?per_page=100&page=N

Lo que se guarda de cada producto es lo mismo que en VTEX: precio y precio
de lista de la variante más barata con existencia, foto, marca, y la url de
la ficha en la tienda. Ni Shopify ni WooCommerce publican EAN por esta ruta,
así que estos productos no entran al cruce por código de barras
(match_by_gtin.py) -- se comparan por firma de nombre como los de Amazon.

USO
---
    python3 scripts/add_json_products.py --store maskota --dry-run --limit 40
    python3 scripts/add_json_products.py --store maskota
    python3 scripts/add_json_products.py --store gonher --paginas 5
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, next_id, registrar_max_id, save_catalog  # noqa: E402
from tiendas_json import TIENDAS_JSON, resolver  # noqa: E402

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")
# Una pausa corta entre páginas: son tiendas chicas y no hay prisa.
PAUSA = 0.6


def fetch(url, intentos=3):
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                       "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8", "ignore"))
        except urllib.error.HTTPError as e:
            if e.code in (404, 403):
                return None
        except Exception:
            pass
        time.sleep(1.5 * (i + 1))
    return None


def iter_shopify(dominio, paginas=0):
    page = 1
    while True:
        datos = fetch(f"https://{dominio}/products.json?limit=250&page={page}")
        items = (datos or {}).get("products") or []
        if not items:
            return
        for p in items:
            yield p
        page += 1
        if paginas and page > paginas:
            return
        time.sleep(PAUSA)


def iter_woo(dominio, paginas=0):
    page = 1
    while True:
        datos = fetch(f"https://{dominio}/wp-json/wc/store/products"
                      f"?per_page=100&page={page}")
        if not datos:
            return
        for p in datos:
            yield p
        if len(datos) < 100:
            return
        page += 1
        if paginas and page > paginas:
            return
        time.sleep(PAUSA)


def _precio_shopify(p):
    """La variante más barata que la tienda marca disponible. Shopify da el
    precio como cadena ('1299.00') y el de lista en compare_at_price."""
    mejor = None
    for v in p.get("variants") or []:
        if v.get("available") is False:
            continue
        try:
            precio = float(v.get("price"))
        except (TypeError, ValueError):
            continue
        try:
            lista = float(v.get("compare_at_price"))
        except (TypeError, ValueError):
            lista = None
        if mejor is None or precio < mejor[0]:
            mejor = (precio, lista)
    return mejor


def _precio_woo(p):
    """WooCommerce da los precios en centavos dentro de prices, con el número
    de decimales aparte (currency_minor_unit)."""
    pr = p.get("prices") or {}
    try:
        div = 10 ** int(pr.get("currency_minor_unit", 2))
    except (TypeError, ValueError):
        div = 100
    try:
        precio = float(pr.get("price")) / div
    except (TypeError, ValueError):
        return None
    lista = None
    try:
        regular = float(pr.get("regular_price")) / div
        if regular > precio:
            lista = regular
    except (TypeError, ValueError):
        pass
    if p.get("is_in_stock") is False:
        return None
    return (precio, lista)


def producto_de(store_id, p):
    """(producto nuevo, motivo de descarte). Uno de los dos es None."""
    tienda = TIENDAS_JSON[store_id]
    shopify = tienda["plataforma"] == "shopify"

    name = ((p.get("title") if shopify else p.get("name")) or "").strip()
    if not name:
        return None, "sin_nombre"

    # Lo que la tienda dice del producto, que es contra lo que se mapea.
    if shopify:
        texto = " ".join(filter(None, [p.get("product_type") or "",
                                       " ".join(p.get("tags") or [])]))
    else:
        texto = " ".join(c.get("name") or "" for c in (p.get("categories") or []))

    resuelto = resolver(tienda["categorias"], texto, name)
    if not resuelto:
        return None, "sin_categoria"
    category, subcategory, icon_key = resuelto

    precio = _precio_shopify(p) if shopify else _precio_woo(p)
    if not precio:
        return None, "sin_stock"
    price, list_price = precio

    if shopify:
        handle = p.get("handle")
        url = f"https://{tienda['dominio']}/products/{handle}" if handle else None
        imgs = p.get("images") or []
        photo = (imgs[0].get("src") if isinstance(imgs[0], dict) else imgs[0]) if imgs else None
        brand = (p.get("vendor") or "").strip()
    else:
        url = p.get("permalink")
        img = (p.get("images") or [{}])[0]
        photo = img.get("src")
        brand = ""
    if not url:
        return None, "sin_url"

    offer = {
        "storeId": store_id,
        "price": round(price, 2),
        "url": url,
        "photo": photo,
        "shippingFee": None,
        "points": None,
        "rating": None,
        "reviewCount": 0,
        "stock": "in_stock",
        "verified": False,
    }
    if list_price:
        offer["listPrice"] = round(list_price, 2)

    product = {
        "name": name,
        "brand": brand or tienda["nombre"],
        "category": category,
        "image": icon_key,
        "photo": photo,
        "specs": [],
        "reviews": [],
        "offers": [offer],
    }
    if subcategory:
        product["subcategory"] = subcategory
    return product, None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--store", required=True, choices=sorted(TIENDAS_JSON))
    ap.add_argument("--paginas", type=int, default=0, help="máximo de páginas (0 = todas)")
    ap.add_argument("--limit", type=int, default=0, help="máximo de productos, para pruebas")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    tienda = TIENDAS_JSON[args.store]
    data = load_catalog()

    # Las urls que ya están, para no dar de alta dos veces el mismo producto.
    vistas = {o.get("url") for p in data["products"] for o in (p.get("offers") or []) if o.get("url")}
    nombres = {(p.get("name") or "").strip().lower() for p in data["products"]}

    it = (iter_shopify if tienda["plataforma"] == "shopify" else iter_woo)
    nuevos, motivos, leidos = [], {}, 0
    for p in it(tienda["dominio"], args.paginas):
        leidos += 1
        prod, motivo = producto_de(args.store, p)
        if motivo:
            motivos[motivo] = motivos.get(motivo, 0) + 1
            continue
        url = prod["offers"][0]["url"]
        if url in vistas:
            motivos["duplicado_url"] = motivos.get("duplicado_url", 0) + 1
            continue
        clave = prod["name"].strip().lower()
        if clave in nombres:
            motivos["duplicado_nombre"] = motivos.get("duplicado_nombre", 0) + 1
            continue
        vistas.add(url)
        nombres.add(clave)
        nuevos.append(prod)
        if args.limit and len(nuevos) >= args.limit:
            break

    print(f"{tienda['nombre']}: leídos {leidos}, nuevos {len(nuevos)}")
    if motivos:
        print("  descartes:", ", ".join(f"{k}={v}" for k, v in sorted(motivos.items())))
    for p in nuevos[:20]:
        print(f"  [{p['category']} / {p.get('subcategory')}] {p['name'][:64]}"
              f"  ->  ${p['offers'][0]['price']:,.2f}")
    if len(nuevos) > 20:
        print(f"  ... y {len(nuevos) - 20} más")

    if args.dry_run:
        print("\n--dry-run: no se escribió nada")
        return
    if not nuevos:
        print("\nnada que agregar")
        return

    # La entrada de la tienda en data.json, si todavía no está.
    if not any(s.get("id") == args.store for s in data.get("stores", [])):
        data.setdefault("stores", []).append(dict(tienda["store"]))
        print(f"  tienda '{args.store}' agregada a data.stores")

    ultimo = None
    for p in nuevos:
        p["id"] = next_id(data)
        ultimo = p["id"]
        data["products"].append(p)
    if ultimo:
        registrar_max_id(data, ultimo)
    save_catalog(data)
    print(f"\nGuardado. Catálogo: {len(data['products'])} productos")


if __name__ == "__main__":
    main()
