"""Repartidores de subcategoría para las categorías que no tenían ninguno.

POR QUÉ
-------
Al medir (19 de septiembre de 2026) quedaban 9,192 fichas sin subcategoría
y 672 en una "Otros". Una parte cae en categorías que sí tienen repartidor
pero cuyas reglas no alcanzaban (eso se arregla en cada sub_* del
clasificador); otra parte cae en categorías que NUNCA tuvieron repartidor:
Cargadores y adaptadores, Electrodomésticos, Drones, Equipo comercial,
Viajes, Impresión 3D, Movilidad eléctrica, Proyectores y "Otros". Acá van
esos, con el mismo contrato que los demás: reciben el título normalizado
(T()) y devuelven la subcategoría o None. Solo agregan subcategoría dentro
de la categoría que la ficha ya tiene; nunca la cambian de categoría.
"""
import re


def sub_cargador(tn):
    # Lo que no es cargador de pared ni de auto: el power bank (es de
    # Baterías portátiles), el adaptador Wi-Fi de domótica.
    # "Inteligente" y "wifi" a secas también los dice el cargador de auto de
    # carga rápida: el descarte pide que sea un enchufe o contacto smart.
    if re.search(r'power ?bank|banco de energia|bateria (externa|portatil)|\btuya\b|'
                 r'(enchufe|contacto|toma)\w*.{0,20}intelig|smart plug', tn):
        return None
    if re.search(r'bateria(s)? (para|de|compatible)? ?(camara|videocamara|canon|sony|nikon|motorola|radio|gopro|dji)|'
                 r'\blp-e\d|\bnp-[fw]\d|para videocamara|cargador (dual|doble|de bateria).{0,40}(bateria|baterias)|'
                 r'cargador de baterias?\b', tn):
        return 'De pilas'
    # El accesorio del cargador no es un cargador: el lector de tarjetas,
    # el adaptador USB-C a HDMI o a Ethernet son cables y adaptadores de
    # datos, y van a "Cable" que es lo más cercano que tiene la lista.
    if re.search(r'lector de tarjetas|\botg\b|a hdmi|a ethernet|\brj45\b|hub usb|'
                 r'cable adaptador|adaptador (usb|tipo c|usb-?c) a ', tn):
        return 'Cable'
    if re.search(r'cargador (de |para |\S+ )?(auto|coche|carro|vehicul)|de auto\b|para auto\b|'
                 r'encendedor|\b12 ?v\b.{0,20}(auto|coche|carro)|car charger', tn):
        return 'De auto'
    if re.search(r'cargador (de |para )?(laptop|portatil|notebook)|para laptop|eliminador|'
                 r'adaptador (de corriente |de alimentacion )?(para|de) (laptop|notebook)|'
                 r'\b(19|19\.5|20) ?v\b.{0,25}\b\d\.\d+ ?a\b', tn):
        return 'Para laptop'
    if re.search(r'\bpilas?\b|\baa\b|\baaa\b|18650|\bnimh\b|ni-mh', tn):
        return 'De pilas'
    if re.search(r'inalambric|wireless|\bqi2?\b|magsafe|magnetic|magnetico|'
                 r'base de carga|estacion de carga|dock de carga|soporte de carga|'
                 r'\bbanco de energia inalambrico\b', tn):
        # La base con varios sitios (reloj, audífonos y teléfono) se vende
        # como estación; la de un solo sitio, como cargador inalámbrico.
        if re.search(r'\b3 en 1\b|\b2 en 1\b|estacion|\bdock\b|\bbase\b', tn):
            return 'Base de carga'
        return 'Inalámbrico'
    if re.match(r'^(?:\S+ )?cables?\b', tn) or (
            'cargador' not in tn and re.search(r'^(?:\S+ ){0,4}cables?\b|cable (usb|tipo c|lightning|micro)', tn)):
        return 'Cable'
    if re.search(r'para herramienta|dewalt|makita|milwaukee|\bryobi\b|\bbosch\b.{0,20}bateria', tn):
        return 'Para herramientas'
    if re.search(r'adaptador (universal )?de (viaje|enchufe|corriente)|adaptador universal|'
                 r'enchufe (europeo|americano|universal)|convertidor de (voltaje|enchufe)|'
                 r'adaptador de alimentacion|fuente de (poder|alimentacion)|'
                 # La regleta, el multicontacto y la placa de pared con USB
                 # son toma de corriente, no cargador de un aparato.
                 r'\bregleta\b|multicontacto|extension electrica|tira de alimentacion|'
                 r'extensor de alimentacion|placa de pared usb|\bgfci\b|conector de enchufe usb', tn):
        return 'Adaptador de corriente'
    if re.search(r'cargador|carga rapida|turbopower|\bpd\b|\bqc ?3|\bgan\b|de pared|'
                 r'\d+ ?w\b|multipuerto|adaptador', tn):
        # "De pared" es la rama que la ola 4 reparte por potencia y por
        # tipo (multipuerto, con cable, para reloj).
        return 'De pared'
    return None


