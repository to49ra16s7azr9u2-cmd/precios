#!/usr/bin/env python3
"""Saca de Celulares lo que no es un teléfono.

Lo que había: la lista de "iPhone" ordenada por precio abría con un anillo
magnético de $99, un aro para el auto de $101 y un cargador de pared de
$149. Medido sobre las 5,498 fichas de Celulares: 378 vienen de Doto, cuyo
importador puso Celulares/Android o Celulares/iPhone a TODO lo que no supo
ubicar --unidades SSD, gabinetes, secadoras, estufas, minisplits,
masajeadores, fundas y micas--, y 15 accesorios de Amazon ("compatible con
iPhone 15 14 13") pasaron la regla de marca+contexto del clasificador antes
de que tuviera guarda para eso.

Regla de la reparación, en este orden y por ficha:

  1. Si el título nombra un teléfono (marca y modelo, o abre con "Celular",
     "Smartphone", "Combo") y no dice "para <teléfono>" ni "compatible con
     <teléfono>", SE QUEDA donde está, incluida la subcategoría: los combos
     de tienda ("Moto G86 + MotoBuds", "POCO C71 con Bocina") son teléfonos
     aunque el clasificador de Amazon los lea como audífonos, bocinas o
     --por "Moto"-- motocicletas.
  2. El teléfono fijo (Vtech, Steren, Panasonic KX, "inalámbrico DECT") va
     a Celulares/Teléfonos fijos, que existe y no lo alcanzaba nada.
  3. Si el clasificador de capturas lo pone en OTRA categoría, va ahí: es el
     mismo criterio con el que entra todo lo demás.
  4. El accesorio DEL teléfono (funda, mica, anillo, soporte, tarjetero,
     obturador, kit de limpieza, SIM) va a Celulares/Accesorios, que es
     nuevo. No se borra nada: la ficha sigue existiendo, con su página, solo
     que ya no compite con los teléfonos en el ranking.
  5. Lo que el clasificador no reconoce y es línea blanca o de otra familia
     conocida (secadora, estufa, minisplit, masajeador, regulador,
     maquinita) se manda por un mapa corto de palabra -> categoría.
  6. El resto se deja y se lista para revisarlo a mano.

Sin --aplicar solo informa y deja el detalle en
data/reparacion-celulares-<fecha>.tsv.
"""
import argparse
import collections
import datetime
import io
import json
import os
import re
import sys
import tempfile
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import load_catalog, save_catalog  # noqa: E402

CLASIFICADOR = os.path.join(AQUI, "clasificar_captura_perifericos.py")


def norm(t):
    t = unicodedata.normalize("NFKD", (t or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c))


