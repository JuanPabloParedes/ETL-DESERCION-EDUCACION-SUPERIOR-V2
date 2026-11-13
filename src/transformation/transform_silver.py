
import os
import glob
import json
import re
import unicodedata
import pandas as pd


def to_snake_case(text):
    """Estandariza los nombres de las columnas."""
    texto = str(text).strip()
    texto = re.sub(r"[^\w\s]", "", texto)
    texto = re.sub(r"\s+", "_", texto)
    return texto.lower()


def clean_dane_code(valor, longitud):
    """Estandariza los códigos geográficos."""
    if pd.isna(valor) or str(valor).strip() == "":
        return None

    valor = str(valor).split(".")[0].strip()

    if valor.isdigit():
        return valor.zfill(longitud)

    return valor


def normalizar_texto(texto):
    """Normaliza textos sin tildes ni signos de puntuación."""
    if pd.isna(texto):
        return ""

    texto = str(texto).upper().strip()
    texto = unicodedata.normalize("NFKD", texto)

    texto = "".join(
        caracter for caracter in texto
        if not unicodedata.combining(caracter)
    )

    texto = re.sub(r"[^\w\s]", "", texto)
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def process_api_bronze():
    """
    Lee y limpia los archivos JSON de matrículas.

    Genera auditorías de duplicados exactos y de grupos
    con cantidades de matrícula diferentes.
    """

    print("=== [Silver] Procesando API de matrículas ===")

    api_dir = os.path.join("data", "bronze", "api")
    silver_dir = os.path.join("data", "silver")

    os.makedirs(silver_dir, exist_ok=True)

    archivos = sorted(
        glob.glob(
            os.path.join(api_dir, "matricula_api_parte_*.json")
        )
    )

    if not archivos:
        raise FileNotFoundError(
            "No se encontraron archivos JSON de matrículas."
        )

    registros = []

    for archivo in archivos:
        with open(archivo, "r", encoding="utf-8") as entrada:
            datos = json.load(entrada)

        if not isinstance(datos, list):
            raise ValueError(
                f"El archivo {archivo} no contiene una lista JSON."
            )

        registros.extend(datos)

    df = pd.DataFrame(registros)

    if df.empty:
        raise ValueError(
            "La extracción de la API no contiene registros."
        )

    print(f"Total registros originales: {len(df):,}")

    # Estandarización de columnas.
    df.columns = [
        to_snake_case(columna)
        for columna in df.columns
    ]

    columna_anio = "a_o"
    columna_matriculas = "matriculados_2015"

    if columna_anio not in df.columns:
        raise ValueError(
            "No se encontró la columna del año."
        )

    if columna_matriculas not in df.columns:
        raise ValueError(
            "No se encontró la columna de matrículas."
        )

    # Estandarización de códigos geográficos.
    for columna in df.columns:

        if "codigo_municipio" in columna or "cod_muni" in columna:
            df[columna] = df[columna].apply(
                lambda valor: clean_dane_code(valor, 5)
            )

        elif "codigo_departamento" in columna or "cod_depto" in columna:
            df[columna] = df[columna].apply(
                lambda valor: clean_dane_code(valor, 2)
            )

    # Comprobar que las cantidades sean numéricas.
    df[columna_matriculas] = pd.to_numeric(
        df[columna_matriculas],
        errors="coerce"
    )

    if df[columna_matriculas].isna().any():
        raise ValueError(
            "Hay cantidades de matrícula vacías o no numéricas."
        )

    # --------------------------------------------------
    # AUDITORÍA 1: DUPLICADOS EXACTOS POR AÑO
    # --------------------------------------------------

    originales_por_anio = (
        df.groupby(columna_anio)
        .size()
        .rename("registros_originales")
    )

    df_unico = df.drop_duplicates()

    unicos_por_anio = (
        df_unico.groupby(columna_anio)
        .size()
        .rename("registros_unicos")
    )

    auditoria_anual = pd.concat(
        [originales_por_anio, unicos_por_anio],
        axis=1
    ).fillna(0)

    auditoria_anual["duplicados_exactos"] = (
        auditoria_anual["registros_originales"]
        - auditoria_anual["registros_unicos"]
    )

    auditoria_anual = auditoria_anual.reset_index()

    ruta_auditoria_anual = os.path.join(
        silver_dir,
        "auditoria_matriculas_por_anio.csv"
    )

    auditoria_anual.to_csv(
        ruta_auditoria_anual,
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------
    # AUDITORÍA 2: CANTIDADES DIFERENTES
    # --------------------------------------------------

    dimensiones = [
        columna for columna in df.columns
        if columna != columna_matriculas
    ]

    grupos = (
        df.groupby(
            dimensiones,
            dropna=False
        )[columna_matriculas]
        .agg(
            cantidad_registros="count",
            cantidades_diferentes="nunique",
            cantidad_minima="min",
            cantidad_maxima="max"
        )
        .reset_index()
    )

    conflictos = grupos[
        grupos["cantidades_diferentes"] > 1
    ].copy()

    ruta_conflictos = os.path.join(
        silver_dir,
        "auditoria_matriculas_cantidades_diferentes.csv"
    )

    conflictos.to_csv(
        ruta_conflictos,
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------
    # ELIMINAR SOLAMENTE DUPLICADOS EXACTOS
    # --------------------------------------------------

    cantidad_eliminada = len(df) - len(df_unico)

    print(
        f"Registros únicos: {len(df_unico):,}"
    )

    print(
        f"Duplicados exactos eliminados: {cantidad_eliminada:,}"
    )

    print(
        f"Grupos con cantidades diferentes: {len(conflictos):,}"
    )

    print("\nReportes de auditoría generados:")
    print(f" - {ruta_auditoria_anual}")
    print(f" - {ruta_conflictos}")

    return df_unico.reset_index(drop=True)


def process_excel_csvs():
    """Lee los CSV extraídos del Excel y limpia sus estructuras."""

    print("\n=== [Silver] Procesando archivos Excel extraídos ===")

    excel_dir = os.path.join(
        "data",
        "bronze",
        "excel_extraido"
    )

    archivos = sorted(
        glob.glob(os.path.join(excel_dir, "*.csv"))
    )

    if not archivos:
        raise FileNotFoundError(
            "No se encontraron CSV en data/bronze/excel_extraido."
        )

    procesados = {}

    for archivo in archivos:

        nombre = os.path.basename(archivo)

        df = pd.read_csv(
            archivo,
            low_memory=False,
            header=None
        )

        if df.empty:
            print(f"Advertencia: {nombre} está vacío.")
            continue

        # Buscar la primera fila con más de tres valores.
        encabezado = None

        for indice, fila in df.iterrows():
            if fila.notna().sum() > 3:
                encabezado = indice
                break

        if encabezado is None:
            print(
                f"Advertencia: no se encontró encabezado en {nombre}."
            )
            continue

        df.columns = df.iloc[encabezado]

        df = df.iloc[
            encabezado + 1:
        ].reset_index(drop=True)

        df = df.dropna(axis=1, how="all")
        df = df.dropna(how="all")

        df.columns = [
            to_snake_case(columna)
            for columna in df.columns
        ]

        cantidad_inicial = len(df)

        df = df.drop_duplicates().reset_index(drop=True)

        nombre_salida = f"silver_{nombre}"

        procesados[nombre_salida] = df

        print(
            f"{nombre}: {len(df):,} filas "
            f"(duplicados exactos eliminados: "
            f"{cantidad_inicial - len(df):,})"
        )

    return procesados


def ejecutar_transformacion_silver():
    """Genera las tablas Silver independientes, sin realizar JOIN."""

    print("\n==========================================")
    print("INICIANDO TRANSFORMACIÓN CAPA SILVER")
    print("==========================================")

    silver_dir = os.path.join("data", "silver")

    os.makedirs(silver_dir, exist_ok=True)

    # Procesar API.
    df_api = process_api_bronze()

    # Procesar archivos CSV extraídos del Excel.
    excel_dfs = process_excel_csvs()

    # Guardar Silver de matrículas.
    ruta_api = os.path.join(
        silver_dir,
        "silver_matricula_api.csv"
    )

    df_api.to_csv(
        ruta_api,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"\nGuardado: {ruta_api}")

    # Guardar las demás tablas Silver.
    for nombre, df in excel_dfs.items():

        ruta = os.path.join(
            silver_dir,
            nombre
        )

        df.to_csv(
            ruta,
            index=False,
            encoding="utf-8-sig"
        )

        print(f"Guardado: {ruta}")

    print("\nTransformación Silver completada.")
    print("Las fuentes permanecen independientes.")
    print("La integración se realizará únicamente en Gold.")

    return True


if __name__ == "__main__":
    ejecutar_transformacion_silver()
