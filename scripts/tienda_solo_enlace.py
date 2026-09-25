#!/usr/bin/env python3
"""Una tienda pasa a «solo enlace»: sin precio en el sitio, con botón a su
página (decisión del usuario, 26-sep-2026, para Amazon).

POR QUÉ
-------
Las políticas del Programa de Afiliados de Amazon México permiten mostrar
precio y disponibilidad solo si vienen de su API (Creators API / PA-API) o
de un enlace que Amazon provee, y prohíben «data mining, robots o
herramientas similares» para sacar datos. Los precios de Amazon del
catálogo salieron de capturas, no de la API, así que no se muestran. El
enlace de afiliado sí se puede mostrar.

QUÉ HACE
--------
Sobre scripts/ocultar_tiendas.py (que guarda y restaura sin perder nada):
  - Fichas donde la tienda es UNA de varias ofertas: la oferta sale de
    `offers` (no entra en ningún precio, orden, rango ni ranking) y queda en
    `enlaces` de la ficha: [{storeId, url}]. La tabla de la ficha la muestra
    como «Ver precio en <tienda>».
  - Fichas donde era la ÚNICA oferta: salen del catálogo publicado, igual
    que con ocultar_tiendas.py. Sin precio y sin otra tienda no hay nada que
    comparar, y ninguna tenía página propia (hace falta 2+ vendedores).
  - La serie de la tienda en el historial de precios (data/hist) se guarda
    aparte y sale del historial publicado: también es un precio mostrado.
  - La tienda sigue en `stores`, con `soloEnlace: true` (nombre y logo para
    el botón; los importadores lo leen para no volver a meter precios).
Todo lo quitado vive en data/tiendas-ocultas.json.gz y en
data/historial-oculto.json.gz (fuera del sitio publicado, ver _config.yml).

USO
---
    python3 scripts/tienda_solo_enlace.py --tienda amazon_mx --dry-run
    python3 scripts/tienda_solo_enlace.py --tienda amazon_mx
    python3 scripts/tienda_solo_enlace.py --tienda amazon_mx --restaurar
Después, regenerar (scripts/regenerar_sitio.sh).
"""
import argparse
import gzip
import io
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import ocultar_tiendas as O  # noqa: E402
from data_io import (load_catalog, save_catalog, leer_json, escribir_texto_json,  # noqa: E402
                     nombre_logico)

HIST_DIR = os.path.join(ROOT, "data", "hist")
HIST_OCULTO = os.path.join(ROOT, "data", "historial-oculto.json.gz")
MOTIVO = "solo enlace: precio no autorizado fuera de la API de la tienda"


def leer_hist_oculto():
    if not os.path.exists(HIST_OCULTO):
        return {}
    with gzip.open(HIST_OCULTO, "rt", encoding="utf-8") as f:
        return json.load(f)


