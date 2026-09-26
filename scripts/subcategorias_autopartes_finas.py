#!/usr/bin/env python3
"""Autopartes en tres niveles: la pieza, no el sistema del auto (26-sep-2026).

POR QUÉ
-------
Autopartes tiene 367 mil fichas y hasta hoy se cortaba sólo por SISTEMA del
auto: «Motor y transmisión» juntaba 77,655 fichas (soportes de motor, poleas,
bandas, empaques, metales de biela...), «Suspensión y dirección» 64,308
(amortiguadores con terminales y rótulas), «Sistema eléctrico y sensores»
51,702 (39 mil sensores de todo tipo con alternadores y claxons). Quien busca
un sensor de oxígeno o una bobina no tiene dónde entrar: la subcategoría es un
cajón de decenas de miles.

Como kakaku (自動車パーツ -> エンジンパーツ -> プラグ): el sistema pasa a ser la
familia (el escalón del medio) y la subcategoría es la PIEZA. Las piezas se
eligieron por lo que de verdad hay en el catálogo (el sustantivo con el que
abren los títulos, contado el 26-sep-2026), no por un catálogo teórico.

Lo que ninguna pieza reconoce se queda en la subcategoría vieja, que sigue
existiendo con el mismo nombre (y la misma url): no hay que redirigir nada.

CÓMO SE APLICA
--------------
  * A lo nuevo: TRES_NIVELES_AUTOPARTES entra en OLA2 (subcategorias_tres_niveles.py),
    y el clasificador lo aplica con afinar_ola2() después de sub_autoparte.
  * A lo que ya está: este script (--aplicar). No respeta el candado de
    movimientos a propósito: sólo cambia la subcategoría DENTRO de la misma
    familia (la pieza de «Motor y transmisión» sigue en esa familia), que
    es justo lo que el candado quería asegurar.

USO
---
    python3 scripts/subcategorias_autopartes_finas.py            # informe
    python3 scripts/subcategorias_autopartes_finas.py --aplicar
"""
import argparse
import collections
import os
import random
import re
import sys
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

CATEGORIA = "Autopartes"

