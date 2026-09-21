#!/usr/bin/env python3
"""Baja las fichas de Coppel a un archivo de trabajo, sin tocar el catálogo.

Es la primera de las dos mitades de la importación de Coppel (la segunda es
add_coppel_products.py). Están separadas por una razón práctica: son 350,000
fichas, o sea horas de descarga, y el catálogo no puede quedarse abierto
tanto rato -- cualquier otro paso que lo guarde mientras tanto pisaría lo
que esto escribió. Acá sólo se baja y se guarda en JSONL; el catálogo se
toca después, en un rato y de una vez.

CÓMO LEE EL CATÁLOGO DE COPPEL
------------------------------
Del sitemap que la propia tienda publica para los buscadores, y de la ficha
de cada producto, el bloque JSON-LD que Coppel pone ahí para lo mismo. El
porqué, qué permite su robots.txt y qué familias entran está en
coppel_sitemap.py.

SE PUEDE CORTAR Y SEGUIR
------------------------
El JSONL se abre en modo "agregar" y al arrancar se leen las urls que ya
están dentro, así que volver a correrlo sigue donde se quedó. Con 350,000
fichas eso no es un lujo: es la única forma de que un corte de red no tire
seis horas de descarga.

RITMO
-----
Por omisión, tandas de 8 urls por llamada a curl (que reusa la conexión) y
medio segundo entre tandas. No es educación abstracta: una tienda que ve
350,000 peticiones en una hora corta el acceso, y el acceso es lo que hace
falta mantener todos los días para refrescar precios.

USO
---
    python3 scripts/cosechar_coppel.py --urls              # sólo junta urls
    python3 scripts/cosechar_coppel.py --familia celulares --limite 50
    python3 scripts/cosechar_coppel.py                     # todas las familias
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from coppel_sitemap import (  # noqa: E402
    FAMILIAS, PRIORITARIAS, RE_PDP, SITEMAP_INDICE, familia_de, id_de,
)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_TRABAJO = os.path.join(RAIZ, "data", "coppel")
URLS_JSON = os.path.join(DIR_TRABAJO, "urls.json")
FICHAS_JSONL = os.path.join(DIR_TRABAJO, "fichas.jsonl")

RE_LD = re.compile(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', re.S)

# Se baja con curl y no con urllib. No es capricho: por el proxy de salida de
# esta sesión, urllib y requests reciben "Remote end closed connection without
# response" contra coppel.com, y curl pasa. Además curl sabe bajar una tanda
# de urls reusando la misma conexión, que es lo que hace viable bajar
# cientos de miles de fichas: una conexión TLS nueva por ficha costaría más
# que la ficha.
#
# No se toca el User-Agent. Se probó poner uno de navegador y la petición
# muere con "HTTP/2 stream not closed cleanly" antes de llegar a Coppel:
# sólo pasan los agentes que empiezan por "curl/". Tampoco hace falta
# disfrazarse -- el agente propio de curl dice la verdad sobre qué está
# leyendo la página, que es lo que corresponde cuando uno entra por el
# sitemap que la tienda publica para que la lean.
CURL = shutil.which("curl") or "curl"


def bajar_tanda(urls, timeout=30):
    """[texto|None] en el mismo orden que `urls`, con una sola llamada a curl."""
    if not urls:
        return []
    tmp = tempfile.mkdtemp(prefix="coppel-")
    try:
        cmd = [CURL, "-sS", "--compressed", "--max-time", str(timeout),
               "--retry", "2", "--retry-delay", "1",
               "-H", "Accept-Language: es-MX,es;q=0.9"]
        destinos = []
        for n, u in enumerate(urls):
            destino = os.path.join(tmp, str(n))
            destinos.append(destino)
            cmd += ["-o", destino, u]
        try:
            subprocess.run(cmd, capture_output=True, timeout=timeout * len(urls) + 30)
        except subprocess.TimeoutExpired:
            pass
        salida = []
        for destino in destinos:
            try:
                with open(destino, encoding="utf-8", errors="replace") as f:
                    cuerpo = f.read()
                salida.append(cuerpo or None)
            except OSError:
                salida.append(None)
        return salida
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def bajar(url, timeout=30):
    return bajar_tanda([url], timeout)[0]


# ---------------------------------------------------------------------
# Paso 1: las urls
# ---------------------------------------------------------------------
def juntar_urls(familias_pedidas=None):
    """{familia: [url, ...]} leyendo el índice de sitemaps y cada archivo."""
    indice = bajar(SITEMAP_INDICE)
    if not indice:
        print("No se pudo leer el índice de sitemaps de Coppel.", file=sys.stderr)
        return {}
    archivos = re.findall(r"<loc>\s*([^<]+?)\s*</loc>", indice)
    salida = {}
    for archivo in archivos:
        fam = familia_de(archivo)
        if fam not in FAMILIAS:
            continue
        if familias_pedidas and fam not in familias_pedidas:
            continue
        cuerpo = bajar(archivo)
        if not cuerpo:
            print(f"  !! {archivo}: no se pudo leer", file=sys.stderr)
            continue
        urls = RE_PDP.findall(cuerpo)
        salida.setdefault(fam, []).extend(urls)
        print(f"  {len(urls):>7,}  {os.path.basename(archivo)}")
        time.sleep(0.4)
    # Una misma ficha puede estar en dos archivos de la misma familia.
    for fam in salida:
        salida[fam] = sorted(set(salida[fam]))
    return salida


# ---------------------------------------------------------------------
# Paso 2: las fichas
# ---------------------------------------------------------------------
def producto_de_ld(html):
    """El bloque JSON-LD @type:Product de la ficha, o None."""
    for bloque in RE_LD.findall(html or ""):
        try:
            obj = json.loads(bloque)
        except ValueError:
            continue
        candidatos = obj if isinstance(obj, list) else [obj]
        for c in candidatos:
            if isinstance(c, dict) and c.get("@type") == "Product":
                return c
    return None


def ficha_de(url, html):
    """El registro que se guarda en el JSONL, o None si la ficha no sirve."""
    if not html:
        return None
    prod = producto_de_ld(html)
    if not prod:
        return None
    oferta = prod.get("offers") or {}
    if isinstance(oferta, list):
        oferta = oferta[0] if oferta else {}
    precio = oferta.get("price")
    try:
        precio = float(str(precio).replace(",", ""))
    except (TypeError, ValueError):
        return None
    if not precio or precio <= 0:
        return None
    marca = prod.get("brand")
    if isinstance(marca, dict):
        marca = marca.get("name")
    disponible = "InStock" in str(oferta.get("availability") or "")
    return {
        "url": url,
        "id": id_de(url),
        "nombre": (prod.get("name") or "").strip(),
        "marca": (marca or "").strip() or None,
        "foto": prod.get("image") or None,
        "sku": prod.get("sku") or None,
        "precio": precio,
        "moneda": oferta.get("priceCurrency") or "MXN",
        "disponible": disponible,
    }


def ya_cosechadas():
    """Las urls que ya están en el JSONL, para poder seguir donde se cortó."""
    hechas = set()
    if not os.path.exists(FICHAS_JSONL):
        return hechas
    with open(FICHAS_JSONL, encoding="utf-8") as f:
        for linea in f:
            try:
                hechas.add(json.loads(linea)["url"])
            except (ValueError, KeyError):
                continue
    return hechas


def cosechar(urls, salida, tanda_n, pausa, familia):
    cuenta = {"ok": 0, "sin_ficha": 0}
    t0 = time.time()
    for i in range(0, len(urls), tanda_n):
        tanda = urls[i:i + tanda_n]
        for url, html in zip(tanda, bajar_tanda(tanda)):
            ficha = ficha_de(url, html)
            if ficha is None:
                cuenta["sin_ficha"] += 1
                continue
            ficha["familia"] = familia
            salida.write(json.dumps(ficha, ensure_ascii=False) + "\n")
            cuenta["ok"] += 1
        hechas = cuenta["ok"] + cuenta["sin_ficha"]
        if (i // max(tanda_n, 1)) % 10 == 0:
            salida.flush()
            ritmo = hechas / max(time.time() - t0, 1)
            faltan = (len(urls) - hechas) / max(ritmo, 0.01) / 60
            print(f"    {hechas:>7,}/{len(urls):,}  "
                  f"{ritmo:.1f}/s  faltan ~{faltan:.0f} min", flush=True)
        time.sleep(pausa)
    salida.flush()
    return cuenta


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--familia", action="append", default=[],
                    help="una familia del sitemap (se puede repetir); por "
                         "omisión, todas las de coppel_sitemap.FAMILIAS")
    ap.add_argument("--prioritarias", action="store_true",
                    help="sólo las familias de coppel_sitemap.PRIORITARIAS")
    ap.add_argument("--urls", action="store_true",
                    help="sólo juntar las urls y guardarlas, sin bajar fichas")
    ap.add_argument("--limite", type=int, default=0,
                    help="fichas por familia, para pruebas")
    ap.add_argument("--tanda", type=int, default=8,
                    help="urls por llamada a curl (reusan la conexión)")
    ap.add_argument("--pausa", type=float, default=0.5,
                    help="segundos entre tandas")
    args = ap.parse_args()

    os.makedirs(DIR_TRABAJO, exist_ok=True)
    pedidas = set(args.familia) or (set(PRIORITARIAS) if args.prioritarias else None)
    if pedidas:
        desconocidas = pedidas - set(FAMILIAS)
        if desconocidas:
            print(f"Familias desconocidas: {', '.join(sorted(desconocidas))}",
                  file=sys.stderr)
            return 2

    if os.path.exists(URLS_JSON) and not args.urls:
        with open(URLS_JSON, encoding="utf-8") as f:
            por_familia = json.load(f)
        print(f"urls.json: {sum(len(v) for v in por_familia.values()):,} urls "
              f"en {len(por_familia)} familias")
    else:
        print("Leyendo los sitemaps de Coppel…")
        por_familia = juntar_urls(pedidas)
        if not por_familia:
            return 1
        with open(URLS_JSON, "w", encoding="utf-8") as f:
            json.dump(por_familia, f, ensure_ascii=False)
        total = sum(len(v) for v in por_familia.values())
        print(f"\n{total:,} urls de producto en {len(por_familia)} familias "
              f"-> {os.path.relpath(URLS_JSON, RAIZ)}")
    if args.urls:
        return 0

    hechas = ya_cosechadas()
    if hechas:
        print(f"Ya cosechadas antes: {len(hechas):,} (se saltan)")

    total = {"ok": 0, "sin_ficha": 0}
    with open(FICHAS_JSONL, "a", encoding="utf-8") as salida:
        for fam in sorted(por_familia):
            if pedidas and fam not in pedidas:
                continue
            urls = [u for u in por_familia[fam] if u not in hechas]
            if args.limite:
                urls = urls[:args.limite]
            if not urls:
                continue
            print(f"\n== {fam}: {len(urls):,} fichas por bajar")
            c = cosechar(urls, salida, args.tanda, args.pausa, fam)
            print(f"   ok={c['ok']:,}  sin ficha={c['sin_ficha']:,}")
            for k in total:
                total[k] += c[k]

    print(f"\n=== {total['ok']:,} fichas guardadas en "
          f"{os.path.relpath(FICHAS_JSONL, RAIZ)} "
          f"({total['sin_ficha']:,} sin ficha legible) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
