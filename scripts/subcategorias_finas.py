#!/usr/bin/env python3
"""Subcategorías finas para tres categorías que se compran por algo más
específico que lo que decía la lista vieja:

  - Suplementos: por nutriente o propósito (Creatina, Magnesio, Vitamina D...),
    no por "Vitaminas y minerales" a secas.
  - Cocina y comedor: por uso y tipo de pieza (Termos, Tazas, Cuchillos y
    tablas, Ollas de presión, Repostería...), no por "Botellas y termos".
  - Libros: por género (Thriller y misterio, Historia, Autoayuda...), no
    por "Literatura y novela" / "No ficción".

Cada repartidor recibe el texto ya normalizado (minúsculas, sin acentos: lo
que el clasificador llama `tn`) y devuelve la subcategoría o None. El orden
de las ramas es el que manda: un "Vitamina D3 + K2" es Vitamina D, y una
"Proteína con colágeno" es Proteínas, porque se compra por lo primero que
nombra el título.

Los importa clasificar_captura_perifericos.py (para las capturas nuevas) y
afinar_subcategorias.py (para reasignar lo que ya está en el catálogo).
"""
import re

# ---------------------------------------------------------------- Suplementos
SUPLEMENTOS = [
    'Proteínas', 'Creatina', 'Aminoácidos y pre-entreno', 'Colágeno',
    'Probióticos y prebióticos', 'Enzimas, fibra y digestivos',
    'Omega 3 y aceites', 'Multivitamínicos', 'Vitamina C', 'Vitamina D y K',
    'Complejo B y biotina', 'Otras vitaminas', 'Magnesio', 'Zinc', 'Calcio',
    'Hierro', 'Electrolitos y minerales', 'Melatonina y sueño', 'Antioxidantes',
    'Articulaciones', 'Salud ocular', 'Cabello, piel y uñas',
    'Sistema inmune', 'Memoria y concentración', 'Salud hormonal y sexual',
    'Salud cardiovascular', 'Control de glucosa', 'Hígado, riñón y vías urinarias',
    'Control de peso', 'Herbolaria y superalimentos', 'Energía y vitalidad',
]

_S = [
    ('Proteínas', r'\bproteina|\bwhey\b|\bcaseina\b|\bprotein\b|\bisolate\b|proteico'),
    ('Creatina', r'\bcreatin'),
    ('Aminoácidos y pre-entreno', r'\bpre ?entreno\b|\bpre-?workout\b|\bbcaa|\baminoacid|\bglutamina\b|'
                                  r'\bl-?carnitina\b|\bcarnitina\b|\boxido nitrico\b|\bcitrulina\b|\barginina\b|'
                                  r'\bbeta ?alanina\b|ganador de peso|\bmass gainer\b|\bgainer\b|\bhmb\b|\btaurina\b|'
                                  r'\bpost ?entreno\b|\bleucina\b|\beaa\b'),
    ('Colágeno', r'\bcolageno|\bcollagen|\bgrenetina'),
    ('Probióticos y prebióticos', r'\bprobiotic|\bprebiotic|\bmicrobiota\b|lactobacil|\bbifidobacter|\binulina\b|'
                                  r'\bsaccharomyces\b|\bflora intestinal\b|\bflora femenina\b|\bxos\b|\bfos\b'),
    ('Enzimas, fibra y digestivos', r'\benzima|\bdigestiv|\bfibra\b|\bpsyllium\b|\bpsilio\b|\bpapaina\b|\bbromelina\b|'
                                    r'\blaxante|\bestrenimiento\b|\breflujo\b|\bacidez\b|\bgases\b|\bcarbon activado\b|'
                                    r'\bglp-?1\b|\bsen\b|\bsabila\b|\baloe vera\b'),
    ('Omega 3 y aceites', r'\bomega|aceite de (pescado|krill|linaza|coco|onagra|higado|oliva|chia|borraja|semilla)|'
                          r'\bmct\b|\bepa\b|\bdha\b|\bfish oil\b|\bkrill\b'),
    ('Melatonina y sueño', r'\bmelatonina\b|\bsueno\b|\bdormir\b|\binsomnio\b|\bvaleriana\b|\bpasiflora\b|'
                           r'\bsleep\b|\brelajante\b|\bl-?teanina\b|\bgaba\b|\bmagnolia\b'),
    ('Salud ocular', r'\bluteina\b|\bzeaxantina\b|\bocular\b|\bvision\b|\bojos\b|\bvista\b|\barandano\b.{0,20}\bojos\b'),
    ('Articulaciones', r'\bglucosamina\b|\bcondroitina\b|\bmsm\b|\barticula|\bcartilago\b|\brodilla|\bhuesos y articulaciones\b|'
                       r'\bmovilidad articular\b|\bacido hialuronico\b.{0,30}articul'),
    ('Cabello, piel y uñas', r'\bcabello\b|\bpelo\b|\bpiel\b|\bunas\b|\bkeratina\b|\bqueratina\b|\bcaida del cabello\b|'
                             r'\bcrecimiento del cabello\b|\bskin\b|\bhair\b|\bnails\b|\bantiedad\b|\bantienvejecimiento\b'),
    ('Sistema inmune', r'\binmun|\blactoferrina\b|\binmunoglobulina\b|\bigg\b|\bimmune\b|\bequinacea\b|\bpropoleo\b|\bpropolis\b|\bdefensas\b|\bsauco\b|\belderberry\b|\bgripe\b'),
    ('Memoria y concentración', r'\bmemoria\b|\bconcentracion\b|\bnootrop|\bcognitiv|\bcerebr|\bbacopa\b|\bmente\b|\bfocus\b|'
                                r'\bginkgo\b|\bfosfatidilserina\b|\blion.?s mane\b|\bmelena de leon\b'),
    ('Salud hormonal y sexual', r'\bmenopausia\b|\bprostata\b|\btestosterona\b|\blibido\b|\bfertilidad\b|\bhormonal\b|'
                                r'\bciclo menstrual\b|\bmaca\b|\btribulus\b|\bsaw palmetto\b|\bpalma enana\b|\bvigor masculino\b|'
                                r'\bsalud masculina\b|\bsalud femenina\b|\bmenstrua|\bsop\b|\bdhea\b|\binositol\b|\bbeta ?sitosterol\b|\bpara (la )?mujer\b|\bpara (el )?hombre\b|\bfor men\b|\bfor women\b'),
    ('Control de peso', r'control de peso|quema ?grasa|\badelgaz|\bsaciante\b|\bdetox\b|reduce medidas|\bperdida de peso\b|'
                        r'\bbajar de peso\b|\btermogenic|\bfat burner\b|\bcla\b|\bgarcinia\b|\bcetona|\bketo\b|\bapetito\b|'
                        r'\bmetabolismo\b|\bslim\b'),
    ('Multivitamínicos', r'\bmultivitamin|\bmulti ?vitamin|\bvitaminas y minerales\b|\bcentrum\b|\bone a day\b|\bmulti\b.{0,10}\bvitamin|'
                         r'\bvitaminas (a|para) (mujer|hombre|ninos|adultos)|\bcomplejo (multi|vitaminico)\b'),
    ('Vitamina C', r'\bvitamina c\b|\bacido ascorbico\b|\bascorbato\b|\bvit\.? ?c\b'),
    ('Vitamina D y K', r'\bvitamina d\b|\bvitamina d3\b|\bd3\b|\bcolecalciferol\b|\bvitamina k\b|\bk2\b|\bmk-?7\b'),
    ('Complejo B y biotina', r'\bvitamina b\b|\bvitamina b\d+\b|\bcomplejo b\b|\bb12\b|\bb-?complex\b|\bbiotina\b|\bacido folico\b|'
                             r'\bfolato\b|\bmetilfolato\b|\bniacina|\bniacinamida\b|\btiamina\b|\briboflavina\b|\bcobalamina\b|\bpiridoxina\b'),
    ('Otras vitaminas', r'\bvitamina [aek]\b|\bvitamina e\b|\btocoferol\b|\bretinol\b|\bbetacaroteno\b|\bvitamina\b'),
    ('Magnesio', r'\bmagnesio\b|\bmagnesium\b|\bcitrato de mg\b|\bmg\b.{0,10}(glicinato|citrato|treonato)'),
    ('Zinc', r'\bzinc\b|\bpicolinato\b'),
    ('Calcio', r'\bcalcio\b|\bcalcium\b|\bsalud osea\b|\bhuesos\b'),
    ('Hierro', r'\bhierro\b|\biron\b|\bferroso\b|\bferritina\b|\banemia\b'),
    ('Electrolitos y minerales', r'\bpotasio\b|\bselenio\b|\byodo\b|\bcromo\b|\bmanganeso\b|\bcobre\b|\bboro\b|\bmolibdeno\b|\bsilicio\b|'
                        r'\bmineral|\belectrolit|\bsales minerales\b|\bhidratacion\b|\bmultimineral\b'),
    ('Antioxidantes', r'\bantioxidant|\bresveratrol\b|\bcoenzima q10\b|\bcoq10\b|\bubiquinol\b|\bglutation\b|\bastaxantina\b|'
                      r'\bnac\b|\bn-?acetil ?cisteina\b|\bacido alfa lipoico\b|\bquercetina\b|\bnmn\b|\bnad\+?\b|\blicopeno\b|'
                      r'\bpolifenol|\bte verde\b|\bcurcumin|\bpterostilbeno\b|\bespermidina\b|\bnicotinamida\b|\blongevidad\b|\benvejecimiento\b|\bpycnogenol\b|\bluteolina\b|\bflavonoid|\bflavanol'),
    ('Energía y vitalidad', r'\benergia\b|\bvitalidad\b|\bfatiga\b|\bcansancio\b|\bcafeina\b|\bguarana\b|\brendimiento\b|\bginseng\b|\brhodiola\b'),
    ('Salud cardiovascular', r'\bcardio|\bcorazon\b|\bcolesterol\b|\bpresion arterial\b|\bcirculaci|\btrigliceridos\b|\bpolicosanol\b|\bomega\b.{0,10}corazon'),
    ('Control de glucosa', r'\bglucosa\b|\bazucar en (la )?sangre\b|\bdiabet|\bberberina\b|\bvanadilo\b|\bcromo\b.{0,20}(glucosa|azucar)|\bgymnema\b|\binsulina\b'),
    ('Hígado, riñón y vías urinarias', r'\bhigado\b|\bhepatic|\brinon|\brenal\b|\burinari|\bvejiga\b|\bd-?manosa\b|\bcardo mariano\b|\bsilimarina\b|\bdrenaje linfatico\b|\bdesintoxica|\bdetox hepatico\b'),
    ('Herbolaria y superalimentos', r'\bfrutas y verduras\b|\bsuperalimento|\bsuper ?food|\bgreens\b|\bverdes en polvo\b|\bcalostro\b|\bmedula osea\b|\borganos?\b|\b(higado|rinon|corazon) de res\b|\badaptogen|\bvinagre de manzana\b|\bapple cider\b|\bcurcuma\b|\bashwagandha\b|\bespirulina\b|\bchlorella\b|\balcachofa\b|\btoronjil\b|\bmoringa\b|'
                   r'\bherbol|\bextracto de (planta|hierba|raiz|hoja|semilla|flor)|\bhongos?\b|\breishi\b|\bcordyceps\b|\bchaga\b|'
                   r'\bjengibre\b|\bajo\b|\bcanela\b|\bdiente de leon\b|\bcardo mariano\b|\bhierba|\bplanta|\bnopal\b|\bchia\b|'
                   r'\barandano\b|\bcranberry\b|\bboldo\b|\bmanzanilla\b|\bte de\b|\bmilenrama\b|\bortiga\b|\bneem\b|\bnoni\b|'
                   r'\bsemilla de calabaza\b|\bavena\b|\bcapsulas? de (planta|hierba)|\bnatural(es)?\b'),
]
_S = [(sub, re.compile(rx)) for sub, rx in _S]


