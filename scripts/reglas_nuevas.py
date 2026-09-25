#!/usr/bin/env python3
"""Reglas de las categorías y subcategorías nuevas del 25-sep-2026.

Ver reorganizar_categorias.py para el porqué. Todo trabaja sobre el título
normalizado (T() de clasificar_captura_perifericos: minúsculas, sin acentos).

- nueva_categoria(tn) -> (cat, sub, icono) | None
  La llama _decidir_base ANTES que el resto de las reglas: son productos
  inconfundibles por su primera palabra (tenis, libro, mochila...) o, en
  autopartes, por traer años de modelo y marca de auto junto a una pieza.
  Autopartes sale como «Refacciones» (el repartidor de siempre le pone la
  subcategoría) y destino() la pasa a Autopartes.

- por_departamento(dept) -> (cat, sub, icono) | None
  La red para lo que ninguna regla reconoce y trae el departamento de
  Walmart/Bodega Aurrerá. Los nombres de departamento de Walmart no siempre
  dicen lo que hay adentro («Calaveras» son calaveras de auto, «Música»
  son libros, «Lámparas y pantallas» son micas): por eso va al final y sólo
  con los departamentos revisados a mano sobre una muestra.
"""
import re

AUTO_MARCA = (r'toyota|nissan|chevrolet|chevy|ford|volkswagen|vw|honda|mazda|gmc|jeep|dodge|chrysler|'
              r'mercedes|bmw|audi|seat|kia|hyundai|mitsubishi|suzuki|subaru|renault|peugeot|fiat|buick|'
              r'cadillac|pontiac|lincoln|infiniti|acura|lexus|volvo|italika|tsuru|jetta|sentra|versa|aveo|'
              r'tacoma|civic|corolla|f-?150|silverado|vento|pointer|golf|beetle|sonic|spark|tornado|frontier|'
              r'np300|hilux|yaris|march|tiida|altima|cr-?v|explorer|ranger|focus|fiesta|ecosport|captiva|'
              r'cruze|malibu|equinox|trax|tahoe|suburban|cherokee|wrangler|ram \d|ibiza|leon|polo|passat|'
              r'mustang|camry|rav4|sienna|odyssey|accord|pilot|mx-?5|cx-?\d|attitude|neon|stratus|mini cooper|cooper|'
              r'expedition|escape|edge|lobo|f-?250|f-?350|super duty|lincoln|navigator|sequoia|tundra|highlander|'
              r'murano|pathfinder|x-?trail|kicks|rogue|journey|durango|charger|challenger|avenger|caliber|'
              r'crafter|amarok|tiguan|touareg|sportage|sorento|rio|forte|elantra|tucson|santa fe|accent|'
              r'outlander|lancer|swift|vitara|colorado|s10|blazer|trailblazer|express|impala|optra|matiz')
AUTO_PIEZA = (r'bujias?|bobinas?|poleas?|baleros?|amortiguador(es)?|alternador(es)?|marcha|terminal(es)?|'
              r'rotulas?|horquillas?|bujes?|sensor(es)?|bombas? (de (agua|gasolina|aceite|combustible)|anticongelante)|'
              r'radiador(es)?|termostato|deposito|tapon|manijas?|molduras?|tolvas?|salpicaderas?|facias?|'
              r'defensas?|faros?|calaveras?|cuartos?|lunas?|limpiaparabrisas|plumas? limpiaparabrisas|'
              r'balatas?|discos? de freno|tambor(es)?|caliper|clutch|embrague|juntas?|empaques?|arnes|'
              r'inyector(es)?|filtros? de (aire|aceite|gasolina|cabina)|banda de (distribucion|accesorios)|'
              r'cadena de distribucion|soportes? de (motor|transmision)|flechas?|homocineticas?|cremallera|'
              r'bieletas?|muelles?|carburador|silenciador|catalizador|motoventilador|compresor|condensador|'
              r'evaporador|tensor(es)?|cubierta|tanque|parrilla|espejo lateral|retrovisor|regulador de ventana|'
              r'elevador(es)? de (cristal|ventana)|chapa|cilindro maestro|bomba de clutch|resorte')
RX_ANIOS = re.compile(r'\b(19[5-9]\d|20[0-3]\d)\s*(?:al|a|-|/)\s*(19[5-9]\d|20[0-3]\d)\b|\bde (19|20)\d\d (?:al?|-) (19|20)\d\d\b')
RX_AUTO_MARCA = re.compile(r'\b(' + AUTO_MARCA + r')\b')
RX_AUTO_PIEZA = re.compile(r'\b(' + AUTO_PIEZA + r')\b')
RX_NO_AUTO = re.compile(r'\b(a escala|juguete|hot wheels|lego|llavero|playera|taza|poster|para ninos|de juguete|control remoto)\b')

# Dos palabras delante como máximo, y ninguna que convierta al objeto en
# otra cosa («raqueta de tenis», «funda para ...»).
_PREFIJO = r'^(?:(?!(?:raquetas?|pelotas?|red|mesa|juego|bolsa|funda|mochila|limpiador|kit|protector|organizador|porta|para|de|con|set)\b)\S+ ){0,2}'

RX_CALZADO = re.compile(_PREFIJO + r'(par de )?(tenis|zapatos?|zapatillas?|botas?|botin(es)?|sandalias?|huaraches?|pantuflas?|'
                        r'chanclas?|mocasines?|alpargatas?|flats|tacones|zuecos|crocs|choclos?)\b'
                        r'(?!.{0,30}\b(de mesa|para (perros?|mascotas?|gatos?|munecas?)|llavero|juguete|decorativ|'
                        r'pelotas?|raqueta|plantillas?|agujetas?|cordones|de vino|de hule para)\b)')
