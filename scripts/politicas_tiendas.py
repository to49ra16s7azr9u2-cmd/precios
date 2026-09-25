#!/usr/bin/env python3
"""Condiciones de compra de cada tienda: envío, meses sin intereses,
devoluciones (pedido del usuario, 26-sep-2026: «お店の評価・総額表示»).

POR QUÉ
-------
El precio del artículo solo no dice cuánto se paga: en una tienda un
cargador de $250 llega gratis y en otra paga envío. Y en México la otra
pregunta de compra es si hay meses sin intereses. Esto deja esas
condiciones en `stores` del manifiesto para que la SPA las use en el
precio total (shippingFeeInfo en js/app.js) y en la ficha de la tienda.

DE DÓNDE SALE CADA DATO
-----------------------
De lo que cada tienda publica en su propio sitio o sus términos de
promoción, revisado el VERIFICADO de abajo. Las páginas de ayuda de
Walmart, Bodega y Sam's piden una verificación anti-robot, así que las
cifras de esas tres se tomaron de sus páginas de ayuda tal como las
indexa el buscador (títulos y fragmentos oficiales). El sitio las muestra
siempre como «según la tienda» y con la fecha: cambian con las promociones.

Campos:
  envioGratisDesdeMXN  compra mínima para envío sin costo (None = no publica)
  envioSiempreGratis   True si toda compra en línea llega sin costo
  envioCostoMXN        costo típico por debajo del mínimo (None = varía)
  msi                  meses sin intereses, texto corto
  devoluciones         texto corto
  tipo                 qué clase de tienda es
  fuente               url de donde sale

USO
---
    python3 scripts/politicas_tiendas.py          # escribe en el manifiesto
"""
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import MANIFEST_PATH, COMPACT  # noqa: E402

VERIFICADO = "2026-09-26"

POLITICAS = {
    "walmart_mx": {
        "tipo": "Tienda departamental y marketplace",
        "envioGratisDesdeMXN": 299, "envioCostoMXN": None,
        "msi": "Meses sin intereses con tarjetas participantes",
        "devoluciones": "Según la política de Walmart y del vendedor",
        "fuente": "https://www.walmart.com.mx/ayuda/articulo/costos-de-envio/b69196cdd6b3406f8e5a42a1c6772fb1",
        "nota": "Celulares: $49 de envío sin importar el monto. Walmart Pass: envío sin mínimo.",
    },
    "bodega_aurrera": {
        "tipo": "Tienda de autoservicio",
        "envioGratisDesdeMXN": 299, "envioCostoMXN": None,
        "msi": None,
        "devoluciones": "Según la política de Bodega Aurrera",
        "fuente": "https://despensa.bodegaaurrera.com.mx/ayuda/articulo/envio-sin-costo-y-formas-de-pago/457a33483d8e404a8c45b5c7fc102ef9",
        "nota": "Despensa a domicilio: hasta 5 km de la tienda que surte.",
    },
    "mercadolibre": {
        "tipo": "Marketplace",
        "envioGratisDesdeMXN": 299, "envioCostoMXN": None,
        "msi": "Meses sin intereses según el vendedor y la tarjeta",
        "devoluciones": "Compra protegida de Mercado Libre",
        "fuente": "https://www.mercadolibre.com.mx/ayuda/costos-envios-gratis_3287",
        "nota": "Envío gratis desde $299 en productos nuevos.",
    },
    "elektra": {
        "tipo": "Tienda departamental y marketplace",
        "envioGratisDesdeMXN": 999, "envioCostoMXN": None,
        "msi": "Hasta 24 meses sin intereses en promociones",
        "devoluciones": "Según la política de Elektra",
        "fuente": "https://www.elektra.mx/terminos-de-promociones",
        "nota": "Envío gratis en productos de menos de 70 kg.",
    },
    "coppel": {
        "tipo": "Tienda departamental",
        "envioGratisDesdeMXN": 499, "envioCostoMXN": None,
        "msi": "Crédito Coppel y meses sin intereses con tarjetas participantes",
        "devoluciones": "30 días, en cualquier tienda Coppel",
        "fuente": "https://www.coppel.com/inf/beneficios-coppel",
        "nota": "Por debajo del mínimo, el envío cuesta entre $50 y $100.",
    },
    "sams_mx": {
        "tipo": "Club de precios (membresía)",
        "envioGratisDesdeMXN": 999, "envioCostoMXN": None,
        "msi": "Meses sin intereses con tarjetas participantes",
        "devoluciones": "Según la política de Sam's Club",
        "fuente": "https://www.sams.com.mx/ayuda/articulo/costos-de-envio/e47a8589ee1c4b5b8c7285f2e46b8bdc",
        "nota": "Membresía Plus: envío gratis sin mínimo. Hasta 32 piezas por pedido.",
    },
    "sephora_mx": {
        "tipo": "Tienda especializada (belleza)",
        "envioGratisDesdeMXN": 599, "envioCostoMXN": 80,
        "msi": None,
        "devoluciones": "Según la política de Sephora",
        "fuente": "https://www.sephora.com.mx/pages/delivery.html",
        "nota": "Promoción de envío gratis desde $599 vigente al 31-dic-2026; envío estándar $80 en CDMX.",
    },
    "marti": {
        "tipo": "Tienda especializada (deportes)",
        "envioSiempreGratis": True,
        "msi": "Hasta 18 meses sin intereses con tarjetas participantes",
        "devoluciones": "Devolución gratis en línea o en tienda",
        "fuente": "https://www.marti.mx/",
    },
}


def main():
    m = json.load(open(MANIFEST_PATH, encoding="utf-8"))
    n = 0
    for s in m.get("stores") or []:
        pol = POLITICAS.get(s["id"])
        # Lo de antes se borra primero: una condición que la tienda dejó de
        # publicar no debe quedar pegada de una corrida vieja.
        for k in ("envioGratisDesdeMXN", "envioSiempreGratis", "envioCostoMXN", "msi", "devoluciones",
                  "tipo", "fuente", "nota", "politicaVerificada"):
            s.pop(k, None)
        if not pol:
            continue
        s.update({k: v for k, v in pol.items() if v is not None})
        s["politicaVerificada"] = VERIFICADO
        n += 1
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(m, f, **COMPACT)
    print(f"condiciones de compra en {n} tiendas (verificadas {VERIFICADO})")


if __name__ == "__main__":
    main()
