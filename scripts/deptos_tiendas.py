"""Lo que el departamento de la tienda sabe y el título no.

POR QUÉ
-------
importar_captura_tienda.py clasifica por el título, y para casi todas las
tiendas es lo correcto: el departamento que ponen es una bolsa mezclada
(«Herramientas Eléctricas» lleno de autopartes). Pero Farmatodo y DelSol
publican un árbol de categorías fino y limpio, y el título de una farmacia
(«Sensodyne Pasta Dental Rapido Alivio 100 Gr») no dice la palabra que el
clasificador busca: la pasta dental caía en Cremas faciales, el enjuague en
Tarros y frascos y el «mouse» de Pantene (un shampoo) en Mouse.

DOS USOS
--------
FIJOS: departamentos que son una sola cosa. El producto va directo a esa
subcategoría, sin pasar por el clasificador (que además descartaba por
«FUERA» las vendas, los pañales y las toallas femeninas, que sí se comparan).

PERMITIDAS: departamentos que no son una sola cosa pero sí un solo mundo
(belleza, juguetes). Si el clasificador manda el producto a otra categoría
del sitio, el título lo engañó: se descarta en vez de dar de alta un error.

Los departamentos se comparan en minúsculas y sin acentos.
"""
import re
import unicodedata


def norm(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c)).strip()


BELLEZA, SALUD, SUPL, BEBES, LIMP = ("Belleza y cuidado personal", "Salud", "Suplementos", "Bebés",
                                     "Limpieza y hogar")

# (regex sobre el departamento normalizado, categoría, subcategoría)
FIJOS = {
    "farmatodo": [
        (r"^desodorantes$", BELLEZA, "Desodorantes"),
        (r"^(proteccion solar|bloqueador solar)$", BELLEZA, "Protección solar"),
        (r"^(shampoo|shampoo y jabon)$", BELLEZA, "Shampoo"),
        (r"^acondicionador$", BELLEZA, "Acondicionadores"),
        (r"^(anticaspa|anticaida|tratamiento capilar|crecimiento de pestanas)$", BELLEZA, "Tratamientos y mascarillas capilares"),
        (r"^tintes$", BELLEZA, "Tintes para cabello"),
        (r"^(gel y ceras|mousse|crema para peinar)$", BELLEZA, "Ceras, geles y fijadores"),
        (r"^(crema dental|gel dentifrico|enjuague bucal|cepillo dental|hilo dental|cuidado dental|limpiador dental|"
         r"spray para encias|ortodoncia|pegamentos para dentadura|almohadillas para dentadura)$", SALUD, "Cuidado dental"),
        (r"^(jabon|bano)$", BELLEZA, "Jabones y geles de baño"),
        (r"^balsamo labial$", BELLEZA, "Bálsamos labiales"),
        (r"^(rastrillos)$", BELLEZA, "Rastrillos y navajas"),
        (r"^crema facial$", BELLEZA, "Cremas faciales"),
        (r"^serum$", BELLEZA, "Sérums faciales"),
        (r"^contorno de ojos$", BELLEZA, "Contorno de ojos y labios"),
        (r"^(desmaquillante y agua micelar|desmaquillantes|toallas desmaquillantes)$", BELLEZA, "Limpiadores y tónicos"),
        (r"^maquillaje$", BELLEZA, "Maquillaje"),
        (r"^(quita esmaltes|manicure y pedicure|corta unas)$", BELLEZA, "Uñas"),
        (r"^locion$", BELLEZA, "Perfumes"),
        (r"^(crema manos|crema corporal|cremas y lociones|antiestrias|crema para cicatrices)$", BELLEZA, "Cremas y lociones corporales"),
        (r"^cremas depiladoras$", BELLEZA, "Depilación"),
        (r"^(toallas femeninas|toalla femenina .*|tampones|pantiprotectores|higiene intima|calzon desechable)$",
         BELLEZA, "Cuidado personal"),
        (r"^(repelentes|repelente bebe)$", LIMP, "Insecticidas y repelentes"),
        (r"^(panal adulto|toallas para incontinencia|panales de cama)$", SALUD, "Salud"),
        (r"^(etapa \d.*|panal(es)? .*|calzon entrenador|toallitas humedas)$", BEBES, "Pañales y cambio"),
        (r"^(biberones y mamilas|escobillon para biberones)$", BEBES, "Biberones"),
        (r"^chupones y mordederas$", BEBES, "Chupones y mordederas"),
        (r"^(vasos entrenadores|extractor de leche|pezoneras|protector de lactancia)$", BEBES, "Alimentación y lactancia"),
        (r"^(vendas y gasas|parches y telas adhesivas|algodones, torundas, pads|otros accesorios de curacion|"
         r"hisopos|abatelenguas|cubrebocas|guantes|ortopedia|otros accesorios medicos|jeringas de perilla|aspirador nasal)$",
         SALUD, "Salud"),
        (r"^termometros$", SALUD, "Termómetros"),
        (r"^baumanometros$", SALUD, "Baumanómetros"),
        (r"^(glucometros|medidores de glucosa|tiras y lancetas|tiras de diagnostico de glucosa)$", SALUD, "Glucómetros"),
        (r"^oximetros$", SALUD, "Oxímetros"),
        (r"^nebulizadores$", SALUD, "Nebulizadores"),
        (r"^multivitaminicos$", SUPL, "Multivitamínicos"),
        (r"^vitamina c$", SUPL, "Vitamina C"),
        (r"^vitamina d$", SUPL, "Vitamina D y K"),
        (r"^complejo b$", SUPL, "Complejo B y biotina"),
        (r"^colageno$", SUPL, "Colágeno"),
        (r"^calcio$", SUPL, "Calcio"),
        (r"^vitamina a$", SUPL, "Otras vitaminas"),
        (r"^sistema inmune$", SUPL, "Sistema inmune"),
        (r"^rendimiento mental$", SUPL, "Memoria y concentración"),
    ],
    "delsol": [],
}

