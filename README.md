# ComparaMX

Comparador de precios entre tiendas mexicanas, inspirado en [Kakaku.com](https://kakaku.com). MVP de demostración.

## Qué hace

La estructura y funcionalidad siguen de cerca a **Kakaku.com** (excepto el mapa, que es propio de ComparaMX); el color es el de **Mercari** (rojo `#FF0211` sobre blanco) en vez del naranja de Kakaku.

- **Inicio**: rankings por categoría (los más baratos de cada categoría, con medalla de posición), como la portada de Kakaku.
- **Barra de categorías** (bajo el header): navega a una página de listado por categoría.
- **Página de listado** (búsqueda o categoría): barra lateral de filtros (categoría, rango de precio) + selector de orden (relevancia, precio, mejor calificado), como las páginas de categoría de Kakaku.
- **Ficha de producto**: breadcrumb, **evolución de precio (gráfico de los últimos 30 días)**, especificaciones, opiniones de compradores (con formulario para agregar tu propia reseña), y una **tabla de comparación de precios** por tienda con envío, disponibilidad, puntos de recompensa y calificación — el corazón de Kakaku.com.
- **Favoritos** (♡/❤️ en cada producto) y **Mi cuenta** (perfil local + resumen), accesibles desde el header, como el "お気に入り" / "マイページ" de Kakaku.
- **Filtros de listado**: categoría, precio, **marca** y **calificación mínima**, más ordenar por relevancia/precio/calificación.
- **Diferencia con Kakaku (única parte no clonada)**: en vez de cubrir todo México, la entrega se compara solo en **3 zonas metropolitanas** (CDMX, Guadalajara, Monterrey), porque fuera de ellas la infraestructura logística es demasiado irregular para una estimación confiable. Dentro de cada zona el pin se elige **por municipio/alcaldía** (p. ej. Cuauhtémoc, Zapopan, San Pedro Garza García). El botón 📍 "Comparar tiempos de entrega" (arriba a la derecha de la tabla) abre el mapa en una ventana modal; al elegir un municipio, la tabla muestra el **precio más barato** y la **entrega más rápida** justo debajo del precio de cada tienda.
- **Precios verificados vs. de referencia**: la tabla de comparación está dividida en dos bloques. Arriba, en un recuadro verde destacado, van las tiendas cuyo precio viene **en vivo de una API real** (ninguna todavía — ver abajo). Debajo, en un bloque más discreto, van las tiendas sin API conectada, marcadas explícitamente como "precio de referencia (no verificado)". Esto evita presentar datos de demostración como si fueran precios reales.
- **Búsqueda abierta (lista para conectar)**: la página de listado ya tiene una sección "🌐 Más resultados en vivo de Mercado Libre" que se activa sola cuando se conecte la API de búsqueda (ver "Estado de las integraciones" más abajo). El catálogo local (16 productos) seguirá existiendo para las fichas con specs/reseñas/gráfico de precio, pero esta sección permite además encontrar productos que no están en ese catálogo, como en Kakaku.com.

### Favoritos, perfil y reseñas: solo en tu navegador

No hay servidor, base de datos ni login real. "Mi cuenta", los favoritos y las reseñas que escribas se guardan con `localStorage` **solo en el navegador donde los creaste**: no se sincronizan entre dispositivos, no las ve nadie más y se pierden si borras los datos del sitio. Es una simulación de cuenta de usuario, no una cuenta real — lo digo explícitamente para no dar una impresión falsa de "comunidad" que en realidad no existe todavía.

## Costo: cero, salvo el hosting

Es un sitio 100% estático (HTML/CSS/JS sin build step):

- **Mapa**: [Leaflet](https://leafletjs.com) (vía CDN) + tiles de OpenStreetMap — sin API key, sin cuenta de facturación (a diferencia de Google Maps).
- **Datos**: `data/data.json`, editable a mano o generable por script. Sin base de datos.
- **Hosting**: se puede publicar gratis en GitHub Pages, Cloudflare Pages, Netlify o Vercel (capa gratuita). No requiere backend.
- **PWA**: `manifest.json` + `sw.js` permiten "Instalar app" desde el navegador y uso offline básico.

## Estructura

```
index.html          página única con 5 vistas: inicio, listado, ficha de producto, favoritos y mi cuenta
css/style.css        estilos (paleta Mercari)
js/app.js             lógica: rutas por hash, rankings, filtros/orden, mapa, comparación, favoritos/perfil/reseñas (localStorage)
data/data.json        categorías, productos (specs, reseñas, ofertas con stock), tiendas, regiones (datos de demo)
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
- `products[].offers[]`: por tienda, `price`, `url`, `shippingFee`, `points` (% de recompensa), `rating`/`reviewCount` (de esa tienda) y `stock` (`in_stock` / `low_stock` / `backorder`). El tiempo de entrega **no** se guarda por región: se calcula en `js/app.js` (`estimateDeliveryDays`) a partir de la distancia (fórmula de Haversine) entre `hubRegion` de la tienda y el municipio elegido, más `infraDays` del municipio destino y un margen extra si el `stock` es `backorder`.
- El **historial de precio de 30 días** que se ve en la ficha de producto no está en `data.json`: se genera en el navegador (`generatePriceHistory`) con una caminata aleatoria determinista (misma semilla = mismo gráfico siempre) que termina en el precio actual. Es una simulación, no datos reales.

## Estado de las integraciones de API reales

Ninguna tienda tiene datos en vivo todavía — **todas las ofertas en `data.json` están marcadas `"verified": false`** y aparecen en el bloque "de referencia". Lo que sí está listo de antemano es la mecánica del frontend (ver "Cómo activar Mercado Libre" más abajo): en cuanto haya credenciales reales, no hace falta rediseñar nada, solo apuntar `LIVE_API_CONFIG` a un backend propio.

**Hallazgo importante:** al investigar más a fondo, todas las opciones comparten el mismo obstáculo estructural, no solo Mercado Libre. En ningún caso esto se puede resolver escribiendo más código o investigando más — hace falta que **el dueño del proyecto** (no un asistente) se registre como negocio/publisher y pase por una aprobación:

| Tienda | ¿API/afiliados disponible? | Notas |
|---|---|---|
| Mercado Libre | 🟡 Requiere app + OAuth | Probado en vivo: ya no hay endpoints públicos sin autenticación (403 `PolicyAgent`). Hace falta una app registrada en developers.mercadolibre.com.mx, flujo OAuth 2.0, y un backend propio para guardar el `client_secret` |
| Walmart México, Coppel, Elektra | 🟡 Requiere cuenta de publisher aprobada en Admitad | Admitad sí ofrece feeds de productos, pero solo **después de que Admitad apruebe tu cuenta como publisher y te acepten en el programa de esa tienda específica** — no es autoservicio inmediato, y una cuenta nueva sin tráfico puede ser rechazada |
| Liverpool | 🟡 Requiere cuenta de publisher aprobada en Awin | Mismo mecanismo que Admitad: cuenta de publisher + aprobación por programa, y no todos los anunciantes de Awin publican feed de productos |
| Walmart Marketplace API (developer.walmart.com/mx) | ❌ No sirve para esto | Corrección: **esta API es para vendedores que publican SUS productos en el marketplace de Walmart**, no para leer los precios de Walmart como tercero. No resuelve nuestro caso de uso |
| Amazon México | 🔴 No disponible ahora | PA-API dejó de aceptar clientes nuevos y se retiró (abr–may 2026). Su reemplazo (Creators API) exige 10 ventas calificadas en los últimos 30 días como afiliado — imposible para un sitio nuevo sin tráfico |
| Costco México | 🔴 Probablemente no | El programa de afiliados de Costco es explícitamente solo para EE. UU. |
| Best Buy México, Office Depot México, Chedraui, Soriana, Sears/Sanborns, Linio | 🔴 No encontrado | Sin programa de afiliados/API público confirmado |

**En resumen: hoy, ninguna integración real es técnicamente accionable por un asistente.** Todas requieren que tú, como negocio, te registres y esperes aprobación en Admitad, Awin y/o Mercado Libre — y ni así hay garantía de aceptación para un sitio nuevo sin tráfico.

### Cómo activar Mercado Libre cuando tengas las credenciales

1. Regístrate en developers.mercadolibre.com.mx, crea una app y obtén `client_id`/`client_secret`.
2. Completa el flujo OAuth 2.0 (requiere que un usuario de Mercado Libre autorice la app) para obtener un `access_token` (y su renovación vía `refresh_token`).
3. Monta un endpoint propio (función serverless, capa gratuita de Cloudflare Workers o similar) con dos rutas:
   - Una que reciba la búsqueda de **un producto ya conocido del catálogo** y devuelva un único resultado `{ price, url, shippingFree, stock }` — usada para poner precios reales a los 16 productos curados.
   - Otra de **búsqueda abierta**, que reciba cualquier término escrito por el usuario y devuelva varios resultados: `{ items: [{ id, title, price, url, shippingFree, stock }] }` — esta es la que hace posible "busca cualquier producto y lo encuentra", como Kakaku.com, en vez de limitarse a los productos ya cargados a mano.
4. En `js/app.js`, en `LIVE_API_CONFIG`, pon `mercadolibre: { enabled: true, proxyUrl: "https://tu-endpoint/item", searchProxyUrl: "https://tu-endpoint/search" }`.
   - `refreshLiveOffers` ya está lista para tomar la respuesta de la primera ruta, marcarla `verified: true` y moverla automáticamente al bloque destacado de la ficha de producto.
   - `fetchLiveSearchResults`/`renderLiveSearchSection` ya están listas para tomar la respuesta de la segunda ruta y mostrar una sección "🌐 Más resultados en vivo de Mercado Libre" en la página de listado cada vez que una búsqueda no encuentre (o para complementar lo que sí encuentre) en el catálogo local. Esos resultados no tienen ficha de producto propia (sin specs/reseñas nuestras): al hacer clic llevan directo al anuncio real en Mercado Libre.
   - No hace falta tocar nada más del frontend — mientras `enabled` esté en `false` (como está por defecto), ninguna de las dos rutas se llama y el comportamiento actual (catálogo local únicamente) no cambia.

## Límites conocidos (no es un clon 1:1 de verdad)

Esto sigue siendo una demo de un solo desarrollador, no Kakaku.com. Lo que falta y por qué no está:

- **Datos e inventario reales**: no hay convenios con tiendas reales; sin eso, "en stock" y los precios son inventados. Requiere partnerships/APIs reales de cada tienda (ver tabla de arriba).
- **Cuentas de usuario reales**: "Mi cuenta"/favoritos/reseñas viven solo en `localStorage` de tu navegador (ver arriba). Una cuenta real necesita backend + autenticación + base de datos.
- **Reseñas y foro de preguntas (掲示板) a escala**: las reseñas que escribes solo las ves tú; no hay moderación, verificación de compra ni comunidad real detrás.
- **Motor de búsqueda avanzado**: la búsqueda es un `includes()` sobre nombre/marca/categoría; no hay autocompletado, tolerancia a errores de tipeo ni búsqueda por especificación técnica.
- **Ingresos por afiliados**: los enlaces "Ver oferta" son `#`; no hay integración real de afiliados ni tracking de conversiones.
- **Otras verticales de Kakaku** (seguros, hipotecas, viajes, autos): fuera de alcance a propósito — son negocios distintos con modelos de datos distintos, no algo que un comparador de electrónica deba fingir tener.
- **Infraestructura a escala**: sitio 100% estático sin backend ni base de datos; correcto para una demo, no para tráfico real de producción.

## Siguientes pasos (fuera del MVP)

1. **Datos reales**: reemplazar `data/data.json` por un feed generado (scraper propio con consentimiento/ToS, programa de afiliados, o carga manual vía panel admin). Ojo: scrapear sitios de terceros sin permiso puede violar sus términos de servicio.
2. **Estimación de entrega real**: sustituir `estimateDeliveryDays` (fórmula de distancia) por datos reales de paquetería/tienda cuando estén disponibles.
3. **Más municipios/zonas**: agregar más municipios a las 3 zonas actuales, o zonas nuevas (Puebla, Tijuana, Mérida...) a medida que haya datos logísticos confiables; el modelo de datos ya lo soporta sin cambios de código.
4. **Backend opcional**: si se necesita actualizar precios automáticamente o tener cuentas reales, añadir una función serverless o un backend mínimo (capa gratuita) en vez de `localStorage`.
5. **Fichas de producto por tienda real** (enlaces de afiliado en vez de `#`).
