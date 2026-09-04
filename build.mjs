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
}

build().catch((err) => {
  console.error(err);
  process.exit(1);
});
