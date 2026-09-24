#!/usr/bin/env python3
"""Aplica SOLO las fusiones de un informe que pasan un segundo filtro.

POR QUÉ
-------
El 17 de septiembre de 2026 se aplicaron merge_amazon_cross_store.py
--todas-las-tiendas (232 fichas absorbidas) y merge_by_name_subset.py (134)
y, al auditar los informes, entre los grupos con precio a 1.8x o más había
fusiones FALSAS -- un precio de otro producto en la ficha, que es lo peor
que le puede pasar a un comparador:

    Crucial E100 480 GB           <- Crucial E100 de 1 TB
    GoPro HERO13 (sola)           <- GoPro HERO13 "con accesorios" (bundle)
    Samson FM1 (micrófono)        <- Samson Q7 (otro micrófono)
    D'Addario Kaplan KS311W       <- D'Addario Prelude (otras cuerdas)
    Rode NT1 Signature con soporte<- Rode NT1 Signature solo

Se revirtió todo (git checkout -- data/). Este script vuelve a aplicar las
fusiones de esos informes, pero solo las que además cumplen:

  1. Mismas capacidades y medidas en todas las fichas: cualquier número
     con unidad (gb, tb, ml, l, kg, g, cm, mm, pulgadas/", w, mah, hz,
     piezas) tiene que aparecer igual en todas, o en ninguna.
  2. Sin indicio de paquete en SOLO algunas fichas: "bundle", "kit",
     "pack", "combo", "con soporte", "con accesorios", "con funda", "+",
     "más", "incluye". Si una lo dice y otra no, no es el mismo artículo.
  3. Mismos códigos: todo token con letras y dígitos (2+ caracteres) que
     tenga una ficha lo tienen todas ("fm1" contra "q7", "ks311w" contra
     nada).
  4. Reacondicionado en todas o en ninguna.
  5. Precio máximo / precio mínimo menor a 1.8. Un producto idéntico puede
     costar el doble en otra tienda, pero a este catálogo esa señal le ha
     costado más fusiones falsas de las que ha permitido buenas.

Lo que no pasa se lista con su motivo y no se toca.

USO
---
    python3 scripts/fusionar_vetado.py informe.json [informe2.json ...]            # ensayo
    python3 scripts/fusionar_vetado.py informe.json --aplicar
"""
import argparse
import collections
import json
import re
import sys
import unicodedata

sys.path.insert(0, "scripts")
from data_io import load_catalog, save_catalog  # noqa: E402
import merge_amazon_cross_store as mcs  # noqa: E402

UNIDAD_RE = re.compile(
    r'\b(\d+(?:[.,]\d+)?)\s*(tb|gb|mb|ml|lts?|litros?|kg|kgs|gr?|gramos|cm|mm|m|"|pulgadas?|pulg|w|watts?|mah|hz|ghz|mhz|'
    r'piezas?|pzas?|pcs|unidades|pack|tazas)\b')
PAQUETE_RE = re.compile(r'\b(bundle|kit|pack|combo|incluye|mas|\+)\b|\bcon (soporte|accesorios|funda|estuche|base|tripie|tripode|cargador|bateria extra|almohadas?)\b')
USADO_RE = re.compile(r'\b(reacondicionad[oa]s?|renewed|refurbished|seminuev[oa]s?|usad[oa]s?|open box|grado [abc]\b)')
CODIGO_RE = re.compile(r'\b(?=[a-z0-9-]*\d)(?=[a-z0-9-]*[a-z])[a-z0-9][a-z0-9-]{1,}\b')


def norm(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s.replace("+", " + ")).strip()


def medidas(n):
    out = set()
    for num, u in UNIDAD_RE.findall(n):
        u = {"lts": "l", "lt": "l", "litros": "l", "litro": "l", "kgs": "kg", "gr": "g", "gramos": "g",
             "pulgadas": '"', "pulgada": '"', "pulg": '"', "watts": "w", "watt": "w", "pzas": "pz",
             "pza": "pz", "piezas": "pz", "pieza": "pz", "pcs": "pz", "unidades": "pz"}.get(u, u)
        out.add((num.replace(",", "."), u))
    return out


ESPEC_RE = re.compile(r'^(\d+(\.\d+)?(v|w|k|p|x|g|gb|tb|mb|ml|kg|cm|mm|mah|hz|ghz|mhz|a|ah|lts?|fps|nits|db|dpi|bar|psi)|'
                      r'ip[x]?\d\d?|usb\d|hdmi\d|ddr\d|wifi\d|\d+en\d|\d+x\d+|x\d+|\d+d|\d+g|\d+k|\d+ma)$')


