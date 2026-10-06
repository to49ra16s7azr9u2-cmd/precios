#!/usr/bin/env python3
"""Ficha técnica de Coppel para las fichas que no tienen ninguna.

POR QUÉ
-------
El 05-oct-2026, de 132 mil fichas que sólo vende Coppel, 3 tenían
especificaciones: cosechar_coppel.py lee del bloque JSON-LD nombre, marca,
foto y precio, y la ficha técnica no viene ahí. Pero la página sí la trae,
estructurada, en el JSON con el que se dibuja la sección «Especificaciones»:

    "specs":[{"name":"Memoria RAM","values":[{"value":"8 GB",...}]}, ...]

CÓMO
----
La misma lectura que cosechar_coppel.py (curl en tandas que reusan la
conexión, con su ritmo), sólo de las fichas del catálogo con oferta de
Coppel y sin especificaciones. Dos pasos, para que un reinicio no tire lo
bajado:

    python3 scripts/specs_coppel.py --bajar     # -> caché JSONL, reanudable
    python3 scripts/specs_coppel.py --aplicar   # caché -> catálogo

Mismos filtros que elektra_specs.py: sin valores largos ni campos con más de
un valor, y como mucho MAX_SPECS renglones. La marca se omite (la ficha ya
la muestra).

SÓLO LO QUE VENDE COPPEL
------------------------
En una muestra al azar de 160, el 89% de las fichas del marketplace («-mkp-»)
traía sólo Medidas, Material y Color, que el vendedor llena de oficio (más de
una dice «10x10x10»). Eso no es una ficha técnica y no se guarda (GENERICOS).
Las que vende Coppel («-pm-», ~5,000) sí traen modelo, capacidad, piezas,
funciones: por omisión se bajan sólo ésas (--todas para el resto).
"""
import argparse
import re
import concurrent.futures
import json
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from cosechar_coppel import bajar_tanda, es_ficha_retirada  # noqa: E402
from data_io import load_catalog, save_catalog, url_real  # noqa: E402
from elektra_specs import MAX_SPECS, MAX_VALOR, _limpia  # noqa: E402

CACHE = "/tmp/coppel_specs/specs_por_url.jsonl"
OMITIR = {"marca"}
GENERICOS = {"medidas", "material", "color"}
# Lo que el vendedor pone de oficio para llenar el campo: «N/A», «No aplica»,
# «0», y medidas con los tres lados iguales y redondos («10x10x10»,
# «1x1x1»), que no son las de ningún producto real.
_RELLENO = re.compile(r"^(n/?a|no aplica|na|sin dato|ninguno|ninguna|-+|0|\.)$", re.I)
_MEDIDA_RELLENO = re.compile(r"^\s*(\d{1,3})\s*(cm)?\s*x\s*\1\s*(cm)?\s*x\s*\1\s*(cm)?\s*$", re.I)
_DEC = json.JSONDecoder()


def specs_de_html(html):
    """[{"label", "value"}] de la sección Especificaciones, o []."""
    i = (html or "").find('"specs":[')
    if i < 0:
        return []
    try:
        lista, _ = _DEC.raw_decode(html, i + len('"specs":'))
    except ValueError:
        return []
    out = []
    for c in lista if isinstance(lista, list) else []:
        nombre = _limpia(c.get("name") or "")
        valores = [v for v in c.get("values") or [] if isinstance(v, dict)]
        if not nombre or nombre.lower() in OMITIR or len(valores) != 1:
            continue
        valor = _limpia(valores[0].get("value") or valores[0].get("name") or "")
        if not valor or len(valor) > MAX_VALOR or _RELLENO.search(valor):
            continue
        if nombre.lower() == "medidas" and _MEDIDA_RELLENO.match(valor):
            continue
        out.append({"label": nombre, "value": valor})
        if len(out) >= MAX_SPECS:
            break
    return out


def faltantes(data):
    """{url de coppel.com: [id de ficha]} de las fichas sin especificaciones."""
    out = {}
    for p in data["products"]:
        if p.get("specs"):
            continue
        for o in p.get("offers") or []:
            if o.get("storeId") == "coppel":
                u = url_real(o.get("url") or "") or o.get("url")
                if u and u.startswith("https://www.coppel.com/"):
                    out.setdefault(u, []).append(p["id"])
    return out


