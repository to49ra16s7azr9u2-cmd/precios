// ComparaMX — proxy de Mercado Libre (Cloudflare Worker)
//
// Qué hace: guarda tus credenciales de Mercado Libre (nunca en el frontend
// estático) y expone dos endpoints simples que js/app.js ya sabe consumir:
//
//   GET /item?q=<búsqueda>          -> { price, url, photo, shippingFree, stock }
//   GET /search?q=<búsqueda>&limit  -> { items: [{ id, title, price, url, photo, shippingFree, stock }] }
//
// Requiere 3 secrets (ver README.md de esta carpeta para cómo obtenerlos):
//   ML_CLIENT_ID, ML_CLIENT_SECRET, ML_REFRESH_TOKEN
//
// No probado contra la API real (este entorno no tiene credenciales ni
// acceso de red a Mercado Libre) — está escrito según la documentación
// pública de la API de Mercado Libre (OAuth 2.0 + /sites/MLM/search).
// Verifica las respuestas reales una vez que lo despliegues con tus
// credenciales; el formato exacto de algunos campos (p. ej. shipping)
// puede variar y quizás haya que ajustarlo.

let cachedToken = null; // { access_token, expires_at } en memoria (por invocación del Worker)

async function getAccessToken(env) {
  if (cachedToken && Date.now() < cachedToken.expires_at - 60_000) {
    return cachedToken.access_token;
  }
  const res = await fetch("https://api.mercadolibre.com/oauth/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "refresh_token",
      client_id: env.ML_CLIENT_ID,
      client_secret: env.ML_CLIENT_SECRET,
      refresh_token: env.ML_REFRESH_TOKEN,
    }),
  });
  if (!res.ok) {
    throw new Error(`No se pudo refrescar el token de Mercado Libre (HTTP ${res.status}): ${await res.text()}`);
  }
  const data = await res.json();
  cachedToken = { access_token: data.access_token, expires_at: Date.now() + data.expires_in * 1000 };
  // OJO: Mercado Libre puede devolver un refresh_token NUEVO en cada refresh
  // (rotación). Si guardas el refresh_token como secret fijo, este Worker
  // dejará de funcionar cuando el primero expire/rote. Para producción real,
  // conviene guardar el refresh_token en Workers KV y actualizarlo aquí con
  // `data.refresh_token` en cada llamada. Se deja así (secret fijo) por
  // simplicidad para la primera prueba.
  return cachedToken.access_token;
}

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
  };
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...corsHeaders() },
  });
}

function stockFromQuantity(qty) {
  if (!qty || qty <= 0) return "backorder";
  if (qty <= 3) return "low_stock";
  return "in_stock";
}

