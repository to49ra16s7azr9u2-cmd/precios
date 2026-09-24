#!/usr/bin/env python3
"""Tercer nivel para las categorías que seguían en plano (24-sep-2026).

POR QUÉ
-------
35 de las 57 categorías ya tenían el escalón del medio (familias_subcategorias.py):
categoría -> familia -> subcategoría, como kakaku.com (パソコン -> ノートパソコン
-> 15インチ). Las otras seguían con una lista corta cortada por UN solo
atributo, y a veces el que no sirve para elegir: las power banks sólo por mAh
(1,204 de 1,883 en «Hasta 10,000 mAh», mezclando la MagSafe de 5,000 mAh con
la de llavero y la solar), las aspiradoras con un «Portátiles» de 670 que
junta la vertical inalámbrica con la de mano para el coche, los televisores
por resolución cuando la gente elige por pulgadas.

Aquí cada una se corta como la corta kakaku: primero por TIPO (lo que cambia
qué aparato es), y el atributo numérico (mAh, pulgadas, TB) queda de
subcategoría sólo donde es lo que se elige, o de filtro. Las familias de cada
categoría están en FAMILIAS_TRES_NIVELES, que familias_subcategorias.py suma a
su tabla.

Nada se divide por marca (la marca ya es un filtro aparte).

Cada entrada de TRES_NIVELES tiene la forma de OLA2 (categoría, viejas que
absorbe o None para toda la categoría, lista fina, repartidor, resto): el
clasificador la aplica a lo nuevo por afinar_ola2() y afinar_subcategorias.py
a lo que ya está.
"""
import re



def _c(ramas):
    return [(sub, re.compile(rx)) for sub, rx in ramas]


def _primera(tn, ramas, _penal=None):
    """La primera rama de la lista que reconoce el título: aquí el orden es
    la prioridad (el tipo le gana al tamaño), no la posición en el título."""
    for sub, rx in ramas:
        if rx.search(tn):
            return sub
    return None


def _mah(tn):
    """Capacidad en mAh del título ya normalizado, o None."""
    best = None
    for m in re.finditer(r'(\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?)\s?(k)?\s?(mah|ah)\b', tn):
        num, k, u = m.group(1), m.group(2), m.group(3)
        if re.fullmatch(r'\d{1,3}(?:[.,]\d{3})+', num):
            v = float(re.sub(r'[.,]', '', num))
        else:
            v = float(num.replace(',', '.'))
        if k:
            v *= 1000
        if u == 'ah':
            v *= 1000
        if 500 <= v <= 400000:
            best = max(best or 0, v)
    if best is None:
        m = re.search(r'\b(5|10|15|20|25|26|27|30|40|50)k\b', tn)
        if m:
            best = float(m.group(1)) * 1000
    return best


def _pulgadas(tn):
    m = re.search(r'\b(\d{2,3})(?:[.,]\d)?\s?(?:pulgadas|pulgada|pulg\b|"|\'\'|”|in\b|inch)', tn)
    if not m:
        m = re.search(r'(?:de|pantalla|tv|television|smart tv)\s(\d{2,3})\b(?! ?(?:hz|w\b|mm|cm|gb|pies|l\b|litros|kg))', tn)
    if m:
        v = int(m.group(1))
        if 10 <= v <= 120:
            return v
    return None


# ------------------------------------------------------ Baterías portátiles
BATERIAS = ['Hasta 10,000 mAh', '10,000 a 20,000 mAh', 'Más de 20,000 mAh',
            'Magnéticas (MagSafe y Qi2)', 'Inalámbricas', 'Con cable integrado o enchufe',
            'Solares', 'Para reloj, consola y otros aparatos',
            'Para laptop (60 W o más)', 'Estaciones de energía',
            'Accesorios y repuestos']
_BAT = _c([
    ('Estaciones de energía', r'estacion de energia|(?<!mophie )power ?station|generador (portatil|solar|electrico)|'
                              r'\b\d{3,4} ?wh\b|\bsolix\b|\becoflow (river|delta|trail)|\bjackery\b|\bbluetti\b|'
                              r'\bsalida ac\b.{0,40}\b\d{3,4} ?w\b|\bonda (pura|sinusoidal)'),
    ('Para reloj, consola y otros aparatos', r'\bpara (el |la |tu )?(apple watch|galaxy watch|reloj|relojes|control(ador)?|dualsense|'
                                             r'ps[45]|nintendo|switch|steam deck|gafas|lentes|anteojos|airpods)|'
                                             r'^(?:\S+ ){0,3}(chaleco|chamarra|calcetines|guantes)\b|\bestuche de carga\b'),
    ('Para laptop (60 W o más)', r'\blaptop|\bmacbook|\bnotebook|\bportatil(es)? (pc|de computadora)|'
                                 r'\b(6[05]|[7-9]\d|1\d\d|2[0-4]\d) ?w\b'),
    ('Magnéticas (MagSafe y Qi2)', r'magsafe|\bmagnetic|\bmagnetica|\bmagnetico|\bqi2\b|\bmaggo\b|\biman\b'),
    ('Solares', r'\bsolar(es)?\b'),
    ('Inalámbricas', r'carga inalambrica|cargador inalambrico|(power ?bank|bateria|banco de energia)[^,.]{0,30}inalambric|'
                     r'inalambric[ao]s? (power ?bank|bateria|banco)|wireless (charg|power)|\bqi\b'),
    ('Con cable integrado o enchufe', r'cables? integrad|cables? incorporad|built.?in cable|con cables?\b|'
                                      r'\benchufe\b|\bclavija\b|\bautoenchufe\b|\bplug\b'),
])
_BAT_ACC = re.compile(r'^(?:\S+ ){0,3}(fundas?|estuches?|case)\b|\bfunda (protectora|de silicon)|\bestuche compatible|'
                      r'\bbolsa (de|para) (almacenamiento|transporte)')


def sub_bateria(tn, sub_vieja=None):
    if sub_vieja == 'Accesorios y repuestos' or _BAT_ACC.search(tn):
        return 'Accesorios y repuestos'
    tipo = _primera(tn, _BAT, {})
    if tipo:
        return tipo
    mah = _mah(tn)
    if mah is None:
        return sub_vieja if sub_vieja in ('Hasta 10,000 mAh', '10,000 a 20,000 mAh', 'Más de 20,000 mAh') else 'Hasta 10,000 mAh'
    if mah <= 10000:
        return 'Hasta 10,000 mAh'
    if mah <= 20000:
        return '10,000 a 20,000 mAh'
    return 'Más de 20,000 mAh'


