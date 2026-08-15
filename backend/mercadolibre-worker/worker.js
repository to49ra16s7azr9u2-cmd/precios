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

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "OPTIONS") return new Response(null, { headers: corsHeaders() });
    try {
      if (url.pathname === "/item") return await handleItem(url, env);
      if (url.pathname === "/search") return await handleSearch(url, env);
      return json({ error: "ruta no encontrada. Usa /item?q=... o /search?q=..." }, 404);
    } catch (err) {
      return json({ error: String(err.message || err) }, 500);
    }
  },
};
