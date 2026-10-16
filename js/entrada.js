/* Pantalla de entrada de ComparaMEX.
 *
 * Se muestra CADA VEZ que alguien abre el sitio desde fuera (dirección,
 * marcador, Google, otra app) y en CUALQUIER página: Inicio, categoría,
 * ficha de producto, 404... Por eso es un archivo propio y sin dependencias
 * (no usa js/app.js, que solo carga en index.html) y lo incluyen index.html y
 * todas las páginas estáticas de SEO (ver page_shell en
 * scripts/generate_seo_pages.py).
 *
 * Colores: negro y rojo del logo. Los dos buscadores (producto y categoría)
 * están a la vista desde el principio. Al elegir una categoría asoma
 * «Compara calidad» para esa categoría; se puede saltar.
 *
 * No guarda nada: la regla es una sola. No se muestra cuando la carga viene de
 * otra página del propio sitio (navegación interna), salvo al recargar.
 */
(function () {
  "use strict";
  var script = document.currentScript;
  var root = script && script.src ? new URL("../", script.src).href : "/";
  var CQ_FLAG = "comparamex.cqScroll";

  // Después de abrir una categoría con «Afinar con Compara calidad»: baja hasta
  // el panel de calidad cuando la lista ya lo pintó.
  function vigilarCq() {
    var flag = null;
    try { flag = sessionStorage.getItem(CQ_FLAG); } catch (e) {}
    if (!flag) return;
    var intentos = 0;
    var t = setInterval(function () {
      var q = document.getElementById("qualityPicker");
      intentos++;
      if (q && !q.classList.contains("hidden")) {
        clearInterval(t);
        try { sessionStorage.removeItem(CQ_FLAG); } catch (e) {}
        q.scrollIntoView({ behavior: "smooth", block: "start" });
      } else if (intentos > 40) {
        clearInterval(t);
        try { sessionStorage.removeItem(CQ_FLAG); } catch (e) {}
      }
    }, 250);
  }
  vigilarCq();

  function debeMostrarse() {
    if (navigator.webdriver || /bot|crawl|spider|lighthouse/i.test(navigator.userAgent)) return false;
    var recarga = false;
    try {
      var nav = performance.getEntriesByType("navigation")[0];
      recarga = !!nav && nav.type === "reload";
    } catch (e) {}
    try {
      if (!recarga && document.referrer && new URL(document.referrer).origin === location.origin) return false;
    } catch (e) {}
    return true;
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function plano(s) {
    return String(s).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  }

  function abrir() {
    var ov = document.createElement("div");
    ov.id = "entradaModal";
    ov.className = "ent-overlay";
    ov.innerHTML =
      '<div class="ent-card" role="dialog" aria-modal="true" aria-labelledby="entTitulo">' +
      '<div class="ent-head">' +
      '<img class="ent-logo" src="' + root + 'icons/icon.svg" alt="" width="34" height="34">' +
      '<div><div class="ent-marca">Compara<span>MEX</span></div>' +
      '<h2 id="entTitulo" class="ent-titulo">¿Cómo quieres empezar?</h2></div>' +
      '<button type="button" class="ent-x" id="entX" aria-label="Cerrar">✕</button></div>' +
      '<form class="ent-bloque" id="entForm" role="search">' +
      '<label class="ent-label" for="entNombre">Buscar por nombre de producto</label>' +
      '<div class="ent-fila"><input id="entNombre" class="ent-input" type="search" placeholder="iPhone, licuadora, laptop…" autocomplete="off" enterkeyhint="search">' +
      '<button type="submit" class="ent-btn ent-btn-rojo">Buscar</button></div></form>' +
      '<div class="ent-bloque">' +
      '<label class="ent-label" for="entCat">Buscar por categoría</label>' +
      '<input id="entCat" class="ent-input" type="search" placeholder="Celulares, herramientas, cocina…" autocomplete="off">' +
      '<div class="ent-cats" id="entCats" role="list"></div>' +
      '<div class="ent-cq ent-oculto" id="entCq"></div></div>' +
      '<div class="ent-pie">' +
      '<button type="button" class="ent-btn ent-btn-borde" id="entInicio">Ir a Inicio</button>' +
      '<button type="button" class="ent-btn ent-btn-fantasma" id="entMirar">Mirar esta pantalla</button></div>' +
      "</div>";
    document.body.appendChild(ov);
    document.documentElement.classList.add("ent-abierto");

    function cerrar() {
      ov.remove();
      document.documentElement.classList.remove("ent-abierto");
      document.removeEventListener("keydown", onKey);
    }
    function onKey(e) { if (e.key === "Escape") cerrar(); }
    document.addEventListener("keydown", onKey);
    ov.addEventListener("click", function (e) { if (e.target === ov) cerrar(); });
    ov.querySelector("#entX").onclick = cerrar;
    ov.querySelector("#entMirar").onclick = cerrar;
    ov.querySelector("#entInicio").onclick = function () { cerrar(); ir(root + "#/"); };

    ov.querySelector("#entForm").onsubmit = function (e) {
      e.preventDefault();
      var q = ov.querySelector("#entNombre").value.trim();
      if (!q) { ov.querySelector("#entNombre").focus(); return; }
      cerrar();
      ir(root + "#/list?q=" + encodeURIComponent(q));
    };

    var cats = [];
    var box = ov.querySelector("#entCats");
    var cq = ov.querySelector("#entCq");
    var inp = ov.querySelector("#entCat");

    function pintar() {
      var q = plano(inp.value.trim());
      var html = "";
      var n = 0;
      cats.forEach(function (c) {
        if (q && plano(c.name).indexOf(q) < 0) return;
        n++;
        html += '<button type="button" class="ent-chip" data-cat="' + esc(c.id) + '">' + esc(c.name) + "</button>";
      });
      if (q) {
        var m = 0;
        cats.forEach(function (c) {
          (c.subs || []).forEach(function (s) {
            if (m >= 10 || plano(s).indexOf(q) < 0 || plano(c.name).indexOf(q) >= 0) return;
            m++;
            n++;
            html += '<button type="button" class="ent-chip ent-chip-sub" data-cat="' + esc(c.id) + '" data-sub="' + esc(s) + '">' +
              esc(s) + ' <span>en ' + esc(c.name) + "</span></button>";
          });
        });
      }
      box.innerHTML = html || '<p class="ent-vacio">Ninguna categoría se llama así. Prueba con otra palabra o busca por nombre arriba.</p>';
    }

    function mostrarCq(c, sub) {
      var nombre = sub ? sub + " (" + c.name + ")" : c.name;
      cq.innerHTML =
        '<img class="ent-cq-logo" src="' + root + 'icons/logo-comparacalidad.png" alt="Compara calidad">' +
        '<p class="ent-cq-q">En <strong>' + esc(nombre) + "</strong>: ¿cuál te alcanza para lo que haces? Elige nivel y tamaño y la lista queda más precisa.</p>" +
        '<div class="ent-cq-btns"><button type="button" class="ent-btn ent-btn-rojo" id="entCqSi">Afinar con Compara calidad</button>' +
        '<button type="button" class="ent-saltar" id="entCqNo">Saltar y ver la lista</button></div>';
      cq.classList.remove("ent-oculto", "ent-pop");
      void cq.offsetWidth;
      cq.classList.add("ent-pop");
      try { cq.scrollIntoView({ block: "nearest", behavior: "smooth" }); } catch (e) {}
      var url = root + "#/list?cat=" + encodeURIComponent(c.id) + (sub ? "&sub=" + encodeURIComponent(sub) : "");
      cq.querySelector("#entCqSi").onclick = function () {
        try { sessionStorage.setItem(CQ_FLAG, "1"); } catch (e) {}
        cerrar();
        ir(url);
        vigilarCq();
      };
      cq.querySelector("#entCqNo").onclick = function () { cerrar(); ir(url); };
    }

    box.addEventListener("click", function (e) {
      var b = e.target.closest ? e.target.closest(".ent-chip") : null;
      if (!b) return;
      box.querySelectorAll(".ent-chip.ent-on").forEach(function (x) { x.classList.remove("ent-on"); });
      b.classList.add("ent-on");
      var c = cats.filter(function (x) { return x.id === b.getAttribute("data-cat"); })[0];
      if (c) mostrarCq(c, b.getAttribute("data-sub"));
    });
    inp.addEventListener("input", function () { cq.classList.add("ent-oculto"); pintar(); });
    inp.addEventListener("keydown", function (e) {
      if (e.key !== "Enter") return;
      e.preventDefault();
      var primero = box.querySelector(".ent-chip");
      if (primero) primero.click();
    });

    fetch(root + "data/categorias-entrada.json")
      .then(function (r) { return r.json(); })
      .then(function (d) { cats = d; pintar(); })
      .catch(function () {
        box.innerHTML = '<p class="ent-vacio">No se pudo cargar la lista de categorías. Usa «Ir a Inicio».</p>';
      });

    ov.querySelector("#entNombre").focus();
  }

  // Misma página (solo cambia el # de la app) o página nueva: assign sirve a ambas.
  function ir(url) { location.assign(url); }

  function iniciar() { if (debeMostrarse()) abrir(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciar);
  else iniciar();
})();
