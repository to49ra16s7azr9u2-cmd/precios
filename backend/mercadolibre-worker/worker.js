// ComparaMX — proxy de Mercado Libre (Cloudflare Worker)
//
// Qué hace: guarda tus credenciales de Mercado Libre (nunca en el frontend
// estático) y expone dos endpoints simples que js/app.js ya sabe consumir:
//
//   GET /item?q=<búsqueda>          -> { price, url, photo, shippingFree, ... }
//   GET /search?q=<búsqueda>&limit  -> { items: [{ id, title, price, url, photo, shippingFree }] }
//
// Requiere 3 secrets (ver README.md de esta carpeta para cómo obtenerlos):
//   ML_CLIENT_ID, ML_CLIENT_SECRET, ML_REFRESH_TOKEN
//
// ---------------------------------------------------------------------------
// POR QUÉ USA LA API DE CATÁLOGO Y NO LA BÚSQUEDA DE PUBLICACIONES
//
// La versión anterior pedía /sites/MLM/search, que es lo que documenta casi
// todo el material viejo sobre esta API. Ese endpoint hoy responde 403 a
// todo el mundo: con token, sin token, desde una IP de datacenter y desde
// una IP residencial. Está cerrado, no es un problema de configuración.
//
// Lo que sí funciona es la familia de CATÁLOGO, que es infraestructura
// distinta y sigue abierta para apps con los permisos concedidos:
//
//   /products/search?site_id=MLM&q=…&status=active   -> productos de catálogo
//   /products/{id}/items                             -> TODAS las ofertas de ese producto
//   /products/{id}                                   -> fotos y variantes
//   /highlights/MLM/category/{cat}                   -> más vendidos
//   /categories/{id}                                 -> metadatos de categoría
//
// Para un comparador esto es mejor que la búsqueda vieja: /products/{id}/items
// devuelve varios vendedores del MISMO producto con su precio, su envío y su
// condición, que es exactamente la tabla que arma ComparaMX.
//
// OJO con los permisos: estos endpoints devuelven 403 PolicyAgent si la app
// tiene los "Permisos" del devcenter en "Sin acceso". Hay que concederlos y
// volver a autorizar (el refresh_token viejo conserva los permisos viejos).
// ---------------------------------------------------------------------------

const SITE = "MLM"; // México
const API = "https://api.mercadolibre.com";

let cachedToken = null; // { access_token, expires_at } en memoria (por invocación del Worker)

