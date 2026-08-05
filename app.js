(() => {
  "use strict";

  const PRICE_RANGES = [
    { id: "all", label: "Todos los precios", min: 0, max: Infinity },
    { id: "u5", label: "Menos de $5,000", min: 0, max: 5000 },
    { id: "5to10", label: "$5,000 – $10,000", min: 5000, max: 10000 },
    { id: "10to15", label: "$10,000 – $15,000", min: 10000, max: 15000 },
    { id: "o15", label: "Más de $15,000", min: 15000, max: Infinity },
  ];

  const state = {
    data: null,
    selectedMetro: null,
    selectedRegion: null, // null hasta que el usuario elige un municipio en el mapa
    query: "",
    category: null, // filtro activo en la vista de lista
    priceRange: "all",
    sort: "relevance",
    offerSort: "price", // 'price' | 'rating' — orden de la tabla de comparación
  };

  const el = {
    catNav: document.getElementById("catNav"),
    searchInput: document.getElementById("searchInput"),
    searchBtn: document.getElementById("searchBtn"),

    viewHome: document.getElementById("viewHome"),
    rankingGrid: document.getElementById("rankingGrid"),

    viewList: document.getElementById("viewList"),
    listBreadcrumb: document.getElementById("listBreadcrumb"),
    listTitle: document.getElementById("listTitle"),
    filterCategory: document.getElementById("filterCategory"),
    filterPrice: document.getElementById("filterPrice"),
    sortSelect: document.getElementById("sortSelect"),
    productList: document.getElementById("productList"),

    viewDetail: document.getElementById("viewDetail"),
    detailBreadcrumb: document.getElementById("detailBreadcrumb"),
    detailIcon: document.getElementById("detailIcon"),
    detailBrand: document.getElementById("detailBrand"),
    detailName: document.getElementById("detailName"),
    detailRating: document.getElementById("detailRating"),
    detailFromPrice: document.getElementById("detailFromPrice"),
    locationBtn: document.getElementById("locationBtn"),
    locationBtnLabel: document.getElementById("locationBtnLabel"),
    sortTabs: document.getElementById("sortTabs"),
    offerRows: document.getElementById("offerRows"),
    specTable: document.getElementById("specTable"),
    reviewCount: document.getElementById("reviewCount"),
    reviewList: document.getElementById("reviewList"),

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
  // logística local (infraDays). No usa datos reales de paquetería.
  function estimateDeliveryDays(hubRegionId, targetRegionId) {
    const hub = regionById(hubRegionId);
    const target = regionById(targetRegionId);
    if (hub.id === target.id) return 1 + target.infraDays;

    const dist = distanceKm(hub, target);
    const sameMetro = hub.metro === target.metro;
    let base;
    if (sameMetro) {
      base = dist < 15 ? 1 : dist < 40 ? 2 : 3;
    } else {
      base = 3 + Math.round(dist / 500);
    }
    return Math.min(base + target.infraDays, 8);
  }

  async function loadData() {
    const res = await fetch("data/data.json");
    state.data = await res.json();
  }

  // ---------- Navegación entre vistas ----------

  function setActiveView(name) {
    el.viewHome.classList.toggle("hidden", name !== "home");
    el.viewList.classList.toggle("hidden", name !== "list");
    el.viewDetail.classList.toggle("hidden", name !== "detail");
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

  function goDetail(productId) {
    navigateTo(`#/p/${productId}`, () => renderDetail(productId));
  }

  function onHashChange() {
    if (!state.data) return;
    const hash = location.hash;
    const detailMatch = hash.match(/#\/p\/(.+)/);
    if (detailMatch) {
      renderDetail(detailMatch[1]);
    } else if (hash === "#/list") {
      renderList();
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
      span.onclick = () => goList({ category: c.id, query: "" });
      el.catNav.appendChild(span);
    });
  }

  // ---------- Vista: Inicio (rankings) ----------

  function renderHome() {
    setActiveView("home");
    renderCatNav();
    el.rankingGrid.innerHTML = "";
    state.data.categories.forEach((cat) => {
      const products = state.data.products
        .filter((p) => p.category === cat.id)
        .slice()
        .sort((a, b) => minPrice(a) - minPrice(b))
        .slice(0, 5);

      const card = document.createElement("div");
      card.className = "ranking-card";
      card.innerHTML = `
        <div class="ranking-card-head">
          <span class="cat-icon">${cat.icon}</span>
          <h2>${cat.name} más buscados</h2>
          <span class="see-all">Ver todos</span>
        </div>
      `;
      card.querySelector(".see-all").onclick = () => goList({ category: cat.id, query: "" });

      products.forEach((p) => {
        const row = document.createElement("div");
        row.className = "ranking-row";
        row.innerHTML = `
          <span class="rank-badge">${products.indexOf(p) + 1}</span>
          <span class="row-icon">${p.image}</span>
          <span class="row-name">${p.name}</span>
          <span class="row-price">${money(minPrice(p))}</span>
        `;
        row.onclick = () => goDetail(p.id);
        card.appendChild(row);
      });
      el.rankingGrid.appendChild(card);
    });
  }

  // ---------- Vista: Lista (búsqueda / categoría) ----------

  function filteredProducts() {
    const range = PRICE_RANGES.find((r) => r.id === state.priceRange) || PRICE_RANGES[0];
    return state.data.products.filter((p) => {
      const matchesQuery = !state.query || p.name.toLowerCase().includes(state.query.toLowerCase());
      const matchesCat = !state.category || p.category === state.category;
      const price = minPrice(p);
      const matchesPrice = price >= range.min && price < range.max;
      return matchesQuery && matchesCat && matchesPrice;
    });
  }

  function sortedProducts(products) {
    const list = products.slice();
    if (state.sort === "price_asc") list.sort((a, b) => minPrice(a) - minPrice(b));
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

    const products = sortedProducts(filteredProducts());
    el.listTitle.textContent = state.query
      ? `Resultados para "${state.query}" (${products.length})`
      : state.category
      ? `${categoryById(state.category).name} (${products.length})`
      : `Todos los productos (${products.length})`;

    el.productList.innerHTML = "";
    if (products.length === 0) {
      el.productList.innerHTML = `<p class="muted">No se encontraron productos.</p>`;
      return;
    }
    products.forEach((p) => {
      const { avg, count } = aggregateRating(p);
      const row = document.createElement("div");
      row.className = "product-row";
      row.innerHTML = `
        <span class="row-icon">${p.image}</span>
        <div class="row-info">
          <div class="row-brand">${p.brand}</div>
          <div class="row-name">${p.name}</div>
          <div class="row-stars">${starsHtml(avg)} <span class="muted">${avg.toFixed(1)} (${count})</span></div>
        </div>
        <div class="row-priceblock">
          <div class="row-from">Desde</div>
          <div class="row-price">${money(minPrice(p))}</div>
          <div class="row-stores">${p.offers.length} tiendas</div>
        </div>
      `;
      row.onclick = () => goDetail(p.id);
      el.productList.appendChild(row);
    });
  }

  function renderFilterCategory() {
    el.filterCategory.innerHTML = "";
    const allOpt = document.createElement("label");
    allOpt.className = "filter-option" + (!state.category ? " active" : "");
    allOpt.innerHTML = `<input type="radio" name="fcat" ${!state.category ? "checked" : ""}> Todas`;
    allOpt.onclick = () => { state.category = null; renderList(); };
    el.filterCategory.appendChild(allOpt);

    state.data.categories.forEach((c) => {
      const opt = document.createElement("label");
      const isActive = state.category === c.id;
      opt.className = "filter-option" + (isActive ? " active" : "");
      opt.innerHTML = `<input type="radio" name="fcat" ${isActive ? "checked" : ""}> ${c.icon} ${c.name}`;
      opt.onclick = () => { state.category = c.id; renderList(); };
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

    el.detailIcon.textContent = product.image;
    el.detailBrand.textContent = product.brand;
    el.detailName.textContent = product.name;

    const { avg, count } = aggregateRating(product);
    el.detailRating.innerHTML = `${starsHtml(avg)} ${avg.toFixed(1)} <span class="rc">(${count} calificaciones)</span>`;
    el.detailFromPrice.innerHTML = `Desde <strong>${money(minPrice(product))}</strong> en ${product.offers.length} tiendas`;

    el.specTable.innerHTML = product.specs
      .map((s) => `<tr><th>${s.label}</th><td>${s.value}</td></tr>`)
      .join("");

    el.reviewCount.textContent = `(${product.reviews.length})`;
    el.reviewList.innerHTML = product.reviews
      .map(
        (r) => `
        <div class="review-item">
          <div class="review-stars">${starsHtml(r.rating)}</div>
          <div class="review-meta">${r.author} · ${r.date}</div>
          <p class="review-comment">${r.comment}</p>
        </div>`
      )
      .join("");

    updateLocationBtn();
    renderSortTabs();
    renderOfferTable(product);
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
      el.locationBtnLabel.textContent = region.name;
      el.locationBtn.classList.add("is-set");
    } else {
      el.locationBtnLabel.textContent = "Comparar tiempos de entrega";
      el.locationBtn.classList.remove("is-set");
    }
  }

  function deliveryLabel(days) {
    if (days <= 1) return { text: "Entrega mañana", cls: "delivery-fast" };
    return { text: `Entrega en ${days} días`, cls: "" };
  }

  function renderOfferTable(product) {
    let rows = product.offers.map((o) => {
      const store = storeById(o.storeId);
      const days = state.selectedRegion
        ? estimateDeliveryDays(store.hubRegion, state.selectedRegion)
        : null;
      return { ...o, store, days };
    });

    if (state.offerSort === "rating") rows.sort((a, b) => b.rating - a.rating);
    else rows.sort((a, b) => a.price - b.price);

    const bestPrice = Math.min(...rows.map((r) => r.price));
    const fastestDays = state.selectedRegion ? Math.min(...rows.map((r) => r.days)) : null;

    el.offerRows.innerHTML = "";
    rows.forEach((r) => {
      const tr = document.createElement("tr");
      let deliveryHtml = "";
      if (r.days !== null) {
        const d = deliveryLabel(r.days);
        deliveryHtml = `<div class="delivery-sub ${d.cls}">${d.text}${r.days === fastestDays ? '<span class="best-tag">MÁS RÁPIDO</span>' : ""}</div>`;
      }
      const shippingText = r.shippingFee === 0 ? "Gratis" : money(r.shippingFee);
      tr.innerHTML = `
        <td>
          <span class="store-badge">
            <span class="store-dot" style="background:${r.store.color}">${r.store.logo}</span>
            ${r.store.name}
          </span>
        </td>
        <td class="price-cell">
          <div class="price-line">${money(r.price)}${r.price === bestPrice ? '<span class="best-tag">MÁS BARATO</span>' : ""}</div>
          ${deliveryHtml}
        </td>
        <td>${shippingText}</td>
        <td>${r.points}%</td>
        <td class="stars-cell">${starsHtml(r.rating)} <span class="rc">${r.rating.toFixed(1)}</span></td>
        <td><button class="buy-btn">Ver oferta</button></td>
      `;
      tr.querySelector(".buy-btn").onclick = () => window.open(r.url, "_blank");
      el.offerRows.appendChild(tr);
    });
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