# familia (= subcategoría vieja, que queda como resto) -> [(pieza, regex)]
# Sólo piezas con cientos de fichas: una subcategoría de menos de 30 no tiene
# página propia (compresores de A/C: 20; bombas de dirección: 9 -> se quedan).
# El título se compara normalizado (minúsculas, sin acentos). Gana la pieza
# que el título nombra PRIMERO; en empate, la primera de la lista.
FINAS = {
    "Motor y transmisión": [
        ("Soportes de motor y transmisión", r"\bsoportes? (de |del )?(motor|transmision|caja)|\brepuesto soporte"),
        ("Poleas y tensores", r"\bpoleas?\b|\btensor(es)?\b"),
        ("Cadenas y kits de distribución", r"\bcadenas? (de )?(tiempo|distribucion)|\bkits? de (distribucion|tiempo)|"
                                           r"\bengranes? de (tiempo|distribucion)|\bguias? de cadena"),
        ("Bandas", r"\bbandas?\b"),
        ("Metales de biela y bancada", r"\bmetal(es)?\b"),
        ("Pistones, anillos y bielas", r"\bpiston(es)?\b|\banillos?\b|\bbielas?\b|\bmonoblock|\bciguenal"),
        ("Cuerpos de aceleración", r"\bcuerpos? (de )?aceleracion"),
        ("Inyectores y carburadores", r"\binyector(es)?\b|\bcarburador(es)?\b|\bregulador(es)? de presion|\bflauta"),
        ("Válvulas, punterías y árbol de levas", r"\bvalvulas?\b|\bpunterias?\b|\barbol(es)? de levas|"
                                                 r"\bbalancin(es)?\b|\bcabeza de motor|\bculata"),
        ("Clutch y embrague", r"\bclutch\b|\bembrague|\bcollarin|\bvolante (motor|de motor|bimasa)|"
                              r"\bplato (de )?presion|\bcilindros? (esclavo|maestro)"),
        ("Engranes, crucetas y diferencial", r"\bengranes?\b|\bcrucetas?\b|\bdiferencial|\bcardan|"
                                             r"\bconvertidor de par"),
        ("Flechas y juntas homocinéticas", r"\bflechas?\b|\bhomocinetic|\bjuntas? lado (rueda|caja)"),
        ("Empaques, juntas y retenes", r"\bempaques?\b|\bjuntas?\b|\bsellos?\b|\breten(es)?\b|\bretenedor(es)?\b"),
        ("Chicotes de acelerador y cambios", r"\bchicotes?\b|\bcables? (de )?(acelerador|selector|cambios)"),
        ("Tapones, cárter y tapas de motor", r"\btapon(es)?\b|\bcarter\b|\btapas? de (punterias|motor|valvulas)"),
    ],
    "Suspensión y dirección": [
        ("Bases y cubrepolvos de amortiguador", r"\bbases? (de |para )?(amortiguador|strut)|\bcubre ?polvos?\b|"
                                                r"\btopes?\b|\bbalero (de )?base"),
        ("Amortiguadores", r"\bamortiguador(es)?\b|\bstruts?\b|\bkit (original|deportivo) ag\b"),
        ("Terminales de dirección", r"\bterminal(es)?\b"),
        ("Rótulas", r"\brotulas?\b"),
        ("Horquillas y brazos de suspensión", r"\bhorquillas?\b|\bbrazos? (de )?(suspension|control|inferior|superior)|"
                                              r"\bbrazos?\b(?! (pitman|loco|auxiliar))"),
        ("Baleros y mazas de rueda", r"\bbaleros?\b|\bmazas?\b|\bmasas? (de )?rueda"),
        ("Resortes y muelles", r"\bresortes?\b|\bmuelles?\b|\bespiral(es)?\b"),
        ("Bujes y gomas de suspensión", r"\bbujes?\b|\bgomas?\b"),
        ("Barras estabilizadoras y bieletas", r"\bbieletas?\b|\bbarras? (estabilizadora|de torsion)|"
                                              r"\btornillos? estabilizador|\btirantes?\b"),
        ("Coples, varillas y cajas de dirección", r"\bcoples?\b|\bcremallera|\bcajas? de direccion|\bvarillas?\b|"
                                                  r"\bflector|\bbrazos? (pitman|loco|auxiliar)"),
        ("Flechas y juntas homocinéticas", r"\bflechas?\b|\bhomocinetic"),
    ],
    "Sistema eléctrico y sensores": [
        ("Sensores de estacionamiento y TPMS", r"\bsensor(es)? (de )?(estacionamiento|reversa|presion (de )?"
                                               r"(neumaticos|llantas))|\btpms\b"),
        ("Sensores de oxígeno", r"\bsensor(es)? (de )?oxigeno|\bsonda lambda"),
        ("Sensores de detonación", r"\bsensor(es)? (de )?detonacion|\bsensor ks\b"),
        ("Sensores de posición (CKP, CMP, TPS)", r"\bsensor(es)? (de )?(la )?(posicion|ckp|cmp|tps|ciguenal|arbol|"
                                                 r"acelerador|pedal)"),
        ("Sensores de presión y flujo (MAP, MAF)", r"\bsensor(es)? (de )?(presion|map|maf|flujo|masa|absoluta|ftp|aceite)"),
        ("Sensores de temperatura", r"\bsensor(es)? (de )?(temp|temperatura|aat|att|cht|ect|iat)\b"),
        ("Sensores de velocidad y ABS", r"\bsensor(es)? (de )?(velocidad|vss|abs|rueda)"),
        ("Claxon", r"\bclaxon|\bbocinas? (de )?claxon"),
        ("Válvulas IAC y de marcha mínima", r"\bvalvulas? (iac |de )?(marcha minima|control de aire)|\biac\b"),
        ("Alternadores y marchas", r"\balternador(es)?\b|\bmarchas?\b(?! minima)|\bmotor(es)? de arranque"),
        ("Bulbos, interruptores y relevadores", r"\bbulbos?\b|\binterruptor(es)?\b|\bswitch\b|\brelevador(es)?\b|"
                                                r"\breles?\b|\bfusibles?\b"),
        ("Arneses y conectores", r"\barnes(es)?\b|\bconector(es)?\b"),
    ],
    "Carrocería, espejos y molduras": [
        ("Espejos laterales", r"\bespejos?\b|\bretrovisor(es)?\b|\blunas?\b"),
        ("Manijas y chapas", r"\bmanijas?\b|\bchapas?\b|\bjaladeras?\b"),
        ("Tolvas, salpicaderas y loderas", r"\btolvas?\b|\bsalpicaderas?\b|\bloderas?\b|\bguardafangos?\b"),
        ("Defensas, fascias y parrillas", r"\bdefensas?\b|\bfacias?\b|\bfascias?\b|\bparrillas?\b|\brejillas?\b|"
                                          r"\bfrentes?\b|\bspoiler|\balerones?\b|\bestribos?\b|\banti ?impacto"),
        ("Cofres, puertas y bisagras", r"\bcofres?\b|\bpuertas?\b|\bbisagras?\b|\bcajuela|\bcompuerta|\bbatea"),
        ("Molduras y emblemas", r"\bmolduras?\b|\bemblemas?\b|\binsignias?\b"),
        ("Elevadores y cristales", r"\belevador(es)?\b|\bcristal(es)?\b|\bmedallon|\bparabrisas"),
    ],
    "Faros y luces": [
        ("Faros de niebla", r"\bfaros? (de )?niebla|\bantiniebla|\bniebla\b"),
        ("Faros", r"\bfaros?\b"),
        ("Calaveras", r"\bcalaveras?\b"),
        ("Cuartos y direccionales", r"\bcuartos?\b|\bdireccional(es)?\b"),
        ("Focos y bombillas para auto", r"\bfocos?\b|\bbombillas?\b|\bhalogenos?\b|\bxenon\b|\bhid\b"),
    ],
    "Enfriamiento y climatización": [
        # «Bomba anticongelante shark ...» es la bomba de agua, no el líquido.
        ("Bombas de agua", r"\bbombas? (de )?(agua|anticongelante)"),
        ("Depósitos de anticongelante", r"\bdepositos?\b|\brecuperador"),
        ("Tomas de agua y termostatos", r"\btomas? (de )?agua|\btermostatos?\b"),
        ("Motoventiladores y aspas", r"\bmotoventilador(es)?\b|\bventilador(es)?\b|\baspas?\b|\bfan clutch|\bclutch fan"),
        ("Radiadores y condensadores", r"\bradiador(es)?\b|\bcondensador(es)?\b|\bevaporador(es)?\b|\benfriador(es)?\b"),
        ("Mangueras y tubos de enfriamiento", r"\bmangueras?\b|\btubos?\b"),
        ("Anticongelante y refrigerante", r"\banticongelante|\brefrigerante"),
        ("Tapones de radiador", r"\btapon(es)?\b"),
    ],
    "Bujías y encendido": [
        ("Cables de bujía", r"\bcables? (de |para )?bujias?|\bjuegos? de cables"),
        ("Bobinas de encendido", r"\bbobinas?\b"),
        ("Bujías", r"\bbujias?\b"),
        ("Tapas y rotores de distribuidor", r"\btapas? (de )?distribuidor|\brotor(es)?\b|\bdistribuidor(es)?\b"),
    ],
    "Bombas": [
        ("Bombas de gasolina", r"\bgasolina\b|\bcombustible\b|\bdiesel\b"),
        ("Bombas de aceite", r"\baceite\b"),
        ("Bombas de agua", r"\bagua\b|\banticongelante"),
    ],
}

