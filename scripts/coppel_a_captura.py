#!/usr/bin/env python3
"""Pasa lo que bajó cosechar_coppel.py al formato que come el importador.

Es la bisagra entre las dos mitades: cosechar_coppel.py deja un JSONL con lo
que dice el JSON-LD de cada ficha de Coppel, y importar_captura_tienda.py
espera la misma forma que el marcador de Walmart --id, title, price, photo,
url, store-- para pasarlo por el clasificador y darlo de alta con sus
guardas.

Escribir esto en vez de un add_coppel_products.py propio no es pereza: el
importador genérico ya deduplica contra el catálogo, clasifica por título,
rechaza lo que no tiene precio y descarta el precio tres veces más caro que
lo más caro de su subcategoría. Un importador nuevo tendría que repetir esas
cuatro cosas, y la que se olvide es la que mete la basura.

QUÉ SE DESCARTA ACÁ
-------------------
Sólo lo que el importador no puede saber: la ficha sin existencia (Coppel la
deja publicada con precio, y un comparador que ofrezca un precio que no se
puede pagar miente) y la que no trae nombre. Todo lo demás --si es un
producto que el sitio compara, en qué categoría cae-- lo decide el
clasificador, que es donde viven las 158 reglas por título.

EL ENLACE DE AFILIADO
---------------------
Se envuelve acá, al convertir, con la base de afiliados.py. Es el mismo
deeplink que devuelve el generador del panel de Admitad: se comparó el
enlace que arma url_afiliado() con el que da el panel para la misma url y
son idénticos carácter por carácter, así que no hace falta pasar por el
panel ficha por ficha.

USO
---
    python3 scripts/coppel_a_captura.py --salida capturas/coppel-2026-09-21.json
    python3 scripts/coppel_a_captura.py --familia celulares --salida /tmp/c.json
"""
import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from afiliados import base_de  # noqa: E402
from coppel_sitemap import id_de  # noqa: E402
from cosechar_coppel import FICHAS_JSONL  # noqa: E402
from envios_coppel import ENVIOS_JSONL  # noqa: E402
from data_io import url_afiliado  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cargar_envios(ruta=ENVIOS_JSONL):
    """{url: datos de envío} de lo que leyó envios_coppel.py.

    Si el archivo no está, el lote entra sin dato de envío: es una sección
    de más en la oferta, no un requisito para importar.
    """
    if not os.path.exists(ruta):
        return {}
    por_url = {}
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            try:
                d = json.loads(linea)
            except ValueError:
                continue
            if d.get("url"):
                por_url[d["url"]] = d
    return por_url


def convertir(fichas, con_afiliado=True, envios=None):
    base = base_de("coppel") if con_afiliado else None
    envios = envios or {}
    vistos = set()
    salida, motivos = [], {"repetida": 0, "sin_nombre": 0, "agotada": 0, "sin_precio": 0}
    for f in fichas:
        # El id se recalcula desde la url en vez de creerle al JSONL: las
        # fichas cosechadas antes de que id_de() conociera el numerador
        # "-mkp-" (el 92% de las prioritarias) se guardaron con id nulo, y
        # son 55,000 que no hace falta volver a bajar para arreglar.
        pid = f.get("id") or id_de(f.get("url") or "")
        if not pid or pid in vistos:
            motivos["repetida"] += 1
            continue
        if not (f.get("nombre") or "").strip():
            motivos["sin_nombre"] += 1
            continue
        if not f.get("precio"):
            motivos["sin_precio"] += 1
            continue
        # Coppel deja publicada la ficha sin existencia, con su precio y
        # todo. Ofrecer un precio que no se puede pagar es peor que no
        # ofrecerlo: el comparador manda al comprador a una página que le
        # dice que no hay.
        if not f.get("disponible"):
            motivos["agotada"] += 1
            continue
        vistos.add(pid)
        item = {
            "store": "coppel",
            "id": pid,
            "title": f["nombre"].strip(),
            "price": f["precio"],
            "photo": f.get("foto") or None,
            "url": url_afiliado(base, f["url"]),
        }
        if f.get("marca"):
            item["brand"] = f["marca"]
        # Lo que la ficha dice del envío y de quién vende. En Coppel el 91%
        # de lo que entra lo vende un tercero en su marketplace y casi la
        # mitad de eso sale de fuera de México: ponerlo al lado del precio
        # de Amazon sin decirlo sería comparar dos cosas distintas.
        env = envios.get(f["url"])
        if env:
            if env.get("gratis") and not env.get("minimoGratis"):
                item["shippingFee"] = 0
            elif env.get("gratis") and env.get("minimoGratis"):
                item["freeShippingFromMXN"] = env["minimoGratis"]
            if env.get("internacional"):
                item["internacional"] = True
            if env.get("marketplace"):
                item["marketplace"] = True
        elif "-mkp-" in f["url"]:
            # Sin la pasada de envíos, al menos lo que dice la url.
            item["marketplace"] = True
            if "venta-internacional" in f["url"]:
                item["internacional"] = True
        salida.append(item)
    return salida, motivos


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--jsonl", default=FICHAS_JSONL)
    ap.add_argument("--familia", action="append", default=[],
                    help="quedarse sólo con estas familias del sitemap")
    ap.add_argument("--salida", help="por omisión capturas/coppel-<fecha>.json")
    ap.add_argument("--sin-afiliado", action="store_true",
                    help="guardar la url pelada de la tienda")
    args = ap.parse_args()

    if not os.path.exists(args.jsonl):
        print(f"No existe {args.jsonl}. Corre antes cosechar_coppel.py.",
              file=sys.stderr)
        return 1

    pedidas = set(args.familia)
    fichas = []
    with open(args.jsonl, encoding="utf-8") as f:
        for linea in f:
            try:
                d = json.loads(linea)
            except ValueError:
                continue
            if pedidas and d.get("familia") not in pedidas:
                continue
            fichas.append(d)

    envios = cargar_envios()
    if envios:
        print(f"envíos leídos: {len(envios):,}")
    items, motivos = convertir(fichas, con_afiliado=not args.sin_afiliado,
                               envios=envios)
    salida = args.salida or os.path.join(
        RAIZ, "capturas",
        f"coppel-{datetime.date.today().isoformat()}-{len(items)}.json")
    os.makedirs(os.path.dirname(salida), exist_ok=True)
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)

    print(f"leídas      {len(fichas):,}")
    for k, v in motivos.items():
        if v:
            print(f"  descartada por {k}: {v:,}")
    print(f"convertidas {len(items):,} -> {os.path.relpath(salida, RAIZ)}")
    if items:
        print(f"\nejemplo:\n  {items[0]['title'][:60]}\n  {items[0]['url'][:110]}")
    print("\nSigue:\n  python3 scripts/importar_captura_tienda.py "
          f"{os.path.relpath(salida, RAIZ)} --dry-run")
    return 0


if __name__ == "__main__":
    sys.exit(main())
