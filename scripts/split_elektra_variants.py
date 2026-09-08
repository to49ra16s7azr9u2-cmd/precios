#!/usr/bin/env python3
"""Separa fichas que juntaron VARIANTES distintas de Elektra bajo un solo
nombre, y les pone un nombre que las distinga.

DE DÓNDE VIENE EL PROBLEMA
--------------------------
Una corrida vieja fusionó 4,656 productos por NOMBRE EXACTO. Elektra corta
el título de sus publicaciones a un largo fijo, así que variantes distintas
del mismo artículo terminan con el nombre idéntico:

    "Silla cúbica 3 en 1 de Children's Factory para niños, mobiliar"

y bajo ese nombre quedaron diez sillas de colores distintos -- más un pack
de cuatro a $12,649 junto a las sueltas de ~$3,200. El sitio mostraba
"desde $3,115" para todas y las ofrecía como si fueran la misma silla a
diez precios. Peor todavía:

    "Par Discos Olimpicos Bumper 5 kg"  -> modelos mkz-bumpolpr05kg
                                          y mkz-bumpolpr25kg (¡25 kg!)

CÓMO SE DECIDE QUE SON DISTINTAS
--------------------------------
Por la ficha que publica la propia Elektra, no por el nombre ni por el
precio: se pide cada URL y se comparan los atributos que describen la
variante (Color, Modelo, Dimensiones, Material, Capacidad, Tamaño, Talla,
Potencia). Si difieren, son productos distintos y se separan. Si coinciden,
es el MISMO producto publicado dos veces y se deja como está.

EL EAN NO SIRVE PARA ESTO (se probó)
------------------------------------
La primera idea fue usar el código de barras: 1,316 fichas tenían dos
ofertas de Elektra con EAN distinto. Pero mirando los casos uno por uno,
el EAN distinto NO prueba que sean productos distintos -- Elektra les
asigna código propio según el proveedor. El mismo iPhone 17 256GB Azul
aparece con 195950643091 (el GTIN real de Apple) y con 7502326386699 (un
código con prefijo GS1 de México), los dos al MISMO precio y el mismo
color. Separarlos por EAN habría partido en dos una ficha correcta.

CÓMO QUEDAN LOS NOMBRES
-----------------------
Al nombre original se le agrega SOLO el atributo que distingue dentro de
ese grupo ("… — Blue", "… — mkz-bumpolpr25kg"). Agregar todos los
atributos haría nombres larguísimos donde casi todo se repite.

QUÉ SE QUEDA CON LA FICHA ORIGINAL
----------------------------------
El grupo con más ofertas (desempate: el más barato), para que la ficha que
ya está indexada siga siendo la que más gente busca. Las ofertas de OTRAS
tiendas (Mercado Libre, Amazon) se quedan también ahí: no hay forma de
saber a qué variante corresponden, y moverlas a una de las nuevas sería
adivinar.

USO
---
    python3 scripts/split_elektra_variants.py --dry-run --min-spread 1.9
    python3 scripts/split_elektra_variants.py --min-spread 1.9
    python3 scripts/split_elektra_variants.py --min-spread 0   # todo el catálogo
"""
import argparse
import os
import re
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from add_elektra_products import fetch_json  # noqa: E402
from data_io import load_catalog, save_catalog  # noqa: E402

# Atributos que describen CUÁL variante es. En ese orden: el primero que
# difiera dentro del grupo es el que va al nombre.
VARIANT_FIELDS = [
    "Color", "Modelo", "Talla", "Tamaño", "Capacidad",
    "Dimensiones (L x Al x An)", "Material", "Potencia",
]

# Valores de relleno que Elektra pone cuando el campo no aplica o nadie lo
# cargó. No describen una variante, así que no pueden usarse para separar:
# "Modelo: Fisico" solo dice que el videojuego viene en disco, y salió en
# varias fichas distintas del mismo juego.
PLACEHOLDERS = {
    "fisico", "físico", "digital", "n/a", "na", "sin tamano", "sin talla",
    "sin color", "unica", "única", "generico", "genérico", "xyz-123",
    "audifonos xyz", "bocinas xyz", "-", "--", "0", "sin modelo",
}


def usable(value):
    return bool(value) and str(value).strip().lower() not in PLACEHOLDERS


def norm_key(value):
    """Clave para agrupar variantes. Sin esto, "Negro" y "negro" -- la misma
    variante escrita distinto por dos capturistas -- quedaban en dos grupos
    y se partía en dos una ficha que estaba bien. Se quitan además espacios
    y signos, porque la misma variante aparece escrita de las dos formas
    ("SIL-315-G" y "sil 315 g")."""
    if value is None:
        return None
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def same_variant(a, b):
    """True si dos claves describen la MISMA variante. Además de la igualdad
    exacta, una contenida en la otra cuenta como la misma: el iPhone 17 Pro
    Max de Elektra aparece con Modelo "iPhone 17 ProMax" en una publicación y
    "17 Pro Max" en otra -- normalizadas son "iphone17promax" y "17promax", y
    tratarlas como variantes distintas partía en dos una ficha correcta."""
    if a is None or b is None:
        return a == b
    return a == b or a in b or b in a