# Lo primero que nombra el título es lo que se compra: "Multivitamínico
# mujer con colágeno" es multivitamínico. Se elige la rama cuyo disparador
# aparece antes; las ramas genéricas ("vitamina", "natural", "mineral")
# cargan una penalización para no ganarle a un nutriente concreto que salga
# unas palabras después.
def _primera(tn, ramas, penal):
    mejor = None
    for sub, rx in ramas:
        m = rx.search(tn)
        if not m:
            continue
        pos = m.start() + penal.get(sub, 0)
        if mejor is None or pos < mejor[0]:
            mejor = (pos, sub)
    return mejor[1] if mejor else None


_S_PENAL = {'Otras vitaminas': 40, 'Herbolaria y superalimentos': 40,
            'Electrolitos y minerales': 25, 'Energía y vitalidad': 25,
            'Cabello, piel y uñas': 15, 'Salud y bienestar': 20,
            'Antioxidantes': 10}


def sub_suplemento_fino(tn):
    sub = _primera(tn, _S, _S_PENAL)
    if sub:
        return sub
    # Última red (21-sep): el probiótico se nombra por su marca y su cuenta
    # de UFC ("60 billones", "18 mil millones de CFU").
    if re.search(r'\bprobi[oó]?tic|\bbio-?k\b|afterbiotics|\btruflora\b|probioslim|'
                 r'\d+ (billones|mil millones)|\bcepas\b|\bcfu\b|\bufc\b', tn):
        return 'Probióticos y prebióticos'
    if re.search(r'urolit(h)?ina?|\bd-?limoneno\b|\bcacao\b|remolacha|superbeets|'
                 r'extracto de cascara', tn):
        return 'Antioxidantes'
    if re.search(r'\bdiosmina\b|salud vascular|microcirculacion|endocalyx|glicocaliz', tn):
        return 'Salud y bienestar'
    if re.search(r'\bprostat|\bfenogreco\b|salud hormonal', tn): return 'Salud hormonal y sexual'
    return None


# ------------------------------------------------------------ Cocina y comedor
COCINA = [
    'Termos y botellas térmicas', 'Botellas de agua', 'Vasos térmicos y de viaje',
    'Tazas', 'Vasos y copas', 'Jarras y dispensadores de bebidas',
    'Tarros y frascos', 'Botellas de vidrio y plástico',
    'Contenedores herméticos', 'Loncheras y termos para alimentos',
    'Platos y bowls', 'Vajillas', 'Cubiertos', 'Cuchillos y tablas',
    'Utensilios de cocina', 'Ollas de presión', 'Ollas y cacerolas',
    'Sartenes y comales', 'Baterías de cocina', 'Repostería y moldes',
    'Básculas y medidores', 'Bar y coctelería', 'Desechables',
    'Organización de cocina', 'Limpieza de cocina',
]

