#!/usr/bin/env python3
"""ComparaMEX Local: mete al catálogo los precios de las tiendas del registro.

QUÉ HACE, POR TIENDA ACTIVA DE local/tiendas.json
--------------------------------------------------
1. Lee su lista de precios: local/precios/<id>.csv, o la url de una Hoja de
   cálculo de Google publicada como CSV (fuente.url).
2. Une cada renglón a una ficha del catálogo, en este orden:
     a. id_comparamex (la tienda ya la confirmó);
     b. el mismo código de barras;
     c. un código de modelo que la ficha nombra, y además el veto de
        fusionar_vetado.py (mismas medidas y códigos, reacondicionado en las
        dos o en ninguna, precio a menos de 1.8x) -- lo mismo que se le
        exige a Walmart o Bodega Aurrerá en emparejar_feed.py.
   Lo que no se une queda en local/revision/<id>.csv con las tres fichas más
   parecidas (vecinos_catalogo.py), para que la tienda elija. No se da de
   alta ninguna ficha nueva: una tienda local compara contra lo que ya está.
3. Reemplaza las ofertas de esa tienda por las de la lista de hoy: cada
   oferta lleva `local` (municipio, lat, lng) y `verificado` (la fecha que
   puso la tienda). Un precio con más de DIAS_VIGENCIA días sin confirmar no
   entra.
4. Registra la tienda en data.json (stores) con local=true y la zona de
   envío (hubRegion) más cercana, para que el cálculo de entrega por
   municipio que ya existe la trate como tienda de la zona.

USO
---
    python3 scripts/local_importar.py                 # informe, sin tocar el catálogo
    python3 scripts/local_importar.py --aplicar
    python3 scripts/local_importar.py --registro otro.json --precios-dir otra/carpeta   # pruebas
"""
import argparse
import collections
import csv
import datetime
import io
import json
import math
import os
import re
import sys
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
from data_io import load_catalog, save_catalog  # noqa: E402
import adjuntar_tienda_de_marca as A  # noqa: E402
import fusionar_vetado as FV  # noqa: E402
from emparejar_feed import codigos, gtin_norm, MAX_FICHAS_POR_CODIGO  # noqa: E402

DIAS_VIGENCIA = 14
EXISTENCIA = {"si": "in_stock", "sí": "in_stock", "pocas": "low_stock", "no": None}


