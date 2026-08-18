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
- **Búsqueda abierta (lista para conectar)**: la página de listado tiene una sección "🌐 Más resultados en vivo de Mercado Libre" que se activa sola cuando se conecte la API de búsqueda (ver "Estado de la integración con Mercado Libre" más abajo). El catálogo local (16 productos) sigue existiendo para las fichas con specs/reseñas/gráfico de precio, pero esta sección permite además encontrar productos que no están en ese catálogo, como en Kakaku.com.
- **Precios verificados vs. de referencia**: la tabla de comparación está dividida en dos bloques. Arriba, en un recuadro verde destacado, van las tiendas cuyo precio viene **en vivo de una API real** (ninguna todavía — ver abajo). Debajo, en un bloque más discreto, van las tiendas sin API conectada, marcadas explícitamente como "precio de referencia (no verificado)". Esto evita presentar datos de demostración como si fueran precios reales.
- **Banner de entrega destacado**: en la ficha de producto, justo arriba de la tabla de comparación, un banner grande (no un botón pequeño escondido) invita a elegir tu municipio; una vez elegido, se pone verde y confirma "✓ Mostrando entrega a {municipio}".
- **Entrega y envío marcados como estimación**: junto a cada línea de "Entrega en N días · envío $X" aparece una etiqueta "🔶 estimado", igual que el bloque de precios de referencia — porque hoy ningún sitio tiene una API de paquetería conectada, esto sigue siendo 100% cálculo por distancia (ver `estimateDeliveryDays`/`estimateShippingFee`), nunca un dato confirmado con la tienda.
- **Diferencia con Kakaku (única parte no clonada)**: en vez de cubrir todo México, la entrega se compara solo en **3 zonas metropolitanas** (CDMX, Guadalajara, Monterrey), porque fuera de ellas la infraestructura logística es demasiado irregular para una estimación confiable. Dentro de cada zona el pin se elige **por municipio/alcaldía** (p. ej. Cuauhtémoc, Zapopan, San Pedro Garza García). Al elegir un municipio, la tabla muestra el **precio más barato**, la **entrega más rápida** y el **costo de envío ajustado a esa distancia** — los tres juntos, justo debajo del precio de cada tienda (no solo en la columna "Envío" aparte, que se sigue mostrando y queda siempre consistente con lo que dice esa línea). Un envío que ya es gratis se mantiene gratis sin importar la distancia; el resto sube un poco por cada ~200 km fuera de la zona metropolitana de origen y por zonas con `infraDays` (menor confiabilidad logística).

### Diseño informado por psicología del consumidor / economía conductual

Cada elemento de esta lista usa **datos reales que ya existían en la app** (no números inventados ni contadores falsos) para reforzar la decisión de compra en el momento adecuado:

- **"Ahorras $X" junto al %** (efecto de encuadre / *framing*, Tversky & Kahneman): el mismo descuento se percibe distinto en porcentaje que en dinero; se muestran los dos a la vez para no depender de que cada persona haga la cuenta.
- **"🔥 Precio mínimo del mes"**: aparece junto al precio principal (no solo al fondo, en el gráfico) cuando el precio de hoy es real y verificablemente el más bajo de los últimos 30 días — mismo cálculo que ya alimenta `renderPriceHistoryChart`, solo movido a donde se decide la compra. Es una señal de urgencia honesta (aversión a la pérdida), no una cuenta regresiva ni un "solo por hoy" falso.
- **"🏆 Recomendado"** (arquitectura de decisión / reduce la sobrecarga de elección, Iyengar & Lepper): una segunda etiqueta, visualmente distinta de "MÁS BARATO" (dorada, no roja), que pondera precio + calificación + disponibilidad inmediata. Solo aparece cuando de verdad difiere de la oferta más barata — p. ej. cuando la más barata está sobre pedido y otra, casi al mismo precio, tiene entrega inmediata — nunca para empujar hacia una opción más cara sin una razón real.
- **Punto pulsante en "Últimas piezas"** (escasez, Cialdini): llama la atención sobre una escasez que ya estaba en los datos (`stock: "low_stock"`), sin agregar un número ni un temporizador inventado.
- **"🔒 Compra en el sitio real de la tienda"** junto a cada botón: reduce la incertidumbre de salir del sitio antes de hacer clic, sin prometer nada que ComparaMX no hace (no hay checkout propio).

## Marcas y ofertas (`#/marcas`)

