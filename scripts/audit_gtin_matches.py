#!/usr/bin/env python3
"""Revisa los cruces por código de barras y deshace los que no son el mismo producto.

EL PROBLEMA
-----------
match_by_gtin.py unía dos publicaciones cuando compartían el código de barras
y la condición (nuevo/usado), pero NO miraba el nombre. Y el `ean` que publica
Elektra no siempre es un código de fabricante: en las herramientas Hyundai
todas comparten el prefijo 6426138, así que varias cayeron en el mismo código
y se unieron entre sí. Ejemplos reales que estaban publicados:

    Bomba De Agua Agrícola Diesel 17 HP ($76,115)  <-  Llave Stilson 8" ($130)
    Hidrolavadora Industrial 20 HP ($105,400)      <-  Tijeras de aviación ($190)
    Aire Minisplit Daewoo ($6,999)                 <-  Control remoto del aire ($139)

La ficha decía "desde $130" para una bomba de $76,115.

EL CRITERIO: LAS DOS SEÑALES A LA VEZ
-------------------------------------
Se deshace un cruce solo cuando FALLAN LAS DOS cosas: el nombre no se parece
Y el precio entre tiendas se va a 5x o más. Ninguna de las dos alcanza sola, y
esto se comprobó sobre el catálogo entero, no se supuso:

  - Solo el nombre NO alcanza. Los nombres de tiendas mexicanas usan sinónimos
    para el mismo artículo (rasuradora / afeitadora / máquina, cortadora /
    recortadora / trimmer), y hasta idiomas distintos: "Mantén a los Hermanos,
    Pierde la Rivalidad" y "Keep the Siblings Lose the Rivalry" son el mismo
    libro y no comparten una palabra. Aplicando solo el nombre salían 1,042
    cruces a deshacer y al revisarlos a mano una buena parte eran correctos
    (la Babyliss UVFoil FXLFS2 contra "BaByliss FX UV Doble Cabezal" es la
    misma afeitadora). Deshacerlos habría roto comparaciones buenas, que es
    justo lo que el sitio existe para dar.

  - Solo el precio NO alcanza. Elektra vende a crédito y marca muchísimo: un
    DualSense a $2,549 contra $799 en Mercado Libre es el MISMO control, y
    huecos de 3x a 5x aparecen en 1,140 cruces perfectamente buenos.

  - Juntas sí discriminan. Entre los cruces de nombre distinto, el 2.4% tiene
    un hueco de 10x o más; entre los de nombre parecido, el 0.15%. Dieciséis
    veces más. De los 40 casos que cumplen las dos condiciones, 39 son
    claramente artículos distintos revisándolos a mano (una bomba de agua
    contra una llave stilson, un minisplit contra su control remoto).

Lo que queda fuera a propósito:

  - Nombre distinto pero precio parecido (unos 1,000 cruces). Puede haber
    errores ahí, pero no se pueden separar de los sinónimos, y como los
    precios se parecen la ficha no queda muy mal aunque el cruce esté mal.
    Sin evidencia para decidir, no se toca.

  - Nombre parecido y precio disparatado (un asiento de bicicleta a $40,000 en
    Elektra contra $285). Las dos tiendas publican de verdad ese precio, y
    mostrar los dos es exactamente para lo que existe un comparador.

Es reanudable: cada tanda de respuestas se anota en data/gtin-auditoria.json
(el nombre que publica Mercado Libre para cada producto), asi que una corrida
cortada no pierde lo consultado y la siguiente sigue donde quedo. El juicio
--comparar los nombres y deshacer-- se rehace entero cada vez sobre lo
anotado, que es gratis y permite cambiar el criterio sin volver a preguntar
15 mil veces.

USO
    python3 scripts/audit_gtin_matches.py --dry-run --min-ratio 5
    python3 scripts/audit_gtin_matches.py --min-ratio 5
    python3 scripts/audit_gtin_matches.py            # todo el catálogo cruzado
"""
import argparse
import json
import os
import re
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog
from match_by_gtin import BY_GTIN, get_json, normalize_gtin

# Palabras que aparecen en todo y no distinguen nada.
STOP = set("""de la el los las un una y o con con para por en del al mas más sin
tipo marca modelo nuevo nueva original color negro negra blanco blanca gris azul
rojo roja verde plata dorado unisex mexico mx pulgada pulgadas cms centimetros
""".split())

# Debajo de esto se considera que no son el mismo artículo.
#
# El número salió de revisar a mano los casos reales, DESPUÉS de arreglar dos
# cosas que hacían fallar la comparación por escritura y no por producto:
#
#   - Plural/singular. "cámaras/cámara" y "bicicleta/bicicletas" contaban como
#     palabras distintas, y por eso el sellador Slime de Mercado Libre no se
#     parecía al mismo sellador Slime nuestro. Se recorta la -s/-es igual que
#     searchStem() en js/app.js.
#   - Código de modelo. "alpine w10s4" contra "Alpine Swt-10s4" es el MISMO
#     subwoofer, pero no comparten ninguna palabra larga. Un código alfanumérico
#     que aparece en los dos nombres (aunque sea dentro de otro) vale por sí
#     solo.
#
# Con eso, en la revisión manual los cruces malos quedaron en 0.00-0.29 y los
# buenos en 0.40 para arriba.
MIN_SIMILITUD = 0.34

