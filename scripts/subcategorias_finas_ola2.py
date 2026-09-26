#!/usr/bin/env python3
"""Segunda ola de subcategorías finas: las subcategorías que eran un cajón
de miles de fichas (Muebles/Sillas, Bocinas/Mediana, Videojuegos/Software,
Climatización/Ventiladores, Instrumentos/Guitarras, Celulares/Android,
Laptops/Oficina, Monitores/Oficina, Autos/Bicicletas) se reparten por tipo,
plataforma, tamaño o marca -- lo que se usa para elegir en cada una.

Cada entrada de OLA2 dice qué categoría toca, qué subcategorías viejas
absorbe (None = toda la categoría), la lista fina en orden y el repartidor.
Lo que el repartidor no reconoce se queda en `resto` (o en su subcategoría
vieja si `resto` es None).
"""
import re
from subcategorias_finas import _primera


def _c(ramas):
    return [(sub, re.compile(rx)) for sub, rx in ramas]


# ------------------------------------------------------------ Muebles/Sillas
SILLAS = ['Sillas de oficina', 'Sillas gamer', 'Sillas de comedor', 'Taburetes y bancos',
          'Sillas plegables y de camping', 'Sillones y reclinables', 'Sillas de exterior',
          'Sillas infantiles', 'Sillas de espera y visitas', 'Mecedoras y colgantes']
_SILLAS = _c([
    ('Sillas gamer', r'\bgamer|\bgaming\b|silla de juegos?|de videojuegos|\brgb\b|racing|estilo carreras'),
    ('Sillas infantiles', r'\binfantil|para ninos?\b|\bninos?\b|\bnina\b|\bbebe|\bkids?\b|periquera|silla alta|trona|\bbooster\b'),
    ('Mecedoras y colgantes', r'mecedora|\bmecedor|silla colgante|\bhamaca\b|\bhuevo\b|\bcolgante\b|silla nido|balancin|planeador|\bglider\b'),
    ('Sillones y reclinables', r'\bsillon(es)?\b|\breclinable|\breclinabl|\bsofa\b|\blove ?seat|\bpuff?\b|\bpouf\b|\bbutaca|\bchaise|\bdiván|\bdivan\b|\bpoltrona|de masaje|\bmasajeador|\brelax\b'),
    ('Sillas plegables y de camping', r'\bplegable|\bcamping\b|\bcampismo\b|\bplaya\b|\bbeach\b|\bfolding\b|\bportatil\b|\bpesca\b|\bpicnic\b|\bconcierto|\bestadio'),
    ('Sillas de exterior', r'\bexterior|\bjardin\b|\bterraza\b|\bpatio\b|\boutdoor\b|\balberca\b|\bpiscina\b|\bbalcon\b|\bratan\b|\brattan\b|\bmimbre\b|\bcamastro|\btumbona|\badirondack\b'),
    ('Taburetes y bancos', r'\btaburete|\bbancos?\b(?! (de trabajo|de pesas|de peso))|\bbanquito|\bbanqueta|\bbanquillo|\bbar\b|\bstool\b|\bbarra de cocina\b|\bisla\b|\bescalon\b|\bpuf\b'),
    ('Sillas de espera y visitas', r'\bespera\b|\bvisitas?\b|\brecepcion\b|\bconsultorio|\bclinica|\biglesia|\bconferencia|\bcapacitacion|\bauditorio|\bapilable|\bpaleta\b|\btableta de escritura|\bescolar\b|\bpupitre'),
    ('Sillas de oficina', r'\boficina\b|\bescritorio\b|\bejecutiv|\bergonomic|\bgerencial|\bsecretarial|\boperativa|\bgiratoria|\bcon ruedas\b|\bmalla\b|\bmesh\b|\bcomputadora\b|\bestudio\b|\bdirector|\bde trabajo\b|\bhome office\b|\boffice\b'),
    ('Sillas de comedor', r'\bcomedor\b|\bcocina\b|\bdining\b|\btapizad|\bde madera\b|\bset de \d|\bjuego de \d|\bpaquete de \d|\b\d sillas\b|\bsillas? (moderna|nordica|escandinava|vintage|industrial|acrilic|de metal|de plastico|tiffany|eames|tulip)|\bbanca de comedor'),
])


def sub_silla(tn):
    return _primera(tn, _SILLAS, {'Sillas de comedor': 30, 'Sillas de oficina': 10})


# ----------------------------------------------------------------- Bocinas
BOCINAS = ['Bluetooth portátiles', 'De fiesta y karaoke', 'Para PC y escritorio', 'De estantería y Hi-Fi',
           'Subwoofers', 'Empotrables y de exterior', 'Bafles y audio profesional', 'Amplificadores y receptores',
           'Barras de sonido', 'Bocinas para auto', 'Radios y reproductores']
_BOCINAS = _c([
    ('Barras de sonido', r'barra de sonido|\bsoundbar|\bsound ?bar\b'),
    ('Bocinas para auto', r'\bpara (auto|coche|carro|camioneta|moto|motocicleta|marina)|\bcoaxial|\btriaxial|\b6x9\b|\b6 ?x ?9\b|\bautomotriz|\bpara vehiculo|\b12 ?v\b.{0,20}(altavoz|bocina)|\bmarinas?\b|\bpara barco'),
    ('Subwoofers', r'\bsubwoofer|\bsub ?woofer|\bsubgrave|\bbajos activos\b'),
    ('Amplificadores y receptores', r'\bamplificador|\breceptor|\breceiver\b|\bpreamplificador|\bpreamp\b|\bmezcladora|\bmixer\b|\bdac\b|\bconsola de audio'),
    ('Radios y reproductores', r'\bradio (am|fm|portatil|de bolsillo|de emergencia|despertador|solar)|\bam/fm\b|\bboombox\b.{0,30}(cd|casete|cassette|radio am)|\breproductor de (cd|casete|cassette|dvd)|\btocadiscos|\bcd player\b|\bgrabadora\b|\bcasetera'),
    ('De fiesta y karaoke', r'\bkaraoke|\bfiesta|\bparty\b|\bdj\b|\bmicrofono inalambrico|con microfono|\bluces led\b|\bpartybox|\btorre de sonido|\bboombox pro|\bcon ruedas\b|\btrolley\b|\bbafle\b.{0,30}bluetooth'),
    ('Bafles y audio profesional', r'\bbafle|\bpa\b|\bmonitor de estudio|\bmonitores de estudio|\bstudio monitor|\bprofesional|\blinea de arreglo|\bline array|\bpasiv[oa]s?\b|\bactiv[oa]s? de \d+|\b\d{3,4} ?w\b.{0,20}(bafle|pasiv)|\bescenario|\bpa system|\bpara eventos|\bde 15 pulgadas|\bde 12 pulgadas|\bde 18 pulgadas|\bgabinete de audio\b|\bmegafono|\bperifoneo|\bde piso\b.{0,20}(torre|columna)|\bdriver\b|\bcompresion\b|\bdiafragma'),
    ('Empotrables y de exterior', r'\bempotra|\bde techo\b|\bin-?ceiling|\bin-?wall\b|\bde pared\b|\bpara pared\b|\bexterior|\boutdoor|\bjardin\b|\bpatio\b|\bde roca|\bimpermeable.{0,30}(pared|exterior)|\bwall mount|\bpara intemperie'),
    ('Para PC y escritorio', r'\bpara (pc|computadora|ordenador|laptop|escritorio|monitor)\b|\bde escritorio|\bdesktop\b|\bpc speaker|\b2\.1\b|\b2\.0\b.{0,20}(pc|computadora|escritorio)|\busb\b.{0,30}(pc|computadora|escritorio)|\bgaming\b.{0,20}(pc|escritorio)|\bminibocina\b.{0,20}(usb|pc)'),
    ('De estantería y Hi-Fi', r'\bestanteria|\bbookshelf|\bhi-?fi\b|\bhifi\b|\balta fidelidad|\bde torre\b|\btorre de audio|\bfloor ?standing|\bde piso\b|\bcanal central|\bcenter channel|\bhome theater|\bcine en casa|\b5\.1\b|\b7\.1\b|\bsistema de altavoces\b|\bde salon\b|\bde sala\b|\bstereo de casa|\bcomponentes? (de )?audio|\bminicomponente|\bmicrocomponente|\bequipo de sonido'),
    ('Bluetooth portátiles', r'\bbluetooth|\bportatil|\binalambric|\bwireless|\bimpermeable|\bipx?[4-8]\b|\brecargable|\btws\b|\bmini\b|\bde mano\b|\bbocina\b|\baltavoz|\bspeaker|\bparlante'),
])


_BT_CABEZA = re.compile(r'^(?:\S+ ){0,2}(bocina|altavoz|parlante|speaker|minialtavoz|minibocina)s? (bluetooth|portatil|inalambric|wireless|portable)')
_BT_SENAS = re.compile(r'\bportatil|\bbluetooth|\brecargable|\bbateria|\btws\b|\bportable')
_FIJA = re.compile(r'\bempotra|\bde techo\b|\bde pared\b|\bpara pared\b|\bin-?wall|\bin-?ceiling|\bde roca|\bwall mount')


def sub_bocina(tn):
    sub = _primera(tn, _BOCINAS, {'Bluetooth portátiles': 60, 'De estantería y Hi-Fi': 15})
    if sub in ('Empotrables y de exterior', 'Subwoofers', 'Bafles y audio profesional', 'De estantería y Hi-Fi') \
            and _BT_CABEZA.search(tn) and not re.search(r'karaoke|fiesta|party|\bbafle', tn):
        return 'Bluetooth portátiles'
    if sub == 'Empotrables y de exterior' and _BT_SENAS.search(tn) and not _FIJA.search(tn):
        return 'Bluetooth portátiles'
    return sub


# ------------------------------------------------------------- Videojuegos
VIDEOJUEGOS = ['Juegos PS5', 'Juegos PS4', 'Juegos Xbox', 'Juegos Nintendo Switch', 'Juegos para PC',
               'Juegos retro y otras plataformas', 'Consolas PlayStation', 'Consolas Xbox', 'Consolas Nintendo',
               'Consolas retro y portátiles', 'Controles y gamepads', 'Volantes, arcade y simuladores',
               'Realidad virtual', 'Cargadores, bases y soportes', 'Fundas, micas y protectores',
               'Cables y adaptadores', 'Tarjetas y suscripciones', 'Otros accesorios gamer']
_VJ_PLATAFORMA = [
    ('Juegos PS5', r'\bps ?5\b|playstation ?5\b|\bplaystation 5\b'),
    ('Juegos PS4', r'\bps ?4\b|playstation ?4\b'),
    ('Juegos Xbox', r'\bxbox\b|\bxsx\b|\bxb1\b|\bxbsx\b|\bxone\b|\bx1\b|\bxbox360|\bx360\b'),
    ('Juegos Nintendo Switch', r'\bswitch\b|\bnintendo\b|\bnsw\b'),
    ('Juegos para PC', r'\bpc\b|\bsteam\b|\bwindows\b'),
    ('Juegos retro y otras plataformas', r'\bps ?[123]\b|playstation ?[123]\b|\bpsp\b|\bps vita\b|\bvita\b|\bwii\b|\bgamecube\b|\bnintendo (64|ds|3ds)\b|\b3ds\b|\bnds\b|\bgame ?boy|\bsnes\b|\bnes\b|\bsega\b|\bgenesis\b|\bdreamcast\b|\bmega ?drive|\batari\b|\bretro\b'),
]
_VJ = _c([
    ('Realidad virtual', r'\brealidad virtual|\bvr\b|\bmeta quest|\boculus|\bpsvr|\bps vr|\bhtc vive|\bpico 4|\bvisor\b.{0,20}(vr|virtual)'),
    ('Volantes, arcade y simuladores', r'\bvolante|\bpedales?\b|\bracing wheel|\barcade|\bfight ?stick|\bpalanca arcade|\bsimulador|\bcockpit|\bhotas\b|\bflight stick|\bgun\b.{0,10}(controller|control)|\bpistola\b|\bmaquinita|\bfreno de mano|\bhandbrake|\bshifter|\bpalanca de cambios'),
    ('Controles y gamepads', r'\bcontrol(es)?\b(?! remoto)|\bcontrolador(es)?\b|\bgamepad|\bmando\b|\bmandos\b|\bcontroller|\bjoysticks?\b|\bjoy-?con|\bdualsense|\bdualshock|\bpro controller|\bjoycon|\bnunchuk|\bwiimote|\bboton(es)? trasero|\bpaddles?\b|\bsplit pad'),
    ('Cargadores, bases y soportes', r'\bcargador|\bcarga\b|\bbase de carga|\bestacion de carga|\bdock\b|\bdocking|\bsoporte|\bstand\b|\bbateria|\bpilas?\b|\bpower bank|\bventilador|\benfriador|\bcooling'),
    ('Fundas, micas y protectores', r'\bfunda|\bestuche|\bcase\b|\bmica|\bprotector|\bskin\b|\bcubierta|\bcarcasa|\bbolsa|\bmochila|\bgrips?\b|\bthumb ?grips?|\btapas? de joystick|\bcubre|cristal templado|vidrio templado|tempered glass|placa frontal|faceplate|dust cover|antipolvo|\bempunadura|\bsling\b'),
    ('Cables y adaptadores', r'\bcable|\badaptador|\bconvertidor|\bhdmi\b|\bav\b|\bextension\b|\bhub\b|\bconector|\bmemoria|\btarjeta (micro ?sd|sd)|\bdisco duro|\bssd\b|\breceptor\b'),
    ('Tarjetas y suscripciones', r'\btarjeta (de )?(regalo|prepago|psn|xbox|nintendo|steam|roblox|fortnite)|\bgift card|\bsuscripcion|\bgame pass|\bps plus|\bplaystation plus|\bnintendo switch online|\bmembresia|\bv-?bucks|\brobux|\bcodigo digital|\bdigital code'),
    ('Otros accesorios gamer', r'\baccesori|\bkit\b|\bauricular|\baudifono|\bheadset|\bmicrofono|\bcamara\b|\bteclado|\bmouse\b|\btapete|\bmousepad|\bsilla|\bluz\b|\blampara|\bfigura|\bamiibo|\bllavero|\bposter|\bpeluche|\btaza|\bplayera'),
])
_VJ_CONSOLA = re.compile(r'^(?:\S+ ){0,2}consola\b|\bconsola (de )?(videojuegos|portatil|retro|nueva|nintendo|xbox|playstation|ps\d)|'
                         r'^(?:\S+ ){0,3}(playstation ?5|ps5|playstation ?4|ps4|xbox (series|one)|nintendo switch( 2| lite| oled)?|steam deck|rog ally|legion go)\b.{0,40}\b(consola|\d+ ?(gb|tb)|slim|pro|digital|edicion|bundle|paquete|blanco|negro)\b|'
                         r'\bsteam deck\b|\brog ally\b|\blegion go\b|\bmsi claw\b|\bconsola\b|'
                         # El nombre pelado de la consola, sin más palabras, también es
                         # la consola: "Nintendo Switch OLED" caía en juegos.
                         r'^(nintendo switch( 2| lite| oled)?|playstation ?[45]|ps ?[45]|'
                         r'xbox (series [sx]|one [sx]?)|wii ?u?)\s*$')
_VJ_ACCESORIO_DE_CONSOLA = re.compile(r'\b(para|for|compatible con) (la )?(consola|ps\d|playstation|xbox|nintendo|switch)|\bcontrol|\bmando\b|\bfunda|\bcable|\bcargador|\bsoporte|\bbase\b|\bmica|\bskin|\badaptador|\bjuego\b|\bvideojuego')


def sub_videojuego(tn, sub_vieja=None):
    # Primero lo que no es juego ni consola.
    acc = _primera(tn, _VJ, {'Otros accesorios gamer': 40, 'Cables y adaptadores': 10, 'Cargadores, bases y soportes': 5})
    es_consola = _VJ_CONSOLA.search(tn) and not re.search(r'\b(para|for|compatible con) (la )?(consola|ps\d|playstation|xbox|nintendo|switch)\b', tn)
    if es_consola and not re.search(r'\bjuego\b|\bvideojuego\b|\bedicion (estandar|deluxe|coleccionista)\b', tn) and (sub_vieja == 'Consolas' or not acc):
        if re.search(r'playstation|\bps ?\d\b|\bpsp\b', tn): return 'Consolas PlayStation'
        if re.search(r'\bxbox\b', tn): return 'Consolas Xbox'
        if re.search(r'\bnintendo\b|\bswitch\b|\bwii\b|\b3ds\b', tn): return 'Consolas Nintendo'
        return 'Consolas retro y portátiles'
    if sub_vieja == 'Accesorios' or (acc and sub_vieja != 'Software'):
        return acc or 'Otros accesorios gamer'
    if sub_vieja == 'Software' or re.search(r'\bjuego\b|\bvideojuego|\bedicion (estandar|deluxe|coleccionista|especial)\b|\bfisico\b', tn) or not acc:
        for sub, rx in _VJ_PLATAFORMA:
            if re.search(rx, tn):
                return sub
        return acc or ('Juegos retro y otras plataformas' if sub_vieja == 'Software' else None)
    return acc


# ------------------------------------------------------- Climatización
VENTILADORES = ['Ventiladores de techo', 'Ventiladores de pedestal', 'Ventiladores de torre',
                'Ventiladores de piso e industriales', 'Ventiladores de mesa y clip',
                'Ventiladores portátiles y de mano', 'Ventiladores de pared', 'Extractores y ventilación',
                'Ventiladores nebulizadores', 'Aspas y refacciones de ventilador']
_VENT = _c([
    ('Aspas y refacciones de ventilador', r'\baspas?\b(?! de)|\bmotor (de|para) ventilador|\brepuesto|\breemplazo|\bcapacitor|\bcontrol remoto para|\brejilla (de|para) ventilador|\bkit de (luz|control)|\bcadena|\bbase (de|para) ventilador|\bcubierta (de|para) ventilador|\bcable de (ventilador|luz)|\bregulador de velocidad'),
    ('Ventiladores de techo', r'\bde techo\b|\bceiling|\bplafon\b|\bcon luz\b|\bcon lampara|\bcon led\b|\bcandil'),
    ('Extractores y ventilación', r'\bextractor|\bextraccion|\bexhaust|\bde escape\b|\bcentrifug|\baxial|\bducto|\bconducto|\binline\b|\bventilacion\b|\bpara bano\b|\bde bano\b|\brecirculador|\bturbina|\bcortina de aire|\bcampana\b|\bsoplador|\bblower|\binvernadero|\bgallinero|\bgranja'),
    ('Ventiladores nebulizadores', r'\bnebuliz|\bmisting|\bde agua\b|\bvapor de agua|\bhumidificador\b.{0,20}ventilador|\bventilador\b.{0,30}(rocio|niebla|bruma|atomiz)|\bcon rocio'),
    ('Ventiladores portátiles y de mano', r'\bsin aspas\b|\bde mano\b|\bportatil|\bmini\b|\bde cuello\b|\bcuello\b|\bpersonal|\bde bolsillo|\bcon bateria|\brecargable|\busb\b|\bplegable|\bcolgante\b|\bcochecito|\bcarriola|\bpara viaje|\bde viaje|\bde mano\b|\bventilador (turbo|pequeno)|\bcon cordon'),
    ('Ventiladores de mesa y clip', r'\bde mesa\b|\bde escritorio\b|\bcon clip\b|\bclip\b|\bde clip\b|\bsobremesa|\bcompacto\b|\bde buro\b|\bde oficina\b|\bcircular\b|\bcirculador de aire|\bvornado'),
    ('Ventiladores de pared', r'\bde pared\b|\bpara pared|\bwall\b|\bmural\b|\boscilante de pared'),
    ('Ventiladores de torre', r'\bde torre\b|\btorre\b|\btower\b|\bsin aspas\b(?!.*(usb|recargable|portatil|mini|de mesa|escritorio|de mano|bateria))|\bbladeless\b(?!.*(usb|recargable|portatil|mini))|\bde columna'),
    ('Ventiladores de piso e industriales', r'\bindustrial|\bde piso\b|\bde suelo\b|\bde alta velocidad|\bde tambor|\bde barril|\bdrum\b|\bbarril|\bcomercial|\bde taller|\bde bodega|\bde almacen|\bfloor\b|\bpotente\b|\bmetalico\b|\b\d{2} ?pulgadas\b.{0,20}(piso|industrial)|\bde caja\b|\bbox fan'),
    ('Ventiladores de pedestal', r'\bde pedestal\b|\bpedestal\b|\bde pie\b|\bstand fan|\baltura ajustable|\boscilante\b|\bde \d{2} ?pulgadas\b'),
])


def sub_ventilador(tn):
    return _primera(tn, _VENT, {'Ventiladores de pedestal': 25, 'Ventiladores portátiles y de mano': 5})


CALEFACTORES = ['Calefactores cerámicos y de aire', 'Calefactores de aceite', 'Calefactores infrarrojos y de cuarzo',
                'Calefactores de gas', 'Calefactores de pared y baño', 'Calefactores de exterior y patio',
                'Calefactores para pies y personales', 'Chimeneas eléctricas', 'Refacciones de calefactor',
                'Tapetes y alfombras calefactoras']
_CALEF = _c([
    # El elemento calefactor es la pieza suelta, casi siempre de una secadora
    # o de un electrodoméstico: 234 fichas en el cajón de los calefactores
    # cerámicos, que es donde va el aparato entero.
    ('Refacciones de calefactor', r'\brepuesto|\breemplazo|\belemento calefactor|\bresistencia calefactora|\btermostato (de|para)|\bresistencia (de|para)|\bcontrol remoto para|\bfiltro (de|para)|\bpiloto\b|\bvalvula\b|\bquemador\b|\bmanguera\b|\bregulador\b'),
    # El tapete calefactor no es un calefactor de pie: se pisa o se pone bajo
    # algo, no calienta el aire. Estaban repartidos entre dos cajones (101 en
    # «cerámicos y de aire» y 324 en «para pies y personales») porque la regla
    # de este último se quedaba con «alfombrilla» y «tapete».
    ('Tapetes y alfombras calefactoras', r'\balfombra calefact|\balfombrilla calefact|'
                                          r'\btapete calefact|\bmanta calefact|\bmanta termica\b|'
                                          r'\balmohadilla calefact|\bcalefactora?\b.{0,12}(alfombra|tapete)|'
                                          r'\b(alfombra|alfombrilla|tapete)\b.{0,18}(calefactor|calefaccion|termic|calienta)'),
    ('Chimeneas eléctricas', r'\bchimenea|\bfireplace|\bhogar electrico|\bestufa de lena electrica|\bllama\b'),
    ('Calefactores de exterior y patio', r'\bexterior|\bpatio\b|\bterraza\b|\bjardin\b|\boutdoor|\bde hongo\b|\bhongo\b|\bpiramide|\bde pie para (patio|terraza|exterior)|\bpirámide|\bfogata'),
    ('Calefactores de gas', r'\bde gas\b|\bgas (lp|natural|butano|propano)|\bpropano|\bbutano\b|\ba gas\b|\bcatalitic|\bceramica a gas'),
    ('Calefactores de pared y baño', r'\bde pared\b|\bpara pared|\bpara bano\b|\bde bano\b|\bwall\b|\bconvector\b|\bempotra|\bde montaje en pared|\bmural'),
    ('Calefactores para pies y personales', r'\bpara pies\b|\bcalienta ?pies|\bde pies\b|\bpersonal\b|\bde escritorio\b|\bbajo escritorio|\bmini\b|\bportatil\b|\bde mano\b|\bpara oficina\b|\busb\b|\balfombrilla|\btapete'),
    ('Calefactores de aceite', r'\bde aceite\b|\baceite\b|\bradiador|\boil\b'),
    ('Calefactores infrarrojos y de cuarzo', r'\binfrarroj|\bcuarzo|\bhalogeno|\bde carbono|\bde fibra de carbono|\bde vela|\bradiante|\bde tubo|\bpanel radiante|\bpanel calefactor'),
    ('Calefactores cerámicos y de aire', r'\bceramic|\bde aire\b|\bventilador\b|\bde torre\b|\btorre\b|\bfan heater|\bcalentador de ambiente|\bcalefactor electrico|\bcalentador electrico|\bcalefactor\b|\bcalentador\b|\bestufa electrica|\bheater'),
])


def sub_calefactor(tn):
    return _primera(tn, _CALEF, {'Calefactores cerámicos y de aire': 40, 'Calefactores para pies y personales': 10})


# ---------------------------------------------------- Instrumentos/Guitarras
GUITARRAS = ['Guitarras acústicas', 'Guitarras electroacústicas', 'Guitarras clásicas', 'Guitarras eléctricas',
             'Bajos', 'Ukuleles', 'Violines, mandolinas y otras cuerdas', 'Amplificadores de guitarra y bajo',
             'Pedales y efectos', 'Cuerdas de guitarra y bajo', 'Fundas, soportes y atriles', 'Accesorios de guitarra']