def distinct_groups(keys):
    """Agrupa claves que son la misma variante y devuelve la lista de
    representantes."""
    reps = []
    for k in keys:
        if not any(same_variant(k, r) for r in reps):
            reps.append(k)
    return reps


def strip_variant_suffix(name):
    """Quita el " — <variante>" que este mismo script pueda haber agregado
    antes, para que volver a correrlo no acumule sufijos."""
    return name.split(" — ")[0].rstrip()


def label_adds_nothing(base_name, label):
    """True si el atributo ya está dicho en el nombre. "Apple iPhone 17 Pro
    Max (256 GB) - Azul profundo — 17 Pro Max" no informa nada nuevo y sí se
    lee peor; en ese caso el nombre se deja como está."""
    if not label:
        return True
    n = re.sub(r"[^a-z0-9]", "", str(base_name).lower())
    l = re.sub(r"[^a-z0-9]", "", str(label).lower())
    return not l or l in n


def rep_for(key, reps):
    for r in reps:
        if same_variant(key, r):
            return r
    return key


def elektra_offers(product):
    return [o for o in (product.get("offers") or []) if o.get("storeId") == "elektra"]


def spread(offers):
    prices = [o["price"] for o in offers if o.get("price")]
    if len(prices) < 2:
        return 1.0
    return max(prices) / min(prices)


def variant_of(url):
    """Atributos de variante que publica Elektra para ESA url, o None si la
    ficha ya no responde (producto dado de baja entre corridas)."""
    slug = re.sub(r"^https?://www\.elektra\.mx/", "", url or "").rsplit("/p", 1)[0]
    if not slug:
        return None
    # Pidiendo cientos de fichas seguidas, Elektra deja caer algunas -- y una
    # ficha que no responde no se puede clasificar, así que su oferta se
    # queda con la ficha original y la separación sale a medias (y distinta
    # en cada corrida). Con reintentos y una pausa creciente, el resultado
    # deja de depender de qué pedido se cayó.
    for intento in range(3):
        data = fetch_json(f"https://www.elektra.mx/api/catalog_system/pub/products/search/{slug}/p")
        if data:
            p = data[0]
            return {f: (p.get(f) or [None])[0] for f in VARIANT_FIELDS if p.get(f)}
        time.sleep(1.5 * (intento + 1))
    return None


def next_id(products, data=None):
    """Primer id libre, y NUNCA uno que ya se haya usado.

    Antes devolvía max(ids existentes) + 1. Si un producto se daba de baja
    --refresh_prices.py poda las publicaciones que Mercado Libre retira, y
    alguna vez se borra a mano-- ese id volvía a quedar libre y el siguiente
    alta se lo llevaba. Pasó de verdad: se dio de baja p125291 (una UGREEN de
    10,000 mAh con precio mal capturado) y el alta siguiente reusó el mismo
    id para otro power bank. Eso rompe cosas que no se ven:

      - /producto/p125291/ ya está indexada por Google apuntando al primero.
      - Los favoritos y el historial de la cuenta guardan ids (Firestore).
      - data/hist/ guarda la serie de precios por id: dos productos
        distintos terminarían compartiendo una sola serie.

    Así que el máximo histórico se guarda en data.json (meta.maxProductId) y
    el id siguiente sale de ahí, no de lo que hay hoy en el catálogo.
    """
    top = 0
    for p in products:
        m = re.match(r"p(\d+)$", p.get("id", ""))
        if m:
            top = max(top, int(m.group(1)))
    if data is not None:
        top = max(top, int((data.get("meta") or {}).get("maxProductId") or 0))
    return top + 1


