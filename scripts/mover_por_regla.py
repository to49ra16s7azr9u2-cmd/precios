#!/usr/bin/env python3
"""Arma grupos de movimiento (el JSON que lee aplicar_movimientos.py) a
partir de reglas explícitas: categoría de origen + expresión sobre el
título -> categoría y subcategoría de destino.

POR QUÉ
-------
Tras repartir las fichas sin subcategoría (19-sep-2026) lo que queda sin
subcategoría es, en su mayoría, ficha con la CATEGORÍA equivocada por la
taxonomía de su tienda: walkie-talkies en Audífonos, instrumental dental y
de belleza en Herramientas, placas y apagadores comunes en Domótica,
correas de reloj en Relojes inteligentes, cabezas móviles de escenario en
Instrumentos, teclados musicales en Teclados. El auditor por acuerdo
(modelo + reglas) no las alcanza porque el clasificador de capturas no
tiene regla de categoría para todas, y el modelo solo propone destinos
dentro de lo que ya vio. Acá se nombran una por una, con su regla, y se
aplican con la misma bitácora que los demás movimientos.

USO
---
    python3 scripts/mover_por_regla.py --salida /tmp/mover_reglas.json      # informa y escribe
    python3 scripts/aplicar_movimientos.py /tmp/mover_reglas.json --todos --motivo "..."
"""
import argparse
import collections
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import load_catalog  # noqa: E402
from subcategorias_finas import sub_cocina_fino  # noqa: E402


def T(s):
    s = re.sub(r'\s+', ' ', (s or '').lower())
    return s.translate(str.maketrans('áéíóúñü', 'aeiounu'))


def tramo_mah(tn):
    m = re.search(r'(\d{1,3}[.,]?\d{3}|\d{4,6})\s*m ?ah', tn)
    if not m:
        return None
    n = int(m.group(1).replace('.', '').replace(',', ''))
    return 'Hasta 10,000 mAh' if n <= 10000 else ('10,000 a 20,000 mAh' if n <= 20000 else 'Más de 20,000 mAh')


