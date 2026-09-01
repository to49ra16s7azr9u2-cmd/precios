#!/usr/bin/env python3
"""Busca el domain_id de Mercado Libre que corresponde a una o más frases.

    python3 scripts/ml_domains.py "librero estante" "mesa de centro"

Sirve para llenar el campo `domain` de los targets de add_products.py. Un
domain_id ("MLM-BOOKCASES") acota la búsqueda al rubro correcto, que es lo
que evita que se cuelen productos de otra categoría.

Además comprueba si ese dominio tiene productos de CATÁLOGO: hay rubros
(ropa, calzado de seguridad) donde Mercado Libre sólo tiene publicaciones de
vendedor y ninguna consulta va a devolver nada, por más keywords que se
prueben. Conviene descartarlos antes de armar una lista larga de targets.
"""
import json
import re
import sys
import urllib.parse
import urllib.request

BASE = "https://comparamx-mercadolibre-proxy.comparamx.workers.dev"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ComparaMEX-bot/1.0)"}


def get(path):
    req = urllib.request.Request(BASE + path, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


# El Worker recorta el cuerpo de /probe a 1200 caracteres (es una sonda de
# diagnóstico, no un proxy). Cuando domain_discovery devuelve muchas filas el
# recorte parte el JSON a la mitad y json.loads revienta, así que se leen los
# pares domain_id/domain_name con una expresión regular: lo que llegó entero
# se aprovecha y lo que quedó cortado simplemente no aparece, en vez de
# perderse la consulta completa por un ValueError.
PAIR_RE = re.compile(
    r'"domain_id"\s*:\s*"([^"]+)"(?:.*?"domain_name"\s*:\s*"([^"]*)")?',
    re.DOTALL,
)


def domains_for(phrase):
    inner = f"/sites/MLM/domain_discovery/search?q={phrase}"
    data = get("/probe?path=" + urllib.parse.quote(inner, safe=""))
    body = data.get("con_token", {}).get("body") or data.get("sin_token", {}).get("body")
    if not body:
        return []
    try:
        rows = [(r.get("domain_id"), r.get("domain_name") or "") for r in json.loads(body)]
    except ValueError:
        rows = [(m.group(1), m.group(2) or "") for m in PAIR_RE.finditer(body)]
    seen, out = set(), []
    for d, name in rows:
        if d and d not in seen:
            seen.add(d)
            out.append((d, name))
    return out


def catalog_count(domain, q):
    try:
        return len(get(
            f"/catalog?domain={urllib.parse.quote(domain)}"
            f"&q={urllib.parse.quote(q)}&limit=22&offset=0"
        ).get("items", []))
    except Exception:
        return -1


def main():
    for phrase in sys.argv[1:]:
        print(f"=== {phrase} ===")
        try:
            found = domains_for(phrase)
        except Exception as e:
            print("  ERROR", e)
            continue
        if not found:
            print("  (sin dominio)")
        # Se sondea con la propia frase, no con una keyword genérica:
        # products/search exige `q` y con un valor genérico casi todo da cero.
        for dom, name in found:
            n = catalog_count(dom, phrase)
            flag = "sin catálogo" if n == 0 else ("error" if n < 0 else f"{n} en catálogo")
            print(f"  {dom:56s} {name}  [{flag}]")


if __name__ == "__main__":
    main()