# ------------------------------------------------------------ Almacenamiento
ALMACENAMIENTO = ['SSD NVMe M.2', 'SSD SATA', 'Discos duros internos',
                  'SSD externos', 'Discos duros externos',
                  'Memorias USB', 'Memorias USB por mayoreo',
                  'Tarjetas microSD', 'Tarjetas SD y otras',
                  'NAS', 'Gabinetes y docks para disco']
_ALM = _c([
    ('Gabinetes y docks para disco', r'\bgabinete\b|\bcarcasa\b|\benclosure\b|\bdocking\b|\bdock\b|\bbase de conexion\b|'
                                     r'\badaptador (usb|sata)\b.{0,30}(disco|ssd|sata)|\bcaja (externa|para disco)|\bduplicador\b|'
                                     r'\bclonador\b|\bcaddy\b|\bbahia (para|de) disco'),
    ('NAS', r'\bnas\b(?!.{0,40}\b(disco duro|hdd|3\.5|interno)\b)(?<!red pro nas)|\bservidor de (archivos|almacenamiento)|\bnube personal\b|\bmy cloud\b|\bdiskstation\b'),
    ('Memorias USB por mayoreo', r'\b(\d{2,4}) (unidades|piezas|pzas|pack|paquete)\b.{0,40}(usb|memoria)|'
                                 r'\b(paquete|pack|lote) de (1\d|[2-9]\d|\d{3})\b|\blogotipo\b|\bpersonaliza|\bpromocional'),
    ('Tarjetas microSD', r'micro ?sd|\bmicrosdxc\b|\bmicrosdhc\b|\btf card\b|\btarjeta tf\b'),
    ('Tarjetas SD y otras', r'\bsdxc\b|\bsdhc\b|\btarjeta (de memoria|sd)\b|\bcfexpress\b|\bcompact ?flash\b|\bxqd\b|'
                            r'\bmemory card\b|\bsd card\b|\bmemoria sd\b|\bpsx?memcard\b|\bmemory stick\b'),
    ('Memorias USB', r'\bmemoria usb|\busb flash|\bflash drive|\bpendrive|\bpen drive|\bunidad(es)? flash|'
                     r'\bmemoria (flash|stick)|\bthumb drive|\blapiz usb|\bmemorias usb\b'),
    ('SSD externos', r'\bssd (externo|portatil)|\bexterno\b.{0,30}\bssd|\bssd\b.{0,40}\b(usb|externo|portatil|thunderbolt)\b|'
                     r'\bunidad(es)? de estado solido (externa|portatil)|\bportable ssd\b|\bt[579]\b.{0,20}ssd'),
    ('Discos duros externos', r'disco duro (externo|portatil)|\bhdd (externo|portatil)|\bexterno\b|\bexternal\b|\busb 3\.0\b.{0,30}\bdisco|'
                              r'\bmy passport\b|\bmy book\b|\bexpansion\b|\bone touch\b'),
    ('SSD NVMe M.2', r'\bnvme\b|\bpcie\b|\bgen ?[345]\b|\bm\.?2\b(?!.{0,30}\bsata\b)'),
    ('SSD SATA', r'\bssd\b|\bestado solido\b|\bsolid state\b'),
    ('Discos duros internos', r'\bhdd\b|disco duro|\b(5400|5900|7200|10000) ?rpm\b|\binterno\b|\b3\.5 ?(pulgadas|")|\bbarracuda\b'),
])


_ALM_INTERNO = [r for r in _ALM if r[0] not in ('SSD externos', 'Discos duros externos')]


def sub_almacenamiento(tn, sub_vieja=None):
    # «SSD interno ... para portátil» o «almacenamiento externo DIY» es
    # interno: si el título lo dice, no se mira lo de externo.
    s = _primera(tn, _ALM_INTERNO if re.search(r'\binterno\b|\binterna\b', tn) else _ALM, {})
    if s:
        return s
    return {'Memorias USB': 'Memorias USB', 'SSD': 'SSD SATA', 'Externo': 'Discos duros externos',
            'Tarjetas de memoria': 'Tarjetas SD y otras', 'Interno': 'Discos duros internos',
            'NAS': 'NAS'}.get(sub_vieja, sub_vieja)


# ------------------------------------------------------------------- Mouse
MOUSE = ['Inalámbricos', 'Con cable', 'Gaming inalámbricos', 'Gaming con cable',
         'Verticales y ergonómicos', 'Trackballs', 'Mousepads y tapetes']
_MOUSE = _c([
    ('Mousepads y tapetes', r'^(?:\S+ ){0,6}(mouse ?pad|mousepad|tapete|alfombrilla|pad (de|para) mouse|desk ?mat)|'
                            r'\bmousepad\b(?!.{0,20}\b(incluido|incluye|de regalo)\b)'),
    ('Trackballs', r'\btrackball|\bbola de seguimiento|\bbola de control|\bthumb ?ball'),
    ('Verticales y ergonómicos', r'\bvertical\b|\bergonomic|\bergonomico|\bergonomica|\bsin dolor|\btunel carpiano|\blift\b'),
])
_GAMER = re.compile(r'\bgam(er|ing)\b|\bpara juegos|\bde juegos|\bvideojuegos|\brgb\b|\bdpi\b.{0,10}\b(1[2-9]|[2-9]\d)[.,]?\d{3}|'
                    r'\b(8|4|2) ?k(hz)?\b.{0,20}(sondeo|polling)|\bsondeo\b|\bpolling\b|\besports\b|\bhero\b|\bpaw\d{4}')
_INAL = re.compile(r'inalambric|\bwireless\b|\bbluetooth\b|\b2[.,]4 ?g(hz)?\b|\brecargable\b|\blightspeed\b|\bsin cable\b')


def sub_mouse3(tn, sub_vieja=None):
    s = _primera(tn, _MOUSE, {})
    if s:
        return s
    if sub_vieja == 'Mousepads y tapetes':
        return sub_vieja
    inal = bool(_INAL.search(tn)) and not re.search(r'\bcon cable\b(?!.{0,10}/)|\balambric|\bcableado\b', tn)
    if _GAMER.search(tn) or sub_vieja == 'Gaming':
        return 'Gaming inalámbricos' if inal else 'Gaming con cable'
    if sub_vieja == 'Ergonómicos':
        return 'Verticales y ergonómicos'
    return 'Inalámbricos' if inal else 'Con cable'


# ----------------------------------------------------- Relojes inteligentes
RELOJES_INT = ['Smartwatches', 'Smartwatches con llamadas', 'Smartwatches deportivos y con GPS',
               'Smartwatches para niños', 'Bandas de actividad', 'Anillos inteligentes',
               'Correas y extensibles', 'Fundas, cargadores y protectores']