_RAMAS = {vieja: [(s, re.compile(rx)) for s, rx in ramas] for vieja, ramas in FINAS.items()}


def pieza(vieja, tn):
    """La subcategoría fina para una ficha de `vieja`, o None (se queda)."""
    mejor = None
    for sub, rx in _RAMAS.get(vieja, ()):
        m = rx.search(tn)
        if m and (mejor is None or m.start() < mejor[0]):
            mejor = (m.start(), sub)
    return mejor[1] if mejor else None


def _repartidor(vieja):
    return lambda tn, sub_vieja: pieza(vieja, tn)


# Forma de OLA2: (categoría, viejas que absorbe, lista fina, repartidor, resto).
TRES_NIVELES_AUTOPARTES = [
    (CATEGORIA, [vieja], [vieja] + [s for s, _ in ramas], _repartidor(vieja), None)
    for vieja, ramas in FINAS.items()
]

# La pieza que el repartidor de una familia puede devolver pero que vive en
# otra (las flechas salen también de «Motor y transmisión»).
_FAMILIA_DE_PIEZA = {}
for _vieja, _ramas in FINAS.items():
    for _s, _ in _ramas:
        _FAMILIA_DE_PIEZA.setdefault(_s, _vieja)
_FAMILIA_DE_PIEZA["Bombas de agua"] = "Bombas"
_FAMILIA_DE_PIEZA["Flechas y juntas homocinéticas"] = "Suspensión y dirección"


