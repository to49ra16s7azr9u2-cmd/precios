#!/usr/bin/env python3
"""Fotos que ya no existen: se cambian por la de otra oferta o se quitan.

POR QUÉ (25-sep-2026)
---------------------
El usuario preguntó por las fichas sin foto. Casi todas tienen url de foto,
pero la tienda ya la borró: muestras de 40 dieron 404 en el 7.5% de las de
Elektra (~5,100 fichas), el 45% de las de Chedraui (~950), todas las de
res.cloudinary.com de Walmart (273) y el 12% de Shopify. La SPA reintenta
y al final pone el ícono, así que la ficha se veía en blanco un rato.

QUÉ HACE
--------
1. --revisar: pide cada foto de los hosts de HOSTS (HEAD, y GET si el
   servidor no acepta HEAD) y guarda las que dan 404/410 en un informe.
   Coppel y Sephora no se revisan: su CDN (Akamai) rechaza este servidor
   pero en un navegador cargan (lo confirmó el usuario).
2. --aplicar INFORME: a cada ficha con la foto rota le pone la primera foto
   de sus otras ofertas o variantes de color que no esté en el informe; si
   no tiene otra, le quita la foto (la SPA pinta el ícono de una vez).

USO
---
    python3 scripts/revisar_fotos.py --revisar /tmp/fotos_rotas.json
    python3 scripts/revisar_fotos.py --aplicar /tmp/fotos_rotas.json
"""
import argparse
import concurrent.futures as cf
import io
import json
import os
import sys
import urllib.parse
import urllib.request
import urllib.error

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import load_catalog, save_catalog  # noqa: E402

HOSTS = {
    "elektra.vteximg.com.br", "chedrauimx.vteximg.com.br", "res.cloudinary.com", "cdn.shopify.com",
    "martimx.vteximg.com.br", "juguetron.vteximg.com.br", "img.gkbcdn.com", "img.myipadbox.com",
    "whirlpoolmex.vtexassets.com", "minisomx.vteximg.com.br", "ae-pic-a1.aliexpress-media.com",
}
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"


def estado(url):
    for metodo in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=metodo, headers={"User-Agent": UA, "Accept": "image/*,*/*"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.status
        except urllib.error.HTTPError as e:
            if e.code in (405, 501) and metodo == "HEAD":
                continue
            return e.code
        except Exception:
            return None     # red: no se decide nada
    return None


def fotos_de(p):
    fotos = [p.get("photo")]
    fotos += [o.get("photo") for o in p.get("offers") or []]
    for v in p.get("colorVariants") or []:
        fotos.append(v.get("photo"))
        fotos += [o.get("photo") for o in v.get("offers") or []]
    vistas, salida = set(), []
    for f in fotos:
        if f and f not in vistas:
            vistas.add(f)
            salida.append(f)
    return salida


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--revisar")
    ap.add_argument("--aplicar")
    ap.add_argument("--hilos", type=int, default=16)
    args = ap.parse_args()
    data = load_catalog()

    if args.revisar:
        urls = set()
        for p in data["products"]:
            for f in fotos_de(p):
                if urllib.parse.urlparse(f).netloc in HOSTS:
                    urls.add(f)
        print(f"Fotos por revisar: {len(urls):,}")
        rotas, sin_red, hechas = [], 0, 0
        with cf.ThreadPoolExecutor(args.hilos) as ex:
            for url, st in zip(urls, ex.map(estado, urls)):
                hechas += 1
                if st in (404, 410):
                    rotas.append(url)
                elif st is None:
                    sin_red += 1
                if hechas % 5000 == 0:
                    print(f"  {hechas:,} revisadas, {len(rotas):,} rotas", flush=True)
        with io.open(args.revisar, "w", encoding="utf-8") as f:
            json.dump(sorted(rotas), f)
        print(f"Rotas: {len(rotas):,}; sin respuesta (se dejan): {sin_red:,} -> {args.revisar}")

    if args.aplicar:
        with io.open(args.aplicar, encoding="utf-8") as f:
            rotas = set(json.load(f))
        cambiadas = quitadas = 0
        for p in data["products"]:
            if p.get("photo") not in rotas:
                continue
            otra = next((f for f in fotos_de(p) if f not in rotas and f != p.get("photo")), None)
            if otra:
                p["photo"] = otra
                cambiadas += 1
            else:
                p.pop("photo", None)
                quitadas += 1
        save_catalog(data)
        print(f"Guardado: {cambiadas:,} fotos cambiadas por la de otra oferta, {quitadas:,} quitadas.")


if __name__ == "__main__":
    main()