_RI = _c([
    ('Fundas, cargadores y protectores', r'^(?:\S+ ){0,4}(cargador|cable de carga|base de carga|protector|mica|funda|case|estuche|film|carcasa|bumper)\b'),
    ('Correas y extensibles', r'\bbandas? de (reloj|relojes)\b|\bcompatible (para|con)\b.{0,50}\b(bandas?|correas?|pulseras?)\b|^(?:\S+ ){0,6}(correas?|bandas? de repuesto|pulsera de repuesto|extensibles?|malla milanesa)\b|'
                              r'\bcompatible con (apple watch|galaxy watch|fitbit|garmin|amazfit|xiaomi).{0,30}\b(banda|correa|pulsera)|'
                              r'\b(banda|correa|pulsera)s? (compatible|de silicon|de cuero|de nylon|de acero|metalica)'),
    ('Anillos inteligentes', r'\banillo inteligente|\bsmart ?ring\b|\boura\b|\bgalaxy ring\b|\banillo\b.{0,30}(salud|sueno|monitor)'),
    ('Smartwatches para niños', r'\bninos?\b|\bnina\b|\bkids?\b|\binfantil|\bjunior\b|\bpara chicos'),
    ('Bandas de actividad', r'\bbanda (inteligente|de actividad|deportiva)|\bsmart ?band|\bmi band\b|\bband \d|\bfitbit (inspire|charge|luxe)|'
                            r'\bpulsera (inteligente|de actividad|deportiva)|\bactividad fisica\b.{0,20}pulsera|\bfitness tracker|'
                            r'\brastreador de (fitness|actividad)'),
    ('Smartwatches deportivos y con GPS', r'\bgps\b|\bforerunner|\bfenix\b|\binstinct\b|\bepix\b|\bpolar\b|\bcoros\b|\bsuunto\b|'
                                          r'\bmilitar|\btactico|\brugged\b|\bresistente\b.{0,20}(golpes|militar)|\boutdoor\b|'
                                          r'\bcorrer\b|\brunning\b|\btriatlon|\bbuceo\b|\bmultideporte'),
    ('Smartwatches con llamadas', r'\bllamadas?\b|\bcalls?\b|\bllamar\b|\besim\b|\blte\b|\b4g\b'),
])


def sub_reloj_int(tn, sub_vieja=None):
    s = _primera(tn, _RI, {})
    if s:
        return s
    if sub_vieja == 'Accesorios':
        return 'Correas y extensibles'
    if sub_vieja == 'Bandas de actividad':
        return sub_vieja
    return 'Smartwatches'


# -------------------------------------------------------------- Aspiradoras
ASPIRADORAS = ['Verticales y de escoba', 'De mano', 'Robots aspiradores', 'De trineo y con bolsa',
               'Seco y húmedo', 'Industriales y comerciales', 'Lavadoras de alfombras y vapor',
               'Accesorios']
_ASP = _c([
    ('Accesorios', r'^(?!aspirador|robot)(?:\S+ ){0,4}(filtros?|bolsas?|ventilador|boquillas?|cepillos?|repuestos?|refacciones?|mangueras?|kit de accesorios|'
                   r'rodillos?|cargador|bateria|baterias|adaptador|accesorios?|tubo|extension|pa[nñ]os?|mopas? de repuesto|'
                   r'almohadillas?|piezas?)\b|\brepuesto para\b|\bcompatible con\b.{0,40}\b(aspiradora|roomba|shark|dyson|xiaomi)|'
                   r'^(?!aspirador|robot).{0,60}\b(para|compatible con) (aspiradoras?|robot aspirador|roomba|irobot|shark|dyson)\b'),
    ('Robots aspiradores', r'\brobot\b|\broomba\b|\brobotica\b|\bdeebot\b|\broborock\b|\bautomatica\b.{0,20}aspiradora|\bmapeo\b|\blidar\b'),
    ('Lavadoras de alfombras y vapor', r'\bmanchas\b|\blava ?alfombras|\blavadora de alfombras|\blimpiadora de alfombras|\bcarpet ?cleaner|'
                                       r'\bextractor(a)? de (manchas|alfombras|tapiceria)|\bvapor\b|\bvaporizador|\bspot ?clean|'
                                       r'\blimpiador(a)? de (tapiceria|pisos)|\bfregadora|\bmopa (electrica|a vapor)|\bhydro'),
    ('Industriales y comerciales', r'\bindustrial|\bcomercial\b|\bcommercial\b|\btambor\b|\b\d{2,3} ?l(itros)?\b.{0,20}\b(acero|industrial)|'
                                   r'\bextractora\b|\bde hombro\b|\bmochila\b|\bbackpack\b|\bde espalda\b'),
    ('Seco y húmedo', r'\bseco ?(y|-|/)? ?(humedo|mojado)|\bhumedo ?(y|-|/)? ?seco|\bwd ?\d|\b(1\d|[2-9]\d) ?(l|litros)\b|\bsolidos y liquidos|\bliquidos\b|\bwet\b|'
                      r'\b\d{1,2} ?galones\b|\bgalon\b|\bshop ?vac\b|\bsopladora\b|\bde taller\b|\bcanister truper\b'),
    ('Robots aspiradores', r'\brobotic'),
    ('De mano', r'\bde mano\b|\bhandheld\b|\bmini\b|\bpara (auto|coche|carro|automovil|vehiculo)\b|\bautomotriz|\bde mesa\b|'
                r'\bportatil de mano|\bdustbuster\b|\bpara (teclado|colchon|cama|mascotas)\b|\bacaros\b|\bbarredora de (polvo|mesa)'),
    ('Verticales y de escoba', r'\bvertical|\bescoba\b|\bvarilla\b|\bstick\b|\bupright\b|\b[23] en 1\b|\binalambric|\bcordless\b|'
                               r'\bsin cable\b|\bstick\b|\bpole\b|\bligera\b'),
    ('De trineo y con bolsa', r'\btrineo\b|\bcanister\b|\bcon bolsa\b|\bsin bolsa\b|\bciclonic|\bmulticiclonic|\bde arrastre\b|'
                              r'\bcapsula\b|\bhepa\b.{0,20}\bcable\b|\bcon cable\b'),
])


def sub_aspiradora3(tn, sub_vieja=None):
    s = _primera(tn, _ASP, {})
    if s:
        return s
    return {'Portátiles': 'Verticales y de escoba', 'De mano': 'De mano', 'De tanque': 'Seco y húmedo',
            'Robots aspiradores': 'Robots aspiradores', 'De escoba': 'Verticales y de escoba',
            'Accesorios': 'Accesorios'}.get(sub_vieja, 'De trineo y con bolsa')


