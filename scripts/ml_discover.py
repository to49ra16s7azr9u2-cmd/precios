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
PAGINAS_POR_CONSULTA = 1

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


NO_MARCA = {"elektra", "chedraui", "marti", "generico", "generica"}


def _top_marcas(cuenta, n):
    """Las n marcas más frecuentes, SIN repetir la misma escrita distinto.

    Las tiendas escriben la marca como quieren y el catálogo la guarda tal
    cual: en Lavadoras/Automáticas convivían MABE y Mabe, WHIRLPOOL y
    Whirlpool, MIDEA y Midea, KOBLENZ y Koblenz, GE y "GE APPLIANCES" y
    "GE Appliances". Cada par gastaba dos consultas para traer lo mismo:
    de las 26 marcas de esa subcategoría, 7 eran repetidas. Se pliegan por
    minúsculas y sin acentos, y se conserva la grafía más usada.
    """
    plegado = collections.Counter()
    grafias = collections.defaultdict(collections.Counter)
    for marca, c in cuenta.items():
        k = sin_acentos(marca).lower()
        plegado[k] += c
        grafias[k][marca] += c
    return [grafias[k].most_common(1)[0][0] for k, _ in plegado.most_common(n)]


def marcas_top(products, cat_id, sub_id, n):
    cuenta = collections.Counter()
    for p in products:
        if p.get("category") == cat_id and p.get("subcategory") == sub_id and p.get("brand"):
            marca = p["brand"].strip()
            # La marca "de la tienda" (Elektra, Chedraui) no es una marca.
            if marca and sin_acentos(marca) not in NO_MARCA:
                cuenta[marca] += 1
    return _top_marcas(cuenta, n)


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
            if marca and sin_acentos(marca) not in NO_MARCA:
                cuenta[marca] += 1
    return _top_marcas(cuenta, n)


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


# Dominios ya confirmados en corridas anteriores: {"cat||sub": [dominio,
# nombre, conocidos, acuerdo]}. Medido el 17-sep-2026: de 344 subcategorías
# solo 116 confirmaban dominio propio; 161 más pertenecen a una categoría
# que SÍ tiene dominios confirmados por otras subcategorías (Cargadores y
# adaptadores / De pared no confirma nada, pero la categoría ya confirmó
# MLM-CELLPHONE_CHARGERS al 100%), y 67 no tienen nada. Reutilizar el
# dominio de la categoría respeta la regla de este archivo --el dominio se
# confirmó contra NUESTRO catálogo, con el 80% de acuerdo-- y sin ello
# el 43% de las subcategorías no aportaba ni un producto.
def cargar_dominios(ruta):
    if not ruta or not os.path.exists(ruta):
        return {}
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def guardar_dominios(ruta, dominios):
    if not ruta:
        return
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(dominios, f, ensure_ascii=False, indent=1)


def targets_para(data, subs, marcas_por_sub, max_por_consulta=None, paginas=None,
                 marcas_desde=0, dominios=None, reusar_dominio=False, recorrer=False):
    conocidos = indice_conocidos(data["products"])
    dominios = dominios if dominios is not None else {}
    por_categoria = collections.defaultdict(dict)   # cat_name -> {dominio: nombre}
    for k, v in dominios.items():
        c = k.split("||")[0]
        por_categoria[c][v[0]] = v[1]
    targets = []
    for cat_id, cat_name, sub_id, sub_name, icono in subs:
        clave = f"{cat_name}||{sub_name}"
        if clave in dominios:
            dom, dom_nombre, n, acuerdo = dominios[clave][0], dominios[clave][1], dominios[clave][2], dominios[clave][3] / 100.0
            elegido = (dom, dom_nombre, n, acuerdo)
            elegidos = [elegido]
        else:
            sondas = marcas_de_categoria(data["products"], cat_id, 2) + [cat_name]
            propios = productos_propios(data["products"], cat_id)
            elegido = dominio_confirmado(cat_id, cat_name, sub_name, conocidos, sondas, propios)
            time.sleep(0.3)
            if elegido:
                dominios[clave] = [elegido[0], elegido[1], elegido[2], int(round(elegido[3] * 100))]
                por_categoria[cat_name][elegido[0]] = elegido[1]
                elegidos = [elegido]
            elif reusar_dominio and por_categoria.get(cat_name):
                # Todos los dominios que la categoría ya confirmó: en una
                # categoría con tres dominios (Muebles: camas, libreros,
                # escritorios) la subcategoría sin dominio propio puede estar
                # en cualquiera, y la consulta por su nombre en un dominio
                # ajeno simplemente devuelve vacío.
                elegidos = [(d, nom, 0, 0.0) for d, nom in por_categoria[cat_name].items()]
                print(f"  ~~ {cat_name} / {sub_name}: sin dominio propio; reusa {len(elegidos)} de la categoría")
            else:
                print(f"  -- {cat_name} / {sub_name}: ningún dominio confirmado")
                continue
        for dom, dom_nombre, n, acuerdo in elegidos:
            _agregar_consultas(data, targets, cat_id, cat_name, sub_id, sub_name, icono,
                               dom, dom_nombre, n, acuerdo, marcas_por_sub, marcas_desde,
                               max_por_consulta, paginas, recorrer)
    return targets


