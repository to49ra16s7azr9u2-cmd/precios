#!/usr/bin/env python3
"""Baja el logo de cada marca con página propia a icons/marcas/<slug>.png.

DE DÓNDE SALEN
--------------
De Wikidata: cada marca con artículo tiene ahí su logo (propiedad P154, un
archivo de Wikimedia Commons) y, muchas veces, su sitio oficial (P856). Se
pregunta por el nombre de la marca en español e inglés, con las grafías
que suele haber (Asus/ASUS), y se exige que la entidad TENGA logo: eso deja
fuera a "Acer" el arce y a "Apple" la fruta sin listas a mano. Si varias
entidades cumplen, gana la que tiene más artículos en Wikipedias, que es
la conocida. La consulta es una sola por tanda (SPARQL), no una por marca:
la API de Wikipedia limita por IP y desde este entorno ya contesta 429.

El archivo se baja de Commons ya reducido (ancho 320) en PNG, que conserva
la transparencia de los logos en SVG.

Para las marcas que Wikidata no conoce (fabricantes mexicanos chicos, marcas
blancas de las tiendas) queda el icono del sitio oficial cuando Wikidata lo
da o cuando <slug>.com / .com.mx / .mx contesta y su <title> nombra a la
marca; es el servicio de favicons de Google, a 128 px. Un dominio adivinado
sin esa comprobación sería de cualquiera, y un logo ajeno es peor que
ninguno.

QUÉ GUARDA
----------
data/marcas-logos.json: {clave de marca: {"archivo": "slug.png", "fuente":
"wikidata"|"favicon", "origen": url}} y, para las que no se encontraron,
{"archivo": null}. Es la memoria entre corridas: lo ya resuelto no se vuelve
a pedir, y sirve para corregir a mano (poner "archivo": null a un logo mal
resuelto, o "origen" con el archivo bueno y borrar "archivo" para que lo
vuelva a bajar).

USO
---
    python3 scripts/build_marcas_logos.py --dry-run          # qué encontraría
    python3 scripts/build_marcas_logos.py                    # todo
    python3 scripts/build_marcas_logos.py --limit 100        # las 100 más grandes
    python3 scripts/build_marcas_logos.py --solo "Spring Air" --reintentar
"""
import argparse
import io
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from data_io import load_catalog  # noqa: E402
from generate_seo_pages import clave_marca, marcas_con_pagina  # noqa: E402

ROOT = os.path.dirname(AQUI)
CARPETA = os.path.join(ROOT, "icons", "marcas")
MEMORIA = os.path.join(ROOT, "data", "marcas-logos.json")
UA = "ComparaMEX-logos/1.0 (https://comparamex.com; comparador de precios de México)"
SPARQL = "https://query.wikidata.org/sparql"
ANCHO = 320
TANDA = 25          # marcas por consulta SPARQL (la búsqueda tarda ~0.5 s por marca)
PAUSA_COMMONS = 1.5  # segundos entre bajadas de Commons (a 0.4 s contestó 429)


def pedir(url, timeout=60, headers=None, datos=None):
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h, data=datos)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get("Content-Type", ""), r.geturl()


# Marcas cuyo nombre es ambiguo y se resuelven a mano (nombre -> entidad de
# Wikidata). Vale más una lista corta y cierta que una heurística larga.
OVERRIDES = {
    "playstation": "Q10677",   # el primer resultado es la PS3; se prefiere la marca
    "apple": "Q312",           # Apple Inc.: su alias es "Apple (company)", no "Apple"
    "disney": "Q7414",         # The Walt Disney Company, no Disney+ ni Disney Channel
    "motorola": "Q634815",     # Motorola (la empresa), no el equipo ciclista
    "invicta": None,           # Wikidata tiene "Invicta italy" y una automotriz británica; la relojera (Q6060981) no tiene logo
    "marvel": "Q173496",       # Marvel Comics, no el universo cinematográfico
    "bgs": None,               # herramientas BGS technic; Wikidata solo conoce a Bethesda
}