# --------------------------------------------------------------- Televisores
TELEVISORES = ['Hasta 32 pulgadas', '40 a 43 pulgadas', '50 a 55 pulgadas', '58 a 65 pulgadas',
               '70 pulgadas o más', 'Portátiles y para auto', 'Dispositivos de streaming',
               'Accesorios y soportes']
_TV_ACC = re.compile(r'^(?:\S+ ){0,4}(soportes?|base|bases|control remoto|controles|mando|cables?|antenas?|protector|'
                     r'funda|limpiador|adaptador|repuesto|tiras? led|retroiluminacion|kit de|patas|pies)\b|'
                     r'\bsoporte (de|para) (pared|tv|televisor|techo)|\bcontrol (remoto )?(universal|de repuesto|compatible)|'
                     r'\bmontaje (de|en) pared|\bpara (tv|televisor|pantalla)s?\b(?!.{0,5}\bde\b)')
_TV_STREAM = re.compile(r'\bfire ?(tv|stick)\b|\broku\b|\bchromecast\b|\bgoogle tv streamer\b|\bapple tv\b|\bstreaming\b|'
                        r'\btv ?box\b|\bandroid tv box\b|\bdecodificador|\breproductor multimedia|\bmi box\b|\bshield\b')
_TV_PORT = re.compile(r'\bportatil|\bauto\b|\bcoche\b|\bcarro\b|\breposacabezas|\bcamper|\b12 ?v\b|\brecargable\b|\bcon bateria')


def sub_tv3(tn, sub_vieja=None):
    p = _pulgadas(tn)
    if _TV_STREAM.search(tn) and (p is None or p < 19):
        return 'Dispositivos de streaming'
    if _TV_ACC.search(tn) or sub_vieja in ('Accesorios y soportes', 'Accesorios de TV'):
        return 'Accesorios y soportes'
    if sub_vieja == 'Portátiles' or _TV_PORT.search(tn) and (p is None or p <= 24):
        return 'Portátiles y para auto'
    if p is None:
        return {'Dispositivos de streaming': 'Dispositivos de streaming'}.get(sub_vieja, '50 a 55 pulgadas')
    if p <= 32:
        return 'Hasta 32 pulgadas'
    if p <= 45:
        return '40 a 43 pulgadas'
    if p <= 56:
        return '50 a 55 pulgadas'
    if p <= 66:
        return '58 a 65 pulgadas'
    return '70 pulgadas o más'


# ------------------------------------------------------------ Refrigeradores
REFRIGERADORES = ['Top mount', 'Bottom freezer', 'Dúplex (side by side)', 'French door',
                  'Una puerta', 'Frigobares', 'Congeladores', 'Cavas de vino',
                  'Refrigeradores comerciales', 'Vitrinas y enfriadores comerciales']
_REF = _c([
    ('Cavas de vino', r'\bcava\b|\bcavas\b|\bvinoteca|\bpara vinos?\b|\benfriador de vino|\bbotellas de vino'),
    ('Vitrinas y enfriadores comerciales', r'\bvitrina|\benfriador (vertical|comercial|de bebidas|de puerta)|\bexhibidor|'
                                           r'\bbarra fria|\bmesa fria|\bpuerta de cristal|\bpuerta de vidrio|\bpastelera'),
    ('Refrigeradores comerciales', r'\bcomercial|\bindustrial|\bmesa de trabajo refrigerada|\bbajo barra|\bdoble puerta de acero|'
                                   r'\bmaqueta|\bchest cooler|\breach.?in'),
    ('Congeladores', r'^(?:\S+ ){0,2}(congelador|congeladora|freezer|arcon)\b|\bcongelador (horizontal|vertical|de \d)'),
    ('Frigobares', r'\bfrigobar|\bminibar|\bmini ?refri|\bmini refrigerador|\bcompacto\b|\bmini fridge|\bde (1|2|3|4)(\.\d)? pies|'
                   r'\bportatil|\bpara auto\b|\b12 ?v\b|\bcooler\b.{0,20}(electrico|compresor)|\bde habitacion\b'),
    ('French door', r'\bfrench ?door|\b3 puertas\b|\b4 puertas\b|\btres puertas|\bcuatro puertas|\bpuerta francesa'),
    ('Dúplex (side by side)', r'\bduplex\b|\bside ?by ?side|\blado a lado'),
    ('Bottom freezer', r'\bbottom\b|\bcongelador inferior|\bcongelador abajo'),
    ('Una puerta', r'\buna puerta\b|\b1 puerta\b|\bsingle door\b|\bone door\b'),
    ('Top mount', r'\btop ?mount|\bcongelador superior|\bdos puertas|\b2 puertas|\brefrigerador\b|\brefrigeradora\b|\bpies\b'),
])


def sub_refri3(tn, sub_vieja=None):
    s = _primera(tn, _REF, {})
    if s:
        return s
    return {'Frigobares': 'Frigobares', 'Uso comercial': 'Refrigeradores comerciales', 'Congeladores': 'Congeladores',
            'Cavas de vino': 'Cavas de vino'}.get(sub_vieja, 'Top mount')


# -------------------------------------------------- Computadoras de escritorio
ESCRITORIO = ['PC gamer', 'Torres de casa y oficina', 'All in One', 'Mini PC',
              'Reacondicionadas']
_ESC = _c([
    ('Reacondicionadas', r'reacondicionad|\brenewed\b|\brefurbished\b|\bseminuevo|\busad[oa]\b|\bgrado [abc]\b'),
    ('All in One', r'\ball ?in ?one\b|\btodo en (uno|1)\b|\baio\b|\bimac\b'),
    ('Mini PC', r'\bmini ?pc\b|\bmini (computadora|ordenador|desktop)|\bmac mini\b|\bnuc\b|\btiny\b|\bmicro (pc|desktop)|'
                r'\bmicro form factor|\busff\b|\bstick pc\b|\bbarebone\b|\bmini torre\b'),
    ('Torres de casa y oficina', r'\bworkstation|\bestacion de trabajo|\bthinkstation|\bprecision\b|\bz[248] g\d|\bxeon\b|\bquadro\b|'
                              r'\brtx a\d{3,4}\b|\bmac (pro|studio)\b'),
    ('PC gamer', r'\bgam(er|ing)\b|\brtx ?\d{4}|\bgtx ?\d{3,4}|\brx ?\d{4}\b|\bpara juegos|\bryzen [79]\b.{0,40}(rtx|rx)|\brgb\b'),
])