def _agregar_consultas(data, targets, cat_id, cat_name, sub_id, sub_name, icono,
                       dom, dom_nombre, n, acuerdo, marcas_por_sub, marcas_desde,
                       max_por_consulta, paginas, recorrer):
    if True:
        # marcas_desde salta las marcas que una corrida anterior ya consultó.
        # En una segunda pasada para agotar la cola larga, sin esto se
        # vuelven a pedir las 60 de arriba --miles de consultas que solo
        # devuelven duplicados-- para llegar a las de abajo.
        marcas = marcas_top(data["products"], cat_id, sub_id, marcas_por_sub)[marcas_desde:]
        consultas = ([sub_name] if not marcas_desde else []) + marcas
        # --recorrer: agotar el dominio. products/search exige una palabra
        # clave, así que "recorrer" es paginar cada consulta genérica hasta
        # que dos páginas seguidas no traigan nada nuevo (ver
        # add_products.py, "parar_tras_vacias"). Las genéricas son el
        # nombre de la categoría y "producto", que es lo que el propio
        # Worker usa cuando no le dan q.
        if recorrer:
            for extra in (cat_name, "producto"):
                if extra not in consultas:
                    consultas.append(extra)
        if not consultas:
            return
        print(f"  {cat_name} / {sub_name} -> {dom} ({dom_nombre}, {n} conocidos, {acuerdo:.0%}); consultas: {consultas}")
        for q in consultas:
            t = {
                "domain": dom, "q": q, "cat": cat_id, "sub": None,
                "max": max_por_consulta or MAX_POR_CONSULTA,
                "pages": paginas or PAGINAS_POR_CONSULTA,
                "icon": icono,
            }
            if recorrer:
                t["parar_tras_vacias"] = 2
            targets.append(t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--dia", type=int, help="índice de rotación (por defecto, los días desde el 1 de septiembre de 2026)")
    ap.add_argument("--ventana", type=int, default=VENTANA)
    ap.add_argument("--marcas", type=int, default=MARCAS_POR_SUB)
    ap.add_argument("--marcas-desde", type=int, default=0,
                    help="saltar las primeras N marcas de cada subcategoría "
                         "(para una segunda pasada que agote la cola larga "
                         "sin repetir lo ya consultado)")
    # Las dos perillas del tamaño de la corrida. El valor por defecto es el
    # de la corrida DIARIA, que tiene que ser barata; para una carga grande
    # ("--ventana 400 --marcas 6 --max 50 --pages 3") se suben a mano y se
    # recorren todas las subcategorías de una vez en lugar de en ocho días.
    ap.add_argument("--max", type=int, default=MAX_POR_CONSULTA,
                    help="productos por consulta (por defecto %(default)s)")
    ap.add_argument("--pages", type=int, default=PAGINAS_POR_CONSULTA,
                    help="páginas de resultados por consulta (por defecto %(default)s)")
    ap.add_argument("--dominios-json",
                    help="archivo con los dominios ya confirmados; se lee al empezar y "
                         "se reescribe al terminar con los nuevos (ahorra las consultas de "
                         "confirmación y deja reusar dominios de la categoría)")
    ap.add_argument("--reusar-dominio", action="store_true",
                    help="si una subcategoría no confirma dominio, consultar en los que "
                         "ya confirmó su categoría")
    ap.add_argument("--recorrer", action="store_true",
                    help="agotar cada dominio: sumar consultas genéricas y paginar hasta "
                         "que dos páginas seguidas no traigan nada nuevo (usar con --pages alto)")
    args = ap.parse_args()

    dia = args.dia if args.dia is not None else (datetime.date.today() - EPOCH).days
    data = load_catalog()
    subs = subcategorias_del_sitio(data)
    hoy = ventana_de(subs, dia, args.ventana)
    print(f"Día {dia}: {len(hoy)} de {len(subs)} subcategorías")
    dominios = cargar_dominios(args.dominios_json)
    targets = targets_para(data, hoy, args.marcas, args.max, args.pages,
                           args.marcas_desde, dominios, args.reusar_dominio, args.recorrer)
    guardar_dominios(args.dominios_json, dominios)
    print(f"\n{len(targets)} consultas de catálogo"
          f" (hasta {args.max} productos x {args.pages} pagina(s) cada una)")
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
