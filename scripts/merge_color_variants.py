"""
Consolida productos de Mercado Libre que son el mismo modelo pero se agregaron
como entradas separadas por diferir solo en color y/o condición
(nuevo vs. reacondicionado). Solo toca productos con "mlQuery" (agregados
desde el proxy de Mercado Libre) -- los productos legacy (geekbuying, etc.)
usan un campo "variants" con otro significado (enlaces por región/moneda) y
no se tocan.

Para cada grupo de productos que, tras quitarles la palabra de color y las
menciones de condición, dejan un texto idéntico (misma categoría, misma
marca), se conserva el de precio más bajo como producto principal y se le
agrega un campo "colorVariants" con el resto (color, precio, condición,
url, foto) para que la interfaz pueda mostrar pastillas de color y el
precio "Desde".

Uso: python3 merge_color_variants.py data/data.json
"""
import json
import re
import sys
import unicodedata
from collections import defaultdict

COLOR_PHRASES = [
    # (regex fragment sin acentos, minúsculas, más largo primero), nombre canónico
    ("gris espacial", "Gris espacial"),
    ("space gray", "Gris espacial"),
    ("space grey", "Gris espacial"),
    ("gris oscuro", "Gris oscuro"),
    ("azul marino", "Azul marino"),
    ("verde oliva", "Verde oliva"),
    ("rose gold", "Oro rosa"),
    ("oro rosa", "Oro rosa"),
    ("negro", "Negro"), ("negra", "Negro"), ("black", "Negro"),
    ("blanco", "Blanco"), ("blanca", "Blanco"), ("white", "Blanco"),
    ("gris", "Gris"), ("gray", "Gris"), ("grey", "Gris"),
    ("azul", "Azul"), ("blue", "Azul"), ("navy", "Azul marino"),
    ("celeste", "Celeste"),
    ("rojo", "Rojo"), ("roja", "Rojo"), ("red", "Rojo"),
    ("rosado", "Rosa"), ("rosada", "Rosa"), ("rosa", "Rosa"), ("pink", "Rosa"),
    ("amarillo", "Amarillo"), ("amarilla", "Amarillo"), ("yellow", "Amarillo"),
    ("verde", "Verde"), ("green", "Verde"),
    ("morado", "Morado"), ("morada", "Morado"), ("purpura", "Morado"),
    ("lila", "Morado"), ("lavanda", "Morado"), ("purple", "Morado"),
    ("naranja", "Naranja"), ("orange", "Naranja"),
    ("dorado", "Dorado"), ("dorada", "Dorado"), ("oro", "Dorado"), ("gold", "Dorado"),
    ("plateado", "Plata"), ("plateada", "Plata"), ("plata", "Plata"), ("silver", "Plata"),
    ("cafe", "Café"), ("marron", "Café"), ("brown", "Café"),
    ("beige", "Beige"),
    ("turquesa", "Turquesa"),
    ("coral", "Coral"),
    ("grafito", "Grafito"), ("graphite", "Grafito"),
    ("transparente", "Transparente"), ("clear", "Transparente"),
    ("multicolor", "Multicolor"),
    ("vino", "Vino"),
    ("borgona", "Vino"),
    ("medianoche", "Medianoche"), ("midnight", "Medianoche"),
    ("starlight", "Starlight"),
]
COLOR_PHRASES.sort(key=lambda x: -len(x[0]))

CONDITION_PATTERNS = [
    re.compile(r"\(?\s*reacondicionad[oa]s?\s*\)?", re.I),
    re.compile(r"\(?\s*open\s*box\s*\)?", re.I),
    re.compile(r"\(?\s*seminuevo\s*\)?", re.I),
    re.compile(r"\(?\s*semi[\s-]?nuevo\s*\)?", re.I),
    re.compile(r"\(?\s*renewed\s*\)?", re.I),
]


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def find_color_span(stripped_lower, start_from=0):
    """Busca la primera aparición (como palabra completa) de una frase de color.
    Devuelve (start, end, canonical_name) o None."""
    best = None
    for phrase, canon in COLOR_PHRASES:
        pat = r"\b" + re.escape(phrase) + r"\b"
        m = re.search(pat, stripped_lower[start_from:])
        if m:
            s, e = m.start() + start_from, m.end() + start_from
            if best is None or s < best[0]:
                best = (s, e, canon)
    return best


