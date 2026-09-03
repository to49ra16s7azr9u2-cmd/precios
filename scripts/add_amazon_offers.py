#!/usr/bin/env python3
"""Agrega Amazon.com.mx como oferta a productos que YA existen en el catálogo.

POR QUÉ ESTE CAMINO Y NO UN IMPORTADOR COMO LOS DE OTRAS TIENDAS
------------------------------------------------------------------
A diferencia de Elektra (API pública permitida por su robots.txt) o
Whirlpool/SharkNinja (páginas de producto sin protección), amazon.com.mx
bloquea el acceso automatizado: un pedido HTTP normal a una ficha de
producto devuelve una página de verificación ("Robot Check" / captcha) con
el texto "To discuss automated access to Amazon data please contact
api-services-support@amazon.com" -- Amazon lo dice explícito, así que no
se scrapea.

La Product Advertising API (PA-API) es el camino oficial, pero requiere una
cuenta de Asociados con al menos 3 ventas calificadas en los últimos 180
días para poder solicitarla -- el plan es juntar esas ventas primero a mano
y pedir la API después.

Mientras tanto, este script cubre la parte que SÍ se puede automatizar: el
link de afiliado de Amazon (SiteStripe) no es más que la URL del producto
con el parámetro `tag=<tu-id-de-asociado>` agregado -- no hace falta abrir
SiteStripe para cada producto, ese tag alcanza para armar el link completo
para cualquier ASIN. Lo que el script NO puede hacer solo es lo que
depende de leer la página de Amazon: precio, título exacto y foto hay que
pasarlos a mano (una vez, no en cada refresco -- ver --price para
actualizar solo eso más adelante).

FORMATO DEL ARCHIVO DE ENTRADA (JSON)
--------------------------------------
Lista de objetos, uno por oferta:

    [
      {"product_id": "p26570", "asin": "B0FQFPN51G", "price": 18999},
      {"product_id": "p26741", "asin": "B0FQFWLX8N", "price": 21999,
       "photo": "https://..."}
    ]

  product_id  id del producto YA existente en el catálogo de ComparaMEX
              (confirmar a mano cuál es -- ver USO abajo para buscarlo)
  asin        el ASIN de Amazon (se saca de la URL: .../dp/B0FQFPN51G/...)
  price       precio actual en MXN, tal como lo viste en la página
  photo       opcional -- si no se pasa, se usa la foto que ya tiene el
              producto en el catálogo (no se hotlinkea nada de Amazon)

USO
---
    # Buscar candidatos por nombre antes de armar el archivo de entrada:
    python3 scripts/add_amazon_offers.py --search "iphone 17 pro max 256"

    # Agregar las ofertas del archivo:
    python3 scripts/add_amazon_offers.py ofertas.json --tag comparamex0d-20 --dry-run
    python3 scripts/add_amazon_offers.py ofertas.json --tag comparamex0d-20

    # --tag es opcional: sin él se agrega con link normal (sin comisión) --
    # útil mientras Amazon México Afiliados no acepta solicitudes nuevas.
    # Correr de nuevo con --tag más adelante actualiza el link de lo ya
    # cargado, sin tener que rehacer el matching.
    python3 scripts/add_amazon_offers.py ofertas.json
"""
import argparse
import json
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog  # noqa: E402

ASIN_RE = re.compile(r"^[A-Z0-9]{10}$")


def affiliate_url(asin, tag):
    # Forma canónica y estable -- sin los parámetros de sesión/búsqueda
    # (crid, dib, sprefix, sr...) que trae un link copiado de una página de
    # resultados, que además delatan que no es un link de afiliado real.
    base = f"https://www.amazon.com.mx/dp/{asin}/"
    if not tag:
        # Amazon México Afiliados no está aceptando solicitudes nuevas por
        # ahora (visto en afiliados.amazon.com.mx: "No estamos aceptando
        # nuevos solicitantes en este momento"). El link funciona igual sin
        # tag -- solo no genera comisión hasta que haya uno. Cuando se
        # consiga, correr este mismo script de nuevo con --tag actualiza el
        # link de las ofertas ya cargadas (no hace falta recargar nada).
        return base
    return f"{base}?tag={urllib.parse.quote(tag)}"


