
from pathlib import Path
import sys
import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

RUTA_SILVER = BASE_DIR / "data" / "silver"
RUTA_GOLD = BASE_DIR / "data" / "gold"

ARCHIVO_MATRICULA = RUTA_SILVER / "silver_matricula_api.csv"
ARCHIVO_DESERCION = RUTA_SILVER / "silver_desercion_departamento.csv"
ARCHIVO_GOLD = RUTA_GOLD / "gold_final.csv"

CLAVES_GOLD = ["departamento_clave", "anio"]

COLUMNAS_TASAS = [
    "tasa_desercion_universitario",
    "tasa_desercion_tyt",
    "tasa_desercion_tecnico_profesional",
    "tasa_desercion_tecnologico",
]


def validar_archivo(ruta):
    """Comprueba que un archivo exista y pueda leerse."""

    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {ruta}"
        )

    return pd.read_csv(ruta, low_memory=False)


def convertir_numerico_validado(serie, nombre, permitir_na=True):
    """
    Convierte una columna a valores numéricos.
    Rechaza textos no numéricos y valores infinitos.
    Conserva los faltantes cuando están permitidos.
    """

    original = serie.copy()
    convertida = pd.to_numeric(original, errors="coerce")

    valores_invalidos = original.notna() & convertida.isna()

    if valores_invalidos.any():
        raise ValueError(
            f"La columna {nombre} contiene valores no numéricos."
        )

    infinitos = convertida.notna() & ~np.isfinite(convertida)

    if infinitos.any():
        raise ValueError(
            f"La columna {nombre} contiene valores infinitos."
        )

    if not permitir_na and convertida.isna().any():
        raise ValueError(
            f"La columna {nombre} contiene valores faltantes."
        )

    return convertida


def convertir_booleanos(serie):
    """Normaliza los valores de una columna booleana."""

    equivalencias = {
        "true": True,
        "false": False,
        "1": True,
        "0": False,
    }

    resultado = serie.astype(str).str.strip().str.lower()
    resultado = resultado.map(equivalencias)

    if resultado.isna().any():
        raise ValueError(
            "La columna coincidio_matricula contiene valores inválidos."
        )

    return resultado


def validar_silver():
    """Valida las tablas independientes de la capa Silver."""

    print("\n--- VALIDACIÓN SILVER ---")

    matricula = validar_archivo(ARCHIVO_MATRICULA)
    desercion = validar_archivo(ARCHIVO_DESERCION)

    print(f"Matrículas: {matricula.shape}")
    print(f"Deserción: {desercion.shape}")

    columnas_api = [
        "c_digo_del_departamento_programa",
        "a_o",
        "matriculados_2015",
    ]

    for columna in columnas_api:
        if columna not in matricula.columns:
            raise ValueError(
                f"Falta la columna {columna} en Silver de matrículas."
            )

    columnas_desercion = [
        "departamento",
        "nivel_formacion",
        "anio",
        "tasa_desercion",
    ]

    for columna in columnas_desercion:
        if columna not in desercion.columns:
            raise ValueError(
                f"Falta la columna {columna} en Silver de deserción."
            )

    # Validar cantidades de matrícula.
    cantidades = convertir_numerico_validado(
        matricula["matriculados_2015"],
        "matriculados_2015"
    )

    negativas = (cantidades.dropna() < 0).sum()

    print(f"Valores negativos de matrícula: {negativas}")

    if negativas > 0:
        raise ValueError(
            "Silver contiene cantidades negativas de matrícula."
        )

    # Validar claves de deserción.
    claves = [
        "departamento",
        "nivel_formacion",
        "anio",
    ]

    if desercion[claves].isna().any().any():
        raise ValueError(
            "Silver de deserción contiene claves faltantes."
        )

    duplicados = desercion.duplicated(
        subset=claves
    ).sum()

    print(f"Duplicados en claves de deserción: {duplicados}")

    if duplicados > 0:
        raise ValueError(
            "Silver de deserción contiene claves duplicadas."
        )

    # Validar tasas de deserción.
    tasas = convertir_numerico_validado(
        desercion["tasa_desercion"],
        "tasa_desercion"
    )

    fuera_rango = (
        (tasas < 0) | (tasas > 1)
    ).sum()

    faltantes = tasas.isna().sum()

    print(f"Tasas fuera del rango 0-1: {fuera_rango}")
    print(f"Tasas faltantes: {faltantes}")

    if fuera_rango > 0:
        raise ValueError(
            "Hay tasas fuera del rango permitido en Silver."
        )

    # Los faltantes se conservan porque pueden representar
    # información no disponible en la fuente original.

    print("Silver validado correctamente.")


