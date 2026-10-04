#!/usr/bin/env python3
"""Corrige lo que la primera corrida de merge_variantes_tienda.py (04-oct-2026)
juntó de más o nombró mal. Se corre una vez; las corridas siguientes de
merge_variantes_tienda.py ya no lo hacen.

  1. LLANTAS Y RINES. Elektra escribe la medida como «235 70/ R 16», que la
     exclusión por medida no leía: 93 fichas de llanta se quedaron con otras
     medidas (otro rin, otra subcategoría) como «variantes». Se vuelven a
     separar: cada variante recupera su ficha con su id de antes (el nombre
     sale de la versión publicada en git o de la captura de Elektra) y deja de
     redirigirse.
  2. CÓDIGO DE ALMACÉN. «Cabecera ... RGH» / «... TRY» es la misma
     publicación desde otro almacén de Elektra: la variante se marca «dup»
     (la ficha no la ofrece; el importador la sigue reconociendo).
  3. NOMBRE DE UN SOLO AUTO. Las familias sin prefijo común se quedaban con
     el nombre de la primera publicación («Soporte de motor ... 1966 a 1969
     excalibur ...» con 3,670 autos): se nombran con las palabras que
     comparte el 80% del grupo, como hace ya merge_variantes_tienda.py.

USO
---
    python3 scripts/reparar_variantes.py --dry-run
    python3 scripts/reparar_variantes.py
"""
import argparse
import collections
import gzip
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import FUSIONADAS_PATH, id_num, load_catalog, next_id, registrar_max_id, save_catalog  # noqa: E402
from merge_variantes_tienda import _ANIOS, _CODIGO_ALMACEN, _ES_LLANTA, nombre_familia, norm, palabras  # noqa: E402
from subcategorias_divisiones import LLANTAS_SUV, llanta_auto, llanta_suv  # noqa: E402


def nombres_publicados(ids):
    """{id: nombre} de la última versión publicada (git HEAD) para estas
    fichas. data/retirados no sirve: para una absorbida guarda el nombre de
    la ficha que quedó."""
    import subprocess
    raiz = os.path.dirname(AQUI)
    manifiesto = json.loads(subprocess.run(["git", "show", "HEAD:data/data.json"], cwd=raiz,
                                           capture_output=True, check=True).stdout)
    out = {}
    for archivos in manifiesto["categoryFiles"].values():
        for a in archivos:
            r = subprocess.run(["git", "show", f"HEAD:{a}.gz"], cwd=raiz, capture_output=True)
            if r.returncode:
                r = subprocess.run(["git", "show", f"HEAD:{a}"], cwd=raiz, capture_output=True)
                cuerpo = r.stdout
            else:
                cuerpo = gzip.decompress(r.stdout)
            if not cuerpo:
                continue
            fichas = json.loads(cuerpo)
            for q in (fichas.get("products") if isinstance(fichas, dict) else fichas) or []:
                if q.get("id") in ids:
                    out[q["id"]] = q.get("name")
    return out


def titulos_de_captura(ruta):
    """{url de elektra.mx: título} de la captura del árbol de Elektra, para
    las fichas que se dieron de alta y se juntaron en la misma corrida."""
    if not ruta or not os.path.exists(ruta):
        return {}
    with open(ruta, encoding="utf-8") as f:
        return {it["url"]: it["title"] for it in json.load(f)}


