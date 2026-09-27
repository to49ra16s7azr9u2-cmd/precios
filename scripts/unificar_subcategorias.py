#!/usr/bin/env python3
"""Revisión del árbol de subcategorías (26-sep-2026): juntar y repartir por el nombre.

POR QUÉ
-------
Medido sobre el catálogo (40 fichas por subcategoría, sus vecinos por
nombre): 128 subcategorías convivían con una hermana que la contiene
(«Perfumes» junto a «Perfumes para mujer», «Tenis» junto a «Tenis para
hombre», «Escritorios» con 9 fichas junto a seis clases de escritorio). Un
perfume para mujer puede caer en cualquiera de las dos, así que las dos
listas quedan incompletas y el visitante no sabe dónde buscar. El error lo
pone el árbol, no el clasificador.

DOS OPERACIONES
---------------
1. UNIR (subcategorias_unidas.py): lo que es lo mismo con dos nombres, o
   una subcategoría de 0 a 30 fichas que repite a su hermana. La vieja sale
   del manifiesto, su url redirige a la que queda (data/redirecciones.json)
   y reorganizar_categorias.destino() manda ahí todo lo que llegue con el
   nombre viejo.
2. ATRIBUTOS: donde el nombre lo dice (género, talla, pulgadas, litros,
   rin; «iPhone» en «Reacondicionados»), y sólo si dice UNA cosa.
   Lo que no lo dice se queda en la general, que sigue siendo el lugar de
   «sin especificar». (Repartir con los vecinos por nombre se probó y acertó
   ~60%: ver la nota sobre ATRIBUTOS.)

Lo que está en el candado donde lo dejaron no se toca.

USO
---
    python3 scripts/unificar_subcategorias.py                    # informe con muestra
    python3 scripts/unificar_subcategorias.py --aplicar          # manifiesto + fichas
    python3 scripts/unificar_subcategorias.py --salida mov.json  # sólo ATRIBUTOS
                                                                 # (lo nuevo de cada día)
"""
import argparse
import collections
import io
import json
import os
import random
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
from data_io import load_catalog, save_catalog  # noqa: E402
from subcategorias_unidas import UNIR  # noqa: E402

CANDADO = os.path.join(ROOT, "data", "clasificacion-a-mano.json")
REDIRECCIONES = os.path.join(ROOT, "data", "redirecciones.json")
BITACORA = os.path.join(ROOT, "data", "movimientos-aplicados.json")

# Repartir con los vecinos por nombre (como completar_subcategorias.py) se
# probó y NO se usa: entre hermanas de la misma categoría acertó ~60% en la
# muestra (26-sep). Los vecinos votan por marca y talla: edredones «king
# size» a «Sábanas king size», almohadas comunes a «memory foam»,
# micrófonos dinámicos a «condensador», y en las divisiones por género gana
# la hermana más grande (tenis PS de preescolar a «Tenis para hombre»).
# Sólo se mueve lo que el NOMBRE dice, abajo.

