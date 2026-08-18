"""Algoritmo de "product matching": une el mismo producto físico publicado
por distintas tiendas/fuentes (SUNSKY, Geekbuying, un futuro feed de
Mercado Libre, etc.) en un solo grupo, para que ComparaMX pueda mostrar una
comparación de precios real entre tiendas en vez de un producto por tienda.

Implementa el flujo de 5 pasos:

  Paso 1  Coincidencia exacta de identificador único (JAN/EAN/ASIN/barcode)
  Paso 2  Preprocesamiento de texto (limpieza de ruido, extracción de
          modelo/specs)
  Paso 3  Coincidencia de modelo + marca + specs clave
  Paso 4  Similitud de texto (Jaccard de tokens + similitud de caracteres,
          como sustituto sin dependencias de una comparación por embeddings)
  Paso 5  Cola de pendientes: candidatos por debajo del umbral, para
          revisión manual o para mandarle un prompt a un LLM

Uso como script (con las fuentes ya descargadas en un directorio):

    python3 scripts/product_matcher.py sunsky.csv:sunsky geekbuying.csv:geekbuying

Uso como librería:

    from product_matcher import Offer, match_products
    result = match_products(offers)
    result["groups"], result["pending_review"]
"""

from __future__ import annotations

import csv
import difflib
import json
import re
import sys
from dataclasses import dataclass, field
from typing import Optional


# ---------- Paso 1: identificador único ----------

def normalize_identifier(raw: Optional[str]) -> Optional[str]:
    """Normaliza un JAN/EAN/UPC/ASIN/barcode para comparar exacto.

    Solo se queda con dígitos (o el ASIN alfanumérico tal cual, en
    mayúsculas). Un identificador vacío, todo-ceros o de longitud
    sospechosa (ni 8/12/13/14 dígitos EAN/UPC ni 10 caracteres ASIN) se
    descarta: es más seguro no usarlo que arriesgar un falso positivo por
    basura en el feed de origen.
    """
    if not raw:
        return None
    raw = raw.strip()
    if not raw:
        return None
    if re.fullmatch(r"[A-Z0-9]{10}", raw) and not raw.isdigit():
        return raw.upper()  # ASIN
    digits = re.sub(r"\D", "", raw)
    if len(digits) in (8, 12, 13, 14) and not set(digits) == {"0"}:
        return digits
    return None


# ---------- Paso 2: preprocesamiento de texto ----------

# Ruido común en nombres de catálogos de afiliados: región de almacén,
# "Global"/"EU Plug"/etc, corchetes/paréntesis vacíos de marketing.
_NOISE_PATTERNS = [
    r"\[[^\]]*warehouse[^\]]*\]",
    r"\bglobal\b",
    r"\beu\s*plug\b",
    r"\bus\s*plug\b",
    r"\buk\s*plug\b",
    r"\bnew\b",
    r"\bversion\b",
]
_NOISE_RE = re.compile("|".join(_NOISE_PATTERNS), re.IGNORECASE)
# El "+" también se limpia (no solo la puntuación general): distintas
# tiendas escriben "16GB+512GB" o "16GB 512GB" para lo mismo, y para
# comparar tokens de contenido (Paso 4) ambas formas deben tokenizar igual.
# extract_specs() ya extrajo esa spec del texto crudo antes de esta
# limpieza, así que no se pierde información.
_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_WS_RE = re.compile(r"\s+")

# Specs frecuentes en electrónica: RAM+almacenamiento ("16GB+512GB"),
# pantalla ("6.77 inch" / "6.77\""), Hz de refresco, capacidad simple
# ("64GB", útil para consolas/almacenamiento suelto).
# Distintas tiendas escriben RAM+almacenamiento con "+" (SUNSKY: "16GB+512GB")
# o solo con espacio (otros feeds: "16GB 512GB"): se aceptan ambas formas,
# exigiendo que los dos números vayan pegados uno al otro (sin texto entre
# medio) para no capturar dos menciones de "GB" que no tengan relación.
_RAM_STORAGE_RE = re.compile(r"(\d+)\s*GB\s*[+/]?\s*(\d+)\s*(GB|TB)\b", re.IGNORECASE)
_SCREEN_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:inch|\"|pulgadas)", re.IGNORECASE)
_HZ_RE = re.compile(r"(\d+)\s*Hz", re.IGNORECASE)
_STORAGE_ONLY_RE = re.compile(r"\b(\d+)\s*(GB|TB)\b", re.IGNORECASE)
# Tokens tipo "código de modelo": letras+dígitos pegados (H27T6, B8745HS,
# GT8, X8) — no intenta ser exhaustivo, es una señal más entre varias.
_MODEL_TOKEN_RE = re.compile(r"\b(?=[A-Za-z]*\d)(?=\d*[A-Za-z])[A-Za-z0-9]{2,10}\b")

