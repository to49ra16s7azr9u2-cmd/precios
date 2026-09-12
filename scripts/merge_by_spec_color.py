#!/usr/bin/env python3
"""Junta en una ficha los colores de un producto cuando el color NO está en
el nombre sino en la spec "Color" que declara la tienda.

EL CASO QUE NINGÚN OTRO merge_* CUBRÍA
--------------------------------------
Elektra publica cada color de un reloj Fralugio como un producto aparte con
EXACTAMENTE el mismo nombre:

    Smart Watch Reloj Watch 8 Ultra Fralugio Llamada Amoled Hd   (Negro)
    Smart Watch Reloj Watch 8 Ultra Fralugio Llamada Amoled Hd   (Amarillo)
    Smart Watch Reloj Watch 8 Ultra Fralugio Llamada Amoled Hd   (Naranja)
    Smart Watch Reloj Watch 8 Ultra Fralugio Llamada Amoled Hd   (Gris)

El color va en la spec "Color" de la ficha y en ningún otro lado. Por eso:

  merge_by_color      no los ve: solo agrupa por el color que dice el NOMBRE.
  merge_same_store    los frena a propósito: la foto es distinta en cada
                      uno, y una foto distinta puede ser un color distinto.
  merge_by_url        no aplica: cada color tiene su propia url.

Y el sitio mostraba las cuatro filas seguidas, iguales a la vista, sin decir
en qué se diferencian. Medido sobre el catálogo: 170 grupos así, más otros
111 de fichas que YA venían fusionadas por color (colorVariants) pero cuyo
nombre, una vez sin color, quedó idéntico al de otra ficha fusionada del
mismo equipo -- merge_by_color tampoco vuelve a juntar esas, porque su firma
exige un color en el nombre y el nombre ya no lo tiene.

CUÁNDO SE FUSIONA
-----------------
Todo lo que no es el color tiene que coincidir: nombre normalizado, marca,
categoría, subcategoría y condición (nuevo/reacondicionado). Además:

  * Las fichas comparten al menos una tienda. Dos fichas del mismo nombre
    en tiendas distintas son un caso de merge_cross_store, con sus reglas.
  * CADA ficha del grupo dice de qué color es: por sus colorVariants (ya
    fusionada antes) o por su spec "Color". Si a una le falta, el grupo no
    se toca: no se le inventa un color a nadie. Los 128 grupos donde
    ninguna ficha declara color se quedan como están (la API de la tienda
    tampoco lo dice: se comprobó con un Galaxy A17 de Elektra).
  * Ninguna otra spec se contradice ("Material", "Capacidad"...). "Color"
    queda fuera de esa comparación porque es justo lo que se espera que
    difiera, y el GTIN también: cada color tiene su propio código de barras.
  * En Iluminación, Joyería y Salud y belleza no se fusiona nada, por lo
    mismo que en merge_by_color: ahí el color es el producto.

Si el color resulta ser EL MISMO en todas las fichas (10 grupos), no son
colores: es la misma publicación repetida, y se hace lo que hace
merge_same_store: una ficha con las ofertas de todas.

CÓMO QUEDA LA FICHA
-------------------
Igual que en merge_by_color: sobrevive la de id más bajo, cada color es una
entrada de colorVariants con sus propias ofertas, product.offers se queda
con las de la variante más barata. Cada oferta se lleva la foto de la ficha
de la que venía, para que la imagen de ese color no se pierda.

USO
---
    python3 scripts/merge_by_spec_color.py --dry-run [--muestra N]
    python3 scripts/merge_by_spec_color.py
"""
import argparse
import os
import re
import shutil
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import id_num, load_catalog, save_catalog, texto_plano  # noqa: E402
from merge_by_color import (  # noqa: E402
    CATEGORIES_SIN_COLOR, collapse_labels, strip_color_from_name,
    variant_min_price, variants_of,
)
from merge_same_store import specs_de, tiendas_de  # noqa: E402
from phone_signature import condition_of  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def color_de_spec(product):
    """El color que declara la tienda en la spec "Color", o None."""
    valores = [s.get("value") for s in (product.get("specs") or [])
               if s.get("label") == "Color" and (s.get("value") or "").strip()]
    if not valores:
        return None
    v = valores[0].strip()
    return v[:1].upper() + v[1:]


