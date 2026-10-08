#!/usr/bin/env python3
"""Separa de su ficha las ofertas que no son el mismo producto (fusiones falsas).

POR QUÉ
-------
Una ficha junta ofertas de varias tiendas bajo un nombre. Cuando una de ellas
es en realidad OTRO artículo --otra capacidad, otro paquete, otra variante,
una publicación mal emparejada--, el precio de ese artículo aparece en la
ficha del primero: la peor falla de un comparador (un «mejor precio» que no
es del producto). Mercado Libre es el caso típico: sus ofertas se emparejan
por búsqueda, y la ficha «Memoria PIODATA iXflash 512 GB» tenía la oferta de
«Pen Drive PioData iXflash 128 GB».

CÓMO SE DETECTA
---------------
Sólo se revisan las ofertas cuyo precio queda a 3x o más (o a 1/3 o menos)
de la mediana de las otras de la misma ficha: es donde un error de
emparejamiento cuesta dinero. Para cada una se obtiene el TÍTULO REAL de la
publicación (el Worker de Mercado Libre para sus ofertas; el «slug» de la url
para las tiendas que lo ponen: Elektra, Walmart, Bodega, Sam's, Coppel) y se
compara con el nombre de la ficha:

  - mismas capacidades, medidas, potencias y paquetes en las dos, o en
    ninguna (número con unidad que no coincida = otro artículo);
  - mismos códigos de modelo (token con letras y dígitos);
  - o muy pocas palabras en común.

Si el título contradice a la ficha, la oferta SALE: pasa a una ficha propia
con el título real (nombre, marca, foto y precio de la publicación), en la
misma categoría. Si no lo contradice, se queda: puede ser sólo otro vendedor.
Cuando la ficha tiene sólo dos ofertas y es la PRIMERA la que no cuadra con
las demás, la que sale es la que no se parece al nombre de la ficha.

USO
---
    python3 scripts/corregir_fusiones.py --dry-run        # informe
    python3 scripts/corregir_fusiones.py                  # aplica
"""
import argparse
import collections
import concurrent.futures
import json
import os
import re
import statistics
import sys
import unicodedata
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, next_id, registrar_max_id, save_catalog, url_real  # noqa: E402

WORKER = "https://comparamx-mercadolibre-proxy.comparamx.workers.dev/item?id="
CACHE = "/tmp/ml_titulos.json"
RATIO = 3.0

UNITS = {'gb': 'cap', 'tb': 'cap', 'ml': 'vol', 'l': 'vol', 'lt': 'vol', 'litros': 'vol', 'kg': 'peso', 'g': 'peso',
         'gr': 'peso', 'w': 'pot', 'mah': 'mah', 'pzas': 'pack', 'piezas': 'pack', 'pz': 'pack', 'pack': 'pack',
         'ct': 'pack', 'pulgadas': 'pulg'}
RXU = re.compile(r'(?<![a-z0-9.])(\d+(?:\.\d+)?)\s?(gb|tb|ml|litros|lt|kg|gr|g|w|mah|pzas|piezas|pz|pack|ct|l|pulgadas)(?![a-z])')
SIZES = {'king', 'queen', 'matrimonial', 'individual', 'twin'}
PAQUETE = re.compile(r'\b(bundle|kit|combo|con (?:soporte|accesorios|funda|estuche|base|cargador)|set de|juego de|paquete de|\d+ ?(?:pack|piezas|pzas|pz))\b')


def norm(s):
    s = unicodedata.normalize('NFKD', (s or '').lower())
    return ''.join(c for c in s if not unicodedata.combining(c))


def feats(t):
    t = norm(t).replace(',', '.')
    u = collections.defaultdict(set)
    for v, k in RXU.findall(t):
        u[UNITS[k]].add(float(v) * (1024 if k == 'tb' else 1000 if k in ('l', 'lt', 'litros') else 1))
    sz = {w for w in re.findall(r'[a-z]+', t) if w in SIZES}
    return u, sz, bool(PAQUETE.search(t))


def modelos(t):
    return {m for m in re.findall(r'[a-z0-9]+', norm(t)) if len(m) >= 4 and re.search(r'[a-z]', m) and re.search(r'\d', m)
            and not re.fullmatch(r'\d+(gb|tb|mb|ml|kg|gr|cm|mm|mah|hz|pzas|x|lt|pack|w|v)', m)
            and not re.match(r'(usb|ddr|wifi|nvme|sata|pcie|gen|lpddr)\d', m)}


def palabras(t):
    return {w for w in re.findall(r'[a-z0-9]+', norm(t)) if len(w) > 2}