_STOPWORDS = {
    "de", "con", "para", "the", "and", "y", "a", "en", "un", "una",
    "inch", "pulgadas", "color", "network", "support", "black", "white",
}


def normalize_text(name: str) -> str:
    """Limpieza básica de ruido antes de comparar (Paso 2)."""
    s = _NOISE_RE.sub(" ", name)
    s = _PUNCT_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip().lower()
    return s


def extract_specs(name: str) -> dict:
    """Extrae specs estructuradas del nombre/título crudo (Paso 2/3)."""
    specs: dict = {}
    m = _RAM_STORAGE_RE.search(name)
    if m:
        ram, storage, unit = m.groups()
        storage_gb = int(storage) * (1024 if unit.upper() == "TB" else 1)
        specs["ram_gb"] = int(ram)
        specs["storage_gb"] = storage_gb
    else:
        m2 = _STORAGE_ONLY_RE.search(name)
        if m2:
            amount, unit = m2.groups()
            specs["storage_gb"] = int(amount) * (1024 if unit.upper() == "TB" else 1)
    m = _SCREEN_RE.search(name)
    if m:
        specs["screen_in"] = round(float(m.group(1)), 2)
    m = _HZ_RE.search(name)
    if m:
        specs["refresh_hz"] = int(m.group(1))
    return specs


def extract_model_tokens(name: str) -> set[str]:
    """Tokens candidatos a "código de modelo" (Paso 3). Cubre dos formas
    comunes de nombrar un modelo: pegado en un solo token alfanumérico
    (H27T6, B8745HS) y separado por espacio (Ace 5, Galaxy S24) — para esto
    último se unen pares de palabras adyacentes letra+número/número+letra.
    Los números que ya son parte de una spec conocida (RAM/almacenamiento/
    pantalla/Hz) se quitan antes, para no generar ruido con esos."""
    clean = _NOISE_RE.sub(" ", name)
    tokens = {t.upper() for t in _MODEL_TOKEN_RE.findall(clean)}

    spec_free = _RAM_STORAGE_RE.sub(" ", clean)
    spec_free = _STORAGE_ONLY_RE.sub(" ", spec_free)
    spec_free = _SCREEN_RE.sub(" ", spec_free)
    spec_free = _HZ_RE.sub(" ", spec_free)
    words = re.findall(r"[A-Za-z]+|\d+", spec_free)
    for w1, w2 in zip(words, words[1:]):
        if w1.isalpha() and w2.isdigit() and len(w2) <= 3 and len(w1) >= 2:
            tokens.add((w1 + w2).upper())
        elif w1.isdigit() and w2.isalpha() and len(w1) <= 3 and len(w2) >= 2:
            tokens.add((w1 + w2).upper())
    return tokens


def _content_tokens(normalized_name: str) -> set[str]:
    return {t for t in normalized_name.split() if t not in _STOPWORDS and len(t) > 1}


# ---------- Paso 4: similitud de texto ----------

def similarity_score(a: "Offer", b: "Offer") -> float:
    """Similitud combinada [0,1]: Jaccard de tokens de contenido (mitad del
    puntaje) + similitud de caracteres tipo difflib (la otra mitad). Es un
    sustituto sin dependencias de comparar embeddings — más barato y sin
    necesitar una API externa, a costa de ser más literal (no capta
    sinónimos). Si en el futuro hay una API de embeddings disponible,
    reemplazar solo esta función basta: el resto del pipeline no cambia.
    """
    tokens_a = _content_tokens(a.normalized_name)
    tokens_b = _content_tokens(b.normalized_name)
    if not tokens_a or not tokens_b:
        jaccard = 0.0
    else:
        inter = len(tokens_a & tokens_b)
        union = len(tokens_a | tokens_b)
        jaccard = inter / union if union else 0.0

    char_ratio = difflib.SequenceMatcher(None, a.normalized_name, b.normalized_name).ratio()

    score = 0.5 * jaccard + 0.5 * char_ratio

    # Penalización dura si las specs extraídas explícitamente se
    # contradicen (p. ej. 128GB vs 512GB): un nombre parecido con una
    # capacidad distinta casi siempre es un producto distinto, no importa
    # qué tan alto salga el resto del puntaje.
    for key in ("ram_gb", "storage_gb", "screen_in"):
        va, vb = a.specs.get(key), b.specs.get(key)
        if va is not None and vb is not None and va != vb:
            score *= 0.3
            break
    return round(score, 4)


