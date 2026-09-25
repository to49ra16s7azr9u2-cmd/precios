#!/usr/bin/env python3
"""Segunda reorganización de categorías (25-sep-2026, noche): las mudanzas que
dependen del NOMBRE de la ficha, no solo de su (categoría, subcategoría).
Las que dependen solo de eso las hace reorganizar_categorias.py --etapa2.

  - Correas de smartwatch que estaban en Joyería -> Relojes inteligentes.
  - Relojes de pared (en Joyería) -> Decoración / Relojes de pared.
  - Tapetes, cubrevolantes y fundas de asiento (en Autopartes/Interior) ->
    Autos y motos / Tapetes, fundas y parasoles: se le agregan al auto, no
    se montan.
  - Espejos de auto en Decoración/Espejos -> Autopartes.
  - Camas de Mascotas sin especie -> de perro o de gato.

Correr DESPUÉS de reorganizar_categorias.py --aplicar --etapa2. Sin --aplicar
cuenta y muestra. No toca lo corregido a mano.
"""
import argparse
import collections
import io
import json
import os
import random
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import ROOT, load_catalog, save_catalog  # noqa: E402
import clasificar_captura_perifericos as C  # noqa: E402
import reglas_nuevas as R  # noqa: E402

RX_SMARTWATCH = re.compile(r"\b(apple watch|iwatch|galaxy watch|smartwatch|smart watch|reloj inteligente|huawei (watch|band|fit)|"
                           r"mi band|xiaomi|amazfit|fitbit|garmin|redmi watch|pixel watch|fossil gen|"
                           r"\d{2} ?/ ?\d{2} ?mm)\b")
RX_AGREGADO = re.compile(r"^(\S+ ){0,2}(tapetes?|cubrevolantes?|fundas?|cubreasientos?|cubre asientos?)\b")


def destino(p, tn):
    cat, sub = p["category"], p.get("subcategory")
    if cat == "Joyería y bisutería" and sub in ("Correas para reloj", "Correas y extensibles") and RX_SMARTWATCH.search(tn):
        return "Relojes inteligentes", "Correas y extensibles"
    if cat == "Joyería y bisutería" and sub == "Relojes de bolsillo y de pared" and re.search(r"\bpared\b", tn):
        return "Decoración de hogar y jardín", "Relojes de pared"
    if cat == "Autopartes" and sub == "Interior y tapicería" and RX_AGREGADO.search(tn):
        return "Autos y motos", "Tapetes, fundas y parasoles"
    if cat == "Decoración de hogar y jardín" and sub and sub.startswith("Espejos"):
        nc = R.nueva_categoria(tn, C.sub_refaccion, C.sub_libro_fino)
        if nc and nc[0] == "Refacciones":
            return "Autopartes", R.sub_autoparte(tn) or "Carrocería, espejos y molduras"
    # Solo camas: en «Juguetes» de Mascotas hay juguetes de niño con
    # mascotas (Super Wings, kits de veterinario) que no son de perro.
    if cat == "Mascotas" and sub == "Camas" and not re.search(r"\bpeces\b|escamas", tn):
        gato = re.search(r"\bgatos?\b|\bfelin", tn)
        return "Mascotas", f"Camas para {'gato' if gato else 'perro'}"
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--muestra", type=int, default=12)
    args = ap.parse_args()
    ruta = os.path.join(ROOT, "data", "clasificacion-a-mano.json")
    candado = json.load(io.open(ruta, encoding="utf-8")) if os.path.exists(ruta) else {}
    data = load_catalog()
    grupos = collections.defaultdict(list)
    for p in data["products"]:
        if p["id"] in candado:
            continue
        d = destino(p, C.T(p.get("name") or ""))
        if d and d != (p["category"], p.get("subcategory")):
            grupos[(p["category"], p.get("subcategory"), *d)].append(p)
    random.seed(25)
    for k, v in sorted(grupos.items(), key=lambda kv: -len(kv[1])):
        print(f"{len(v):7,}  {k[0]}/{k[1]} -> {k[2]}/{k[3]}")
        for p in random.sample(v, min(args.muestra, len(v))):
            print(f"            {p['name'][:95]}")
    print(f"Total: {sum(len(v) for v in grupos.values()):,}")
    if args.aplicar:
        for (_c, _s, cat, sub), v in grupos.items():
            for p in v:
                p["category"], p["subcategory"] = cat, sub
        save_catalog(data)
        print("Guardado.")


if __name__ == "__main__":
    main()