RX_LIBRO = re.compile(r'^libros?\b|\b(tapa|pasta) (blanda|dura)\b|\beditorial\b|\bediciones\b|\bisbn\b|\b97[89]\d{10}\b|'
                      r'\bpenguin random house\b|\bpaidos\b|\balfaguara\b|\banagrama\b|\bsalamandra\b|\bfondo de cultura\b')
RX_NO_LIBRO = re.compile(r'\b(funda|estuche|lampara|atril|soporte para libro|separador|forro|marcador|videojuego|'
                         r'nintendo|playstation|xbox|juego de mesa|rompecabezas|audiolibro|ebook reader|kindle)\b')
RX_ROPA = re.compile(_PREFIJO + r'(playeras?|blusas?|camisas?|camisetas?|pantalon(es)?|jeans|pants|joggers?|leggings?|leggins|'
                     r'shorts?|bermudas?|faldas?|vestidos?|chamarras?|chaquetas?|abrigos?|sudaderas?|sueteres?|'
                     r'sweaters?|cardigans?|blazers?|trajes? de bano|bikinis?|calcetines|calcetas|boxers?|trusas?|'
                     r'calzones|brasieres?|brassieres?|pijamas?|gorras?|sombreros?|gorros?|bufandas?|jerseys?|'
                     r'overoles?|paraguas|camisones?|batas? de bano|chalecos? (de|para) (mujer|hombre|dama|caballero))\b'
                     r'(?!.{0,30}\b(para (perros?|gatos?|mascotas?|munecas?)|de munec|llavero|funda para|protector)\b)')
RX_BEBE = re.compile(r'\b(bebe|beba|bebes|recien nacido|recien nacida|\d{1,2} ?meses)\b')
RX_NINO = re.compile(r'\b(nino|nina|ninos|ninas|infantil|junior|kids|boys|girls|juvenil)\b')
RX_BOLSA = re.compile(_PREFIJO.replace(r'bolsa|', '').replace(r'mochila|', '') +
                      r'(mochilas?|bolsas?|bolsos?|carteras?|monederos?|cangureras?|rinoneras?|maletin(es)?|'
                      r'portafolios|neceser(es)?|cosmetiqueras?|tote bags?|backpacks?|bandoleras?)\b'
                      r'(?!.{0,30}\b(de dormir|de basura|para basura|de aire|de agua caliente|de hielo|para (perros?|gatos?|mascotas?)|'
                      r'de (regalo|celofan|papel|plastico|tela ecologica|mandado)|herramientas?|ziploc|hermeticas?|'
                      r'para (congelar|alimentos|aspiradora|residuos|pan|hielo|lavanderia)|de vacio|para cafe|de te|'
                      r'de terciopelo|para (aretes|joyas|joyeria|collares)|organizadoras? de joyas|deshumidificador\w*|'
                      r'(de|para) colchon|de embalaje)\b)')
RX_JARDIN = re.compile(r'^(?:\S+ ){0,2}(macetas?|maceteros?|jardineras?|plantas? artificial(es)?|arbol(es)? artificial(es)?|'
                       r'flores artificiales|mangueras? (de jardin|para jardin|de riego|flexible|expandible)|'
                       r'aspersor(es)?|pistola de riego|albercas?|piscinas?|inflables? (para alberca|de alberca)|'
                       r'flotador(es)? (para alberca|inflable)|asador(es)?|parrillas? (de carbon|para asar|asador)|'
                       r'sombrillas? (de|para) (jardin|playa|patio|exterior|terraza)|toldos?|pergolas?|gnomos?|'
                       r'fuentes? de (jardin|agua decorativa)|cesped artificial|pasto artificial)\b')
RX_PAPELERIA = re.compile(r'^(?:\S+ ){0,2}(cuadernos?|libretas?|agendas?|boligrafos?|lapices|lapiz|lapiceros|colores|'
                          r'crayolas|crayones|plumones|marcadores? (permanentes?|de agua|para pizarron|de colores)|'
                          r'marcatextos|resaltadores?|borradores?|sacapuntas|pegamento|resistol|lapiz adhesivo|'
                          r'cinta (adhesiva|canela|diurex|masking|de embalaje)|masking|engrapadoras?|grapas|clips|'
                          r'folders?|carpetas?|archiveros?|sobres|hojas (blancas|de color|bond)|papel (bond|fotografico|'
                          r'opalina|kraft|china|crepe)|cartulinas?|foami|diamantina|acuarelas?|oleos|pinceles|lienzos?|'
                          r'caballetes?|block de dibujo|juego de geometria|calculadoras?|pizarron(es)?|pizarras?|'
                          r'corchos?|etiquetadoras?|rotuladoras?|perforadoras?|guillotinas?|enmicadoras?|'
                          r'trituradoras? de papel|estuches? de arte|lapiceras?|estuche escolar|plumas? '
                          r'(de gel|de tinta|punto fino|fuente|stylo))\b')
RX_PERFUME = re.compile(r'^(?:\S+ ){0,2}(perfumes?|colonia|fragancia|body mist|set de perfumes?)\b|\b(edp|edt|eau de parfum|eau de toilette|eau de cologne)\b')
RX_MASCOTA_ALIM = re.compile(r'^(?:\S+ ){0,3}(croquetas?|alimento (humedo |seco )?(para )?(perros?|gatos?|cachorros?|mascotas?)|'
                             r'premios? para (perros?|gatos?)|snacks? para (perros?|gatos?)|pate para gatos?)\b')
