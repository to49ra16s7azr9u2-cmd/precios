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
