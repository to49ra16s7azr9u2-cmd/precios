# ComparaMEX Local — datos

Todo lo que está en esta carpeta se publica con el sitio (el repositorio se
sirve entero). Por eso aquí sólo va información pública del negocio: nombre,
giro, dirección, municipio, horario, WhatsApp y sitio. Nada de datos de
contacto personales, RFC, cuentas ni pagos.

## Archivos

- `tiendas.json` — el registro de tiendas (ver abajo).
- `precios/<id de tienda>.csv` — la lista de precios de cada tienda, con las
  columnas de `plantilla-precios.csv`. En vez del archivo, la tienda puede
  dar la url de una Hoja de cálculo de Google «publicada en la web como CSV»
  (`fuente.url` en el registro).
- `revision/` y `reportes/` — salida de los scripts para cada tienda; NO se
  publican (.gitignore).

## Registro (`tiendas.json`)

```json
{
  "id": "loc-14098-ferreteria-del-centro",
  "nombre": "Ferretería del Centro",
  "giro": "Ferretería",
  "municipio": "14098",
  "direccion": "Av. Juárez 120, Centro, San Pedro Tlaquepaque, Jal.",
  "lat": 20.6409, "lng": -103.3117,
  "horario": "L-S 9:00-19:00",
  "whatsapp": "523300000000",
  "sitio": null,
  "plan": "gratis",
  "alta": "2026-09-24",
  "activa": true,
  "fuente": {"tipo": "csv"}
}
```

`municipio` es la clave INEGI de 5 dígitos (la misma que usa el mapa de
«¿Dónde estás?», `data/mexico-municipios.json`).

## Columnas de la lista de precios

| columna | qué va | obligatoria |
|---|---|---|
| producto | nombre como lo vende la tienda | sí |
| marca | | recomendada |
| modelo | código de modelo del fabricante (BCD704C1) | recomendada |
| gtin | código de barras | recomendada |
| precio | precio de mostrador en MXN, IVA incluido | sí |
| existencia | si / pocas / no | sí |
| fecha | día en que la tienda confirmó el precio (AAAA-MM-DD) | sí |
| id_comparamex | la ficha del catálogo, cuando la tienda la confirmó | no |

Con código de barras o de modelo el producto se une solo a su ficha (con el
mismo veto que cualquier fusión). Sin ellos, `local_importar.py` deja en
`revision/<tienda>.csv` las tres fichas más parecidas para que la tienda
elija y se anote en `id_comparamex`.

Un precio con más de 14 días sin confirmar no se muestra.
