#!/usr/bin/env python3
"""Los avisos de «¿Está en la categoría equivocada?» de la ficha.

DE DÓNDE VIENEN
---------------
El botón de la ficha (js/app.js, setupCategoryReport) guarda en Firestore
reportes-categoria/{auto}: {pid, deCat, deSub, aCat, aSub, creado}. Sin
texto libre ni usuario, así que la colección es de lectura pública y esto la
baja por la API REST con la llave web del sitio (la misma que ya está en
js/firebase-init.js): no hacen falta credenciales de administrador. Las
reglas están en firestore-reportes.rules.

QUÉ HACE CON ELLOS
------------------
Basta UN aviso (decisión del usuario, 26-sep-2026), con dos resguardos:

  1. La ficha sigue donde estaba al avisarla (si ya se movió, está atendido).
  2. Los VECINOS (las 25 fichas de nombre más parecido, sólo con lo que va
     antes de «para»; ver juez_origen.py) no la contradicen: al menos
     MIN_VECINOS de ellos están en la categoría que dice el aviso. -> se mueve.

  Si los vecinos SÍ la contradicen puede ser por dos razones muy distintas:
  la ficha está bien (aviso equivocado), o sus parecidos están todos mal
  puestos junto con ella (los cubrevolantes que un día cayeron en bloque en
  Autopartes). Para distinguirlas se mira el BLOQUE: vecinos con la misma
  cabeza de nombre y en el mismo lugar que la ficha avisada.
    - Sin bloque (menos de MIN_BLOQUE): el aviso va a revisión a mano.
    - Con bloque: los vecinos no sirven de juez (están mal con ella), así
      que se piden jueces que no dependan de ellos: la categoría que le puso
      la tienda (juez_origen.aprender) o dónde vive la cabeza del nombre en
      el resto del catálogo, SIN contar el bloque. Si uno de los dos coincide
      con el aviso y el precio cabe en el destino, se mueve la ficha y,
      ficha por ficha con la misma prueba, el resto del bloque. Lo que no
      pasa la prueba queda en la cola de revisión con el bloque listado.

La subcategoría es la que nombró el aviso; si no nombró ninguna, queda vacía
y completar_subcategorias.py la decide. Lo que se mueve entra además a
data/ejemplos-verificados.jsonl: los modelos aprenden de lo que la gente
corrigió. La cola de revisión (--cola) se guarda en
data/reportes-categoria-cola.json para revisarla en la siguiente auditoría.

USO
---
    python3 scripts/reportes_categoria.py                  # informe y cola
    python3 scripts/reportes_categoria.py --salida /tmp/reportes.json
    python3 scripts/aplicar_movimientos.py /tmp/reportes.json --todos --motivo "avisos de visitantes"
"""
import argparse
import collections
import json
import math
import statistics
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import load_catalog  # noqa: E402
from detectar_mal_clasificados import tokens  # noqa: E402
from juez_origen import CORTES_A_PROPOSITO, aprender, lo_que_es, precio  # noqa: E402
from origen_categorias import cargar as cargar_origen  # noqa: E402
from auditar_subcategorias_tienda import cabeza  # noqa: E402
import ejemplos_verificados as EV  # noqa: E402

PROYECTO = "comparamx"
LLAVE_WEB = "AIzaSyABXhT-z1-61Ghb_H32X5o2pOdedFX0_zU"   # la de js/firebase-init.js, pública
COLECCION = "reportes-categoria"
MIN_AVISOS = 1
MIN_BLOQUE = 3       # vecinos iguales y en el mismo lugar para sospechar error en bloque
MIN_CABEZA = 20
MIN_VECINOS = 0.3
K = 25
MAX_DF = 3000