_GUIT = _c([
    ('Cuerdas de guitarra y bajo', r'^(?:\S+ ){0,3}cuerdas?\b(?! (de|para) (violin|viola|cello|violonchelo|contrabajo|arpa|piano))|\bjuego de cuerdas\b|\bset de cuerdas\b|\bcuerdas? (para|de) (guitarra|bajo|ukulele|electrica|acustica|clasica)|\bstrings?\b(?! (violin|viola|cello))|\bencordado|\bencordadura|\bcuerda (individual|suelta)|\brotosound\b|\btru bass\b'),
    ('Pedales y efectos', r'\bpedal(es|era)?\b|\befectos?\b|\boverdrive|\bdistorsion|\bdistortion|\breverb|\bdelay\b|\blooper|\bwah\b|\bfuzz\b|\bchorus\b|\bcompresor\b|\bafinador de pedal|\bmultiefectos|\bprocesador de (guitarra|efectos)|\bstompbox'),
    ('Amplificadores de guitarra y bajo', r'\bamplificador|\bamp\b|\bcombo\b.{0,20}(guitarra|bajo|w\b)|\bcabezal|\bgabinete\b.{0,20}(guitarra|bajo|\d+x\d+)|\bcabinet\b|\bbafle para (guitarra|bajo)'),
    ('Fundas, soportes y atriles', r'\bfunda|\bestuche|\bcase\b|\bgig ?bag|\bsoporte|\bstand\b|\batril|\bcolgador|\bgancho de pared|\brack (de|para) guitarra|\bexhibi'),
    ('Accesorios de guitarra', r'\bcapo|\bcapotrasto|\bcejilla|\bcorrea|\bstrap\b|\bpuas?\b|\bpicks?\b|\bplumillas?\b|\bafinador|\btuner\b|\bslide\b|\bclavij|\bafinadores?\b|\bpastillas?\b|\bpickups?\b|\bpuente\b|\bcejuela|\bsillin|\bselector\b|\bpotenciometro|\bjack\b|\bcable (para|de) (guitarra|instrumento)|\bcable de instrumento|\btrastes?\b|\bgolpeador|\bpickguard|\bperillas?\b|\bknobs?\b|\bmastil|\bcuello de guitarra|\bdiapason|\bmetronomo|\bhumidificador|\bkit de (limpieza|mantenimiento|herramientas)|\blimpiador|\bpulidor|\bcuerdas de repuesto|\bboton (de|para) correa|\bstrap ?lock|\bcapodastro|\bejercitador de dedos|\bentrenador de dedos|\bhummer|\bwhammy|\bpalanca de (vibrato|tremolo)|\btremolo\b|\bcubierta de (puente|pastilla)|\btapa\b|\btornillos?\b|\bmecanismo de afinacion'),
    ('Ukuleles', r'\bukulele|\bukelele|\bukulel'),
    ('Violines, mandolinas y otras cuerdas', r'\bmandolina|\bbanjo|\bcharango|\bcuatro\b|\bbalalaika|\bbouzouki|\blaud\b|\bbandurria|\bvihuela|\bguitarron|\bbajo sexto|\bbajo quinto|\brequinto|\bjarana|\bcavaquinho|\btres cubano|\bdobro|\bresonador|\bharpa|\barpa\b|\blira\b|\bcitara|\bsitar\b|\bkalimba|\bviolonchelo|\bcello\b|\bviolin\b|\bviola\b|\bcontrabajo|\bshamisen\b|\bektara\b|\biktara\b|\btumbi\b'),
    ('Bajos', r'\bbajo (electrico|acustico|electroacustico|de \d cuerdas|precision|jazz)|\bbajos?\b|\bbass\b|\bprecision bass|\bjazz bass|\bp-?bass|\bj-?bass'),
    ('Guitarras eléctricas', r'\belectrica|\belectric guitar|\bstratocaster|\btelecaster|\bles paul|\bsg\b|\bibanez\b.{0,20}(rg|gio|grg|s\d)|\bjackson\b|\bschecter|\besp ltd|\bprs\b|\bepiphone\b(?!.*acustica)|\bsquier\b|\bgretsch\b|\bflying v|\bexplorer\b|\bhollow ?body|\bsemi ?hollow|\bhumbucker|\bdiestros?\b.{0,20}electric|\bzurd[oa]s?\b.{0,20}electric'),
    ('Guitarras electroacústicas', r'\belectroacustic|\belectro-?acustic|\bacoustic-?electric|\bacustica electrica|\bcon ecualizador|\bcon preamp|\bcon pastilla|\bcon eq\b'),
    ('Guitarras clásicas', r'\bclasica|\bde nylon|\bcuerdas de nylon|\bflamenc|\bespanola|\bcriolla|\brequinto|\bconcierto\b|\bclassical'),
    ('Guitarras acústicas', r'\bacustica|\bacoustic|\bdreadnought|\bfolk\b|\bjumbo\b|\bparlor|\bconcert\b|\bauditorium|\bcuerdas de acero|\bde 12 cuerdas|\btravel guitar|\bguitarra de viaje|\bguitarra\b'),
])


def sub_guitarra(tn):
    return _primera(tn, _GUIT, {'Accesorios de guitarra': 5, 'Guitarras acústicas': 30})


# ---------------------------------------------------------- Celulares/Android
ANDROID = ['Samsung Galaxy', 'Motorola', 'Xiaomi, Redmi y POCO', 'Honor y Huawei', 'OPPO, Vivo y Realme',
           'Google Pixel', 'OnePlus, Nothing y Sony', 'ZTE, TCL, Infinix y Tecno', 'Nokia y otras marcas', 'Reacondicionados']
_ANDROID = _c([
    ('Samsung Galaxy', r'\bsamsung\b|\bgalaxy\b'),
    ('Motorola', r'\bmotorola\b|\bmoto ?[geczx]\b|\bmoto edge|\bmoto razr|\brazr\b|\bmoto\b'),
    ('Xiaomi, Redmi y POCO', r'\bxiaomi\b|\bredmi\b|\bpoco\b|\bmi (note|10|11|12|13|14)\b'),
    ('Honor y Huawei', r'\bhonor\b|\bhuawei\b|\bnova \d|\bmagic ?\d|\bp\d0\b|\bmate \d'),
    ('OPPO, Vivo y Realme', r'\boppo\b|\bvivo\b|\brealme\b|\breno ?\d|\bfind x|\biqoo'),
    ('Google Pixel', r'\bgoogle pixel\b|\bpixel \d|\bpixel (fold|pro|a)\b'),
    ('OnePlus, Nothing y Sony', r'\boneplus\b|\bnothing phone|\bnothing\b|\bsony\b|\bxperia\b|\bnord\b'),
    ('ZTE, TCL, Infinix y Tecno', r'\bzte\b|\btcl\b|\binfinix\b|\btecno\b|\bnubia\b|\bblade\b|\baxon\b|\bhot \d|\bspark \d|\bcamon\b|\bpova\b'),
    ('Nokia y otras marcas', r'\bnokia\b|\balcatel\b|\blanix\b|\bbmobile\b|\bblackview\b|\bdoogee\b|\bulefone\b|\boukitel\b|\bcubot\b|\bumidigi\b|\bfossibot\b|\bkyocera\b|\bcat\b|\bcrosscall|\bblu\b|\bhotwav\b|\bagm\b|\bhisense\b|\blg\b|\bsoyes\b|\bunihertz\b|\bfairphone|\bsmartphone|\bcelular|\btelefono|\bandroid'),
])


def sub_android(tn):
    if re.search(r'reacondicionad|renewed|\brefurbished|\bseminuevo|\busado\b|\bopen box|\bcertified', tn):
        return 'Reacondicionados'
    return _primera(tn, _ANDROID, {'Nokia y otras marcas': 60})


# ----------------------------------------------------------- Laptops/Oficina
LAPTOPS = ['MacBook', 'Chromebook', '2 en 1 y convertibles', 'Ultraligeras (13" y 14")', 'Laptops de 15" y 16"',
           'Laptops de 17" o más', 'Laptops básicas y mini', 'Workstation y empresariales', 'Gamer']
_RX_PULG = re.compile(r'(?<!\d)(\d{2}(?:[.,]\d)?)\s?(?:pulgadas|pulg\b|"|”|\'\'|inch|in\b|-inch)')

# "27 x 27 pulgadas" es un tapete, no un monitor de 27". Las medidas en
# forma A x B (y las resoluciones 1920 x 1080) se borran del título ANTES
# de buscar el tamaño de pantalla: ningún monitor ni laptop dice su tamaño
# así, y con ellas dentro entraban a las subcategorías por pulgadas un
# tapete para trasplante de plantas, una puerta para perro de 71 x 28.3
# pulgadas y una funda antipolvo de 24 27 32 pulgadas.
_RX_DIM = re.compile(r'\d+(?:[.,]\d+)?\s?[x×]\s?\d+(?:[.,]\d+)?'
                     r'(?:\s?[x×]\s?\d+(?:[.,]\d+)?)?'
                     r'(?:\s?(?:pulgadas|pulg\b|"|”|cm|mm|m\b|in\b))?')


def _sin_dimensiones(tn):
    return _RX_DIM.sub(' ', tn)


def _pulgadas(tn):
    tn = _sin_dimensiones(tn)
    m = _RX_PULG.search(tn)
    if not m:
        m = re.search(r'(?<!\d)(1[0-9](?:[.,]\d)?)\b(?=\s?(?:fhd|hd|wuxga|qhd|oled|ips|led|touch|tactil))', tn)
    if not m:
        m = re.search(r'\b(?:de|laptop|portatil|notebook|ultrabook) (1[0-9](?:[.,]\d)?)\b(?!\s?(?:gb|tb|mp|hz|w\b|generacion|gen\b|core|nucleos))', tn)
    if not m:
        return None
    try:
        v = float(m.group(1).replace(',', '.'))
    except ValueError:
        return None
    return v if 10 <= v <= 19 else None


def sub_laptop(tn, sub_vieja=None):
    if sub_vieja == 'Gamer' or re.search(r'\bgamer|\bgaming\b|\brtx ?\d|\bgtx ?\d|\btuf\b|\brog\b|\blegion\b|\bnitro\b|\bpredator\b|\bomen\b|\bvictus\b|\bkatana\b|\bcyborg\b|\balienware\b', tn):
        return 'Gamer'
    if re.search(r'\bmacbook\b|\bapple\b.{0,20}\bm[1-5]\b', tn): return 'MacBook'
    if re.search(r'\bchromebook|\bchrome ?os\b', tn): return 'Chromebook'
    if re.search(r'\b2 en 1\b|\b2-en-1\b|\b2-in-1\b|\bconvertible|\byoga\b|\bflip\b|\bx360\b|\bsurface pro\b|\bsurface go\b|\btablet\b.{0,20}(teclado|keyboard)|\bdesmontable|\b360\b', tn):
        return '2 en 1 y convertibles'
    if re.search(r'\bworkstation|\bthinkpad (p|t|x1)|\bprecision \d|\bzbook|\bprobook|\belitebook|\blatitude\b|\bempresarial|\bbusiness\b|\bxeon\b|\bquadro\b|\brtx a\d|\bvpro\b|\bthinkbook', tn):
        return 'Workstation y empresariales'
    if re.search(r'\bceleron|\bpentium|\bn[45]\d{3}\b|\bn100\b|\bn150\b|\bn95\b|\bn200\b|\bathlon\b|\bmini laptop|\bnetbook|\b4 ?gb (de )?ram\b|\bemmc\b|\bmediatek\b|\bde 1[01](\.\d)? pulgadas', tn):
        return 'Laptops básicas y mini'
    p = _pulgadas(tn)
    if p is None:
        return None
    if p >= 17: return 'Laptops de 17" o más'
    if p >= 15: return 'Laptops de 15" y 16"'
    if p >= 12.5: return 'Ultraligeras (13" y 14")'
    return 'Laptops básicas y mini'


# ---------------------------------------------------------- Monitores/Oficina
MONITORES = ['Hasta 22 pulgadas', '23 a 25 pulgadas', '27 pulgadas', '28 a 34 pulgadas', '35 pulgadas o más',
             'Ultrawide y curvos', 'Táctiles e industriales', 'Monitores 4K y profesionales', 'Portátiles', 'Gaming']
_RX_MON = re.compile(r'(?<!\d)(\d{2}(?:[.,]\d)?)\s?(?:pulgadas|pulg\b|"|”|\'\'|inch|in\b|-inch|”)')


def sub_monitor(tn, sub_vieja=None):
    if sub_vieja in ('Portátiles', 'Gaming'):
        return sub_vieja
    if re.search(r'\bportatil|\bextensor de pantalla|\bpantalla portatil|\btriple\b|\bpara laptop\b', tn): return 'Portátiles'
    if re.search(r'\bgamer|\bgaming\b|\b(144|165|170|180|200|240|360) ?hz\b|\bfreesync|\bg-?sync|\bde juego', tn): return 'Gaming'
    if re.search(r'\btactil|\btouch|\bindustrial|\bkiosco|\bkiosk|\bsenalizacion|\bsignage|\bpunto de venta|\bpos\b|\bcaja registradora|\bcarcasa metalica|\bopen frame|\bpara rack|\bmedico|\bquirurgic|\bcctv|\bbnc\b', tn):
        return 'Táctiles e industriales'
    if re.search(r'\bultrawide|\bultra ?wide|\b21:9\b|\b32:9\b|\bcurv|\b1500r\b|\b1800r\b|\b1000r\b|\bsuper ?wide', tn): return 'Ultrawide y curvos'
    if re.search(r'\b4k\b|\buhd\b|\b3840\s?x\s?2160|\b5k\b|\b5120\s?x|\b6k\b|\b8k\b|\bprofesional|\bcreadores|\bcreators?|\bdiseno grafico|\bcolor accurate|\badobe rgb|\bdci-?p3\b|\bcalibrad|\bthunderbolt|\bstudio display|\bpro display', tn):
        return 'Monitores 4K y profesionales'
    tn = _sin_dimensiones(tn)
    m = _RX_MON.search(tn)
    if not m:
        m = re.search(r'(?<!\d)((?:1[5-9]|2[0-9]|3[0-9]|4[0-9])(?:[.,]\d)?)\b(?=\s?(?:fhd|full hd|hd|qhd|wqhd|ips|va\b|led|lcd|oled|tn\b))', tn)
    if not m:
        m = re.search(r'\b(?:monitor|pantalla|de) ((?:1[5-9]|2[0-9]|3[0-9]|4[0-9])(?:[.,]\d)?)\b(?!\s?(?:gb|tb|hz|w\b|ms|puertos|k\b|bit|cm))', tn)
    if not m:
        return None
    v = float(m.group(1).replace(',', '.'))
    if v < 15 or v > 65: return None
    if v <= 22.9: return 'Hasta 22 pulgadas'
    if v <= 25.9: return '23 a 25 pulgadas'
    if v <= 27.9: return '27 pulgadas'
    if v <= 34.9: return '28 a 34 pulgadas'
    return '35 pulgadas o más'


# ------------------------------------------------------------- Bicicletas
BICICLETAS = ['Bicicletas de montaña', 'Bicicletas urbanas y de paseo', 'Bicicletas de ruta', 'Bicicletas infantiles',
              'Bicicletas BMX', 'Bicicletas plegables', 'Bicicletas eléctricas', 'Triciclos y bicicletas de carga',
              'Bicicletas sin pedales y balance', 'Bicicletas de gravel y ciclocross', 'Accesorios para bicicleta']
_BICI = _c([
    ('Accesorios para bicicleta', r'\bbag\b|\bbell\b|\bfork\b|\bcontroller|\bbattery|\bhelmet|\bpulley|\bchain\b|\bsaddle|\bseat\b|\blights?\b|\block\b|\bpump\b|\bbottle|\bcage\b|\btires?\b|\btyres?\b|\btube\b|\bbrakes?\b|\bspeedometer|\bcomputer\b|\bdecal|\bsticker|\bcarrier|\bbox\b|\btrophy|\bmount\b|\bholder|\bcover\b|\bkit\b|\bparts?\b|\bscrews?\b|\bbolts?\b|\bshock\b|\bhandlebar|\bstem\b|\bcrank|\bderailleur|\bhub\b|\bspokes?\b|\btools?\b|\bstand\b|\bdollhouse|\bminiature|\bvinyl|\bconversion|\bconversion|\bkit de conversion|\bcontrolador|\bbateria (de|para) (bici|e-?bike)|\bmodification|\bfender|\bbasket|\bpannier|\bgloves?\b|\bjersey|\bshorts?\b|\bglasses|\bshoes?\b|\bcleats?\b|\bbolsa|\balforja|\bcasco|\bcandado|\bluz\b|\bluces|\bbomba\b|\bportabici|\bsoporte|\brack\b|\bcanasta|\bcanastilla|\bsillin|\basiento|\bmanubrio|\bmanillar|\bpedal(es)?\b|\bcadena\b|\bllanta|\bcamara\b|\brin\b|\brines\b|\bfreno|\bpinon|\bcambio|\bdesviador|\bguardabarro|\bsalpicadera|\btimbre|\bespejo|\bcubierta\b|\bfunda|\bruedas? de entrenamiento|\brueditas|\bpata de cabra|\bsoporte lateral|\bportaequipaje|\bportabultos|\bremolque|\bkit de (reparacion|conversion)|\bherramienta|\bcuentakilometros|\bvelocimetro|\bciclocomputador|\bsilla (infantil|para nino|portabebe)|\bpuños|\bpunos|\bgrips?\b|\bcinta de manubrio|\bplato\b|\bbiela|\bcassette|\bhorquilla|\bsuspension\b(?! completa| delantera| doble)|\bamortiguador|\brayos?\b|\bmasa\b|\bbuje|\bejes?\b|\btrainer\b|\brodillo|\bentrenador\b|\bbotella|\bportabotella|\bguantes|\bjersey|\blentes|\bzapatillas|\bcalas|\bprotector'),
    ('Bicicletas eléctricas', r'\belectrica|\be-?bike|\bebike|\b\d{3,4} ?w\b|\b\d{2} ?v\b.{0,15}\d+ ?ah|\bmotor\b|\bpedelec|\basistencia electrica'),
    ('Bicicletas sin pedales y balance', r'\bsin pedales|\bbalance\b|\bde equilibrio|\bbalance bike|\bcamicleta|\bcorrepasillos|\bde impulso'),
    ('Triciclos y bicicletas de carga', r'\btriciclo|\btres ruedas|\b3 ruedas|\bde carga\b|\bcargo\b|\btandem\b|\bcuadriciclo|\bcuatro ruedas|\bde reparto'),
    ('Bicicletas infantiles', r'\binfantil|\bpara ninos?\b|\bninos?\b|\bnina\b|\bkids?\b|\brodada (12|14|16|20)\b|\br ?(12|14|16|20)\b|\b(12|14|16|20) pulgadas\b|\bde \d a \d anos\b|\bprincesas?\b|\bbarbie\b|\bspiderman|\bpaw patrol|\bfrozen\b|\bcon rueditas|\bruedas de entrenamiento'),
    ('Bicicletas BMX', r'\bbmx\b|\bfreestyle\b|\bacrobacia|\bde trucos'),
    ('Bicicletas plegables', r'\bplegable|\bfolding|\bfoldable|\bbrompton|\bdahon'),
    ('Bicicletas de gravel y ciclocross', r'\bgravel|\bciclocross|\bcyclocross|\bcx\b|\bmixta\b'),
    ('Bicicletas de ruta', r'\bde ruta|\bruta\b|\bde carrera|\bcarreras?\b|\bcarretera|\broad\b|\btriatlon|\baero\b|\bfixie|\bfixed gear|\bpinon fijo|\bde pista|\bcontrarreloj'),
    ('Bicicletas de montaña', r'\bmontana|\bmtb\b|\bmountain|\btodo terreno|\benduro\b|\bdownhill|\btrail\b|\bcross country|\bxc\b|\bdoble suspension|\bsuspension (completa|delantera|doble)|\bhardtail|\brodada (26|27\.5|29)\b|\br ?(26|27\.5|29)\b|\b29er\b'),
    ('Bicicletas urbanas y de paseo', r'\burbana|\bde paseo|\bciudad|\bcity\b|\bcruiser|\bde playa|\bbeach\b|\bvintage|\bretro\b|\bholandesa|\bhibrida|\bhybrid|\bcon canasta|\bcon cesta|\bfemenina|\bpara mujer|\bde mujer|\bcomfort|\bfitness|\bbicicleta\b'),
])


def sub_bicicleta(tn):
    return _primera(tn, _BICI, {'Bicicletas urbanas y de paseo': 40, 'Accesorios para bicicleta': 3})


# --------------------------------------------------------------- Registro
# (categoría, subcategorías viejas que absorbe (None = todas), lista fina,
#  repartidor(tn, sub_vieja), subcategoría para lo que no reconoce)
OLA2 = [
    ('Muebles', ['Sillas'], SILLAS, lambda tn, sv: sub_silla(tn), 'Sillas de comedor'),
    ('Bocinas', None, BOCINAS, lambda tn, sv: sub_bocina(tn), 'Bluetooth portátiles'),
    ('Videojuegos', None, VIDEOJUEGOS, sub_videojuego, None),
    ('Climatización', ['Ventiladores'], VENTILADORES, lambda tn, sv: sub_ventilador(tn), 'Ventiladores de pedestal'),
    ('Climatización', ['Calefactores'], CALEFACTORES, lambda tn, sv: sub_calefactor(tn), 'Calefactores cerámicos y de aire'),
    ('Instrumentos musicales', ['Guitarras', 'Cuerdas'], GUITARRAS, lambda tn, sv: sub_guitarra(tn), 'Accesorios de guitarra'),
    # Los celulares no se dividen por marca (la marca ya es un filtro aparte):
    # solo se separan los reacondicionados. Las subcategorías por marca de
    # una primera versión se absorben de vuelta en Android.
    ('Celulares', ANDROID + ['Android'], ['Android', 'Reacondicionados'],
     lambda tn, sv: 'Reacondicionados' if re.search(r'reacondicionad|renewed|\brefurbished|\bseminuevo|\busado\b|\bopen box|\bcertified', tn) else 'Android', None),
    ('Laptops', None, LAPTOPS, sub_laptop, 'Laptops de 15" y 16"'),
    ('Monitores', None, MONITORES, sub_monitor, '23 a 25 pulgadas'),
    ('Autos, bicicletas y motos', ['Bicicletas'], BICICLETAS, lambda tn, sv: sub_bicicleta(tn), 'Bicicletas urbanas y de paseo'),
]


def afinar_ola2(cat, sub, tn):
    """Gancho para el clasificador y la auditoría: después del reparto
    normal, si (cat, sub) cae en una subcategoría que la ola 2 dividió,
    devuelve la fina."""
    # Los repartos se encadenan: el de toda la categoría (Bocinas) deja
    # 'Bluetooth portátiles' y el de la ola 5 lo vuelve a partir por tipo.
    for c, viejas, lista, f, resto in OLA2:
        if c != cat:
            continue
        if viejas is not None and sub not in viejas and sub not in lista:
            continue
        if sub in lista and not (viejas and sub in viejas):
            continue
        nueva = f(tn, sub)
        sub = nueva or resto or sub
    return sub


# =========================================================== TERCERA OLA
# ------------------------------------- Herramientas/Herramientas eléctricas
HERRAMIENTAS_E = ['Taladros y rotomartillos', 'Atornilladores', 'Sierras', 'Esmeriladoras y pulidoras',
                  'Lijadoras', 'Routers, fresadoras y multiherramientas', 'Compresores y herramienta neumática',
                  'Generadores', 'Hidrolavadoras', 'Flejadoras y empacadoras', 'Pistolas de calor, engrapadoras y clavadoras',
                  'Herramientas de banco', 'Baterías y cargadores de herramienta']
_HERR_E = _c([
    ('Medición', r'\bnivel laser|\bcinta metrica|\bmedidor laser|\bdistanciometro|\bdetector de (metales|pared|vigas|cables)|\bmultimetro|\btermometro|\bcamara termica|\bendoscopio|\bboroscopio|\bflexometro|\bmedidor de (distancia|humedad|espesor)|\bcalibrador|\bvernier|\bnivel\b'),
    ('Baterías y cargadores de herramienta', r'^(?:\S+ ){0,3}(bateria|cargador|pila)s?\b|\bbateria (de repuesto|compatible|para (dewalt|makita|milwaukee|bosch|ryobi|black|truper|craftsman))|\bcargador (de bateria|para (dewalt|makita|milwaukee|bosch|ryobi))'),
    ('Flejadoras y empacadoras', r'\bflejad|\bempacadora|\batadora\b|\bde flejado\b|\bfleje'),
    ('Herramientas de banco', r'\bde banco\b|\bbanco de (trabajo|sierra)|\btaladro de columna|\bsierra de mesa|\bsierra de banco|\besmeril de banco|\btorno\b(?! (de|para) unas)|\bprensa de banco|\bcepilladora|\bcanteadora|\bsierra de cinta|\bsierra cinta'),
    ('Generadores', r'\bgenerador|\bplanta de luz|\bplanta electrica|\binversor generador|\bgrupo electrogeno'),
    ('Hidrolavadoras', r'\bhidrolavadora|\blavadora a presion|\blavadora de presion|\bpressure washer|\bkarcher|\blavadora electrica de alta presion'),
    ('Compresores y herramienta neumática', r'\bcompresor|\bneumatic|\bpistola de (pintar|pintura|aire|impacto neumatica)|\baerografo|\bclavadora neumatica|\bmanguera de aire|\bpistola de clavos neumatica'),
    ('Pistolas de calor, engrapadoras y clavadoras', r'\bpistola de (calor|silicon|silicona|grapas|clavos|pegamento)|\bengrapadora|\bclavadora|\bgrapadora|\bsoplete|\bpistola termica|\bdecapador'),
    ('Routers, fresadoras y multiherramientas', r'\brouter\b|\bfresadora|\brebajadora|\bmultiherramienta|\bmulti ?tool|\boscilante|\bdremel|\bmototool|\bmini ?torno|\brotativa|\bgrabador\b'),
    ('Sierras', r'\bsierra|\bcaladora|\bingletadora|\bsable\b|\bmotosierra|\bcortadora de (azulejo|ceramica|metal|concreto)|\btronzadora|\bcortadora\b'),
    ('Esmeriladoras y pulidoras', r'\besmeril|\bamoladora|\bpulidora|\bpulidor\b|\brectificadora|\bangular\b|\bmini esmeril'),
    ('Lijadoras', r'\blijadora|\blijador\b|\borbital|\bde banda\b|\bcepillo electrico'),
    ('Atornilladores', r'\batornillador|\bdestornillador electrico|\bdesarmador (electrico|inalambrico|a bateria)|\bllave de impacto|\bimpact driver|\bimpacto\b(?!.*taladro)|\bpistola de impacto|\bmatraca electrica'),
    ('Taladros y rotomartillos', r'\btaladro|\brotomartillo|\bmartillo (demoledor|perforador|rompedor|electrico)|\bdemoledor|\bperforador|\bdrill\b|\bpercutor'),
])


def sub_herramienta_e(tn):
    return _primera(tn, _HERR_E, {'Baterías y cargadores de herramienta': 0})


# ----------------------------------------------------- Belleza/Maquillaje
MAQUILLAJE = ['Bases y correctores', 'Polvos, rubores y bronceadores', 'Labiales', 'Sombras y delineadores',
              'Máscaras de pestañas y cejas', 'Pestañas postizas', 'Brochas y esponjas', 'Paletas y sets de maquillaje',
              'Primers y fijadores', 'Organizadores de maquillaje']