def _por_diez(x, y):
    """2.2 contra 2200 (kW/W), 14 contra 140: el mismo número mal escrito, no otro artículo."""
    a, b = sorted((x, y))
    return a > 0 and any(abs(b / a - f) < 0.02 * f for f in (10, 100, 1000))


def contradice(nombre, titulo, slug=False, categoria=None):
    """Motivo por el que `titulo` no es el mismo artículo que `nombre`, o None.

    Sólo cuenta lo que es inequívoco: otra capacidad de almacenamiento, otro
    tamaño de cama, otra cantidad de piezas o una medida/potencia que difiere
    más de lo que explica el redondeo (270 ml contra 260 ml es el mismo
    biberón; 247 L contra 90 L, no). Las palabras que cambian entre tiendas
    y los códigos de modelo se descartaron: el 90% de lo que marcaban era el
    mismo producto con otro texto."""
    nu, ns, npq = feats(nombre)
    tu, ts, tpq = feats(titulo)
    # Capacidad: la mayor cifra en GB/TB es el almacenamiento (la RAM va aparte
    # y es menor); si difiere, es otra versión. TB se pasa a GB.
    if nu.get('cap') and tu.get('cap') and categoria not in ('Laptops', 'Computadoras de escritorio'):
        a, b = max(nu['cap']), max(tu['cap'])
        if a != b and min(a, b) >= 32:
            if not (slug and str(int(b)).endswith(str(int(a)))):
                return f"capacidad: {a:g} contra {b:g}"
    if slug:
        pass
    else:
        for k, tol in (('vol', 0.15), ('peso', 0.15), ('pot', 0.2), ('pack', 0.25), ('pulg', 0.1)):
            if nu.get(k) and tu.get(k) and not any(abs(x - y) <= tol * max(x, y) or _por_diez(x, y) for x in nu[k] for y in tu[k]):
                return f"{k}: {sorted(nu[k])} contra {sorted(tu[k])}"
    if ns and ts and not (ns & ts):
        return f"tamaño: {sorted(ns)} contra {sorted(ts)}"
    return None


def slug_titulo(url):
    u = url_real(url) or url or ""
    p = urllib.parse.unquote(urllib.parse.urlparse(u).path)
    host = urllib.parse.urlparse(u).netloc
    s = ""
    if "/ip/" in p:
        partes = [x for x in p.split("/ip/")[1].split("/") if x]
        s = max(partes[:-1] or [""], key=len) if len(partes) > 1 else ""
    elif "/pdp/" in p:
        s = re.sub(r'-(pm|mkp)-\d+$', '', p.split("/pdp/")[1].strip("/"))
    elif host.endswith("elektra.mx") and p.endswith("/p"):
        s = re.sub(r'-\d{8,}$', '', p[:-2].split("/")[-1])
    if not s:
        return None
    return s.replace("-", " ")


def ml_id(url):
    m = re.search(r'(MLM)-?(\d+)', url_real(url) or url or "")
    return f"MLM{m.group(2)}" if m else None


def titulo_ml(item_id, cache):
    if item_id in cache:
        return cache[item_id]
    try:
        with urllib.request.urlopen(urllib.request.Request(WORKER + item_id, headers={'User-Agent': 'Mozilla/5.0'}), timeout=40) as r:
            d = json.loads(r.read().decode("utf-8"))
        cache[item_id] = {k: d.get(k) for k in ("title", "brand", "photo", "price", "gtin")}
    except Exception:
        cache[item_id] = None
    return cache[item_id]


def guardar_cache(cache):
    tmp = CACHE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(dict(list(cache.items())), f)
    os.replace(tmp, CACHE)


