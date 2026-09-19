// Cuenta una visita de categoría desde las páginas estáticas.
//
// POR QUÉ APARTE DE js/app.js
// Las fichas estáticas (producto/<id>/) no cargan la aplicación ni el SDK de
// Firebase: son HTML servido tal cual, y ahí llega la mayor parte del
// tráfico de buscadores. Sin esto, el ranking "en vivo" de la portada solo
// vería a quien navega dentro de la aplicación.
//
// QUÉ MANDA
// Una suma de uno al contador de su categoría en el documento del día
// (popularidad/AAAA-MM-DD), por la API REST de Firestore. No manda quién,
// ni qué producto, ni identificador alguno: solo "alguien abrió algo de
// Herramientas". No usa cookies ni almacena datos personales, así que no
// depende del consentimiento de analítica.
//
// EL MISMO FRENO QUE LA APLICACIÓN
// Recargar diez veces la misma ficha cuenta una sola vez cada 30 minutos,
// con la marca guardada en este navegador (localStorage), en la misma clave
// que usa js/app.js para que las dos vías no cuenten doble.
(function () {
  var PROYECTO = "comparamx";
  var CLAVE = "AIzaSyABXhT-z1-61Ghb_H32X5o2pOdedFX0_zU";   // la misma clave web pública de js/firebase-init.js
  var MINUTOS = 30;
  var LS = "comparamex.vistasEnviadas";

  function hoy() {
    return new Date().toISOString().slice(0, 10);
  }
  // Un campo con espacios o acentos va entre acentos graves en fieldPath.
  function campo(categoria) {
    return "cats.`" + String(categoria).replace(/\\/g, "\\\\").replace(/`/g, "\\`") + "`";
  }
  function yaContada(id) {
    try {
      var m = JSON.parse(localStorage.getItem(LS) || "{}");
      if (Date.now() - (m[id] || 0) < MINUTOS * 60000) return true;
      m[id] = Date.now();
      var ids = Object.keys(m);
      if (ids.length > 300) {
        ids.sort(function (a, b) { return m[a] - m[b]; })
           .slice(0, ids.length - 300).forEach(function (k) { delete m[k]; });
      }
      localStorage.setItem(LS, JSON.stringify(m));
    } catch (e) { /* navegación privada: se cuenta igual, sin freno */ }
    return false;
  }

  function contar(categoria, idFicha) {
    if (!categoria || yaContada(idFicha || categoria)) return;
    var doc = "projects/" + PROYECTO + "/databases/(default)/documents/popularidad/" + hoy();
    // update con máscara vacía + updateTransforms: crea el documento si es
    // la primera visita del día y suma uno si ya existe.
    var cuerpo = JSON.stringify({
      writes: [{
        update: { name: doc },
        updateMask: { fieldPaths: [] },
        updateTransforms: [{ fieldPath: campo(categoria), increment: { integerValue: "1" } }],
      }],
    });
    try {
      fetch("https://firestore.googleapis.com/v1/projects/" + PROYECTO +
            "/databases/(default)/documents:commit?key=" + CLAVE,
            { method: "POST", headers: { "Content-Type": "application/json" }, body: cuerpo, keepalive: true })
        .catch(function () { /* sin red o sin permiso: el ranking sigue con su dato de siempre */ });
    } catch (e) { /* idem */ }
  }

  window.ComparaMXVistas = { contar: contar };
})();
