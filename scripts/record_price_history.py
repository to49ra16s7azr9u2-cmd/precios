#!/usr/bin/env python3
"""Anota el precio de hoy de cada producto, por tienda, en data/hist/.

POR QUÉ EXISTE
--------------
Hasta ahora el refresco diario SOBREESCRIBÍA el precio y el valor anterior se
perdía. Eso es exactamente lo contrario de lo que hace un comparador serio:
en Kakaku.com el gráfico de evolución del precio es la función central, y es
lo único que un competidor NO puede copiar --se construye día a día y no se
puede reconstruir después--.

Vale por tres cosas a la vez:

  - Producto: "¿es buen momento para comprar?" no se puede contestar con el
    precio de hoy. Con la serie sí, y es lo que hace volver a un usuario.
  - SEO: cada ficha gana texto propio que ninguna otra página tiene ("precio
    más bajo registrado: $X el 12 de agosto") y que cambia solo. Es también
    la salida para las 16,427 fichas de una sola tienda, que hoy no tienen
    nada que comparar: contra su propio pasado sí.
  - Datos: una foto del precio de hoy es un commodity que cualquiera saca
    scrapeando. Una serie temporal normalizada por GTIN no, y es lo único de
    acá que se puede licenciar.

FORMATO
-------
data/hist/<slug>-<n>.json, partido igual que data/det (misma posición dentro
de la categoría, mismo tamaño de chunk), para que el navegador pueda pedir
UNA pieza y no el histórico entero:

    {"p123": {"elektra": [7, 499, 12, 449], "mercadolibre": [7, 530]}}

Los pares son (día, precio) y el día es la cantidad de días desde EPOCH. Solo
se anota cuando el precio CAMBIA respecto del último anotado: un producto que
no se movió en un mes ocupa un par, no treinta.

Cuando una tienda DEJA de vender el producto se anota (día, null): la serie
queda cerrada en esa fecha. Sin eso el último precio se arrastraba para
siempre como si fuera el de hoy, y la página de bajadas llegó a anunciar
"bajó en Elektra" de productos que Elektra ya no tenía. Si la tienda vuelve,
la serie sigue con un precio nuevo después del null.

De cada tienda se guarda su precio MÍNIMO en ese producto, que es el que la
ficha muestra como "desde".

QUIÉN PONE ESE PRECIO
---------------------
Junto a las series de precio va "_v": por tienda, QUÉ VENDEDOR era el que
tenía el mínimo ese día, también solo cuando cambia:

    {"p123": {"mercadolibre": [7, 530, 12, 300],
              "_v": {"mercadolibre": [7, "MLM3083968918", 12, "MLM4756848484"]}}}

Sin esto una bajada de precio y un cambio de vendedor eran indistinguibles.
En Mercado Libre una publicación de catálogo tiene varios vendedores, y
cuando aparece uno nuevo más barato el mínimo de la tienda cae de golpe sin
que nadie haya rebajado nada (un teclado "bajó" de $2,980 a $300: el de
$2,980 sigue ahí, se sumó otro). En Elektra pasa al revés: cuando Elektra
se queda sin existencia, el precio publicado pasa a ser el de un tercero
del marketplace, a veces disparatado, y al reponerse "baja" 95%. De las 40
bajadas de 70% o más que había, 13 eran esto. Con "_v", el ranking de
bajadas solo cuenta las de un MISMO vendedor (ver bajada_de() en
generate_seo_pages.py). Las claves que empiezan con "_" no son tiendas: los
lectores del historial (serie_diaria, dailySeries en js/app.js) las saltan.

El vendedor es el id de la publicación en Mercado Libre (MLM…), el sellerId
en las tiendas VTEX (Elektra, Chedraui, Martí; "1" es la tienda misma) y la
tienda en las demás, que solo tienen un vendedor. Si no se sabe (una fila
VTEX de antes de que se guardara el sellerId) se anota null: desconocido, no
"el mismo".
"""
import argparse
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import web_summary
from data_io import (
    DETAIL_CHUNK_SIZE, ROOT, load_catalog, slugify, _category_slugs,
)
from vtex_stores import TIENDAS_VTEX

HIST_DIR = "data/hist"

# Día 0 de la serie. Fijo para siempre: cambiarlo desplazaría todo lo ya
# anotado. Es el día del primer commit con datos del catálogo.
EPOCH = datetime.date(2026, 9, 1)

# Cuánto pasado se conserva en el archivo que sirve el sitio. Un año cubre
# de sobra "¿está barato ahora?" (que es la pregunta) y evita que el
# repositorio crezca sin fin.
DIAS_MAX = 365


