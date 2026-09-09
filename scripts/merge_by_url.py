#!/usr/bin/env python3
"""Junta los productos que son la MISMA publicación repetida en el catálogo.

Dos fichas distintas apuntando a la misma url de Mercado Libre son el mismo
artículo entrado dos veces (importaciones distintas, en fechas distintas). El
sitio los mostraba como dos productos: cada uno con una parte de las ofertas,
así que NINGUNO de los dos enseñaba la comparación completa -- justo lo único
que este sitio existe para hacer. Eran 1,251 grupos, 2,812 fichas.

Compartir la url es la señal más fuerte que hay (no se parece: ES el mismo
anuncio), pero no alcanza sola: en Mercado Libre varios colores de un mismo
modelo cuelgan de la misma página de catálogo, y ahí sí son SKU distintos
(el iPhone Air Space Black y el Light Gold comparten url y tienen GTIN
distintos). Así que se pide, además de la url compartida:

  - la misma categoría,
  - ningún par de GTIN confirmados distintos (ver confirm_gtins.py),
  - ninguna ficha con variantes de color ya fusionadas (merge_by_color.py
    guarda ahí una estructura propia que este script no sabe unir), y
  - una segunda señal en el nombre: o se parecen (MIN_SIMILITUD, el mismo
    umbral calibrado a mano en audit_gtin_matches.py) o comparten código de
    modelo.

Lo que no cumple TODO eso se deja como está y se cuenta en el resumen: es
preferible una ficha repetida a dos artículos distintos fusionados en uno,
que es una fusión que después nadie puede deshacer.

Sobrevive la ficha con el id más bajo: es la más vieja, la que ya tiene
página estática publicada, historial de precios y --si alguien enlazó algo--
los enlaces. Las demás le entregan sus ofertas (sin repetir url) y los
campos que a ella le falten.

USO
    python3 scripts/merge_by_url.py --dry-run
    python3 scripts/merge_by_url.py
"""
import argparse
import collections
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audit_gtin_matches as ag
import web_summary
from data_io import load_catalog, save_catalog


# Campos que la ficha que sobrevive adopta de las otras SOLO si no los tiene.
# El nombre y la marca no están: son los de la ficha vieja y se respetan, que
# es lo que ya vio quien la tenga guardada o enlazada.
CAMPOS_QUE_SE_HEREDAN = ("subcategory", "gtin", "photo", "image", "mlQuery")


# Palabras que en esta clase de catálogo NO son adorno: separan un modelo de
# otro dentro de la misma familia. Si una aparece en un nombre y no en el
# otro, son dos artículos distintos por más que compartan la página de
# catálogo -- la JBL PartyBox On-the-Go 2 y la "2 Plus" cuelgan de la misma
# url y no son el mismo aparato, igual que Tales of Arise para Xbox One y
# para Series X.
MARCADORES = {
    "plus", "pro", "max", "mini", "lite", "ultra", "premium", "deluxe",
    "standard", "one", "series", "slim", "nano", "air", "gaming",
    "inalambrico", "inalambrica", "bluetooth",
}