# (categoría origen, regex que debe cumplir, regex que NO debe cumplir o None,
#  categoría destino, subcategoría destino o función(tn) -> sub|None)
REGLAS = [
    ('Audífonos', r'walkie|talkie|\bradios?\b(?! ?control)|onda corta|reproductor (mp3|de cd|de musica)|discman|intercomunicador',
     r'^(?:\S+ ){0,2}(auricular|audifono|headset|earbud|headphone)|radio fm|for iphone|mp3 player|conduccion osea|open ?ear',
     'Bocinas', 'Radios y reproductores'),
    ('Audífonos', r'^(?:\S+ )?microfono', r'diadema con microfono|con microfono|auricular|audifonos? con', 'Instrumentos musicales', 'Micrófonos'),
    ('Herramientas', r'\bdental|\bbucal|articulador', None, 'Belleza y cuidado personal', 'Cuidado personal'),
    ('Herramientas', r'manicura|pedicura|\bunas\b|nail (art|drill|lamp|tips)|\bnails\b', r'aerografo|pulverizador de pintura', 'Belleza y cuidado personal', 'Uñas'),
    ('Herramientas', r'\bfacial|guasha|gua sha|analizador de (piel|cabello)|cuero cabelludo|celulitis|drenaje linfatico|escultura corporal|esculpir corporal',
     None, 'Belleza y cuidado personal', 'Dispositivos de cuidado facial'),
    ('Herramientas', r'\bcabello\b|\bbarba\b|\bbarber|\bbigote\b|peinar|extensiones de cabello|\bpelo\b|peluquer', r'lija|sierra|taladro', 'Belleza y cuidado personal', 'Cuidado del cabello'),
    ('Herramientas', r'maquillaje|corrector|paleta de crema', None, 'Belleza y cuidado personal', 'Maquillaje'),
    ('Herramientas', r'\bobd ?2\b|\bobd ?ii\b|escaner automotriz|diagnostico automotriz', None, 'Autos, bicicletas y motos', 'Accesorios y refacciones'),
    ('Herramientas', r'masaje|masajeador|rodillo de masaje|spiky ball', None, 'Belleza y cuidado personal', 'Masajeadores'),
    ('Herramientas', r'agarres? (para|de) gym|agarraderas|para gym\b|para gimnasio', None, 'Deportes y fitness', 'Accesorios de fuerza'),
    ('Domótica y hogar inteligente', r'apagador|tapa ciega|placa (armada|ciega|cristal|valo|solaris|lugano|flat|slim|dimmer|de (acero|aluminio|plastico|nylon|cristal|pared)|con \d|\d|cubre)|'
     r'(\d|con|dos|tres) (contactos?|interruptores?|apagadores?|modulos?)\b|cubierta para interruptor|tapa para placa|placa cubre',
     r'intelig|wifi|wi-fi|tuya|zigbee|alexa|smart|matter|\bapp\b|magnetic|shelly|sonoff|\bwiz\b|connected',
     'Herramientas', 'Material eléctrico'),
    ('Domótica y hogar inteligente', r'letrero|\bneon\b', r'intelig|wifi|smart|tuya|alexa|\bapp\b|rgbic|govee|tira', 'Iluminación', 'Decorativa'),
    ('Domótica y hogar inteligente', r'adaptador (universal )?de (viaje|enchufe)|adaptador de enchufe|enchufe (europeo|americano)|convertidor a tierra',
     r'control remoto|\bfoco\b|intelig', 'Cargadores y adaptadores', 'Adaptador de corriente'),
    ('Domótica y hogar inteligente', r'kit.{0,25}camaras|\bcctv\b|\bdahua\b|\bhikvision\b|\bnvr\b|\bdvr\b', None, 'Cámaras de seguridad', 'Kits de vigilancia'),
    ('Relojes inteligentes', r'\bcorreas?\b|extensible|pulsera (de|elastica|para|deportiva)|banda (de|para) reloj',
     r'apple watch|galaxy watch|smart ?watch|mi band|fitbit|garmin|huawei watch|amazfit|smart|whoop|pixel watch|xiaomi',
     'Joyería y bisutería', 'Correas y extensibles'),
    ('Instrumentos musicales', r'cabeza (movil|robotica)|cabezas moviles|\bpar ?led\b|\bpar ?\d{2,3}\b|estrobo|\bdmx\b|\bbeam\b|\bwash\b|barra led|maquina de humo|liquido.{0,10}humo|canon de luces|elevacion.{0,20}iluminacion|\bwasher\b|luces led (par|rgb)|kit home party|\bgobo\b',
     r'cuerdas|strings', 'Iluminación', 'Escenario'),
    ('Teclados', r'\b(25|32|37|49|54|61|76|88) teclas\b|casiotone|\bpsr|\byamaha\b|\bcasio\b|\balesis\b|\bpiano\b|\bkboard\b|\bkosmos\b|\bkorg\b|\broland\b|teclado (musical|digital|infantil)',
     r'mecanic|gamer|gaming|\busb\b|qwerty|espanol|\bpc\b|computadora|juego|membrana|touchpad|bluetooth|inalambric|2\.4 ?g|para (mac|windows|ipad|tablet)', 'Instrumentos musicales', 'Teclados electrónicos'),
    ('Cargadores y adaptadores', r'power ?bank|banco de energia|bateria (externa|portatil)|powerbank', None, 'Baterías portátiles', tramo_mah),
    ('Baterías portátiles', r'arrancador|jump ?starter', None, 'Autos, bicicletas y motos', 'Baterías para auto'),
    ('Juegos de mesa', r'play-?doh|\bslime\b|plastilina|kit de ciencia|pegatinas|stickers|arena sensorial|cuaderno de actividades|libro de (pegatinas|actividades)',
     None, 'Juguetes y bebés', 'Juguetes educativos'),
    ('Iluminación', r'interruptor termomagnetico|placa armada|extension domestica|\bapagador|\bcontacto\b|pastilla termo', r'intelig|wifi', 'Herramientas', 'Material eléctrico'),
    ('Cámaras y fotografía', r'protector (de )?lente.{0,40}(iphone|samsung|galaxy|pixel|xiaomi|celular|smartphone)|mica.{0,20}camara.{0,30}(iphone|galaxy|pixel)',
     None, 'Celulares', 'Accesorios'),
    ('Televisores', r'^(?:\S+ ){0,3}(auriculares|audifonos)', None, 'Audífonos', 'Diadema inalámbrica'),
    ('Televisores', r'barra de sonido|\bsoundbar\b', None, 'Bocinas', 'Barras de sonido'),
    ('Mascotas', r'carriola.{0,25}\bbebe\b|para bebe\b', r'perro|gato|mascota', 'Juguetes y bebés', 'Carriolas'),
    # "Otros / Varios" es en buena parte cocina y mesa (Elektra manda ahí
    # tablas, vajilla, moldes, especieros): la subcategoría fina la decide
    # el mismo repartidor de Cocina y comedor, y lo que no reconoce no se
    # mueve.
    ('Otros', r'cuchillo|tabla (de|para) (cortar|picar)|tablas? de cortar|vajilla|\bplato|\bvaso|\btaza|\btermo|botella|'
              r'\bjarra|especi(a|ero)|escurridor|bandeja|charola|cubiert(os|eria)|\bmolde|reposteria|fondant|'
              r'\bcuenco|\bbowl\b|salero|pimentero|\bsarten|\bolla|cacerola|plancha de hierro|hierro fundido|'
              r'\bcomal|tequilero|\bcopa|\bjarro|\btarro|frasco|tapas? para conservas|conservas|contenedor(es)? (de|para) (alimentos|comida)|'
              r'recipiente|tupper|hermetic|lonchera|\brallador|\bpelador|\bcolador|\bbatidor\b|\bespatula|'
              r'\bcucharon|\bpinzas? de cocina|\bmandolina\b|cortador|espiralizador|molinillo|molino de (especias|pimienta|cafe|sal)|'
              r'\bmortero|\bbascula de cocina|\bcoctel|\bshaker\b|\bhielera\b|\bdesechable|bolsas de papel|servilleta|'
              r'\bmantel|posavasos|dispensador de aceite|aceitera|vinagrera|\bazucarera|\btetera|\bcafetera de prensa|\bprensa francesa|'
              r'\bcantimplora|termica|organizador (de |para )?(cocina|especias|fregadero|refrigerador|latas|cubiertos)|estante para especias|'
              r'rejillas? de coccion|\bwok\b|\bvaporera\b|\btortillero|\bsalsera|\bensaladera|\bfrutero|\bpanera|'
              r'limpieza de (cafetera|cocina)|tabletas de limpieza|descalcificador',
     r'parrilla|asador|\bcarbon\b|para mascotas|para perros|para gatos|\bbano\b|celular|telefono|camara|'
     r'\bsilla|\bsoporte|\bcoche\b|\bauto\b|tablet|ipad|\bbuffet\b|catering|calentador|\bportavasos\b',
     'Cocina y comedor', lambda tn: sub_cocina_fino(tn), (None, 'Varios', 'Organización del hogar')),
    ('Juegos de mesa', r'piscina|acuatico|\bplaya\b|\bbalon\b|\balberca\b|water ?football|aros de buceo|resbaladilla|columpio|tobogan',
     r'rompecabezas|puzzle|juego de mesa|juego de cartas', 'Juguetes y bebés', 'Juegos de exterior'),
    ('Juegos de mesa', r'kit de (arte|manualidades|ciencia|cristales|cultivo|experimentos)|manualidades|estampilla|tatuajes|alcancia|engranajes|'
                       r'modelo (anatomico|de flor|del cuerpo|de cerebro|de esqueleto)|\besqueleto\b|\bosmo\b|set de juego de (limpieza|cocina|te|doctor)|'
                       r'\bplay-?doh\b|\bslime\b|plastilina|\bcrayola\b|pegatinas|\bstickers\b|cuaderno de actividades|libro de (pegatinas|actividades|colorear)|'
                       r'arena (sensorial|cinetica|magica)|\bmontessori\b|juguete sensorial|\bfelt fun\b|\bskillmatics\b|para colorear|\bpintura\b',
     r'rompecabezas|puzzle|juego de mesa|juego de cartas|tarjetas', 'Juguetes y bebés', 'Juguetes educativos'),
    ('Juegos de mesa', r'\bpeluche|\bmuneca|\bfigura\b|\bfiguras\b|\bfunko\b|\bplaymobil\b|\blego\b|bloques',
     r'juego de cartas|card game|juego de mesa|expansion|funkoverse|\btcg\b|rompecabezas|puzzle', 'Juguetes y bebés', lambda tn: 'Peluches' if 'peluche' in tn else ('Muñecas' if 'muneca' in tn else ('Bloques de construcción' if re.search(r'lego|bloques', tn) else 'Figuras de acción'))),
    ('Instrumentos musicales', r'\blasers?\b.{0,25}(rg|rgb|dj|alienpro|steelpro|verde|rojo|fiesta)|luces? (led )?(dj|de fiesta|robotica)|cabezas? (movil|robotica)',
     None, 'Iluminación', 'Escenario'),
    ('Herramientas', r'bomba (de aire |de pie |de piso )?(para|de) (bicicleta|bici)|foot pump.{0,30}bicicleta|inflador (para|de) (bicicleta|bici)|bomba de aire',
     r'compresor|acuario|pecera', 'Autos, bicicletas y motos', 'Bombas e infladores'),
    ('Herramientas', r'taburete|\bsilla\b|\bbanco\b (de|para) (taller|trabajo|garaje)|banco rodante', r'banco de trabajo con|prensa|escalera|escalon|peldano|fregadero|\bcarro\b|carrito', 'Muebles', 'Taburetes y bancos'),
    ('Herramientas', r'\blibrero\b|bookshelf|estante organizador.{0,30}(sala|cocina|bano|hogar)|estanteria de almacenamiento para (cocina|bano)', None, 'Muebles', 'Libreros'),
    ('Muebles', r'^(?:\S+ ){0,2}(sandalias?|chanclas?|zapat(os|illas)|tenis)\b', r'zapatera|mueble|organizador|estante|taburete|banco|\bmesa\b|sensor|cambiador', 'Calzado', lambda tn: 'Sandalias' if re.search(r'sandalia|chancla', tn) else ('Tenis' if 'tenis' in tn else 'Zapatos de vestir')),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--salida', required=True)
    ap.add_argument('--muestras', type=int, default=3)
    args = ap.parse_args()
    data = load_catalog()
    reg = {c['id']: {s['id'] for s in (c.get('subcategories') or [])} for c in data['categories']}
    grupos = collections.defaultdict(list)
    muestras = collections.defaultdict(list)
    for p in data['products']:
        tn = T(p.get('name'))
        for regla in REGLAS:
            cat, si, no, cat2, sub2 = regla[:5]
            subs = regla[5] if len(regla) > 5 else None   # subcategorías de origen a las que se limita
            if p.get('category') != cat or not re.search(si, tn) or (no and re.search(no, tn)):
                continue
            if subs is not None and p.get('subcategory') not in subs:
                continue
            s2 = sub2(tn) if callable(sub2) else sub2
            if not s2 or s2 not in reg.get(cat2, ()):
                break
            k = f"{cat} | {p.get('subcategory')} | {cat2} | {s2}"
            grupos[k].append(p['id'])
            if len(muestras[k]) < args.muestras:
                muestras[k].append((p.get('name') or '')[:100])
            break
    for k, ids in sorted(grupos.items(), key=lambda kv: -len(kv[1])):
        print(f"{len(ids):5d}  {k}")
        for m in muestras[k]:
            print(f"           {m}")
    print(f"\nTotal: {sum(len(v) for v in grupos.values())} fichas en {len(grupos)} grupos -> {args.salida}")
    json.dump(grupos, open(args.salida, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)


if __name__ == '__main__':
    main()