# departamento -> categorías del sitio en las que puede caer
_BELLEZA_D = (r"^(cuidado-del-cabello|rostro|ojos|labiales|cuidado-de-la-piel|higiene-personal|higiene-personal-hombres|"
              r"cuidado-personal-ella|fragancias|unas|accesorios-belleza|accesorios-de-belleza|talcos|bano-e-higiene)$")
_JUGUETES_D = (r"^(munecas-y-accesorios|figuras-de-accion|peluches|montables|lanzadores|carros-y-autopistas|"
               r"jugueteria-bebes|juegos-exterior|control-remoto-radio-control|casas-cocinas|juegos-de-mesa|"
               r"coleccionables)$")
PERMITIDAS = {
    "delsol": [
        (_BELLEZA_D, {BELLEZA, SALUD, LIMP}),
        (_JUGUETES_D, {"Juguetes", "Juegos de mesa", BEBES, "Bicicletas y movilidad", "Deportes y fitness",
                       "Videojuegos", "Papelería y oficina", "Decoración de hogar y jardín"}),
        (r"^(bicicletas-y-scooters|patines-patinetas)$", {"Bicicletas y movilidad", "Deportes y fitness", "Juguetes"}),
    ],
    "farmatodo": [
        (r".", {BELLEZA, SALUD, SUPL, BEBES, LIMP}),
    ],
}


# Un suplemento mal colgado de otro departamento («Revita.Sod Suplemento
# Alimenticio» estaba en Anticaída): el título manda y lo decide el clasificador.
_SUPLEMENTO_TITULO = re.compile(r"suplemento|vitamin|multivit|colageno|omega ?3|probiotic", re.I)


def fijar(tienda, dept, titulo=""):
    """(categoría, subcategoría) si el departamento decide solo; si no, None."""
    d = norm(dept)
    if _SUPLEMENTO_TITULO.search(norm(titulo)) and not re.search(r"vitamin|multivit|colageno|calcio|sistema inmune|rendimiento", d):
        return None
    for rx, cat, sub in FIJOS.get(tienda, ()):
        if re.search(rx, d):
            return cat, sub
    return None


def permitida(tienda, dept, categoria):
    """False si el departamento fija un mundo al que `categoria` no pertenece."""
    d = norm(dept)
    for rx, cats in PERMITIDAS.get(tienda, ()):
        if re.search(rx, d):
            return categoria in cats
    return True
