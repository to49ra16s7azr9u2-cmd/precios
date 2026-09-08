#!/usr/bin/env python3
"""Actualiza SOLO la disponibilidad de las ofertas de Amazon México.

QUÉ HACE Y QUÉ NO
-----------------
Lee la página del producto que ya está guardada en el catálogo
(https://www.amazon.com.mx/dp/<ASIN>) y actualiza `offer.stock`. Nada más:
NO toca el precio, NO agrega productos y -- a pedido expreso del usuario --
NUNCA BORRA NADA. Un producto agotado se queda en el sitio marcado como
"No disponible"; que hoy no haya existencias no significa que el producto
no exista, y una ficha con su historial de precios sigue sirviendo.

Esa es la diferencia con refresh_elektra.py y refresh_other_stores.py, que
sí podan lo que se dio de baja.

POR QUÉ SOLO LA DISPONIBILIDAD
------------------------------
Es lo único que se lee del HTML sin ambigüedad: Amazon publica un bloque
`id="availability"` con un texto corto y fijo ("Disponible", "Sólo
queda(n) N en stock.", "No disponible."). El precio aparece en varios
lugares de la página con valores distintos (con y sin cupón, por
suscripción, de otros vendedores) y elegir uno sería adivinar cuál cobra
Amazon hoy.

SOBRE LOS TÉRMINOS DE AMAZON
----------------------------
El robots.txt de amazon.com.mx permite /dp/ para `User-agent: *` (solo
bloquea subrutas como /dp/product-availability/), pero sus Condiciones de
Uso prohíben "data mining, robots, or similar data gathering and
extraction tools", y hay bloques `Disallow: /` para agentes de scraping
conocidos. El usuario pidió esto sabiéndolo. Se hace lo mínimo y lo más
suave posible: 1,174 páginas, de a una, con una pausa entre cada una.

CUANDO NO SE PUEDE LEER
-----------------------
Amazon devuelve a veces una página de 4 KB sin producto (su interstitial
antibot). Eso NO se interpreta como "agotado": la oferta se deja como
estaba y se cuenta aparte. Inventar un "no disponible" porque nos
bloquearon sería peor que no actualizar.

USO
---
    python3 scripts/refresh_amazon_stock.py --dry-run --limit 20
    python3 scripts/refresh_amazon_stock.py
"""
import argparse
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog  # noqa: E402

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/17.0 Safari/605.1.15")

# Una página de producto real pesa más de 1 MB; el interstitial antibot,
# 4 KB. El corte no necesita ser fino, solo distinguir una de otra.
MIN_PAGINA = 200_000

_ASIN_RE = re.compile(r"/dp/([A-Z0-9]{10})")
_DISPO_RE = re.compile(r'id="availability".*?<span[^>]*>(.*?)</span>', re.S)
_TAGS_RE = re.compile(r"<[^>]+>|\s+")


def asin_de(url):
    m = _ASIN_RE.search(url or "")
    return m.group(1) if m else None


def stock_de(html):
    """Estado de la oferta según el bloque de disponibilidad, o None si la
    página no lo trae (no se adivina)."""
    m = _DISPO_RE.search(html)
    if not m:
        return None
    texto = _TAGS_RE.sub(" ", m.group(1)).strip().lower()
    if not texto:
        return None
    if "solo queda" in texto or "sólo queda" in texto or "quedan" in texto:
        return "low_stock"
    if "no disponible" in texto or "no está disponible" in texto or "agotado" in texto:
        return "out_of_stock"
    if "disponible" in texto or "en stock" in texto:
        return "in_stock"
    if "pedido" in texto or "reserva" in texto:
        return "backorder"
    return None


def bajar(asin, timeout=30):
    try:
        out = subprocess.run(
            ["curl", "-s", "--compressed", "--max-time", str(timeout), "-A", UA,
             f"https://www.amazon.com.mx/dp/{asin}/"],
            capture_output=True, text=True, errors="ignore", timeout=timeout + 10)
        return out.stdout or ""
    except Exception:
        return ""


def ofertas_amazon(products):
    out = []
    for p in products:
        nodos = list(p.get("offers") or [])
        for v in p.get("colorVariants") or []:
            if "offers" in v:
                nodos += list(v.get("offers") or [])
        for o in nodos:
            if o.get("storeId") != "amazon_mx":
                continue
            a = asin_de(o.get("url"))
            if a:
                out.append((p, o, a))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--pausa", type=float, default=3.0,
                    help="segundos entre páginas (por defecto 3)")
    ap.add_argument("--save-every", type=int, default=200)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = load_catalog()
    todo = ofertas_amazon(data["products"])
    print(f"Ofertas de Amazon con ASIN: {len(todo)}")
    if args.limit:
        todo = todo[: args.limit]
    print(f"A revisar en esta tanda: {len(todo)}\n")

    stats = {"revisados": 0, "sin_cambio": 0, "cambiados": 0,
             "bloqueados": 0, "sin_dato": 0}
    cambios = []
    t0 = time.time()
    for i, (product, offer, asin) in enumerate(todo, 1):
        html = bajar(asin)
        stats["revisados"] += 1
        if len(html) < MIN_PAGINA:
            stats["bloqueados"] += 1
        else:
            nuevo = stock_de(html)
            if nuevo is None:
                stats["sin_dato"] += 1
            elif nuevo == offer.get("stock"):
                stats["sin_cambio"] += 1
            else:
                cambios.append((product["id"], product["name"][:44],
                                offer.get("stock"), nuevo))
                offer["stock"] = nuevo
                stats["cambiados"] += 1
        if i % 50 == 0:
            ritmo = i / max(1e-9, time.time() - t0)
            print(f"  {i}/{len(todo)} · {stats['cambiados']} cambios · "
                  f"{stats['bloqueados']} bloqueados · "
                  f"faltan ~{(len(todo) - i) / ritmo / 60:.0f} min", flush=True)
        if args.save_every and not args.dry_run and i % args.save_every == 0 and cambios:
            save_catalog(data)
            print(f"  [guardado parcial en {i}]", flush=True)
        if i < len(todo):
            time.sleep(args.pausa)

    print("\n=== Resumen ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    if cambios:
        print(f"\n  Cambios ({len(cambios)}):")
        for pid, nombre, antes, ahora in cambios[:30]:
            print(f"   {pid:9} {nombre:44} {antes} -> {ahora}")
        if len(cambios) > 30:
            print(f"   ... y {len(cambios) - 30} más")

    if args.dry_run:
        print("\n(--dry-run: no se escribió nada)")
        return
    if cambios:
        save_catalog(data)
        print(f"\nGuardado: {len(cambios)} ofertas con disponibilidad nueva. "
              "Ningún producto se dio de baja.")
    else:
        print("\nNada que guardar.")


if __name__ == "__main__":
    main()
