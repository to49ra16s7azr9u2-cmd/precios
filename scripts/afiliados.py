"""Los enlaces de afiliado de cada tienda, en un solo lugar.

POR QUÉ
-------
Hasta ahora cada importador recibía su enlace por la línea de comandos
(--affiliate-base) y no quedaba escrito en ningún lado. Eso significa que el
enlace vive en la memoria de quien corrió el comando: al reimportar una tienda
meses después hay que volver a buscarlo en el panel de Admitad, y si se olvida,
la importación entra sin afiliado y no se nota hasta que alguien revisa las
urls guardadas.

Este módulo es ese lugar. Los enlaces que ya estaban en uso se recuperaron de
las urls guardadas en el catálogo (la parte anterior a ?ulp=), así que son los
mismos que se vienen usando, no unos nuevos.

CÓMO SE USA
-----------
    from afiliados import base_de
    url = url_afiliado(base_de("aliexpress"), url_de_la_tienda)

Los importadores siguen aceptando --affiliate-base; lo que se pase por ahí
gana sobre lo que diga este archivo, para poder probar un enlace nuevo sin
tocar código.

AMAZON VA APARTE
----------------
Amazon no envuelve la url: le agrega ?tag=. Eso lo arma affiliate_url() en
add_amazon_offers.py con TAG_AMAZON, que está acá abajo por completitud.

QUÉ NO ESTÁ ACÁ
---------------
Las tiendas sin programa aprobado todavía. Se dejan nombradas y en None a
propósito: así se ve de un vistazo qué falta, en vez de que la ausencia de una
clave se confunda con un olvido.
"""

TAG_AMAZON = "comparamex0d-20"

# storeId -> enlace base de Admitad, o None si todavía no hay programa.
BASES = {
    # --- aprobados y en uso -------------------------------------------------
    "alibaba":    "https://rzekl.com/g/pm1aev55cl43517c81ee219aa26f6f/",
    "aliexpress": "https://rzekl.com/g/1e8d11449443517c81ee16525dc3e8/",
    "geekbuying": "https://bywiola.com/g/78tuvzaw8k43517c81ee0267b86f6e/?f_id=19717",
    "molnija":    ("https://rzekl.com/g/h8f6ydwll243517c81ee26e097ca3d/"
                   "?erid=MvGzQC98w3Z1gMq1owpZAzT3&f_id=25405"),
    "motorola":   "https://qbzdl.com/g/1unk9900kb43517c81eeb708316999/?f_id=25850",
    "sunsky":     "https://dorinebeaumont.com/g/7npkd4cs1i43517c81ee869a299fda/?f_id=15762",
    "whirlpool":  "https://rzekl.com/c/hkjqq2fi8q43517c81ee82ed2bb6aa/",
    "woodestic":  "https://naiawork.com/g/do86ucnzhx43517c81eec586cc6aee/?f_id=26480",
    "sharkninja": "https://qbzdl.com/g/q0sfihl3xd43517c81eefd1d6a8d3c/",

    # --- aprobado, pero sin productos en el catálogo ------------------------
    # Shopee cerró su operación local en México en 2022 y desde entonces vende
    # cross-border. El enlace funciona (redirige a shopee.com.mx con los
    # parámetros de tracking), pero su API contesta 403 con el error 90309999
    # a cualquier lectura automática, así que todavía no hay de dónde sacar
    # los productos. El enlace queda anotado para cuando lo haya.
    "shopee": "https://zallj.com/g/qy94wfbelw43517c81ee6e79f7c2cd/",

    # --- solicitado, esperando moderación -----------------------------------
    # Vevor (Admitad, "Vevor Many GEOs"): 5% de comisión, pago a 47 días, 3% de
    # conversión y 86% de confirmación. Todavía no es una tienda del catálogo:
    # sus 149 productos entran hoy por Amazon, Mercado Libre y Elektra. Si el
    # programa se aprueba, vevor.com.mx pasa a ser tienda propia y esos
    # productos ganan una segunda oferta con la que compararse.
    "vevor": None,

    # --- con programa confirmado, en espera a propósito ---------------------
    # Elektra y Coppel piden vistas mensuales en la solicitud, así que se
    # posponen hasta que el sitio tenga tráfico que reportar. No es un olvido:
    # solicitar con cifras flojas quema el intento, y Elektra es la tienda más
    # grande del catálogo (69,875 ofertas, 38% del total).
    "elektra": None,  # Admitad: /store/offers/elektra-mx/
    "coppel":  None,  # Admitad: /store/offers/coppel-mx/ -- aún sin productos

    # --- con programa confirmado, falta solicitarlo -------------------------
    "miniso":       None,  # Admitad: /store/offers/miniso-mx/
    "mercadolibre": None,  # programa propio, alta por cuenta propia

    # --- sin programa encontrado hasta hoy ----------------------------------
    "chedraui": None,
    "gandhi": None,
    "juguetron": None,
    "marti": None,
    "doto": None,
    "maskota": None,
    "fantasias_miguel": None,
    "refacciones_originales": None,
}


def base_de(store_id):
    """El enlace de la tienda, o None si no tiene programa todavía."""
    return BASES.get(store_id)