RX_FUNKO = re.compile(r'^(?:\S+ ){0,2}(funko|figura coleccionable|figuras coleccionables|coleccionable)\b|\bfunko pop\b')
RX_FIESTA = re.compile(r'^(?:\S+ ){0,2}(globos?|pinatas?|guirnaldas?|papel picado|confeti|velas? de cumpleanos|'
                       r'decoracion (de|para) fiesta|kit de fiesta|articulos para fiesta|banderines)\b')
RX_DISFRAZ = re.compile(r'^(?:\S+ ){0,2}(disfraz|disfraces|mascaras? (de halloween|halloween|de terror|de latex)|'
                        r'peluca de disfraz|capa de (mago|vampiro|superheroe)|tunica)\b|\bhalloween\b.*\b(mascara|disfraz|aplicacion fx)\b')
RX_DECO = [
    (re.compile(r'^(?:\S+ ){0,4}(cojin(es)?|fundas? de cojin|fundas? para cojin|almohadones?)\b'), 'Cojines'),
    (re.compile(r'^(?:\S+ ){0,2}(tapetes? (decorativos?|de sala|para sala|de pasillo|shaggy|vinilico)|alfombras?)\b'
                r'(?!.{0,20}\b(de yoga|para auto|para carro|de bano|de ratón|de raton|para mouse)\b)'), 'Tapetes y alfombras'),
    (re.compile(r'^(?:\S+ ){0,2}relojes? de pared\b'), 'Relojes de pared'),
    (re.compile(r'^(?:\S+ ){0,2}(floreros?|jarrones?|centros? de mesa)\b'), 'Floreros y centros de mesa'),
    (re.compile(r'^(?:\S+ ){0,2}(portarretratos?|marcos? (para|de) fotos?)\b'), 'Portarretratos'),
    (re.compile(r'^(?:\S+ ){0,2}(vinil(o)? decorativo|stickers? de pared|calcomanias? de pared)\b'), 'Vinil decorativo'),
    (re.compile(r'^(?:\S+ ){0,2}(arbol(es)? de navidad|esferas? navidenas?|adornos? navidenos?|adornos? de arbol|'
                r'nacimiento navideno|coronas? navidenas?|calabaza decorativa|decoracion de halloween|dia de muertos)\b'),
     'Navidad y temporada'),
]
RX_COCINA = re.compile(r'^(?:\S+ ){0,2}(mandil|delantal|coladera|colador|pelador|rallador|espatulas?|cucharon|'
                       r'pinzas de cocina|batidor manual|rodillo|tablas? para picar|moldes? (para|de) (hornear|pastel|'
                       r'reposteria|panque)|charolas? para hornear|refractarios?|contenedor(es)? hermetico|'
                       r'organizador(es)? de (cocina|alacena)|escurridor(es)?|especiero)\b')
RX_BANO = re.compile(r'^(?:\S+ ){0,2}(set de (bano|accesorios de bano)|dispensador de jabon|jabonera|portacepillos|'
                     r'cortinero|toallero|porta ?rollos?|tapetes? de bano|cortinas? de bano)\b')
RX_CUIDADO_AUTO = re.compile(r'\b(abrillantador|cera para (auto|carro)|shampoo para (auto|carro)|aromatizante para (auto|carro)|'
                             r'armor ?all|sonax|limpiador de (vestiduras|tableros|rines|llantas)|pulidor|pads? de pulido|'
                             r'aceite (para motor|mineral|sintetico|semisintetico) ?\d*w?|anticongelante|'
                             r'aditivo para (motor|gasolina|combustible)|liquido de frenos)\b')


def sub_calzado(tn):
    if re.search(r'\bpantuflas?\b', tn): return 'Pantuflas'
    if re.search(r'\b(seguridad|industrial|casquillo|dielectric|antiderrapante de trabajo)\b', tn): return 'Calzado de seguridad'
    if re.search(r'\b(botas?|botin(es)?)\b', tn): return 'Botas'
    if re.search(r'\b(sandalias?|huaraches?|chanclas?|crocs|zuecos|alpargatas?)\b', tn): return 'Sandalias'
    if re.search(r'\btenis\b', tn):
        return 'Tenis para niños' if RX_NINO.search(tn) else 'Tenis'
    if re.search(r'\b(vestir|oxford|tacon(es)?|formal|zapatillas?|stiletto)\b', tn): return 'Zapatos de vestir'
    return 'Zapatos casuales'


def sub_ropa(tn):
    if RX_NINO.search(tn): return 'Ropa de niños'
    for rx, s in [
        (r'\b(pijamas?|camisones?|batas?)\b', 'Pijamas'),
        (r'\b(calcetines|calcetas)\b', 'Calcetines'),
        (r'\b(boxers?|trusas?|calzones|brasieres?|brassieres?|lenceria)\b', 'Ropa interior'),
        (r'\b(trajes? de bano|bikinis?)\b', 'Trajes de baño'),
        (r'\b(gorras?|sombreros?|gorros?|bufandas?)\b', 'Gorras y sombreros'),
        (r'\bparaguas\b', 'Paraguas'),
        (r'\b(chamarras?|chaquetas?|abrigos?|sueteres?|sweaters?|cardigans?|blazers?|chalecos?)\b', 'Chamarras y suéteres'),
        (r'\bsudaderas?\b', 'Sudaderas'),
        (r'\b(jerseys?|deportiv[oa]|running|fitness|gym)\b', 'Ropa deportiva'),
        (r'\b(vestidos?)\b', 'Vestidos'),
        (r'\bfaldas?\b', 'Faldas'),
        (r'\b(shorts?|bermudas?)\b', 'Shorts y bermudas'),
        (r'\b(pantalon(es)?|jeans|pants|joggers?|leggings?|leggins|overoles?)\b', 'Pantalones y jeans'),
        (r'\bcamisas?\b', 'Camisas'),
        (r'\bblusas?\b', 'Blusas y tops'),
        (r'\b(playeras?|camisetas?)\b', 'Playeras'),
    ]:
        if re.search(rx, tn):
            return s
    return 'Playeras'