def sub_electro(tn):
    if re.search(r'campana', tn): return 'Campanas de cocina'
    if re.search(r'lavavajilla|lavaplatos', tn): return 'Lavavajillas'
    if re.search(r'microondas', tn): return 'Microondas'
    if re.search(r'calentador de agua|\bboiler\b|calentador (de paso|solar|electrico)|'
                 r'regadera electrica', tn): return 'Calentadores de agua'
    if re.search(r'maquina de coser|overlock|\bsinger\b|\bbrother\b.{0,20}(coser|costura)', tn):
        return 'Máquinas de coser'
    if re.search(r'vaporizador|generador de vapor|cepillo de vapor|robot de planchado|'
                 r'\bsteamer\b', tn): return 'Vaporizadores de ropa'
    if re.search(r'\bplancha\b(?!.{0,15}(electrica|de asar|parrilla|para asar|antiadherente para))|'
                 r'\bplanchas?\b.{0,15}(vapor|ropa|de viaje)|\biron\b', tn):
        return 'Planchas'
    if re.search(r'extractor de jugo|exprimidor|juguera|\bjuicer\b', tn): return 'Extractores de jugo'
    if re.search(r'licuadora|turbolicuador|batidora de inmersion|mezcladora de inmersion|'
                 r'\bmixer\b|\bblender\b', tn): return 'Licuadoras'
    if re.search(r'freidora de aire|air ?fryer|horno freidora', tn): return 'Freidoras de aire'
    if re.search(r'\bestufa|parrilla (de gas|electrica de cocina)|\bcooktop\b|'
                 r'cubierta (de gas|de induccion)', tn): return 'Estufas'
    if re.search(r'\bhorno\b(?! freidora)', tn): return 'Hornos'
    if re.search(r'purificador de agua|filtro de agua|osmosis', tn): return 'Purificadores de agua'
    if re.search(r'dispensador de agua|enfriador de agua|despachador de agua', tn):
        return 'Dispensadores de agua'
    if re.search(r'robot limpiacristales|limpia ?cristales', tn): return 'Robots limpiacristales'
    if re.search(r'tostador|sandwichera|waflera|crepera|batidora|amasadora|arrocera|'
                 r'olla (multiusos|electrica|de coccion lenta|arrocera)|instant pot|'
                 r'maquina de (helados|palomitas|pan|pasta)|procesador|molino|picadora|'
                 r'parrilla electrica|plancha electrica|\bgriddle\b|vaporera|hervidor|'
                 r'freidora electrica|cafetera|tetera electrica|\bhervidora\b', tn):
        return 'Pequeños electrodomésticos de cocina'
    # Última red (21-sep): la marca y la línea dicen el aparato cuando el
    # título no lo nombra ("Rowenta Perfomance 1725w DW2350").
    if re.search(r'\browenta\b|\bt-fal\b.{0,25}(puregliss|fv\d)|\bdw\d{4}\b|\bfv\d{4}\b|'
                 r'estacion de planchado|zapata (de )?teflon|manguera.{0,15}plancha|'
                 r'suela antiadherente|\bplanchas\b', tn):
        return 'Planchas'
    if re.search(r'plancha y parrilla|\bgriddler\b|parrilla para interiores|\bgx1\d{2}\b', tn):
        return 'Parrillas y planchas eléctricas'
    if re.search(r'batidor (de )?mano|licuadora de mano|batidor de inmersion', tn):
        return 'Licuadoras'
    if re.search(r'robot de limpieza (de |automatica de )?(ventanas|vidrio|cristal)|\bhutt\b|'
                 r'limpieza de vidrio inteligente', tn):
        return 'Robots limpiacristales'
    if re.search(r'extractor purificador|purificador.{0,25}(isla|de cocina)', tn):
        return 'Campanas de cocina'
    if re.search(r'\bcocina\b \w+ ?\d|puerta ciega', tn): return 'Estufas'
    if re.search(r'mezclador para pan ?cake|dosificador.{0,20}pancake|pancake machine', tn):
        return 'Pequeños electrodomésticos de cocina'
    return None


