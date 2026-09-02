#!/usr/bin/env python3
"""Da de alta productos nuevos en data/data.json desde el catálogo de Mercado Libre.

Uso:
    python3 scripts/add_products.py <targets.json> [--dry-run] [--data ruta]

`targets.json` es una lista de objetos, uno por consulta:

    {"domain": "MLM-BOOKCASES", "q": "librero estante",
     "cat": "Muebles", "sub": "Libreros",
     "max": 10, "pages": 2, "icon": "sofa",
     "must": ["librero"], "not": ["repisa flotante"]}

  domain  domain_id de Mercado Libre (obtenerlo con /probe, ver ml_domains.py)
  q       palabras clave dentro de ese dominio -- ES EL PARÁMETRO QUE MÁS PESA
  cat/sub `id` (no `name`) de la categoría y subcategoría de data.json
  max     tope de productos a tomar de esta consulta
  pages   páginas de 22 a recorrer con offset (rara vez hace falta más de 2)
  icon    clave del set de iconos; usar la que ya domina en esa categoría
  must    si está, el título debe contener al menos uno de estos textos
  not     el título no debe contener ninguno de estos textos

Por qué /catalog y no /search
-----------------------------
`/search` está topado a 12 resultados y mezcla dominios: probándolo salieron
agujetas dentro de "Calzado de seguridad" y una batería de recambio dentro de
"Máquinas de coser". `/catalog?domain=…` recorre el catálogo real de un
domain_id, así que lo que vuelve ya está acotado al rubro correcto.

Cómo sacarle volumen
--------------------
El rendimiento viene de la VARIEDAD DE KEYWORDS, no del paginado: `q` es una
búsqueda real dentro del dominio y `products/search` la exige siempre, así que
un `q` genérico ("producto") devuelve cero en casi todos los dominios. Conviene
listar varias entradas con el mismo cat/sub y distinto `q` -- la deduplicación
es global, así que no se pisan entre ellas.

Hay dominios que simplemente no tienen catálogo (ropa, calzado de seguridad):
ahí Mercado Libre sólo tiene publicaciones de vendedor, no productos de
catálogo, y toda consulta vuelve vacía. No es un fallo del script.
"""
import argparse
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_io import load_catalog, save_catalog  # noqa: E402

BASE = "https://comparamx-mercadolibre-proxy.comparamx.workers.dev"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ComparaMEX-bot/1.0)"}
PAGE = 22  # MAX_CATALOG_CANDIDATES del Worker
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Consumibles y reposiciones: fuera del catálogo por decisión de producto
# tomada al principio del proyecto (el comparador es de bienes durables).
BANNED = [
    "capsula", "detergente", "suavizante", "jabon", "cartucho", "tinta",
    "toner", "repuesto", "recambio", "pilas aa", "bateria aa", "shampoo",
    "champu", "desodorante", "pañales", "panales", "toallitas", "suplemento",
    "vitamina", "proteina", "cafe molido", "grano de cafe", "kit de limpieza",
    "limpiador", "perfume", "maquillaje", "labial", "medicamento", "pastillas",
    "pegamento", "agujeta", "cordones para", "plantilla para", "solo funda",
    "unicamente el", "no incluye",
    # La cámara desechable se usa una vez y se tira: es un consumible, y
    # además no es una cámara instantánea aunque el dominio las mezcle.
    "camara desechable", "desechable",
    "kit limpieza", "rollo de etiquetas", "papel termico",
]

# El domain_id acota el rubro pero no separa el aparato de sus accesorios:
# dentro de MLM-SEWING_MACHINES vinieron una bolsa de transporte y una batería
# de recambio, y dentro del dominio de motores para cortina, una central
# electrónica. Estos patrones descartan el accesorio y dejan el aparato.
ACCESSORY = [
    "bolsa almacenamiento", "bolsa de almacenamiento", "bolsa para", "estuche para",
    "funda para maquina", "bateria recargable para", "bateria para", "cargador para",
    "central electronica", "tarjeta electronica", "control remoto para",
    "soporte para", "base para", "adaptador para", "cable para", "kit de reparacion",
    "juego de agujas", "set de agujas", "aguja para", "bobina para", "pedal para",
    "motor para maquina", "iluminacion para", "refaccion",
    "cable de alimentacion", "cable de señal", "contra chapa", "simulada", "dummy",
    "barboquejo", "puntas de", "puntas para", "juego de puntas",
    "carcasa para", "case para", "gabinete para disco",
]