def sub_bolsa(tn):
    if re.search(r'\b(laptop|portatil|notebook|portalaptop)\b', tn): return 'Mochilas para laptop'
    if re.search(r'\bmochilas?|backpacks?\b', tn): return 'Mochilas'
    if re.search(r'\b(carteras?|monederos?|tarjetero)\b', tn): return 'Carteras y monederos'
    if re.search(r'\b(cangureras?|rinoneras?|bandoleras?|cruzad[oa])\b', tn): return 'Cangureras y bolsos cruzados'
    if re.search(r'\b(cosmetiqueras?|neceser(es)?)\b', tn): return 'Cosmetiqueras y neceseres'
    return 'Bolsas para mujer'


def sub_jardin(tn):
    for rx, s in [
        (r'\b(macetas?|maceteros?|jardineras?)\b', 'Macetas y jardineras'),
        (r'\b(artificial(es)?|cesped|pasto)\b', 'Plantas artificiales'),
        (r'\b(mangueras?|aspersor(es)?|riego|regaderas?)\b', 'Riego y mangueras'),
        (r'\b(albercas?|piscinas?|inflables?|flotador(es)?)\b', 'Albercas e inflables'),
        (r'\b(asador(es)?|parrillas?)\b', 'Asadores y parrillas'),
        (r'\b(sombrillas?|toldos?|pergolas?|carpas?)\b', 'Sombrillas, toldos y carpas'),
    ]:
        if re.search(rx, tn):
            return s
    return 'Decoración de jardín'


def sub_papeleria(tn):
    for rx, s in [
        (r'\b(etiquetadoras?|rotuladoras?)\b', 'Etiquetadoras y rotuladoras'),
        (r'\bcalculadoras?\b', 'Calculadoras'),
        (r'\b(pizarron(es)?|pizarras?|corchos?)\b', 'Pizarrones'),
        (r'\b(libretas?|agendas?)\b', 'Libretas y agendas'),
        (r'\bcuadernos?\b', 'Cuadernos'),
        (r'\b(boligrafos?|lapices|lapiz|lapiceros|plumas?|plumones|marcadores?|marcatextos|resaltadores?)\b', 'Escritura'),
        (r'\b(colores|crayolas|crayones|acuarelas?|oleos|pinceles|lienzos?|caballetes?|dibujo|foami|diamantina|estuches? de arte)\b', 'Arte y dibujo'),
        (r'\b(cinta canela|embalaje|emplaye|cajas? de carton)\b', 'Embalaje'),
        (r'\b(hojas|papel|sobres|cartulinas?)\b', 'Papel y sobres'),
        (r'\b(folders?|carpetas?|archiveros?|clips|engrapadoras?|grapas|perforadoras?)\b', 'Organización'),
        (r'\b(lapiceras?|estuche escolar|juego de geometria|sacapuntas|borradores?|pegamento|resistol|tijeras)\b', 'Útiles escolares'),
    ]:
        if re.search(rx, tn):
            return s
    return 'Artículos de oficina'


