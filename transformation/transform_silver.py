import os
import glob
import json
import pandas as pd
import re

def to_snake_case(text):
    """Convierte cadenas a formato snake_case limpio."""
    text = re.sub(r'[^\w\s]', '', str(text))
    text = re.sub(r'\s+', '_', text.strip())
    return text.lower()

def clean_dane_code(val, length):
    """Formatea códigos DANE asegurando ceros a la izquierda y cadena limpia."""
    if pd.isna(val) or val is None:
        return ""
    val_str = str(val).split('.')[0].strip()
    return val_str.zfill(length) if val_str.isdigit() else val_str

def process_api_bronze():
    """Lee y consolida los 8 archivos JSON de la API en la capa Silver."""
    print("=== Procesando Datos de la API (Matrículas) ===")
    api_dir = os.path.join("data", "bronze", "api")
    json_files = sorted(glob.glob(os.path.join(api_dir, "matricula_api_parte_*.json")))
    
    if not json_files:
        print("⚠ No se encontraron archivos JSON en data/bronze/api/")
        return None

    records = []
    for file_path in json_files:
        print(f"  - Cargando {os.path.basename(file_path)}...")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            records.extend(data)

    df_api = pd.DataFrame(records)
    print(f"Total registros cargados desde API: {len(df_api):,}")

    # 1. Estandarización de nombres de columnas
    df_api.columns = [to_snake_case(col) for col in df_api.columns]

    # 2. Formateo de códigos DANE (si existen las columnas)
    for col in df_api.columns:
        if 'codigo_municipio' in col or 'cod_muni' in col:
            df_api[col] = df_api[col].apply(lambda x: clean_dane_code(x, 5))
        elif 'codigo_departamento' in col or 'cod_depto' in col:
            df_api[col] = df_api[col].apply(lambda x: clean_dane_code(x, 2))

    # 3. Limpieza de duplicados exactos
    initial_len = len(df_api)
    df_api = df_api.drop_duplicates()
    print(f"Registros únicos tras eliminar duplicados: {len(df_api):,} (Removidos: {initial_len - len(df_api)})")

    return df_api

def process_excel_csvs():
    """Limpia y estandariza los CSVs extraídos del Excel en data/bronze/excel_extraido/."""
    print("\n=== Procesando Datos del Excel (Deserción) ===")
    excel_dir = os.path.join("data", "bronze", "excel_extraido")
    csv_files = glob.glob(os.path.join(excel_dir, "*.csv"))

    if not csv_files:
        print("⚠ No se encontraron CSVs en data/bronze/excel_extraido/")
        return {}

    processed_dfs = {}
    for file_path in csv_files:
        file_name = os.path.basename(file_path)
        print(f"  - Procesando {file_name}...")
        df = pd.read_csv(file_path, low_memory=False)
        
        # Estandarizar columnas
        df.columns = [to_snake_case(col) for col in df.columns]
        
        # Formatear códigos DANE en archivos del excel si aplican
        for col in df.columns:
            if 'codigo' in col or 'cod' in col:
                df[col] = df[col].apply(lambda x: clean_dane_code(x, 2 if 'dep' in col else 5))
        
        df = df.drop_duplicates()
        clean_name = f"silver_{file_name}"
        processed_dfs[clean_name] = df

    return processed_dfs

def main():
    # Rutas de salida
    silver_dir = os.path.join("data", "silver")
    os.makedirs(silver_dir, exist_ok=True)

    # 1. Procesar API
    df_api_silver = process_api_bronze()
    if df_api_silver is not None:
        api_output_path = os.path.join(silver_dir, "silver_matricula_api_consolidado.csv")
        df_api_silver.to_csv(api_output_path, index=False, encoding='utf-8')
        print(f"✓ Guardado: {api_output_path} ({len(df_api_silver):,} filas)")

    # 2. Procesar CSVs del Excel
    excel_dfs = process_excel_csvs()
    for file_name, df_clean in excel_dfs.items():
        output_path = os.path.join(silver_dir, file_name)
        df_clean.to_csv(output_path, index=False, encoding='utf-8')
        print(f"✓ Guardado: {output_path} ({len(df_clean):,} filas)")

    print("\n¡Proceso de Capa Silver completado con éxito!")

if __name__ == "__main__":
    main()