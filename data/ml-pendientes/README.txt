LOTES DE URLS PARA EL GENERADOR DE ENLACES DE MERCADO LIBRE
============================================================

1. Entra al panel de afiliados de Mercado Libre > "Generar enlaces".
2. Abre lote-001.txt, copia sus 30 urls y pégalas en el generador.
3. Copia TODO lo que devuelva el panel (los enlaces .../social/...) y
   pégalo al final de salida.txt (un enlace por línea). El orden no importa
   y pueden mezclarse varios lotes en el mismo archivo: el emparejado es por
   contenido, no por posición.
4. Sigue con lote-002.txt, lote-003.txt... los que alcances.
5. Cuando quieras aplicar lo que llevas:

   python3 scripts/ml_enlaces.py --entrada data/ml-pendientes/todas.txt --salida data/ml-pendientes/salida.txt
   python3 scripts/aplicar_afiliados.py --tienda mercadolibre
   python3 scripts/ml_lotes.py          # rehace los lotes sin lo ya enlazado

Los lotes van en orden de prioridad: primero los productos con página
pública (dos o más vendedores), ordenados por número de reseñas.