def codigos(n):
    out = set()
    for t in re.split(r'[\s/,()]+', n):
        for c in t.split("-"):           # "awkf3b-negra" -> "awkf3b", "negra"
            c = c.strip(".:;")
            if len(c) < 2 or not re.search(r'\d', c) or not re.search(r'[a-z]', c):
                continue
            if ESPEC_RE.match(c) or UNIDAD_RE.fullmatch(c):
                continue
            out.add(c)
    return out


def motivo(grupo):
    nombres = [norm(f.get("nombre") or "") for f in grupo]
    meds = [medidas(n) for n in nombres]
    for i in range(len(meds)):
        for j in range(i + 1, len(meds)):
            if meds[i] and meds[j] and meds[i] != meds[j]:
                return f"medidas distintas {sorted(meds[i]-meds[j])[:2]} vs {sorted(meds[j]-meds[i])[:2]}"
    # Un reacondicionado no es el mismo artículo que uno nuevo (Reuse y
    # Amazon Renewed contra el nuevo: otro precio, otra garantía).
    usado = [bool(USADO_RE.search(n)) for n in nombres]
    if any(usado) and not all(usado):
        return "reacondicionado contra nuevo"
    paq = [bool(PAQUETE_RE.search(n)) for n in nombres]
    if any(paq) and not all(paq):
        return "paquete/bundle en solo una ficha"
    cods = [codigos(n) for n in nombres]
    union = set().union(*cods)
    for c in cods:
        if union - c and c - (union - c) == set() and len(union) > len(c):
            pass
    # todo código que tenga una lo tienen todas
    for i in range(len(cods)):
        for j in range(i + 1, len(cods)):
            if cods[i] != cods[j]:
                return f"códigos distintos {sorted(cods[i]-cods[j])[:2]} vs {sorted(cods[j]-cods[i])[:2]}"
    precios = [f.get("precio") for f in grupo if isinstance(f.get("precio"), (int, float)) and f.get("precio") > 0]
    if len(precios) >= 2 and max(precios) / min(precios) >= 1.8:
        return f"precio {max(precios)/min(precios):.1f}x"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("informes", nargs="+")
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--keep-pages", action="store_true")
    args = ap.parse_args()

    grupos = []
    for f in args.informes:
        grupos += json.load(open(f, encoding="utf-8"))
    ok, no = [], collections.Counter()
    ejemplos = collections.defaultdict(list)
    for g in grupos:
        m = motivo(g)
        if m:
            clave = m.split(" ")[0] + (" " + m.split(" ")[1] if m.startswith("medidas") or m.startswith("códigos") or m.startswith("paquete") else "")
            no[clave] += 1
            if len(ejemplos[clave]) < 3:
                ejemplos[clave].append((m, [(f.get("tiendas"), f.get("precio"), (f.get("nombre") or "")[:60]) for f in g]))
        else:
            ok.append(g)
    print(f"Grupos en los informes: {len(grupos)}   pasan el filtro: {len(ok)}   rechazados: {sum(no.values())}")
    for k, v in no.most_common():
        print(f"  {v:5}  {k}")
        for m, fichas in ejemplos[k][:2]:
            print(f"           · {m}")
            for t, p, n in fichas:
                print(f"               {str(t):<28} {str(p):>9}  {n}")
    if not args.aplicar:
        print("(ensayo: corré con --aplicar para escribir)")
        return

    data = load_catalog()
    por_id = {p["id"]: p for p in data["products"]}
    absorbidas = set()
    hechas = 0
    for g in ok:
        fichas = [por_id[f["id"]] for f in g if f["id"] in por_id and f["id"] not in absorbidas]
        if len(fichas) < 2:
            continue
        # misma regla de supervivencia que los otros scripts: id más bajo
        fichas.sort(key=lambda p: int(re.sub(r"\D", "", p["id"]) or 0))
        mcs.fusionar(fichas)
        for p in fichas[1:]:
            absorbidas.add(p["id"])
        hechas += 1
    data["products"] = [p for p in data["products"] if p["id"] not in absorbidas]
    save_catalog(data)
    print(f"Fusiones aplicadas: {hechas}; fichas absorbidas: {len(absorbidas)}; catálogo: {len(data['products']):,}")
    if not args.keep_pages:
        import shutil, os
        for pid in absorbidas:
            d = os.path.join("producto", pid)
            if os.path.isdir(d):
                shutil.rmtree(d)


if __name__ == "__main__":
    main()