# 1. Es un teléfono (o un combo que lo incluye).
RX_TELEFONO = re.compile(
    # "Purso DE celular", "funda PARA celular": el celular no es la cabeza.
    r'^(?:\S+ ){0,3}(?<!de )(?<!para )(?<!for )(?<!del )(celular|smartphone|combo|telefono (celular|movil|inteligente))\b|'
    r'\b(iphone ?(\d{1,2}|se|air|xr|xs|x)\b|samsung galaxy|galaxy ([asmzf]\d{1,2}|note|z fold|z flip)\b|'
    r'moto ?(g|e|edge|razr) ?\d|motorola (moto|edge|razr|g\d)|redmi (note|\d|a\d)|poco [cfmx]\d|'
    r'xiaomi \d|honor (\d|x\d|magic)|oppo (a\d|reno|find)|realme (\d|c\d|gt|narzo)|vivo [vyx]\d|'
    r'infinix|tecno (spark|camon|pova)|nokia [cg]?\d|zte (blade|axon)|nubia|lanix|\bblu [a-z]\d|'
    r'alcatel \d|tcl \d0|google pixel|pixel \d|huawei (nova|mate|pura|p\d)|one ?plus|nothing phone|'
    r'cat s\d|ulefone|doogee|blackview|oukitel|cubot|umidigi|fossibot|hotwav|\bagm\b|xperia|hisense u\d|'
    r'sonim|\bdoro\b)'
)
# El teléfono sin marca reconocible (SOYES, Melrose, HTC, "teléfono para
# personas mayores"): la ficha técnica en el título lo delata igual que en la
# regla 2 del clasificador. "Dual SIM" es de un teléfono, no de un accesorio.
RX_FICHA_TELEFONO = re.compile(
    r'\d+ ?gb ?\+ ?\d+ ?gb|\d+ ?\+ ?\d+ ?gb\b|\d+ ?gb (de )?ram|\bram\b.{0,15}\brom\b|dual sim|dual nano|'
    r'\bandroid \d+(\.\d+)?\b|desbloqueado|liberado|telefono (celular|movil|inteligente|con tapa|de tapa|basico|senior)|'
    r'smartphone|(personas|adultos) mayores|boton sos|\bsenior\b|\b(flip|cell|feature|rugged) ?phone\b|'
    r'telefono celular|celular .{0,30}(\d+ ?gb|5g|4g|lte)|reacondicionado|\d+ ?/ ?\d+ ?gb\b|'
    # Elektra pega el título sin espacios ("AppleiPhone13Pro128GBAzul").
    r'iphone ?\d{1,2}|\b(64|128|256|512) ?gb\b'
)
# ... salvo que el teléfono aparezca como aquello PARA lo que se vende: el
# teléfono tiene que ser el objeto directo ("para iPhone", "compatible con
# Galaxy S24", "para celular"). Con 25 caracteres de holgura, "Hecho para
# Estados Unidos por Motorola" convertía un Moto G en accesorio.
RX_PARA_TELEFONO = re.compile(
    r'\b(para|compatible (con|for|with)|for|fits?)\b (el |la |los |las |tu |su |mi |un |una )?'
    r'(iphone|celular(es)?|telefonos? (celular|movil|inteligente)|telefonos?\b(?! (fijo|inalambrico|alambrico))|'
    r'smartphones?|samsung|galaxy|xiaomi|redmi|motorola|huawei|honor|oppo|realme|android|movil(es)?)\b'
)
# 2. Teléfono fijo.
RX_FIJO = re.compile(
    r'^(?:\S+ ){0,2}telefonos?\b(?! (celular|movil|inteligente)).{0,45}\b(inalambrico|alambrico|fijo|de linea|de casa|'
    r'de escritorio|dect|\bip\b|\bsip\b|duo|automatico|con (cable|pantalla|teclado)|caller id|identificador de llamadas)|'
    r'\bvtech\b|\bsteren\b.{0,30}\btel\b|panasonic kx|yealink|grandstream|roseta telefonica|\btel-\d{3,4}\b|'
    r'select sound|ctrl expert|\bat&t\b.{0,30}inalambrico|\blm[- ]?\d{4}\b'
)
# 4. Accesorio del teléfono.
RX_ACCESORIO = re.compile(
    r'\bfunda|\bmica|protector (de )?pantalla|cristal templado|vidrio templado|carcasa|\bcase\b|\banillo|'
    r'ring (holder|stand)|\bsoporte|\bholder\b|tarjetero|popsocket|obturador|palo (de )?selfie|'
    r'kit de limpieza|tarjeta sim\b|\bcorrea|\bcordon|\bgrip\b|\bstand\b|\bmount\b|\bcable\b|cargador|adaptador|'
    r'abrazadera|base de montaje|amplificador de senal|bolsa (seca|impermeable|grande impermeable)|lupa de pantalla|'
    r'\bantena\b|cinta adhesiva|estacion usb|\bluz para|lapiz|stylus|bloque de pared|enchufes? de pared|paraguas|'
    r'chip (telcel|express)|telcel chip|\bcarcel\b|enfriador|guantes|bolsa brazo|telefono retro|'
    r'\bpurso\b|\bbolso\b|clip para cinturon|herramientas? de (apertura|reparacion)|corte de pantalla|'
    r'kit de reparacion|espatula|ventosa|pegamento|adhesivo|reemplazo de pantalla|pantalla lcd|digitalizador|ensamblaje'
)
RX_CONTEXTO_TEL = re.compile(
    r'iphone|celular|telefono|smartphone|galaxy|samsung|xiaomi|android|magsafe|lightning|\bmovil\b|usb-?c|'
    # El ecosistema del teléfono (AirPods, Apple Watch, iPad, AirTag) y las
    # marcas que solo hacen accesorios: la funda de iPad de Native Union no
    # tiene mejor cajón que este.
    r'airpods?|apple watch|\bipad\b|airtag|native union|\bbelkin\b|\bzagg\b|prodigee|telcel'
)
# El accesorio que abre el título ("Anillo magnético...", "Bloque de pared
# con cargador...", "iOttie Easy One Touch 5 Soporte...") o que se nombra
# como tal ("funda para", "mica de"). Es lo que separa a un accesorio de un
# teléfono que solo menciona "para Android" en la ficha: el mini smartphone
# SOYES "para Android 8.1" es un teléfono, la funda "para Android" no.
# Sin "batería", "kit", "base" ni "pantalla" en la lista: el Ulefone Armor
# "Smartphone, Batería 22000mAh", el vivo "Photography Kit, 16GB+1TB" y el
# ASHATA "con Base de Carga" son teléfonos que los nombran de paso.
RX_ACCESORIO_FUERTE = re.compile(
    r'^(?:\S+ ){0,3}(funda|mica|protector|carcasa|\bcase\b|anillo|soporte|cargador|cable|adaptador|bloque|'
    r'estuche|bolsa|correa|lapiz|lapices|stylus|antena|luz|lupa|cinta|paraguas|sombra|enchufes?|abrazadera|'
    r'holder|ring|mando|gamepad|obturador|palo|tarjetero|popsocket|brazalete|carcel|enfriador|guantes|'
    r'medidor|microscopio|maquina|impresora|chip)\b|'
    # "soporte de carga", "cargador de mesa" y "cable de carga" son rasgos
    # del teléfono (el Doro senior, el Sonim); solo cuentan con "para" o
    # "universal". La funda, la mica y el protector cuentan siempre...
    # ... y "soporte para" no cuenta en ninguna forma: el Sonim XP10
    # "incluye soporte para teléfono" y el HONIKOVA trae "soporte para
    # descarga 4G". El soporte que se vende solo lo recoge RX_ACCESORIO.
    r'(funda|mica|protector|carcasa|cristal|vidrio) (para|compatible|de|universal)'
)
# La cabeza del título manda: si abre con otro aparato ("Unidad Flash USB C
# de 64 GB compatible con iPhone", "Impresora de fotos para smartphone",
# "Cámara PTZ", "Receptor de 1 DIN"), no es un teléfono por más que la ficha
# mencione GB o "smartphone". Eran los cinco primeros de "iPhone, más
# baratos" después de la primera pasada.
RX_CABEZA_NO_TELEFONO = re.compile(
    r'^(?:\S+ ){0,5}(unidad flash|memoria usb|pendrive|impresora|camara|receptor|estereo|autoestereo|radio|'
    r'proyector|miniproyector|bocina|monitor|tablet|tableta|laptop|reloj|smartwatch|audifonos?|cable|cargador|'
    r'adaptador|bateria externa|power ?bank|control|mando|teclado|mouse|lampara|ventilador|dron|consola|'
    r'walkie|equipo de prueba|amplificador de senal|memoria (ram|ddr)|\bddr\d|punto de acceso|hotspot|'
    r'enrutador|maracas?|shaker|speaker|altavoz|reemplazo|repuesto|pantalla lcd|digitalizador|kit soldador|soldador)\b'
)
# ... salvo cuando vienen de regalo con el teléfono.
RX_REGALO = re.compile(r'(\+|\bcon|incluye|gratis) (funda|mica|protector)|(funda|mica|protector) (de regalo|incluid|gratis)')
# 5. Mapa corto para lo que el clasificador no reconoce (línea blanca de
#    Doto, sobre todo). Primera coincidencia gana.
MAPA = [
    (re.compile(r'\bsecadora'), ("Lavadoras", "Secadoras")),
    (re.compile(r'\blavadora'), ("Lavadoras", "Automáticas")),
    (re.compile(r'\bestufa|\bparrilla'), ("Electrodomésticos", "Estufas")),
    (re.compile(r'microondas'), ("Electrodomésticos", "Microondas")),
    (re.compile(r'\bhorno'), ("Electrodomésticos", "Hornos")),
    (re.compile(r'campana'), ("Electrodomésticos", "Campanas de cocina")),
    (re.compile(r'congelador|refrigerador'), ("Refrigeradores", "Refrigeradores")),
    (re.compile(r'\bolla\b|jarra electrica|procesador de alimentos|licuadora|tostador|batidora'), ("Electrodomésticos", "Pequeños electrodomésticos de cocina")),
    (re.compile(r'dispensador de agua'), ("Electrodomésticos", "Purificadores de agua")),
    (re.compile(r'affresh|limpiador de'), ("Electrodomésticos", "Otros")),
    (re.compile(r'cuchillos?\b'), ("Cocina y comedor", "Utensilios de cocina")),
    (re.compile(r'wi-?fi en malla|\bdeco m\d|mesh'), ("Redes", "Routers")),
    (re.compile(r'tarjeta de video|geforce|radeon'), ("Componentes y accesorios de PC", "Componentes")),
    (re.compile(r'bossa|\bbocina'), ("Bocinas", "Mediana")),
    (re.compile(r'hoverboard|elgato|conectores'), ("Otros", "Varios")),
    (re.compile(r'minisplit|mini split|aire acondicionado'), ("Climatización", "Aires acondicionados")),
    (re.compile(r'masajeador|pistola .{0,12}masaje'), ("Salud", "Masajeadores")),
    # El "radio de coche Android para Mazda" es la unidad principal del
    # auto, no un radio portátil: va antes que la regla de radios.
    (re.compile(r'\breceptor\b|\bestereo\b|autoestereo|\bkenwood\b|pioneer (sph|deh|mvh|avh)|\b[12] ?din\b|'
                r'radio (de |para |del )?(coche|auto|carro|automovil)|carplay|android auto|doble din|head ?unit'), ("Autos, bicicletas y motos", "Estéreos para auto")),
    (re.compile(r'\bregulador|no ?break|\bups\b'), ("Otros", "Inversores")),
    (re.compile(r'\bmonitor\b|pantalla led de \d+|led-monitor|lcd monitor'), ("Monitores", "Oficina")),
    (re.compile(r'play ?station|\bps[45]\b|\bxbox\b|nintendo switch'), ("Videojuegos", "Software")),
    (re.compile(r'camara de vigilancia|\btapo\b'), ("Cámaras de seguridad", "Cámaras interiores")),
    (re.compile(r'adaptador inalambrico usb|wifi usb'), ("Componentes y accesorios de PC", "Accesorios")),
    (re.compile(r'\bcareta\b'), ("Salud", "Salud")),
    # Lo que la búsqueda "celular" de Amazon trajo por la palabra y no es
    # de teléfonos (paredes celulares, apoyo celular, redes celulares):
    # fuera de Celulares antes que nada, aunque sea a Varios.
    (re.compile(r'detector emf|arcilla|mezclador de vortice|paredes celulares|suplemento|medidor de energia|microscopio'), ("Otros", "Varios")),
    (re.compile(r'maquinita|\barcade\b'), ("Juguetes y bebés", "Juegos arcade")),
    (re.compile(r'\brouter\b'), ("Redes", "Routers")),
    (re.compile(r'skullcandy|\bjlab\b|\bjbuds\b|cascos? over-?ear'), ("Audífonos", None)),
    (re.compile(r'cable .{0,30}(hdmi|alargue|extension|\brgb\b|\bpin\b|sata)'), ("Componentes y accesorios de PC", "Accesorios")),
]
# Antes que el clasificador: lo que éste confunde con seguridad. El
# masajeador "de percusión" cae en Instrumentos musicales/Baterías, la barra
# de sonido en Domótica, y la silla reclinable en Cocina y comedor.
PRIORIDAD = [
    (re.compile(r'masajeador|pistola .{0,12}masaje'), ("Salud", "Masajeadores")),
    # El "radio de coche Android para Mazda" es la unidad principal del
    # auto, no un radio portátil: va antes que la regla de radios.
    (re.compile(r'\breceptor\b|\bestereo\b|autoestereo|\bkenwood\b|pioneer (sph|deh|mvh|avh)|\b[12] ?din\b|'
                r'radio (de |para |del )?(coche|auto|carro|automovil)|carplay|android auto|doble din|head ?unit'), ("Autos, bicicletas y motos", "Estéreos para auto")),
    (re.compile(r'barra de sonido|soundbar'), ("Bocinas", "Barras de sonido")),
    (re.compile(r'silla de ruedas|sillas de ruedas|scooter|patinete de movilidad|elevacion de silla|almohadilla de asiento|movilidad'), ("Salud", "Movilidad")),
    (re.compile(r'sillas? de camping|tumbona'), ("Deportes y fitness", "Campismo")),
    (re.compile(r'\bsillas?\b|\bsillon|asiento simulador'), ("Muebles", "Sillas")),
    (re.compile(r'^(?:\S+ ){0,3}radios?\b'), ("Otros", "Radios")),
    (re.compile(r'memoria (ram|ddr)|\bddr\d|\bsodimm\b'), ("Componentes y accesorios de PC", "Memoria RAM")),
    (re.compile(r'punto de acceso|hotspot|enrutador|\bmifi\b'), ("Redes", "Access points")),
    (re.compile(r'maracas?|shaker|sonajero'), ("Instrumentos musicales", "Percusión")),
    (re.compile(r'\bspeaker|altavoz'), ("Bocinas", "Mediana")),
    (re.compile(r'soldador|estacion de soldadura'), ("Herramientas", "Soldadura")),
    (re.compile(r'meta quest|\boculus\b'), ("Videojuegos", "Consolas")),
    (re.compile(r'impresora|\binstax\b'), ("Impresoras", None)),
    (re.compile(r'unidad flash|memoria usb|pendrive'), ("Almacenamiento", "Memorias USB")),
    (re.compile(r'camara ptz'), ("Cámaras de seguridad", "Cámaras PTZ")),
    (re.compile(r'^(?:\S+ ){0,3}(mini )?camara\b'), ("Cámaras de seguridad", "Otros")),
    (re.compile(r'videou?j?uego'), ("Videojuegos", "Software")),
    (re.compile(r'airpods? (pro|max|\d)'), ("Audífonos", "Earbuds inalámbricos")),
    (re.compile(r'walkie|radio (poc|de dos vias|bidireccional)|talkabout'), ("Otros", "Radios")),
    (re.compile(r'bateria magnetic|power ?bank magnetic'), ("Baterías portátiles", None)),
    (re.compile(r'medidor|microscopio|detector|mezclador|arcilla|suplemento|kit escolar|microsoft 365'), ("Otros", "Varios")),
]


