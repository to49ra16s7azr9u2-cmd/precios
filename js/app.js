(() => {
  "use strict";

  // Cuántos productos se dibujan a la vez en una lista/ranking. Sin esto,
  // una categoría grande (o "Todos los productos") crea miles de filas de
  // DOM de una sola vez -- con el catálogo ya en ~15,000 productos, la
  // categoría más grande tardaba varios segundos en pintarse y "Todos"
  // llegaba a 200,000 nodos de DOM. Con paginación cada vista solo dibuja
  // PAGE_SIZE filas sin importar cuánto crezca el catálogo.
  const PAGE_SIZE = 60;

  const RATING_FILTERS = [
    { id: "all", label: "Todas", min: 0 },
    { id: "r4", label: "4★ o más", min: 4 },
    { id: "r45", label: "4.5★ o más", min: 4.5 },
  ];

  // Filtro de tamaño físico (distinto de la capacidad, que ya se navega
  // como subcategoría): solo se usa en Baterías portátiles, vía la
  // especificación "Tamaño" que agrega add_powerbanks.py.
  const SIZE_FILTERS = [
    { id: "all", label: "Todos los tamaños" },
    { id: "Pequeño", label: "Pequeño" },
    { id: "Mediano", label: "Mediano" },
    { id: "Grande", label: "Grande" },
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
    includeShipping: "comparamx_include_shipping",
    categoryClicks: "comparamx_category_clicks",
    productViews: "comparamx_product_views",
    storeClicks: "comparamx_store_clicks",
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
    mercadolibre: {
      enabled: true,
      proxyUrl: "https://comparamx-mercadolibre-proxy.comparamx.workers.dev/item",
      searchProxyUrl: "https://comparamx-mercadolibre-proxy.comparamx.workers.dev/search",
    },
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
        // La API de catálogo de Mercado Libre no informa la cantidad
        // disponible, así que el stock queda desconocido. Se deja en null
        // a propósito: mostrar "En stock" por defecto sería inventarlo.
        stock: data.stock ?? null,
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
    icons: null, // set de ilustraciones SVG (data/icons.json) que reemplaza a los emoji en todo el sitio
    selectedMetro: null,
    selectedRegion: null, // null hasta que el usuario elige un municipio en el mapa
    query: "",
    category: null, // filtro activo en la vista de lista
    subcategory: null, // sub-nivel dentro de la categoría (si tiene)
    priceMin: null, // null = sin tope inferior
    priceMax: null, // null = sin tope superior
    includeShipping: readLS(LS_KEYS.includeShipping, false), // suma envío conocido al precio mostrado en todo el sitio
    brands: new Set(), // marcas seleccionadas; vacío = todas
    minRating: "all",
    excludeUsed: false, // filtro "Excluir usados"
    magsafeOnly: false, // filtro "Solo compatibles con MagSafe" (Baterías portátiles)
    sizeFilter: "all", // filtro "Tamaño" (Baterías portátiles)
    page: 1, // página actual de la lista/ranking (ver PAGE_SIZE)
    sort: "relevance",
    offerSort: "price", // 'price' | 'rating' — orden de la tabla de comparación
    brandCategory: null, // filtro activo en /marcas; null = todas las categorías
  };

  const el = {
    catNav: document.getElementById("catNav"),
    catNavToggle: document.getElementById("catNavToggle"),
    catNavToggleLabel: document.getElementById("catNavToggleLabel"),
    searchInput: document.getElementById("searchInput"),
    searchBtn: document.getElementById("searchBtn"),
    searchSuggestions: document.getElementById("searchSuggestions"),
    shipToggle: document.getElementById("shipToggle"),
    shipToggleLabel: document.getElementById("shipToggleLabel"),

    viewHome: document.getElementById("viewHome"),
    homeCategoryGrid: document.getElementById("homeCategoryGrid"),
    homeTopCategoriesList: document.getElementById("homeTopCategoriesList"),
    homeRankings: document.getElementById("homeRankings"),
    homeMostViewed: document.getElementById("homeMostViewed"),

    viewList: document.getElementById("viewList"),
    listBreadcrumb: document.getElementById("listBreadcrumb"),
    listTitle: document.getElementById("listTitle"),
    filterCategory: document.getElementById("filterCategory"),
    priceRangeMin: document.getElementById("priceRangeMin"),
    priceRangeMax: document.getElementById("priceRangeMax"),
    priceRangeFill: document.getElementById("priceRangeFill"),
    priceNumMin: document.getElementById("priceNumMin"),
    priceNumMax: document.getElementById("priceNumMax"),
    filterBrand: document.getElementById("filterBrand"),
    filterBrandSearch: document.getElementById("filterBrandSearch"),
    filterRating: document.getElementById("filterRating"),
    filterCondition: document.getElementById("filterCondition"),
    filterMagsafeGroup: document.getElementById("filterMagsafeGroup"),
    filterMagsafe: document.getElementById("filterMagsafe"),
    filterSizeGroup: document.getElementById("filterSizeGroup"),
    filterSize: document.getElementById("filterSize"),
    sortSelect: document.getElementById("sortSelect"),
    productList: document.getElementById("productList"),
    pagination: document.getElementById("pagination"),
    liveSearchSection: document.getElementById("liveSearchSection"),
    liveSearchResults: document.getElementById("liveSearchResults"),

    viewDetail: document.getElementById("viewDetail"),
    detailBreadcrumb: document.getElementById("detailBreadcrumb"),
    detailIcon: document.getElementById("detailIcon"),
    detailBrand: document.getElementById("detailBrand"),
    detailName: document.getElementById("detailName"),
    detailRating: document.getElementById("detailRating"),
    detailColors: document.getElementById("detailColors"),
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
    offerGroupVerified: document.getElementById("offerGroupVerified"),
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

    backToTopBtn: document.getElementById("backToTopBtn"),
  };

  let map = null;
  let regionMarkers = {};

  function money(n) {
    return n.toLocaleString("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 0 });
  }

  // "1 tiendas"/"0 calificaciones" salían en cada fila del catálogo y en
  // cada ficha: con casi todos los productos en una sola tienda, el plural
  // mal puesto era lo primero que se veía al entrar.
  function plural(n, singular, pluralForm) {
    return `${n} ${n === 1 ? singular : pluralForm}`;
  }

  // Los textos de variante (color/talla) y sus URLs vienen tal cual del feed
  // de la tienda, no de un input del usuario, pero igual pueden traer
  // comillas o símbolos raros — se escapan antes de meterlos en un atributo
  // HTML para no depender de que el feed nunca traiga algo inesperado.
  function htmlEscapeAttr(s) {
    return String(s).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
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

  function subcategoryById(categoryId, subId) {
    if (!subId) return null;
    const cat = categoryById(categoryId);
    if (!cat || !cat.subcategories) return null;
    return cat.subcategories.find((s) => s.id === subId) || null;
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

  // Envío ESTIMADO (MXN) para cuando una tienda no expone costo real ni un
  // umbral de envío gratis verificable (ver shippingFeeInfo). Son valores
  // de referencia aproximados -- NO cotizaciones reales de paquetería --
  // calculados a partir de lo que ya se sabe de cada tienda (tipo de
  // catálogo, días típicos de entrega ya investigados en typicalShippingDays,
  // y si es nacional o envío internacional directo). Se muestran siempre
  // marcados como "🔶 estimado" (mismo badge que ya usan los días de
  // entrega estimados), nunca mezclados con un monto confirmado por la API
  // o por un umbral de envío gratis real.
  //   - mercadolibre: envío nacional pagado sin monto expuesto por la API;
  //     tarifa de paquetería nacional básica de referencia.
  //   - sunsky / geekbuying / molnija / glasseslit: electrónica/accesorios
  //     ligeros, envío internacional directo.
  //   - woodestic: juegos de mesa de madera, más voluminosos/pesados que el
  //     resto del catálogo internacional.
  //   - aliexpress: catálogo general, su propia nota de envío dice que el
  //     estándar suele ser gratis o barato en artículos <2kg.
  //   - alibaba: plataforma mayorista, envíos de mayor volumen/peso.
  //   - theluxurycloset: bolsos/joyería de lujo, paquetería asegurada.
  const SHIPPING_ESTIMATE_MXN = {
    mercadolibre: 99,
    sunsky: 150,
    geekbuying: 180,
    molnija: 200,
    glasseslit: 100,
    woodestic: 280,
    aliexpress: 130,
    alibaba: 350,
    theluxurycloset: 500,
  };

  // Costo de envío de una oferta: { fee, estimated }. fee nunca es null
  // (siempre hay un número que sumar), pero estimated:true marca que ese
  // número es una referencia aproximada y no un dato confirmado, para que
  // la UI lo distinga de un monto real.
  //   1) offer.shippingFee ya es un dato conocido (0 = gratis confirmado
  //      por la API de origen, o un monto real si algún día la API lo
  //      expone) -> estimated: false.
  //   2) Si no, el umbral de envío gratis en USD que la propia tienda
  //      publica (freeShippingThresholdUSD), comparado contra el precio
  //      real en USD de esa oferta (priceOriginal) -- si lo alcanza, es
  //      honesto afirmar "$0 de envío" con la misma base que ya se usa
  //      para el badge "Envío gratis" -> estimated: false.
  //   3) Si ninguno de los dos aplica, se usa SHIPPING_ESTIMATE_MXN de la
  //      tienda -> estimated: true. Si la tienda ni siquiera está en esa
  //      tabla, $0 sin marcar (no debería pasar con el catálogo actual).
  function shippingFeeInfo(offer) {
    if (offer.shippingFee != null) return { fee: offer.shippingFee, estimated: false };
    const store = storeById(offer.storeId);
    const threshold = store && store.freeShippingThresholdUSD;
    const priceUSD = offer.priceOriginal && offer.priceOriginal.currency === "USD" ? offer.priceOriginal.amount : null;
    if (threshold != null && priceUSD != null && priceUSD >= threshold) return { fee: 0, estimated: false };
    const estimate = SHIPPING_ESTIMATE_MXN[offer.storeId];
    return estimate != null ? { fee: estimate, estimated: true } : { fee: 0, estimated: false };
  }

  // true cuando, con el toggle "Incluir envío" activo, el precio mostrado
  // de esta oferta incluye un envío ESTIMADO (no confirmado) -- para
  // marcarlo aparte y que no se lea como si ya fuera el costo real final.
  function shippingIsEstimated(offer) {
    return state.includeShipping && shippingFeeInfo(offer).estimated;
  }

  // Precio a mostrar/ordenar/filtrar en toda la app, según el toggle
  // global "Incluir envío" (state.includeShipping). Con el toggle apagado
  // se comporta exactamente como antes (solo el precio del artículo).
  function displayPrice(offer) {
    if (!state.includeShipping) return offer.price;
    return offer.price + shippingFeeInfo(offer).fee;
  }

  // Mismo ajuste que displayPrice(), pero para listPrice (precio de lista
  // antes del descuento) -- así el % y el monto ahorrado calculados sobre
  // "precio con envío" siguen siendo correctos (el envío es el mismo en
  // ambos lados de la resta, así que el ahorro en pesos no cambia, pero el
  // % sí depende de sumarlo a los dos).
  function displayListPrice(offer) {
    if (offer.listPrice == null) return null;
    if (!state.includeShipping) return offer.listPrice;
    return offer.listPrice + shippingFeeInfo(offer).fee;
  }

  function minPrice(product) {
    return Math.min(...product.offers.map((o) => displayPrice(o)));
  }

  // true cuando, con "Incluir envío" activo, el precio "Desde" mostrado en
  // una fila de lista incluye un envío ESTIMADO (no confirmado) -- para
  // avisar ahí mismo, sin tener que entrar a la ficha para enterarse.
  function cheapestOfferShippingEstimated(product) {
    if (!state.includeShipping) return false;
    const cheapest = product.offers.reduce((a, b) => (displayPrice(b) < displayPrice(a) ? b : a));
    return shippingIsEstimated(cheapest);
  }

  // Cantidad de opciones de compra a mostrar junto al precio ("N tiendas").
  // Para un producto fusionado por color (colorVariants, ver
  // merge_color_variants.py) todas las variantes son del mismo vendedor
  // (Mercado Libre), pero cada una es un anuncio propio con su propio
  // precio -- se cuentan igual que tiendas distintas para que el usuario
  // vea de un vistazo cuántas opciones hay, no solo cuántos vendedores.
  function offerCount(product) {
    return Math.max(product.offers.length, (product.colorVariants || []).length);
  }

  // Compatibilidad con MagSafe (especificación "MagSafe: Sí" que agrega
  // scripts/add_powerbanks.py cuando el título de Mercado Libre lo dice
  // explícitamente) -- usado por el filtro de Baterías portátiles.
  function isMagSafe(product) {
    return (product.specs || []).some((s) => s.label === "MagSafe" && /s[ií]/i.test(s.value));
  }

  // Tamaño físico (especificación "Tamaño" que agrega add_powerbanks.py),
  // eje aparte de la capacidad (que ya se navega como subcategoría).
  function productSize(product) {
    const s = (product.specs || []).find((s) => s.label === "Tamaño");
    return s ? s.value : null;
  }

  // Detecta productos usados/preowned (p.ej. The Luxury Closet, donde nuevo
  // y preowned del mismo modelo se agrupan como un solo producto) para
  // poder mostrarlo de un vistazo y ofrecer un filtro "Excluir usados".
  function isUsed(product) {
    return (product.specs || []).some(
      (s) => s.label === "Condición" && /preowned|usado|reacondicionad/i.test(s.value)
    );
  }

  // Reacondicionado (certificado, con garantía del vendedor) no es lo mismo
  // que usado/preowned (venta entre particulares): se distingue para no
  // llamarlo "Usado" a secas, que sería impreciso. isUsed() sigue tratando
  // ambos como "no nuevo" a efectos del filtro "Excluir usados".
  function conditionBadge(product) {
    const c = (product.specs || []).find((s) => s.label === "Condición");
    if (!c) return "";
    if (/reacondicionad/i.test(c.value)) {
      return `<span class="used-badge" title="Reacondicionado por Mercado Libre, con garantía del vendedor">${icon("recycle")} Reacondicionado</span>`;
    }
    if (/preowned|usado/i.test(c.value)) {
      return `<span class="used-badge" title="Producto usado/preowned">${icon("rotate")} Usado</span>`;
    }
    return "";
  }

  // Equipo de uso comercial/industrial (p.ej. refrigeradores de
  // restaurante, aspiradoras industriales): se incluye en el catálogo,
  // pero se marca claramente para no confundirlo con la versión doméstica
  // del mismo tipo de producto.
  function usageBadge(product) {
    const u = (product.specs || []).find((s) => s.label === "Uso");
    if (!u || !/comercial|industrial/i.test(u.value)) return "";
    return `<span class="commercial-badge" title="Equipo de uso comercial/industrial, no doméstico">${icon("factory")} Uso comercial</span>`;
  }

  // Puntaje de "popularidad" para el ranking de cada categoría, sumando
  // señales reales (nunca inventadas):
  //   - 3 puntos por cada clic real hacia la tienda en ESTE navegador
  //     (trackStoreClick, botón "Ver oferta"/variantes de color)
  //   - 1 punto por cada visita real a la ficha del producto en ESTE
  //     navegador (trackProductView)
  //   - 10/8/6 puntos por cada reseña real de 5/4/3 estrellas que tiene el
  //     producto (reseñas propias del catálogo + las que este usuario
  //     agregó localmente), 0 para 1-2 estrellas
  // Clics y visitas son "lo que tú más visitaste" (un sitio estático sin
  // backend no puede medir eso agregado de todos los visitantes, ver
  // trackCategoryClick), pero las reseñas sí son un dato compartido real.
  function reviewStarPoints(product) {
    const STAR_POINTS = { 5: 10, 4: 8, 3: 6 };
    const all = [...getUserReviews(product.id), ...(product.reviews || [])];
    return all.reduce((sum, r) => sum + (STAR_POINTS[r.rating] || 0), 0);
  }
  function popularityScore(product) {
    const clicks = readLS(LS_KEYS.storeClicks, {})[product.id] || 0;
    const views = readLS(LS_KEYS.productViews, {})[product.id] || 0;
    return clicks * 3 + views * 1 + reviewStarPoints(product);
  }

  // Descuento de la oferta más barata, si tiene listPrice (precio de lista)
  // más alto que el precio actual. Devuelve el % o null.
  function bestDiscountPct(product) {
    const cheapest = product.offers.reduce((a, b) => (displayPrice(b) < displayPrice(a) ? b : a));
    const price = displayPrice(cheapest);
    const listPrice = displayListPrice(cheapest);
    if (!listPrice || listPrice <= price) return null;
    return Math.round((1 - price / listPrice) * 100);
  }

  // Monto ahorrado (en pesos) de la oferta más barata frente a su listPrice.
  // Se muestra junto al % de descuento: un mismo descuento se "siente" más
  // grande o más chico según se enmarque en % o en dinero real (efecto de
  // encuadre / framing, Tversky & Kahneman), así que mostrar ambos a la vez
  // no deja el tamaño del ahorro a la interpretación de cada quien.
  function bestSavingsAmount(product) {
    const cheapest = product.offers.reduce((a, b) => (displayPrice(b) < displayPrice(a) ? b : a));
    const price = displayPrice(cheapest);
    const listPrice = displayListPrice(cheapest);
    if (!listPrice || listPrice <= price) return null;
    return listPrice - price;
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
    const prices = product.offers.map((o) => displayPrice(o));
    const minP = Math.min(...prices);
    const maxP = Math.max(...prices);
    const priceRange = maxP - minP || 1;
    let best = null;
    let bestScore = -Infinity;
    product.offers.forEach((o) => {
      const priceScore = 1 - (displayPrice(o) - minP) / priceRange; // 1 = más barato
      const ratingScore = (o.rating || 0) / 5;
      // Stock desconocido (las ofertas en vivo de Mercado Libre no lo
      // informan) puntúa neutro: castigarlo como "sobre pedido" hundiría
      // injustamente a esas ofertas por un dato que nadie afirmó.
      const stockScore = o.stock == null ? 0.5
        : o.stock === "in_stock" ? 1
        : o.stock === "low_stock" ? 0.5
        : 0;
      const score = priceScore * 0.4 + ratingScore * 0.3 + stockScore * 0.3;
      if (score > bestScore) { bestScore = score; best = o; }
    });
    const cheapest = product.offers.reduce((a, b) => (displayPrice(b) < displayPrice(a) ? b : a));
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

  // Mapea el nombre de color (ya normalizado por merge_color_variants.py,
  // p.ej. "Gris espacial") a un color de fondo real para pintar el punto.
  const COLOR_SWATCH_HEX = {
    "Negro": "#1a1a1a",
    "Blanco": "#f5f5f5",
    "Gris": "#9e9e9e",
    "Gris espacial": "#54524f",
    "Gris oscuro": "#4a4a4a",
    "Azul": "#2563eb",
    "Azul marino": "#1e3a5f",
    "Celeste": "#7dd3fc",
    "Rojo": "#dc2626",
    "Rosa": "#f472b6",
    "Oro rosa": "#e8b4b8",
    "Amarillo": "#facc15",
    "Verde": "#22c55e",
    "Verde oliva": "#6b7f3a",
    "Morado": "#9333ea",
    "Naranja": "#f97316",
    "Dorado": "#d4af37",
    "Plata": "#c0c0c0",
    "Café": "#6b4423",
    "Beige": "#d9c8a9",
    "Turquesa": "#14b8a6",
    "Coral": "#ff6f61",
    "Grafito": "#383838",
    "Transparente": "transparent",
    "Multicolor": "linear-gradient(135deg,#dc2626,#facc15,#22c55e,#2563eb)",
    "Vino": "#722f37",
    "Medianoche": "#191932",
    "Starlight": "#f0ead6",
  };

  function colorSwatchHtml(colorVariants) {
    if (!colorVariants || colorVariants.length === 0) return "";
    // Un punto por color único (si el mismo color aparece nuevo y
    // reacondicionado, cuenta una sola vez para el resumen visual).
    const seen = [];
    colorVariants.forEach((v) => {
      if (v.color && !seen.includes(v.color)) seen.push(v.color);
    });
    if (seen.length === 0) return "";
    const maxDots = 6;
    const shown = seen.slice(0, maxDots);
    const extra = seen.length - shown.length;
    const dots = shown
      .map((c) => {
        const bg = COLOR_SWATCH_HEX[c] || "#bbb";
        const border = c === "Blanco" || c === "Transparente" || c === "Starlight" ? "border:1px solid #ccc;" : "";
        return `<span class="color-dot" style="background:${bg};${border}" title="${htmlEscapeAttr(c)}"></span>`;
      })
      .join("");
    return `<div class="row-colors">${dots}${extra > 0 ? `<span class="color-dot-extra">+${extra}</span>` : ""}</div>`;
  }

  // Versión para la ficha de producto: cada punto es un link directo al
  // anuncio de ese color/condición en Mercado Libre, con el precio de esa
  // variante en el tooltip.
  function detailColorSwatchHtml(product) {
    const variants = product.colorVariants;
    if (!variants || variants.length === 0) return "";
    const dots = variants
      .map((v) => {
        const bg = COLOR_SWATCH_HEX[v.color] || "#bbb";
        const border = v.color === "Blanco" || v.color === "Transparente" || v.color === "Starlight" ? "border:1px solid #ccc;" : "";
        const refurb = v.condition === "refurbished" ? " · Reacondicionado" : "";
        const label = `${v.color || "Otro"}${refurb} — ${money(v.price)}`;
        return `<a class="color-dot-link" href="${htmlEscapeAttr(v.url)}" target="_blank" rel="noopener" title="${htmlEscapeAttr(label)}"><span class="color-dot" style="background:${bg};${border}"></span></a>`;
      })
      .join("");
    return `<div class="detail-colors-inner"><span class="detail-colors-label">Colores disponibles:</span> ${dots}</div>`;
  }

  // Pinta la imagen de un producto dentro de `container`.
  //
  // El catálogo local NO trae fotos: no hay una fuente propia con derechos
  // para las fotos de producto, así que por defecto se ve una ilustración
  // de la categoría (ver data/icons.json, product.image guarda la clave).
  // Cuando hay una API conectada (hoy solo Mercado Libre), la foto real
  // llega en la respuesta y se guarda en product.photo; entonces se
  // muestra esa.
  //
  // Si la URL falla (enlace roto, caída del CDN, bloqueo de hotlinking), el
  // onerror vuelve a la ilustración en vez de dejar el icono de imagen rota.
  // Reintentos con backoff antes de caer a la ilustración: probando en serio
  // contra el catálogo real, la gran mayoría de las fotos de AliExpress (y
  // del resto de las tiendas) cargan bien -- pero bajo carga alta (muchas
  // fotos del mismo CDN pidiéndose a la vez, que es justo lo que pasa al
  // abrir una lista de 60 productos) una fracción falla de forma transitoria
  // y sí carga bien si se reintenta unos segundos después. Antes cualquier
  // fallo, transitorio o no, se rendía a la ilustración para siempre sin
  // reintentar.
  const IMG_MAX_RETRIES = 2;
  const IMG_RETRY_DELAY_MS = 900;

  function renderProductMedia(container, product, variant) {
    if (!container) return;
    const iconKey = product.image || "box";
    if (!product.photo) {
      container.innerHTML = icon(iconKey, "product-placeholder-icon");
      container.classList.remove("has-photo");
      return;
    }
    container.classList.add("has-photo");
    container.textContent = "";
    const className = variant === "detail" ? "product-photo product-photo-detail" : "product-photo";
    let attempt = 0;
    // Crea un <img> nuevo en cada intento (en vez de reasignar .src al
    // mismo elemento): reasignar el mismo string a un <img> que ya falló no
    // siempre dispara una carga de red nueva en Chromium (lo trata como
    // "sin cambios"), lo cual se confirmó armando una prueba real con un
    // fallo simulado -- un elemento nuevo no tiene ese historial y sí
    // vuelve a pedir la imagen.
    const attach = () => {
      const img = document.createElement("img");
      img.className = className;
      img.alt = product.name || "";
      img.loading = "lazy";
      // Algunos CDN de terceros aplican protección anti-hotlink por
      // Referer; sin referrer de por medio, ese chequeo nunca puede
      // rechazar la carga.
      img.referrerPolicy = "no-referrer";
      img.onerror = () => {
        attempt += 1;
        if (attempt <= IMG_MAX_RETRIES) {
          setTimeout(attach, IMG_RETRY_DELAY_MS * attempt);
        } else {
          container.classList.remove("has-photo");
          container.innerHTML = icon(iconKey, "product-placeholder-icon");
        }
      };
      container.textContent = "";
      container.appendChild(img);
      img.src = product.photo;
    };
    attach();
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

  // "Top 5 más visitadas" en Inicio: cuenta reales de clics hacia cada
  // categoría en ESTE navegador (localStorage), nunca un número inventado
  // -- un sitio estático sin backend no tiene forma honesta de medir
  // clics agregados de todos los visitantes, así que el ranking es
  // siempre "lo que tú más visitaste", no "lo más popular del sitio".
  function trackCategoryClick(categoryId) {
    if (!categoryId) return;
    const counts = readLS(LS_KEYS.categoryClicks, {});
    counts[categoryId] = (counts[categoryId] || 0) + 1;
    writeLS(LS_KEYS.categoryClicks, counts);
  }
  function topClickedCategories(n) {
    const counts = readLS(LS_KEYS.categoryClicks, {});
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .map(([id, count]) => ({ cat: categoryById(id), count }))
      .filter((x) => x.cat) // por si una categoría se renombró/eliminó desde el último clic
      .slice(0, n);
  }

  // "Más visto en este navegador" en Inicio: mismo principio honesto que
  // trackCategoryClick() -- cuenta real de visitas a cada ficha de
  // producto EN ESTE navegador, nunca un número agregado de todo el
  // sitio (no hay backend que lo mida).
  function trackProductView(productId) {
    if (!productId) return;
    const counts = readLS(LS_KEYS.productViews, {});
    counts[productId] = (counts[productId] || 0) + 1;
    writeLS(LS_KEYS.productViews, counts);
  }
  function mostViewedProduct() {
    const counts = readLS(LS_KEYS.productViews, {});
    const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    for (const [id, count] of sorted) {
      const product = state.data.products.find((p) => p.id === id);
      if (product) return { product, count }; // salta ids de productos ya eliminados del catálogo
    }
    return null;
  }

  // Clics reales hacia la tienda (botón "Ver oferta"/variantes de color en
  // la tabla de ofertas), mismo principio honesto que trackProductView():
  // solo cuenta lo que pasó en ESTE navegador.
  function trackStoreClick(productId) {
    if (!productId) return;
    const counts = readLS(LS_KEYS.storeClicks, {});
    counts[productId] = (counts[productId] || 0) + 1;
    writeLS(LS_KEYS.storeClicks, counts);
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

  // El corazón usaba los emoji 🤍/❤, que en Windows (Segoe UI Emoji) se ven
  // con degradado y brillo -- justo el efecto "3D" que se quería quitar. Un
  // SVG plano con fill="currentColor" se ve igual de flat en cualquier
  // sistema y hereda el color por CSS (.fav-btn / .row-fav-btn.is-fav), sin
  // depender de qué fuente de emoji tenga instalada quien lo mire.
  const HEART_FILLED_PATH =
    "M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z";
  const HEART_OUTLINE_PATH =
    "M16.5 3c-1.74 0-3.41.81-4.5 2.09C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54L12 21.35l1.45-1.32C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3zm-4.4 15.55l-.1.1-.1-.1C7.14 14.24 4 11.39 4 8.5 4 6.5 5.5 5 7.5 5c1.54 0 3.04.99 3.57 2.36h1.87C13.46 5.99 14.96 5 16.5 5c2 0 3.5 1.5 3.5 3.5 0 2.89-3.14 5.74-7.9 10.05z";
  function favIconHtml(productId) {
    const path = isFavorite(productId) ? HEART_FILLED_PATH : HEART_OUTLINE_PATH;
    return `<svg class="heart-icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="${path}"/></svg>`;
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
    // Set de iconos ilustrados (SVG en línea) usado en vez de emoji en todo
    // el sitio; si falla, ICON_FALLBACK cubre cualquier clave pedida.
    try {
      const res3 = await fetch("data/icons.json");
      state.icons = await res3.json();
    } catch {
      state.icons = {};
    }
  }

  // Markup SVG de línea para un box de 24x24 si el set de iconos no cargó.
  const ICON_FALLBACK = '<rect x="3" y="3" width="18" height="18" rx="3" fill="none" stroke="currentColor" stroke-width="1.7"/>';

  // Devuelve el <svg> en línea para `key` (clave de data/icons.json). Se usa
  // en vez de emoji en toda la interfaz: mismo trazo/color en cualquier
  // sistema operativo, en vez de depender de la fuente de emoji instalada.
  function icon(key, cls) {
    const inner = (state.icons && state.icons[key]) || ICON_FALLBACK;
    return `<svg class="icon${cls ? " " + cls : ""}" viewBox="0 0 24 24" aria-hidden="true">${inner}</svg>`;
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
    // A diferencia de category/query, subcategory se resetea a null salvo
    // que quien llama la pase explícita -- así ningún caller (buscador,
    // tarjeta "Todas", etc.) puede olvidarse de "soltar" una subcategoría
    // de una navegación anterior y dejarla pegada donde ya no aplica.
    state.subcategory = opts && opts.subcategory !== undefined ? opts.subcategory : null;
    if (opts && opts.query !== undefined) state.query = opts.query;
    navigateTo("#/list", renderList);
  }

  // Entrar a una categoría (desde Inicio, la barra de categorías o el
  // filtro) siempre parte del ranking de popularidad, como en Kakaku.com:
  // ahí es donde vive el paso 2 del recorrido (categoría → ranking → precio).
  function goCategoryRanking(categoryId, subcategoryId) {
    trackCategoryClick(categoryId);
    state.sort = "popularity";
    goList({ category: categoryId, subcategory: subcategoryId || null, query: "" });
  }

  function goDetail(productId) {
    // Si el hash ya es el de este mismo producto (p. ej. se hace clic de
    // nuevo en la misma ficha sin haber navegado a otro lado), navigateTo()
    // llama renderDetail() directo sin cambiar location.hash -- eso nunca
    // dispara "hashchange", que es donde onHashChange() cuenta la visita
    // (ver ahí el porqué: renderDetail se re-ejecuta por otras razones,
    // como marcar favorito, que no son visitas nuevas). Se cuenta acá para
    // cubrir justo ese caso, sin duplicar el conteo del caso normal
    // (hash distinto), que sigue contándose únicamente en onHashChange.
    if (location.hash === `#/p/${productId}`) trackProductView(productId);
    navigateTo(`#/p/${productId}`, () => renderDetail(productId));
  }

  // Vuelve a pintar la vista que ya esté visible (sin cambiar el hash ni
  // hacer scroll-to-top como sí hace onHashChange en una navegación real)
  // -- usado por el toggle "Incluir envío", que cambia el precio en
  // cualquier vista sin que el usuario haya navegado a ningún lado.
  function rerenderCurrentView() {
    const hash = location.hash;
    const detailMatch = hash.match(/#\/p\/(.+)/);
    if (detailMatch) renderDetail(detailMatch[1]);
    else if (hash === "#/list" || hash.startsWith("#/list?")) renderList();
    else if (hash === "#/favorites") renderFavorites();
    else if (hash === "#/account") renderAccount();
    else if (hash === "#/marcas" || hash.startsWith("#/marcas?")) renderBrands();
    else renderHome();
  }

  function onHashChange() {
    if (!state.data) return;
    const hash = location.hash;
    const detailMatch = hash.match(/#\/p\/(.+)/);
    if (detailMatch) {
      // Se cuenta acá (no dentro de renderDetail) porque renderDetail()
      // también se vuelve a llamar sin que haya una navegación real (p.
      // ej. al marcar/desmarcar favorito, o al cambiar el toggle "Incluir
      // envío") -- onHashChange en cambio solo corre cuando el hash
      // realmente cambió: navegación interna (goDetail), un link directo
      // a #/p/<id> (páginas SEO estáticas), o adelante/atrás del navegador.
      trackProductView(detailMatch[1]);
      renderDetail(detailMatch[1]);
    } else if (hash === "#/list" || hash.startsWith("#/list?")) {
      // Permite enlazar directo a una categoría filtrada (p. ej. desde las
      // páginas estáticas de SEO: #/list?cat=Celulares&sub=Celulares), sin
      // lo cual esos enlaces caían al inicio en vez de abrir el listado ya
      // filtrado.
      // Un hash con "?" es siempre un link externo/profundo (páginas
      // estáticas de SEO, o una URL pegada a mano) y se trata como
      // especificación completa: category/subcategory se derivan enteros
      // de la URL (subcategory cae a null si no viene "sub", igual que
      // goList()). Un hash "#/list" sin "?" en cambio solo puede venir de
      // una navegación interna (goList() ya deja el state listo en JS
      // antes de cambiar el hash, sin codificarlo en la URL), así que ahí
      // no se toca nada -- si se pisara siempre iguial, un link profundo a
      // una categoría sin "sub" no limpiaba una subcategoría que hubiera
      // quedado puesta de la navegación anterior (iban a parar 0
      // resultados: categoría nueva + subcategoría de otra categoría).
      const qs = hash.includes("?") ? new URLSearchParams(hash.split("?")[1]) : null;
      if (qs) {
        state.category = qs.get("cat") || null;
        state.subcategory = qs.get("sub") || null;
      }
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
    // Los submenús viven en document.body (ver más abajo), no dentro de
    // #catNav, así que hay que limpiarlos aparte en cada repintado.
    document.querySelectorAll(".cat-submenu").forEach((node) => node.remove());
    state.data.categories.forEach((c) => {
      const hasSub = c.subcategories && c.subcategories.length > 0;
      const item = document.createElement("div");
      item.className = "cat-item";

      const label = document.createElement("span");
      label.innerHTML = `${icon(c.icon, "cat-item-icon")} ${c.name}${hasSub ? " ▾" : ""}`;
      const isActive = location.hash === "#/list" && state.category === c.id && !state.subcategory;
      label.className = isActive ? "active" : "";
      label.onclick = () => goCategoryRanking(c.id);
      item.appendChild(label);

      if (hasSub) {
        const submenu = document.createElement("div");
        submenu.className = "cat-submenu";
        c.subcategories.forEach((s) => {
          const link = document.createElement("a");
          link.innerHTML = `${icon(s.icon, "cat-item-icon")} ${s.name}`;
          const subActive =
            location.hash === "#/list" && state.category === c.id && state.subcategory === s.id;
          link.className = subActive ? "active" : "";
          link.onclick = (e) => {
            e.stopPropagation();
            goCategoryRanking(c.id, s.id);
          };
          submenu.appendChild(link);
        });
        // position:fixed (en vez de absolute) para que el submenú escape del
        // overflow:hidden de .cats (necesario para el plegado de la barra de
        // categorías) -- si no, el submenú quedaría cortado detrás de la
        // barra en vez de flotar por encima.
        //
        // El submenú tampoco es descendiente de .cat-item en el DOM (está en
        // document.body), así que moverse del item al submenú cuenta como
        // "salir" de .cat-item -- de ahí el pequeño retraso antes de
        // esconderlo, cancelable si el mouse entra al submenú a tiempo.
        let hideTimer = null;
        const cancelHide = () => { if (hideTimer) clearTimeout(hideTimer); };
        const scheduleHide = () => { hideTimer = setTimeout(() => submenu.classList.remove("visible"), 120); };
        item.addEventListener("mouseenter", () => {
          cancelHide();
          const r = item.getBoundingClientRect();
          submenu.style.left = `${r.left}px`;
          submenu.style.top = `${r.bottom}px`;
          submenu.classList.add("visible");
        });
        item.addEventListener("mouseleave", scheduleHide);
        submenu.addEventListener("mouseenter", cancelHide);
        submenu.addEventListener("mouseleave", scheduleHide);
        document.body.appendChild(submenu);
      }

      el.catNav.appendChild(item);
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
      <span class="category-card-icon category-card-icon--photo">${icon("shopping-bag")}</span>
      <span class="category-card-name">Todas</span>
      <span class="category-card-count">${state.data.products.length} productos</span>
    `;
    allCard.onclick = () => { state.sort = "relevance"; goList({ category: null, query: "" }); };
    el.homeCategoryGrid.appendChild(allCard);

    state.data.categories.forEach((cat) => {
      const categoryProducts = state.data.products.filter((p) => p.category === cat.id);
      const card = document.createElement("button");
      card.type = "button";
      card.className = "category-card";
      card.innerHTML = `
        <span class="category-card-icon category-card-icon--photo"></span>
        <span class="category-card-name">${cat.name}</span>
        <span class="category-card-count">${categoryProducts.length} productos</span>
      `;
      const iconEl = card.querySelector(".category-card-icon");
      // El ícono es la foto real del producto más popular de la categoría
      // (mismo criterio de "popular" que el resto del sitio -- ver
      // topByPopularity: reseñas totales, excluyendo usados), no un emoji
      // fijo -- así el ícono cambia solo si cambia lo que más se vende.
      // renderProductMedia ya sabe reintentar y caer al emoji del propio
      // producto si la foto falla o no existe, así que no hace falta
      // duplicar esa lógica acá. El marco es un rectángulo horizontal
      // (category-card-icon--photo, con object-fit:contain) en vez del
      // círculo original -- un círculo recorta los bordes de una foto de
      // producto real (a diferencia de un emoji, que no tiene "bordes"
      // que perder), así que se aplica siempre, tanto para las fotos
      // como para el emoji de respaldo, para que todas las tarjetas
      // compartan la misma forma de marco.
      const topProduct = topByPopularity(categoryProducts, 1)[0];
      if (topProduct) {
        renderProductMedia(iconEl, topProduct);
      } else if (cat.iconImage) {
        // Categoría sin productos (no debería pasar hoy, pero por si acaso):
        // cae a la ilustración subida a mano, si la categoría tiene una.
        iconEl.innerHTML = `<img src="${htmlEscapeAttr(cat.iconImage)}" alt="">`;
      } else {
        iconEl.innerHTML = icon(cat.icon);
      }
      card.onclick = () => goCategoryRanking(cat.id);
      el.homeCategoryGrid.appendChild(card);
    });

    renderHomeTopCategories();
    renderHomeRankings();
    renderHomeMostViewed();
  }

  // Debajo del ranking: la ficha (resumida) del producto más visto en
  // este navegador -- mismo principio honesto que renderHomeTopCategories
  // (ver trackProductView), nunca un "más visto" agregado de todo el
  // sitio porque no hay backend que lo mida.
  function renderHomeMostViewed() {
    const top = mostViewedProduct();
    el.homeMostViewed.innerHTML = "";
    if (!top) {
      const empty = document.createElement("p");
      empty.className = "most-viewed-empty";
      empty.textContent = "Todavía no visitaste ninguna ficha de producto en este navegador. Entra a un producto y aparecerá aquí.";
      el.homeMostViewed.appendChild(empty);
      return;
    }
    const { product, count } = top;
    const { avg, count: ratingCount } = aggregateRating(product);
    const discountPct = bestDiscountPct(product);
    const savings = bestSavingsAmount(product);
    const card = document.createElement("div");
    card.className = "most-viewed-card";
    card.innerHTML = `
      <div class="most-viewed-icon"></div>
      <div class="most-viewed-info">
        <p class="muted small">${htmlEscapeAttr(product.brand)} · ${plural(count, "visita", "visitas")} en este navegador</p>
        <h3>${htmlEscapeAttr(product.name)}${conditionBadge(product)}${usageBadge(product)}</h3>
        <div class="detail-rating">
          ${ratingCount > 0
            ? `${starsHtml(avg)} ${avg.toFixed(1)} <span class="rc">(${plural(ratingCount, "calificación", "calificaciones")})</span>`
            : colorSwatchHtml(product.colorVariants) || `<span class="rc">Sin calificaciones todavía</span>`}
        </div>
        <p class="detail-fromprice">
          ${offerCount(product) > 1 ? "Desde " : ""}<strong>${money(minPrice(product))}</strong>${discountPct ? `<span class="discount-badge">-${discountPct}%</span>` : ""} en ${plural(offerCount(product), "tienda", "tiendas")}
          ${savings ? `<span class="save-amount">Ahorras ${money(savings)}</span>` : ""}
        </p>
        <button type="button" class="most-viewed-cta">Ver ficha completa →</button>
      </div>
    `;
    renderProductMedia(card.querySelector(".most-viewed-icon"), product, "detail");
    card.onclick = () => goDetail(product.id);
    el.homeMostViewed.appendChild(card);
  }

  function renderHomeTopCategories() {
    const top = topClickedCategories(5);
    el.homeTopCategoriesList.innerHTML = "";
    if (top.length === 0) {
      const empty = document.createElement("p");
      empty.className = "home-top-categories-empty";
      empty.textContent = "Todavía no hay categorías visitadas en este navegador. Explora el catálogo y aparecerán aquí.";
      el.homeTopCategoriesList.appendChild(empty);
      return;
    }
    top.forEach(({ cat, count }, i) => {
      const item = document.createElement("button");
      item.type = "button";
      item.className = "home-top-category-item";
      item.innerHTML = `
        <span class="home-top-category-rank">${i + 1}</span>
        <span class="home-top-category-photo"></span>
        <span class="home-top-category-name">${cat.name}</span>
        <span class="home-top-category-count">${plural(count, "clic", "clics")}</span>
      `;
      // Foto del #2 en popularidad de la categoría (no el #1: esa ya es la
      // que se ve en la tarjeta de categoría de más arriba en la misma
      // página -- repetirla acá se vería como que el panel no cargó una
      // foto distinta). Si la categoría no llega a tener un segundo
      // producto, renderProductMedia cae sola a la ilustración.
      const categoryProducts = state.data.products.filter((p) => p.category === cat.id);
      const second = topByPopularity(categoryProducts, 2)[1];
      if (second) renderProductMedia(item.querySelector(".home-top-category-photo"), second);
      item.onclick = () => goCategoryRanking(cat.id);
      el.homeTopCategoriesList.appendChild(item);
    });
  }

  // Top N por el mismo criterio de "popularidad" que ya usa el resto del
  // sitio (ver popularityScore) -- no es un ranking de ventas reales, es el
  // mismo puntaje que ya se muestra como "más populares" en cualquier
  // categoría, solo que acá se arma un resumen de 3 en 3 para la portada
  // en vez de la lista completa paginada.
  // Los usados se excluyen del ranking (a diferencia del listado normal,
  // donde siguen apareciendo y el usuario puede optar por ocultarlos con
  // "Excluir usados"): un ranking implica "esto es lo que vas a poder
  // comprar", pero un artículo usado específico no tiene reproducibilidad
  // -- para cuando otra persona lo vea, esa pieza en particular puede ya
  // no estar disponible, así que recomendarla como "top" es engañoso.
  function topByPopularity(products, n) {
    return products.filter((p) => !isUsed(p)).sort((a, b) => popularityScore(b) - popularityScore(a)).slice(0, n);
  }

  // Resumen de rankings en Inicio, estilo Kakaku.com: un bloque general con
  // el top 3 de todo el catálogo, más un bloque por cada una de las 3
  // categorías con más productos (esa es la señal de "categoría popular"
  // que sí se puede calcular de forma honesta con los datos que hay --
  // "Otros" se excluye del top 3 porque es la bolsa de misceláneos sin
  // equivalente en la taxonomía, no una categoría real que alguien busque).
  function renderHomeRankings() {
    el.homeRankings.innerHTML = "";

    const topCategories = state.data.categories
      .filter((c) => c.id !== "Otros")
      .map((c) => ({ cat: c, count: state.data.products.filter((p) => p.category === c.id).length }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 3);

    const blocks = [
      { title: `${icon("trophy")} Ranking general ComparaMX`, products: state.data.products, onMore: () => { state.sort = "popularity"; goList({ category: null, query: "" }); } },
      ...topCategories.map(({ cat }) => ({
        title: `${icon(cat.icon, "cat-item-icon")} ${cat.name} — ranking`,
        products: state.data.products.filter((p) => p.category === cat.id),
        onMore: () => goCategoryRanking(cat.id),
      })),
    ];

    blocks.forEach((block) => {
      const top3 = topByPopularity(block.products, 3);
      if (top3.length === 0) return;
      const section = document.createElement("div");
      section.className = "ranking-block";
      section.innerHTML = `
        <div class="ranking-block-head">${block.title}</div>
        <div class="ranking-block-list"></div>
        <button type="button" class="ranking-block-more">Ver ranking completo →</button>
      `;
      renderProductListInto(section.querySelector(".ranking-block-list"), top3, {
        emptyText: "",
        withRank: true,
        medals: true,
        onFavToggle: renderHomeRankings,
      });
      section.querySelector(".ranking-block-more").onclick = block.onMore;
      el.homeRankings.appendChild(section);
    });
  }

  // ---------- Vista: Lista (búsqueda / categoría) ----------

  function brandsInScope() {
    const scoped = state.category
      ? state.data.products.filter((p) => p.category === state.category)
      : state.data.products;
    return [...new Set(scoped.map((p) => p.brand))].sort();
  }

  // Rango real de precios (con el toggle de envío ya aplicado) del alcance
  // actual -- misma noción de "alcance" que brandsInScope(), solo por
  // categoría -- para que el slider de precio siempre cubra el 100% de lo
  // que hay para ver en vez de un tope fijo global que sería inútil tanto
  // en una categoría barata como en una cara.
  function priceScopeBounds() {
    const scoped = state.category
      ? state.data.products.filter((p) => p.category === state.category)
      : state.data.products;
    if (scoped.length === 0) return { min: 0, max: 1000 };
    const prices = scoped.map(minPrice);
    const min = Math.floor(Math.min(...prices));
    const max = Math.max(Math.ceil(Math.max(...prices)), min + 1);
    return { min, max };
  }

  function filteredProducts() {
    const ratingMin = (RATING_FILTERS.find((r) => r.id === state.minRating) || RATING_FILTERS[0]).min;
    return state.data.products.filter((p) => {
      const q = state.query.toLowerCase();
      const matchesQuery =
        !q ||
        p.name.toLowerCase().includes(q) ||
        p.brand.toLowerCase().includes(q) ||
        p.category.toLowerCase().includes(q);
      const matchesCat = !state.category || p.category === state.category;
      const matchesSub = !state.subcategory || p.subcategory === state.subcategory;
      const price = minPrice(p);
      const matchesPrice = (state.priceMin == null || price >= state.priceMin) && (state.priceMax == null || price <= state.priceMax);
      const matchesBrand = state.brands.size === 0 || state.brands.has(p.brand);
      // Redondeado a 1 decimal para que coincida con el valor mostrado en pantalla.
      const matchesRating = Math.round(aggregateRating(p).avg * 10) / 10 >= ratingMin;
      const matchesCondition = !state.excludeUsed || !isUsed(p);
      const matchesMagsafe = !state.magsafeOnly || isMagSafe(p);
      const matchesSize = state.sizeFilter === "all" || productSize(p) === state.sizeFilter;
      return matchesQuery && matchesCat && matchesSub && matchesPrice && matchesBrand && matchesRating && matchesCondition && matchesMagsafe && matchesSize;
    });
  }

  function sortedProducts(products) {
    const list = products.slice();
    if (state.sort === "popularity") list.sort((a, b) => popularityScore(b) - popularityScore(a));
    else if (state.sort === "price_asc") list.sort((a, b) => minPrice(a) - minPrice(b));
    else if (state.sort === "price_desc") list.sort((a, b) => minPrice(b) - minPrice(a));
    else if (state.sort === "rating_desc") list.sort((a, b) => aggregateRating(b).avg - aggregateRating(a).avg);
    return list;
  }

  function renderList() {
    state.page = 1; // toda entrada "de cero" a la lista arranca en la página 1
    setActiveView("list");
    renderCatNav();

    el.listBreadcrumb.innerHTML = `<a href="#/">Inicio</a>`;
    if (state.category) {
      const cat = categoryById(state.category);
      el.listBreadcrumb.innerHTML += ` &gt; <a href="#" id="breadcrumbCatOnly">${cat.name}</a>`;
      const sub = subcategoryById(state.category, state.subcategory);
      if (sub) el.listBreadcrumb.innerHTML += ` &gt; ${sub.name}`;
    } else if (state.query) {
      el.listBreadcrumb.innerHTML += ` &gt; Resultados de búsqueda`;
    } else {
      el.listBreadcrumb.innerHTML += ` &gt; Todos los productos`;
    }
    const breadcrumbCatOnly = document.getElementById("breadcrumbCatOnly");
    if (breadcrumbCatOnly) {
      breadcrumbCatOnly.onclick = (e) => {
        e.preventDefault();
        state.subcategory = null;
        renderList();
      };
    }

    el.sortSelect.value = state.sort;

    renderFilterCategory();
    renderFilterPrice();
    renderFilterBrand();
    renderFilterRating();
    renderFilterCondition();
    renderFilterMagsafe();
    renderFilterSize();

    renderProductListPage();
    renderLiveSearchSection();
  }

  // Dibuja solo el cuerpo de la lista (filas + paginación + título) sin
  // tocar filtros/breadcrumb -- lo usan tanto renderList() (vista nueva) como
  // los controles de paginación y el toggle de favorito (para no perder la
  // página en la que está el usuario ni repintar todo de nuevo).
  function renderProductListPage() {
    // Paso 2 del recorrido estilo Kakaku.com (categoría → ranking de
    // populares → precio): al entrar por una categoría, sin búsqueda de
    // texto, la lista se muestra como ranking numerado en vez de lista plana.
    const isCategoryRanking = !!state.category && !state.query;

    const filtered = filteredProducts();
    const sorted = sortedProducts(filtered);
    const totalPages = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE));
    state.page = Math.min(Math.max(1, state.page), totalPages);
    const startIdx = (state.page - 1) * PAGE_SIZE;
    const pageItems = sorted.slice(startIdx, startIdx + PAGE_SIZE);

    renderProductListInto(el.productList, pageItems, {
      emptyText: "No se encontraron productos con estos filtros.",
      onFavToggle: renderProductListPage,
      withRank: isCategoryRanking,
      // La corona y las medallas de color solo significan algo cuando la
      // lista de verdad está ordenada por popularidad. Con orden por precio
      // o relevancia seguían apareciendo, dándole un "🏆 #1" al primero de
      // una lista que no es un ranking; ahí se deja la numeración a secas.
      medals: state.sort === "popularity",
      rankOffset: startIdx,
    });
    renderPagination(totalPages);

    const subLabel = subcategoryById(state.category, state.subcategory);
    // El título decía siempre "más populares" aunque el orden fuera otro:
    // al entrar por un enlace directo (#/list?cat=...), que es justo como
    // llega alguien desde Google o desde las páginas estáticas de
    // categoría, el orden queda en "Relevancia" y el título contradecía al
    // selector de orden que tenía al lado.
    const SORT_LABELS = {
      popularity: "más populares",
      relevance: "por relevancia",
      price_asc: "del más barato al más caro",
      price_desc: "del más caro al más barato",
      rating_desc: "mejor calificados",
    };
    const sortLabel = SORT_LABELS[state.sort] || SORT_LABELS.relevance;
    el.listTitle.textContent = state.query
      ? `Resultados para "${state.query}" (${filtered.length})`
      : state.category
      ? `${categoryById(state.category).name}${subLabel ? " › " + subLabel.name : ""} — ${sortLabel} (${filtered.length})`
      : `Todos los productos — ${sortLabel} (${filtered.length})`;
  }

  function renderPagination(totalPages) {
    if (totalPages <= 1) {
      el.pagination.innerHTML = "";
      return;
    }
    const goToPage = (p) => {
      state.page = p;
      renderProductListPage();
      el.productList.scrollIntoView({ block: "start", behavior: "instant" });
    };
    const prevDisabled = state.page <= 1;
    const nextDisabled = state.page >= totalPages;
    el.pagination.innerHTML = `
      <button class="page-btn" id="pagePrev" ${prevDisabled ? "disabled" : ""}>&laquo; Anterior</button>
      <span class="page-indicator">Página ${state.page} de ${totalPages}</span>
      <button class="page-btn" id="pageNext" ${nextDisabled ? "disabled" : ""}>Siguiente &raquo;</button>
    `;
    if (!prevDisabled) el.pagination.querySelector("#pagePrev").onclick = () => goToPage(state.page - 1);
    if (!nextDisabled) el.pagination.querySelector("#pageNext").onclick = () => goToPage(state.page + 1);
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
      // Este resultado viene directo de la búsqueda en vivo de Mercado
      // Libre (no es una oferta guardada del catálogo): shippingFree ya es
      // un dato real y confiable (gratis = no suma nada); cuando es false
      // se suma la misma tarifa de referencia que el resto del catálogo
      // usa para Mercado Libre (SHIPPING_ESTIMATE_MXN.mercadolibre).
      const liveShipEstimated = state.includeShipping && !item.shippingFree;
      const livePrice = item.price + (liveShipEstimated ? SHIPPING_ESTIMATE_MXN.mercadolibre : 0);
      row.innerHTML = `
        <span class="row-icon">${icon("search")}</span>
        <div class="row-info">
          <div class="row-brand">Mercado Libre</div>
          <div class="row-name">${htmlEscapeAttr(item.title)}</div>
          <div class="row-stars muted">${shippingText}</div>
        </div>
        <div class="row-priceblock">
          <div class="row-price">${money(livePrice)}</div>
          ${liveShipEstimated ? `<span class="shipping-estimate-note">${icon("alert-triangle")} envío estimado incluido</span>` : ""}
          <div class="row-external-badge">Ver en Mercado Libre ↗</div>
        </div>
      `;
      // Los resultados en vivo sí traen foto real de la tienda; si no viene,
      // se queda la lupa como marcador.
      renderProductMedia(row.querySelector(".row-icon"), { photo: item.photo, image: "search", name: item.title });
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
      const rank = (opts.rankOffset || 0) + i + 1;
      // Un pequeño aviso "de un vistazo" en la lista, sin abrir la ficha,
      // de que este producto tiene más colores/tallas disponibles (los
      // pills completos, con link a cada uno, viven en la tabla de la
      // ficha de producto — ver renderOfferRows).
      const variantCount = Math.max(0, ...p.offers.map((o) => (o.variants ? o.variants.length : 0)));
      const usedBadge = conditionBadge(p);
      const commercialBadge = usageBadge(p);
      const row = document.createElement("div");
      const rankClass = opts.medals && rank >= 2 && rank <= 4 ? ` rank-${rank}` : "";
      row.className = "product-row" + (opts.withRank ? " has-rank" + rankClass : "");
      row.innerHTML = `
        ${opts.withRank ? `<span class="rank-badge">${opts.medals && rank === 1 ? icon("crown") : rank}</span>` : ""}
        <span class="row-icon"></span>
        <div class="row-info">
          <div class="row-brand">${p.brand}</div>
          <div class="row-name">${p.name}${usedBadge}${commercialBadge}${variantCount > 0 ? `<span class="variant-count-badge" title="También disponible en otros colores/tallas">${icon("palette")} +${variantCount}</span>` : ""}</div>
          ${
            // Sin reseñas propias todavía, la fila mostraba "☆☆☆☆☆ 0.0 (0)"
            // en los 16 mil productos: 60 veces por página de puro ruido que
            // además hacía ver el sitio como si no hubiera cargado. Cuando
            // no hay calificaciones simplemente no se pinta la línea (la
            // ficha del producto sí lo dice, una sola vez y en contexto).
            // En su lugar, si el producto junta varios colores (fusionados
            // por merge_color_variants.py), ese mismo espacio muestra los
            // puntos de color disponibles.
            count > 0
              ? `<div class="row-stars">${starsHtml(avg)} <span class="muted">${avg.toFixed(1)} (${count})</span></div>`
              : colorSwatchHtml(p.colorVariants)
          }
        </div>
        <div class="row-priceblock">
          ${offerCount(p) > 1 ? `<div class="row-from">Desde</div>` : ""}
          <div class="row-price">${money(minPrice(p))}${bestDiscountPct(p) ? `<span class="discount-badge">-${bestDiscountPct(p)}%</span>` : ""}</div>
          ${cheapestOfferShippingEstimated(p) ? `<span class="shipping-estimate-note">${icon("alert-triangle")} envío estimado incluido</span>` : ""}
          <div class="row-stores">${plural(offerCount(p), "tienda", "tiendas")}</div>
        </div>
        <button class="row-fav-btn" aria-label="Favorito"></button>
      `;
      renderProductMedia(row.querySelector(".row-icon"), p);
      row.onclick = () => goDetail(p.id);
      bindFavToggle(row.querySelector(".row-fav-btn"), p.id, opts.onFavToggle);
      row.querySelector(".row-fav-btn").innerHTML = favIconHtml(p.id);
      container.appendChild(row);
    });
  }

  function renderFilterCategory() {
    el.filterCategory.innerHTML = "";
    const allOpt = document.createElement("label");
    allOpt.className = "filter-option" + (!state.category ? " active" : "");
    allOpt.innerHTML = `<input type="radio" name="fcat" ${!state.category ? "checked" : ""}> Todas`;
    allOpt.onclick = () => {
      state.category = null;
      state.subcategory = null;
      state.brands.clear();
      state.sort = "relevance";
      renderList();
    };
    el.filterCategory.appendChild(allOpt);

    // Con una categoría ya elegida, el panel se recorta a mostrar solo esa
    // categoría y sus subcategorías (más "Todas" arriba, para volver) --
    // antes seguía listando las otras ~50 categorías aunque ninguna
    // aplicara ya, obligando a scrollear un montón para ver dónde estaba
    // parada la selección actual y qué subcategorías tenía.
    const categoriesToShow = state.category
      ? state.data.categories.filter((c) => c.id === state.category)
      : state.data.categories;

    categoriesToShow.forEach((c) => {
      const isActive = state.category === c.id;
      const opt = document.createElement("label");
      opt.className = "filter-option" + (isActive && !state.subcategory ? " active" : "");
      opt.innerHTML = `<input type="radio" name="fcat" ${isActive && !state.subcategory ? "checked" : ""}> ${icon(c.icon, "cat-item-icon")} ${c.name}`;
      opt.onclick = () => {
        state.category = c.id;
        state.subcategory = null;
        state.brands.clear();
        state.sort = "popularity";
        renderList();
      };
      el.filterCategory.appendChild(opt);

      // Las subcategorías solo se muestran, sangradas, cuando su categoría
      // ya está activa -- así el filtro no se vuelve una lista gigante con
      // las ~40 subcategorías de las 15 categorías todas a la vez.
      if (isActive && c.subcategories && c.subcategories.length > 0) {
        c.subcategories.forEach((s) => {
          const subActive = state.subcategory === s.id;
          const subOpt = document.createElement("label");
          subOpt.className = "filter-option filter-suboption" + (subActive ? " active" : "");
          subOpt.innerHTML = `<input type="radio" name="fcat" ${subActive ? "checked" : ""}> ${icon(s.icon, "cat-item-icon")} ${s.name}`;
          subOpt.onclick = () => {
            state.subcategory = s.id;
            renderList();
          };
          el.filterCategory.appendChild(subOpt);
        });
      }
    });
  }

  // Slider de dos manijas + inputs numéricos (reemplaza la vieja lista de
  // rangos fijos). A diferencia de renderFilterBrand()/renderFilterRating()
  // etc., los <input type=range>/<input type=number> son estáticos en el
  // HTML (ver index.html) y NO se recrean en cada render -- solo se
  // actualizan sus atributos min/max/step/value acá, para no perder el
  // arrastre en curso ni el foco del usuario.
  function renderFilterPrice() {
    const { min, max } = priceScopeBounds();
    // Redondea los límites al múltiplo "limpio" más cercano hacia afuera
    // (10/100/500 según el tamaño del rango) para que el slider no
    // arranque en un número como $9,842.
    const step = max - min > 20000 ? 500 : max - min > 2000 ? 100 : 10;
    const boundMin = Math.floor(min / step) * step;
    const boundMax = Math.max(Math.ceil(max / step) * step, boundMin + step);

    const curMin = state.priceMin == null ? boundMin : Math.min(Math.max(state.priceMin, boundMin), boundMax);
    const curMax = state.priceMax == null ? boundMax : Math.min(Math.max(state.priceMax, boundMin), boundMax);

    [el.priceRangeMin, el.priceRangeMax].forEach((input) => {
      input.min = boundMin;
      input.max = boundMax;
      input.step = step;
    });
    el.priceRangeMin.value = curMin;
    el.priceRangeMax.value = curMax;
    el.priceNumMin.value = state.priceMin == null ? "" : state.priceMin;
    el.priceNumMax.value = state.priceMax == null ? "" : state.priceMax;
    el.priceNumMin.placeholder = money(boundMin);
    el.priceNumMax.placeholder = money(boundMax);

    updatePriceRangeFill(boundMin, boundMax, curMin, curMax);
  }

  function updatePriceRangeFill(boundMin, boundMax, curMin, curMax) {
    const span = boundMax - boundMin || 1;
    const leftPct = ((curMin - boundMin) / span) * 100;
    const rightPct = ((curMax - boundMin) / span) * 100;
    el.priceRangeFill.style.left = `${leftPct}%`;
    el.priceRangeFill.style.right = `${100 - rightPct}%`;
  }

  // min/max en pesos reales (null = sin tope, "todos los precios") a partir
  // de los valores actuales del slider/inputs; null cuando el valor está
  // pegado al límite del alcance actual (equivale a "sin filtro" en ese
  // extremo, así el filtro no se queda pegado si luego cambia de categoría
  // y el alcance se agranda).
  function commitPriceRange(vMin, vMax) {
    const boundMin = Number(el.priceRangeMin.min);
    const boundMax = Number(el.priceRangeMin.max);
    state.priceMin = vMin <= boundMin ? null : vMin;
    state.priceMax = vMax >= boundMax ? null : vMax;
    renderList();
  }

  function renderFilterBrand() {
    el.filterBrand.innerHTML = "";
    const brands = brandsInScope();
    // Si una marca seleccionada ya no aplica en el alcance actual, se descarta.
    [...state.brands].forEach((b) => { if (!brands.includes(b)) state.brands.delete(b); });

    // El cuadro de búsqueda solo filtra qué checkboxes se muestran; no toca
    // state.brands, así que una marca ya marcada sigue activa aunque quede
    // oculta al escribir otra búsqueda.
    const query = (el.filterBrandSearch.value || "").trim().toLowerCase();
    const visibleBrands = query ? brands.filter((b) => b.toLowerCase().includes(query)) : brands;

    if (query && visibleBrands.length === 0) {
      const empty = document.createElement("p");
      empty.className = "filter-empty";
      empty.textContent = `Sin marcas para "${el.filterBrandSearch.value.trim()}"`;
      el.filterBrand.appendChild(empty);
      return;
    }

    visibleBrands.forEach((b) => {
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

  function renderFilterCondition() {
    el.filterCondition.innerHTML = "";
    const opt = document.createElement("label");
    opt.className = "filter-option" + (state.excludeUsed ? " active" : "");
    opt.innerHTML = `<input type="checkbox" ${state.excludeUsed ? "checked" : ""}> Excluir usados`;
    opt.onclick = (e) => {
      e.preventDefault();
      state.excludeUsed = !state.excludeUsed;
      renderList();
    };
    el.filterCondition.appendChild(opt);
  }

  // Filtro "Solo compatibles con MagSafe": solo tiene sentido en Baterías
  // portátiles (un power bank sin MagSafe sigue siendo un power bank
  // válido, así que no se excluye del catálogo, pero el usuario que
  // específicamente busca uno magnético necesita poder filtrarlo). El
  // grupo entero se esconde fuera de esa categoría en vez de mostrar un
  // filtro que no aplicaría a nada.
  function renderFilterMagsafe() {
    const relevant = state.category === "Baterías portátiles";
    el.filterMagsafeGroup.classList.toggle("hidden", !relevant);
    if (!relevant) {
      state.magsafeOnly = false;
      return;
    }
    el.filterMagsafe.innerHTML = "";
    const opt = document.createElement("label");
    opt.className = "filter-option" + (state.magsafeOnly ? " active" : "");
    opt.innerHTML = `<input type="checkbox" ${state.magsafeOnly ? "checked" : ""}> Solo compatibles con MagSafe`;
    opt.onclick = (e) => {
      e.preventDefault();
      state.magsafeOnly = !state.magsafeOnly;
      renderList();
    };
    el.filterMagsafe.appendChild(opt);
  }

  // Filtro "Tamaño" (Baterías portátiles): eje aparte de la capacidad, que
  // ya se navega como subcategoría (Hasta 10,000 mAh / etc.) -- un power
  // bank puede ser chico en mAh pero seguir siendo un ladrillo grande, o
  // al revés, así que se ofrecen ambos por separado.
  function renderFilterSize() {
    const relevant = state.category === "Baterías portátiles";
    el.filterSizeGroup.classList.toggle("hidden", !relevant);
    if (!relevant) {
      state.sizeFilter = "all";
      return;
    }
    el.filterSize.innerHTML = "";
    SIZE_FILTERS.forEach((s) => {
      const opt = document.createElement("label");
      const isActive = state.sizeFilter === s.id;
      opt.className = "filter-option" + (isActive ? " active" : "");
      opt.innerHTML = `<input type="radio" name="fsize" ${isActive ? "checked" : ""}> ${s.label}`;
      opt.onclick = () => { state.sizeFilter = s.id; renderList(); };
      el.filterSize.appendChild(opt);
    });
  }

  // ---------- Vista: Favoritos ----------

  function renderFavorites() {
    setActiveView("favorites");
    renderCatNav();
    const favIds = getFavorites();
    const products = state.data.products.filter((p) => favIds.includes(p.id));
    renderProductListInto(el.favoritesList, products, {
      emptyText: "Aún no tienes favoritos. Toca el corazón en cualquier producto para guardarlo aquí.",
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
  const CATEGORY_ICON_FALLBACK = {
    "Compras generales": "shopping-bag",
    "Belleza": "sparkle",
    "Viajes": "plane",
    "Educación": "graduation-cap",
    "Software e IA": "robot",
    "Hosting y dominios": "server",
    "Otros": "box",
    "Salud y bienestar": "leaf",
  };

  function brandCategories() {
    const list = state.brandsData.brands.map((b) => b.category);
    return [...new Set(list)].sort();
  }

  function categoryCardIconHtml(cat) {
    const photo = CATEGORY_ICONS[cat];
    if (photo) return `<img src="${photo}" alt="" loading="lazy">`;
    return icon(CATEGORY_ICON_FALLBACK[cat] || "tag");
  }

  function renderBrandCategoryFilter() {
    el.brandCategoryFilter.innerHTML = "";
    const all = state.brandsData.brands;

    const allCard = document.createElement("button");
    allCard.type = "button";
    allCard.className = "category-card" + (!state.brandCategory ? " active" : "");
    allCard.innerHTML = `
      <span class="category-card-icon">${icon("shopping-bag")}</span>
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
    const sub = subcategoryById(product.category, product.subcategory);
    const subCrumb = sub
      ? ` &gt; <a href="#/list" id="breadcrumbSub">${sub.name}</a>`
      : "";
    el.detailBreadcrumb.innerHTML =
      `<a href="#/">Inicio</a> &gt; <a href="#/list" id="breadcrumbCat">${cat.name}</a>${subCrumb} &gt; ${product.name}`;
    document.getElementById("breadcrumbCat").onclick = (e) => {
      e.preventDefault();
      goList({ category: product.category, subcategory: null, query: "" });
    };
    if (sub) {
      document.getElementById("breadcrumbSub").onclick = (e) => {
        e.preventDefault();
        goList({ category: product.category, subcategory: product.subcategory, query: "" });
      };
    }

    renderProductMedia(el.detailIcon, product, "detail");
    el.detailBrand.textContent = product.brand;
    el.detailName.innerHTML = `${htmlEscapeAttr(product.name)}${conditionBadge(product)}${usageBadge(product)}`;
    el.detailFavBtn.innerHTML = favIconHtml(product.id);
    bindFavToggle(el.detailFavBtn, product.id, () => renderDetail(product.id));

    const { avg, count } = aggregateRating(product);
    el.detailRating.innerHTML =
      count > 0
        ? `${starsHtml(avg)} ${avg.toFixed(1)} <span class="rc">(${plural(count, "calificación", "calificaciones")})</span>`
        : `<span class="rc">Sin calificaciones todavía</span>`;
    el.detailColors.innerHTML = detailColorSwatchHtml(product);
    const discountPct = bestDiscountPct(product);
    const savings = bestSavingsAmount(product);
    el.detailFromPrice.innerHTML = `
      ${offerCount(product) > 1 ? "Desde " : ""}<strong>${money(minPrice(product))}</strong>${discountPct ? `<span class="discount-badge">-${discountPct}%</span>` : ""} en ${plural(offerCount(product), "tienda", "tiendas")}
      ${savings ? `<span class="save-amount">Ahorras ${money(savings)}</span>` : ""}
      ${cheapestOfferShippingEstimated(product) ? `<span class="shipping-estimate-note">${icon("alert-triangle")} incluye envío estimado (ver tabla de abajo)</span>` : ""}
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
  function renderOfferRows(tbody, rows, bestPrice, fastestDays, recommendedStoreId, productId) {
    tbody.innerHTML = "";
    rows.forEach((r) => {
      const tr = document.createElement("tr");
      // r puede venir de una API en vivo (fetchLiveOffer) donde shippingFee,
      // points y rating pueden faltar (null/undefined): nunca deben tronar el
      // render, solo mostrarse como "—" cuando no hay dato.
      //
      // Ninguna tienda del catálogo tiene todavía un shippingFee numérico
      // real (viene siempre null de los feeds de origen), y las 11 marcas
      // que sí tienen productos son todas de envío internacional directo
      // (hubRegion null) -- así que antes la columna "Envío" salía en blanco
      // ("—") en el 100% de las filas del sitio entero, sin excepción. Se
      // muestra "Envío internacional" en la columna (dato honesto que sí se
      // conoce: la tienda no tiene centro de distribución en México) en vez
      // de dejarla vacía; el costo exacto sigue sin inventarse.
      //
      // Además, 6 de esas 11 tiendas publican un umbral fijo de envío
      // gratis en USD en su propia página de envíos (investigado por
      // tienda, no inventado) -- como cada oferta ya trae su precio real en
      // priceOriginal, se puede comparar contra ese umbral y afirmar "Envío
      // gratis" con la misma base que si viniera del feed. Las otras 5 no
      // publican un umbral numérico único y consistente, así que en su
      // lugar llevan una nota informativa sobre su política real de envío.
      const threshold = r.store.freeShippingThresholdUSD;
      const priceUSD = r.priceOriginal && r.priceOriginal.currency === "USD" ? r.priceOriginal.amount : null;
      const qualifiesFreeShipping = threshold != null && priceUSD != null && priceUSD >= threshold;
      const intlTooltip = threshold != null
        ? `Envío gratis en compras mayores a $${threshold} USD según ${r.store.name}; este producto ($${priceUSD} USD) no alcanza el mínimo.`
        : r.store.shippingNote || `${r.store.name} no tiene centro de distribución en México; el costo de envío se cotiza en su sitio.`;
      const shippingHtml =
        r.shippingFee === 0 ? '<span class="ship-badge">Envío gratis</span>'
        : r.shippingFee != null ? money(r.shippingFee)
        : qualifiesFreeShipping
        ? `<span class="ship-badge" title="${htmlEscapeAttr(`Según la política pública de ${r.store.name}: envío gratis en compras de $${threshold}+ USD, y este producto ($${priceUSD} USD) sí alcanza el mínimo.`)}">Envío gratis</span>`
        : r.shipEstimateFee != null
        ? `${money(r.shipEstimateFee)} <span class="est-badge" title="${htmlEscapeAttr(`Referencia aproximada, no una cotización real de paquetería. ${intlTooltip}`)}">${icon("alert-triangle")} estimado</span>`
        : !r.store.hubRegion
        ? `<span class="ship-badge ship-badge-intl" title="${htmlEscapeAttr(intlTooltip)}">${icon("globe")} Envío internacional</span>`
        : "—";
      // Texto corto de envío para mostrar junto a la entrega, en el momento
      // en que el usuario elige su municipio en el mapa (no solo en la
      // columna aparte). El costo ya viene ajustado por distancia/zona
      // (ver estimateShippingFee) cuando hay una región seleccionada.
      const shippingShort = r.shippingFee === 0 ? "envío gratis"
        : r.shippingFee != null ? `envío ${money(r.shippingFee)}`
        : r.shipEstimateFee != null ? `envío ${money(r.shipEstimateFee)} (estimado)`
        : null;
      let deliveryHtml = "";
      if (r.days !== null) {
        const d = deliveryLabel(r.days);
        // La entrega y el envío por municipio son siempre nuestra propia
        // estimación por distancia (no hay ninguna fuente en vivo conectada
        // todavía, a diferencia del precio) — se marca igual que los
        // precios "de referencia", para no dar a entender que es un dato
        // confirmado con la tienda.
        deliveryHtml = `<div class="delivery-sub ${d.cls}">${d.text}${r.days === fastestDays ? '<span class="best-tag">MÁS RÁPIDO</span>' : ""}${shippingShort ? ` · ${shippingShort}` : ""}<span class="est-badge" title="Estimado por distancia, no confirmado con la tienda">${icon("alert-triangle")} estimado</span></div>`;
      } else if (r.store.typicalShippingDays) {
        // Mismo hueco que el de "Envío": sin hubRegion nunca se calcula un
        // estimado por distancia, así que esta celda se quedaba vacía en el
        // 100% de las filas del sitio. Se usa el rango de días típico
        // publicado en la página de envíos de cada tienda (investigado por
        // tienda, no inventado) en vez de dejarla en blanco.
        const [lo, hi] = r.store.typicalShippingDays;
        deliveryHtml = `<div class="delivery-sub">Entrega en ${lo}–${hi} días${shippingShort ? ` · ${shippingShort}` : ""}<span class="est-badge" title="Rango típico publicado por la tienda para envío internacional, no una estimación por distancia ni un dato confirmado por pedido">${icon("alert-triangle")} estimado</span></div>`;
      }
      const stockInfo = STOCK_INFO[r.stock] || null;
      // r.price/r.listPrice ya vienen ajustados por displayPrice()/
      // displayListPrice() en renderOfferTable() (o sin ajustar si el
      // toggle "Incluir envío" está apagado, que es lo mismo que antes).
      let discountHtml = "";
      if (r.listPrice && r.listPrice > r.price) {
        const pct = Math.round((1 - r.price / r.listPrice) * 100);
        // Se muestra el % junto con el monto ahorrado en pesos: el mismo
        // descuento "se siente" distinto según se enmarque en porcentaje o
        // en dinero real (efecto de encuadre), así que se dan los dos.
        discountHtml = `<span class="list-price">${money(r.listPrice)}</span><span class="discount-badge">-${pct}%</span><span class="save-amount">Ahorras ${money(r.listPrice - r.price)}</span>`;
      }
      // Con "Incluir envío" activo, el precio de arriba ya suma el envío
      // -- pero cuando ese monto es un ESTIMADO y no un dato confirmado
      // (ver shippingIsEstimated()), se avisa para que no se lea como el
      // costo real exacto.
      const shipEstimateNote = r.shipEstimated
        ? `<span class="shipping-estimate-note">${icon("alert-triangle")} incluye envío estimado</span>`
        : "";
      const pointsHtml = r.points == null ? "—" : `${r.points}%`;
      const ratingHtml = r.rating == null ? "—" : `${starsHtml(r.rating)} <span class="rc">${r.rating.toFixed(1)}</span>`;
      // "Recomendado" es una etiqueta aparte de "MÁS BARATO": no repite la
      // misma fila (renderOfferTable ya evita eso), y su criterio se explica
      // en el tooltip para que se lea como una sugerencia transparente y no
      // como un sello arbitrario.
      const isRecommended = r.storeId === recommendedStoreId;
      // Cuando el feed de origen traía la misma variante en otros
      // colores/tallas, se guardó como r.variants en vez de crear una
      // ficha de producto aparte por cada una (evita inflar el catálogo
      // con "el mismo mueble en 6 acabados"). Se muestran como pastillas
      // clicables junto al nombre de la tienda para que sea obvio de un
      // vistazo que hay más opciones, sin abrir la tabla completa.
      // Cada pastilla lleva su propia foto en miniatura (como el selector de
      // color de Kakaku.com) para que la diferencia entre variantes se vea
      // de un vistazo, no solo se lea en texto.
      const variantsHtml = r.variants && r.variants.length
        ? `<div class="variant-pills" title="También disponible en otras variantes">
            <span class="variant-pills-label">${icon("palette")} ${r.variants.length + 1} variantes:</span>
            ${[{ label: "Esta", url: r.url, photo: r.photo }, ...r.variants].map(
              (v, i) => `<button class="variant-pill${i === 0 ? " active" : ""}" data-url="${htmlEscapeAttr(v.url)}">${v.photo ? `<img src="${htmlEscapeAttr(v.photo)}" alt="" loading="lazy">` : ""}<span>${htmlEscapeAttr(v.label)}</span></button>`
            ).join("")}
          </div>`
        : "";
      // Alibaba.com es una plataforma mayorista, a diferencia de las demás
      // tiendas del catálogo (que sí son de venta al menudeo): buena parte
      // de sus publicaciones tienen un pedido mínimo (MOQ) -- en una
      // revisión real del catálogo, ~39% de los productos de Alibaba traían
      // "wholesale"/"bulk"/"OEM"/"private label" directo en el título, y
      // es casi seguro que el MOQ real alcance a más (muchas publicaciones
      // no lo dicen en el título, solo en la página del producto). Se avisa
      // en todas las ofertas de Alibaba, no solo en esa fracción detectable
      // por palabra clave.
      const wholesaleHtml = r.storeId === "alibaba"
        ? `<span class="wholesale-badge" title="Alibaba es una plataforma mayorista: este producto puede tener un pedido mínimo (MOQ) mayor a 1 unidad. Verifica la cantidad mínima en la página del producto antes de comprar.">${icon("alert-triangle")} Posible pedido mínimo</span>`
        : "";
      tr.innerHTML = `
        <td>
          <span class="store-badge">
            ${storeDotHtml(r.store)}
            ${r.store.name}${r.colorLabel ? ` <span class="store-color-label">— ${htmlEscapeAttr(r.colorLabel)}</span>` : ""}
          </span>
          ${wholesaleHtml}
          ${variantsHtml}
        </td>
        <td class="price-cell">
          <div>${discountHtml}</div>
          <div class="price-line">
            ${money(r.price)}${r.price === bestPrice ? '<span class="best-tag">MÁS BARATO</span>' : ""}${isRecommended ? `<span class="best-tag recommended-tag" title="Mejor combinación de precio, calificación y disponibilidad">${icon("trophy")} RECOMENDADO</span>` : ""}
          </div>
          ${shipEstimateNote}
          ${deliveryHtml}
        </td>
        <td>${shippingHtml}</td>
        <td>${stockInfo ? `<span class="stock-badge ${stockInfo.cls}">${stockInfo.text}</span>` : "—"}</td>
        <td>${pointsHtml}</td>
        <td class="stars-cell">${ratingHtml}</td>
        <td>
          <button class="buy-btn">Ver oferta</button>
          <div class="buy-trust">${icon("lock")} Compra en el sitio real de la tienda</div>
        </td>
      `;
      tr.querySelector(".buy-btn").onclick = () => { trackStoreClick(productId); window.open(r.url, "_blank"); };
      tr.querySelectorAll(".variant-pill").forEach((btn) => {
        btn.onclick = (e) => {
          e.stopPropagation();
          tr.querySelectorAll(".variant-pill").forEach((b) => b.classList.remove("active"));
          btn.classList.add("active");
          trackStoreClick(productId);
          window.open(btn.dataset.url, "_blank");
        };
      });
      tbody.appendChild(tr);
    });
  }

  function renderOfferTable(product) {
    // Un producto fusionado por color (colorVariants, ver
    // merge_color_variants.py) tiene una sola oferta guardada en
    // product.offers -- la del color más barato -- pero "N tiendas" en la
    // cabecera ya cuenta cada color como una opción aparte (ver
    // offerCount()). La tabla de comparación tiene que mostrar esa misma
    // cantidad de filas o el resumen de arriba no cuadra con el detalle de
    // abajo: se arma una fila por cada color/condición, reusando los demás
    // campos (tienda, puntos, calificación, stock) de la oferta base, que
    // son iguales para todos los colores.
    const baseOffers = product.colorVariants && product.colorVariants.length > 1
      ? product.colorVariants.map((v) => ({
          ...product.offers[0],
          price: v.price,
          url: v.url,
          photo: v.photo,
          listPrice: null,
          colorLabel: v.color ? `${v.color}${v.condition === "refurbished" ? " (Reacondicionado)" : ""}` : null,
        }))
      : product.offers;
    let rows = baseOffers.map((o) => {
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
      // price/listPrice se ajustan acá por displayPrice()/displayListPrice()
      // (toggle global "Incluir envío" en el precio mostrado); shippingFee
      // arriba es un ajuste aparte, solo para la columna "Envío" y la
      // fecha de entrega estimada por municipio -- no son lo mismo.
      return {
        ...o, store, days, shippingFee,
        price: displayPrice(o),
        listPrice: displayListPrice(o),
        shipEstimated: shippingIsEstimated(o),
        // Monto de referencia para la columna "Envío" cuando no hay dato
        // confirmado -- se muestra siempre (no solo con el toggle activo),
        // marcado como estimado, en vez de solo el badge "🌍 Envío
        // internacional" sin ningún monto.
        shipEstimateFee: shippingFeeInfo(o).estimated ? shippingFeeInfo(o).fee : null,
      };
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

    renderOfferRows(el.offerRowsVerified, verifiedRows, bestPrice, fastestDays, recommendedStoreId, product.id);
    renderOfferRows(el.offerRowsReference, referenceRows, bestPrice, fastestDays, recommendedStoreId, product.id);
    // Hoy ninguna tienda tiene API en vivo conectada, así que el grupo
    // "verificados" saldría vacío en el 100% de las fichas: una tabla con
    // sus 6 encabezados y ni una fila se lee como si el sitio estuviera
    // roto. Se esconde entero mientras no haya nada que mostrar, y vuelve
    // solo cuando alguna tienda sí traiga precio en vivo.
    el.offerGroupVerified.classList.toggle("hidden", verifiedRows.length === 0);
  }

  // ---------- Mapa de entrega (modal) ----------
  // Leaflet se carga de forma perezosa (recién al abrir el mapa) para no
  // bloquear la carga inicial de la página con un <script> externo síncrono.
  let leafletLoadPromise = null;
  function ensureLeafletLoaded() {
    if (window.L) return Promise.resolve();
    if (leafletLoadPromise) return leafletLoadPromise;
    leafletLoadPromise = new Promise((resolve, reject) => {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
      document.head.appendChild(link);
      const script = document.createElement("script");
      script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
      script.onload = () => resolve();
      script.onerror = () => reject(new Error("No se pudo cargar el mapa."));
      document.head.appendChild(script);
    });
    return leafletLoadPromise;
  }

  function openMapModal() {
    if (!state.selectedMetro) {
      state.selectedMetro = state.data.metros[0].id;
    }
    renderMetroTabs();
    renderRegionChips();
    el.mapModal.classList.remove("hidden");
    ensureLeafletLoaded()
      .then(() => initOrUpdateMap())
      .catch(() => closeMapModal());
  }

  function closeMapModal() {
    el.mapModal.classList.add("hidden");
  }

  function renderMetroTabs() {
    el.metroTabs.innerHTML = "";
    let activeTab = null;
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
      if (m.id === state.selectedMetro) activeTab = tab;
      el.metroTabs.appendChild(tab);
    });
    // Con 32 estados la barra es más ancha que la pantalla: al elegir uno
    // que quedó fuera de vista (o al abrir el modal) la pestaña activa se
    // trae a la vista en vez de dejarla escondida a la izquierda o derecha.
    if (activeTab) activeTab.scrollIntoView({ block: "nearest", inline: "center" });
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

  // ---------- Autocompletado de categorías en el buscador ----------
  //
  // No busca productos (eso lo sigue haciendo Enter/el botón, como
  // siempre): sugiere categorías y subcategorías por nombre a medida que
  // se escribe, tolerando texto parcial ("aud" -> Audífonos) y errores de
  // tipeo ("audifonso") vía distancia de Levenshtein, para que alguien que
  // solo tiene una idea aproximada de la categoría no tenga que escribirla
  // entera ni bien para encontrarla.
  let searchSuggestionItems = [];
  let searchActiveIndex = -1;

  function normalizeSearchText(s) {
    return (s || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .trim();
  }

  // Distancia de edición estándar (inserción/borrado/sustitución) --
  // ambos textos de acá son cortos (nombres de categoría), así que la
  // tabla DP es trivial en tamaño y no hace falta optimizarla.
  function levenshteinDistance(a, b) {
    const m = a.length;
    const n = b.length;
    if (m === 0) return n;
    if (n === 0) return m;
    const row = new Array(n + 1);
    for (let j = 0; j <= n; j++) row[j] = j;
    for (let i = 1; i <= m; i++) {
      let prevDiag = row[0];
      row[0] = i;
      for (let j = 1; j <= n; j++) {
        const tmp = row[j];
        row[j] = Math.min(
          row[j] + 1,
          row[j - 1] + 1,
          prevDiag + (a[i - 1] === b[j - 1] ? 0 : 1)
        );
        prevDiag = tmp;
      }
    }
    return row[n];
  }

  // Menor puntaje = mejor coincidencia; null = ni siquiera tolerando
  // errores de tipeo se parece lo suficiente como para sugerirlo.
  function searchMatchScore(query, target) {
    const q = normalizeSearchText(query);
    const t = normalizeSearchText(target);
    if (!q) return null;
    if (t === q) return 0;
    if (t.startsWith(q)) return 1;
    const words = t.split(/\s+/);
    if (words.some((w) => w.startsWith(q))) return 2;
    if (t.includes(q)) return 3;
    let best = Infinity;
    for (const candidate of [t, ...words]) {
      const d = levenshteinDistance(q, candidate);
      if (d < best) best = d;
    }
    // Tolerancia proporcional al largo de lo escrito: con "tv" (2
    // caracteres) un solo error ya cambia demasiado la palabra, pero con
    // "audifonos" (9) sobran 2-3 errores para seguir siendo reconocible.
    const tolerance = Math.max(1, Math.floor(q.length * 0.34));
    return best <= tolerance ? 4 + best : null;
  }

  function buildSearchSuggestions(query) {
    if (!state.data || !normalizeSearchText(query)) return [];
    const pool = [];
    state.data.categories.forEach((cat) => {
      pool.push({ matchText: cat.name, label: cat.name, catLabel: null, catId: cat.id, subId: null, icon: cat.icon });
      (cat.subcategories || []).forEach((sub) => {
        pool.push({
          matchText: sub.name,
          label: sub.name,
          catLabel: cat.name,
          catId: cat.id,
          subId: sub.id,
          icon: sub.icon,
        });
      });
    });
    const scored = pool
      .map((item) => ({ ...item, score: searchMatchScore(query, item.matchText) }))
      .filter((item) => item.score !== null)
      .sort((a, b) => a.score - b.score || a.matchText.length - b.matchText.length);
    const seen = new Set();
    const out = [];
    for (const item of scored) {
      const key = `${item.catId}|${item.subId || ""}`;
      if (seen.has(key)) continue;
      seen.add(key);
      out.push(item);
      if (out.length >= 8) break;
    }
    return out;
  }

  function hideSearchSuggestions() {
    searchSuggestionItems = [];
    searchActiveIndex = -1;
    el.searchSuggestions.innerHTML = "";
    el.searchSuggestions.classList.add("hidden");
  }

  function selectSearchSuggestion(item) {
    el.searchInput.value = "";
    hideSearchSuggestions();
    goCategoryRanking(item.catId, item.subId);
  }

  function updateSearchActiveHighlight() {
    el.searchSuggestions.querySelectorAll(".search-suggestion-item").forEach((node, i) => {
      node.classList.toggle("active", i === searchActiveIndex);
    });
  }

  function renderSearchSuggestions(items) {
    searchSuggestionItems = items;
    searchActiveIndex = -1;
    if (!items.length) {
      el.searchSuggestions.innerHTML = "";
      el.searchSuggestions.classList.add("hidden");
      return;
    }
    el.searchSuggestions.innerHTML = items
      .map(
        (it, i) => `
      <div class="search-suggestion-item" data-index="${i}">
        ${icon(it.icon, "search-suggestion-icon")}
        <span>${htmlEscapeAttr(it.label)}${it.catLabel ? ` <span class="search-suggestion-cat">— ${htmlEscapeAttr(it.catLabel)}</span>` : ""}</span>
      </div>
    `
      )
      .join("");
    el.searchSuggestions.classList.remove("hidden");
    el.searchSuggestions.querySelectorAll(".search-suggestion-item").forEach((node) => {
      // mousedown (no click): dispara antes que el blur del input, que si
      // no se adelantara escondería el desplegable antes de registrar el clic.
      node.addEventListener("mousedown", (e) => {
        e.preventDefault();
        selectSearchSuggestion(items[Number(node.dataset.index)]);
      });
    });
  }

  // ---------- Eventos globales ----------

  function bindEvents() {
    el.searchInput.addEventListener("input", () => {
      renderSearchSuggestions(buildSearchSuggestions(el.searchInput.value));
    });
    el.searchInput.addEventListener("focus", () => {
      if (el.searchInput.value.trim()) renderSearchSuggestions(buildSearchSuggestions(el.searchInput.value));
    });
    el.searchInput.addEventListener("blur", () => setTimeout(hideSearchSuggestions, 120));
    el.searchInput.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown" && searchSuggestionItems.length) {
        e.preventDefault();
        searchActiveIndex = Math.min(searchActiveIndex + 1, searchSuggestionItems.length - 1);
        updateSearchActiveHighlight();
        return;
      }
      if (e.key === "ArrowUp" && searchSuggestionItems.length) {
        e.preventDefault();
        searchActiveIndex = Math.max(searchActiveIndex - 1, -1);
        updateSearchActiveHighlight();
        return;
      }
      if (e.key === "Escape") {
        hideSearchSuggestions();
        return;
      }
      if (e.key === "Enter") {
        if (searchActiveIndex >= 0 && searchSuggestionItems[searchActiveIndex]) {
          e.preventDefault();
          selectSearchSuggestion(searchSuggestionItems[searchActiveIndex]);
          return;
        }
        hideSearchSuggestions();
        goList({ query: el.searchInput.value.trim(), category: null });
      }
    });
    el.searchBtn.addEventListener("click", () => {
      hideSearchSuggestions();
      goList({ query: el.searchInput.value.trim(), category: null });
    });

    // Toggle global "Incluir envío": afecta el precio mostrado en toda la
    // app (inicio, lista, detalle), así que en vez de renderList() se
    // vuelve a pintar lo que sea que esté visible ahora mismo.
    el.shipToggle.checked = state.includeShipping;
    el.shipToggleLabel.classList.toggle("active", state.includeShipping);
    el.shipToggle.addEventListener("change", () => {
      state.includeShipping = el.shipToggle.checked;
      el.shipToggleLabel.classList.toggle("active", state.includeShipping);
      writeLS(LS_KEYS.includeShipping, state.includeShipping);
      rerenderCurrentView();
    });

    // Slider de precio de dos manijas + inputs numéricos. "input" solo
    // actualiza el dibujo (barra de relleno + campo numérico espejo) sin
    // volver a filtrar 6,000+ productos en cada pixel de arrastre; el
    // filtro real (renderList) se dispara en "change" (al soltar la
    // manija) igual que los campos numéricos al perder el foco/Enter.
    el.priceRangeMin.addEventListener("input", () => {
      let vMin = Number(el.priceRangeMin.value);
      const vMax = Number(el.priceRangeMax.value);
      if (vMin > vMax) { vMin = vMax; el.priceRangeMin.value = vMin; }
      el.priceNumMin.value = vMin;
      updatePriceRangeFill(Number(el.priceRangeMin.min), Number(el.priceRangeMin.max), vMin, vMax);
    });
    el.priceRangeMin.addEventListener("change", () => {
      commitPriceRange(Number(el.priceRangeMin.value), Number(el.priceRangeMax.value));
    });
    el.priceRangeMax.addEventListener("input", () => {
      const vMin = Number(el.priceRangeMin.value);
      let vMax = Number(el.priceRangeMax.value);
      if (vMax < vMin) { vMax = vMin; el.priceRangeMax.value = vMax; }
      el.priceNumMax.value = vMax;
      updatePriceRangeFill(Number(el.priceRangeMin.min), Number(el.priceRangeMin.max), vMin, vMax);
    });
    el.priceRangeMax.addEventListener("change", () => {
      commitPriceRange(Number(el.priceRangeMin.value), Number(el.priceRangeMax.value));
    });
    el.priceNumMin.addEventListener("change", () => {
      const boundMin = Number(el.priceRangeMin.min);
      const boundMax = Number(el.priceRangeMin.max);
      const raw = el.priceNumMin.value.trim();
      let v = raw === "" ? boundMin : Math.max(0, Number(raw));
      if (Number.isNaN(v)) v = boundMin;
      const vMax = state.priceMax == null ? boundMax : state.priceMax;
      commitPriceRange(Math.min(v, vMax), vMax);
    });
    el.priceNumMax.addEventListener("change", () => {
      const boundMin = Number(el.priceRangeMin.min);
      const boundMax = Number(el.priceRangeMin.max);
      const raw = el.priceNumMax.value.trim();
      let v = raw === "" ? boundMax : Math.max(0, Number(raw));
      if (Number.isNaN(v)) v = boundMax;
      const vMin = state.priceMin == null ? boundMin : state.priceMin;
      commitPriceRange(vMin, Math.max(v, vMin));
    });

    // Con tantas categorías la barra ya no cabe en una fila (ver .cats en
    // style.css): arranca colapsada a una línea y este botón la despliega,
    // en vez de dejarla siempre abierta empujando el resto de la página.
    el.catNavToggle.addEventListener("click", () => {
      const expanded = el.catNav.classList.toggle("expanded");
      el.catNavToggle.setAttribute("aria-expanded", String(expanded));
      el.catNavToggleLabel.textContent = expanded ? "Menos categorías" : "Más categorías";
    });

    el.sortSelect.addEventListener("change", (e) => {
      state.sort = e.target.value;
      renderList();
    });

    // Marca y Categoría se pueden plegar: son las listas más largas del
    // panel de filtros (categorías con sus subcategorías, o decenas de
    // marcas), así que quedan colapsables para no empujar Precio/
    // Calificación/Condición fuera de la vista. El contenido interno
    // (filterCategory/filterBrand) se re-genera en cada renderList(), pero
    // el <h3> y el .filter-group que lo envuelven son estáticos del HTML,
    // así que este listener se registra una sola vez acá.
    // Filtra la lista de checkboxes de Marca en vivo, sin disparar
    // renderList() completo (no cambia el catálogo, solo qué checkboxes
    // se muestran), así que el input no pierde el foco al escribir.
    el.filterBrandSearch.addEventListener("input", () => renderFilterBrand());

    document.querySelectorAll(".filter-group-collapsible > h3").forEach((h3) => {
      h3.addEventListener("click", () => {
        h3.closest(".filter-group").classList.toggle("collapsed");
      });
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

    // Botón "volver arriba": aparece recién después de bajar un poco (no
    // tiene sentido mostrarlo ya arriba del todo) y queda fijo en la misma
    // esquina de la pantalla (position:fixed en CSS) sin importar cuánto
    // se baje, en vez de moverse con el contenido de la página.
    const BACK_TO_TOP_THRESHOLD = 400;
    window.addEventListener(
      "scroll",
      () => {
        el.backToTopBtn.classList.toggle("is-hidden", window.scrollY < BACK_TO_TOP_THRESHOLD);
      },
      { passive: true }
    );
    el.backToTopBtn.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
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
