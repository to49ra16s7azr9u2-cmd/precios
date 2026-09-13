// El popup no captura nada: le manda órdenes al content script que vive en
// la pestaña de Amazon y muestra lo que este responde. Así el recorrido
// sigue aunque el popup se cierre.
const PATRONES = ["https://www.amazon.com.mx/*", "http://localhost/*"];
const $ = (id) => document.getElementById(id);
let pestaña = null;

async function pestañaDeAmazon() {
  const [activa] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (activa && /amazon\.com\.mx|localhost/.test(activa.url || "")) return activa;
  const todas = await chrome.tabs.query({ url: PATRONES });
  todas.sort((a, b) => (b.lastAccessed || 0) - (a.lastAccessed || 0));
  return todas[0] || null;
}

async function mandar(msg) {
  if (!pestaña) return null;
  try {
    return await chrome.tabs.sendMessage(pestaña.id, msg);
  } catch (e) {
    // La pestaña se abrió antes de instalar la extensión: se inyecta y se
    // vuelve a intentar una vez.
    try {
      await chrome.scripting.executeScript({ target: { tabId: pestaña.id }, files: ["content.js"] });
      return await chrome.tabs.sendMessage(pestaña.id, msg);
    } catch (e2) { return null; }
  }
}

function pintar(r, extra) {
  const e = $("estado");
  if (!r) {
    e.className = "aviso";
    e.textContent = "No encuentro una pestaña de amazon.com.mx con un listado. Abre una búsqueda, un departamento o «Los más vendidos» y vuelve a abrir esto.";
    for (const b of document.querySelectorAll("button")) b.disabled = true;
    return;
  }
  e.className = "";
  for (const b of document.querySelectorAll("button")) b.disabled = false;
  $("pausa").textContent = r.activo ? "Pausar" : "Reanudar";
  $("pausa").disabled = !r.activo && !r.cola;
  e.textContent = "Pestaña: " + (r.dept || r.url.slice(0, 50)) +
    "\nAcumulados: " + r.acumulados + " (" + r.sinPrecio + " sin precio)" +
    "\nCola: " + r.cola + " listados · páginas leídas: " + r.paginas +
    (r.activo ? "\n▶ recorriendo…" : (r.motivo ? "\n⏸ " + r.motivo : "")) +
    (extra ? "\n" + extra : "");
}

async function refrescar(extra) { pintar(await mandar({ accion: "resumen" }), extra); }

async function accion(msg) {
  const r = await mandar(msg);
  pintar(r && r.resumen ? r.resumen : r, r && r.texto);
}

document.addEventListener("DOMContentLoaded", async () => {
  pestaña = await pestañaDeAmazon();
  await refrescar();
  $("capturar").onclick = () => accion({ accion: "capturar" });
  $("siguientes").onclick = () => accion({ accion: "siguientes" });
  $("recorrer").onclick = () => accion({ accion: "deptos", prof: parseInt($("prof").value, 10) });
  $("lista").onclick = () => {
    const urls = $("urls").value.split(/\s+/).filter((u) => /amazon\.com\.mx|localhost/.test(u));
    if (urls.length) accion({ accion: "lista", urls });
  };
  $("pausa").onclick = () => accion({ accion: $("pausa").textContent === "Pausar" ? "pausar" : "reanudar" });
  $("descargar").onclick = () => accion({ accion: "descargar" });
  $("vaciar").onclick = () => { if (window.confirm("¿Borrar lo acumulado y la cola?")) accion({ accion: "vaciar" }); };
  setInterval(() => refrescar(), 1000);
});
