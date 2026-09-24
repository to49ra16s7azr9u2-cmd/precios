#!/usr/bin/env python3
"""Baja el feed de productos de un programa de Soicos al formato que come
importar_captura_tienda.py.

DE DÓNDE SALE
-------------
La API de feeds de Soicos (panel -> API): api.soicos.com/api/program/<id>/
datafeed, en JSON paginado (hasta 1000 por página, 60 pedidos por minuto).
Cada producto trae nombre, precio en MXN, precio anterior, stock, foto,
marca, categoría de la tienda, a veces GTIN, y la url YA convertida en
deeplink de afiliado (ad.soicos.com/-XXXX?dl=<url de la tienda>): no hay que
envolverla después.

EL TOKEN NO VA AL REPOSITORIO
-----------------------------
La url lleva token= y aid=, que son credenciales de la cuenta. Se leen de
las variables SOICOS_TOKEN y SOICOS_AID (o de un archivo .env fuera del
repositorio con --env) y nunca se escriben en un archivo versionado. La
captura que sale de acá tampoco las lleva: sólo el deeplink de cada
producto, que es público (es lo que se pone en el botón).

QUÉ SE DESCARTA
---------------
Lo agotado (stock 0) y lo que no trae precio: un comparador que ofrece un
precio que no se puede pagar miente. Y los departamentos de súper y
farmacia (comida, bebidas, vinos y licores, medicamentos, limpieza del
hogar, pañales, alimento para mascotas): el catálogo no los compara y el
clasificador los mandaría, por el título, a la categoría que más se les
parezca (un queso a «Cocina y comedor»). Con --todo entran igual.

PROGRAMAS (aceptados el 24-sep-2026)
------------------------------------
    9839 Lenovo MX (406)          11897 Sam's Club (13 mil)
    11896 Walmart (750 mil)       11487 Bodega Aurrerá (843 mil)
    11337 Sephora (11 mil)        12167 Bodega Despensa (82 mil)
    15695 Reuse (1.5 mil)
(11608, Walmart Súper OnDemand, devuelve el mismo feed que 11896.)

USO
---
    SOICOS_TOKEN=... SOICOS_AID=... python3 scripts/soicos_a_captura.py \\
        --programa 11897 --tienda sams_mx --salida /tmp/sams.json
    python3 scripts/soicos_a_captura.py --env /ruta/fuera/del/repo/soicos.env \\
        --programa 9839 --tienda lenovo --salida /tmp/lenovo.json
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

API = "https://api.soicos.com/api/program/{programa}/datafeed"
POR_PAGINA = 1000
PAUSA = 1.1   # 60 pedidos por minuto


def credenciales(env):
    if env:
        for linea in open(env, encoding="utf-8"):
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                k, v = linea.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    token, aid = os.environ.get("SOICOS_TOKEN"), os.environ.get("SOICOS_AID")
    if not token or not aid:
        sys.exit("faltan SOICOS_TOKEN y SOICOS_AID (variables o --env)")
    return token, aid


def pagina(programa, token, aid, n, categoria=None):
    q = {"token": token, "aid": aid, "per_page": POR_PAGINA, "page": n}
    if categoria:
        q["category_id"] = categoria
    url = API.format(programa=programa) + "?" + urllib.parse.urlencode(q)
    for intento in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "ComparaMEX/1.0"}),
                                        timeout=120) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001 -- red: se reintenta
            espera = 2 ** (intento + 1)
            print(f"  página {n}: {e}; reintento en {espera} s", file=sys.stderr)
            time.sleep(espera)
    raise SystemExit(f"la página {n} no bajó")


def numero(x):
    try:
        v = float(str(x).replace(",", ""))
    except (TypeError, ValueError):
        return None
    return v if v > 0 else None


DEPARTAMENTOS_FUERA = re.compile(
    r'medicamento|refresco|vino|queso|carne|comida|caramelo|helado|pur[eé]|verdura|fruta|chocolate|cerveza|'
    r'licor|tequila|whisky|brandy|\bron\b|vodka|abarrote|l[aá]cteo|leche|botana|galleta|cereal|\bpan\b|panader|'
    r'embutido|salchich|jam[oó]n|pollo|pescado|marisco|huevo|aceites y vinagres|arroz|frijol|^pastas$|sopa|salsa|'
    r'condimento|especias|endulzante|az[uú]car|^agua$|jugo|bebida|snack|dulce|semilla|enlatad|^congelados|'
    r'detergente|papel higi|pañal|toallas? femenin|vitamina|suplemento|farmacia|analg|alimento para|croqueta|'
    r'caf[eé] (en grano|molido|soluble)|^t[eé]\b|mantequilla|yogur|tortilla|harina|mayonesa|at[uú]n|sardina|'
    r'cigarr|champagne|mezcal|ginebra|\bgin\b|cognac|limpieza para mascotas|suavizante|cloro|desinfectante|'
    r'lavatrastes|insecticida|nutrici|f[oó]rmula|papas|frituras|palomitas|ingredientes|estomacal', re.I)

RX_ID_TIENDA = re.compile(r"/ip/(?:[^/?#]+/)*?(\d{6,})(?:[/?#]|$)")


def item(d, tienda, todo=False):
    """Un producto del feed en el formato del marcador, o None si no entra."""
    if not todo and DEPARTAMENTOS_FUERA.search(d.get("category") or ""):
        return None
    precio = numero(d.get("price"))
    if not precio or not d.get("name") or not d.get("url") or not d.get("stock"):
        return None
    real = urllib.parse.unquote(urllib.parse.parse_qs(urllib.parse.urlparse(d["url"]).query).get("dl", [""])[0])
    m = RX_ID_TIENDA.search(real)
    pid = m.group(1) if m else (d.get("sku") or str(d["id"]))
    # Reuse manda el nombre envuelto en «:"...»; se quita el envoltorio.
    # y a veces con un prefijo de sistema («trained_algorithmic_media:"...»).
    titulo = re.sub(r"^[a-z_]+:", "", re.sub(r"\s+", " ", d["name"]).strip())
    titulo = titulo.strip(':"\' ').replace('""', '"')
    # Reuse sólo vende reacondicionados, pero no todos sus nombres lo dicen
    # («Samsung Galaxy A15 4G Negro»): se escribe, para que la ficha no se
    # lea como nueva ni se una con la nueva (fusionar_vetado.USADO_RE).
    if tienda == "reuse_mx" and not re.search(r"reacondicionad", titulo, re.I):
        titulo += " Reacondicionado"
    # Lenovo no escribe el número de parte en el nombre y es lo que empareja
    # su ficha con la misma laptop en Amazon o Mercado Libre
    # (adjuntar_tienda_de_marca.py busca códigos de modelo en el nombre).
    if tienda == "lenovo" and d.get("sku"):
        parte = re.sub(r"^[a-z]{2}_[A-Z]{2}", "", d["sku"]).upper()
        if parte and parte.lower() not in titulo.lower():
            titulo = f"{titulo} ({parte})"
    out = {"store": tienda, "id": str(pid), "title": titulo, "price": precio, "url": d["url"],
           "photo": d.get("img") or None}
    antes = numero(d.get("from_price"))
    if antes and antes > precio:
        out["listPrice"] = antes
    marca = (d.get("brand") or "").strip()
    if marca and marca.lower() not in ("none", "null", "generico", "genérico", "n/a"):
        out["brand"] = marca
    gtin = re.sub(r"\D", "", str(d.get("gtin") or ""))
    if 8 <= len(gtin) <= 14:
        out["gtin"] = gtin
    if d.get("category"):
        out["dept"] = d["category"]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--programa", required=True, type=int)
    ap.add_argument("--tienda", required=True, help="storeId de importar_captura_tienda.TIENDAS")
    ap.add_argument("--salida", required=True)
    ap.add_argument("--env", help="archivo con SOICOS_TOKEN= y SOICOS_AID= (fuera del repositorio)")
    ap.add_argument("--categoria", type=int, action="append", default=[],
                    help="category_id del feed (se puede repetir); sin esto, el feed entero")
    ap.add_argument("--max-paginas", type=int)
    ap.add_argument("--todo", action="store_true", help="no descartar los departamentos de súper y farmacia")
    args = ap.parse_args()
    token, aid = credenciales(args.env)

    items, vistos, total, sin = [], set(), 0, 0
    for cat in args.categoria or [None]:
        n, ultima = 1, None
        while ultima is None or n <= ultima:
            d = pagina(args.programa, token, aid, n, cat)
            ultima = d["meta"]["last_page"]
            if args.max_paginas:
                ultima = min(ultima, args.max_paginas)
            for x in d["data"]:
                total += 1
                it = item(x, args.tienda, args.todo)
                if not it:
                    sin += 1
                    continue
                if it["id"] in vistos:
                    continue
                vistos.add(it["id"])
                items.append(it)
            if n % 20 == 0 or n == ultima:
                print(f"  página {n}/{ultima}: {len(items):,} productos", file=sys.stderr)
            n += 1
            time.sleep(PAUSA)
    json.dump(items, open(args.salida, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"feed: {total:,}; agotados, sin precio o de súper: {sin:,}; productos distintos: {len(items):,} -> {args.salida}")


if __name__ == "__main__":
    main()
