 
import os
import re
import unicodedata
import pandas as pd

# Rutas del proyecto
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


def normalizar_departamento(valor):
    """Normaliza nombres de departamentos."""
    if pd.isna(valor):
        return None

    texto = str(valor).strip().upper()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        c for c in texto if not unicodedata.combining(c)
    )
    texto = re.sub(r"[^\w\s]", "", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto


def integrar_datos():
    print("=== INTEGRACIÓN SILVER -> GOLD ===")

    # 1. Leer archivos Silver
    matricula = pd.read_csv(
        ARCHIVO_MATRICULA, low_memory=False
    )
    desercion = pd.read_csv(
        ARCHIVO_DESERCION, low_memory=False
    )

    print(f"Registros de matrícula: {len(matricula):,}")
    print(f"Registros de deserción: {len(desercion):,}")

    # 2. Validar columnas de matrícula
    columnas_matricula = [
        "departamento_de_oferta_del_programa",
        "a_o",
        "matriculados_2015",
    ]

    for columna in columnas_matricula:
        if columna not in matricula.columns:
            raise ValueError(
                f"Falta la columna de matrícula: {columna}"
            )

    # 3. Preparar matrícula
    matricula["departamento_clave"] = (
        matricula["departamento_de_oferta_del_programa"]
        .apply(normalizar_departamento)
    )

    matricula["anio"] = pd.to_numeric(
        matricula["a_o"], errors="coerce"
    )

    matricula["matriculados_2015"] = pd.to_numeric(
        matricula["matriculados_2015"], errors="coerce"
    )

    matricula = matricula.dropna(
        subset=["departamento_clave", "anio"]
    )

    # Agregar matrícula por departamento y año
    matricula_agregada = (
        matricula.groupby(
            ["departamento_clave", "anio"],
            as_index=False
        )
        .agg(
            departamento_matricula=(
                "departamento_de_oferta_del_programa",
                "first"
            ),
            matricula_reportada=(
                "matriculados_2015", "sum"
            ),
            registros_matricula=(
                "matriculados_2015", "count"
            ),
        )
    )

    print(
        "Grupos de matrícula agregados:",
        len(matricula_agregada)
    )

    # 4. Validar y preparar deserción
    columnas_desercion = [
        "departamento",
        "nivel_formacion",
        "anio",
        "tasa_desercion",
    ]

    for columna in columnas_desercion:
        if columna not in desercion.columns:
            raise ValueError(
                f"Falta la columna de deserción: {columna}. "
                "Ejecuta primero limpiar_desercion_departamento.py."
            )

    desercion_larga = desercion.copy()

    desercion_larga["departamento_clave"] = (
        desercion_larga["departamento"]
        .apply(normalizar_departamento)
    )

    desercion_larga["anio"] = pd.to_numeric(
        desercion_larga["anio"], errors="coerce"
    )

    desercion_larga["tasa_desercion"] = pd.to_numeric(
        desercion_larga["tasa_desercion"],
        errors="coerce"
    )

    desercion_larga = desercion_larga.dropna(
        subset=[
            "departamento_clave",
            "anio",
            "nivel_formacion",
            "tasa_desercion",
        ]
    )

    desercion_larga = desercion_larga[
        desercion_larga["tasa_desercion"].between(0, 1)
    ].copy()

    # Validar unicidad por departamento, nivel y año
    claves = [
        "departamento_clave",
        "nivel_formacion",
        "anio",
    ]

    duplicados = desercion_larga.duplicated(
        subset=claves, keep=False
    )

    if duplicados.any():
        print(
            desercion_larga.loc[
                duplicados,
                claves + ["tasa_desercion"],
            ].head(20).to_string(index=False)
        )
        raise ValueError(
            "Hay tasas repetidas para el mismo departamento, "
            "nivel de formación y año."
        )

    print(
        "Registros de deserción válidos:",
        len(desercion_larga)
    )

    # 5. Integrar por departamento y año.
    # La tasa conserva su nivel de formación.
    # La matrícula corresponde al total agregado disponible
    # para el departamento y año, no a un nivel específico.
    integrado = pd.merge(
        desercion_larga,
        matricula_agregada,
        on=["departamento_clave", "anio"],
        how="left",
        validate="many_to_one",
        indicator=True,
    )

    integrado["coincidio_matricula"] = (
        integrado["_merge"] == "both"
    )

    integrado = integrado.drop(columns=["_merge"])

    # 6. Organizar columnas del Gold
    integrado = integrado.rename(
        columns={
            "departamento": "departamento_desercion",
        }
    )

    columnas_finales = [
        "departamento_desercion",
        "departamento_matricula",
        "departamento_clave",
        "nivel_formacion",
        "anio",
        "tasa_desercion",
        "matricula_reportada",
        "registros_matricula",
        "coincidio_matricula",
    ]

    integrado = integrado[columnas_finales]

    # 7. Guardar Gold
    os.makedirs(RUTA_GOLD, exist_ok=True)

    integrado.to_csv(
        ARCHIVO_FINAL,
        index=False,
        encoding="utf-8"
    )

    # 8. Validaciones
    print("\n=== VALIDACIÓN GOLD ===")
    print("Filas Gold:", len(integrado))
    print(
        "Departamentos:",
        integrado["departamento_clave"].nunique()
    )
    print(
        "Años:",
        integrado["anio"].min(),
        "-",
        integrado["anio"].max()
    )
    print(
        "Filas con matrícula coincidente:",
        int(integrado["coincidio_matricula"].sum())
    )
    print(
        "Filas sin matrícula coincidente:",
        int((~integrado["coincidio_matricula"]).sum())
    )
    print(
        "Niveles de formación:\n",
        integrado["nivel_formacion"].value_counts().to_string()
    )
    print("Archivo Gold guardado en:", ARCHIVO_FINAL)

    print(
        "\nIMPORTANTE: matricula_reportada suma la columna "
        "matriculados_2015. Confirma su significado antes "
        "de interpretar ese valor como matrícula total."
    )


if __name__ == "__main__":
    integrar_datos()