def sub_dron(tn):
    if re.search(r'^(?:\S+ ){0,3}(bateria|helice|helices|cargador|funda|estuche|mochila|'
                 r'filtro|hub|cable|kit de accesorios|protector|tren de aterrizaje|'
                 r'landing|control remoto para|gafas|goggles)', tn):
        return 'Accesorios'
    if re.search(r'\bdji\b|\bmavic\b|\bmini [234]\b|\bair [23]\b|\bavata\b|\bneo\b', tn):
        return 'DJI'
    if re.search(r'\bfpv\b|gafas vr|racing', tn): return 'FPV'
    if re.search(r'\bgps\b|retorno automatico|return to home', tn): return 'Con GPS'
    if re.search(r'mini dron|mini drone|drone mini|dron mini|plegable|de bolsillo', tn):
        return 'Mini drones'
    if re.search(r'principiante|para ninos|de juguete|juguete|kids|infantil', tn):
        return 'Para principiantes'
    if re.search(r'\bdron\b|\bdrone\b|cuadricoptero|quadcopter', tn):
        return 'Mini drones' if re.search(r'\bmini\b|plegable', tn) else 'Para principiantes'
    return None


def sub_comercial(tn):
    if re.search(r'refrigerad|congelador|enfriador|vitrina (refrigerada|fria)|'
                 r'mesa refrigerada|exhibidor (refrigerado|frio)|camara fria|'
                 r'refrigeracion', tn): return 'Refrigeración comercial'
    # «Punto de venta» eran 1,326 fichas con la caja registradora, la terminal,
    # el cajón de dinero, el lector de códigos y hasta el exhibidor de
    # cigarrillos, que sólo comparten la frase «punto de venta» en su título.
    # Son compras distintas y se separan como las separa kakaku.
    #
    # El exhibidor va PRIMERO porque «Estante para Cigarrillos ... Punto de
    # Venta» decía la frase y se quedaba acá en vez de irse a Mobiliario.
    if re.search(r'^(?:\S+ ){0,3}(estante|exhibidor|anaquel|vitrina|mostrador|gondola)\b', tn):
        return 'Mobiliario'
    if re.search(r'caja registradora|cash register|\bregistradora\b|'
                 r'sistema de punto de venta', tn):
        return 'Cajas registradoras'
    if re.search(r'cajon (de|para) dinero|cash drawer|gaveta (de|para) dinero', tn):
        return 'Cajones de dinero'
    if re.search(r'lector (de|para) codigo|escaner (de|para) codigo|barcode scanner|'
                 r'lector de barras', tn):
        return 'Lectores de código de barras'
    if re.search(r'terminal (de|punto)|terminal pos\b|\btpv\b', tn):
        return 'Terminales punto de venta'
    if re.search(r'punto de venta|\bpos\b|lector de codigo|'
                 r'terminal|cajon de dinero|impresora de tickets|escaner de codigo', tn):
        return 'Punto de venta'
    if re.search(r'prensa de calor|plancha de sublimacion|prensa (termica|para tazas|para gorras)|'
                 r'heat press', tn): return 'Prensas de calor'
    if re.search(r'impresora de sublimacion|sublimacion', tn): return 'Impresoras de sublimación'
    if re.search(r'\bcarro\b|\bcarrito\b|\bcarros\b|carro de servicio|carro recolector|'
                 r'carro volcador|\btrolley\b', tn): return 'Carros de servicio'
    if re.search(r'\bmesa\b|\bmesas\b|estante|anaquel|repisa|rack|tarja|fregadero|'
                 r'lavabo|lambrin|mueble|banco|silla|exhibidor|mostrador|vitrina', tn):
        return 'Mobiliario'
    if re.search(r'freidora|plancha|estufa|parrilla|horno|campana|licuadora|batidora|'
                 r'rebanadora|tortilladora|baño maria|bano maria|salamandra|'
                 r'gratinador|marmita|extractor|tostador|asador|comal|cocina', tn):
        return 'Cocina industrial'
    return None


def sub_viaje(tn):
    if re.search(r'\bpesca\b|pescar|\bcana\b|\bcarrete\b|\bsenuelo|\banzuelo|'
                 r'\bbuceo\b|pesca sub', tn): return 'Pesca'
    if re.search(r'camping|campismo|acampar|casa de campana|tienda de campana|'
                 r'sleeping|bolsa de dormir|tactic|militar|senderismo|hiking|'
                 r'mochila (de )?(montana|trekking)', tn): return 'Camping'
    if re.search(r'maleta|valija|equipaje|\bluggage\b|\bspinner\b|\btrolley\b|'
                 r'bolso|bolsa|mochila|\bbag\b|funda (para|de) maleta|'
                 r'organizador de (viaje|equipaje)|neceser|portatrajes|\bduffel\b', tn):
        return 'Maletas'
    return None


