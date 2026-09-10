#!/usr/bin/env python3
"""Fusiona fichas que son la MISMA publicación repetida dentro de una tienda.

POR QUÉ HACE FALTA ADEMÁS DE LOS OTROS merge_*
-----------------------------------------------
Cada script de fusión cubre un caso y ninguno cubría este:

  merge_cross_store   exige que las fichas estén en tiendas DISTINTAS.
  merge_by_url        exige que compartan la url de la publicación.
  merge_by_signature  es solo de celulares, por firma estructurada.
  merge_by_color      es el mismo equipo en colores distintos.

Elektra publica el mismo producto bajo varios SKU: misma url salvo el número
del final, mismo nombre, misma marca, misma foto y el mismo precio. Como la
tienda es una sola y la url no coincide, ninguno de los cuatro los tocaba, y
el sitio mostraba dos, tres y hasta cinco filas idénticas -- que es lo peor
que puede hacer un comparador: parecen productos distintos y no lo son.

Medido sobre el catálogo: 152 grupos, 417 fichas. Casi todo son relojes
inteligentes de Elektra (Fralugio y parecidos).

CUÁNDO SE FUSIONA Y CUÁNDO NO
-----------------------------
Todo tiene que coincidir: nombre normalizado, marca, categoría,
subcategoría, y la FOTO. La foto es la que decide de verdad, porque es lo
único que separa un SKU repetido de una variante real: cuando Elektra
publica dos colores con el mismo nombre, cada uno trae su propia foto
("azul-buds.jpg" contra "negro-buds.jpg") o su propio EAN en el nombre del
archivo ("7503056054629.jpg" contra "...4636.jpg"). Se compara el nombre del
archivo y no la url entera porque el id numérico del asset cambia cuando la
tienda vuelve a subir la misma imagen.

Además, ninguna spec puede contradecir a otra: si dos fichas declaran
"Color" y no dicen lo mismo, son dos productos aunque el nombre no lo diga.
(Sobre los 152 grupos de hoy no hay ni uno así -- donde las dos declaran un
atributo, coinciden las dos.) Lo mismo con los GTIN confirmados, con el
mismo criterio que merge_by_url.

Las fichas con colorVariants quedan afuera enteras: ahí el color ya está
resuelto adentro de la ficha y fusionar dos sería otro problema distinto.

QUÉ FICHA SOBREVIVE
-------------------
La de id más bajo -- la más vieja, la que probablemente ya esté indexada --
igual que merge_cross_store y merge_by_signature. Se queda con todas las
ofertas del grupo (deduplicadas por url), así que si los SKU repetidos
tenían precios distintos, el comparador se queda con todos y muestra el más
barato, que es justo lo que no podía hacer con las fichas separadas.

USO
---
    python3 scripts/merge_same_store.py --dry-run
    python3 scripts/merge_same_store.py
"""
import argparse
import collections
import os
import shutil
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import id_num, load_catalog, save_catalog, texto_plano  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def tiendas_de(product):
    return {o.get("storeId") for o in (product.get("offers") or [])}


def archivo_de_foto(product):
    """El nombre del archivo de la foto, sin el id del asset ni el ?v=.

    Elektra sube la misma imagen más de una vez y cada copia recibe un id
    distinto en la ruta (.../ids/28163402/azul-buds.jpg), así que comparar
    la url entera diría que son fotos distintas cuando es la misma.
    """
    return (product.get("photo") or "").split("?")[0].rsplit("/", 1)[-1].lower()


def specs_de(product, label):
    """Los valores normalizados de esa spec, o None si la ficha no la declara."""
    valores = [texto_plano(s.get("value"))
               for s in (product.get("specs") or []) if s.get("label") == label]
    return tuple(sorted(valores)) if valores else None


def se_contradicen(fichas):
    """¿Hay algún atributo que dos fichas declaren distinto?"""
    labels = {s.get("label") for p in fichas for s in (p.get("specs") or [])}
    for label in labels:
        # Que una ficha no declare el atributo no contradice nada: falta el
        # dato, no dice otra cosa. Solo cuentan las que sí lo declaran.
        declarados = {v for v in (specs_de(p, label) for p in fichas) if v is not None}
        if len(declarados) > 1:
            return label
    gtins = {p["gtin"] for p in fichas if p.get("gtin")}
    if len(gtins) > 1:
        return "GTIN confirmados distintos"
    return None