_C = [
    # Lo que se descarta por nombre antes de mirar el resto: el accesorio
    # de organización o limpieza se nombra por lo que organiza ("porta
    # botellas", "cepillo para botellas") y se llevaría la botella.
    ('Limpieza de cocina', r'\bcepillos? (de|para) (limpieza|botella|biberon|vaso|taza|platos|cocina)|\bcepillos? de cocina\b|\bsoporte para esponja|limpia ?botellas|\besponja|'
                           r'\bestropajo|\bfibra (de|para) (cocina|trastes)|\blavatrastes\b|\bpano de cocina\b|\btrapos? de cocina\b|'
                           r'\bescobilla|\bjabon (para|de) trastes\b|\bcubo de basura\b|\bbote de basura\b|\bbasurero\b'),
    ('Organización de cocina', r'\borganizador|\bestante|\brack\b|\brepisa|\bespeciero|\bporta ?(vasos|botellas|tazas|cubiertos|rollo|utensilios|platos|tapas|cuchillos)|'
                               r'\bbotellero|\bescurridor|\bescurreplatos|\bsoporte (para|de) (botellas|vasos|tazas|platos|cuchillos|tapas|tablas|ollas|sartenes)|'
                               r'\bcajonera|\bcesta (para|de) (cocina|fruta|pan)|\bfrutero|\bpanera\b|\bcarrito (de|para) (cocina|verduras)|'
                               r'\bdispensador (de|para) (cereal|granos|jabon)|\bganchos? (para|de) (cocina|tazas)|\bcolgador|\bbandeja (giratoria|organizadora)|'
                               r'\blazy susan\b|\bseparador de cajon|\bdivisor(es)? de cajon|\btapete (para|de) (escurrir|secado)|\balmacenamiento de cocina\b|'
                               r'\borganizadores? (de|para) (refrigerador|alacena|despensa|cocina)|\bcaja de almacenamiento\b|'
                               r'\bportarrollos?\b|\bclips? (para|de) bolsa|\brevestimientos? antideslizantes?|\bforro (de|para) (gabinete|cajon|repisa)|'
                               r'\bcaballete de mesa\b|\bbolsa (de|para) plancha\b|\bfunda (de|para) plancha\b|\bcubierta (para|de) microondas'),
    # Bar
    ('Bar y coctelería', r'\bcoctelera|\bshaker\b|\bcocteler|\bsacacorchos|\bdescorchador|\bdestapador|\babridor(es)? de (botellas|cerveza|vino)|'
                         r'\bcubos? de hielo\b|\bhielera|\bcubitera|\bmolde para hielo\b|\bbomba de vacio para vino\b|\btapon(es)? (de|para) vino|'
                         r'\bvertedor(es)?\b|\bdecantador|\baireador de vino\b|\bjigger\b|\bmedidor de (licor|cocteles)|\bmezclador de (bebidas|cocteles)|'
                         r'\bbarra de bar\b|\bkit de (bar|cocteleria|barman)|\bcerveza\b.{0,20}\bkit\b|\bposavasos|\bcopas? de (vino|champa|coctel|martini|whisky|brandy)|'
                         r'\bvasos? (de|para) (whisky|shot|chupito|cerveza|coctel|tequila|mezcal)|\bshots?\b|\bcaballitos? (de|para) tequila|\bjarra cervecera\b|\btarro cervecero\b|'
                         r'\btapa (de|para) vino\b|\bherramientas? de bar\b|\bmixologia\b'),
    # Bebidas para llevar
    ('Loncheras y termos para alimentos', r'\blonchera|\blunch ?box|\bbento\b|\btermo (para|de) (alimentos|comida|sopa)|\bporta ?alimentos|\bportaviandas|'
                                          r'\bfiambrera|\bcontenedor (de|para) (almuerzo|lunch)|\bbolsa (termica|de almuerzo|para lunch)|\btermo alimentos\b|'
                                          r'\btermo de comida\b|\bjarro (para|de) sopa\b|\bfood jar\b|\bcalienta ?comida\b|'
                                          r'\bbentgo\b.{0,25}(compartimentos|lunch|snack|bento)|\bbote (para|de) comida\b'),
    ('Vasos térmicos y de viaje', r'\bbubba\b|\bdual sip\b|\bcold cup\b|\bmagslider\b|\benfriador de lata\b|\bcan cooler\b|'
                                  r'\bvasos? (termic|de viaje|de acero|con popote|con tapa y popote|aislad)|\btumbler|\bvaso (stanley|yeti|owala|hydro flask|contigo|thermos)\b|'
                                  r'\bvaso (de|para) (cafe|viaje)\b|\btravel mug\b|\btaza (termica|de viaje|con tapa)|\bvaso quencher\b|\bquencher\b|'
                                  r'\bvaso (de )?\d+ ?(oz|onzas)\b.{0,40}(tapa|popote|aislad|acero)|\bvasos?\b.{0,50}(popote|pajita|pajilla|aislad|termic)|\bvaso (con|de) asa\b|\bsmoothsip\b|\bflip ?top\b|\bvaso (para|de) (smoothie|licuado|malteada)'),
    ('Termos y botellas térmicas', r'\btermos?\b(?!\s*(electrico|de gas))|\bbotella (termica|de acero|aislada|termo)|\btermica\b.{0,30}botella|^(hydro ?flask|yeti|stanley|thermos)\b.{0,25}(botella|termo|\d+ ?(ml|oz|l)\b)|\bacero inoxidable\b.{0,40}\bbotella|\bbotella\b.{0,40}\bacero inoxidable\b|'
                                   r'\bdoble pared\b|\baislad[ao]s? al vacio\b|\bvacuum\b|\baislamiento\b.{0,30}botella|\bbotella\b.{0,30}aislamiento'),
    ('Botellas de agua', r'\bfreesip\b|\bhydrojug\b|\bsoft flask\b|\bbotellas? (de|para) agua|\bcantimplora|\bbotella (deportiva|plegable|de tritan|de plastico|infantil|para ninos|para gym|con popote|con filtro|motivacional)|'
                         r'\bnalgene\b|\btritan\b|\bbotella\b.{0,30}(\bml\b|\bl\b|litro|onzas|\boz\b).{0,40}(deport|gym|ciclismo|bici|escolar|ninos)|\bbotella\b.{0,20}(gym|deportiva|ciclismo|para bicicleta)|'
                         r'\bbotella (con|de) (marcador|medidor|tiempo)|\bbotella galon\b|\bbotella (de )?1 galon\b|\banfora\b|\bbotella\b.{0,40}(silicona|plegable|colapsable)'),
    ('Vasos y copas', r'\bsin tallo\b|\bstemless\b|\bvasos?\b|\bcopas?\b|\bcaballitos?\b|\bhighball\b|\bcaliz\b|\bvaso (de vidrio|de cristal|de plastico|para beber|apilable)'),
    ('Tazas', r'\bminitazas?\b|\bset de mate\b|\bmate de (acero|calabaza)\b|\btazas?\b|\bmugs?\b|\btaza (de|para) (cafe|te)|\bjarro\b|\bjarritos?\b|\btaza de ceramica\b|\btazon (para|de) (cafe|te)\b|\bpocillo'),
    ('Jarras y dispensadores de bebidas', r'\bairpot\b|\bcanon dispensador\b|\bespigas? de agua\b|\bjarras?\b|\bpitcher\b|\bdispensador (de|para) (bebidas|agua|jugo|limonada|aguas frescas)|\bvitrolero|\bgarrafa|'
                                          r'\bdispensador de agua\b|\bjarra (de|para) (agua|jugo|leche|te|cafe)|\btetera\b|\bcafetera (de|para) (piston|prensa|servir)|\bprensa francesa\b|'
                                          r'\bjarra electrica\b|\bhervidor\b'),
    ('Tarros y frascos', r'\bmatra(z|ces)\b|\berlenmeyer\b|\btarros?\b(?! cervecer)|\bfrascos?\b|\bmason\b|\btapas? (para|de) (tarro|frasco|mason)|\banillos? de sellado\b|\bfrasco (de vidrio|hermetico|con tapa|para conserva)|'
                         r'\bjuego de frascos\b|\bbotes? (de|para) (vidrio|cocina|almacenamiento|especias)\b|\balacena\b.{0,20}frasco|\bfrascos? (para|de) (especias|condimentos|salsa|miel|mermelada)'),
    ('Botellas de vidrio y plástico', r'\bbotellas? (de |para )?(vidrio|plastico|pet\b|jugo|leche|aceite|salsa|condimento|vino|licor|cerveza|kombucha|kefir|agua mineral|almacenamiento|vacias?|con tapa|con tapon|exprimibles?|hermeticas?)|'
                                      r'\bdispensador(es)? (de|para) (aceite|salsa|condimento|vinagre|jabon de cocina|jabon)|\baceitera|\bvinagrera|\brociador de aceite\b|\bbotellas? (de|con) (corcho|rosca)|'
                                      r'\bbotellas? de \d+ ?(ml|oz|onzas)\b'),
    ('Contenedores herméticos', r'\btapas? de silicona\b|\btapas? reutilizables\b|\btapa (para|de) lata\b|\bcaja de aislamiento\b|\balmacenamiento de alimentos\b|\brecipientes? hermetic|\bcontenedor(es)? (hermetic|de alimentos|para alimentos|de comida|para comida|de cocina|para cereal|de vidrio|de plastico|con tapa|apilable)|'
                                r'\btuppers?\b|\btupperware|\btopper(s)?\b|\brecipientes? (de|para) (almacenamiento|alimentos|comida|vidrio|plastico|cocina|cereal|refrigerador|congelador)|'
                                r'\bjuego de recipientes\b|\bcontenedores? (organizador|para refrigerador)|\bcajas? (para|de) (alimentos|comida|pan|galletas|cereal)|\bhermetic|'
                                r'\bbolsas? (de silicona|reutilizables|para congelar|ziploc|con cierre)|\bcontenedor(es)?\b|\brecipientes?\b|\bfiambrera\b|\bcubo de almacenamiento\b|\bbarril (de|para) (arroz|granos)'),
    # Mesa
    ('Vajillas', r'\bvajillas?\b|\bjuego de (vajilla|platos|mesa)|\bset de (vajilla|platos)|\bservicio para \d+ personas\b|\bplatos? y tazones?\b.{0,20}(juego|set|piezas)'),
    ('Desechables', r'\bbolsas? (para|de) (horno|asado)\b|\bdesechabl|\bpajillas?\b|\bagitador(es)?\b|\bbiodegradabl|\bcompostabl|\bhoja de palma\b|\bpopotes?\b|\bpajitas?\b|\bsorbetes?\b|\bde carton\b|\bde papel\b.{0,20}(platos|vasos)|'
                    r'\bvasos? (de papel|de carton|de plastico transparente|desechable)|\bplatos? (de papel|de carton|desechable|de unicel)|\bservilletas?\b|\bmantel(es)? de plastico\b|'
                    r'\bcubiertos? desechable|\bcharolas? de (carton|papel|aluminio)|\bpapel (aluminio|encerado|de hornear|film|antiadherente)\b|\bplastico (adherente|film)\b'),
    ('Cubiertos', r'\bcubiertos?\b|\bcucharas?\b(?! (de madera|de silicona|medidora|para servir|para helado|ranurada|de cocina|espumadera|de nylon))|\btenedor(es)?\b|'
                  r'\bcuchillos? de mesa\b|\bcucharitas?\b|\bcucharillas?\b|\bset de cubiertos\b|\bjuego de cubiertos\b|\bcubertería|\bpalillos? (chinos|para comer|de bambu)\b|\bchopsticks?\b'),
    ('Cuchillos y tablas', r'\bbarra de afilado\b|\btijeras?\b|\bcuchillos?\b|\btablas? (de|para) (cortar|picar|cocina|queso|carne|pan)|\bafilador|\bchaira\b|\bset de cuchillos\b|\bjuego de cuchillos\b|\bcuchillo (de chef|santoku|cebollero|de pan|para verduras)\b|'
                           r'\bmandolina\b|\bhacha de cocina\b|\btabla de picar\b|\bbloque (de|para) cuchillos\b|\btijeras? de cocina\b|\bpelador\b|\bcortador de (verduras|pizza|manzana|frutas|espiral)|\bespiralizador|\brebanador'),
    ('Platos y bowls', r'\bmantequera\b|\bvasitos? (para|de) salsa\b|\b(bolas?|bowls?) de mezcla\b|\bpropagador de mantequilla\b|\bplatos?\b|\btazon(es)?\b|\bbowls?\b|\bensaladera|\bcuencos?\b|\bfuentes? (para|de) (servir|mesa|ensalada)|\bplaton(es)?\b|\bbandejas? (para|de) servir\b|\bcharolas?\b|'
                       r'\bplatitos?\b|\bsoperas?\b|\bsalseras?\b|\bmantequillera|\bazucarera|\bsalero|\bpimentero|\bramekin|\bmolcajete|\bportacubiertos'),
    # Cocción
    ('Baterías de cocina', r'\bbaterias? de cocina\b|\bjuego de (ollas|sartenes|cacerolas)|\bset de (ollas|sartenes|cacerolas)|\bollas? y sartenes\b|\bcookware set\b|\butensilios de cocina\b.{0,20}\d+ ?(pz|piezas)'),
    ('Ollas de presión', r'\bollas? (express|expres|a presion|de presion|presto)|\bolla exprés\b|\bpresto\b|\bpressure cooker\b|\bolla rapida\b'),
    ('Sartenes y comales', r'\bkadai\b|\bsart[eé]n|\bcomal(es)?\b|\bwok\b|\bplanchas? (de|para) (asar|cocina|carne)|\bparrilla (de|para) (estufa|cocina)\b|\bgrill (de|para) estufa\b|\bcrepera\b(?!.*electric)|\bpaellera|\bomelet'),
    ('Ollas y cacerolas', r'\basadera\b|\brostizador\b|\btapas?\b(?=.{0,25}(vidrio|cristal))|\binserto (de )?acero inoxidable\b|\bollas?\b|\bcacerolas?\b|\bcazuela|\bcazo\b|\bmarmita|\bvaporera\b|\bpocillo|\bolla (de|para) (caldo|frijoles|tamales|pasta)|\bbudinera|\bcaldero|\bolla holandesa\b|\bdutch oven\b|\bcaldera\b'),
    ('Repostería y moldes', r'\b(plancha|piedra) (de acero )?(para|de) pizza\b|\bacero para pizza\b|\bmoldes?\b|\breposteri|\bpasteler|\bmanga pastelera\b|\bduyas?\b|\brodillo\b|\bespatula (de|para) (reposteria|pastel|decorar)|\bsoporte (para|de) pastel\b|\bbase giratoria\b|'
                            r'\bcharola (para|de) (hornear|horno|galletas)|\bbandeja (para|de) (hornear|horno|galletas)|\bcortadores? de galletas\b|\bcupcake|\bmuffin|\bcake\b|\bpastel\b|\bhornear\b|\bhorneado\b|'
                            r'\btapete de silicona\b|\bcapacillos?\b|\bbatidor(es)? (de globo|manual)\b|\btamiz|\bcernidor|\bbrocha (de|para) (reposteria|cocina)|\bpanaderia\b|\bmasa\b.{0,20}(pizza|pan)|\bpizza\b.{0,20}(piedra|pala|cortador)'),
    ('Básculas y medidores', r'\bbascula|\bbalanza|\bpesa (de|para) cocina\b|\btazas? medidoras?\b|\bcucharas? medidoras?\b|\bmedidor(es)?\b|\btermometro|\btemporizador|\btimer\b|\bvaso medidor\b|\bjarra medidora\b'),
    ('Utensilios de cocina', r'\bdelantal(es)?\b|\bguantes?\b.{0,25}(horno|barbacoa|asador|fuego|parrilla)|'
                             r'\bcentrifugador(a)? de ensaladas?\b|\bsoplete\b|\bflameador\b|\bsoplador (de )?carbon\b|'
                             r'\binfusor|\bsacabolas\b|\bcaminos? de mesa\b|'
                             r'\b(juego|set) de herramientas\b(?! de bar)|\bherramientas? (de|para) (barbacoa|asador|parrilla|cocina)\b|\butensilio|\bespatula|\bcucharon|\bvolteador|\bpinzas?\b|\bbatidor|\bpelador|\brallador|\bcolador|\bescurridor de (pasta|verduras)|\bexprimidor|\bprensa (de|para) (ajo|papas|limon|tortilla)|'
                             r'\bmachacador|\bpasapures|\btortillero|\bmortero|\bmolinillo|\bcucharas? (de madera|de silicona|para servir|ranurada|de cocina|de nylon)|\bespumadera|\bcucharas? para helado\b|'
                             r'\babrelatas|\babridor|\bembudo|\brasp?ador|\bbrocha\b|\bcepillo (de|para) (verduras|papas)|\bpincel de cocina\b|\bprensa\b|\bdescorazonador|\bdeshuesador|\bcortador\b|\bpicador\b|'
                             r'\btenedor (para|de) (carne|asador)|\bpala (de|para) (cocina|pizza)|\bmanoplas?\b|\bguantes? (de|para) (cocina|horno)|\bagarradera|\bsalvamantel|\bposa ?olla|\bposa ?plato|\bmantel(es)?\b|'
                             r'\bindividual(es)? (de|para) mesa\b|\bservilleteros?\b|\bcolador\b|\bprensador\b|\brebanadora\b|\bcortador de huevo\b|\bseparador de yema\b|\bcascanueces|\bmoledor|\bespiral'),
]
_C = [(sub, re.compile(rx)) for sub, rx in _C]


