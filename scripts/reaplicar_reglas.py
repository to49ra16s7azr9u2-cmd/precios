#!/usr/bin/env python3
"""Aplica las reglas de HOY a las fichas que ya están en el catálogo.

EL PROBLEMA (23-sep-2026)
-------------------------
Al buscar por qué quedaban fichas mal clasificadas, la causa más grande no
era una regla mala sino una regla ARREGLADA: clasificar_captura_perifericos.py
decide la categoría sólo al dar de alta. Cuando una regla se corrige, la
corrección vale para lo que entra después; lo que entró con la regla vieja
se queda donde estaba. Ejemplo: la regla de All in One aceptaba «todo en
uno» en cualquier título y metió en Computadoras de escritorio carriolas,
recortadoras y pasta dental. Se arregló la regla y esas fichas seguían ahí.

kakaku.com no tiene este problema porque la categoría de cada producto se
deriva de un maestro central: si cambia la definición, se remapea todo.
Este script es ese remapeo. Corre en cada regeneración y hace que el
catálogo entero obedezca a las reglas vigentes.

CÓMO DECIDE
-----------
Para cada ficha pasa su nombre por decidir() (la misma función que usa la
captura: EXPLICITOS, FUERA, reglas, el sustantivo que manda, repartidores
de subcategoría). Si hoy la mandaría a OTRA categoría, la mueve, salvo:

  1. Candado a mano. Lo que una persona movió (data/clasificacion-a-mano.json,
     que escribe aplicar_movimientos.py) no lo deshace una regla. Para las
     decisiones viejas, que la bitácora sólo guarda por grupo, no se
     revierte un movimiento «de A a B» que la bitácora registra como hecho
     a mano de B a A.
  2. Fuente estructurada. Lo que sólo vende Mercado Libre tiene su categoría
     del árbol de categorías de la tienda (domain_id), no de un título.
  3. Coherencia. El título tiene que ARRANCAR como los productos de la
     categoría nueva (es_coherente: alguna de sus primeras palabras, sin
     contar las que vienen tras «de», es propia de ella). Una regla que se
     dispara con un complemento («Cuadro canvas ... cafetera antigua»,
     «Rompecabezas de perros») no mueve nada: va al informe.
  4. Veto del catálogo. Un modelo bayesiano entrenado sobre el catálogo
     entero puntúa las dos categorías; si prefiere la actual por más de
     VETO nats, no se mueve y va al informe. Es lo que atrapa una regla que
     hoy está MAL (la de RAM se llevaba las PC de escritorio que dicen
     «16 GB de RAM»): el informe agrupa esos conflictos por regla para
     arreglarla, en vez de estropear el catálogo con ella.
  5. Lo que hoy caería en FUERA o no encaja en nada se queda: esto no borra.

Sólo cambia la categoría (con la subcategoría que da el repartidor de la
categoría nueva). La subcategoría dentro de la misma categoría es trabajo
de los repartidores y de sync_subcategories.

CACHÉ
-----
Pasar 460 mil títulos por el clasificador lleva ~20 min en 4 procesos. La
decisión se guarda por (id, nombre) junto con la huella del clasificador y
de sus tablas; si nada de eso cambió, la corrida siguiente no reclasifica
nada. Cuando cambia una regla, se reclasifica todo: justamente el caso.

USO
---
    python3 scripts/reaplicar_reglas.py            # informe, no toca nada
    python3 scripts/reaplicar_reglas.py --aplicar  # mueve y anota en la bitácora
"""
import argparse
import collections
import datetime
import hashlib
import io
import json
import math
import multiprocessing
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
from data_io import load_catalog, save_catalog  # noqa: E402
from detectar_mal_clasificados import Bayes, tokens  # noqa: E402

CANDADO = os.path.join(ROOT, "data", "clasificacion-a-mano.json")
BITACORA = os.path.join(ROOT, "data", "movimientos-aplicados.json")
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "comparamex", "reaplicar-reglas.json")
VETO = 4.0   # nats (~55 veces más probable la categoría actual)
FUENTES_ESTRUCTURADAS = {"mercadolibre"}
ARCHIVOS_DEL_CLASIFICADOR = [
    "clasificar_captura_perifericos.py", "subcategorias_finas.py", "subcategorias_finas_ola2.py",
    "subcategorias_redes.py", "deportes_por_deporte.py", "atipicos.py",
]
# data/vocabulario-cabeza.json NO entra en la huella: se regenera en cada
# corrida y cambia un poco con cada ficha nueva, así que reclasificaría todo
# (~20 min) todos los días. Es una señal secundaria (el sustantivo que
# manda y la coherencia); cuando cambie una regla de verdad, la huella de
# los .py dispara la corrida completa igual.