def clasificar_en_proceso(fichas):
    """Corre el clasificador de capturas sobre las fichas como si fueran una
    captura. Es un script (lee sys.argv al importarse), así que se ejecuta
    con argv y __file__ puestos a mano en vez de importarlo."""
    captura = [{"asin": p["id"], "title": p["name"], "price": (p["offers"][0].get("price") if p["offers"] else None),
                "photo": p.get("photo"), "url": (p["offers"][0].get("url") if p["offers"] else "") or ""}
               for p in fichas]
    tmp_in = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(captura, tmp_in, ensure_ascii=False); tmp_in.close()
    tmp_out = tmp_in.name + ".alta.json"
    argv_antes, stdout_antes = sys.argv, sys.stdout
    sys.argv = ["clasificar", tmp_in.name, tmp_out]
    sys.stdout = io.StringIO()
    try:
        g = {"__name__": "__main__", "__file__": CLASIFICADOR}
        exec(compile(open(CLASIFICADOR, encoding="utf-8").read(), CLASIFICADOR, "exec"), g)
    finally:
        sys.argv, sys.stdout = argv_antes, stdout_antes
        os.unlink(tmp_in.name)
    alta = {a["asin"]: (a["category"], a["subcategory"], a.get("image")) for a in json.load(open(tmp_out, encoding="utf-8"))}
    os.unlink(tmp_out)
    fuera = {it["asin"]: motivo for it, motivo in g["fuera"]}
    return alta, fuera


