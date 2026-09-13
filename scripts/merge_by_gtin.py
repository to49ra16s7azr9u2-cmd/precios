#!/usr/bin/env python3
"""Fusiona fichas de tiendas distintas que publican el MISMO código de barras.

EL PROBLEMA
-----------
match_by_gtin.py le pregunta a Mercado Libre por el código de barras de una
ficha y le pega la oferta que encuentra. Pero cuando las dos publicaciones ya
están en el catálogo como fichas separadas -- Chedraui por su lado, Elektra
por el suyo -- nadie las junta: no hay a quién preguntarle, la respuesta ya
está adentro. Al escribir este archivo había 1,185 códigos de barras
repartidos entre fichas de tiendas distintas, cada una con su página y su
precio, sin comparación. Por ejemplo:

    8806099061951  Chedraui "Celular Samsung Galaxy A37 5G 256GB 8GB RAM..."
                   Elektra  "Samsung Galaxy A37 5G 256gb 8gb Ram"

merge_cross_store.py no los ve porque pide que el nombre normalizado sea
IDÉNTICO, y cada tienda escribe el suyo.

POR QUÉ NO ALCANZA EL CÓDIGO SOLO
---------------------------------
Está documentado en audit_gtin_matches.py con casos reales que hubo que
deshacer: el `ean` que publica Elektra no siempre es un código de fabricante.
En las herramientas Hyundai todas comparten el prefijo 6426138, así que
varias caen en el mismo código sin ser el mismo producto:

    Bomba De Agua Agrícola Diesel 17 HP ($76,115)  <-  Llave Stilson 8" ($130)
    Hidrolavadora Industrial 20 HP ($105,400)  <-  Tijeras de aviación ($190)

Y en ean_dudosos.py está el otro modo de fallar: un multipack publicado con
el código de la pieza suelta. Unirlos deja el paquete anunciado al precio de
la pieza.

Por eso acá el código de barras ABRE la puerta pero no decide. Para fusionar
hacen falta, además, todas estas:

  1. Misma categoría.
  2. Una ficha por tienda. Dos del mismo vendedor son trabajo de
     merge_same_store.py, no de acá.
  3. El nombre se parece: similitud >= MIN_SIMILITUD (0.34, el umbral que
     audit_gtin_matches.py calibró a mano sobre este catálogo) o los dos
     nombres comparten un código de modelo. Este es el punto: el criterio
     del auditor se aplica ANTES de unir, no después de haber unido mal.
  4. Misma versión y misma capacidad (_misma_version de merge_by_url.py):
     128 GB y 256 GB no son el mismo producto aunque compartan página.
  5. Ninguna declara una cantidad de piezas que la otra no declare, para no
     repetir el caso del kit de 10 memorias con el código de una.
  6. El precio entre tiendas no se va a 5x o más. Elektra vende a crédito y
     marca mucho, así que huecos de 3x son normales y buenos; 5x con todo lo
     anterior cumplido es raro y prefiero no unir.
  7. Ninguna oferta está en la lista de ean_dudosos.py.

Las fichas que no pasan alguna de estas se quedan como están: el script
prefiere dejar dos fichas sueltas (que es lo que ya hay hoy) antes que
inventar una comparación falsa, que es lo que engaña al que entra.

USO
    python3 scripts/merge_by_gtin.py --dry-run
    python3 scripts/merge_by_gtin.py --dry-run --motivos  # por qué NO une
    python3 scripts/merge_by_gtin.py
"""
import argparse
import collections
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog  # noqa: E402
import audit_gtin_matches as ag  # noqa: E402
import merge_by_url as mu  # noqa: E402
from ean_dudosos import ean_utilizable  # noqa: E402
from match_by_gtin import normalize_gtin  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_RATIO = 5.0

# "Kit 10 piezas", "pack de 2", "3 unidades", "2 pzas": si una ficha lo dice y
# la otra no, no son la misma unidad de venta aunque compartan el código.
# El (?<![\d.]) y el (?![\d.]) son por una medida real del catálogo: en
# "Llantas R-26x2.125, Paquete de 5" el "125" del decimal queda pegado a la
# palabra "paquete" y se leía como un paquete de 125 piezas, así que la ficha
# no se fusionaba con su gemela que decía lo mismo. La cantidad se escribe
# "5 piezas" o "paquete de 5"; nunca al final de un decimal.
CANTIDAD_RE = re.compile(
    r"(?<![\d.])(\d{1,3})\s*(?:pz|pzs|pzas|piezas?|unidades?)\b|"
    r"(?:pack|paquete|kit|set)\s+(?:de\s+)?(\d{1,3})(?![\d.])"
)


def cantidad(nombre):
    n = set()
    for a, b in CANTIDAD_RE.findall(mu._normalizar(nombre)):
        v = a or b
        if v and int(v) > 1:
            n.add(int(v))
    return n


def gtins_de(product):
    """Todos los códigos utilizables de la ficha, de cualquier tienda."""
    out = set()
    for o in product.get("offers") or []:
        if not ean_utilizable(o):
            continue
        g = normalize_gtin(o.get("ean"))
        if g:
            out.add(g)
    return out


def tiendas_de(product):
    return {o.get("storeId") for o in product.get("offers") or []
            if o.get("storeId")}


