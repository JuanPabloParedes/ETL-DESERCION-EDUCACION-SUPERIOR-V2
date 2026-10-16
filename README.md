# ETL — Deserción y Matrícula en la Educación Superior en Colombia

## 1. Descripción del Proyecto
Este proyecto implementa un proceso de Extracción, Transformación y Carga (ETL) para analizar la deserción y la matrícula estudiantil en la educación superior en Colombia. El flujo de datos utiliza fuentes públicas oficiales del Ministerio de Educación Nacional (MEN) y de la plataforma Datos Abiertos (`datos.gov.co`).

El proyecto está estructurado bajo la **Arquitectura Medallion**:
- **Bronze (Extracción):** Almacenamiento de datos crudos extraídos de archivos Excel y de la API REST de matrícula.
- **Silver (Transformación y Limpieza):** Estandarización de nombres, depuración de registros duplicados, normalización de códigos DANE y generación de tablas limpias.
- **Gold (Integración y Análisis):** Unificación de las fuentes por departamento, nivel de formación y año, generando el dataset definitivo para la evaluación de KPIs y visualización.

---

## 2. Contexto del Problema y Objetivo General
La deserción estudiantil en la educación superior colombiana representa un desafío crítico para las políticas públicas y las instituciones académicas.

**Objetivo General:** Contribuir a la caracterización y análisis de la deserción universitaria mediante la integración y calidad de datos de matrícula y deserción a nivel territorial y por nivel de formación durante el periodo 2010-2024.

---

## 3. Fuentes de Datos
1. **Estadísticas de Deserción (Excel / MEN):**
   - Archivo original: `data/bronze/articles-415244_recurso_19.xlsx`
   - Hoja principal extraída: `TD - departamento` (exportada a `data/bronze/excel_extraido/td_departamento.csv`).
   - *Nota de reproducibilidad:* Debido a su tamaño en repositorio, el archivo original `td_departamento.csv` se genera mediante el script de extracción de Excel o debe ubicarse en la carpeta `data/bronze/excel_extraido/` para reprocesar Silver desde cero.
2. **API REST de Matrícula (`datos.gov.co`):**
   - Endpoint: Dataset `5wck-szir` (`https://www.datos.gov.co/resource/5wck-szir.json`).
   - Descargado por lotes y almacenado en `data/bronze/api/matricula_api_parte_*.json`.

---

## 4. Estructura del Repositorio

```text
ETL-DESERCION-EDUCACION-SUPERIOR-V2/
├── data/
│   ├── bronze/
│   │   ├── articles-415244_recurso_19.xlsx
│   │   ├── excel_extraido/*.csv
│   │   └── api/*.json
│   ├── silver/
│   │   ├── silver_desercion_departamento.csv
│   │   ├── silver_matricula_api.csv
│   │   └── silver_dataset_integrado.csv
│   └── gold/
│       └── gold_final.csv
├── src/
│   ├── extraction/
│   │   ├── extraction_excel.py
│   │   └── extraction_api.py
│   ├── transformation/
│   │   ├── limpiar_desercion_departamento.py
│   │   └── transform_silver.py
│   └── validation/
│       └── validar_calidad.py
├── notebooks/
│   └── analisis_desercion_gold.ipynb
├── docs/
│   └── resumen_silver.md
├── check_env.py
├── integrar_datos.py
├── main.py
├── run_notebook.py
├── requirements.txt
├── .gitignore
└── README.md