# ATRIBUTOS: (categoría, subcategoría de origen, [(expresión, destino)]).
# Sólo cuando el NOMBRE lo dice, y sólo si apunta a UN destino: «sábana
# queen/king» no se mueve. Lo que no lo dice se queda en la general.
_MUJER = r"\b(mujer|mujeres|dama|damas|femenin[oa]|femme|woman|women|for her)\b"
_HOMBRE = r"\b(hombre|hombres|caballero|caballeros|masculin[oa]|homme|for men|for him)\b"
_NINOS = r"\b(niñ[oa]s?|nin[oa]s?|infantil(es)?|kids?|junior|toddler|bebé|bebe)\b"
ATRIBUTOS = [
    ("Celulares", "Reacondicionados", [(r"\biphone\b", "iPhone reacondicionados")]),
    ("Celulares", "iPhone", [(r"reacondicionad|\brenewed\b|seminuevo|refurbish|\busado\b", "iPhone reacondicionados")]),
    ("Belleza y cuidado personal", "Perfumes", [(_MUJER, "Perfumes para mujer"), (_HOMBRE, "Perfumes para hombre"),
                                                (r"\bunisex\b", "Perfumes unisex")]),
    ("Calzado", "Tenis", [(_NINOS, "Tenis para niños"), (_MUJER, "Tenis para mujer"), (_HOMBRE, "Tenis para hombre")]),
    ("Joyería y bisutería", "Relojes", [(_NINOS, "Relojes infantiles")]),
    ("Blancos y ropa de cama", "Sábanas", [(r"\bking\b", "Sábanas king size"), (r"\bqueen\b", "Sábanas queen size"),
                                           (r"\bmatrimonial(es)?\b", "Sábanas matrimoniales"),
                                           (r"\bindividual(es)?\b", "Sábanas individuales"),
                                           (r"\bcuna\b|\bbeb[eé]s?\b", "Sábanas para cuna y bebé")]),
    ("Muebles", "Colchones", [(r"\bking\b", "Colchones king size"), (r"\bqueen\b", "Colchones queen size"),
                              (r"\bmatrimonial(es)?\b", "Colchones matrimoniales"),
                              (r"\bindividual(es)?\b", "Colchones individuales"),
                              (r"\bcuna\b|\binfantil\b|\bbeb[eé]s?\b", "Colchones infantiles y de cuna")]),
    ("Tabletas", "Tabletas Android", [("REQUIERE", r"\btablet\b|\btableta android"), ("PULGADAS", {(0, 8.9): "Tabletas Android de 8 pulgadas o menos",
                                                    (10, 11.9): "Tabletas Android de 10 a 11 pulgadas",
                                                    (12, 20): "Tabletas Android de 12 pulgadas o más"})]),
    ("Electrodomésticos", "Freidoras de aire", [("LITROS", {(0, 3.0): "Freidoras de aire hasta 3 L",
                                                            (3.5, 5.0): "Freidoras de aire de 3.5 a 5 L",
                                                            (5.5, 7.0): "Freidoras de aire de 5.5 a 7 L",
                                                            (8, 40): "Freidoras de aire de 8 L o más"})]),
    ("Instrumentos musicales", "Micrófonos", [(r"inal[aá]mbric|wireless", "Micrófonos inalámbricos"),
                                              (r"condensador|\busb\b", "Micrófonos de condensador y USB"),
                                              (r"lavalier|\bsolapa\b", "Micrófonos lavalier")]),
    ("Herramientas", "Brocas", [("REQUIERE", r"\bbrocas?\b"),
                                (r"broca sierra|sierra de copa|sierra copa|cortac[ií]rculo", "Sierras de copa y cortacírculos"),
                                (r"concreto|mamposter[ií]a|\bsds\b|hormig[oó]n|percusi[oó]n|rotomartillo", "Brocas para concreto y SDS"),
                                (r"\bmetal(es)?\b|cobalto|\bcobalt\b|\bhss\b|acero r[aá]pido|alta velocidad", "Brocas para metal"),
                                (r"\bmadera\b|barrena|brad point|\bpala\b|forstner|sinf[ií]n", "Brocas para madera")]),
    ("Blancos y ropa de cama", "Almohadas", [(r"lactancia|embarazo|maternidad", "Almohadas de lactancia y embarazo"),
                                             (r"cervical|ortop[eé]dic|\bpiernas\b|\brodillas\b", "Almohadas cervicales y ortopédicas"),
                                             (r"^\s*fundas? (de|para) almohada", "Fundas de almohada"),
                                             (r"^\s*protector(es)? (de|para) almohada", "Protectores de almohada")]),
    ("Blancos y ropa de cama", "Edredones", [(r"relleno|\bduvet\b|inserto", "Rellenos de edredón (duvet)"),
                                             (r"funda n[oó]rdica|funda (de|para) edred[oó]n", "Fundas nórdicas y de edredón")]),
    ("Belleza y cuidado personal", "Corporales", [(r"body mist|\bsplash\b|\bbruma\b|fragancia corporal|\bmist\b", "Body mist y splash"),
                                                  (r"crema corporal|loci[oó]n corporal|body lotion|crema para (el )?cuerpo", "Cremas y lociones corporales"),
                                                  (r"exfoliante", "Exfoliantes corporales"),
                                                  (r"masajeador", "Masajeadores")]),
    ("Belleza y cuidado personal", "Maquillaje", [(r"^\s*base\b|base de maquillaje|maquillaje l[ií]quido|foundation", "Bases de maquillaje"),
                                                  (r"\bpaleta\b|set de maquillaje|kit de maquillaje", "Paletas y sets de maquillaje"),
                                                  (r"organizador|cosmetiquera", "Organizadores de maquillaje")]),
    # Duplicados que se retiran (UNIR): antes, lo que el nombre ubica en otra
    # hermana; el resto lo lleva UNIR al guardar.
    ("Belleza y cuidado personal", "Cremas y sérums faciales", [("EXCLUYE", r"m[aá]quina|dispositivo|t[oó]nico"),
                                                                (r"s[eé]rum|ampolleta", "Sérums faciales")]),
    ("Belleza y cuidado personal", "Bases y correctores", [(r"\bcorrector", "Correctores"), (r"\bprimer\b", "Primers y fijadores"),
                                                           ("EXCLUYE", r"brocha|esponja|pincel|borla"),
                                                           (r"\bpolvo", "Polvos, rubores y bronceadores")]),
    ("Herramientas", "Cerraduras y candados", [(r"\bcandado|padlock", "Candados")]),
    ("Autos y motos", "Llantas para auto", [("RIN", {(13, 14): "Llantas para auto rin 13 y 14", (15, 15): "Llantas para auto rin 15",
                                                     (16, 16): "Llantas para auto rin 16", (17, 17): "Llantas para auto rin 17",
                                                     (18, 18): "Llantas para auto rin 18", (19, 24): "Llantas para auto rin 19 o más"})]),
]
_RX_PULG = re.compile(r"(?<![\d.,])(\d{1,2}(?:[.,]\d{1,2})?)\s*(?:\"|”|''|pulgadas|pulg\b|in\b|inch)", re.I)
_RX_LITROS = re.compile(r"(?<![\d.,])(\d{1,2}(?:[.,]\d{1,2})?)\s*(l|lt|lts|litros?|qt|cuartos?)\b", re.I)
_RX_RIN = re.compile(r"(?:\d{3}/\d{2}\s*z?r\s*|\brin\s*|\br)(\d{2})\b", re.I)