# Marcas que se revisaron a ojo el 19 de septiembre de 2026 y cuyo logo
# automático era de otra cosa (Kaiser -> la aseguradora, Mega -> un banco
# indonesio, Pioneer -> un videojuego, Milwaukee -> una bandera...). Ni
# Wikidata ni el favicon: se quedan con las iniciales hasta que alguien
# ponga el archivo a mano en icons/marcas/ y lo anote en marcas-logos.json.
SIN_LOGO = {
    "invicta",
    "america",
    "icon",
    "kaiser",
    "alfa",
    "milwaukee",
    "rhino",
    "standard",
    "hr",
    "akrapovic",
    "continental",
    "dbebe",
    "blink",
    "perfectchoice",
    "providencia",
    "remington",
    "concord",
    "california",
    "timco",
    "aztron",
    "mega",
    "onepiece",
    "dash",
    "pegaso",
    "impercaucho",
    "giorgio",
    "goliath",
    "delta",
    "eko",
    "pure",
    "carmin",
    "cayro",
    "pioneer",
    "promo",
    "man",
    "planet",
    "breville",
    "spar",
    "sol",
    "bellagio",
    "insignia",
    "gravita",
    "atm",
    "brunos",
    "crosley",
    "red",
    "navien",
    "mac",
}

# Clases (P31) que dicen "esto es una empresa o una marca". Con una de estas
# el candidato entra aunque no tenga descripción.
CLASES_EMPRESA = {
    "Q4830453", "Q6881511", "Q891723", "Q783794", "Q1589009", "Q658255",   # empresa, pública, privada, filial
    "Q431289", "Q167270", "Q18388277", "Q1058914", "Q1637706",             # marca, marca registrada, tecnológica, software, fabricante
    "Q10929058", "Q62008942", "Q2424752", "Q15401930",                     # consolas y productos
}
# Sin clase de empresa, la descripción tiene que hablar de una: así se van
# el equipo ciclista "Motorola", el buscador "Base" y el lenguaje "Icon".
RX_EMPRESA = re.compile(r"empresa|compa[nñ][ií]a|fabricante|marca|corporaci|conglomerado|franquicia|consola|"
                        r"juguete|producto|cadena|tienda|minorista|videojuego|company|brand|manufacturer|"
                        r"corporation|franchise|product|console|toy|retailer|chain|maker", re.I)
# "Apple Inc." se llama como la marca: los apellidos societarios no cuentan.
RX_SUFIJO = re.compile(r"[\s,]+(inc\.?|corp\.?|corporation|company|co\.?|ltd\.?|limited|s\.?a\.?(?: de c\.?v\.?)?|"
                       r"gmbh|llc|plc|group|grupo|international|de m[eé]xico|m[eé]xico|brands|holdings|"
                       r"technolog(y|ies)|electronics|industries|innovations|solutions|mobility)$", re.I)

# Clases (P31) que no son una marca aunque lleven logo: ciudades, cortes,
# clubes, universidades, canales... Los homónimos vienen de ahí.
CLASES_EXCLUIDAS = {
    "Q515", "Q3957", "Q486972", "Q1549591", "Q15284", "Q532", "Q7930989", "Q56061", "Q134626",  # ciudad, pueblo, municipio
    "Q6256", "Q7275", "Q10864048",                      # país, estado, división administrativa
    "Q41487", "Q190752", "Q895914",                     # cortes
    "Q476028", "Q847017", "Q4438121", "Q12973014",      # clubes y equipos deportivos
    "Q3918", "Q875538", "Q2385804", "Q38723",           # universidades y escuelas
    "Q1616075", "Q1254874", "Q15265344", "Q1762059",    # canales y emisoras
    "Q7278", "Q327333", "Q2659904",                     # partidos y agencias de gobierno
    "Q33506", "Q3196771", "Q207694",                    # museos
    "Q46970", "Q18127", "Q5", "Q215380", "Q11424", "Q482994", "Q5398426", "Q1667921",  # aerolíneas, sellos, personas, bandas, obras
    "Q16521", "Q288514", "Q1002697", "Q11032", "Q41298",  # taxón, convención, periódico, revista
}


