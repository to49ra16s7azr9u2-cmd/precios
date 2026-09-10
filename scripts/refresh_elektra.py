#!/usr/bin/env python3
"""Refresca precios (y baja lo agotado) de los productos de Elektra.

POR QUÉ HACE FALTA
------------------
Elektra es hoy la tienda dominante del catálogo -- ~76,000 de las ~88,000
ofertas guardadas -- y hasta ahora NINGUNA de ellas se podía refrescar:
refresh_prices.py cubre Mercado Libre y refresh_other_stores.py cubre
SUNSKY/theluxurycloset/GeekBuying/Glasseslit/Whirlpool. O sea que el 89%
de los precios del sitio se quedaban congelados en el momento de la
importación. Para un comparador de precios eso es justo el defecto que no
se puede tener: el usuario ve un precio en la lista, entra a la tienda, y
el precio es otro.

CÓMO
----
No se pide producto por producto (serían ~76,000 pedidos). Se re-recorren
las MISMAS categorías del importador (CATEGORY_MAP de
add_elektra_products.py) con la misma API pública de VTEX que autoriza el
robots.txt de Elektra (`Allow: /api/catalog_system/pub/products/search?fq=*`),
de a 50 productos por pedido, y se arma un mapa url -> (precio, listPrice,
disponible). Después se aplica ese mapa al catálogo. Son ~1,500 pedidos
para cubrir las 76,000 ofertas, contra 76,000 del camino ingenuo.

QUÉ SE PODA Y QUÉ NO (importante)
---------------------------------
Hay dos situaciones distintas y NO se tratan igual:

  - "visto y agotado": el producto apareció en el recorrido pero sin
    existencias o sin precio. Es una baja REAL y se poda (--no-prune lo
    desactiva).
  - "no visto": el producto no apareció en ningún lado del recorrido. Eso
    NO prueba que se haya dado de baja -- pudo cambiarse a una categoría
    que este script no recorre, o alguna página del recorrido pudo fallar.
    Podar por esto podría borrar decenas de miles de productos por un
    recorrido incompleto, así que por defecto NO se poda: se informa y hay
    que pedirlo expresamente con --prune-missing.

Además, si el recorrido junta mucho menos de lo esperado (ver
MIN_WALK_RATIO) el script se planta y no escribe nada: es la señal de que
la API respondió mal, no de que Elektra se quedó sin catálogo.

YA ES UN ATAJO
--------------
Desde que hay más tiendas VTEX (Chedraui, Martí; ver vtex_stores.py) la
lógica vive en refresh_vtex.py, que es exactamente esto con la tienda como
parámetro. Este archivo equivale a `refresh_vtex.py --store elektra`, para
que el workflow y la documentación que lo nombran sigan valiendo.

USO
---
    python3 scripts/refresh_elektra.py --dry-run
    python3 scripts/refresh_elektra.py
    python3 scripts/refresh_elektra.py --no-prune
    python3 scripts/refresh_elektra.py --limit-categories 3   # prueba rápida
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from refresh_vtex import main as _main  # noqa: E402


def main():
    _main(["--store", "elektra"] + sys.argv[1:])


if __name__ == "__main__":
    main()
