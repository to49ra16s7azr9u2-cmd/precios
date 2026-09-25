#!/usr/bin/env python3
"""Precios del día de las tiendas que vienen por Soicos (Walmart, Bodega
Aurrerá y su Despensa, Sam's Club, Sephora, Lenovo, Reuse), para la corrida
diaria (.github/workflows/refresh-precios.yml).

POR QUÉ UN SCRIPT APARTE DE refrescar_soicos.py
-----------------------------------------------
refrescar_soicos.py come la captura completa de soicos_a_captura.py (con
nombre, foto, marca...) y carga el catálogo una vez por tienda: sirve para
una tienda a mano, no para las 1.7 millones de filas de los siete feeds cada
día. Acá se baja sólo lo que hace falta para el precio (url, precio, precio
anterior, stock), en paralelo y sin tocar el catálogo, y después se aplica
todo junto con una sola carga. Las dos mitades están separadas para que la
bajada (~2 h, casi toda espera de red) corra en segundo plano mientras el
workflow refresca Mercado Libre y las tiendas VTEX.

QUÉ SE CAMBIA
-------------
Por cada oferta del catálogo de esas tiendas cuya url de la tienda (la que
va dentro del deeplink, dl=) está en el feed con stock: precio, precio
anterior (sólo si es mayor), stock y el deeplink vigente. Lo que el feed ya
no trae, o trae agotado, se deja como está -- igual que refresh_vtex.py con
--no-prune: el sitio no borra fichas por agotarse.

EL TOKEN NO VA AL REPOSITORIO
-----------------------------
SOICOS_TOKEN y SOICOS_AID se leen del entorno (en GitHub, de los secretos
del repositorio). Sin ellos la bajada avisa y sale con 0: la corrida sigue
con las demás tiendas. El archivo que se baja no lleva credenciales.

USO
---
    python3 scripts/soicos_precios.py --bajar /tmp/soicos.json.gz
    python3 scripts/soicos_precios.py --aplicar /tmp/soicos.json.gz --dry-run
    python3 scripts/soicos_precios.py --aplicar /tmp/soicos.json.gz
"""
import argparse
import gzip
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import soicos_a_captura as S  # noqa: E402
from data_io import url_real  # noqa: E402

# (programa, storeId). La Despensa de Bodega es otro programa pero la misma
# tienda del catálogo.
PROGRAMAS = [
    (11896, "walmart_mx"),
    (11487, "bodega_aurrera"),
    (12167, "bodega_aurrera"),
    (11897, "sams_mx"),
    (11337, "sephora_mx"),
    (9839, "lenovo"),
    (15695, "reuse_mx"),
]

# La API admite 60 pedidos por minuto y cada página de 1000 tarda 15-35 s en
# llegar: con 8 a la vez y un pedido cada 1.1 s como mínimo se aprovecha la
# espera sin pasar el límite (16 páginas en 69 s, medido el 25-sep-2026).
HILOS = 8
ENTRE_PEDIDOS = 1.1


class Ritmo:
    """Un pedido cada ENTRE_PEDIDOS segundos como mínimo, entre todos los hilos."""

    def __init__(self, pausa):
        self.pausa, self.proximo, self.lock = pausa, 0.0, threading.Lock()

    def esperar(self):
        with self.lock:
            ahora = time.monotonic()
            espera = max(0.0, self.proximo - ahora)
            self.proximo = max(ahora, self.proximo) + self.pausa
        if espera:
            time.sleep(espera)


def clave(url):
    return url_real(url) or url


def filas(pagina):
    for d in pagina.get("data") or []:
        precio = S.numero(d.get("price"))
        if not precio or not d.get("url"):
            continue
        antes = S.numero(d.get("from_price"))
        stock = str(d.get("stock") or "0").strip() not in ("0", "", "None", "false", "False")
        yield clave(d["url"]), [precio, antes if antes and antes > precio else None, stock, d["url"]]