Catálogo de programas de afiliados de **Admitad**, aparte del comparador de electrónica: **52 marcas** de moda, viajes, educación, software/IA, VPN, hosting, belleza, joyería, hogar y finanzas, agrupadas en 13 categorías con filtro lateral. Cada tarjeta enlaza directo al programa de afiliado real (`rel="sponsored"`, se abre en pestaña nueva) — a diferencia del resto del sitio, **estos son enlaces reales**, no `#` de demostración.

- **Origen de los datos**: `data/brands.json`, construido a partir de los 54 programas a los que el operador del sitio se unió en Admitad (nombre, categoría y descripción tomados de una hoja de cálculo que llevaba; los enlaces y logos, de las capturas de cada pantalla "Join program").
- **Qué se excluyó y por qué**: de 54 programas originales quedaron 52 —
  - **LoveMachines** (contenido para adultos): fuera de lugar en un sitio de comparación de propósito general sin una sección o aviso de edad dedicados.
  - **Admitad**: es la propia red de afiliados, no una tienda a la que enlazar.
- **Por qué es una sección aparte y no está mezclada con la electrónica**: son marcas de rubros completamente distintos (VPN, tours, cursos de inglés, joyería...) sin relación con "comparar el precio de un iPhone entre tiendas mexicanas". Meterlas en el mismo catálogo habría diluido lo que hace específico a ComparaMX.
- **Logos**: recortados de las capturas de pantalla de Admitad (no hay archivos de marca oficiales), en `icons/brands/`. Cargan con `loading="lazy"` porque son 52 imágenes.

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
index.html          página única con 6 vistas: inicio, listado, ficha de producto, marcas y ofertas, favoritos y mi cuenta
css/style.css        estilos (paleta Mercari)
js/app.js             lógica: rutas por hash, rankings, filtros/orden, mapa, comparación, marcas y ofertas, favoritos/perfil/reseñas (localStorage)
data/data.json        categorías, productos (specs, reseñas, ofertas con stock), tiendas, regiones (datos de demo)
data/brands.json      catálogo de 52 marcas afiliadas (Admitad), fuera del comparador de electrónica
icons/brands/          logos de las 52 marcas, recortados de las capturas de Admitad
icons/, manifest.json, sw.js   PWA
backend/mercadolibre-worker/   Cloudflare Worker + guía para conectar la API real de Mercado Libre (opcional, desactivado por defecto)
scripts/generate_seo_pages.py  genera producto/, categoria/, sitemap.xml y robots.txt (ver "Páginas estáticas para SEO" más abajo)
producto/<id>/, categoria/<slug>/   páginas estáticas generadas, una por producto y por categoría — no se editan a mano
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
- `products[].offers[].verified`: `true` si el precio viene de una API real (ninguna oferta lo tiene por ahora), `false` si es dato de demostración. Controla en cuál de los dos bloques de la tabla aparece la oferta.
- `products[].image`: emoji que representa al producto. Es lo que se ve por defecto, porque el catálogo local **no incluye fotos** (ver "Fotos de producto" más abajo).
- `products[].photo` (opcional): URL de la foto real del producto. Si está presente, sustituye al emoji en la portada, el listado y la ficha. El repo no trae ninguna; la llena sola la API de Mercado Libre cuando se conecta.

## Fotos de producto

La ficha muestra un emoji, no una foto. No es una limitación técnica —el soporte de fotos ya está implementado y probado— sino de **derechos sobre las imágenes**: las fotos de producto son de las tiendas o de los fabricantes, y enlazarlas directamente desde sus servidores (*hotlinking*) consume su ancho de banda, suele violar sus términos de servicio y se rompe en cuanto cambian la URL. Por eso el repo no incluye ninguna foto ni ninguna URL a fotos ajenas.

La vía legítima es la API: la respuesta de Mercado Libre incluye la foto del anuncio (`secure_thumbnail`), y usarla para mostrar el producto al que se enlaza es justamente para lo que sirve. El Worker ya la devuelve como `photo`, y el frontend la adopta automáticamente (`refreshLiveOffers` → `product.photo`). Es decir: **en cuanto conectes la API de Mercado Libre, sus productos pasan a mostrar la foto real sin tocar más código**; las tiendas sin API se quedan con el emoji.

