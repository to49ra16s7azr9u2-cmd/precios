"""Toma la banda de ventaja 9-15 del informe de vocabulario y deja pasar
solo los pares origen->destino que se revisaron a mano y salieron bien."""
import collections, csv, json, re, sys

# (origen, destino): None = pasa todo; regex = tiene que NO cumplirla
ACEPTADOS = {
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

filas = list(csv.DictReader(open(sys.argv[1], encoding='utf-8'), delimiter='\t'))
grupos = collections.defaultdict(list)
cuenta = collections.Counter()
for f in filas:
    v = float(f['ventaja'])
    if not (9.0 <= v < 15.0):
        continue
    par = (f['categoria'], f['destino_propuesto'])
    if par not in ACEPTADOS:
        cuenta['par no aceptado'] += 1
        continue
    no = ACEPTADOS[par]
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
