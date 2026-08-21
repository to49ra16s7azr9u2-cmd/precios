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

async function searchProducts(token, q, limit, domain) {
  const params = new URLSearchParams({
    site_id: SITE,
    q,
    status: "active",
    limit: String(limit),
  });
  if (domain) params.set("domain_id", domain);
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

// Busca primero acotado a la categoría que predijo domain_discovery y, si eso
// no da nada (o no hubo predicción), repite sin filtro. El filtro va en la
// consulta y no reordenando lo que vuelve: para "iphone 15" el catálogo
// devuelve tantas fundas y cables que el teléfono no aparece en las primeras
// dos docenas de resultados, así que reordenar no alcanzaba.
async function candidatesFor(token, q, limit) {
  const domain = await expectedDomain(q);
  if (domain) {
    const inDomain = await searchProducts(token, q, limit, domain);
    if (inDomain.length) return inDomain;
  }
  return searchProducts(token, q, limit);
}

// ---------------------------------------------------------------------------
// FILTRO DE COINCIDENCIA
//
// La búsqueda del catálogo devuelve lo que se le parezca, no lo que se pidió.
// Probando con productos reales de ComparaMX salió, por ejemplo:
//
//   "Honor 100 Pro 12GB+256GB"        -> HONOR 400 LITE 256 GB   (otro modelo)
//   "Blackview Oscal Marine 2 4GB"    -> Pantalla LCD para Blackview Shark 8
//   "Xiaomi POCO X8 Pro 12GB+512GB"   -> POCO X8 Pro MAX          (otra variante)
//
// Publicar esos precios sería inventarlos: diría "Blackview Oscal Marine 2:
// $388" cuando esos $388 son un repuesto de pantalla de otro teléfono. Ante la
// duda se prefiere no mostrar nada — el producto se queda con sus precios de
// referencia, que es justo lo que hacía antes de conectar la API.
// ---------------------------------------------------------------------------

// Palabras que delatan un accesorio o un repuesto. Si aparecen en el título
// pero no en lo que se buscó, el resultado no es el producto pedido.
const ACCESSORY_WORDS = [
  "funda", "case", "carcasa", "protector", "mica", "vidrio", "templado",
  "pantalla", "lcd", "display", "cable", "cargador", "adaptador", "bateria",
  "soporte", "cover", "estuche", "correa", "mochila", "maletin", "repuesto",
  "juguete", "para nino", "para nina",
];

// Minúsculas, sin acentos, y separando letra de número ("16GB" -> "16 gb",
// "X8" -> "x 8") para que "512GB" y "512 GB" se comparen igual.
function normalize(s) {
  return String(s || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/(\d)([a-z])/g, "$1 $2")
    .replace(/([a-z])(\d)/g, "$1 $2")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

const tokensOf = (s) => normalize(s).split(" ").filter(Boolean);

// Palabras genéricas que casi todos los títulos traen: no dicen nada sobre si
// el producto es el correcto, así que no cuentan para la cobertura.
const NOISE = new Set(["gb", "ram", "dual", "sim", "celular", "smartphone", "global", "version", "g", "tb", "mah"]);

function hasForeignAccessoryWord(query, title) {
  const q = normalize(query);
  const t = normalize(title);
  return ACCESSORY_WORDS.some((w) => t.includes(normalize(w)) && !q.includes(normalize(w)));
}

// Un resultado se acepta solo si trae TODOS los números del texto buscado (son
// los que distinguen "Honor 100" de "Honor 400", o 256 GB de 512 GB) y además
// la mayoría de sus palabras.
function matchesQuery(query, title) {
  if (hasForeignAccessoryWord(query, title)) return false;
  const qt = tokensOf(query);
  const tt = new Set(tokensOf(title));
  const numbers = qt.filter((t) => /^\d+$/.test(t));
  if (numbers.some((n) => !tt.has(n))) return false;
  const words = [...new Set(qt.filter((t) => !/^\d+$/.test(t) && !NOISE.has(t)))];
  if (words.length === 0) return numbers.length > 0;
  const covered = words.filter((w) => tt.has(w)).length;
  return covered / words.length >= 0.6;
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

  const candidates = await candidatesFor(token, q, MAX_CANDIDATES);
  if (candidates.length === 0) return json({ error: "sin resultados" }, 404);

  const results = await offersFor(token, candidates);
  // Solo sirve un resultado que de verdad sea el producto pedido: dar el precio
  // de un modelo parecido sería presentarlo como si fuera el de este.
  const hit = results.find((r) => r && matchesQuery(q, r.product.name));
  if (!hit) return json({ error: "sin coincidencia confiable" }, 404);

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

  const candidates = await candidatesFor(token, q, MAX_CANDIDATES);
  const results = await offersFor(token, candidates);

  const items = results
    .filter((r) => r && !hasForeignAccessoryWord(q, r.product.name))
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
