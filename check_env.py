import importlib
import sys

REQUERIDOS = [
    "pandas",
    "numpy",
    "matplotlib",
    "seaborn",
    "openpyxl",
    "requests",
    "jupyter",
    "nbconvert",
]

print("--- COMPROBACIÓN DE DEPENDENCIAS INSTALADAS ---")
faltantes = []

for paquete in REQUERIDOS:
    try:
        importlib.import_module(paquete)
        print(f"  [OK] {paquete}")
    except ImportError:
        print(f"  [X]  {paquete} -> NO INSTALADO")
        faltantes.append(paquete)

if faltantes:
    print(f"\n[ERROR] Faltan los siguientes paquetes: {', '.join(faltantes)}")
    print("Ejecuta: pip install -r requirements.txt")
    sys.exit(1)
else:
    print("\n[ÉXITO] Todas las dependencias están disponibles.")