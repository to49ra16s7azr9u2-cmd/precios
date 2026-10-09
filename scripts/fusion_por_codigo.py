#!/usr/bin/env python3
"""Informe de fusiones por CÓDIGO DE MODELO en el nombre, categoría por categoría.

POR QUÉ
-------
Muchos fabricantes (VentDepot y sus marcas: GreyTape, SecurityCode, CloudVortex...,
y casi todas las marcas chinas) rotulan su producto con un código propio
-- «MXSUC-003», «MXAXI-054», «GTX-9200» -- que viaja igual a todas las tiendas, aunque
cada una escriba el título a su manera (y los vendedores de Mercado Libre repitan el
mismo anuncio con títulos distintos: «Venta de Candados para Garaje MXSUC-003»,
«Candado Ventdepot Mxsuc-003 3 Piezas Azul», «Candado con combinación ... mxsuc-003-5»).
Esas fichas son la MISMA y quedaban sueltas: el 9-oct-2026 había 1,990 códigos de ese
estilo repartidos en más de una ficha (4,227 fichas).

QUÉ HACE
--------
Para una categoría, agrupa las fichas que comparten un código de modelo (el código
base: «mxsuc-003-5» y «mxsuc-003» son el mismo), parte cada grupo en subgrupos donde
TODAS las parejas pasan el veto de fusionar_vetado.motivo (mismas medidas, mismos
demás códigos, ni paquete en solo una, ni reacondicionado contra nuevo, precio a menos
de 1.8x), y escribe un informe en el formato de fusionar_vetado.py:

    python3 scripts/fusion_por_codigo.py "Climatización" --informe /tmp/f_clima.json
    python3 scripts/fusionar_vetado.py /tmp/f_clima.json            # ensayo (mismo veto otra vez)
    python3 scripts/fusionar_vetado.py /tmp/f_clima.json --aplicar

No fusiona nada por sí mismo. Códigos aceptados: los de VentDepot (mx + 3 letras +
3 dígitos) siempre; los demás solo si el token (letras y dígitos, 6+ caracteres, no
una medida) aparece en 2 a 8 fichas de la categoría.
"""
import argparse
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fusionar_vetado as FV  # noqa: E402
from data_io import load_catalog  # noqa: E402

MX_RE = re.compile(r"\b(mx[a-z]{3})-?(\d{3})(?:-\d{1,2})?\b")
TOKEN_RE = re.compile(r"\b(?=[a-z0-9-]*\d)(?=[a-z0-9-]*[a-z])[a-z0-9]{2,}(?:-[a-z0-9]+){0,3}\b")
STOP = re.compile(r"^(?:\d+(?:gb|tb|mb|mah|ml|cm|mm|kg|lb|pzs?|pcs|w|v|hz|l|lts?|in|oz|g|m)|[a-z]?\d{1,2}[a-z]?|"
                  r"\d+x\d+(?:x\d+)?(?:cm|mm|m)?|\d{4}|ipx\d+|usb\d?|wifi\d?|hdmi\d?|[45]k|[45]g|\dd|\den\d|\d+en\d+|r\d+|m\d+|"
                  r"ddr\d|a\d{1,2}|s\d{1,2}|v\d{1,2}|\d+k|\d+p)$")
MAX_GRUPO = 8
STOP2 = re.compile(r"^(?:\d+(?:gb|tb|mb|gr|kg|ml|cm|mm|lb|oz)[a-z]+|insta360|seer\d*|\d+btus?|\d+cfm|\d+rpm|\d+psi|\d+btu\w*|\d+tons?|\d+litros?|\d+velocidades|\d+w|\d+hp|\d+kw|"
                   r"\d+v|\d+hz|\d+pulg\w*|\d+mm|\d+cm|\d+pz\w*|\d+pcs|\d+gb|\d+tb|\d+mah)$")
UNIDADES_EXTRA = re.compile(r"(?<![\d.,])(\d+(?:[.,]\d+)?)\s*(tons?|toneladas?|btus?|v|volts?|hp|rpm|cfm|psi|kw|w|hz|litros?|lts?|l)\b")
COLORES = {"negro", "negra", "blanco", "blanca", "gris", "azul", "rojo", "roja", "rosa", "verde", "plata", "plateado",
           "dorado", "morado", "amarillo", "naranja", "cafe", "beige", "grafito", "multicolor", "transparente"}