def nueva_categoria(tn, sub_refaccion=None, sub_libro=None):
    """(cat, sub, icono) para lo que es inconfundiblemente de una categoría
    nueva, o None. sub_refaccion/sub_libro: los repartidores del
    clasificador (se pasan para no importarlo en círculo)."""
    # Años de modelo y marca o modelo de auto juntos («2007 al 2013 mini»,
    # «oem ranger de 2019 a 2023 ford») es una autoparte aunque la pieza no
    # esté en la lista: el departamento de Walmart las reparte por Cocina,
    # Herramientas o Instrumentos musicales.
    es_auto = not RX_NO_AUTO.search(tn) and (
        (RX_ANIOS.search(tn) and (RX_AUTO_MARCA.search(tn) or re.search(r'\boem\b', tn)))
        or (re.search(r'\boem\b', tn) and RX_AUTO_MARCA.search(tn)))
    # Tapetes, cubrevolantes y fundas de asiento «para ford f-250 1996»: se le
    # agregan al auto, no se montan (segunda reorganización del 25-sep).
    if es_auto and re.match(r'^(\S+ ){0,2}(tapetes?|cubrevolantes?|fundas?|cubreasientos?|cubre asientos?)\b', tn):
        return ('Autos, bicicletas y motos', 'Tapetes, fundas y parasoles', 'car')
    if es_auto or (not RX_NO_AUTO.search(tn) and RX_AUTO_PIEZA.search(tn) and RX_AUTO_MARCA.search(tn)
                   and re.match(r'^(?:\S+ ){0,3}(' + AUTO_PIEZA + r')\b', tn)):
        if True:
            sub = sub_autoparte(tn) or (sub_refaccion(tn) if sub_refaccion else None)
            # «Condensador de enfriamiento ... 2012 nissan» salía como
            # refacción de refrigerador, y «espejo escape 2008 ford» (la
            # camioneta Escape) como escape: se descartan y va el respaldo.
            if sub and (sub.startswith('Refacciones para') or (
                    sub == 'Escape' and not re.search(r'\b(silenciador|mofle|tubo|catalizador|resonador|multiple|múltiple|escape (deportivo|universal))', tn))):
                sub = None
            if not sub:
                sub = ('Enfriamiento y climatización' if re.search(r'\b(bombas? (de agua|anticongelante)|radiador|termostato|anticongelante|motoventilador|ventilador|condensador)\b', tn)
                       else 'Faros y luces' if re.search(r'\b(faros?|calaveras?|cuartos?|luces|focos?)\b', tn)
                       else 'Carrocería, espejos y molduras' if re.search(r'\b(manijas?|molduras?|tolvas?|salpicaderas?|facias?|defensas?|parrilla|espejo|retrovisor|lunas?|cubierta)\b', tn)
                       else 'Para autos')
            return ('Refacciones', sub, 'gear')
    if RX_LIBRO.search(tn) and not RX_NO_LIBRO.search(tn):
        return ('Libros', (sub_libro(tn) if sub_libro else None), 'book')
    if RX_CALZADO.search(tn):
        if RX_BEBE.search(tn):
            return ('Juguetes y bebés', 'Ropa y calzado de bebé', 'toy')
        return ('Calzado', sub_calzado(tn), 'shoe')
    # Ropa y disfraces para perro («Disfraz sudadera duende navidad perro
    # talla 4 pet pals») no son de persona: se quedan donde estén.
    para_mascota = re.search(r'\b(perros?|gatos?|mascotas?|pet pals)\b', tn)
    if RX_ROPA.search(tn) and not para_mascota and not re.match(r'(llantas?|neum[aá]ticos?|rines?)\b', tn):   # llanta «blazer hp»
        if RX_BEBE.search(tn):
            return ('Juguetes y bebés', 'Ropa y calzado de bebé', 'toy')
        return ('Ropa y accesorios', sub_ropa(tn), 'shirt')
    # Lo que se llama «bolsa» o «mochila» pero es de otra cosa (revisión de
    # muestras del 25-sep): loncheras, portabebés, bolsas de boxeo o de
    # peso, de bicicleta/moto, de leche materna o sanitarias.
    if RX_BOLSA.search(tn) and not re.search(
            r'\b(loncheras?|almuerzo|termicas?|enfriador\w*|cuchillos|portabebes?|porta bebes|canguros?|'
            r'leche materna|panales|toallitas|sanitarias|boxeo|bulgara|contrapeso|\d+ ?kg|bicicletas?|motocicletas?|'
            r'moto|sillin|hidratacion|para (perros?|gatos?|mascotas?)|transportadora)\b', tn):
        return ('Bolsas y mochilas', sub_bolsa(tn), 'bag')
    # «Lápiz delineador de labios», «bolígrafo para cejas», «broca
    # perforadora», «cautín tipo lápiz» no son papelería.
    if RX_PAPELERIA.search(tn) and not re.search(
            r'\b(labios|ojos|cejas|delineador|khol|kohl|sombra|contorno|barba|brocas?|cautin|carpintero|'
            r'jardineria|cpvc|pvc|sds)\b', tn):
        return ('Papelería y oficina', sub_papeleria(tn), 'pencil')
    if RX_JARDIN.search(tn):
        return ('Jardín y exterior', sub_jardin(tn), 'leaf')
    if re.search(r'^(?:\S+ ){0,2}(lentes?|gafas|anteojos) de sol\b', tn):
        return ('Joyería y bisutería', 'Lentes de sol', 'ring')
    if re.search(r'^(?:\S+ ){0,2}(lentes? (oftalmicos?|de lectura|para computadora)|armazon(es)?( oftalmico)?|anteojos de lectura)\b', tn):
        return ('Joyería y bisutería', 'Lentes oftálmicos y de lectura', 'ring')
    if re.search(r'^(?:\S+ ){0,3}(correas?|extensibles?|bandas?|pulsos?|micas?|protector(es)?)\b.{0,40}\b(apple watch|galaxy watch|smartwatch|huawei (watch|fit|band)|mi band|amazfit|fitbit)\b', tn):
        return ('Relojes inteligentes',
                'Fundas, cargadores y protectores' if re.search(r'\b(micas?|protector(es)?|fundas?)\b', tn)
                else 'Correas y extensibles', 'watch')
    if RX_PERFUME.search(tn):
        return ('Belleza y cuidado personal', 'Perfumes', 'sparkle')
    if RX_MASCOTA_ALIM.search(tn):
        return ('Mascotas', 'Alimento para mascotas', 'paw')
    if RX_FUNKO.search(tn):
        return ('Juguetes y bebés', 'Funko y coleccionables', 'toy')
    if RX_DISFRAZ.search(tn) and not para_mascota:
        return ('Juguetes y bebés', 'Disfraces', 'toy')
    if RX_FIESTA.search(tn):
        return ('Juguetes y bebés', 'Artículos para fiestas', 'toy')
    for rx, s in RX_DECO:
        if rx.search(tn):
            return ('Decoración de hogar y jardín', s, 'vase')
    if RX_BANO.search(tn):
        return ('Blancos y ropa de cama', 'Accesorios de baño', 'pillow')
    if RX_CUIDADO_AUTO.search(tn) and not RX_AUTO_PIEZA.search(tn):
        return ('Autos, bicicletas y motos', 'Limpieza y cuidado del auto', 'car')
    if RX_COCINA.search(tn):
        return ('Cocina y comedor', None, 'coffee')
    return None