_MAQ = _c([
    ('Organizadores de maquillaje', r'\borganizador|\bestuche (de|para) maquillaje|\bneceser|\bcosmetiquera|\bbolsa de maquillaje|\bespejo (de|para) maquillaje|\bespejo\b'),
    ('Brochas y esponjas', r'\bbrochas?\b|\besponjas?\b|\bsponge|\bpuff\b|\bblender\b|\bbrush(es)?\b|\bbeauty ?blender|\bpinceles? (de|para) maquillaje|\bset de brochas|\bkit de brochas|\baplicador|\blimpiador de brochas'),
    ('Pestañas postizas', r'\bpestanas postizas|\bpestanas magneticas|\bpestanas (de|con) (pelo|seda|vison)|\bpestanas (individuales|en racimo|3d|5d)|\bpegamento (de|para) pestanas|\bextensiones de pestanas|\bfalse lashes|\blashes?\b'),
    ('Máscaras de pestañas y cejas', r'\bmascara (de|para) pestanas|\bmascara\b(?!.*(facial|de cara|led|hidratante))|\brimel|\bmascara de pestanas|\bpestanas\b|\bcejas?\b|\blapiz de cejas|\bgel (de|para) cejas|\bpomada (de|para) cejas|\bbrow\b|\bmascara\b'),
    ('Primers y fijadores', r'\bprimer|\bprebase|\bfijador|\bsetting spray|\bspray fijador|\bsellador de maquillaje'),
    ('Paletas y sets de maquillaje', r'\bpaleta|\bpalette|\bkit de maquillaje|\bset de maquillaje|\bestuche de maquillaje|\bmaletin de maquillaje|\bcaja de maquillaje'),
    ('Labiales', r'\blabial|\blabios|\blipstick|\blip (gloss|tint|balm|liner|oil|stain)|\bgloss\b|\bdelineador de labios|\btinte labial|\bbalsamo labial|\blabiales|\bbrillo labial|\blip\b'),
    ('Sombras y delineadores', r'\bsombras?\b|\beyeshadow|\bdelineador|\beyeliner|\blapiz de ojos|\bkajal|\bkohl\b|\bglitter\b|\bpigmento'),
    ('Polvos, rubores y bronceadores', r'\bpolvo (compacto|suelto|translucido|matificante|bronceador)|\brubor|\bblush|\bbronceador|\bbronzer|\biluminador|\bhighlighter|\bcontorno|\bcontour|\bpolvos? (de|para) (rostro|cara|acabado)|\bpolvo\b'),
    ('Bases y correctores', r'\bbase (de|para) maquillaje|\bbase\b|\bfoundation|\bcorrector|\bconcealer|\bbb cream|\bcc cream|\bmaquillaje (liquido|en polvo|compacto|fluido)|\btinted|\btono\b.{0,20}(base|maquillaje)|\bteint\b|\bcobertura'),
])


def sub_maquillaje(tn):
    return _primera(tn, _MAQ, {'Bases y correctores': 15, 'Máscaras de pestañas y cejas': 5})


# ------------------------------------------------------- Joyería/Relojes
RELOJES = ['Relojes para hombre', 'Relojes para mujer', 'Relojes infantiles', 'Relojes deportivos y digitales',
           'Relojes de bolsillo y de pared', 'Correas y extensibles', 'Cajas y estuches para relojes']
_REL = _c([
    ('Cajas y estuches para relojes', r'\bcaja (para|de) relojes|\bestuche (para|de) relojes|\borganizador de relojes|\bexhibidor de relojes|\bwatch (box|case|winder)|\benrollador|\bsoporte (para|de) reloj|\bvitrina'),
    ('Correas y extensibles', r'\bcorreas?\b|\bextensibles?\b|\bpulseras? (para|de|compatible)|\bbandas? (para|de|compatible)|\bmalla (para|de)|\bbrazalete (para|de) reloj|\bhebilla|\bpasadores?\b|\bstrap\b|\bband\b.{0,20}(watch|reloj)|\brepuesto'),
    ('Relojes de bolsillo y de pared', r'\bde bolsillo|\bde pared\b|\bdespertador|\bde mesa\b|\bde escritorio|\bleontina|\bde enfermera|\breloj de arena|\bnixie'),
    ('Relojes infantiles', r'\binfantil|\bpara ninos?\b|\bninos?\b|\bnina\b|\bkids?\b|\bminecraft|\bpaw patrol|\bfrozen\b|\bspiderman|\bspider-man|\bprincesas|\bpokemon|\bmario\b|\bdisney|\bmarvel|\bbatman|\bcars\b|\bpeppa'),
    ('Relojes deportivos y digitales', r'\bdigital|\bg-?shock|\bcasio (f-?91|w-?\d|ae-?\d|a1\d{2}|ca-?\d|dw-?\d)|\bcronometro|\bdeportivo|\bsport\b|\bmilitar|\btactico|\bgarmin|\bpolar\b|\bsuunto|\bcoros\b|\bmonitor de frecuencia|\bpulsometro|\bpodometro|\bled watch|\bcronografo digital'),
    ('Relojes para mujer', r'\bmujer|\bdama|\bwomen|\bwoman|\bfemenin|\bladies|\bpara ella|\bnina\b|\bde ella'),
    ('Relojes para hombre', r'\bhombre|\bcaballero|\bmen\b|\bmens\b|\bmasculin|\bpara el\b|\bgentleman'),
])


def sub_reloj_pulsera(tn):
    return _primera(tn, _REL, {'Relojes para hombre': 5, 'Relojes deportivos y digitales': 10})


# ------------------------------------------------- Refacciones/Para autos
REFACCIONES_AUTO = ['Frenos', 'Suspensión y dirección', 'Motor y transmisión', 'Filtros y aceites', 'Bujías y encendido',
                    'Sistema eléctrico y sensores', 'Faros y luces', 'Enfriamiento y climatización', 'Escape',
                    'Carrocería, espejos y molduras', 'Limpiaparabrisas', 'Interior y tapicería', 'Llaves y cerraduras de auto']
_REF = _c([
    ('Limpiaparabrisas', r'\bwiper|\bwindshield wiper|\blimpiaparabrisas|\bplumas? (de|para) (limpia|parabrisas)|\bwiper|\bescobillas? (de|del) limpia|\bbomba de agua del limpiaparabrisas|\bdeposito (de|del) limpiaparabrisas'),
    ('Llaves y cerraduras de auto', r'\bkey fob|\bkey shell|\bremote key|\bcar key|\bdoor lock actuator|\bignition switch|\bllave (de|para) (auto|coche|carro)|\bcarcasa (de|para) (llave|control)|\bcontrol remoto (de|para) (auto|coche|alarma)|\bchapa (de|para) (puerta|encendido|cajuela)|\bcerradura (de|para) (puerta|auto)|\bswitch de encendido|\bcilindro de encendido|\bactuador de cerradura|\bkeyless|\bllave inteligente|\bfob\b'),
    ('Frenos', r'\bbrakes?\b|\bbrake (pad|disc|rotor|caliper|line|hose|drum|shoe)|\brotors?\b|\bfreno|\bbalatas?\b|\bpastillas? (de|para) freno|\bdiscos? (de|para) freno|\btambor(es)? de freno|\bcaliper|\bmordaza|\bcilindro (maestro|de rueda)|\bbooster\b|\bmanguera de freno|\bliquido de frenos|\bbrake|\babs\b|\bzapatas?\b'),
    ('Suspensión y dirección', r'\bshocks?\b|\bstruts?\b|\bcontrol arm|\btie rod|\bball joint|\bsway bar|\bstabilizer|\bwheel (hub|bearing)|\bhub bearing|\bsteering|\bcoil spring|\bleaf spring|\bbushing|\bsuspension|\bamortiguador|\bresorte|\bespiral|\brotula|\bterminal (de|del)? ?direccion|\bbrazo (de|del)? ?(control|suspension)|\bbarra (estabilizadora|de direccion|de torsion)|\bbieleta|\bhorquilla|\bbuje|\bmaza\b|\bbalero de rueda|\bbaleros?\b|\bcremallera|\bbomba de direccion|\bdireccion (asistida|hidraulica|electrica)|\bstrut\b|\bshock\b|\bcaja de direccion|\btirante|\bsoporte de amortiguador|\bbase de amortiguador'),
    ('Escape', r'\bexhaust|\bmuffler|\bcatalytic|\bo2 sensor|\boxygen sensor|\bescape\b|\bmofle|\bsilenciador|\bcatalizador|\bcatalitico|\bheader|\bcolector de escape|\bmuffler|\bexhaust|\bresonador|\bsensor de oxigeno|\btubo de escape'),
    ('Enfriamiento y climatización', r'\bradiator|\bthermostat|\bwater pump|\bcooling fan|\bcondenser|\bevaporator|\ba/?c compressor|\bblower|\bheater core|\bcoolant|\bintercooler|\bradiador|\btermostato|\bbomba de agua|\bventilador (de|del) (motor|radiador)|\bmotoventilador|\bcondensador|\bevaporador|\bcompresor (de|del) (aire|a/c|ac)|\bmanguera (de|del) radiador|\bdeposito (de|del) (anticongelante|refrigerante)|\banticongelante|\brefrigerante|\bcalefaccion\b|\bnucleo de calefaccion|\bmotor del soplador|\bblower motor|\btapon de radiador|\binterenfriador|\bintercooler'),
    ('Faros y luces', r'\bheadlights?\b|\bheadlamp|\btail ?lights?\b|\bfog (light|lamp)|\bturn signal|\bled bulbs?\b|\bbulbs?\b|\bdaytime running|\blight bar\b|\bfaros?\b|\bfaro\b|\bcalaveras?\b|\bluz (antiniebla|de freno|trasera|de reversa|de dia|de cortesia|de placa|led para|de niebla)|\bfocos? (h[1-9]|h1[0-3]|9005|9006|9007|led)|\bheadlight|\btail ?light|\bhalogeno|\bxenon|\bhid\b|\bluces? (led )?(para|de) (auto|coche|carro|camioneta)|\bbarra de luz|\bbarra led|\bcuartos?\b.{0,10}(luz|led|delantero)|\bdrl\b|\bluz antiniebla|\bcubierta de (luz|faro)|\bmica (de|para) (faro|calavera)|\bantiniebla|\bestrobo|\btorreta|\bluz de emergencia'),
    ('Bujías y encendido', r'\bspark plugs?\b|\bignition coil|\bignition\b|\bglow plug|\bdistributor\b|\bbujias?\b|\bbobinas? (de|para) encendido|\bcables? (de|para) bujia|\bdistribuidor|\bmodulo de encendido|\bspark plug|\bignition coil|\btapa de distribuidor|\brotor de distribuidor|\bcable de bujias'),
    ('Sistema eléctrico y sensores', r'\bsensors?\b|\bswitch\b|\brelay\b|\bfuse\b|\balternator|\bstarter\b|\bmodule\b|\bharness|\bconnector|\bactuator|\bfuel pump|\binjector|\bthrottle body|\bvoltage regulator|\bwiring|\bsensor(es)?\b|\balternador|\bmarcha\b|\bmotor de arranque|\bstarter\b|\brelevador|\brele\b|\bfusible|\bcaja de fusibles|\barnes\b|\bconector electrico|\binterruptor\b|\bswitch\b|\bmodulo\b|\bcomputadora (de|del) (motor|auto)|\becu\b|\bcuerpo de aceleracion|\bactuador\b|\bsolenoide|\bbomba de (gasolina|combustible)|\binyector|\bregulador (de|del) (voltaje|presion)|\bpotenciometro|\bcableado|\bterminal(es)? de bateria|\bcables? (de|para) bateria|\bcables? pasa ?corriente|\bportafusible|\bclaxon|\bbocina (de|del) (auto|claxon)|\bmedidor|\bindicador\b|\btablero\b'),
    ('Filtros y aceites', r'\b(oil|air|fuel|cabin|transmission) filter|\bfilters?\b|\bmotor oil|\bengine oil|\bfiltro (de|del)? ?(aceite|aire|gasolina|combustible|cabina|habitaculo|diesel|transmision)|\baceite (de|para) motor|\baceite\b.{0,20}(sae|\d+w-?\d+)|\b\d+w-?\d+\b|\bliquido (de|para) (transmision|direccion|frenos)|\baditivo|\blimpiador de inyectores|\bgrasa\b|\blubricante|\bfiltro\b'),
    ('Motor y transmisión', r'\bengine\b|\bvalves?\b|\bsolenoid|\bgasket|\btiming (belt|chain|kit)|\bserpentine|\bbelt\b|\bpulley|\btensioner|\btransmission|\bclutch|\bflywheel|\bcv (axle|joint)|\bdriveshaft|\bdifferential|\bturbo(charger)?\b|\bcamshaft|\bcrankshaft|\bpiston|\bcylinder head|\bintake manifold|\bcarburetor|\boil pump|\bengine mount|\bseal\b|\bmotor\b|\bpiston|\bbiela|\bciguenal|\barbol de levas|\bvalvulas?\b|\bjunta (de|del)? ?(cabeza|culata|tapa)|\bempaque|\bbanda (de|del)? ?(distribucion|tiempo|accesorios|alternador)|\bcadena de (distribucion|tiempo)|\bpolea|\btensor|\bkit de distribucion|\btransmision|\bcaja de (velocidades|cambios)|\bembrague|\bclutch|\bvolante motor|\bflecha|\bcardan|\bjunta homocinetica|\bdiferencial|\bconvertidor de par|\bsoporte (de|del)? ?(motor|transmision)|\bcarter|\btapa de valvulas|\bculata|\bcabeza de motor|\bturbo\b|\bturbina|\bmanguera (de|del)? ?(aire|turbo)|\bmultiple de admision|\bcarburador|\bcorrea\b|\bbomba de aceite|\bretén|\breten\b|\bsello\b'),
    ('Carrocería, espejos y molduras', r'\bmirror|\bbumper|\bgrille?\b|\bfender\b|\bhood\b|\bdoor handle|\bemblem|\btrim\b|\bspoiler|\bmud ?flap|\bwindshield\b(?!.*wiper)|\bwindow\b|\bbody kit|\bespejo|\bretrovisor|\bdefensa|\bfacia|\bfascia|\bparrilla|\bcofre\b|\bsalpicadera|\bguardafango|\bloderas?\b|\bmoldura|\bemblema|\blogo\b|\bmanija|\bcalavera de puerta|\bcajuela|\bcubierta (de|para) (defensa|parrilla)|\bspoiler|\baleron|\bestribo|\bbisagra|\bpuerta\b|\bcristal|\bventana\b|\bparabrisas\b(?!.*limpia)|\bcarroceria|\bpanel\b|\bpintura (para|de) auto|\bretoque|\bprotector (de|para) (defensa|parachoques)|\bparachoques|\bfrente (2 din|universal)|\bmarco (de|para) (placa|estereo)|\bcubre ?llanta|\bportaplacas?\b|\btapon (de|para) (gasolina|rin)|\bantena\b'),
    ('Interior y tapicería', r'\bfloor mats?\b|\bseat covers?\b|\bsteering wheel cover|\bcar mat|\bsun ?shade|\bcup holder|\btapete|\balfombra|\bfunda (de|para) (asiento|volante|palanca)|\bvolante\b|\bpalanca de (velocidades|cambios)|\bperilla|\bpedal(es)?\b|\bconsola central|\btablero\b|\bposavasos|\bcubierta de asiento|\basiento\b|\bcinturon de seguridad|\bviseras?\b|\bcortinas? (para|de) (auto|coche)|\bparasol|\bportavasos|\borganizador|\bcubre ?volante|\bpiso\b'),
])


def sub_refaccion_auto(tn):
    return _primera(tn, _REF, {'Motor y transmisión': 10, 'Filtros y aceites': 5, 'Sistema eléctrico y sensores': 8, 'Carrocería, espejos y molduras': 8})


# ------------------------------------------------- Mascotas/Jaulas y corrales
JAULAS = ['Jaulas para perro', 'Corrales y rejas para mascotas', 'Jaulas y recintos para gato', 'Jaulas para aves',
          'Jaulas y hábitats para roedores', 'Acuarios y terrarios', 'Gallineros y conejeras']
_JAU = _c([
    ('Camas', r'^(?:\S+ ){0,2}(cama|colchoneta|cojin|almohadilla)\b'),
    ('Comederos', r'^(?:\S+ ){0,2}(comedero|dispensador (de|automatico de) (comida|alimento)|alimentador)\b'),
    ('Transportadoras', r'^(?:\S+ ){0,2}transportadora\b|\bjaula de viaje|\bbolsa de transporte'),
    ('Acuarios y terrarios', r'\bacuario|\bpecera|\bterrario|\bvivario|\breptil|\btortuga|\bpez\b|\bpeces\b|\biguana|\bgecko|\bserpiente|\barana\b|\btarantula|\banfibio|\bcangrejo|\bcamaron|\bhabitat (para|de) (reptil|tortuga|anfibio)'),
    ('Gallineros y conejeras', r'\bgallinero|\bgallinas?\b|\bpollos?\b|\bconejera|\bconejos?\b|\bpatos?\b|\bcodorniz|\baves de corral|\bcorral (para|de) (gallinas|pollos|conejos|patos)|\bnido de (gallina|ave)|\bponedora'),
    ('Jaulas para aves', r'\baves?\b|\bpajaros?\b|\bpericos?\b|\bperiquito|\bloros?\b|\bcanarios?\b|\bcacatua|\bninfa|\bagapornis|\bcotorra|\bpajarera|\bjaula (para|de) (ave|pajaro|perico|loro|canario)|\bcolumpio para (ave|pajaro)|\bpercha'),
    ('Jaulas y hábitats para roedores', r'\bhamster|\bcobaya|\bcuyo|\bconejillo|\bchinchilla|\bhuron|\bjerbo|\brata|\braton|\berizo|\broedor|\bcuy\b|\bdegu\b|\banimales pequenos|\bpequenas mascotas|\brueda de ejercicio|\bhabitat (para|de) (hamster|roedor)|\btunel para (hamster|roedor)'),
    ('Jaulas y recintos para gato', r'\bgatos?\b|\bgatito|\bfelino|\bcat\b|\bcatio|\bgatera'),
    ('Corrales y rejas para mascotas', r'\bcorral|\bcerca\b|\bvalla|\breja|\bbarrera|\bplaypen|\bpanel(es)?\b|\bpuerta (para|de) (bebe|mascota|perro)|\bdivisor|\brecinto'),
    ('Jaulas para perro', r'\bperros?\b|\bcachorro|\bcanino|\bperrera|\bcaseta|\bkennel|\bcrate|\bjaula\b|\btransportadora|\bdog\b'),
])


def sub_jaula(tn):
    return _primera(tn, _JAU, {'Jaulas para perro': 0, 'Corrales y rejas para mascotas': 10})


# ------------------------------------------------------ Tabletas/Android
TAB_MARCAS_VIEJAS = ['Samsung Galaxy Tab', 'Lenovo Tab', 'Xiaomi, Huawei y Honor', 'Amazon Fire', 'Otras tabletas Android']
TABLETAS = ['Tabletas Android de 8 pulgadas o menos', 'Tabletas Android de 10 a 11 pulgadas', 'Tabletas Android de 12 pulgadas o más',
            'Tabletas Android con 4G o 5G', 'Tabletas para niños', 'Tabletas de dibujo y escritura', 'Tabletas Windows y rugged',
            'Tabletas Android', 'Accesorios para tableta']
_TAB = _c([
    ('Accesorios para tableta', r'^(?:\S+ ){0,3}(funda|estuche|case|soporte|tripode|teclado|cargador|cable|mica|protector|lapiz|stylus|pen|base|dock|montaje|brazo|bateria|adaptador|modulo|tiristor|pantalla lcd|display)s?\b|\bfunda (para|con)|\bprotector de pantalla|\bsoporte (para|de) tablet|\blapiz (para|optico|digital|stylus)|\bpara tablet\b.{0,10}(funda|soporte|teclado)|\bmodulo de|\bcomponente'),
    ('Tabletas de dibujo y escritura', r'\btableta (de|para) (dibujo|escritura|dibujar|escribir)|\btablero de dibujo|\bpizarra (magica|electronica|lcd)|\btableta lcd|\bwacom|\bhuion|\bxp-?pen|\bgaomon|\bdibujo digital|\btableta grafica|\bwriting tablet|\bdrawing tablet|\bboox|\bremarkable|\bkindle scribe|\be ink\b|\btinta electronica|\btinta e'),
    ('Tabletas para niños', r'\bpara ninos?\b|\binfantil|\bninos?\b|\bnina\b|\bkids?\b|\bpaw patrol|\bfrozen|\bspiderman|\bprincesas|\bbluey|\bpeppa|\beducativa|\bfire (7|hd 8|hd 10) kids'),
    ('Tabletas Windows y rugged', r'\bwindows\b|\bsurface\b|\brugged|\bresistente\b|\bindustrial|\bgetac|\bpanasonic toughbook|\bzebra\b|\bhoneywell|\bintel core|\bceleron|\bn100\b|\bn150\b|\bcaja registradora|\bpos\b|\bpunto de venta|\bchuwi\b.{0,20}windows'),
])
_RX_TAB = re.compile(r'(?<![\d.])(\d{1,2}(?:[.,]\d)?)\s?(?:pulgadas|pulg\b|"|”|\'\'|inch|in\b|-inch)')


def sub_tableta(tn):
    sub = _primera(tn, _TAB, {'Tabletas para niños': 5})
    if sub:
        return sub
    if re.search(r'\b4g\b|\b5g\b|\blte\b|\bsim\b|\bcelular\b|\bllamadas', tn):
        return 'Tabletas Android con 4G o 5G'
    m = _RX_TAB.search(tn)
    if not m:
        return 'Tabletas Android'
    v = float(m.group(1).replace(',', '.'))
    if not 5 <= v <= 20:
        return 'Tabletas Android'
    if v >= 11.5: return 'Tabletas Android de 12 pulgadas o más'
    if v >= 9.5: return 'Tabletas Android de 10 a 11 pulgadas'
    return 'Tabletas Android de 8 pulgadas o menos'



# ------------------------------------ Electrodomésticos/Purificadores de agua
PURIFICADORES = ['Accesorios de purificador', 'Ósmosis inversa', 'Purificadores de grifo y encimera', 'Purificadores bajo tarja', 'Jarras y botellas con filtro',
                 'Filtros y membranas de repuesto', 'Destiladores e ionizadores', 'Filtros para regadera', 'Filtros para refrigerador y cafetera',
                 'Ablandadores y filtros de casa completa', 'Dispensadores de agua']
_PUR = _c([
    ('Filtros para refrigerador y cafetera', r'\brefrigerador|\bnevera|\bcafetera|\bcafe\b|\bkeurig|\bnespresso|\bbrita\b.{0,20}(cafetera)|\bmaquina de cafe|\bcompatible con (samsung|lg|whirlpool|ge|frigidaire|bosch|kenmore|maytag)|\blt\d{3,4}|\bda29|\bda97|\bultrawf|\bedr\dr|\bmwf\b|\bxwf\b|\badq\d'),
    ('Filtros para regadera', r'\bregadera|\bducha|\bshower|\bcabezal de ducha|\bfiltro de bano'),
    ('Jarras y botellas con filtro', r'\bjarra|\bpitcher|\bbotella (con|de) filtro|\bbotella filtrante|\bpaja de filtro|\bpajita filtrante|\bfiltro portatil|\bpurificador portatil|\bsupervivencia|\bcamping|\bmochilero|\blifestraw|\bbrita\b|\bpur\b.{0,10}jarra|\bdispensador de agua con filtro'),
    ('Destiladores e ionizadores', r'\bdestilador|\bdestilada|\bdestilacion|\bionizador|\balcalin|\bhidrogeno|\bgenerador de agua|\bagua hidrogenada|\bph \d'),
    ('Ablandadores y filtros de casa completa', r'\bablandador|\bsuavizador|\bcasa completa|\bwhole house|\btoda la casa|\bentrada de agua|\bsedimentos? (de|para) (casa|entrada|cisterna)|\bcisterna|\btinaco|\bdescalcificador|\bantisarro|\bpara toda la casa|\bfiltro de (entrada|sedimento)|\bcarcasa (de|para) filtro|\bportafiltro|\bbig blue'),
    ('Dispensadores de agua', r'\bdispensador de agua\b(?!.*filtro)|\bdespachador de agua|\benfriador de agua|\bgarrafon|\bbomba (de|para) garrafon|\bwater dispenser|\bwater cooler'),
    ('Filtros y membranas de repuesto', r'\binline\b|\ben linea\b|\bpara (rv|casa rodante|calentador)|\bprefiltro|\brepuesto|\breemplazo|\breplacement|\bmembrana|\bcartucho|\bcartuchos|\bfiltros? de (carbon|sedimento|ceramica|ultrafiltracion)|\bcarbon activado|\bpostfiltro|\bprefiltro|\bfiltro (de repuesto|compatible)|\bpaquete de \d+ filtros|\b\d+ (piezas|unidades|pack).{0,20}filtro|\betapa\b.{0,10}(repuesto|filtro)|\bfiltro\b.{0,30}(repuesto|reemplazo|compatible)|\bcompatible con'),
    ('Ósmosis inversa', r'\bosmosis|\bro\b|\breverse osmosis|\bgpd\b|\btanque presurizado|\bsistema (de )?\d etapas|\b\d etapas'),
    ('Accesorios de purificador', r'\btuberia|\btubo\b|\bconector|\bconexion rapida|\bllave (de|para) (purificador|osmosis|agua purificada)|\bvalvula\b|\btanque\b|\bbomba (de|para) (osmosis|presion)|\bmanometro|\bsoporte (de|para) filtro|\bkit de (instalacion|tuberia)|\bpastillas? potabilizadoras|\bpotabilizador'),
    ('Purificadores de grifo y encimera', r'\bsobre (la )?tarja|\bgrifo|\bllave\b|\bencimera|\bsobre (la )?mesa|\bcountertop|\bfaucet|\bde mesa\b|\badaptador de grifo|\bvalvula desviadora|\bpurificador de agua (de|para) (grifo|llave|cocina|mesa)'),
    ('Purificadores bajo tarja', r'\bbajo (tarja|fregadero|lavabo|mesada|encimera)|\bunder ?sink|\bdebajo del fregadero|\bpurificador de agua\b|\bfiltro de agua\b|\bultrafiltracion|\bpurificador\b'),
])


def sub_purificador(tn):
    return _primera(tn, _PUR, {'Purificadores bajo tarja': 40, 'Filtros y membranas de repuesto': 10, 'Filtros para refrigerador y cafetera': 0})


# ------------------------------------------ Deportes/Equipo de gimnasio
GIMNASIO = ['Bancos y racks', 'Máquinas multifuncionales y poleas', 'Máquinas de cardio', 'Barras de dominadas y calistenia',
            'Accesorios de fuerza', 'Tablas y balance', 'Máquinas de abdominales']
