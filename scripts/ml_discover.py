#!/usr/bin/env python3
"""Descubre productos nuevos en Mercado Libre todos los días, sin listas a mano.

POR QUÉ
-------
Mercado Libre es la única tienda con API en vivo y la que más se cruza con
las demás por código de barras, pero sus productos entraban solo cuando
alguien escribía a mano una lista de consultas (add_products.py con un
targets.json: dominio + palabras clave + categoría del sitio). Con 331
subcategorías eso no escala, y el catálogo de Mercado Libre se quedaba en
lo que se cargó el primer día.

CÓMO
----
La lista de consultas se deriva de la propia taxonomía del sitio, que es lo
único que hace falta saber para dar de alta un producto:

  1. Cada subcategoría del sitio ("Libreros" en "Muebles") es una frase.
     domain_discovery de Mercado Libre (ver ml_domains.py) propone a qué
     dominios de su catálogo corresponde ("MLM-BOOKCASES").
  2. El dominio se CONFIRMA contra nuestro propio catálogo, no contra el
     nombre: se pide una página del dominio y se mira qué productos de esa
     página ya tenemos. Si al menos tres son conocidos y el 80% o más de
     ellos está en la categoría buscada, el dominio es de esa categoría.
     Si no hay con qué comprobarlo, no se carga nada de ahí. La primera
     versión aceptaba el dominio por parecido de nombre y para "De pared"
     en Cargadores proponía "Cargadores de vehículos eléctricos".
  3. Dentro del dominio se consulta por el nombre de la subcategoría y por
     las marcas que más productos tienen en esa subcategoría en nuestro
     catálogo: son las consultas que más devuelven, y son distintas cada
     vez que el catálogo cambia.
  4. add_products.py hace el resto (veto de consumibles y accesorios,
     reacondicionados, duplicados por id y por nombre) y da de alta lo
     nuevo con la CATEGORÍA puesta y SIN subcategoría: dentro de un mismo
     dominio conviven tipos distintos (en cargadores de celular, los de
     pared con los power bank), así que heredar la subcategoría del
     target sería adivinar. Se la ponen después las reglas por nombre
     (clasificar_subcategorias.py, classify_cargadores.py), que se niegan
     ante la duda.

Cada corrida atiende una VENTANA de subcategorías, elegida por el día (el
mismo día siempre atiende las mismas, así que una corrida repetida no
duplica trabajo), y va rotando: con 40 por día, las 331 se recorren en
poco más de una semana. Así el costo diario es acotado (~40 consultas de
dominio + ~120 de catálogo) y ninguna subcategoría se queda sin revisar.

QUÉ NO ENTRA
------------
Las categorías que el catálogo decidió no comparar (ropa, calzado, lujo
de segunda mano, papelería) y las subcategorías que no nombran un producto
("Otros", "Varios", "Accesorios"): buscar "Otros Videojuegos" en Mercado
Libre no dice qué es lo que se está buscando.

USO
---
    python3 scripts/ml_discover.py --dry-run          # qué haría hoy
    python3 scripts/ml_discover.py                    # la ventana de hoy
    python3 scripts/ml_discover.py --dia 3 --ventana 5  # una ventana concreta, para probar
"""
import argparse
import collections
import datetime
import json
import os
import re
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import add_products  # noqa: E402
from data_io import load_catalog, sin_acentos  # noqa: E402
from ml_domains import domains_for  # noqa: E402

# Cuántos productos ya conocidos tiene que haber en la página de muestra de
# un dominio, y qué fracción de ellos en la categoría buscada, para creer
# que el dominio es de esa categoría.
MIN_CONOCIDOS = 3
MIN_ACUERDO = 0.8

# Mismo día 0 que el historial de precios: la rotación se calcula desde acá.
EPOCH = datetime.date(2026, 9, 1)
VENTANA = 40          # subcategorías por corrida
MARCAS_POR_SUB = 2    # consultas por marca, además de la del nombre
MAX_POR_CONSULTA = 12

CATEGORIAS_FUERA = {
    "Ropa y accesorios", "Calzado", "Artículos de lujo (preowned)",
    "Papelería y oficina", "Otros", "Fitness",
}
# Subcategorías que califican, no nombran: no sirven como consulta.
GENERICAS = {
    "otros", "otros juegos", "varios", "accesorios", "accesorios y repuestos",
    "grande", "mediana", "pequena", "consumibles", "software", "otro calzado",
    "oficina", "gaming", "gamer", "oficina y estudio", "resistentes",
    "torre / escritorio", "all in one", "mini pc", "full hd y hd", "4k y qled",
    "membrana", "mecanicos", "ergonomicos", "componentes",
    "perifericos y accesorios", "hasta 10,000 mah", "10,000 a 20,000 mah",
    "mas de 20,000 mah", "uso comercial", "woodestic", "dji", "bebes",
    "android", "iphone", "apple", "apple (ipad)", "portatiles",
    "para ninos y principiantes", "con gps", "fpv y carreras", "mini drones",
}
STOP = {"de", "del", "la", "las", "el", "los", "y", "e", "para", "con", "sin",
        "en", "a", "o", "u", "por", "otros", "otras", "accesorios"}


