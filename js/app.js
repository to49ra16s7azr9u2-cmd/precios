(() => {
  "use strict";

  const PRICE_RANGES = [
    { id: "all", label: "Todos los precios", min: 0, max: Infinity },
    { id: "u5", label: "Menos de $5,000", min: 0, max: 5000 },
    { id: "5to10", label: "$5,000 – $10,000", min: 5000, max: 10000 },
    { id: "10to15", label: "$10,000 – $15,000", min: 10000, max: 15000 },
    { id: "o15", label: "Más de $15,000", min: 15000, max: Infinity },
  ];

  const RATING_FILTERS = [
    { id: "all", label: "Todas", min: 0 },
    { id: "r4", label: "4★ o más", min: 4 },
    { id: "r45", label: "4.5★ o más", min: 4.5 },
  ];

  const STOCK_INFO = {
    in_stock: { text: "En stock", cls: "stock-in", extraDays: 0 },
    low_stock: { text: "Últimas piezas", cls: "stock-low", extraDays: 0 },
    backorder: { text: "Sobre pedido", cls: "stock-back", extraDays: 3 },
  };

  const LS_KEYS = {
    favorites: "comparamx_favorites",
    profile: "comparamx_profile",
    reviews: "comparamx_reviews",
  };

  // ---------- Precios en vivo desde APIs reales (desactivado por defecto) ----------
  // Mercado Libre exige ahora una app registrada + OAuth para leer su API (ya no
  // hay endpoints públicos sin autenticación); y el client_secret no puede vivir
  // en JS de un sitio estático, así que la llamada real debe pasar por un backend
  // propio (ver backend/mercadolibre-worker/). Para activar esto:
  //   1) Sigue backend/mercadolibre-worker/README.md para registrar tu app,
  //      completar el flujo OAuth y desplegar el Worker.
  //   2) Pon las dos URLs del Worker aquí abajo y cambia `enabled` a true.
  // Con eso desactivado (como está por defecto), Mercado Libre simplemente se
  // queda en el grupo "de referencia" como las demás tiendas.
  //
  // Las otras 4 tiendas (amazon_mx, walmart_mx, liverpool, costco_mx) llevan
  // aquí la misma entrada `{ enabled: false, proxyUrl: null }`, aunque hoy
  // ninguna tiene un backend real detrás. No es decoración: fetchLiveOffer()
  // y refreshLiveOffers() ya son genéricos por storeId (no hay nada
  // hardcodeado a Mercado Libre en el camino precio→foto), así que el día
  // que exista un partner API accesible para alguna de ellas, el mismo
  // patrón que usa el Worker de Mercado Libre (backend/mercadolibre-worker/)
  // se replica para esa tienda, se pega su proxyUrl aquí, se pone
  // `enabled: true`, y sus precios y fotos reales aparecen solos —
  // exactamente como pasa hoy con Mercado Libre — sin tocar el resto del
  // código. Mientras siga en `null`/`false`, esa tienda se queda en el
  // grupo "de referencia" con su emoji, igual que ahora.
  //
  // Nota sobre Amazon México (amazon_mx): sí existe una API de productos de
  // Amazon (Product Advertising API, sustituida en 2026 por "Creators API"),
  // y sí cubre el marketplace de México. Pero es exclusiva del programa de
  // afiliados: para obtener acceso hace falta una cuenta de Amazon Associates
  // ya aprobada Y con ventas de afiliado reales (10 ventas calificadas en los
  // últimos 30 días con la Creators API), no solo estar registrado. Es un
  // problema de huevo y gallina para un sitio nuevo sin tráfico: no se puede
  // conseguir acceso a la API sin ventas, y no hay ventas sin el sitio ya
  // funcionando. Por eso amazon_mx se queda igual que las demás: la entrada
  // está lista, pero no hay nada que conectar todavía.
  const LIVE_API_CONFIG = {
    mercadolibre: { enabled: false, proxyUrl: null, searchProxyUrl: null },
    amazon_mx: { enabled: false, proxyUrl: null },
    walmart_mx: { enabled: false, proxyUrl: null },
    liverpool: { enabled: false, proxyUrl: null },
    costco_mx: { enabled: false, proxyUrl: null },
  };

  async function fetchLiveOffer(storeId, product) {
    const cfg = LIVE_API_CONFIG[storeId];
    if (!cfg || !cfg.enabled || !cfg.proxyUrl) return null;
    try {
      const q = encodeURIComponent(product.mlQuery || `${product.brand} ${product.name}`);
      const res = await fetch(`${cfg.proxyUrl}?q=${q}`);
      if (!res.ok) return null;
      const data = await res.json();
      if (!data || !data.price) return null;
      return {
        storeId,
        price: data.price,
        url: data.url || "#",
        // Foto real del producto publicada por la tienda. Solo llega por API;
        // el catálogo local no trae fotos (ver renderProductMedia).
        photo: data.photo || null,
        shippingFee: data.shippingFree ? 0 : data.shippingFee ?? null,
        points: null,
        rating: data.rating ?? null,
        reviewCount: data.reviewCount ?? 0,
        stock: data.stock || "in_stock",
        verified: true,
      };
    } catch {
      return null; // sin conexión, proxy caído, etc.: se ignora y no se muestra nada "en vivo"
    }
  }

  // Intenta reemplazar la oferta de referencia de cada tienda "en vivo" por el
  // resultado real, y vuelve a pintar la tabla si algo cambió. No hace nada
  // mientras LIVE_API_CONFIG esté desactivado.
  async function refreshLiveOffers(product) {
    const storeIds = Object.keys(LIVE_API_CONFIG).filter((id) => LIVE_API_CONFIG[id].enabled);
    if (storeIds.length === 0) return;
    const results = await Promise.all(storeIds.map((id) => fetchLiveOffer(id, product)));
    let changed = false;
    let gotPhoto = false;
    results.forEach((liveOffer) => {
      if (!liveOffer) return;
      const idx = product.offers.findIndex((o) => o.storeId === liveOffer.storeId);
      if (idx >= 0) product.offers[idx] = { ...product.offers[idx], ...liveOffer };
      else product.offers.push(liveOffer);
      // La primera foto real que llegue se adopta como foto del producto. El
      // catálogo local no tiene fotos propias, así que esta es la única vía
      // legítima para mostrar el producto de verdad y no un emoji.
      if (liveOffer.photo && !product.photo) {
        product.photo = liveOffer.photo;
        gotPhoto = true;
      }
      changed = true;
    });
    if (changed && currentProduct() === product) {
      renderOfferTable(product);
      if (gotPhoto) renderProductMedia(el.detailIcon, product, "detail");
    }
  }

  // Búsqueda abierta: le pasa el término tal cual al proxy de Mercado Libre
  // (no busca solo dentro de los 16 productos curados) y espera de vuelta
  // { items: [{ id, title, price, url, shippingFree, stock }] }.
  // Devuelve [] si está desactivado, falla la red, o no hay resultados.
  async function fetchLiveSearchResults(query) {
    const cfg = LIVE_API_CONFIG.mercadolibre;
    if (!cfg.enabled || !cfg.searchProxyUrl || !query) return [];
    try {
      const res = await fetch(`${cfg.searchProxyUrl}?q=${encodeURIComponent(query)}&limit=8`);
      if (!res.ok) return [];
      const data = await res.json();
      return Array.isArray(data.items) ? data.items : [];
    } catch {
      return [];
    }
  }

  const state = {
    data: null,
    selectedMetro: null,
    selectedRegion: null, // null hasta que el usuario elige un municipio en el mapa
    query: "",
    category: null, // filtro activo en la vista de lista
    priceRange: "all",
    brands: new Set(), // marcas seleccionadas; vacío = todas
    minRating: "all",
    sort: "relevance",
    offerSort: "price", // 'price' | 'rating' — orden de la tabla de comparación
    brandCategory: null, // filtro activo en /marcas; null = todas las categorías
  };

  const el = {
    catNav: document.getElementById("catNav"),
    searchInput: document.getElementById("searchInput"),
    searchBtn: document.getElementById("searchBtn"),

    viewHome: document.getElementById("viewHome"),
    homeCategoryGrid: document.getElementById("homeCategoryGrid"),

    viewList: document.getElementById("viewList"),
    listBreadcrumb: document.getElementById("listBreadcrumb"),
    listTitle: document.getElementById("listTitle"),
    filterCategory: document.getElementById("filterCategory"),
    filterPrice: document.getElementById("filterPrice"),
    filterBrand: document.getElementById("filterBrand"),
    filterRating: document.getElementById("filterRating"),
    sortSelect: document.getElementById("sortSelect"),
    productList: document.getElementById("productList"),
    liveSearchSection: document.getElementById("liveSearchSection"),
    liveSearchResults: document.getElementById("liveSearchResults"),

    viewDetail: document.getElementById("viewDetail"),
    detailBreadcrumb: document.getElementById("detailBreadcrumb"),
    detailIcon: document.getElementById("detailIcon"),
    detailBrand: document.getElementById("detailBrand"),
    detailName: document.getElementById("detailName"),
    detailRating: document.getElementById("detailRating"),
    detailFromPrice: document.getElementById("detailFromPrice"),
    detailFavBtn: document.getElementById("detailFavBtn"),
    deliveryBanner: document.getElementById("deliveryBanner"),
    deliveryBannerTitle: document.getElementById("deliveryBannerTitle"),
    deliveryBannerSubtitle: document.getElementById("deliveryBannerSubtitle"),
    locationBtn: document.getElementById("locationBtn"),
    locationBtnLabel: document.getElementById("locationBtnLabel"),
    sortTabs: document.getElementById("sortTabs"),
    offerRowsVerified: document.getElementById("offerRowsVerified"),
    offerRowsReference: document.getElementById("offerRowsReference"),
    verifiedEmptyNote: document.getElementById("verifiedEmptyNote"),
    specTable: document.getElementById("specTable"),
    reviewCount: document.getElementById("reviewCount"),
    reviewList: document.getElementById("reviewList"),
    reviewForm: document.getElementById("reviewForm"),
    reviewAuthor: document.getElementById("reviewAuthor"),
    reviewRating: document.getElementById("reviewRating"),
    reviewComment: document.getElementById("reviewComment"),

    viewBrands: document.getElementById("viewBrands"),
    brandCategoryFilter: document.getElementById("brandCategoryFilter"),
    brandsTitle: document.getElementById("brandsTitle"),
    brandGrid: document.getElementById("brandGrid"),

    viewFavorites: document.getElementById("viewFavorites"),
    favoritesList: document.getElementById("favoritesList"),

    viewAccount: document.getElementById("viewAccount"),
    profileForm: document.getElementById("profileForm"),
    profileName: document.getElementById("profileName"),
    accountSummary: document.getElementById("accountSummary"),

    mapModal: document.getElementById("mapModal"),
    mapModalClose: document.getElementById("mapModalClose"),
    metroTabs: document.getElementById("metroTabs"),
    regionChips: document.getElementById("regionChips"),
  };

  let map = null;
  let regionMarkers = {};

  function money(n) {
    return n.toLocaleString("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 0 });
  }

  function storeById(id) {
    return state.data.stores.find((s) => s.id === id);
  }

  // Logo real de la tienda si hay uno (icons/stores/*.png); si no, cae en
  // las iniciales de siempre sobre el color de marca — nunca deja el badge
  // vacío.
  function storeDotHtml(store) {
    if (store.logoImg) {
      return `<span class="store-dot has-logo"><img src="${store.logoImg}" alt="${store.name}" loading="lazy"></span>`;
    }
    return `<span class="store-dot" style="background:${store.color}">${store.logo}</span>`;
  }

  function categoryById(id) {
    return state.data.categories.find((c) => c.id === id);
  }

  function regionById(id) {
    return state.data.regions.find((r) => r.id === id);
  }

  function metroById(id) {
    return state.data.metros.find((m) => m.id === id);
  }

  function regionsInMetro(metroId) {
    return state.data.regions.filter((r) => r.metro === metroId);
  }

  function minPrice(product) {
    return Math.min(...product.offers.map((o) => o.price));
  }

  // Proxy de "popularidad" para el ranking de cada categoría: suma de
  // reseñas entre todas las tiendas del producto.
  function totalReviews(product) {
    return product.offers.reduce((sum, o) => sum + (o.reviewCount || 0), 0);
  }

  // Descuento de la oferta más barata, si tiene listPrice (precio de lista)
  // más alto que el precio actual. Devuelve el % o null.
  function bestDiscountPct(product) {
    const cheapest = product.offers.reduce((a, b) => (b.price < a.price ? b : a));
    if (!cheapest.listPrice || cheapest.listPrice <= cheapest.price) return null;
    return Math.round((1 - cheapest.price / cheapest.listPrice) * 100);
  }

  // Monto ahorrado (en pesos) de la oferta más barata frente a su listPrice.
  // Se muestra junto al % de descuento: un mismo descuento se "siente" más
  // grande o más chico según se enmarque en % o en dinero real (efecto de
  // encuadre / framing, Tversky & Kahneman), así que mostrar ambos a la vez
  // no deja el tamaño del ahorro a la interpretación de cada quien.
  function bestSavingsAmount(product) {
    const cheapest = product.offers.reduce((a, b) => (b.price < a.price ? b : a));
    if (!cheapest.listPrice || cheapest.listPrice <= cheapest.price) return null;
    return cheapest.listPrice - cheapest.price;
  }

  // Recomendación transparente ("mejor opción"), no solo "más barato": pondera
  // precio (peso 0.4), calificación (0.3) y disponibilidad inmediata (0.3)
  // por oferta. Reduce la sobrecarga de elección (Iyengar & Lepper) dando un
  // default razonable en vez de dejar 4-5 filas sin ningún orden sugerido;
  // se muestra solo cuando difiere de la oferta más barata, para no duplicar
  // la misma fila con dos etiquetas redundantes. El precio sigue pesando más
  // que cualquier otro factor individual, así que solo gana una oferta algo
  // más cara cuando la diferencia es real (p. ej. la más barata está sobre
  // pedido y otra, casi al mismo precio, tiene entrega inmediata) — no basta
  // con tener mejor calificación para justificar pagar más.
  function bestValueOffer(product) {
    const prices = product.offers.map((o) => o.price);
    const minP = Math.min(...prices);
    const maxP = Math.max(...prices);
    const priceRange = maxP - minP || 1;
    let best = null;
    let bestScore = -Infinity;
    product.offers.forEach((o) => {
      const priceScore = 1 - (o.price - minP) / priceRange; // 1 = más barato
      const ratingScore = (o.rating || 0) / 5;
      const stockScore = o.stock === "in_stock" ? 1 : o.stock === "low_stock" ? 0.5 : 0;
      const score = priceScore * 0.4 + ratingScore * 0.3 + stockScore * 0.3;
      if (score > bestScore) { bestScore = score; best = o; }
    });
    const cheapest = product.offers.reduce((a, b) => (b.price < a.price ? b : a));
    return best && best.storeId !== cheapest.storeId ? best : null;
  }

  function aggregateRating(product) {
    const totalReviews = product.offers.reduce((sum, o) => sum + o.reviewCount, 0);
    if (totalReviews === 0) return { avg: 0, count: 0 };
    const weighted = product.offers.reduce((sum, o) => sum + o.rating * o.reviewCount, 0);
    return { avg: weighted / totalReviews, count: totalReviews };
  }

  function starsHtml(avg) {
    const filled = Math.round(avg);
    return "★".repeat(filled) + "☆".repeat(5 - filled);
  }

  // Pinta la imagen de un producto dentro de `container`.
  //
  // El catálogo local NO trae fotos: no hay una fuente propia con derechos
  // para las fotos de producto, así que por defecto se ve un emoji. Cuando
  // hay una API conectada (hoy solo Mercado Libre), la foto real llega en la
  // respuesta y se guarda en product.photo; entonces se muestra esa.
  //
  // Si la URL falla (enlace roto, caída del CDN, bloqueo de hotlinking), el
  // onerror vuelve al emoji en vez de dejar el icono de imagen rota.
  function renderProductMedia(container, product, variant) {
    if (!container) return;
    const emoji = product.image || "📦";
    if (!product.photo) {
      container.textContent = emoji;
      container.classList.remove("has-photo");
      return;
    }
    container.classList.add("has-photo");
    container.textContent = "";
    const img = document.createElement("img");
    img.className = variant === "detail" ? "product-photo product-photo-detail" : "product-photo";
    img.src = product.photo;
    img.alt = product.name || "";
    img.loading = "lazy";
    img.onerror = () => {
      container.classList.remove("has-photo");
      container.textContent = emoji;
    };
    container.appendChild(img);
  }

  // Distancia aproximada entre dos puntos (km), fórmula de Haversine
  function distanceKm(a, b) {
    const R = 6371;
    const toRad = (d) => (d * Math.PI) / 180;
    const dLat = toRad(b.lat - a.lat);
    const dLng = toRad(b.lng - a.lng);
    const s =
      Math.sin(dLat / 2) ** 2 +
      Math.cos(toRad(a.lat)) * Math.cos(toRad(b.lat)) * Math.sin(dLng / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(s));
  }

  // Estima días de entrega según distancia tienda->municipio y confiabilidad
  // logística local (infraDays), más un margen si el producto está sobre
  // pedido. No usa datos reales de paquetería.
  function estimateDeliveryDays(hubRegionId, targetRegionId, stock) {
    const hub = regionById(hubRegionId);
    const target = regionById(targetRegionId);
    const base = hub.id === target.id ? 1 : (() => {
      const dist = distanceKm(hub, target);
      const sameMetro = hub.metro === target.metro;
      if (sameMetro) return dist < 15 ? 1 : dist < 40 ? 2 : 3;
      return 3 + Math.round(dist / 500);
    })();
    const stockExtra = (STOCK_INFO[stock] || STOCK_INFO.in_stock).extraDays;
    return Math.min(base + target.infraDays + stockExtra, 10);
  }

  // Ajusta el costo de envío según qué tan lejos está el municipio elegido
  // del centro de distribución de la tienda: más distancia y zonas con
  // infraestructura más difícil cuestan un poco más. Si el envío base ya es
  // gratis, se mantiene gratis (una promoción de "envío gratis" normalmente
  // aplica a todo el país). baseFee puede ser null (dato en vivo sin costo
  // de envío conocido): en ese caso no se ajusta, se deja tal cual.
  function estimateShippingFee(baseFee, hubRegionId, targetRegionId) {
    if (baseFee == null || baseFee === 0) return baseFee;
    const hub = regionById(hubRegionId);
    const target = regionById(targetRegionId);
    if (hub.id === target.id) return baseFee;
    const sameMetro = hub.metro === target.metro;
    let extra = target.infraDays * 20; // zona con logística menos confiable
    if (!sameMetro) {
      const dist = distanceKm(hub, target);
      extra += Math.round(dist / 200) * 15; // ~$15 extra cada ~200 km fuera de la zona
    }
    return baseFee + extra;
  }

  // ---------- Almacenamiento local (favoritos, perfil, reseñas propias) ----------
  // Todo esto vive solo en localStorage: no hay servidor ni cuentas reales.

  function readLS(key, fallback) {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch {
      return fallback;
    }
  }
  function writeLS(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      /* almacenamiento no disponible (modo privado, etc.): se ignora */
    }
  }

  function getFavorites() {
    return readLS(LS_KEYS.favorites, []);
  }
  function isFavorite(productId) {
    return getFavorites().includes(productId);
  }
  function toggleFavorite(productId) {
    const favs = getFavorites();
    const idx = favs.indexOf(productId);
    if (idx === -1) favs.push(productId);
    else favs.splice(idx, 1);
    writeLS(LS_KEYS.favorites, favs);
    return idx === -1;
  }

  function getProfile() {
    return readLS(LS_KEYS.profile, { name: "" });
  }
  function setProfileName(name) {
    writeLS(LS_KEYS.profile, { name });
  }

  function getAllUserReviews() {
    return readLS(LS_KEYS.reviews, {});
  }
  function getUserReviews(productId) {
    return getAllUserReviews()[productId] || [];
  }
  function addUserReview(productId, review) {
    const all = getAllUserReviews();
    all[productId] = all[productId] || [];
    all[productId].unshift(review);
    writeLS(LS_KEYS.reviews, all);
  }

  function favIconHtml(productId) {
    return isFavorite(productId) ? "❤" : "🤍";
  }

  // Botón de favorito reutilizable: alterna el estado y vuelve a pintar la
  // vista actual para que el ícono quede sincronizado en todos lados.
  function bindFavToggle(btnEl, productId, onToggle) {
    btnEl.classList.toggle("is-fav", isFavorite(productId));
    btnEl.onclick = (e) => {
      e.stopPropagation();
      e.preventDefault();
      toggleFavorite(productId);
      onToggle();
    };
  }

  async function loadData() {
    const res = await fetch("data/data.json");
    state.data = await res.json();
    // Catálogo de marcas/afiliados (Admitad): independiente del comparador de
    // electrónica, así que un fallo aquí no debe tumbar el resto del sitio.
    try {
      const res2 = await fetch("data/brands.json");
      state.brandsData = await res2.json();
    } catch {
      state.brandsData = { brands: [] };
    }
  }

  // ---------- Navegación entre vistas ----------

  function setActiveView(name) {
    el.viewHome.classList.toggle("hidden", name !== "home");
    el.viewList.classList.toggle("hidden", name !== "list");
    el.viewDetail.classList.toggle("hidden", name !== "detail");
    el.viewBrands.classList.toggle("hidden", name !== "brands");
    el.viewFavorites.classList.toggle("hidden", name !== "favorites");
    el.viewAccount.classList.toggle("hidden", name !== "account");
    if (name !== "detail") closeMapModal();
  }

  // Navega al hash indicado; si ya estamos en ese hash, "hashchange" no se
  // dispara solo, así que forzamos el render para reflejar el nuevo estado
  // (p. ej. cambiar de categoría o buscar estando ya en la vista de lista).
  function navigateTo(hash, renderFn) {
    if (location.hash === hash) renderFn();
    else location.hash = hash;
  }

  function goHome() {
    navigateTo("#/", renderHome);
  }

  function goList(opts) {
    if (opts && opts.category !== undefined) state.category = opts.category;
    if (opts && opts.query !== undefined) state.query = opts.query;
    navigateTo("#/list", renderList);
  }

  // Entrar a una categoría (desde Inicio, la barra de categorías o el
  // filtro) siempre parte del ranking de popularidad, como en Kakaku.com:
  // ahí es donde vive el paso 2 del recorrido (categoría → ranking → precio).
  function goCategoryRanking(categoryId) {
    state.sort = "popularity";
    goList({ category: categoryId, query: "" });
  }

  function goDetail(productId) {
    navigateTo(`#/p/${productId}`, () => renderDetail(productId));
  }

  function onHashChange() {
    if (!state.data) return;
    const hash = location.hash;
    const detailMatch = hash.match(/#\/p\/(.+)/);
    if (detailMatch) {
      renderDetail(detailMatch[1]);
    } else if (hash === "#/list" || hash.startsWith("#/list?")) {
      // Permite enlazar directo a una categoría filtrada (p. ej. desde las
      // páginas estáticas de SEO: #/list?cat=Celulares), sin lo cual esos
      // enlaces caían al inicio en vez de abrir el listado ya filtrado.
      const qs = hash.includes("?") ? new URLSearchParams(hash.split("?")[1]) : null;
      const cat = qs && qs.get("cat");
      if (cat) state.category = cat;
      renderList();
    } else if (hash === "#/favorites") {
      renderFavorites();
    } else if (hash === "#/account") {
      renderAccount();
    } else if (hash === "#/marcas" || hash.startsWith("#/marcas?")) {
      const qs = hash.includes("?") ? new URLSearchParams(hash.split("?")[1]) : null;
      const cat = qs && qs.get("cat");
      if (cat) state.brandCategory = cat;
      renderBrands();
    } else {
      renderHome();
    }
    window.scrollTo(0, 0);
  }

  // ---------- Header: navegación de categorías ----------

  function renderCatNav() {
    el.catNav.innerHTML = "";
    state.data.categories.forEach((c) => {
      const span = document.createElement("span");
      span.textContent = `${c.icon} ${c.name}`;
      const isActive = location.hash === "#/list" && state.category === c.id;
      span.className = isActive ? "active" : "";
      span.onclick = () => goCategoryRanking(c.id);
      el.catNav.appendChild(span);
    });
  }

  // ---------- Vista: Inicio (solo selección de categoría) ----------

  // Inicio ahora es puramente el primer paso del recorrido estilo
  // Kakaku.com: categoría → ranking de productos populares → comparación de
  // precios. Los rankings en sí viven en la vista de categoría (renderList).
  function renderHome() {
    setActiveView("home");
    renderCatNav();
    el.homeCategoryGrid.innerHTML = "";

    const allCard = document.createElement("button");
    allCard.type = "button";
    allCard.className = "category-card";
    allCard.innerHTML = `
      <span class="category-card-icon">🗂️</span>
      <span class="category-card-name">Todas</span>
      <span class="category-card-count">${state.data.products.length} productos</span>
    `;
    allCard.onclick = () => { state.sort = "relevance"; goList({ category: null, query: "" }); };
    el.homeCategoryGrid.appendChild(allCard);

    state.data.categories.forEach((cat) => {
      const count = state.data.products.filter((p) => p.category === cat.id).length;
      const card = document.createElement("button");
      card.type = "button";
      card.className = "category-card";
      card.innerHTML = `
        <span class="category-card-icon">${cat.icon}</span>
        <span class="category-card-name">${cat.name}</span>
        <span class="category-card-count">${count} productos</span>
      `;
      card.onclick = () => goCategoryRanking(cat.id);
      el.homeCategoryGrid.appendChild(card);
    });
  }

  // ---------- Vista: Lista (búsqueda / categoría) ----------

  function brandsInScope() {
    const scoped = state.category
      ? state.data.products.filter((p) => p.category === state.category)
      : state.data.products;
    return [...new Set(scoped.map((p) => p.brand))].sort();
  }

  function filteredProducts() {
    const range = PRICE_RANGES.find((r) => r.id === state.priceRange) || PRICE_RANGES[0];
    const ratingMin = (RATING_FILTERS.find((r) => r.id === state.minRating) || RATING_FILTERS[0]).min;
    return state.data.products.filter((p) => {
      const q = state.query.toLowerCase();
      const matchesQuery =
        !q ||
        p.name.toLowerCase().includes(q) ||
        p.brand.toLowerCase().includes(q) ||
        p.category.toLowerCase().includes(q);
      const matchesCat = !state.category || p.category === state.category;
      const price = minPrice(p);
      const matchesPrice = price >= range.min && price < range.max;
      const matchesBrand = state.brands.size === 0 || state.brands.has(p.brand);
      // Redondeado a 1 decimal para que coincida con el valor mostrado en pantalla.
      const matchesRating = Math.round(aggregateRating(p).avg * 10) / 10 >= ratingMin;
      return matchesQuery && matchesCat && matchesPrice && matchesBrand && matchesRating;
    });
  }

  function sortedProducts(products) {
    const list = products.slice();
    if (state.sort === "popularity") list.sort((a, b) => totalReviews(b) - totalReviews(a));
    else if (state.sort === "price_asc") list.sort((a, b) => minPrice(a) - minPrice(b));
    else if (state.sort === "price_desc") list.sort((a, b) => minPrice(b) - minPrice(a));
    else if (state.sort === "rating_desc") list.sort((a, b) => aggregateRating(b).avg - aggregateRating(a).avg);
    return list;
  }

  function renderList() {
    setActiveView("list");
    renderCatNav();

    el.listBreadcrumb.innerHTML = `<a href="#/">Inicio</a>`;
    if (state.category) {
      el.listBreadcrumb.innerHTML += ` &gt; ${categoryById(state.category).name}`;
    } else if (state.query) {
      el.listBreadcrumb.innerHTML += ` &gt; Resultados de búsqueda`;
    } else {
      el.listBreadcrumb.innerHTML += ` &gt; Todos los productos`;
    }

    el.sortSelect.value = state.sort;

    renderFilterCategory();
    renderFilterPrice();
    renderFilterBrand();
    renderFilterRating();

    // Paso 2 del recorrido estilo Kakaku.com (categoría → ranking de
    // populares → precio): al entrar por una categoría, sin búsqueda de
    // texto, la lista se muestra como ranking numerado en vez de lista plana.
    const isCategoryRanking = !!state.category && !state.query;

    renderProductListInto(el.productList, sortedProducts(filteredProducts()), {
      emptyText: "No se encontraron productos con estos filtros.",
      onFavToggle: renderList,
      withRank: isCategoryRanking,
    });

    const products = filteredProducts();
    el.listTitle.textContent = state.query
      ? `Resultados para "${state.query}" (${products.length})`
      : state.category
      ? `🏆 ${categoryById(state.category).name} — más populares (${products.length})`
      : `Todos los productos (${products.length})`;

    renderLiveSearchSection();
  }

  // Busca en vivo en Mercado Libre (si está activado) para complementar el
  // catálogo local. Se queda oculta y no hace ninguna llamada mientras
  // LIVE_API_CONFIG.mercadolibre esté desactivado.
  async function renderLiveSearchSection() {
    const query = state.query;
    if (!query || !LIVE_API_CONFIG.mercadolibre.enabled) {
      el.liveSearchSection.classList.add("hidden");
      el.liveSearchResults.innerHTML = "";
      return;
    }
    const items = await fetchLiveSearchResults(query);
    if (state.query !== query || location.hash !== "#/list") return; // el usuario ya cambió de búsqueda/vista

    el.liveSearchSection.classList.toggle("hidden", items.length === 0);
    el.liveSearchResults.innerHTML = "";
    items.forEach((item) => {
      const row = document.createElement("div");
      row.className = "product-row is-external";
      const shippingText = item.shippingFree ? "Envío gratis" : "";
      row.innerHTML = `
        <span class="row-icon">🔎</span>
        <div class="row-info">
          <div class="row-brand">Mercado Libre</div>
          <div class="row-name">${item.title}</div>
          <div class="row-stars muted">${shippingText}</div>
        </div>
        <div class="row-priceblock">
          <div class="row-price">${money(item.price)}</div>
          <div class="row-external-badge">Ver en Mercado Libre ↗</div>
        </div>
      `;
      // Los resultados en vivo sí traen foto real de la tienda; si no viene,
      // se queda la lupa como marcador.
      renderProductMedia(row.querySelector(".row-icon"), { photo: item.photo, image: "🔎", name: item.title });
      row.onclick = () => window.open(item.url, "_blank");
      el.liveSearchResults.appendChild(row);
    });
  }

  // Renderiza una lista de filas de producto (usada en /list y /favorites)
  function renderProductListInto(container, products, opts) {
    container.innerHTML = "";
    if (products.length === 0) {
      container.innerHTML = `<p class="empty-state">${opts.emptyText}</p>`;
      return;
    }
    products.forEach((p, i) => {
      const { avg, count } = aggregateRating(p);
      const rank = i + 1;
      const row = document.createElement("div");
      row.className = "product-row" + (opts.withRank ? " has-rank" : "");
      row.innerHTML = `
        ${opts.withRank ? `<span class="rank-badge">${rank === 1 ? "👑" : rank}</span>` : ""}
        <span class="row-icon">${p.image}</span>
        <div class="row-info">
          <div class="row-brand">${p.brand}</div>
          <div class="row-name">${p.name}</div>
          <div class="row-stars">${starsHtml(avg)} <span class="muted">${avg.toFixed(1)} (${count})</span></div>
        </div>
        <div class="row-priceblock">
          <div class="row-from">Desde</div>
          <div class="row-price">${money(minPrice(p))}${bestDiscountPct(p) ? `<span class="discount-badge">-${bestDiscountPct(p)}%</span>` : ""}</div>
          <div class="row-stores">${p.offers.length} tiendas</div>
        </div>
        <button class="row-fav-btn" aria-label="Favorito"></button>
      `;
      renderProductMedia(row.querySelector(".row-icon"), p);
      row.onclick = () => goDetail(p.id);
      bindFavToggle(row.querySelector(".row-fav-btn"), p.id, opts.onFavToggle);
      row.querySelector(".row-fav-btn").textContent = favIconHtml(p.id);
      container.appendChild(row);
    });
  }

  function renderFilterCategory() {
    el.filterCategory.innerHTML = "";
    const allOpt = document.createElement("label");
    allOpt.className = "filter-option" + (!state.category ? " active" : "");
    allOpt.innerHTML = `<input type="radio" name="fcat" ${!state.category ? "checked" : ""}> Todas`;
    allOpt.onclick = () => { state.category = null; state.brands.clear(); state.sort = "relevance"; renderList(); };
    el.filterCategory.appendChild(allOpt);

    state.data.categories.forEach((c) => {
      const opt = document.createElement("label");
      const isActive = state.category === c.id;
      opt.className = "filter-option" + (isActive ? " active" : "");
      opt.innerHTML = `<input type="radio" name="fcat" ${isActive ? "checked" : ""}> ${c.icon} ${c.name}`;
      opt.onclick = () => { state.category = c.id; state.brands.clear(); state.sort = "popularity"; renderList(); };
      el.filterCategory.appendChild(opt);
    });
  }

  function renderFilterPrice() {
    el.filterPrice.innerHTML = "";
    PRICE_RANGES.forEach((r) => {
      const opt = document.createElement("label");
      const isActive = state.priceRange === r.id;
      opt.className = "filter-option" + (isActive ? " active" : "");
      opt.innerHTML = `<input type="radio" name="fprice" ${isActive ? "checked" : ""}> ${r.label}`;
      opt.onclick = () => { state.priceRange = r.id; renderList(); };
      el.filterPrice.appendChild(opt);
    });
  }

  function renderFilterBrand() {
    el.filterBrand.innerHTML = "";
    const brands = brandsInScope();
    // Si una marca seleccionada ya no aplica en el alcance actual, se descarta.
    [...state.brands].forEach((b) => { if (!brands.includes(b)) state.brands.delete(b); });

    brands.forEach((b) => {
      const opt = document.createElement("label");
      const isActive = state.brands.has(b);
      opt.className = "filter-option" + (isActive ? " active" : "");
      opt.innerHTML = `<input type="checkbox" ${isActive ? "checked" : ""}> ${b}`;
      opt.onclick = (e) => {
        e.preventDefault();
        if (state.brands.has(b)) state.brands.delete(b);
        else state.brands.add(b);
        renderList();
      };
      el.filterBrand.appendChild(opt);
    });
  }

  function renderFilterRating() {
    el.filterRating.innerHTML = "";
    RATING_FILTERS.forEach((r) => {
      const opt = document.createElement("label");
      const isActive = state.minRating === r.id;
      opt.className = "filter-option" + (isActive ? " active" : "");
      opt.innerHTML = `<input type="radio" name="frating" ${isActive ? "checked" : ""}> ${r.label}`;
      opt.onclick = () => { state.minRating = r.id; renderList(); };
      el.filterRating.appendChild(opt);
    });
  }

  // ---------- Vista: Favoritos ----------

  function renderFavorites() {
    setActiveView("favorites");
    renderCatNav();
    const favIds = getFavorites();
    const products = state.data.products.filter((p) => favIds.includes(p.id));
    renderProductListInto(el.favoritesList, products, {
      emptyText: "Aún no tienes favoritos. Toca el corazón 🤍 en cualquier producto para guardarlo aquí.",
      onFavToggle: renderFavorites,
    });
  }

  // ---------- Vista: Marcas y ofertas (catálogo de afiliados, Admitad) ----------

  // Iconos ilustrados (subidos por el usuario) para las categorías que tienen
  // uno; el resto usa un emoji plano como respaldo, mismo criterio visual
  // que el resto del sitio (ver cat.icon en renderCatNav).
  const CATEGORY_ICONS = {
    "Electrónica y gaming": "icons/categories/electronica-gaming.png",
    "VPN y seguridad": "icons/categories/vpn-seguridad.png",
    "Moda y accesorios": "icons/categories/moda-accesorios.png",
    "Electrodomésticos y hogar": "icons/categories/electrodomesticos-hogar.png",
    "Joyería y relojes": "icons/categories/joyeria-relojes.png",
    "Finanzas": "icons/categories/finanzas.png",
  };
  const CATEGORY_EMOJI_FALLBACK = {
    "Compras generales": "🛍️",
    "Belleza": "💄",
    "Viajes": "✈️",
    "Educación": "🎓",
    "Software e IA": "🤖",
    "Hosting y dominios": "🌐",
    "Otros": "📦",
    "Salud y bienestar": "🌿",
  };

  function brandCategories() {
    const list = state.brandsData.brands.map((b) => b.category);
    return [...new Set(list)].sort();
  }

  function categoryCardIconHtml(cat) {
    const photo = CATEGORY_ICONS[cat];
    if (photo) return `<img src="${photo}" alt="" loading="lazy">`;
    return CATEGORY_EMOJI_FALLBACK[cat] || "🏷️";
  }

  function renderBrandCategoryFilter() {
    el.brandCategoryFilter.innerHTML = "";
    const all = state.brandsData.brands;

    const allCard = document.createElement("button");
    allCard.type = "button";
    allCard.className = "category-card" + (!state.brandCategory ? " active" : "");
    allCard.innerHTML = `
      <span class="category-card-icon">🛍️</span>
      <span class="category-card-name">Todas</span>
      <span class="category-card-count">${all.length}</span>
    `;
    allCard.onclick = () => { state.brandCategory = null; renderBrands(); };
    el.brandCategoryFilter.appendChild(allCard);

    brandCategories().forEach((cat) => {
      const count = all.filter((b) => b.category === cat).length;
      const isActive = state.brandCategory === cat;
      const card = document.createElement("button");
      card.type = "button";
      card.className = "category-card" + (isActive ? " active" : "");
      card.innerHTML = `
        <span class="category-card-icon">${categoryCardIconHtml(cat)}</span>
        <span class="category-card-name">${cat}</span>
        <span class="category-card-count">${count}</span>
      `;
      card.onclick = () => { state.brandCategory = cat; renderBrands(); };
      el.brandCategoryFilter.appendChild(card);
    });
  }

  function renderBrands() {
    setActiveView("brands");
    renderCatNav();
    renderBrandCategoryFilter();

    const all = state.brandsData.brands;
    const shown = state.brandCategory ? all.filter((b) => b.category === state.brandCategory) : all;
    el.brandsTitle.textContent = state.brandCategory ? `${state.brandCategory} (${shown.length})` : `Todas las marcas (${shown.length})`;

    el.brandGrid.innerHTML = "";
    if (shown.length === 0) {
      el.brandGrid.innerHTML = `<p class="empty-state">No hay marcas en esta categoría todavía.</p>`;
      return;
    }
    shown.forEach((b) => {
      const card = document.createElement("a");
      card.className = "brand-card";
      card.href = b.url;
      card.target = "_blank";
      card.rel = "noopener sponsored";
      card.innerHTML = `
        <div class="brand-card-logo"><img src="${b.logo}" alt="${b.name}" loading="lazy"></div>
        <div class="brand-card-body">
          <div class="brand-card-cat">${b.category}</div>
          <div class="brand-card-name">${b.name}</div>
          <p class="brand-card-desc">${b.description}</p>
        </div>
      `;
      el.brandGrid.appendChild(card);
    });
  }

  // ---------- Vista: Mi cuenta ----------

  function renderAccount() {
    setActiveView("account");
    renderCatNav();
    el.profileName.value = getProfile().name || "";
    const favCount = getFavorites().length;
    const reviewCount = Object.values(getAllUserReviews()).reduce((sum, arr) => sum + arr.length, 0);
    el.accountSummary.textContent = `${favCount} favorito(s) guardado(s) · ${reviewCount} reseña(s) escritas en este navegador.`;
  }

  // ---------- Vista: Ficha de producto ----------

  function currentProduct() {
    const match = location.hash.match(/#\/p\/(.+)/);
    if (!match || !state.data) return null;
    return state.data.products.find((p) => p.id === match[1]) || null;
  }

  function renderDetail(productId) {
    const product = state.data.products.find((p) => p.id === productId);
    if (!product) { goHome(); return; }

    setActiveView("detail");
    renderCatNav();

    const cat = categoryById(product.category);
    el.detailBreadcrumb.innerHTML =
      `<a href="#/">Inicio</a> &gt; <a href="#/list" id="breadcrumbCat">${cat.name}</a> &gt; ${product.name}`;
    document.getElementById("breadcrumbCat").onclick = (e) => {
      e.preventDefault();
      goList({ category: product.category, query: "" });
    };

    renderProductMedia(el.detailIcon, product, "detail");
    el.detailBrand.textContent = product.brand;
    el.detailName.textContent = product.name;
    el.detailFavBtn.textContent = favIconHtml(product.id);
    bindFavToggle(el.detailFavBtn, product.id, () => renderDetail(product.id));

    const { avg, count } = aggregateRating(product);
    el.detailRating.innerHTML = `${starsHtml(avg)} ${avg.toFixed(1)} <span class="rc">(${count} calificaciones)</span>`;
    const discountPct = bestDiscountPct(product);
    const savings = bestSavingsAmount(product);
    el.detailFromPrice.innerHTML = `
      Desde <strong>${money(minPrice(product))}</strong>${discountPct ? `<span class="discount-badge">-${discountPct}%</span>` : ""} en ${product.offers.length} tiendas
      ${savings ? `<span class="save-amount">Ahorras ${money(savings)}</span>` : ""}
    `;

    el.specTable.innerHTML = product.specs
      .map((s) => `<tr><th>${s.label}</th><td>${s.value}</td></tr>`)
      .join("");

    renderReviews(product);

    updateLocationBtn();
    renderSortTabs();
    renderOfferTable(product);
    refreshLiveOffers(product);
  }

  function renderReviews(product) {
    el.reviewAuthor.value = getProfile().name || "";
    const userReviews = getUserReviews(product.id);
    const allReviews = [...userReviews, ...product.reviews];
    el.reviewCount.textContent = `(${allReviews.length})`;
    el.reviewList.innerHTML = allReviews
      .map(
        (r) => `
        <div class="review-item">
          <div class="review-stars">${starsHtml(r.rating)}</div>
          <div class="review-meta">${r.author}${r.isLocal ? " · tú" : ""} · ${r.date}</div>
          <p class="review-comment">${r.comment}</p>
        </div>`
      )
      .join("");
  }

  function renderSortTabs() {
    const tabs = [
      { id: "price", label: "Precio más bajo" },
      { id: "rating", label: "Mejor calificado" },
    ];
    el.sortTabs.innerHTML = "";
    tabs.forEach((t) => {
      const btn = document.createElement("button");
      btn.className = "sort-tab" + (state.offerSort === t.id ? " active" : "");
      btn.textContent = t.label;
      btn.onclick = () => {
        state.offerSort = t.id;
        renderSortTabs();
        const product = currentProduct();
        if (product) renderOfferTable(product);
      };
      el.sortTabs.appendChild(btn);
    });
  }

  function updateLocationBtn() {
    if (state.selectedRegion) {
      const region = regionById(state.selectedRegion);
      el.locationBtnLabel.textContent = "Cambiar ubicación";
      el.locationBtn.classList.add("is-set");
      el.deliveryBanner.classList.add("is-set");
      el.deliveryBannerTitle.textContent = `✓ Mostrando entrega a ${region.name}`;
      el.deliveryBannerSubtitle.textContent = "¿Otro municipio? Puedes cambiarlo cuando quieras.";
    } else {
      el.locationBtnLabel.textContent = "Elegir mi ubicación";
      el.locationBtn.classList.remove("is-set");
      el.deliveryBanner.classList.remove("is-set");
      el.deliveryBannerTitle.textContent = "¿Cuándo llega a tu casa?";
      el.deliveryBannerSubtitle.textContent = "Elige tu municipio y compara el tiempo de entrega de cada tienda.";
    }
  }

  function deliveryLabel(days) {
    if (days <= 1) return { text: "Entrega mañana", cls: "delivery-fast" };
    return { text: `Entrega en ${days} días`, cls: "" };
  }

  // Pinta un grupo de filas (verificado o de referencia) en su <tbody>.
  // bestPrice/fastestDays se calculan sobre TODAS las ofertas (ambos grupos),
  // para que "MÁS BARATO"/"MÁS RÁPIDO" reflejen la comparación completa aunque
  // se muestren en tablas separadas.
  function renderOfferRows(tbody, rows, bestPrice, fastestDays, recommendedStoreId) {
    tbody.innerHTML = "";
    rows.forEach((r) => {
      const tr = document.createElement("tr");
      // r puede venir de una API en vivo (fetchLiveOffer) donde shippingFee,
      // points y rating pueden faltar (null/undefined): nunca deben tronar el
      // render, solo mostrarse como "—" cuando no hay dato.
      const shippingHtml =
        r.shippingFee === 0 ? '<span class="ship-badge">Envío gratis</span>'
        : r.shippingFee == null ? "—"
        : money(r.shippingFee);
      // Texto corto de envío para mostrar junto a la entrega, en el momento
      // en que el usuario elige su municipio en el mapa (no solo en la
      // columna aparte). El costo ya viene ajustado por distancia/zona
      // (ver estimateShippingFee) cuando hay una región seleccionada.
      const shippingShort = r.shippingFee === 0 ? "envío gratis" : r.shippingFee == null ? null : `envío ${money(r.shippingFee)}`;
      let deliveryHtml = "";
      if (r.days !== null) {
        const d = deliveryLabel(r.days);
        // La entrega y el envío por municipio son siempre nuestra propia
        // estimación por distancia (no hay ninguna fuente en vivo conectada
        // todavía, a diferencia del precio) — se marca igual que los
        // precios "de referencia", para no dar a entender que es un dato
        // confirmado con la tienda.
        deliveryHtml = `<div class="delivery-sub ${d.cls}">${d.text}${r.days === fastestDays ? '<span class="best-tag">MÁS RÁPIDO</span>' : ""}${shippingShort ? ` · ${shippingShort}` : ""}<span class="est-badge" title="Estimado por distancia, no confirmado con la tienda">🔶 estimado</span></div>`;
      } else if (state.selectedRegion && !r.store.hubRegion) {
        // Tiendas que envían directo desde el extranjero (sin centro de
        // distribución mexicano): no hay con qué estimar días por
        // municipio, así que se avisa en vez de dejar la celda en blanco.
        deliveryHtml = `<div class="delivery-sub">Envío internacional${shippingShort ? ` · ${shippingShort}` : ""}</div>`;
      }
      const stockInfo = STOCK_INFO[r.stock] || STOCK_INFO.in_stock;
      let discountHtml = "";
      if (r.listPrice && r.listPrice > r.price) {
        const pct = Math.round((1 - r.price / r.listPrice) * 100);
        // Se muestra el % junto con el monto ahorrado en pesos: el mismo
        // descuento "se siente" distinto según se enmarque en porcentaje o
        // en dinero real (efecto de encuadre), así que se dan los dos.
        discountHtml = `<span class="list-price">${money(r.listPrice)}</span><span class="discount-badge">-${pct}%</span><span class="save-amount">Ahorras ${money(r.listPrice - r.price)}</span>`;
      }
      const pointsHtml = r.points == null ? "—" : `${r.points}%`;
      const ratingHtml = r.rating == null ? "—" : `${starsHtml(r.rating)} <span class="rc">${r.rating.toFixed(1)}</span>`;
      // "Recomendado" es una etiqueta aparte de "MÁS BARATO": no repite la
      // misma fila (renderOfferTable ya evita eso), y su criterio se explica
      // en el tooltip para que se lea como una sugerencia transparente y no
      // como un sello arbitrario.
      const isRecommended = r.storeId === recommendedStoreId;
      tr.innerHTML = `
        <td>
          <span class="store-badge">
            ${storeDotHtml(r.store)}
            ${r.store.name}
          </span>
        </td>
        <td class="price-cell">
          <div>${discountHtml}</div>
          <div class="price-line">
            ${money(r.price)}${r.price === bestPrice ? '<span class="best-tag">MÁS BARATO</span>' : ""}${isRecommended ? '<span class="best-tag recommended-tag" title="Mejor combinación de precio, calificación y disponibilidad">🏆 RECOMENDADO</span>' : ""}
          </div>
          ${deliveryHtml}
        </td>
        <td>${shippingHtml}</td>
        <td><span class="stock-badge ${stockInfo.cls}">${stockInfo.text}</span></td>
        <td>${pointsHtml}</td>
        <td class="stars-cell">${ratingHtml}</td>
        <td>
          <button class="buy-btn">Ver oferta</button>
          <div class="buy-trust">🔒 Compra en el sitio real de la tienda</div>
        </td>
      `;
      tr.querySelector(".buy-btn").onclick = () => window.open(r.url, "_blank");
      tbody.appendChild(tr);
    });
  }

  function renderOfferTable(product) {
    let rows = product.offers.map((o) => {
      const store = storeById(o.storeId);
      // Tiendas sin hubRegion (envío internacional directo, p. ej. SUNSKY o
      // Geekbuying) no tienen un centro de distribución mexicano desde el
      // cual estimar distancia/días por municipio: se deja sin estimar en
      // vez de tronar contra una región inexistente.
      const days = state.selectedRegion && store.hubRegion
        ? estimateDeliveryDays(store.hubRegion, state.selectedRegion, o.stock)
        : null;
      const shippingFee = state.selectedRegion && store.hubRegion
        ? estimateShippingFee(o.shippingFee, store.hubRegion, state.selectedRegion)
        : o.shippingFee;
      return { ...o, store, days, shippingFee };
    });

    if (state.offerSort === "rating") rows.sort((a, b) => b.rating - a.rating);
    else rows.sort((a, b) => a.price - b.price);

    const bestPrice = Math.min(...rows.map((r) => r.price));
    const knownDays = rows.map((r) => r.days).filter((d) => d !== null);
    const fastestDays = state.selectedRegion && knownDays.length ? Math.min(...knownDays) : null;
    const recommended = bestValueOffer(product);
    const recommendedStoreId = recommended ? recommended.storeId : null;

    const verifiedRows = rows.filter((r) => r.verified);
    const referenceRows = rows.filter((r) => !r.verified);

    renderOfferRows(el.offerRowsVerified, verifiedRows, bestPrice, fastestDays, recommendedStoreId);
    renderOfferRows(el.offerRowsReference, referenceRows, bestPrice, fastestDays, recommendedStoreId);
    el.verifiedEmptyNote.classList.toggle("hidden", verifiedRows.length > 0);
  }

  // ---------- Mapa de entrega (modal) ----------

  function openMapModal() {
    if (!state.selectedMetro) {
      state.selectedMetro = state.data.metros[0].id;
    }
    renderMetroTabs();
    renderRegionChips();
    el.mapModal.classList.remove("hidden");
    initOrUpdateMap();
  }

  function closeMapModal() {
    el.mapModal.classList.add("hidden");
  }

  function renderMetroTabs() {
    el.metroTabs.innerHTML = "";
    state.data.metros.forEach((m) => {
      const tab = document.createElement("button");
      tab.className = "metro-tab" + (m.id === state.selectedMetro ? " active" : "");
      tab.textContent = m.name;
      tab.onclick = () => {
        state.selectedMetro = m.id;
        renderMetroTabs();
        renderRegionChips();
        panToMetro(m);
        renderMarkersForMetro();
      };
      el.metroTabs.appendChild(tab);
    });
  }

  function renderRegionChips() {
    el.regionChips.innerHTML = "";
    regionsInMetro(state.selectedMetro).forEach((r) => {
      const chip = document.createElement("button");
      chip.className = "region-chip" + (r.id === state.selectedRegion ? " active" : "");
      chip.textContent = r.name;
      chip.onclick = () => selectRegion(r.id);
      el.regionChips.appendChild(chip);
    });
  }

  function selectRegion(regionId) {
    state.selectedRegion = regionId;
    renderRegionChips();
    highlightMarker();
    updateLocationBtn();
    const product = currentProduct();
    if (product) renderOfferTable(product);
    closeMapModal();
  }

  function panToMetro(metro) {
    if (!map) return;
    map.setView([metro.center.lat, metro.center.lng], metro.zoom);
  }

  function initOrUpdateMap() {
    if (!map) {
      const metro = metroById(state.selectedMetro);
      map = L.map("map", { zoomControl: true, scrollWheelZoom: false }).setView(
        [metro.center.lat, metro.center.lng],
        metro.zoom
      );
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap",
        maxZoom: 15,
      }).addTo(map);
    }
    renderMarkersForMetro();
    setTimeout(() => map.invalidateSize(), 50);
  }

  function renderMarkersForMetro() {
    Object.values(regionMarkers).forEach((m) => map.removeLayer(m));
    regionMarkers = {};

    regionsInMetro(state.selectedMetro).forEach((r) => {
      const marker = L.circleMarker([r.lat, r.lng], {
        radius: 10,
        color: "#FF0211",
        weight: 2,
        fillColor: "#ffb3b3",
        fillOpacity: 0.9,
      }).addTo(map);
      marker.bindTooltip(r.name, { permanent: false });
      marker.on("click", () => selectRegion(r.id));
      regionMarkers[r.id] = marker;
    });
    highlightMarker();
  }

  function highlightMarker() {
    Object.entries(regionMarkers).forEach(([id, marker]) => {
      const isActive = id === state.selectedRegion;
      marker.setStyle({
        radius: isActive ? 14 : 10,
        fillColor: isActive ? "#FF0211" : "#ffb3b3",
        color: isActive ? "#8c0007" : "#FF0211",
      });
    });
  }

  // ---------- Eventos globales ----------

  function bindEvents() {
    el.searchInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") goList({ query: el.searchInput.value.trim(), category: null });
    });
    el.searchBtn.addEventListener("click", () => goList({ query: el.searchInput.value.trim(), category: null }));

    el.sortSelect.addEventListener("change", (e) => {
      state.sort = e.target.value;
      renderList();
    });

    el.locationBtn.addEventListener("click", openMapModal);
    el.mapModalClose.addEventListener("click", closeMapModal);
    el.mapModal.addEventListener("click", (e) => {
      if (e.target === el.mapModal) closeMapModal();
    });

    el.reviewForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const product = currentProduct();
      if (!product) return;
      const author = el.reviewAuthor.value.trim() || "Anónimo";
      const rating = Number(el.reviewRating.value);
      const comment = el.reviewComment.value.trim();
      if (!comment) return;
      addUserReview(product.id, {
        author,
        rating,
        comment,
        date: new Date().toISOString().slice(0, 10),
        isLocal: true,
      });
      setProfileName(author);
      el.reviewComment.value = "";
      renderReviews(product);
    });

    el.profileForm.addEventListener("submit", (e) => {
      e.preventDefault();
      setProfileName(el.profileName.value.trim());
      renderAccount();
    });

    window.addEventListener("hashchange", onHashChange);
  }

  async function main() {
    await loadData();
    bindEvents();
    onHashChange();

    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("sw.js").catch(() => {});
    }
  }

  main();
})();