def registrar_max_id(data, ultimo_id):
    """Deja anotado en el manifiesto el id más alto que se llegó a usar."""
    n = int(re.sub(r"\D", "", str(ultimo_id)) or 0)
    meta = data.setdefault("meta", {})
    meta["maxProductId"] = max(int(meta.get("maxProductId") or 0), n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-spread", type=float, default=1.9,
                    help="solo fichas donde la oferta más cara vale N veces la más barata")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = load_catalog()
    todo = []
    for p in data["products"]:
        offs = elektra_offers(p)
        if len(offs) < 2:
            continue
        if spread(offs) < args.min_spread:
            continue
        todo.append(p)
    if args.limit:
        todo = todo[: args.limit]
    print(f"Fichas a revisar: {len(todo)}")
    if not todo:
        return

    urls = {o["url"] for p in todo for o in elektra_offers(p) if o.get("url")}
    print(f"Fichas de Elektra a consultar: {len(urls)}")
    specs = {}
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        for url, v in zip(urls, pool.map(variant_of, urls)):
            specs[url] = v

    nid = next_id(data["products"], data)
    nuevos, sin_datos, iguales = [], 0, 0
    for p in todo:
        offs = elektra_offers(p)
        vistos = [(o, specs.get(o.get("url"))) for o in offs]
        # Sin ficha de al menos dos ofertas no se puede comparar nada.
        if sum(1 for _, v in vistos if v) < 2:
            sin_datos += 1
            continue
        # El atributo que distingue: el primero de VARIANT_FIELDS con más de
        # un valor entre las ofertas que sí trajeron ficha.
        campo = None
        con_ficha = [v for _, v in vistos if v]
        for f in VARIANT_FIELDS:
            declaran = [v.get(f) for v in con_ficha if usable(v.get(f))]
            # TODAS las ofertas con ficha tienen que declarar el campo. Si a
            # una le falta, no se sabe qué variante es y agruparla aparte
            # sería inventarle una: se vio con un iPhone 17 Pro Max donde
            # una oferta no traía Color y quedaba en un grupo "None" propio.
            if len(declaran) != len(con_ficha):
                continue
            if len(distinct_groups([norm_key(x) for x in declaran])) > 1:
                campo = f
                break
        if not campo:
            iguales += 1
            continue

        # Se agrupa por el valor NORMALIZADO ("Negro" y "negro" son el mismo
        # color; sin esto se partía en dos una variante sola), pero para el
        # nombre se guarda el valor tal como lo escribe la tienda.
        grupos = defaultdict(list)
        etiqueta = {}
        huerfanas = []
        reps = distinct_groups([norm_key(v.get(campo)) for _, v in vistos if v])
        for o, v in vistos:
            if not v:
                # La ficha de Elektra ya no responde (producto dado de baja
                # entre corridas): no se sabe qué variante es. Se queda con
                # la ficha original en vez de estrenar una "variante None",
                # que sería inventarle una variante que nadie declaró.
                huerfanas.append(o)
                continue
            raw = v.get(campo)
            k = rep_for(norm_key(raw), reps)
            etiqueta.setdefault(k, raw)
            grupos[k].append(o)
        # El grupo que se queda con la ficha original: el que más ofertas
        # tiene; a igualdad, el más barato.
        def rank(item):
            key, os_ = item
            return (-len(os_), min(o.get("price") or 0 for o in os_))
        orden = sorted(grupos.items(), key=rank)
        base_key, base_offs = orden[0]
        otros = [o for o in (p.get("offers") or []) if o.get("storeId") != "elektra"]
        p["offers"] = otros + base_offs + huerfanas
        # El nombre base es el ORIGINAL, sin el sufijo que pueda haberle
        # puesto una corrida anterior: sin esto, correr el script dos veces
        # dejaba nombres como "... — Blue — 0756118141912".
        base_name = strip_variant_suffix(p["name"])
        base_label = etiqueta.get(base_key)
        if not label_adds_nothing(base_name, base_label):
            p["name"] = f"{base_name} — {base_label}"

        for key, os_ in orden[1:]:
            nuevo = {
                "id": f"p{nid}",
                "name": (base_name if label_adds_nothing(base_name, etiqueta.get(key))
                         else f"{base_name} — {etiqueta.get(key)}"),
                "brand": p.get("brand", ""),
                "category": p.get("category"),
                "subcategory": p.get("subcategory"),
                "image": p.get("image", "box"),
                "specs": [],
                "offers": os_,
            }
            if p.get("photo"):
                nuevo["photo"] = p["photo"]
            data["products"].append(nuevo)
            nuevos.append((p["id"], nuevo["id"], campo, etiqueta.get(key), len(os_)))
            nid += 1

    print(f"\nSeparadas por {len(set(n[0] for n in nuevos))} fichas -> {len(nuevos)} fichas nuevas")
    print(f"  sin ficha de Elektra suficiente (se dejan como están): {sin_datos}")
    print(f"  variantes iguales -> era el MISMO producto, se deja  : {iguales}")
    for src, dst, campo, key, n in nuevos[:30]:
        print(f"   {src:9} -> {dst:9}  {campo}={str(key)[:28]:28} ({n} oferta/s)")
    if len(nuevos) > 30:
        print(f"   ... y {len(nuevos) - 30} más")

    if args.dry_run:
        print("\n(--dry-run: no se escribió nada)")
        return
    if not nuevos:
        print("\nNada que separar.")
        return
    registrar_max_id(data, nid - 1)
    save_catalog(data)
    print(f"\nGuardado. Catálogo: {len(data['products'])} productos")


if __name__ == "__main__":
    main()
