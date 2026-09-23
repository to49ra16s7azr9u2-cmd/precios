"""Qué fichas no deberían encabezar un "Precio: menor a mayor".

EL PROBLEMA
-----------
Al ordenar una categoría por precio, arriba no quedaban los productos más
baratos sino los errores más baratos: medido el 23 de septiembre de 2026,
Laptops abría con un tapete para trasplantar plantas de $120 y una
minicámara, Refrigeradores con raspadores de hielo e imanes, Lavadoras con
bolas de lana para la secadora. Se leía como si el orden trajera productos
de otras categorías.

POR QUÉ NO BASTA CON EL PRECIO
------------------------------
generate_seo_pages.py ya descartaba lo que vale menos del 15% de la mediana
de su subcategoría. Eso atrapa el imán de $149 entre refrigeradores de
miles, pero también la bocina Bluetooth de $179 que sí es una bocina (hay
14,558 fichas bajo ese piso y la mayoría son productos baratos de verdad).
Quien ordena por "más barato" quiere ver esa bocina.

LA SEGUNDA SEÑAL: CÓMO ARRANCA EL NOMBRE
---------------------------------------
Un producto se nombra por lo que es ("Bocina Portátil Bluetooth GLB-5023");
un accesorio o un error se nombra por otra cosa ("Cajón de madera para
bocinas", "Imanes para refrigerador"). El vocabulario de cada subcategoría
sale del catálogo mismo: las palabras con que abren los nombres de sus
fichas de precio normal (las que aparecen en al menos el 5% de ellas). Lo
que va después de "para", "for" o "compatible" no cuenta: ahí el producto
es un complemento, no el sujeto.

Una ficha es atípica cuando cumple LAS DOS: precio bajo el piso de su
subcategoría Y un arranque de nombre sin ninguna palabra de ese
vocabulario. No se borra ni se esconde: la SPA la manda al final del orden
por precio y /barato/ no la pone en su lista.
"""
import collections
import re
import unicodedata

from roles_subcategorias import es_producto

UMBRAL_ATIPICO = float(__import__("os").environ.get("ATIPICOS_UMBRAL", 0.15))
MIN_PARA_MEDIANA = 8
FRACCION_VOCABULARIO = 0.05
MIN_VOCABULARIO = 3
# Cuántas veces más frecuente tiene que ser la palabra en la subcategoría
# que en el catálogo entero para contar como suya. Sin esto "pulgadas" y
# "portátil" eran vocabulario de Laptops, y una mesa de camping de 69
# pulgadas o una hoja de sierra "portátil" pasaban por laptops.
LIFT_MIN = float(__import__("os").environ.get("ATIPICOS_LIFT", 3))
LIFT_FUERTE = 60
PALABRAS_CABEZA = int(__import__("os").environ.get("ATIPICOS_N", 2))

_VACIAS = set("""
de del la las el los y e o u con sin para por en a al the and for with of
set kit juego pack paquete pieza piezas pzs pz pcs unidades unidad
generico generica generic nuevo nueva original venta internacional marca
color tipo modelo estilo mini gran grande pequeno pequena plus pro max
ultra premium profesional universal compatible
""".split())
# El producto nombrado como tema de otra cosa: la laptop de juguete, el Funko
# de una serie de televisión, la temporada en DVD. Empiezan con la palabra
# correcta ("Laptop Vtech Kidi Secrets", "Serie de TV Scooby-Doo"), así que
# el vocabulario no los separa; el precio imposible más una de estas
# palabras sí.
_JUGUETE = re.compile(
    r"\b(juguete|juguetes|toy|toys|infantil|para ninos|para ninas|didactic[ao]|"
    r"kidi|vtech|fisher[ -]price|f-p|funko|figura|peluche|llavero|miniatura|"
    r"replica|disfraz|dvd|blu-?ray|temporada|temporadas|serie de tv|monster high|"
    r"barbie|lego|playmobil|hot wheels|montessori)\b")

# Donde el juguete ES el producto, esas palabras no dicen nada.
_CATEGORIAS_DE_JUGUETE = {"Juguetes y bebés", "Juegos de mesa", "Mascotas", "Videojuegos", "Libros"}

# Las pocas palabras de dos letras que sí nombran un producto.
_CORTAS = {"tv", "pc"}
_CORTE = re.compile(r"\b(?:para|for|compatible|compatibles|p/|repuesto de|refaccion para)\b")


