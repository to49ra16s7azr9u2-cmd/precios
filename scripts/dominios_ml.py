#!/usr/bin/env python3
"""Recupera el domain_id de Mercado Libre de cada ficha que vino de ahí.

PARA QUÉ
--------
Mercado Libre tiene su propia taxonomía, hecha para México y mucho más fina
que la nuestra en algunos rubros ("MLM-DRILL_BITS" son las brocas,
"MLM-BOOKCASES" los libreros). ml_discover.py ya la usa para BUSCAR, y de
paso CONFIRMA cada dominio contra nuestro catálogo: de los 102 confirmados,
63 apuntan a una sola subcategoría nuestra con 100% de acuerdo.

Lo que faltaba era saber a qué dominio pertenece cada ficha nuestra. Con
eso, esos 63 dominios dejan de ser una curiosidad y pasan a ser una segunda
opinión sobre la subcategoría, hecha por quien vende el producto.

CÓMO SE LLEGÓ ACÁ (y qué caminos no sirven)
-------------------------------------------
  /items/MLM…              403. Mercado Libre lo cerró con su PolicyAgent,
                           con token y sin token.
  /sites/MLM/search?q=…    403, lo mismo.
  /catalog?domain=…        200, pero es el camino inverso: hay que saber el
                           dominio para pedir, y devuelve pocas fichas por
                           consulta. Cruzando por itemId no coincidió nada.
  /products/<id>           200 CON TOKEN, y trae "domain_id". Este sirve.

La clave es que 60,009 de nuestras 61,415 fichas de Mercado Libre guardan
la url del producto de CATÁLOGO (`/p/MLM67286583`), no la de una
publicación suelta. Ese id es justo el que /products/<id> acepta.

RITMO Y CUOTA
-------------
El Worker tiene un tope de 100,000 peticiones por día que se reinicia a las
00:00 UTC; pasado el tope contesta el error 1027 de Cloudflare. 60,009
consultas caben en un día, pero hay que dejar margen para el refresco de
precios, así que por omisión se para en 40,000 y se puede seguir al día
siguiente: lo ya consultado se guarda y no se vuelve a pedir.

USO
---
    python3 scripts/dominios_ml.py --limite 200      # prueba
    python3 scripts/dominios_ml.py                   # tanda del día
"""
import argparse
import collections
import concurrent.futures
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, url_real  # noqa: E402

BASE = "https://comparamx-mercadolibre-proxy.comparamx.workers.dev"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "data", "ml-dominios-producto.json")

RE_CAT = re.compile(r"/p/(MLM\d+)")
RE_DOMINIO = re.compile(r'"domain_id":"(MLM-[A-Z0-9_]+)"')
CURL = "curl"


def ids_del_catalogo(products):
    """{id de producto nuestro: id de catálogo de Mercado Libre}"""
    out = {}
    for p in products:
        for o in (p.get("offers") or []):
            if o.get("storeId") != "mercadolibre":
                continue
            m = RE_CAT.search(url_real(o.get("url", "")) or o.get("url", ""))
            if m:
                out[p["id"]] = m.group(1)
            break
    return out


def pedir(mlm_id, timeout=40):
    """domain_id de ese producto de catálogo, o None.

    Va por /probe porque /products/<id> sólo contesta CON TOKEN, y el token
    vive en el Worker: el proxy lo pone y nosotros nunca lo vemos.
    """
    inner = f"/products/{mlm_id}"
    url = f"{BASE}/probe?path={urllib.parse.quote(inner, safe='')}"
    try:
        r = subprocess.run([CURL, "-sS", "--max-time", str(timeout), url],
                           capture_output=True, timeout=timeout + 10)
        d = json.loads(r.stdout)
    except Exception:
        return None
    cuerpo = (d.get("con_token") or {}).get("body") or ""
    # El Worker recorta el cuerpo de /probe a 1200 caracteres, así que el
    # JSON llega partido y json.loads() falla siempre. Por eso se saca el
    # campo con una expresión regular, igual que hace ml_domains.py con los
    # pares de domain_discovery.
    m = RE_DOMINIO.search(cuerpo)
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limite", type=int, default=40000,
                    help="consultas de esta corrida (por omisión %(default)s)")
    ap.add_argument("--paralelas", type=int, default=6)
    ap.add_argument("--pausa", type=float, default=0.1)
    args = ap.parse_args()

    data = load_catalog()
    pares = ids_del_catalogo(data["products"])
    print(f"fichas de Mercado Libre con id de catálogo: {len(pares):,}")

    ya = {}
    if os.path.exists(SALIDA):
        with open(SALIDA, encoding="utf-8") as f:
            ya = json.load(f)
        print(f"ya consultadas antes: {len(ya):,}")

    faltan = [(pid, mlm) for pid, mlm in pares.items() if mlm not in ya][:args.limite]
    if not faltan:
        print("nada por consultar")
        return 0
    print(f"por consultar en esta corrida: {len(faltan):,}\n")

    t0 = time.time()
    hechas = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.paralelas) as pool:
        bloque = args.paralelas * 4
        for i in range(0, len(faltan), bloque):
            grupo = faltan[i:i + bloque]
            for (pid, mlm), dom in zip(grupo, pool.map(lambda t: pedir(t[1]), grupo)):
                ya[mlm] = dom or ""
                hechas += 1
            if (i // max(bloque, 1)) % 20 == 0:
                with open(SALIDA, "w", encoding="utf-8") as f:
                    json.dump(ya, f, ensure_ascii=False)
                ritmo = hechas / max(time.time() - t0, 1)
                con = sum(1 for v in ya.values() if v)
                print(f"    {hechas:>7,}/{len(faltan):,}  {ritmo:.1f}/s  "
                      f"con dominio: {con:,}  faltan ~{(len(faltan)-hechas)/max(ritmo,0.01)/60:.0f} min",
                      flush=True)
            time.sleep(args.pausa)
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(ya, f, ensure_ascii=False)
    con = collections.Counter(v for v in ya.values() if v)
    print(f"\n=== {sum(con.values()):,} fichas con dominio, {len(con)} dominios distintos ===")
    for k, n in con.most_common(12):
        print(f"   {n:>6,}  {k}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
