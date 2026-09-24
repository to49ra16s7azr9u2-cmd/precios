#!/usr/bin/env python3
"""Tercer juez de la clasificación: los vecinos más parecidos del catálogo.

POR QUÉ
-------
El modelo del catálogo (Bayes, reclasificar_hibrido.py / ModeloCatalogo) mira
la categoría entera: suma las palabras del título contra el vocabulario de
cada categoría. Se equivoca de una forma típica: las categorías grandes con
mucho vocabulario técnico atraen lo que no es suyo -- tabletas, NAS, consolas
portátiles y mini PC acababan en Laptops por «8 GB RAM», «SSD», «Intel».

Los vecinos miran otra cosa: cuáles son las 25 fichas más parecidas a ESTA
(por las palabras poco comunes que comparten, pesadas por lo raras que son) y
en qué categoría están. Una tableta se parece a otras tabletas aunque comparta
«8 GB RAM» con mil laptops.

Medido el 24-sep-2026 contra las fichas del candado manual (lo movido a mano,
que es la referencia), en los cambios que el modelo propone con 16 nats o más
sobre la regla:
    sólo el modelo:              87% a lo correcto, 9% estropea
    modelo + vecinos (>= 50%):   93% a lo correcto, 6% estropea
Con márgenes menores los vecinos ayudan (50% -> 66-72%) pero no llegan al 80%,
así que no se bajó ningún umbral: los vecinos sólo filtran.

USO
---
    v = Vecinos(productos)
    v.respalda(nueva, actual, pid=pid)            # ficha del catálogo (se excluye a sí misma)
    v.respalda(nueva, actual, titulo="...")       # título nuevo (captura)
"""
import collections
import math

from detectar_mal_clasificados import tokens

K = 25
MAX_DF = 4000          # palabras en más fichas que esto no distinguen nada
MIN_VOTO = 0.5


class Vecinos:
    def __init__(self, productos):
        self.cat = {}
        self.ts = {}
        df = collections.Counter()
        for p in productos:
            c = p.get("category")
            if not c or c == "Otros":
                continue
            ts = tokens(p.get("name"))
            self.cat[p["id"]] = c
            self.ts[p["id"]] = ts
            df.update(ts)
        n = max(len(self.cat), 1)
        self.idf = {t: math.log(n / k) for t, k in df.items() if k <= MAX_DF}
        self.inv = collections.defaultdict(list)
        for pid, ts in self.ts.items():
            for t in ts:
                if t in self.idf:
                    self.inv[t].append(pid)

    def mas_parecidas(self, pid=None, titulo=None, k=K):
        """[(id, peso)] de las k fichas más parecidas (sin ella misma)."""
        ts = self.ts.get(pid) if titulo is None else tokens(titulo)
        sc = collections.Counter()
        for t in ts or ():
            w = self.idf.get(t)
            if w is None:
                continue
            for q in self.inv[t]:
                if q != pid:
                    sc[q] += w
        return sc.most_common(k)

    def votos(self, pid=None, titulo=None):
        """{categoría: fracción del peso} entre los K vecinos más parecidos."""
        v = collections.Counter()
        for q, s in self.mas_parecidas(pid=pid, titulo=titulo):
            v[self.cat[q]] += s
        tot = sum(v.values()) or 1
        return {c: s / tot for c, s in v.items()}

    def respalda(self, nueva, actual, pid=None, titulo=None):
        """¿Los vecinos ponen a la ficha en `nueva` (la mitad del peso o más,
        y más que en `actual`)?"""
        v = self.votos(pid=pid, titulo=titulo)
        return v.get(nueva, 0) >= MIN_VOTO and v.get(nueva, 0) > v.get(actual, 0)
