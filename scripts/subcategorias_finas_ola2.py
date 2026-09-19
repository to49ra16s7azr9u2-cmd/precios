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
    ('Bocinas para auto', r'\bpara (auto|coche|carro|camioneta|moto|motocicleta|marina)|\bcoaxial|\btriaxial|\b6x9\b|\b6 ?x ?9\b|\btweeter|\bmid ?bass|\bwoofer de \d|\bautomotriz|\bpara vehiculo|\b12 ?v\b.{0,20}(altavoz|bocina)|marinas?\b'),
    ('Subwoofers', r'\bsubwoofer|\bsub ?woofer|\bsubgrave|\bbajos activos\b'),
    ('Amplificadores y receptores', r'\bamplificador|\breceptor|\breceiver\b|\bpreamplificador|\bpreamp\b|\bmezcladora|\bmixer\b|\bdac\b|\bconsola de audio'),
    ('Radios y reproductores', r'\bradio (am|fm|portatil|de bolsillo|de emergencia|despertador|solar)|\bam/fm\b|\bboombox\b|\breproductor de (cd|casete|cassette|dvd)|\btocadiscos|\bcd player\b|\bgrabadora\b|\bcasetera'),
    ('De fiesta y karaoke', r'\bkaraoke|\bfiesta|\bparty\b|\bdj\b|\bmicrofono inalambrico|con microfono|\bluces led\b|\bpartybox|\btorre de sonido|\bboombox pro|\bcon ruedas\b|\btrolley\b|\bbafle\b.{0,30}bluetooth'),
    ('Bafles y audio profesional', r'\bbafle|\bpa\b|\bmonitor de estudio|\bmonitores de estudio|\bstudio monitor|\bprofesional|\blinea de arreglo|\bline array|\bpasiv[oa]s?\b|\bactiv[oa]s? de \d+|\b\d{3,4} ?w\b.{0,20}(bafle|pasiv)|\bescenario|\bpa system|\bpara eventos|\bde 15 pulgadas|\bde 12 pulgadas|\bde 18 pulgadas|\bgabinete de audio\b|\bmegafono|\bperifoneo|\bde piso\b.{0,20}(torre|columna)|\bdriver\b|\bcompresion\b|\bdiafragma'),
    ('Empotrables y de exterior', r'\bempotra|\bde techo\b|\bin-?ceiling|\bin-?wall\b|\bde pared\b|\bpara pared\b|\bexterior|\boutdoor|\bjardin\b|\bpatio\b|\bde roca|\bimpermeable.{0,30}(pared|exterior)|\bwall mount|\bpara intemperie'),
    ('Para PC y escritorio', r'\bpara (pc|computadora|ordenador|laptop|escritorio|monitor)\b|\bde escritorio|\bdesktop\b|\bpc speaker|\b2\.1\b|\b2\.0\b.{0,20}(pc|computadora|escritorio)|\busb\b.{0,30}(pc|computadora|escritorio)|\bgaming\b.{0,20}(pc|escritorio)|\bminibocina\b.{0,20}(usb|pc)'),
    ('De estantería y Hi-Fi', r'\bestanteria|\bbookshelf|\bhi-?fi\b|\bhifi\b|\balta fidelidad|\bde torre\b|\btorre de audio|\bfloor ?standing|\bde piso\b|\bcanal central|\bcenter channel|\bhome theater|\bcine en casa|\b5\.1\b|\b7\.1\b|\bsistema de altavoces\b|\bde salon\b|\bde sala\b|\bstereo de casa|\bcomponentes? (de )?audio|\bminicomponente|\bmicrocomponente|\bequipo de sonido'),
    ('Bluetooth portátiles', r'\bbluetooth|\bportatil|\binalambric|\bwireless|\bimpermeable|\bipx?[4-8]\b|\brecargable|\btws\b|\bmini\b|\bde mano\b|\bbocina\b|\baltavoz|\bspeaker|\bparlante'),
])


def sub_bocina(tn):
    return _primera(tn, _BOCINAS, {'Bluetooth portátiles': 60, 'De estantería y Hi-Fi': 15})


# ------------------------------------------------------------- Videojuegos
VIDEOJUEGOS = ['Juegos PS5', 'Juegos PS4', 'Juegos Xbox', 'Juegos Nintendo Switch', 'Juegos para PC',
               'Juegos retro y otras plataformas', 'Consolas PlayStation', 'Consolas Xbox', 'Consolas Nintendo',
               'Consolas retro y portátiles', 'Controles y gamepads', 'Volantes, arcade y simuladores',
               'Realidad virtual', 'Cargadores, bases y soportes', 'Fundas, micas y protectores',
               'Cables y adaptadores', 'Tarjetas y suscripciones', 'Otros accesorios gamer']