# ---------- Modelo de datos ----------

@dataclass
class Offer:
    source: str          # p. ej. "sunsky", "geekbuying", "mercadolibre"
    source_id: str        # id del producto dentro de esa fuente
    name: str
    brand: str
    price: float
    currency: str
    url: str
    picture: Optional[str] = None
    identifier: Optional[str] = None  # JAN/EAN/UPC/ASIN/barcode, sin normalizar
    category: Optional[str] = None

    normalized_name: str = field(init=False)
    normalized_identifier: Optional[str] = field(init=False)
    normalized_brand: str = field(init=False)
    model_tokens: set = field(init=False)
    specs: dict = field(init=False)

    def __post_init__(self):
        self.normalized_name = normalize_text(self.name)
        self.normalized_identifier = normalize_identifier(self.identifier)
        self.normalized_brand = normalize_text(self.brand or "")
        self.model_tokens = extract_model_tokens(self.name)
        self.specs = extract_specs(self.name)

    @property
    def key(self):
        return (self.source, self.source_id)


@dataclass
class Group:
    offers: list = field(default_factory=list)
    matched_by: str = ""  # "identifier" | "model_specs" | "similarity"
    confidence: float = 1.0

    def add(self, offer: Offer):
        self.offers.append(offer)

    def to_dict(self):
        return {
            "matched_by": self.matched_by,
            "confidence": self.confidence,
            "offers": [
                {
                    "source": o.source, "source_id": o.source_id, "name": o.name,
                    "brand": o.brand, "price": o.price, "currency": o.currency,
                    "url": o.url, "picture": o.picture,
                }
                for o in self.offers
            ],
        }


# ---------- Pipeline ----------

SIMILARITY_THRESHOLD = 0.60  # Paso 4: por debajo de esto, a la cola de revisión (Paso 5)


def _group_by_identifier(offers: list[Offer]):
    """Paso 1."""
    buckets: dict[str, list[Offer]] = {}
    ungrouped = []
    for o in offers:
        if o.normalized_identifier:
            buckets.setdefault(o.normalized_identifier, []).append(o)
        else:
            ungrouped.append(o)
    groups = []
    still_ungrouped = list(ungrouped)
    for ident, bucket in buckets.items():
        sources = {o.source for o in bucket}
        if len(bucket) > 1 and len(sources) > 1:
            # Antes de confiar en el identificador, se descartan las
            # coincidencias donde las specs explícitas (RAM/almacenamiento/
            # pantalla) se contradicen: un barcode reciclado por error en
            # el feed de origen (pasa) no debe unir dos productos distintos.
            consistent, inconsistent = _split_by_spec_consistency(bucket)
            if len(consistent) > 1:
                groups.append(Group(offers=consistent, matched_by="identifier", confidence=1.0))
            else:
                still_ungrouped.extend(consistent)
            still_ungrouped.extend(inconsistent)
        else:
            still_ungrouped.extend(bucket)
    return groups, still_ungrouped


def _split_by_spec_consistency(bucket: list[Offer]):
    """Separa un bucket-por-identificador en el subconjunto más grande de
    specs mutuamente consistentes vs. el resto (posible barcode reciclado)."""
    if len(bucket) <= 1:
        return bucket, []
    best_subset = [bucket[0]]
    rest = bucket[1:]
    changed = True
    leftover = []
    while changed:
        changed = False
        still_rest = []
        for o in rest:
            if all(_specs_compatible(o, ref) for ref in best_subset):
                best_subset.append(o)
                changed = True
            else:
                still_rest.append(o)
        rest = still_rest
    leftover.extend(rest)
    return best_subset, leftover


