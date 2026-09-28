// Google Analytics de las páginas estáticas (producto/, categoria/...).
// Antes iba en línea en cada una de las 21 mil páginas; acá se baja una vez
// y queda en caché (26-sep, aligerar el sitio).
//
// Estas páginas no tienen el aviso de cookies (viven fuera de la SPA): por
// defecto Consent Mode queda denegado, y solo se concede si ya había una
// elección guardada en localStorage de una visita anterior a la SPA (mismo
// origen, mismo storage). Se carga sin async ni defer, antes que gtag.js.
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('consent', 'default', {
  'analytics_storage': 'denied',
  'ad_storage': 'denied',
  'ad_user_data': 'denied',
  'ad_personalization': 'denied'
});
try {
  if (localStorage.getItem('comparamexCookieConsent') === 'accepted') {
    gtag('consent', 'update', {
      'analytics_storage': 'granted',
      'ad_storage': 'granted',
      'ad_user_data': 'granted',
      'ad_personalization': 'granted'
    });
  }
} catch (e) {}
gtag('js', new Date());
gtag('config', 'G-NZ0RG4S274');

// Respaldo de las fotos: las páginas piden la miniatura al CDN de la tienda
// (miniatura() en scripts/generate_seo_pages.py); si ese tamaño no existe,
// se pide la original, sacada de la miniatura con las reglas inversas. Antes
// cada <img> llevaba la URL original completa en su onerror (28-sep: el 9%
// de una página de categoría, contra el límite de 1 GB de GitHub Pages).
function fo(img) {
  img.onerror = null;
  var u = img.getAttribute('src') || '', o = u;
  try {
    if (/\/\/http2\.mlstatic\.com\//.test(u)) {
      o = u.replace(/-[A-Z]\.(jpe?g|webp|png)(\?.*)?$/i, '-O.jpg');
    } else if (/(vteximg\.com\.br|vtexassets\.com)\/arquivos\/ids\//.test(u)) {
      o = u.replace(/(\/arquivos\/ids\/\d+)-\d+-\d+/, '$1');
    } else if (/\/\/i5\.walmartimages\.com/.test(u)) {
      var x = new URL(u);
      x.searchParams.set('odnHeight', '2000');
      x.searchParams.set('odnWidth', '2000');
      o = x.toString();
    } else if (/\/\/m\.media-amazon\.com\/images\/I\//.test(u)) {
      o = u.replace(/\._AC_SL\d+_\./, '.');
    }
  } catch (e) {}
  if (o !== u) img.src = o;
}
