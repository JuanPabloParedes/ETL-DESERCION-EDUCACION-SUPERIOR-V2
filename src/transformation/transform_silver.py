import os
import glob
import json
import pandas as pd
import re

def to_snake_case(text):
    """
    Convierte un texto a minúsculas y reemplaza los espacios por guiones bajos.
    Se usa para estandarizar los nombres de todas las columnas.
    """
    text = re.sub(r'[^\w\s]', '', str(text)) 
    text = re.sub(r'\s+', '_', text.strip()) 
    return text.lower()

def clean_dane_code(val, length):
    """
    Agrega ceros a la izquierda a los códigos de municipio o departamento 
    para asegurar que siempre tengan la misma longitud numérica.
    """
    if pd.isna(val) or val is None or str(val).strip() == "":
        return None  
    val_str = str(val).split('.')[0].strip() 
    return val_str.zfill(length) if val_str.isdigit() else val_str

def normalizar_texto(texto):
    """
    Convierte el texto a mayúsculas, elimina las tildes y signos de puntuación.
    Es fundamental para que el cruce de datos no falle por diferencias de escritura.
    Ejemplo: 'Bogotá, D.C.' se convierte en 'BOGOTA DC' en ambas tablas.
    """
    if pd.isna(texto): return ""
    texto = str(texto).upper().strip()
    reemplazos = (("Á", "A"), ("É", "E"), ("Í", "I"), ("Ó", "O"), ("Ú", "U"))
    for a, b in reemplazos:
        texto = texto.replace(a, b)
    # Eliminar signos de puntuación (puntos, comas)
    texto = re.sub(r'[^\w\s]', '', texto)
    return texto.strip()

def process_api_bronze():
    """
    Lee los archivos JSON de matrícula extraídos de la API, los une en una 
    sola tabla, formatea sus columnas y elimina los registros duplicados.
    """
    print("=== [Silver] Procesando Datos de la API (Matrículas) ===")
    api_dir = os.path.join("data", "bronze", "api")
    json_files = sorted(glob.glob(os.path.join(api_dir, "matricula_api_parte_*.json")))
    
    if not json_files: return None

    records = []
    for file_path in json_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            records.extend(data)

    df_api = pd.DataFrame(records)
    print(f" -> Total registros cargados desde API: {len(df_api):,}")

    # Aplicar formato estándar a los nombres de las columnas
    df_api.columns = [to_snake_case(col) for col in df_api.columns]

    # Formatear los códigos numéricos de ubicación
    for col in df_api.columns:
        if 'codigo_municipio' in col or 'cod_muni' in col:
            df_api[col] = df_api[col].apply(lambda x: clean_dane_code(x, 5))
        elif 'codigo_departamento' in col or 'cod_depto' in col:
            df_api[col] = df_api[col].apply(lambda x: clean_dane_code(x, 2))

    # Eliminar datos exactamente iguales
    initial_len = len(df_api)
    df_api = df_api.drop_duplicates()
    print(f" -> Registros únicos tras limpiar duplicados: {len(df_api):,} (Removidos: {initial_len - len(df_api)})")

    return df_api

def process_excel_csvs():
    """
    Lee los archivos CSV de deserción, identifica dónde empiezan realmente 
    los datos útiles y descarta el texto introductorio del Ministerio.
    """
    print("\n=== [Silver] Procesando Datos del Excel (Deserción) ===")
    excel_dir = os.path.join("data", "bronze", "excel_extraido")
    csv_files = glob.glob(os.path.join(excel_dir, "*.csv"))

    if not csv_files: return {}

    processed_dfs = {}
    for file_path in csv_files:
        file_name = os.path.basename(file_path)
        
        # Leer el archivo completo sin asignar nombres de columnas todavía
        df = pd.read_csv(file_path, low_memory=False, header=None)
        
        # Buscar dinámicamente la fila que contiene los nombres de las columnas
        header_idx = 0
        for i, row in df.iterrows():
            if row.notna().sum() > 3: 
                header_idx = i
                break
                
        # Asignar la fila encontrada como nombres de columna y descartar lo anterior
        df.columns = df.iloc[header_idx]
        df = df.iloc[header_idx + 1:].reset_index(drop=True)
        
        # Limpiar filas y columnas que estén en blanco
        df = df.dropna(axis=1, how='all')
        df = df.dropna(how='all')
        
        # Aplicar formato estándar a los nombres de las columnas
        df.columns = [to_snake_case(col) for col in df.columns]
        
        df = df.drop_duplicates()
        clean_name = f"silver_{file_name}"
        processed_dfs[clean_name] = df
        print(f" -> Procesado {file_name}: {len(df):,} filas limpias.")

    return processed_dfs

