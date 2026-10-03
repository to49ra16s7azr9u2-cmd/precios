#!/bin/bash
# Recorrido diario de Mercado Libre por ventanas de 100 subcategorías.
#
#   bash scripts/ronda_ml_recorrido.sh 0 1 2 3 > /tmp/ronda_recorrido_$(date -u +%m%d).log 2>&1
#
# Cada ventana corre ml_discover.py en modo --recorrer (agota los dominios
# confirmados de cada subcategoría) y agrega lo nuevo al catálogo. Antes de
# cada ventana se mira el Worker: si contesta 429 (tope diario de 100,000
# pedidos, se reinicia a las 00:00 UTC) se para y se dice cuál faltó.
#
# Vive en el repositorio (y no en /tmp) porque un reinicio del contenedor
# borra /tmp y la copia de trabajo: así la ronda se puede volver a correr con
# sólo clonar. El caché de dominios confirmados va en data/ por lo mismo.
set -o pipefail
cd "$(dirname "$0")/.."
WORKER="https://comparamx-mercadolibre-proxy.comparamx.workers.dev/item?id=MLM1"
DOMINIOS="data/ml-dominios-confirmados.json"

estado_worker() { curl -s -o /dev/null -w "%{http_code}" --max-time 30 "$WORKER"; }
cuantos() { python3 -c "import sys; sys.path.insert(0, 'scripts'); from data_io import load_catalog; print(len(load_catalog()['products']))"; }

echo "Worker -> HTTP $(estado_worker)"
ANTES=$(cuantos)
echo "productos antes: $ANTES"
ULTIMA=""
for V in "$@"; do
  CODIGO=$(estado_worker)
  if [ "$CODIGO" = "429" ]; then
    echo "=== CUOTA AGOTADA antes de la ventana $V ==="
    break
  fi
  echo "########## RECORRIDO ventana $V ##########"
  python3 scripts/ml_discover.py --dia "$V" --ventana 100 --marcas 60 --max 400 --pages 45 \
    --dominios-json "$DOMINIOS" --reusar-dominio --recorrer 2>&1 \
    | grep -E --line-buffered "^Día|consultas de catálogo|Agregados|Traceback|Error|^  -- " || true
  echo "########## ventana $V LISTA: $(cuantos) productos ##########"
  ULTIMA=$V
  if [ "$(estado_worker)" = "429" ]; then
    echo "=== CUOTA AGOTADA tras la ventana $V ==="
    break
  fi
done
DESPUES=$(cuantos)
echo "productos antes $ANTES -> después $DESPUES (+$((DESPUES - ANTES)))"
echo "=== RECORRIDO OK ==="
