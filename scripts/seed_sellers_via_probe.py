"""Puebla `sellers` en un subconjunto de productos usando /probe.

Es un puente para verificar la funcionalidad ANTES de desplegar el Worker
nuevo: /probe recorta el cuerpo a 1200 caracteres, así que hay que pedir un
vendedor por llamada (limit=1&offset=i). Sirve para unas decenas de
productos, no para los ~7,700 del catálogo -- eso lo hace refresh_prices.py
una vez que el Worker devuelva `sellers`.
"""
import json, re, sys, urllib.parse, urllib.request, concurrent.futures as cf

BASE = "https://comparamx-mercadolibre-proxy.comparamx.workers.dev"
H = {"User-Agent": "ComparaMEX-bot/1.0"}
MAX_SELLERS = 8


def probe(path):
    u = BASE + "/probe?path=" + urllib.parse.quote(path, safe="")
    with urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=40) as r:
        d = json.load(r)
    return (d.get("con_token") or {}).get("body") or ""


def one_seller(pid, offset):
    body = probe(f"/products/{pid}/items?limit=1&offset={offset}")
    try:
        r = json.loads(body)["results"][0]
    except Exception:
        return None
    if (r.get("currency_id") or "MXN") != "MXN" or not isinstance(r.get("price"), (int, float)):
        return None
    row = {
        "itemId": r["item_id"],
        "price": r["price"],
        "url": f"https://www.mercadolibre.com.mx/p/{pid}?pdp_filters=item_id:{r['item_id']}",
    }
    op = r.get("original_price")
    if isinstance(op, (int, float)) and op > r["price"]:
        row["listPrice"] = op
    if (r.get("shipping") or {}).get("free_shipping"):
        row["shippingFee"] = 0
    st = ((r.get("seller_address") or {}).get("state") or {}).get("name")
    if st:
        row["state"] = st
    if r.get("official_store_id"):
        row["official"] = True
    return row


def sellers_for(pid, count):
    n = min(count, MAX_SELLERS)
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        rows = list(ex.map(lambda i: one_seller(pid, i), range(n)))
    return [r for r in rows if r]


def main(data_path, limit):
    data = json.load(open(data_path, encoding="utf-8"))
    todo = []
    for p in data["products"]:
        for node in (p.get("offers") or []) + (p.get("colorVariants") or []):
            m = re.search(r"/p/(MLM\d+)", node.get("url") or "")
            if m and (node.get("sellerCount") or 0) > 1 and not node.get("sellers"):
                todo.append((p, node, m.group(1), node["sellerCount"]))
    todo.sort(key=lambda t: -t[3])
    todo = todo[:limit]
    print(f"nodos a poblar: {len(todo)}")
    done = 0
    for p, node, pid, cnt in todo:
        rows = sellers_for(pid, cnt)
        if len(rows) >= 2:
            node["sellers"] = rows
            done += 1
            print(f"  {p['id']:8s} {pid} -> {len(rows)} vendedores  ${min(r['price'] for r in rows):,.0f}–${max(r['price'] for r in rows):,.0f}  {p['name'][:42]}")
    json.dump(data, open(data_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"poblados {done} nodos")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 40)