async function mlSearch(env, q, limit) {
  const token = await getAccessToken(env);
  const res = await fetch(
    `https://api.mercadolibre.com/sites/MLM/search?q=${encodeURIComponent(q)}&limit=${limit}`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  if (!res.ok) throw new Error(`Mercado Libre search falló (HTTP ${res.status})`);
  return res.json();
}

// Foto del producto tal como la publica Mercado Libre. Se prefiere
// secure_thumbnail (https) porque el sitio se sirve por https y un http://
// quedaría bloqueado como contenido mixto. La miniatura de búsqueda es
// pequeña; se pide una versión mayor cambiando el sufijo -I/-V por -O, que
// es el formato de imagen original de su CDN (si no existe, el navegador se
// queda sin foto y el frontend cae al icono, así que no rompe nada).
function pictureFrom(item) {
  const thumb = item.secure_thumbnail || item.thumbnail;
  if (!thumb) return null;
  return thumb.replace(/-[IVO]\.jpg$/, "-O.jpg");
}

async function handleItem(url, env) {
  const q = url.searchParams.get("q");
  if (!q) return json({ error: "falta ?q=" }, 400);
  const data = await mlSearch(env, q, 1);
  const item = data.results && data.results[0];
  if (!item) return json({ error: "sin resultados" }, 404);
  return json({
    price: item.price,
    url: item.permalink,
    photo: pictureFrom(item),
    shippingFree: !!(item.shipping && item.shipping.free_shipping),
    stock: stockFromQuantity(item.available_quantity),
  });
}

async function handleSearch(url, env) {
  const q = url.searchParams.get("q");
  const limit = url.searchParams.get("limit") || "8";
  if (!q) return json({ items: [] });
  const data = await mlSearch(env, q, limit);
  const items = (data.results || []).map((item) => ({
    id: item.id,
    title: item.title,
    price: item.price,
    url: item.permalink,
    photo: pictureFrom(item),
    shippingFree: !!(item.shipping && item.shipping.free_shipping),
    stock: stockFromQuantity(item.available_quantity),
  }));
  return json({ items });
}

// NOTA: aquí vivía un endpoint /debug que probaba varias rutas de la API y
// devolvía sus respuestas crudas. Se eliminó porque /users/me responde con
// datos personales del titular de la cuenta (nombre, email, CURP) y este
// Worker es una URL pública sin autenticación: cualquiera que la visitara
// los veía. Si hace falta volver a diagnosticar, hazlo con `wrangler tail`
// (los logs van a tu terminal, no a una respuesta pública) y nunca
// devuelvas el cuerpo de /users/me en una respuesta HTTP.
//
// Resultado de ese diagnóstico (2026-08): con credenciales válidas de una
// app no certificada, Mercado Libre bloquea con 403 PolicyAgent
// ("PA_UNAUTHORIZED_RESULT_FROM_POLICIES") TODOS los endpoints de datos de
// producto — /sites/MLM/search, /items/{id}, /sites/MLM/categories,
// búsqueda por categoría y /highlights. Lo único que respondió 200 fue
// /users/me, es decir, los datos de la propia cuenta. No es un problema de
// configuración ni de scopes: es la restricción de acceso al catálogo que
// Mercado Libre aplicó en 2025.
//
// Segunda ronda (también 2026-08), para descartar que el bloqueo fuera por
// el token o por la IP del Worker: se llamaron los mismos endpoints SIN
// cabecera Authorization, con otro User-Agent y contra api.mercadolibre.com.mx.
// Todos 403 igual. Y abriendo
// https://api.mercadolibre.com/sites/MLM/search?q=iphone&limit=1 en un
// navegador doméstico (IP residencial, sin token) la respuesta es el mismo
// 403 "forbidden". O sea: no es el token, no es el scope y no es la IP de
// datacenter — el endpoint de búsqueda está cerrado para todos. Por eso
// LIVE_API_CONFIG.mercadolibre sigue en `enabled: false` en js/app.js.
//
// Si algún día se recupera el acceso (p. ej. tras certificar la app), la
// prueba más corta es pedir /item?q=iphone a este Worker: si devuelve un
// precio en vez de un error 500, volvió a funcionar.

// Tercera ronda: la búsqueda de ítems (/sites/MLM/search) está cerrada, pero
// Mercado Libre tiene otras familias de endpoints que no se habían probado —
// sobre todo el CATÁLOGO (/products/search, /products/{id}), que es
// infraestructura distinta de la búsqueda de publicaciones. Este barrido las
// prueba todas con token, para no ir de a un despliegue por vez.
//
// Igual que /diag: no toca ningún recurso de cuenta, solo catálogo y datos
// de referencia, cuyo cuerpo es público.
//
// Además de la lista fija, acepta ?path=/lo/que/sea para probar un endpoint
// suelto sin volver a desplegar. Ese parámetro está acotado a propósito:
//
//   - solo se arma la URL contra api.mercadolibre.com (nunca un host
//     arbitrario), porque a la petición se le adjunta el access_token y
//     mandarlo a un host de terceros sería filtrarlo;
//   - se rechaza cualquier ruta de /users (incluido /users/me), que es la
//     que devuelve nombre, email y CURP del titular. Ese fue justamente el
//     error del /debug anterior y no se repite.
async function handleProbe(env, reqUrl) {
  let token = null;
  let tokenError = null;
  try {
    token = await getAccessToken(env);
  } catch (err) {
    tokenError = String(err.message || err);
  }

  const custom = reqUrl.searchParams.get("path");
  if (custom) {
    if (!custom.startsWith("/")) return json({ error: "path debe empezar con /" }, 400);
    if (/^\/users(\/|$)/.test(custom)) {
      return json({ error: "ruta bloqueada: /users expone datos personales" }, 403);
    }
    const target = `https://api.mercadolibre.com${custom}`;
    const out = { target };
    for (const mode of ["con_token", "sin_token"]) {
      if (mode === "con_token" && !token) continue;
      const init = mode === "con_token" ? { headers: { Authorization: `Bearer ${token}` } } : {};
      try {
        const res = await fetch(target, init);
        const body = await res.text();
        out[mode] = { status: res.status, body: body.slice(0, 1200) };
      } catch (err) {
        out[mode] = { status: "fetch_error", body: String(err.message || err) };
      }
    }
    return json(out);
  }

  const endpoints = {
    // Catálogo (familia distinta de la búsqueda de publicaciones)
    products_search: "https://api.mercadolibre.com/products/search?site_id=MLM&q=iphone&status=active",
    products_search_cat: "https://api.mercadolibre.com/products/search?site_id=MLM&category_id=MLM1055",
    // Predicción de categoría a partir de un texto
    domain_discovery: "https://api.mercadolibre.com/sites/MLM/domain_discovery/search?q=iphone",
    // Datos de referencia puros (si esto falla, el bloqueo es total)
    currencies: "https://api.mercadolibre.com/currencies",
    sites: "https://api.mercadolibre.com/sites",
    site_mlm: "https://api.mercadolibre.com/sites/MLM",
    category_detail: "https://api.mercadolibre.com/categories/MLM1055",
    listing_types: "https://api.mercadolibre.com/sites/MLM/listing_types",
    // Variantes de búsqueda que no se habían probado
    search_by_category: "https://api.mercadolibre.com/sites/MLM/search?category=MLM1055&limit=1",
    search_by_nickname: "https://api.mercadolibre.com/sites/MLM/search?nickname=TEST&limit=1",
    trends: "https://api.mercadolibre.com/trends/MLM",
  };
  const results = { token_ok: token ? true : tokenError };
  for (const [name, endpoint] of Object.entries(endpoints)) {
    for (const mode of ["con_token", "sin_token"]) {
      if (mode === "con_token" && !token) continue;
      const init = mode === "con_token" ? { headers: { Authorization: `Bearer ${token}` } } : {};
      try {
        const res = await fetch(endpoint, init);
        const body = await res.text();
        results[`${name}__${mode}`] = { status: res.status, body: body.slice(0, 160) };
      } catch (err) {
        results[`${name}__${mode}`] = { status: "fetch_error", body: String(err.message || err) };
      }
    }
  }
  return json(results);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "OPTIONS") return new Response(null, { headers: corsHeaders() });
    try {
      if (url.pathname === "/probe") return await handleProbe(env, url);
      if (url.pathname === "/item") return await handleItem(url, env);
      if (url.pathname === "/search") return await handleSearch(url, env);
      return json({ error: "ruta no encontrada. Usa /item?q=... o /search?q=..." }, 404);
    } catch (err) {
      return json({ error: String(err.message || err) }, 500);
    }
  },
};