def sub_escritorio3(tn, sub_vieja=None):
    s = _primera(tn, _ESC, {})
    if s:
        return s
    return {'All in One': 'All in One', 'Mini PC': 'Mini PC'}.get(sub_vieja, 'Torres de casa y oficina')


# -------------------------------------------------------------------- Viajes
VIAJES = ['Maletas de cabina', 'Maletas medianas', 'Maletas grandes', 'Sets de maletas',
          'Mochilas y bolsas de viaje', 'Accesorios de viaje', 'Camping', 'Pesca']
_VIA = _c([
    ('Pesca', r'\bpesca\b|\bcana de pescar|\bcarrete\b|\banzuelo|\bsenuelo|\bfishing\b'),
    # Lo que ARRANCA como maleta es maleta aunque traiga candado o almohada.
    ('Accesorios de viaje', r'^(?!maleta|equipaje|set de maleta|juego de maleta)(?:.*)(\balmohada\b|\bcandado|\betiquetas?\b|'
                            r'\borganizador(es)? de (maleta|equipaje|viaje)|\bcubos de (embalaje|empaque)|'
                            r'\bbascula (de|para) (equipaje|maleta)|\bfunda (para|de) maleta|\bcubre ?maleta|\bneceser|\bestuche\b|'
                            r'\btocador\b|\bbolsas? de aseo|\bcosmetiquera|'
                            r'\badaptador (universal|de viaje)|\bantifaz|\btapones|\bcorrea (de|para) equipaje|\bbolsas? de compresion|'
                            r'\bpasaporte|\bkit de viaje|\bbotella(s)? de viaje|\bcojin de viaje)'),
    ('Sets de maletas', r'\b(set|juego) de (\d )?(maletas|equipaje)|\bmaletas?\b.{0,40}\b(set|juego) de\b|'
                        r'\bmaletas?\b.{0,40}\b\d ?(piezas|pzs)\b|\bpaquete de (2|3|4) maletas'),
    ('Mochilas y bolsas de viaje', r'\bentrenamiento\b|\b\d{2} ?l\b|\bgym\b|\bmochila|\bbackpack\b|\bmaleta de mano\b.{0,10}\bmochila|\bbolsa de viaje|\bmaleta de lona|\bduffel|'
                                   r'\bmaletin\b|\bpetate\b|\bbolso de viaje|\bmaleta deportiva|\bbolsa de lona|\bweekender|'
                                   r'\briñonera|\brinonera|\bcangurera'),
    ('Camping', r'\bcamping\b|\bcampismo\b|\bcasa de campana|\bcarpa\b|\bsleeping|\bsaco de dormir|\bhamaca\b|\blinterna\b|\bnevera\b|\bhielera'),
    ('Maletas de cabina', r'\bcabina\b|\bcarry ?on\b|\bde mano\b|\bequipaje de mano|\b(18|19|20|21|22) ?(pulgadas|"|in\b|pulg)|\bpequena\b|\b10 ?kg\b'),
    ('Maletas grandes', r'\bgrande\b|\b(28|29|30|31|32) ?(pulgadas|"|in\b|pulg)|\b(23|25|32) ?kg\b|\bdocumentar\b|\bextra ?grande'),
    ('Maletas medianas', r'\bmediana\b|\b(24|25|26|27) ?(pulgadas|"|in\b|pulg)|\bmaleta'),
])


def sub_viaje(tn, sub_vieja=None):
    s = _primera(tn, _VIA, {})
    if s:
        return s
    return {'Maletas': 'Maletas medianas', 'Maletas de cabina': 'Maletas de cabina', 'Camping': 'Camping',
            'Mochilas y bolsas de viaje': 'Mochilas y bolsas de viaje', 'Maletas grandes': 'Maletas grandes',
            'Pesca': 'Pesca', 'Sets de maletas': 'Sets de maletas'}.get(sub_vieja, 'Accesorios de viaje')


# --------------------------------------------------------------------- Salud
SALUD = ['Cepillos de dientes eléctricos', 'Irrigadores bucales', 'Cuidado dental',
         'Baumanómetros', 'Oxímetros', 'Termómetros', 'Glucómetros', 'Nebulizadores', 'Otros aparatos médicos',
         'Básculas', 'Sillas de ruedas', 'Andaderas, bastones y muletas', 'Movilidad y apoyo', 'Salud']
_SAL = _c([
    ('Irrigadores bucales', r'\birrigador|\bwater ?pik|\bwaterpik|\bhilo dental de agua|\bflosser\b|\bhilo dental (electrico|de agua)'),
    ('Cepillos de dientes eléctricos', r'\bcepillo(s)? (de dientes |dental )?(electrico|sonico|recargable)|\boral-?b (pro|io|vitality|genius)|'
                                       r'\bsonicare\b|\bcepillo electrico|\bcabezales?\b'),
    ('Baumanómetros', r'\bbaumanometro|\btensiometro|\bpresion arterial|\bmonitor de presion|\bblood pressure|\besfigmomanometro'),
    ('Oxímetros', r'\boximetro|\bsaturacion de oxigeno|\bpulsioximetro|\bspo2\b'),
    ('Termómetros', r'\btermometro'),
    ('Glucómetros', r'\bglucometro|\bglucosa\b|\btiras reactivas|\blancetas|\bmedidor de azucar'),
    ('Nebulizadores', r'\bnebulizador|\binhalador|\bconcentrador de oxigeno|\bcpap\b|\bmascarilla de oxigeno'),
    ('Sillas de ruedas', r'\bsilla de ruedas|\bsillas de ruedas|\bwheelchair\b|\bscooter de movilidad|\bscooter electrico para (adultos mayores|discapacitad)'),
    ('Andaderas, bastones y muletas', r'\bandadera|\bbaston|\bmuleta|\bcaminador(a)?\b|\brollator|\bandador\b'),
    ('Básculas', r'\bbascula|\bpesa (corporal|digital|de bano)'),
    ('Otros aparatos médicos', r'\bestetoscopio|\bmonitor\b|\bdoppler|\belectrocardiograma|\becg\b|\botoscopio|\bmedidor\b'),
    ('Movilidad y apoyo', r'\bsilla (de bano|para ducha|comodo)|\bbarra de (apoyo|seguridad)|\belevador de (asiento|inodoro)|\bcama (de hospital|clinica)|'
                          r'\bcojin (antiescaras|ortopedico)|\bantiescaras|\bgrua\b|\bfaja\b|\brodillera|\bferula|\bcollarin|\bsoporte lumbar'),
    ('Cuidado dental', r'\bdental\b|\bdientes\b|\bblanqueador|\bortodonc|\bhilo dental|\bpasta dental|\benjuague|\bprotesis|\bbucal'),
])