def normal(s):
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower())


def sin_sufijo(etiqueta):
    e = etiqueta.strip()
    for _ in range(2):
        e = RX_SUFIJO.sub("", e)
    return e


def por_que_no(nombre, c):
    """Motivo por el que un candidato no sirve, o None si sirve."""
    orden, qid, logo, web, enl, desc, clases, etiquetas = c
    n = normal(nombre)
    if clases & CLASES_EXCLUIDAS:
        return "clase excluida"
    if not any(normal(e) == n or normal(sin_sufijo(e)) == n for e in etiquetas):
        return "no se llama así"
    if not (clases & CLASES_EMPRESA) and not RX_EMPRESA.search(desc or ""):
        return "no parece empresa: " + (desc[:40] or "sin descripción")
    return None


def buscar_wikidata(nombres, idioma):
    """{nombre: [(orden, qid, logo, web, sitelinks, descripción, clases, etiquetas)]}
    con la búsqueda de entidades de Wikidata (la misma del buscador de su
    sitio) corrida dentro de SPARQL: una consulta por tanda, no por marca."""
    esc = lambda t: t.replace("\\", "\\\\").replace('"', '\\"')  # noqa: E731
    valores = " ".join(f'"{esc(n)}"' for n in nombres)
    q = f"""
SELECT ?q ?ord ?item ?logo ?web ?enl ?d
       (GROUP_CONCAT(DISTINCT ?cl; separator=",") AS ?clases)
       (GROUP_CONCAT(DISTINCT ?et; separator="|") AS ?etiquetas) WHERE {{
  VALUES ?q {{ {valores} }}
  SERVICE wikibase:mwapi {{
    bd:serviceParam wikibase:api "EntitySearch"; wikibase:endpoint "www.wikidata.org";
                    mwapi:search ?q; mwapi:language "{idioma}"; mwapi:limit "8" .
    ?item wikibase:apiOutputItem mwapi:item . ?ord wikibase:apiOrdinal true .
  }}
  ?item wdt:P154 ?logo .
  OPTIONAL {{ ?item wdt:P856 ?web }}
  OPTIONAL {{ ?item wikibase:sitelinks ?enl }}
  OPTIONAL {{ ?item schema:description ?d FILTER(LANG(?d) = "{idioma}") }}
  OPTIONAL {{ ?item wdt:P31 ?cl }}
  OPTIONAL {{ {{ ?item rdfs:label ?et }} UNION {{ ?item skos:altLabel ?et }} FILTER(LANG(?et) IN ("es", "en")) }}
}} GROUP BY ?q ?ord ?item ?logo ?web ?enl ?d ORDER BY ?q ?ord"""
    datos = urllib.parse.urlencode({"query": q}).encode()
    for intento in range(4):
        try:
            cuerpo, _, _ = pedir(SPARQL, timeout=180, headers={"Accept": "application/sparql-results+json",
                                                              "Content-Type": "application/x-www-form-urlencoded"}, datos=datos)
            break
        except Exception:  # noqa: BLE001
            if intento == 3:
                raise
            time.sleep(15 * (intento + 1))
    out = {}
    for b in json.loads(cuerpo)["results"]["bindings"]:
        g = lambda k: b.get(k, {}).get("value", "")  # noqa: E731
        out.setdefault(g("q"), []).append((
            int(g("ord") or 0), g("item").rsplit("/", 1)[-1], g("logo"), g("web") or None, int(g("enl") or 0),
            g("d"), {c.rsplit("/", 1)[-1] for c in g("clases").split(",") if c}, [e for e in g("etiquetas").split("|") if e],
        ))
    return out