def grupos_por_gtin(products):
    por = collections.defaultdict(list)
    for p in products:
        for g in gtins_de(p):
            por[g].append(p)
    return {g: ps for g, ps in por.items() if len(ps) > 1}


def se_puede_fusionar(fichas):
    """(True, None) o (False, motivo)."""
    if len({p.get("category") for p in fichas}) > 1:
        return False, "categorías distintas"

    tiendas = [tiendas_de(p) for p in fichas]
    if any(not t for t in tiendas):
        return False, "alguna ficha no dice de qué tienda es"
    vistas = set()
    for t in tiendas:
        if t & vistas:
            return False, "dos fichas de la misma tienda"
        vistas |= t

    confirmados = {p["gtin"] for p in fichas if p.get("gtin")}
    if len(confirmados) > 1:
        return False, "GTIN confirmados distintos"
    if any(p.get("colorVariants") for p in fichas):
        return False, "variantes de color"

    jefe = fichas[0]
    for otro in fichas[1:]:
        a, b = jefe.get("name") or "", otro.get("name") or ""
        s = ag.similitud(a, b)
        if s is None:
            return False, "sin palabras útiles para comparar el nombre"
        if s < ag.MIN_SIMILITUD and not ag._comparten_modelo(a, b):
            return False, "nombres que no se parecen"
        if not mu._misma_version(a, b):
            return False, "distinta versión o capacidad en el nombre"
        if cantidad(a) != cantidad(b):
            return False, "una declara cantidad de piezas y la otra no"

    if ratio_del_grupo(fichas) >= MAX_RATIO:
        return False, f"precios a {MAX_RATIO:.0f}x o más entre tiendas"
    return True, None


def ratio_del_grupo(fichas):
    por = {}
    for p in fichas:
        for o in p.get("offers") or []:
            t, pr = o.get("storeId"), o.get("price")
            if t and pr:
                por.setdefault(t, []).append(pr)
    if len(por) < 2:
        return 1.0
    m = [min(v) for v in por.values()]
    return max(m) / min(m) if min(m) else 1.0


def fusionar(fichas):
    """Deja todo en la ficha de id más bajo. Devuelve (jefe, absorbidas)."""
    jefe, resto = fichas[0], fichas[1:]
    urls = {o.get("url") for o in jefe.get("offers") or [] if o.get("url")}
    for otro in resto:
        for o in otro.get("offers") or []:
            u = o.get("url")
            if u and u in urls:
                continue
            jefe.setdefault("offers", []).append(o)
            if u:
                urls.add(u)
        for campo in ("subcategory", "gtin", "photo", "image", "brand",
                      "specs", "reviews"):
            if not jefe.get(campo) and otro.get(campo):
                jefe[campo] = otro[campo]
    return jefe, resto


def id_num(p):
    s = p["id"][1:]
    return int(s) if s.isdigit() else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--motivos", action="store_true",
                    help="lista los grupos que NO se fusionan y por qué")
    ap.add_argument("--keep-pages", action="store_true")
    args = ap.parse_args()

    data = load_catalog()
    grupos = grupos_por_gtin(data["products"])
    print(f"Códigos de barras compartidos por 2+ fichas: {len(grupos)}")

    hechos, motivos, absorbidas, ya = [], collections.Counter(), set(), set()
    for g in sorted(grupos):
        fichas = sorted(grupos[g], key=id_num)
        if any(p["id"] in ya for p in fichas):
            motivos["alguna ficha ya se fusionó en otro código"] += 1
            continue
        ok, motivo = se_puede_fusionar(fichas)
        if not ok:
            motivos[motivo] += 1
            if args.motivos:
                print(f"  [no] {g}  {motivo}")
                for p in fichas:
                    print(f"        {p['id']}  {(p.get('name') or '')[:66]}")
            continue
        jefe, resto = fusionar(fichas)
        ya.update(p["id"] for p in fichas)
        absorbidas.update(p["id"] for p in resto)
        hechos.append((g, jefe, resto))

    for g, jefe, resto in hechos:
        precios = sorted(
            (o.get("price"), o.get("storeId"))
            for o in jefe["offers"] if o.get("price")
        )
        detalle = " | ".join(f"{s} ${pr:,.0f}" for pr, s in precios)
        print(f"  {g}  {jefe['id']} <- {', '.join(p['id'] for p in resto)}")
        print(f"        {(jefe.get('name') or '')[:66]}")
        print(f"        {detalle}")

    print(f"\nGrupos fusionados: {len(hechos)}; "
          f"fichas absorbidas: {len(absorbidas)}")
    print("No se fusionaron:")
    for motivo, n in motivos.most_common():
        print(f"  {n:6d}  {motivo}")

    if not hechos:
        return
    data["products"] = [p for p in data["products"]
                        if p["id"] not in absorbidas]
    print(f"Catálogo: {len(data['products'])} productos")

    if args.dry_run:
        print("(--dry-run: no se escribió nada)")
        return

    save_catalog(data)
    if not args.keep_pages:
        n = 0
        for pid in absorbidas:
            ruta = os.path.join(ROOT, "producto", pid)
            if os.path.isdir(ruta):
                shutil.rmtree(ruta)
                n += 1
        print(f"Páginas estáticas borradas: {n}")
    print("Catálogo actualizado.")


if __name__ == "__main__":
    main()
