#!/usr/bin/env python3
"""Avisa a Bing (y a los demás buscadores de IndexNow: Yandex, Seznam,
Naver...) de las páginas nuevas o cambiadas, en vez de esperar a que las
vuelvan a rastrear (pedido del usuario, 26-sep-2026).

CÓMO
----
IndexNow pide una clave publicada en la raíz del sitio: el archivo
/0a95a0d1bb21ba0903efc6e089a2aaf0.txt, que contiene la clave y nada más. La clave NO es secreta
(cualquiera la puede leer; solo prueba que el aviso viene del dueño del
sitio), por eso vive en el repositorio.

Se leen los sitemaps (sitemap-*.xml, con <lastmod> por página) y se avisan
las urls cuyo lastmod cambió desde el último aviso. Lo avisado queda en
data/indexnow-enviado.json (url -> lastmod), fuera del sitio publicado. La
primera corrida avisa todo (~22 mil urls, en tandas de 10 mil).

CUÁNDO CORRERLO
---------------
DESPUÉS de publicar (git push) y de que GitHub Pages termine de desplegar:
el buscador va a pedir la página y la clave en ese momento.

    python3 scripts/indexnow.py            # muestra cuántas avisaría
    python3 scripts/indexnow.py --enviar   # avisa de verdad
Tras enviar, commitear data/indexnow-enviado.json con el próximo cambio.
"""
import argparse
import glob
import json
import os
import re
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = "comparamex.com"
CLAVE = "0a95a0d1bb21ba0903efc6e089a2aaf0"
REGISTRO = os.path.join(ROOT, "data", "indexnow-enviado.json")
ENDPOINT = "https://api.indexnow.org/indexnow"
TANDA = 10000          # máximo de urls por aviso según el protocolo


def urls_del_sitemap():
    out = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "sitemap-*.xml"))):
        texto = open(f, encoding="utf-8").read()
        for bloque in re.findall(r"<url>(.*?)</url>", texto, re.S):
            loc = re.search(r"<loc>(.*?)</loc>", bloque)
            mod = re.search(r"<lastmod>(.*?)</lastmod>", bloque)
            if loc:
                out[loc.group(1).strip()] = mod.group(1).strip() if mod else ""
    return out


def avisar(urls):
    cuerpo = json.dumps({"host": HOST, "key": CLAVE,
                         "keyLocation": f"https://{HOST}/{CLAVE}.txt",
                         "urlList": urls}).encode()
    req = urllib.request.Request(ENDPOINT, data=cuerpo,
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--enviar", action="store_true")
    args = ap.parse_args()
    if not os.path.isfile(os.path.join(ROOT, CLAVE + ".txt")):
        sys.exit(f"falta el archivo de la clave {CLAVE}.txt en la raíz")
    actuales = urls_del_sitemap()
    registro = json.load(open(REGISTRO, encoding="utf-8")) if os.path.isfile(REGISTRO) else {}
    pendientes = [u for u, m in actuales.items() if registro.get(u) != m]
    print(f"urls en los sitemaps: {len(actuales):,}; a avisar: {len(pendientes):,}")
    if not args.enviar or not pendientes:
        return
    for i in range(0, len(pendientes), TANDA):
        tanda = pendientes[i:i + TANDA]
        try:
            estado = avisar(tanda)
        except urllib.error.HTTPError as e:
            # 400 formato, 403 clave no encontrada/no válida, 422 urls de otro
            # host, 429 demasiados avisos: se corta y se reintenta otro día.
            print(f"IndexNow respondió {e.code}: {e.read()[:300]!r}")
            break
        print(f"tanda {i // TANDA + 1}: {len(tanda):,} urls -> HTTP {estado}")
        for u in tanda:
            registro[u] = actuales[u]
    with open(REGISTRO, "w", encoding="utf-8") as f:
        json.dump(registro, f, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


if __name__ == "__main__":
    main()
