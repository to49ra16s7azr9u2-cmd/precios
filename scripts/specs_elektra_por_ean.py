#!/usr/bin/env python3
"""Ficha técnica de Elektra para fichas SIN ninguna, buscándola por código de barras.

POR QUÉ (07-oct-2026)
---------------------
Las ~470 mil fichas que sólo venden Walmart, Bodega Aurrera o Sam's no traen
ni una especificación (Walmart MX responde «/blocked» a cualquier lector, ver
CLAUDE/notas de tiendas) y son más de la mitad del catálogo. Pero el número
final de su url ES su código de barras sin el dígito verificador
(match_by_gtin.gtin_de_walmex), y Elektra, que sí publica ficha técnica en su
API de catálogo, vende muchas de las mismas marcas: en una muestra al azar de
60 fichas de Walmart (sin autopartes), 5 estaban en Elektra por código de
barras (8%), todas con ficha técnica de 4 a 9 campos.

CÓMO
----
La API pública de catálogo de VTEX que autoriza el robots.txt de Elektra
acepta varios `fq=alternateIds_Ean:X` a la vez (se unen con OR): 40 formas
por pedido (20 códigos x dos formas, con y sin cero adelante), con el
User-Agent con el que nos presentamos. Para ~450 mil códigos son ~22 mil
pedidos, con pausa entre uno y otro, y NO gastan cuota del Worker de
Mercado Libre.

Dos pasos, reanudables:

    python3 scripts/specs_elektra_por_ean.py --bajar     # -> /tmp/elektra/specs_por_ean.jsonl
    python3 scripts/specs_elektra_por_ean.py --aplicar   # caché -> catálogo

SIN FALSOS POSITIVOS
--------------------
Como el código de Walmart lo armamos nosotros, y el de Elektra a veces es
interno de la tienda (ver ean_dudosos.py), cada coincidencia pasa las MISMAS
comprobaciones que match_by_gtin.py: el nombre tiene que parecerse
(audit_gtin_matches.similitud >= MIN_SIMILITUD) y la condición (nuevo /
reacondicionado) tiene que coincidir. Sólo se llena la ficha que no tiene
ninguna especificación.
"""
import argparse
import json
import os
import sys
import time
import urllib.parse

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from add_elektra_products import fetch_json  # noqa: E402
from data_io import load_catalog, save_catalog, url_real  # noqa: E402
from ean_dudosos import ean_utilizable  # noqa: E402
from elektra_specs import specs_from  # noqa: E402
from match_by_gtin import TIENDAS_WALMEX, gtin_de_walmex, normalize_gtin  # noqa: E402
from phone_signature import condition_of  # noqa: E402

API = "https://www.elektra.mx/api/catalog_system/pub/products/search"
CACHE = "/tmp/elektra/specs_por_ean.jsonl"
# Más exigente que el 0.34 de match_by_gtin: acá el código de Walmart lo
# armamos nosotros y una ficha con otra figura de la misma colección («Red
# Hulk» contra «Capitán América», 0.375) heredaría una ficha técnica ajena.
MIN_PARECIDO = 0.5
MAX_FORMAS = 40  # fq= por pedido: con 60 la API responde 400 (url larga)


def codigos_de(p):
    """Códigos de barras normalizados que conocemos de la ficha."""
    out = []
    g = normalize_gtin(str(p.get("gtin") or ""))
    if g:
        out.append(g)
    for o in p.get("offers") or []:
        if ean_utilizable(o):
            g = normalize_gtin(o.get("ean"))
            if g:
                out.append(g)
        if o.get("storeId") in TIENDAS_WALMEX:
            g = gtin_de_walmex(url_real(o.get("url") or "") or o.get("url"))
            if g:
                out.append(g)
    vistos = []
    for g in out:
        if g not in vistos:
            vistos.append(g)
    return vistos


def faltantes(data):
    """{código: [id de ficha]} de las fichas sin especificaciones."""
    out = {}
    for p in data["products"]:
        if p.get("specs"):
            continue
        for g in codigos_de(p):
            out.setdefault(g, []).append(p["id"])
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
                vistos[d["g"]] = d
    return vistos