def ejecutar_transformacion_silver():
    """
    Función principal que coordina la limpieza de las dos fuentes de datos y 
    realiza la integración de ambas tablas en un único archivo.
    """
    print("\nIniciando transformación Capa Silver...")
    
    silver_dir = os.path.join("data", "silver")
    os.makedirs(silver_dir, exist_ok=True)

    # Limpiar tablas independientes
    df_api_silver = process_api_bronze()
    excel_dfs = process_excel_csvs()

    if df_api_silver is None or not excel_dfs: return False

    # Guardar una copia de cada tabla limpia por separado
    df_api_silver.to_csv(os.path.join(silver_dir, "silver_matricula_api.csv"), index=False, encoding='utf-8')
    for file_name, df_clean in excel_dfs.items():
        df_clean.to_csv(os.path.join(silver_dir, file_name), index=False, encoding='utf-8')

    print("\n=== [Silver] Integrando Fuentes (JOIN) ===")
    
    dataset_desercion_objetivo = 'silver_td_departamento.csv' 
    
    if dataset_desercion_objetivo in excel_dfs:
        df_desercion = excel_dfs[dataset_desercion_objetivo]
        
        # ¡NOMBRES EXACTOS! Ya no adivinamos. Le decimos exactamente qué columnas cruzar
        col_api_nombre = 'departamento_de_oferta_del_programa'
        col_excel_nombre = 'departamento_de_oferta_del_programa'
        
        if col_api_nombre in df_api_silver.columns and col_excel_nombre in df_desercion.columns:
            print(f" -> Cruzando columnas exactas por nombre de departamento...")
            
            # Crear columnas temporales súper limpias (sin tildes, sin comas, en mayúsculas)
            df_api_silver['llave_cruce'] = df_api_silver[col_api_nombre].apply(normalizar_texto)
            df_desercion['llave_cruce'] = df_desercion[col_excel_nombre].apply(normalizar_texto)
            
            # Unir ambas tablas conservando solo los departamentos que existan en las dos
            df_integrado = pd.merge(
                df_api_silver,
                df_desercion,
                on='llave_cruce',
                how='inner',
                suffixes=('_matricula', '_desercion')
            )
            
            # Borrar la columna temporal y guardar el archivo final
            df_integrado = df_integrado.drop(columns=['llave_cruce'])
            ruta_integrado = os.path.join(silver_dir, "silver_dataset_integrado.csv")
            df_integrado.to_csv(ruta_integrado, index=False, encoding='utf-8')
            
            print(f"JOIN EXITOSO. Dataset integrado guardado.")
            print(f" -> Total de registros consolidados en el archivo final: {len(df_integrado):,}")
            
            if len(df_integrado) == 0:
                print("⚠ ALERTA ROJA: El cruce dio 0 filas. Revisa que los nombres de los departamentos coincidan.")
        else:
            print(f"Error en el JOIN: No se encontraron las columnas especificadas.")
    else:
        print(f"Advertencia: No se encontró '{dataset_desercion_objetivo}'.")

    print("Proceso de Capa Silver completado.")
    return True

if __name__ == "__main__":
    ejecutar_transformacion_silver()