def _specs_compatible(a: Offer, b: Offer) -> bool:
    # Marcas distintas y conocidas en ambos lados: casi seguro que es un
    # error de datos de origen (p. ej. un identificador reciclado), no el
    # mismo producto. Esto es lo que más importa cuando ninguna spec
    # numérica es extraíble del nombre (un "Samsung Galaxy S24" no trae
    # RAM/almacenamiento en el título) y por eso no bastaría con comparar
    # solo specs.
    if a.normalized_brand and b.normalized_brand and a.normalized_brand != b.normalized_brand:
        return False
    for key in ("ram_gb", "storage_gb", "screen_in"):
        va, vb = a.specs.get(key), b.specs.get(key)
        if va is not None and vb is not None and va != vb:
            return False
    return True


def _group_by_model_specs(offers: list[Offer]):
    """Paso 3: misma marca + al menos un token de modelo en común + specs
    compatibles (cuando ambas partes traen esa spec)."""
    by_brand: dict[str, list[Offer]] = {}
    for o in offers:
        by_brand.setdefault(o.normalized_brand, []).append(o)

    groups = []
    ungrouped = []
    for brand, bucket in by_brand.items():
        used = set()
        for i, a in enumerate(bucket):
            if a.key in used:
                continue
            cluster = [a]
            for b in bucket[i + 1:]:
                if b.key in used:
                    continue
                if a.source == b.source:
                    continue  # el matching cruza fuentes, no deduplica dentro de una misma fuente aquí
                shared_model = a.model_tokens & b.model_tokens
                if shared_model and _specs_compatible(a, b):
                    cluster.append(b)
                    used.add(b.key)
            if len(cluster) > 1:
                used.add(a.key)
                groups.append(Group(offers=cluster, matched_by="model_specs", confidence=0.9))
    remaining = [o for o in offers if o.key not in {off.key for g in groups for off in g.offers}]
    return groups, remaining


def _group_by_similarity(offers: list[Offer], threshold: float = SIMILARITY_THRESHOLD):
    """Paso 4: compara por pares dentro del mismo bucket de marca (evita
    O(n²) sobre todo el catálogo). Devuelve grupos con score >= threshold y
    dos listas de sobrantes: los que sí se compararon pero no llegaron al
    umbral (van a Paso 5 con su mejor candidato) y los que no tuvieron con
    quién compararse."""
    by_brand: dict[str, list[Offer]] = {}
    for o in offers:
        by_brand.setdefault(o.normalized_brand, []).append(o)

    groups = []
    pending: list[tuple[Offer, Optional[Offer], float]] = []
    grouped_keys: set = set()

    for brand, bucket in by_brand.items():
        n = len(bucket)
        best_for: dict[tuple, tuple[Optional[Offer], float]] = {o.key: (None, 0.0) for o in bucket}
        used = set()
        pairs = []
        for i in range(n):
            for j in range(i + 1, n):
                a, b = bucket[i], bucket[j]
                if a.source == b.source:
                    continue
                score = similarity_score(a, b)
                pairs.append((score, a, b))
                if score > best_for[a.key][1]:
                    best_for[a.key] = (b, score)
                if score > best_for[b.key][1]:
                    best_for[b.key] = (a, score)
        pairs.sort(key=lambda t: -t[0])
        for score, a, b in pairs:
            if score < threshold:
                break
            if a.key in used or b.key in used:
                continue
            groups.append(Group(offers=[a, b], matched_by="similarity", confidence=score))
            used.add(a.key)
            used.add(b.key)
            grouped_keys.add(a.key)
            grouped_keys.add(b.key)
        for o in bucket:
            if o.key in used:
                continue
            candidate, score = best_for[o.key]
            pending.append((o, candidate, score))

    remaining_offers = [o for o, _, _ in pending if o.key not in grouped_keys]
    pending = [(o, c, s) for o, c, s in pending if o.key not in grouped_keys]
    return groups, pending