def huella_clasificador():
    h = hashlib.sha1()
    for nombre in ARCHIVOS_DEL_CLASIFICADOR:
        ruta = os.path.join(AQUI, nombre)
        if os.path.exists(ruta):
            with open(ruta, "rb") as f:
                h.update(f.read())
    return h.hexdigest()[:16]


_clasif = None


def _init():
    global _clasif
    import clasificar_captura_perifericos as c  # noqa: E402
    _clasif = c


def _decidir(par):
    pid, asin, nombre, marca = par
    d = _clasif.decidir({"asin": asin or pid, "title": nombre})
    if d["estado"] != "alta":
        return pid, None
    coherente = d["via"] in ("explicito", "antes_de_fuera") or _clasif.es_coherente(nombre, d["category"], marca)
    return pid, [d["category"], d["subcategory"], d["image"], d["via"], d.get("regla"), coherente]


def asin_de(p):
    for o in p.get("offers") or []:
        m = re.search(r"/dp/([A-Z0-9]{10})", o.get("url") or "")
        if m:
            return m.group(1)
    return None


def cargar_json(ruta, defecto):
    try:
        with io.open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return defecto


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--procesos", type=int, default=max(1, os.cpu_count() or 1))
    ap.add_argument("--informe", help="JSON con los movimientos y los conflictos, para revisar")
    ap.add_argument("--ejemplos", type=int, default=2)
    args = ap.parse_args()

    data = load_catalog()
    productos = data["products"]
    huella = huella_clasificador()
    cache = cargar_json(CACHE, {})
    if cache.get("huella") != huella:
        cache = {"huella": huella, "d": {}}
    memo = cache["d"]

    pendientes = []
    for p in productos:
        clave = hashlib.sha1((p["id"] + "\0" + (p.get("name") or "")).encode()).hexdigest()[:12]
        if memo.get(p["id"], [None])[0] != clave:
            pendientes.append((p["id"], asin_de(p), p.get("name") or "", p.get("brand") or ""))
    print(f"fichas: {len(productos):,}; a reclasificar (clasificador {huella}): {len(pendientes):,}")
    if pendientes:
        with multiprocessing.Pool(args.procesos, initializer=_init) as pool:
            for i, (pid, dec) in enumerate(pool.imap_unordered(_decidir, pendientes, chunksize=500)):
                memo[pid] = [None, dec]
                if (i + 1) % 50000 == 0:
                    print(f"  {i + 1:,}")
        nombres = {p["id"]: p.get("name") or "" for p in productos}
        for pid, _, _, _ in pendientes:
            memo[pid][0] = hashlib.sha1((pid + "\0" + nombres[pid]).encode()).hexdigest()[:12]
        vivos = {p["id"] for p in productos}
        cache["d"] = {k: v for k, v in memo.items() if k in vivos}
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        with open(CACHE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, separators=(",", ":"))
        memo = cache["d"]

    # Candados
    a_mano = cargar_json(CANDADO, {})
    revertir_no = set()
    for e in cargar_json(BITACORA, []):
        if e.get("automatico"):
            continue
        for k in (e.get("grupos") or {}):
            partes = [x.strip() for x in k.split("|")]
            if len(partes) == 4 and partes[0] != partes[2]:
                revertir_no.add((partes[2], partes[0]))   # (hoy en, iría a)

    _vec = []

    def vecinos():
        if not _vec:
            from vecinos_catalogo import Vecinos
            _vec.append(Vecinos(productos))
        return _vec[0]

    # Modelo del catálogo (para el veto)
    modelo = Bayes()
    toks = {}
    for p in productos:
        ts = tokens(p.get("name"))
        toks[p["id"]] = ts
        if p.get("category") and p["category"] != "Otros":
            modelo.entrenar(p["category"], ts)
    modelo.preparar()

    subs_de = {c["id"]: {s["id"] for s in (c.get("subcategories") or [])} for c in data["categories"]}
    mover, conflictos = collections.defaultdict(list), collections.defaultdict(list)
    motivos = collections.Counter()
    por_id = {p["id"]: p for p in productos}
    for p in productos:
        dec = (memo.get(p["id"]) or [None, None])[1]
        if not dec:
            continue
        cat2, sub2, img, via, n_regla, coherente = dec
        cat = p.get("category")
        if cat2 == cat or cat2 not in subs_de:
            continue
        if sub2 and sub2 not in subs_de[cat2]:
            sub2 = None
        if a_mano.get(p["id"], [None])[0] == cat:
            motivos["candado: movida a mano"] += 1
            continue
        if (cat, cat2) in revertir_no:
            motivos["candado: revertiría un movimiento de la bitácora"] += 1
            continue
        tiendas = {o.get("storeId") for o in p.get("offers") or []}
        if tiendas and tiendas <= FUENTES_ESTRUCTURADAS:
            motivos["fuente estructurada (Mercado Libre)"] += 1
            continue
        if not coherente:
            motivos["el título no arranca como la categoría nueva"] += 1
            conflictos[f"regla#{n_regla} ({via}) sin coherencia | {cat} -> {cat2}"].append(p["id"])
            continue
        pt = modelo.puntajes(toks[p["id"]])
        # El veto cede cuando los vecinos (vecinos_catalogo.py) respaldan a la
        # regla: dos jueces contra uno. Sin esto, lo que se archivó mal en
        # bloque quedaba protegido por el propio error -- la Surface Studio,
        # el NAS de Synology y los monitores que estaban en Celulares hacían
        # que el Bayes «prefiriera» Celulares para ellos mismos (24-sep-2026).
        if cat in pt and cat2 in pt and pt[cat] - pt[cat2] > VETO \
                and not vecinos().respalda(cat2, cat, pid=p["id"]):
            motivos["veto del catálogo"] += 1
            conflictos[f"regla#{n_regla} ({via}) | {cat} -> {cat2}"].append(p["id"])
            continue
        mover[(cat, p.get("subcategory"), cat2, sub2, img)].append(p["id"])

    total = sum(len(v) for v in mover.values())
    print(f"\nse mueven: {total:,} en {len(mover)} grupos")
    for k, n in motivos.most_common():
        print(f"  no se mueven: {n:6,}  {k}")
    for k, v in sorted(mover.items(), key=lambda kv: -len(kv[1]))[:40]:
        print(f"{len(v):6}  {k[0]} / {k[1]}  ->  {k[2]} / {k[3]}")
        for x in v[:args.ejemplos]:
            print(f"            {por_id[x]['name'][:85]}")
    print("\nconflictos por regla (la regla de hoy contradice al catálogo: revisar la regla):")
    for k, v in sorted(conflictos.items(), key=lambda kv: -len(kv[1]))[:25]:
        print(f"{len(v):6}  {k}")
        for x in v[:args.ejemplos]:
            print(f"            {por_id[x]['name'][:85]}")
    if args.informe:
        with open(args.informe, "w", encoding="utf-8") as f:
            json.dump({"mover": {" | ".join(map(str, k)): v for k, v in mover.items()},
                       "conflictos": conflictos}, f, ensure_ascii=False, indent=1)

    if not args.aplicar or not total:
        if not args.aplicar:
            print("\n(sin --aplicar: no se tocó el catálogo)")
        return
    for (cat, sub, cat2, sub2, img), ids in mover.items():
        for pid in ids:
            p = por_id[pid]
            p["category"], p["subcategory"] = cat2, sub2
            if img:
                p["image"] = img
    save_catalog(data)
    bit = cargar_json(BITACORA, [])
    bit.append({"fecha": datetime.date.today().isoformat(), "origen": "reaplicar_reglas.py",
                "motivo": f"reglas de hoy (clasificador {huella}) aplicadas al catálogo",
                "automatico": True,
                "grupos": {f"{k[0]} | {k[1]} | {k[2]} | {k[3]}": len(v) for k, v in mover.items()}})
    with io.open(BITACORA, "w", encoding="utf-8") as f:
        json.dump(bit, f, ensure_ascii=False, indent=1)
    print(f"\nGuardado: {total:,} fichas movidas; bitácora actualizada.")


if __name__ == "__main__":
    main()
