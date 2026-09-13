// Sin trabajo de fondo: el recorrido vive en la pestaña de Amazon
// (content.js) y el popup solo le manda órdenes. El service worker existe
// para que Chrome trate la extensión como MV3 completa.
chrome.runtime.onInstalled.addListener(() => {});
