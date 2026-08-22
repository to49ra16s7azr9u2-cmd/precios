"""
Consolida productos de Mercado Libre que son el mismo modelo pero se agregaron
como entradas separadas por diferir solo en color y/o condición
(nuevo vs. reacondicionado). Solo toca productos con "mlQuery" o
"colorVariants" (agregados/fusionados antes desde el proxy de Mercado
Libre) -- los productos legacy (geekbuying, etc.) usan un campo "variants"
con otro significado (enlaces por región/moneda) y no se tocan.

Para cada grupo de productos que, tras quitarles la palabra de color y las
menciones de condición, dejan un texto idéntico (misma categoría, misma
marca), se conserva el de precio más bajo como producto principal y se le
agrega un campo "colorVariants" con el resto (color, precio, condición,
url, foto) para que la interfaz pueda mostrar pastillas de color y el
precio "Desde".

Es seguro correr este script varias veces (p.ej. después de cada categoría
nueva): un producto que ya tiene "colorVariants" de una corrida anterior se
vuelve a agrupar usando TODAS sus variantes ya conocidas (no solo el color
que quedó como principal la vez pasada), así que una corrida nueva puede
sumarle más colores sin perder los que ya tenía.

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
    ("morado", "Morado"), ("morada", "Morado"), ("purpura", "Morado"), ("violeta", "Morado"),
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
    ("natural", "Natural"),
    ("desierto", "Desierto"), ("desert", "Desierto"),
    ("blanco estelar", "Starlight"), ("blanca estelar", "Starlight"),
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


UNIT_WORDS = r"gb|mb|tb|kg|mah|watts?|hz|kpa|pulgadas?|in"


def normalize_key(s):
    """Distintos vendedores/lotes escriben el mismo modelo con puntuación
    distinta: "iPhone 15 (128 GB) - Azul" vs "iPhone 15 128 GB Negro". Se
    quitan paréntesis, guiones y comas (dejando solo letras/números/espacios)
    para que la comparación de la clave no dependa de ese formato -- ya el
    requisito de que todos los tokens numéricos coincidan sigue intacto."""
    s = re.sub(r"[(),\-/|]", " ", s)
    # "128GB" vs "128 GB" vs "128 Gb": junta dígito+unidad sin espacio y sin
    # mayúsculas para que la variación de formato entre vendedores no rompa
    # la comparación (esto opera sobre texto ya en minúsculas).
    s = re.sub(r"(\d)\s*(" + UNIT_WORDS + r")\b", r"\1\2", s, flags=re.I)
    return re.sub(r"\s{2,}", " ", s).strip()


def find_color_span(stripped_lower, start_from=0):
    """Busca la ÚLTIMA aparición (como palabra completa) de una frase de
    color. Devuelve (start, end, canonical_name) o None.

    Se prefiere la última en vez de la primera porque varios títulos de
    Mercado Libre repiten una palabra de color como parte del NOMBRE DEL
    MODELO antes del color real de venta, p.ej. "Redragon Dragonborn White
    K630-pd Teclado Negro" -- "White" es parte del modelo (todas las
    variantes de color se llaman igual), "Negro" es el color que de verdad
    se está vendiendo, y va al final. Tomar la primera aparición quitaba
    "White" y dejaba "Negro" pegado en el texto, así que dos anuncios del
    mismo teclado en distinto color no coincidían."""
    best = None
    for phrase, canon in COLOR_PHRASES:
        pat = r"\b" + re.escape(phrase) + r"\b"
        for m in re.finditer(pat, stripped_lower[start_from:]):
            s, e = m.start() + start_from, m.end() + start_from
            if best is None or s > best[0]:
                best = (s, e, canon)
    return best


def normalize_bare_gb(original_title):
    """"256G" como abreviación de "256GB" (común en celulares Samsung/Xiaomi
    importados) se escribe indistintamente con o sin la "B" final -- sin
    normalizar, "Galaxy S25 Ultra 256gb Titanium Black" y "...256G Titanium
    Gray" quedan con distinta clave de agrupación y no se fusionan como
    variantes del mismo modelo. Se exige "G" mayúscula específicamente (no
    "g" minúscula, que casi siempre son gramos de peso, p.ej. "172 g") para
    no confundir ambos casos -- por eso esto corre ANTES de bajar a
    minúsculas en el resto del pipeline, mientras el mayúsculas/minúsculas
    original todavía se puede distinguir."""
    return re.sub(r"(?<=\d)G(?=\s|$|[^a-zA-Z])", "GB", original_title)


def strip_color_and_condition(original_title):
    """Devuelve (canonical_key, display_title_sin_color, color_canonico_o_None,
    condicion) operando sobre el texto original (preserva may/minúsculas para
    el título de exhibición) usando una copia sin acentos alineada en
    posición para encontrar los tramos a quitar."""
    original_title = normalize_bare_gb(original_title)
    stripped = strip_accents(original_title)
    stripped_lower = stripped.lower()

    color_span = find_color_span(stripped_lower)
    color_canon = None
    display = original_title
    key_text = stripped_lower

    if color_span:
        s, e, color_canon = color_span

        # Algunos vendedores encadenan dos palabras de color para el mismo
        # tono (p.ej. "Morado Color Violeta", donde "morado" y "violeta"
        # son sinónimos del mismo color pero AMBOS aparecen en el título,
        # o "Negro Space Gray"). find_color_span ya se quedó con la última
        # ("violeta"); acá se sigue quitando hacia atrás -- primero un
        # conector "color"/"color del X" si hay, después cualquier otra
        # palabra de color que quede pegada justo al final de lo que
        # sobra -- hasta que no quede ninguna. Así la clave de agrupación
        # no se queda con un "morado" suelto que no coincide con el resto
        # de las variantes del mismo modelo.
        while True:
            m2 = re.search(r"(?:^|\s)color(?:\s+del\s+\w+)?\s*$", stripped_lower[:s])
            if m2:
                s = m2.start() + (1 if stripped_lower[m2.start()] == " " else 0)
            trailing_color = next(
                (m for phrase, _ in COLOR_PHRASES
                 if (m := re.search(r"\b" + re.escape(phrase) + r"\s*$", stripped_lower[:s]))),
                None,
            )
            if not trailing_color:
                break
            s = trailing_color.start()

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


def entries_for(p):
    """Todas las variantes (color, condición, precio, url, foto, mlQuery) que
    representa hoy este producto de nivel superior: si ya viene de una
    fusión anterior, sus colorVariants; si no, su única oferta actual."""
    if p.get("colorVariants"):
        return [dict(v) for v in p["colorVariants"]]
    title = p.get("mlQuery") or p["name"]
    _, display, title_color, condition = strip_color_and_condition(title)
    color = color_from_spec(p) or title_color
    o = p["offers"][0]
    return [{
        "color": color,
        "condition": condition,
        "price": o["price"],
        "url": o["url"],
        "photo": o.get("photo") or p.get("photo"),
        "mlQuery": title,
    }]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/data.json"
    d = json.load(open(path))
    products = d["products"]

    candidates = [p for p in products if "mlQuery" in p or p.get("colorVariants")]
    print(f"Productos de Mercado Libre: {len(candidates)}")

    groups = defaultdict(list)
    for p in candidates:
        title = p.get("mlQuery") or p["name"]
        brand = (p.get("brand") or "").strip()
        if brand:
            title = re.sub(r"^" + re.escape(brand) + r"\s+", "", title, flags=re.I)
        key_text, _, _, _ = strip_color_and_condition(title)
        group_key = (p["category"], brand.lower(), normalize_key(key_text))
        groups[group_key].append(p)

    merged_count = 0
    variant_group_count = 0
    to_remove_ids = set()

    for group_key, members in groups.items():
        if len(members) < 2:
            continue

        all_entries = []
        for p in members:
            all_entries.extend(entries_for(p))

        # Deduplica por (color, condicion), quedándose con el más barato de cada combo.
        by_combo = {}
        for e in all_entries:
            combo = (e["color"], e["condition"])
            if combo not in by_combo or e["price"] < by_combo[combo]["price"]:
                by_combo[combo] = e

        combos = sorted(by_combo.values(), key=lambda e: e["price"])
        primary_entry = combos[0]

        # El producto de nivel superior que sobrevive es el que ya representa
        # (por url) la variante más barata; si esa variante viene de un
        # colorVariants existente y no de ningún miembro directo, se usa el
        # primer miembro como contenedor y se le sobrescribe la oferta.
        primary_p = next(
            (p for p in members if any(o.get("url") == primary_entry["url"] for o in p["offers"])),
            members[0],
        )
        for p in members:
            if p is not primary_p:
                to_remove_ids.add(p["id"])
                merged_count += 1

        primary_p["offers"][0]["price"] = primary_entry["price"]
        primary_p["offers"][0]["url"] = primary_entry["url"]
        primary_p["offers"][0]["photo"] = primary_entry.get("photo")
        primary_p["mlQuery"] = primary_entry.get("mlQuery") or primary_p.get("mlQuery")
        _, display, _, _ = strip_color_and_condition(
            re.sub(r"^" + re.escape((primary_p.get("brand") or "").strip()) + r"\s+", "",
                   primary_entry.get("mlQuery") or primary_p["name"], flags=re.I)
        )
        primary_p["name"] = display or primary_p["name"]

        if len(combos) == 1:
            primary_p.pop("colorVariants", None)
            continue

        variant_group_count += 1
        primary_p["colorVariants"] = combos

    d["products"] = [p for p in products if p["id"] not in to_remove_ids]

    print(f"Grupos con variantes de color/condición: {variant_group_count}")
    print(f"Productos fusionados/eliminados: {merged_count}")
    print(f"Total de productos: {len(products)} -> {len(d['products'])}")

    json.dump(d, open(path, "w"), ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    main()