def leer_cache():
    vistos = {}
    if os.path.exists(CACHE):
        with open(CACHE, encoding="utf-8") as f:
            for linea in f:
                try:
                    d = json.loads(linea)
                except ValueError:
                    continue
                vistos[d["url"]] = d.get("specs") or []
    return vistos


def bajar(urls, tanda_n, paralelas, pausa, limite):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    hechos = leer_cache()
    pendientes = [u for u in urls if u not in hechos]
    if limite:
        pendientes = pendientes[:limite]
    print(f"Fichas de Coppel sin ficha técnica: {len(urls):,}; ya en caché: {len(hechos):,}; "
          f"por bajar: {len(pendientes):,}", flush=True)
    con = sin_html = 0
    t0 = time.time()
    bloque = tanda_n * paralelas
    with open(CACHE, "a", encoding="utf-8") as f, \
            concurrent.futures.ThreadPoolExecutor(max_workers=paralelas) as pool:
        for i in range(0, len(pendientes), bloque):
            grupo = pendientes[i:i + bloque]
            tandas = [grupo[j:j + tanda_n] for j in range(0, len(grupo), tanda_n)]
            for tanda, cuerpos in zip(tandas, pool.map(bajar_tanda, tandas)):
                for u, html in zip(tanda, cuerpos):
                    if html is None:
                        # Sin respuesta: no se anota y se reintenta otro día.
                        sin_html += 1
                        continue
                    ficha = [] if es_ficha_retirada(html) else specs_de_html(html)
                    con += bool(ficha)
                    f.write(json.dumps({"url": u, "specs": ficha}, ensure_ascii=False) + "\n")
            f.flush()
            if (i // bloque) % 50 == 0:
                hechas = i + len(grupo)
                print(f"  {hechas:,}/{len(pendientes):,}  con ficha {con:,}  sin respuesta {sin_html:,}  "
                      f"{hechas / max(time.time() - t0, 1):.1f}/s", flush=True)
            time.sleep(pausa)
    print(f"Bajado: {len(pendientes):,} fichas, {con:,} con ficha técnica; sin respuesta {sin_html:,}")


def aplicar(data, mapa, dry_run, con_genericos=False):
    cache = leer_cache()
    por_id = {p["id"]: p for p in data["products"]}
    llenas = campos = 0
    for u, ids in mapa.items():
        ficha = cache.get(u)
        if not ficha or (not con_genericos and all(x["label"].lower() in GENERICOS for x in ficha)):
            continue
        for pid in ids:
            p = por_id[pid]
            if not p.get("specs"):
                p["specs"] = ficha
                llenas += 1
                campos += len(ficha)
    con = sum(1 for p in data["products"] if p.get("specs"))
    print(f"Fichas que ganan ficha técnica: {llenas:,} ({campos:,} campos); "
          f"con especificaciones: {con:,} de {len(data['products']):,} ({con / len(data['products']):.0%})")
    if dry_run:
        print("(--dry-run: no se escribió nada)")
        return
    save_catalog(data)
    print("Guardado.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bajar", action="store_true")
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--tanda", type=int, default=8)
    ap.add_argument("--paralelas", type=int, default=5)
    ap.add_argument("--pausa", type=float, default=0.4)
    ap.add_argument("--limite", type=int, default=0, help="sólo las primeras N fichas (prueba)")
    ap.add_argument("--todas", action="store_true", help="también las del marketplace (-mkp-)")
    ap.add_argument("--con-genericos", action="store_true",
                    help="aplicar también las fichas que sólo traen medidas, material y color (sin relleno)")
    args = ap.parse_args()
    if not (args.bajar or args.aplicar):
        ap.error("--bajar y/o --aplicar")
    data = load_catalog()
    mapa = faltantes(data)
    if args.bajar:
        urls = sorted(u for u in mapa if args.todas or "-pm-" in u)
        bajar(urls, args.tanda, args.paralelas, args.pausa, args.limite)
    if args.aplicar:
        aplicar(data, mapa, args.dry_run, args.con_genericos)
    return 0


if __name__ == "__main__":
    sys.exit(main())