STOPWORDS = {"de", "la", "el", "para", "con", "y", "en", "a", "por", "del", "los", "las"}

# Lote de mayoreo ("30pz Audifonos ..."): no es un producto de consumo, es una
# venta al por mayor, y en una lista de comparación de precios se ve como si
# el mismo artículo costara diez veces más. Se dejan pasar los packs chicos
# (2, 3, 4 piezas), que sí son presentación de venta normal.
BULK_RE = re.compile(
    r"\b(\d{2,})\s*(?:pz|pzs|piezas|unidades|pack)\b"      # "30pz ..."
    r"|\b(?:pack|paquete|lote|caja)\s*(?:de\s*)?(\d{2,})\b"  # "Pack 100 ..."
)

# Algunos vendedores meten un precio dentro del título ("Persiana ... $1,312"),
# que además no coincide con el precio real de la oferta. Mostrarlo sería
# contradecir en el nombre el precio que la propia fila indica.
PRICE_IN_TITLE_RE = re.compile(r"\$\s*\d")


def is_junk_title(title):
    m = BULK_RE.search(norm(title))
    if m and int(next(g for g in m.groups() if g)) >= 10:
        return True
    return bool(PRICE_IN_TITLE_RE.search(title))


def get(path):
    req = urllib.request.Request(BASE + path, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r)


def catalog(domain, q, offset):
    return get(
        f"/catalog?domain={urllib.parse.quote(domain)}"
        f"&q={urllib.parse.quote(q)}&limit={PAGE}&offset={offset}"
    ).get("items", [])


def norm(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]+", " ", s).strip()


def sig(name):
    """Firma para deduplicar variantes con el mismo nombre reordenado."""
    return " ".join(sorted(w for w in norm(name).split() if w not in STOPWORDS))


def ml_id(url):
    m = re.search(r"(MLM\d+)", url or "")
    return m.group(1) if m else None


def sellers_of(item, product_id):
    """Vendedores normalizados, mismo formato que refresh_prices.py.

    Solo con MÁS DE UNO: el frontend no expande filas con uno solo
    (sellerRows exige length >= 2) y guardarlo sería peso muerto.
    """
    out = []
    for s in item.get("sellers") or []:
        item_id, price = s.get("itemId"), s.get("price")
        if not item_id or not isinstance(price, (int, float)) or price <= 0:
            continue
        row = {
            "itemId": item_id,
            "price": price,
            "url": f"https://www.mercadolibre.com.mx/p/{product_id}?pdp_filters=item_id:{item_id}",
        }
        if s.get("listPrice"):
            row["listPrice"] = s["listPrice"]
        if s.get("shippingFee") == 0:
            row["shippingFee"] = 0
        if s.get("state"):
            row["state"] = s["state"]
        if s.get("official"):
            row["official"] = True
        out.append(row)
    return out if len(out) > 1 else []