def sub_salud(tn, sub_vieja=None):
    s = _primera(tn, _SAL, {})
    if s:
        return s
    return {'Cuidado dental': 'Cuidado dental', 'Movilidad': 'Movilidad y apoyo', 'Equipo de monitoreo médico': 'Otros aparatos médicos',
            'Básculas': 'Básculas'}.get(sub_vieja, 'Salud')


# --------------------------------------------------------------------- Redes
REDES = ['Routers', 'Sistemas mesh', 'Repetidores', 'Access points',
         'Switches PoE', 'Switches administrables', 'Switches no administrables',
         'Módems', 'Cables y adaptadores de red']
_RED = _c([
    ('Cables y adaptadores de red', r'^(?!switch)(?:\S+ ){0,3}(cables?|patch cord|conectores?|jacks?|keystone|ponchadora|pinzas?|probador|'
                                    r'tester|bobina|rj-?45|coples?|acopladores?)\b|\bcable (de red|ethernet|utp|cat ?\d)|\bpatch panel'),
    ('Sistemas mesh', r'\bsistema (wi-?fi )?(mesh|de malla)|\bmesh (wi-?fi|system)\b|\bdeco\b|\beero\b|\borbi\b|\bvelop\b|\bnest wifi\b|'
                      r'\bsistema wi-?fi para todo el hogar|\b\d nodos\b|\bmesh\b.{0,40}\b(paquete|pack) de \d'),
    ('Repetidores', r'\brepetidor|\bextensor|\bamplificador (de senal|wifi|wi-fi)|\bextender\b|\brange extender'),
    ('Cables y adaptadores de red', r'\badaptador (wifi|wi-fi|inalambrico|usb wifi|bluetooth|de red usb)|\btarjeta (de red|wifi|wi-fi)|'
                                      r'\bdongle\b|\bantena wifi usb|\badaptador pcie|\bnic\b'),
    ('Módems', r'\bmodem|\bmodems|\bdocsis|\bont\b|\bcable modem|\b4g lte\b.{0,20}router|\bmifi\b|\bhotspot\b|\brouter (4g|5g|lte|con sim)'),
    ('Access points', r'^(?!.*\bswitch\b).*(\baccess point|\bpunto de acceso|\bunifi\b|\beap\d|\bomada\b|\bexterior\b.{0,20}\bwifi|\bcpe\b|\bpunto a punto|\bantena sectorial)'),
    ('Switches PoE', r'\bpoe\b|\bpoe\+'),
    ('Switches no administrables', r'\bno administrable|\bno gestionado|\bunmanaged'),
    ('Switches administrables', r'\badministrable|\bgestionado|\bmanaged\b|\bcapa (2|3)\b|\blayer (2|3)\b|\bsmart switch|\bl2\+?\b|\bvlan'),
    ('Switches no administrables', r'\bswitch\b|\bconmutador|\bhub de red|\bdesktop switch|\bno administrable|\bplug and play'),
    ('Routers', r'\brouter|\benrutador|\bwifi (6|7)\b|\bdoble banda\b|\btri-?banda\b|\bgaming router'),
])


def sub_red(tn, sub_vieja=None):
    s = _primera(tn, _RED, {})
    if s:
        return s
    return {'Switches': 'Switches no administrables', 'Routers': 'Routers', 'Repetidores': 'Repetidores',
            'Access points': 'Access points', 'Módems': 'Módems',
            'Cables y adaptadores de red': 'Cables y adaptadores de red'}.get(sub_vieja, 'Routers')


# ------------------------------------------------- Decoración de hogar y jardín
DECORACION = ['Espejos de baño con luz', 'Espejos de cuerpo completo', 'Espejos de tocador y maquillaje',
              'Espejos decorativos de pared', 'Asadores']
_DEC = _c([
    ('Asadores', r'\basador|\bparrilla|\bgrill\b|\bbbq\b|\bcarbon\b'),
    ('Espejos de baño con luz', r'\bban[o]\b.{0,40}\b(led|luz|ilumin|retroilumin)|\b(led|luz|ilumin|retroilumin).{0,40}\bbano\b'),
    ('Espejos de tocador y maquillaje', r'\btocador|\bmaquillaje|\bcosmetico|\bde aumento|\baumento \dx|\b\dx\b|\bde mesa\b|\bvanity\b|\bhollywood\b'),
    ('Espejos de cuerpo completo', r'\bcuerpo (completo|entero)|\bde pie\b|\bde piso\b|\bvestidor|\bfull length|\bde puerta\b|\bpara puerta|'
                                   r'\bx ?1[4-9]\d\b|\b1[4-9]\d ?x|\bcheval|\balto\b'),
    ('Espejos de baño con luz', r'\bled\b|\bluz\b|\biluminado|\bantiempan|\bdesempan|\bbano\b|\bbaño\b|\btactil\b|\binteligente'),
    ('Espejos decorativos de pared', r'\bespejo|\bespejos'),
])


def sub_decoracion(tn, sub_vieja=None):
    return _primera(tn, _DEC, {}) or ('Asadores' if sub_vieja == 'Asadores' else 'Espejos decorativos de pared')


# -------------------------------------------------------------- Impresión 3D
IMPRESION_3D = ['Impresoras FDM', 'Impresoras de resina', 'Escáneres 3D',
                'Filamentos', 'Resinas', 'Boquillas y hotends', 'Camas y superficies', 'Refacciones y accesorios']