# Medidas que tampoco son adorno: 128 GB y 256 GB no son el mismo producto.
# Se comparan solo las unidades que DECLARAN los dos nombres.
UNIDADES = (
    (re.compile(r"(\d+(?:\.\d+)?)\s*tb\b"), "tb"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*gb\b"), "gb"),
    (re.compile(r"(\d+)\s*mah\b"), "mah"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*ton\b"), "ton"),
    (re.compile(r"(\d+)\s*btu\b"), "btu"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(?:pulgada|pulgadas|pulg)\b"), "pulgadas"),
    (re.compile(r"(\d+)\s*hz\b"), "hz"),
    (re.compile(r"(\d+)\s*w\b"), "w"),
)


def _marcadores(nombre):
    return {w for w in ag._limpiar(nombre).split() if w in MARCADORES}


def _normalizar(nombre):
    """Minúsculas sin acentos, PERO conservando el punto decimal.

    ag._limpiar() reemplaza todo lo que no sea letra o dígito por espacio, así
    que "1.5 ton" se volvía "1 5 ton" y la medida se leía como 5 -- con lo
    cual 1.5 y 2.5 toneladas quedaban iguales. Para comparar medidas hay que
    quedarse con el punto.
    """
    t = unicodedata.normalize("NFKD", (nombre or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"(?<=\d),(?=\d\d\d)", "", t)   # 18,000 -> 18000
    return re.sub(r"[^a-z0-9.]+", " ", t)


def _medidas(nombre):
    limpio = _normalizar(nombre)
    return {
        unidad: {float(x) for x in rx.findall(limpio)}
        for rx, unidad in UNIDADES
        if rx.search(limpio)
    }


def _misma_version(a, b):
    """False si los nombres declaran distinta versión, tamaño o capacidad."""
    if _marcadores(a) != _marcadores(b):
        return False
    ma, mb = _medidas(a), _medidas(b)
    for unidad, valores in ma.items():
        if unidad in mb and valores != mb[unidad]:
            return False
    return True


def similitud(a, b):
    ta, tb = ag._tokens(a), ag._tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def grupos_por_url(products):
    """Componentes conexas de productos unidos por compartir una url.

    Conexas y no pares sueltos: si A y B comparten una url y B y C otra, los
    tres son la misma publicación y hay que mirarlos juntos.
    """
    por_url = collections.defaultdict(list)
    for p in products:
        for o in web_summary.purchase_options(p):
            if o.get("url"):
                por_url[o["url"]].append(p["id"])

    padre = {}

    def raiz(x):
        padre.setdefault(x, x)
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    def unir(a, b):
        ra, rb = raiz(a), raiz(b)
        if ra != rb:
            padre[ra] = rb

    for ids in por_url.values():
        unicos = sorted(set(ids))
        for otro in unicos[1:]:
            unir(unicos[0], otro)

    juntos = collections.defaultdict(list)
    for x in padre:
        juntos[raiz(x)].append(x)
    return [
        sorted(g, key=lambda i: (int(i[1:]) if i[1:].isdigit() else 0, i))
        for g in juntos.values() if len(g) > 1
    ]


def se_puede_fusionar(fichas):
    """(True, None) o (False, motivo)."""
    if len({p["category"] for p in fichas}) > 1:
        return False, "categorías distintas"
    gtins = {p["gtin"] for p in fichas if p.get("gtin")}
    if len(gtins) > 1:
        return False, "GTIN confirmados distintos"
    if any(p.get("colorVariants") for p in fichas):
        return False, "variantes de color"
    jefe = fichas[0]
    for otro in fichas[1:]:
        if (similitud(jefe["name"], otro["name"]) < ag.MIN_SIMILITUD
                and not ag._comparten_modelo(jefe["name"], otro["name"])):
            return False, "nombres que no se parecen"
        if not _misma_version(jefe["name"], otro["name"]):
            return False, "distinta versión o capacidad en el nombre"
    return True, None


def fusionar(fichas):
    """Deja todo en la primera ficha y devuelve cuántas ofertas se sumaron."""
    jefe = fichas[0]
    urls = {o.get("url") for o in jefe.get("offers") or [] if o.get("url")}
    sumadas = 0
    for otro in fichas[1:]:
        for o in otro.get("offers") or []:
            url = o.get("url")
            if url and url in urls:
                # Misma publicación: lo único que puede traer de nuevo es el
                # código de barras que la otra importación sí anotó.
                if o.get("ean"):
                    for propio in jefe["offers"]:
                        if propio.get("url") == url and not propio.get("ean"):
                            propio["ean"] = o["ean"]
                continue
            jefe.setdefault("offers", []).append(o)
            if url:
                urls.add(url)
            sumadas += 1
        for campo in CAMPOS_QUE_SE_HEREDAN:
            if not jefe.get(campo) and otro.get(campo):
                jefe[campo] = otro[campo]
        if not jefe.get("specs") and otro.get("specs"):
            jefe["specs"] = otro["specs"]
        if not jefe.get("reviews") and otro.get("reviews"):
            jefe["reviews"] = otro["reviews"]
    return sumadas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--muestra", type=int, default=0,
                    help="imprime N grupos fusionables para revisarlos a mano")
    args = ap.parse_args()

    data = load_catalog()
    por_id = {p["id"]: p for p in data["products"]}
    grupos = grupos_por_url(data["products"])

    descartes = collections.Counter()
    fusionables = []
    for grupo in grupos:
        fichas = [por_id[i] for i in grupo]
        ok, motivo = se_puede_fusionar(fichas)
        if ok:
            fusionables.append(fichas)
        else:
            descartes[motivo] += 1

    print(f"Grupos de fichas que comparten publicación: {len(grupos):,}")
    print(f"  fusionables: {len(fusionables):,} "
          f"({sum(len(f) - 1 for f in fusionables):,} fichas se van)")
    for motivo, n in descartes.most_common():
        print(f"  se dejan como están por {motivo}: {n:,}")

    if args.muestra:
        print()
        for fichas in fusionables[:args.muestra]:
            print(f"  {fichas[0]['category']}")
            for i, p in enumerate(fichas):
                marca = "queda  " if i == 0 else "se une "
                print(f"    {marca} {p['id']:>9}  {len(p.get('offers') or []):>2} of  "
                      f"{p['name'][:70]}")

    ofertas = 0
    fuera = set()
    for fichas in fusionables:
        ofertas += fusionar(fichas)
        fuera.update(p["id"] for p in fichas[1:])

    print(f"\nOfertas que se suman a la ficha que queda: {ofertas:,}")

    if args.dry_run:
        print("(--dry-run: no se escribió nada)")
        return

    data["products"] = [p for p in data["products"] if p["id"] not in fuera]
    save_catalog(data)
    print(f"Catálogo guardado: {len(data['products']):,} productos "
          f"({len(fuera):,} menos)")


if __name__ == "__main__":
    main()
