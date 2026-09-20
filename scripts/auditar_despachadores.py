"""Busca en los despachadores sub_* el patrón que se comió Celulares: una
última línea que devuelve una subcategoría SIN condición, de modo que todo
lo que entra al rubro sale clasificado aunque no sea del rubro."""
import ast, io, os, sys

ARCHIVOS = ['scripts/clasificar_captura_perifericos.py',
            'scripts/subcategorias_redes.py',
            'scripts/subcategorias_finas.py',
            'scripts/subcategorias_finas_ola2.py']

def ultima_sentencia(fn):
    return fn.body[-1] if fn.body else None

print(f"{'despachador':38} {'archivo':34} último paso")
print("-" * 110)
sospechosos = []
for arch in ARCHIVOS:
    if not os.path.exists(arch):
        continue
    arbol = ast.parse(open(arch, encoding='utf-8').read(), arch)
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.FunctionDef) or not nodo.name.startswith('sub_'):
            continue
        u = ultima_sentencia(nodo)
        if isinstance(u, ast.Return):
            v = u.value
            if isinstance(v, ast.Constant) and v.value is None:
                estado = "return None  (bien: deja el hueco)"
            elif isinstance(v, ast.Constant):
                estado = f"return {v.value!r}  <-- CAJÓN INCONDICIONAL"
                sospechosos.append((nodo.name, arch, v.value))
            elif isinstance(v, ast.Call):
                estado = "return <llamada>  (delega en otra función)"
            else:
                estado = "return <expresión>"
        elif isinstance(u, ast.If):
            estado = "termina en un if  (sin salida por defecto)"
        else:
            estado = type(u).__name__
        print(f"{nodo.name:38} {os.path.basename(arch):34} {estado}")
print()
print(f"Cajones incondicionales: {len(sospechosos)}")
for n, a, v in sospechosos:
    print(f"   {n}  ->  {v!r}")