def dia_de(fecha):
    return (fecha - EPOCH).days


_ML_ITEM = re.compile(r"MLM-?(\d+)")


def vendedor_de(row):
    """Quién pone el precio de esta fila, o None si no se sabe."""
    tienda = row.get("storeId")
    if row.get("sellerId"):
        return str(row["sellerId"])
    if tienda in TIENDAS_VTEX:
        # Varios vendedores por artículo (ver vendedor_publicable): sin
        # sellerId anotado no se sabe cuál puso el precio.
        return None
    if tienda == "mercadolibre":
        m = _ML_ITEM.search(str(row.get("url") or ""))
        return f"MLM{m.group(1)}" if m else None
    return tienda


def precios_por_tienda(product):
    """{storeId: (precio mínimo de esa tienda en este producto, vendedor)}.

    Mínimo sobre las MISMAS filas que el sitio publica, no sobre
    product["offers"]: las variantes de color se expanden y una publicación
    de catálogo de Mercado Libre se abre por vendedor cuando son 2 o más y
    todos tienen su propio enlace. Se reutiliza el espejo de web_summary.py
    en vez de repetir la regla acá, que era justo de donde venía la
    diferencia: el historial medía la caja de compra y la ficha mostraba el
    vendedor más barato, así que la gráfica dibujaba una línea que no pasaba
    por el precio que el visitante estaba leyendo justo encima (763 series,
    con diferencias de hasta 5x), y de los productos fusionados por color en
    el formato viejo (sin storeId propio) no se anotaba ningún color.
    """
    minimos = {}
    for o in web_summary.seller_rows(product):
        tienda, precio = o.get("storeId"), o.get("price")
        if not tienda or precio is None:
            continue
        try:
            precio = round(float(precio), 2)
        except (TypeError, ValueError):
            continue
        if tienda not in minimos or precio < minimos[tienda][0]:
            minimos[tienda] = (precio, vendedor_de(o))
    return minimos


def anotar(serie, dia, precio):
    """Agrega (dia, precio) a una serie plana. True si cambió algo.

    No se anota si el precio es el mismo que el último, ni se duplica un día
    ya anotado (correr el script dos veces el mismo día no ensucia la serie:
    si el precio cambió entre las dos corridas, se corrige el punto de hoy).
    """
    if serie and serie[-1] == precio:
        return False
    if serie and serie[-2] == dia:
        # Corrección del punto de hoy. Si con eso vuelve al valor de ayer, el
        # punto sobra: se quita en vez de dejar dos iguales seguidos.
        if len(serie) >= 4 and serie[-3] == precio:
            del serie[-2:]
        else:
            serie[-1] = precio
        return True
    serie.extend([dia, precio])
    return True


def podar(serie, dia_hoy):
    """Deja solo el último año, conservando el punto anterior al corte.

    Ese punto de más importa: sin él, una serie cuyo precio no se movió en
    todo el año quedaría vacía y el gráfico no tendría de dónde arrancar.
    """
    corte = dia_hoy - DIAS_MAX
    pares = list(zip(serie[::2], serie[1::2]))
    dentro = [i for i, (d, _) in enumerate(pares) if d >= corte]
    if not dentro:
        return serie[-2:] if serie else serie
    desde = max(0, dentro[0] - 1)
    return [x for par in pares[desde:] for x in par]


def cargar(fname):
    path = os.path.join(ROOT, fname)
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def escribir(fname, payload):
    path = os.path.join(ROOT, fname)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    nuevo = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            if f.read() == nuevo:
                return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(nuevo)
    return True


def ubicacion_actual(products):
    """{id_de_producto: archivo de historial} según el catálogo de HOY.

    El reparto se calcula SIEMPRE con el catálogo actual, nunca con el del
    día que se está anotando. Al rellenar días viejos desde git, la
    categoría y la posición de un producto pueden haber sido otras, y si
    cada día eligiera su propio archivo la serie de un producto quedaría
    desparramada entre varios.
    """
    grupos = {}
    for p in products:
        grupos.setdefault(p.get("category") or "", []).append(p)
    slugs = _category_slugs(grupos.keys())
    donde = {}
    for cat_id, items in grupos.items():
        slug = slugs[cat_id]
        for i, p in enumerate(items):
            donde[p["id"]] = f"{HIST_DIR}/{slug}-{i // DETAIL_CHUNK_SIZE + 1}.json"
    return donde


