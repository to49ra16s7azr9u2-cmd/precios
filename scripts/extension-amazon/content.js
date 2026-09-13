// Captura de Amazon para ComparaMEX: el mismo código sirve de content
// script de la extensión (scripts/extension-amazon/) y de marcador
// (scripts/captura_amazon.html lo carga tal cual). Lee un listado de
// amazon.com.mx, acumula productos en localStorage, sigue páginas, recorre
// subdepartamentos y parte por tramos de precio lo que Amazon corta.
const ComparaMEX = (() => {
  const KEY = "comparamex.captura.amazon";   // productos acumulados
  const COLA = "comparamex.captura.cola";    // estado del recorrido
  const ESPERA = window.__comparamexEspera || [2500, 5000];  // ms entre páginas, al azar
  const MAX_PAG = 20;        // freno duro por listado
  const TOPE_AMAZON = 7;     // Amazon corta los departamentos en ~7 páginas
  const BANDAS = [0, 300, 600, 1000, 1500, 2500, 4000, 7000, 12000, 20000, 40000, 80000];  // MXN
  const ANCHO_MIN = 50;      // no se parte un tramo de menos de $50

  // Lo que se ve SIEMPRE es lo que esta función devuelve: la consola imprime
  // el valor de lo último que se evaluó, y eso no lo esconde ningún filtro.
  // Por eso el cuerpo no es async: el recorrido arranca aparte y el panel
  // en la página es el que va contando.
  if (!/amazon\.com\.mx$|^localhost$/.test(location.hostname)) {
    const fuera = () => "ComparaMEX: esto no es amazon.com.mx. Abre un listado de esa tienda y vuelve a ejecutarlo.";
    return { capturar: fuera, resumen: () => null };
  }

  // ---------- almacén ----------
  const leer = (k, def) => { try { const v = JSON.parse(localStorage.getItem(k) || "null"); return v == null ? def : v; } catch (e) { return def; } };
  const escribir = (k, v) => localStorage.setItem(k, JSON.stringify(v));
  let acumulado = leer(KEY, []);
  if (!Array.isArray(acumulado)) acumulado = [];
  const vistos = new Set(acumulado.map((x) => x.asin));
  const estado = Object.assign({ cola: [], hechas: {}, nodos: {}, activo: false, motivo: "", prof: 0, latido: 0, paginas: 0 }, leer(COLA, {}));
  const guardar = () => { escribir(KEY, acumulado); escribir(COLA, estado); };

  // ---------- util ----------
  const norm = (t) => (t || "").trim().replace(/\s+/g, " ");
  const precioDe = (txt) => {
    const m = /\$\s?([\d.,]+)/.exec(txt || "");
    if (!m) return null;
    const n = parseFloat(m[1].replace(/,/g, ""));
    return isFinite(n) && n > 0 ? n : null;
  };
  // La foto viene con la transformación que Amazon esté probando ese día;
  // se deja el id de la imagen con _AC_SX679_, que es la que usa el catálogo.
  const fotoDe = (src) => {
    const m = /\/images\/I\/([^.\/]+)\./.exec(src || "");
    return m ? "https://m.media-amazon.com/images/I/" + m[1] + "._AC_SX679_.jpg" : (src || null);
  };
  const rhDe = (u) => { const m = /[?&]rh=([^&#]*)/.exec(u); return m ? decodeURIComponent(m[1].replace(/\+/g, " ")) : ""; };
  const nodoDe = (u) => {
    const n = /(?:^|,)n:(\d+)/.exec(rhDe(u)); if (n) return n[1];
    const b = /\/(?:gp\/(?:bestsellers|new-releases|movers-and-shakers|most-wished-for)|zgbs|new-releases)\/[^\/?#]+\/(\d+)/.exec(u);
    return b ? b[1] : null;
  };
  const esBS = (u) => /\/(gp\/(bestsellers|new-releases|movers-and-shakers|most-wished-for)|zgbs)\b/.test(u);
  const dormir = (ms) => new Promise((r) => setTimeout(r, ms));
  const azar = () => ESPERA[0] + Math.random() * (ESPERA[1] - ESPERA[0]);
  const abs = (href, base) => { try { return new URL(href, base).href; } catch (e) { return null; } };

  // ---------- leer un listado (documento ya cargado o bajado) ----------
  const SELECTORES = [
    'div[data-component-type="s-search-result"][data-asin]',
    '.s-main-slot div[data-asin]:not([data-asin=""])',
    '[data-cel-widget^="search_result_"][data-asin]',
    'div[role="listitem"][data-asin]:not([data-asin=""])',
    // Los más vendidos y los nuevos lanzamientos (p13n): tarjetas con data-asin.
    '#gridItemRoot [data-asin], .p13n-sc-uncoverable-faceout[data-asin], [id^="p13n-asin-index-"][data-asin]',
    'div[data-asin]:not([data-asin=""])',
  ];
  const deptDe = (doc) => {
    const cands = [
      doc.querySelector("#departments .a-text-bold"),
      doc.querySelector("#zg_banner_text"),
      doc.querySelector('#s-refinements .a-text-bold, .s-navigation-item.a-text-bold'),
      doc.querySelector("h1"),
    ];
    for (const c of cands) {
      const t = norm(c && c.textContent);
      // "Filtros", "Departamento", "Resultados" son encabezados de la columna, no un departamento.
      if (t && t.length < 80 && !/^(filtros|departamento|resultados|ver todo|todos)\b/i.test(t)) return t.replace(/^Los más (vendidos|deseados) en |^Nuevos lanzamientos en |^Subiendo como la espuma en /i, "");
    }
    return norm(doc.title).replace(/^Amazon\.com\.mx\s*:?\s*/i, "").replace(/^Los más vendidos en /i, "") || null;
  };
  const extraer = (doc, url) => {
    let filas = [];
    for (const sel of SELECTORES) {
      filas = Array.from(doc.querySelectorAll(sel)).filter((d) => /^[A-Z0-9]{10}$/.test(d.getAttribute("data-asin") || ""));
      if (filas.length) break;
    }
    // El departamento solo tiene sentido en un departamento (rh=n:...) o en
    // los más vendidos; en una búsqueda suelta ("Celulares") no hay ninguno.
    const node = nodoDe(url), via = esBS(url) ? "bs" : "s";
    const dept = (node || esBS(url)) ? deptDe(doc) : null;
    const items = [];
    for (const d of filas) {
      const asin = d.getAttribute("data-asin");
      const h2 = d.querySelector("h2");
      let title = norm(h2 ? h2.textContent : "");
      if (!title) { const img = d.querySelector("img[alt]"); title = norm(img ? img.getAttribute("alt") : ""); }
      if (!title) { const a = d.querySelector('a[href*="/dp/"]'); title = norm(a ? a.textContent : ""); }
      if (!title) continue;
      const sponsored = !!d.querySelector('.puis-sponsored-label-text, .s-sponsored-label-text, [aria-label="Patrocinado"], [aria-label="Sponsored"]');
      // .a-text-price es el precio tachado (de lista): no es el que se paga.
      const po = d.querySelector(".a-price:not(.a-text-price) .a-offscreen, .p13n-sc-price, [class*='p13n-sc-price'], .a-color-price");
      const price = precioDe(po ? po.textContent : "");
      const img = d.querySelector("img.s-image, img[src*='/images/I/']");
      const item = { asin, title, price, photo: fotoDe(img ? img.getAttribute("src") : ""),
                     url: "https://www.amazon.com.mx/dp/" + asin };
      if (sponsored) item.sponsored = true;
      if (dept) item.dept = dept;
      if (node) item.node = node;
      item.via = via;
      const rk = d.querySelector(".zg-bdg-text");
      if (rk) { const n = parseInt(norm(rk.textContent).replace(/\D/g, ""), 10); if (n) item.rank = n; }
      items.push(item);
    }
    // Página siguiente, si el listado la ofrece.
    let sig = null;
    const a = doc.querySelector('a.s-pagination-next:not(.s-pagination-disabled), li.a-last:not(.a-disabled) a[href]');
    if (a) sig = abs(a.getAttribute("href"), url);
    // Subdepartamentos: enlaces del menú de la izquierda que solo llevan nodo
    // (rh=n:...), sin marca ni otros filtros. En los más vendidos, el árbol.
    const subs = new Set();
    for (const l of doc.querySelectorAll('#departments a[href], #s-refinements a[href*="rh=n"], .s-navigation-indent-1 a[href], .s-navigation-indent-2 a[href]')) {
      const h = abs(l.getAttribute("href"), url); if (!h) continue;
      const rh = rhDe(h); const n = nodoDe(h);
      if (n && n !== node && /^n:\d+(,n:\d+)*$/.test(rh)) subs.add(abs("/s?rh=n%3A" + n, url));
    }
    if (esBS(url)) {
      for (const l of doc.querySelectorAll('#zg-left-col a[href], [class*="zg-browse"] a[href], .zg-nav-tree a[href], [id^="zg_browseRoot"] a[href]')) {
        const h = abs(l.getAttribute("href"), url); if (!h) continue;
        const n = nodoDe(h);
        if (n && n !== node && esBS(h)) subs.add(h.split("?")[0]);
      }
    }
    return { items, sig, subs: Array.from(subs), n: filas.length };
  };

  // ---------- acumular ----------
  const sumar = (items) => {
    let nuevos = 0;
    for (const it of items) {
      if (vistos.has(it.asin)) continue;
      vistos.add(it.asin); acumulado.push(it); nuevos++;
    }
    return nuevos;
  };

  // ---------- tramos de precio ----------
  const conBanda = (url, a, b) => {
    const u = new URL(url);
    const rh = rhDe(url).split(",").filter((p) => p && !p.startsWith("p_36:"));
    rh.push("p_36:" + Math.round(a * 100) + "-" + (b == null ? "" : Math.round(b * 100)));
    u.searchParams.set("rh", rh.join(","));
    u.searchParams.delete("page");
    return u.href;
  };
  const partir = (t) => {
    if (esBS(t.url)) return [];
    if (!t.banda) {
      const out = [];
      for (let i = 0; i < BANDAS.length; i++) {
        const b = BANDAS[i + 1] == null ? null : BANDAS[i + 1];
        out.push({ url: conBanda(t.url, BANDAS[i], b), prof: t.prof, banda: [BANDAS[i], b], sub: false });
      }
      return out;
    }
    const [a, b] = t.banda;
    if (b == null) return [];              // el tramo abierto de arriba no se parte
    if (b - a <= ANCHO_MIN) return [];
    const m = Math.round((a + b) / 2);
    return [{ url: conBanda(t.url, a, m), prof: t.prof, banda: [a, m], sub: false },
            { url: conBanda(t.url, m, b), prof: t.prof, banda: [m, b], sub: false }];
  };

  // ---------- panel ----------
  let panel = null, cuerpo = null, botones = {};
  const boton = (texto, fn) => { const b = document.createElement("button"); b.textContent = texto; b.onclick = fn;
    b.style.cssText = "margin:4px 4px 0 0;padding:6px 10px;border:0;border-radius:6px;background:#FF0211;color:#fff;font:600 13px system-ui,sans-serif;cursor:pointer"; return b; };
  const pintar = (extra) => {
    if (!panel || !document.body.contains(panel)) {
      panel = document.createElement("div"); panel.id = "comparamex-panel";
      panel.style.cssText = "position:fixed;z-index:2147483647;bottom:16px;right:16px;width:340px;background:#111;color:#fff;padding:14px 16px;border-radius:12px;font:13px/1.45 system-ui,sans-serif;box-shadow:0 8px 28px rgba(0,0,0,.4);white-space:pre-line";
      cuerpo = document.createElement("div"); panel.appendChild(cuerpo);
      const fila = document.createElement("div"); fila.style.marginTop = "8px"; panel.appendChild(fila);
      botones.sig = boton("Páginas siguientes", () => arrancar([{ url: location.href, prof: 0, sub: false }]));
      botones.rec = boton("Recorrer departamentos", () => {
        const p = parseInt(window.prompt("¿Cuántos niveles de subdepartamentos? (0 = solo este, 1 = sus hijos, 2 = también los nietos)", "1") || "0", 10);
        if (isNaN(p)) return; estado.prof = Math.max(0, Math.min(3, p)); arrancar([{ url: location.href, prof: 0, sub: true }]);
      });
      botones.lista = boton("Lista de URLs", () => {
        const t = window.prompt("Pega URLs de Amazon separadas por espacios (departamentos, búsquedas, más vendidos):", "");
        if (!t) return;
        const urls = t.split(/\s+/).filter((u) => /amazon\.com\.mx/.test(u));
        estado.prof = 0; arrancar(urls.map((u) => ({ url: u, prof: 0, sub: false })));
      });
      botones.pausa = boton("Pausar", () => { if (estado.activo) { estado.activo = false; estado.motivo = "pausado a mano"; guardar(); pintar(); } else if (estado.cola.length) { arrancar([]); } });
      botones.bajar = boton("Descargar JSON", descargar);
      botones.vaciar = boton("Vaciar", () => { if (!window.confirm("¿Borrar los " + acumulado.length + " productos acumulados y la cola?")) return;
        acumulado.length = 0; vistos.clear(); Object.assign(estado, { cola: [], hechas: {}, nodos: {}, activo: false, motivo: "", paginas: 0 }); guardar(); pintar(); });
      const x = boton("×", () => panel.remove()); x.style.background = "#444"; x.style.float = "right";
      panel.insertBefore(x, cuerpo);
      for (const k of ["sig", "rec", "lista", "pausa", "bajar", "vaciar"]) fila.appendChild(botones[k]);
      document.body.appendChild(panel);
    }
    botones.pausa.textContent = estado.activo ? "Pausar" : (estado.cola.length ? "Reanudar" : "Pausar");
    const sinPrecio = acumulado.filter((x) => x.price == null).length;
    cuerpo.textContent = "ComparaMEX · acumulados: " + acumulado.length + " (" + sinPrecio + " sin precio)" +
      "\nCola: " + estado.cola.length + " listados · páginas leídas: " + estado.paginas +
      (estado.activo ? "\n▶ recorriendo…" : (estado.motivo ? "\n⏸ " + estado.motivo : "")) +
      (extra ? "\n" + extra : "");
  };

  const descargar = () => {
    const json = JSON.stringify(acumulado, null, 1);
    window.__comparamexJSON = json;
    const fecha = new Date().toISOString().slice(0, 10);
    try {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([json], { type: "application/json" }));
      a.download = "amazon-" + fecha + "-" + acumulado.length + ".json";
      document.body.appendChild(a); a.click(); a.remove();
    } catch (e) { /* queda el portapapeles */ }
    try { navigator.clipboard.writeText(json).catch(() => {}); } catch (e) { /* sin API */ }
    if (typeof copy === "function") { try { copy(json); } catch (e) { /* idem */ } }
    pintar("Descargado amazon-" + fecha + "-" + acumulado.length + ".json (y copiado al portapapeles).");
  };

  // ---------- el recorrido ----------
  const bajar = async (url) => {
    for (let intento = 0; intento < 2; intento++) {
      let r;
      try { r = await fetch(url, { credentials: "include" }); } catch (e) { r = null; }
      if (r && r.ok) {
        const html = await r.text();
        if (/validateCaptcha|Robot Check|Escribe los caracteres/i.test(html)) return { captcha: true };
        const doc = new DOMParser().parseFromString(html, "text/html");
        if (/Algo falló|Something went wrong/i.test(doc.title || "")) { await dormir(15000); continue; }
        return { doc };
      }
      if (r && (r.status === 503 || r.status === 429)) { await dormir(20000); continue; }
      return { error: r ? "HTTP " + r.status : "sin respuesta" };
    }
    return { error: "Amazon no responde" };
  };
  const detener = (motivo) => { estado.activo = false; estado.motivo = motivo; guardar(); pintar(); };
  const encolar = (nuevos) => {
    for (const t of nuevos) {
      if (estado.hechas[t.url]) continue;
      const n = nodoDe(t.url);
      if (n && !t.banda && estado.nodos[n] && !esBS(t.url)) continue;  // ese departamento ya se recorrió
      estado.hechas[t.url] = 1; if (n && !t.banda) estado.nodos[n] = 1;
      estado.cola.push(t);
    }
  };
  const recorrer = async (t) => {
    let url = t.url, pag = 0, capado = false;
    while (url && pag < MAX_PAG && estado.activo) {
      let doc;
      if (pag === 0 && url === location.href) doc = document;
      else {
        const r = await bajar(url);
        if (r.captcha) { estado.cola.unshift(t); return detener("Amazon pidió un captcha. Abre una página de Amazon en esta pestaña, resuélvelo y vuelve a ejecutar el marcador."); }
        if (r.error) { estado.cola.unshift(t); return detener("Amazon respondió " + r.error + " en " + url + ". Vuelve a ejecutar el marcador para seguir."); }
        doc = r.doc;
      }
      const r = extraer(doc, url);
      pag++; estado.paginas++; estado.latido = Date.now();
      const nuevos = sumar(r.items);
      if (pag === 1 && t.sub && t.prof < estado.prof) encolar(r.subs.map((u) => ({ url: u, prof: t.prof + 1, sub: true })));
      guardar();
      pintar("Ahora: " + (r.items[0] && r.items[0].dept ? r.items[0].dept : url.slice(0, 60)) + (t.banda ? " ($" + t.banda[0] + "–" + (t.banda[1] == null ? "∞" : t.banda[1]) + ")" : "") +
             " · pág. " + pag + " · " + nuevos + " nuevos");
      if (!r.n) break;
      url = r.sig;
      capado = pag >= TOPE_AMAZON;
      if (url) await dormir(azar());
    }
    // Se llegó al tope de Amazon: lo que falta se pide por tramos de precio.
    if (capado && estado.activo) encolar(partir(t));
  };
  const correr = async () => {
    window.__comparamexCorriendo = true;
    try {
      while (estado.cola.length && estado.activo) {
        const t = estado.cola.shift(); guardar();
        await recorrer(t);
        if (estado.cola.length && estado.activo) await dormir(azar());
      }
      if (estado.activo) detener("Recorrido terminado: " + acumulado.length + " productos. Descarga el JSON.");
    } catch (e) { detener("Error: " + (e && e.message)); }
    window.__comparamexCorriendo = false;
  };
  const arrancar = (nuevos) => {
    if (window.__comparamexCorriendo) { pintar("Ya hay un recorrido andando en esta pestaña."); return; }
    if (estado.activo && Date.now() - estado.latido < 30000) { pintar("Ya hay un recorrido andando en otra pestaña. Espera a que termine o páusalo allí."); return; }
    encolar(nuevos);
    estado.activo = true; estado.motivo = ""; estado.latido = Date.now(); guardar(); pintar();
    correr();
  };

  // ---------- lo que se puede pedir desde fuera ----------
  const resumen = () => ({
    url: location.href, dept: deptDe(document),
    acumulados: acumulado.length, sinPrecio: acumulado.filter((x) => x.price == null).length,
    cola: estado.cola.length, paginas: estado.paginas, activo: !!estado.activo, motivo: estado.motivo || "",
  });
  const capturar = () => {
    const r = extraer(document, location.href);
    if (!r.n) {
      pintar("No encuentro productos en esta página. ¿Es un listado? Si lo es, Amazon cambió su HTML: avísame.");
      return "ComparaMEX: no encuentro tarjetas de producto con ninguno de los " + SELECTORES.length + " selectores.";
    }
    const nuevos = sumar(r.items);
    guardar();
    // Si quedó un recorrido a medias (captcha, pestaña cerrada), se retoma.
    const aMedias = estado.cola.length && (!estado.activo || Date.now() - estado.latido > 30000);
    pintar(nuevos + " nuevos en esta página" + (r.sig ? " · hay página siguiente" : "") + (r.subs.length ? " · " + r.subs.length + " subdepartamentos" : "") +
           (aMedias ? "\nHay un recorrido a medias: pulsa Reanudar." : ""));
    return "ComparaMEX: " + nuevos + " nuevos, " + (r.items.length - nuevos) + " ya estaban. ACUMULADOS: " + acumulado.length +
           ". El panel de abajo a la derecha tiene los botones para seguir solo y para descargar el JSON.";
  };
  const siguientes = () => arrancar([{ url: location.href, prof: 0, sub: false }]);
  const deptos = (prof) => { estado.prof = Math.max(0, Math.min(3, prof | 0)); arrancar([{ url: location.href, prof: 0, sub: true }]); };
  const lista = (urls) => { estado.prof = 0; arrancar(urls.map((u) => ({ url: u, prof: 0, sub: false }))); };
  const pausar = () => { if (estado.activo) { estado.activo = false; estado.motivo = "pausado a mano"; guardar(); pintar(); } };
  const reanudar = () => { if (!estado.activo && estado.cola.length) arrancar([]); };
  const vaciar = () => { acumulado.length = 0; vistos.clear(); Object.assign(estado, { cola: [], hechas: {}, nodos: {}, activo: false, motivo: "", paginas: 0 }); guardar(); pintar(); };
  return { capturar, siguientes, deptos, lista, pausar, reanudar, descargar, vaciar, resumen, arrancar, extraer, estado, acumulado };
})();

if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.onMessage) {
  // Extensión: el popup manda órdenes y espera un resumen de vuelta.
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
} else {
  // Marcador o consola: captura la página que tengo delante.
  ComparaMEX.capturar();
}
