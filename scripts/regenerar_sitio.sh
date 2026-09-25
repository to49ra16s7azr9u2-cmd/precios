#!/usr/bin/env bash
# La cadena que deja el sitio al día después de cualquier cambio en el
# catálogo o en las reglas. Antes vivía fuera del repo; desde el 23-sep
# arranca con reaplicar_reglas.py: si una regla del clasificador cambió, el
# catálogo entero pasa por las reglas de hoy (con candado para lo movido a
# mano y veto del catálogo), en vez de que la corrección valga sólo para lo
# que entre después.
set -eo pipefail
cd "$(dirname "$0")/.."
# El informe completo queda en el log; acá sólo el resumen. (Un «| head»
# directo le cortaba la salida a python con SIGPIPE antes de guardar.)
echo "=== reaplicar_reglas ==="
python3 scripts/reaplicar_reglas.py --aplicar > /tmp/reaplicar_reglas.log 2>&1
sed -n '1,25p;/^Guardado/p' /tmp/reaplicar_reglas.log
# Después, el juez híbrido: el modelo del catálogo + el sustantivo + las
# reglas (reclasificar_hibrido.py). Mueve lo que el catálogo mismo dice que
# está fuera de lugar, con las definiciones y lo movido a mano intocables.
echo "=== reclasificar_hibrido ==="
python3 scripts/reclasificar_hibrido.py --aplicar > /tmp/reclasificar_hibrido.log 2>&1
sed -n '1,12p;/^Guardado/p' /tmp/reclasificar_hibrido.log
echo "=== sync_subcategories ==="; python3 scripts/sync_subcategories.py 2>&1 | tail -3
echo "=== compute_facets ==="; python3 scripts/compute_facets.py 2>&1 | tail -2
echo "=== compute_quality_axes ==="; python3 scripts/compute_quality_axes.py 2>&1 | tail -2
echo "=== aplicar_afiliados ==="; python3 scripts/aplicar_afiliados.py --todas 2>&1 | tail -3
echo "=== record_price_history ==="; python3 scripts/record_price_history.py 2>&1 | tail -4
echo "=== build_search_index ==="; python3 scripts/build_search_index.py 2>&1 | tail -2
echo "=== build_buscador ==="; python3 scripts/build_buscador.py 2>&1 | tail -1
echo "=== build_retirados_index ==="; python3 scripts/build_retirados_index.py 2>&1 | tail -2
echo "=== build_marcas_index ==="; python3 scripts/build_marcas_index.py 2>&1 | tail -2
echo "=== vocabulario_cabeza ==="; python3 scripts/vocabulario_cabeza.py 2>&1 | tail -1
echo "=== generate_seo_pages ==="; python3 scripts/generate_seo_pages.py 2>&1 | tail -12
echo "=== comprimir_datos ==="; python3 scripts/comprimir_datos.py 2>&1 | tail -1
echo "=== FINAL OK ==="
