#!/usr/bin/env python3
"""Enlaces internos rotos en las páginas estáticas del sitio.

Recorre todos los .html del sitio (menos data/ y node_modules/), saca cada
href y src relativo o con / al principio, y mira que exista el archivo al que
apunta (una carpeta vale si tiene index.html). Lo externo (http, mailto, tel,
javascript), las anclas (#...) y las rutas del SPA (#/...) no se miran.

Se corre antes de cada publicación: la cifra que importa es la última línea,
"enlaces rotos: N / M en P páginas", y tiene que ser 0.

    python3 scripts/verificar_enlaces.py            # resumen
    python3 scripts/verificar_enlaces.py --lista 50 # y los primeros 50 rotos
"""
import argparse
import os
import re
import sys
from urllib.parse import unquote, urlsplit

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
FUERA = {"data", "node_modules", ".git", ".github", "scripts"}
RX = re.compile(r'\b(?:href|src)="([^"]+)"')


def existe(destino):
    if os.path.isdir(destino):
        return os.path.exists(os.path.join(destino, "index.html"))
    return os.path.exists(destino)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lista", type=int, default=0)
    args = ap.parse_args()
    paginas = enlaces = 0
    rotos = []
    for base, dirs, archivos in os.walk(RAIZ):
        if base == RAIZ:
            dirs[:] = [d for d in dirs if d not in FUERA]
        for a in archivos:
            if not a.endswith(".html"):
                continue
            ruta = os.path.join(base, a)
            paginas += 1
            with open(ruta, encoding="utf-8", errors="replace") as f:
                html = f.read()
            for u in RX.findall(html):
                if re.match(r"^(?:[a-z][a-z0-9+.-]*:|//|#)", u, re.I) or "${" in u or "' +" in u:
                    continue
                camino = unquote(urlsplit(u).path)
                if not camino:
                    continue
                enlaces += 1
                destino = os.path.join(RAIZ, camino.lstrip("/")) if camino.startswith("/") \
                    else os.path.normpath(os.path.join(base, camino))
                if not existe(destino):
                    rotos.append((os.path.relpath(ruta, RAIZ), u))
    for r in rotos[:args.lista]:
        print("  ", *r)
    print(f"enlaces rotos: {len(rotos)} / {enlaces} en {paginas} páginas")
    sys.exit(1 if rotos else 0)


if __name__ == "__main__":
    main()
