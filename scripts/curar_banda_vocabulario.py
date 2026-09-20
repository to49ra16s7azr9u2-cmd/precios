"""Deja pasar del informe de vocabulario solo los pares origen->destino que
se revisaron a mano y salieron bien, por banda de ventaja.

Los errores del auditor no están repartidos al azar: se agrupan por par.
"Refacciones -> Electrodomésticos" está mal SIEMPRE (la bandeja de repuesto
de una freidora sí es una refacción), y "Muebles -> Juegos de mesa" está
bien siempre. Por eso la revisión es por par y no por ficha.

Cuanto más abajo la banda, menos pares sobreviven: en 9-15 pasaron 19 y en
3-9 solo 8. Abajo de 3 no se revisó: el auditor ahí ya no distingue.
"""
import collections, csv, json, re, sys

# (origen, destino): None = pasa todo; regex = tiene que NO cumplirla
ACEPTADOS_9_15 = {
    ('Muebles', 'Blancos y ropa de cama'): None,
    ('Muebles', 'Juegos de mesa'): None,
    ('Muebles', 'Equipo comercial'): None,
    ('Muebles', 'Deportes y fitness'): None,
    ('Muebles', 'Iluminación'): None,
    ('Muebles', 'Otros'): None,
    ('Muebles', 'Almacenamiento'): None,
    ('Muebles', 'Juguetes y bebés'): None,
    ('Autos, bicicletas y motos', 'Deportes y fitness'): None,
    ('Autos, bicicletas y motos', 'Almacenamiento'): None,
    ('Autos, bicicletas y motos', 'Cámaras y fotografía'): None,
    ('Herramientas', 'Equipo comercial'): None,
    ('Herramientas', 'Otros'): None,
    ('Fitness', 'Deportes y fitness'): None,
    ('Bocinas', 'Instrumentos musicales'): None,
    ('Otros', 'Muebles'): None,
    # Mixtos: se salva la parte buena con un filtro.
    # Sin la palabra "inteligente" son cerraduras y componentes sueltos, que
    # ya tienen su lugar en Herramientas.
    ('Herramientas', 'Domótica y hogar inteligente'):
        r'^(?!.*(intelig|smart|\bwifi\b|alexa|google home|zigbee|\bapp\b|remoto))'
        # "20 interruptores táctiles inteligentes de 6x6x5 mm, 4 pines" es un
        # componente electrónico suelto: la palabra viene de una traducción.
        r'|\bpines?\b|\d ?x ?\d ?x ?\d ?mm',
    # El ventilador de 120/140 mm es del gabinete de la PC, no del cuarto.
    ('Componentes y accesorios de PC', 'Climatización'):
        r'\b(80|92|120|140|200) ?mm\b|\bargb\b|\brgb\b|gabinete|case fan|\bpwm\b',
    # La pantalla "de repuesto para HP Envy" es una pieza, no un monitor.
    ('Componentes y accesorios de PC', 'Monitores'):
        r'\brepuesto\b|\breemplazo\b|\bpara (hp|dell|lenovo|asus|acer)\b'
        # La base de conexión es un accesorio y el todo-en-uno es una
        # computadora; ninguno de los dos es un monitor.
        r'|base de conexion|\bdocking\b|\bdock\b|todo en uno|all.?in.?one',
}

# Banda 3-9: casi todo se cae. Los pares que sobreviven son los que el
# auditor acierta por goleada aunque la ventaja sea chica.
ACEPTADOS_3_9 = {
    ('Muebles', 'Juegos de mesa'): None,
    ('Muebles', 'Blancos y ropa de cama'): None,
    ('Muebles', 'Otros'): None,
    ('Muebles', 'Almacenamiento'): None,
    ('Otros', 'Cocina y comedor'): None,
    ('Fitness', 'Deportes y fitness'): None,
    ('Refacciones', 'Movilidad eléctrica'): None,
    # Cremas y champús de bebé sí; el kit de ciencia del cuerpo humano no.
    ('Juguetes y bebés', 'Belleza y cuidado personal'):
        r'kit de ciencia|cuerpo humano|\bmodelo\b',
}

BANDAS = [(9.0, 15.0, ACEPTADOS_9_15), (3.0, 9.0, ACEPTADOS_3_9)]

filas = list(csv.DictReader(open(sys.argv[1], encoding='utf-8'), delimiter='\t'))
grupos = collections.defaultdict(list)
cuenta = collections.Counter()
for f in filas:
    v = float(f['ventaja'])
    tabla = next((t for lo, hi, t in BANDAS if lo <= v < hi), None)
    if tabla is None:
        continue
    par = (f['categoria'], f['destino_propuesto'])
    if par not in tabla:
        cuenta['par no aceptado'] += 1
        continue
    no = tabla[par]
    if no and re.search(no, f['nombre'].lower()):
        cuenta['filtrado dentro del par'] += 1
        continue
    grupos[f"{f['categoria']} | {f['subcategoria']} | {f['destino_propuesto']} | "].append(f['id'])
    cuenta['aceptada'] += 1

json.dump(grupos, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(dict(cuenta))
for k in sorted(grupos, key=lambda k: -len(grupos[k]))[:20]:
    print(f"  {len(grupos[k]):4}  {k}")
print(f"Total: {sum(len(v) for v in grupos.values())} fichas en {len(grupos)} grupos")
