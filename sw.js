// ComparaMEX — soporte offline básico
//
// El número se sube cuando cambia la lista FILES de acá abajo. Ya NO hace
// falta subirlo en cada cambio de index.html/css/js: el HTML pasó a ser
// red-primero (ver más abajo), que era el motivo real de la regla.
//
// Por qué: index.html es el archivo que NOMBRA las versiones de los demás
// (js/app.min.js?v=<huella>, css/style.min.css?v=<huella>). Sirviéndolo
// desde la caché, un visitante que ya tenía el sitio instalado recibía el
// index viejo, que pide las huellas viejas, así que seguía corriendo el
// código anterior una carga entera -- con los datos nuevos, que sí van por
// red. Justo la mezcla que ya rompió el sitio una vez (ver el comentario de
// /data/ más abajo), y que esta semana habría dejado la pestaña colgada a
// quien tuviera en favoritos uno de los productos que se fusionaron.
//
// El número lleva 30 y pico de commits sin subir, lo que confirma que la
// regla "acordate de subirlo" no se sostiene sola.
const CACHE = "comparamx-v158";
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

  // El HTML va por red primero, igual que el catálogo y por el mismo motivo:
  // es lo que decide qué versión del js y del css se van a pedir. Si no hay
  // conexión cae a la caché, así que el soporte offline sigue igual.
  const esHtml = e.request.mode === "navigate"
    || url.pathname === "/"
    || url.pathname.endsWith("/")
    || url.pathname.endsWith(".html");

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
  if (esHtml || url.pathname.includes("/data/")) {
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