def registrar(products, fecha, donde, dry_run=False, podar_viejo=True):
    """Anota los precios de `products` con la fecha dada.

    `donde` es el reparto de ubicacion_actual(). Un producto que no esté ahí
    (existía ese día pero ya no) se ignora: guardarle historial sería guardar
    algo que ninguna página puede mostrar.
    """
    dia = dia_de(fecha)
    stats = {"series_nuevas": 0, "puntos": 0, "cierres": 0, "archivos": 0, "ignorados": 0}

    por_archivo = {}
    for p in products:
        fname = donde.get(p["id"])
        if not fname:
            stats["ignorados"] += 1
            continue
        por_archivo.setdefault(fname, []).append(p)

    for fname, items in por_archivo.items():
        hist = cargar(fname)
        for p in items:
            por_tienda = hist.setdefault(p["id"], {})
            vendedores = por_tienda.setdefault("_v", {})
            hoy = precios_por_tienda(p)
            for tienda, (precio, vendedor) in hoy.items():
                serie = por_tienda.get(tienda)
                if serie is None:
                    serie = por_tienda[tienda] = []
                    stats["series_nuevas"] += 1
                if anotar(serie, dia, precio):
                    stats["puntos"] += 1
                # "No se sabe" solo se anota cuando antes sí se sabía: ahí
                # corta la cadena del mismo vendedor. Una serie que sería
                # solo nulls no dice nada y pesaría (68 mil filas de Elektra
                # sin sellerId el primer día: +2.8 MB de historial).
                if vendedor is not None or vendedores.get(tienda):
                    anotar(vendedores.setdefault(tienda, []), dia, vendedor)
            # Tiendas con serie que hoy no venden el producto: se cierra la
            # serie con null. Una serie que ya termina en null no se toca.
            for tienda, serie in por_tienda.items():
                if tienda.startswith("_"):
                    continue
                if tienda not in hoy and serie and serie[-1] is not None:
                    if anotar(serie, dia, None):
                        stats["cierres"] += 1
            if podar_viejo:
                for tienda in list(por_tienda):
                    if tienda == "_v":
                        for t in list(vendedores):
                            vendedores[t] = podar(vendedores[t], dia)
                    else:
                        por_tienda[tienda] = podar(por_tienda[tienda], dia)
            # Un vendedor sin serie de precio (la tienda salió del producto
            # hace más de un año y se podó) no dice nada de nadie.
            for t in list(vendedores):
                if t not in por_tienda:
                    del vendedores[t]
            if not vendedores:
                del por_tienda["_v"]
            if not por_tienda:
                del hist[p["id"]]
        if not dry_run and escribir(fname, hist):
            stats["archivos"] += 1
    return stats


def limpiar_huerfanos(donde, dry_run=False):
    """Borra del historial los productos que ya no están, y los archivos que
    quedaron de un reparto anterior (una categoría renombrada, por ejemplo)."""
    hist_dir = os.path.join(ROOT, HIST_DIR)
    if not os.path.isdir(hist_dir):
        return 0, 0
    vigentes = set(donde.values())
    quitados, archivos = 0, 0
    for nombre in sorted(os.listdir(hist_dir)):
        fname = f"{HIST_DIR}/{nombre}"
        path = os.path.join(hist_dir, nombre)
        if fname not in vigentes:
            archivos += 1
            if not dry_run:
                os.remove(path)
            continue
        hist = cargar(fname)
        sobran = [pid for pid in hist if donde.get(pid) != fname]
        if not sobran:
            continue
        for pid in sobran:
            del hist[pid]
        quitados += len(sobran)
        if not dry_run:
            escribir(fname, hist)
    return quitados, archivos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--fecha", help="YYYY-MM-DD (por defecto hoy). Para rellenar días viejos.")
    args = ap.parse_args()

    fecha = (
        datetime.date.fromisoformat(args.fecha) if args.fecha
        else datetime.date.today()
    )
    data = load_catalog()
    donde = ubicacion_actual(data["products"])
    quitados, archivos_borrados = limpiar_huerfanos(donde, args.dry_run)
    stats = registrar(data["products"], fecha, donde, args.dry_run)
    print(f"Fecha {fecha} (día {dia_de(fecha)})")
    print(f"  series nuevas: {stats['series_nuevas']:,}")
    print(f"  puntos anotados: {stats['puntos']:,}")
    print(f"  series cerradas (la tienda dejó de vender): {stats['cierres']:,}")
    print(f"  archivos escritos: {stats['archivos']:,}")
    if quitados or archivos_borrados:
        print(f"  historial huérfano quitado: {quitados:,} productos, {archivos_borrados} archivos")
    if args.dry_run:
        print("(--dry-run: no se escribió nada)")


if __name__ == "__main__":
    main()
