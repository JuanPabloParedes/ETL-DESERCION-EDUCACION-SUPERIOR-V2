# ETL — Deserción en la Educación Superior en Colombia

## 1. Descripción del proyecto

Este proyecto desarrolla un proceso ETL para trabajar con información relacionada con la deserción y la matrícula en la educación superior en Colombia, utilizando fuentes de datos públicas.

El proceso se organiza mediante la arquitectura Medallion:

- **Bronze:** extracción y almacenamiento de los datos de origen.
- **Silver:** limpieza y estandarización de los datos.
- **Gold:** integración de las fuentes y generación del conjunto de datos final.

Este documento describe principalmente la etapa **Bronze: Extracción**, a cargo del integrante responsable de obtener y almacenar los datos originales.

## 2. Objetivo de la etapa Bronze

Obtener información de las fuentes seleccionadas y almacenarla en el proyecto para que pueda ser utilizada en las etapas posteriores.

Las actividades realizadas son:

- Leer el archivo Excel con estadísticas de deserción.
- Extraer las hojas seleccionadas y guardarlas en archivos CSV.
- Consultar una API REST con información de matrícula en educación superior.
- Guardar las respuestas de la API en archivos JSON.
- Documentar las fuentes, los archivos generados y los procedimientos de ejecución.

La etapa Bronze no realiza la limpieza de duplicados, el tratamiento de valores nulos, la normalización de variables ni la integración de las fuentes. Estas actividades corresponden a las etapas posteriores.

## 3. Fuentes de datos

### 3.1. Archivo Excel de estadísticas de deserción

**Archivo original:** `articles-415244_recurso_19.xlsx`

**Ubicación:** `data/bronze/`

El archivo contiene estadísticas relacionadas con la deserción y la permanencia en la educación superior. Se seleccionaron nueve hojas para su extracción:

1. TD - departamento
2. TD - metodología
3. TD - sexo
4. TD - sector
5. TD - área de conocimiento
6. Tasa deserción cohorte acumulad
7. TDCA - departamento
8. TDCA - metodología
9. TGA - departamento

Las hojas incluyen información desagregada por categorías como departamento, metodología, sexo, sector y área de conocimiento, así como indicadores de deserción y graduación por cohorte.

**Salida:** archivos CSV almacenados en `data/bronze/excel_extraido/`.

El archivo Excel original se conserva en Bronze. Al exportar las hojas a CSV se excluyen las filas y columnas completamente vacías; los valores de las celdas con información no se transforman intencionalmente.

### 3.2. API REST de matrícula en educación superior

**Fuente:** datos.gov.co — conjunto de datos identificado como `5wck-szir`.

**Endpoint utilizado:**

https://www.datos.gov.co/resource/5wck-szir.json

La API proporciona registros relacionados con la matrícula en educación superior. Esta fuente es complementaria a las estadísticas de deserción del Excel.

El script consulta la API por lotes de hasta 50.000 registros, utilizando los parámetros `$limit` y `$offset`, y guarda las respuestas en archivos JSON.

**Ubicación de los archivos:** `data/bronze/api/`.

En la ejecución documentada se descargaron 390.903 registros, distribuidos en ocho archivos JSON. Esta cantidad corresponde a esa ejecución y puede cambiar si la fuente se actualiza.

Los archivos JSON conservan el contenido de las respuestas recibidas, sin realizar transformaciones de sus campos.

## 4. Estructura del proyecto

```text
ETL-DESERCION-EDUCACION-SUPERIOR-V2/
│
├── data/
│   └── bronze/
│       ├── articles-415244_recurso_19.xlsx
│       ├── excel_extraido/
│       │   ├── tasa_desercion_cohorte_acumulad.csv
│       │   ├── td_area_de_conocimiento.csv
│       │   ├── td_departamento.csv
│       │   ├── td_metodologia.csv
│       │   ├── td_sector.csv
│       │   ├── td_sexo.csv
│       │   ├── tdca_departamento.csv
│       │   ├── tdca_metodologia.csv
│       │   └── tga_departamento.csv
│       │
│       └── api/
│           ├── matricula_api_parte_001.json
│           ├── matricula_api_parte_002.json
│           ├── matricula_api_parte_003.json
│           ├── matricula_api_parte_004.json
│           ├── matricula_api_parte_005.json
│           ├── matricula_api_parte_006.json
│           ├── matricula_api_parte_007.json
│           └── matricula_api_parte_008.json
│
├── src/
│   └── extraction/
│       ├── extraction_excel.py
│       └── extraction_api.py
│
├── requirements.txt
└── README.md
```

## 5. Requisitos

Para ejecutar los scripts se requiere:

- Python 3.10 o compatible.
- Acceso a internet para consultar la API.
- Las dependencias indicadas en `requirements.txt`.

## 6. Instalación del entorno

Desde la carpeta principal del proyecto, abrir una terminal y ejecutar:

```bash
python -m venv .venv
```

Activar el entorno virtual en Windows:

```bash
.venv\Scripts\activate
```

Instalar las dependencias:

```bash
python -m pip install -r requirements.txt
```

## 7. Ejecución de la extracción

Los siguientes comandos deben ejecutarse desde la carpeta principal del repositorio.

### 7.1. Extraer el Excel

```bash
python src/extraction/extraction_excel.py
```

El script lee las nueve hojas seleccionadas y genera sus archivos CSV en:

```text
data/bronze/excel_extraido/
```

Al finalizar, muestra el número de filas y columnas de cada hoja extraída.

### 7.2. Extraer la API REST

```bash
python src/extraction/extraction_api.py
```

El script consulta el endpoint de matrícula y almacena las respuestas JSON en:

```text
data/bronze/api/
```

La extracción requiere conexión a internet. El número de registros y archivos puede variar si la fuente cambia.

## 8. Dependencias

El archivo `requirements.txt` contiene las librerías utilizadas:

- `pandas`: lectura del Excel y exportación a CSV.
- `openpyxl`: soporte para lectura de archivos Excel.
- `requests`: consultas HTTP a la API REST.

## 9. Consideraciones sobre los datos

- El Excel original se conserva como fuente de referencia.
- Los CSV son exportaciones de las hojas seleccionadas; no conservan todas las características de formato del Excel.
- Los JSON contienen las respuestas recibidas de la API.
- La información de matrícula y la información de deserción corresponden a indicadores diferentes. No se deben considerar directamente integrables sin revisar sus campos, periodos y categorías.
- La extracción de la API puede generar archivos nuevos si la fuente cambia.
- La limpieza, la integración y la creación de indicadores finales se desarrollan en las etapas Silver y Gold, fuera del alcance de esta etapa.

## 10. Responsable de la etapa

**Responsabilidad:** Integrante 1 — Extracción y Bronze.

**Entregables:**

- Script de extracción del Excel.
- Script de extracción de la API REST.
- Archivo Excel original.
- CSV generados a partir de las nueve hojas seleccionadas.
- Respuestas JSON obtenidas de la API.
- Instrucciones para reproducir las extracciones.

---

Proyecto académico de ETL sobre deserción en la educación superior en Colombia.