OPUESTOS = (({"inverter"}, {"estandar", "convencional", "on off"}), ({"solo frio"}, {"frio calor", "frio/calor", "calor"}),
            ({"izquierdo", "izquierda"}, {"derecho", "derecha"}), ({"delantero", "delantera"}, {"trasero", "trasera"}))


def precio_min(p):
    v = [o["price"] for o in (p.get("offers") or []) if isinstance(o.get("price"), (int, float)) and o["price"] > 0]
    for var in p.get("colorVariants") or []:
        v += [o["price"] for o in (var.get("offers") or []) if isinstance(o.get("price"), (int, float)) and o["price"] > 0]
    return min(v) if v else None


def tiendas(p):
    s = {o.get("storeId") for o in (p.get("offers") or [])}
    for var in p.get("colorVariants") or []:
        s |= {o.get("storeId") for o in (var.get("offers") or [])}
    return sorted(x for x in s if x)


def claves_de(nombre):
    n = FV.norm(nombre)
    out = {m.group(1) + m.group(2) for m in MX_RE.finditer(n)}
    mx_prefijos = {c for c in out}
    toks = set()
    for t in TOKEN_RE.findall(n):
        t = t.replace("-", "")
        if len(t) >= 6 and not STOP.match(t) and not STOP2.match(t) and len(re.findall(r"\d", t)) >= 2 \
                and len(re.findall(r"[a-z]", t)) >= 2 and not any(t.startswith(m[:5]) for m in mx_prefijos if m):
            toks.add(t)
    return out, toks


def ficha(p):
    return {"id": p["id"], "nombre": p.get("name"), "tiendas": ",".join(tiendas(p)), "precio": precio_min(p),
            "brand": p.get("brand"), "categoria": p.get("category"),
            "facets": p.get("facets") or {}}


PULG_RE = re.compile(r"(?<![\d.,x])(\d{1,3}(?:[.,]\d{1,2})?)\s*(?:\"|''|”|pulgadas?|pulg\b|in\b|inch)")
PALABRA_RE = re.compile(r"[a-z]{3,}")
RELLENO = COLORES | {"para", "con", "sin", "los", "las", "una", "uno", "del", "por", "pieza", "piezas", "pzas", "set", "kit"}


def _pulgadas(n):
    return {x.replace(",", ".") for x in PULG_RE.findall(n)}


def _jaccard(na, nb):
    a = {w for w in PALABRA_RE.findall(na) if w not in RELLENO}
    b = {w for w in PALABRA_RE.findall(nb) if w not in RELLENO}
    return len(a & b) / max(1, len(a | b))


def _unidades(n):
    out = set()
    for num, u in UNIDADES_EXTRA.findall(n):
        u = {"ton": "ton", "tons": "ton", "tonelada": "ton", "toneladas": "ton", "btu": "btu", "btus": "btu",
             "volt": "v", "volts": "v", "lts": "l", "lt": "l", "litro": "l", "litros": "l"}.get(u, u)
        out.add((num.replace(",", "."), u))
    return out


ORIGINAL_RE = re.compile(r"\boriginal(?:es)?\b|\bgenuin[oa]s?\b|\boem\b")
COMPAT_RE = re.compile(r"\bcompatibles?\b|\bgenerico\b|\bgenerica\b|\bremanufactur\w+|\brecargad\w+|\balto rendimiento\b|\breemplazo\b|\brepuesto\b")
CANTIDAD_RE = re.compile(r"(?<![\d.,x])(\d{1,3})\s*(?:piezas?|pzas?|pzs?|pcs|unidades|pack|paquetes?|cartuchos|botes|botellas|rollos|bolsas)\b|"
                         r"\b(?:pack|paquete|paq|kit|set|juego|caja)\.?\s*(?:de|x)?\s*(\d{1,3})\b")


def _cantidad(n):
    v = {int(x) for m in CANTIDAD_RE.finditer(n) for x in m.groups() if x}
    v = {x for x in v if x > 1}
    return max(v) if v else None


def _marca_en_otro(a, b, na, nb):
    ma, mb = FV.norm(a.get("brand") or ""), FV.norm(b.get("brand") or "")
    if not ma or not mb or ma == mb or ma in mb or mb in ma:
        return True
    return ma in nb or mb in na      # la marca de una aparece en el nombre de la otra