_VJ_PLATAFORMA = [
    ('Juegos PS5', r'\bps ?5\b|playstation ?5\b|\bplaystation 5\b'),
    ('Juegos PS4', r'\bps ?4\b|playstation ?4\b'),
    ('Juegos Xbox', r'\bxbox\b'),
    ('Juegos Nintendo Switch', r'\bswitch\b|\bnintendo\b'),
    ('Juegos para PC', r'\bpc\b|\bsteam\b|\bwindows\b'),
    ('Juegos retro y otras plataformas', r'\bps ?[123]\b|playstation ?[123]\b|\bpsp\b|\bps vita\b|\bvita\b|\bwii\b|\bgamecube\b|\bnintendo (64|ds|3ds)\b|\b3ds\b|\bnds\b|\bgame ?boy|\bsnes\b|\bnes\b|\bsega\b|\bgenesis\b|\bdreamcast\b|\bmega ?drive|\batari\b|\bretro\b'),
]
_VJ = _c([
    ('Realidad virtual', r'\brealidad virtual|\bvr\b|\bmeta quest|\boculus|\bpsvr|\bps vr|\bhtc vive|\bpico 4|\bvisor\b.{0,20}(vr|virtual)'),
    ('Volantes, arcade y simuladores', r'\bvolante|\bpedales?\b|\bracing wheel|\barcade|\bfight ?stick|\bjoystick|\bpalanca|\bsimulador|\bcockpit|\bhotas\b|\bflight stick|\bgun\b.{0,10}(controller|control)|\bpistola\b'),
    ('Controles y gamepads', r'\bcontrol(es)?\b(?! remoto)|\bgamepad|\bmando\b|\bmandos\b|\bcontroller|\bjoy-?con|\bdualsense|\bdualshock|\bpro controller|\bjoycon|\bnunchuk|\bwiimote'),
    ('Cargadores, bases y soportes', r'\bcargador|\bcarga\b|\bbase de carga|\bestacion de carga|\bdock\b|\bdocking|\bsoporte|\bstand\b|\bbateria|\bpilas?\b|\bpower bank|\bventilador|\benfriador|\bcooling'),
    ('Fundas, micas y protectores', r'\bfunda|\bestuche|\bcase\b|\bmica|\bprotector|\bskin\b|\bcubierta|\bcarcasa|\bbolsa|\bmochila|\bgrips?\b|\bthumb ?grips?|\btapas? de joystick|\bcubre'),
    ('Cables y adaptadores', r'\bcable|\badaptador|\bconvertidor|\bhdmi\b|\bav\b|\bextension\b|\bhub\b|\bconector|\bmemoria|\btarjeta (micro ?sd|sd)|\bdisco duro|\bssd\b|\breceptor\b'),
    ('Tarjetas y suscripciones', r'\btarjeta (de )?(regalo|prepago|psn|xbox|nintendo|steam|roblox|fortnite)|\bgift card|\bsuscripcion|\bgame pass|\bps plus|\bplaystation plus|\bnintendo switch online|\bmembresia|\bv-?bucks|\brobux|\bcodigo digital|\bdigital code'),
    ('Otros accesorios gamer', r'\baccesori|\bkit\b|\bauricular|\baudifono|\bheadset|\bmicrofono|\bcamara\b|\bteclado|\bmouse\b|\btapete|\bmousepad|\bsilla|\bluz\b|\blampara|\bfigura|\bamiibo|\bllavero|\bposter|\bpeluche|\btaza|\bplayera'),
])
_VJ_CONSOLA = re.compile(r'^(?:\S+ ){0,2}consola\b|\bconsola (de )?(videojuegos|portatil|retro|nueva|nintendo|xbox|playstation|ps\d)|'
                         r'^(?:\S+ ){0,3}(playstation ?5|ps5|playstation ?4|ps4|xbox (series|one)|nintendo switch( 2| lite| oled)?|steam deck|rog ally|legion go)\b.{0,40}\b(consola|\d+ ?(gb|tb)|slim|pro|digital|edicion|bundle|paquete|blanco|negro)\b|'
                         r'\bsteam deck\b|\brog ally\b|\blegion go\b|\bmsi claw\b|\bconsola\b')
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
    if sub_vieja == 'Software' or re.search(r'\bjuego\b|\bvideojuego|\bedicion (estandar|deluxe|coleccionista|especial)\b|\bfisico\b', tn):
        for sub, rx in _VJ_PLATAFORMA:
            if re.search(rx, tn):
                return sub
        return acc or 'Juegos retro y otras plataformas'
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
    ('Ventiladores portátiles y de mano', r'\bde mano\b|\bportatil|\bmini\b|\bde cuello\b|\bcuello\b|\bpersonal|\bde bolsillo|\bcon bateria|\brecargable|\busb\b|\bplegable|\bcolgante\b|\bcochecito|\bcarriola|\bpara viaje|\bde viaje|\bde mano\b|\bventilador (turbo|pequeno)|\bcon cordon'),
    ('Ventiladores de mesa y clip', r'\bde mesa\b|\bde escritorio\b|\bcon clip\b|\bclip\b|\bde clip\b|\bsobremesa|\bcompacto\b|\bde buro\b|\bde oficina\b|\bcircular\b|\bcirculador de aire|\bvornado'),
    ('Ventiladores de pared', r'\bde pared\b|\bpara pared|\bwall\b|\bmural\b|\boscilante de pared'),
    ('Ventiladores de torre', r'\bde torre\b|\btorre\b|\btower\b|\bsin aspas\b|\bbladeless\b|\bde columna'),
    ('Ventiladores de piso e industriales', r'\bindustrial|\bde piso\b|\bde suelo\b|\bde alta velocidad|\bde tambor|\bde barril|\bdrum\b|\bbarril|\bcomercial|\bde taller|\bde bodega|\bde almacen|\bfloor\b|\bpotente\b|\bmetalico\b|\b\d{2} ?pulgadas\b.{0,20}(piso|industrial)|\bde caja\b|\bbox fan'),
    ('Ventiladores de pedestal', r'\bde pedestal\b|\bpedestal\b|\bde pie\b|\bstand fan|\baltura ajustable|\boscilante\b|\bde \d{2} ?pulgadas\b'),
])