async function getAccessToken(env) {
  if (cachedToken && Date.now() < cachedToken.expires_at - 60_000) {
    return cachedToken.access_token;
  }
  const res = await fetch(`${API}/oauth/token`, {
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
    throw new Error(`No se pudo refrescar el token de Mercado Libre (HTTP ${res.status})`);
  }
  const data = await res.json();
  cachedToken = { access_token: data.access_token, expires_at: Date.now() + data.expires_in * 1000 };
  // OJO: Mercado Libre puede devolver un refresh_token NUEVO en cada refresh
  // (rotación). Si guardas el refresh_token como secret fijo, este Worker
  // dejará de funcionar cuando el primero rote. Para producción real conviene
  // guardarlo en Workers KV y actualizarlo aquí con `data.refresh_token`.
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

async function mlGet(token, path) {
  const res = await fetch(`${API}${path}`, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) throw new Error(`Mercado Libre ${path} respondió HTTP ${res.status}`);
  return res.json();
}

// La miniatura que publica Mercado Libre termina en -I.jpg (chica). El mismo
// archivo con sufijo -O.jpg es el original, que se ve bien en la ficha. Si esa
// variante no existiera, el navegador se queda sin foto y el frontend cae al
// emoji, así que no rompe nada.
function biggerPicture(url) {
  return url ? url.replace(/-[IVO]\.jpg$/, "-O.jpg") : null;
}

// La foto puede venir en `pictures` (respuesta de /products/search) o en el
// picker de variantes (respuesta de /products/{id}), donde la variante activa
// es la que trae el tag "selected".
function photoFrom(product) {
  const direct = product?.pictures?.[0]?.url || product?.pictures?.[0]?.secure_url;
  if (direct) return biggerPicture(direct);
  for (const picker of product?.pickers || []) {
    for (const variant of picker.products || []) {
      if (variant.thumbnail && (variant.tags || []).includes("selected")) {
        return biggerPicture(variant.thumbnail);
      }
    }
  }
  const anyThumb = product?.pickers?.[0]?.products?.[0]?.thumbnail;
  return anyThumb ? biggerPicture(anyThumb) : null;
}

// Página del producto en el catálogo: es la que muestra a todos los vendedores
// compitiendo por el mismo artículo, así que es el destino correcto para un
// comparador. El campo `permalink` de la API viene vacío en estos productos.
function catalogUrl(productId) {
  return `https://www.mercadolibre.com.mx/p/${productId}`;
}

// De todas las ofertas de un producto de catálogo se queda con la más barata,
// que es la que compite en la tabla de ComparaMX. Devuelve null si el producto
// no tiene ofertas activas (pasa: el catálogo incluye productos descatalogados).
async function cheapestOffer(token, productId) {
  let data;
  try {
    data = await mlGet(token, `/products/${productId}/items?limit=20`);
  } catch {
    return null;
  }
  const offers = (data.results || []).filter((o) => typeof o.price === "number");
  if (offers.length === 0) return null;
  const best = offers.reduce((a, b) => (b.price < a.price ? b : a));
  return {
    price: best.price,
    // `original_price` es el precio tachado. Solo se manda si de verdad es
    // mayor que el vigente; si no, no hay descuento que mostrar.
    priceOriginal: typeof best.original_price === "number" && best.original_price > best.price
      ? best.original_price
      : null,
    currency: best.currency_id || "MXN",
    condition: best.condition || null,
    shippingFree: !!best.shipping?.free_shipping,
    // Mercado Libre solo informa el costo cuando el envío es gratis (0). Si no
    // lo es, no manda monto, así que se deja en null y el frontend muestra "—"
    // en vez de inventar una cifra.
    shippingFee: best.shipping?.free_shipping ? 0 : null,
    sellerCount: data.paging?.total ?? offers.length,
    // Ubicación del vendedor de la oferta ganadora. Sirve para estimar entrega.
    sellerState: best.seller_address?.state?.name || null,
  };
}

async function searchProducts(token, q, limit) {
  const params = new URLSearchParams({
    site_id: SITE,
    q,
    status: "active",
    limit: String(limit),
  });
  const data = await mlGet(token, `/products/search?${params}`);
  return data.results || [];
}

// Categoría que Mercado Libre le asigna al texto buscado. Sirve para separar el
// producto en sí de sus accesorios: "iphone 15" devuelve en el catálogo cables y
// fundas antes que el teléfono, y sin esto la ficha mostraría el precio de una
// funda como si fuera el del celular.
//
// OJO: este endpoint responde 200 SIN cabecera Authorization y 403 CON ella
// (al revés que el resto de la API), así que se llama sin token a propósito.
async function expectedDomain(q) {
  try {
    const res = await fetch(`${API}/sites/${SITE}/domain_discovery/search?q=${encodeURIComponent(q)}&limit=1`);
    if (!res.ok) return null;
    const data = await res.json();
    return data?.[0]?.domain_id || null;
  } catch {
    return null;
  }
}

// Ordena los productos del catálogo poniendo delante los que caen en la
// categoría que se esperaba para la búsqueda. No descarta el resto: si la
// predicción falla, los demás siguen disponibles como respaldo.
function preferDomain(products, domain) {
  if (!domain) return products;
  const match = products.filter((p) => p.domain_id === domain);
  return match.length ? [...match, ...products.filter((p) => p.domain_id !== domain)] : products;
}

// Buena parte del catálogo no tiene ningún vendedor activo — esos productos
// responden 404 "No winners found". Por eso se piden bastantes más candidatos
// de los que hacen falta y se consultan sus ofertas en paralelo, quedándose con
// los primeros que sí tengan. Cada consulta es una subpetición y un Worker
// tiene un tope por invocación, así que el número de candidatos va acotado.
const MAX_CANDIDATES = 24;

async function offersFor(token, products) {
  return Promise.all(
    products.map(async (product) => {
      const offer = await cheapestOffer(token, product.id);
      return offer ? { product, offer } : null;
    })
  );
}

async function handleItem(url, env) {
  const q = url.searchParams.get("q");
  if (!q) return json({ error: "falta ?q=" }, 400);
  const token = await getAccessToken(env);

  const [domain, found] = await Promise.all([expectedDomain(q), searchProducts(token, q, MAX_CANDIDATES)]);
  if (found.length === 0) return json({ error: "sin resultados" }, 404);

  const candidates = preferDomain(found, domain).slice(0, MAX_CANDIDATES);
  const results = await offersFor(token, candidates);
  const hit = results.find(Boolean); // el primero en el orden ya priorizado
  if (!hit) return json({ error: "sin ofertas activas" }, 404);

  let photo = photoFrom(hit.product);
  if (!photo) {
    try {
      photo = photoFrom(await mlGet(token, `/products/${hit.product.id}`));
    } catch {
      photo = null;
    }
  }
  return json({
    id: hit.product.id,
    title: hit.product.name,
    url: catalogUrl(hit.product.id),
    photo,
    ...hit.offer,
  });
}

async function handleSearch(url, env) {
  const q = url.searchParams.get("q");
  if (!q) return json({ items: [] });
  const limit = Math.min(parseInt(url.searchParams.get("limit") || "8", 10) || 8, 12);
  const token = await getAccessToken(env);

  const [domain, found] = await Promise.all([expectedDomain(q), searchProducts(token, q, MAX_CANDIDATES)]);
  const candidates = preferDomain(found, domain).slice(0, MAX_CANDIDATES);
  const results = await offersFor(token, candidates);

  const items = results
    .filter(Boolean)
    .slice(0, limit)
    .map(({ product, offer }) => ({
      id: product.id,
      title: product.name,
      url: catalogUrl(product.id),
      photo: photoFrom(product),
      ...offer,
    }));
  return json({ items });
}


// Sonda de diagnóstico. Acepta ?path=/lo/que/sea para probar un endpoint suelto
// sin volver a desplegar. Va acotada a propósito:
//
//   - la URL se arma siempre contra api.mercadolibre.com (nunca un host
//     arbitrario), porque a la petición se le adjunta el access_token y
//     mandarlo a un tercero sería filtrarlo;
//   - se rechaza cualquier ruta de /users (incluida /users/me), que devuelve
//     nombre, email y CURP del titular. Una versión anterior de este Worker
//     los expuso en una URL pública; por eso el bloqueo es explícito.
async function handleProbe(env, reqUrl) {
  const custom = reqUrl.searchParams.get("path");
  if (!custom) return json({ error: "usa ?path=/algo" }, 400);
  if (!custom.startsWith("/")) return json({ error: "path debe empezar con /" }, 400);
  if (/^\/users(\/|$)/.test(custom)) {
    return json({ error: "ruta bloqueada: /users expone datos personales" }, 403);
  }
  let token = null;
  try {
    token = await getAccessToken(env);
  } catch {
    token = null;
  }
  const target = `${API}${custom}`;
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

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "OPTIONS") return new Response(null, { headers: corsHeaders() });
    try {
      if (url.pathname === "/item") return await handleItem(url, env);
      if (url.pathname === "/search") return await handleSearch(url, env);
      if (url.pathname === "/probe") return await handleProbe(env, url);
      return json({ error: "ruta no encontrada. Usa /item?q=... o /search?q=..." }, 404);
    } catch (err) {
      return json({ error: String(err.message || err) }, 500);
    }
  },
};