_I3D = _c([
    ('Escáneres 3D', r'\bescaner|\bscanner|\bescaneo 3d'),
    ('Resinas', r'^(?:\S+ ){0,4}resinas?\b|\bresina (uv|lavable|estandar|abs|de \d|para impresora|fotopolimer)|\bfotopolimero'),
    ('Filamentos', r'\bfilamento|\bfilament\b(?!.{0,20}(winder|dryer|secador|rewinder))|\bpla\+?\b.{0,20}\b(1[.,]75|2[.,]85|kg)\b|\bpetg\b|\btpu\b.{0,10}\b1[.,]75'),
    ('Boquillas y hotends', r'\bboquilla|\bnozzle|\bhot ?end|\bhotend|\bextrusor|\bextruder|\bbloque calefactor|\bheater block|\bgarganta|\bheatbreak'),
    ('Camas y superficies', r'\bheat ?bed|\bheated bed|\bbuild plate|\bcama\b|\bplaca (de construccion|pei|magnetica|flexible)|\bsuperficie de impresion|\bbuild plate|\bpei\b|\bhoja de acero'),
    ('Impresoras de resina', r'\bresina\b|\bmsla\b|\bsla\b|\blcd\b.{0,20}\b(impresora|printer)|\bphoton\b|\bmars\b|\bsaturn\b|\bmono\b'),
    ('Refacciones y accesorios', r'^(?:\S+ ){0,3}(kit|repuesto|refaccion|motor|ventilador|correa|banda|sensor|termistor|cable|'
                                 r'placa|tarjeta|pantalla|rodamiento|tornillo|husillo|resorte|tubo|secador|caja|cubierta|recinto|soporte|'
                                 r'herramienta|espatula|lubricante|pegamento|adhesivo)\b|\bcompatible con\b|\bpara (bambu|creality|ender|prusa|anycubic|elegoo)'),
    ('Refacciones y accesorios', r'\baccessor|\breplacement|\bparts?\b|\bfeeder|\bspool|\bwinder|\bthermostat|\bheater|\bservices?\b|'
                                 r'\bupgrade|\bkit\b|\bdryer|\bsecador|\benclosure'),
    ('Impresoras FDM', r'\bimpresora 3d|\b3d printer|\bimpresora de 3d|\bimpresoras 3d|\bfdm\b|\bcorexy\b'),
])


def sub_3d(tn, sub_vieja=None):
    s = _primera(tn, _I3D, {})
    if s:
        return s
    return {'Impresoras': 'Impresoras FDM', 'Filamentos': 'Filamentos', 'Escáneres 3D': 'Escáneres 3D'}.get(
        sub_vieja, 'Refacciones y accesorios')


# ------------------------------------------------------ Movilidad eléctrica
MOVILIDAD = ['Scooters para adultos', 'Scooters para niños', 'Bicicletas eléctricas plegables y urbanas',
             'Bicicletas eléctricas de montaña', 'Hoverboards, patinetas y monociclos', 'Accesorios']
_MOV = _c([
    ('Accesorios', r'\breplacement|\bparts?\b|\binstrument display|\bcontroller\b|\bguante|^(?:\S+ ){0,4}(caja|cargador|baterias?|llantas?|neumaticos?|camaras?|frenos?|asiento|sillin|guardabarros|luces?|faro|'
                   r'candado|soporte|funda|bolsa|casco|repuesto|refaccion|kit|motor|controlador|display|acelerador|amortiguador|'
                   r'espejo|timbre|mangos?|pu[nñ]os?|parrilla)\b'),
    ('Hoverboards, patinetas y monociclos', r'\bskateboard|\bhoverboard|\bpatineta (electrica|autoequilibr)|\bmonociclo|\bautoequilibr|\bself.?balanc|\bsegway\b.{0,20}(ninebot s|mini)|\bonewheel'),
    ('Scooters para niños', r'\bninos?\b|\bnina\b|\bkids?\b|\binfantil|\bjunior\b|\bpara (chicos|adolescentes)'),
    ('Bicicletas eléctricas de montaña', r'(bici(cleta)?|e-?bike).{0,40}\b(montana|mtb|todo terreno|fat ?tire|llantas? (gruesas|anchas)|off.?road)|'
                                         r'\b(montana|mtb|fat ?tire)\b.{0,40}(bici|e-?bike)'),
    ('Bicicletas eléctricas plegables y urbanas', r'\bbici(cleta)?s?\b|\be-?bike|\bpedaleo asistido|\bpedelec'),
    ('Scooters para adultos', r'\bscooter|\bpatinete|\bpatin electrico|\bmonopatin|\bninebot\b|\bxiaomi\b.{0,20}\bscooter'),
])


def sub_movilidad(tn, sub_vieja=None):
    s = _primera(tn, _MOV, {})
    if s:
        return s
    return {'Patinetes eléctricos': 'Scooters para adultos', 'Bicicletas eléctricas': 'Bicicletas eléctricas plegables y urbanas',
            'Accesorios': 'Accesorios'}.get(sub_vieja, 'Scooters para adultos')


# ------------------------------------------------------------------ Celulares
# Android no se divide por marca (pedido del usuario): sólo se aparta lo que
# es otro aparato aunque sea Android -- el plegable --. El resto de Celulares
# ya estaba cortado por tipo y sólo gana familias.
def sub_celular3(tn, sub_vieja=None):
    if sub_vieja in ('Android', None) and re.search(r'\bplegable|\bfold\b|\bflip\b|\bz ?fold|\bz ?flip|\brazr\b|\bfind n\d', tn) \
            and not re.search(r'\bfunda|\bcase\b|\bprotector|\bmica\b', tn):
        return 'Plegables'
    return sub_vieja


# -------------------------------------------------------------------- Drones
DRONES = ['Mini drones', 'Para principiantes', 'Con cámara 4K', 'FPV', 'Accesorios']
_DRO = _c([
    ('Accesorios', r'^(?:\S+ ){0,4}(baterias?|helices|cargador|estuche|funda|mochila|protector|filtros?|control|repuesto|'
                   r'tren de aterrizaje|kit|soporte|antena|gafas de repuesto|cable)\b'),
    ('FPV', r'\bfpv\b|\bcarreras\b|\bracing\b|\bavata\b|\bgafas\b'),
    ('Con cámara 4K', r'\b4k\b|\b6k\b|\b8k\b|\bmavic\b|\bair 3\b|\bair 2s\b|\bmini 4 pro\b|\bhasselblad\b|\bgimbal de 3 ejes'),
    ('Mini drones', r'\bmini\b|\bnano\b|\bde bolsillo|\bpequen|\bplegable\b.{0,20}\bmini'),
    ('Para principiantes', r'\bninos?\b|\bprincipiantes?\b|\bjuguete|\bkids?\b|\bpara nino'),
])


def sub_dron(tn, sub_vieja=None):
    s = _primera(tn, _DRO, {})
    if s:
        return s
    if sub_vieja == 'Con GPS':
        return 'Con cámara 4K'
    return sub_vieja if sub_vieja in DRONES else 'Para principiantes'