def palabras(texto):
    return {w for w in re.findall(r"[a-z0-9]+", sin_acentos(texto)) if len(w) > 2 and w not in STOP}


def subcategorias_del_sitio(data):
    """[(cat_id, cat_name, sub_id, sub_name, icono)] en orden fijo."""
    out = []
    for c in data["categories"]:
        if c["name"] in CATEGORIAS_FUERA or c["id"] in CATEGORIAS_FUERA:
            continue
        for s in c.get("subcategories") or []:
            if sin_acentos(s["name"]) in GENERICAS:
                continue
            out.append((c["id"], c["name"], s["id"], s["name"], c.get("icon") or "box"))
    return out


def marcas_top(products, cat_id, sub_id, n):
    cuenta = collections.Counter()
    for p in products:
        if p.get("category") == cat_id and p.get("subcategory") == sub_id and p.get("brand"):
            marca = p["brand"].strip()
            # La marca "de la tienda" (Elektra, Chedraui) no es una marca.
            if marca and sin_acentos(marca) not in {"elektra", "chedraui", "marti", "generico", "generica"}:
                cuenta[marca] += 1
    return [m for m, _ in cuenta.most_common(n)]


def ventana_de(subs, dia, tam):
    if not subs:
        return []
    i0 = (dia * tam) % len(subs)
    doble = subs + subs
    return doble[i0:i0 + tam]


def indice_conocidos(products):
    """{id de catálogo MLM…: categoría} y {firma del nombre: categoría} de
    lo que ya está en el catálogo: con esto se comprueba de qué es un
    dominio mirando sus productos, no su nombre."""
    por_id, por_firma = {}, {}
    for p in products:
        por_firma[add_products.sig(p["name"])] = p.get("category")
        nodos = list(p.get("offers") or [])
        for v in p.get("colorVariants") or []:
            nodos += list(v.get("offers") or []) if "offers" in v else [v]
        for o in nodos:
            i = add_products.ml_id(o.get("url"))
            if i:
                por_id[i] = p.get("category")
    return por_id, por_firma


MIN_TITULOS = 10


def _raices(texto):
    # "audifonos" y "audifono" comparten raíz; con 5 letras alcanza para
    # que "barra"/"barras", "bocina"/"bocinas" cuenten como la misma.
    return {w[:5] for w in palabras(texto)}


def titulos_nombran(items, nombres):
    """True si el 80% de los títulos contiene alguna palabra de la
    categoría o subcategoría (por raíz)."""
    aciertos = 0
    for it in items:
        if _raices(it.get("title") or "") & nombres:
            aciertos += 1
    return aciertos / len(items) >= MIN_ACUERDO


def marcas_de_categoria(products, cat_id, n):
    cuenta = collections.Counter()
    for p in products:
        if p.get("category") == cat_id and p.get("brand"):
            marca = p["brand"].strip()
            if marca and sin_acentos(marca) not in {"elektra", "chedraui", "marti", "generico", "generica"}:
                cuenta[marca] += 1
    return [m for m, _ in cuenta.most_common(n)]


def productos_propios(products, cat_id, n=3):
    """[(consulta, id de catálogo MLM…)] de productos de Mercado Libre que
    ya tenemos en la categoría, para preguntarle a un dominio por ellos."""
    out = []
    for p in products:
        if p.get("category") != cat_id:
            continue
        for o in p.get("offers") or []:
            if o.get("storeId") != "mercadolibre":
                continue
            iid = add_products.ml_id(o.get("url"))
            if iid and re.match(r"MLM\d+$", iid) and "/p/" in (o.get("url") or ""):
                out.append((" ".join(p["name"].split()[:6]), iid))
                break
        if len(out) >= n:
            break
    return out