# Departamento de Walmart/Bodega -> categoría, revisados sobre una muestra
# (25-sep). El orden importa: la primera que coincide gana.
_DEPTOS = [
    (r'cerveza|vino|licor|oscura y ambar|cupon|cafe de grano|^accion$|^drama$|comedia$|pelicula', None),
    (r'otra ropa para moto|otros accesorios motos|accesorios e interiores|accesorios interiores|amortiguador|anticongelante|'
     r'retrovisor|limpiaparabrisas|^faros$|^cuartos$|calaveras|ventilacion|rines y tapones|herramientas electricas|'
     r'refaccion|autopart|suspension|frenos|motor', ('Refacciones', None, 'gear')),
    (r'aceites para motor|aditivos y lubricantes|pulido, limpieza y cuidado|accesorios de limpieza$',
     ('Autos, bicicletas y motos', 'Limpieza y cuidado del auto', 'car')),
    (r'botas y guantes', ('Herramientas', None, 'wrench')),
    (r'tenis|zapat|botas|botines|sandalia|calzado|pantufla|huarache|flats', ('Calzado', None, 'shoe')),
    (r'libro|novela|literatura|clasicos|cuentos|comics|historietas|idiomas|diccionario|enciclopedia|biografia|'
     r'poesia|revista|ficcion|terror y suspenso|auto ayuda|^musical$|^musica$|actividades y didacticos',
     ('Libros', None, 'book')),
    (r'mochilas, loncheras|papeleria|colores y plumines|diseno y dibujo|libretas|escritura|pinturas y pinceles|'
     r'estuches de arte|^papel$|embalaje|articulos de oficina|manualidades|negocio y punto de venta',
     ('Papelería y oficina', None, 'pencil')),
    (r'mochila|bolsas para|carteras|monedero|maletin|cosmetiquera', ('Bolsas y mochilas', None, 'bag')),
    (r'playera|blusa|tops|short|pantalon|falda|vestido|chamarra|sueter|ropa|jersey|pijama|gorra|sombrero|'
     r'calceti|traje de bano|lenceria|brasier|ecologicos, entrenadores', ('Ropa y accesorios', None, 'shirt')),
    (r'maceta|jardin|riego|manguera|alberca|inflable|asador|sombrillas y bases|toldo',
     ('Jardín y exterior', None, 'leaf')),
    (r'funko|juguetes de coleccion|figuras de accion|peluches|munecas|preescolar|casitas y cocinas|juegos al aire libre',
     ('Juguetes y bebés', None, 'toy')),
    (r'disfra|halloween|accesorios y complementos', ('Juguetes y bebés', 'Disfraces', 'toy')),
    (r'fiesta', ('Juguetes y bebés', 'Artículos para fiestas', 'toy')),
    (r'biberon|lactancia|mordedera|chupon|panal|carriola|juguetes de bebe', ('Juguetes y bebés', None, 'toy')),
    (r'perfume', ('Belleza y cuidado personal', 'Perfumes', 'sparkle')),
    (r'crema corporal|sales de bano|accesorios para tu cabello|manicure|rasuradoras', ('Belleza y cuidado personal', None, 'sparkle')),
    (r'aromaterapia|velas y veladoras', ('Limpieza y hogar', 'Aromatizantes y velas', 'house')),
    (r'cojin|tapetes y alfombras|^decoracion$|tapices y posters|arboles de navidad|letras, buzones', ('Decoración de hogar y jardín', None, 'vase')),
    (r'utensilios de cocina|horneado|ollas y cacerolas|hermeticos|bar y cocteleria|articulos para cafe|organizadores de cocina',
     ('Cocina y comedor', None, 'coffee')),
    (r'accesorios de bano', ('Blancos y ropa de cama', 'Accesorios de baño', 'pillow')),
    (r'instrumental medico|collarines|ortopedia|bastones|fajas ortopedicas|cuidado del paciente|cubre bocas|equipo para tu salud|masajeadores|basculas',
     ('Salud', None, 'heart-pulse')),
    (r'pulseras|collares|relojes para|lentes de sol|lentes oftalmicos', ('Joyería y bisutería', None, 'ring')),
    (r'herramientas manuales|cables electricos|^pinturas$|accesorios para pintar|cadenas y candados|plomeria|contactos y apagadores|'
     r'extensiones, multicontactos|sierras|maquinaria para construccion|lonas y cuerdas|lentes de seguridad|juegos de herramientas|'
     r'organizadores de herramientas|botas y guantes', ('Herramientas', None, 'wrench')),
    (r'equipo para pescar', ('Viajes', 'Pesca', 'suitcase')),
    (r'accesorios para acampar|carpas', ('Viajes', 'Camping', 'suitcase')),
    (r'baseball|futbol|deportes acuaticos|otros deportes|gimnasios', ('Deportes y fitness', None, 'dumbbell')),
    (r'smartwatch', ('Relojes inteligentes', None, 'watch')),
    (r'accesorios de red', ('Redes', None, 'wifi')),
    (r'microfonos|amplificadores|tornamesas|atriles', ('Instrumentos musicales', None, 'guitar')),
    (r'^fotografia$', ('Cámaras y fotografía', None, 'camera')),
    (r'^cartuchos$', ('Impresoras', None, 'printer')),
]
_DEPTOS = [(re.compile(rx), v) for rx, v in _DEPTOS]