_C_PENAL = {'Desechables': 10, 'Contenedores herméticos': 5, 'Bar y coctelería': 5}


def sub_cocina_fino(tn):
    sub = _primera(tn, _C, _C_PENAL)
    if sub:
        return sub
    # Red de última hora para lo que solo dice el sustantivo.
    if re.search(r'\bbotellas?\b', tn): return 'Botellas de agua'
    if re.search(r'\btapon(es)?\b|\bcorcho', tn): return 'Bar y coctelería'
    if re.search(r'juego de cocina|set de cocina|utensilios', tn): return 'Baterías de cocina'
    if re.search(r'\bpopote|\bpajita', tn): return 'Desechables'
    if re.search(r'\b\d{1,2} ?(oz|onzas)\b', tn): return 'Termos y botellas térmicas'
    return None


# ------------------------------------------------------------------- Libros
LIBROS = [
    'Novela contemporánea', 'Novela romántica', 'Thriller y misterio',
    'Fantasía', 'Ciencia ficción', 'Terror', 'Clásicos', 'Poesía y teatro',
    'Cuentos y relatos', 'Historia', 'Biografías y memorias',
    'Autoayuda y desarrollo personal', 'Negocios y finanzas', 'Psicología',
    'Filosofía y ensayo', 'Religión y espiritualidad', 'Política y sociedad',
    'Ciencia y divulgación', 'Salud y bienestar', 'Cocina y gastronomía',
    'Arte, diseño y fotografía', 'Música y cine', 'Viajes y guías',
    'Hogar, manualidades y mascotas', 'Infantil', 'Juvenil', 'Manga',
    'Cómics y novela gráfica', 'Educación y texto escolar', 'Idiomas',
    'Técnicos y profesionales', 'Deportes',
]