def build_index(products):
    seen_ml, seen_sig = set(), set()
    for p in products:
        seen_sig.add(sig(p["name"]))
        for o in list(p.get("offers", [])) + list(p.get("colorVariants") or []):
            i = ml_id(o.get("url"))
            if i:
                seen_ml.add(i)
    return seen_ml, seen_sig


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("targets")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    # data/data.json dejó de ser el catálogo entero: ahora es un manifiesto
    # que apunta a data/products-N.json (ver data_io). Este script seguía
    # leyéndolo a mano y reventaba en data["products"], que ya no existe ahí.
    data = load_catalog()
    products = data["products"]
    cat_ids = {c["id"]: {s["id"] for s in c.get("subcategories", [])} for c in data["categories"]}
    seen_ml, seen_sig = build_index(products)
    next_num = max(int(re.sub(r"\D", "", p["id"]) or 0) for p in products) + 1

    with open(args.targets, encoding="utf-8") as f:
        targets = json.load(f)

    added = []
    skipped = {"dup": 0, "banned": 0, "refurb": 0, "filtro": 0, "nodata": 0}
    for t in targets:
        cat, sub = t["cat"], t["sub"]
        if cat not in cat_ids or sub not in cat_ids[cat]:
            print(f"!! categoría/subcategoría inexistente: {cat} / {sub}")
            continue
        must = [norm(x) for x in t.get("must", [])]
        never = [norm(x) for x in t.get("not", [])]
        want, got = t.get("max", 8), 0
        for page in range(t.get("pages", 2)):
            if got >= want:
                break
            try:
                items = catalog(t["domain"], t.get("q", "producto"), page * PAGE)
            except Exception as e:
                print(f"!! error {t['domain']} q={t.get('q')!r}: {e}")
                break
            if not items:
                break
            for it in items:
                if got >= want:
                    break
                title, iid = it.get("title") or "", it.get("id")
                n = norm(title)
                if not iid or not title or not it.get("photo") or not it.get("price"):
                    skipped["nodata"] += 1
                    continue
                if iid in seen_ml or sig(title) in seen_sig:
                    skipped["dup"] += 1
                    continue
                if it.get("isRefurb"):
                    skipped["refurb"] += 1
                    continue
                # `allow` levanta el veto de palabras concretas SOLO para este
                # target. Hace falta porque el veto es global y hay
                # subcategorías donde el consumible ES el producto: Impresoras
                # tiene "Consumibles", y ahí un cartucho de tinta es
                # exactamente lo que se busca, no algo que colar por error.
                allowed = {norm(x) for x in t.get("allow", [])}
                vetoes = [norm(x) for x in BANNED + ACCESSORY if norm(x) not in allowed]
                if any(b in n for b in vetoes) or is_junk_title(title):
                    skipped["banned"] += 1
                    continue
                if (must and not any(m in n for m in must)) or any(x in n for x in never):
                    skipped["filtro"] += 1
                    continue

                offer = {
                    "storeId": "mercadolibre",
                    "price": it["price"],
                    "url": it.get("url") or f"https://www.mercadolibre.com.mx/p/{iid}",
                    "photo": it["photo"],
                    "shippingFee": it.get("shippingFee"),
                    "points": None,
                    "rating": None,
                    "reviewCount": 0,
                    "stock": None,
                    "verified": True,
                }
                if it.get("priceOriginal"):
                    offer["listPrice"] = it["priceOriginal"]
                # El Worker ya manda cuántos vendedores tiene la publicación y
                # la lista de ellos (winnerOffer los calcula igual para
                # /catalog que para /item). Guardarlos acá cuesta cero: si no,
                # el producto nace diciendo "1 vendedor" hasta que pase
                # refresh_prices.py al día siguiente.
                if isinstance(it.get("sellerCount"), int) and it["sellerCount"] > 1:
                    offer["sellerCount"] = it["sellerCount"]
                if it.get("lowestPrice") and it["lowestPrice"] < it["price"]:
                    offer["lowestPrice"] = it["lowestPrice"]
                sellers = sellers_of(it, iid)
                if sellers:
                    offer["sellers"] = sellers

                products.append({
                    "id": f"p{next_num}",
                    "name": title,
                    "brand": it.get("brand") or "",
                    "category": cat,
                    "subcategory": sub,
                    "image": t.get("icon", "box"),
                    "photo": it["photo"],
                    "specs": it.get("specs") or [],
                    "reviews": [],
                    "offers": [offer],
                    "mlQuery": title,
                })
                next_num += 1
                seen_ml.add(iid)
                seen_sig.add(sig(title))
                added.append((cat, sub, title, it["price"]))
                got += 1
            time.sleep(0.3)
        if got:
            print(f"  +{got:<3} {cat}/{sub}  ← q={t.get('q')!r}")

    print(f"\nAgregados: {len(added)}   descartados: {skipped}")
    for cat, sub, name, price in added:
        print(f"  [{cat}/{sub}] ${price:,.0f}  {name[:72]}")

    if args.dry_run:
        print("\n(dry-run: no se guardó nada)")
    elif added:
        save_catalog(data)
        print(f"\nCatálogo guardado: {len(products)} productos")


if __name__ == "__main__":
    main()
