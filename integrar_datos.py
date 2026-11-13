
import os
import re
import unicodedata
import pandas as pd


# ============================================================
# CONFIGURACIÓN DE RUTAS
# ============================================================

RUTA_SILVER = os.path.join("data", "silver")
RUTA_GOLD = os.path.join("data", "gold")

ARCHIVO_MATRICULA = os.path.join(
    RUTA_SILVER, "silver_matricula_api.csv"
)

ARCHIVO_DESERCION = os.path.join(
    RUTA_SILVER, "silver_desercion_departamento.csv"
)

ARCHIVO_FINAL = os.path.join(
    RUTA_GOLD, "gold_final.csv"
)

ARCHIVO_AUDITORIA_MATRICULAS = os.path.join(
    RUTA_GOLD, "auditoria_calidad_matriculas.csv"
)

ARCHIVO_MATRICULAS_EXCLUIDAS = os.path.join(
    RUTA_GOLD, "auditoria_registros_matricula_excluidos.csv"
)

ARCHIVO_AUDITORIA_JOIN = os.path.join(
    RUTA_GOLD, "auditoria_cobertura_join_por_anio.csv"
)

ARCHIVO_JOIN_SIN_COINCIDENCIA = os.path.join(
    RUTA_GOLD, "auditoria_join_sin_coincidencia.csv"
)


# ============================================================
# CÓDIGOS DANE DE DEPARTAMENTOS
# ============================================================

CODIGOS_DEPARTAMENTO = {
    "05": "ANTIOQUIA",
    "08": "ATLANTICO",
    "11": "BOGOTA DC",
    "13": "BOLIVAR",
    "15": "BOYACA",
    "17": "CALDAS",
    "18": "CAQUETA",
    "19": "CAUCA",
    "20": "CESAR",
    "23": "CORDOBA",
    "25": "CUNDINAMARCA",
    "27": "CHOCO",
    "41": "HUILA",
    "44": "LA GUAJIRA",
    "47": "MAGDALENA",
    "50": "META",
    "52": "NARINO",
    "54": "NORTE DE SANTANDER",
    "63": "QUINDIO",
    "66": "RISARALDA",
    "68": "SANTANDER",
    "70": "SUCRE",
    "73": "TOLIMA",
    "76": "VALLE DEL CAUCA",
    "81": "ARAUCA",
    "85": "CASANARE",
    "86": "PUTUMAYO",
    "88": (
        "ARCHIPIELAGO DE SAN ANDRES "
        "PROVIDENCIA Y SANTA CATALINA"
    ),
    "91": "AMAZONAS",
    "94": "GUAINIA",
    "95": "GUAVIARE",
    "97": "VAUPES",
    "99": "VICHADA",
}

DEPARTAMENTOS_VALIDOS = {
    " ".join(valor.split())
    for valor in CODIGOS_DEPARTAMENTO.values()
}

NIVELES_FORMACION_VALIDOS = {
    "Universitario",
    "TyT",
    "Técnico Profesional",
    "Tecnológico",
}


# ============================================================
# FUNCIONES DE NORMALIZACIÓN
# ============================================================

def normalizar_departamento(valor):
    """Normaliza nombres de departamentos para compararlos."""

    if pd.isna(valor):
        return None

    texto = str(valor).strip().upper()

    texto = unicodedata.normalize("NFKD", texto)

    texto = "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(caracter)
    )

    texto = re.sub(r"[^\w\s]", "", texto)
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def normalizar_codigo(valor):
    """Estandariza códigos DANE de departamento."""

    if pd.isna(valor):
        return None

    codigo = str(valor).split(".")[0].strip()

    if not codigo.isdigit():
        return None

    return codigo.zfill(2)


# ============================================================
# PREPARACIÓN Y AUDITORÍA DE MATRÍCULAS
# ============================================================