def search(data, query):
    terms = [t.lower() for t in query.split() if t]
    hits = []
    for p in data["products"]:
        n = p["name"].lower()
        if all(t in n for t in terms):
            hits.append(p)
    print(f"{len(hits)} candidatos para '{query}':\n")
    for p in hits[:25]:
        specs = ", ".join(f"{s['label']}={s['value']}" for s in (p.get("specs") or [])[:4])
        print(f"  {p['id']:<9} {p['name'][:60]}")
        if specs:
            print(f"            {specs}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?", help="JSON con las ofertas a agregar")
    ap.add_argument("--search", help="buscar productos existentes por nombre, para armar product_id")
    ap.add_argument("--tag", help="tu tracking id de Amazon Associates (el 'tag' de un link de SiteStripe)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = load_catalog()

    if args.search:
        search(data, args.search)
        return

    if not args.input:
        print("Se requiere <input.json> (o usar --search para buscar product_id primero)",
              file=sys.stderr)
        sys.exit(2)
    if not args.tag:
        print("AVISO: sin --tag -- se agrega con link normal (sin comisión) hasta "
              "que haya un tracking id de Amazon Associates.", file=sys.stderr)

    with open(args.input, encoding="utf-8") as f:
        rows = json.load(f)

    by_id = {p["id"]: p for p in data["products"]}
    added, skipped = [], {"sin_producto": 0, "asin_invalido": 0, "sin_precio": 0, "ya_existe": 0}

    for row in rows:
        pid = row.get("product_id")
        product = by_id.get(pid)
        if not product:
            print(f"  ! product_id '{pid}' no existe en el catálogo -- se omite", file=sys.stderr)
            skipped["sin_producto"] += 1
            continue
        asin = (row.get("asin") or "").strip().upper()
        if not ASIN_RE.match(asin):
            print(f"  ! ASIN inválido '{asin}' para {pid} -- se omite", file=sys.stderr)
            skipped["asin_invalido"] += 1
            continue
        price = row.get("price")
        if not price or price <= 0:
            print(f"  ! sin precio válido para {pid}/{asin} -- se omite", file=sys.stderr)
            skipped["sin_precio"] += 1
            continue

        url = affiliate_url(asin, args.tag)
        offers = product.setdefault("offers", [])
        existing = next((o for o in offers if o.get("storeId") == "amazon_mx"), None)
        if existing:
            existing["price"] = price
            existing["url"] = url
            if row.get("photo"):
                existing["photo"] = row["photo"]
            if row.get("bundleNote"):
                existing["bundleNote"] = row["bundleNote"]
            print(f"  = actualizado {pid} ({product['name'][:40]}) -> ${price:,.2f}")
            skipped["ya_existe"] += 1
            continue

        offer = {
            "storeId": "amazon_mx",
            "price": price,
            "url": url,
            "shippingFee": None,
            "stock": "in_stock",
            "verified": False,
        }
        if row.get("photo"):
            offer["photo"] = row["photo"]
        # bundleNote: el listado de Amazon trae un regalo (audífonos, etc.)
        # incluido en el precio pero el product_id apunta al equipo SIN
        # regalo (mismo criterio que merge_bundle_offers.py) -- se anota
        # acá para que se muestre junto al precio en vez de perderse.
        if row.get("bundleNote"):
            offer["bundleNote"] = row["bundleNote"]
        offers.append(offer)
        added.append((pid, product["name"], price))
        print(f"  + {pid}  {product['name'][:50]}  -> ${price:,.2f} MXN")

    print(f"\nAgregadas: {len(added)}   {skipped}")

    if not added and not skipped["ya_existe"]:
        return
    if args.dry_run:
        print("(--dry-run: no se escribió nada)")
        return

    stores = data.setdefault("stores", [])
    if not any(s["id"] == "amazon_mx" for s in stores):
        stores.append({
            "id": "amazon_mx",
            "name": "Amazon México",
            "hubRegion": None,
            "color": "#FF9900",
            "logo": "AMZ",
            "typicalShippingDays": [2, 6],
        })

    save_catalog(data)
    print("Catálogo actualizado.")


if __name__ == "__main__":
    main()
