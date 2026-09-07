#!/usr/bin/env node
// Genera las versiones minificadas que sirve index.html (js/app.min.js,
// js/firebase-init.min.js, css/style.min.css) a partir de los archivos
// "fuente" (js/app.js, js/firebase-init.js, css/style.css), que siguen
// siendo los que se editan a mano.
//
// IMPORTANTE: correr `npm run build` (o `node build.mjs`) antes de cada
// push que toque alguno de esos 3 archivos -- igual que compute_facets.py
// o generate_seo_pages.py, esto no se dispara solo. Si se te olvida, el
// sitio sigue funcionando (sirve el .min.js/.min.css DESACTUALIZADO) pero
// tus cambios no se ven reflejados hasta el próximo build.
import * as esbuild from "esbuild";
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";

// Sella index.html con la huella del contenido de cada archivo construido
// (css/style.min.css?v=..., js/app.min.js?v=...).
//
// POR QUÉ: GitHub Pages sirve estos archivos con cache-control max-age=600
// y sin cambiar de URL, así que el navegador que ya los tiene sigue
// mostrando la versión vieja del sitio aunque el push ya esté publicado.
// Pasó de verdad: el usuario no veía un botón nuevo que sí estaba
// desplegado. Con la huella en la URL, un cambio en el archivo cambia la
// URL y el navegador lo vuelve a pedir; si no cambió, sigue usando su
// copia y no se pierde el cacheo.
//
// Las páginas estáticas de SEO (categoria/, producto/) no cargan estos
// archivos -- son autónomas -- así que solo hay que sellar index.html.
function stampCacheBusting() {
  const archivos = ["css/style.min.css", "js/app.min.js", "js/firebase-init.min.js"];
  let html = readFileSync("index.html", "utf8");
  for (const ruta of archivos) {
    const hash = createHash("sha256").update(readFileSync(ruta)).digest("hex").slice(0, 8);
    const re = new RegExp(`(["'])${ruta.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}(\\?v=[0-9a-f]+)?\\1`, "g");
    html = html.replace(re, `$1${ruta}?v=${hash}$1`);
  }
  writeFileSync("index.html", html);
  console.log("index.html sellado con la huella de los 3 archivos construidos");
}

async function build() {
  await esbuild.build({
    entryPoints: ["js/app.js"],
    outfile: "js/app.min.js",
    minify: true,
    target: "es2019",
    logLevel: "info",
  });

  await esbuild.build({
    entryPoints: ["js/firebase-init.js"],
    outfile: "js/firebase-init.min.js",
    minify: true,
    format: "esm",
    target: "es2019",
    logLevel: "info",
  });

  await esbuild.build({
    entryPoints: ["css/style.css"],
    outfile: "css/style.min.css",
    minify: true,
    logLevel: "info",
  });

  stampCacheBusting();
}

build().catch((err) => {
  console.error(err);
  process.exit(1);
});