def _t(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def _raiz(w):
    for suf in ("es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[: -len(suf)]
    return w


def cabeza(p):
    """Las primeras palabras con contenido del nombre, antes de "para", en orden.

    Cada una va como (raíz, viene_tras_de): en "Separadores de refrigerador"
    la segunda palabra es complemento de la primera, no el sujeto.
    """
    marca = set(re.findall(r"[a-z0-9]+", _t(p.get("brand"))))
    texto = _CORTE.split(_t(p.get("name")), 1)[0]
    salida = []
    tras_de = False
    for w in re.findall(r"[a-zñ]{2,}", texto):
        if w in ("de", "del"):
            tras_de = True
            continue
        if (len(w) > 2 or w in _CORTAS) and w not in _VACIAS and w not in marca:
            salida.append((_raiz(w), tras_de))
            if len(salida) >= PALABRAS_CABEZA:
                break
        tras_de = False
    return salida


def _precio(p):
    xs = [o.get("price") for o in p.get("offers") or [] if o.get("price")]
    return min(xs) if xs else None


def _es_de_aqui(cab, lift):
    """¿El nombre arranca como los productos de la subcategoría?

    La primera palabra es casi siempre el sustantivo ("Hoja de sierra...",
    "Laptop HP..."), así que basta con que ELLA sea del vocabulario. La
    segunda sólo cuenta si es muy propia de la subcategoría (lift alto):
    salva "Acouto Laptop..." sin dejar pasar "Parque portátil para
    mascotas" por la palabra "portátil": los sustantivos propios de una
    subcategoría ("laptop", "televisor", "refrigerador") pasan de 100, los
    modificadores comunes ("pulgadas", "portátil", "pantalla") no llegan a
    60. Y no cuenta si viene tras "de": en "Separadores de refrigerador" el
    refrigerador es el complemento.
    """
    if not cab:
        return False
    if lift.get(cab[0][0], 0) >= LIFT_MIN:
        return True
    return any(lift.get(w, 0) >= LIFT_FUERTE for w, tras_de in cab[1:] if not tras_de)


def vocabularios(products, excluir=()):
    """{(categoría, subcategoría): {palabra: lift}} con el vocabulario de
    arranque de cada subcategoría, sacado de sus fichas (menos `excluir`)."""
    total = 0
    global_df = collections.Counter()
    por_sub = collections.defaultdict(collections.Counter)
    n_sub = collections.Counter()
    for p in products:
        c = {w for w, _ in cabeza(p)}
        global_df.update(c)
        total += 1
        if p["id"] in excluir:
            continue
        k = (p.get("category"), p.get("subcategory"))
        por_sub[k].update(c)
        n_sub[k] += 1
    salida = {}
    for k, frecuencia in por_sub.items():
        n = n_sub[k]
        minimo = max(MIN_VOCABULARIO, FRACCION_VOCABULARIO * n)
        salida[k] = {
            w: (c / n) / (global_df[w] / total)
            for w, c in frecuencia.items() if c >= minimo
        }
    return salida


def es_de_aqui(p, lift):
    return _es_de_aqui(cabeza(p), lift)


def marcar(products):
    """Devuelve el conjunto de ids atípicos (ver el docstring del módulo)."""
    por_sub = collections.defaultdict(list)
    for p in products:
        sub = p.get("subcategory")
        if not sub or sub == "Accesorios" or not es_producto(p.get("category"), sub):
            continue
        pr = _precio(p)
        if pr:
            por_sub[(p.get("category"), sub)].append((pr, p))
    total = 0
    global_df = collections.Counter()
    cabezas = {}
    for p in products:
        c = cabeza(p)
        cabezas[p["id"]] = c
        global_df.update({w for w, _ in c})
        total += 1
    atipicos = set()
    for fichas in por_sub.values():
        if len(fichas) < MIN_PARA_MEDIANA:
            continue
        precios = sorted(pr for pr, _ in fichas)
        piso = precios[len(precios) // 2] * UMBRAL_ATIPICO
        bajas = [p for pr, p in fichas if pr < piso]
        if not bajas:
            continue
        normales = [p for pr, p in fichas if pr >= piso]
        frecuencia = collections.Counter()
        for p in normales:
            frecuencia.update({w for w, _ in cabezas[p["id"]]})
        minimo = max(MIN_VOCABULARIO, FRACCION_VOCABULARIO * len(normales))
        lift = {
            w: (n / len(normales)) / (global_df[w] / total)
            for w, n in frecuencia.items() if n >= minimo
        }
        for p in bajas:
            if not _es_de_aqui(cabezas[p["id"]], lift) or (
                p.get("category") not in _CATEGORIAS_DE_JUGUETE and _JUGUETE.search(_t(p.get("name")))
            ):
                atipicos.add(p["id"])
    return atipicos