def grupos_fusionables(products):
    # Cuántos productos del catálogo usan cada archivo de foto: una foto que
    # solo tienen las fichas del grupo prueba algo, una que tienen 126
    # productos distintos ("1.jpeg.jpg", el nombre que Elektra le pone a la
    # primera imagen de cualquier cosa) no prueba nada.
    uso_de_foto = collections.Counter(
        archivo_de_foto(p) for p in products if archivo_de_foto(p))

    por_clave = defaultdict(list)
    for p in products:
        if p.get("colorVariants"):
            continue
        clave = (texto_plano(p.get("name")), texto_plano(p.get("brand") or ""),
                 p.get("category"), p.get("subcategory"))
        por_clave[clave].append(p)

    fusionables, frenados = [], []
    for fichas in por_clave.values():
        if len(fichas) < 2:
            continue
        # Lo que define este caso es que la tienda repitió su publicación, y
        # eso se ve en que TODAS las fichas del grupo la tienen a ella. Que
        # una además traiga una oferta de Mercado Libre no lo cambia: es una
        # ficha que ya se consolidó entre tiendas y a la que le quedaron al
        # lado los SKU sueltos de Elektra (pasa con un Galaxy A56, un
        # cargador de Apple Watch y un power bank solar). Dos fichas SIN
        # ninguna tienda en común, en cambio, son un caso de
        # merge_cross_store, que tiene sus propias reglas.
        comunes = set.intersection(*[tiendas_de(p) for p in fichas])
        if not comunes:
            frenados.append((fichas, "no comparten tienda -- es de merge_cross_store"))
            continue

        # El nombre igual NO alcanza: Elektra publica varios colores del
        # mismo equipo con un nombre solo. Lo que los separa es la foto, y
        # tiene que ser la misma foto Y que no la use nadie más:
        #
        #   - Cinco fichas "INFINIX HOT 60 PRO PLUS" comparten hasta la url
        #     de la publicación y traen cinco fotos distintas, cada una
        #     nombrada con su EAN (4894947092626, ...2688, ...2701, ...2596,
        #     ...2657). Son cinco colores. Por eso la url compartida NO sirve
        #     como prueba: Elektra reusa una url para toda la familia.
        #   - "1.jpeg.jpg" es el nombre que Elektra le pone a la primera
        #     imagen de cualquier cosa; lo tienen 126 productos del catálogo,
        #     así que dos fichas que coincidan en ESE nombre no coinciden en
        #     nada. Por eso además se exige que la foto sea de este grupo y
        #     de nadie más.
        fotos = {archivo_de_foto(p) for p in fichas}
        if not (len(fotos) == 1 and all(fotos)
                and uso_de_foto[next(iter(fotos))] == len(fichas)):
            frenados.append((fichas, "la foto no dice que sean la misma ficha "
                                     "(pueden ser colores distintos)"))
            continue

        motivo = se_contradicen(fichas)
        if motivo:
            frenados.append((fichas, f"specs que no coinciden: {motivo}"))
            continue
        fusionables.append(sorted(fichas, key=id_num))
    return fusionables, frenados


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--muestra", type=int, default=10)
    args = ap.parse_args()

    data = load_catalog()
    grupos, frenados = grupos_fusionables(data["products"])

    sobran = sum(len(g) - 1 for g in grupos)
    print(f"Grupos de la misma publicación repetida en una tienda: {len(grupos)}")
    print(f"Fichas involucradas: {sum(len(g) for g in grupos)}; se eliminarían {sobran}")
    por_categoria = defaultdict(int)
    for g in grupos:
        por_categoria[g[0]["category"]] += len(g) - 1
    for cat, n in sorted(por_categoria.items(), key=lambda x: -x[1]):
        print(f"   {n:5}  {cat}")
    for g in grupos[:args.muestra]:
        precios = sorted({o.get("price") for p in g for o in (p.get("offers") or [])
                          if o.get("price") is not None})
        print(f"\n  {[p['id'] for p in g]}  precios: {precios}")
        print(f"    {g[0]['name'][:76]}")
    if frenados:
        print(f"\nGrupos que NO se fusionan: {len(frenados)}")
        for fichas, motivo in frenados[:args.muestra]:
            print(f"   {[p['id'] for p in fichas]}  {motivo}")
            print(f"      {fichas[0]['name'][:70]}")

    if not grupos:
        return
    if args.dry_run:
        print("\n(--dry-run: no se escribió nada)")
        return

    a_borrar = set()
    for fichas in grupos:
        principal = fichas[0]
        vistas = {o.get("url") for o in principal.setdefault("offers", [])}
        for p in fichas[1:]:
            for o in p.get("offers") or []:
                if o.get("url") in vistas:
                    continue
                principal["offers"].append(o)
                vistas.add(o.get("url"))
            if not principal.get("specs") and p.get("specs"):
                principal["specs"] = p["specs"]
            if not principal.get("gtin") and p.get("gtin"):
                principal["gtin"] = p["gtin"]
            a_borrar.add(p["id"])

    data["products"] = [p for p in data["products"] if p["id"] not in a_borrar]
    save_catalog(data)
    print(f"\nFichas fusionadas y eliminadas: {len(a_borrar)}")
    print(f"Catálogo: {len(data['products'])} productos")

    # La página estática de la ficha que desaparece queda huérfana:
    # generate_seo_pages.py solo escribe las de los productos actuales.
    borradas = 0
    for pid in a_borrar:
        d = os.path.join(ROOT, "producto", pid)
        if os.path.isdir(d):
            shutil.rmtree(d)
            borradas += 1
    print(f"Páginas estáticas huérfanas eliminadas: {borradas}")


if __name__ == "__main__":
    main()