def elegir(nombre, candidatos):
    """El primer candidato que se llama como la marca y no es una ciudad,
    una corte, un club... La búsqueda ya viene ordenada por relevancia."""
    # Una entidad puede tener varios logos (Apple: uno blanco y uno negro);
    # sobre fondo blanco el blanco no se ve, así que va al final.
    for c in sorted(candidatos, key=lambda c: (c[0], "white" in c[2].lower() or "blanco" in c[2].lower(), -c[4])):
        if por_que_no(nombre, c) is None:
            orden, qid, logo, web, enl, desc, clases, etiquetas = c
            return {"qid": qid, "logo": logo, "web": web, "wikis": enl, "desc": desc}
    return None


def por_qid(qids):
    """{qid: (logo, web, desc)} para los overrides."""
    valores = " ".join(f"wd:{q}" for q in qids)
    q = f"""SELECT ?item ?logo ?web ?d WHERE {{ VALUES ?item {{ {valores} }} ?item wdt:P154 ?logo .
      OPTIONAL {{ ?item wdt:P856 ?web }} OPTIONAL {{ ?item schema:description ?d FILTER(LANG(?d) = "es") }} }}"""
    datos = urllib.parse.urlencode({"query": q}).encode()
    cuerpo, _, _ = pedir(SPARQL, timeout=120, headers={"Accept": "application/sparql-results+json",
                                                      "Content-Type": "application/x-www-form-urlencoded"}, datos=datos)
    out = {}
    for b in json.loads(cuerpo)["results"]["bindings"]:
        g = lambda k: b.get(k, {}).get("value", "")  # noqa: E731
        qid = g("item").rsplit("/", 1)[-1]
        if qid in out and not ("white" in out[qid][0].lower() or "blanco" in out[qid][0].lower()):
            continue
        out[qid] = (g("logo"), g("web") or None, g("d"))
    return out


def bajar_logo(url, destino):
    """Baja el archivo de Commons reducido a PNG. True si quedó escrito."""
    # Special:FilePath acepta ?width= y devuelve la miniatura (PNG para SVG).
    u = url.replace("http://", "https://")
    u += ("&" if "?" in u else "?") + f"width={ANCHO}"
    try:
        cuerpo, tipo, _ = pedir(u, timeout=60)
    except Exception as e:  # noqa: BLE001
        print(f"    no se pudo bajar {url}: {e}", file=sys.stderr)
        return False
    if not tipo.startswith("image/") or len(cuerpo) < 200:
        return False
    if "png" not in tipo:
        cuerpo = a_png(cuerpo)
        if not cuerpo:
            return False
    with open(destino, "wb") as f:
        f.write(cuerpo)
    return True


def a_png(cuerpo):
    """JPG/GIF/WebP -> PNG del mismo ancho, para que todo sea .png."""
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(cuerpo)).convert("RGBA")
        if im.width > ANCHO:
            im = im.resize((ANCHO, max(1, round(im.height * ANCHO / im.width))))
        out = io.BytesIO()
        im.save(out, "PNG", optimize=True)
        return out.getvalue()
    except Exception:  # noqa: BLE001
        return None