def bajar(codigos, pausa, limite):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    hechos = leer_cache()
    pendientes = [g for g in codigos if g not in hechos]
    if limite:
        pendientes = pendientes[:limite]
    print(f"Códigos sin ficha: {len(codigos):,}; ya en caché: {len(hechos):,}; por pedir: {len(pendientes):,}", flush=True)
    con = fallidos = n = 0
    with open(CACHE, "a", encoding="utf-8") as f:
        i = 0
        while i < len(pendientes):
            lote, formas = [], []
            while i + len(lote) < len(pendientes):
                g = pendientes[i + len(lote)]
                extra = [g, g.zfill(13)] if len(g) < 13 else [g]
                if lote and len(formas) + len(extra) > MAX_FORMAS:
                    break
                lote.append(g)
                formas += extra
            q = "&".join("fq=" + urllib.parse.quote(f"alternateIds_Ean:{x}") for x in formas)
            res = fetch_json(f"{API}?{q}&_from=0&_to={len(formas) - 1}")
            if res is None:
                fallidos += 1          # no se anota: se pide otro día
                i += len(lote)
                time.sleep(pausa * 4)
                continue
            por_codigo = {}
            for prod in res:
                ficha = specs_from(prod)
                for it in prod.get("items") or []:
                    e = normalize_gtin(str(it.get("ean") or ""))
                    if e:
                        por_codigo.setdefault(e, (prod.get("productName") or "", ficha))
            for g in lote:
                nombre, ficha = por_codigo.get(g, ("", []))
                con += bool(ficha)
                f.write(json.dumps({"g": g, "nombre": nombre, "specs": ficha}, ensure_ascii=False) + "\n")
            f.flush()
            i += len(lote)
            n += 1
            if n % 50 == 0:
                print(f"  {n:,} pedidos; {i:,} códigos; con ficha {con:,}; fallidos {fallidos}", flush=True)
            time.sleep(pausa)
    print(f"Bajado: {len(pendientes):,} códigos, {con:,} con ficha técnica; pedidos fallidos {fallidos}")


def aplicar(data, mapa, dry_run):
    from audit_gtin_matches import MIN_SIMILITUD, similitud
    cache = leer_cache()
    por_id = {p["id"]: p for p in data["products"]}
    llenas = campos = nombre_no = condicion_no = 0
    for g, ids in mapa.items():
        d = cache.get(g)
        if not d or not d.get("specs"):
            continue
        for pid in ids:
            p = por_id[pid]
            if p.get("specs"):
                continue
            parecido = similitud(p.get("name", ""), d.get("nombre", ""))
            if parecido is not None and parecido < max(MIN_SIMILITUD, MIN_PARECIDO):
                nombre_no += 1
                continue
            if condition_of(p.get("name", "")) != condition_of(d.get("nombre", "")):
                condicion_no += 1
                continue
            p["specs"] = d["specs"]
            llenas += 1
            campos += len(d["specs"])
    con = sum(1 for p in data["products"] if p.get("specs"))
    print(f"Fichas que ganan ficha técnica: {llenas:,} ({campos:,} campos); rechazadas por nombre {nombre_no:,}, por condición {condicion_no:,}; "
          f"con especificaciones: {con:,} de {len(data['products']):,} ({con / len(data['products']):.1%})")
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
    ap.add_argument("--pausa", type=float, default=0.7, help="segundos entre pedidos")
    ap.add_argument("--limite", type=int, default=0, help="sólo los primeros N códigos (prueba)")
    args = ap.parse_args()
    if not (args.bajar or args.aplicar):
        ap.error("--bajar y/o --aplicar")
    data = load_catalog()
    mapa = faltantes(data)
    if args.bajar:
        # Primero lo que no es refacción de auto: ahí Elektra casi no vende.
        por_id = {p["id"]: p for p in data["products"]}
        orden = sorted(mapa, key=lambda g: por_id[mapa[g][0]]["category"] in ("Autopartes", "Autos y motos"))
        bajar(orden, args.pausa, args.limite)
    if args.aplicar:
        aplicar(data, mapa, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