def guardar_hist_oculto(d):
    with gzip.GzipFile(HIST_OCULTO, "wb", mtime=0) as g, io.TextIOWrapper(g, encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def archivos_hist():
    if not os.path.isdir(HIST_DIR):
        return []
    return sorted({nombre_logico(n) for n in os.listdir(HIST_DIR) if n.endswith((".json", ".json.gz"))})


def sacar_del_historial(tiendas, dry_run):
    """{archivo: {pid: {tienda: serie, "_v": {tienda: serie}}}} con lo quitado."""
    oculto = leer_hist_oculto()
    n = 0
    for nombre in archivos_hist():
        fname = os.path.join("data", "hist", nombre)
        hist = leer_json(fname)
        cambio = False
        for pid, series in hist.items():
            for t in tiendas:
                if t in series:
                    guardado = oculto.setdefault(pid, {})
                    guardado[t] = series.pop(t)
                    v = (series.get("_v") or {}).pop(t, None)
                    if v is not None:
                        guardado.setdefault("_v", {})[t] = v
                    cambio = True
                    n += 1
        if cambio and not dry_run:
            escribir_texto_json(fname, json.dumps(hist, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
    if not dry_run:
        guardar_hist_oculto(oculto)
    return n


def devolver_al_historial(tiendas):
    oculto = leer_hist_oculto()
    n = 0
    for nombre in archivos_hist():
        fname = os.path.join("data", "hist", nombre)
        hist = leer_json(fname)
        cambio = False
        for pid, series in hist.items():
            g = oculto.get(pid)
            if not g:
                continue
            for t in tiendas:
                if t in g:
                    series[t] = g.pop(t)
                    v = (g.get("_v") or {}).pop(t, None)
                    if v is not None:
                        series.setdefault("_v", {})[t] = v
                    cambio = True
                    n += 1
        if cambio:
            escribir_texto_json(fname, json.dumps(hist, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
    # Lo que no encontró su ficha en data/hist (fichas que siguen ocultas)
    # se queda guardado para una restauración posterior.
    guardar_hist_oculto({pid: g for pid, g in oculto.items() if any(k != "_v" for k in g)})
    return n


def convertir(data, tiendas, guardar_archivo=True):
    """Pasa las ofertas de `tiendas` a enlaces (o archiva la ficha si era su
    única oferta) y deja la tienda en `stores` con soloEnlace. La llama
    también data_io.save_catalog como red de seguridad."""
    tienda_meta = {s["id"]: dict(s) for s in data.get("stores") or [] if s["id"] in tiendas}
    guardado, fuera_p, fuera_o = O.ocultar(data, tiendas, MOTIVO)
    por_id = {p["id"]: p for p in data["products"]}
    for e in fuera_o:
        p = por_id.get(e["productId"])
        url = (e["offer"] or {}).get("url")
        if p is None or not url:
            continue
        enl = p.setdefault("enlaces", [])
        if not any(x.get("storeId") == e["offer"]["storeId"] for x in enl):
            enl.append({"storeId": e["offer"]["storeId"], "url": url})
    # ocultar() saca la tienda de `stores`; acá vuelve, marcada.
    for s in tienda_meta.values():
        s["soloEnlace"] = True
        data.setdefault("stores", []).append(s)
    if guardar_archivo:
        O.guardar(guardado)
        print(f"solo enlace ({', '.join(sorted(tiendas))}): {len(fuera_o):,} ofertas a enlace, "
              f"{len(fuera_p):,} fichas al archivo")
    return guardado, fuera_p


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tienda", action="append", required=True)
    ap.add_argument("--restaurar", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    tiendas = set(args.tienda)
    data = load_catalog()
    antes = len(data["products"])

    if args.restaurar:
        for p in data["products"]:
            if p.get("enlaces"):
                p["enlaces"] = [e for e in p["enlaces"] if e.get("storeId") not in tiendas]
                if not p["enlaces"]:
                    del p["enlaces"]
        guardado, vp, vo = O.restaurar(data, tiendas)
        for s in data.get("stores") or []:
            if s["id"] in tiendas:
                s.pop("soloEnlace", None)
        print(f"Restauradas {vp:,} fichas y {vo:,} ofertas")
        if args.dry_run:
            print("(--dry-run: no se escribió nada)")
            return
        O.guardar(guardado)
        save_catalog(data)
        print(f"Series devueltas al historial: {devolver_al_historial(tiendas):,}")
        return

    guardado, fuera_p = convertir(data, tiendas, guardar_archivo=False)
    print(f"Tienda(s) en solo enlace: {', '.join(sorted(tiendas))}")
    print(f"  fichas que salen (era su única oferta): {len(fuera_p):,}")
    print(f"  fichas que se quedan con el enlace:     {sum(1 for p in data['products'] if p.get('enlaces')):,}")
    print(f"  catálogo: {antes:,} -> {len(data['products']):,}")
    n = sacar_del_historial(tiendas, args.dry_run)
    print(f"  series de historial guardadas aparte: {n:,}")
    if args.dry_run:
        print("(--dry-run: no se escribió el catálogo)")
        return
    O.guardar(guardado)
    save_catalog(data)
    print("Guardado. Falta regenerar (scripts/regenerar_sitio.sh).")


if __name__ == "__main__":
    main()