def es_llanta(p):
    sub = p.get("subcategory") or ""
    return bool(_ES_LLANTA.search(norm(p.get("nombreTienda") or p.get("name")))) or "Llantas" in sub or "Rines" in sub


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--captura", default="/tmp/elektra/elektra-arbol.json",
                    help="captura de Elektra de la misma corrida (títulos de lo que no estaba publicado)")
    args = ap.parse_args()
    data = load_catalog()
    with open(FUSIONADAS_PATH, encoding="utf-8") as f:
        fusionadas = json.load(f)
    absorbidas = collections.defaultdict(list)
    for vieja, nueva in fusionadas.items():
        absorbidas[nueva].append(vieja)
    con_variantes = {p["id"] for p in data["products"] for o in p.get("offers") or [] if o.get("variants")}
    publicados = nombres_publicados({a for d in con_variantes for a in absorbidas.get(d, [])})
    por_url = titulos_de_captura(args.captura)
    print(f"nombres recuperados: {len(publicados):,} publicados, {len(por_url):,} de la captura")

    def nombres_del_grupo(p, o):
        ns = [p.get("nombreTienda") or p["name"]]
        ns += [publicados[a] for a in absorbidas.get(p["id"], []) if publicados.get(a)]
        ns += [por_url[v["url"]] for v in o.get("variants") or [] if v.get("url") in por_url]
        return ns

    nid = next_id(data["products"], data)
    nuevas, separadas, dups, renombradas = [], 0, 0, 0
    for p in data["products"]:
        for o in p.get("offers") or []:
            vs = o.get("variants")
            if not vs:
                continue
            if es_llanta(p):
                # 1. Separar.
                candidatas = {pid: publicados.get(pid) for pid in absorbidas.get(p["id"], [])}
                usadas = set()
                for v in vs:
                    etiqueta = norm(v["label"].rstrip("…"))
                    pid = next((q for q, n in candidatas.items()
                                if q not in usadas and n and etiqueta and etiqueta in norm(n)), None)
                    base = p.get("nombreTienda") or p["name"]
                    if pid:
                        usadas.add(pid)
                        nombre = candidatas[pid]
                    elif v["url"] in por_url:
                        # Alta de esta misma corrida (Elektra): nunca se publicó,
                        # le toca cualquiera de sus ids absorbidos sin nombre.
                        pid = next((q for q, n in candidatas.items() if q not in usadas and not n), None)
                        if not pid:
                            pid = f"p{nid}"
                            nid += 1
                        usadas.add(pid)
                        nombre = por_url[v["url"]]
                    else:
                        pid = f"p{nid}"
                        nid += 1
                        nombre = (" ".join(w for w, _ in palabras(base)[:max(1, len(palabras(base)) - len(v["label"].split()))])
                                  + " " + v["label"].rstrip("…")).strip()
                    tn = norm(nombre)
                    sub = p.get("subcategory")
                    if sub and sub.startswith("Llantas") and "moto" not in sub:
                        sub = (llanta_suv(tn) if sub in LLANTAS_SUV else llanta_auto(tn)) or sub
                    q = {"id": pid, "name": nombre, "brand": p.get("brand") or "", "category": p["category"],
                         "subcategory": sub, "image": p.get("image") or "box", "specs": [],
                         "offers": [{"storeId": o["storeId"], "price": o["price"], "stock": "in_stock", "url": v["url"]}]}
                    if v.get("photo") or p.get("photo"):
                        q["photo"] = v.get("photo") or p.get("photo")
                    nuevas.append(q)
                    fusionadas.pop(pid, None)
                    separadas += 1
                for campo in ("variants", "variantLabel"):
                    o.pop(campo, None)
                p.pop("alias", None)
                if p.get("nombreTienda"):
                    p["name"] = p.pop("nombreTienda")
                continue
            # 2. Código de almacén.
            for v in vs:
                if not v.get("dup") and _CODIGO_ALMACEN.match(v["label"].strip()):
                    v["dup"] = True
                    dups += 1
            # 3. Nombre de un solo auto.
            if o.get("variantLabel") or p.get("nombreTienda") or len(vs) < 2:
                continue
            nombres = nombres_del_grupo(p, o)
            if len(nombres) < 3 or sum(1 for n in nombres if _ANIOS.search(n)) < 0.8 * len(nombres):
                continue
            nuevo = nombre_familia(nombres, p["name"])
            if nuevo:
                p["nombreTienda"] = p["name"]
                p["name"] = nuevo
                renombradas += 1
    print(f"llantas separadas: {separadas:,} fichas recuperadas; variantes de almacén marcadas: {dups:,}; "
          f"familias renombradas: {renombradas:,}")
    for q in nuevas[:8]:
        print(f"   {q['id']} {q['subcategory']} | {q['name'][:70]}")
    ejemplos = [p for p in data["products"] if p.get("nombreTienda") and "varios modelos" in p["name"]
                and not any(o.get("variantLabel") for o in p.get("offers") or [])]
    for p in ejemplos[:8]:
        print(f"   {p['id']} «{p['nombreTienda'][:50]}» -> «{p['name']}»")
    if args.dry_run:
        print("(--dry-run: no se escribió nada)")
        return 0
    ids = {p["id"] for p in data["products"]}
    data["products"].extend(q for q in nuevas if q["id"] not in ids)
    registrar_max_id(data, nid - 1)
    save_catalog(data)
    with open(FUSIONADAS_PATH, "w", encoding="utf-8") as f:
        json.dump(fusionadas, f, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    print(f"Guardado. Catálogo: {len(data['products']):,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
