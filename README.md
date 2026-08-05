# ComparaMX

Comparador de precios entre tiendas mexicanas, inspirado en [Kakaku.com](https://kakaku.com). MVP de demostración.

## Qué hace

La estructura y funcionalidad siguen de cerca a **Kakaku.com** (excepto el mapa, que es propio de ComparaMX); el color es el de **Mercari** (rojo `#FF0211` sobre blanco) en vez del naranja de Kakaku.

- **Inicio**: rankings por categoría (los más baratos de cada categoría, con medalla de posición), como la portada de Kakaku.
- **Barra de categorías** (bajo el header): navega a una página de listado por categoría.
- **Página de listado** (búsqueda o categoría): barra lateral de filtros (categoría, rango de precio) + selector de orden (relevancia, precio, mejor calificado), como las páginas de categoría de Kakaku.
- **Ficha de producto**: breadcrumb, especificaciones, opiniones de compradores, y una **tabla de comparación de precios** por tienda con envío, puntos de recompensa y calificación de la tienda — el corazón de Kakaku.com.
- **Diferencia con Kakaku (única parte no clonada)**: en vez de cubrir todo México, la entrega se compara solo en **3 zonas metropolitanas** (CDMX, Guadalajara, Monterrey), porque fuera de ellas la infraestructura logística es demasiado irregular para una estimación confiable. Dentro de cada zona el pin se elige **por municipio/alcaldía** (p. ej. Cuauhtémoc, Zapopan, San Pedro Garza García). El botón 📍 "Comparar tiempos de entrega" (arriba a la derecha de la tabla) abre el mapa en una ventana modal; al elegir un municipio, la tabla muestra el **precio más barato** y la **entrega más rápida** justo debajo del precio de cada tienda.

## Costo: cero, salvo el hosting

Es un sitio 100% estático (HTML/CSS/JS sin build step):

- **Mapa**: [Leaflet](https://leafletjs.com) (vía CDN) + tiles de OpenStreetMap — sin API key, sin cuenta de facturación (a diferencia de Google Maps).
- **Datos**: `data/data.json`, editable a mano o generable por script. Sin base de datos.
- **Hosting**: se puede publicar gratis en GitHub Pages, Cloudflare Pages, Netlify o Vercel (capa gratuita). No requiere backend.
- **PWA**: `manifest.json` + `sw.js` permiten "Instalar app" desde el navegador y uso offline básico.

## Estructura

```
index.html          página única con 3 vistas: inicio (rankings), listado (filtros) y ficha de producto
css/style.css        estilos (paleta Mercari)
js/app.js             lógica: rutas por hash, rankings, filtros/orden, mapa, tabla de comparación
data/data.json        categorías, productos (specs, reseñas, ofertas), tiendas, regiones (datos de demo)
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