def compatibles(a, b, estricto=False):
    na, nb = FV.norm(a["nombre"]), FV.norm(b["nombre"])
    if estricto:
        # Códigos genéricos (no los MX de VentDepot, que identifican el SKU solos):
        # original contra compatible, otra marca o un paquete de más es otro artículo.
        if bool(ORIGINAL_RE.search(na)) != bool(ORIGINAL_RE.search(nb)):
            return False
        if bool(COMPAT_RE.search(na)) != bool(COMPAT_RE.search(nb)):
            return False
        if not _marca_en_otro(a, b, na, nb):
            return False
        qa, qb = _cantidad(na), _cantidad(nb)
        if qa != qb:
            return False
        # Un código genérico es de la tienda o del vehículo tanto como del producto:
        # solo se une entre tiendas distintas (los duplicados de una tienda los ve merge_same_store).
        if set(a["tiendas"].split(",")) & set(b["tiendas"].split(",")):
            return False
        if a.get("categoria") in ("Autopartes", "Autos y motos"):
            ha = next(iter(PALABRA_RE.findall(na)), "")
            hb = next(iter(PALABRA_RE.findall(nb)), "")
            if ha != hb:
                return False
    if FV.motivo([a, b]) is not None:
        return False
    ma = {m.group(1) + m.group(2) for m in MX_RE.finditer(na)}
    mb = {m.group(1) + m.group(2) for m in MX_RE.finditer(nb)}
    if ma and mb and ma != mb:
        return False
    pa, pb = _pulgadas(na), _pulgadas(nb)
    if pa and pb and pa != pb:
        return False
    if estricto and _jaccard(na, nb) < 0.25:
        return False
    ua, ub = _unidades(na), _unidades(nb)
    if ua and ub and ua != ub:
        return False
    ca = {w for w in re.findall(r"[a-z]+", na) if w in COLORES}
    cb = {w for w in re.findall(r"[a-z]+", nb) if w in COLORES}
    if ca and cb and ca != cb:
        return False
    for x, y in OPUESTOS:
        if (any(k in na for k in x) and any(k in nb for k in y)) or (any(k in nb for k in x) and any(k in na for k in y)):
            return False
    return True


def subgrupos(fichas, estricto=False):
    """Cliques greedy: cada ficha entra al primer subgrupo con el que TODAS sus parejas pasan el veto."""
    out = []
    for f in fichas:
        for g in out:
            if all(compatibles(a, f, estricto) for a in g):
                g.append(f)
                break
        else:
            out.append([f])
    return [g for g in out if len(g) >= 2]


FIRMA_STOP = set("de del la el los las para con sin por en al y o e un una unos unas que su sus the and for of with pza pzas "
                 "pieza piezas pz pzs color colores modelo mod tipo marca nuevo nueva original originales envio gratis oferta "
                 "venta internacional".split())
FIRMA_NUM_RE = re.compile(r"\d+(?:[.,]\d+)?")


def firma_de(nombre):
    """Las palabras y los números del nombre (1.5 es UN número), sin colores ni relleno."""
    n = FV.norm(nombre).replace("+", " mas ")
    nums = {m.replace(",", ".") for m in FIRMA_NUM_RE.findall(n)}
    cuenta = collections.Counter(w for w in re.findall(r"[a-z]+", n)
                                 if w not in FIRMA_STOP and w not in COLORES and (len(w) > 1 or w not in "ayoeu"))
    cods = {t.replace("-", "") for t in TOKEN_RE.findall(n)}
    # con la cuenta de cada palabra: «USB-C a USB-C» no es «USB-C a USB A»
    return tuple(sorted({f"{w}#{c}" for w, c in cuenta.items()} | nums | cods))


def informe_firma(prods, cat):
    """Agrupa por (subcategoría, firma del nombre): el mismo nombre con otro orden, otra puntuación o sin el color."""
    grupos = collections.defaultdict(list)
    for p in prods:
        f = firma_de(p.get("name"))
        if len(f) >= 4:
            grupos[(p.get("subcategory"), f)].append(p)
    informe = []
    for fichas in grupos.values():
        if not (2 <= len(fichas) <= MAX_GRUPO):
            continue
        for g in subgrupos([ficha(p) for p in fichas], estricto=True):
            informe.append(g)
    informe.sort(key=lambda g: -len(g))
    return informe


def _facetas_en_conflicto(a, b):
    """Una faceta que las dos fichas declaran y no dicen igual (color, talla, capacidad...): son dos productos."""
    fa, fb = a.get("facets") or {}, b.get("facets") or {}
    for k in fa.keys() & fb.keys():
        if k == "pack_n":
            continue
        va, vb = fa[k], fb[k]
        if isinstance(va, list) or isinstance(vb, list):
            continue
        if va != vb:
            return True
    return False


