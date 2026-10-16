# Resumen de Procesamiento Capa Silver - V2

## 1. Consolidación de Matrícula (API `5wck-szir`)
- **Entrada:** 8 archivos JSON en `data/bronze/api/` (390,903 registros totales).
- **Procesamiento:** 
  - Consolidación de partes JSON.
  - Conversión de columnas a `snake_case`.
  - Normalización de códigos DANE.
  - Eliminación de 106,599 duplicados exactos.
- **Salida:** `data/silver/silver_matricula_api_consolidado.csv` (284,304 registros únicos).

## 2. Consolidación de Deserción (Excel)
- **Entrada:** 9 archivos CSV en `data/bronze/excel_extraido/`.
- **Procesamiento:** Estandarización de nombres de columnas y formateo de códigos territoriales.
- **Salida:** 9 archivos `silver_*.csv` en `data/silver/`.