_L = [
    ('Manga', r'\bmanga\b|\bshonen\b|\bshojo\b|\bseinen\b|\bone piece\b|\bnaruto\b|\bdragon ball\b|\bjujutsu\b|\bchainsaw man\b|\bdemon slayer\b|\bkimetsu\b|\bmy hero academia\b|\bberserk\b|\btokyo ghoul\b|\bspy x family\b|\bhaikyu\b|\battack on titan\b|\bshingeki\b|\bbleach\b|\bsailor moon\b|\bvol\.? ?\d+\b.{0,20}\b(tomo|manga)\b'),
    ('Cómics y novela gráfica', r'\bcomics?\b|\bnovela grafica\b|\bmarvel\b|\bdc comics\b|\bbatman\b|\bsuperman\b|\bspider-?man\b|\bx-men\b|\bavengers\b|\bwatchmen\b|\bhistorieta|\btebeo|\bmafalda\b|\bcondorito\b|\bsnoopy\b|\bgarfield\b|\bcalvin y hobbes\b|\bmortadelo\b|\bgraphic novel\b|\bstar wars\b.{0,20}(comic|tomo)'),
    ('Infantil', r'\binfantil|\bpara ninos\b|\bninos de \d|\bcuentos? para (dormir|ninos|bebes)|\bbebes?\b|\bpreescolar\b|\bmis primer|\bprimeras palabras\b|\blibro de (tela|carton|bano)|\bpop-?up\b|\bpara colorear\b|\bpeppa\b|\bpaw patrol\b|\bbluey\b|\bdisney\b(?!.*(historia|biograf))|\bpixar\b|\bdr\.? seuss\b|\bgruffalo\b|\bmonstruo de colores\b|\belmer\b|\bteo\b|\bcuentos clasicos\b|\bfabulas?\b|\bpequen[oa]s? (lector|cientif|explorad)|\bde \d a \d anos\b|\b\+ ?\d anos\b|\baprende (a leer|los numeros|las letras)\b|\babecedario\b|\blibro (con|de) (sonidos|texturas|solapas|pegatinas|stickers)\b|\bharry potter\b.{0,30}ilustrad|\bcuento ilustrado\b|\balbum ilustrado\b|\bjulia donaldson\b|\bpequeno\b.{0,15}(libro|cuento)'),
    ('Juvenil', r'\bjuvenil|\byoung adult\b|\bya\b.{0,10}(novela|romance)|\badolescent|\bteen\b|\bwattpad\b|\bbooktok\b|\bharry potter\b|\bpercy jackson\b|\blos juegos del hambre\b|\bhunger games\b|\bcrepusculo\b|\bdivergente\b|\bmaze runner\b|\bheartstopper\b|\bboulevard\b|\bcancion de hielo\b.{0,10}ilustrad|\balas de (sangre|onix|hierro)\b|\bfourth wing\b|\biron flame\b|\btrono de cristal\b|\bacotar\b|\buna corte de\b|\bel principito\b'),
    ('Cocina y gastronomía', r'\bcocina\b|\bcafe\b|\bbarbecue\b|\bbbq\b|\bpitmaster\b|\bcurr(y|ies)\b|\bpasta\b|\btacos\b|\bsalsas\b|\bpanes\b|\brecetas?\b|\bgastronom|\bcocinar\b|\breposteria\b|\bpanaderia\b|\bcocinero|\bchef\b|\bcomida\b|\bplatillos\b|\bvinos?\b|\bmezcal\b|\bcocteles\b|\bbebidas\b|\bpostres\b|\bhornear\b|\bfreidora de aire\b|\bthermomix\b|\bveganas?\b.{0,10}recet|\bdieta\b.{0,10}recet'),
    ('Deportes', r'\bfutbol\b|\bsoccer\b|\bbeisbol\b|\bbasquet|\bbasket|\bnba\b|\bnfl\b|\bformula 1\b|\bf1\b|\bciclismo\b|\bmaraton\b|\brunning\b|\bcorrer\b|\bcrossfit\b|\bgimnasio\b|\bentrenamiento\b(?!.*(mental|cerebral))|\batleta\b|\bolimpic|\bboxeo\b|\bajedrez\b|\bdeportes?\b|\bmessi\b|\bcristiano ronaldo\b|\bjordan\b|\bkobe\b|\bmundial\b.{0,10}(futbol|2026)|\bclub (america|chivas)\b|\bpumas\b|\btenis\b|\bgolf\b'),
    ('Thriller y misterio', r'\bthriller\b|\bmisterio\b|\bsuspenso\b|\bsuspense\b|\bpolicia[cl]|\bpolicial\b|\bdetective\b|\bcrimen\b|\bcrimenes\b|\basesin|\bhomicid|\bnovela negra\b|\bnegra\b.{0,10}novela|\bintriga\b|\bconspira|\bespionaje\b|\bespia\b|\bagatha christie\b|\bpoirot\b|\bsherlock\b|\bconan doyle\b|\bstieg larsson\b|\bmillennium\b|\bdan brown\b|\bcodigo da vinci\b|\bjohn grisham\b|\bjames patterson\b|\blee child\b|\bjack reacher\b|\bharlan coben\b|\bgillian flynn\b|\bperdida\b.{0,10}flynn|\bpaula hawkins\b|\bla chica del tren\b|\bcolleen hoover\b.{0,10}verity|\bverity\b|\bfreida mcfadden\b|\bla asistenta\b|\bla mujer de la casa\b|\bjoel dicker\b|\bharry quebert\b|\bcamilla lackberg\b|\bjo nesbo\b|\bhenning mankell\b|\bpierre lemaitre\b|\bdolores redondo\b|\btrilogia del baztan\b|\bjuan gomez-?jurado\b|\breina roja\b.{0,10}jurado|\bcarmen mola\b|\beva garcia saenz\b|\bel silencio de la ciudad blanca\b|\bjavier castillo\b|\bla chica de nieve\b|\bmikel santiago\b|\bcesar perez gellida\b|\bbenjamin black\b|\bpatricia highsmith\b|\bripley\b|\bdaphne du maurier\b|\brebeca\b|\bel silencio de los corderos\b|\bhannibal\b|\bthomas harris\b|\bpsicologico\b|\bdesaparicion\b|\bsecuestro\b|\bvenganza\b|\bsecreto\b.{0,10}(oscuro|familiar|mortal)|\bculpable\b|\binocente\b|\btestigo\b|\bcadaver\b(?! exquisito)|\bel caso\b|\bexpediente\b|\binvestigador|\bcomisario\b|\binspector\b|\bforense\b|\bfbi\b|\bcia\b'),
    ('Terror', r'\bterror\b|\bhorror\b|\bmiedo\b(?!.*(supera|vence|sin miedo|dejar))|\bstephen king\b|\blovecraft\b|\bcthulhu\b|\bdracula\b|\bvampir|\bzombi|\bfantasma|\bposesion\b|\bdemonio|\bexorcis|\bmaldicion\b|\bmaldit|\bcasa embrujada\b|\bpesadilla|\bsatanic|\bmacabr|\bgotic[ao]\b|\bmariana enriquez\b|\bjunji ito\b|\bit\b.{0,5}(stephen|king)|\bel resplandor\b|\bcementerio de animales\b|\bfrankenstein\b|\bmary shelley\b|\bcarrie\b.{0,10}king|\bcuentos de terror\b|\bcreepypasta|\bsangre\b.{0,10}(terror|horror)'),
    ('Ciencia ficción', r'\bciencia ficcion\b|\bsci-?fi\b|\bdistop|\butopia\b|\bpostapocalip|\bapocalip|\bfin del mundo\b|\bcyberpunk\b|\bandroid|\brobots?\b(?!.*(ninos|infantil|aprende))|\bmarcian|\bmarte\b|\bextraterrestre|\balienigena|\bviaje en el tiempo\b|\bgalaxia\b|\bespacio\b.{0,10}(nave|exterior|profundo)|\bnave espacial\b|\bdune\b|\bfundacion\b.{0,10}asimov|\basimov\b|\bphilip k\.? dick\b|\bblade runner\b|\bbradbury\b|\bcronicas marcianas\b|\bel problema de los tres cuerpos\b|\bliu cixin\b|\bwilliam gibson\b|\bneuromante\b|\bursula k\b|\ble guin\b|\bandy weir\b|\bel marciano\b|\bproyecto hail mary\b|\bblack mirror\b|\bready player one\b|\bel cuento de la criada\b|\bmargaret atwood\b|\bcadaver exquisito\b|\bstar wars\b|\bstar trek\b|\bhalo\b|\bwarhammer\b|\bmass effect\b|\bmundo feliz\b|\bfahrenheit 451\b|\b1984\b'),
    ('Fantasía', r'\bfantasia\b|\bfantastic|\bdragon|\bmagia\b|\bmagico\b|\bmago\b|\bhechicer|\bbruja\b(?!.*(wicca|ritual))|\bbrujas\b|\belfos?\b|\benanos?\b|\borcos?\b|\bhadas?\b|\bhada\b|\breino\b|\bcorona\b(?!.*(covid|virus|cerveza))|\btrono\b|\bespada\b|\bprofecia\b|\btolkien\b|\bhobbit\b|\bsenor de los anillos\b|\bsilmarillion\b|\bnarnia\b|\bharry potter\b|\browling\b|\bgeorge r\.? ?r\.? martin\b|\bjuego de tronos\b|\bcancion de hielo y fuego\b|\bbrandon sanderson\b|\bmistborn\b|\bnacidos de la bruma\b|\bel archivo de las tormentas\b|\bel camino de los reyes\b|\bpatrick rothfuss\b|\bel nombre del viento\b|\bsarah j\.? maas\b|\bacotar\b|\buna corte de\b|\btrono de cristal\b|\bcrescent city\b|\brebecca yarros\b|\bempireo\b|\balas de\b|\bfourth wing\b|\bleigh bardugo\b|\bseis de cuervos\b|\bsombra y hueso\b|\bgrisha\b|\bholly black\b|\bel principe cruel\b|\bcassandra clare\b|\bcazadores de sombras\b|\bpercy jackson\b|\brick riordan\b|\bandrzej sapkowski\b|\bthe witcher\b|\bgeralt\b|\bbrujo\b|\bterry pratchett\b|\bmundodisco\b|\bneil gaiman\b|\bamerican gods\b|\bcoraline\b|\bmitolog|\bleyendas? (de|del|nordicas|celtas|artur)|\bcuentos de hadas\b|\bprincesa\b|\bcaballer|\bvampiros? y\b|\bhombre lobo\b|\blicantrop|\bcrepusculo\b|\bstephenie meyer\b|\bcazadora\b|\breina roja\b|\bvictoria aveyard\b|\bel poder de los cinco\b|\beragon\b|\bpaolini\b|\bmemorias de idhun\b|\blaura gallego\b|\bromantasy\b|\bromantasia\b'),
    ('Novela romántica', r'\bromantic|\bromance\b|\bhistoria de amor\b|\bnovela de amor\b|\bamor (prohibido|imposible|eterno|verdadero|a primera vista|de verano)\b|\benamor|\berotic|\bseduc|\bcolleen hoover\b|\bromper el circulo\b|\bit ends with us\b|\bali hazelwood\b|\bemily henry\b|\btessa bailey\b|\belena armas\b|\bmegan maxwell\b|\bmoruena estringana\b|\bnicholas sparks\b|\bel diario de noa\b|\bjojo moyes\b|\byo antes de ti\b|\bjulia quinn\b|\bbridgerton\b|\bsally rooney\b|\bgente normal\b|\btaylor jenkins reid\b|\bsiete maridos\b|\bevelyn hugo\b|\blucy score\b|\bana huang\b|\btwisted\b|\bmercedes ron\b|\bculpa mia\b|\bculpables\b|\balice kellen\b|\bbelen\b.{0,10}(historia|amor)|\bnovia\b|\bboda\b.{0,10}(novela|amor)|\bex\b.{0,5}novi|\benemies to lovers\b|\bfake dating\b|\bslow burn\b|\bspicy\b|\bhot\b.{0,10}(novela|romance)|\bdark romance\b|\bnew adult\b|\bchick lit\b|\bcomedia romantica\b|\bdespues de\b.{0,5}(after|todd)|\bafter\b.{0,10}(anna todd|amor)|\banna todd\b|\bsarah adams\b|\babby jimenez\b|\bcasey mcquiston\b|\brojo, blanco y sangre azul\b|\bheartstopper\b|\bboulevard\b|\bflor m\.? salvador\b|\bcuando no queden mas estrellas\b|\btodo lo que nunca fuimos\b|\bel amor en los tiempos\b'),
    ('Historia', r'\bhistoria (de mexico|universal|del mundo|de la humanidad|de espana|de europa|de america|de roma|de grecia|antigua|contemporanea|moderna|medieval|minima|breve|de la (revolucion|conquista|independencia|guerra|iglesia|ciencia|filosofia|cristiandad|inquisicion|humanidad)|del (siglo|imperio|holocausto|mundo)|de los (aztecas|mayas|incas|vikingos|reyes|papas))|\bhistoriad|\bhistoric[ao]s?\b|\bhistoria\b(?=.{0,30}(mexico|mundial|universal|humana|militar|politica|economica|social|cultural|colonial))|\bguerra\b|\bsegunda guerra\b|\bprimera guerra\b|\brevolucion\b|\bconquista\b|\bimperio\b|\bmexica\b|\bazteca|\bmaya\b|\bindependencia\b|\bporfiri|\bsiglo (xv|xvi|xvii|xviii|xix|xx)\b|\bmedieval\b|\bantigua roma\b|\bgrecia\b|\begipto\b|\bvikingo|\bnazi|\bholocausto\b|\bhitler\b|\bstalin\b|\bnapoleon\b|\bcristobal colon\b|\bcortes\b.{0,20}(conquista|moctezuma)|\bmoctezuma\b|\bjuarez\b|\bvilla\b.{0,10}zapata|\bzapata\b|\bcristeros?\b|\btlatelolco\b|\b1968\b|\bcronicas? de (la|el|un|los|indias)\b|\barqueolog|\bcivilizacion|\bprehispanic|\bvirreinato\b|\bcolonia\b.{0,15}(nueva espana|mexico)|\bnueva espana\b|\bhistoriador'),
    ('Biografías y memorias', r'\bbiograf|\bautobiograf|\bmemorias\b|\bmemoir\b|\bmi vida\b|\bvida de\b|\bvida y obra\b|\bdiario de\b(?!.*(greg|nikki|ana frank))|\bdiario de ana frank\b|\bconfesiones\b|\bcartas\b.{0,20}\ba\b|\btestimonio\b|\bla historia de (mi|su) vida\b|\bel hombre que\b|\bla mujer que\b|\bretrato de\b|\ben primera persona\b|\bsemblanza\b'),
    ('Autoayuda y desarrollo personal', r'\bautoayuda\b|\bguia practica\b|\bcomo empezar\b|\btransform(a|ar) tu\b|\bcrecimiento personal\b|\bsanacion interior\b|\bvida plena\b|\bdesarrollo personal\b|\bhabitos?\b|\bexito\b|\bmotivaci|\bsuperacion\b|\bmindfulness\b|\bmeditaci|\bfelicidad\b|\bautoestima\b|\bproposito\b|\bcambia tu\b|\btu mejor version\b|\bpoder de\b|\bel arte de\b|\bcomo (ganar|hacer|dejar de|ser|lograr|vivir|dejar)\b|\bdisciplina\b|\bproductividad\b|\bmanana\b.{0,10}(rutina|club)|\bsutil arte\b|\bagenda\b|\bplanner\b|\bgratitud\b|\bmanifestaci|\bley de (la )?atraccion\b|\bcoaching\b|\bcoach\b|\bresiliencia\b|\bsanar\b|\bsanacion\b|\bpaz interior\b|\bvida plena\b|\bactitud\b|\bpiensa\b|\bmentalidad\b|\bconfianza\b|\bmiedo\b|\bvulnerab|\bduelo\b|\bperdon\b|\bstoic|\bestoic|\bikigai\b|\bwabi.?sabi\b|\bhygge\b|\bsimplifica\b|\bordenar\b.{0,10}(casa|vida)|\bmarie kondo\b|\bbrene brown\b|\brobin sharma\b|\bjames clear\b|\bmark manson\b|\bdale carnegie\b|\bstephen covey\b|\bpaulo coelho\b|\bjoe dispenza\b|\bwayne dyer\b|\blouise hay\b|\bdeepak chopra\b|\beckhart tolle\b'),
    ('Negocios y finanzas', r'\bnegocios?\b|\bfinanzas?\b|\bdinero\b|\brico\b|\briqueza\b|\binversion|\binvertir\b|\bbolsa de valores\b|\bacciones\b.{0,10}bolsa|\bcriptomoneda|\bbitcoin\b|\bemprend|\bstartup\b|\bliderazgo\b|\blider\b|\bmarketing\b|\bventas\b|\bvender\b|\bnegociaci|\bmanagement\b|\bgerencia\b|\badministracion\b|\bestrategia\b|\bempresa|\bempresari|\bmba\b|\beconomia\b|\beconomico\b|\bcapitalismo\b|\bpadre rico\b|\bkiyosaki\b|\bwarren buffett\b|\belon musk\b|\bsteve jobs\b|\bjeff bezos\b|\bhabitos de la gente altamente\b|\bpiense y hagase rico\b|\bnapoleon hill\b|\bcontabilidad\b|\bimpuestos\b|\bsat\b|\bfiscal\b|\bcomercio\b|\bproductividad empresarial\b|\bcliente|\bjefe\b|\btrabajo\b.{0,10}(remoto|equipo)|\bcarrera\b.{0,10}profesional'),
    ('Psicología', r'\bpsicolog|\bpsiquiatr|\bpsicoanal|\bemocion|\bansiedad\b|\bdepresion\b|\btrauma\b|\bapego\b|\bnarcisis|\bmente\b|\bmental\b|\bcerebro\b(?!.*(ciencia|neurociencia))|\bconducta\b|\bcomportamiento\b|\bfreud\b|\bjung\b|\blacan\b|\bterapia\b|\bterapeut|\bautismo\b|\btdah\b|\binteligencia emocional\b|\bpersonalidad\b|\bcriar\b|\bcrianza\b|\bpadres\b|\bmaternidad\b|\bpaternidad\b|\bhijos\b|\badolescencia\b.{0,10}(guia|padres)|\bpareja\b|\brelaciones\b.{0,10}(toxic|sanas|de pareja)|\bdivorcio\b|\bcodependencia\b|\bsexualidad\b|\bsexo\b'),
    ('Filosofía y ensayo', r'\bfilosof|\bensayo|\bpensamiento\b|\betica\b|\bmoral\b|\bexistencial|\bnietzsche\b|\bplaton\b|\baristoteles\b|\bsocrates\b|\bkant\b|\bhegel\b|\bmarx\b|\bmarco aurelio\b|\bseneca\b|\bepicteto\b|\bschopenhauer\b|\bheidegger\b|\bsartre\b|\bcamus\b|\bbyung-?chul han\b|\bfoucault\b|\bzizek\b|\bsavater\b|\bbauman\b|\bel mito de sisifo\b|\bmeditaciones\b|\bdialogos\b|\bmetafisica\b|\blogica\b|\bepistemolog|\bsobre la (verdad|libertad|felicidad|muerte|brevedad)\b|\bcartas a un\b|\bteoria\b.{0,10}(critica|social)'),
    ('Religión y espiritualidad', r'\bbiblia\b|\bbiblic|\bdios\b|\bjesus\b|\bcristo\b|\bcristian|\bcatolic|\bevangeli|\biglesia\b|\boracion|\brezar\b|\bespiritual|\bvirgen (de|maria)\b|\bguadalupe\b|\bpapa francisco\b|\bpapa leon\b|\bbudis|\bbuda\b|\bzen\b|\bhindu|\bislam|\bcoran\b|\bjudaism|\btora\b|\bkabbalah\b|\bcabala\b|\btarot\b|\bastrolog|\bhoroscop|\bzodiac|\barcangel|\bmilagros\b|\bsagrad|\bchaman|\bsalmos\b|\bteolog|\bmisa\b|\bcatecismo\b|\bconfirmacion\b|\bprimera comunion\b|\breiki\b|\bchakras?\b|\bcristales\b.{0,10}(energia|sanacion)|\bbrujeria\b|\bbruja\b|\bwicca\b|\besoteri|\bmagia\b(?!.*(novela|fantasia|dragon|hechicer))|\brunas\b|\bnumerolog|\bmeditacion guiada\b|\bun curso de milagros\b|\bel secreto\b|\bconversaciones con dios\b|\bosho\b|\bkrishnamurti\b|\bdalai lama\b|\bthich nhat hanh\b'),
    ('Política y sociedad', r'\bpolitic|\bsociedad\b|\bsocial\b|\bfeminis|\bgenero\b|\bmujeres\b(?!.*novela)|\bmachismo\b|\bracismo\b|\bdemocracia\b|\bdictadura\b|\bcorrupcion\b|\bnarco|\bcartel\b|\bviolencia\b|\bcrimen organizado\b|\bperiodis|\breportaje\b|\binvestigacion periodistica\b|\bmexico\b.{0,20}(actual|hoy|contemporaneo|politica)|\bamlo\b|\blopez obrador\b|\bsheinbaum\b|\btrump\b|\bcalderon\b|\bpena nieto\b|\bfox\b|\bsalinas\b|\bmorena\b|\bpri\b|\bpan\b(?! (de|dulce|casero|integral))|\belecciones\b|\bcapitalismo\b|\bsocialismo\b|\bcomunismo\b|\banarqu|\bglobalizacion\b|\bderechos humanos\b|\bmigraci|\bmigrante|\bfrontera\b|\bdesigualdad|\bpobreza\b|\bgeopolit|\bchomsky\b|\bcambio climatico\b|\becolog|\bmedio ambiente\b|\bsociolog|\bantropolog|\bactivis|\bderechos\b|\bjusticia\b|\bley\b|\bcultura\b.{0,10}(mexicana|popular)|\bidentidad\b|\bnacion\b|\bpatria\b|\bmasacre\b|\bdesaparecidos\b|\bayotzinapa\b'),
    ('Ciencia y divulgación', r'\bciencia\b|\bcientif|\bdivulgaci|\buniverso\b|\bcosmos\b|\bastronom|\bfisica\b|\bquimica\b|\bbiolog|\bevolucion\b|\bgenetic|\badn\b|\bneurocien|\bmatematic|\bnumeros\b|\binfinito\b|\bagujeros? negros?\b|\bbig bang\b|\bteoria de la relatividad\b|\bcuantic|\bdarwin\b|\beinstein\b|\bhawking\b|\bsagan\b|\bcarl sagan\b|\bharari\b|\bsapiens\b|\bhomo deus\b|\bdawkins\b|\bnewton\b|\bgalileo\b|\btierra\b(?! de)|\bplanetas?\b|\bespacio\b.{0,10}(exploracion|nasa)|\bnasa\b|\bdinosaurio|\bfosil|\bclima\b|\bgeolog|\bocean|\banimales\b|\bnaturaleza\b|\bbotanica\b|\bplantas\b|\binsectos\b|\baves\b|\becosistema|\binteligencia artificial\b|\btecnolog|\bcomputaci|\bprogramaci|\brobot|\balgoritm|\binternet\b|\bredes sociales\b|\bfuturo\b|\binvento|\bingenier|\bmedicina\b.{0,10}(historia|divulg)|\bcuerpo humano\b|\bvirus\b|\bpandemia\b|\bvacuna|\bmicrobio'),
    ('Salud y bienestar', r'\bsalud\b|\bbienestar\b|\bdieta\b|\bnutricion\b|\balimentacion\b|\bayuno\b|\bketo\b|\bvegan|\bvegetarian|\badelgaz|\bbajar de peso\b|\bfitness\b|\bmedicina natural\b|\benfermedad|\bcancer\b|\bdiabetes\b|\bintestino\b|\bmicrobiota\b|\bhormonas?\b|\bmenopausia\b|\bembarazo\b|\bparto\b|\blactancia\b|\bsueno\b|\bdormir\b|\bestres\b|\brespiracion\b|\blongevidad\b|\benvejec|\banti-?aging\b|\bdolor cronico\b|\bhigado\b|\bdesintox|\bremedios\b|\byoga\b|\bpilates\b|\bherbolaria\b|\bplantas medicinales\b|\bhomeopat|\bnaturista\b|\bmasaje\b|\brelajacion\b'),
    ('Arte, diseño y fotografía', r'\barte\b|\bartista|\bpintura\b|\bpintor|\bescultura\b|\barquitectura\b|\barquitect|\bdiseno\b|\bdesign\b|\bfotograf|\bgrabado\b|\bdibujo\b|\bdibujar\b|\bilustraci|\bacuarela\b|\bcaligraf|\blettering\b|\bfrida kahlo\b|\bdiego rivera\b|\bpicasso\b|\bvan gogh\b|\bda vinci\b|\bmonet\b|\bbanksy\b|\bmuseo\b|\bgaleria\b|\bcatalogo\b|\bmoda\b|\bfashion\b|\bcoleccion\b.{0,10}(arte|fotograf)|\bbellas artes\b|\bhistoria del arte\b|\bestetica\b|\btatuaje|\bgraffiti\b|\bstreet art\b|\banime\b.{0,10}(arte|ilustr|dibuj)|\bcomo dibujar\b|\bmanga\b.{0,10}(dibujar|como)|\bcoloring\b|\bcolorear\b.{0,10}(adultos|mandalas)|\bmandalas?\b'),
    ('Música y cine', r'\bmusica\b|\bmusical\b|\bcancion|\bguitarra\b|\bpiano\b|\bpartitura|\brock\b|\bjazz\b|\bbeatles\b|\bqueen\b|\bmetallica\b|\bbad bunny\b|\btaylor swift\b|\bbanda\b.{0,10}(historia|biograf)|\bcine\b|\bpelicula|\bfilm\b|\bdirector\b.{0,10}(cine|pelicul)|\bhollywood\b|\bstar wars\b|\bel senor de los anillos\b.{0,15}(pelicul|cine|arte)|\bharry potter\b.{0,15}(pelicul|cine)|\bseries?\b.{0,10}(tv|netflix|television)|\bnetflix\b|\bguion\b|\bteatro\b.{0,10}(cine|television)|\bactor\b|\bactriz\b|\btelevision\b|\bkpop\b|\bk-pop\b|\bbts\b|\bblackpink\b|\bopera\b|\bbroadway\b|\bmariachi\b|\bcorridos\b|\bsinfoni|\bconcierto\b|\bdj\b|\bhip ?hop\b|\brap\b'),
    ('Viajes y guías', r'\bguia (de viaje|turistica|lonely)|\blonely planet\b|\bturis|\bmochilero\b|\bcamino de santiago\b|\bnomada digital\b|\bviajar (por|a|en|sin|con)\b|\bsenderismo\b|\bmontanismo\b|\batlas\b|\bmapas?\b|\bruta (de|por)\b|\bitinerario'),
    ('Hogar, manualidades y mascotas', r'\bmanualidad|\bcrochet\b|\btejido\b|\btejer\b|\bganchillo\b|\bcostura\b|\bcoser\b|\bbordado\b|\bpunto de cruz\b|\borigami\b|\bpapiroflexia\b|\bscrapbook|\bcarpinteria\b|\bbricolaje\b|\bjardin|\bhuerto\b|\bplantas de interior\b|\bcactus\b|\bsuculentas\b|\bbonsai\b|\bdecoracion\b|\binterior(ismo|es)\b|\bhogar\b|\bcasa\b.{0,10}(decorar|organizar|limpieza)|\bfeng shui\b|\bmascotas?\b|\bperros?\b|\bgatos?\b|\bcachorro\b|\badiestramiento\b|\bacuario\b|\bpeces\b|\bcaballos?\b|\bboda\b|\bfiesta\b|\bcumpleanos\b|\bregalo\b.{0,10}(ideas|hacer)|\bdiy\b|\bhazlo tu mismo\b|\bcerveza artesanal\b|\bcandelas\b|\bvelas\b|\bjabones\b|\bhobby\b|\bmodelismo\b|\bfilatelia\b|\bautos?\b.{0,10}(clasicos|historia|guia)|\bmotocicletas?\b'),
    ('Educación y texto escolar', r'\beducaci|\bescolar\b|\bpreparatoria\b|\bsecundaria\b|\bprimaria\b|\bbachillerato\b|\buniversidad\b|\buniversitari|\blibro de texto\b|\bcuaderno\b|\bejercicios\b|\bexamen\b|\badmision\b|\bunam\b|\bipn\b|\bcomipems\b|\bexani\b|\bceneval\b|\btoefl\b|\bielts\b|\bsat\b.{0,10}(examen|prep)|\bmatematicas\b.{0,10}(secundaria|primaria|preparatoria|ejercicios)|\bgramatica\b|\bortografia\b|\bredaccion\b|\bcaligrafia\b.{0,10}(escolar|ninos)|\bpedagog|\bdidactic|\bdocente|\bmaestro|\bprofesor|\benseñanza\b|\bensenanza\b|\baprendizaje\b|\bsep\b|\bplan de estudios\b|\bmontessori\b|\bwaldorf\b|\bhomeschool|\btareas\b|\bvacaciones\b.{0,10}(cuaderno|activ)|\blectura\b.{0,10}(comprension|guia)|\bdiccionario\b|\benciclopedia\b|\batlas escolar\b'),
    ('Idiomas', r'\bidiomas?\b|(aprende|aprender|curso|gramatica|vocabulario|diccionario|verbos|metodo|hablar|practica|domina|ejercicios) (de |el |en )?(ingles|frances|aleman|italiano|portugues|japones|chino|coreano|ruso|arabe|latin|nahuatl)\b|\bingles (basico|intermedio|avanzado|para|sin esfuerzo|en \d|facil|rapido)\b|\bedicion bilingue\b|\bmaya\b.{0,10}(lengua|idioma|aprende)|\bvocabulario\b|\bverbos\b|\bgramatica (inglesa|francesa|alemana)|\bbilingue\b|\btraduccion\b|\baprende (ingles|frances|aleman|italiano|japones|chino|coreano)|\bcurso de (ingles|frances|aleman|italiano|japones|chino)|\benglish (grammar|vocabulary|course|for|in use)\b|\blearn english\b|\bspanish\b.{0,10}(learn|for)|\bdele\b|\bhsk\b|\bjlpt\b|\bcambridge\b.{0,10}(english|ingles)|\boxford\b|\bpalabras en\b'),
    ('Técnicos y profesionales', r'\bderecho\b|\bjuridic|\bjuridica\b|\babogad|\bcodigo (civil|penal|fiscal|de comercio)\b|\bconstitucion politica\b|\bley federal\b|\bleyes\b|\bjurisprudencia\b|\bmedicina\b|\banatomia\b|\bfisiologia\b|\bfarmacolog|\benfermeria\b|\bodontolog|\bveterinaria\b|\bpsicometr|\bingenieria\b|\bcalculo\b|\balgebra\b|\bestadistica\b|\bcontabilidad\b|\bauditoria\b|\bfinanzas corporativas\b|\barquitectura\b.{0,10}(manual|tecnic)|\bconstruccion\b|\belectricidad\b|\belectronica\b|\bmecanica\b|\bautomotriz\b|\bprogramacion\b|\bpython\b|\bjava\b|\bjavascript\b|\bexcel\b|\bautocad\b|\bsql\b|\bredes\b.{0,10}(computo|cisco)|\bciberseguridad\b|\bciencia de datos\b|\bmachine learning\b|\bmanual\b|\btratado\b|\bcompendio\b|\bprontuario\b|\bnormas? (iso|nom|mexicanas)\b|\bagronom|\bganader|\bnutricion clinica\b|\bfisioterapia\b|\bquiropractic|\bacupuntura\b|\bgastronomia\b.{0,10}(tecnic|profesional)'),
    ('Poesía y teatro', r'\bpoesia\b|\bpoemas?\b|\bpoetas?\b|\bpoetica\b|\bantologia poetica\b|\bversos\b|\bsonetos?\b|\bhaiku|\bteatro\b|\bdramaturg|\bobra de teatro\b|\btragedia\b|\bcomedia\b(?!.*(novela|romantica))|\bmonolog|\bsabines\b|\bbenedetti\b|\bneruda\b|\bpaz\b.{0,10}(octavio|poes)|\boctavio paz\b|\blorca\b|\bbecquer\b|\bsor juana\b|\bpizarnik\b|\bbukowski\b|\brupi kaur\b|\bshakespeare\b|\bhamlet\b|\bromeo y julieta\b|\bmacbeth\b|\bcalderon de la barca\b|\bla vida es sueno\b'),
    ('Cuentos y relatos', r'\bcuentos?\b(?! (para|infantil|clasic|de hadas|ilustrad))|\brelatos?\b|\bnarrativa breve\b|\bantologia\b|\bficciones\b|\bborges\b|\bcortazar\b|\bchejov\b|\bpoe\b|\bcarver\b|\bmonterroso\b|\brulfo\b|\bel llano en llamas\b|\bquiroga\b|\bmicrorrelato|\bfabulas? de\b'),
    ('Clásicos', r'\bclasicos? (de la literatura|universal|ilustrad|de siempre)|\bcoleccion clasicos\b|\bpenguin clasicos\b|\bletras hispanicas\b|\bcatedra\b|\bsepan cuantos\b|\baustral\b|\bcervantes\b|\bdon quijote\b|\bquijote\b|\bhomero\b|\biliada\b|\bodisea\b|\bdante\b|\bdivina comedia\b|\bshakespeare\b|\bdostoievski\b|\bdostoyevski\b|\btolstoi\b|\bcrimen y castigo\b|\banna karenina\b|\bguerra y paz\b|\bvictor hugo\b|\bmiserables\b|\bdumas\b|\bmontecristo\b|\bmosqueteros\b|\bjane austen\b|\borgullo y prejuicio\b|\bbronte\b|\bjane eyre\b|\bcumbres borrascosas\b|\bdickens\b|\bkafka\b|\bmetamorfosis\b|\bel proceso\b|\bjoyce\b|\bulises\b|\bproust\b|\bflaubert\b|\bmadame bovary\b|\bstendhal\b|\bbalzac\b|\bzola\b|\bwilde\b|\bdorian gray\b|\bstevenson\b|\bdr\.? jekyll\b|\bla isla del tesoro\b|\bmelville\b|\bmoby dick\b|\bhemingway\b|\bel viejo y el mar\b|\bfitzgerald\b|\bgran gatsby\b|\bsteinbeck\b|\bfaulkner\b|\bvirginia woolf\b|\borwell\b|\b1984\b|\brebelion en la granja\b|\bhuxley\b|\bun mundo feliz\b|\bbradbury\b|\bfahrenheit\b|\bsalinger\b|\bguardian entre el centeno\b|\bkerouac\b|\bcamus\b|\bel extranjero\b|\bla peste\b|\bsartre\b|\bhesse\b|\bsiddharta\b|\bdemian\b|\bel lobo estepario\b|\bmann\b.{0,10}(montana magica|thomas)|\bgoethe\b|\bfausto\b|\bwerther\b|\bnietzsche\b.{0,10}zaratustra|\bmarquez\b|\bcien anos de soledad\b|\bgarcia marquez\b|\bcortazar\b.{0,10}rayuela|\brayuela\b|\bvargas llosa\b|\bborges\b|\bpedro paramo\b|\bjuan rulfo\b|\bcarlos fuentes\b|\bla region mas transparente\b|\baura\b.{0,10}fuentes|\bsabato\b|\bel tunel\b|\bbioy casares\b|\bonetti\b|\bgaldos\b|\bclarin\b|\bla regenta\b|\blazarillo\b|\bcelestina\b|\bmio cid\b|\bquevedo\b|\bgongora\b|\blope de vega\b|\bunamuno\b|\bniebla\b|\bmachado\b|\bdelibes\b|\bcela\b|\bla colmena\b|\bcarmen laforet\b|\bnada\b.{0,10}laforet|\btolkien\b.{0,10}(anotado|ilustrado)|\bpenguin clasicos\b|\bausten\b|\bcolleccion clasicos\b|\bcatedra\b|\bletras hispanicas\b|\balianza\b.{0,10}clasic|\bgredos\b|\bporrua\b|\bsepan cuantos\b'),
    ('Novela contemporánea', r'\bnovela\b|\bficcion\b|\bliteratura\b|\bnarrativa\b|\bhistoria de\b|\bsaga familiar\b|\bpremio (nobel|planeta|alfaguara|cervantes|nadal|herralde|biblioteca breve|pulitzer|booker|goncourt)\b|\bbest ?seller\b|\bmas vendido\b|\bisabel allende\b|\bmario benedetti\b|\bharuki murakami\b|\bmurakami\b|\bfernanda melchor\b|\bvaleria luiselli\b|\bguadalupe nettel\b|\bjuan villoro\b|\belena poniatowska\b|\bangeles mastretta\b|\blaura esquivel\b|\bcomo agua para chocolate\b|\bsamanta schweblin\b|\bmariana enriquez\b|\bpaulo coelho\b|\bel alquimista\b|\bcarlos ruiz zafon\b|\bla sombra del viento\b|\barturo perez-?reverte\b|\bjavier marias\b|\balmudena grandes\b|\bjulia navarro\b|\bmaria duenas\b|\bel tiempo entre costuras\b|\bdolores redondo\b|\belena ferrante\b|\bkhaled hosseini\b|\bcometas en el cielo\b|\bkazuo ishiguro\b|\bsaramago\b|\bensayo sobre la ceguera\b|\bgabriel garcia marquez\b|\bjulio cortazar\b|\bjorge luis borges\b|\broberto bolano\b|\bbolano\b|\bpedro almodovar\b|\bcormac mccarthy\b|\bla carretera\b|\bpaul auster\b|\bdon delillo\b|\bphilip roth\b|\bjonathan franzen\b|\bmargaret atwood\b|\bzadie smith\b|\bchimamanda\b|\bhan kang\b|\bla vegetariana\b|\bsally rooney\b|\bdonna tartt\b|\bel jilguero\b|\bhanya yanagihara\b|\btan poca vida\b|\bocean vuong\b|\bbrit bennett\b|\bfredrik backman\b|\bun hombre llamado ove\b|\bbonnie garmus\b|\blecciones de quimica\b|\bdelia owens\b|\bla chica salvaje\b|\bgabrielle zevin\b|\bmanana y tarde\b|\brebecca serle\b|\bmatt haig\b|\bla biblioteca de la medianoche\b|\bjohn green\b|\bbajo la misma estrella\b|\bciudades de papel\b'),
]
_L = [(sub, re.compile(rx)) for sub, rx in _L]

