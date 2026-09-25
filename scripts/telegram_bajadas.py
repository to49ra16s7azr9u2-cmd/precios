#!/usr/bin/env python3
"""Publica en un canal de Telegram los productos que bajaron de precio
(pedido del usuario, 26-sep-2026: traer visitas por otro camino que no sea
el buscador).

QUÉ PUBLICA
-----------
Las mismas bajadas que /ofertas/ (generate_seo_pages.bajada_de: dentro de
una misma tienda y un mismo vendedor, sostenidas 2 días, de 10% o más),
con dos filtros más para que el canal no sea ruido:
  - la ficha tiene página propia en el sitio (el enlace lleva a
    comparamex.com/producto/<id>/, donde se comparan las tiendas);
  - bajó al menos PCT_MINIMO y cuesta al menos PRECIO_MINIMO.
De esas, las MAX_POR_CORRIDA más populares que todavía no se publicaron.
Lo publicado queda en data/telegram-publicados.json (id -> día de la
bajada): la misma bajada no se repite; una bajada nueva del mismo
producto, sí.

CUÁNDO CORRERLO
---------------
DESPUÉS de publicar el sitio (git push), para que el enlace ya exista:

    set -a; . /ruta/fuera/del/repo/telegram.env; set +a
    python3 scripts/telegram_bajadas.py --enviar

Sin --enviar solo muestra los mensajes (prueba). Tras enviar hay que
commitear data/telegram-publicados.json con el siguiente cambio del sitio.

CREDENCIALES (NO VAN AL REPOSITORIO)
------------------------------------
TELEGRAM_BOT_TOKEN  el token que da @BotFather.
TELEGRAM_CHAT_ID    el canal, p. ej. @comparamex_ofertas (el bot tiene que
                    ser administrador del canal con permiso de publicar).
"""
import argparse
import html
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)

REGISTRO = os.path.join(ROOT, "data", "telegram-publicados.json")
PCT_MINIMO = 15.0
PRECIO_MINIMO = 300
MAX_POR_CORRIDA = 12
PAUSA_S = 4          # Telegram: un canal aguanta ~20 mensajes por minuto
API = "https://api.telegram.org/bot{token}/{metodo}"


def money(n):
    return "$" + f"{n:,.0f}"


def candidatos(data):
    import generate_seo_pages as G
    tiendas = {s["id"]: s.get("name") or s["id"] for s in data.get("stores") or []}
    nombres_cat = {c["id"]: c["name"] for c in data["categories"]}
    out = []
    for p in data["products"]:
        b = G.bajada_de(p["id"])
        if not b:
            continue
        pct, tienda, antes, ahora, dia = b
        if pct < PCT_MINIMO or ahora < PRECIO_MINIMO:
            continue
        if not os.path.isfile(os.path.join(ROOT, "producto", p["id"], "index.html")):
            continue
        out.append({
            "id": p["id"], "dia": dia, "pct": pct, "antes": antes, "ahora": ahora,
            "tienda": tiendas.get(tienda, tienda), "nombre": p.get("name") or "",
            "categoria": nombres_cat.get(p.get("category"), p.get("category") or ""),
            "foto": G.miniatura(p.get("photo") or "", 600) if p.get("photo") else "",
            # Popular = más reseñas y más tiendas, como el resto del sitio.
            "popularidad": (G.total_review_count(p), G.seller_total(p)),
        })
    out.sort(key=lambda c: (c["popularidad"], c["pct"]), reverse=True)
    return out


def mensaje(c):
    etiqueta = "".join(ch for ch in c["categoria"].title() if ch.isalnum())
    return (
        f"📉 <b>{html.escape(c['nombre'][:180])}</b>\n"
        f"Antes {money(c['antes'])} → <b>ahora {money(c['ahora'])}</b> "
        f"(−{c['pct']:.0f}%) en {html.escape(c['tienda'])}\n\n"
        f"Compara precios en otras tiendas:\n"
        f"https://comparamex.com/producto/{c['id']}/\n\n"
        f"#Ofertas #{etiqueta}\n"
        f"<i>Enlaces de afiliado: podemos recibir una comisión, sin costo para ti.</i>"
    )


def llamar(token, metodo, params):
    datos = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(API.format(token=token, metodo=metodo), data=datos)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def enviar(token, chat, c):
    texto = mensaje(c)
    if c["foto"] and len(texto) <= 1024:
        try:
            return llamar(token, "sendPhoto", {"chat_id": chat, "photo": c["foto"],
                                               "caption": texto, "parse_mode": "HTML"})
        except urllib.error.HTTPError:
            pass          # Telegram no pudo bajar la foto: va solo el texto
    return llamar(token, "sendMessage", {"chat_id": chat, "text": texto, "parse_mode": "HTML"})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--enviar", action="store_true", help="publicar de verdad (sin esto, solo muestra)")
    ap.add_argument("--max", type=int, default=MAX_POR_CORRIDA)
    args = ap.parse_args()

    from data_io import load_catalog
    data = load_catalog()
    registro = json.load(open(REGISTRO, encoding="utf-8")) if os.path.isfile(REGISTRO) else {}
    todos = candidatos(data)
    nuevos = [c for c in todos if registro.get(c["id"]) != c["dia"]][:args.max]
    print(f"bajadas publicables: {len(todos):,}; nuevas en esta corrida: {len(nuevos)}")

    if not args.enviar:
        for c in nuevos:
            print("-" * 60)
            print(mensaje(c))
        return

    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        sys.exit("faltan TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID")
    enviados = 0
    for c in nuevos:
        try:
            r = enviar(token, chat, c)
        except urllib.error.HTTPError as e:
            print(f"error {e.code} con {c['id']}: {e.read()[:200]!r}")
            break
        if not r.get("ok"):
            print(f"Telegram rechazó {c['id']}: {r}")
            break
        registro[c["id"]] = c["dia"]
        enviados += 1
        time.sleep(PAUSA_S)
    with open(REGISTRO, "w", encoding="utf-8") as f:
        json.dump(registro, f, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    print(f"publicados: {enviados}")


if __name__ == "__main__":
    main()