def validar_gold():
    """Valida la integración y los indicadores de Gold."""

    print("\n--- VALIDACIÓN GOLD ---")

    gold = validar_archivo(ARCHIVO_GOLD)

    print(f"Dimensiones: {gold.shape}")

    columnas_obligatorias = (
        CLAVES_GOLD
        + COLUMNAS_TASAS
        + [
            "suma_matriculas_reportadas",
            "registros_matricula",
            "coincidio_matricula",
        ]
    )

    for columna in columnas_obligatorias:
        if columna not in gold.columns:
            raise ValueError(
                f"Falta la columna obligatoria: {columna}"
            )

    # Validar claves.
    if gold[CLAVES_GOLD].isna().any().any():
        raise ValueError(
            "Gold contiene departamentos o años faltantes."
        )

    departamentos = (
        gold["departamento_clave"]
        .astype(str)
        .str.strip()
    )

    if departamentos.eq("").any():
        raise ValueError(
            "Gold contiene departamentos vacíos."
        )

    # Validar que exista una fila por departamento y año.
    duplicados = gold.duplicated(
        subset=CLAVES_GOLD
    ).sum()

    print(f"Claves departamento-año duplicadas: {duplicados}")

    if duplicados > 0:
        raise ValueError(
            "Gold contiene combinaciones departamento-año repetidas."
        )

    # Validar años enteros.
    anios = convertir_numerico_validado(
        gold["anio"],
        "anio",
        permitir_na=False
    )

    if ((anios % 1) != 0).any():
        raise ValueError(
            "Gold contiene años que no son números enteros."
        )

    gold["anio"] = anios.astype(int)

    # Validar tasas de deserción.
    for columna in COLUMNAS_TASAS:
        gold[columna] = convertir_numerico_validado(
            gold[columna],
            columna
        )

        fuera_rango = (
            (gold[columna] < 0)
            | (gold[columna] > 1)
        ).sum()

        faltantes = gold[columna].isna().sum()

        print(
            f"{columna}: "
            f"fuera de rango={fuera_rango}, "
            f"faltantes={faltantes}"
        )

        if fuera_rango > 0:
            raise ValueError(
                f"Valores fuera de rango en {columna}."
            )

    # Validar cantidades de matrícula y registros.
    matriculas = convertir_numerico_validado(
        gold["suma_matriculas_reportadas"],
        "suma_matriculas_reportadas"
    )

    registros = convertir_numerico_validado(
        gold["registros_matricula"],
        "registros_matricula"
    )

    if (matriculas.dropna() < 0).any():
        raise ValueError(
            "Se encontraron valores negativos de matrículas."
        )

    if (registros.dropna() < 0).any():
        raise ValueError(
            "Se encontraron cantidades negativas de registros."
        )

    if ((registros.dropna() % 1) != 0).any():
        raise ValueError(
            "La cantidad de registros debe ser un número entero."
        )

    # Validar coincidencias del JOIN.
    coincidencias = convertir_booleanos(
        gold["coincidio_matricula"]
    )

    gold["coincidio_matricula"] = coincidencias

    coincidencias_true = coincidencias.sum()
    coincidencias_false = (~coincidencias).sum()

    print(f"Coincidencias con matrículas: {coincidencias_true}")
    print(f"Sin coincidencia: {coincidencias_false}")

    # Cuando existe coincidencia deben existir datos válidos.
    filas_con_coincidencia = gold.loc[coincidencias]

    if filas_con_coincidencia["suma_matriculas_reportadas"].isna().any():
        raise ValueError(
            "Hay coincidencias sin valores de matrícula."
        )

    if filas_con_coincidencia["registros_matricula"].isna().any():
        raise ValueError(
            "Hay coincidencias sin cantidad de registros."
        )

    if (
        filas_con_coincidencia["registros_matricula"] <= 0
    ).any():
        raise ValueError(
            "Las coincidencias deben tener al menos un registro de matrícula."
        )

    # Cuando no existe coincidencia, los datos de matrícula
    # deben permanecer faltantes y no convertirse en cero.
    filas_sin_coincidencia = gold.loc[~coincidencias]

    if filas_sin_coincidencia[
        ["suma_matriculas_reportadas", "registros_matricula"]
    ].notna().any().any():
        raise ValueError(
            "Hay filas sin coincidencia que contienen datos de matrícula."
        )

    # Resumen temporal.
    print(
        f"Periodo de deserción: "
        f"{gold['anio'].min()} - {gold['anio'].max()}"
    )

    print(
        f"Departamentos analizados: "
        f"{gold['departamento_clave'].nunique()}"
    )

    print("Gold validado correctamente.")


def ejecutar_validaciones():
    """Ejecuta las validaciones de Silver y Gold."""

    try:
        print("===================================")
        print("VALIDACIÓN DE CALIDAD DEL ETL")
        print("===================================")

        validar_silver()
        validar_gold()

        print("\n===================================")
        print("TODAS LAS VALIDACIONES FINALIZARON")
        print("===================================")

    except Exception as error:
        print(f"\nERROR DE VALIDACIÓN: {error}")
        sys.exit(1)


if __name__ == "__main__":
    ejecutar_validaciones()