def match_products(offers: list[Offer], threshold: float = SIMILARITY_THRESHOLD) -> dict:
    """Corre el pipeline completo de 5 pasos y devuelve:
      groups          -> grupos de 2+ ofertas de fuentes distintas para el mismo producto
      singletons      -> ofertas que no encontraron pareja en ningún paso (siguen
                          siendo productos válidos de una sola tienda, no van a revisión)
      pending_review  -> candidatos con score bajo el umbral: {offer, best_candidate, score, llm_prompt}
    """
    step1_groups, remaining = _group_by_identifier(offers)
    step3_groups, remaining = _group_by_model_specs(remaining)
    step4_groups, pending_raw = _group_by_similarity(remaining, threshold)

    all_groups = step1_groups + step3_groups + step4_groups
    matched_keys = {o.key for g in all_groups for o in g.offers}

    pending_review = []
    singletons = []
    for o, candidate, score in pending_raw:
        if candidate is None:
            singletons.append(o)
        else:
            pending_review.append({
                "offer": o, "candidate": candidate, "score": score,
                "llm_prompt": build_llm_disambiguation_prompt(o, candidate),
            })

    return {
        "groups": all_groups,
        "singletons": singletons,
        "pending_review": pending_review,
        "stats": {
            "input_offers": len(offers),
            "groups": len(all_groups),
            "by_identifier": len(step1_groups),
            "by_model_specs": len(step3_groups),
            "by_similarity": len(step4_groups),
            "pending_review": len(pending_review),
            "singletons": len(singletons),
        },
    }


def build_llm_disambiguation_prompt(a: Offer, b: Offer) -> str:
    """Paso 5, rama LLM: prompt listo para mandarle a un modelo (o para que
    lo lea un humano) y decidir si dos ofertas de tiendas distintas son el
    mismo producto físico. No se llama a ningún API aquí — se deja el
    prompt armado para quien integre esto (p. ej. un Worker con acceso a la
    API de Claude, o revisión manual)."""
    return (
        "¿Estas dos publicaciones de tiendas distintas son el mismo producto físico? "
        "Responde solo SI o NO, y si es SI incluye qué variante (color/capacidad) aplica si difieren.\n\n"
        f"Tienda A ({a.source}): {a.name}\n"
        f"Tienda B ({b.source}): {b.name}\n"
    )


# ---------- Carga de feeds reales (CSV) ----------

def load_offers_from_csv(path: str, source: str, delimiter: str = ";") -> list[Offer]:
    """Carga un feed CSV de Admitad (formato SUNSKY o Geekbuying) y lo
    normaliza a Offer. Detecta las columnas disponibles por nombre en vez
    de asumir un orden fijo, porque cada tienda expone columnas distintas
    (p. ej. Geekbuying no trae `barcode`)."""
    offers = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            price_raw = row.get("price") or row.get("sale_price") or "0"
            try:
                price = float(price_raw)
            except ValueError:
                continue
            offers.append(Offer(
                source=source,
                source_id=row.get("id", ""),
                name=row.get("name") or row.get("title") or "",
                brand=row.get("vendor", ""),
                price=price,
                currency=row.get("currencyId", ""),
                url=row.get("url", ""),
                picture=row.get("picture") or row.get("image_link"),
                identifier=row.get("barcode"),
                category=row.get("categoryId") or row.get("product_type"),
            ))
    return offers


def _cli():
    if len(sys.argv) < 2:
        print("Uso: product_matcher.py archivo1.csv:fuente1 [archivo2.csv:fuente2 ...]")
        sys.exit(1)
    all_offers: list[Offer] = []
    for arg in sys.argv[1:]:
        path, _, source = arg.partition(":")
        source = source or path
        all_offers.extend(load_offers_from_csv(path, source))

    result = match_products(all_offers)
    print(json.dumps(result["stats"], indent=2, ensure_ascii=False))

    cross_source_groups = [g for g in result["groups"] if len({o.source for o in g.offers}) > 1]
    print(f"\nGrupos con 2+ tiendas distintas: {len(cross_source_groups)}")
    for g in cross_source_groups[:10]:
        print(f"  [{g.matched_by} conf={g.confidence}]", [f"{o.source}:{o.name[:50]}" for o in g.offers])

    if result["pending_review"]:
        print(f"\nPrimeros {min(5, len(result['pending_review']))} pendientes de revisión:")
        for p in result["pending_review"][:5]:
            print(f"  score={p['score']:.2f}  {p['offer'].source}:{p['offer'].name[:50]!r}  <->  {p['candidate'].source}:{p['candidate'].name[:50]!r}")


if __name__ == "__main__":
    _cli()
