#!/usr/bin/env python3
"""Detecta (y opcionalmente quita) ofertas pegadas al producto EQUIVOCADO.

EL PROBLEMA
-----------
Las fichas de tiendas distintas se unieron en algún momento por "código de
modelo": si dos productos comparten un código tipo G100 o M607, se
tomaron como el mismo producto. Ese criterio produce falsos positivos
espectaculares, porque el mismo código lo usan fabricantes que no tienen
nada que ver entre sí. Casos reales encontrados en el catálogo:

    Motorola G100 (celular)        <- sistema de guitarra Gemini GMU-G100
    Corsair K100 (teclado)         <- memoria USB Kodak K100
    Logitech M100 (mouse)          <- hub inteligente Aqara M100
    Canon T100 (cámara réflex)     <- foco LED T100 de 30 W
    Brady M610 (etiquetadora)      <- cuerdas de ukelele Martin M610

No es solo un precio de más en la tabla: es un precio FALSO (casi siempre
mucho más barato, porque el otro producto es más barato) y un botón "Ver
oferta" que manda al comprador a otra cosa.

CÓMO SE DETECTA
---------------
La url de las tiendas que no son Mercado Libre lleva el nombre del
producto en el slug, así que se compara contra el nombre guardado:

  1. Se toman solo las palabras ALFABÉTICAS de 4+ letras de cada lado. Se
     descarta a propósito el código de modelo (que es justo lo que produjo
     el match equivocado) y las palabras de relleno.
  2. Si NO comparten ni una palabra, el slug describe otro producto.
  3. Escape: si el slug menciona la MARCA del producto, se conserva. Sin
     esta regla se irían casos correctos donde la tienda usa otro nombre
     para lo mismo ("Frigobar 128 L" vs "refrigerador-compacto-128-l-
     negro-...-whirlpool").

Las urls de Mercado Libre (/p/MLM…) no se revisan: son numéricas, no
describen el producto.

USO
---
    python3 scripts/audit_cross_store.py            # solo reporta
    python3 scripts/audit_cross_store.py --fix      # quita las ofertas malas
"""
import argparse
import os
import re
import sys
import unicodedata
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog  # noqa: E402

STOP = {
    "para", "con", "del", "los", "las", "por", "que", "este", "esta", "color",
    "negro", "blanco", "gris", "plateado", "pack", "paquete", "unidades",
    "pulgadas", "pulg", "inch",
}


def _norm(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def words(s):
    return {t for t in re.split(r"[^a-z]+", _norm(s)) if len(t) >= 4} - STOP


def real_url(offer_url):
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(offer_url or "").query)
    ulp = qs.get("ulp", [None])[0]
    return urllib.parse.unquote(ulp) if ulp else (offer_url or "")


def mismatches(products):
    out = []
    for p in products:
        offers = p.get("offers") or []
        if len({o.get("storeId") for o in offers}) < 2:
            continue
        name_words = words(p.get("name"))
        if not name_words:
            continue
        brand = _norm(p.get("brand") or "")
        brand0 = re.split(r"[^a-z0-9]+", brand)[0] if brand else ""
        for o in offers:
            url = real_url(o.get("url"))
            if not url or "/p/MLM" in url:
                continue
            slug = _norm(urllib.parse.unquote(url))
            if brand0 and len(brand0) >= 3 and brand0 in slug:
                continue
            slug_words = words(slug.split("/")[-2] if slug.endswith("/p") else slug)
            if slug_words and not (name_words & slug_words):
                out.append((p, o, url))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true")
    args = ap.parse_args()

    data = load_catalog()
    bad = mismatches(data["products"])
    print(f"Ofertas pegadas a un producto que no es el suyo: {len(bad)}\n")
    for p, o, url in bad:
        print(f"  {p['id']}  {p['name'][:50]}")
        print(f"        {o.get('storeId')} ${o.get('price'):,.0f}  {url[:88]}")

    if not bad:
        return
    if not args.fix:
        print("\n(usar --fix para quitarlas)")
        return

    drop = {(p["id"], id(o)) for p, o, _ in bad}
    removed_products = 0
    survivors = []
    for p in data["products"]:
        offers = p.get("offers") or []
        alive = [o for o in offers if (p["id"], id(o)) not in drop]
        if offers and not alive:
            removed_products += 1
            continue
        p["offers"] = alive
        survivors.append(p)
    data["products"] = survivors
    save_catalog(data)
    print(f"\nOfertas quitadas: {len(bad)}; productos sin ninguna oferta viva: {removed_products}")
    print(f"Catálogo: {len(data['products'])} productos.")


if __name__ == "__main__":
    main()