def familias(hijas_para_autos=(), resto_moto=None):
    """El escalón del medio de Autopartes: una familia por sistema del auto,
    con la subcategoría vieja (el resto) primero y sus piezas después."""
    fams = []
    for vieja in FINAS:
        miembros = [vieja] + [s for s, fam in _FAMILIA_DE_PIEZA.items() if fam == vieja]
        fams.append((vieja, miembros))
    otras = ["Para autos", "Frenos", "Filtros y aceites", "Escape", "Motores", "Limpiaparabrisas",
             "Interior y tapicería", "Llaves y cerraduras de auto"]
    ya = {m for _, ms in fams for m in ms}
    otras += [s for s in hijas_para_autos if s not in ya and s not in otras]
    fams.append(("Otras piezas para auto", otras))
    return fams


def T(s):
    # NFKD y no una tabla: también hay «Vàlvula» y «Aceleración» con otras tildes.
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s)


def main():
    from data_io import load_catalog, save_catalog
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--muestras", type=int, default=4)
    args = ap.parse_args()
    data = load_catalog()
    cambios = collections.Counter()
    quedan = collections.Counter()
    ejemplos = collections.defaultdict(list)
    for p in data["products"]:
        if p.get("category") != CATEGORIA or p.get("subcategory") not in FINAS:
            continue
        vieja = p["subcategory"]
        nueva = pieza(vieja, T(p.get("name")))
        if not nueva:
            quedan[vieja] += 1
            continue
        cambios[(vieja, nueva)] += 1
        ejemplos[(vieja, nueva)].append(p.get("name") or "")
        if args.aplicar:
            p["subcategory"] = nueva
    random.seed(7)
    for vieja in FINAS:
        tot = sum(n for (v, _), n in cambios.items() if v == vieja) + quedan[vieja]
        print(f"\n=== {vieja}: {tot:,} fichas; se quedan {quedan[vieja]:,}")
        for (v, s), n in sorted(cambios.items(), key=lambda x: -x[1]):
            if v != vieja:
                continue
            print(f"   {n:7,}  {s}")
            for e in random.sample(ejemplos[(v, s)], min(args.muestras, len(ejemplos[(v, s)]))):
                print(f"              {e[:90]}")
    print(f"\nTotal: {sum(cambios.values()):,} fichas a su pieza; {sum(quedan.values()):,} se quedan en el sistema")
    if args.aplicar and cambios:
        # Las subcategorías nuevas se registran en data.categories (lo hace
        # también sync_subcategories.py, pero así el orden sigue al de FINAS).
        cat = next(c for c in data["categories"] if c["id"] == CATEGORIA)
        existentes = {s["id"] for s in cat.get("subcategories") or []}
        icono = next((s.get("icon") for s in cat.get("subcategories") or [] if s.get("icon")), cat.get("icon"))
        for vieja, ramas in FINAS.items():
            for s, _ in ramas:
                if s not in existentes:
                    cat.setdefault("subcategories", []).append({"id": s, "name": s, "icon": icono})
                    existentes.add(s)
        save_catalog(data)
        print("Guardado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