_GYM = _c([
    ('Protección y soportes', r'\bknee (pads?|brace|support|sleeve)|\brodillera|\bcodera|\btobillera|\bmunequera|\bfaja\b|\belbow (pad|brace)|\bankle (brace|support)|\bwrist (brace|support|wrap)'),
    ('Máquinas de cardio', r'\bcaminadora|\bcinta de correr|\btreadmill|\beliptica|\bescalador(a)?\b|\bstepper|\bremo\b(?! en t)|\bremadora|\browing|\bair ?bike|\bairbike|\bcama elastica|\brebounder|\bpedalera|\bpedal ejercitador|\bbicicleta de brazos|\bbicicleta (de ejercicio|fija|estatica|spinning)|\bspinning|\bmini bicicleta|\bpedaleador|\bcuerda para saltar|\bjump rope|\bsalto de cuerda|\btrampolin|\bmini ?trampolin|\bslide board|\bski\b'),
    ('Máquinas de abdominales', r'\babdominal|\bab ?wheel|\brueda (abdominal|de abdominales)|\bab roller|\bcrunch|\bcore\b.{0,10}(maquina|entrenador)|\bab machine|\bcintura\b.{0,10}(maquina|twist)|\btwister|\bplancha\b.{0,10}(abdominal|entrenador)'),
    ('Barras de dominadas y calistenia', r'\bdominadas|\bpull ?up|\bchin ?up|\bcalistenia|\bparalelas|\bdip (station|bar)|\bpower tower|\bbarras? (de|para) (dominadas|puerta|pared|flexiones)|\bflexiones|\bpush ?up|\banillos (de|para) gimnasia|\banillas|\btabla de flexiones|\bfondos\b'),
    ('Bancos y racks', r'\bbanco (de |para )?(pesas|mancuernas|press|ejercicio|fitness|abdominal|entrenamiento|musculacion)|\bbanco (plano|inclinado|ajustable|multiposicion|multiejercicio|olimpico|romano|scott|hiperextension)|\brack\b|\bjaula (de|para) (sentadillas|potencia|power)|\bpower rack|\bsquat rack|\bsoporte (de|para) (barra|pesas|sentadillas|discos|mancuernas)|\bhalf rack|\bportadiscos|\bportamancuernas|\bestante (de|para) (pesas|mancuernas|discos)|\bhack squat|\bpress de banca|\bbench\b'),
    ('Máquinas multifuncionales y poleas', r'\bremo en t|\bt-?bar row|\b(maquina|aparato|equipo|estacion)\w* (con |de )?peso integrado|\bmultifuncional|\bmultiestacion|\bmultigimnasio|\bmulti ?gym|\bhome gym|\bgimnasio en casa\b(?!.*(banda|mancuerna|kit portatil))|\bmaquina smith|\bsmith\b|\bpolea|\bpoleas|\bcable (machine|crossover)|\bcrossover|\bprensa de piernas|\bleg press|\bextension de piernas|\bcurl de piernas|\bmaquina (de|para) (pecho|piernas|espalda|hombro|gluteo|abductor|aductor|pantorrilla|remo|jalon|press)|\bjalon\b|\blat pulldown|\bpulley\b|\bcable machine|\bleg press|\bhip thrust|\bsquat machine|\bbelt squat|\bgym equipment|\bfitness equipment|\bhack squat|\bestacion(es)?\b|\bmaquina de (cable|fuerza|musculacion|gimnasio)|\bpec deck|\bgluteo\b.{0,10}maquina|\bhip thrust'),
    ('Tablas y balance', r'\bbosu|\bbalance board|\btabla de equilibrio|\bdisco de equilibrio|\bbalance\b|\bpelota (de|para) (pilates|ejercicio|estabilidad|yoga)|\bfitball|\bbalon (de|para) (ejercicio|pilates|estabilidad)|\bmedicine ball|\bbalon medicinal|\bslam ball|\bwall ball|\bplataforma vibratoria|\bvibratoria|\bstep\b.{0,10}(aerobic|ejercicio|plataforma)|\bplataforma de step|\bescalon de ejercicio'),
    ('Accesorios de fuerza', r'\bagarre|\bgrip|\bstraps?\b|\bcorreas? (de|para) (levantamiento|muneca|tobillo|entrenamiento)|\bcinturon (de|para) (levantamiento|pesas|gimnasio|lastre)|\bmunequera|\brodillera|\bcodera|\bguantes (de|para) (gimnasio|gym|pesas|entrenamiento|levantamiento)|\bmagnesio\b|\btiza\b|\bchalk|\bcuerda (de|para) (batalla|battle)|\bbattle rope|\bchaleco (de|con) (peso|lastre)|\blastre|\btobilleras? (de|con) peso|\bmuñequeras con peso|\bpasador\b|\bcollarin|\babrazadera|\bcierre (de|para) barra|\bgancho|\bmanija|\bagarradera|\baccesorio (de|para) (polea|cable|maquina)|\bbarra (z|w|ez|romana|hexagonal|olimpica|recta|de tricep|de curl|para polea)|\bmancuernas?\b|\bdiscos? (de|para) (pesas|barra)|\bkettlebell|\bpesa rusa|\bligas? (de|para) (ejercicio|resistencia)|\bbanda (de|para) (resistencia|ejercicio)|\bbandas? (elasticas|de resistencia)|\bentrenador de (agarre|antebrazo|dedos|muneca)|\bejercitador'),
])


def sub_gimnasio(tn):
    return _primera(tn, _GYM, {'Accesorios de fuerza': 20})


# ---------------------------------------- Domótica/Cerraduras inteligentes
CERRADURAS = ['Cerraduras con huella digital', 'Cerraduras con teclado y código', 'Cerraduras Wi-Fi y con app',
              'Cerraduras de puerta inteligentes', 'Cerraduras para gabinete y casillero', 'Cerraduras para puerta de vidrio y corrediza',
              'Candados inteligentes', 'Accesorios y refacciones de cerradura']
_CERR = _c([
    ('Accesorios y refacciones de cerradura', r'^(?:\S+ ){0,3}(bateria|cargador|tarjeta|llave|gateway|hub|puente|modulo|adaptador|cable|placa|caja|kit de instalacion|cilindro|repuesto|funda|cubierta)s?\b|\btarjetas? (rfid|ic|nfc|de acceso|de proximidad)|\bpuente wifi|\bwifi bridge|\bgateway\b|\bllaves? (de repuesto|adicionales)'),
    ('Candados inteligentes', r'\bcandado|\bpadlock|\bcandado (de|con) huella|\bcandado inteligente|\bcandado bluetooth'),
    ('Cerraduras para gabinete y casillero', r'\bgabinete|\bcasillero|\blocker|\bcajon|\bcajones|\barmario|\bmueble|\bvitrina|\btaquilla|\bcerradura (de|para) (gabinete|cajon|casillero|locker|armario|mueble)|\bbuzon|\bcaja fuerte'),
    ('Cerraduras para puerta de vidrio y corrediza', r'\bvidrio|\bcristal|\bcorrediza|\bcorredera|\bpuerta de (vidrio|cristal|aluminio)|\bmarco de aluminio|\bpuerta corrediza|\bsliding'),
    ('Cerraduras con huella digital', r'\bhuella|\bdactilar|\bfingerprint|\bbiometric|\breconocimiento facial|\bfacial|\bpalma|\bvena'),
    ('Cerraduras Wi-Fi y con app', r'\bwifi|\bwi-?fi|\bapp\b|\balexa|\bgoogle|\btuya|\bsmart life|\bzigbee|\bmatter|\bhomekit|\bbluetooth|\bcontrol (remoto|por app)|\bremoto\b|\bttlock|\baugust\b|\byale\b.{0,20}(wifi|bluetooth|app)|\bschlage encode|\bkwikset halo|\bnuki\b'),
    ('Cerraduras con teclado y código', r'\bteclado|\bcodigo|\bcontrasena|\bkeypad|\bclave\b|\bpin\b|\bcombinacion|\bdigital|\belectronica|\bsin llave|\bkeyless'),
    ('Cerraduras de puerta inteligentes', r'\bcerrojo|\bdeadbolt|\bmanija|\bmanilla|\bperilla|\bpicaporte|\bchapa\b|\bcerradura\b'),
])


def sub_cerradura(tn):
    return _primera(tn, _CERR, {'Cerraduras de puerta inteligentes': 40, 'Cerraduras con teclado y código': 8, 'Cerraduras Wi-Fi y con app': 12})


# -------------------------------- Proyectores/Pantallas de proyección
PANTALLAS = ['Pantallas enrollables manuales', 'Pantallas eléctricas motorizadas', 'Pantallas con trípode y portátiles',
             'Pantallas de marco fijo', 'Pantallas inflables y de exterior', 'Pantallas de suelo y de mesa', 'Telas y pantallas ALR',
             'Lámparas de proyector', 'Soportes para proyector', 'Otros accesorios de proyector',
             'Pantallas de proyección']
_PAN = _c([
    ('Proyectores', r'^(?:\S+ ){0,3}(mini ?)?proyector(es)?\b(?!.{0,40}(pantalla|soporte|lampara|bombilla|control|filtro|cable|funda|lente|adaptador|bateria|mount|tripode))|^(?:\S+ ){0,2}(proyector|projector) (4k|1080p|portatil|led|laser|inteligente|smart|android|wifi|de bolsillo|mini)'),
    ('Lámparas de proyector', r'\blampara|\bbombilla|\bbulb\b|\bfoco (de|para) proyector|\bmodulo de lampara|\blamp\b|\belplp|\bnp\d{2}lp|\bsp-lamp|\bpoa-lmp|\bet-lae|\bet-lal|\bdt\d{4}|\b5j\.\w+'),
    ('Soportes para proyector', r'\bsoporte|\bmontaje|\bbase (para|de) proyector|\btripie|\btripode (para|de) proyector|\bbracket|\bmount\b|\bestante (para|de) proyector|\brepisa|\bbrazo'),
    ('Otros accesorios de proyector', r'\bcontrol remoto|\bmando a distancia|\bfiltro|\bventilador|\bcable|\badaptador|\blente\b|\bfunda|\bmaletin|\bestuche|\bbolsa|\bcubierta|\btapa|\bplaca|\bboard\b|\bpower supply|\bfuente de alimentacion|\bbateria|\bbattery|\brepuesto (para|de) proyector|\bpara proyector\b(?!.{0,40}pantalla)|\bhead-?up|\bhud\b|\bcars? for\b'),
    ('Pantallas inflables y de exterior', r'\binflable|\binflatable|\bexterior|\boutdoor|\bal aire libre|\bjardin|\bpatio|\bcine al aire libre|\bcamping'),
    ('Telas y pantallas ALR', r'\balr\b|\bclr\b|\brechazo de luz ambiental|\bluz ambiental|\btela (de|para) proyecci|\blona\b(?!.*(tripode|enrollable|electrica))|\bpantalla de tela\b|\bfabric\b|\bmaterial de proyeccion|\bpantalla plegable (de tela|anti ?arrugas)|\banti ?arrugas|\bcon ojales|\bcon ganchos'),
    ('Pantallas eléctricas motorizadas', r'\belectric|\bmotorizad|\bmotorized|\bcon control remoto|\bcon motor|\bautomatica|\bde techo\b.{0,20}(electric|motor)|\bretractil electrica|\btensionada'),
    ('Pantallas con trípode y portátiles', r'\btripode|\btripie|\bcon soporte\b|\bde pie\b|\bde piso\b|\bportatil|\bplegable|\bcon base|\bstand\b|\bpull ?up|\bautoportante|\bcon maleta|\bcon bolsa'),
    ('Pantallas de marco fijo', r'\bmarco fijo|\bfixed frame|\bde marco\b|\bmarco de aluminio|\bfija\b|\bfijo\b|\bde pared fija|\bmontaje en pared'),
    ('Pantallas de suelo y de mesa', r'\bde suelo|\bde mesa\b|\bfloor rising|\bsobre mesa|\bde escritorio|\btabletop|\bcompacta'),
    ('Pantallas enrollables manuales', r'\benrollable|\bmanual|\bretractil|\bdesplegable|\bpull ?down|\bde techo|\bde pared|\bcortina'),
    # La pantalla que no dice cómo se monta va al cajón genérico, que ya
    # existe. Antes esta línea estaba pegada a la de «enrollables manuales» y
    # se llevaba 2,462 fichas ahí: casi toda la ficha de Amazon dice «pantalla
    # de proyección» y nada más, así que el cajón específico terminó lleno de
    # pantallas que nadie dijo que fueran enrollables. Va al final, después de
    # que todas las formas concretas tuvieron su turno.
    ('Pantallas de proyección', r'\bpantalla (de|para) proyecci|\bpantalla proyector|'
                                r'\bpantalla de proyector|\bproyeccion\b'),
])


def sub_pantalla_proy(tn):
    return _primera(tn, _PAN, {'Pantallas de proyección': 40, 'Otros accesorios de proyector': 5})


OLA2 += [
    ('Herramientas', ['Herramientas eléctricas'], HERRAMIENTAS_E, lambda tn, sv: sub_herramienta_e(tn), None),
    ('Belleza y cuidado personal', ['Maquillaje'], MAQUILLAJE, lambda tn, sv: sub_maquillaje(tn), None),
    ('Joyería y bisutería', ['Relojes'], RELOJES, lambda tn, sv: sub_reloj_pulsera(tn), None),
    ('Refacciones', ['Para autos'], REFACCIONES_AUTO, lambda tn, sv: sub_refaccion_auto(tn), None),
    ('Mascotas', ['Jaulas y corrales'], JAULAS, lambda tn, sv: sub_jaula(tn), None),
    ('Tabletas', ['Android'] + TAB_MARCAS_VIEJAS, TABLETAS, lambda tn, sv: sub_tableta(tn), 'Tabletas Android'),
    ('Electrodomésticos', ['Purificadores de agua'], PURIFICADORES, lambda tn, sv: sub_purificador(tn), None),
    ('Deportes y fitness', ['Equipo de gimnasio'], GIMNASIO, lambda tn, sv: sub_gimnasio(tn), None),
    ('Domótica y hogar inteligente', ['Cerraduras inteligentes'], CERRADURAS, lambda tn, sv: sub_cerradura(tn), None),
    ('Proyectores y accesorios', ['Pantallas de proyección'], PANTALLAS, lambda tn, sv: sub_pantalla_proy(tn), None),
]


# =========================================================== CUARTA OLA
def _tamano_cama(tn):
    if re.search(r'\bking\b|\bcalifornia king', tn): return 'king'
    if re.search(r'\bqueen\b', tn): return 'queen'
    if re.search(r'\bmatrimonial|\bfull\b|\bdoble\b|\b135 ?x|\b140 ?x', tn): return 'matrimonial'
    if re.search(r'\bindividual|\btwin\b|\bsingle\b|\b90 ?x|\b100 ?x|\b105 ?x', tn): return 'individual'
    return None


# ------------------------------------------ Instrumentos/Baterías, Viento, Teclados
BATERIAS = ['Baterías acústicas', 'Baterías electrónicas', 'Platillos', 'Baquetas y escobillas', 'Parches',
            'Pedales y herrajes de batería', 'Tarolas y cajas', 'Pads de práctica', 'Fundas y accesorios de batería',
            'Percusión']
_BAT = _c([
    ('Pads de práctica', r'\bpad (de|para) practica|\balmohadilla de practica|\bpractice pad|\bpad\b.{0,20}practica|\bpracticador\b|\breflexx\b'),
    ('Baquetas y escobillas', r'\bbaquetas?\b|\bdrumsticks?|\bescobillas?\b|\bbrushes\b|\bmazos?\b|\bmallets?\b|\brods\b'),
    ('Parches', r'\bparches?\b|\bdrumhead|\bhead\b.{0,15}(tom|snare|bass)|\bevans\b|\bremo\b'),
    ('Platillos', r'\bplatillos?\b|\bcymbals?\b|\bhi-?hat|\bcrash\b|\bride\b|\bsplash\b|\bchina\b.{0,10}(platillo|cymbal)|\bzildjian|\bsabian|\bmeinl\b.{0,20}(platillo|cymbal)|\bpaiste'),
    ('Pedales y herrajes de batería', r'\bpedal(es)?\b|\bherrajes?\b|\bhardware\b|\batril\b|\bsoporte (de|para) (platillo|tarola|tom|bombo|hi-?hat)|\bstand\b|\babrazadera|\bclamp\b|\bllaves?\b.{0,30}afinacion|\bdrum ?key|\bllaves?\b.{0,20}\bdw\b|\bdwsm\d|\btornillo|\bbanco (de|para) bateria|\btrono\b|\bthrone\b|\brack (de|para) bateria|\bcadena\b|\bbeater|\bmaza\b'),
    ('Tarolas y cajas', r'\btarola|\bsnare\b|\bcaja (de|para) bateria|\bredoblante'),
    ('Baterías electrónicas', r'\bcaja de ritmos|\bdrum machine|\belectronic|\belectric|\bdigital|\bmalla\b|\bmesh\b|\bmodulo (de )?(sonido|bateria)|\bbateria (de )?aire|\bair drum|\bvirtual'),
    ('Fundas y accesorios de batería', r'\bfunda|\bestuche|\bcase\b|\bbag\b|\btapete|\balfombra|\bsilenciador|\bmute\b|\bmicrofono|\bmonitor|\bkit de (limpieza|afinacion|supervivencia)|\bmochila\b|\bbaquetero\b'),
    # El tambor de mano no es una batería, y «Percusión» ya existía. El cajón
    # de «Baterías» tenía 374 fichas y adentro había timbales, tambores de
    # lengua, panderetas y cucharas irlandesas: todo lo que se golpea y no es
    # un kit. Va después de los accesorios y antes del kit: la «llave de
    # afinación de tambor» es un herraje de batería, no un instrumento, y si
    # esta regla fuera primero se lo llevaría por decir «tambor».
    ('Percusión', r'\btambor(es)?\b|\btimbal|\bpandereta|\bpandero\b|\bcajon (flamenco|peruano)|'
                  r'\bbongo|\bconga|\bdjembe|\bcabasa|\bguiro\b|\bmaracas?\b|\bclaves\b|'
                  r'\bcascabel|\bchimes\b|\bcowbell|\bcencerro|\bhandpan|\bhang drum|'
                  r'\btongue drum|\bsteel tongue|\bpanda drum|\brain drum|\btriangulo musical|'
                  r'\bcastanuelas?\b|\bxilofono|\bglockenspiel|\bmarimba|\bshaker\b|'
                  r'\bpercusion\b|\bsonaja|\bpalo de lluvia|\bvibraslap|\bgong\b'),
    ('Baterías acústicas', r'\bbateria (acustica|de \d piezas|completa|shell|junior|infantil)|\bjuego de bateria|\bdrum (set|kit)|\bshell pack|\bbombo\b|\btom\b|\btoms\b|\bbateria\b'),
])


def sub_bateria_musical(tn):
    return _primera(tn, _BAT, {'Baterías acústicas': 30, 'Fundas y accesorios de batería': 5})


VIENTO = ['Saxofones', 'Flautas traversas', 'Clarinetes y oboes', 'Trompetas, trombones y metales', 'Armónicas y melódicas',
          'Ocarinas, silbatos y flautas dulces', 'Instrumentos de viento digitales', 'Boquillas, cañas y accesorios de viento']
_VIE = _c([
    ('Boquillas, cañas y accesorios de viento', r'\bboquilla|\bcanas?\b|\breeds?\b|\bligadura|\bcorrea|\bfunda|\bestuche|\bcase\b|\batril|\bsoporte|\blimpiador|\bkit de (limpieza|mantenimiento)|\baceite (de|para) (valvula|piston)|\bgrasa (de|para) corcho|\bsordina|\bmute\b|\bpaño|\bpano\b|\bhisopo|\bcordon|\barnes\b|\bpad\b|\balmohadilla|\bmouthpiece|\bembocadura|\bpistones?\b|\btubistas?\b|papel en polvo|\bfieltro\b'),
    ('Instrumentos de viento digitales', r'\bdigital|\belectronic|\bmidi\b|\bsintetizador de viento|\bewi\b|\baerophone|\bsaxofon electronico'),
    ('Armónicas y melódicas', r'\barmonica|\bharmonica|\bmelodica|\bpianica|\bacordeon'),
    ('Ocarinas, silbatos y flautas dulces', r'\bocarina|\bsilbato|\bwhistle|\bflauta dulce|\bflauta de pan|\bquena|\bzampona|\bflauta (nativa|indigena|de bambu|de madera|irlandesa)|\brecorder\b|\bkazoo|\bpito\b|\bflauta (para|de) ninos|\bdescantador\b|\bflautas? de pan\b|\bpanflauta\b'),
    ('Saxofones', r'\bsaxofon|\bsaxo\b|\bsax\b|\bsaxophone'),
    ('Flautas traversas', r'\bflauta (traversa|transversal)|\bflauta\b|\bflute\b|\bpiccolo|\bflautin'),
    ('Clarinetes y oboes', r'\bclarinete|\boboe|\bfagot|\bbassoon|\bclarinet|\bshehnai\b'),
    ('Trompetas, trombones y metales', r'\btrompeta|\btrombon|\btuba\b|\bcorneta|\bcorno|\btrompa\b|\bbombardino|\beufonio|\bfliscorno|\bsousafon|\bmetales?\b|\bbugle|\bcornet|\btrumpet|\bhelicon|\beuphonium\b'),
])


def sub_viento(tn):
    s = _primera(tn, _VIE, {'Boquillas, cañas y accesorios de viento': 5})
    if s:
        return s
    # Sin nombre propio: "instrumento de viento madera", la suona china y la
    # barra de palisandro son todos de lengüeta, la familia del oboe.
    if re.search(r'viento (de )?madera|woodwind|\bsuona\b|\bpalisandro\b|'
                 r'viento (folclorico|popular)', tn):
        return 'Clarinetes y oboes'
    return None


TECLADOS_MUS = ['Pianos digitales', 'Teclados electrónicos', 'Sintetizadores y controladores MIDI', 'Acordeones',
                'Órganos y otros teclados', 'Bancos, soportes y accesorios de teclado']
_TEC = _c([
    ('Bancos, soportes y accesorios de teclado', r'\bbanco|\bsoporte|\bstand\b|\bpedal|\bfunda|\bestuche|\bcubierta|\batril|\bcable|\badaptador|\bpegatinas?|\bstickers?|\bbolsa|\bllave de afinacion'),
    ('Acordeones', r'\bacordeon|\bbandoneon|\bconcertina|\baccordion'),
    ('Sintetizadores y controladores MIDI', r'\bsintetizador|\bsynth|\bmidi\b|\bcontrolador|\bworkstation|\bgroovebox|\bsecuenciador|\bsampler|\bpad\b|\bmontage\b|\barturia\b|\bminilab\b'),
    ('Órganos y otros teclados', r'\borgano|\bclavecin|\bharmonium|\barmonio\b|\bshruti\b|\bsurpeti\b|\bcelesta|\bmelotron|\bmellotron'),
    ('Pianos digitales', r'\bpiano digital|\bpiano electrico|\bpiano electronico|\bpiano de (88|76) teclas|\b88 teclas|\bpiano\b(?!.*(teclado (de|para) ninos|juguete))|\bclavinova|\bcasio (px|cdp|ap)|\byamaha (p-?\d|ydp|clp)|\broland (fp|rp|hp)|\bkorg'),
    ('Teclados electrónicos', r'\bteclado|\bkeyboard|\bteclas\b|\bcasiotone|\bpsr\b'),
])


def sub_teclado_musical(tn):
    return _primera(tn, _TEC, {'Teclados electrónicos': 20, 'Bancos, soportes y accesorios de teclado': 3})


# ---------------------------------------------------------------- Audífonos
AUDIFONOS_INAL = ['Earbuds con cancelación de ruido', 'Earbuds deportivos', 'Earbuds de cuello', 'Earbuds para niños',
                  'Earbuds inalámbricos', 'Diadema con cancelación de ruido', 'Diadema inalámbrica', 'Almohadillas y repuestos']
_AUD = _c([
    ('Almohadillas y repuestos', r'\balmohadillas?\b|\bear ?pads?\b|\bear ?tips?\b|\bpuntas (de|para) (oido|silicona)|\bestuche (de )?(carga|reemplazo|repuesto)|\bcaja de carga|\bcable (de repuesto|de reemplazo|para)|\bfunda (para|de) (airpods|audifonos|auriculares|estuche)|\brepuesto|\bganchos? (para|de) (oreja|oido)|\bdiadema de repuesto|\bcorrea|\bsoporte (para|de) audifonos'),
    ('Earbuds para niños', r'\bpara ninos?\b|\binfantil|\bninos?\b|\bnina\b|\bkids?\b|\bkawaii|\bhello kitty|\bdisney|\bmarvel'),
    ('Diadema con cancelación de ruido', r'(supraaural|over-?ear|on-?ear|diadema|headphones?|over the ear|circumaural|wh-?1000|quietcomfort|qc\d+|xm[3-6]\b|beats (solo|studio)|tune (5|6|7)\d0|live 7\d0).{0,80}(cancelacion (activa )?de ruido|\banc\b|noise cancel)|(cancelacion (activa )?de ruido|\banc\b|noise cancel).{0,80}(supraaural|over-?ear|on-?ear|diadema|headphones?|circumaural)|\bwh-?1000xm|\bquietcomfort|\bbose qc|\bxm[3-6]\b|\bbeats studio|\bsony ult wear'),
    ('Diadema inalámbrica', r'\bsupraaural|\bover-?ear|\bon-?ear|\bdiadema|\bheadphones?\b|\bover the ear|\bcircumaural|\bbeats solo|\btune (5|6|7)\d0|\blive 7\d0|\bplegables?\b|\bvincha|\bde vincha'),
    ('Earbuds con cancelación de ruido', r'cancelacion (activa )?de ruido|\banc\b|noise cancel|\bcancelacion de ruido'),
    ('Earbuds deportivos', r'\bdeportiv|\bsport\b|\bsports\b|\bgym\b|\bcorrer\b|\brunning|\bejercicio|\bgancho|\bear ?hook|\bipx[5-8]|\bip6[78]|\bsudor|\bsweat'),
    ('Earbuds de cuello', r'\bcuello\b|\bneckband|\bneck\b|\bmagnetic|\bmagnetic'),
    ('Earbuds inalámbricos', r'\btws\b|\btrue wireless|\bearbuds?\b|\bin-?ear|\bintraaur|\binalambric|\bbluetooth|\baudifono|\bauricular|\bmanos libres'),
])


_RX_ANC = re.compile(r'cancelacion (activa )?de ruido|\banc\b|noise cancel')


