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
# --vecinos-fuertes: cuando el 80%+ de las 25 fichas más parecidas está en la
# categoría nueva y casi ninguna en la actual, no se exige el sustantivo
# (es_coherente bloqueaba 5,206 correcciones). Medido el 26-sep-2026: 53 de
# 60 bien (88%), ~900 fichas.
echo "=== reclasificar_hibrido ==="
python3 scripts/reclasificar_hibrido.py --aplicar --vecinos-fuertes > /tmp/reclasificar_hibrido.log 2>&1
sed -n '1,12p;/^Guardado/p' /tmp/reclasificar_hibrido.log
# Subcategorías comodín («Accesorios», «Refacciones para X») partidas por
# el nombre de la pieza; el modelo se reentrena en cada corrida con el
# catálogo y los ejemplos verificados (partir_genericas.py).
echo "=== partir_genericas ==="; python3 scripts/partir_genericas.py --aplicar 2>&1 | tail -2
echo "=== prior_tienda ==="; python3 scripts/prior_tienda.py --aplicar 2>&1 | tail -1
# Autopartes por pieza (ver subcategorias_autopartes_finas.py): también lo que
# el candado de movimientos dejó en el sistema viejo.
echo "=== autopartes_finas ==="; python3 scripts/subcategorias_autopartes_finas.py --aplicar 2>&1 | tail -2
echo "=== divisiones ==="; python3 scripts/subcategorias_divisiones.py --aplicar 2>&1 | tail -2
# Reglas de la auditoría por subcategoría (auditar_subcategorias_tienda.py):
# lo que entra nuevo con los mismos errores se corrige en cada corrida.
echo "=== reglas de auditoría ==="
python3 scripts/mover_por_regla.py --lote todos --salida /tmp/auditoria-mov.json > /tmp/auditoria-mov.log 2>&1
tail -1 /tmp/auditoria-mov.log
# Sin movimientos (todo lo de las reglas ya está en su lugar) aplicar_movimientos
# sale con error «ningún grupo elegido» y con pipefail cortaba la cadena.
if python3 -c "import json,sys; sys.exit(0 if json.load(open('/tmp/auditoria-mov.json')) else 1)"; then
  python3 scripts/aplicar_movimientos.py /tmp/auditoria-mov.json --todos --motivo "reglas de auditoría (automático)" 2>&1 | tail -1
fi
# Fusiones: sin esto el catálogo acumulaba duplicados desde el 17-sep (los
# scripts existían pero nadie los corría). Van después de clasificar porque
# casi todas exigen la misma categoría. Salidas completas en /tmp/fusiones.log.
echo "=== fusiones ==="
{
  python3 scripts/merge_by_gtin.py
  python3 scripts/merge_cross_store.py
  python3 scripts/merge_amazon_cross_store.py --dry-run --todas-las-tiendas --muestra 0 --informe /tmp/fusion_amazon.json
  python3 scripts/fusionar_vetado.py /tmp/fusion_amazon.json --aplicar
  python3 scripts/merge_by_color.py
  python3 scripts/merge_by_signature.py
  python3 scripts/merge_same_store.py --muestra 0
  python3 scripts/merge_by_spec_color.py --muestra 0
  python3 scripts/merge_misma_foto.py --muestra 0
} > /tmp/fusiones.log 2>&1
grep -E "absorbidas|fusionados|Catálogo|catálogo" /tmp/fusiones.log | tail -12
echo "=== completar_subcategorias ==="; python3 scripts/completar_subcategorias.py --aplicar 2>&1 | tail -1
echo "=== sync_subcategories ==="; python3 scripts/sync_subcategories.py 2>&1 | tail -3
echo "=== compute_facets ==="; python3 scripts/compute_facets.py 2>&1 | tail -2
echo "=== compute_quality_axes ==="; python3 scripts/compute_quality_axes.py 2>&1 | tail -2
echo "=== politicas_tiendas ==="; python3 scripts/politicas_tiendas.py 2>&1 | tail -1
echo "=== enlaces_manuales ==="; python3 scripts/aplicar_enlaces_manuales.py 2>&1 | tail -1
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
