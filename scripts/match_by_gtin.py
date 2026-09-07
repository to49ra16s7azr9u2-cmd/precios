#!/usr/bin/env python3
"""Agrega la oferta de Mercado Libre a productos que hoy solo tienen una
tienda, cuando el CÓDIGO DE BARRAS coincide exactamente.

EL PROBLEMA QUE RESUELVE
------------------------
ComparaMEX es un comparador, pero ~76,000 de sus ~89,000 ofertas son de
Elektra y no tienen con qué compararse: un producto, una tienda, un precio.
Si ese mismo producto está en Mercado Libre, hoy no nos enteramos.

POR QUÉ POR CÓDIGO DE BARRAS Y NO POR NOMBRE
--------------------------------------------
Unir por nombre/modelo ya se intentó en este catálogo y salió mal. Está
documentado en scripts/audit_cross_store.py, con casos reales que hubo que
deshacer:

    Motorola G100 (celular)   <- sistema de guitarra Gemini GMU-G100
    Corsair K100 (teclado)    <- memoria USB Kodak K100
    Canon T100 (cámara)       <- foco LED T100 de 30 W

No es "un precio de más": es un precio FALSO (casi siempre más barato,
porque el otro producto es más barato) y un botón "Ver oferta" que manda al
comprador a otra cosa. El código de barras no admite esa ambigüedad: o es
exactamente el mismo producto, o no hay resultado. Por eso este script NO
tiene umbral de similitud ni cola de revisión: solo une coincidencias
exactas, y ante la duda no une nada.

DE DÓNDE SALEN LOS CÓDIGOS
--------------------------
  - Nuestro lado: el `ean` que publica la API de Elektra, que ya se guarda
    en cada oferta durante el refresco de precios (ver refresh_elektra.py).
  - Mercado Libre: el atributo GTIN del producto de catálogo, vía el
    endpoint /by-gtin del Worker (backend/mercadolibre-worker).

Ojo: no todos los `ean` de Elektra son códigos del fabricante. En datos
reales se ven códigos internos de la tienda (un iPhone 17 Pro con
0400064180616, que no es un código de Apple). Esos simplemente no
encuentran nada del otro lado -- son un no-resultado, no un riesgo.

USO
---
    python3 scripts/match_by_gtin.py --dry-run --limit 300   # ver qué uniría
    python3 scripts/match_by_gtin.py --limit 2000            # aplicar por tandas
    python3 scripts/match_by_gtin.py                         # todo el catálogo

REQUIERE el Worker con /by-gtin desplegado:
    cd backend/mercadolibre-worker && npx wrangler deploy
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog  # noqa: E402

BY_GTIN = "https://comparamx-mercadolibre-proxy.comparamx.workers.dev/by-gtin"
ITEM = "https://comparamx-mercadolibre-proxy.comparamx.workers.dev/item"

# Un código de barras de fabricante es EAN-13, UPC-A (12) o GTIN-14. Fuera de
# esos largos es un código interno de la tienda, y pedirlo a Mercado Libre es
# gastar una petición para que no encuentre nada.
VALID_GTIN_LENGTHS = {12, 13, 14}


def normalize_gtin(raw):
    """Deja el código en dígitos y sin ceros de relleno a la izquierda.

    Un mismo producto se publica como UPC-A de 12 dígitos, EAN-13 con un 0
    adelante o GTIN-14 con dos: 840023287053 / 0840023287053 /
    00840023287053 son el MISMO código. Sin normalizar, el mismo producto no
    coincidiría consigo mismo.
    """
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) not in VALID_GTIN_LENGTHS:
        return None
    stripped = digits.lstrip("0")
    # Visto en datos reales de Elektra: "0000008301383" (un iPhone 15). Tiene
    # 13 dígitos, pero descontando el relleno son 7 -- un consecutivo interno
    # de la tienda, no un código de fabricante. El prefijo GS1 de compañía ya
    # ocupa 7-9 dígitos, así que por debajo de 8 no puede ser un GTIN real:
    # se descarta acá en vez de gastar una petición para que no encuentre nada.
    if len(stripped) < 8:
        return None
    return stripped


def get_json(url, retries=2):
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):
                try:
                    return json.load(e)
                except Exception:
                    return None
            if attempt == retries:
                return None
            time.sleep(1.5 * (attempt + 1))
        except Exception:
            if attempt == retries:
                return None
            time.sleep(1.5 * (attempt + 1))
    return None


def candidates(products):
    """Productos que pueden ganar algo: tienen código de barras y todavía no
    tienen oferta de Mercado Libre."""
    out = []
    for p in products:
        offers = p.get("offers") or []
        if any(o.get("storeId") == "mercadolibre" for o in offers):
            continue
        for o in offers:
            gtin = normalize_gtin(o.get("ean"))
            if gtin:
                out.append((p, gtin))
                break
    return out


def ml_offer_for(gtin):
    """(oferta_lista_para_guardar, producto_ml) del producto de catálogo con
    ESE código de barras, o (None, motivo)."""
    res = get_json(f"{BY_GTIN}?gtin={urllib.parse.quote(gtin)}")
    if res is None:
        return None, "sin_respuesta"
    if res.get("error") and not res.get("results"):
        return None, "error_worker"
    results = res.get("results") or []
    if not results:
        return None, "sin_coincidencia"
    # Más de un producto de catálogo con el mismo código de barras no debería
    # pasar; si pasa, no hay forma de saber cuál es y no se une ninguno.
    if len(results) > 1:
        return None, "ambiguo"
    ml = results[0]
    # Confirmación: el código que devuelve Mercado Libre para ESE producto
    # tiene que incluir el que pedimos. Si el endpoint alguna vez devolviera
    # resultados aproximados, esto lo corta acá.
    #
    # OJO: el campo viene con VARIOS códigos separados por coma cuando el
    # mismo producto se fabricó con más de un empaque. Probado contra la API
    # real, la PlayStation 5 Standard (MLM37361084) devuelve
    # "711719541028, 711719548560". Normalizando la cadena entera se pegaban
    # los dos números en uno de 24 dígitos, que no es un largo de GTIN
    # válido: normalize_gtin devolvía None y la comprobación rechazaba una
    # coincidencia BUENA. Hay que partir por coma y ver si el nuestro está
    # entre ellos.
    if ml.get("gtin"):
        publicados = {normalize_gtin(x) for x in str(ml["gtin"]).split(",")}
        publicados.discard(None)
        if publicados and gtin not in publicados:
            return None, "gtin_no_confirma"
    detail = get_json(f"{ITEM}?id={urllib.parse.quote(ml['id'])}")
    if not detail or not detail.get("price"):
        return None, "sin_ofertas_activas"
    offer = {
        "storeId": "mercadolibre",
        "price": detail["price"],
        "url": detail.get("url") or ml.get("url"),
        "stock": "in_stock",
        "verified": True,
    }
    for src, dst in (("shippingFee", "shippingFee"), ("sellerCount", "sellerCount"),
                     ("lowestPrice", "lowestPrice"), ("sellers", "sellers")):
        if detail.get(src) is not None:
            offer[dst] = detail[src]
    if detail.get("priceOriginal"):
        offer["listPrice"] = detail["priceOriginal"]
    return offer, ml


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="máximo de productos a consultar (0 = todos)")
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = load_catalog()
    todo = candidates(data["products"])
    print(f"Productos con código de barras y sin oferta de Mercado Libre: {len(todo)}")
    todo = todo[args.offset:]
    if args.limit:
        todo = todo[: args.limit]
    if not todo:
        print("Nada que consultar.")
        return
    print(f"A consultar en esta tanda: {len(todo)}\n")

    # Sonda: si el Worker desplegado no tiene /by-gtin, no tiene sentido
    # lanzar miles de peticiones que van a fallar todas.
    probe = get_json(f"{BY_GTIN}?gtin={todo[0][1]}")
    if probe is None or (probe.get("error") and "ruta no encontrada" in str(probe.get("error"))):
        print(
            "El Worker desplegado no tiene el endpoint /by-gtin.\n"
            "Despliega la versión nueva antes de usar este script:\n"
            "    cd backend/mercadolibre-worker && npx wrangler deploy",
            file=sys.stderr,
        )
        raise SystemExit(2)

    stats = {"consultados": 0, "unidos": 0, "sin_coincidencia": 0, "ambiguo": 0,
             "sin_ofertas_activas": 0, "gtin_no_confirma": 0, "error_worker": 0,
             "sin_respuesta": 0}
    unidos = []

    # Las peticiones van en paralelo, pero el conteo y la escritura en el
    # catálogo se serializan: "leer, sumar uno, guardar" desde varios hilos
    # pierde incrementos, y un resumen con números mal contados es peor que
    # no tenerlo (es lo único con lo que se decide si la corrida salió bien).
    from threading import Lock
    lock = Lock()

    def work(item):
        product, gtin = item
        offer, info = ml_offer_for(gtin)
        with lock:
            stats["consultados"] += 1
            if offer is None:
                stats[info] = stats.get(info, 0) + 1
                return
            product.setdefault("offers", []).append(offer)
            stats["unidos"] += 1
            unidos.append((product["id"], product["name"], gtin, info.get("name"), offer["price"]))

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        list(pool.map(work, todo))

    print("=== Resumen ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    if unidos:
        print(f"\n  Unidos ({len(unidos)}):")
        for pid, name, gtin, ml_name, price in unidos[:30]:
            print(f"   {pid}  {gtin:>14}  {name[:38]:38} <- ML: {(ml_name or '')[:34]:34} ${price:,.0f}")
        if len(unidos) > 30:
            print(f"   ... y {len(unidos) - 30} más")

    if args.dry_run:
        print("\n(--dry-run: no se guardó nada)")
        return
    if unidos:
        save_catalog(data)
        print(f"\nGuardado: {len(unidos)} productos ahora comparan precio entre dos tiendas.")
    else:
        print("\nNada que guardar.")


if __name__ == "__main__":
    main()
