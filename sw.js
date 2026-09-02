// ComparaMEX — soporte offline básico
//
// IMPORTANTE: sube este número cada vez que cambie index.html, css/style.js
// o js/app.js y hagas push. Si no, el Service Worker sigue sirviendo la
// versión cacheada anterior a los visitantes que ya lo tenían instalado
// (cache-first: la página nueva llega recién en la SEGUNDA carga, y solo si
// el número cambió — con el mismo número nunca se refresca).
const CACHE = "comparamx-v126";
const FILES = [
  "./",
  "./index.html",
  "./manifest.json",
  "./css/style.css",
  "./js/app.js",
  "./js/firebase-init.js",
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

// キャッシュ優先・なければネットワーク(更新時は新しいファイルを取得して差し替え)
self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  if (new URL(e.request.url).origin !== location.origin) return; // Leaflet CDN はそのままネットワーク
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