def candidatas(p, todas=False):
    """Índices de ofertas con precio a RATIO veces de la mediana de las otras."""
    ofertas = p.get("offers") or []
    if len(ofertas) < 2 or p.get("colorVariants"):
        return []
    out = []
    for i, o in enumerate(ofertas):
        if not o.get("price"):
            continue
        if todas:
            out.append(i)
            continue
        otros = [x["price"] for j, x in enumerate(ofertas) if j != i and x.get("price")]
        if not otros:
            continue
        m = statistics.median(otros)
        if m and (o["price"] >= RATIO * m or o["price"] <= m / RATIO):
            out.append(i)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--todas", action="store_true",
                    help="revisar TODAS las ofertas de las fichas con varias (no sólo las de precio atípico)")
    ap.add_argument("--sin-ml", action="store_true", help="con --todas, no consultar Mercado Libre")
    ap.add_argument("--hilos", type=int, default=6)
    ap.add_argument("--informe", default="/tmp/corregir_fusiones.json")
    args = ap.parse_args()

    data = load_catalog()
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    plan = []          # (producto, índice de oferta, título real, datos extra, motivo)
    pendientes = {}
    for p in data["products"]:
        for i in candidatas(p, args.todas):
            o = p["offers"][i]
            if o.get("storeId") == "mercadolibre" and not args.sin_ml:
                iid = ml_id(o.get("url") or "")
                if iid:
                    pendientes[iid] = True
    ids = [i for i in pendientes if i not in cache]
    print(f"Ofertas de Mercado Libre a consultar: {len(ids)} (en caché {len(pendientes) - len(ids)})", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.hilos) as ex:
        for n, _ in enumerate(ex.map(lambda i: titulo_ml(i, cache), ids), 1):
            if n % 100 == 0:
                print(f"  {n}/{len(ids)}", flush=True)
                guardar_cache(cache)
    guardar_cache(cache)

    for p in data["products"]:
        cand = candidatas(p, args.todas)
        if not cand:
            continue
        ofertas = p["offers"]
        for i in cand:
            o = ofertas[i]
            store = o.get("storeId")
            if store == "mercadolibre":
                if args.sin_ml:
                    continue
                d = cache.get(ml_id(o.get("url") or "") or "")
                if not d or not d.get("title"):
                    continue
                titulo, extra = d["title"], d
            else:
                titulo = slug_titulo(o.get("url") or "")
                extra = {}
                if not titulo or len(titulo.split()) < 4:
                    continue
            # Con dos ofertas el precio es simétrico: sale la que no se parece a la ficha.
            if len(ofertas) == 2 and i == 0:
                continue
            motivo = contradice(p["name"], titulo, slug=store != "mercadolibre", categoria=p.get("category"))
            if motivo:
                plan.append((p, i, titulo, extra, motivo))
    print(f"\nOfertas que contradicen a su ficha: {len(plan)} en {len({x[0]['id'] for x in plan})} fichas")
    for p, i, titulo, extra, motivo in plan[:40]:
        o = p["offers"][i]
        print(f"  {p['id']:9} {o['storeId'][:6]:6} ${o['price']:>9,.2f} | {p['name'][:42]:42} | {titulo[:42]:42} | {motivo}")
    json.dump([{"id": p["id"], "name": p["name"], "i": i, "store": p["offers"][i]["storeId"], "price": p["offers"][i]["price"],
                "titulo": t, "motivo": m} for p, i, t, e, m in plan], open(args.informe, "w"), ensure_ascii=False, indent=1)
    if args.dry_run or not plan:
        print(f"\n(informe en {args.informe}{'; --dry-run: nada guardado' if args.dry_run else ''})")
        return

    nid = next_id(data["products"], data)
    quitar = collections.defaultdict(set)
    nuevas = []
    grupos = collections.OrderedDict()
    for p, i, titulo, extra, motivo in plan:
        quitar[p["id"]].add(i)
        grupos.setdefault((p["id"], norm(titulo)), []).append((p, i, titulo, extra))
    for (_, _), miembros in grupos.items():
        p, i, titulo, extra = miembros[0]
        o = p["offers"][i]
        if o.get("storeId") == "mercadolibre":
            nombre, foto, marca = extra.get("title"), extra.get("photo"), extra.get("brand") or ""
        else:
            nombre, foto, marca = titulo.strip().capitalize(), None, p.get("brand") or ""
        nuevo = {"id": f"p{nid}", "name": nombre, "brand": marca, "category": p["category"],
                 "subcategory": p.get("subcategory"), "image": p.get("image") or "box", "specs": [],
                 "offers": [m[0]["offers"][m[1]] for m in miembros]}
        if foto:
            nuevo["photo"] = foto
        elif p.get("photo") and o.get("storeId") != "mercadolibre":
            nuevo["photo"] = p["photo"]
        if extra.get("gtin"):
            nuevo["gtin"] = extra["gtin"]
        nuevas.append(nuevo)
        nid += 1
    for p in data["products"]:
        if p["id"] in quitar:
            p["offers"] = [o for j, o in enumerate(p["offers"]) if j not in quitar[p["id"]]]
    data["products"].extend(nuevas)
    registrar_max_id(data, nid - 1)
    save_catalog(data)
    print(f"\nSeparadas {len(nuevas)} ofertas a fichas propias. Catálogo: {len(data['products'])} productos")


if __name__ == "__main__":
    main()