def sub_audifono_inal(tn, sub_vieja=None):
    s = _primera(tn, _AUD, {'Earbuds inalámbricos': 60, 'Diadema inalámbrica': 8,
                            'Earbuds de cuello': 10, 'Earbuds deportivos': 6})
    # El despachador ya decidió la forma (diadema o botón) mirando el modelo;
    # acá solo se elige DENTRO de esa familia. Sin esto un "Sennheiser HD
    # 400S", bien puesto en Diadema, salía como Earbuds: la palabra
    # "audífono" del título cae en la rama de botón y ninguna de diadema
    # engancha, porque el título nunca dice "diadema".
    if s and sub_vieja and s != 'Almohadillas y repuestos':
        anc = bool(_RX_ANC.search(tn))
        if sub_vieja.startswith('Diadema') and s.startswith('Earbuds'):
            return 'Diadema con cancelación de ruido' if anc else 'Diadema inalámbrica'
        if sub_vieja.startswith('Earbuds') and s.startswith('Diadema'):
            return 'Earbuds con cancelación de ruido' if anc else 'Earbuds inalámbricos'
    return s


# ------------------------------------------------------------ Muebles
COLCHONES = ['Colchones individuales', 'Colchones matrimoniales', 'Colchones queen size', 'Colchones king size',
             'Colchones infantiles y de cuna', 'Colchones plegables y de sofá cama', 'Toppers y sobrecolchones', 'Colchones']
_COL = _c([
    ('Toppers y sobrecolchones', r'^(?:\S+ ){0,3}(topper|sobrecolchon|cubre ?colchon|mattress topper|protector (de|para) colchon)\b'),
    ('Colchones infantiles y de cuna', r'\bcuna|\binfantil|\bpara ninos?\b|\bbebe|\bcrib\b|\bmoises|\bcorral'),
    ('Colchones plegables y de sofá cama', r'\bplegable|\bsofa cama|\bfuton|\bde suelo|\btatami|\bcolchoneta|\bcamping|\binflable|\bde aire\b|\bde viaje|\benrollable'),
])


def sub_colchon(tn):
    s = _primera(tn, _COL, {})
    if s:
        return s
    t = _tamano_cama(tn)
    return {'king': 'Colchones king size', 'queen': 'Colchones queen size', 'matrimonial': 'Colchones matrimoniales',
            'individual': 'Colchones individuales'}.get(t, 'Colchones')


ESCRITORIOS = ['Escritorios de oficina', 'Escritorios gamer', 'Escritorios en L y esquineros', 'Escritorios de altura ajustable',
               'Escritorios infantiles y estudiantiles', 'Mesas para laptop y de cama', 'Escritorios plegables y compactos',
               'Accesorios y organizadores de escritorio']
_ESC = _c([
    ('Accesorios y organizadores de escritorio', r'\borganizador|\bsoporte (para|de) monitor|\belevador|\bbandeja (para|de) teclado|\bcajonera\b|\bcajon (para|de) escritorio|\bpasacables|\bgestion de cables|\btapete|\balfombrilla|\bprotector de escritorio|\bportalapices|\blampara|\brepisa (para|de) escritorio|\bextension de escritorio|\breposapies|\bsoporte (para|de) (laptop|cpu|computadora)|\bpc gamer\b|\bmemoria usb'),
    ('Mesas para laptop y de cama', r'\bmesa (para|de) (laptop|cama|portatil|computadora portatil)|\bde cama\b|\bbandeja (para|de) (cama|laptop|sofa)|\bcon ruedas\b.{0,20}(cama|sofa)|\blap ?desk|\bmesita (para|de) (laptop|cama)|\bmesa auxiliar con ruedas'),
    ('Escritorios de altura ajustable', r'\baltura ajustable|\bajustable en altura|\bde pie\b|\bstanding|\belectrico|\bsit-?stand|\belevable|\bregulable en altura|\bmotorizado|\bconvertidor'),
    ('Escritorios gamer', r'\bgamer|\bgaming\b|\bled\b|\brgb\b|\bfibra de carbono|\bpara pc gamer'),
    ('Escritorios en L y esquineros', r'\ben l\b|\ben forma de l|\bl-?shaped|\besquinero|\bde esquina|\besquina\b|\ben u\b'),
    ('Escritorios infantiles y estudiantiles', r'\binfantil|\bpara ninos?\b|\bninos?\b|\bnina\b|\bkids?\b|\bestudiantil|\bestudiante|\bpupitre|\bescolar|\bjuvenil'),
    ('Escritorios plegables y compactos', r'\bplegable|\bcompacto|\bpequeno|\bmini\b|\bflotante|\bde pared\b|\babatible|\bmesa plegable'),
    ('Escritorios de oficina', r'\boficina|\bejecutivo|\bgerencial|\bsecretarial|\bhome office|\bcon cajones|\bde madera|\bde cristal|\bde vidrio|\bmoderno|\bescritorio|\bmesa (de|para) (computadora|computador|estudio|trabajo|oficina)|\bmesa gamer'),
])


def sub_escritorio(tn):
    return _primera(tn, _ESC, {'Escritorios de oficina': 40, 'Escritorios plegables y compactos': 10, 'Escritorios gamer': 3})


SOFAS = ['Sofás de 2 y 3 plazas', 'Sofás seccionales y esquineros', 'Sofás cama', 'Sillones de masaje', 'Sofás infantiles',
         'Puffs y otomanas', 'Fundas y accesorios para sofá', 'Sillones y reclinables']
_SOF = _c([
    ('Fundas y accesorios para sofá', r'\bfundas?\b|\bcubre ?sofa|\bprotector (de|para) sofa|\bcojin(es)?\b(?! (de|para) (silla|asiento))|\bbandeja (de|para) (sofa|reposabrazos)|\bpatas? (de|para) sofa|\borganizador (de|para) sofa|\bresorte'),
    ('Sillones de masaje', r'\bmasaje|\bmasajeador|\bmasajeadora|\bmassage'),
    ('Sofás infantiles', r'\binfantil|\bpara ninos?\b|\bninos?\b|\bnina\b|\bkids?\b|\bbebe|\bprincesa|\bastronauta|\bdinosaurio|\bunicornio'),
    ('Puffs y otomanas', r'\bpuff?s?\b|\bpouf|\botoman|\bbanco tapizado|\btaburete tapizado|\bpera\b|\bbean ?bag|\breposapies'),
    ('Sofás cama', r'\bsofa ?cama|\bsofacama|\bcama (extraible|nido)|\bfuton|\bconvertible en cama|\bdesplegable'),
    ('Sofás seccionales y esquineros', r'\bseccional|\besquiner|\ben forma de l|\ben l\b|\bmodular|\bchaise ?longue|\bsala (esquinera|modular|en l|completa|de \d piezas)|\bjuego de sala|\bconjunto de sala'),
    ('Sillones y reclinables', r'\bsillon(es)?\b(?! (de|para) (2|3|dos|tres) plazas)|\breclinable|\breclinabl|\bbutaca|\bpoltrona|\bloveseat|\blove seat|\bindividual\b|\bde 1 plaza|\buna plaza|\bchaise'),
    ('Sofás de 2 y 3 plazas', r'\bsofa|\b(2|3|dos|tres) plazas|\bde \d plazas|\bcouch|\bchesterfield|\bloveseat'),
])


def sub_sofa(tn):
    return _primera(tn, _SOF, {'Sofás de 2 y 3 plazas': 30, 'Sillones y reclinables': 15})


MESAS_CENTRO = ['Mesas de centro', 'Mesas auxiliares y laterales', 'Mesas para TV y consolas', 'Mesas de cama y con ruedas',
                'Mesas plegables y multiusos', 'Mesas de exterior']
_MC = _c([
    ('Mesas para TV y consolas', r'\bmesa (para|de) tv|\bmueble (para|de) tv|\brack (para|de) tv|\bconsola\b(?! (mezcladora|de audio|de juegos|de videojuegos))|\bcentro de entretenimiento|\bcredenza|\baparador|\brecibidor|\bde entrada\b'),
    ('Mesas de cama y con ruedas', r'\bmesa (de|para) cama|\bcon ruedas|\bmesa auxiliar movil|\bcarrito|\bmesa (para|de) laptop|\bsobre cama|\bmesa de hospital'),
    ('Mesas de exterior', r'\bexterior|\bjardin|\bterraza|\bpatio|\boutdoor|\bplaya|\bcamping|\bratan|\brattan'),
    ('Mesas plegables y multiusos', r'\bplegable|\bmultiusos|\bmulti ?funcional|\bde trabajo|\bmesa de (dibujo|manualidades|costura)|\bcaballete|\bmesa (alta|de bar)|\bmesa (de|para) (impresora|maquina)'),
    ('Mesas auxiliares y laterales', r'\bauxiliar|\blateral|\bde esquina|\besquinera|\bmesita|\bde noche|\bnido\b|\bpedestal|\bde apoyo|\bde sala\b(?!.*centro)|\bmesa de (lampara|telefono)|\bside table|\bend table'),
    ('Mesas de centro', r'\bmesa (de )?centro|\bcentro\b|\bcoffee table|\bmesa (de|para) (sala|cafe|te)|\bmesa\b'),
])


def sub_mesa_centro(tn):
    return _primera(tn, _MC, {'Mesas de centro': 30, 'Mesas auxiliares y laterales': 5})


CAMAS = ['Bases de cama y box', 'Cabeceras', 'Camas individuales', 'Camas matrimoniales', 'Camas queen y king', 'Literas',
         'Camas infantiles', 'Camas plegables y catres', 'Accesorios y refacciones de cama']
_CAM = _c([
    ('Accesorios y refacciones de cama', r'\bpatas? (de|para) (cama|box)|\brueda|\banillos?\b|\brepuesto|\bresorte|\btrampolin|\bcama elastica|\bherraje|\bconector|\bsoporte central|\bbarandal|\bbarrera|\bescalera (de|para) litera|\bmarco de cama\b.{0,20}(piezas|patas)|\btablas? (de|para) cama'),
    ('Cabeceras', r'\bcabecera|\bcabecero|\bheadboard|\brespaldo (de|para) cama'),
    ('Literas', r'\blitera|\bbunk|\bcama alta|\bcama nido|\bcama elevada|\bloft bed|\bcama triple'),
    ('Camas infantiles', r'\binfantil|\bpara ninos?\b|\bninos?\b|\bnina\b|\bkids?\b|\bbebe|\bcuna|\bprincesa|\bcarro|\bcoche\b|\bmontessori|\btoddler|\bjuvenil'),
    ('Camas plegables y catres', r'\bplegable|\bcatre|\bcama de (campana|camping|invitados)|\bportatil|\bde aire\b|\binflable|\bcamping|\bcama auxiliar|\bde hospital|\bhospitalaria|\barticulada'),
    ('Bases de cama y box', r'\bbox\b(?! ?spring de)|\bbase (de|para) cama|\bbase\b|\bsomier|\btambor\b|\bbox ?spring|\bbastidor|\bplataforma'),
])


def sub_cama(tn):
    s = _primera(tn, _CAM, {'Bases de cama y box': 5})
    if s:
        return s
    t = _tamano_cama(tn)
    return {'king': 'Camas queen y king', 'queen': 'Camas queen y king', 'matrimonial': 'Camas matrimoniales',
            'individual': 'Camas individuales'}.get(t)


# ------------------------------------------------------------ Juguetes/Bebés
BEBES = ['Alimentación y lactancia', 'Baño e higiene del bebé', 'Pañales y cambio', 'Chupones y mordederas', 'Seguridad para bebé',
         'Ropa y calzado de bebé', 'Juguetes para bebé', 'Portabebés y canguros', 'Sillas de comer y mecedoras', 'Cuidado y salud del bebé']
_BEB = _c([
    ('Portabebés y canguros', r'\bportabebe|\bcanguro|\bfular|\brebozo|\bmochila (porta|ergonomica)|\bcargador de bebe|\bcarrier\b'),
    ('Sillas de comer y mecedoras', r'\bsilla (de|para) comer|\bperiquera|\btrona\b|\bmecedora|\bcolumpio (para|de) bebe|\bbouncer|\bhamaca (para|de) bebe|\bsilla vibradora|\bgimnasio (para|de) bebe|\btapete de (juego|actividades)|\bcentro de actividades|\bbrincolin'),
    ('Pañales y cambio', r'\bpanal|\bpanales|\bcambiador|\bcambio de panal|\btoallitas humedas|\btoallitas\b|\bcubeta (de|para) panales|\bbote (de|para) panales|\bcrema (para|de) rozaduras|\brozaduras|\bdiaper'),
    ('Chupones y mordederas', r'\bchupon|\bchupete|\bmordedera|\bmordedor|\bdentici|\bpacifier|\bteether|\bportachupon|\bcadena (para|de) chupon'),
    ('Alimentación y lactancia', r'\bbiberon|\bmamila|\btetina|\bextractor de leche|\bsacaleches|\blactancia|\bleche materna|\bbolsas? (de|para) leche|\besterilizador|\bcalienta ?biberon|\bplato (para|de) bebe|\bvaso (entrenador|de aprendizaje|antiderrame)|\bcuchara (para|de) bebe|\bbabero|\bpapilla|\bprocesador de alimentos para bebe|\bformula\b|\bcereal (para|de) bebe|\balimentador|\btermo (para|de) (biberon|bebe)|\bcojin de lactancia|\balmohada de lactancia|\bbrassiere de lactancia|\bprotectores de lactancia|\bpezoneras'),
    ('Baño e higiene del bebé', r'\btina (de|para) bebe|\bbanera|\bbanadera|\bchampu\b|\bshampoo|\bjabon\b|\bgel de bano|\bespuma\b|\bcrema (hidratante|corporal)|\baceite (para|de) bebe|\btalco|\bcepillo (de|para) (bebe|cabello)|\bpeine\b|\bcortaunas|\btoalla (con capucha|para bebe)|\besponja|\btermometro de bano|\basiento (de|para) bano|\bcapa de bano|\bbath\b'),
    ('Cuidado y salud del bebé', r'\baspirador nasal|\btermometro|\bhumidificador|\bmonitor (de|para) bebe|\bvaporizador|\bsuero\b|\bvitaminas (para|de) bebe|\bprotector solar (para|de) bebe|\bcrema (para|de) (bebe|piel)|\bkit de (cuidado|salud)|\bbotiquin|\bsalud\b|\bpomada|\bcuidado de la piel'),
    ('Seguridad para bebé', r'\bprotector(es)? (de|para) (esquinas|enchufes|contactos|puertas|cajones)|\bseguro (de|para) (cajon|puerta|gabinete)|\bpuerta de seguridad|\breja de seguridad|\bbarrera (de|para) (escalera|cama|seguridad)|\bcerradura (de|para) (bebe|nino|cajon)|\ba prueba de ninos|\bmonitor de (respiracion|movimiento)|\bcasco (para|de) bebe|\brodilleras (para|de) bebe|\barnes (de|para) (seguridad|caminar)|\bcorrea (anti ?perdida|de seguridad)|\bandador (con|de) seguridad'),
    ('Ropa y calzado de bebé', r'\bropa\b|\bmameluco|\bpijama|\bbody\b|\bbodys\b|\bcalcetines|\bzapatos? (de|para) bebe|\bgorro|\bmanoplas|\bconjunto (de|para) bebe|\bvestido|\bpanalero|\bcobija (de|para) bebe|\bmanta (de|para) bebe|\bsaco de dormir|\bsleeping bag|\bswaddle|\benvoltura|\bropa (de|para) bebe|\bbaby (clothes|outfit)'),
    ('Juguetes para bebé', r'\bjuguete|\bsonaja|\bsonajero|\bmovil (para|de) cuna|\bpeluche|\bcubos? (de|para) bebe|\blibro (de tela|de bano|blandito)|\bproyector (de|para) (cuna|bebe)|\bpiano (de|para) bebe|\bcaminador|\bandadera|\bcorrepasillos|\bapilable|\bgimnasio de actividades|\bmesa de actividades|\bmuneca|\bcochecito de muneca|\bpelota (para|de) bebe|\bjuego (de|para) bebe|\bmordedor de juguete'),
])


def sub_bebe(tn):
    return _primera(tn, _BEB, {'Juguetes para bebé': 10, 'Cuidado y salud del bebé': 8, 'Ropa y calzado de bebé': 8})


# ---------------------------------------------------- Cargadores/De pared
CARGADORES_PARED = ['Cargadores de pared hasta 20 W', 'Cargadores de pared de 25 a 45 W', 'Cargadores de pared de 65 W o más',
                    'Cargadores multipuerto y estaciones de carga', 'Cargadores de pared con cable', 'Cargadores para reloj y accesorios pequeños']
_RX_W = re.compile(r'(?<![\d.])(\d{1,3}) ?w\b')


def sub_cargador_pared(tn):
    if re.search(r'\breloj|\bwatch\b|\bairpods|\bauricular|\bearbuds|\bsmartwatch|\bpixel watch|\bgalaxy watch|'
                 r'\bfitbit|\bgarmin|\bamazfit|\bhuawei band|\bmi band|\boura\b|\banillo inteligente', tn) and \
       not re.search(r'estacion|\b[2-9] en 1\b|\bdock\b', tn):
        return 'Cargadores para reloj y accesorios pequeños'
    if re.search(r'\bregletas?\b|multicontactos?\b|power strip|extension electrica|\b[3-9] (tomas|enchufes)\b', tn):
        return 'Regletas y multicontactos'
    if re.search(r'\b([4-9]|1\d|2\d) puertos|\bmultipuerto|\bmulti ?puerto|\bestacion de carga|\bcharging station|\btorre de carga|\bconcentrador de carga|\bhub de carga|\b3 puertos|\b4 puertos', tn):
        return 'Cargadores multipuerto y estaciones de carga'
    ws = [int(x) for x in _RX_W.findall(tn) if 3 <= int(x) <= 400]
    w = max(ws) if ws else None
    con_cable = bool(re.search(r'\bcon cable|\b\+ cable|\bcable incluido|\bkit\b.{0,20}cable|\bcargador y cable|\bcable (usb|tipo|lightning|c a c)', tn))
    if w is None:
        return 'Cargadores de pared con cable' if con_cable else None
    if w >= 65: return 'Cargadores de pared de 65 W o más'
    if w >= 25: return 'Cargadores de pared de 25 a 45 W'
    return 'Cargadores de pared con cable' if con_cable else 'Cargadores de pared hasta 20 W'


# ---------------------------------------------- Blancos/Cobijas eléctricas
COBIJAS_E = ['Cobijas eléctricas individuales', 'Cobijas eléctricas matrimoniales', 'Cobijas eléctricas queen y king',
             'Mantas eléctricas USB y portátiles', 'Chales y mantas eléctricas para regazo', 'Almohadillas y cojines térmicos',
             'Repuestos y controles de cobija eléctrica']


def sub_cobija_electrica(tn):
    if re.search(r'\brepuesto|\breemplazo|\bcontrol(ador)? (de|para) (manta|cobija)|\bcable calefactor|\badaptador|\bcontrolador\b', tn):
        return 'Repuestos y controles de cobija eléctrica'
    if re.search(r'\balmohadilla|\bcojin|\bpad\b|\bcompresa|\bcalentador de (pies|manos)|\bpara (cuello|espalda|hombros|abdomen|cintura|rodilla)', tn):
        return 'Almohadillas y cojines térmicos'
    if re.search(r'\bchal\b|\bmanton|\bregazo|\bpara sofa\b|\bhombros\b|\bponcho|\bwearable|\busable|\bcon mangas|\bcapa\b', tn):
        return 'Chales y mantas eléctricas para regazo'
    if re.search(r'\busb\b|\bpilas|\bbateria|\bportatil|\bpower ?bank|\b5 ?v\b|\b12 ?v\b|\bpara (coche|auto|carro|camping)|\bde viaje', tn):
        return 'Mantas eléctricas USB y portátiles'
    t = _tamano_cama(tn)
    if t in ('king', 'queen'): return 'Cobijas eléctricas queen y king'
    if t == 'matrimonial': return 'Cobijas eléctricas matrimoniales'
    if t == 'individual': return 'Cobijas eléctricas individuales'
    m = re.search(r'(\d{2,3}) ?x ?(\d{2,3}) ?(cm|pulgadas|in\b|")', tn)
    if m:
        a, b = int(m.group(1)), int(m.group(2)); unit = m.group(3)
        w = max(a, b) * (2.54 if unit != 'cm' else 1)
        if w >= 200: return 'Cobijas eléctricas queen y king'
        if w >= 150: return 'Cobijas eléctricas matrimoniales'
        return 'Cobijas eléctricas individuales'
    return None


# --------------------------------------------------------- Belleza/Faciales
FACIALES = ['Cremas y sérums faciales', 'Limpiadores y tónicos', 'Mascarillas faciales', 'Contorno de ojos y labios',
            'Dispositivos de cuidado facial', 'Vaporizadores y equipo de spa', 'Exfoliantes y peelings', 'Cuidado facial masculino']
_FAC = _c([
    ('Vaporizadores y equipo de spa', r'\bvaporizador|\bvapor ozono|\bozono\b|\bhidrodermoabrasion|\bmicrodermoabrasion|\bequipo (de|para) (spa|estetica|facial profesional)|\banalizador de piel|\bcamilla|\blampara lupa|\bdermapen|\bmicroneedling|\bradiofrecuencia|\bhifu\b|\bcavitacion|\bpistola de oxigeno|\bmaquina (facial|de belleza)|\bcabina'),
    ('Dispositivos de cuidado facial', r'\bmascara led|\bluz led|\bterapia de luz|\blimpiador facial (electrico|sonico|ultrasonico)|\bcepillo facial|\bmasajeador facial|\bgua sha|\brodillo (de jade|facial|de cuarzo)|\bmicrocorriente|\bems\b|\bdispositivo|\bextractor de puntos negros|\baspirador de poros|\bpore cleaner|\bvacuum|\bespatula ultrasonica|\bnebulizador facial|\bvaporizador facial portatil|\bderma ?roller|\bdermaplaning|\bherramienta'),
    ('Contorno de ojos y labios', r'\bcontorno de ojos|\beye cream|\bcrema (para|de) ojos|\bojeras|\bparches (para|de) ojos|\beye patch|\bmascarilla (de|para) ojos|\bserum de pestanas|\bbalsamo labial|\blabios\b.{0,20}(mascarilla|balsamo|exfoliante)|\bcontorno\b'),
    ('Mascarillas faciales', r'\bmascarilla|\bmascara (facial|de arcilla|de tela|hidratante|peel)|\bsheet mask|\bface mask|\bmask\b|\bparches? (de|para) (acne|espinillas)|\bpimple patch'),
    ('Exfoliantes y peelings', r'\bexfoliante|\bpeeling|\bscrub\b|\bacido (glicolico|salicilico|lactico|mandelico)\b.{0,20}(exfoli|peel)|\bretinol\b.{0,10}peel|\bpeel\b'),
    ('Limpiadores y tónicos', r'\blimpiador|\bcleanser|\bjabon facial|\bgel limpiador|\bespuma limpiadora|\bagua micelar|\bdesmaquillante|\btonico|\btoner\b|\bbruma\b|\bmist\b|\bagua (de rosas|termal|floral)|\bhidrosol|\bmicellar'),
    ('Cuidado facial masculino', r'\bpara hombre|\bmasculino|\bmen\b|\bfor men|\bbarba\b.{0,20}(crema|aceite|balsamo)|\bafter ?shave|\bpost ?afeitado'),
    ('Cremas y sérums faciales', r'\bcrema|\bserum|\bsuero\b|\bhidratante|\bmoisturizer|\baceite facial|\bface oil|\bgel facial|\bemulsion|\besencia|\bessence|\bampolla|\bampoule|\bretinol|\bacido hialuronico|\bniacinamida|\bvitamina c\b|\bantiedad|\banti-?aging|\bantiarrugas|\bcolageno\b|\bprotector solar facial|\bbloqueador facial|\bspf\b|\bfacial\b'),
])


def sub_facial(tn):
    return _primera(tn, _FAC, {'Cremas y sérums faciales': 25, 'Cuidado facial masculino': 12, 'Dispositivos de cuidado facial': 6})


# ----------------------------------------------------------- Mascotas
JUGUETES_MASC = ['Juguetes para perro', 'Juguetes para gato', 'Juguetes para aves y roedores']
_JM = _c([
    ('Juguetes para aves y roedores', r'\baves?\b|\bpajaro|\bperico|\bloro|\bcotorra|\bhamster|\bconejo|\bcobaya|\bcuyo|\bchinchilla|\broedor|\bhuron|\brueda de ejercicio|\bcolumpio para (ave|perico)|\bperchas?\b'),
    ('Juguetes para gato', r'\bgatos?\b|\bgatito|\bfelino|\bcatnip|\bhierba gatera|\bvarita\b|\bcana (de|para) gato|\bplumas\b|\braton de juguete|\blaser\b|\bcat\b|\bkitten'),
    ('Juguetes para perro', r'\bperros?\b|\bcachorro|\bcanino|\bkong\b|\bmordedera|\bmordedor|\bpelota|\bcuerda|\bhueso\b|\bfrisbee|\bdisco volador|\blanzador|\bchirriante|\bsqueak|\bdog\b|\bpuppy|\bjuguete'),
])


def sub_juguete_mascota(tn):
    return _primera(tn, _JM, {'Juguetes para perro': 20})


CAMAS_MASC = ['Camas para perro', 'Camas para gato', 'Camas elevadas y colchonetas', 'Cuevas, iglús y tiendas para mascotas', 'Cojines y mantas para mascotas']
_CM = _c([
    ('Cuevas, iglús y tiendas para mascotas', r'\bcueva|\biglu|\btienda\b|\bcarpa|\bcasa\b|\bcasita|\bnido\b|\bcapucha|\bcon techo|\bcerrada|\btunel'),
    ('Camas elevadas y colchonetas', r'\belevada|\bcatre|\bhamaca|\bcuna elevada|\bcolchoneta|\btapete|\balfombrilla|\bcolchon (para|de) (perro|gato|mascota)|\bcojin plano|\bmat\b|\brefrescante|\bgel frio|\bcooling'),
    ('Cojines y mantas para mascotas', r'\bcojin|\bmanta|\bcobija|\bfrazada|\bfunda (de|para) cama|\bcubierta|\balmohada'),
    ('Camas para gato', r'\bgatos?\b|\bgatito|\bfelino|\bcat\b|\bkitten'),
    ('Camas para perro', r'\bperros?\b|\bcachorro|\bcanino|\bdog\b|\bpuppy|\bcama'),
])