def sin_acentos(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def dominio_valido(dominio, nombre):
    """El sitio existe y su <title> u og:site_name nombra a la marca."""
    try:
        cuerpo, tipo, final = pedir(f"https://{dominio}/", timeout=20)
    except Exception:  # noqa: BLE001
        return False
    if "html" not in tipo:
        return False
    html = cuerpo[:200000].decode("utf-8", "ignore")
    m = re.search(r"<title[^>]*>([^<]{0,200})", html, re.I)
    og = re.search(r'property=["\']og:site_name["\'][^>]*content=["\']([^"\']{0,120})', html, re.I)
    textos = sin_acentos((m.group(1) if m else "") + " " + (og.group(1) if og else ""))
    clave = re.sub(r"[^a-z0-9]", "", sin_acentos(nombre))
    return bool(clave) and clave in re.sub(r"[^a-z0-9]", "", textos)


FAVICON_VACIO = None


def bajar_favicon(dominio, destino):
    """El icono del sitio vía Google (hasta 128 px). False si es el genérico."""
    global FAVICON_VACIO
    try:
        cuerpo, tipo, _ = pedir(f"https://www.google.com/s2/favicons?domain={dominio}&sz=128", timeout=30)
    except Exception:  # noqa: BLE001
        return False
    if FAVICON_VACIO is None:
        try:
            FAVICON_VACIO, _, _ = pedir("https://www.google.com/s2/favicons?domain=dominio-que-no-existe-xyz.invalid&sz=128", timeout=30)
        except Exception:  # noqa: BLE001
            FAVICON_VACIO = b""
    if not tipo.startswith("image/") or cuerpo == FAVICON_VACIO or len(cuerpo) < 300:
        return False
    png = a_png(cuerpo) if "png" not in tipo else cuerpo
    if not png:
        return False
    with open(destino, "wb") as f:
        f.write(png)
    return True


def dominios_candidatos(nombre, slug, web):
    out = []
    if web:
        d = urllib.parse.urlparse(web).netloc.lower()
        if d:
            out.append(d)
    base = re.sub(r"[^a-z0-9]", "", sin_acentos(nombre))
    for d in (f"{base}.com.mx", f"{base}.mx", f"{base}.com", f"{slug}.com.mx", f"{slug}.mx", f"{slug}.com"):
        if d not in out:
            out.append(d)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="consultar Wikidata y decir qué haría, sin bajar nada")
    ap.add_argument("--limit", type=int, default=None, help="solo las N marcas con más productos")
    ap.add_argument("--solo", action="append", default=[], help="solo esta marca (se puede repetir)")
    ap.add_argument("--reintentar", action="store_true", help="volver a buscar las que quedaron sin logo")
    ap.add_argument("--sin-favicon", action="store_true", help="no probar el icono del sitio oficial")
    args = ap.parse_args()

    marcas = marcas_con_pagina(load_catalog())
    if args.solo:
        quiero = {clave_marca(s) for s in args.solo}
        marcas = [m for m in marcas if clave_marca(m[0]) in quiero]
    if args.limit:
        marcas = marcas[:args.limit]
    memoria = json.load(io.open(MEMORIA, encoding="utf-8")) if os.path.exists(MEMORIA) else {}
    os.makedirs(CARPETA, exist_ok=True)

    pendientes = []
    for nombre, slug, items in marcas:
        k = clave_marca(nombre)
        if k in SIN_LOGO:
            memoria[k] = {"archivo": None, "nota": "revisada a ojo: el logo automático era de otra cosa"}
            continue
        m = memoria.get(k)
        if m and m.get("archivo") and os.path.exists(os.path.join(CARPETA, m["archivo"])):
            # Con --reintentar, un favicon se vuelve a intentar por Wikidata:
            # el logo de verdad vale más que el icono del sitio.
            if not (args.reintentar and m.get("fuente") == "favicon"):
                continue
        if m and m.get("archivo") is None and "origen" not in m and not args.reintentar:
            continue   # ya se buscó y no hay; --reintentar lo vuelve a intentar
        pendientes.append((nombre, slug, k, len(items)))
    con_logo = sum(1 for nombre, _s, _i in marcas if (memoria.get(clave_marca(nombre)) or {}).get("archivo"))
    print(f"Marcas con página: {len(marcas)}   con logo ya: {con_logo}   a buscar: {len(pendientes)}")
    if not pendientes:
        return

    # 1. Wikidata, por tandas: primero en español, lo que falte en inglés
    encontrados, rechazados = {}, {}
    forzados = {k: q for k, q in OVERRIDES.items() if q}
    # None en OVERRIDES: no buscar en Wikidata (lo que hay ahí es otra cosa),
    # pero sí probar el icono del sitio oficial.
    vetados = {k for k, q in OVERRIDES.items() if not q}
    try:
        fijos = por_qid(sorted(set(forzados.values()))) if forzados else {}
    except Exception as e:  # noqa: BLE001
        print(f"  no se pudieron leer los overrides: {e}", file=sys.stderr)
        fijos = {}
    for nombre, slug, k, n in pendientes:
        if k in forzados and forzados[k] in fijos:
            logo, web, desc = fijos[forzados[k]]
            encontrados[nombre] = {"qid": forzados[k], "logo": logo, "web": web, "wikis": 0, "desc": desc}
    for idioma in ("es", "en"):
        faltan = [n for n, _s, k, _c in pendientes if n not in encontrados and k not in vetados]
        for i in range(0, len(faltan), TANDA):
            tanda = faltan[i:i + TANDA]
            try:
                r = buscar_wikidata(tanda, idioma)
            except Exception as e:  # noqa: BLE001
                print(f"  la búsqueda ({idioma}) falló en la tanda {i // TANDA + 1}: {e}", file=sys.stderr)
                r = {}
            hechos = 0
            for nombre in tanda:
                rechazados.setdefault(nombre, []).extend(r.get(nombre, []))
                e = elegir(nombre, r.get(nombre, []))
                if e:
                    encontrados[nombre] = e
                    hechos += 1
            print(f"  Wikidata ({idioma}) tanda {i // TANDA + 1}/{(len(faltan) + TANDA - 1) // TANDA}: {hechos} de {len(tanda)}")
            time.sleep(1.0)

    # 2. bajar de Commons (en serie, con pausa: es un solo origen)
    bajados, fallidos = 0, []
    for nombre, slug, k, n in pendientes:
        hit = encontrados.get(nombre)
        if not hit:
            fallidos.append((nombre, slug, k, None))
            continue
        logo, web, qid, desc = hit["logo"], hit["web"], hit["qid"], hit["desc"]
        destino = os.path.join(CARPETA, slug + ".png")
        if args.dry_run:
            print(f"  {nombre:28} {qid:11} {desc[:44]:44} | {urllib.parse.unquote(logo).rsplit('/', 1)[-1][:40]}")
            continue
        if bajar_logo(logo, destino):
            memoria[k] = {"archivo": slug + ".png", "fuente": "wikidata", "origen": logo, "qid": qid, "web": web, "desc": desc}
            bajados += 1
        else:
            fallidos.append((nombre, slug, k, web))
        time.sleep(PAUSA_COMMONS)
    print(f"\nWikidata: {bajados} logos bajados; sin logo ahí: {len(fallidos)}")

    # 3. el icono del sitio oficial, validando el dominio
    fav = 0
    if not args.sin_favicon and not args.dry_run:
        def intentar(t):
            nombre, slug, k, web = t
            for d in dominios_candidatos(nombre, slug, web):
                if (web and d == urllib.parse.urlparse(web).netloc.lower()) or dominio_valido(d, nombre):
                    if bajar_favicon(d, os.path.join(CARPETA, slug + ".png")):
                        return k, {"archivo": slug + ".png", "fuente": "favicon", "origen": f"https://{d}/"}
            return k, {"archivo": None}
        # Lo que ya tenía favicon y no consiguió logo en Wikidata se queda como estaba.
        fallidos = [t for t in fallidos if (memoria.get(t[2]) or {}).get("fuente") != "favicon"]
        with ThreadPoolExecutor(max_workers=6) as ex:
            for k, m in ex.map(intentar, fallidos):
                memoria[k] = m
                fav += bool(m.get("archivo"))
        print(f"Favicon del sitio oficial: {fav}   sin logo: {len(fallidos) - fav}")
    elif args.dry_run:
        for nombre, _, _, _ in fallidos:
            razones = "; ".join(f"{c[1]} {por_que_no(nombre, c)}" for c in sorted(rechazados.get(nombre, []))[:2])
            print(f"  sin logo en Wikidata: {nombre:28} {razones}")

    if not args.dry_run:
        json.dump(memoria, io.open(MEMORIA, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
        con = sum(1 for nombre, _s, _i in marcas if (memoria.get(clave_marca(nombre)) or {}).get("archivo"))
        print(f"\nGuardado {MEMORIA}: {con} de {len(marcas)} marcas con logo en icons/marcas/")


if __name__ == "__main__":
    main()