def bajar_avisos():
    """Todos los documentos de la colección, como dicts planos."""
    base = (f"https://firestore.googleapis.com/v1/projects/{PROYECTO}/databases/(default)/"
            f"documents/{COLECCION}")
    out, token = [], None
    while True:
        q = {"pageSize": "300", "key": LLAVE_WEB}
        if token:
            q["pageToken"] = token
        try:
            with urllib.request.urlopen(base + "?" + urllib.parse.urlencode(q), timeout=60) as r:
                pagina = json.load(r)
        except urllib.error.HTTPError as e:
            # 403 = las reglas de firestore-reportes.rules todavía no están
            # puestas en la consola de Firebase. No es un error de la corrida.
            print(f"Firestore respondió {e.code}: sin avisos que leer "
                  f"({'faltan las reglas de firestore-reportes.rules' if e.code == 403 else e.reason})")
            return out
        for d in pagina.get("documents", []):
            f = d.get("fields", {})
            out.append({k: (v.get("stringValue") if "stringValue" in v else v.get("integerValue"))
                        for k, v in f.items()} | {"_id": d["name"].rsplit("/", 1)[-1]})
        token = pagina.get("nextPageToken")
        if not token:
            return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--salida", help="JSON para aplicar_movimientos.py")
    ap.add_argument("--cola", help="JSON con lo que queda para revisar a mano")
    ap.add_argument("--desde-archivo", help="avisos ya bajados (lista JSON), para probar sin red")
    args = ap.parse_args()

    avisos = json.load(open(args.desde_archivo)) if args.desde_archivo else bajar_avisos()
    print(f"avisos: {len(avisos):,}")
    if not avisos:
        if args.salida:
            json.dump({}, open(args.salida, "w"))
        return

    por_ficha = collections.defaultdict(list)
    for a in avisos:
        if a.get("pid"):
            por_ficha[a["pid"]].append(a)

    data = load_catalog()
    prods = data["products"]
    pos = {p["id"]: i for i, p in enumerate(prods)}
    subs_de = {c["id"]: {s["id"] for s in c.get("subcategories") or []} for c in data["categories"]}

    # Vecinos (índice de palabras del catálogo entero).
    idx, df = collections.defaultdict(list), collections.Counter()
    for i, p in enumerate(prods):
        for w in set(tokens(p.get("name") or "")):
            df[w] += 1
            idx[w].append(i)
    n = len(prods)

    def vecinos(i):
        # Lo que va antes de «para» dice qué es la cosa; pero si ahí sólo queda
        # una palabra muy común («Tenis para niño toy story»), no hay con qué
        # buscar y se usa el nombre entero.
        nombre = prods[i].get("name") or ""
        ws = [w for w in set(tokens(lo_que_es(nombre))) if 0 < df[w] <= MAX_DF]
        if len(ws) < 2:
            ws = [w for w in set(tokens(nombre)) if 0 < df[w] <= MAX_DF]
        sc = collections.Counter()
        for w in ws:
            d = df[w]
            if True:
                peso = math.log(n / d)
                for j in idx[w]:
                    if j != i:
                        sc[j] += peso
        return [j for j, _ in sc.most_common(K)]

    # Jueces que NO son los vecinos, para cuando los vecinos están mal en bloque.
    claves, _, por_cabeza, mandato = aprender(prods, cargar_origen())
    por_sub = collections.defaultdict(list)
    for p in prods:
        x = precio(p)
        if x:
            por_sub[(p["category"], p.get("subcategory"))].append(x)
            por_sub[(p["category"], None)].append(x)
    mediana = {k: statistics.median(v) for k, v in por_sub.items() if len(v) >= 10}

    def origen_dice(i):
        votos = {mandato[k] for k in claves.get(i, ()) if k in mandato}
        return votos.pop() if len(votos) == 1 else None

    def cabeza_dice(i, sin):
        """Dónde vive la cabeza del nombre en el catálogo, SIN contar el bloque
        sospechoso (si no, el bloque mal puesto se vota a sí mismo)."""
        h = cabeza(prods[i].get("name"))
        if not h or h not in por_cabeza:
            return None
        c = collections.Counter(por_cabeza[h])
        for j in sin:
            if cabeza(prods[j].get("name")) == h:
                c[prods[j]["category"]] -= 1
        tot = sum(v for v in c.values() if v > 0)
        if tot < MIN_CABEZA:
            return None
        cat, k = c.most_common(1)[0]
        return cat if k / tot >= 0.5 else None

    def segundo_juez(i, actual, cat, bloque):
        """Los jueces independientes de los vecinos que apoyan mover a `cat`.
        La cabeza del nombre VETA si vive en otra categoría fuera del bloque
        (un aviso equivocado sobre un cubrevolante: el departamento de Walmart
        diría Autopartes, pero «cubrevolante» vive en Autos y motos). El origen
        no cuenta en los cortes que nuestra taxonomía hace a propósito y la
        tienda no (CORTES_A_PROPOSITO de juez_origen.py)."""
        cab = cabeza_dice(i, bloque)
        if cab and cab != cat:
            return []
        apoyo = []
        if origen_dice(i) == cat and (actual, cat) not in CORTES_A_PROPOSITO:
            apoyo.append("origen")
        if cab == cat:
            apoyo.append("cabeza")
        return apoyo

    def precio_cabe(i, cat, sub):
        m, x = mediana.get((cat, sub)) or mediana.get((cat, None)), precio(prods[i])
        return bool(m and x and m / 4 <= x <= m * 4)

    grupos = collections.defaultdict(list)
    ejemplos, cola, revisar = [], collections.Counter(), []

    def mover(j, cat, sub, motivo):
        q = prods[j]
        grupos[f"{q['category']} | {q.get('subcategory') or None} | {cat} | {sub}"].append(q["id"])
        ejemplos.append({"nombre": q["name"], "cat": cat, "sub": sub})
        print(f"  MOVER ({motivo})  {q['id']}  {q['category']}/{q.get('subcategory')} -> {cat}/{sub}  {q['name'][:60]}")

    movidas = set()
    for pid, lista in por_ficha.items():
        i = pos.get(pid)
        if i is None:
            cola["la ficha ya no existe (fusionada u oculta)"] += 1
            continue
        p = prods[i]
        vigentes = [a for a in lista if a.get("deCat") == p["category"]
                    and (a.get("deSub") or None) == (p.get("subcategory") or None)]
        if not vigentes:
            cola["ya se movió desde el aviso"] += 1
            continue
        votos = collections.Counter(a.get("aCat") for a in vigentes if a.get("aCat") in subs_de)
        if not votos:
            cola["sólo «no sé, pero aquí no va»: revisar a mano"] += 1
            revisar.append({"pid": pid, "motivo": "no sé, pero aquí no va", "donde": [p["category"], p.get("subcategory")],
                            "nombre": p["name"]})
            continue
        cat, nv = votos.most_common(1)[0]
        subs = collections.Counter(a.get("aSub") for a in vigentes
                                   if a.get("aCat") == cat and a.get("aSub") in subs_de[cat])
        sub = subs.most_common(1)[0][0] if subs else None
        vec = vecinos(i)
        share = (sum(1 for j in vec if prods[j]["category"] == cat) / len(vec)) if vec else 0.0
        if share >= MIN_VECINOS:
            mover(i, cat, sub, f"{nv} aviso(s), vecinos {share:.0%}")
            movidas.add(i)
            continue
        # Los vecinos no lo acompañan. ¿Es porque la ficha está bien, o porque
        # sus parecidos están TODOS mal puestos con ella? Bloque = vecinos con
        # la misma cabeza de nombre y en el mismo lugar que la ficha avisada.
        h = cabeza(p.get("name"))
        bloque = [j for j in vec if prods[j]["category"] == p["category"]
                  and prods[j].get("subcategory") == p.get("subcategory")
                  and cabeza(prods[j].get("name")) == h]
        if len(bloque) < MIN_BLOQUE:
            cola["los vecinos lo contradicen (no hay bloque): revisar a mano"] += 1
            revisar.append({"pid": pid, "motivo": f"vecinos en contra ({share:.0%})", "a": [cat, sub],
                            "donde": [p["category"], p.get("subcategory")], "nombre": p["name"]})
            continue
        # Jueces independientes de los vecinos: el origen de la tienda y dónde
        # vive la cabeza del nombre fuera del bloque. Basta uno, y el precio.
        apoyo = segundo_juez(i, p["category"], cat, bloque)
        if not apoyo or not precio_cabe(i, cat, sub):
            cola["posible error en bloque sin segundo juez: revisar a mano"] += 1
            revisar.append({"pid": pid, "motivo": "posible error en bloque", "a": [cat, sub],
                            "donde": [p["category"], p.get("subcategory")], "nombre": p["name"],
                            "bloque": [[prods[j]["id"], prods[j]["name"]] for j in bloque]})
            continue
        mover(i, cat, sub, f"{nv} aviso(s) + {'+'.join(apoyo)}, error en bloque")
        movidas.add(i)
        # El resto del bloque se mueve con ella sólo si ESA ficha también tiene
        # un juez independiente a favor y el precio le cabe; si no, a revisión.
        for j in bloque:
            if j in movidas:
                continue
            aj = segundo_juez(j, prods[j]["category"], cat, bloque)
            if aj and precio_cabe(j, cat, sub):
                mover(j, cat, sub, f"bloque de {pid} + {'+'.join(aj)}")
                movidas.add(j)
            else:
                revisar.append({"pid": prods[j]["id"], "motivo": f"bloque de {pid} sin segundo juez", "a": [cat, sub],
                                "donde": [prods[j]["category"], prods[j].get("subcategory")], "nombre": prods[j]["name"]})

    print(f"se mueven: {sum(len(v) for v in grupos.values())}")
    for k, v in cola.most_common():
        print(f"  no: {v:5}  {k}")
    if args.cola:
        json.dump(revisar, open(args.cola, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"cola de revisión: {len(revisar)} -> {args.cola}")
    if args.salida:
        json.dump(grupos, open(args.salida, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        if ejemplos:
            EV.agregar(ejemplos, fuente="avisos de visitantes (botón de la ficha)")
        print(f"-> {args.salida}")


if __name__ == "__main__":
    main()
