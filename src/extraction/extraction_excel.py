from pathlib import Path
import pandas as pd
import re
import unicodedata


# ============================================================
# CONFIGURACIÓN
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[2]

EXCEL_FILE = (
    ROOT_DIR
    / "data"
    / "bronze"
    / "articles-415244_recurso_19.xlsx"
)

OUTPUT_DIR = ROOT_DIR / "data" / "bronze" / "excel_extraido"

HOJAS = [
    "TD - departamento",
    "TD - metodología",
    "TD - sexo",
    "TD - sector",
    "TD - área de conocimiento",
    "Tasa deserción cohorte acumulad",
    "TDCA - departamento",
    "TDCA - metodología",
    "TGA - departamento",
]


def normalizar_nombre(texto):
    """Generar un nombre de archivo consistente a partir de una hoja."""
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        caracter for caracter in texto
        if not unicodedata.combining(caracter)
    )
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    return texto.strip("_")


def extraer_excel():
    print("=" * 60)
    print("EXTRACCIÓN DE DATOS - BRONZE")
    print("=" * 60)

    if not EXCEL_FILE.exists():
        raise FileNotFoundError(
            f"No se encontró el Excel original: {EXCEL_FILE}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Leer el libro una sola vez
    libro = pd.ExcelFile(EXCEL_FILE)
    hojas_disponibles = libro.sheet_names

    # Eliminar solamente CSV de extracciones anteriores de estas hojas.
    # No se toca el Excel original ni otros archivos.
    nombres_esperados = {
        f"{normalizar_nombre(hoja)}.csv" for hoja in HOJAS
    }

    for archivo in OUTPUT_DIR.glob("*.csv"):
        if archivo.name in nombres_esperados or archivo.name.startswith(
            ("td_", "tdca_", "tga_", "tasa_desercion_")
        ):
            archivo.unlink()

    total_extraidas = 0

    for hoja in HOJAS:
        if hoja not in hojas_disponibles:
            print(f"ADVERTENCIA: No existe la hoja '{hoja}'.")
            continue

        df = pd.read_excel(
            libro,
            sheet_name=hoja,
            header=None,
            dtype=object
        )

        # Excluir columnas completamente vacías sin modificar
        # los valores de las columnas que contienen información.
        columnas_con_datos = df.notna().any(axis=0)
        df = df.loc[:, columnas_con_datos]

        # Excluir filas completamente vacías.
        df = df.dropna(axis=0, how="all")

        nombre_archivo = normalizar_nombre(hoja) + ".csv"
        ruta_salida = OUTPUT_DIR / nombre_archivo

        # Guardar sin añadir encabezados ni índice.
        df.to_csv(
            ruta_salida,
            index=False,
            header=False,
            encoding="utf-8-sig"
        )

        total_extraidas += 1

        print(
            f"Hoja: {hoja} | Filas: {df.shape[0]} | "
            f"Columnas: {df.shape[1]} | Archivo: {nombre_archivo}"
        )

    print("-" * 60)
    print(f"Hojas extraídas: {total_extraidas} de {len(HOJAS)}")
    print(f"Destino: {OUTPUT_DIR}")
    print("Extracción finalizada.")


if __name__ == "__main__":
    extraer_excel()