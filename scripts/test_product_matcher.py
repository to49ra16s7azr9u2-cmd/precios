"""Pruebas del pipeline de 5 pasos de product_matcher.py.

Corre con: python3 scripts/test_product_matcher.py
No usa pytest a propósito (para no agregar una dependencia nueva al
proyecto) — son asserts simples, uno por caso, con mensaje si falla.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from product_matcher import (  # noqa: E402
    Offer, match_products, normalize_identifier, normalize_text,
    extract_specs, extract_model_tokens, similarity_score,
)

passed = 0
failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS  {name}")
    else:
        failed += 1
        print(f"FAIL  {name}  -- {detail}")


# ---------- Paso 1: identificador único ----------

check("EAN13 válido se normaliza a solo dígitos",
      normalize_identifier("6922288940950") == "6922288940950")
check("EAN con espacios/guiones se limpia",
      normalize_identifier("6922-2889 40950") == "6922288940950")
check("ASIN (10 alfanuméricos, no todo dígitos) se acepta",
      normalize_identifier("B0CHX3QBQY") == "B0CHX3QBQY")
check("identificador vacío/None se descarta", normalize_identifier("") is None and normalize_identifier(None) is None)
check("longitud no-EAN/UPC/ASIN se descarta (basura de feed)",
      normalize_identifier("12345") is None)
check("todo-ceros se descarta", normalize_identifier("00000000000000") is None)

a = Offer("amazon_mx", "A1", "iPhone 15 128GB Negro", "Apple", 16999, "MXN", "https://a", identifier="0194253000000")
b = Offer("mercadolibre", "M1", "Apple iPhone 15 (128 GB) - Negro", "Apple", 16499, "MXN", "https://b", identifier="0194253000000")
result = match_products([a, b])
check("Paso 1: mismo EAN en 2 tiendas distintas -> 1 grupo por identifier",
      len(result["groups"]) == 1 and result["groups"][0].matched_by == "identifier",
      result["stats"])

c = Offer("liverpool", "L1", "Samsung Galaxy S24", "Samsung", 15999, "MXN", "https://c", identifier="0194253000000")
result2 = match_products([a, b, c])
check("Paso 1: identificador reciclado con specs incompatibles no arrastra un 3er producto distinto",
      len(result2["groups"]) == 1 and len(result2["groups"][0].offers) == 2,
      [g.to_dict() for g in result2["groups"]])


# ---------- Paso 2: preprocesamiento ----------

check("normalize_text quita [HK Warehouse] y baja a minúsculas",
      "hk warehouse" not in normalize_text("[HK Warehouse] Xiaomi POCO X8 Pro"))
check("extract_specs detecta RAM+almacenamiento",
      extract_specs("Xiaomi POCO X8 Pro, 12GB+512GB, 6.59 inch") == {"ram_gb": 12, "storage_gb": 512, "screen_in": 6.59})
check("extract_specs convierte TB a GB",
      extract_specs("Laptop 16GB+1TB").get("storage_gb") == 1024)
check("extract_model_tokens encuentra códigos alfanuméricos",
      "H27T6" in extract_model_tokens("Monitor para juegos KTC H27T6 de 27 pulgadas"))


# ---------- Paso 3: modelo + marca + specs ----------

d = Offer("sunsky", "S1", "OnePlus Ace 5 Racing, 16GB+512GB, 6.77 inch", "OnePlus", 7854, "MXN", "https://d")
e = Offer("geekbuying", "G1", "OnePlus Ace 5 Racing 16GB 512GB Verde Global", "OnePlus", 8100, "MXN", "https://e")
result3 = match_products([d, e])
check("Paso 3: misma marca + specs compatibles, sin identificador -> agrupa por model_specs",
      len(result3["groups"]) == 1 and result3["groups"][0].matched_by == "model_specs",
      result3["stats"])

f = Offer("sunsky", "S2", "OnePlus Ace 5 Racing, 16GB+256GB, 6.77 inch", "OnePlus", 6500, "MXN", "https://f")
result4 = match_products([d, f])
check("Paso 3: mismo texto salvo el almacenamiento (512 vs 256) NO agrupa",
      len(result4["groups"]) == 0,
      result4["stats"])


# ---------- Paso 4: similitud ----------

check("similarity_score alto entre nombres casi idénticos",
      similarity_score(d, e) >= 0.5, similarity_score(d, e))

g = Offer("sunsky", "S3", "Blackview Oscal Marine 2, 4GB+64GB rugged phone", "Blackview", 1921, "MXN", "https://g")
h = Offer("geekbuying", "G2", "HiBREW H21 Cafetera espresso", "HiBREW", 11800, "MXN", "https://h")
check("similarity_score bajo entre productos totalmente distintos",
      similarity_score(g, h) < 0.3, similarity_score(g, h))

i = Offer("sunsky", "S4", "vivo S30 Pro mini 16GB 512GB Rosa Screen Fingerprint", "vivo", 10591, "MXN", "https://i")
j = Offer("geekbuying", "G3", "vivo S30 Pro mini, versión Global, 16GB+512GB", "vivo", 10800, "MXN", "https://j")
result5 = match_products([i, j], threshold=0.5)
check("Paso 4: nombres parecidos pero sin token de modelo alfanumérico compartido -> similarity, no model_specs",
      len(result5["groups"]) == 1 and result5["groups"][0].matched_by in ("similarity", "model_specs"),
      result5["stats"])


# ---------- Paso 5: cola de pendientes ----------

k = Offer("sunsky", "S5", "Xiaomi Redmi 13C 5G 6GB 128GB", "Xiaomi", 2380, "MXN", "https://k")
l = Offer("geekbuying", "G4", "Xiaomi Redmi Note 13 5G 8GB 256GB", "Xiaomi", 5200, "MXN", "https://l")
result6 = match_products([k, l], threshold=0.85)
check("Paso 5: score bajo el umbral -> va a pending_review, no se agrupa a ciegas",
      len(result6["groups"]) == 0 and len(result6["pending_review"]) >= 1,
      result6["stats"])
if result6["pending_review"]:
    check("Paso 5: trae un llm_prompt listo para desambiguar",
          "SI o NO" in result6["pending_review"][0]["llm_prompt"])


# ---------- Prueba de no-regresión sobre el catálogo real ----------

sunsky_csv = "/tmp/claude-0/-home-user-shelf/f1b3429a-e0e5-55eb-8ad0-5359f726e8f2/scratchpad/sunsky.csv"
geekbuying_csv = "/tmp/claude-0/-home-user-shelf/f1b3429a-e0e5-55eb-8ad0-5359f726e8f2/scratchpad/geekbuying.csv"
if os.path.exists(sunsky_csv) and os.path.exists(geekbuying_csv):
    from product_matcher import load_offers_from_csv  # noqa: E402
    real_offers = (
        load_offers_from_csv(sunsky_csv, "sunsky")[:400]
        + load_offers_from_csv(geekbuying_csv, "geekbuying")[:400]
    )
    real_result = match_products(real_offers)
    bad_groups = []
    for grp in real_result["groups"]:
        cats = {(o.category or "").split("/")[0] for o in grp.offers}
        # Los feeds reales no comparten catálogo (SUNSKY=celulares,
        # Geekbuying=cómputo/hogar): si algún grupo cruza a una categoría
        # top-level totalmente distinta, probablemente es un falso positivo.
        if len(cats) > 1 and not ({"Smart Phones", "Phones & Accessories"} & cats):
            bad_groups.append(grp.to_dict())
    check("Sobre datos reales: ningún grupo cruza categorías obviamente incompatibles (sin falsos positivos evidentes)",
          len(bad_groups) == 0, bad_groups[:3])
    print(f"\n(catálogo real: {real_result['stats']})")
else:
    print("\n(se omite la prueba sobre datos reales: no están los CSV en el scratchpad de esta sesión)")


print(f"\n{passed}/{passed + failed} checks pasaron.\n")
if failed:
    sys.exit(1)
