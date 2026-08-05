# ComparaMX

Comparador de precios entre tiendas mexicanas, inspirado en [Kakaku.com](https://kakaku.com). MVP de demostración.

## Qué hace

- Busca un producto y compara su precio entre varias tiendas (Amazon México, Mercado Libre, Walmart México, Liverpool, Costco México).
- A diferencia de Kakaku.com (que cubre todo Japón), aquí la cobertura de entrega se limita a **3 zonas metropolitanas** (CDMX, Guadalajara, Monterrey), porque fuera de esas zonas la infraestructura logística de México es demasiado irregular para dar una estimación confiable. Dentro de cada zona, el pin se elige **por municipio/alcaldía** (p. ej. Cuauhtémoc, Zapopan, San Pedro Garza García), no por la zona metropolitana completa.
- Al tocar un pin del mapa (o un chip de municipio), la tabla de comparación recalcula al instante el **precio más barato** y la **entrega más rápida** para ese municipio, según la distancia al centro de distribución de cada tienda y un factor de confiabilidad logística local (`infraDays`).

## Costo: cero, salvo el hosting

Es un sitio 100% estático (HTML/CSS/JS sin build step):

- **Mapa**: [Leaflet](https://leafletjs.com) (vía CDN) + tiles de OpenStreetMap — sin API key, sin cuenta de facturación (a diferencia de Google Maps).
- **Datos**: `data/data.json`, editable a mano o generable por script. Sin base de datos.
- **Hosting**: se puede publicar gratis en GitHub Pages, Cloudflare Pages, Netlify o Vercel (capa gratuita). No requiere backend.
- **PWA**: `manifest.json` + `sw.js` permiten "Instalar app" desde el navegador y uso offline básico.

## Estructura

```
index.html          página única (lista de productos + vista de comparación)
css/style.css        estilos
js/app.js             lógica: búsqueda, filtro, mapa, tabla de comparación
data/data.json        productos, tiendas, regiones y precios/tiempos de entrega (datos de demo)
icons/, manifest.json, sw.js   PWA
```

## Cómo probarlo

```
python3 -m http.server 8000
# abrir http://localhost:8000/
```

## Modelo de datos (`data/data.json`)

- `metros`: las 3 zonas metropolitanas cubiertas (id, nombre, centro y zoom del mapa para esa zona).
- `regions`: municipios/alcaldías dentro de cada zona (`metro`, nombre, lat/lng, `infraDays`: días extra por confiabilidad logística local — p. ej. zonas periféricas como Xochimilco o Tlajomulco suman 1 día).
- `stores`: tiendas comparadas, con `hubRegion` (municipio donde está el centro de distribución de la tienda).
- `products[].offers[]`: por tienda, solo `price` y `url`. El tiempo de entrega **no** se guarda por región: se calcula en `js/app.js` (`estimateDeliveryDays`) a partir de la distancia (fórmula de Haversine) entre `hubRegion` de la tienda y el municipio elegido, más `infraDays` del municipio destino. Esto evita tener que mantener a mano una tabla de días por cada combinación tienda×municipio.

## Siguientes pasos (fuera del MVP)

1. **Datos reales**: reemplazar `data/data.json` por un feed generado (scraper propio con consentimiento/ToS, programa de afiliados, o carga manual vía panel admin). Ojo: scrapear sitios de terceros sin permiso puede violar sus términos de servicio.
2. **Estimación de entrega real**: sustituir `estimateDeliveryDays` (fórmula de distancia) por datos reales de paquetería/tienda cuando estén disponibles.
3. **Más municipios/zonas**: agregar más municipios a las 3 zonas actuales, o zonas nuevas (Puebla, Tijuana, Mérida...) a medida que haya datos logísticos confiables; el modelo de datos ya lo soporta sin cambios de código.
4. **Backend opcional**: si se necesita actualizar precios automáticamente, añadir una función serverless (Cloudflare Workers/Vercel Functions, capa gratuita) que regenere `data.json` en un cron, sin tocar el frontend.
5. **Fichas de producto por tienda real** (enlaces de afiliado en vez de `#`).