def bajar(salida, minutos, hilos, solo=None):
    token, aid = os.environ.get("SOICOS_TOKEN"), os.environ.get("SOICOS_AID")
    if not token or not aid:
        print("AVISO: faltan los secretos SOICOS_TOKEN y SOICOS_AID; no se bajan los feeds de Soicos.")
        return
    limite = time.monotonic() + minutos * 60
    ritmo = Ritmo(ENTRE_PEDIDOS)
    precios, informe = {}, {}

    def una(programa, n):
        if time.monotonic() > limite:
            return None
        ritmo.esperar()
        try:
            return S.pagina(programa, token, aid, n)
        except SystemExit as e:  # pagina() sale así tras 5 intentos
            print(f"  programa {programa}, página {n}: {e}", file=sys.stderr)
            return None

    for programa, tienda in PROGRAMAS:
        if solo and programa not in solo:
            continue
        t0 = time.monotonic()
        primera = una(programa, 1)
        if not primera:
            informe[programa] = {"tienda": tienda, "paginas": 0, "bajadas": 0}
            continue
        ultima = primera["meta"]["last_page"]
        destino = precios.setdefault(tienda, {})
        destino.update(filas(primera))
        bajadas = 1
        with ThreadPoolExecutor(max_workers=hilos) as pool:
            for pag in pool.map(lambda n: una(programa, n), range(2, ultima + 1)):
                if pag:
                    destino.update(filas(pag))
                    bajadas += 1
        informe[programa] = {"tienda": tienda, "paginas": ultima, "bajadas": bajadas}
        print(f"programa {programa} ({tienda}): {bajadas}/{ultima} páginas en "
              f"{(time.monotonic() - t0) / 60:.0f} min; {len(destino):,} urls de la tienda", flush=True)
    tmp = salida + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump({"programas": informe, "precios": precios}, f, separators=(",", ":"))
    os.replace(tmp, salida)
    print(f"Guardado {salida}")


def aplicar(archivo, dry_run):
    from data_io import load_catalog, save_catalog
    if not os.path.exists(archivo):
        print(f"No hay {archivo} (sin secretos de Soicos o la bajada falló): nada que aplicar.")
        return
    with gzip.open(archivo, "rt", encoding="utf-8") as f:
        feed = json.load(f)
    precios = feed["precios"]
    data = load_catalog()
    stats = {t: {"ofertas": 0, "cambian": 0, "iguales": 0, "agotadas": 0, "sin_feed": 0} for t in precios}
    deltas = []
    for p in data["products"]:
        ofertas = list(p.get("offers") or [])
        for v in p.get("colorVariants") or []:
            ofertas.extend(v.get("offers") or [])
        for o in ofertas:
            tienda = o.get("storeId")
            if tienda not in precios:
                continue
            st = stats[tienda]
            st["ofertas"] += 1
            fila = precios[tienda].get(clave(o.get("url")))
            if not fila:
                st["sin_feed"] += 1
                continue
            precio, antes, stock, deeplink = fila
            if not stock:
                st["agotadas"] += 1
                continue
            nuevo = {"price": precio, "stock": "in_stock", "url": deeplink}
            if antes:
                nuevo["listPrice"] = antes
            if all(o.get(k) == v for k, v in nuevo.items()) and (antes or "listPrice" not in o):
                st["iguales"] += 1
                continue
            viejo = o.get("price")
            if viejo and abs(viejo - precio) >= 0.01:
                deltas.append((abs(precio - viejo) / viejo, p["name"], viejo, precio))
            o.update(nuevo)
            if not antes:
                o.pop("listPrice", None)
            st["cambian"] += 1
    for t, st in stats.items():
        cubre = (st["ofertas"] - st["sin_feed"]) / (st["ofertas"] or 1)
        print(f"  {t:15} ofertas {st['ofertas']:>8,}  cambian {st['cambian']:>7,}  iguales {st['iguales']:>8,}  "
              f"agotadas {st['agotadas']:>6,}  fuera del feed {st['sin_feed']:>7,}  ({cubre:.0%} cubiertas)")
    deltas.sort(reverse=True)
    for pct, nombre, viejo, nuevo in deltas[:10]:
        print(f"   {pct:6.0%}  {nombre[:56]:56} ${viejo:,.2f} -> ${nuevo:,.2f}")
    if dry_run:
        print("(--dry-run: no se guardó nada)")
        return
    if any(st["cambian"] for st in stats.values()):
        save_catalog(data)
        print("Guardado.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--bajar", metavar="SALIDA")
    g.add_argument("--aplicar", metavar="ARCHIVO")
    ap.add_argument("--minutos", type=float, default=170,
                    help="deja de pedir páginas pasado este tiempo y guarda lo que haya")
    ap.add_argument("--hilos", type=int, default=HILOS)
    ap.add_argument("--programa", type=int, action="append", help="sólo estos programas (para probar)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.bajar:
        bajar(args.bajar, args.minutos, args.hilos, args.programa)
    else:
        aplicar(args.aplicar, args.dry_run)


if __name__ == "__main__":
    main()