TRES_NIVELES = [
    ('Baterías portátiles', None, BATERIAS, sub_bateria, None),
    ('Almacenamiento', None, ALMACENAMIENTO, sub_almacenamiento, None),
    ('Mouse', None, MOUSE, sub_mouse3, None),
    ('Relojes inteligentes', None, RELOJES_INT, sub_reloj_int, None),
    ('Aspiradoras', None, ASPIRADORAS, sub_aspiradora3, None),
    ('Televisores', None, TELEVISORES, sub_tv3, None),
    ('Refrigeradores', None, REFRIGERADORES, sub_refri3, None),
    ('Computadoras de escritorio', None, ESCRITORIO, sub_escritorio3, None),
    ('Viajes', None, VIAJES, sub_viaje, None),
    ('Salud', None, SALUD, sub_salud, None),
    ('Redes', None, REDES, sub_red, None),
    ('Decoración de hogar y jardín', None, DECORACION, sub_decoracion, None),
    ('Impresión 3D', None, IMPRESION_3D, sub_3d, None),
    ('Movilidad eléctrica', None, MOVILIDAD, sub_movilidad, None),
    ('Celulares', ['Android'], ['Android', 'Plegables'], sub_celular3, None),
    ('Drones', None, DRONES, sub_dron, None),
]

# El escalón del medio de cada una (familias_subcategorias.py lo suma a su
# tabla). Sólo se nombran subcategorías de rol «producto»: los accesorios ya
# tienen su propio grupo.
FAMILIAS_TRES_NIVELES = {
    "Baterías portátiles": [
        ("Por capacidad", ["Hasta 10,000 mAh", "10,000 a 20,000 mAh", "Más de 20,000 mAh"]),
        ("Por tipo", ["Magnéticas (MagSafe y Qi2)", "Inalámbricas", "Con cable integrado o enchufe", "Solares",
                      "Para reloj, consola y otros aparatos"]),
        ("Alta potencia", ["Para laptop (60 W o más)", "Estaciones de energía"]),
    ],
    "Almacenamiento": [
        ("SSD", ["SSD NVMe M.2", "SSD SATA", "SSD externos"]),
        ("Discos duros", ["Discos duros internos", "Discos duros externos"]),
        ("Memorias y tarjetas", ["Memorias USB", "Memorias USB por mayoreo", "Tarjetas microSD", "Tarjetas SD y otras"]),
        ("Red y conexión", ["NAS", "Gabinetes y docks para disco"]),
    ],
    "Mouse": [
        ("Para casa y oficina", ["Inalámbricos", "Con cable"]),
        ("Gaming", ["Gaming inalámbricos", "Gaming con cable"]),
        ("Ergonómicos", ["Verticales y ergonómicos", "Trackballs"]),
    ],
    "Relojes inteligentes": [
        ("Smartwatches", ["Smartwatches", "Smartwatches con llamadas", "Smartwatches deportivos y con GPS",
                          "Smartwatches para niños"]),
        ("Pulseras y anillos", ["Bandas de actividad", "Anillos inteligentes"]),
    ],
    "Aspiradoras": [
        ("Para la casa", ["Verticales y de escoba", "De mano", "Robots aspiradores", "De trineo y con bolsa"]),
        ("Uso rudo y lavado", ["Seco y húmedo", "Industriales y comerciales", "Lavadoras de alfombras y vapor"]),
    ],
    "Televisores": [
        ("Por tamaño", ["Hasta 32 pulgadas", "40 a 43 pulgadas", "50 a 55 pulgadas", "58 a 65 pulgadas",
                        "70 pulgadas o más"]),
        ("Otros formatos", ["Portátiles y para auto", "Dispositivos de streaming"]),
    ],
    "Refrigeradores": [
        ("Para la casa", ["Top mount", "Bottom freezer", "Dúplex (side by side)", "French door", "Una puerta"]),
        ("Compactos y especiales", ["Frigobares", "Congeladores", "Cavas de vino"]),
        ("Uso comercial", ["Refrigeradores comerciales", "Vitrinas y enfriadores comerciales"]),
    ],
    "Computadoras de escritorio": [
        ("Torres", ["PC gamer", "Torres de casa y oficina", "Reacondicionadas"]),
        ("Compactas", ["All in One", "Mini PC"]),
    ],
    "Viajes": [
        ("Maletas", ["Maletas de cabina", "Maletas medianas", "Maletas grandes", "Sets de maletas"]),
        ("Bolsas y accesorios", ["Mochilas y bolsas de viaje", "Accesorios de viaje"]),
        ("Aire libre", ["Camping", "Pesca"]),
    ],
    "Salud": [
        ("Cuidado dental", ["Cepillos de dientes eléctricos", "Irrigadores bucales", "Cuidado dental"]),
        ("Monitoreo en casa", ["Baumanómetros", "Oxímetros", "Termómetros", "Glucómetros", "Nebulizadores",
                               "Monitoreo y diagnóstico", "Básculas"]),
        ("Movilidad", ["Sillas de ruedas", "Andaderas, bastones y muletas", "Movilidad y apoyo"]),
    ],
    "Redes": [
        ("Wi-Fi y módems", ["Routers", "Sistemas mesh", "Repetidores", "Access points", "Módems"]),
        ("Switches", ["Switches PoE", "Switches administrables", "Switches no administrables"]),
    ],
    "Decoración de hogar y jardín": [
        ("Espejos", ["Espejos de baño con luz", "Espejos de cuerpo completo", "Espejos de tocador y maquillaje",
                     "Espejos decorativos de pared"]),
    ],
    "Impresión 3D": [
        ("Impresoras y escáneres", ["Impresoras FDM", "Impresoras de resina", "Escáneres 3D"]),
        ("Materiales", ["Filamentos", "Resinas"]),
    ],
    "Movilidad eléctrica": [
        ("Scooters", ["Scooters para adultos", "Scooters para niños"]),
        ("Bicicletas eléctricas", ["Bicicletas eléctricas plegables y urbanas", "Bicicletas eléctricas de montaña"]),
    ],
    "Celulares": [
        ("Smartphones", ["Android", "iPhone", "Plegables", "Resistentes", "Reacondicionados"]),
        ("Teléfonos sencillos", ["Básicos", "Teléfonos fijos"]),
    ],
    "Drones": [
        ("Con cámara", ["Con cámara 4K", "FPV"]),
        ("Para empezar", ["Mini drones", "Para principiantes"]),
    ],
}

# Rol de las subcategorías nuevas que no son el producto (roles_subcategorias.py).
ROLES_TRES_NIVELES = {
    "Relojes inteligentes": {"Correas y extensibles": "accesorio", "Fundas, cargadores y protectores": "accesorio"},
    "Impresión 3D": {"Filamentos": "consumible", "Resinas": "consumible", "Boquillas y hotends": "parte",
                     "Camas y superficies": "parte", "Refacciones y accesorios": "parte"},
    "Redes": {"Cables y adaptadores de red": "accesorio"},
    "Televisores": {"Accesorios y soportes": "accesorio"},
    "Almacenamiento": {},
}