def sub_ventilador(tn):
    return _primera(tn, _VENT, {'Ventiladores de pedestal': 25, 'Ventiladores portátiles y de mano': 5})


CALEFACTORES = ['Calefactores cerámicos y de aire', 'Calefactores de aceite', 'Calefactores infrarrojos y de cuarzo',
                'Calefactores de gas', 'Calefactores de pared y baño', 'Calefactores de exterior y patio',
                'Calefactores para pies y personales', 'Chimeneas eléctricas', 'Refacciones de calefactor']
_CALEF = _c([
    ('Refacciones de calefactor', r'\brepuesto|\breemplazo|\btermostato (de|para)|\bresistencia (de|para)|\bcontrol remoto para|\bfiltro (de|para)|\bpiloto\b|\bvalvula\b|\bquemador\b|\bmanguera\b|\bregulador\b'),
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
             'Bajos', 'Ukuleles', 'Mandolinas, banjos y otras cuerdas', 'Amplificadores de guitarra y bajo',
             'Pedales y efectos', 'Cuerdas de guitarra y bajo', 'Fundas, soportes y atriles', 'Accesorios de guitarra']
_GUIT = _c([
    ('Cuerdas de guitarra y bajo', r'\bcuerdas?\b(?! (de|para) (violin|viola|cello|violonchelo|contrabajo|arpa|piano))|\bstrings?\b|\bencordado|\bencordadura'),
    ('Pedales y efectos', r'\bpedal(es|era)?\b|\befectos?\b|\boverdrive|\bdistorsion|\bdistortion|\breverb|\bdelay\b|\blooper|\bwah\b|\bfuzz\b|\bchorus\b|\bcompresor\b|\bafinador de pedal|\bmultiefectos|\bprocesador de (guitarra|efectos)|\bstompbox'),
    ('Amplificadores de guitarra y bajo', r'\bamplificador|\bamp\b|\bcombo\b.{0,20}(guitarra|bajo|w\b)|\bcabezal|\bgabinete\b.{0,20}(guitarra|bajo|\d+x\d+)|\bcabinet\b|\bbafle para (guitarra|bajo)'),
    ('Fundas, soportes y atriles', r'\bfunda|\bestuche|\bcase\b|\bgig ?bag|\bsoporte|\bstand\b|\batril|\bcolgador|\bgancho de pared|\brack (de|para) guitarra|\bexhibi'),
    ('Accesorios de guitarra', r'\bcapo|\bcapotrasto|\bcejilla|\bcorrea|\bstrap\b|\bpuas?\b|\bpicks?\b|\bplumillas?\b|\bafinador|\btuner\b|\bslide\b|\bclavij|\bafinadores?\b|\bpastillas?\b|\bpickups?\b|\bpuente\b|\bcejuela|\bselector\b|\bpotenciometro|\bjack\b|\bcable (para|de) (guitarra|instrumento)|\bcable de instrumento|\btrastes?\b|\bgolpeador|\bpickguard|\bperillas?\b|\bknobs?\b|\bmastil|\bcuello de guitarra|\bdiapason|\bmetronomo|\bhumidificador|\bkit de (limpieza|mantenimiento|herramientas)|\blimpiador|\bpulidor|\bcuerdas de repuesto|\bboton (de|para) correa|\bstrap ?lock|\bcapodastro|\bejercitador de dedos|\bentrenador de dedos|\bhummer|\bwhammy|\bpalanca de (vibrato|tremolo)|\btremolo\b|\bcubierta de (puente|pastilla)|\btapa\b|\btornillos?\b|\bmecanismo de afinacion'),
    ('Ukuleles', r'\bukulele|\bukelele|\bukulel'),
    ('Mandolinas, banjos y otras cuerdas', r'\bmandolina|\bbanjo|\bcharango|\bcuatro\b|\bbalalaika|\bbouzouki|\blaud\b|\bbandurria|\bvihuela|\bguitarron|\bbajo sexto|\bbajo quinto|\brequinto|\bjarana|\bcavaquinho|\btres cubano|\bdobro|\bresonador|\bharpa|\barpa\b|\blira\b|\bcitara|\bsitar\b|\bkalimba|\bviolonchelo|\bcello\b|\bviolin\b|\bviola\b|\bcontrabajo'),
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
    ('Google Pixel', r'\bpixel\b|\bgoogle\b'),
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
_RX_PULG = re.compile(r'(\d{2}(?:[.,]\d)?)\s?(?:pulgadas|pulg\b|"|”|\'\'|inch|in\b|-inch)')


def _pulgadas(tn):
    m = _RX_PULG.search(tn)
    if not m:
        m = re.search(r'\b(1[0-9](?:[.,]\d)?)\b(?=\s?(?:fhd|hd|wuxga|qhd|oled|ips|led|touch|tactil))', tn)
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
_RX_MON = re.compile(r'(\d{2}(?:[.,]\d)?)\s?(?:pulgadas|pulg\b|"|”|\'\'|inch|in\b|-inch|”)')


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
    m = _RX_MON.search(tn)
    if not m:
        m = re.search(r'\b(1[5-9]|2[0-9]|3[0-9]|4[0-9])(?:[.,]\d)?\b(?=\s?(?:fhd|full hd|hd|qhd|wqhd|ips|va\b|led|lcd|oled|tn\b))', tn)
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
    ('Accesorios para bicicleta', r'\bbolsa|\balforja|\bcasco|\bcandado|\bluz\b|\bluces|\bbomba\b|\bportabici|\bsoporte|\brack\b|\bcanasta|\bcanastilla|\bsillin|\basiento|\bmanubrio|\bmanillar|\bpedal(es)?\b|\bcadena\b|\bllanta|\bcamara\b|\brin\b|\brines\b|\bfreno|\bpinon|\bcambio|\bdesviador|\bguardabarro|\bsalpicadera|\btimbre|\bespejo|\bcubierta\b|\bfunda|\bruedas? de entrenamiento|\brueditas|\bpata de cabra|\bsoporte lateral|\bportaequipaje|\bportabultos|\bremolque|\bkit de (reparacion|conversion)|\bherramienta|\bcuentakilometros|\bvelocimetro|\bciclocomputador|\bsilla (infantil|para nino|portabebe)|\bpuños|\bpunos|\bgrips?\b|\bcinta de manubrio|\bplato\b|\bbiela|\bcassette|\bhorquilla|\bsuspension\b(?! completa| delantera| doble)|\bamortiguador|\brayos?\b|\bmasa\b|\bbuje|\bejes?\b|\btrainer\b|\brodillo|\bentrenador\b|\bbotella|\bportabotella|\bguantes|\bjersey|\blentes|\bzapatillas|\bcalas|\bprotector'),
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
    ('Celulares', ['Android'], ANDROID, lambda tn, sv: sub_android(tn), 'Nokia y otras marcas'),
    ('Laptops', None, LAPTOPS, sub_laptop, 'Laptops de 15" y 16"'),
    ('Monitores', None, MONITORES, sub_monitor, '23 a 25 pulgadas'),
    ('Autos, bicicletas y motos', ['Bicicletas'], BICICLETAS, lambda tn, sv: sub_bicicleta(tn), 'Bicicletas urbanas y de paseo'),
]