def _medidas(tipo, nombre):
    """Los valores de la medida que dice el nombre (pueden ser varios)."""
    if tipo == "PULGADAS":
        return {float(m.group(1).replace(",", ".")) for m in _RX_PULG.finditer(nombre)}
    if tipo == "LITROS":
        out = set()
        for m in _RX_LITROS.finditer(nombre):
            v = float(m.group(1).replace(",", "."))
            out.add(round(v * 0.946, 1) if m.group(2).lower().startswith(("qt", "cuart")) else v)
        return out
    if tipo == "RIN":
        return {float(m.group(1)) for m in _RX_RIN.finditer(nombre)}
    return set()


def por_atributo(reglas, nombre):
    """El único destino que dice el nombre, o None (ninguno o más de uno).
    ("REQUIERE", rx): sin eso en el nombre no se mueve nada (las «tabletas
    de tricloro» mal puestas en Tabletas); ("EXCLUYE", rx): con eso tampoco
    (la «esponja para polvo» no es un polvo)."""
    dest = set()
    for rx, d in reglas:
        if rx == "REQUIERE":
            if not re.search(d, nombre, re.I):
                return None
            continue
        if rx == "EXCLUYE":
            if re.search(d, nombre, re.I):
                return None
            continue
        if isinstance(d, dict):
            for v in _medidas(rx, nombre):
                for (lo, hi), s in d.items():
                    if lo <= v <= hi:
                        dest.add(s)
        elif re.search(rx, nombre, re.I):
            dest.add(d)
    return dest.pop() if len(dest) == 1 else None


def cargar_candado():
    if not os.path.exists(CANDADO):
        return {}
    with io.open(CANDADO, encoding="utf-8") as f:
        return json.load(f)


def en_candado(p, candado):
    fijo = candado.get(p["id"])
    if isinstance(fijo, list) and fijo:
        return fijo[0] == p["category"] and (fijo[1] if len(fijo) > 1 else None) == p.get("subcategory")
    if isinstance(fijo, dict):
        return fijo.get("category") == p["category"] and fijo.get("subcategory") == p.get("subcategory")
    return False


def proponer(prods, candado):
    """[(ficha, sub nueva, motivo)] de ATRIBUTOS."""
    out = []
    attr = {(cat, sub): reglas for cat, sub, reglas in ATRIBUTOS}
    for p in prods:
        reglas = attr.get((p["category"], p.get("subcategory")))
        if reglas and not en_candado(p, candado):
            dest = por_atributo(reglas, p.get("name") or "")
            if dest and dest != p.get("subcategory"):
                out.append((p, dest, "atributo"))

    return out


