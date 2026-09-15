#!/usr/bin/env python3
"""Vacía las subcategorías comodín ("Otros", "Varios") repartiendo sus fichas
en subcategorías que dicen algo.

POR QUÉ
-------
Una subcategoría llamada "Otros" no ayuda a nadie: el filtro la ofrece, el
comprador la abre y encuentra mil cosas que no tienen relación. En el catálogo
había 16,554 fichas así (8.5%), y la más grande, "Otros / Varios" con 3,926,
resultó ser sobre todo cocina y mesa -- botellas, termos, vasos, vajilla,
sartenes -- que no es "otros" en ningún sentido: es una categoría propia que
al catálogo le faltaba.

QUÉ HACE
--------
Mueve fichas entre categorías y subcategorías siguiendo GRUPOS. No borra
ningún producto: lo que no reconoce se queda donde está.

Es idempotente y se puede correr las veces que haga falta.

USO
---
    python3 scripts/reclasificar_otros.py --dry-run
    python3 scripts/reclasificar_otros.py
"""
import argparse
import collections
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog  # noqa: E402


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s)


# (categoría origen, subcategoría origen) -> [(regex, categoría destino, subcategoría destino)]
# El orden manda: lo más específico primero.
COCINA = "Cocina y comedor"
GRUPOS = {
    ("Otros", "Varios"): [
        # El soporte de celular no es cocina ni "varios": es un accesorio con
        # forma propia, y son 745.
        (r"\bsoporte\b.{0,30}(telefono|celular|tablet|tableta|movil|ipad)|"
         r"\b(soporte|base|sujetador|montaje)\b.{0,25}(telefono|celular|tablet|tableta)|"
         r"selfie stick|tripie para (celular|telefono)|\bgooseneck\b",
         "Otros", "Soportes para dispositivos"),
        (r"\b(botella|termo|termos|hydro ?flask|cantimplora|shaker|tumbler|"
         r"botellas|garrafon)\b", COCINA, "Botellas y termos"),
        (r"\b(vaso|vasos|taza|tazas|\bmug\b|jarra|jarras|copa|copas|tarro)\b",
         COCINA, "Vasos y tazas"),
        (r"\b(plato|platos|vajilla|tazon|tazones|\bbowl\b|cubiertos|"
         r"cuchara|cucharas|tenedor|cuchillo de mesa|charola|bandeja de servir)\b",
         COCINA, "Vajilla"),
        (r"\b(sarten|sartenes|olla|ollas|cacerola|budinera|vaporera|comal|"
         r"\bwok\b|freidora de aceite|parrilla de mesa)\b", COCINA, "Ollas y sartenes"),
        (r"\b(utensilio|espatula|batidor|colador|rallador|tabla de (picar|cortar)|"
         r"pinzas de cocina|cucharon|abrelatas|pelador|exprimidor manual|"
         r"raspador|molde|rodillo|mortero)\b", COCINA, "Utensilios de cocina"),
        (r"\b(contenedor|contenedores|tupper|frasco|frascos|hermetico|"
         r"recipiente|recipientes|tapas?\b.{0,20}(bandeja|envase)|bolsa para congelar)\b",
         COCINA, "Contenedores"),
        (r"\b(escurridor|especiero|portacuchillos|dispensador de (cereal|agua|jabon)|"
         r"organizador de (cocina|refrigerador|utensilios|alacena|gabinete)|"
         r"estante para microondas|portarrollos)\b", COCINA, "Organización de cocina"),
        # Lo que quedó y sí nombra algo de cocina, aunque sea de refilón.
        (r"\b(cocina|refrigerador|microondas|horno|alacena|despensa|mesa|comedor)\b",
         COCINA, "Organización de cocina"),
    ],
    # La arracada es un arete y el dije un dije: "Otros" los escondía a los dos.
    ("Joyería y bisutería", "Otros"): [
        (r"\b(arracada|arracadas|broquel|broqueles|arete|aretes|pendiente)\b",
         "Joyería y bisutería", "Aretes"),
        (r"\b(dije|dijes|charm|charms|separador|dijes? colgante)\b",
         "Joyería y bisutería", "Dijes y charms"),
        (r"\b(cadena|cadenas|collar|collares|gargantilla|medalla)\b",
         "Joyería y bisutería", "Collares"),
        (r"\b(pulsera|pulseras|esclava|brazalete)\b", "Joyería y bisutería", "Pulseras"),
        (r"\b(anillo|anillos|argolla|sortija)\b", "Joyería y bisutería", "Anillos"),
        (r"\b(reloj|relojes)\b", "Joyería y bisutería", "Relojes"),
        (r"\b(lentes|gafas)\b", "Joyería y bisutería", "Lentes de sol"),
        (r"\b(joyero|alhajero|exhibidor|organizador)\b", "Joyería y bisutería", "Joyeros"),
    ],
    ("Deportes y fitness", "Otros"): [
        (r"\b(natacion|goggles|gorra de alberca|alberca|snorkel|buceo|"
         r"traje de neopreno|aletas)\b", "Deportes y fitness", "Natación"),
        (r"\b(mma|boxeo|guantes de box|costal|espinillera|protector bucal|careta)\b",
         "Deportes y fitness", "Boxeo"),
        (r"\b(futbol|soccer|porteria|tachones|canilleras)\b", "Deportes y fitness", "Fútbol"),
        (r"\b(patin|patines|patineta|skate|scooter|monopatin)\b",
         "Deportes y fitness", "Patines y patinetas"),
        (r"\b(tabla|surf|paddle|kayak|remo)\b", "Deportes y fitness", "Deportes acuáticos"),
        (r"\b(campamento|casa de campana|sleeping|mochila de montana|senderismo|"
         r"excursion|linterna de campamento)\b", "Deportes y fitness", "Campismo"),
        (r"\b(tenis de mesa|raqueta|badminton|padel)\b", "Deportes y fitness", "Raquetas"),
        (r"\b(pesa|mancuerna|barra|disco|kettlebell)\b", "Deportes y fitness", "Pesas"),
        (r"\b(diadema|munequera|rodillera|codera|faja|cinturon)\b",
         "Deportes y fitness", "Protección y soportes"),
    ],
    ("Cargadores y adaptadores", "Otros"): [
        (r"\b(laptop|notebook|portatil|macbook)\b|\b(asus|lenovo|hp|dell|acer|toshiba)\b",
         "Cargadores y adaptadores", "Para laptop"),
        (r"\b(pilas?|\baa\b|\baaa\b|18650|ni-?mh|recargables)\b",
         "Cargadores y adaptadores", "De pilas"),
        (r"\b(taladro|atornillador|herramienta|black and decker|dewalt|makita|bosch)\b",
         "Cargadores y adaptadores", "Para herramientas"),
        (r"\bcargador de auto|\b12 ?v\b.{0,15}(auto|coche)|encendedor",
         "Cargadores y adaptadores", "De auto"),
        (r"\binalambric|\bqi\b|\bmagsafe\b", "Cargadores y adaptadores", "Inalámbrico"),
        (r"\bcable\b|\busb\b", "Cargadores y adaptadores", "Cable"),
        (r"\badaptador\b|\bca/?cc\b|\bac/?dc\b|fuente de poder|eliminador",
         "Cargadores y adaptadores", "Adaptador de corriente"),
        (r"\bcargador\b", "Cargadores y adaptadores", "De pared"),
    ],
    # Juegos de mesa de verdad, que estaban todos bajo "Otros juegos".
    ("Juegos de mesa", "Otros juegos"): [
        (r"\b(rompecabeza|puzzle|puzle)\b", "Juegos de mesa", "Rompecabezas"),
        (r"\b(memoria|memorama)\b", "Juegos de mesa", "De memoria"),
        (r"\b(trivia|trivial|preguntas|adivina|palabras)\b", "Juegos de mesa", "De preguntas"),
        (r"\b(fiesta|party)\b", "Juegos de mesa", "De fiesta"),
        (r"\b(educativ|aprend|escolar|didactic|stem|programacion|matematic|anatomic)\b",
         "Juegos de mesa", "Educativos"),
        (r"\b(estrategia|catan|risk|carcassonne|ticket to ride|asmodee|"
         r"devir|days of wonder)\b", "Juegos de mesa", "De estrategia"),
        (r"\b(cartas|naipes|baraja|mazo|uno\b)\b", "Juegos de mesa", "De cartas"),
        (r"\b(infantil|ninos|kids|\d\+)\b", "Juegos de mesa", "Infantiles"),
        (r"\b(juego de mesa|board game|hasbro|mattel|ravensburger|goliath)\b",
         "Juegos de mesa", "De mesa clásicos"),
    ],
    # Lo que está en la categoría del aparato pero es una pieza suelta.
    ("Lavadoras", None): [
        (r"\b(manguera|interruptor|sello|rodamiento|tarjeta|motor|banda|"
         r"bomba|valvula|perilla|filtro|tapa|cajon dispensador|repuesto|"
         r"compatible con|pieza|refaccion)\b",
         "Refacciones", "Refacciones para electrodomésticos"),
        (r"\b(soporte|estante|base|pedestal|tapete|carro)\b", "Otros", "Organización del hogar"),
        (r"\b(centrifuga|centrifugadora|exprimidora)\b", "Lavadoras", "Portátiles"),
        (r"\blavadora de (vasos|platos|copas)\b", "Electrodomésticos", "Lavavajillas"),
        (r"\blavadora|lavarropa", "Lavadoras", "Automáticas"),
    ],
    ("Teclados", None): [
        (r"\b(midi|piano|sintetizador|\d{2} teclas|organo|controlador musical)\b",
         "Instrumentos musicales", "Teclados"),
        (r"\b(bandeja|soporte|brazo|mesa)\b", "Muebles", "Escritorios"),
        (r"\b(cable|keycap|teclas de repuesto|switches?|lubricante|"
         r"estabilizador|funda|cubre ?teclado|reposamunecas)\b",
         "Componentes y accesorios de PC", "Accesorios"),
        (r"\b(gaming|gamer|rgb|mecanic)\b", "Teclados", "Mecánicos"),
        (r"\bteclado\b", "Teclados", "Membrana"),
    ],
    ("Baterías portátiles", None): [
        (r"\b(arrancador|jump ?start|pasa corriente|compresor de aire)\b",
         "Autos, bicicletas y motos", "Accesorios y refacciones"),
        (r"\b(cargador de pared|cargador usb|adaptador)\b",
         "Cargadores y adaptadores", "De pared"),
        (r"\b(cubierta|funda|carcasa|cable|repuesto|compatible con)\b",
         "Cargadores y adaptadores", "Cable"),
        (r"\b(estacion de energia|generador|inversor)\b", "Otros", "Estaciones de energía"),
        (r"\b(\d{4,6}) ?mah\b", "Baterías portátiles", "Hasta 10,000 mAh"),
        (r"\b(power ?bank|bateria portatil|bateria externa)\b",
         "Baterías portátiles", "Hasta 10,000 mAh"),
    ],
    # La cámara de seguridad no es fotografía: es vigilancia, y el catálogo
    # tiene su propia categoría. Eran 391 mal puestas.
    ("Cámaras y fotografía", None): [
        (r"\b(seguridad|vigilancia|videovigilancia|\bcctv\b|\bptz\b|"
         r"vision nocturna|timbre con camara|videoportero)\b",
         "Cámaras de seguridad", "Interiores"),
        (r"\b(webcam|camara web)\b", "Componentes y accesorios de PC", "Webcams"),
        (r"\b(digital|compacta|llavero|vintage|infantil)\b",
         "Cámaras y fotografía", "Compactas"),
        (r"\b(tripie|tripode|estabilizador|gimbal|flash|filtro|correa|bolsa|"
         r"mochila|bateria|cargador|tarjeta|aro de luz)\b",
         "Cámaras y fotografía", "Accesorios"),
    ],
    ("Iluminación", None): [
        (r"\b(extractor|ventilador|campana)\b", "Climatización", "Ventiladores"),
        (r"\b(conector|cable|soldadura|balastra|transformador|driver led)\b",
         "Herramientas", "Material eléctrico"),
        (r"\b(empotrad|spot|downlight|\bplafon\b|panel led)\b",
         "Iluminación", "Empotrada"),
        (r"\b(foco|focos|bombilla|\bled\b)\b", "Iluminación", "Focos"),
        (r"\b(lampara|luz|luces|linterna)\b", "Iluminación", "Decorativa"),
    ],
    ("Domótica y hogar inteligente", None): [
        (r"\b(camara|videoportero|timbre con camara)\b", "Cámaras de seguridad", "Interiores"),
        (r"\b(timbre|sensor|detector|alarma)\b", "Domótica y hogar inteligente", "Sensores"),
        (r"\b(luz|foco|lampara|empotrada|\bhue\b|tira led)\b",
         "Domótica y hogar inteligente", "Iluminación inteligente"),
        (r"\b(contacto|toma de corriente|\bgfci\b|apagador)\b",
         "Herramientas", "Material eléctrico"),
        (r"\b(interruptor|boton|control remoto|regulador)\b",
         "Domótica y hogar inteligente", "Interruptores inteligentes"),
        (r"\b(enchufe|plug)\b", "Domótica y hogar inteligente", "Enchufes inteligentes"),
    ],
    ("Televisores", None): [
        (r"\b(soporte|montaje|rack|mueble|base)\b",
         "Componentes y accesorios de PC", "Accesorios de monitor"),
        (r"\b(tableta grafica|pantalla grafica|xppen|wacom)\b", "Monitores", "Oficina"),
        (r"\b(portatil|ruedas|con bateria)\b", "Televisores", "Portátiles"),
        (r"\b(4k|uhd)\b", "Televisores", "4K"),
        (r"\b(televisor|smart tv|pantalla)\b", "Televisores", "HD"),
    ],
    ("Cafeteras", None): [
        (r"\b(filtro|jarra de repuesto|refaccion|repuesto)\b",
         "Refacciones", "Refacciones para electrodomésticos"),
        (r"\b(k.?cup|capsula|pod)\b", "Cafeteras", "De cápsulas"),
        (r"\b(personal|individual|de viaje|portatil|\d{3} ?ml)\b", "Cafeteras", "Portátiles"),
        (r"\bcafetera\b", "Cafeteras", "De goteo"),
    ],
    ("Instrumentos musicales", None): [
        (r"\b(estrobo|luz disco|barra laser|par led|cabeza movil|"
         r"maquina de humo|escenario|\bdmx\b)\b", "Iluminación", "Escenario"),
        (r"\b(pedal|efecto|flanger|overdrive|distorsion|\bwah\b|looper)\b",
         "Instrumentos musicales", "Efectos y pedales"),
        (r"\b(maraca|pandero|cencerro|shaker|percusion|caja de ritmos|"
         r"tambor|conga|bongo)\b", "Instrumentos musicales", "Baterías"),
        (r"\b(cable|funda|estuche|atril|correa|banqueta|afinador|"
         r"capotraste|pua|puas|cuerdas)\b", "Instrumentos musicales", "Accesorios"),
        (r"\b(interfaz|mezcladora|monitor|midi|sampler|grabadora)\b",
         "Instrumentos musicales", "Producción de audio"),
    ],
    ("Herramientas", None): [
        (r"\b(polipasto|malacate|montacargas|gato hidraulico|grua)\b",
         "Herramientas", "Construcción"),
        (r"\b(imantada|magnetica|esquina para soldar|careta)\b", "Herramientas", "Soldadura"),
        (r"\b(cortador|cortadora|corte|sierra|cizalla)\b", "Herramientas", "Herramientas eléctricas"),
        (r"\b(kit|juego|set)\b.{0,20}(driver|impacto|taladro|atornillador)",
         "Herramientas", "Herramientas eléctricas"),
        (r"\b(electric|inalambric|bateria|\bv\b ?max|sin escobillas)\b",
         "Herramientas", "Herramientas eléctricas"),
        (r"\bherramienta\b", "Herramientas", "Herramientas manuales"),
    ],
}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = load_catalog()
    movidos = collections.Counter()
    quedan = collections.Counter()

    for p in data["products"]:
        clave = (p.get("category"), p.get("subcategory"))
        reglas = GRUPOS.get(clave)
        if not reglas:
            continue
        tn = norm(p.get("name"))
        for rx, cat, sub in reglas:
            if re.search(rx, tn):
                p["category"], p["subcategory"] = cat, sub
                movidos[(cat, sub)] += 1
                break
        else:
            quedan[clave] += 1

    for (cat, sub), n in movidos.most_common():
        print(f"  {n:6,}  -> {cat} / {sub}")
    print(f"\nfichas movidas: {sum(movidos.values()):,}")
    if quedan:
        print("\nsiguen sin reconocer (se dejan donde están):")
        for k, n in quedan.most_common():
            print(f"  {n:6,}  {k[0]} / {k[1]}")

    if args.dry_run:
        print("\n--dry-run: no se escribió nada")
        return
    if not movidos:
        print("\nnada que mover")
        return
    save_catalog(data)
    print("\nGuardado.")


if __name__ == "__main__":
    main()
