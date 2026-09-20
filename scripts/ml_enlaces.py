#!/usr/bin/env python3
"""Arma el mapa url de producto -> enlace de afiliado de Mercado Libre.

POR QUÉ NO ALCANZA CON EL ORDEN
-------------------------------
Mercado Libre no tiene API de afiliados: el panel genera los enlaces de a 30
en el navegador y devuelve una lista suelta, sin decir a qué producto
corresponde cada uno. Lo natural es emparejar por posición, y eso se probó
primero: SALIÓ MAL. De 140 enlaces, 56 quedaron apuntando a otro producto --
el 40%. La lista que devuelve el panel no conserva el orden de entrada de
forma confiable, y además intercala una línea de rechazo por cada producto no
elegible, lo que corre todo lo que sigue.

Emparejar mal no es un detalle: la ficha de un producto terminaría mandando
al comprador a otro distinto. Por eso acá no se usa la posición para nada.

CÓMO SE EMPAREJA
----------------
Por contenido, cruzando dos fuentes que las dos vienen de Mercado Libre:

  1. Cada enlace se abre y se lee su <meta property="og:title">, que es el
     nombre del producto destacado en esa página.
  2. Para cada url de entrada se pide el título oficial a la API
     (el worker de ml_discover.py).

Si los dos títulos normalizados son idénticos, es el mismo producto. Lo que
no empareja de forma única se deja afuera: dos variantes con el NOMBRE exacto
igual (pasó con dos labiales NYX) no se pueden distinguir así, y adivinar
sería justo el error que este script existe para evitar.

USO
---
    python3 scripts/ml_enlaces.py --entrada urls.txt --salida enlaces.txt
    python3 scripts/ml_enlaces.py --entrada urls.txt --salida enlaces.txt --dry-run
"""
import argparse
import collections
import concurrent.futures as cf
import html
import json
import os
import re
import subprocess
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

WORKER = "https://comparamx-mercadolibre-proxy.comparamx.workers.dev/item?id="
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")
RX_OG = re.compile(r'property="og:title"[^>]*content="([^"]*)"')


def norm(s):
    # Doble unescape: el og:title llega con &quot; y a veces &amp;quot;.
    s = html.unescape(html.unescape(s or ""))
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


def _curl(url, timeout="40"):
    return subprocess.run(["curl", "-sSL", "--compressed", "--max-time", timeout,
                           "-A", UA, "-H", "Accept-Language: es-MX,es;q=0.9", url],
                          capture_output=True, text=True).stdout


def og_title(enlace):
    m = RX_OG.search(_curl(enlace))
    return enlace, (m.group(1) if m else None)


def titulo_api(mlm):
    try:
        return mlm, json.loads(_curl(WORKER + mlm)).get("title")
    except Exception:
        return mlm, None


def titulos_de_entrada(ids, ogs):
    """Pide el título de cada url de entrada, por bloques y en orden.

    POR QUÉ POR BLOQUES: el worker tiene tope diario (100,000 peticiones,
    se reinicia a las 00:00 UTC) y pedir los 3,000 títulos de todos los
    lotes en cada corrida se lo come sin necesidad. Los lotes van en orden
    de prioridad y el panel se llena de arriba hacia abajo, así que los
    enlaces devueltos casi siempre salen de los primeros: se corta apenas
    no quedan enlaces por emparejar, o cuando tres bloques seguidos no
    emparejan ninguno más.

    NO HAY SEGUNDA FUENTE: la página del producto (mercadolibre.com.mx/p/…)
    contesta con la pantalla de verificación de cuenta, sin og:title, así
    que si el worker está en 429 no se puede emparejar y hay que esperar al
    reinicio. Se avisa en vez de emparejar a ciegas.
    """
    api, faltan, sin_avance, BLOQUE = {}, {norm(t) for t in ogs.values() if t}, 0, 250
    for i in range(0, len(ids), BLOQUE):
        with cf.ThreadPoolExecutor(max_workers=5) as ex:
            bloque = dict(ex.map(titulo_api, ids[i:i + BLOQUE]))
        api.update(bloque)
        if not any(bloque.values()):
            print("  el worker no devolvió ni un título: suele ser el tope diario "
                  "(429, se reinicia a las 00:00 UTC). Vuelve a correrlo después.")
            break
        antes = len(faltan)
        for t in bloque.values():
            if t:
                faltan.discard(norm(t))
        print(f"  títulos leídos: {min(i + BLOQUE, len(ids)):,}/{len(ids):,}   "
              f"enlaces por emparejar: {len(faltan)}")
        if not faltan:
            break
        sin_avance = sin_avance + 1 if len(faltan) == antes else 0
        if sin_avance >= 3:
            break
    return api


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entrada", required=True, help="las urls que se pegaron en el panel")
    ap.add_argument("--salida", required=True, help="lo que devolvió el panel")
    ap.add_argument("--mapa", default="data/ml-afiliados.json")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    urls = [l.strip() for l in open(args.entrada, encoding="utf-8")
            if l.strip().startswith("http")]
    enlaces = [l.strip() for l in open(args.salida, encoding="utf-8")
               if l.strip().startswith("http")]
    print(f"urls de entrada: {len(urls)}   enlaces devueltos: {len(enlaces)}")

    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        ogs = dict(ex.map(og_title, enlaces))
    faltan = [e for e, t in ogs.items() if not t]
    if faltan:
        print(f"  sin og:title (no se pueden emparejar): {len(faltan)}")

    ids = [u.rsplit("/", 1)[-1] for u in urls]
    api = titulos_de_entrada(ids, ogs)

    por_titulo = collections.defaultdict(list)
    for mlm, t in api.items():
        if t:
            por_titulo[norm(t)].append(mlm)

    mapa, ambiguos, sin = {}, [], []
    for enlace, t in ogs.items():
        if not t:
            continue
        cand = por_titulo.get(norm(t))
        if cand and len(cand) == 1:
            mapa[f"https://www.mercadolibre.com.mx/p/{cand[0]}"] = enlace
        elif cand:
            ambiguos.append(t)
        else:
            sin.append(t)

    print(f"emparejados: {len(mapa)}   ambiguos: {len(ambiguos)}   sin coincidencia: {len(sin)}")
    for t in ambiguos[:5]:
        print(f"  ambiguo (dos productos con el mismo nombre): {t[:70]}")
    for t in sin[:5]:
        print(f"  sin coincidencia: {t[:70]}")

    if args.dry_run:
        print("\n--dry-run: no se escribió nada")
        return
    if not mapa:
        print("\nnada que escribir")
        return

    previo = {}
    if os.path.exists(args.mapa):
        with open(args.mapa, encoding="utf-8") as f:
            previo = json.load(f)
    nuevos = sum(1 for k in mapa if k not in previo)
    previo.update(mapa)
    os.makedirs(os.path.dirname(args.mapa) or ".", exist_ok=True)
    with open(args.mapa, "w", encoding="utf-8") as f:
        json.dump(previo, f, ensure_ascii=False, indent=1, sort_keys=True)
    print(f"\n{args.mapa}: {len(previo)} enlaces ({nuevos} nuevos)")
    print("Ahora: python3 scripts/aplicar_afiliados.py --tienda mercadolibre")


if __name__ == "__main__":
    main()