def icono_de(data, cat, sub):
    c = next((x for x in data["categories"] if x["id"] == cat), None)
    if not c:
        return "box"
    s = next((x for x in c.get("subcategories") or [] if x["id"] == sub), None) if sub else None
    return (s or {}).get("icon") or c.get("icon") or "box"


def decidir(p, alta, fuera):
    """-> (accion, categoría nueva, subcategoría nueva) o None si se queda."""
    tn = norm(p["name"])
    cat, sub = p["category"], p.get("subcategory")
    para = bool(RX_PARA_TELEFONO.search(tn))
    ficha = bool(RX_FICHA_TELEFONO.search(tn))
    fuerte = bool(RX_ACCESORIO_FUERTE.search(tn)) and not RX_REGALO.search(tn)
    # Teléfono: nombra marca y modelo o trae ficha técnica, no abre con un
    # accesorio, y si dice "para <teléfono>" es porque además trae la ficha
    # (el mini smartphone "para Android 8.1"), no porque sea la funda.
    # Con "para <teléfono>" en el título, "smartphone" a secas ya no alcanza
    # como ficha (el cable "para smartphone" la tiene): hace falta un dato
    # duro --GB, RAM, dual SIM, desbloqueado.
    ficha_dura = bool(re.search(r'\d+ ?gb|\bram\b|dual sim|desbloqueado|liberado|reacondicionado|(personas|adultos) mayores', tn))
    es_telefono = ((bool(RX_TELEFONO.search(tn)) or ficha) and not fuerte and not (para and not ficha_dura)
                   and not RX_CABEZA_NO_TELEFONO.search(tn))
    if RX_FIJO.search(tn) and not RX_TELEFONO.search(tn):
        return ("FIJO", "Celulares", "Teléfonos fijos") if sub != "Teléfonos fijos" else None
    # Lo inequívoco del mapa de prioridad va ANTES que la prueba de teléfono,
    # salvo que el título abra con el teléfono: la impresora "para iPhone 16"
    # y el receptor de auto "con control iPhone" nombran un modelo, pero el
    # producto es lo que abre el título.
    abre_con_telefono = bool(re.match(r'^(?:\S+ ){0,2}', tn)) and bool(RX_TELEFONO.match(tn))
    if not abre_con_telefono:
        for rx, (c2, s2) in PRIORIDAD:
            if rx.search(tn):
                return ("MAPA", c2, s2)
    # Debajo de $300 no hay teléfono, ni el básico de 2G: lo que está en
    # Celulares a ese precio sin un dato duro de ficha (GB, RAM, SIM,
    # desbloqueado) es un accesorio, diga "celular" donde diga.
    precios = [o["price"] for o in p["offers"] if o.get("price")]
    if precios and min(precios) < 300 and not ficha_dura:
        return ("ACCESORIO", "Celulares", "Accesorios") if sub != "Accesorios" else None
    if es_telefono:
        return None
    clas = alta.get(p["id"])
    # El cable y el cargador tienen su categoría y el clasificador la conoce;
    # el resto de accesorios del teléfono se queda en Celulares/Accesorios
    # AUNQUE el clasificador les vea otra cosa (el anillo "para celular auto"
    # iba a Autos, la abrazadera "de bicicleta para celular" a Bicicletas).
    if clas and clas[0] in ("Cargadores y adaptadores", "Herramientas"):
        return ("CLASIFICADOR", clas[0], clas[1])
    if (RX_ACCESORIO.search(tn) and RX_CONTEXTO_TEL.search(tn)) or para or (fuerte and RX_CONTEXTO_TEL.search(tn)):
        return ("ACCESORIO", "Celulares", "Accesorios") if sub != "Accesorios" else None
    if clas and clas[0] != "Celulares":
        return ("CLASIFICADOR", clas[0], clas[1])
    m = re.search(r'\bbateria\b.{0,30}?(\d{1,2}[.,]?\d{3}) ?mah|power ?bank', tn)
    if m:
        mah = int(re.sub(r'\D', '', m.group(1))) if m.group(1) else None
        tramo = (None if mah is None else "Hasta 10,000 mAh" if mah <= 10000
                 else "10,000 a 20,000 mAh" if mah <= 20000 else "Más de 20,000 mAh")
        return ("MAPA", "Baterías portátiles", tramo)
    for rx, (c2, s2) in MAPA:
        if rx.search(tn):
            if c2 == "Audífonos":
                s2 = "Earbuds inalámbricos" if re.search(r'inalambric|bluetooth|\btws\b', tn) else "Earbuds con cable"
            return ("MAPA", c2, s2)
    if clas is None and p["id"] in fuera:
        return ("REVISAR", cat, sub)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()
    data = load_catalog()
    fichas = [p for p in data["products"] if p["category"] == "Celulares"]
    alta, fuera = clasificar_en_proceso(fichas)
    cuenta = collections.Counter()
    destinos = collections.Counter()
    lineas = []
    for p in fichas:
        d = decidir(p, alta, fuera)
        if not d:
            cuenta["se queda"] += 1
            continue
        accion, c2, s2 = d
        tiendas = ",".join(sorted({o["storeId"] for o in p["offers"]}))
        cuenta[accion] += 1
        if accion != "REVISAR":
            destinos[(accion, c2, s2)] += 1
        lineas.append(f"{accion}\t{p['id']}\t{tiendas}\t{p['category']}/{p.get('subcategory')}\t{c2}/{s2}\t{fuera.get(p['id'], '')}\t{p['name'][:100]}")
        if args.aplicar and accion != "REVISAR":
            p["category"], p["subcategory"] = c2, s2
            p["image"] = icono_de(data, c2, s2)
    hoy = datetime.date.today().isoformat()
    ruta = os.path.join(AQUI, "..", "data", f"reparacion-celulares-{hoy}.tsv")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("accion\tid\ttiendas\tde\ta\tmotivo_fuera\tnombre\n" + "\n".join(sorted(lineas)) + "\n")
    print(f"Fichas de Celulares: {len(fichas)}")
    for k, n in cuenta.most_common():
        print(f"  {n:5d}  {k}")
    print("\nDestinos:")
    for (a, c, s), n in destinos.most_common():
        print(f"  {n:5d}  {a:12s} -> {c} / {s}")
    print(f"\nDetalle en {os.path.relpath(ruta, os.getcwd())}")
    if args.aplicar:
        save_catalog(data)
        print("Catálogo guardado.")
    else:
        print("(sin --aplicar no se guarda nada)")


if __name__ == "__main__":
    main()