def sub_impresion3d(tn):
    if re.search(r'filamento|\bpla\b|\bpetg\b|\babs\b|\btpu\b|resina', tn): return 'Filamentos'
    if re.search(r'escaner 3d|scanner 3d|3d scanner', tn): return 'Escáneres 3D'
    if re.search(r'^(?:\S+ ){0,4}(impresora|impresoras)\b|\bender\b|bambu lab|bambu\b|'
                 r'\bp1s\b|\bp2s\b|\bh2d\b|\bx1c\b|\ba1 mini\b|\bphoton\b|\bsaturn\b|'
                 r'\bmars\b|\bcreator\b|\bsparkx\b|\bkobra\b|\bk1\b|\bk2\b|\bcr-?10\b|'
                 r'\bprusa\b|\bmk4\b|\bsovol\b|\bqidi\b|\belegoo neptune\b', tn):
        if re.search(r'^(?:\S+ ){0,3}(kit|componentes|estacion|caja|secador|tanque|'
                     r'placa|boquilla|nozzle|cama|extrusor|hotend|camara|ams|sistema|'
                     r'tren|componente|repuesto|refaccion|filtro|ventilador)', tn):
            return 'Accesorios'
        return 'Impresoras'
    if re.search(r'estacion de (lavado|curado)|secador|secadora de filamento|boquilla|'
                 r'\bnozzle\b|\bhotend\b|extrusor|cama (caliente|magnetica)|placa de (construccion|impresion)|'
                 r'\bpei\b|tanque de resina|\bfep\b|\bams\b|accesorio|repuesto|refaccion|kit', tn):
        return 'Accesorios'
    return None


def sub_movilidad(tn):
    if re.search(r'^(?:\S+ ){0,3}(soporte|montaje|cargador|bateria|llanta|neumatico|funda|'
                 r'casco|candado|rueda|kit|accesorio|manubrio|asiento|luz|freno)', tn):
        return 'Accesorios'
    if re.search(r'bicicleta electrica|\be-?bike\b|bici electrica', tn): return 'Bicicletas eléctricas'
    if re.search(r'patin|scooter|patineta|monopatin|hoverboard|autoequilibrio|gokart|go-?kart|'
                 r'segway|ninebot|\bkickscooter\b|\bxiaomi\b.{0,20}electric', tn):
        return 'Patinetes eléctricos'
    return None


def sub_proyector(tn):
    if re.search(r'pantalla (de |para )?proyec|pantalla (enrollable|electrica|motorizada|'
                 r'con tripie|con tripode|portatil|de marco|inflable|de suelo|de mesa|alr)|'
                 r'tela de proyeccion|\bscreen\b', tn): return 'Pantallas de proyección'
    if re.search(r'lampara (de |para )?proyector', tn): return 'Lámparas de proyector'
    if re.search(r'soporte (de |para )?proyector|montaje (de |para )?proyector|'
                 r'base (de |para )?proyector', tn): return 'Soportes para proyector'
    if re.search(r'^(?:\S+ ){0,3}(control remoto|mando|cable|funda|estuche|maleta|'
                 r'filtro|lente|adaptador|bateria|bolsa|mochila)', tn): return 'Accesorios'
    if re.search(r'proyector|miniproyector|mini proyector|\bnebula\b|\bcapsule\b|'
                 r'\bepson\b|\bbenq\b|\bviewsonic\b|\boptoma\b|\bxgimi\b|\bwanbo\b', tn):
        return 'Proyectores'
    return None


_RX_COCINA = re.compile(r'cuchillo|arrocera|\bolla|sarten|vapor de verduras|freidora|licuadora|cafetera|'
                        r'tortilla|vajilla|\bplato|\bvaso|\btaza|\btermo|botella|\bjarra|especia|'
                        r'tabla (de|para) (cortar|picar)|escurridor|bandeja|charola|cubiertos|molde|reposteria')