def informe_misma(prods, cat):
    """El MISMO nombre exacto (sin acentos ni puntuación) dentro de una subcategoría, también dentro de una misma
    tienda (publicaciones repetidas de vendedores distintos). Precio a menos de 1.5x y ninguna faceta en conflicto."""
    grupos = collections.defaultdict(list)
    for p in prods:
        n = " ".join(re.findall(r"[a-z0-9]+", FV.norm(p.get("name"))))
        if len(n.split()) >= 4 and len(n) >= 24 and "varios modelos" not in n:
            grupos[(p.get("subcategory"), n)].append(p)
    informe = []
    for fichas in grupos.values():
        if not (2 <= len(fichas) <= 15):
            continue
        fs = [ficha(p) for p in fichas]
        cliques = []
        for f in fs:
            for g in cliques:
                if all(FV.motivo([a, f]) is None and not _facetas_en_conflicto(a, f)
                       and max(a["precio"] or 1, f["precio"] or 1) / max(1, min(a["precio"] or 1, f["precio"] or 1))
                       < (1.07 if set(a["tiendas"].split(",")) & set(f["tiendas"].split(",")) else 1.12)
                       for a in g):
                    g.append(f)
                    break
            else:
                cliques.append([f])
        informe += [g for g in cliques if len(g) >= 2]
    informe.sort(key=lambda g: -len(g))
    return informe


def informe_de(prods, cat):
    mx = collections.defaultdict(list)
    gen = collections.defaultdict(list)
    for p in prods:
        a, b = claves_de(p.get("name"))
        for c in a:
            mx[c].append(p)
        for c in b:
            gen[c].append(p)
    vistos = set()
    informe = []
    for tabla, tope in ((mx, 60), (gen, MAX_GRUPO)):
        for clave, fichas in tabla.items():
            if not (2 <= len(fichas) <= tope):
                continue
            ids = tuple(sorted(f["id"] for f in fichas))
            if ids in vistos:
                continue
            vistos.add(ids)
            for g in subgrupos([ficha(p) for p in fichas], estricto=tabla is gen):
                clave_g = tuple(sorted(x["id"] for x in g))
                if clave_g in vistos and tabla is gen:
                    continue
                vistos.add(clave_g)
                informe.append(g)
    # un id solo en un grupo: el más grande gana
    informe.sort(key=lambda g: -len(g))
    usados = set()
    final = []
    for g in informe:
        g = [x for x in g if x["id"] not in usados]
        if len(g) >= 2:
            final.append(g)
            usados |= {x["id"] for x in g}
    return final


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("categorias", nargs="+")
    ap.add_argument("--informe", required=True, help="ruta del informe; con {cat} se escribe uno por categoría")
    ap.add_argument("--muestra", type=int, default=6)
    ap.add_argument("--modo", choices=["codigo", "firma", "misma"], default="codigo")
    args = ap.parse_args()
    data = load_catalog()
    if args.categorias == ["todas"]:
        args.categorias = sorted({p.get("category") for p in data["products"] if p.get("category")})
    por_cat = collections.defaultdict(list)
    for p in data["products"]:
        if p.get("category") in set(args.categorias):
            por_cat[p["category"]].append(p)
    todos = []
    for cat in args.categorias:
        prods = por_cat.get(cat, [])
        final = (informe_firma(prods, cat) if args.modo == 'firma' else informe_misma(prods, cat) if args.modo == 'misma'
                 else informe_de(prods, cat))
        print(f"## {cat}: {len(prods):,} fichas; grupos propuestos: {len(final)} con {sum(len(g) for g in final)} fichas")
        for g in final[:args.muestra]:
            print("  ·", len(g), "fichas")
            for x in g[:4]:
                print(f"      {x['id']:<9} {x['tiendas']:<28} {x['precio'] or 0:>9,.0f}  {(x['nombre'] or '')[:78]}")
        if "{cat}" in args.informe:
            ruta = args.informe.replace("{cat}", re.sub(r"\W+", "_", cat))
            json.dump(final, open(ruta, "w", encoding="utf-8"), ensure_ascii=False)
        todos += final
    if "{cat}" not in args.informe:
        json.dump(todos, open(args.informe, "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    main()