def sub_cama_mascota(tn):
    return _primera(tn, _CM, {'Camas para perro': 25, 'Camas para gato': 5, 'Cojines y mantas para mascotas': 3})


# ------------------------------- Electrodomésticos/Pequeños electrodomésticos de cocina
PEQUENOS = ['Tostadoras', 'Arroceras y ollas multiusos', 'Wafleras, sandwicheras y creperas', 'Batidoras y amasadoras',
            'Máquinas de helados y postres', 'Freidoras eléctricas', 'Molinos y procesadores', 'Parrillas y planchas eléctricas',
            'Vaporeras y hervidores de huevos', 'Máquinas de palomitas y snacks', 'Máquinas de pan y pasta', 'Otros electrodomésticos de cocina']
_PEQ = _c([
    ('Tostadoras', r'\btostador|\btoaster'),
    ('Wafleras, sandwicheras y creperas', r'\bwaf+lera|\bwaffle|\bgofre|\bsandwichera|\bpanini|\bcrepera|\bcrepe|\braclette|\bmaquina (de|para) (hot cakes|pancakes|donas|cake pops|tacos|tortillas)|\btortilladora electrica'),
    ('Arroceras y ollas multiusos', r'\barrocera|\bolla (arrocera|electrica|de coccion lenta|multiusos|programable|a presion electrica|de presion electrica)|\bmulticooker|\binstant pot|\bslow cooker|\bcoccion lenta|\bolla lenta|\bcrock-?pot|\bolla express electrica'),
    ('Freidoras eléctricas', r'\bfreidora electrica|\bfreidora de aceite|\bfreidora\b(?!.*aire)|\bdeep fryer'),
    ('Máquinas de helados y postres', r'\bhelad|\bice cream|\bcreami|\byogurtera|\byogur|\bchocolatera|\bfuente de chocolate|\bslushi|\bgranizad|\braspado|\bmaquina de hielo|\balgodon de azucar|\bfondue'),
    ('Máquinas de palomitas y snacks', r'\bpalomit|\bpopcorn|\bhot dog|\bmaquina de (nachos|churros|elotes|crepas)|\bcalentador de (tortillas|nachos)'),
    ('Máquinas de pan y pasta', r'\bmaquina (de|para) (pan|pasta)|\bpanificadora|\bbread maker|\bamasadora de pan|\bextrusora de pasta|\bmaquina de tortillas'),
    ('Batidoras y amasadoras', r'\bbatidora|\bamasadora|\bmezcladora|\bstand mixer|\bplanetaria|\bmixer\b|\bespumador de leche|\bfrother|\bbatidor electrico'),
    ('Molinos y procesadores', r'\bmolino|\bmolinillo|\bprocesador|\bpicador|\bpicadora|\bchopper|\brallador electrico|\bcortador (de|para) verduras electrico|\bexprimidor electrico|\bmoledor|\bfood prep|\bcafe de grano'),
    ('Parrillas y planchas eléctricas', r'\bparrilla (electrica|de interior|de contacto)|\bplancha (electrica|de asar|de cocina)|\bgrill electric|\basador electrico|\bsarten electric|\belectric skillet|\bhot plate|\bparrilla\b|\bplancha\b|\bteppanyaki|\bgriddle'),
    ('Vaporeras y hervidores de huevos', r'\bvaporera|\bhervidor de huevos|\bcocedor de huevos|\begg cooker|\bsteamer|\bcocina al vapor|\bcalentador de biberones'),
    ('Otros electrodomésticos de cocina', r'\bbascula|\bbalanza|\bsellador|\bal vacio|\bdeshidratador|\bfiambrera electrica|\blonchera electrica|\bcalentador de comida|\bcalienta ?platos|\besterilizador|\babrelatas electrico|\bcuchillo electrico|\bafilador electrico|\bhervidor\b|\btetera electrica|\bmaquina de (sodas|agua con gas)|\bsodastream|\bcocedor|\btermo electrico|\bjarra electrica'),
])


def sub_pequeno_electro(tn):
    return _primera(tn, _PEQ, {'Otros electrodomésticos de cocina': 10, 'Parrillas y planchas eléctricas': 5})


# ----------------------------------------------- Herramientas/Herramientas manuales
MANUALES = ['Juegos de herramientas', 'Llaves y dados', 'Desarmadores y puntas', 'Pinzas y alicates', 'Martillos, cinceles y mazos',
            'Herramientas de corte manual', 'Prensas y sujeción', 'Herramientas manuales']
_MAN = _c([
    ('Juegos de herramientas', r'\bjuego de herramientas|\bkit de herramientas|\bset de herramientas|\bcaja de herramientas\b.{0,20}(piezas|pz|pcs)|\b\d{2,3} (piezas|pzs?|pcs)\b.{0,30}herramientas|\bherramientas\b.{0,20}\b\d{2,3} (piezas|pzs?|pcs)'),
    ('Llaves y dados', r'\bllaves?\b|\bdados?\b|\bmatraca|\btrinquete|\bratchet|\bvaso\b|\bvasos\b|\bsocket|\bwrench|\ballen\b|\bhexagonal|\btorx\b|\btorquimetro|\btorque|\bllave (inglesa|perica|stillson|combinada|espanola|mixta|de tubo|ajustable|de impacto)|\bautocle'),
    ('Desarmadores y puntas', r'\bdesarmador|\bdestornillador|\bscrewdriver|\bpuntas?\b|\bbits?\b|\bjuego de (desarmadores|destornilladores|puntas)|\bprecision\b.{0,20}(desarmador|destornillador)'),
    ('Pinzas y alicates', r'\bpinzas?\b|\balicates?\b|\bpliers?|\bpelacables|\bcrimpadora|\bponchadora|\bcortacable|\bcorta ?frio|\bde presion\b|\bprensa de mano|\btenazas?'),
    ('Martillos, cinceles y mazos', r'\bmartillo|\bmazo\b|\bmarro\b|\bmaceta\b|\bcincel|\bpunzon|\bbotador|\bhammer|\bhacha\b|\bmaza\b'),
    ('Herramientas de corte manual', r'\bcutter|\bnavaja|\bcuchilla|\bsegueta|\barco de sierra|\bserrucho|\bsierra manual|\bcortavidrio|\btijeras (de|para) (lamina|hojalata|jardin|podar|cable)|\bcortatubos|\blima\b|\bescofina|\bcortadora manual|\bcizalla|\bformon|\bgubia'),
    ('Prensas y sujeción', r'\bprensa|\bsargento|\bclamp|\btornillo de banco|\bsujeta|\babrazadera|\bgato\b|\bcaballete|\bsoporte de trabajo'),
])


def sub_manual(tn):
    return _primera(tn, _MAN, {'Juegos de herramientas': 0})


# ---------------------------------------------- Iluminación/Lámparas de techo
TECHO = ['Lámparas colgantes', 'Candiles y arañas', 'Plafones y lámparas de sobreponer', 'Rieles y spots', 'Lámparas industriales y de nave',
         'Ventiladores con luz', 'Lámparas de techo para exterior']
_TCH = _c([
    ('Ventiladores con luz', r'\bventilador'),
    ('Lámparas industriales y de nave', r'\bindustrial\b(?!.*(colgante|vintage|retro|estilo))|\bufo\b|\bhigh ?bay|\bnave\b|\bbodega\b|\balmacen\b|\bcampana industrial|\b\d{3} ?w\b.{0,20}(industrial|ufo|nave)'),
    ('Rieles y spots', r'\briel|\btrack\b|\bspots?\b|\bdirigible|\bproyector de techo|\bkit de iluminacion sobre riel'),
    ('Candiles y arañas', r'\bcandil|\barana|\bchandelier|\bde cristal|\bcristales|\bde velas|\bcandelabro'),
    ('Lámparas de techo para exterior', r'\bexterior|\boutdoor|\bjardin|\bporche|\bterraza|\bintemperie|\bip6[5-8]'),
    ('Lámparas colgantes', r'\bcolgante|\bpendant|\bsuspension|\bde isla|\bisla de cocina|\bfarol colgante|\blampara de (comedor|bar)'),
    ('Plafones y lámparas de sobreponer', r'\bplafon|\bsobreponer|\bsemiempotra|\bempotra|\bflush|\bde techo|\bceiling|\bcircular|\bredonda|\bcuadrada|\bpanel led|\bluz de techo|\blampara led'),
])


def sub_lampara_techo(tn):
    return _primera(tn, _TCH, {'Plafones y lámparas de sobreponer': 20})


# -------------------------------------------- Domótica/Iluminación inteligente
ILUM_INTEL = ['Focos inteligentes', 'Tiras LED inteligentes', 'Lámparas y plafones inteligentes', 'Luces inteligentes de exterior y solares',
              'Paneles y luces decorativas inteligentes', 'Controladores e interruptores de luz', 'Lámparas de escritorio y noche inteligentes']
_ILI = _c([
    ('Controladores e interruptores de luz', r'\bcontrolador|\bcontroller|\binterruptor|\bdimmer|\bregulador|\bapagador|\bswitch\b|\bhub\b|\bpuente|\bbridge|\bmodulo|\breceptor|\bfuente de alimentacion|\btransformador|\bconector'),
    ('Tiras LED inteligentes', r'\btiras? (led|de luz|de luces)|\bled strip|\bcinta led|\bneon\b|\bluces de cadena|\bstring lights|\bserie de luces|\bguirnalda|\bluces led (para|de) (tv|monitor|escritorio|habitacion)|\bretroiluminacion'),
    ('Paneles y luces decorativas inteligentes', r'\bpanel(es)? (led|de luz|hexagonal|modular)|\bhexagon|\bnanoleaf|\bgovee glide|\bluz de ambiente|\blampara (de ambiente|rgb de piso|de esquina)|\bbarra de luz|\blight bar|\bluz decorativa|\bproyector (de estrellas|galaxia|led)|\blampara de lava|\bluz nocturna\b(?!.*escritorio)'),
    ('Luces inteligentes de exterior y solares', r'\bsolar|\bexterior|\boutdoor|\bjardin|\bpatio|\bcamino|\bpathway|\bfachada|\bluz de inundacion|\bflood|\breflector|\bcon sensor de movimiento\b.{0,20}(exterior|solar)|\bip6[5-8]'),
    ('Lámparas de escritorio y noche inteligentes', r'\bde escritorio|\bde mesa|\bde noche|\bde buro|\bde lectura|\bluz nocturna|\bdespertador|\bde cabecera|\bbedside'),
    ('Lámparas y plafones inteligentes', r'\bplafon|\blampara de techo|\bluz de techo|\bempotra|\bdownlight|\bcolgante|\bcandil|\blampara de pie|\blampara de pared|\baplique|\bventilador de techo|\blampara\b'),
    ('Focos inteligentes', r'\bfoco|\bbombilla|\bbulb|\bfocos|\ba19\b|\be26\b|\be27\b|\bgu10|\bpar38|\bbr30|\bvela\b|\bfilamento|\bcandelabro'),
])


def sub_ilum_intel(tn):
    return _primera(tn, _ILI, {'Lámparas y plafones inteligentes': 15, 'Focos inteligentes': 5})


# ------------------------------------------------------- Teclados/Mecánicos
TECLADOS_MEC = ['Mecánicos 60% y compactos', 'Mecánicos 65% y 75%', 'Mecánicos TKL (80%)', 'Mecánicos tamaño completo',
                'Mecánicos inalámbricos', 'Switches, keycaps y accesorios']
_TKM = _c([
    ('Switches, keycaps y accesorios', r'\bkeycaps?\b|\bteclas? (de repuesto|pbt|abs)\b|\bswitch(es)?\b(?! (mecanico|azul|rojo|marron|red|blue|brown).{0,10}teclado)|^(?:\S+ ){0,3}switches\b|\bextractor|\bkeycap puller|\blubricante|\blube\b|\bestabilizador|\breposamunecas|\bwrist rest|\bcable (coiled|espiral|aviador)|\bfunda|\bcubierta|\bplate\b|\bpcb\b|\bkit (de )?(teclado|barebone)|\bbarebone'),
    ('Mecánicos 60% y compactos', r'\b60 ?%|\b61 teclas|\b64 teclas|\b40 ?%|\bmini\b|\bcompacto|\b6[0-4]-?key'),
    ('Mecánicos 65% y 75%', r'\b65 ?%|\b75 ?%|\b68 teclas|\b84 teclas|\b82 teclas|\b81 teclas|\b6[5-8]-?key|\b8[0-4]-?key|\b70 ?%'),
    ('Mecánicos TKL (80%)', r'\btkl\b|\btenkeyless|\b80 ?%|\b87 teclas|\b88 teclas|\bsin teclado numerico|\b87-?key'),
    ('Mecánicos tamaño completo', r'\b100 ?%|\b104 teclas|\b105 teclas|\b108 teclas|\btamano completo|\bfull ?size|\b96 ?%|\b98 ?%|\b1800|\bcon teclado numerico|\b99 teclas|\b10[4-8]-?key'),
    ('Mecánicos inalámbricos', r'\binalambric|\bwireless|\bbluetooth|\b2[.,]4 ?g|\btri-?mode|\btrimodo|\bmodo triple'),
])


def sub_teclado_mec(tn):
    return _primera(tn, _TKM, {'Mecánicos inalámbricos': 30})


# ------------------------------------------------------ Otros/Paneles solares
SOLAR = ['Paneles solares', 'Cargadores solares portátiles', 'Kits solares y controladores de carga', 'Accesorios y limpieza de paneles solares',
         'Luces y ventiladores solares', 'Bombas y calentadores solares']
_SOL = _c([
    ('Accesorios y limpieza de paneles solares', r'\blimpieza|\bcepillo|\bpertiga|\bprobador|\bmultimetro|\bconector(es)?\b|\bmc4\b|\bcable\b|\bsoporte|\bmontaje|\brack\b|\bestructura|\bcaja de conexion|\bfusible|\bdiodo|\bextension'),
    ('Luces y ventiladores solares', r'\bluz|\bluces|\bfoco|\blampara|\bfarol|\bventilador|\breflector|\bpaisaje|\bjardin\b(?!.*(kit|panel de \d))'),
    ('Bombas y calentadores solares', r'\bbomba|\bcalentador|\bcalefactor|\bfuente\b|\bboiler'),
    ('Cargadores solares portátiles', r'\bcargador|\bpower ?bank|\bbanco de energia|\bplegable|\bportatil|\bde bolsillo|\bmochila|\bcelular|\btelefono|\busb\b'),
    ('Kits solares y controladores de carga', r'\bkit\b|\bcontrolador|\binversor|\bregulador|\bbateria|\bsistema solar|\boff ?grid|\bestacion de energia|\bgenerador solar|\bmppt|\bpwm'),
    ('Paneles solares', r'\bpanel|\bmodulo solar|\bcelda|\bmonocristalino|\bpolicristalino|\bfotovoltaic|\b\d{2,3} ?w\b'),
])


def sub_solar(tn):
    return _primera(tn, _SOL, {'Paneles solares': 20, 'Accesorios y limpieza de paneles solares': 3})


# ------------------------------------------------------- Deportes/Pesas
PESAS = ['Mancuernas', 'Barras y discos', 'Kettlebells', 'Pesas de tobillo y chalecos con peso', 'Sets de pesas', 'Bancos y racks']
_PES = _c([
    ('Bancos y racks', r'\bbanco|\brack\b|\bsoporte (de|para) (barra|pesas|discos|mancuernas)|\bestante|\bportadiscos|\bjaula|\baparato para abdominales|\briel ejercitador'),
    ('Pesas de tobillo y chalecos con peso', r'\btobillera|\btobillo|\bmunequera con peso|\bchaleco|\blastre|\bcinturon (con|de) peso|\bpesas? (de|para) (tobillo|muneca|cuerpo)|\bbrazalete con peso'),
    ('Kettlebells', r'\bkettlebell|\bpesa rusa|\bpesas rusas'),
    ('Sets de pesas', r'\bset de (pesas|mancuernas|discos)|\bjuego de (pesas|mancuernas|discos)|\bkit de (pesas|mancuernas)|\b\d+ en 1\b|\bajustable'),
    ('Barras y discos', r'\bbarra|\bdiscos?\b|\bolimpic|\bbumper|\bcollarin|\bplates?\b|\bbarbell|\bcurl\b'),
    ('Mancuernas', r'\bmancuerna|\bdumbbell|\bpesas?\b'),
])


def sub_pesa(tn):
    return _primera(tn, _PES, {'Mancuernas': 15, 'Sets de pesas': 5})


OLA2 += [
    ('Instrumentos musicales', ['Baterías'], BATERIAS + ['Percusión'], lambda tn, sv: sub_bateria_musical(tn), None),
    ('Instrumentos musicales', ['Viento'], VIENTO, lambda tn, sv: sub_viento(tn), None),
    ('Instrumentos musicales', ['Teclados'], TECLADOS_MUS, lambda tn, sv: sub_teclado_musical(tn), None),
    ('Audífonos', ['Earbuds inalámbricos', 'Diadema inalámbrica'], AUDIFONOS_INAL, lambda tn, sv: sub_audifono_inal(tn, sv), None),
    ('Muebles', ['Colchones'], COLCHONES, lambda tn, sv: sub_colchon(tn), None),
    ('Muebles', ['Escritorios'], ESCRITORIOS, lambda tn, sv: sub_escritorio(tn), None),
    # Con resto: el sofá que no dice de qué tipo es ("Sala 3 2 1", "sofá
    # de tela gris") se queda en el de dos y tres plazas, que es el más
    # común; sin él quedaba en 'Sofás', que ya no existe en la lista.
    ('Muebles', ['Sofás'], SOFAS, lambda tn, sv: sub_sofa(tn), 'Sofás de 2 y 3 plazas'),
    ('Muebles', ['Mesas de centro'], MESAS_CENTRO, lambda tn, sv: sub_mesa_centro(tn), None),
    ('Muebles', ['Camas'], CAMAS, lambda tn, sv: sub_cama(tn), None),
    ('Juguetes y bebés', ['Bebés'], BEBES, lambda tn, sv: sub_bebe(tn), None),
    ('Cargadores y adaptadores', ['De pared'], CARGADORES_PARED, lambda tn, sv: sub_cargador_pared(tn), None),
    ('Blancos y ropa de cama', ['Cobijas eléctricas'], COBIJAS_E, lambda tn, sv: sub_cobija_electrica(tn), None),
    ('Belleza y cuidado personal', ['Faciales'], FACIALES, lambda tn, sv: sub_facial(tn), None),
    ('Mascotas', ['Juguetes'], JUGUETES_MASC, lambda tn, sv: sub_juguete_mascota(tn), None),
    ('Mascotas', ['Camas'], CAMAS_MASC, lambda tn, sv: sub_cama_mascota(tn), None),
    ('Electrodomésticos', ['Pequeños electrodomésticos de cocina'], PEQUENOS, lambda tn, sv: sub_pequeno_electro(tn), None),
    ('Herramientas', ['Herramientas manuales'], MANUALES, lambda tn, sv: sub_manual(tn), None),
    ('Iluminación', ['Lámparas de techo'], TECHO, lambda tn, sv: sub_lampara_techo(tn), None),
    ('Domótica y hogar inteligente', ['Iluminación inteligente'], ILUM_INTEL, lambda tn, sv: sub_ilum_intel(tn), None),
    ('Teclados', ['Mecánicos'], TECLADOS_MEC, lambda tn, sv: sub_teclado_mec(tn), None),
    ('Otros', ['Paneles solares'], SOLAR, lambda tn, sv: sub_solar(tn), None),
    ('Deportes y fitness', ['Pesas'], PESAS, lambda tn, sv: sub_pesa(tn), None),
]


# =========================================================== QUINTA OLA
# ------------------------------------------------ Bocinas/Bluetooth portátiles
BT_MARCAS_VIEJAS = ['JBL', 'Sony', 'Bose', 'Marshall y Bang & Olufsen', 'Anker Soundcore', 'Xiaomi y Tronsmart',
                    'Bocinas Bluetooth de otras marcas']
BT_PORTATILES = ['Mini bocinas y de llavero', 'Bocinas Bluetooth compactas (hasta 20 W)', 'Bocinas Bluetooth medianas (20 a 60 W)',
                 'Bocinas Bluetooth potentes (60 W o más)', 'Bocinas Bluetooth impermeables', 'Bocinas con luces LED',
                 'Bocinas Bluetooth con radio, USB y micrófono', 'Bocinas Bluetooth', 'Accesorios para bocinas']
_BTP = _c([
    ('Accesorios para bocinas', r'^(?:\S+ ){0,3}(funda|estuche|soporte|base|cargador|cable|adaptador|correa|bateria|alfombrilla|montaje|bracket|tapa|rejilla|repuesto)s?\b|\bpara (jbl|bose|sony|marshall|soundcore|sonos|echo|alexa|altavoz|bocina)\b.{0,10}(funda|estuche|soporte|cargador|cable|adaptador|correa)|\bcompatible con\b.{0,30}(funda|estuche|soporte|cargador|cable|adaptador)'),
    ('Mini bocinas y de llavero', r'\bmini\b|\bllavero|\bde bolsillo|\bpequen|\bbitty boomers|\bclip ?[2-5]\b|\bgo ?[2-4]\b|\bmicro\b|\bcompact'),
    ('Bocinas con luces LED', r'\bluces? led|\bled\b|\brgb\b|\bluz de colores|\bluces de colores|\bcon luz\b|\bluminos'),
    ('Bocinas Bluetooth impermeables', r'\bimpermeable|\bwaterproof|\bipx?[5-8]\b|\ba prueba de agua|\bresistente al agua|\bpara ducha|\bflotante|\bsumergible'),
    ('Bocinas Bluetooth con radio, USB y micrófono', r'\bradio\b|\bfm\b|\busb\b|\btf\b|\bmicro ?sd|\bcon microfono|\bkaraoke|\baux\b'),
])
_RX_W_BOC = re.compile(r'(?<![\d.])(\d{1,4}) ?w\b(?! ?h)')