def tiene_variantes(product):
    vs = product.get("colorVariants") or []
    return bool(vs) and any(v.get("color") for v in vs)


def todas_las_tiendas(product):
    tiendas = set(tiendas_de(product))
    for v in product.get("colorVariants") or []:
        tiendas |= {o.get("storeId") for o in (v.get("offers") or [])}
    return tiendas


def modelo_sin_color(product):
    """La spec "Modelo" sin el color de la ficha, o None si no la declara.

    Elektra mete el color adentro del modelo de los relojes Fralugio:
    "WATCH 8 ULTRA SMART" para el negro y "WATCH 8 ULTRA AMARILLO SMART"
    para el amarillo (a veces pegado: "VA9ULTRANEGRO" / "VA9ULTRANARANJA").
    Comparado tal cual, eso frenaba 69 grupos que son exactamente el caso
    que este script existe para juntar. Se quita solo el color que la
    MISMA ficha declara en su spec "Color": no se adivina qué palabra es un
    color, se le cree a la tienda.
    """
    modelo = specs_de(product, "Modelo")
    if modelo is None:
        return None
    color = texto_plano(color_de_spec(product) or "")
    palabras = [w for w in color.split() if len(w) >= 3]
    out = []
    for valor in modelo:
        for w in palabras:
            if " " in valor:
                valor = re.sub(rf"(?<![a-z0-9]){re.escape(w)}(?![a-z0-9])", " ", valor)
            else:
                # Código pegado ("va9ultranegro"): el color va al final o al
                # principio, sin separador. Solo ahí se quita como subcadena.
                valor = re.sub(rf"^{re.escape(w)}|{re.escape(w)}$", "", valor)
        out.append(re.sub(r"\s+", " ", valor).strip())
    return tuple(sorted(out))


def se_contradicen_salvo_color(fichas):
    labels = {s.get("label") for p in fichas for s in (p.get("specs") or [])}
    for label in labels - {"Color"}:
        lector = modelo_sin_color if label == "Modelo" else (lambda p: specs_de(p, label))
        declarados = {v for v in (lector(p) for p in fichas) if v is not None}
        if len(declarados) > 1:
            return label
    return None


def grupos_fusionables(products):
    por_clave = defaultdict(list)
    for p in products:
        if p.get("category") in CATEGORIES_SIN_COLOR:
            continue
        clave = (texto_plano(p.get("name")), texto_plano(p.get("brand") or ""),
                 p.get("category"), p.get("subcategory"), condition_of(p.get("name") or ""))
        por_clave[clave].append(p)

    fusionables, frenados = [], []
    for fichas in por_clave.values():
        if len(fichas) < 2:
            continue
        if not set.intersection(*[todas_las_tiendas(p) for p in fichas]):
            frenados.append((fichas, "no comparten tienda -- es de merge_cross_store"))
            continue
        sin_color = [p["id"] for p in fichas
                     if not tiene_variantes(p) and not color_de_spec(p)]
        if sin_color:
            frenados.append((fichas, f"sin color declarado: {', '.join(sin_color)}"))
            continue
        motivo = se_contradicen_salvo_color(fichas)
        if motivo:
            frenados.append((fichas, f"specs que no coinciden: {motivo}"))
            continue
        fusionables.append(sorted(fichas, key=id_num))
    return fusionables, frenados


def variantes_de(product):
    """Las variantes de la ficha.

    Cuando la ficha es de UN color (el de su spec), su foto es la foto de
    ese color y se guarda en cada oferta para que no se pierda al fusionar.
    Una ficha que ya traía varios colores no dice de cuál es su foto, así
    que a sus variantes no se les pone nada.
    """
    if tiene_variantes(product):
        return [{"color": v.get("color"), "offers": list(v.get("offers") or [])}
                for v in variants_of(product)]
    etiqueta = color_de_spec(product)
    out = []
    for v in variants_of(product, etiqueta):
        ofertas = []
        for o in v.get("offers") or []:
            o = dict(o)
            if not o.get("photo") and product.get("photo"):
                o["photo"] = product["photo"]
            ofertas.append(o)
        out.append({"color": v.get("color"), "offers": ofertas})
    return out


