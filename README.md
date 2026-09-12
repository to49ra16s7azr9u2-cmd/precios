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
- **Búsqueda abierta (lista para conectar)**: la página de listado tiene una sección "🌐 Más resultados en vivo de Mercado Libre" que se activa sola cuando se conecte la API de búsqueda (ver "Estado de la integración con Mercado Libre" más abajo). El catálogo local (42 productos) sigue existiendo para las fichas con specs/reseñas, pero esta sección permite además encontrar productos que no están en ese catálogo, como en Kakaku.com.
- **Precios verificados vs. de referencia**: la tabla de comparación está dividida en dos bloques. Arriba, en un recuadro verde destacado, van las tiendas cuyo precio viene **en vivo de una API real** (ninguna todavía — ver abajo). Debajo, en un bloque más discreto, van las tiendas sin API conectada, marcadas explícitamente como "precio de referencia (no verificado)". Esto evita presentar datos de demostración como si fueran precios reales.
- **Banner de entrega destacado**: en la ficha de producto, justo arriba de la tabla de comparación, un banner grande (no un botón pequeño escondido) invita a elegir tu municipio; una vez elegido, se pone verde y confirma "✓ Mostrando entrega a {municipio}".
- **Entrega y envío marcados como estimación**: junto a cada línea de "Entrega en N días · envío $X" aparece una etiqueta "🔶 estimado", igual que el bloque de precios de referencia — porque hoy ningún sitio tiene una API de paquetería conectada, esto sigue siendo 100% cálculo por distancia (ver `estimateDeliveryDays`/`estimateShippingFee`), nunca un dato confirmado con la tienda.
- **Cobertura de entrega nacional**: las 32 entidades de México están cubiertas en el selector de ubicación (la barra de pestañas se desplaza horizontalmente para verlas todas). Ciudad de México, Guadalajara y Monterrey tienen varios **municipios/alcaldías** reales para elegir (p. ej. Cuauhtémoc, Zapopan, San Pedro Garza García), porque son las únicas zonas con varios pines cargados; el resto de los estados usa un solo punto de referencia, la capital estatal, así que el estimado varía más dentro de un estado grande que dentro de esas 3 zonas. Al elegir una región, la tabla muestra el **precio más barato**, la **entrega más rápida** y el **costo de envío ajustado a esa distancia** — los tres juntos, justo debajo del precio de cada tienda (no solo en la columna "Envío" aparte, que se sigue mostrando y queda siempre consistente con lo que dice esa línea). Un envío que ya es gratis se mantiene gratis sin importar la distancia; el resto sube un poco por cada ~200 km fuera de la zona metropolitana de origen y por regiones con `infraDays` (menor confiabilidad logística).

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

- `metros`: las 32 entidades de México (id, nombre, centro y zoom del mapa para esa entidad). Solo `cdmx`/`gdl`/`mty` tienen varios municipios reales; las otras 29 son un solo punto (su capital).
- `regions`: municipios/alcaldías dentro de `cdmx`/`gdl`/`mty`, o la capital estatal para las otras 29 entidades (`metro`, nombre, lat/lng, `infraDays`: días extra por confiabilidad logística local — p. ej. zonas periféricas como Xochimilco o Tlajomulco suman 1 día, capitales más alejadas de las rutas troncales suman 2).
- `stores`: tiendas comparadas, con `hubRegion` (municipio donde está el centro de distribución de la tienda; `null` si la tienda envía desde fuera de México, como SUNSKY o Geekbuying).
- `products[].offers[]`: por tienda, `price`, `url`, `shippingFee`, `points` (% de recompensa), `rating`/`reviewCount` (de esa tienda) y `stock` (`in_stock` / `low_stock` / `backorder`). El tiempo de entrega **no** se guarda por región: se calcula en `js/app.js` (`estimateDeliveryDays`) a partir de la distancia (fórmula de Haversine) entre `hubRegion` de la tienda y la región elegida, más `infraDays` de la región destino y un margen extra si el `stock` es `backorder`.
- `products[].offers[].verified`: `true` si el precio viene de una API real (ninguna oferta lo tiene por ahora), `false` si es dato de demostración o de un feed de afiliados (ver "🔶 Precios de referencia" en la app). Controla en cuál de los dos bloques de la tabla aparece la oferta.
- `products[].image`: emoji que representa al producto. Se usa como respaldo cuando no hay `photo`.
- `products[].photo` (opcional): URL de la foto real del producto, tomada del feed de la tienda o rellenada por la API de Mercado Libre cuando se conecta. Si está presente, sustituye al emoji en la portada, el listado y la ficha.

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

## Rastreadores de IA

El sitio pide no ser usado para entrenar modelos, por tres vías, y conviene
saber cuál funciona de verdad:

| Dónde | Qué hace | ¿Activo hoy? |
|---|---|---|
| `robots.txt` | Bloquea por nombre ~30 rastreadores de IA (GPTBot, ClaudeBot, CCBot, PerplexityBot, Bytespider…) | **Sí** |
| `<meta name="robots" content="index, follow, noai, noimageai">` | Señal en el HTML de cada página | **Sí** |
| `_headers` (`X-Robots-Tag: noai, noimageai`) | Misma señal en la cabecera HTTP | **No** |

`_headers` está escrito en el formato de Cloudflare Pages y Netlify, pero
comparamex.com lo sirve GitHub Pages, que ni lee ese archivo ni permite
cabeceras propias — `curl -I https://comparamex.com/` devuelve
`server: GitHub.com` y ninguna `X-Robots-Tag`. El archivo se conserva para
que empiece a aplicarse solo si algún día se mueve el hosting; mientras
tanto no hace nada, y su propio comentario lo dice.

Las tres vías son peticiones, no barreras: dependen de que el rastreador se
identifique con su nombre real y obedezca. Desde un hosting estático no hay
manera de forzarlo. Un bloqueo de verdad — que mira la huella de la
conexión en vez de creerle al User-Agent — requiere un proxy delante, por
ejemplo el "Block AI Bots" de Cloudflare.

## Estado de la integración con Mercado Libre

Por decisión explícita, ComparaMX solo integra la unidad de negocio **Mercado Libre** de su plataforma de desarrolladores (no Global Selling, Mercado Envíos ni Mercado Pago — esas sirven para vender, enviar o cobrar, y ComparaMX no hace ninguna de las tres cosas; solo compara y enlaza a la tienda real).

Ninguna tienda tiene datos en vivo todavía — **todas las ofertas están marcadas `"verified": false`**. Lo que sí está listo de antemano:

- **El frontend** (`js/app.js` → `LIVE_API_CONFIG`): apenas se le da una URL de backend y se pone `enabled: true`, empieza a mostrar precios reales sin tocar nada más del código.
- **El backend**: `backend/mercadolibre-worker/` tiene un Cloudflare Worker completo (capa gratuita) listo para desplegar, más una guía paso a paso (`backend/mercadolibre-worker/README.md`) para registrar tu app en Mercado Libre, completar el flujo OAuth 2.0 y desplegarlo. **No lo pude probar en vivo**: este entorno no tiene tus credenciales ni acceso de red a la API de Mercado Libre (bloquea las peticiones desde este sandbox con 403, tanto al API como al portal de desarrolladores) — verifica tú las respuestas reales una vez desplegado.

Una vez que sigas esa guía y despliegues el Worker, solo falta pegar sus dos URLs en `LIVE_API_CONFIG.mercadolibre` (`proxyUrl` y `searchProxyUrl`).

## Cómo entran productos nuevos

Tres caminos, según la tienda:

- **Tiendas VTEX (Elektra, Chedraui, Martí)** — `scripts/vtex_stores.py`
  declara cada tienda (dominio, ids de categoría y a qué categoría del sitio
  va cada una); `scripts/add_vtex_products.py --store chedraui --preset todo`
  las carga y `scripts/refresh_vtex.py --store chedraui` las refresca (el
  workflow diario corre las tres). Cualquier otra tienda mexicana sobre VTEX
  entra con una entrada más en ese registro: se probaron 30 dominios de
  retail y solo esos tres exponen la API pública de catálogo.
- **Mercado Libre** — `scripts/ml_discover.py` corre todos los días en el
  workflow: toma una ventana de subcategorías del sitio, confirma contra el
  propio catálogo a qué dominio de Mercado Libre corresponde cada una y da
  de alta lo que todavía no tenemos, con categoría puesta y la subcategoría
  a cargo de `clasificar_subcategorias.py`. Para una carga dirigida sigue
  valiendo `scripts/add_products.py targets.json`.
- **Amazon México** — sin API (ver arriba). `scripts/captura_amazon.html`
  es un marcador para el navegador que, en una página de resultados de
  amazon.com.mx, copia al portapapeles los productos de la página en el JSON
  que entienden `match_amazon_capture.py` y `add_amazon_standalone.py`.

## Juntar el mismo producto entre tiendas (`scripts/product_matcher.py`)

Cada producto real que hay hoy en el catálogo viene de **una sola tienda** (SUNSKY, Geekbuying, Molnija Shop, StyleWE, Glasseslit o Woodestic) porque todavía no hay dos fuentes con el mismo producto físico. `scripts/product_matcher.py` es el algoritmo para cuando sí las haya: dado un lote de ofertas de varias tiendas/feeds, decide cuáles son el mismo producto y las junta en un grupo (una ficha, N ofertas), en vez de crear una ficha por tienda.

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