def strip_color_and_condition(original_title):
    """Devuelve (canonical_key, display_title_sin_color, color_canonico_o_None,
    condicion) operando sobre el texto original (preserva may/minúsculas para
    el título de exhibición) usando una copia sin acentos alineada en
    posición para encontrar los tramos a quitar."""
    stripped = strip_accents(original_title)
    stripped_lower = stripped.lower()

    color_span = find_color_span(stripped_lower)
    color_canon = None
    display = original_title
    key_text = stripped_lower

    if color_span:
        s, e, color_canon = color_span
        # Si justo antes hay "color" o "color del <palabra>", se quita también.
        prefix = stripped_lower[:s]
        m2 = re.search(r"(?:^|\s)color(?:\s+del\s+\w+)?\s*$", prefix)
        if m2:
            s = m2.start() if prefix[m2.start()] != " " else m2.start() + 1

        display = (original_title[:s] + " " + original_title[e:]).strip()
        key_text = (stripped_lower[:s] + " " + stripped_lower[e:]).strip()

    condition = "new"
    for pat in CONDITION_PATTERNS:
        m = pat.search(display)
        if m:
            condition = "refurbished"
            display = (display[:m.start()] + " " + display[m.end():]).strip()
            key_text = pat.sub(" ", key_text)
            break

    display = re.sub(r"\s{2,}", " ", display).strip(" ,-")
    key_text = re.sub(r"\s{2,}", " ", key_text).strip(" ,-")

    return key_text, display, color_canon, condition


def color_from_spec(product):
    for s in product.get("specs") or []:
        if s.get("label") == "Color" and s.get("value"):
            v = s["value"].strip()
            v_stripped = strip_accents(v).lower()
            for phrase, canon in COLOR_PHRASES:
                if phrase == v_stripped:
                    return canon
            return v.title()
    return None


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/data.json"
    d = json.load(open(path))
    products = d["products"]

    ml_products = [p for p in products if "mlQuery" in p]
    print(f"Productos de Mercado Libre: {len(ml_products)}")

    groups = defaultdict(list)
    for p in ml_products:
        title = p.get("mlQuery") or p["name"]
        brand = (p.get("brand") or "").strip()
        if brand:
            title = re.sub(r"^" + re.escape(brand) + r"\s+", "", title, flags=re.I)
        key_text, display, title_color, condition = strip_color_and_condition(title)
        spec_color = color_from_spec(p)
        color = spec_color or title_color
        group_key = (p["category"], p["brand"].strip().lower(), key_text)
        groups[group_key].append({
            "product": p,
            "display": display,
            "color": color,
            "condition": condition,
        })

    merged_count = 0
    variant_group_count = 0
    to_remove_ids = set()

    for group_key, members in groups.items():
        if len(members) < 2:
            continue

        # Deduplica por (color, condicion), quedándose con el más barato de cada combo.
        by_combo = {}
        for m in members:
            combo = (m["color"], m["condition"])
            price = m["product"]["offers"][0]["price"]
            if combo not in by_combo or price < by_combo[combo]["product"]["offers"][0]["price"]:
                by_combo[combo] = m

        combos = list(by_combo.values())
        combos.sort(key=lambda m: m["product"]["offers"][0]["price"])
        primary = combos[0]
        primary_p = primary["product"]

        # Elimina siempre los miembros del grupo que no quedaron como
        # representantes de su combo (duplicados exactos de color+condición).
        kept_ids = {m["product"]["id"] for m in combos}
        for m in members:
            if m["product"]["id"] not in kept_ids:
                to_remove_ids.add(m["product"]["id"])
                merged_count += 1

        if len(combos) == 1:
            # Solo eran duplicados exactos del mismo color/condición: no hace
            # falta colorVariants, ya se quedó el más barato como único.
            continue

        variant_group_count += 1
        color_variants = []
        for m in combos:
            o = m["product"]["offers"][0]
            color_variants.append({
                "color": m["color"],
                "condition": m["condition"],
                "price": o["price"],
                "url": o["url"],
                "photo": o.get("photo") or m["product"].get("photo"),
                "mlQuery": m["product"].get("mlQuery"),
            })
        primary_p["colorVariants"] = color_variants
        primary_p["name"] = primary["display"] or primary_p["name"]

        for m in combos[1:]:
            to_remove_ids.add(m["product"]["id"])
            merged_count += 1

    d["products"] = [p for p in products if p["id"] not in to_remove_ids]

    print(f"Grupos con variantes de color/condición: {variant_group_count}")
    print(f"Productos fusionados/eliminados: {merged_count}")
    print(f"Total de productos: {len(products)} -> {len(d['products'])}")

    json.dump(d, open(path, "w"), ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    main()