def por_departamento(dept_normalizado):
    if not dept_normalizado:
        return None
    for rx, v in _DEPTOS:
        if rx.search(dept_normalizado):
            return v or False     # False = departamento que se descarta a propósito
    return None


# El género de un libro cuando el título no lo dice: el departamento de
# Walmart sí («Novelas», «Clásicos», «Comics e historietas»...).
_LIBRO_DEPTO = [
    (r'novela', 'Novela contemporánea'), (r'clasicos', 'Clásicos'),
    (r'cuentos y fabulas|actividades y didacticos|preescolar|infantil', 'Infantil'),
    (r'comics|historietas', 'Cómics y novela gráfica'), (r'manga', 'Manga'),
    (r'juvenil', 'Juvenil'), (r'auto ?ayuda|desarrollo personal', 'Autoayuda y desarrollo personal'),
    (r'diccionario|enciclopedia|texto', 'Educación y texto escolar'),
    (r'biografia', 'Biografías y memorias'), (r'terror|suspenso', 'Terror'),
    (r'fantasia|ficcion', 'Fantasía'), (r'poesia|teatro', 'Poesía y teatro'),
    (r'historia', 'Historia'), (r'negocio|finanza|economia', 'Negocios y finanzas'),
    (r'cocina', 'Cocina y gastronomía'), (r'religion|espiritual', 'Religión y espiritualidad'),
    (r'psicologia', 'Psicología'), (r'arte|diseno|fotografia|moda', 'Arte, diseño y fotografía'),
]
_LIBRO_DEPTO = [(re.compile(rx), s) for rx, s in _LIBRO_DEPTO]


def sub_libro_por_departamento(dept_normalizado):
    for rx, s in _LIBRO_DEPTO:
        if dept_normalizado and rx.search(dept_normalizado):
            return s
    return None


def sub_decoracion_nueva(tn):
    """La subcategoría nueva de Decoración que el título nombra, o None."""
    for rx, sub in RX_DECO:
        if rx.search(tn):
            return sub
    return None