def manifiesto(data, retirar):
    """Quita las subcategorías de `retirar` ({(cat, sub): (cat2, sub2)}) y
    crea las de destino que falten con la familia de la primera que llega."""
    por_id = {c["id"]: c for c in data["categories"]}
    creadas, quitadas = [], []
    for (c, s), (c2, s2) in retirar.items():
        cat, dest = por_id.get(c), por_id.get(c2)
        if not cat or not dest:
            continue
        vieja = next((x for x in cat.get("subcategories") or [] if x["id"] == s), None)
        if not any(x["id"] == s2 for x in dest.get("subcategories") or []):
            nueva = {"id": s2, "name": s2, "icon": (vieja or {}).get("icon") or dest.get("icon")}
            if vieja and vieja.get("fam") and c == c2:
                nueva["fam"] = vieja["fam"]
            dest.setdefault("subcategories", []).append(nueva)
            creadas.append(f"{c2} / {s2}")
        if vieja:
            cat["subcategories"] = [x for x in cat["subcategories"] if x["id"] != s]
            quitadas.append(f"{c} / {s}")
    return creadas, quitadas


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--salida", help="JSON para aplicar_movimientos.py con ATRIBUTOS")
    ap.add_argument("--muestras", type=int, default=60)
    args = ap.parse_args()
    sys.path.insert(0, AQUI)
    from data_io import slugify

    data = load_catalog()
    prods = data["products"]
    candado = cargar_candado()

    # 1. UNIR (las fichas las mueve destino() al guardar; aquí se cuentan).
    unidas = collections.Counter()
    for p in prods:
        k = (p["category"], p.get("subcategory"))
        if k in UNIR:
            unidas[(k, UNIR[k])] += 1
    print(f"UNIR: {len(UNIR)} subcategorías, {sum(unidas.values()):,} fichas")
    for ((c, s), (c2, s2)), n in unidas.most_common(15):
        print(f"  {n:6,}  {c} / {s} -> {s2 if c == c2 else c2 + ' / ' + s2}")

    # 2 y 3. ATRIBUTOS y REPARTIR
    mov = proponer(prods, candado)
    cuenta = collections.Counter((p["category"], p.get("subcategory"), s2, m.split()[0]) for p, s2, m in mov)
    print(f"\nATRIBUTOS: {len(mov):,} fichas")
    for (c, s, s2, m), n in cuenta.most_common(60):
        print(f"  {n:6,}  {c} / {s} -> {s2}  ({m})")
    random.seed(5)
    print("\nMuestra:")
    for p, s2, m in random.sample(mov, min(args.muestras, len(mov))):
        print(f"  {p.get('subcategory')} -> {s2} [{m}] | {p['name'][:75]}")

    grupos = collections.defaultdict(list)
    for p, s2, m in mov:
        grupos[f"{p['category']} | {p.get('subcategory')} | {p['category']} | {s2}"].append(p["id"])
    if args.salida:
        json.dump(grupos, open(args.salida, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(f"-> {args.salida}")
    if not args.aplicar:
        return

    # Manifiesto: las de UNIR y las generales con RESTO se retiran.
    retirar = dict(UNIR)
    creadas, quitadas = manifiesto(data, retirar)
    print(f"\nmanifiesto: {len(quitadas)} subcategorías retiradas, {len(creadas)} creadas: {creadas}")

    # Fichas: REGLAS/REPARTIR aquí; las de UNIR, destino() dentro de save_catalog.
    n = 0
    for p, s2, m in mov:
        p["subcategory"] = s2
        n += 1
    print(f"fichas repartidas: {n:,}")

    # Candado a los nombres nuevos: si no, lo fijado en «Charms» dejaría de
    # reconocerse como fijado al pasar a «Dijes y charms».
    cambios = 0
    for pid, v in candado.items():
        if isinstance(v, list) and v and (v[0], v[1] if len(v) > 1 else None) in retirar:
            c2, s2 = retirar[(v[0], v[1])]
            v[:2] = [c2, s2]
            cambios += 1
    with io.open(CANDADO, "w", encoding="utf-8") as f:
        json.dump(candado, f, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    print(f"candado: {cambios:,} entradas con el nombre nuevo")

    # Redirecciones de las urls de subcategorías retiradas.
    with io.open(REDIRECCIONES, encoding="utf-8") as f:
        red = json.load(f)
    rutas = red.setdefault("rutas", {})
    for (c, s), (c2, s2) in retirar.items():
        rutas[f"categoria/{slugify(c)}/{slugify(s)}/"] = f"categoria/{slugify(c2)}/{slugify(s2)}/"
    with io.open(REDIRECCIONES, "w", encoding="utf-8") as f:
        json.dump(red, f, ensure_ascii=False, indent=1)
        f.write("\n")

    # Bitácora
    bit = json.load(io.open(BITACORA, encoding="utf-8")) if os.path.exists(BITACORA) else []
    g = collections.Counter()
    for ((c, s), (c2, s2)), k in unidas.items():
        g[f"{c} | {s} | {c2} | {s2}"] += k
    for k, v in grupos.items():
        g[k] += len(v)
    import datetime
    bit.append({"fecha": datetime.date.today().isoformat(), "origen": "unificar_subcategorias.py",
                "motivo": "revisión del árbol: subcategorías duplicadas unidas y generales repartidas",
                "grupos": dict(g)})
    with io.open(BITACORA, "w", encoding="utf-8") as f:
        json.dump(bit, f, ensure_ascii=False, indent=0)

    save_catalog(data)
    print("Guardado.")


if __name__ == "__main__":
    main()
