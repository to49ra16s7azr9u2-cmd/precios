(() => {
  "use strict";

  const state = {
    data: null,
    selectedMetro: null,
    selectedRegion: null, // null hasta que el usuario elige un municipio en el mapa
    query: "",
    category: null,
  };

  const el = {
    grid: document.getElementById("productGrid"),
    listTitle: document.getElementById("listTitle"),
    catNav: document.getElementById("catNav"),
    searchInput: document.getElementById("searchInput"),
    searchBtn: document.getElementById("searchBtn"),
    viewList: document.getElementById("viewList"),
    viewDetail: document.getElementById("viewDetail"),
    backBtn: document.getElementById("backBtn"),
    detailIcon: document.getElementById("detailIcon"),
    detailName: document.getElementById("detailName"),
    detailCat: document.getElementById("detailCat"),
    locationBtn: document.getElementById("locationBtn"),
    locationBtnLabel: document.getElementById("locationBtnLabel"),
    mapModal: document.getElementById("mapModal"),
    mapModalClose: document.getElementById("mapModalClose"),
    metroTabs: document.getElementById("metroTabs"),
    regionChips: document.getElementById("regionChips"),
    offerRows: document.getElementById("offerRows"),
  };

  let map = null;
  let regionMarkers = {};

  function money(n) {
    return n.toLocaleString("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 0 });
  }

  function storeById(id) {
    return state.data.stores.find((s) => s.id === id);
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

  function renderCategories() {
    const cats = [...new Set(state.data.products.map((p) => p.category))];
    el.catNav.innerHTML = "";
    const allSpan = document.createElement("span");
    allSpan.textContent = "Todas";
    allSpan.className = state.category === null ? "active" : "";
    allSpan.onclick = () => { state.category = null; renderCategories(); renderGrid(); };
    el.catNav.appendChild(allSpan);
    cats.forEach((c) => {
      const s = document.createElement("span");
      s.textContent = c;
      s.className = state.category === c ? "active" : "";
      s.onclick = () => { state.category = c; renderCategories(); renderGrid(); };
      el.catNav.appendChild(s);
    });
  }

  function filteredProducts() {
    return state.data.products.filter((p) => {
      const matchesQuery = !state.query || p.name.toLowerCase().includes(state.query.toLowerCase());
      const matchesCat = !state.category || p.category === state.category;
      return matchesQuery && matchesCat;
    });
  }

  function renderGrid() {
    const products = filteredProducts();
    el.listTitle.textContent = state.query
      ? `Resultados para "${state.query}" (${products.length})`
      : "Productos populares";
    el.grid.innerHTML = "";
    if (products.length === 0) {
      el.grid.innerHTML = `<p class="muted">No se encontraron productos.</p>`;
      return;
    }
    products.forEach((p) => {
      const card = document.createElement("div");
      card.className = "product-card";
      card.innerHTML = `
        <div class="icon">${p.image}</div>
        <div class="name">${p.name}</div>
        <div class="cat">${p.category}</div>
        <div class="price-row">
          <span class="from">Desde</span>
          <span class="price">${money(minPrice(p))}</span>
        </div>
        <div class="stores-count">${p.offers.length} tiendas comparadas</div>
      `;
      card.onclick = () => showDetail(p.id);
      el.grid.appendChild(card);
    });
  }

  function showList() {
    el.viewDetail.classList.add("hidden");
    el.viewList.classList.remove("hidden");
    location.hash = "#/";
  }

  function showDetail(productId) {
    const product = state.data.products.find((p) => p.id === productId);
    if (!product) return;
    el.viewList.classList.add("hidden");
    el.viewDetail.classList.remove("hidden");
    location.hash = `#/p/${productId}`;

    el.detailIcon.textContent = product.image;
    el.detailName.textContent = product.name;
    el.detailCat.textContent = product.category;

    updateLocationBtn();
    renderOfferTable(product);
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

  function currentProduct() {
    const match = location.hash.match(/#\/p\/(.+)/);
    if (!match) return null;
    return state.data.products.find((p) => p.id === match[1]) || null;
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
        color: "#e0301e",
        weight: 2,
        fillColor: "#ffcc4d",
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
        fillColor: isActive ? "#e0301e" : "#ffcc4d",
        color: isActive ? "#7a1c10" : "#e0301e",
      });
    });
  }

  function deliveryLabel(days) {
    if (days <= 1) return { text: "Entrega mañana", cls: "delivery-fast" };
    return { text: `Entrega en ${days} días`, cls: "" };
  }

  function renderOfferTable(product) {
    const rows = product.offers
      .map((o) => {
        const store = storeById(o.storeId);
        const days = state.selectedRegion
          ? estimateDeliveryDays(store.hubRegion, state.selectedRegion)
          : null;
        return { ...o, store, days };
      })
      .sort((a, b) => a.price - b.price);

    const bestPrice = rows[0].price;
    const fastestDays = state.selectedRegion ? Math.min(...rows.map((r) => r.days)) : null;

    el.offerRows.innerHTML = "";
    rows.forEach((r) => {
      const tr = document.createElement("tr");
      let deliveryHtml = "";
      if (r.days !== null) {
        const d = deliveryLabel(r.days);
        deliveryHtml = `<div class="delivery-sub ${d.cls}">${d.text}${r.days === fastestDays ? '<span class="best-tag">MÁS RÁPIDO</span>' : ""}</div>`;
      }
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
        <td><button class="buy-btn">Ver oferta</button></td>
      `;
      tr.querySelector(".buy-btn").onclick = () => window.open(r.url, "_blank");
      el.offerRows.appendChild(tr);
    });
  }

  function onHashChange() {
    const match = location.hash.match(/#\/p\/(.+)/);
    if (match && state.data) {
      showDetail(match[1]);
    } else if (state.data) {
      el.viewDetail.classList.add("hidden");
      el.viewList.classList.remove("hidden");
      closeMapModal();
    }
  }

  function bindEvents() {
    el.searchInput.addEventListener("input", (e) => {
      state.query = e.target.value.trim();
      renderGrid();
    });
    el.searchBtn.addEventListener("click", () => renderGrid());
    el.backBtn.addEventListener("click", showList);
    el.locationBtn.addEventListener("click", openMapModal);
    el.mapModalClose.addEventListener("click", closeMapModal);
    el.mapModal.addEventListener("click", (e) => {
      if (e.target === el.mapModal) closeMapModal();
    });
    window.addEventListener("hashchange", onHashChange);
  }

  async function main() {
    await loadData();
    renderCategories();
    renderGrid();
    bindEvents();
    onHashChange();

    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("sw.js").catch(() => {});
    }
  }

  main();
})();
