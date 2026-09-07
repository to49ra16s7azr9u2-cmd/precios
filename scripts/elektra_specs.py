#!/usr/bin/env python3
"""Ficha técnica de un producto de Elektra, a partir de su JSON de VTEX.

POR QUÉ
-------
La API pública de VTEX que ya recorremos todos los días
(refresh_elektra.py) devuelve `allSpecifications`: la ficha técnica
completa que la tienda publica, campo por campo. No se estaba leyendo.

El efecto de no leerla se mide: 75,312 de los 81,603 productos del
catálogo (92%) no tienen NINGUNA especificación, y las categorías más
grandes -- Herramientas (7,268), Refacciones (5,308), Joyería (4,569) --
no tienen un solo filtro ni bloque de "Compara calidad", porque del
nombre no se puede sacar nada confiable. La tienda sí lo tiene
estructurado.

No cuesta un pedido más: la misma respuesta que ya se descarga trae los
campos; se estaban tirando.

QUÉ SE GUARDA Y QUÉ NO
----------------------
Todo lo que la tienda declare, MENOS:

  - Texto de marketing: "Customer Bennefits 1..4" son frases de folleto
    ("Con iluminación LED que te permite visualizar tus alimentos"), no
    datos comparables.
  - Códigos internos: Sapcategory, CBT, Bonoderegalo, "Atributos
    generales" -- identificadores del ERP de la tienda que no significan
    nada para quien compra.
  - Valores largos: por encima de MAX_VALOR son descripciones, no
    especificaciones. Se descartan en vez de recortarlas a la mitad de
    una frase.
  - Campos vacíos, o con más de un valor: dos valores para el mismo campo
    no se resuelven eligiendo uno.

Y se topa en MAX_SPECS campos, porque una ficha con 40 renglones no se
lee -- y porque el catálogo lo baja el navegador.
"""
import re

# Ruido conocido, medido sobre 4,632 productos de 23 categorías.
RUIDO = {
    "sapcategory", "cbt", "bonoderegalo", "atributos generales",
    # Duplica "Garantía con Proveedor", que viene en un formato legible
    # ("1 Año") en vez de un número suelto.
    "meses de garantía",
}
RUIDO_PREFIJOS = ("customer bennefit", "customer benefit")

MAX_VALOR = 80
MAX_SPECS = 16

_ESPACIOS = re.compile(r"\s+")


def _limpia(v):
    return _ESPACIOS.sub(" ", str(v)).strip()


def specs_from(vtex_product):
    """[{"label", "value"}] de la ficha técnica, o [] si no trae nada útil."""
    out = []
    for campo in vtex_product.get("allSpecifications") or []:
        nombre = _limpia(campo)
        bajo = nombre.lower()
        if bajo in RUIDO or bajo.startswith(RUIDO_PREFIJOS):
            continue
        valores = vtex_product.get(campo)
        if not isinstance(valores, list) or len(valores) != 1:
            continue
        valor = _limpia(valores[0])
        if not valor or len(valor) > MAX_VALOR:
            continue
        # "Sí"/"No" a secas informan poco por sí solos, pero en contexto sí
        # ("Despachador de Agua: Sí"), así que se conservan.
        out.append({"label": nombre, "value": valor})
        if len(out) >= MAX_SPECS:
            break
    return out
