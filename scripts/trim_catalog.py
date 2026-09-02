#!/usr/bin/env python3
"""Quita del catálogo los campos que no aportan información: los que valen
su default en (casi) todo el catálogo y la foto repetida.

POR QUÉ
-------
El SPA descarga TODO el catálogo al abrir. Midiendo el estado antes de este
script: 80.6 MB en crudo (7.6 MB con gzip), 1.27 s solo de JSON.parse en
escritorio y 254 MB de heap -- en un Android de gama baja eso es una pestaña
que se cae. Al mirar qué ocupaba ese peso, buena parte no era información:

  - `photo` estaba repetida en el producto y en su oferta en 87,213 de
    87,228 productos (el 100%): ~9.7 MB de strings idénticas.
  - `reviews: []` vacío en los 87,228 productos.
  - `points` y `rating` valían null y `reviewCount` 0 en el 100% de las
    ofertas; `sellerCount`/`shippingFee` null y `verified` false en ~90%.

Nada de eso se pierde al borrarlo: quien lo lee ya usa un default
equivalente (ver los .get()/|| en generate_seo_pages.py y js/app.js).

QUÉ NO SE TOCA
--------------
`stock` se conserva aunque el 90.7% valga "in_stock". Ahí el default NO es
equivalente: el código distingue a propósito "sin stock informado"
(o.stock == null -> puntúa 0.5, neutro) de "in_stock" (puntúa 1), y borrarlo
haría que toda oferta con stock confirmado pasara a contar como
desconocida, cambiando el orden de "mejor opción" y quitando su distintivo.

Es idempotente y conviene correrlo después de cada importación o refresco
(esos scripts vuelven a escribir los defaults).

USO
---
    python3 scripts/trim_catalog.py --dry-run
    python3 scripts/trim_catalog.py
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog  # noqa: E402

# Campo de la oferta -> valor que se considera "sin información". Si el campo
# vale exactamente eso, se borra. `stock` NO está acá a propósito (ver
# encabezado).
OFFER_DEFAULTS = {
    "points": None,
    "rating": None,
    "reviewCount": 0,
    "sellerCount": None,
    "lowestPrice": None,
    "shippingFee": None,
    "listPrice": None,
    "verified": False,
    "sellers": None,
}


def trim(products):
    stats = {k: 0 for k in OFFER_DEFAULTS}
    stats["reviews"] = 0
    stats["photo_oferta"] = 0
    for p in products:
        if p.get("reviews") == []:
            del p["reviews"]
            stats["reviews"] += 1
        photo = p.get("photo")
        for o in p.get("offers") or []:
            for field, default in OFFER_DEFAULTS.items():
                if field in o and o[field] == default:
                    del o[field]
                    stats[field] += 1
            # La foto de la oferta solo se borra si es EXACTAMENTE la del
            # producto; cuando difiere (variantes de color) es información
            # real y se queda.
            if photo and o.get("photo") == photo:
                del o["photo"]
                stats["photo_oferta"] += 1
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = load_catalog()
    before = len(json.dumps(data["products"], ensure_ascii=False))
    stats = trim(data["products"])
    after = len(json.dumps(data["products"], ensure_ascii=False))

    print(f"Productos: {len(data['products'])}\n")
    print("Campos borrados:")
    for k, v in sorted(stats.items(), key=lambda kv: -kv[1]):
        if v:
            print(f"  {k:<16} {v:>8}")
    print(f"\nJSON en memoria: {before / 1048576:.1f} MB -> {after / 1048576:.1f} MB "
          f"({100 * (before - after) / before:.0f}% menos)")

    if args.dry_run:
        print("\n(--dry-run: no se escribió nada)")
        return
    save_catalog(data)
    print("\nCatálogo actualizado.")


if __name__ == "__main__":
    main()
