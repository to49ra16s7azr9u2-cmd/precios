// Captura de Walmart y Bodega Aurrerá para ComparaMEX: el mismo código sirve
// de content script de la extensión (scripts/extension-walmart/) y de
// marcador (scripts/captura_walmart.html lo carga tal cual). Lee un listado
// de walmart.com.mx o bodegaaurrera.com.mx, acumula productos en
// localStorage, sigue páginas y recorre subdepartamentos.
//
// POR QUÉ ESTO Y NO UN IMPORTADOR EN EL SERVIDOR
// Las dos tiendas sirven sus páginas solo a navegadores de verdad: cualquier
// petición desde un script recibe la página "Verifica tu identidad" (PerimeterX),
// incluso para los términos y condiciones. El único camino que respeta eso es
// el mismo que con Amazon: la persona abre la tienda en su navegador, con su
// sesión, y este código lee lo que la tienda ya le mostró, despacio.
//
// CÓMO LEE LA PÁGINA
// Las dos tiendas corren sobre la misma plataforma (la de walmart.com):
// páginas Next.js con un <script id="__NEXT_DATA__"> que trae los productos
// del listado como JSON. Eso es lo primero que se lee, porque no depende de
// clases CSS que cambian cada semana. Si no está, se leen los datos
// estructurados (JSON-LD) y, en último caso, las tarjetas del DOM.
//
// CÓMO SIGUE PÁGINAS
// Como extensión, NAVEGA: carga la página siguiente en la misma pestaña y
// sigue solo al cargar (el content script corre en cada página). Así cada
// página es una carga normal del navegador, que es lo que la tienda espera.
// Como marcador no hay forma de sobrevivir a la navegación, así que baja las
// páginas con fetch, y si la tienda contesta con la verificación, se detiene
// y recomienda la extensión.
const ComparaMEX = (() => {
  const KEY = "comparamex.captura.walmart.v1";   // productos acumulados (por dominio)
  const COLA = "comparamex.captura.walmart.cola.v1";
  const ESPERA = window.__comparamexEspera || [3000, 6000];  // ms entre páginas, al azar
  const MAX_PAG = 30;        // freno duro por listado (la tienda muestra 40 por página)
  const POCOS = 20;          // una página con menos tarjetas que esto es la última

  const host = location.hostname;
  const TIENDA = /bodegaaurrera\.com\.mx$/.test(host) ? "bodega_aurrera"
               : /walmart\.com\.mx$/.test(host) ? "walmart_mx"
               : host === "localhost" || host === "127.0.0.1" ? (window.__comparamexTienda || "walmart_mx") : null;
  if (!TIENDA) {
    const fuera = () => "ComparaMEX: esto no es walmart.com.mx ni bodegaaurrera.com.mx. Abre un listado de una de esas tiendas y vuelve a ejecutarlo.";
    return { capturar: fuera, resumen: () => null };
  }
  const NOMBRE = TIENDA === "walmart_mx" ? "Walmart" : "Bodega Aurrerá";
  const ARCHIVO = TIENDA === "walmart_mx" ? "walmart" : "bodega-aurrera";
  const EXTENSION = typeof chrome !== "undefined" && !!(chrome.runtime && chrome.runtime.id);

  // ---------- almacén ----------
  const leer = (k, def) => { try { const v = JSON.parse(localStorage.getItem(k) || "null"); return v == null ? def : v; } catch (e) { return def; } };
  const escribir = (k, v) => localStorage.setItem(k, JSON.stringify(v));
  let acumulado = leer(KEY, []);
  if (!Array.isArray(acumulado)) acumulado = [];
  const vistos = new Set(acumulado.map((x) => x.id));
  const estado = Object.assign({ cola: [], hechas: {}, activo: false, motivo: "", prof: 0, latido: 0, paginas: 0,
                                 actual: null, esperada: null }, leer(COLA, {}));
  const guardar = () => { escribir(KEY, acumulado); escribir(COLA, estado); };

  // ---------- util ----------
  const norm = (t) => (t || "").trim().replace(/\s+/g, " ");
  const numero = (v) => { const n = typeof v === "number" ? v : parseFloat(String(v == null ? "" : v).replace(/[^\d.]/g, "")); return isFinite(n) && n > 0 ? n : null; };
  const precioDe = (txt) => { const m = /\$\s?([\d.,]+)/.exec(txt || ""); return m ? numero(m[1].replace(/,/g, "")) : null; };
  const abs = (href, base) => { try { return new URL(href, base || location.href).href; } catch (e) { return null; } };
  const idDe = (u) => { const m = /\/ip\/(?:[^\/?#]+\/)*?(\d{6,})(?:[\/?#]|$)/.exec(u || ""); return m ? m[1] : null; };
  const dormir = (ms) => new Promise((r) => setTimeout(r, ms));
  const azar = () => ESPERA[0] + Math.random() * (ESPERA[1] - ESPERA[0]);
  // Dos URLs son el mismo listado si coinciden ruta, búsqueda y página; los
  // demás parámetros (de tracking, de orden) los pone la tienda al redirigir.
  const clave = (u) => { try { const x = new URL(u); return x.pathname.replace(/\/$/, "") + "|" + (x.searchParams.get("q") || "") + "|" + (x.searchParams.get("page") || "1"); } catch (e) { return u; } };
  const paginaDe = (u) => { try { return parseInt(new URL(u).searchParams.get("page") || "1", 10) || 1; } catch (e) { return 1; } };
  const conPagina = (u, n) => { const x = new URL(u); if (n <= 1) x.searchParams.delete("page"); else x.searchParams.set("page", String(n)); return x.href; };
  const bloqueada = (doc, url) => /\/blocked(\?|$)/.test(url || "") || /Verifica tu identidad|px-captcha/i.test((doc && doc.title) || "") || !!(doc && doc.querySelector && doc.querySelector("#px-captcha"));

  // ---------- leer un listado: 1) __NEXT_DATA__ ----------
  const esProducto = (o) => o && typeof o === "object" && !Array.isArray(o) && typeof o.name === "string" && o.name.length > 3 &&
    (o.canonicalUrl || o.usItemId || o.productPageUrl) && (o.priceInfo || o.price != null || o.offers);
  const productoDe = (o, base) => {
    const pi = o.priceInfo || {};
    const cp = pi.currentPrice || {};
    const price = numero(cp.price) || precioDe(cp.priceString) || numero(pi.linePrice) || precioDe(pi.linePrice) ||
                  numero(o.price) || precioDe(o.price) || numero(o.offers && o.offers.price) || null;
    const was = pi.wasPrice || {};
    const listPrice = numero(was.price) || precioDe(was.priceString) || null;
    const url = abs(o.canonicalUrl || o.productPageUrl || "", base);
    const id = String(o.usItemId || idDe(url) || o.id || "");
    if (!id || !url) return null;
    const ii = o.imageInfo || {};
    const item = { id, title: norm(o.name), price, photo: ii.thumbnailUrl || o.image || o.imageUrl || null, url };
    if (listPrice && price && listPrice > price) item.listPrice = listPrice;
    if (o.brand) item.brand = norm(o.brand);
    const disp = (o.availabilityStatusV2 && o.availabilityStatusV2.value) || o.availabilityStatus;
    if (disp && /out_of_stock|agotado/i.test(String(disp))) item.agotado = true;
    if (o.isSponsoredFlag || o.sponsoredProduct) item.sponsored = true;
    if (o.sellerName) item.seller = norm(o.sellerName);
    return item;
  };
  const buscarEnJSON = (raiz, base) => {
    const out = [], ids = new Set();
    const pila = [[raiz, 0]];
    while (pila.length) {
      const [v, d] = pila.pop();
      if (!v || typeof v !== "object" || d > 30) continue;
      if (Array.isArray(v)) { for (const x of v) pila.push([x, d + 1]); continue; }
      if (esProducto(v) && (!v.__typename || /product/i.test(v.__typename))) {
        const it = productoDe(v, base);
        if (it && !ids.has(it.id)) { ids.add(it.id); out.push(it); }
        continue;
      }
      for (const k in v) if (Object.prototype.hasOwnProperty.call(v, k)) pila.push([v[k], d + 1]);
    }
    return out;
  };
  const desdeNext = (doc, url) => {
    const s = doc.querySelector("script#__NEXT_DATA__");
    if (!s) return [];
    let datos; try { datos = JSON.parse(s.textContent); } catch (e) { return []; }
    // Con el JSON entero se colarían los "recomendados" y los carruseles;
    // si el listado principal está donde siempre, se lee solo ese.
    const pp = datos && datos.props && datos.props.pageProps;
    const id = pp && pp.initialData;
    const stacks = id && id.searchResult && id.searchResult.itemStacks;
    if (Array.isArray(stacks) && stacks.length) {
      const items = [].concat(...stacks.map((st) => (st && st.items) || []));
      const r = buscarEnJSON(items, url);
      if (r.length) return r;
    }
    return buscarEnJSON(datos, url);
  };

  // ---------- 2) JSON-LD ----------
  const desdeJsonLd = (doc, url) => {
    const out = [];
    for (const s of doc.querySelectorAll('script[type="application/ld+json"]')) {
      let j; try { j = JSON.parse(s.textContent); } catch (e) { continue; }
      const nodos = [].concat(j && j["@graph"] ? j["@graph"] : j);
      for (const n of nodos) {
        if (!n) continue;
        const lista = n["@type"] === "ItemList" ? (n.itemListElement || []).map((e) => e.item || e) : (n["@type"] === "Product" ? [n] : []);
        for (const p of lista) {
          if (!p || !p.name) continue;
          const u = abs(p.url || p["@id"] || "", url); const id = idDe(u);
          if (!id) continue;
          const of = Array.isArray(p.offers) ? p.offers[0] : (p.offers || {});
          const item = { id, title: norm(p.name), price: numero(of.price) || numero(of.lowPrice) || null,
                         photo: Array.isArray(p.image) ? p.image[0] : (p.image || null), url: u };
          if (p.brand) item.brand = norm(typeof p.brand === "string" ? p.brand : p.brand.name);
          out.push(item);
        }
      }
    }
    return out;
  };

  // ---------- 3) tarjetas del DOM ----------
  const desdeDOM = (doc, url) => {
    const out = [], vistas = new Set();
    for (const a of doc.querySelectorAll('a[href*="/ip/"]')) {
      // Los enlaces de la navegación, cabecera y pie no son tarjetas.
      if (a.closest("nav, aside, header, footer")) continue;
      const u = abs(a.getAttribute("href"), url); const id = idDe(u);
      if (!id || vistas.has(id)) continue;
      const card = a.closest('[data-item-id], [data-testid*="item" i], [data-testid*="product" i], li, article, [role="group"]') || a.parentElement;
      if (!card) continue;
      const t = card.querySelector('[data-automation-id="product-title"], h2, h3');
      let title = norm(t ? t.textContent : "");
      if (!title) { const img = card.querySelector("img[alt]"); title = norm(img ? img.getAttribute("alt") : ""); }
      if (!title) title = norm(a.textContent);
      if (!title || title.length < 4) continue;
      const pr = card.querySelector('[data-automation-id="product-price"], [itemprop="price"], [class*="price" i]');
      const price = precioDe(pr ? pr.textContent : card.textContent);
      const img = card.querySelector("img[src]");
      vistas.add(id);
      out.push({ id, title, price, photo: img ? abs(img.getAttribute("src"), url) : null, url: u.split("?")[0] });
    }
    return out;
  };

  const deptDe = (doc) => {
    const cands = [
      doc.querySelector('nav[aria-label*="breadcrumb" i] li:last-child, [data-automation-id="breadcrumb"] li:last-child, ol.breadcrumb li:last-child'),
      doc.querySelector("h1"),
    ];
    for (const c of cands) {
      const t = norm(c && c.textContent);
      if (t && t.length < 80 && !/^(resultados|inicio|home)\b/i.test(t)) return t.replace(/^Resultados (de|para) /i, "");
    }
    return norm(doc.title).replace(/\s*[|·-]\s*(Walmart|Bodega Aurrer[aá]).*$/i, "") || null;
  };
  const extraer = (doc, url) => {
    let items = desdeNext(doc, url), via = "next";
    if (!items.length) { items = desdeJsonLd(doc, url); via = "jsonld"; }
    if (!items.length) { items = desdeDOM(doc, url); via = "dom"; }
    const dept = deptDe(doc);
    for (const it of items) { it.store = TIENDA; it.via = via; if (dept) it.dept = dept; }
    // Página siguiente, si el listado la ofrece.
    let sig = null;
    const a = doc.querySelector('a[aria-label="Siguiente página"], a[aria-label="Página siguiente"], a[aria-label="Next Page"], a[data-testid="NextPage"], nav[aria-label*="pagin" i] a[rel="next"], a[rel="next"]');
    if (a && a.getAttribute("href")) sig = abs(a.getAttribute("href"), url);
    // Subdepartamentos: enlaces de la navegación lateral a otros listados.
    const subs = new Set(); const actual = clave(url);
    for (const l of doc.querySelectorAll('aside a[href], nav a[href], [data-testid*="nav" i] a[href], [class*="leftnav" i] a[href], [data-testid="facet"] a[href]')) {
      // El rastro de migas lleva a los departamentos de arriba (más anchos):
      // recorrerlos multiplicaría el trabajo, no lo afinaría.
      if (l.closest('[aria-label*="breadcrumb" i], [data-automation-id="breadcrumb"], .breadcrumb')) continue;
      const h = abs(l.getAttribute("href"), url); if (!h) continue;
      let x; try { x = new URL(h); } catch (e) { continue; }
      if (x.hostname !== location.hostname) continue;
      if (!/^\/(browse|content|cp)\//.test(x.pathname)) continue;
      if (clave(h) === actual) continue;
      subs.add(x.origin + x.pathname);
    }
    return { items, sig, subs: Array.from(subs), n: items.length };
  };

  // ---------- acumular ----------
  const sumar = (items) => {
    let nuevos = 0;
    for (const it of items) {
      if (vistos.has(it.id)) continue;
      vistos.add(it.id); acumulado.push(it); nuevos++;
    }
    return nuevos;
  };

  // ---------- panel ----------
  let panel = null, cuerpo = null, botones = {};
  const boton = (texto, fn) => { const b = document.createElement("button"); b.textContent = texto; b.onclick = fn;
    b.style.cssText = "margin:4px 4px 0 0;padding:6px 10px;border:0;border-radius:6px;background:#0071CE;color:#fff;font:600 13px system-ui,sans-serif;cursor:pointer"; return b; };
  const pintar = (extra) => {
    if (!document.body) return;
    if (!panel || !document.body.contains(panel)) {
      panel = document.createElement("div"); panel.id = "comparamex-panel";
      panel.style.cssText = "position:fixed;z-index:2147483647;bottom:16px;right:16px;width:340px;background:#111;color:#fff;padding:14px 16px;border-radius:12px;font:13px/1.45 system-ui,sans-serif;box-shadow:0 8px 28px rgba(0,0,0,.4);white-space:pre-line";
      cuerpo = document.createElement("div"); panel.appendChild(cuerpo);
      const fila = document.createElement("div"); fila.style.marginTop = "8px"; panel.appendChild(fila);
      botones.sig = boton("Páginas siguientes", () => arrancar([{ url: location.href, prof: 0, sub: false, pedido: true }]));
      botones.rec = boton("Recorrer departamentos", () => {
        const p = parseInt(window.prompt("¿Cuántos niveles de subdepartamentos? (0 = solo este, 1 = sus hijos, 2 = también los nietos)", "1") || "0", 10);
        if (isNaN(p)) return; estado.prof = Math.max(0, Math.min(3, p)); arrancar([{ url: location.href, prof: 0, sub: true, pedido: true }]);
      });
      botones.lista = boton("Lista de URLs", () => {
        const t = window.prompt("Pega URLs de " + NOMBRE + " separadas por espacios (departamentos o búsquedas):", "");
        if (!t) return;
        const urls = t.split(/\s+/).filter((u) => u.indexOf(location.hostname) >= 0);
        estado.prof = 0; arrancar(urls.map((u) => ({ url: u, prof: 0, sub: false, pedido: true })));
      });
      botones.pausa = boton("Pausar", () => { if (estado.activo) pausar(); else if (estado.cola.length || estado.actual) reanudar(); });
      botones.bajar = boton("Descargar JSON", descargar);
      botones.vaciar = boton("Vaciar", () => { if (!window.confirm("¿Borrar los " + acumulado.length + " productos acumulados y la cola?")) return; vaciar(); });
      const x = boton("×", () => panel.remove()); x.style.background = "#444"; x.style.float = "right";
      panel.insertBefore(x, cuerpo);
      for (const k of ["sig", "rec", "lista", "pausa", "bajar", "vaciar"]) fila.appendChild(botones[k]);
      document.body.appendChild(panel);
    }
    botones.pausa.textContent = estado.activo ? "Pausar" : ((estado.cola.length || estado.actual) ? "Reanudar" : "Pausar");
    const sinPrecio = acumulado.filter((x) => x.price == null).length;
    cuerpo.textContent = "ComparaMEX · " + NOMBRE + " · acumulados: " + acumulado.length + " (" + sinPrecio + " sin precio)" +
      "\nCola: " + estado.cola.length + " listados · páginas leídas: " + estado.paginas +
      (estado.activo ? "\n▶ recorriendo…" : (estado.motivo ? "\n⏸ " + estado.motivo : "")) +
      (extra ? "\n" + extra : "");
  };

  const descargar = () => {
    const json = JSON.stringify(acumulado, null, 1);
    window.__comparamexJSON = json;
    const fecha = new Date().toISOString().slice(0, 10);
    const nombre = ARCHIVO + "-" + fecha + "-" + acumulado.length + ".json";
    try {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([json], { type: "application/json" }));
      a.download = nombre;
      document.body.appendChild(a); a.click(); a.remove();
    } catch (e) { /* queda el portapapeles */ }
    try { navigator.clipboard.writeText(json).catch(() => {}); } catch (e) { /* sin API */ }
    if (typeof copy === "function") { try { copy(json); } catch (e) { /* idem */ } }
    pintar("Descargado " + nombre + " (y copiado al portapapeles).");
  };

  // ---------- el recorrido ----------
  const detener = (motivo) => { estado.activo = false; estado.motivo = motivo; estado.esperada = null; guardar(); pintar(); };
  const encolar = (nuevos) => {
    let n_ = 0;
    for (const t of nuevos) {
      const k = clave(t.url);
      if (!t.pedido && estado.hechas[k]) continue;
      estado.hechas[k] = 1; estado.cola.push(t); n_++;
    }
    return n_;
  };
  // La página siguiente: el enlace del listado si lo trae; si no, page=N+1
  // mientras la página venga llena. Una página corta es la última.
  const siguienteDe = (r, url) => {
    if (r.sig) return r.sig;
    if (r.n < POCOS) return null;
    return conPagina(url, paginaDe(url) + 1);
  };
  // Lee la página que se tiene (doc) como parte del recorrido de t. Devuelve
  // la URL que sigue dentro del mismo listado, o null si el listado terminó.
  const leerPagina = (doc, url, t) => {
    const r = extraer(doc, url);
    t.pag = (t.pag || 0) + 1; estado.paginas++; estado.latido = Date.now();
    // La tienda devuelve la última página otra vez cuando se le pide una que
    // no existe: la misma lista de ids dos veces seguidas es el final.
    const firma = r.items.map((i) => i.id).join(",");
    if (firma && firma === t.firmaPrev) { estado.paginas--; return null; }
    t.firmaPrev = firma;
    const nuevos = sumar(r.items);
    if (t.pag === 1 && t.sub && t.prof < estado.prof) encolar(r.subs.map((u) => ({ url: u, prof: t.prof + 1, sub: true })));
    guardar();
    pintar("Ahora: " + ((r.items[0] && r.items[0].dept) || url.slice(0, 60)) + " · pág. " + t.pag + " · " + nuevos + " nuevos");
    if (!r.n || t.pag >= MAX_PAG) return null;
    return siguienteDe(r, url);
  };

  // Modo extensión: navegar. Cada carga de página vuelve a ejecutar este
  // script, que retoma desde estado.actual / estado.esperada.
  const irA = async (url) => { estado.esperada = url; estado.latido = Date.now(); guardar(); await dormir(azar()); if (estado.activo) location.href = url; };
  const pasoNavegando = async () => {
    let t = estado.actual;
    if (!t) {
      if (!estado.cola.length) return detener("Recorrido terminado: " + acumulado.length + " productos. Descarga el JSON.");
      t = estado.cola.shift(); t.pag = 0; t.firmaPrev = ""; estado.actual = t; guardar();
      if (clave(t.url) !== clave(location.href)) return irA(t.url);
    }
    const sig = leerPagina(document, location.href, t);
    if (sig) return irA(sig);
    estado.actual = null; guardar();
    if (!estado.cola.length) return detener("Recorrido terminado: " + acumulado.length + " productos. Descarga el JSON.");
    const t2 = estado.cola.shift(); t2.pag = 0; t2.firmaPrev = ""; estado.actual = t2; guardar();
    return irA(t2.url);
  };
  const retomarAlCargar = () => {
    if (!estado.activo) return;
    if (bloqueada(document, location.href)) return detener(NOMBRE + " pidió verificar tu identidad. Resuélvelo, abre el listado y pulsa Reanudar.");
    if (estado.esperada && clave(estado.esperada) === clave(location.href)) { estado.esperada = null; guardar(); pintar(); pasoNavegando(); return; }
    if (estado.actual && clave(estado.actual.url) === clave(location.href) && !estado.actual.pag) { pintar(); pasoNavegando(); return; }
    // Otra página: el recorrido sigue vivo en otra pestaña, o la persona se
    // fue a otro lado. No se toca; se avisa.
    if (Date.now() - estado.latido > 10 * 60 * 1000) return detener("El recorrido se quedó a medias (la pestaña se cerró o cambió de página). Pulsa Reanudar en un listado.");
    pintar("Hay un recorrido andando (¿en otra pestaña?). Esta página no es la que esperaba.");
  };

  // Modo marcador: bajar con fetch, como con Amazon.
  const bajar = async (url) => {
    for (let intento = 0; intento < 2; intento++) {
      let r;
      try { r = await fetch(url, { credentials: "include" }); } catch (e) { r = null; }
      if (r && r.ok) {
        const html = await r.text();
        const doc = new DOMParser().parseFromString(html, "text/html");
        if (bloqueada(doc, r.url)) return { bloqueada: true };
        return { doc };
      }
      if (r && (r.status === 503 || r.status === 429)) { await dormir(20000); continue; }
      return { error: r ? "HTTP " + r.status : "sin respuesta" };
    }
    return { error: NOMBRE + " no responde" };
  };
  const recorrerConFetch = async (t) => {
    let url = t.url; t.pag = 0; t.firmaPrev = "";
    while (url && estado.activo) {
      let doc;
      if (!t.pag && clave(url) === clave(location.href)) doc = document;
      else {
        const r = await bajar(url);
        if (r.bloqueada) { estado.cola.unshift(t); return detener(NOMBRE + " pide verificar la identidad a las descargas del marcador. Usa la extensión (scripts/extension-walmart/), que navega página por página."); }
        if (r.error) { estado.cola.unshift(t); return detener(NOMBRE + " respondió " + r.error + " en " + url + ". Vuelve a ejecutar el marcador para seguir."); }
        doc = r.doc;
      }
      url = leerPagina(doc, url, t);
      if (url) await dormir(azar());
    }
  };
  const correrConFetch = async () => {
    window.__comparamexCorriendo = true;
    try {
      while (estado.cola.length && estado.activo) {
        const t = estado.cola.shift(); guardar();
        await recorrerConFetch(t);
        if (estado.cola.length && estado.activo) await dormir(azar());
      }
      if (estado.activo) detener("Recorrido terminado: " + acumulado.length + " productos. Descarga el JSON.");
    } catch (e) { detener("Error: " + (e && e.message)); }
    window.__comparamexCorriendo = false;
  };

  const arrancar = (nuevos) => {
    if (window.__comparamexCorriendo) { pintar("Ya hay un recorrido andando en esta pestaña."); return; }
    if (estado.activo && Date.now() - estado.latido < 30000 && !nuevos.length) { pintar("Ya hay un recorrido andando en otra pestaña. Espera a que termine o páusalo allí."); return; }
    // Una tanda nueva (nada pendiente y algo pedido a mano) empieza limpia.
    if (nuevos.length && !estado.cola.length && !estado.actual) estado.hechas = {};
    encolar(nuevos);
    if (!estado.cola.length && !estado.actual) { pintar("No hay nada que recorrer."); return; }
    estado.activo = true; estado.motivo = ""; estado.latido = Date.now(); guardar(); pintar();
    if (EXTENSION) pasoNavegando(); else correrConFetch();
  };
  const pausar = () => { if (estado.activo) { estado.activo = false; estado.motivo = "pausado a mano"; estado.esperada = null; guardar(); pintar(); } };
  const reanudar = () => { if (!estado.activo && (estado.cola.length || estado.actual)) arrancar([]); };
  const vaciar = () => { acumulado.length = 0; vistos.clear(); Object.assign(estado, { cola: [], hechas: {}, activo: false, motivo: "", paginas: 0, actual: null, esperada: null }); guardar(); pintar(); };

  // ---------- lo que se puede pedir desde fuera ----------
  const resumen = () => ({
    url: location.href, dept: deptDe(document), tienda: NOMBRE,
    acumulados: acumulado.length, sinPrecio: acumulado.filter((x) => x.price == null).length,
    cola: estado.cola.length + (estado.actual ? 1 : 0), paginas: estado.paginas, activo: !!estado.activo, motivo: estado.motivo || "",
  });
  const capturar = () => {
    if (bloqueada(document, location.href)) return "ComparaMEX: esta es la página de verificación de " + NOMBRE + ", no un listado.";
    const r = extraer(document, location.href);
    if (!r.n) {
      pintar("No encuentro productos en esta página. ¿Es un listado? Si lo es, " + NOMBRE + " cambió su página: avísame.");
      return "ComparaMEX: no encuentro productos ni en __NEXT_DATA__, ni en JSON-LD, ni en el DOM.";
    }
    const nuevos = sumar(r.items);
    guardar();
    const aMedias = (estado.cola.length || estado.actual) && !estado.activo;
    pintar(nuevos + " nuevos en esta página (leídos de " + r.items[0].via + ")" + (r.sig ? " · hay página siguiente" : "") + (r.subs.length ? " · " + r.subs.length + " subdepartamentos" : "") +
           (aMedias ? "\nHay un recorrido a medias: pulsa Reanudar." : ""));
    return "ComparaMEX: " + nuevos + " nuevos, " + (r.items.length - nuevos) + " ya estaban. ACUMULADOS: " + acumulado.length +
           ". El panel de abajo a la derecha tiene los botones para seguir solo y para descargar el JSON.";
  };
  const siguientes = () => arrancar([{ url: location.href, prof: 0, sub: false, pedido: true }]);
  const deptos = (prof) => { estado.prof = Math.max(0, Math.min(3, prof | 0)); arrancar([{ url: location.href, prof: 0, sub: true, pedido: true }]); };
  const lista = (urls) => { estado.prof = 0; arrancar(urls.map((u) => ({ url: u, prof: 0, sub: false, pedido: true }))); };
  return { capturar, siguientes, deptos, lista, pausar, reanudar, descargar, vaciar, resumen, arrancar, extraer, retomarAlCargar, estado, acumulado, tienda: TIENDA };
})();

if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.onMessage) {
  // Extensión: el popup manda órdenes y espera un resumen de vuelta; y al
  // cargar cada página se retoma el recorrido si esta es la que se esperaba.
  chrome.runtime.onMessage.addListener((msg, remitente, responder) => {
    let texto = null;
    const f = ComparaMEX[msg.accion];
    if (msg.accion === "resumen") { responder(ComparaMEX.resumen()); return; }
    if (typeof f === "function") {
      const r = msg.accion === "deptos" ? f(msg.prof) : msg.accion === "lista" ? f(msg.urls || []) : f();
      if (typeof r === "string") texto = r;
    }
    responder({ resumen: ComparaMEX.resumen(), texto });
  });
  if (typeof ComparaMEX.retomarAlCargar === "function") ComparaMEX.retomarAlCargar();
} else {
  // Marcador o consola: captura la página que tengo delante.
  ComparaMEX.capturar();
}
