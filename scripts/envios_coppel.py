#!/usr/bin/env python3
"""Lee de cada ficha de Coppel qué dice sobre el envío, y quién vende.

POR QUÉ HACE FALTA UNA PASADA APARTE
------------------------------------
El JSON-LD que lee cosechar_coppel.py trae nombre, marca, foto y precio,
pero no dice nada del envío. Y en Coppel eso importa más que en las otras
tiendas del catálogo: de las fichas que entran, el 91% no las vende Coppel
sino un tercero en su marketplace, y casi la mitad de esas se envían desde
fuera de México. Publicar ese precio al lado del de Amazon sin decirlo sería
comparar dos cosas distintas.

QUÉ SE LEE
----------
El bloque `data-testid="pdp_delivery"` de la ficha, que es el mismo texto
que ve quien entra a comprar. En 60 fichas al azar salieron cuatro
variantes, todas gratis:

    30  Envío internacional gratis
    20  Envío gratis*
     8  Envío gratis a partir de $499*
     2  Envío internacional gratis a partir de $499*

O sea que Coppel no cobra envío por ninguno de estos productos; lo que
cambia es si hay mínimo de compra y si sale de México. Por eso lo que se
guarda es el texto tal cual y dos banderas derivadas de él, y no un monto:
inventar un costo donde la tienda dice "gratis" sería peor dato que no
tener ninguno.

SE PUEDE CORTAR Y SEGUIR
------------------------
Igual que la cosecha: el JSONL se abre en modo "agregar" y al arrancar se
saltan las urls que ya están dentro.

USO
---
    python3 scripts/envios_coppel.py capturas/coppel-2026-09-21.json
    python3 scripts/envios_coppel.py --urls-de data/coppel/fichas.jsonl
"""
import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cosechar_coppel import DIR_TRABAJO, bajar_tanda  # noqa: E402
from data_io import url_real  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENVIOS_JSONL = os.path.join(DIR_TRABAJO, "envios.jsonl")

RE_ENTREGA = re.compile(
    r'data-testid="pdp_delivery"[^>]*>(.*?)</strong>', re.S)
RE_ETIQUETAS = re.compile(r"<[^>]+>")
# "a partir de $499" -> el mínimo de compra para que el envío salga gratis.
RE_MINIMO = re.compile(r"a partir de \$\s*([\d,]+)")


def texto_de_envio(html):
    m = RE_ENTREGA.search(html or "")
    if not m:
        return None
    return " ".join(RE_ETIQUETAS.sub("", m.group(1)).split()).strip() or None


def datos_de_envio(url, html):
    texto = texto_de_envio(html)
    if not texto:
        return None
    bajo = texto.lower()
    minimo = RE_MINIMO.search(bajo)
    return {
        "url": url,
        "envio": texto,
        # El slug de la url y el texto de la ficha dicen lo mismo; se miran
        # los dos porque el slug está en todas las urls que ya tenemos y el
        # texto es el que ve el comprador.
        "internacional": "internacional" in bajo or "venta-internacional" in url,
        "marketplace": "-mkp-" in url,
        "gratis": "gratis" in bajo,
        "minimoGratis": int(minimo.group(1).replace(",", "")) if minimo else None,
    }


def urls_pedidas(rutas, urls_de):
    urls = []
    for ruta in rutas or []:
        for it in json.load(open(ruta, encoding="utf-8")):
            u = url_real(it.get("url") or "") or it.get("url")
            if u:
                urls.append(u)
    if urls_de:
        for linea in open(urls_de, encoding="utf-8"):
            try:
                urls.append(json.loads(linea)["url"])
            except (ValueError, KeyError):
                continue
    vistas, salida = set(), []
    for u in urls:
        if u not in vistas:
            vistas.add(u)
            salida.append(u)
    return salida


def ya_hechas():
    if not os.path.exists(ENVIOS_JSONL):
        return set()
    hechas = set()
    with open(ENVIOS_JSONL, encoding="utf-8") as f:
        for linea in f:
            try:
                hechas.add(json.loads(linea)["url"])
            except (ValueError, KeyError):
                continue
    return hechas


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("capturas", nargs="*", help="json(s) en formato de captura")
    ap.add_argument("--urls-de", help="JSONL de cosechar_coppel.py")
    ap.add_argument("--tanda", type=int, default=8)
    ap.add_argument("--paralelas", type=int, default=5)
    ap.add_argument("--pausa", type=float, default=0.4)
    args = ap.parse_args()

    urls = urls_pedidas(args.capturas, args.urls_de)
    if not urls:
        print("Nada que leer.", file=sys.stderr)
        return 1
    hechas = ya_hechas()
    faltan = [u for u in urls if u not in hechas]
    print(f"{len(urls):,} urls; ya leídas {len(hechas):,}; por leer {len(faltan):,}")
    if not faltan:
        return 0

    import concurrent.futures
    bloque = args.tanda * args.paralelas
    ok = sin = 0
    t0 = time.time()
    os.makedirs(DIR_TRABAJO, exist_ok=True)
    with open(ENVIOS_JSONL, "a", encoding="utf-8") as salida, \
            concurrent.futures.ThreadPoolExecutor(max_workers=args.paralelas) as pool:
        for i in range(0, len(faltan), bloque):
            grupo = faltan[i:i + bloque]
            tandas = [grupo[j:j + args.tanda] for j in range(0, len(grupo), args.tanda)]
            for tanda, cuerpos in zip(tandas, pool.map(bajar_tanda, tandas)):
                for u, html in zip(tanda, cuerpos):
                    d = datos_de_envio(u, html)
                    if d is None:
                        sin += 1
                        continue
                    salida.write(json.dumps(d, ensure_ascii=False) + "\n")
                    ok += 1
            if (i // max(bloque, 1)) % 10 == 0:
                salida.flush()
                hechas_n = ok + sin
                ritmo = hechas_n / max(time.time() - t0, 1)
                print(f"    {hechas_n:>7,}/{len(faltan):,}  {ritmo:.1f}/s  "
                      f"faltan ~{(len(faltan) - hechas_n) / max(ritmo, 0.01) / 60:.0f} min",
                      flush=True)
            time.sleep(args.pausa)
    print(f"\n=== {ok:,} fichas con dato de envío en "
          f"{os.path.relpath(ENVIOS_JSONL, RAIZ)} ({sin:,} sin el dato) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