Esto no es algo cableado solo para Mercado Libre: `fetchLiveOffer()` recibe la foto en un campo genérico (`photo`) y `LIVE_API_CONFIG` ya trae una entrada `{ enabled: false, proxyUrl: null }` para las 5 tiendas del catálogo (Amazon México, Mercado Libre, Walmart México, Liverpool, Costco México), no solo para Mercado Libre. Hoy las otras 4 no tienen ningún backend real detrás, así que se quedan en `false`/`null` y siguen mostrando su emoji. Pero si en el futuro alguna ofrece un partner API accesible, el mismo patrón que usa `backend/mercadolibre-worker/` (un Worker que guarda las credenciales y devuelve `{ price, photo, ... }`) se replica para esa tienda, se pega su URL en su entrada de `LIVE_API_CONFIG`, se pone `enabled: true`, y su precio y su foto real aparecen solos, sin tocar `renderProductMedia` ni ningún otro código de render.

Detalles de la implementación (`renderProductMedia` en `js/app.js`):

- Si no hay `photo`, se muestra el emoji de siempre — el diseño actual no cambia en absoluto.
- Si la URL falla (enlace roto, CDN caído, bloqueo de hotlinking), el `onerror` vuelve al emoji en vez de dejar el icono de imagen rota.
- La imagen se ajusta con `object-fit: contain`, así que no se deforma ni se sale del recuadro sea cual sea su proporción.

### ¿Por qué Amazon México (amazon_mx) no está conectado?

Sí existe una API de productos de Amazon (**Product Advertising API**, sustituida en 2026 por la **Creators API** — la PA-API v5 se retiró el 15 de mayo de 2026) y sí cubre el marketplace de México (`amazon.com.mx`, credenciales propias por marketplace). El problema no es que no exista, sino a quién se la dan: es exclusiva del programa de afiliados **Amazon Associates**, y no basta con estar inscrito — la Creators API exige que la cuenta ya tenga **10 ventas de afiliado calificadas en los últimos 30 días** para obtener y mantener el acceso (antes, con la PA-API, eran 3 ventas en 180 días para el acceso inicial y >10/mes para mantenerlo). Es un problema de huevo y gallina para un sitio nuevo: no hay forma de conseguir acceso a la API sin ventas de afiliado ya en marcha, y no hay ventas sin el sitio ya funcionando con tráfico real. Por eso `amazon_mx` se queda con la misma entrada vacía que las demás tiendas sin API — no por falta de investigación, sino porque el acceso está condicionado a un volumen de negocio que ComparaMX no tiene todavía.

La Selling Partner API (SP-API) de Amazon tampoco sirve para esto: es para que un vendedor ya registrado administre su propio inventario y pedidos, no para consultar el catálogo general de la tienda.

## Páginas estáticas para SEO

ComparaMX es una SPA: todo el contenido se pinta con JavaScript y las rutas van por `#hash` (`#/p/p1`). Para un buscador eso es un problema doble — una página que no ejecute JS ve una pantalla en blanco, y aunque la ejecute, un `#` no cuenta como una URL distinta para indexar, así que las 16 fichas de producto competirían todas por la misma URL "/". Kakaku.com, la referencia de este proyecto, sí tiene una URL real por producto; eso es lo que replica esta parte.

`scripts/generate_seo_pages.py` lee `data/data.json` y genera, ya con el contenido renderizado en el HTML (visible sin ejecutar JS):

- `producto/<id>/index.html` — una página por producto, con `<title>`/`<meta description>`/Open Graph/canonical, datos estructurados `schema.org Product` (JSON-LD, con `AggregateOffer` y `AggregateRating`) y la tabla comparativa de precios ya en el HTML.
- `categoria/<slug>/index.html` — una por categoría, con la lista de productos y su precio.
- `sitemap.xml` y `robots.txt` en la raíz, listando todas las URLs anteriores.

Cada página estática enlaza de vuelta a la SPA interactiva (mapa de entrega, historial de precio, reseñas) con un botón "Abrir ComparaMX interactivo →" — sirven para que un buscador indexe contenido real y para la primera impresión de quien llega desde una búsqueda, no para reemplazar la app.

**Cuándo correrlo**: cada vez que cambie `data/data.json` (precio, producto o tienda nueva).

```
python3 scripts/generate_seo_pages.py
```

No es un paso de build obligatorio — `index.html` sigue funcionando igual sin esto —, es un generador opcional que hay que volver a correr y commitear cuando cambien los datos; no se regenera solo en cada visita ni en cada deploy.

**Antes de desplegar a producción**: edita `SITE_URL` al inicio del script con el dominio real y vuelve a correrlo. Ahora mismo genera con `https://comparamx.example` como placeholder — un canonical o una URL de Open Graph apuntando a un dominio de ejemplo es peor para SEO que no tenerlas, así que el script imprime un aviso si detecta que sigue en ese valor.