# La segunda señal: cuánto se tiene que ir el precio entre tiendas para que,
# SUMADO a que el nombre no coincide, se considere que no es el mismo
# artículo. Ver la explicación de arriba: 5x deja fuera el rango donde los
# huecos grandes son reales (Elektra a crédito llega a 3x-5x sobre Mercado
# Libre en productos que sí son el mismo).
RATIO_PARA_DESHACER = 5.0

CHECKPOINT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "gtin-auditoria.json",
)
CADA = 200


def cargar_checkpoint():
    try:
        with open(CHECKPOINT, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def guardar_checkpoint(estado):
    os.makedirs(os.path.dirname(CHECKPOINT), exist_ok=True)
    tmp = CHECKPOINT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=0, sort_keys=True)
    os.replace(tmp, CHECKPOINT)


def _stem(w):
    """Misma poda de plural que searchStem() en js/app.js."""
    if len(w) >= 7 and w.endswith("es"):
        return w[:-2]
    if len(w) >= 5 and w.endswith("s"):
        return w[:-1]
    return w


def _limpiar(texto):
    t = unicodedata.normalize("NFKD", (texto or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", t)


def _tokens(texto):
    return {_stem(w) for w in _limpiar(texto).split()
            if len(w) >= 3 and w not in STOP}


def _codigos(texto):
    """Tokens alfanuméricos que parecen código de modelo (letras Y dígitos)."""
    return {
        w for w in _limpiar(texto).split()
        if len(w) >= 4 and any(c.isdigit() for c in w) and any(c.isalpha() for c in w)
    }


def _comparten_modelo(a, b):
    """True si un código de modelo de un nombre aparece en el otro.

    Se busca como subcadena porque las tiendas lo escriben con y sin prefijo o
    guion: "w10s4" está dentro de "swt10s4".
    """
    ca, cb = _codigos(a), _codigos(b)
    if not ca or not cb:
        return False
    if ca & cb:
        return True
    # Uno dentro del otro: "10s4" (de "Swt-10s4") está dentro de "w10s4". El
    # mínimo de 4 evita que un "12v" o un "220" hagan coincidir cualquier cosa.
    for x in ca:
        for y in cb:
            corto, largo = (x, y) if len(x) <= len(y) else (y, x)
            if len(corto) >= 4 and corto in largo:
                return True
    return False


def similitud(a, b):
    """Palabras compartidas sobre el nombre más corto (0 a 1).

    Se divide por el más corto y no por la unión: los nombres de Elektra son
    mucho más largos (traen la ficha técnica entera en el título), y con la
    unión un cruce bueno pero de nombres de largo muy distinto daría bajo.
    """
    if _comparten_modelo(a, b):
        return 1.0
    A, B = _tokens(a), _tokens(b)
    if not A or not B:
        return None  # sin palabras útiles no se puede juzgar: no se toca
    return len(A & B) / min(len(A), len(B))


def gtin_de(product):
    for o in product.get("offers") or []:
        if o.get("storeId") != "mercadolibre":
            g = normalize_gtin(o.get("ean"))
            if g:
                return g
    return None


def ratio_de_precios(product):
    por = {}
    for o in product.get("offers") or []:
        t, pr = o.get("storeId"), o.get("price")
        if t and pr:
            por.setdefault(t, []).append(pr)
    if len(por) < 2:
        return 1.0
    m = [min(v) for v in por.values()]
    return max(m) / min(m) if min(m) else 1.0


def candidatos(products, min_ratio):
    for p in products:
        tiendas = {o.get("storeId") for o in (p.get("offers") or [])}
        if "mercadolibre" not in tiendas or len(tiendas) < 2:
            continue
        if ratio_de_precios(p) < min_ratio:
            continue
        g = gtin_de(p)
        if g:
            yield p, g


def limpiar_historial(deshechos, dry_run=False):
    """Saca de data/hist/ la serie de Mercado Libre de los cruces deshechos.

    El historial es de solo-agregar: record_price_history.py anota lo que ve
    hoy y nunca borra, que es lo correcto para una tienda que deja de vender
    un producto --eso es historia de verdad--. Pero acá el precio de Mercado
    Libre nunca fue de este producto: era el de otro artículo que compartía
    el código de barras. Dejarlo haría que la ficha siguiera diciendo "bajó
    de $76,115 a $130".
    """
    from record_price_history import HIST_DIR, cargar, escribir
    from data_io import ROOT as _ROOT

    ids = {d[1] for d in deshechos}
    if not ids:
        return 0
    carpeta = os.path.join(_ROOT, HIST_DIR)
    if not os.path.isdir(carpeta):
        return 0
    quitadas = 0
    for nombre in sorted(os.listdir(carpeta)):
        if not nombre.endswith(".json"):
            continue
        fname = f"{HIST_DIR}/{nombre}"
        hist = cargar(fname)
        toco = False
        for pid in ids & set(hist):
            if "mercadolibre" in hist[pid]:
                del hist[pid]["mercadolibre"]
                quitadas += 1
                toco = True
                if not hist[pid]:
                    del hist[pid]
        if toco and not dry_run:
            escribir(fname, hist)
    return quitadas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--min-ratio", type=float, default=1.0,
                    help="solo revisar productos cuyo precio entre tiendas difiera al menos esto")
    ap.add_argument("--concurrency", type=int, default=4)
    args = ap.parse_args()

    data = load_catalog()
    todos = list(candidatos(data["products"], args.min_ratio))
    nombres = cargar_checkpoint()
    print(f"Cruces a revisar: {len(todos):,}  "
          f"(ya consultados: {sum(1 for p, _ in todos if p['id'] in nombres):,})")

    # 1) Preguntar solo por lo que falte.
    pendientes = [(p, g) for p, g in todos if p["id"] not in nombres]
    stats = {"sin_respuesta": 0, "ambiguo": 0}
    lock = Lock()
    t0 = time.time()

    def work(item):
        p, g = item
        res = get_json(f"{BY_GTIN}?gtin={g}")
        with lock:
            if res is None:
                stats["sin_respuesta"] += 1
                return
            resultados = res.get("results") or []
            if len(resultados) != 1:
                # Sin un unico producto de catalogo no hay nombre con el cual
                # comparar; se anota para no volver a preguntar.
                nombres[p["id"]] = ""
                stats["ambiguo"] += 1
            else:
                nombres[p["id"]] = resultados[0].get("name") or ""
            hechos = len(nombres)
            if hechos % CADA == 0 and not args.dry_run:
                guardar_checkpoint(nombres)
            if hechos % 1000 == 0:
                v = hechos / max(1, time.time() - t0)
                print(f"  consultados {hechos:,}  ({v:.1f}/s)", flush=True)

    if pendientes:
        try:
            with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
                list(pool.map(work, pendientes))
        finally:
            if not args.dry_run:
                guardar_checkpoint(nombres)

    # 2) Juzgar TODO lo anotado (gratis, y repetible con otro criterio).
    stats.update({"ok": 0, "deshechos": 0, "sin_nombre": 0, "sin_consultar": 0,
                  "nombre_distinto_precio_normal": 0})
    deshechos = []
    for p, _ in todos:
        nombre_ml = nombres.get(p["id"])
        if nombre_ml is None:
            stats["sin_consultar"] += 1
            continue
        if not nombre_ml:
            stats["sin_nombre"] += 1
            continue
        s = similitud(p.get("name"), nombre_ml)
        if s is None:
            stats["sin_nombre"] += 1
            continue
        if s >= MIN_SIMILITUD:
            stats["ok"] += 1
            continue
        # Nombre distinto, pero sin la segunda señal no se toca (ver arriba).
        r = ratio_de_precios(p)
        if r < RATIO_PARA_DESHACER:
            stats["nombre_distinto_precio_normal"] += 1
            continue
        quitadas = [o for o in p["offers"] if o.get("storeId") == "mercadolibre"]
        if not quitadas:
            continue
        p["offers"] = [o for o in p["offers"] if o.get("storeId") != "mercadolibre"]
        stats["deshechos"] += 1
        deshechos.append((s, p["id"], p.get("name", ""), nombre_ml,
                          [o.get("price") for o in quitadas], r))

    deshechos.sort(key=lambda x: (x[0], x[1]))
    print("\n=== Cruces deshechos ===")
    for s, pid, nuestro, ml, precios, r in deshechos[:60]:
        print(f"  sim {s:.2f}  {r:.0f}x  {pid}")
        print(f"     nuestro: {nuestro[:74]}")
        print(f"     ML     : {ml[:74]}   (se quita la oferta de ${precios})")
    if len(deshechos) > 60:
        print(f"  ... y {len(deshechos) - 60} más")

    print("\n=== Resumen ===")
    for k, v in stats.items():
        print(f"  {k}: {v:,}")

    if args.dry_run:
        n = limpiar_historial(deshechos, dry_run=True)
        print(f"  (se quitarían {n:,} series de Mercado Libre del historial)")
        print("(--dry-run: no se escribió nada)")
        return
    if stats["deshechos"]:
        n = limpiar_historial(deshechos)
        print(f"Series de Mercado Libre quitadas del historial: {n:,}")
        save_catalog(data)
        print("Guardado.")


if __name__ == "__main__":
    main()
