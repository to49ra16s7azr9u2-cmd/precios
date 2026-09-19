// Sin trabajo de fondo: el recorrido vive en la pestaña de la tienda
// (content.js), que navega página por página y se retoma solo en cada carga.
// El popup solo le manda órdenes. El service worker existe para que Chrome
// trate la extensión como MV3 completa.
chrome.runtime.onInstalled.addListener(() => {});
