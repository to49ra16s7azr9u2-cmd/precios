#!/usr/bin/env python3
"""Baja los productos de Reuse, Avera y Farmatodo y los deja en el formato de
captura que come importar_captura_tienda.py (id, title, price, photo, url,
store, dept, brand, listPrice).

POR QUÉ NO POR EL FEED
----------------------
Estas cuatro tiendas (DelSol, Reuse, Avera, Farmatodo) tienen programa en
Soicos con implementación «COMPARAMEX» (08-oct-2026), pero el feed de la API
pide credenciales que no viven en el repositorio. Los tres sitios que sí
publican su catálogo de forma abierta se leen directo:

  * Reuse y Avera son Shopify: /products.json (250 por página) es el catálogo
    público que la propia tienda sirve a sus temas. Sin cuenta, sin sesión.
  * DelSol es IBM WebSphere Commerce: sin API pública; cada página de
    categoría (las de su sitemap) trae el JSON de sus productos. Su robots.txt
    responde 400, es decir, no veda nada. Se pide una página por segundo.
  * Farmatodo es VTEX: /api/catalog_system/pub/products/search, la misma API
    que usa el sitio. Su robots.txt veda /busca/, /account/, /checkout/, etc.;
    la API no está entre ellos.

El enlace de afiliado se guarda envuelto (a diferencia de Elektra): la base
sale de afiliados.SOICOS_TIENDAS y el formato es el de siempre,
ad.soicos.com/-XXXX?dl=<url de la tienda codificada>. El importador deduplica
por la url real, así que lo ya cargado por el feed de Reuse (otra base, misma
url de reuse.mx) no se repite.

QUÉ NO ENTRA
------------
Alimentos, bebidas y medicamentos: Farmatodo es farmacia y súper, y el
comparador no tiene dónde ponerlos (ver FARMATODO_RAMAS). Lo demás lo decide
el clasificador por título.

USO
---
    python3 scripts/tiendas_soicos_a_captura.py reuse_mx   --salida /tmp/reuse.json
    python3 scripts/tiendas_soicos_a_captura.py avera      --salida /tmp/avera.json
    python3 scripts/tiendas_soicos_a_captura.py farmatodo  --salida /tmp/farmatodo.json
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from afiliados import SOICOS_TIENDAS  # noqa: E402

UA = "Mozilla/5.0 (compatible; ComparaMEX/1.0; +https://comparamex.mx)"
PAUSA = 0.4


def deeplink(tienda, url):
    return SOICOS_TIENDAS[tienda] + urllib.parse.quote(url, safe="")


def get(url, intentos=4):
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8"), r.headers
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if isinstance(e, urllib.error.HTTPError) and e.code in (400, 404):
                raise
            time.sleep(2 ** (i + 1))
    raise RuntimeError("sin respuesta: " + url)


def numero(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return v if v > 0 else None


# ---------------------------------------------------------------------------
# Shopify (Reuse, Avera)
# ---------------------------------------------------------------------------
SHOPIFY = {
    "reuse_mx": "https://www.reuse.mx",
    "avera": "https://avera.mx",
}


def limpiar_titulo(t):
    t = re.sub(r"\s+", " ", t or "").strip()
    return t.strip(':"\' ')


# Lo que estas tiendas venden además de productos: seguros, garantías
# extendidas y servicio técnico (Reuse: 705 de 936 «productos» eran seguros).
NO_PRODUCTO_TIPO = re.compile(r"seguro|garant|servicio|instalaci|wk_|env[ií]o|donaci", re.I)
NO_PRODUCTO_TITULO = re.compile(r"\b(seguro|garant[ií]a|servicio t[eé]cnico|instalaci[oó]n|p[oó]liza)\b", re.I)


def shopify(tienda):
    raiz = SHOPIFY[tienda]
    out, pagina, vistos = [], 1, set()
    while True:
        txt, _ = get(f"{raiz}/products.json?limit=250&page={pagina}")
        productos = json.loads(txt).get("products") or []
        if not productos:
            break
        for p in productos:
            if p["id"] in vistos:
                continue
            vistos.add(p["id"])
            titulo = limpiar_titulo(p.get("title"))
            vendor = (p.get("vendor") or "").strip()
            # La variante: la primera con existencia (casi todas son una sola,
            # «Default Title»).
            v = next((v for v in p.get("variants") or [] if v.get("available") and numero(v.get("price"))), None)
            if not titulo or not v:
                continue
            if NO_PRODUCTO_TIPO.search(p.get("product_type") or "") or NO_PRODUCTO_TITULO.search(titulo):
                continue
            marca = vendor if vendor and vendor.lower() not in ("none", "null", "n/a", "-") else ""
            # Avera escribe el nombre sin la marca: se antepone, para el que
            # lee la lista y para emparejarla con el mismo modelo de otra tienda.
            if marca and marca.lower() not in titulo.lower() and tienda == "avera":
                titulo = f"{marca} {titulo}"
            # Reuse sólo vende reacondicionados, aunque no todos los nombres lo
            # digan: se escribe, para que no se lea como nuevo ni se una con el
            # nuevo (mismo criterio que soicos_a_captura.item).
            if tienda == "reuse_mx" and not re.search(r"reacondicionad", titulo, re.I):
                titulo += " Reacondicionado"
            url = f"{raiz}/products/{p['handle']}"
            if len(p.get("variants") or []) > 1:
                url += f"?variant={v['id']}"
            elif tienda == "reuse_mx":
                # El feed de Soicos escribió las de Reuse con ?variant=: la
                # misma url, para que el importador las reconozca.
                url += f"?variant={v['id']}"
            precio, antes = numero(v["price"]), numero(v.get("compare_at_price"))
            foto = (p.get("images") or [{}])[0].get("src")
            it = {"store": tienda, "id": str(v["id"]), "title": titulo, "price": precio,
                  "photo": foto, "url": deeplink(tienda, url)}
            if antes and antes > precio:
                it["listPrice"] = antes
            if marca:
                it["brand"] = marca
            if p.get("product_type"):
                it["dept"] = p["product_type"]
            out.append(it)
        print(f"  {tienda}: página {pagina}, {len(out)} con existencia", flush=True)
        pagina += 1
        time.sleep(PAUSA)
    return out


# ---------------------------------------------------------------------------
# Farmatodo (VTEX)
# ---------------------------------------------------------------------------
FARMATODO = "https://www.farmatodo.com.mx"
# Ramas del árbol de Farmatodo que se recorren (id de categoría). Todo lo que
# no está acá --Medicamentos, Genéricos, Especialidades, Diabetes,
# Dermatología (fármacos), Abarrotes, Bebidas, Lácteos, Congelados, Despensa,
# fórmulas y alimentación infantil-- no se compara en el sitio.
FARMATODO_RAMAS = {
    315: "Cuidado personal y belleza",
    366: "Dermocosmética",
    163: "Bebés",
    254: "Farmacia (aparatos y accesorios)",
    223: "Suplementos y vitamínicos",
    686160: "Cuidado de la ropa",
    686202: "Limpieza del hogar",
}
# Dentro de las ramas: las que sí son medicina o comida.
FARMATODO_SIN = {
    168, 173,                                # alimentación del bebé y fórmulas
    278, 292, 301, 268, 264, 272,            # estomacales, dolor, gripe, salud femenina, ojos, bienestar sexual
}
# Productos que, por el nombre, siguen siendo medicamento o comida.
MEDICINA_RE = re.compile(
    r"\b(\d+ ?mg|\d+ ?mcg|tabletas? (recubiertas?|efervescentes?)|c[aá]psulas? blandas?|jarabe|ampolleta|"
    r"inyectable|suspensi[oó]n oral|soluci[oó]n oftalm|gotas oft|supositorio|ovulos?|[oó]vulos|"
    r"antibi[oó]tic|ibuprofeno|paracetamol|naproxeno|loratadina|omeprazol|metformina)\b", re.I)


# Departamentos de Farmatodo (el nivel más fino de su árbol) que son
# medicina, suero o alimento clínico aunque cuelguen de una rama que sí se
# recorre: no se comparan.
FARMATODO_DEPTO_FUERA = re.compile(
    r"soluciones salinas|nutricional|ginecolog|control metab|dermatitis|ung[uü]entos|pomadas|homeopat|"
    r"resfriado|antirreum|anticoagul|psoriasis|osteoartritis|antiobesidad|cicatrizante|calmante|probi[oó]tic|"
    r"cat[eé]ter|venoclisis|jeringas y agujas|vaso copro|antis[eé]pticos|cuidado de los ojos|material de curaci",
    re.I)


def vtex_pagina(fq, desde):
    url = (f"{FARMATODO}/api/catalog_system/pub/products/search?fq={urllib.parse.quote(fq, safe=':/')}"
           f"&_from={desde}&_to={desde + 49}")
    try:
        txt, h = get(url)
    except urllib.error.HTTPError as e:
        if e.code in (400, 404):
            return [], 0
        raise
    total = 0
    m = re.search(r"/(\d+)$", h.get("resources") or "")
    if m:
        total = int(m.group(1))
    return json.loads(txt), total


def hojas(nodo, ruta, salida):
    """Categorías hoja bajo `nodo`, saltando las excluidas."""
    if nodo["id"] in FARMATODO_SIN:
        return
    ruta = ruta + [nodo["id"]]
    hijos = nodo.get("children") or []
    if not hijos:
        salida.append(ruta)
    else:
        # Se pide el nodo entero si cabe en una consulta (2,500 máx. en VTEX)
        # y no tiene hijos excluidos; si no, se baja a las hojas.
        if any(h["id"] in FARMATODO_SIN for h in hijos):
            for h in hijos:
                hojas(h, ruta, salida)
        else:
            salida.append(ruta)


def producto_farmatodo(p, depto):
    if str(p.get("Controlado", [""])[0]).lower().startswith(("s", "1")):
        return None
    if str(p.get("Antibiotico", [""])[0]).lower().startswith(("s", "1")):
        return None
    titulo = limpiar_titulo(p.get("productName"))
    if not titulo or MEDICINA_RE.search(titulo) or FARMATODO_DEPTO_FUERA.search(depto):
        return None
    for it in p.get("items") or []:
        for s in it.get("sellers") or []:
            co = s.get("commertialOffer") or {}
            precio, lista = numero(co.get("Price")), numero(co.get("ListPrice"))
            if precio and (co.get("AvailableQuantity") or 0) > 0:
                imgs = it.get("images") or []
                foto = imgs[0]["imageUrl"] if imgs else None
                if foto:
                    foto = foto.split("?")[0]
                res = {"store": "farmatodo", "id": str(p["productId"]), "title": titulo, "price": precio,
                       "photo": foto, "url": deeplink("farmatodo", p["link"].split("?")[0]), "dept": depto}
                if lista and lista > precio:
                    res["listPrice"] = lista
                marca = (p.get("brand") or "").strip()
                if marca and marca.lower() not in ("none", "null", "n/a", "-", "genérico", "generico"):
                    res["brand"] = marca
                ean = re.sub(r"\D", "", str(it.get("ean") or ""))
                if 8 <= len(ean) <= 14:
                    res["gtin"] = ean
                return res
    return None


def farmatodo():
    txt, _ = get(f"{FARMATODO}/api/catalog_system/pub/category/tree/3")
    arbol = {n["id"]: n for n in json.loads(txt)}
    consultas = []
    for rid in FARMATODO_RAMAS:
        if rid in arbol:
            hojas(arbol[rid], [], consultas)
    print(f"  farmatodo: {len(consultas)} consultas de categoría", flush=True)
    out, vistos = [], set()
    for ruta in consultas:
        fq = "C:/" + "/".join(str(i) for i in ruta) + "/"
        desde = 0
        while desde < 2500:
            prods, total = vtex_pagina(fq, desde)
            if not prods:
                break
            for p in prods:
                if p["productId"] in vistos:
                    continue
                vistos.add(p["productId"])
                depto = (p.get("categories") or ["/"])[0].strip("/").split("/")[-1]
                it = producto_farmatodo(p, depto)
                if it:
                    out.append(it)
            desde += 50
            time.sleep(PAUSA)
        print(f"  {fq}: {len(vistos)} vistos, {len(out)} guardados", flush=True)
    return out


# ---------------------------------------------------------------------------
# DelSol (IBM WebSphere Commerce)
# ---------------------------------------------------------------------------
DELSOL = "https://www.delsol.com.mx"
# Departamentos del sitemap de DelSol que se recorren. Ropa (mujer, hombre,
# infantiles), dulcería y farmacia no se comparan en el sitio; telefonía y
# outlet no tienen sitemap público de categorías (403) o repiten los demás.
DELSOL_SITEMAPS = ["electronica", "hogar", "jugueteria", "bebes", "deportivo",
                   "escolarypapeleria", "bellezaycuidadopersonal"]
RX_LOC = re.compile(r"<loc>([^<]+)</loc>")
RX_PROD = re.compile(r"var m = (\{.*?\});\s*\n\s*m\.pathCategory", re.S)
RX_ENLACE = re.compile(r'id="catalogEntry_img(\d+)"\s+href="([^"]+)"')


def delsol_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read().decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:
            if e.code in (400, 403, 404):
                return ""
            time.sleep(2 ** (i + 1))
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            time.sleep(2 ** (i + 1))
    return ""


def delsol_categorias():
    """Urls de categoría de los sitemaps (que se anidan dos niveles)."""
    hojas, vistas = [], set()
    pendientes = [f"{DELSOL}/sitemap/sitemap_{n}.xml" for n in DELSOL_SITEMAPS]
    while pendientes:
        u = pendientes.pop()
        txt = delsol_get(u)
        time.sleep(PAUSA)
        for loc in RX_LOC.findall(txt):
            if loc in vistas:
                continue
            vistas.add(loc)
            if loc.endswith(".xml"):
                pendientes.append(loc)
            else:
                hojas.append(loc)
    return sorted(hojas)


def delsol_producto(d, enlace, depto):
    if str(d.get("buyable")) != "true" or depto.lower().startswith("ropa"):
        return None
    skus = d.get("sKUs") or []
    precios = []
    for fuente in [d] + skus:
        for p in fuente.get("price") or []:
            if p.get("usage") == "Offer" and numero(p.get("value")):
                precios.append(numero(p["value"]))
    lista = [numero(p.get("value")) for p in d.get("price") or [] if p.get("usage") == "Display"]
    titulo = limpiar_titulo(re.sub(r"\s+", " ", d.get("name") or ""))
    if not precios or not titulo:
        return None
    precio = min(precios)
    it = {"store": "delsol", "id": str(d["uniqueID"]), "title": titulo, "price": precio,
          "photo": d.get("thumbnail") or None, "url": deeplink("delsol", enlace), "dept": depto}
    if lista and lista[0] and lista[0] > precio:
        it["listPrice"] = lista[0]
    marca = (d.get("manufacturer") or "").strip()
    if marca and marca.lower() not in ("none", "null", "n/a", "-", "generico", "genérico"):
        it["brand"] = marca
    return it


def delsol():
    cats = delsol_categorias()
    print(f"  delsol: {len(cats)} categorías", flush=True)
    out, vistos = [], set()
    for cat in cats:
        depto = urllib.parse.unquote(cat.rstrip("/").split("/")[-1])
        depto = re.sub(r"-\d+$", "", depto)
        base = urllib.parse.quote(cat, safe=":/")
        desde, ant = 0, len(vistos)
        while True:
            h = delsol_get(f"{base}?pageSize=48&pageView=grid&beginIndex={desde}")
            time.sleep(PAUSA)
            enlaces = {i: u for i, u in RX_ENLACE.findall(h)}
            nuevos = 0
            for blob in RX_PROD.findall(h):
                try:
                    d = json.loads(blob)
                except ValueError:
                    continue
                uid = str(d.get("uniqueID"))
                if uid in vistos or uid not in enlaces:
                    continue
                vistos.add(uid)
                nuevos += 1
                it = delsol_producto(d, enlaces[uid], depto)
                if it:
                    out.append(it)
            if len(enlaces) < 48 or not nuevos:
                break
            desde += 48
        if len(vistos) > ant:
            print(f"  {depto}: +{len(vistos) - ant} (total {len(vistos)}, guardados {len(out)})", flush=True)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tienda", choices=["reuse_mx", "avera", "farmatodo", "delsol"])
    ap.add_argument("--salida", required=True)
    args = ap.parse_args()
    items = {"farmatodo": farmatodo, "delsol": delsol}[args.tienda]() if args.tienda in ("farmatodo", "delsol") \
        else shopify(args.tienda)
    with open(args.salida, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    print(f"{args.tienda}: {len(items)} productos -> {args.salida}")


if __name__ == "__main__":
    main()
