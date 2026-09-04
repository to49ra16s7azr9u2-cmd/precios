// ComparaMEX — soporte offline básico
//
// IMPORTANTE: sube este número cada vez que cambie index.html, css/style.js
// o js/app.js y hagas push. Si no, el Service Worker sigue sirviendo la
// versión cacheada anterior a los visitantes que ya lo tenían instalado
// (cache-first: la página nueva llega recién en la SEGUNDA carga, y solo si
// el número cambió — con el mismo número nunca se refresca).
const CACHE = "comparamx-v144";
const FILES = [
  "./",
  "./index.html",
  "./manifest.json",
  "./css/style.min.css",
  "./js/app.min.js",
  "./js/firebase-init.min.js",
  "./data/data.json",
  "./data/icons.json",
  "./data/shipping-rates.json",
  "./icons/icon.svg",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(FILES)));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);
  if (url.origin !== location.origin) return; // Leaflet CDN はそのままネットワーク

  // El catálogo (data/) va SIEMPRE por red primero, y solo cae a la caché si
  // no hay conexión.
  //
  // Antes iba cache-first como todo lo demás, y eso rompió el sitio entero
  // para los visitantes que ya lo tenían instalado: data/data.json dejó de
  // ser el catálogo completo y pasó a ser un manifiesto que apunta a
  // data/products-N.json. Un visitante que se quedó con el data.json VIEJO
  // en la caché y recibió el app.js NUEVO no tenía `productFiles` que leer,
  // así que el catálogo quedaba en cero y TODAS las páginas mostraban "No se
  // encontraron productos". El manifiesto y los archivos a los que apunta
  // tienen que verse entre sí sí o sí; además, en un comparador de precios,
  // servir precios viejos de la caché es justo lo que no se quiere.
  if (url.pathname.includes("/data/")) {
    e.respondWith(
      fetch(e.request)
        .then((res) => {
          if (res.ok) {
            const copy = res.clone();
            caches.open(CACHE).then((c) => c.put(e.request, copy));
          }
          return res;
        })
        .catch(() => caches.match(e.request))
    );
    return;
  }

  // El resto (app shell: html/css/js/iconos) sigue siendo キャッシュ優先・
  // なければネットワーク — es lo que da el arranque instantáneo y el soporte
  // offline, y se refresca con el número de versión de arriba.
  e.respondWith(
    caches.match(e.request).then((cached) => {
      const fresh = fetch(e.request)
        .then((res) => {
          if (res.ok) {
            const copy = res.clone();
            caches.open(CACHE).then((c) => c.put(e.request, copy));
          }
          return res;
        })
        .catch(() => cached);
      return cached || fresh;
    })
  );
});
