# Backend de Mercado Libre para ComparaMX

Este es el backend mínimo que hace falta para conectar Mercado Libre de verdad
(ver `js/app.js` → `LIVE_API_CONFIG`). Es un [Cloudflare Worker](https://workers.cloudflare.com/)
(capa gratuita) que guarda tus credenciales y hace de intermediario entre
ComparaMX (sitio estático) y la API de Mercado Libre.

> ⚠️ **Seguridad**: en ningún paso de esta guía debes compartir tu
> `client_secret`, `refresh_token` ni `access_token` conmigo, en el chat, en
> un commit, ni en ningún lugar público. Todo eso vive únicamente en tu
> cuenta de Cloudflare (como "secret" del Worker) o en tu propia terminal
> mientras haces el intercambio inicial. Lo único que necesitas devolverme
> (o poner tú mismo en `js/app.js`) es la **URL del Worker ya desplegado**
> (algo como `https://comparamx-mercadolibre-proxy.tuusuario.workers.dev`).

## 1. Registra tu aplicación en Mercado Libre

1. Entra a https://developers.mercadolibre.com.mx/ con tu cuenta de Mercado
   Libre (o crea una si no tienes).
2. Ve a **"Mis aplicaciones"** → **"Crear nueva aplicación"**.
3. Completa el formulario:
   - **Nombre**: lo que quieras, p. ej. "ComparaMX".
   - **Unidad de negocio**: elige **Mercado Libre** (no Global Selling, ni
     Mercado Envíos, ni Mercado Pago — esas son para otra cosa, ver la
     explicación que te di antes).
   - **Redirect URI / URI de retorno**: por ahora pon
     `https://example.com/callback` (solo la usarás una vez, a mano, en el
     paso 3 — no hace falta que sea un servidor real).
4. Al crear la app te van a mostrar **App ID (Client ID)** y **Client
   Secret**. Guárdalos en un lugar seguro (gestor de contraseñas), no en
   texto plano en el repositorio.

## 2. Autoriza la app (una sola vez, manualmente)

Abre esta URL en tu navegador, reemplazando `APP_ID` y la redirect URI por
las tuyas exactas (deben coincidir con lo que registraste):

```
https://auth.mercadolibre.com.mx/authorization?response_type=code&client_id=APP_ID&redirect_uri=https://example.com/callback
```

Inicia sesión con tu cuenta de Mercado Libre y autoriza la app. El navegador
te va a redirigir a algo como:

```
https://example.com/callback?code=TG-XXXXXXXXXXXXXXXX-XXXXXXXX
```

Esa página dará error (no existe un servidor real ahí) — **eso es normal**,
lo único que necesitas es copiar el valor de `code` de la URL antes de que
expire (dura pocos minutos, así que sigue rápido al paso 3).

## 3. Cambia el `code` por un `refresh_token` (una sola vez)

Desde tu propia terminal (no la comparto conmigo), ejecuta:

```bash
curl -X POST https://api.mercadolibre.com/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "client_id=APP_ID" \
  -d "client_secret=TU_CLIENT_SECRET" \
  -d "code=EL_CODE_DEL_PASO_2" \
  -d "redirect_uri=https://example.com/callback"
```

La respuesta trae `access_token` y `refresh_token`. El que te importa
guardar es el **`refresh_token`** — el Worker lo va a usar para pedir
`access_token` nuevos automáticamente (los `access_token` expiran a las
pocas horas; el `refresh_token` es el que necesitas conservar).

## 4. Despliega el Worker

Necesitas Node.js y una cuenta gratuita de Cloudflare.

```bash
cd backend/mercadolibre-worker
npm install -g wrangler   # si no lo tienes
wrangler login             # abre el navegador para autenticarte con Cloudflare

wrangler secret put ML_CLIENT_ID
wrangler secret put ML_CLIENT_SECRET
wrangler secret put ML_REFRESH_TOKEN

wrangler deploy
```

Al terminar, `wrangler deploy` imprime la URL pública del Worker, algo como:

```
https://comparamx-mercadolibre-proxy.TUUSUARIO.workers.dev
```

## 5. Conéctalo al frontend

En `js/app.js`, busca `LIVE_API_CONFIG` (cerca del principio del archivo) y
cámbialo por:

```js
const LIVE_API_CONFIG = {
  mercadolibre: {
    enabled: true,
    proxyUrl: "https://comparamx-mercadolibre-proxy.TUUSUARIO.workers.dev/item",
    searchProxyUrl: "https://comparamx-mercadolibre-proxy.TUUSUARIO.workers.dev/search",
  },
};
```

Con eso:

- En la ficha de cada uno de los 16 productos del catálogo, Mercado Libre
  pasará automáticamente al bloque **"✅ Precios verificados en tiempo
  real"** (arriba, destacado) en vez de "de referencia".
- En la página de listado, buscar cualquier término mostrará también una
  sección **"🌐 Más resultados en vivo de Mercado Libre"** para productos
  que no están en el catálogo curado.

## Notas honestas sobre este Worker

- **No lo pude probar en vivo**: este entorno no tiene tus credenciales ni
  acceso de red a Mercado Libre (su API bloquea las peticiones desde este
  sandbox con 403, tanto autenticadas como no). Está escrito según la
  documentación pública de OAuth 2.0 de Mercado Libre, pero **verifica tú
  las respuestas reales** una vez desplegado — es posible que algún nombre
  de campo (p. ej. `shipping.free_shipping`) necesite un ajuste menor.
- **Rotación de `refresh_token`**: Mercado Libre puede devolver un
  `refresh_token` nuevo cada vez que se usa uno. Este Worker guarda el
  `refresh_token` como secret fijo por simplicidad; si después de un tiempo
  deja de funcionar, probablemente sea por esto — la solución es guardar el
  `refresh_token` en [Workers KV](https://developers.cloudflare.com/kv/) y
  actualizarlo en cada refresh en vez de usar un secret fijo.
- **Límites de la API**: Mercado Libre aplica límites de tasa (rate limits)
  no completamente documentados públicamente; si ComparaMX recibe tráfico
  real, puede hacer falta cachear resultados (p. ej. con Workers KV o Cache
  API) para no excederlos.
- **Campos que este Worker no rellena**: `rating` y `points` (puntos de
  recompensa) no vienen del endpoint de búsqueda de Mercado Libre, y
  `shippingFee` exacto solo se sabe si el envío es gratis (`free_shipping`);
  si no lo es, no se manda un monto. El frontend (`js/app.js`) ya está
  preparado para esto: muestra "—" en esas columnas en vez de fallar. Esto
  se verificó simulando el Worker con un servidor de prueba local — no es
  solo una suposición.