def leer_lista(tienda, precios_dir):
    fuente = tienda.get("fuente") or {}
    if fuente.get("url"):
        req = urllib.request.Request(fuente["url"], headers={"User-Agent": "ComparaMEX/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            texto = r.read().decode("utf-8-sig")
    else:
        ruta = os.path.join(precios_dir, f"{tienda['id']}.csv")
        if not os.path.exists(ruta):
            return None
        texto = io.open(ruta, encoding="utf-8-sig").read()
    return [{(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
            for row in csv.DictReader(io.StringIO(texto))]


def precio(x):
    try:
        v = float(str(x).replace("$", "").replace(",", "").strip())
    except ValueError:
        return None
    return v if v > 0 else None


def zona_mas_cercana(regiones, lat, lng):
    if lat is None or lng is None:
        return None
    def dist(r):
        return math.hypot((r["lat"] - lat), (r["lng"] - lng) * math.cos(math.radians(lat)))
    return min((r for r in regiones if r.get("lat") is not None), key=dist)["id"]


def texto_renglon(r):
    return " ".join(x for x in (r.get("marca"), r.get("producto"), r.get("modelo")) if x)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--registro", default=os.path.join(RAIZ, "local", "tiendas.json"))
    ap.add_argument("--precios-dir", default=os.path.join(RAIZ, "local", "precios"))
    ap.add_argument("--revision-dir", default=os.path.join(RAIZ, "local", "revision"))
    ap.add_argument("--hoy", help="fecha de referencia AAAA-MM-DD (pruebas)")
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()
    hoy = datetime.date.fromisoformat(args.hoy) if args.hoy else datetime.date.today()

    tiendas = [t for t in json.load(io.open(args.registro, encoding="utf-8")) if t.get("activa")]
    if not tiendas:
        print("registro sin tiendas activas: nada que hacer")
        return
    data = load_catalog()
    productos = data["products"]
    por_id = {p["id"]: p for p in productos}
    por_gtin = collections.defaultdict(list)
    por_codigo = collections.defaultdict(list)
    for p in productos:
        if not p.get("offers"):
            continue
        g = gtin_norm(p.get("gtin"))
        if g:
            por_gtin[g].append(p)
        for c in codigos(p.get("name")):
            por_codigo[c].append(p)
    por_codigo = {c: ps for c, ps in por_codigo.items() if len(ps) <= MAX_FICHAS_POR_CODIGO}
    vecinos = None

    ids_locales = {t["id"] for t in tiendas}
    nuevas = collections.defaultdict(list)   # id de ficha -> ofertas locales
    resumen = []
    for t in tiendas:
        filas = leer_lista(t, args.precios_dir)
        if filas is None:
            resumen.append((t["id"], "sin lista de precios"))
            continue
        cuenta = collections.Counter()
        sin_unir = []
        for r in filas:
            pr = precio(r.get("precio"))
            stock = EXISTENCIA.get((r.get("existencia") or "si").lower(), "in_stock")
            try:
                fecha = datetime.date.fromisoformat(r.get("fecha") or "")
            except ValueError:
                cuenta["sin fecha válida"] += 1
                continue
            if not pr or not r.get("producto"):
                cuenta["sin precio o sin producto"] += 1
                continue
            if (hoy - fecha).days > DIAS_VIGENCIA:
                cuenta[f"precio con más de {DIAS_VIGENCIA} días"] += 1
                continue
            if stock is None:
                cuenta["sin existencia"] += 1
                continue
            texto = texto_renglon(r)
            ficha, via = None, None
            if r.get("id_comparamex") and r["id_comparamex"] in por_id:
                ficha, via = por_id[r["id_comparamex"]], "confirmada"
            if not ficha:
                g = gtin_norm(r.get("gtin"))
                cands = por_gtin.get(g, []) if g else []
                if cands:
                    ficha, via = max(cands, key=lambda p: len(p.get("offers") or [])), "código de barras"
            if not ficha:
                for c in codigos(texto):
                    for p in por_codigo.get(c, []):
                        if A.nombra(p.get("name"), c) and not FV.motivo(
                                [{"nombre": p["name"], "precio": A.precio_min(p)}, {"nombre": texto, "precio": pr}]):
                            ficha, via = p, "código de modelo"
                            break
                    if ficha:
                        break
            if not ficha:
                if vecinos is None:
                    from vecinos_catalogo import Vecinos
                    vecinos = Vecinos(productos)
                parecidas = [por_id[q] for q, _ in vecinos.mas_parecidas(titulo=texto, k=3) if q in por_id]
                sin_unir.append((r, parecidas))
                cuenta["por confirmar"] += 1
                continue
            cuenta[via] += 1
            oferta = {"storeId": t["id"], "price": pr, "stock": stock,
                      "url": t.get("sitio") or (f"https://wa.me/{t['whatsapp']}" if t.get("whatsapp") else None),
                      "verificado": fecha.isoformat(),
                      "local": {"municipio": t["municipio"], "lat": t.get("lat"), "lng": t.get("lng")}}
            nuevas[ficha["id"]].append(oferta)
        resumen.append((t["id"], dict(cuenta)))
        if sin_unir:
            os.makedirs(args.revision_dir, exist_ok=True)
            ruta = os.path.join(args.revision_dir, f"{t['id']}.csv")
            with io.open(ruta, "w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(["producto", "marca", "modelo", "precio", "candidata_1", "nombre_1",
                            "candidata_2", "nombre_2", "candidata_3", "nombre_3"])
                for r, ps in sin_unir:
                    fila = [r.get("producto"), r.get("marca"), r.get("modelo"), r.get("precio")]
                    for p in ps[:3]:
                        fila += [p["id"], p["name"][:120]]
                    w.writerow(fila)
            print(f"  {t['id']}: {len(sin_unir)} renglones por confirmar -> {ruta}")

    for tid, c in resumen:
        print(f"{tid}: {c}")
    total = sum(len(v) for v in nuevas.values())
    print(f"ofertas locales vigentes: {total}")
    if not args.aplicar:
        print("(sin --aplicar: no se tocó el catálogo)")
        return

    # Las ofertas de estas tiendas se reemplazan enteras por la lista de hoy.
    for p in productos:
        if any(o.get("storeId") in ids_locales for o in p.get("offers") or []):
            p["offers"] = [o for o in p["offers"] if o.get("storeId") not in ids_locales]
    for pid, ofs in nuevas.items():
        por_id[pid].setdefault("offers", []).extend(ofs)
    stores = data.setdefault("stores", [])
    regiones = data.get("regions") or []
    for t in tiendas:
        s = next((s for s in stores if s["id"] == t["id"]), None)
        if s is None:
            s = {"id": t["id"]}
            stores.append(s)
        s.update({"name": t["nombre"], "local": True, "municipio": t["municipio"],
                  "hubRegion": zona_mas_cercana(regiones, t.get("lat"), t.get("lng")),
                  "typicalShippingDays": [0, 1], "logo": "".join(w[0] for w in t["nombre"].split()[:2]).upper(),
                  "color": "#0a8a3c"})
    save_catalog(data)
    print(f"Guardado: {total} ofertas locales.")


if __name__ == "__main__":
    main()