## Estado de la integración con Mercado Libre

Por decisión explícita, ComparaMX solo integra la unidad de negocio **Mercado Libre** de su plataforma de desarrolladores (no Global Selling, Mercado Envíos ni Mercado Pago — esas sirven para vender, enviar o cobrar, y ComparaMX no hace ninguna de las tres cosas; solo compara y enlaza a la tienda real).

Ninguna tienda tiene datos en vivo todavía — **todas las ofertas están marcadas `"verified": false`**. Lo que sí está listo de antemano:

- **El frontend** (`js/app.js` → `LIVE_API_CONFIG`): apenas se le da una URL de backend y se pone `enabled: true`, empieza a mostrar precios reales sin tocar nada más del código.
- **El backend**: `backend/mercadolibre-worker/` tiene un Cloudflare Worker completo (capa gratuita) listo para desplegar, más una guía paso a paso (`backend/mercadolibre-worker/README.md`) para registrar tu app en Mercado Libre, completar el flujo OAuth 2.0 y desplegarlo. **No lo pude probar en vivo**: este entorno no tiene tus credenciales ni acceso de red a la API de Mercado Libre (bloquea las peticiones desde este sandbox con 403, tanto al API como al portal de desarrolladores) — verifica tú las respuestas reales una vez desplegado.

Una vez que sigas esa guía y despliegues el Worker, solo falta pegar sus dos URLs en `LIVE_API_CONFIG.mercadolibre` (`proxyUrl` y `searchProxyUrl`).

## Juntar el mismo producto entre tiendas (`scripts/product_matcher.py`)

Cada producto real que hay hoy en el catálogo viene de **una sola tienda** (SUNSKY o Geekbuying) porque todavía no hay dos fuentes con el mismo producto físico. `scripts/product_matcher.py` es el algoritmo para cuando sí las haya: dado un lote de ofertas de varias tiendas/feeds, decide cuáles son el mismo producto y las junta en un grupo (una ficha, N ofertas), en vez de crear una ficha por tienda.

Sigue un pipeline de 5 pasos, cada uno con un umbral de confianza más bajo que el anterior:

1. **Identificador único** (JAN/EAN/UPC/ASIN/barcode) — coincidencia exacta. Se descarta si el identificador es sospechoso (todo ceros, longitud rara) o si dos ofertas comparten identificador pero su marca/specs se contradicen (barcode reciclado por error en el feed de origen — pasa de verdad, ver los tests).
2. **Preprocesamiento de texto** — quita ruido de marketing (`[HK Warehouse]`, `Global`, etc.) y extrae specs estructuradas (RAM+almacenamiento, tamaño de pantalla, Hz) y "tokens de modelo" (tanto pegados: `H27T6`, como separados: `Ace 5` → `ACE5`).
3. **Marca + modelo + specs** — mismo fabricante, al menos un token de modelo en común, specs compatibles.
4. **Similitud de texto** — Jaccard de tokens de contenido + similitud de caracteres (sustituto sin dependencias de comparar por embeddings; cambiar solo `similarity_score()` si más adelante hay una API de embeddings disponible). Compara solo dentro del mismo bucket de marca, no todo contra todo, para no ser O(n²) sobre el catálogo completo.
5. **Cola de pendientes** — lo que queda debajo del umbral no se agrupa a ciegas: se guarda con su mejor candidato y un prompt ya armado para que lo resuelva un LLM o una persona.

Probado contra los feeds reales completos de SUNSKY + Geekbuying (3,063 ofertas, corre en <1s): cero falsos positivos, incluidas parejas trampa como "OUKITEL P2001 Plus" (central eléctrica) vs. "Oukitel WP23 Plus" (celular) — misma marca, nombre parecido, pero el score de similitud (0.13-0.16) queda muy por debajo del umbral (0.60) y no se agrupan.

```bash
python3 scripts/test_product_matcher.py   # 20 casos (sintéticos + sobre datos reales)
python3 scripts/product_matcher.py sunsky.csv:sunsky geekbuying.csv:geekbuying
```

## Límites conocidos (no es un clon 1:1 de verdad)

Esto sigue siendo una demo de un solo desarrollador, no Kakaku.com. Lo que falta y por qué no está:

- **Datos e inventario reales**: no hay convenios con tiendas reales; sin eso, "en stock" y los precios son inventados. Requiere partnerships/APIs reales de cada tienda.
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