def fusionar(fichas):
    """Deja en la primera ficha las variantes de todas. Devuelve la lista de
    colores resultante (uno solo = era la misma publicación repetida)."""
    principal = fichas[0]
    crudas = [v for p in fichas for v in variantes_de(p) if v.get("color") and v.get("offers")]
    canon = collapse_labels({v["color"] for v in crudas})
    variantes = []
    for v in crudas:
        etiqueta = canon.get(v["color"], v["color"])
        previa = next((x for x in variantes if x["color"].lower() == etiqueta.lower()), None)
        if previa:
            urls = {o.get("url") for o in previa["offers"]}
            previa["offers"].extend(o for o in v["offers"] if o.get("url") not in urls)
        else:
            variantes.append({"color": etiqueta, "offers": list(v["offers"])})
    for p in fichas[1:]:
        if not principal.get("photo") and p.get("photo"):
            principal["photo"] = p["photo"]
        if not principal.get("specs") and p.get("specs"):
            principal["specs"] = p["specs"]
    variantes.sort(key=variant_min_price)
    # La foto que ya es la de la ficha no dice nada nuevo: Elektra usa la
    # misma imagen para los cuatro colores de un reloj, y guardarla cuatro
    # veces solo pesa.
    for v in variantes:
        for o in v["offers"]:
            if o.get("photo") and o["photo"] == principal.get("photo"):
                o.pop("photo")
    if len(variantes) >= 2:
        principal["colorVariants"] = variantes
        principal["name"] = strip_color_from_name(principal["name"], [v["color"] for v in variantes])
        principal["offers"] = list(variantes[0]["offers"])
    else:
        # Un solo color: no hay variantes que mostrar, solo ofertas que sumar.
        # La foto de la oferta sobra: es la de la ficha.
        principal.pop("colorVariants", None)
        principal["offers"] = [{k: v for k, v in o.items() if k != "photo"}
                               for o in variantes[0]["offers"]] if variantes else principal.get("offers") or []
    return [v["color"] for v in variantes]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--muestra", type=int, default=12)
    args = ap.parse_args()

    data = load_catalog()
    grupos, frenados = grupos_fusionables(data["products"])

    print(f"Grupos fusionables: {len(grupos)}  "
          f"(fichas: {sum(len(g) for g in grupos)}, se eliminarían {sum(len(g) - 1 for g in grupos)})")
    por_categoria = defaultdict(int)
    for g in grupos:
        por_categoria[g[0]["category"]] += len(g) - 1
    for cat, n in sorted(por_categoria.items(), key=lambda x: -x[1]):
        print(f"   {n:5}  {cat}")
    for g in grupos[:args.muestra]:
        colores = [", ".join(v["color"] for v in p.get("colorVariants") or []) or color_de_spec(p) for p in g]
        print(f"\n  {[p['id'] for p in g]}")
        print(f"    {g[0]['name'][:76]}")
        print(f"    colores: {colores}")
    if frenados:
        motivos = defaultdict(int)
        for _, m in frenados:
            motivos[m.split(":")[0].split(" -- ")[0]] += 1
        print(f"\nGrupos que NO se fusionan: {len(frenados)}  "
              + ", ".join(f"{m} {n}" for m, n in sorted(motivos.items(), key=lambda x: -x[1])))
        for fichas, motivo in frenados[:args.muestra]:
            print(f"   {[p['id'] for p in fichas]}  {motivo}")
            print(f"      {fichas[0]['name'][:70]}")

    if not grupos:
        return
    if args.dry_run:
        print("\n(--dry-run: no se escribió nada)")
        return

    a_borrar = set()
    con_variantes = repetidas = 0
    for fichas in grupos:
        colores = fusionar(fichas)
        if len(colores) >= 2:
            con_variantes += 1
        else:
            repetidas += 1
        a_borrar |= {p["id"] for p in fichas[1:]}

    data["products"] = [p for p in data["products"] if p["id"] not in a_borrar]
    save_catalog(data)
    print(f"\nFichas fusionadas y eliminadas: {len(a_borrar)}  "
          f"(grupos con variantes de color: {con_variantes}, publicaciones repetidas: {repetidas})")
    print(f"Catálogo: {len(data['products'])} productos")

    borradas = 0
    for pid in a_borrar:
        d = os.path.join(ROOT, "producto", pid)
        if os.path.isdir(d):
            shutil.rmtree(d)
            borradas += 1
    print(f"Páginas estáticas huérfanas eliminadas: {borradas}")


if __name__ == "__main__":
    main()