def dominio_confirmado(cat_id, cat_name, sub_name, conocidos, sondas, propios):
    """(dominio, nombre, conocidos, acuerdo) confirmado para la categoría,
    o None. `sondas` son las consultas con las que se pide la página de
    muestra: las marcas con más productos en la categoría y el nombre de la
    categoría -- lo que más devuelve. El nombre de la subcategoría no sirve
    de sonda ("De pared" trae 0 resultados en cualquier dominio)."""
    por_id, por_firma = conocidos
    nombres = _raices(cat_name) | _raices(sub_name)
    frase = f"{sub_name} {cat_name}"
    try:
        candidatos = domains_for(frase)[:3]
    except Exception as e:  # red, cuota, JSON cortado
        print(f"  !! domain_discovery falló para {frase!r}: {e}")
        return None
    for dom, nombre in candidatos:
        mejor = (0, 0.0)
        for q in sondas:
            try:
                items = add_products.catalog(dom, q, 0)
            except Exception as e:
                print(f"  !! /catalog falló para {dom}: {e}")
                break
            time.sleep(0.3)
            cats = []
            for it in items:
                c = por_id.get(it.get("id")) or por_firma.get(add_products.sig(it.get("title") or ""))
                if c:
                    cats.append(c)
            if len(cats) >= MIN_CONOCIDOS:
                acuerdo = sum(1 for c in cats if c == cat_id) / len(cats)
                if acuerdo >= MIN_ACUERDO:
                    return dom, nombre, len(cats), acuerdo
                mejor = max(mejor, (len(cats), acuerdo))
                break  # con muestra suficiente y sin acuerdo, el dominio no es de acá
            mejor = max(mejor, (len(cats), 0.0))
            # Segunda prueba, también contra datos y no contra el nombre del
            # dominio: si los títulos que devuelve nombran el producto de la
            # categoría ("audífonos", "barra de sonido"), el dominio es de
            # ahí aunque no tengamos todavía esos artículos. Se exige el
            # 80% de al menos diez títulos; los que no lo nombran (un
            # "Samsung Galaxy A16" no dice "celular") no confirman nada.
            if len(items) >= MIN_TITULOS and titulos_nombran(items, nombres):
                return dom, nombre, len(items), 1.0
        # Tercera prueba: se le pregunta al dominio por productos NUESTROS de
        # la categoría, por su nombre. Los dominios de Mercado Libre son
        # hojas (Audífonos, no Electrónica), así que si devuelve dos de tres
        # audífonos que ya tenemos, el dominio es de audífonos. Cuesta tres
        # consultas por candidato, por eso va al final.
        hallados = 0
        for q, iid in propios[:3]:
            try:
                items = add_products.catalog(dom, q, 0)
            except Exception:
                break
            time.sleep(0.3)
            if any(it.get("id") == iid for it in items):
                hallados += 1
        if hallados >= 2:
            return dom, nombre, hallados, 1.0
        n, acuerdo = mejor
        if n < MIN_CONOCIDOS:
            print(f"     {dom} ({nombre}): solo {n} conocidos, no alcanza para confirmar")
        else:
            print(f"     {dom} ({nombre}): {acuerdo:.0%} de los conocidos están en {cat_name}, no es de ahí")
    return None


def targets_para(data, subs, marcas_por_sub):
    conocidos = indice_conocidos(data["products"])
    targets = []
    for cat_id, cat_name, sub_id, sub_name, icono in subs:
        sondas = marcas_de_categoria(data["products"], cat_id, 2) + [cat_name]
        propios = productos_propios(data["products"], cat_id)
        elegido = dominio_confirmado(cat_id, cat_name, sub_name, conocidos, sondas, propios)
        time.sleep(0.3)
        if not elegido:
            print(f"  -- {cat_name} / {sub_name}: ningún dominio confirmado")
            continue
        dom, dom_nombre, n, acuerdo = elegido
        consultas = [sub_name] + marcas_top(data["products"], cat_id, sub_id, marcas_por_sub)
        print(f"  {cat_name} / {sub_name} -> {dom} ({dom_nombre}, {n} conocidos, {acuerdo:.0%}); consultas: {consultas}")
        for q in consultas:
            targets.append({
                "domain": dom, "q": q, "cat": cat_id, "sub": None,
                "max": MAX_POR_CONSULTA, "pages": 1, "icon": icono,
            })
    return targets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--dia", type=int, help="índice de rotación (por defecto, los días desde el 1 de septiembre de 2026)")
    ap.add_argument("--ventana", type=int, default=VENTANA)
    ap.add_argument("--marcas", type=int, default=MARCAS_POR_SUB)
    args = ap.parse_args()

    dia = args.dia if args.dia is not None else (datetime.date.today() - EPOCH).days
    data = load_catalog()
    subs = subcategorias_del_sitio(data)
    hoy = ventana_de(subs, dia, args.ventana)
    print(f"Día {dia}: {len(hoy)} de {len(subs)} subcategorías")
    targets = targets_para(data, hoy, args.marcas)
    print(f"\n{len(targets)} consultas de catálogo")
    if not targets:
        return
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(targets, f, ensure_ascii=False)
        ruta = f.name
    try:
        add_products.main([ruta] + (["--dry-run"] if args.dry_run else []))
    finally:
        os.unlink(ruta)


if __name__ == "__main__":
    main()