## Límites conocidos

Lo que el sitio **no** hace, para que nadie se lo imagine leyendo lo demás.
Los números son una foto del catálogo publicado, no una promesa: salen de
correr los scripts sobre `data/`, así que envejecen a medida que entra
producto nuevo. Para recalcular el primero:

```bash
python3 -c "import sys,collections; sys.path.insert(0,'scripts'); \
from data_io import load_catalog; d=load_catalog(); \
c=collections.Counter(len({o['storeId'] for o in p.get('offers') or []}) \
for p in d['products']); t=sum(c.values()); m=sum(n for k,n in c.items() if k>=2); \
print(f'{m:,} de {t:,} ({100*m/t:.1f}%) con 2+ tiendas')"
```

- **Comparar el mismo producto entre tiendas es la excepción**: de 92,565
  fichas, 16,953 (18.3%) tienen ofertas de 2 o más tiendas; las otras 75,612
  tienen una sola. No es un defecto del agrupador, es la composición del
  catálogo: cada tienda vende modelos distintos, y solo se agrupa cuando hay
  GTIN igual o una firma de producto que aguanta revisión. Un comparador que
  fusionara a ciegas para inflar ese número mostraría el precio de un
  producto en la ficha de otro, que es el peor error posible acá.
- **No hay convenio con ninguna de las 14 tiendas**: los precios se leen de
  sus sitios públicos y sus APIs abiertas, no de un feed acordado. Si una
  tienda cambia su HTML o corta el acceso, esa tienda deja de actualizarse
  hasta que se arregle el script. Los enlaces "Ver oferta" van directo a la
  tienda y **no dejan comisión**; los únicos enlaces de afiliado del sitio
  son los 72 de la sección "Marcas y ofertas".
- **El precio es el de la última corrida, no el de este segundo**: el job
  nocturno (09:00 UTC) relee lo que puede y anota el precio del día en el
  historial. Entre corrida y corrida el precio mostrado puede estar viejo, y
  el del sitio de la tienda manda siempre.
- **"En stock" es lo que dijo la tienda la última vez que se pudo leer**, y
  los productos no se borran cuando se agotan: la ficha y su historial de
  precios se quedan, porque saber qué valía algo que ya no se consigue
  también sirve.
- **Cuentas, favoritos y reseñas viven en el navegador**: `localStorage`, sin
  servidor ni autenticación. Se pierden al limpiar el navegador, no viajan a
  otro dispositivo y nadie más las ve. No hay moderación ni verificación de
  compra, así que no son reseñas de una comunidad: son notas propias.
- **La entrega es una estimación por distancia**, no un dato de paquetería:
  `estimateDeliveryDays` calcula sobre la distancia al hub de la tienda. 29
  de las 32 entidades usan un solo punto (su capital), así que dentro de un
  estado grande el número es grueso.
- **Las specs son las que la tienda publicó**: no se verifican contra el
  fabricante. Cuando el título no alcanza para decidir una subcategoría o
  una marca, el campo queda vacío en vez de rellenarse con una suposición.
- **Otras verticales de Kakaku** (seguros, hipotecas, viajes, autos): fuera
  de alcance a propósito. Son negocios distintos, no algo que un comparador
  de productos deba fingir tener.
- **Sitio 100% estático**: sin backend ni base de datos. Todo lo dinámico se
  resuelve en el navegador o se precalcula en el build, lo que fija el techo
  de lo que se puede ofrecer (nada de alertas de precio por correo, por
  ejemplo).

## Siguientes pasos

1. **Cerrar el círculo del afiliado**: las tiendas comparadas hoy no dejan
   comisión. Las solicitudes a las redes que las representan están en
   trámite; cuando alguna apruebe, basta con darle su `affiliateBase` a la
   tienda en `data/data.json` — `url_afiliado()` en `scripts/data_io.py` ya
   envuelve el enlace, no hace falta tocar el front.
2. **Más tiendas que se puedan releer solas**: hoy el job nocturno actualiza
   Mercado Libre, las tres VTEX (Elektra, Chedraui, Martí) y el resto por
   `refresh_other_stores.py`. Amazon entra por captura manual con el
   bookmarklet (`scripts/captura_amazon.html`) porque bloquea la lectura
   automática.
3. **Estimación de entrega real**: sustituir `estimateDeliveryDays` (fórmula
   de distancia) por datos de paquetería cuando haya de dónde sacarlos.
4. **Más municipios por estado**: se cubren las 32 entidades, pero 29 con un
   solo punto (su capital). Agregar municipios reales donde haya datos
   logísticos confiables — el modelo de datos ya lo soporta sin tocar código.
5. **Backend opcional**: para cuentas de verdad o alertas de precio por
   correo hace falta servidor; hoy todo eso choca con ser un sitio estático.