def preparar_matriculas():
    """
    Prepara matrículas por departamento y año.

    Genera reportes de calidad antes de excluir registros
    que no cumplen las condiciones necesarias.
    """

    print("\n--- PREPARACIÓN Y AUDITORÍA DE MATRÍCULAS ---")

    if not os.path.exists(ARCHIVO_MATRICULA):
        raise FileNotFoundError(ARCHIVO_MATRICULA)

    df = pd.read_csv(
        ARCHIVO_MATRICULA,
        low_memory=False
    )

    columnas = [
        "c_digo_del_departamento_programa",
        "a_o",
        "matriculados_2015",
    ]

    for columna in columnas:
        if columna not in df.columns:
            raise ValueError(
                f"Falta la columna {columna} "
                "en la tabla de matrículas."
            )

    total_original = len(df)

    # Número de fila del archivo CSV, incluyendo encabezado.
    df["numero_fila_csv"] = range(2, total_original + 2)

    # Normalización de código DANE.
    df["codigo_departamento"] = (
        df["c_digo_del_departamento_programa"]
        .apply(normalizar_codigo)
    )

    df["departamento_clave"] = (
        df["codigo_departamento"]
        .map(CODIGOS_DEPARTAMENTO)
    )

    # Conversión de año y cantidad de matrículas.
    df["anio"] = pd.to_numeric(
        df["a_o"],
        errors="coerce"
    )

    df["matriculados_2015"] = pd.to_numeric(
        df["matriculados_2015"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # IDENTIFICACIÓN DE REGISTROS CON PROBLEMAS
    # --------------------------------------------------------

    codigo_ausente = df["codigo_departamento"].isna()

    codigo_no_reconocido = (
        df["codigo_departamento"].notna()
        & df["departamento_clave"].isna()
    )

    anio_invalido = (
        df["anio"].isna()
        | (
            df["anio"].notna()
            & (df["anio"] % 1 != 0)
        )
    )

    matricula_invalida = (
        df["matriculados_2015"].isna()
        | (df["matriculados_2015"] < 0)
    )

    registros_excluidos = (
        codigo_ausente
        | codigo_no_reconocido
        | anio_invalido
        | matricula_invalida
    )

    # --------------------------------------------------------
    # REPORTE DETALLADO DE REGISTROS EXCLUIDOS
    # --------------------------------------------------------

    excluidos = df.loc[registros_excluidos].copy()

    def obtener_motivos(fila):
        motivos = []

        if pd.isna(fila["codigo_departamento"]):
            motivos.append("Código DANE ausente o inválido")

        elif pd.isna(fila["departamento_clave"]):
            motivos.append("Código DANE no reconocido")

        if pd.isna(fila["anio"]):
            motivos.append("Año ausente o no numérico")

        elif fila["anio"] % 1 != 0:
            motivos.append("Año no entero")

        if pd.isna(fila["matriculados_2015"]):
            motivos.append("Matrícula ausente o no numérica")

        elif fila["matriculados_2015"] < 0:
            motivos.append("Cantidad de matrícula negativa")

        return "; ".join(motivos)

    if not excluidos.empty:
        excluidos["motivo_exclusion"] = excluidos.apply(
            obtener_motivos,
            axis=1
        )

        excluidos.to_csv(
            ARCHIVO_MATRICULAS_EXCLUIDAS,
            index=False,
            encoding="utf-8-sig"
        )

    else:
        # Se genera igualmente el archivo con sus encabezados.
        excluidos["motivo_exclusion"] = pd.Series(dtype=str)

        excluidos.to_csv(
            ARCHIVO_MATRICULAS_EXCLUIDAS,
            index=False,
            encoding="utf-8-sig"
        )

    # --------------------------------------------------------
    # REPORTE RESUMIDO DE CALIDAD
    # --------------------------------------------------------

    total_excluidos = int(registros_excluidos.sum())

    total_validos = total_original - total_excluidos

    auditoria = pd.DataFrame([{
        "registros_originales": total_original,
        "registros_validos": total_validos,
        "registros_excluidos": total_excluidos,
        "codigos_ausentes_o_invalidos": int(codigo_ausente.sum()),
        "codigos_no_reconocidos": int(
            codigo_no_reconocido.sum()
        ),
        "anios_invalidos": int(anio_invalido.sum()),
        "matriculas_invalidas": int(
            matricula_invalida.sum()
        ),
    }])

    auditoria.to_csv(
        ARCHIVO_AUDITORIA_MATRICULAS,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"Registros originales: {total_original:,}")
    print(f"Registros válidos: {total_validos:,}")
    print(f"Registros excluidos: {total_excluidos:,}")
    print(f"Códigos ausentes o inválidos: {codigo_ausente.sum():,}")
    print(
        "Códigos no reconocidos: "
        f"{codigo_no_reconocido.sum():,}"
    )
    print(f"Años inválidos: {anio_invalido.sum():,}")
    print(f"Matrículas inválidas: {matricula_invalida.sum():,}")

    print("\nReportes de calidad generados:")
    print(f" - {ARCHIVO_AUDITORIA_MATRICULAS}")
    print(f" - {ARCHIVO_MATRICULAS_EXCLUIDAS}")

    # --------------------------------------------------------
    # CONSERVAR ÚNICAMENTE REGISTROS VÁLIDOS
    # --------------------------------------------------------

    df = df.loc[~registros_excluidos].copy()

    if df.empty:
        raise ValueError(
            "No existen registros válidos de matrículas."
        )

    df["anio"] = df["anio"].astype(int)

    # --------------------------------------------------------
    # AGREGACIÓN POR DEPARTAMENTO Y AÑO
    # --------------------------------------------------------

    # Las sumas representan valores reportados por la fuente.
    # No equivalen necesariamente a estudiantes únicos.

    agregado = (
        df.groupby(
            ["departamento_clave", "anio"],
            as_index=False
        )
        .agg(
            suma_matriculas_reportadas=(
                "matriculados_2015",
                "sum"
            ),
            registros_matricula=(
                "matriculados_2015",
                "count"
            ),
        )
    )

    claves = ["departamento_clave", "anio"]

    if agregado[claves].isna().any().any():
        raise ValueError(
            "La agregación contiene claves nulas."
        )

    if agregado.duplicated(subset=claves).any():
        raise ValueError(
            "Hay claves repetidas en la agregación de matrículas."
        )

    print(
        f"\nMatrículas agregadas: {len(agregado):,} "
        "combinaciones departamento-año."
    )

    return agregado


# ============================================================
# PREPARACIÓN DE TASAS DE DESERCIÓN
# ============================================================

def preparar_desercion():
    """Prepara las tasas SPADIES sin eliminar valores faltantes."""

    print("\n--- PREPARACIÓN DE TASAS DE DESERCIÓN ---")

    if not os.path.exists(ARCHIVO_DESERCION):
        raise FileNotFoundError(ARCHIVO_DESERCION)

    df = pd.read_csv(
        ARCHIVO_DESERCION,
        low_memory=False
    )

    columnas = [
        "departamento",
        "nivel_formacion",
        "anio",
        "tasa_desercion",
    ]

    for columna in columnas:
        if columna not in df.columns:
            raise ValueError(
                f"Falta la columna {columna} "
                "en la tabla de deserción."
            )

    df["departamento_clave"] = (
        df["departamento"]
        .apply(normalizar_departamento)
    )

    df["anio"] = pd.to_numeric(
        df["anio"],
        errors="coerce"
    )

    df["tasa_desercion"] = pd.to_numeric(
        df["tasa_desercion"],
        errors="coerce"
    )

    df["nivel_formacion"] = (
        df["nivel_formacion"]
        .astype("string")
        .str.strip()
    )

    # Las claves de integración no pueden estar vacías.
    if df["departamento_clave"].isna().any():
        raise ValueError(
            "SPADIES contiene departamentos sin identificar."
        )

    if df["anio"].isna().any():
        raise ValueError(
            "SPADIES contiene años ausentes o inválidos."
        )

    if (df["anio"] % 1 != 0).any():
        raise ValueError(
            "SPADIES contiene años que no son enteros."
        )

    if df["nivel_formacion"].isna().any():
        raise ValueError(
            "SPADIES contiene niveles de formación vacíos."
        )

    # Comprobar que los departamentos correspondan al catálogo DANE.
    departamentos_desconocidos = (
        set(df["departamento_clave"].unique())
        - DEPARTAMENTOS_VALIDOS
    )

    if departamentos_desconocidos:
        raise ValueError(
            "SPADIES contiene departamentos que no están "
            "en el catálogo DANE normalizado: "
            f"{sorted(departamentos_desconocidos)}"
        )

    # Comprobar niveles de formación.
    niveles_desconocidos = (
        set(df["nivel_formacion"].dropna().unique())
        - NIVELES_FORMACION_VALIDOS
    )

    if niveles_desconocidos:
        raise ValueError(
            "Se encontraron niveles de formación no reconocidos: "
            f"{sorted(niveles_desconocidos)}"
        )

    df["anio"] = df["anio"].astype(int)

    # Las tasas deben estar entre 0 y 1.
    # Los valores faltantes se conservan como NA.

    fuera_rango = (
        (df["tasa_desercion"] < 0)
        | (df["tasa_desercion"] > 1)
    )

    if fuera_rango.any():
        raise ValueError(
            "Se encontraron tasas de deserción fuera del rango 0-1."
        )

    # --------------------------------------------------------
    # VALIDACIÓN DE CLAVES SPADIES
    # --------------------------------------------------------

    claves = [
        "departamento_clave",
        "nivel_formacion",
        "anio",
    ]

    duplicados = df.duplicated(
        subset=claves,
        keep=False
    )

    if duplicados.any():
        ejemplos = df.loc[duplicados, claves].head(10)

        raise ValueError(
            "Hay combinaciones repetidas en SPADIES:\n"
            f"{ejemplos}"
        )

    # --------------------------------------------------------
    # TRANSFORMACIÓN DE TABLA LARGA A TABLA ANCHA
    # --------------------------------------------------------

    tabla_ancha = df.pivot(
        index=["departamento_clave", "anio"],
        columns="nivel_formacion",
        values="tasa_desercion",
    ).reset_index()

    tabla_ancha.columns.name = None

    columnas_niveles = {
        "Universitario": "tasa_desercion_universitario",
        "TyT": "tasa_desercion_tyt",
        "Técnico Profesional": (
            "tasa_desercion_tecnico_profesional"
        ),
        "Tecnológico": "tasa_desercion_tecnologico",
    }

    tabla_ancha = tabla_ancha.rename(
        columns=columnas_niveles
    )

    return tabla_ancha


# ============================================================
# VALIDACIONES PREVIAS AL JOIN
# ============================================================

def validar_claves_integracion(matriculas, desercion):
    """Comprueba las claves antes de integrar las fuentes."""

    claves = ["departamento_clave", "anio"]

    for nombre, df in [
        ("Matrículas", matriculas),
        ("Deserción", desercion),
    ]:

        if df[claves].isna().any().any():
            raise ValueError(
                f"{nombre} contiene claves de integración nulas."
            )

        if df.duplicated(subset=claves).any():
            raise ValueError(
                f"{nombre} contiene claves departamento-año repetidas."
            )

    print("\nValidación previa del JOIN:")
    print(" - Claves nulas: 0")
    print(" - Claves duplicadas: 0")
    print(" - Ambas fuentes listas para integración.")


# ============================================================
# INTEGRACIÓN GOLD Y AUDITORÍAS DEL JOIN
# ============================================================

def integrar_datos():
    """Integra las fuentes a nivel departamento-año."""

    os.makedirs(RUTA_GOLD, exist_ok=True)

    print("\n======================================")
    print("INICIANDO INTEGRACIÓN CAPA GOLD")
    print("======================================")

    matriculas = preparar_matriculas()
    desercion = preparar_desercion()

    # --------------------------------------------------------
    # VALIDAR CLAVES ANTES DE INTEGRAR
    # --------------------------------------------------------

    validar_claves_integracion(
        matriculas,
        desercion
    )

    # --------------------------------------------------------
    # JOIN
    # --------------------------------------------------------

    # SPADIES es la base del análisis.
    # Se conservan sus registros aunque no tengan matrícula.

    gold = pd.merge(
        desercion,
        matriculas,
        on=["departamento_clave", "anio"],
        how="left",
        validate="one_to_one",
        indicator=True,
    )

    gold["coincidio_matricula"] = (
        gold["_merge"] == "both"
    )

    gold = gold.drop(columns=["_merge"])

    # --------------------------------------------------------
    # VALIDACIONES POSTERIORES AL JOIN
    # --------------------------------------------------------

    claves_gold = [
        "departamento_clave",
        "anio",
    ]

    if gold.duplicated(subset=claves_gold).any():
        raise ValueError(
            "La tabla Gold contiene claves departamento-año repetidas."
        )

    if gold[claves_gold].isna().any().any():
        raise ValueError(
            "La tabla Gold contiene claves de integración nulas."
        )

    if len(gold) != len(desercion):
        raise ValueError(
            "El JOIN modificó la cantidad de filas de SPADIES "
            "en una integración LEFT."
        )

    # --------------------------------------------------------
    # AUDITORÍA DE COBERTURA POR AÑO
    # --------------------------------------------------------

    coincidencias = int(
        gold["coincidio_matricula"].sum()
    )

    sin_coincidencia = (
        len(gold) - coincidencias
    )

    auditoria_join = (
        gold.groupby("anio")
        .agg(
            departamentos_con_desercion=(
                "departamento_clave",
                "nunique"
            ),
            coincidencias_matricula=(
                "coincidio_matricula",
                "sum"
            ),
            sin_coincidencia=(
                "coincidio_matricula",
                lambda serie: (~serie).sum()
            ),
        )
        .reset_index()
    )

    auditoria_join["porcentaje_cobertura"] = (
        auditoria_join["coincidencias_matricula"]
        / auditoria_join["departamentos_con_desercion"]
        * 100
    ).round(2)

    auditoria_join.to_csv(
        ARCHIVO_AUDITORIA_JOIN,
        index=False,
        encoding="utf-8-sig"
    )

    print("\nAuditoría de cobertura del JOIN:")
    print(
        auditoria_join.to_string(index=False)
    )

    # --------------------------------------------------------
    # AUDITORÍA DE COMBINACIONES SIN COINCIDENCIA
    # --------------------------------------------------------

    sin_match = gold.loc[
        ~gold["coincidio_matricula"],
        ["departamento_clave", "anio"]
    ].copy()

    if not matriculas.empty:
        anio_minimo_api = int(matriculas["anio"].min())
        anio_maximo_api = int(matriculas["anio"].max())

        def explicar_sin_coincidencia(anio):
            if anio < anio_minimo_api:
                return "Año anterior al periodo disponible en API"

            if anio > anio_maximo_api:
                return "Año posterior al periodo disponible en API"

            return (
                "No se encontró combinación departamento-año "
                "en la API"
            )

        sin_match["motivo_sin_coincidencia"] = (
            sin_match["anio"].apply(
                explicar_sin_coincidencia
            )
        )

    else:
        sin_match["motivo_sin_coincidencia"] = (
            "La fuente de matrículas no contiene registros válidos"
        )

    sin_match.to_csv(
        ARCHIVO_JOIN_SIN_COINCIDENCIA,
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------------
    # ORGANIZACIÓN DE COLUMNAS GOLD
    # --------------------------------------------------------

    columnas_iniciales = [
        "departamento_clave",
        "anio",
        "tasa_desercion_universitario",
        "tasa_desercion_tyt",
        "tasa_desercion_tecnico_profesional",
        "tasa_desercion_tecnologico",
        "suma_matriculas_reportadas",
        "registros_matricula",
        "coincidio_matricula",
    ]

    columnas_disponibles = [
        columna
        for columna in columnas_iniciales
        if columna in gold.columns
    ]

    gold = gold[columnas_disponibles]

    # --------------------------------------------------------
    # EXPORTACIÓN GOLD
    # --------------------------------------------------------

    gold.to_csv(
        ARCHIVO_FINAL,
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------------
    # RESUMEN FINAL
    # --------------------------------------------------------

    print("\n======================================")
    print("INTEGRACIÓN GOLD COMPLETADA")
    print("======================================")

    print(f"Registros finales: {len(gold):,}")
    print(f"Coincidencias con matrículas: {coincidencias:,}")
    print(f"Sin coincidencia: {sin_coincidencia:,}")

    print(
        "Claves departamento-año duplicadas: "
        f"{gold.duplicated(subset=claves_gold).sum()}"
    )

    print(
        f"Periodo de deserción: "
        f"{gold['anio'].min()} - {gold['anio'].max()}"
    )

    print(
        "Departamentos analizados: "
        f"{gold['departamento_clave'].nunique()}"
    )

    print(f"\nArchivo Gold generado: {ARCHIVO_FINAL}")

    print("\nReportes de auditoría generados:")
    print(f" - {ARCHIVO_AUDITORIA_MATRICULAS}")
    print(f" - {ARCHIVO_MATRICULAS_EXCLUIDAS}")
    print(f" - {ARCHIVO_AUDITORIA_JOIN}")
    print(f" - {ARCHIVO_JOIN_SIN_COINCIDENCIA}")

    print(
        "\nNota metodológica:"
        "\nLa integración se realiza por departamento y año, "
        "debido a que las tasas de deserción utilizadas "
        "están agregadas a ese nivel."
        "\nLas matrículas corresponden a sumas de valores "
        "reportados por la fuente y no representan "
        "necesariamente estudiantes únicos."
        "\nLos resultados no permiten atribuir tasas de "
        "deserción a instituciones o programas específicos "
        "ni establecer relaciones causales."
    )

    return gold


# ============================================================
# EJECUCIÓN DIRECTA
# ============================================================

if __name__ == "__main__":
    integrar_datos()
