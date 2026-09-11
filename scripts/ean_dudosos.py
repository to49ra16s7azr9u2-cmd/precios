#!/usr/bin/env python3
"""Ofertas cuyo código de barras publicado NO identifica a lo que se vende.

EL CASO
-------
Un GTIN identifica una unidad de venta. Un paquete de N piezas tiene el
suyo, distinto al de la pieza suelta. Cuando una tienda le pega a un
multipack el código de la pieza, el código deja de servir para lo único
para lo que lo usamos -- decir "esto y aquello son el mismo producto" -- y
empieza a mentir: une un paquete de 10 con una pieza y la ficha termina
anunciando el paquete al precio de la pieza.

Ejemplo real de este catálogo, el que originó el archivo:

    Elektra, "Memoria MICRO ADATA SD UHS-I 64GB KIT 10 piezas"  $1,777
    Elektra, "Micro SD HC 64GB con adaptador SD clase 10 ADATA"    $289
    ambas publicadas con el EAN 4713435796849

El de la pieza suelta es correcto; el del kit no. Con ese código,
match_by_gtin.py le pegó al kit la oferta de Mercado Libre de UNA tarjeta
($233) y el comparador mostraba "desde $233" sobre un producto de $1,777.

POR QUÉ POR URL Y NO POR CÓDIGO
--------------------------------
El código en sí es bueno: sigue siendo el de la tarjeta suelta y ahí une
bien. Lo que hay que descartar es esa PUBLICACIÓN concreta. Descartar el
código entero tiraría una unión correcta.

QUIÉN LO USA
------------
  match_by_gtin.py  no toma esa oferta como candidata a unir
  refresh_vtex.py   no vuelve a escribirle el `ean` en cada refresco
                    (si no, el refresco de mañana deshace la separación)

Las entradas se agregan a mano, una por caso verificado. No hay detector
automático: distinguir "multipack con el código de la pieza" de "pieza con
su código" necesita leer la ficha.
"""

# url de la oferta -> por qué se descarta su `ean`
DESCARTADOS = {
    "https://www.elektra.mx/memoria-micro-adata-sd-uhs-i-64gb-kit-10-piezas-1300667957/p":
        "Kit de 10 tarjetas publicado con el EAN de una sola (4713435796849), "
        "el mismo que Elektra usa en su ficha de la pieza suelta.",

    "https://www.elektra.mx/disco-de-corte-acero-inox-makita-d-71685-4-12-pulg-50pz-1300337105/p":
        "Paquete de 50 discos publicado con el EAN 088381567510. No sabemos "
        "si ese código es el del paquete o el de un disco, y no hay manera de "
        "averiguarlo desde acá; lo que sí se comprobó es a qué lleva usarlo: "
        "el producto de catálogo de Mercado Libre al que apunta se vende por "
        "pieza desde $35, y unirlo dejaba el paquete de $929 anunciado a $35. "
        "Ante la duda no se une (ver scripts/split_multipack.py).",
}


def ean_utilizable(offer):
    """False si el `ean` de esta oferta no identifica lo que se vende."""
    return (offer.get("url") or "") not in DESCARTADOS