# ---------------------------------------------------------------------------
# Subcategoría de Autopartes por la PIEZA que nombra el título (25-sep).
#
# Revisando lo importado de Walmart salió que la mitad de las autopartes
# estaba en una subcategoría que no era: amortiguadores en «Bujías y
# encendido», manijas de puerta en «Frenos», soportes de motor en
# «Enfriamiento», salpicaderas de auto en «Carenados» (que es de moto). El
# repartidor viejo (sub_refaccion) prueba sus reglas en orden y gana la
# primera que aparezca EN CUALQUIER PARTE del título: «Válvula marcha
# mínima» caía en eléctrico por «marcha». Acá gana la pieza que el título
# nombra PRIMERO, que en estos títulos («<pieza> <modelo> <años> <marca>»)
# es la que se vende.
# ---------------------------------------------------------------------------
_PIEZAS = [
    ('Frenos', r'balatas?|pastillas? de freno|discos? de freno|tambor(es)? de freno|calipers?|mordazas?|'
               r'cilindros? de rueda|bombas? de freno|mangueras? de freno|zapatas?|booster|chicotes? de freno|'
               r'liquido de frenos|kit de frenos|frenos?'),
    ('Suspensión y dirección', r'amortiguador(es)?|bases? (de )?amortiguador(es)?|resortes?|muelles?|rotulas?|'
               r'terminal(es)?( (exterior|interior|de direccion))?|horquillas?|bieletas?|barras? estabilizadoras?|'
               r'bujes?|cremallera|caja de direccion|coples? (de )?direccion|brazos? (auxiliar|pitman|loco|de suspension|'
               r'de control|tensor)|mazas?|baleros?|flechas?|juntas? homocineticas?|tornillos? estabilizador(es)?|'
               r'gomas? de barra|combo resortes|kit de suspension|espiral(es)?'),
    ('Bombas', r'bombas? (de )?(agua|aceite|gasolina|combustible|direccion|alta presion)'),
    ('Motor y transmisión', r'soportes? (de )?(motor|transmision)|metal(es)? (de )?(biela|centro|bancada)|metales|bielas?|'
               r'pistones|piston|anillos|empaques?|juntas? (de cabeza|de multiple|de tapa)|sellos? (de )?valvulas?|'
               r'valvulas? (de )?(admision|escape|pcv|egr)|punterias?|arbol(es)? de levas|ciguenal|cadenas? (de )?tiempo|'
               r'bandas? (de )?tiempo|kit de distribucion|tensor(es)?( de accesorios| de banda)?|poleas?( tensoras?)?|'
               r'bandas?( de accesorios| serpentin)?|clutch|embrague|collarin|volante motor|carter|'
               r'tapon (de )?(llenado de )?aceite|tapas? de punterias|multiple de admision|cuerpos? de aceleracion|'
               r'inyector(es)?|carburador|turbo|monoblock|culata|cabeza de motor|transmision|convertidor de par|'
               r'crucetas?|diferencial|cardan|regulador de presion|motor(es)? (completo|parcial|de \d)'),
    ('Filtros y aceites', r'filtros?|aceites?( de motor| sintetico)?|lubricante|aditivo'),
    ('Bujías y encendido', r'bujias?|bobinas?( de encendido| ignicion)?|cables? de bujias?|distribuidor|tapas? de distribuidor|'
               r'rotor|modulo de encendido'),
    ('Sistema eléctrico y sensores', r'sensor(es)?|switch|interruptor(es)?|alternador(es)?|marcha|motor de arranque|'
               r'relevador(es)?|reles?|fusibles?|arnes|modulos?( de control)?|computadora|bulbos?|'
               r'valvulas? (iac|de )?marcha minima|regulador de voltaje|claxon|bocinas? claxon|baterias?|'
               r'controles? de elevador|actuador(es)?'),
    ('Faros y luces', r'faros?( de niebla)?|calaveras?|cuartos?|focos?|direccional(es)?|stops?|luz|luces|halogenos?|'
               r'cambio de luz|biseles?'),
    ('Enfriamiento y climatización', r'radiador(es)?|termostatos?|tomas? de agua|depositos? (de )?(anticongelante|recuperador|'
               r'agua|refrigerante)|tapon(es)? (de )?radiador|mangueras? (de )?(radiador|superior|inferior|agua|calefaccion)|'
               r'tubos? de enfriamiento|motoventilador(es)?|ventilador(es)?|fan clutch|aspas?|condensador(es)?|'
               r'compresor(es)?|evaporador(es)?|calefactor|anticongelante|refrigerante|conector manguera'),
    ('Escape', r'mofles?|silenciador(es)?|catalizador(es)?|multiple de escape|tubos? de escape|resonador(es)?|colas? de escape'),
    ('Limpiaparabrisas', r'limpiaparabrisas|plumas? (limpiaparabrisas|limpiadoras?)|brazos? limpiaparabrisas|'
               r'depositos? (de )?limpiaparabrisas'),
    ('Llaves y cerraduras de auto', r'llaves?( control| de encendido)?|carcasas? (de|para) llave|cilindros? (de )?(encendido|llave)|'
               r'chapas?|cerraduras?|control(es)? de alarma'),
    ('Interior y tapicería', r'tapetes?|cubrevolantes?|fundas? (de |para )?asientos?|cubreasientos|volantes?|palancas?|'
               r'perillas?|consolas?|tableros?|asientos?|cinturon(es)? de seguridad|viseras?|alfombras?'),
    ('Carrocería, espejos y molduras', r'espejos?|retrovisor(es)?|molduras?|facias?|defensas?|parrillas?|salpicaderas?|'
               r'cofres?|puertas?|manijas?|bisagras?|tolvas?|guardafangos?|loderas?|spoiler|emblemas?|cristal(es)?|'
               r'medallon|parabrisas|elevador(es)?( de (cristal|ventana|vidrio))?|lunas?|tapon(es)? (de )?gasolina|'
               r'porta ?placas?|estribos?|rejillas?|marcos? de faro|cuartos? de (salpicadera|carroceria)'),
]
_MOTO = {
    'Frenos': 'Frenos de moto', 'Faros y luces': 'Luces de moto', 'Escape': 'Motor, carburación y escape de moto',
    'Motor y transmisión': 'Motor, carburación y escape de moto', 'Suspensión y dirección': 'Suspensión y dirección de moto',
    'Filtros y aceites': 'Filtros y aceites de moto', 'Bujías y encendido': 'Eléctrico y baterías de moto',
    'Sistema eléctrico y sensores': 'Eléctrico y baterías de moto', 'Carrocería, espejos y molduras': 'Carenados, plásticos y tanques',
    'Interior y tapicería': 'Asientos, parrillas y accesorios de moto', 'Bombas': 'Motor, carburación y escape de moto',
    'Enfriamiento y climatización': 'Motor, carburación y escape de moto', 'Llaves y cerraduras de auto': 'Para motos',
    'Limpiaparabrisas': 'Para motos',
}
_RX_PIEZAS = [(s, re.compile(r'\b(' + rx + r')\b')) for s, rx in _PIEZAS]
RX_MOTO_CTX = re.compile(r'\b(motos?|motocicletas?|motoneta|italika|cuatrimoto|scooter|\d{2,4} ?cc|harley|yamaha|kawasaki|'
                         r'suzuki gn|honda (cg|cb|xr|cbr|goldwing|gl)|vento|dinamo|bajaj|ktm|ducati)\b')
RX_MOTO_PROPIAS = re.compile(r'\b(cadenas?|sprockets?|catarinas?|kit de arrastre|pinon(es)?)\b')
RX_MOTO_MANUBRIO = re.compile(r'\b(manubrios?|punos?|manetas?|espejos?|controles? de manubrio|acelerador)\b')


def sub_autoparte(tn):
    """Subcategoría de Autopartes por la primera pieza que nombra el título,
    o None si no nombra ninguna conocida."""
    mejor = None
    for s, rx in _RX_PIEZAS:
        m = rx.search(tn)
        if m and (mejor is None or m.start() < mejor[0]):
            mejor = (m.start(), s)
    moto = RX_MOTO_CTX.search(tn) and not re.search(r'\b(bocina|tapete)s? .{0,40}\b(19|20)\d\d\b', tn)
    if moto:
        if RX_MOTO_PROPIAS.search(tn):
            return 'Cadenas, sprockets y transmisión'
        if RX_MOTO_MANUBRIO.search(tn) and (mejor is None or mejor[1] in ('Carrocería, espejos y molduras',
                                                                       'Sistema eléctrico y sensores')):
            return 'Manubrios, espejos y controles'
        if re.search(r'\b(llantas?|camaras?|neumaticos?)\b', tn):
            return 'Llantas y cámaras de moto'
        return _MOTO.get(mejor[1]) if mejor else None
    return mejor[1] if mejor else None
