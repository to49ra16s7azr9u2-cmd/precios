#!/usr/bin/env python3
"""Ejemplos de clasificación verificados a mano, para que los modelos crezcan.

POR QUÉ (25-sep-2026, noche)
----------------------------
Los modelos del catálogo (el bayesiano de detectar_mal_clasificados.py, que
usan reclasificar_hibrido.py, reaplicar_reglas.py y partir_genericas.py) se
entrenan con el catálogo tal como está: aprenden de lo bien puesto y de lo
mal puesto por igual, y nunca de lo que se revisó a mano. El usuario pidió
que el modelo de clasificación crezca en cada vuelta.

Cada vez que se revisa una muestra (un grupo aprobado para mover, o uno
rechazado) sus fichas quedan acá como verdad: la aprobada con su destino, la
rechazada con la categoría en que ya estaba. Los modelos las suman al
entrenar con PESO veces el peso de una ficha cualquiera. La lista solo
crece: cada revisión la hace más grande.

Formato: data/ejemplos-verificados.jsonl, una línea por ejemplo:
    {"nombre": ..., "cat": ..., "sub": ... o null, "fuente": ..., "fecha": ...}

USO
---
    import ejemplos_verificados as EV
    EV.agregar([{"nombre": "...", "cat": "...", "sub": "..."}], fuente="revisión X")
    for ej in EV.cargar(): ...
    python3 scripts/ejemplos_verificados.py            # cuántos hay, por categoría
"""
import collections
import datetime
import io
import json
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(AQUI)
RUTA = os.path.join(ROOT, "data", "ejemplos-verificados.jsonl")
PESO = 5


def cargar():
    if not os.path.exists(RUTA):
        return []
    with io.open(RUTA, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def agregar(ejemplos, fuente, fecha=None):
    """Suma ejemplos (sin repetir nombre+cat+sub). Devuelve cuántos entraron."""
    ya = {(e["nombre"], e["cat"], e.get("sub")) for e in cargar()}
    fecha = fecha or datetime.date.today().isoformat()
    n = 0
    with io.open(RUTA, "a", encoding="utf-8") as f:
        for e in ejemplos:
            k = (e["nombre"], e["cat"], e.get("sub"))
            if k in ya or not e.get("nombre") or not e.get("cat"):
                continue
            ya.add(k)
            f.write(json.dumps({"nombre": e["nombre"], "cat": e["cat"], "sub": e.get("sub"),
                                "fuente": fuente, "fecha": fecha}, ensure_ascii=False) + "\n")
            n += 1
    return n


def main():
    ejs = cargar()
    print(f"{len(ejs):,} ejemplos verificados")
    for c, n in collections.Counter(e["cat"] for e in ejs).most_common():
        print(f"  {n:6,}  {c}")


if __name__ == "__main__":
    main()


def entrenar(modelo_cat=None, modelos_sub=None, tokens=None, peso=PESO):
    """Suma los ejemplos a un modelo bayesiano de categorías (Bayes de
    detectar_mal_clasificados.py) y, si se da, a los de subcategoría
    (dict categoría -> Bayes). Llamar ANTES de preparar()."""
    if tokens is None:
        from detectar_mal_clasificados import tokens
    n = 0
    for e in cargar():
        ts = tokens(e["nombre"])
        for _ in range(peso):
            if modelo_cat is not None:
                modelo_cat.entrenar(e["cat"], ts)
            if modelos_sub is not None and e.get("sub"):
                modelos_sub[e["cat"]].entrenar(e["sub"], ts)
        n += 1
    return n