# La subcategoría vieja sirve de pista cuando el título no dice el género.
_L_HEREDA = {
    'Literatura y novela': 'Novela contemporánea',
    'No ficción': None,
    'Infantil': 'Infantil',
    'Juvenil': 'Juvenil',
    'Cómic y manga': 'Cómics y novela gráfica',
    'Ciencia': 'Ciencia y divulgación',
    'Arte': None,
    'Gastronomía': 'Cocina y gastronomía',
    'Estilo de vida': 'Hogar, manualidades y mascotas',
    'Especializados': 'Técnicos y profesionales',
}

# Géneros que un título infantil/juvenil no debe abandonar aunque nombre
# dragones o crímenes: si la tienda ya lo tenía como Infantil, el "Harry
# Potter" sigue siendo juvenil y el "cuento de dinosaurios" infantil.
_L_NINOS = {'Infantil', 'Juvenil'}


def sub_libro_fino(tn, sub_vieja=None):
    """Género a partir del título (+ subtítulo/H1 si viene pegado en tn).
    `sub_vieja` es la subcategoría con la que llegó de la tienda."""
    if sub_vieja in _L_NINOS:
        # Dentro de niños solo se distingue manga/cómic; lo demás se queda.
        for sub, rx in _L[:2]:
            if rx.search(tn):
                return sub
        return sub_vieja
    if sub_vieja == 'Cómic y manga':
        return 'Manga' if _L[0][1].search(tn) else 'Cómics y novela gráfica'
    for sub, rx in _L:
        if rx.search(tn):
            return sub
    return _L_HEREDA.get(sub_vieja)
