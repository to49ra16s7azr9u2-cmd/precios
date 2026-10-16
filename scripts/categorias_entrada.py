#!/usr/bin/env python3
"""Escribe data/categorias-entrada.json: lista mínima (categoría, cantidad,
subcategorías) para la pantalla de entrada (js/entrada.js), que corre en
CUALQUIER página -- también en las estáticas de SEO, donde no está data.json.
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
man = json.load(open(os.path.join(ROOT, "data", "data.json"), encoding="utf-8"))
stats = man.get("categoryStats", {})
out = []
for c in man["categories"]:
    st = stats.get(c["id"], {})
    subs = st.get("subs") or {}
    out.append({"id": c["id"], "name": c["name"], "n": st.get("n", 0),
                "subs": [k for k, v in sorted(subs.items(), key=lambda kv: -kv[1]) if v > 0]})
out.sort(key=lambda x: -x["n"])
with open(os.path.join(ROOT, "data", "categorias-entrada.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
print(f"categorias-entrada.json: {len(out)} categorías")
