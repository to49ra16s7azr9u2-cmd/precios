#!/usr/bin/env python3
"""Junta en UNA ficha los productos que son el mismo equipo en otro color.

EL PROBLEMA
-----------
La lista mostraba el mismo teléfono cinco veces seguidas:

    iPhone 17 256GB Libre Blanco     $19,999
    iPhone 17 256GB Negro Medianoche $17,099
    iPhone 17 256GB Libre Azul       ...
    iPhone 17 256GB Libre Lavanda    ...
    iPhone 17 256GB Libre Verde      ...

Son el mismo producto. Quien busca un iPhone 17 de 256 GB quiere ver UNA
ficha con el precio más bajo y elegir el color adentro, no cinco fichas
que compiten entre sí y esconden cuál es realmente el más barato.

QUÉ SE CONSIDERA "EL MISMO EQUIPO"
----------------------------------
La firma estructurada de phone_signature.py SIN el color: marca, modelo,
almacenamiento, RAM, compañía, regalo, condición, eSIM y red tienen que
coincidir. O sea que NO se juntan (y está bien que no):

    - un 256 GB con un 512 GB
    - un nuevo con un reacondicionado
    - un "sólo eSIM" con uno de SIM física  <- pedido expreso del usuario
    - un Telcel con uno libre
    - uno con audífonos de regalo con uno sin regalo

Si a una ficha le falta el modelo, la capacidad o el color, la firma queda
incompleta y esa ficha no se junta con nadie.

CÓMO QUEDA LA FICHA
-------------------
Cada color pasa a ser una entrada de `colorVariants` CON SUS PROPIAS
OFERTAS, así que un color de Elektra y otro de Mercado Libre conviven sin
que uno herede la tienda del otro:

    colorVariants: [
      {"color": "Azul marino", "offers": [ ...ofertas de ese color... ]},
      {"color": "Blanco",      "offers": [ ... ]},
    ]

El nombre del color es el COMPLETO ("Azul marino", "Azul hielo"), no el
color base: el Galaxy S25 FE tiene dos azules distintos y en la lista de
variantes tienen que poder distinguirse.

Sobrevive la ficha de id más bajo (la más vieja, la que probablemente ya
esté indexada), igual que en merge_cross_store.py y merge_by_signature.py.
product.offers queda con las ofertas de la variante más barata, para que
cualquier lector viejo que mire product.offers directamente siga viendo un
precio razonable.

USO
---
    python3 scripts/merge_by_color.py --dry-run
    python3 scripts/merge_by_color.py
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import id_num, load_catalog, registrar_fusiones, save_catalog  # noqa: E402
from phone_signature import (  # noqa: E402
    FINISH_QUALIFIERS, color_full_of, condition_of, signature,
)
from match_amazon_capture import COLOR_CANON, COLORS  # noqa: E402

# palabra tal como la escriben las tiendas -> color canónico
COLORS_CANON = {c: COLOR_CANON.get(c, c) for c in COLORS}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# La firma estructurada de phone_signature.py está construida y probada para
# teléfonos (capacidad, RAM, compañía, eSIM). Aplicarla a un sillón leería
# "modelo" donde no hay, así que solo Celulares pasa por ese camino.
CATEGORIES = ("Celulares",)

# El resto del catálogo va por el camino GENÉRICO de abajo (generic_key):
# dos fichas se juntan solo si su nombre es IDÉNTICO una vez quitado el
# color. Sin modelos, sin parecidos, sin adivinar.
#
# Estas categorías quedan fuera porque ahí el color NO es un acabado, es el
# producto:
#   - Iluminación: "luz blanca" y "luz cálida" son focos distintos.
#   - Joyería: un anillo de oro y uno de plata no son el mismo anillo en
#     otro color -- ni cuestan lo mismo.
#   - Salud: el tono de un tinte o de una base de maquillaje es
#     lo que se compra.
CATEGORIES_SIN_COLOR = ("Iluminación", "Joyería y bisutería", "Salud")


_ACENTOS = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")
_NO_PALABRA_RE = re.compile(r"[^a-z0-9]+")


def _tokens(texto):
    """Tokens comparables de un nombre: sin acentos, sin puntuación, en
    minúscula y EN ORDEN.

    En orden a propósito, no como conjunto: "Adaptador HDMI a VGA" y
    "Adaptador VGA a HDMI" tienen las mismas palabras y son dos productos
    distintos. Perder alguna fusión por el orden es barato; juntar dos
    productos que no son el mismo, no.
    """
    return [t for t in _NO_PALABRA_RE.split(texto.translate(_ACENTOS).lower()) if t]


def generic_key(product):
    """Clave de agrupación para las categorías que NO son Celulares, o None.

    Dos fichas comparten clave cuando, quitado el color, les queda el mismo
    nombre palabra por palabra, la misma marca, la misma categoría y la
    misma condición. Es deliberadamente estricto: acá no hay firma
    estructurada que diga qué es capacidad y qué es modelo, así que lo
    único en lo que se puede confiar es en que el resto del nombre coincida
    exactamente.

    Devuelve None -- y la ficha no se junta con nadie -- cuando:
      * la categoría es una en la que el color es el producto,
      * el nombre no declara color (no hay nada que separar),
      * quitarle el color no cambia el nombre (el color venía de un campo
        que no está en el título, así que no se puede comparar el resto),
      * lo que queda son menos de 4 palabras: "Funda para iPhone" describe
        cientos de productos distintos.
    """
    if product.get("category") in CATEGORIES_SIN_COLOR:
        return None
    marca = (product.get("brand") or "").strip().lower()
    if not marca:
        return None
    nombre = product.get("name") or ""
    etiqueta = color_label(product)
    if not etiqueta:
        return None
    resto = strip_color_from_name(nombre, [etiqueta])
    if resto == nombre:
        return None
    toks = _tokens(resto)
    if len(toks) < 4:
        return None
    return (product.get("category"), marca, " ".join(toks), condition_of(nombre))




# Una palabra de color que en realidad es parte de un nombre propio no
# describe el producto: "Aspiradora Black & Decker Ciclónica Roja" es ROJA,
# no negra, y "Xiaomi Black Shark ... Negro" es negro por el "Negro" del
# final, no por el "Black" del modelo. Se borran esas apariciones ANTES de
# leer el color, con el mismo criterio que ya usa la limpieza del nombre.
def _sin_colores_de_nombre_propio(name):
    texto = name
    for palabra in sorted(COLORS, key=len, reverse=True):
        texto = re.sub(
            rf"(?<![\w]){re.escape(palabra)}(?![\w])",
            lambda m: "" if _quita_si_es_color(m) == m.group(0) else m.group(0),
            texto,
            flags=re.I,
        )
    return texto


def color_parts(product):
    """(color base, apellidos) del nombre, o (None, ()) si no dice color."""
    base, quals = color_full_of(_sin_colores_de_nombre_propio(product.get("name", "")))
    if not base:
        return None, ()
    # Los apellidos que YA están dentro del color base sobran: color_of
    # devuelve "titanio del desierto" como base y ("desierto", "titanio")
    # como apellidos, y concatenarlos daba "Titanio del desierto desierto
    # titanio".
    limpios = tuple(q for q in (quals or ()) if q not in base)
    return base, limpios


def color_label(product):
    """Nombre para mostrar del color ("Azul marino"), no solo el base."""
    base, quals = color_parts(product)
    if not base:
        return None
    etiqueta = base if not quals else f"{base} {' '.join(quals)}"
    return etiqueta[:1].upper() + etiqueta[1:]


def collapse_labels(labels):
    """etiqueta cruda -> etiqueta canónica, colapsando las formas de escribir
    el MISMO color.

    Trabaja sobre las ETIQUETAS y no sobre los productos porque las fichas
    ya fusionadas por color traen sus variantes con el nombre escrito por
    Mercado Libre ("Naranja", "Naranja cósmico", "Naranja cósmico titanio"),
    y ahí no hay producto al que preguntarle.
    """
    por_base = defaultdict(list)
    sueltas = {}
    for raw in labels:
        base, quals = color_full_of(raw)
        if not base:
            sueltas[raw] = raw
            continue
        limpios = tuple(q for q in (quals or ()) if q not in base)
        por_base[base].append((raw, limpios))
    out = dict(sueltas)
    for base, miembros in por_base.items():
        # Se agrupa por INCLUSIÓN, no por igualdad: "Naranja", "Naranja
        # cósmico" y "Naranja cósmico titanio" son apellidos anidados -- la
        # misma pintura descrita con más o menos detalle -- y el iPhone 17
        # Pro tiene un solo naranja. En cambio "Azul marino" y "Azul hielo"
        # son conjuntos DISJUNTOS: dos azules reales del Galaxy S25 FE, y
        # esos sí se quedan separados.
        cadenas = []  # cada cadena: [(raw, quals), ...] compatibles entre sí
        # De MÁS específico a menos: así las cadenas de cada acabado real se
        # forman primero y el nombre pelado llega al final, cuando ya puede
        # ver que encaja en dos y quedarse aparte. Al revés, el pelado creaba
        # la primera cadena y se llevaba puesto al primer acabado que
        # apareciera ("Azul" terminaba etiquetado "Azul marino").
        for raw, quals in sorted(miembros, key=lambda m: -len(m[1])):
            compatibles = [c for c in cadenas
                           if all(set(q) <= set(quals) or set(quals) <= set(q) for _, q in c)]
            # Compatible con DOS cadenas a la vez = ambiguo: un "Azul" pelado
            # cuando el equipo tiene "Azul marino" y "Azul hielo" no dice
            # cuál de los dos es, así que se queda como su propia variante en
            # vez de meterlo en una a dedo.
            if len(compatibles) == 1:
                compatibles[0].append((raw, quals))
            else:
                cadenas.append([(raw, quals)])
        for cadena in cadenas:
            mejor = max((r for r, _ in cadena), key=len)
            for raw, _ in cadena:
                out[raw] = mejor
    return out


def collapse_colors(productos):
    """id de producto -> etiqueta de color, colapsando las formas de escribir
    el MISMO color.

    Dentro de un grupo, "Naranja" y "Naranja cósmico" son el mismo color del
    iPhone 17 Pro escrito de dos formas: solo existe un naranja. Pero "Azul
    marino" y "Azul hielo" del Galaxy S25 FE son DOS azules reales. La regla
    es la misma que usa merge_by_signature.py: con un solo apellido para ese
    color base, el apellido no distingue nada y se colapsa; con dos o más,
    cada uno es su propia variante y el que viene sin apellido queda aparte
    porque no se sabe cuál es.
    """
    por_base = defaultdict(list)
    for p in productos:
        base, quals = color_parts(p)
        if base:
            por_base[base].append((p, quals))
    etiquetas = {}
    for base, miembros in por_base.items():
        con_apellido = {q for _, q in miembros if q}
        if len(con_apellido) <= 1:
            # Un solo apellido (o ninguno): todos son el mismo color. Se usa
            # la forma más descriptiva que haya aparecido.
            mejor = max((color_label(p) for p, _ in miembros), key=len)
            for p, _ in miembros:
                etiquetas[p["id"]] = mejor
        else:
            for p, _ in miembros:
                etiquetas[p["id"]] = color_label(p)
    return etiquetas


# Conectores que quedan colgando cuando se quita el color: "... - Color
# plata" -> "... -", "... con cámara azul" -> "... con cámara".
_COLA_RE = re.compile(
    r"(?:\s*[-–—,:/]\s*|\s+)(?:de\s+)?(?:color(?:es)?|con|en|tono)?\s*$", re.I
)
_ESPACIOS_RE = re.compile(r"\s{2,}")
_SEPARADORES_RE = re.compile(r"\s*[-–—]\s*[-–—]\s*")


# Palabras que sí pueden seguir a un color sin que deje de ser un color:
# son los apellidos de acabado ("Negro Medianoche", "Titanio del desierto").
_TRAS_COLOR_OK = {q.lower() for q in FINISH_QUALIFIERS} | {c.lower() for c in COLORS}


def _quita_si_es_color(m):
    """Reemplazo del color por un espacio, salvo cuando la palabra parece
    parte del NOMBRE del modelo.

    "Xiaomi Black Shark" perdía el "Black" y quedaba "Xiaomi Shark": ahí
    "Black" no describe el color, es el modelo. La señal es que lo sigue otra
    palabra con mayúscula que no es un color ni un apellido de acabado --
    "Negro Medianoche" sí se quita entero, "Black Shark" no se toca.
    """
    resto = m.string[m.end():]
    # "Black+Decker" y "Black & Decker" son UNA marca: quitarle el color
    # dejaba "Licuadora +Decker".
    #
    # El "+" tiene que ir PEGADO a la palabra siguiente. Con espacio, "+"
    # es el separador de paquete que usan las tiendas de blancos ("Sabanas
    # Trinity King Size Rosa+ Almohada Frosty"), y protegerlo ahí dejaba
    # sin fusionar 106 juegos de sábanas que solo se diferencian en el
    # color. El "&" sí se acepta con espacios: nadie arma un paquete con
    # "&", pero media docena de marcas lo llevan en el nombre.
    if re.match(r"\+[A-Za-zÁÉÍÓÚÑáéíóúñ]", resto) or re.match(r"\s*&\s*[A-ZÁÉÍÓÚÑ]", resto):
        return m.group(0)
    siguiente = re.match(r"\s+([A-Za-zÁÉÍÓÚÑáéíóúñ]+)", resto)
    if siguiente:
        palabra = siguiente.group(1)
        if (palabra[:1].isupper() and palabra.lower() not in _TRAS_COLOR_OK
                and (m.group(0).lower() in _COLORES_EN_INGLES or not _es_titulo(m.string))):
            return m.group(0)
    return " "


# La mayúscula de la palabra siguiente sólo dice algo cuando el nombre está
# escrito en minúscula ("xiaomi Black Shark"). Coppel, Elektra y Mercado
# Libre escriben Cada Palabra Con Mayúscula, y ahí «Colcha Trinity Color
# Negro Matrimonial» perdía el «Negro» como si fuera nombre propio: la ficha
# quedaba sin color y no se juntaba con la Rosa ni con la Gris (medido el
# 26-sep: miles de grupos así). En esos nombres sólo un color en INGLÉS
# seguido de mayúscula se lee como nombre propio (Black Shark, White Rabbit).
_COLORES_EN_INGLES = {
    "black", "white", "blue", "red", "green", "silver", "gold", "pink", "rose",
    "gray", "grey", "purple", "yellow", "orange", "brown", "violet", "navy",
    "midnight", "starlight", "graphite", "space", "cream", "coral", "lime",
}


def _es_titulo(texto):
    palabras = re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]{4,}", texto)
    return len(palabras) >= 3 and sum(w[0].isupper() for w in palabras) >= 0.7 * len(palabras)


def strip_color_from_name(name, labels):
    """Quita del nombre el color, para que la ficha fusionada no se llame por
    uno solo de los colores que contiene.

    Se quitan TODAS las formas del color que aparecen en el grupo ("Salvia",
    "Azul neblina", "Negro medianoche"), porque el nombre que sobrevive es el
    de una ficha y puede traer cualquiera de ellas.

    Si lo que queda es demasiado corto para identificar el producto, se
    devuelve el nombre original: una ficha llamada "Apple iPhone" no le sirve
    a nadie, y un nombre con un color de más es mejor que uno sin modelo.
    """
    fuera = set()
    for lab in labels:
        for parte in [lab] + lab.split():
            if len(parte) >= 3:
                fuera.add(parte.lower())
    # Las etiquetas están canonizadas ("Morado", "Negro titanio") pero el
    # nombre trae la palabra tal como la escribió la tienda ("Violeta",
    # "Titanium Black"). Sin esto, esos nombres se quedaban con el color
    # puesto. Solo se quita la palabra si canoniza a un color que este grupo
    # de verdad tiene: así "Black" se va de un Galaxy negro, pero un modelo
    # que se llamara "Black Shark" no pierde su nombre.
    bases = {l.split()[0].lower() for l in labels if l}
    for palabra, canonico in COLORS_CANON.items():
        if canonico.lower() in bases and re.search(rf"(?<![\w]){re.escape(palabra)}(?![\w])", name, re.I):
            fuera.add(palabra.lower())
    texto = name
    for palabra in sorted(fuera, key=len, reverse=True):
        texto = re.sub(
            rf"(?<![\w]){re.escape(palabra)}(?![\w])",
            lambda m: _quita_si_es_color(m),
            texto,
            flags=re.I,
        )
    texto = _SEPARADORES_RE.sub(" - ", texto)
    texto = _ESPACIOS_RE.sub(" ", texto).strip()
    # Se limpia la cola varias veces: "- Color" deja "-" al quitar "Color".
    for _ in range(3):
        nuevo = _COLA_RE.sub("", texto).strip()
        if nuevo == texto:
            break
        texto = nuevo
    texto = texto.strip(" -–—,:/")
    texto = _ESPACIOS_RE.sub(" ", texto).strip()
    # Menos de 3 palabras o menos de 12 caracteres: se quedó sin producto.
    if len(texto) < 12 or len(texto.split()) < 3:
        return name
    return texto


def variants_of(product, etiqueta=None):
    """Variantes de color de una ficha, ya en el formato nuevo.

    Una ficha que YA venía fusionada por color (colorVariants del formato
    viejo de Mercado Libre, con price/url/sellers sueltos en la variante)
    se convierte acá: cada una de esas variantes era, en los hechos, una
    oferta de Mercado Libre.
    """
    viejas = product.get("colorVariants") or []
    if viejas and not any("offers" in v for v in viejas):
        out = []
        for v in viejas:
            oferta = {"storeId": "mercadolibre", "price": v.get("price"), "url": v.get("url")}
            for campo in ("shippingFee", "sellerCount", "lowestPrice", "sellers", "photo"):
                if v.get(campo) is not None:
                    oferta[campo] = v[campo]
            out.append({"color": v.get("color") or etiqueta or color_label(product), "offers": [oferta]})
        return out
    if viejas:
        return viejas
    return [{"color": etiqueta or color_label(product), "offers": product.get("offers") or []}]


def variant_min_price(variant):
    precios = [o.get("price") for o in (variant.get("offers") or []) if o.get("price")]
    return min(precios) if precios else float("inf")


def firma_telefono(p):
    """Firma de teléfono de la ficha, también para las que no dicen el color
    en el nombre pero SÍ lo traen en colorVariants.

    Las fichas del catálogo de Mercado Libre se llaman «iPhone 17 (256 GB)»
    y los colores van en colorVariants: con signature() a secas quedaban
    fuera de todo grupo, y las fichas de un solo color de las demás tiendas
    (Walmart, Coppel, Telcel...) no tenían dónde entrar. El 26-sep-2026 el
    iPhone 17 de 256 GB estaba repartido en ~40 fichas.
    """
    sig = signature(p)
    if sig:
        return sig
    colores = [v.get("color") for v in p.get("colorVariants") or [] if v.get("color")]
    if not colores:
        return None
    return signature({**p, "name": f"{p.get('name') or ''} {colores[0]}"})


# «Libre» y no decir compañía son lo mismo: un equipo sin compañía se vende
# liberado. Telcel, AT&T, Movistar y Unefon sí separan.
def _compania(c):
    return None if c in (None, "libre") else c


def _partir_por_comodines(ps, firmas):
    """RAM y red sin declarar valen como comodín, pero sólo si en
    el grupo hay a lo sumo UN valor declarado de cada una. Con dos (4G y
    5G, 6 y 8 GB) no se sabe a cuál pertenece el que no dice: se parte por
    el valor declarado y los que no dicen se quedan fuera."""
    grupos = [ps]
    for i in (0, 1):        # ram, red
        nuevos = []
        for g in grupos:
            declarados = {firmas[p["id"]][i] for p in g} - {None}
            if len(declarados) <= 1:
                nuevos.append(g)
                continue
            for val in declarados:
                nuevos.append([p for p in g if firmas[p["id"]][i] == val])
        grupos = nuevos
    return grupos


def _precio_min(p):
    precios = [o.get("price") for o in p.get("offers") or [] if o.get("price")]
    for v in p.get("colorVariants") or []:
        precios += [o.get("price") for o in v.get("offers") or [] if o.get("price")]
    return min(precios) if precios else None


PRECIO_MAX_RATIO = 1.8   # el mismo tope que fusionar_vetado.py


def _sin_precios_raros(ps):
    """Fuera las fichas con precio a 1.8 veces o más de la mediana del grupo:
    un «iPhone 17» a mitad de precio es otra cosa (reacondicionado sin
    decirlo, una funda, un anticipo)."""
    precios = sorted(x for x in (_precio_min(p) for p in ps) if x)
    if not precios:
        return ps
    med = precios[len(precios) // 2]
    return [p for p in ps if _precio_min(p) and med / PRECIO_MAX_RATIO < _precio_min(p) < med * PRECIO_MAX_RATIO]


def _colores_de(p, etiquetas):
    cs = {v.get("color") for v in p.get("colorVariants") or [] if v.get("color")}
    if etiquetas.get(p["id"]):
        cs.add(etiquetas[p["id"]])
    return cs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--informe", help="guarda los grupos (ids y nombres) para revisarlos a mano")
    args = ap.parse_args()

    data = load_catalog()
    grupos = defaultdict(list)
    firmas = {}
    for p in data["products"]:
        if p.get("category") in CATEGORIES:
            sig = firma_telefono(p)
            if not sig:
                continue  # firma incompleta -> no se junta con nadie
            brand, model, storage, ram, _color, carrier, bundle, cond, esim, net = sig
            firmas[p["id"]] = (ram, net)
            # La compañía NO es comodín: sin compañía = liberado, y un Telcel
            # no es el mismo equipo que uno liberado.
            grupos[("tel", brand, model, storage, _compania(carrier), bundle, cond, esim)].append(p)
        else:
            clave = generic_key(p)
            if clave:
                grupos[("gen",) + clave].append(p)

    fusionables = []
    for clave, ps0 in grupos.items():
        if len(ps0) < 2:
            continue
        partes = _partir_por_comodines(ps0, firmas) if clave[0] == "tel" else [ps0]
        for ps in partes:
            ps = _sin_precios_raros(ps)
            if len(ps) < 2:
                continue
            etiquetas = collapse_colors(ps)
            colores = set().union(*(_colores_de(p, etiquetas) for p in ps))
            # Dos fichas del mismo color no son "el mismo equipo en otro color":
            # eso es un duplicado y lo resuelve merge_by_signature.py.
            if len(colores) < 2:
                continue
            # Una ficha sin color (ni en el nombre ni en variantes) no entra.
            ps = [p for p in ps if _colores_de(p, etiquetas)]
            if len(ps) >= 2:
                fusionables.append(sorted(ps, key=id_num))

    drop = set()
    resumen = []
    for ps in fusionables:
        principal = ps[0]
        etiquetas = collapse_colors(ps)
        crudas = []
        for p in ps:
            for v in variants_of(p, etiquetas.get(p["id"])):
                if v.get("color") and v.get("offers"):
                    crudas.append(v)
        canon = collapse_labels({v["color"] for v in crudas})
        variantes = []
        for v in crudas:
            etiqueta = canon.get(v["color"], v["color"])
            clave = etiqueta.lower()
            previa = next((x for x in variantes if x["color"].lower() == clave), None)
            if previa:
                # Mismo color repetido entre dos fichas: se suman las ofertas
                # en una sola variante en vez de listar el color dos veces.
                urls = {o.get("url") for o in previa["offers"]}
                previa["offers"].extend(o for o in v["offers"] if o.get("url") not in urls)
            else:
                variantes.append({"color": etiqueta, "offers": list(v["offers"])})
        for p in ps:
            if p is not principal:
                drop.add(p["id"])
                if not principal.get("photo") and p.get("photo"):
                    principal["photo"] = p["photo"]
                if not principal.get("specs") and p.get("specs"):
                    principal["specs"] = p["specs"]
        if len(variantes) < 2:
            continue
        variantes.sort(key=variant_min_price)
        principal["colorVariants"] = variantes
        # El nombre no puede seguir siendo el de un solo color cuando la
        # ficha ya contiene todos (a pedido del usuario).
        principal["name"] = strip_color_from_name(
            principal["name"], [v["color"] for v in variantes]
        )
        # product.offers se queda con las de la variante más barata: es lo
        # que ve cualquier lector viejo que no sepa de colorVariants.
        principal["offers"] = list(variantes[0]["offers"])
        resumen.append((principal["id"], principal["name"],
                        [v["color"] for v in variantes], principal.get("category")))

    # Limpieza de nombres de fichas que YA estaban fusionadas de una corrida
    # anterior: sin esto, cambiar la regla de limpieza no arreglaba nada de lo
    # ya hecho, porque esas fichas no vuelven a entrar en ningún grupo.
    renombradas = 0
    for p in data["products"]:
        if p["id"] in drop:
            continue
        vs = p.get("colorVariants") or []
        if len(vs) < 2 or not any("offers" in v for v in vs):
            continue
        nuevo = strip_color_from_name(p["name"], [v.get("color") for v in vs if v.get("color")])
        if nuevo != p["name"]:
            p["name"] = nuevo
            renombradas += 1
    print(f"Nombres limpiados de color: {renombradas}")

    por_cat = defaultdict(int)
    for pid, _n, _c, cat in resumen:
        por_cat[cat] += 1
    print(f"Grupos fusionables (mismo equipo, distinto color): {len(resumen)}")
    print("  por categoría: " + ", ".join(
        f"{c} {n}" for c, n in sorted(por_cat.items(), key=lambda kv: -kv[1])))
    print(f"Fichas absorbidas: {len(drop)}")
    for pid, name, colores, _cat in resumen[:25]:
        print(f"   {pid:9} {name[:52]:52} <- {', '.join(colores)[:60]}")
    if len(resumen) > 25:
        print(f"   ... y {len(resumen) - 25} grupos más")

    if args.informe:
        with open(args.informe, "w", encoding="utf-8") as f:
            json.dump([{"queda": ps[0]["id"], "nombre": ps[0]["name"],
                        "fichas": [[p["id"], p["name"], _precio_min(p)] for p in ps]} for ps in fusionables],
                      f, ensure_ascii=False, indent=0)
        print(f"Informe: {args.informe}")
    if args.dry_run:
        print("\n(--dry-run: no se escribió nada)")
        return
    if not drop and not renombradas:
        print("\nNada que fusionar ni que renombrar.")
        return
    data["products"] = [p for p in data["products"] if p["id"] not in drop]
    save_catalog(data)
    # La url de la absorbida pudo estar indexada: su /producto/<id>/ lleva a
    # la que quedó (build_retirados_index.py). Antes se borraban las páginas
    # y la url caía en el 404 genérico.
    registrar_fusiones((p["id"], ps[0]["id"]) for ps in fusionables for p in ps[1:] if p["id"] in drop)
    print(f"\nGuardado. Catálogo: {len(data['products'])} productos; fusiones registradas para redirigir.")


if __name__ == "__main__":
    main()