def sub_bt_portatil(tn):
    sub = _primera(tn, _BTP, {'Bocinas con luces LED': 10, 'Bocinas Bluetooth impermeables': 15, 'Bocinas Bluetooth con radio, USB y micrófono': 25})
    if sub in ('Accesorios para bocinas', 'Mini bocinas y de llavero'):
        return sub
    ws = [int(x) for x in _RX_W_BOC.findall(tn) if 1 <= int(x) <= 5000]
    if re.search(r'\bpmpo\b', tn):
        ws = [w // 10 for w in ws]     # los "25,000 W PMPO" son marketing
    w = max(ws) if ws else None
    if w is not None and w >= 60:
        return 'Bocinas Bluetooth potentes (60 W o más)'
    if sub:
        return sub
    if w is None:
        return 'Bocinas Bluetooth'
    return 'Bocinas Bluetooth medianas (20 a 60 W)' if w >= 20 else 'Bocinas Bluetooth compactas (hasta 20 W)'



# --------------------------------------------- Componentes/Memoria RAM
RAM = ['RAM DDR5 para PC de escritorio', 'RAM DDR4 para PC de escritorio', 'RAM DDR5 para laptop (SODIMM)', 'RAM DDR4 para laptop (SODIMM)',
       'RAM DDR3 y anteriores', 'Memoria para servidor y workstation', 'RAM para Mac', 'Accesorios de memoria']
_RAM = _c([
    ('Accesorios de memoria', r'\badaptador|\bdisipador|\bheatsink|\bprobador|\btester|\bcaja\b|\bbandeja|\btarjeta adaptadora|\bconversor|\bextractor'),
    ('Memoria para servidor y workstation', r'\becc\b|\brdimm|\blrdimm|\bregistered|\bservidor|\bserver|\bworkstation|\bxeon|\bepyc|\bthreadripper|\bpoweredge|\bproliant|\bsupermicro'),
    ('RAM para Mac', r'\bmac\b|\bimac\b|\bmacbook|\bmac pro|\bmac mini|\bapple\b'),
    ('RAM DDR5 para laptop (SODIMM)', r'ddr5.{0,60}(sodimm|so-dimm|laptop|portatil|notebook|262-?pin)|(sodimm|so-dimm|laptop|portatil|notebook).{0,60}ddr5'),
    ('RAM DDR4 para laptop (SODIMM)', r'ddr4.{0,60}(sodimm|so-dimm|laptop|portatil|notebook|260-?pin)|(sodimm|so-dimm|laptop|portatil|notebook).{0,60}ddr4'),
    ('RAM DDR3 y anteriores', r'\bddr3|\bddr2\b|\bddr\b(?!\d)|\bpc3-|\bpc2-|\bsdram\b|\b1600 ?mhz|\b1333 ?mhz|\b1066|\b800 ?mhz|\b667 ?mhz|\b240-?pin|\b204-?pin'),
    ('RAM DDR5 para PC de escritorio', r'\bddr5|\bpc5-|\b288-?pin.{0,30}ddr5|\b(4800|5200|5600|6000|6400|6800|7200|8000) ?m(hz|t/s)'),
    ('RAM DDR4 para PC de escritorio', r'\bddr4|\bpc4-|\budimm|\bdimm\b|\b(2133|2400|2666|2933|3000|3200|3600|4000) ?mhz'),
])


def sub_ram(tn):
    if re.search(r'\bsodimm|\bso-dimm|\blaptop|\bportatil|\bnotebook', tn) and not re.search(r'ddr[2-5]', tn):
        return 'RAM DDR4 para laptop (SODIMM)'
    return _primera(tn, _RAM, {'RAM DDR4 para PC de escritorio': 5})


# ------------------------------------------------------ Mascotas/Comederos
COMEDEROS = ['Comederos automáticos', 'Platos y tazones para mascotas', 'Comederos elevados', 'Comederos lentos y antivoracidad',
             'Fuentes y dispensadores de agua', 'Comederos para aves y roedores', 'Tapetes y accesorios de alimentación']
_COM = _c([
    ('Tapetes y accesorios de alimentación', r'\btapete|\balfombrilla|\bmantel|\bcuchara (para|de) (comida|alimento|lata)|\btapa (para|de) lata|\bcontenedor (de|para) (comida|croquetas|alimento)|\bbolsa (de|para) (comida|croquetas)|\bdispensador de bolsas|\bmedidor|\bpala (para|de) (comida|croquetas)|\bportacomida|\bsoporte (para|de) (plato|tazon|comedero)'),
    ('Comederos para aves y roedores', r'\baves?\b|\bpajaro|\bperico|\bloro|\bcanario|\bcolibri|\bhamster|\bconejo|\bcobaya|\bcuyo|\broedor|\bgallina|\bpollo|\bacuario|\bpeces|\bpez\b|\btortuga|\breptil'),
    ('Fuentes y dispensadores de agua', r'\bfuente|\bbebedero|\bdispensador (de|automatico de) agua|\bagua\b.{0,30}(dispensador|fuente|bebedero)|\bbotella de agua|\bwater'),
    ('Comederos automáticos', r'\bautomatic|\bprogramable|\btemporizad|\bdispensador (de|automatico de) (comida|alimento|croquetas)|\balimentador (automatico|inteligente|programable|con camara|wifi)|\bsmart feeder|\bcon camara|\bwifi|\bapp\b|\bpor gravedad|\bgravedad'),
    ('Comederos lentos y antivoracidad', r'\blent[oa]\b|\balimentacion lenta|\bantivoracidad|\banti ?voracidad|\bslow feeder|\blaberinto|\binteractivo|\bde laberinto|\blick mat|\btapete de lamer|\bpuzzle'),
    ('Comederos elevados', r'\belevad|\bcon soporte|\bde altura ajustable|\baltura ajustable|\bcon base|\bde acero inoxidable con soporte|\bestacion de alimentacion|\bpedestal'),
    ('Platos y tazones para mascotas', r'\bplato|\btazon|\bcuenco|\bbowl|\bcomedero|\bdoble\b|\bde ceramica|\bde acero'),
])


def sub_comedero(tn):
    return _primera(tn, _COM, {'Platos y tazones para mascotas': 30, 'Comederos elevados': 6})


# ------------------------------------- Refacciones/Refacciones para electrodomésticos
REF_ELECTRO = ['Refacciones para lavadora y secadora', 'Refacciones para refrigerador', 'Refacciones para estufa y horno',
               'Refacciones para licuadora y batidora', 'Refacciones para aspiradora y robot', 'Refacciones para cafetera',
               'Refacciones para freidora de aire', 'Refacciones para microondas', 'Refacciones para aire acondicionado y ventilador',
               'Refacciones para calentador de agua', 'Refacciones para plancha y vaporizador', 'Refacciones para bocinas y audio',
               'Refacciones para otros electrodomésticos']
_RE = _c([
    ('Refacciones para freidora de aire', r'\bfreidora|\bair ?fryer|\bninja\b.{0,20}(cesta|canasta|forro)|\bcosori|\bforros? (de|para) (freidora|air)'),
    ('Refacciones para aspiradora y robot', r'\baspirador|\brobot\b|\broomba|\broborock|\becovacs|\bdeebot|\blimpiacristales|\bwinbot|\bhutt\b|\bdreame|\bshark\b.{0,20}(aspirador|filtro|cepillo)|\bdyson|\bmopa\b|\bpano de fregona|\bpanos? de (limpieza|microfibra) (para|compatible)|\bcepillo (lateral|central|de rodillo)|\bbolsas? (para|de) aspirador|\bfiltro hepa'),
    ('Refacciones para cafetera', r'\bcafetera|\bnespresso|\bkeurig|\bdolce gusto|\bespresso|\bportafiltro|\bcafe\b.{0,20}(filtro|junta|empaque|valvula)|\bmolino de cafe|\bgrupo de cafe'),
    ('Refacciones para lavadora y secadora', r'\blavadora|\bsecadora|\bwasher|\bdryer|\bagitador|\btapa de lavadora|\bmanguera de (lavadora|desague|entrada)|\bbomba de (drenaje|desague|agua de lavadora)|\bcorrea de (lavadora|secadora)|\belemento calefactor.{0,20}secador|\bfiltro de pelusa|\bperilla de lavadora|\bcapacitor de (lavadora|secadora)|\bamortiguador de lavadora|\bactuador de lavadora'),
    ('Refacciones para refrigerador', r'\brefrigerador|\bnevera|\bcongelador|\bfrigobar|\bfridge|\bfreezer|\bcompresor\b(?!.{0,20}aire)|\bempaque de (puerta|refrigerador)|\bdespachador de hielo|\bfabricador de hielo|\bice maker|\btermostato de refrigerador|\bcharola (de|del) (refrigerador|evaporador)|\bevaporador\b|\bdamper|\bmotor (de|del) ventilador del (refrigerador|evaporador|condensador)'),
    ('Refacciones para estufa y horno', r'\bestufa|\bhorno|\bparrilla de estufa|\bquemador|\bperilla de (estufa|horno)|\bencendedor|\btermopar|\bbujia de (estufa|horno)|\bresistencia (de|del) horno|\belemento calefactor (de|del) horno|\bvidrio de horno|\bcristal de (horno|estufa)|\bcomal de estufa|\bvalvula de gas|\bpiloto\b|\bboiler'),
    ('Refacciones para licuadora y batidora', r'\blicuadora|\bbatidora|\bblender|\bvaso de (licuadora|nutribullet|ninja)|\bcuchilla de (licuadora|batidora)|\bnutribullet|\bvitamix|\bempaque de (licuadora|vaso)|\bacoplador|\bacoplamiento|\btapa de (licuadora|vaso)|\bmixer\b'),
    ('Refacciones para microondas', r'\bmicroondas|\bmagnetron|\bplato (giratorio|de microondas)|\banillo giratorio|\bmica de microondas|\bfusible de microondas'),
    ('Refacciones para aire acondicionado y ventilador', r'\baire acondicionado|\bminisplit|\bmini split|\bsplit\b|\bcontrol remoto (para|de) (aire|minisplit|ventilador)|\bcapacitor (de|para) (aire|ventilador)|\bmotor (de|del) ventilador|\bfiltro (de|del) (aire acondicionado|minisplit)|\baspa|\bventilador\b|\bcompresor de aire acondicionado|\btarjeta (de|del) (minisplit|aire)|\bturbina'),
    ('Refacciones para calentador de agua', r'\bcalentador de agua|\bboiler|\bcalentador (de paso|instantaneo|solar)|\btermostato de (calentador|boiler)|\banodo|\bresistencia (de|para) (calentador|boiler)|\bpiloto de (calentador|boiler)|\bvalvula de (alivio|calentador)'),
    ('Refacciones para plancha y vaporizador', r'\bplancha\b|\bvaporizador|\bsuela\b|\bplancha de (vapor|ropa)|\bbase de plancha|\bcable de plancha'),
    ('Refacciones para bocinas y audio', r'\bbocina|\baltavoz|\bsonos|\bbose|\bjbl|\becho\b|\balexa|\baudio|\bwoofer|\btweeter|\bcargador (para|de) (bocina|altavoz|sonos|bose|jbl)|\bbase de cargador'),
    ('Refacciones para otros electrodomésticos', r'\brepuesto|\breemplazo|\brefaccion|\bcompatible|\bpieza|\bperilla|\bfiltro|\bsensor|\btermostato|\bmotor|\bresistencia|\bempaque|\bmanguera|\bvalvula|\bcable|\btapa|\bcuchilla|\bfusible|\bcapacitor|\bbanda|\bcorrea|\bengrane|\bbomba|\btarjeta|\bmodulo|\bboton'),
])


def sub_ref_electro(tn):
    return _primera(tn, _RE, {'Refacciones para otros electrodomésticos': 60, 'Refacciones para bocinas y audio': 8})


# ---------------------------------------------------- Refacciones/Para motos
REF_MOTO = ['Frenos de moto', 'Llantas y cámaras de moto', 'Cadenas, sprockets y transmisión', 'Luces de moto',
            'Carenados, plásticos y tanques', 'Motor, carburación y escape de moto', 'Eléctrico y baterías de moto',
            'Manubrios, espejos y controles', 'Suspensión y dirección de moto', 'Asientos, parrillas y accesorios de moto', 'Filtros y aceites de moto']
_RM = _c([
    ('Frenos de moto', r'\bfreno|\bbalata|\bpastilla|\bdisco de freno|\bcaliper|\bmordaza|\bbomba de freno|\bmanguera de freno|\bzapata|\btambor\b(?! selector)|\bpalanca de freno|\bpedal de freno'),
    ('Llantas y cámaras de moto', r'\bllanta|\bneumatico|\bcamara\b|\brin\b|\brines\b|\bmasa\b|\brayos?\b|\bbalero de rueda|\btubeless|\bmichelin|\bpirelli|\btimsun|\bkenda\b|\bvalvula de llanta'),
    ('Cadenas, sprockets y transmisión', r'\bcadena|\bsprocket|\bpinon|\bcorona\b|\bkit de (arrastre|transmision)|\bbanda (de|para) (transmision|cvt)|\bclutch|\bembrague|\bcaja de (cambios|velocidades)|\btambor selector|\bselector de cambios|\bpalanca de (cambios|velocidades)|\bvariador|\bcvt\b|\bclutch|\brodillos? (de|para) variador|\bcardan'),
    ('Luces de moto', r'\bfaro|\bluz\b|\bluces|\bcalavera|\bdireccional|\bintermitente|\bfoco\b|\bled\b|\bcuarto\b|\bstop\b|\blampara'),
    ('Eléctrico y baterías de moto', r'\bbateria|\bcdi\b|\bbobina|\bregulador|\brectificador|\bestator|\bmagneto|\bmarcha\b|\bmotor de arranque|\brele\b|\brelevador|\bswitch|\bfusible|\barnes|\bcableado|\bbujia|\bcapuchon|\bclaxon|\bsensor|\bvelocimetro|\btablero|\bcarburador electronico|\bencendido|\bcable de (bujia|acelerador|clutch|embrague|freno|velocimetro)'),
    ('Motor, carburación y escape de moto', r'\bmotor\b|\bcarburador|\bpiston|\bcilindro|\bcigueñal|\bciguenal|\bvalvula|\bculata|\bcabeza de motor|\bjunta|\bempaque|\bescape|\bmofle|\bsilenciador|\bmultiple|\binyector|\bbomba de (gasolina|aceite|combustible)|\bradiador|\btermostato|\bbomba de agua|\bkit de (motor|cilindro)|\btapa de (motor|clutch|magneto)|\barbol de levas|\bbalancin|\bcadena de tiempo|\btensor'),
    ('Manubrios, espejos y controles', r'\bmanubrio|\bmanillar|\bespejo|\bretrovisor|\bpuno|\bpuños|\bgrips?\b|\bmaneral|\bpalanca\b|\bacelerador|\bmanigueta|\bcontrol (de|del) (luces|manubrio)|\bmando\b|\bprotector de manos|\bcubre ?manos|\bbalancin de manubrio|\bcontrapeso'),
    ('Suspensión y dirección de moto', r'\bamortiguador|\bsuspension|\bhorquilla|\bbarra de (suspension|horquilla)|\bbotella\b|\bsello de (aceite|horquilla)|\bretenes|\bbalero de direccion|\bbasculante|\bmono ?shock|\btijera'),
    ('Carenados, plásticos y tanques', r'\bcarenado|\bplastico|\bcubierta|\bsalpicadera|\bguardafango|\btanque\b|\btapa de tanque|\bcofre|\bcarcasa|\bfaldon|\bdefensa|\bpanel\b|\bmascarilla|\bcupula|\bparabrisas|\bcubre|\bfrontal|\blateral\b|\btapa\b|\bemblema|\bcalcomania|\bsticker'),
    ('Asientos, parrillas y accesorios de moto', r'\basiento|\bsillin|\bparrilla|\bportaequipaje|\bmaleta|\bbaul\b|\btop case|\balforja|\bcaballete|\bpata\b|\bpata de cabra|\bsoporte lateral|\bcandado|\balarma|\bfunda\b|\bcubierta para moto|\bespejo\b|\bposapies|\bestribo|\bpedal\b|\bprotector\b|\bslider|\bdeslizador|\brespaldo|\bportaplacas|\bportacelular|\bsoporte (para|de) (celular|telefono)'),
    ('Filtros y aceites de moto', r'\bfiltro|\baceite|\blubricante|\bgrasa|\bliquido de frenos|\banticongelante|\brefrigerante|\baditivo'),
])


def sub_ref_moto(tn):
    # La comodín «Para motos» de algunas tiendas traía piezas de AUTO
    # («Cubre polvo macheta tsuru 1984 nissan»): esas no se reparten entre
    # las de moto (26-sep-2026). Devuelve None y las toma el repartidor de
    # autopartes.
    import reglas_nuevas as _rn
    if _rn.RX_AUTO_MARCA.search(tn) and not _rn.RX_MOTO_EXPLICITA.search(tn):
        return None
    return _primera(tn, _RM, {'Carenados, plásticos y tanques': 10, 'Asientos, parrillas y accesorios de moto': 5})


# ------------------------------------- Domótica/Interruptores inteligentes
INTERRUPTORES = ['Interruptores Wi-Fi', 'Interruptores Zigbee, Matter y Thread', 'Dimmers y reguladores inteligentes',
                 'Módulos y relés inteligentes', 'Interruptores y botones inalámbricos', 'Breakers y protectores inteligentes',
                 'Enchufes y contactos inteligentes', 'Interruptores táctiles y de escena']
_INT = _c([
    ('Breakers y protectores inteligentes', r'\bdisyuntor|\bbreaker|\binterruptor termomagnetico|\bproteccion contra sobre|\bpastilla\b|\b\d{2,3} ?a\b.{0,20}(disyuntor|breaker|wifi)|\bmedidor de energia|\bconsumo\b.{0,20}(monitor|medidor)'),
    ('Enchufes y contactos inteligentes', r'\benchufe|\bcontacto\b|\btomacorriente|\bsmart plug|\bplug\b|\bmulticontacto|\bregleta|\bextension\b|\bclavija'),
    ('Dimmers y reguladores inteligentes', r'\bdimmer|\bregulador|\batenuador|\bregulable|\bde intensidad|\bdimmable'),
    ('Módulos y relés inteligentes', r'\bmodulo|\brele\b|\brelay|\bmini\b.{0,20}(interruptor|switch)|\bde empotrar|\bpara empotrar|\bdetras del interruptor|\bsonoff (mini|basic|dual|4ch|pow|th)|\bshelly|\bplaca\b|\bcontrolador (de|para) (persiana|cortina|garaje|ventilador)|\bpersiana|\bcortina|\bgaraje'),
    ('Interruptores y botones inalámbricos', r'\binalambric|\bwireless|\bsin cableado|\bsin cable|\bboton\b|\bpulsador|\bcontrol remoto|\bremoto|\b433|\brf\b|\bkinetico|\bautoalimentado|\bsin bateria|\bsin pilas|\bcon pilas|\bmando\b'),
    ('Interruptores Zigbee, Matter y Thread', r'\bzigbee|\bmatter\b|\bthread\b|\bz-?wave|\bhue\b|\baqara|\bhomekit'),
    ('Interruptores táctiles y de escena', r'\btactil|\btouch|\bde escena|\bescenas?\b|\bpanel de (escena|control)|\bvidrio templado|\bcristal templado|\bneon\b'),
    ('Interruptores Wi-Fi', r'\bwifi|\bwi-?fi|\btuya|\bsmart life|\balexa|\bgoogle|\binteligente|\bsmart\b|\binterruptor|\bswitch'),
])


def sub_interruptor(tn):
    return _primera(tn, _INT, {'Interruptores Wi-Fi': 40, 'Interruptores táctiles y de escena': 10, 'Interruptores y botones inalámbricos': 6})


# ---------------------------------------- Electrodomésticos/Freidoras de aire
FREIDORAS = ['Freidoras de aire hasta 3 L', 'Freidoras de aire de 3.5 a 5 L', 'Freidoras de aire de 5.5 a 7 L',
             'Freidoras de aire de 8 L o más', 'Freidoras de aire de doble canasta', 'Hornos freidora y multifunción',
             'Accesorios y repuestos para freidora de aire', 'Freidoras de aire']
_RX_L = re.compile(r'(?<![\d.])(\d{1,2}(?:[.,]\d)?) ?(?:l\b|lt\b|lts\b|litros?\b|liter|qt\b|quart|cuartos?\b)')


def sub_freidora(tn):
    if re.search(r'^(?:\S+ ){0,3}(forros?|papel|cesta|canasta|bandeja|rejilla|molde|accesorios?|kit|asa|repuesto|reemplazo|filtro|tapa|manija|recetario|libro|silicona)\b|\brepuesto|\breemplazo|\baccesorios? (para|de)|\bforros? (de|para)|\bpapel (para|de)|\bcompatible (con|para)\b.{0,30}(cesta|canasta|forro|bandeja)', tn):
        return 'Accesorios y repuestos para freidora de aire'
    if re.search(r'\bdoble (canasta|cesta|zona|cajon)|\bdual ?zone|\bdual ?basket|\b2 (canastas|cestas|zonas|cajones)|\bdos (canastas|cestas|zonas)|\bdualzone|\bdual flex|\bflexdrawer', tn):
        return 'Freidoras de aire de doble canasta'
    if re.search(r'\bhorno freidora|\bhorno (de aire|tostador|multifuncion|de conveccion).{0,30}(freidora|air ?fryer)|\b(freidora|air ?fryer).{0,30}\bhorno|\btostador\b(?!.{0,30}(combo|sandwichera|\+))|\brotisserie|\basador giratorio', tn):
        return 'Hornos freidora y multifunción'
    vals = []
    for m in _RX_L.finditer(tn):
        v = float(m.group(1).replace(',', '.'))
        if re.search(r'qt|quart|cuarto', m.group(0)):
            v *= 0.946
        if 0.5 <= v <= 40:
            vals.append(v)
    if not vals:
        return 'Freidoras de aire'
    v = max(vals)
    if v >= 7.6: return 'Freidoras de aire de 8 L o más'
    if v >= 5.2: return 'Freidoras de aire de 5.5 a 7 L'
    if v >= 3.2: return 'Freidoras de aire de 3.5 a 5 L'
    return 'Freidoras de aire hasta 3 L'


# ------------------------------------------ Climatización/Aires acondicionados
AIRES = ['Minisplit', 'Aires acondicionados portátiles', 'Aires acondicionados de ventana', 'Aires acondicionados para auto y RV',
         'Mini enfriadores personales', 'Accesorios y refacciones de aire acondicionado', 'Aires acondicionados']
_AC = _c([
    ('Accesorios y refacciones de aire acondicionado', r'\bdeflector|\bcubierta|\bfunda|\bsoporte|\bbase\b|\bkit de (ventana|sellado|instalacion)|\bsellado de ventana|\bmanguera de (escape|salida|drenaje)|\btubo de escape|\bcontrol remoto|\bfiltro|\bcapacitor|\btarjeta|\bcompresor\b|\bmotor\b|\bventilador\b(?!.*(portatil|de aire acondicionado portatil))|\bgas refrigerante|\br-?410|\br-?32\b|\btuberia|\bcable|\bbomba de condensado|\btermostato|\bsensor|\brepuesto|\breemplazo|\bpanel de control|\bboard|\bplaca'),
    ('Aires acondicionados para auto y RV', r'\bpara (auto|coche|carro|camion|camioneta|vehiculo|rv|casa rodante|autocaravana|barco|lancha)|\b12 ?v\b|\b24 ?v\b|\bde techo\b.{0,20}(rv|camion)|\brv\b|\bcamper|\bfurgon'),
    ('Mini enfriadores personales', r'\bmini\b|\bpersonal|\bde escritorio|\bde mesa|\bportatil\b.{0,40}(usb|recargable|agua|humidificador|\d{3} ?ml)|\busb\b|\brecargable|\benfriador (de aire )?(personal|portatil|evaporativo|de agua)|\bventilador de aire acondicionado|\b\d{3} ?ml\b|\bhielo\b'),
    ('Aires acondicionados de ventana', r'\bde ventana|\bventana\b|\bwindow\b|\bde pared\b(?!.*(minisplit|split))|\bthrough the wall|\bcasetera'),
    ('Aires acondicionados portátiles', r'\bportatil|\bportable|\bmovil\b|\bcon ruedas|\bpinguino|\bde.?longhi'),
    ('Minisplit', r'\bminisplit|\bmini ?split|\bsplit\b|\binverter|\bton(elada)?s?\b|\b\d{4,5} ?btu|\bseer\b|\bmultisplit|\bmulti ?zona|\bcassette|\bpiso ?techo|\bde ducto|\bcondensadora|\bevaporadora|\bmirage|\bmabe\b|\bcarrier\b|\blg\b|\bhisense|\bmidea|\bwhirlpool|\byork\b|\bdaikin|\bgree\b|\bcolden'),
])


def sub_aire(tn):
    return _primera(tn, _AC, {'Minisplit': 30, 'Aires acondicionados portátiles': 10, 'Accesorios y refacciones de aire acondicionado': 3})


# --------------------------------------------- Blancos/Toallas, Sábanas, Protectores
TOALLAS = ['Toallas de baño', 'Toallas de manos y faciales', 'Juegos de toallas', 'Toallas de playa y alberca',
           'Batas y toallas con capucha', 'Toallas de microfibra y deportivas', 'Toallas de cocina y paños']
_TOA = _c([
    ('Toallas de cocina y paños', r'\bde cocina|\bpano|\bpanos|\btrapos?\b|\bsecador de (platos|trastes)|\bwaffle\b.{0,20}cocina|\bpara (platos|trastes|vajilla)'),
    ('Batas y toallas con capucha', r'\bbata|\balbornoz|\bcon capucha|\bponcho|\btoalla (para|de) bebe|\bbebe\b|\brobe\b|\bkimono|\bcapa de bano'),
    ('Toallas de microfibra y deportivas', r'\bmicrofibra|\bdeportiv|\bgym\b|\bgimnasio|\byoga|\bsecado rapido|\bde viaje|\bcamping|\bcompacta|\bpara (el )?cabello|\bturbante|\bde golf|\bgolf\b|\bde enfriamiento|\bcooling'),
    ('Toallas de playa y alberca', r'\bplaya|\balberca|\bpiscina|\bbeach|\bpool\b|\bde surf|\bredonda'),
    ('Juegos de toallas', r'\bjuego|\bset\b|\bpaquete de \d|\b\d+ piezas|\b\d+ pzas?|\bpack de \d|\bde \d+ (toallas|piezas)|\bcombo'),
    ('Toallas de manos y faciales', r'\bde manos?\b|\bfacial|\bpara (la )?cara|\bde tocador|\bwashcloth|\bhand towel|\bde mano\b|\btoallita|\bpequena|\b\d{2} ?x ?\d{2} ?cm\b(?!.*(bano|cuerpo))'),
    ('Toallas de baño', r'\bde bano|\bcuerpo|\bbath|\bextra grande|\bjumbo|\bde cuerpo|\btoalla'),
])


def sub_toalla(tn):
    return _primera(tn, _TOA, {'Toallas de baño': 30, 'Juegos de toallas': 8})


SABANAS = ['Sábanas individuales', 'Sábanas matrimoniales', 'Sábanas queen size', 'Sábanas king size', 'Sábanas para cuna y bebé',
           'Fundas de almohada', 'Fundas nórdicas y de edredón', 'Sábanas']


def sub_sabana(tn):
    if re.search(r'\bfundas? (de|para) almohada|\bpillowcase|\bfundas? de cojin', tn) and not re.search(r'\bjuego de sabanas|\bsabanas\b.{0,40}fundas', tn):
        return 'Fundas de almohada'
    if re.search(r'\bfunda (nordica|de edredon|para edredon)|\bduvet cover|\bcubre ?edredon', tn):
        return 'Fundas nórdicas y de edredón'
    if re.search(r'\bcuna|\bbebe|\bmoises|\bcorral|\bcrib\b|\bbassinet', tn):
        return 'Sábanas para cuna y bebé'
    t = _tamano_cama(tn)
    if re.search(r'\bsplit king|\bcalifornia king|\bcal king', tn): t = 'king'
    return {'king': 'Sábanas king size', 'queen': 'Sábanas queen size', 'matrimonial': 'Sábanas matrimoniales',
            'individual': 'Sábanas individuales'}.get(t, 'Sábanas')


PROTECTORES = ['Protectores de colchón impermeables', 'Protectores de colchón acolchados', 'Toppers y sobrecolchones',
               'Protectores de almohada', 'Protectores para cuna', 'Protectores de colchón']


def sub_protector(tn):
    if re.search(r'\btopper|\bsobrecolchon|\bmemory foam|\bviscoelastic|\bde espuma|\b\d ?cm de (espesor|grosor)|\bcolchoneta correctora|\bplumas|\bde ganso|\bpillow ?top', tn):
        return 'Toppers y sobrecolchones'
    if re.search(r'\bprotector(es)? (de|para) almohada|\bfunda protectora (de|para) almohada|\bpillow protector', tn):
        return 'Protectores de almohada'
    if re.search(r'\bcuna|\bbebe|\bmoises|\bcrib\b|\bpara ninos\b', tn):
        return 'Protectores para cuna'
    if re.search(r'\bimpermeable|\bwaterproof|\ba prueba de (agua|liquidos)|\bantifluidos|\bantiacaros|\bhipoalergenico|\bantimanchas|\bcubre ?colchon (impermeable|antifluidos)', tn):
        return 'Protectores de colchón impermeables'
    if re.search(r'\bacolchad|\bquilted|\bmullido|\bacolchonado|\bpad\b', tn):
        return 'Protectores de colchón acolchados'
    return 'Protectores de colchón'


# ------------------------------------------------------- Autos/Llantas
LLANTAS = ['Llantas para auto', 'Llantas para camioneta y SUV', 'Llantas para moto', 'Llantas para bicicleta',
           'Rines', 'Cámaras y accesorios de llanta', 'Llantas para carretilla y equipo']
_LL = _c([
    ('Cámaras y accesorios de llanta', r'\bcamara\b|\bvalvula|\btapon(es)? de (valvula|rin)|\bkit de reparacion|\bparche|\btuerca|\bbirlo|\bcubre ?llanta|\bmedidor de presion|\bmanometro|\bcompresor|\binflador|\bcadenas? (para|de) nieve|\bbalanceo|\bcontrapeso|\bsensor (de presion|tpms)|\btpms|\bllave de (cruz|rin|birlos)|\bprotector de rin|\bespaciador|\bseparador de rin|\bcubierta (de|para) llanta'),
    ('Rines', r'\brin(es)?\b|\bwheels?\b(?! (chair|barrow))|\baro\b|\baros\b|\bllantas? y rines'),
    ('Llantas para carretilla y equipo', r'\bcarretilla|\bdiablito|\bcarrito|\bpodadora|\btractor|\bmontacargas|\bcuatrimoto|\batv\b|\bgo ?kart|\bremolque|\btrailer|\bandador|\bsilla de ruedas|\bpatin|\bscooter|\bcarriola|\bmaquinaria|\bindustrial|\bmacizas?\b|\bsolida'),
    ('Llantas para bicicleta', r'\bbicicleta|\bbici\b|\bciclismo|\bmtb\b|\b(24|26|27\.5|29) ?(x|pulgadas)|\b700 ?x|\br ?(12|14|16|20|24|26|29)\b|\bkenda|\bmaxxis|\bcontinental grand|\bschwalbe|\bgravel|\bruta\b.{0,10}bici'),
    ('Llantas para moto', r'\bmoto|\bitalika|\b[1-4]\.\d{2}-\d{2}\b|\bmotocicleta|\bscooter|\btubeless\b(?!.*(auto|camioneta|rin \d{2}))|\b\d{2,3}/\d{2}-\d{2}\b|\bmichelin (pilot|city|road)|\bpirelli (diablo|angel|mt)|\btimsun|\bcst\b|\bmetzeler|\bdunlop (d\d|sportmax)'),
    ('Llantas para camioneta y SUV', r'\bcamioneta|\bsuv\b|\bpickup|\bpick-?up|\btodo terreno|\ball terrain|\ba/t\b|\bm/t\b|\bmud terrain|\blt ?\d{3}|\b4x4\b|\bsuv\b|\b\d{2} ?r ?\d{2}\.5\b|\b\d{2}x\d{1,2}\.\d{2}|\boff ?road|\b(31|33|35)x'),
    ('Llantas para auto', r'\bllanta|\bneumatico|\btire\b|\b\d{3}/\d{2} ?r ?1[3-9]|\bmichelin|\bbridgestone|\bgoodyear|\bcontinental|\bpirelli|\bfirestone|\bhankook|\byokohama|\bkumho|\bnexen|\btoyo|\bfalken|\buniroyal|\bgeneral tire|\bdunlop|\bbfgoodrich|\bcooper'),
])


# Medida de llanta de auto o camioneta, con o sin diagonal: «275/35zr20»,
# «235 70 r16», «185 r14», «p185/60 r16», «11 r24.5», «27x8.50 r14». Ancho 155+: «120/70zr17»
# y «110/80zr19» son de moto (26-sep-2026).
MEDIDA_AUTO = (r'(?:\b|lt|p)(?:1[5-9]|2\d|3[0-5])\d[ /-]\d{2} ?z? ?r ?f?\d{2}(\.5)?c?\b|\b\d{3} ?-? ?r ?1[3-9] ?c?\b|'
               r'\b\d{2} ?r ?\d{2}\.5\b|\b\d{2}x\d{1,2}\.\d{2} ?-?r? ?\d{2}\b|\b\d{1,2}\.\d{2} ?r ?1[3-9]\b|'
               r'\b\d{3}/\d{2} [a-z]+ r ?1[3-9]\b')


_MEDIDA_ANCHO = re.compile(r'(?:\b|lt|p)(\d{3})[ /-](\d{2}) ?z? ?r ?f?(\d{2})\b')


def _medida_de_camioneta(tn):
    """Ancho/perfil/rin de camioneta o SUV: rin 17+ con perfil 60+, rin 16
    con perfil 65+, rin 20+ con perfil 50+, o 265 de ancho o más en rin 17+.
    «205/55 r16» o «215/60 r16» (Jetta, Camry) quedan de auto."""
    for m in _MEDIDA_ANCHO.finditer(tn):
        w, a, r = (int(x) for x in m.groups())
        if (r >= 17 and a >= 60) or (r == 16 and a >= 65) or (r >= 20 and a >= 50) \
                or (w >= 265 and r >= 17 and a >= 50):
            return True
    return False


_RX_SUV = dict(_LL)['Llantas para camioneta y SUV']


def _auto_o_camioneta(tn, s):
    # Entre auto y camioneta no decide la posición en el título: «llanta» va
    # casi siempre primero y con la ventaja de 30 caracteres le ganaba a la
    # medida de camioneta que viene al final (26-sep-2026: «llanta kenda
    # klever a/t2 245/70r16» quedaba de auto; 10,877 fichas iban y venían).
    if s in ('Llantas para auto', 'Llantas para camioneta y SUV'):
        return 'Llantas para camioneta y SUV' if (_RX_SUV.search(tn) or _medida_de_camioneta(tn)) \
            else 'Llantas para auto'
    return s


def sub_llanta(tn):
    # Medida de auto («275/35zr20», «205/55 r16») y ninguna palabra de moto:
    # no es llanta de moto aunque diga «michelin pilot», ni de bicicleta por «r16» (26-sep-2026: 37
    # llantas Michelin Pilot Sport de auto estaban entre las de moto).
    if re.search(MEDIDA_AUTO, tn) and not re.search(
            r'\bmoto|motocicleta|scooter|cuatrimoto|italika|pirelli (diablo|angel)|pilot (power|road|street)|'
            r'michelin road|sportmax|metzeler|timsun', tn):
        s = _primera(tn, [x for x in _LL if x[0] not in ('Llantas para moto', 'Llantas para bicicleta')],
                     {'Llantas para auto': 30, 'Rines': 5})
        return _auto_o_camioneta(tn, s)
    s = _primera(tn, _LL, {'Llantas para auto': 30, 'Rines': 5})
    s = _auto_o_camioneta(tn, s)
    # «r14» o «r12» solos también son rines de auto y de moto: sin una
    # palabra de bicicleta no se decide bicicleta (26-sep-2026).
    if s == 'Llantas para bicicleta' and not re.search(
            r'bici|ciclismo|\bmtb\b|\b700 ?x|\b(12|16|20|24|26|27\.5|28|29) ?x ?[1-4](\.\d+)?\b|rodada|kenda|schwalbe|gravel', tn):
        return None
    return s


# ------------------------------------------------ Muebles/Mesas de comedor
COMEDOR = ['Mesas de comedor', 'Juegos de comedor', 'Mesas de comedor extensibles', 'Mesas altas y de bar',
           'Antecomedores y mesas de cocina', 'Mesas de comedor para exterior', 'Bancas de comedor']
_CMD = _c([
    ('Bancas de comedor', r'\bbanca|\bbanco (de|para) comedor|\bbench'),
    ('Mesas altas y de bar', r'\bmesa (alta|de bar|tipo bar|bistro)|\bde bar\b|\bbarra\b|\bpub\b|\baltura de bar|\balta\b'),
    ('Mesas de comedor para exterior', r'\bexterior|\bjardin|\bterraza|\bpatio|\boutdoor|\bratan|\brattan|\bplaya|\bcamping'),
    ('Juegos de comedor', r'\bjuego|\bcon \d sillas|\by \d sillas|\bcon sillas|\bset de comedor|\bcomedor (de|para) \d (personas|puestos|sillas)|\bconjunto|\bcomedor completo|\bcomedor (redondo|rectangular|cuadrado|moderno|minimalista)\b.{0,40}sillas|\bantecomedor\b.{0,30}sillas'),
    ('Mesas de comedor extensibles', r'\bextensible|\bextendible|\bplegable|\babatible|\bcon extension|\bexpandible'),
    ('Antecomedores y mesas de cocina', r'\bantecomedor|\bde cocina|\bdesayunador|\bpequena|\bpara \d personas\b(?!.*(6|8|10|12))|\bcompacta'),
    ('Mesas de comedor', r'\bmesa|\bcomedor'),
])


def sub_comedor(tn):
    return _primera(tn, _CMD, {'Mesas de comedor': 30, 'Antecomedores y mesas de cocina': 10, 'Mesas altas y de bar': 5})


# ---------------------------- Herramientas/Accesorios para herramientas eléctricas
ACC_ELEC = ['Brocas', 'Discos de corte y desbaste', 'Hojas y cuchillas de sierra', 'Lijas y accesorios de lijado',
            'Puntas y dados de impacto', 'Baterías y cargadores de herramienta', 'Accesorios para rotomartillo y demoledor',
            'Accesorios de multiherramienta y mototool', 'Refacciones de herramientas eléctricas', 'Accesorios para herramientas eléctricas']
_AE = _c([
    ('Baterías y cargadores de herramienta', r'\bbateria|\bcargador|\bpila\b|\bbattery|\bcharger|\badaptador de bateria'),
    ('Brocas', r'\bbrocas?\b|\bdrill bits?|\bjuego de brocas|\bmecha|\bbroca (para|de) (concreto|madera|metal|vidrio|azulejo)|\bsierra copa|\bhole saw|\bcopa\b|\bavellanador|\bmacho\b|\bmachuelo|\btarraja|\bcortador de agujeros'),
    ('Discos de corte y desbaste', r'\bdiscos?\b|\bde corte|\bde desbaste|\bflap\b|\bdisco (diamante|diamantado|abrasivo|de lija)|\bmuela|\bcepillo (de alambre|de copa)|\brueda (de alambre|abrasiva|de pulir)|\bpulido\b.{0,20}(disco|almohadilla|esponja)|\bbonete'),
    ('Hojas y cuchillas de sierra', r'\bhojas?\b|\bcuchillas?\b|\bsegueta|\bblade|\bsierra (circular|caladora|sable|de cinta).{0,20}(hoja|disco)|\bnavaja (de|para) (cutter|sierra)|\bcadena (de|para) motosierra|\bespada (de|para) motosierra|\bhoja (de|para) (sierra|caladora|sable|ingletadora)'),
    ('Lijas y accesorios de lijado', r'\blijas?\b|\blijado|\bsandpaper|\bpapel de lija|\bbanda de lija|\brollo de lija|\bplato de lija|\bbase de lija|\balmohadilla de lija|\bgrano \d'),
    ('Puntas y dados de impacto', r'\bpuntas?\b|\bbits?\b|\bdados? de impacto|\bimpacto\b.{0,20}(dado|punta|adaptador)|\bextension (de|para) (puntas|dados)|\bportapuntas|\bportabrocas|\bmandril|\bchuck\b|\badaptador (hexagonal|de dados|de mandril)'),
    ('Accesorios para rotomartillo y demoledor', r'\bsds\b|\bcincel(es)? (sds|para rotomartillo|de demolicion)|\bpunta (sds|de demolicion)|\bpala (sds|de demolicion)|\brotomartillo|\bdemoledor|\bmartillo demoledor'),
    ('Accesorios de multiherramienta y mototool', r'\bdremel|\bmototool|\bmultiherramienta|\bmulti ?tool|\boscilante|\bminitorno|\bmini torno|\bgrabado|\bfresas? (de|para) (dremel|mototool|grabado)|\bpiedras? (de|para) (dremel|mototool|pulir)|\bkit de (accesorios|dremel|mototool)'),
    ('Refacciones de herramientas eléctricas', r'\brepuesto|\breemplazo|\bcarbones?\b|\bescobillas? de carbon|\bcarbon brush|\binterruptor|\bswitch\b|\bmotor\b|\brotor|\bestator|\barmadura|\bengrane|\bpinon|\bcable\b|\bgatillo|\bresorte|\bempuñadura|\bmango\b|\bguarda\b|\bvolante|\bconjunto|\bensamble|\bkit de reparacion|\bcompatible con (dewalt|makita|bosch|milwaukee|black|truper|ryobi|craftsman|stanley)'),
    ('Accesorios para herramientas eléctricas', r'\baccesorio|\bkit\b|\bjuego\b|\bset\b|\bguia\b|\bbase\b|\bsoporte|\bmesa\b|\bprensa|\btope\b|\bcera\b|\bmaletin|\bestuche|\bbolsa|\bfunda|\bpara (taladro|sierra|esmeril|lijadora|router|compresor|hidrolavadora|caladora|amoladora|pulidora)'),
])


def sub_acc_electrica(tn):
    return _primera(tn, _AE, {'Accesorios para herramientas eléctricas': 40, 'Refacciones de herramientas eléctricas': 15})


# ---------------------------------------- Autos/Accesorios para bicicleta
ACC_BICI = ['Luces para bicicleta', 'Candados para bicicleta', 'Cascos y protección para ciclismo', 'Bombas e infladores',
            'Sillines y asientos', 'Bolsas, canastas y portabultos', 'Portabicicletas y soportes', 'Pedales, manubrios y puños',
            'Ciclocomputadoras y soportes para celular', 'Ropa y calzado de ciclismo', 'Refacciones y transmisión de bicicleta',
            'Asientos infantiles y remolques', 'Herramientas y mantenimiento de bicicleta', 'Accesorios para bicicleta']
_AB = _c([
    ('Asientos infantiles y remolques', r'\basiento (infantil|para nino|delantero para|trasero para)|\bsilla (infantil|para nino|portabebe)|\bportabebe|\bremolque|\btrailer|\bruedas de entrenamiento|\brueditas|\bbarra (de|para) (remolque|arrastre)'),
    ('Luces para bicicleta', r'\bluz|\bluces|\bfaro|\bfarol|\blampara|\bled\b|\breflej|\bcatadioptrico|\bintermitente|\bdireccional'),
    ('Candados para bicicleta', r'\bcandado|\bcadena (de|con) (seguridad|candado)|\bu-?lock|\bantirrobo|\bcable (de|con) (seguridad|candado)|\balarma'),
    ('Cascos y protección para ciclismo', r'\bcasco|\bhelmet|\brodillera|\bcodera|\bmunequera|\bprotecci|\bgafas|\blentes|\bguantes'),
    ('Bombas e infladores', r'\bbomba|\binflador|\bpump\b|\bco2\b|\bcompresor|\bmanometro'),
    ('Sillines y asientos', r'\bsillin|\basiento|\bsaddle|\bfunda (de|para) (sillin|asiento)|\bcubre ?asiento|\btija|\bposte de asiento|\bseatpost|\bcojin (de|para) (sillin|asiento)'),
    ('Bolsas, canastas y portabultos', r'\bbolsa|\balforja|\bcanasta|\bcanastilla|\bcesta|\bportabultos|\bportaequipaje|\bparrilla|\brack\b(?! (de|para) (auto|coche|techo|pared|piso))|\bmochila|\bpannier|\bbag\b'),
    ('Portabicicletas y soportes', r'\bportabici|\bporta ?bicicleta|\bsoporte (de|para) (bicicleta|bici|techo|pared|piso|rueda)|\bcolgador|\bgancho|\brack (de|para) (auto|coche|techo|pared|piso|bicicleta)|\bestacionamiento|\bcaballete|\bpata de cabra|\bpata lateral|\bsoporte lateral|\brodillo|\btrainer|\bentrenador|\bstand\b'),
    ('Pedales, manubrios y puños', r'\bpedal|\bmanubrio|\bmanillar|\bpuños?\b|\bpunos?\b|\bgrips?\b|\bcinta (de|para) manubrio|\bhandlebar|\bpotencia\b|\bstem\b|\bcuernos|\bbar ?ends|\bcalapies|\btimbre|\bcampana|\bclaxon|\bespejo|\bretrovisor'),
    ('Ciclocomputadoras y soportes para celular', r'\bciclocomputador|\bcomputadora (de|para) bicicleta|\bvelocimetro|\bcuentakilometros|\bodometro|\bgps\b|\bsoporte (de|para) (celular|telefono|smartphone|movil|gopro|camara)|\bporta ?celular|\bwahoo|\bgarmin|\bbryton|\bcadencia|\bsensor de (velocidad|cadencia|potencia)|\bmedidor de potencia'),
    ('Ropa y calzado de ciclismo', r'\bjersey|\bmaillot|\bculotte|\bculote|\bshorts? (de|para) ciclismo|\blicra|\bzapatillas|\bzapatos (de|para) ciclismo|\bcalas|\bcleats|\bcubrezapatos|\bchaleco|\bbalaclava|\bmangas|\bpierneras|\brompevientos|\bimpermeable\b.{0,10}(ciclismo|ciclista)'),
    ('Refacciones y transmisión de bicicleta', r'\bcadena\b|\bcassette|\bpinon|\bplato\b|\bbiela|\bdesviador|\bcambio|\bpalanca de cambio|\bshifter|\bfreno|\bbalata|\bpastilla|\bdisco de freno|\bcable (de|para) (freno|cambio)|\bfunda (de|para) cable|\bhorquilla|\bsuspension|\bamortiguador|\bllanta|\bcamara|\brin\b|\brines\b|\brayos?\b|\bmasa\b|\bbuje|\bbalero|\bcaja de (direccion|centro)|\beje\b|\bcuadro\b|\bmarco\b|\bguardabarro|\bsalpicadera|\bguardafango|\bcubierta|\bneumatico|\bshimano|\bsram|\btransmision|\bgrupo\b'),
    ('Herramientas y mantenimiento de bicicleta', r'\bherramienta|\bmultiherramienta|\bkit de (reparacion|parches|herramientas)|\bparches|\bdesmontador|\blubricante|\baceite|\bgrasa|\blimpiador|\bdesengrasante|\bcepillo (de|para) cadena|\bextractor|\btronchacadena|\bllave (de|para) (radios|pedales|cassette|centro)|\bsoporte de reparacion|\bcaballete de (taller|reparacion)'),
    ('Accesorios para bicicleta', r'\bbicicleta|\bbici\b|\bciclismo|\bciclista|\baccesorio'),
])


def sub_acc_bici(tn):
    return _primera(tn, _AB, {'Accesorios para bicicleta': 60, 'Refacciones y transmisión de bicicleta': 6})


# ---------------------------------------------------- Autos/Bocinas para auto
BOC_AUTO = ['Bocinas coaxiales de 6.5 pulgadas', 'Bocinas coaxiales 6x9 y 6x8', 'Bocinas de 4 a 5.25 pulgadas',
            'Bocinas de componentes', 'Tweeters', 'Medios rangos y bocinas profesionales', 'Subwoofers para auto',
            'Bocinas marinas y para moto', 'Accesorios de audio para auto']
_BA = _c([
    ('Accesorios de audio para auto', r'\badaptador|\barnes|\bcable\b|\brejilla|\bespaciador|\banillo|\bsoporte|\bbase\b|\bkit de (instalacion|cables)|\bcapacitor|\bcrossover\b(?!.*bocina)|\bdivisor de frecuencia|\bcaja (acustica|para bocina|de bocina)|\bgabinete|\bmaterial (aislante|acustico)|\bplug|\bconector|\bfusible|\bportafusible|\bcontrol de (bajos|graves)|\bbass knob|\bmicrofono|\bepoxi|\bpegamento'),
    ('Subwoofers para auto', r'\bsubwoofer|\bsub ?woofer|\bwoofer de (8|10|12|15|18)|\b(8|10|12|15|18) ?(pulgadas|")\b.{0,30}(woofer|graves|bajos)|\bcajon|\bamplificado|\bbajo\b'),
    ('Bocinas marinas y para moto', r'\bmarin|\bpara (moto|motocicleta|barco|lancha|jet ?ski|golf|atv|utv|cuatrimoto)|\bimpermeable|\bwaterproof|\bmotocicleta|\bmanubrio|\bmoto\b'),
    ('Tweeters', r'\btweeter|\bbala\b|\bdriver de (titanio|compresion)|\bagudos|\bsuper ?tweeter|\bdomo\b'),
    ('Medios rangos y bocinas profesionales', r'\bmedio ?rango|\bmid ?range|\bmid ?bass|\bmedios?\b|\bpro audio|\bprofesional|\b(6|8|10) ?(pulgadas|")\b.{0,30}(medio|mid|rango|profesional|abierto)|\bcono de papel|\bde competencia|\bspl\b|\baudiopipe|\bprv\b|\bcerwin|\btimpano'),
    ('Bocinas de componentes', r'\bcomponentes?\b|\bset de componentes|\bseparad|\bkit (de )?(2|3) vias\b.{0,30}(tweeter|componente)|\bcon tweeter y crossover|\bcomponent'),
    ('Bocinas coaxiales 6x9 y 6x8', r'\b6 ?x ?9\b|\b6x9|\b6 ?x ?8\b|\b6x8|\bovalad|\b5 ?x ?7\b|\b5x7|\b4 ?x ?6\b|\b4x6|\b4 ?x ?10'),
    ('Bocinas coaxiales de 6.5 pulgadas', r'\b6[.,]5 ?(pulgadas|"|\'\'|in\b)|\b6[.,]5\b|\b165 ?mm|\b16[.,]5 ?cm|\b6 ?(pulgadas|")|\b6 ?1/2'),
    ('Bocinas de 4 a 5.25 pulgadas', r'\b(4|5|5[.,]25|5[.,]5|3[.,]5|3) ?(pulgadas|"|\'\'|in\b)|\b(10|13) ?cm|\b(3|4|5)-inch|\bpequen'),
])


def sub_bocina_auto(tn):
    return _primera(tn, _BA, {'Accesorios de audio para auto': 5, 'Bocinas marinas y para moto': 8, 'Bocinas coaxiales de 6.5 pulgadas': 10, 'Bocinas de 4 a 5.25 pulgadas': 10})


OLA2 += [
    ('Bocinas', ['Bluetooth portátiles'] + BT_MARCAS_VIEJAS, BT_PORTATILES, lambda tn, sv: sub_bt_portatil(tn), None),
    ('Componentes y accesorios de PC', ['Memoria RAM'], RAM, lambda tn, sv: sub_ram(tn), None),
    ('Mascotas', ['Comederos'], COMEDEROS + ['Bebederos'], lambda tn, sv: sub_comedero(tn), None),
    ('Refacciones', ['Refacciones para electrodomésticos'], REF_ELECTRO, lambda tn, sv: sub_ref_electro(tn), None),
    ('Refacciones', ['Para motos'], REF_MOTO, lambda tn, sv: sub_ref_moto(tn), None),
    ('Domótica y hogar inteligente', ['Interruptores inteligentes'], INTERRUPTORES, lambda tn, sv: sub_interruptor(tn), None),
    ('Electrodomésticos', ['Freidoras de aire'], FREIDORAS, lambda tn, sv: sub_freidora(tn), None),
    ('Climatización', ['Aires acondicionados'], AIRES, lambda tn, sv: sub_aire(tn), None),
    ('Blancos y ropa de cama', ['Toallas'], TOALLAS, lambda tn, sv: sub_toalla(tn), None),
    ('Blancos y ropa de cama', ['Sábanas'], SABANAS, lambda tn, sv: sub_sabana(tn), None),
    ('Blancos y ropa de cama', ['Protectores de colchón'], PROTECTORES, lambda tn, sv: sub_protector(tn), None),
    ('Autos, bicicletas y motos', ['Llantas'], LLANTAS, lambda tn, sv: sub_llanta(tn), None),
    ('Muebles', ['Mesas de comedor'], COMEDOR, lambda tn, sv: sub_comedor(tn), None),
    ('Herramientas', ['Accesorios para herramientas eléctricas'], ACC_ELEC, lambda tn, sv: sub_acc_electrica(tn), None),
    ('Autos, bicicletas y motos', ['Accesorios para bicicleta'], ACC_BICI, lambda tn, sv: sub_acc_bici(tn), None),
    ('Autos, bicicletas y motos', ['Bocinas para auto'], BOC_AUTO, lambda tn, sv: sub_bocina_auto(tn), None),
]


# ------------------------------------------------ Muebles/Muebles de cocina
# 2,749 fichas en un solo cajón, y adentro dos productos que no se parecen en
# nada: la cocina integral de dos metros y la alacena suelta. Es la partición
# que hace kakaku y la que hace falta para que comparar sirva de algo: una
# cocina integral de 220 cm no compite con un gabinete superior de 80.
MUEBLES_COCINA = ['Cocinas integrales', 'Alacenas y gabinetes de cocina',
                  'Encimeras y cubiertas', 'Carros e islas de cocina']
_MCO = _c([
    ('Cocinas integrales', r'\bcocina integral|\bcocina modular|\bcocineta\b'),
    ('Carros e islas de cocina', r'\bcarro (de|para) cocina|\bcarrito (de|para) cocina|'
                                 r'\bisla (de|para) cocina|\bmueble auxiliar'),
    ('Encimeras y cubiertas', r'\bencimera|\bcubierta (de|para) cocina|\bbarra (de|para) cocina'),
    ('Alacenas y gabinetes de cocina', r'\balacena|\bgabinete|\barmario|\bdespensero|'
                                       r'\bmueble (rack )?(de |para )?cocina|\borganizador (de|para) cocina'),
])


def sub_mueble_cocina(tn):
    # Sólo la cabecera: «lámparas colgantes para isla de cocina» no es un
    # mueble de cocina, y mirando el título entero se iría a islas.
    return _primera(" ".join(tn.split()[:6]), _MCO, {})


# ------------------------------------------------------ Herramientas/Plomería
# «Plomería» juntaba el monomando, la regadera, la tarja, la bomba de agua y
# el tubo. Son cinco compras distintas con cinco rangos de precio distintos.
PLOMERIA = ['Grifos y monomandos', 'Regaderas y duchas', 'Tarjas y fregaderos',
            'Bombas de agua', 'Tuberías y conexiones', 'Sanitarios y accesorios de baño']
_PLO = _c([
    ('Bombas de agua', r'\bbomba (de agua|sumergible|centrifuga|periferica)|\bhidroneumatic|'
                       r'\bpresurizador|\bmotobomba'),
    ('Regaderas y duchas', r'\bregadera|\bducha\b|\bcabezal de ducha|\bshower\b'),
    ('Grifos y monomandos', r'\bmonomando|\bgrifo|\bmezcladora|\bfaucet|'
                            r'\bllave (de|para) (fregadero|lavabo|cocina|jardin|nariz)'),
    ('Tarjas y fregaderos', r'\btarja\b|\bfregadero|\blavabo|\blavadero\b|\bsink\b'),
    ('Sanitarios y accesorios de baño', r'\bwc\b|\binodoro|\bsanitario\b|\btaza de bano|'
                                        r'\bmingitorio|\basiento (de|para) (wc|bano)'),
    ('Tuberías y conexiones', r'\btuberia|\btubo (de|pvc|cpvc|cobre)|\bconexion|\bniple\b|'
                              r'\bcople\b|\bvalvula|\bcodo (de|pvc|cpvc)|\bmanguera (de|para) (agua|jardin)'),
])


def sub_plomeria(tn):
    return _primera(" ".join(tn.split()[:6]), _PLO, {})


OLA2 += [
    ('Muebles', ['Muebles de cocina'], MUEBLES_COCINA, lambda tn, sv: sub_mueble_cocina(tn), None),
    ('Herramientas', ['Plomería'], PLOMERIA, lambda tn, sv: sub_plomeria(tn), None),
]

# Tercer nivel de las categorías que seguían en plano (24-sep-2026): Baterías
# portátiles, Almacenamiento, Mouse, Aspiradoras, Televisores... Ver el módulo.
from subcategorias_tres_niveles import TRES_NIVELES  # noqa: E402
OLA2 += TRES_NIVELES
