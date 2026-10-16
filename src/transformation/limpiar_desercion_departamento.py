
import pandas as pd
from pathlib import Path
import unicodedata

# Rutas del proyecto
entrada = Path("data/bronze/excel_extraido/td_departamento.csv")
salida = Path("data/silver/silver_desercion_departamento.csv")

if not entrada.exists():
    raise FileNotFoundError(f"No se encontró el archivo: {entrada}")

# Leer el archivo original sin asumir que la primera fila es el encabezado
df = pd.read_csv(entrada, header=None, low_memory=False)

registros = []
nivel_actual = None
columnas_anio = None

def normalizar_nivel(texto):
    texto = str(texto).strip()
    prefijo = "Nivel de formación"
    if texto.lower().startswith(prefijo.lower()):
        return texto[len(prefijo):].strip()
    return texto

# Recorrer todas las filas del archivo original
for _, fila in df.iterrows():
    valores = fila.tolist()
    primero = str(valores[0]).strip() if pd.notna(valores[0]) else ""

    # Identificar el nivel de formación
    if primero.lower().startswith("nivel de formación"):
        nivel_actual = normalizar_nivel(primero)
        columnas_anio = None
        continue

    # Identificar el encabezado con los años
    if primero.lower().startswith("departamento de oferta del programa"):
        columnas_anio = []
        for valor in valores[1:]:
            try:
                anio = int(float(valor))
                if 2000 <= anio <= 2100:
                    columnas_anio.append(anio)
                else:
                    columnas_anio.append(None)
            except (TypeError, ValueError):
                columnas_anio.append(None)
        continue

    # Saltar filas que no pertenecen a una tabla válida
    if not nivel_actual or columnas_anio is None or not primero:
        continue

    if primero.lower().startswith(("na:", "nota:", "fuente:", "corte de información")):
        continue

    # Registrar cada departamento y su tasa por año
    for posicion, anio in enumerate(columnas_anio, start=1):
        if anio is None or posicion >= len(valores):
            continue

        valor = valores[posicion]

        if pd.isna(valor):
            tasa = None
        else:
            try:
                tasa = float(valor)
            except (TypeError, ValueError):
                tasa = None

        registros.append({
            "departamento": primero,
            "nivel_formacion": nivel_actual,
            "anio": anio,
            "tasa_desercion": tasa
        })

resultado = pd.DataFrame(registros)

if resultado.empty:
    raise ValueError(
        "No se extrajeron registros. Revisa la estructura del CSV original."
    )

# Normalizar el nombre del departamento para facilitar el cruce
def normalizar_departamento(texto):
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.upper().split())

resultado["departamento_clave"] = resultado["departamento"].apply(
    normalizar_departamento
)

# Eliminar solo filas completamente repetidas en las mismas claves y valor
resultado = resultado.drop_duplicates(
    subset=[
        "departamento_clave",
        "nivel_formacion",
        "anio",
        "tasa_desercion"
    ]
)

salida.parent.mkdir(parents=True, exist_ok=True)
resultado.to_csv(salida, index=False, encoding="utf-8-sig")

print("=== LIMPIEZA DE DESERCIÓN POR DEPARTAMENTO ===")
print("Registros generados:", len(resultado))
print("Niveles encontrados:")
print(resultado["nivel_formacion"].value_counts().to_string())
print("Años:", resultado["anio"].min(), "-", resultado["anio"].max())
print("Archivo guardado en:", salida)
print("\nPrimeros registros:")
print(resultado.head(10).to_string(index=False))
