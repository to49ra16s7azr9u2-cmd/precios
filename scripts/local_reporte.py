#!/usr/bin/env python3
"""ComparaMEX Local: reporte de precios de mercado para una tienda.

Para cada producto que la tienda tiene en el catálogo: su precio, el más
barato de las demás tiendas (y cuál es), la diferencia y si es el más barato
de su municipio. Es el «市場価格レポート» del plan: la misma información de
precios que tienen las cadenas grandes, devuelta a la tienda chica.

Sale en local/reportes/<id>-<fecha>.csv, que NO se publica (.gitignore): es
para mandárselo a la tienda.

USO
---
    python3 scripts/local_reporte.py --tienda loc-14098-ferreteria-del-centro
"""
import argparse
import csv
import datetime
import io
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
from data_io import load_catalog  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tienda", required=True)
    ap.add_argument("--salida-dir", default=os.path.join(RAIZ, "local", "reportes"))
    args = ap.parse_args()

    data = load_catalog()
    nombres = {s["id"]: s.get("name", s["id"]) for s in data.get("stores") or []}
    local = json.load(io.open(os.path.join(RAIZ, "data", "local.json"), encoding="utf-8"))
    tienda = local["tiendas"].get(args.tienda)
    if not tienda:
        sys.exit(f"la tienda {args.tienda} no está en data/local.json (¿se corrió local_importar.py --aplicar?)")
    por_id = {p["id"]: p for p in data["products"]}
    filas = []
    for pid, ofs in local["ofertas"].items():
        mias = [o for o in ofs if o["t"] == args.tienda]
        p = por_id.get(pid)
        if not mias or not p:
            continue
        mio = min(o["p"] for o in mias)
        otras = [o for o in p.get("offers") or [] if o.get("price")]
        mejor = min(otras, key=lambda o: o["price"]) if otras else None
        # Otras tiendas locales del mismo municipio (o con sucursal en todos).
        del_mun = [o["p"] for o in ofs if o["t"] != args.tienda
                   and local["tiendas"].get(o["t"], {}).get("m") in (tienda.get("m"), "*")]
        filas.append({
            "ficha": pid, "producto": p["name"], "tu_precio": mio,
            "mas_barato_otra_tienda": mejor["price"] if mejor else "",
            "tienda_mas_barata": nombres.get(mejor["storeId"], mejor["storeId"]) if mejor else "",
            "diferencia_pct": round((mio / mejor["price"] - 1) * 100, 1) if mejor else "",
            "tiendas_que_lo_venden": len({o.get("storeId") for o in p.get("offers") or []}),
            "mas_barato_del_municipio": "si" if all(mio <= x for x in del_mun) else "no",
        })
    filas.sort(key=lambda f: (f["diferencia_pct"] == "", -(f["diferencia_pct"] or 0)))
    os.makedirs(args.salida_dir, exist_ok=True)
    ruta = os.path.join(args.salida_dir, f"{args.tienda}-{datetime.date.today().isoformat()}.csv")
    with io.open(ruta, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]) if filas else ["ficha"])
        w.writeheader()
        w.writerows(filas)
    con = [f for f in filas if f["diferencia_pct"] != ""]
    print(f"{tienda.get('n')}: {len(filas)} productos en el catálogo; comparables {len(con)}")
    print(f"  el más barato de todas las tiendas: {sum(1 for f in con if f['diferencia_pct'] <= 0)}")
    print(f"  15% o más arriba del más barato: {sum(1 for f in con if f['diferencia_pct'] >= 15)}")
    print(f"  el más barato de su municipio: {sum(1 for f in filas if f['mas_barato_del_municipio'] == 'si')}")
    print(f"-> {ruta}")


if __name__ == "__main__":
    main()