def sub_otros(tn):
    """La categoría "Otros" tiene subcategorías que sí dicen algo: baño,
    organización del hogar, soportes para dispositivos, radios, energía
    solar. Lo que no encaja en ninguna se queda como está: moverlo a otra
    categoría es trabajo del auditor, no de este repartidor."""
    if _RX_COCINA.search(tn) or re.search(r'bicicleta|caminadora|eliptica|\bcamara\b', tn):
        # Lo de cocina no es "Organización del hogar" (es Cocina y comedor,
        # y de moverlo se encarga reclasificar_otros.py); la bicicleta fija
        # "con soporte para tablet" no es un soporte.
        return None
    # El soporte tiene que ABRIR el título: la botella "con soporte de
    # montaje" y la bicicleta fija "con soporte para tablet" no lo son.
    if re.match(r'^(?:\S+ ){0,3}(soportes?|bases?|sujetador|montaje|tripode|tripie|palo|selfie|gooseneck|brazo|clip|anillo|holder|mount)\b', tn) and \
       re.search(r'telefono|celular|tablet|tableta|movil|ipad|iphone|selfie|smartphone|gopro|camara de accion', tn):
        return 'Soportes para dispositivos'
    if re.search(r'\bradio\b(?! ?control)|\bradios\b|walkie|onda corta|\bam ?/ ?fm\b|'
                 r'radio (am|fm|portatil|de bolsillo)', tn): return 'Radios'
    if re.search(r'panel(es)? solar|placa solar|modulo fotovoltaico', tn): return 'Paneles solares'
    if re.search(r'inversor|\binverter\b', tn): return 'Inversores'
    if re.search(r'estacion de energia|power station|\becoflow\b|\bbluetti\b|\bjackery\b', tn):
        return 'Estaciones de energía'
    if re.search(r'generador', tn): return 'Generadores'
    if re.search(r'controlador de carga|\bmppt\b|\bpwm\b|kit solar', tn):
        return 'Kits solares y controladores de carga'
    if re.search(r'cargador solar', tn): return 'Cargadores solares portátiles'
    if re.search(r'(luz|lampara|foco|ventilador|luces).{0,20}solar', tn): return 'Luces y ventiladores solares'
    if re.search(r'bomba solar|calentador solar', tn): return 'Bombas y calentadores solares'
    if re.search(r'\bbano\b|\bducha\b|regadera|\bwc\b|inodoro|\btoilet|cepillo de dientes|'
                 r'jabonera|porta ?(rollo|papel)|cortina de bano|tapete de bano|'
                 r'dispensador de jabon|limpiacristales|escobilla', tn): return 'Baño'
    if re.search(r'organizador|\bcaja\b.{0,25}(almacen|organiz|guardar)|cesto|canasta|'
                 r'perchas?\b|ganchos? (para|de) (ropa|colgar)|\bcajas? (de|para) (almacenamiento|guardar)|'
                 r'zapatera|estante|repisa|cubo (de )?basura|bote de basura|tendedero|'
                 r'burro de planchar|\bbandeja giratoria\b|separador de cajon', tn):
        return 'Organización del hogar'
    # Última red (21-sep): la herramienta de limpieza del panel, el conector
    # solar y el soporte de laptop, que no abren el título con "soporte". Va
    # al final para no quitarle la ficha al baño ni a la organización.
    if re.search(r'lavadora de paneles|limpieza.{0,30}(panel|solar)|cepillo.{0,30}(taladro|polvo)|'
                 r'poste de extension|\bplumero\b|brocha para limpiar|paneles fotovoltaicos', tn):
        return 'Accesorios y limpieza de paneles solares'
    if re.search(r'(cable|conector|conectores).{0,25}solar|rack-?a-?tiers|\bmc4\b', tn):
        return 'Kits solares y controladores de carga'
    if re.search(r'panel de carga solar|sol-?pak|bateria(s)? solar(es)?', tn):
        return 'Cargadores solares portátiles'
    if re.search(r'bateria de expansion|\bsolix\b|\bbp2000\b', tn): return 'Estaciones de energía'
    if re.search(r'soporte (para|de) (laptop|pc|micr[oó]fono|monitor)|soporte ajustable|'
                 r'soporte de (brazo|silicona)|\bmount-?pc\b', tn):
        return 'Soportes para dispositivos'
    return None


def sub_tv_pulgadas(tn):
    """Para el televisor que no dice HD ni 4K: el tamaño lo delata. Hoy
    ninguna pantalla de 43" o más se vende en HD, y ninguna de 32" en 4K."""
    m = re.search(r'(\d{2,3})\s*(?:"|\'\'|pulg|pulgadas|\bin\b|\bp\b)', tn)
    if not m:
        return None
    pulg = int(m.group(1))
    if pulg >= 43:
        return '4K'
    if 24 <= pulg <= 40:
        return 'HD'
    return None
