from pathlib import Path
import sys
import pandas as pd


def validar_gold():
    base_dir = Path(__file__).resolve().parent.parent.parent
    gold_path = base_dir / "data" / "gold" / "gold_final.csv"

    print("==================================================")
    print("      AUDITORÍA Y VALIDACIÓN DE DATOS (GOLD)     ")
    print("==================================================")

    if not gold_path.exists():
        print(f"[ERROR] No se encontró el archivo Gold en: {gold_path}")
        sys.exit(1)

    df = pd.read_csv(gold_path)
    print(f"[OK] Archivo Gold cargado exitosamente.")
    print(f"     Dimensiones: {df.shape[0]} filas, {df.shape[1]} columnas\n")

    print("--- 1. Evaluación de Nulos ---")
    nulos = df.isnull().sum()
    for col, cant in nulos.items():
        pct = (cant / len(df)) * 100
        print(f"  - {col}: {cant} nulos ({pct:.1f}%)")

    print("\n--- 2. Evaluación de Duplicados ---")
    dup_exactos = df.duplicated().sum()
    print(f"  - Filas completamente duplicadas: {dup_exactos}")

    key_cols = ["departamento_clave", "nivel_formacion", "anio"]
    dup_keys = df.duplicated(subset=key_cols).sum()
    print(f"  - Duplicados por clave de negocio {key_cols}: {dup_keys}")

    print("\n--- 3. Consistencia de Rangos y Valores ---")
    print(
        f"  - Periodo analizado (Años): {df['anio'].min()} a {df['anio'].max()}"
    )
    print(
        f"  - Tasa de deserción min: {df['tasa_desercion'].min():.4f}, max: {df['tasa_desercion'].max():.4f}"
    )

    tasa_fuera_rango = (
        (df["tasa_desercion"] < 0) | (df["tasa_desercion"] > 1)
    ).sum()
    if tasa_fuera_rango > 0:
        print(
            f"  [ADVERTENCIA] Hay {tasa_fuera_rango} registros con tasa fuera del rango [0, 1]"
        )
    else:
        print("  [OK] Todas las tasas de deserción se encuentran entre 0 y 1.")

    print("\n==================================================")
    print("       VALIDACIÓN COMPLETADA CON ÉXITO            ")
    print("==================================================")


if __name__ == "__main__":
    validar_gold()