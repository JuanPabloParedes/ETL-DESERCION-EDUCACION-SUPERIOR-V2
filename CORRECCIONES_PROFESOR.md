# Correcciones realizadas a partir de las observaciones del profesor

## 1. Revisión del JOIN y nivel de granularidad

Se revisó el nivel de granularidad de las fuentes utilizadas para la integración. La información de matrículas contiene datos de instituciones y programas académicos, mientras que las tasas de deserción obtenidas de SPADIES están agregadas por departamento, nivel de formación y año.

Por esta razón, la integración se realiza utilizando las claves `departamento_clave` y `anio`. No se realiza una asociación directa por institución o programa, debido a que la fuente de deserción utilizada no dispone de tasas con ese nivel de detalle.

Esta decisión evita asignar una misma tasa departamental a instituciones o programas específicos como si representara su comportamiento individual.

**Limitación:** la observación relacionada con la integración a nivel de institución y programa no puede resolverse completamente con las fuentes actuales. Para hacerlo sería necesario disponer de una fuente de deserción con información comparable a nivel institucional o de programa académico.

## 2. Validación de claves y cardinalidad

Se incorporaron controles para identificar claves nulas y duplicadas antes de realizar la integración.

También se implementó una validación de cardinalidad uno a uno mediante el parámetro `validate="one_to_one"` de Pandas. Posteriormente, se comprueba que las claves departamento-año sean únicas en Gold y que el LEFT JOIN conserve los registros provenientes de SPADIES.

Adicionalmente, se generan reportes de cobertura y de registros sin coincidencia para identificar los periodos en los que no existen datos de matrículas disponibles.

## 3. Revisión de registros con cantidades diferentes

Se identificaron 14 grupos de registros que comparten las dimensiones de identificación, pero presentan diferentes valores en la cantidad de matrículas reportadas.

La auditoría permite observar diferencias entre los valores mínimos y máximos de algunos grupos. Por ejemplo, se identificaron registros asociados a programas de instituciones como la Universidad del Tolima, la Universidad Autónoma de Bucaramanga y la Universidad Tecnológica de Bolívar.

Estos grupos no se clasifican automáticamente como duplicados exactos ni se eliminan, debido a que presentan diferencias en el valor de matrícula. Se conservan y se documentan mediante el archivo `auditoria_matriculas_cantidades_diferentes.csv`.

La auditoría identifica las diferencias, pero no permite establecer por sí sola su causa. Por tanto, no se asume que los valores diferentes sean errores ni que representen estudiantes únicos.

## 4. Revisión de la clasificación de riesgo

Se retiró la clasificación de riesgo de la capa Gold, debido a que las tasas utilizadas corresponden a un nivel departamental.

Una clasificación de riesgo institucional o por programa requeriría indicadores calculados con información de esa misma granularidad. Mantener dicha clasificación con los datos actuales podría generar interpretaciones incorrectas.

## 5. Fortalecimiento de las validaciones de calidad

Se fortalecieron las validaciones de las capas Silver y Gold mediante controles para verificar:

- Existencia y lectura de los archivos requeridos.
- Presencia de columnas obligatorias.
- Valores numéricos e identificación de valores infinitos.
- Cantidades de matrículas negativas.
- Claves nulas y duplicadas.
- Tasas de deserción dentro del rango permitido de 0 a 1.
- Años expresados como números enteros.
- Cantidades de registros no negativas y enteras.
- Consistencia entre las coincidencias del JOIN y los valores de matrícula.

Los valores faltantes de las tasas y los registros sin coincidencia de matrículas se conservan como valores ausentes. No se reemplazan automáticamente por cero, ya que la ausencia de información no equivale a un valor de cero.

## 6. Ampliación de las pruebas automatizadas

Se ampliaron las pruebas automatizadas de 21 a **36 casos**, ejecutados mediante `unittest`.

Las pruebas cubren:

- Extracción de información desde la API y archivos Excel.
- Transformaciones y normalización de datos.
- Preparación y validación de las fuentes de matrículas y deserción.
- Validación de claves para la integración.
- Conservación de registros y generación de auditorías en Gold.
- Conversión y validación de valores numéricos y booleanos.
- Detección de tasas fuera de rango, cantidades negativas, claves duplicadas y años no enteros.
- Consistencia entre los indicadores de coincidencia y los valores de matrícula.

En la última ejecución se obtuvo el resultado:

`Ran 36 tests ... OK`

Esto confirma que las 36 pruebas implementadas finalizaron satisfactoriamente.

## 7. Limitaciones metodológicas y cobertura

El proyecto presenta un análisis descriptivo a nivel departamental. Las sumas de matrículas corresponden a valores reportados por la fuente y no necesariamente representan estudiantes únicos.

La integración no permite atribuir tasas de deserción a instituciones o programas específicos, identificar motivos individuales de deserción ni establecer relaciones causales entre las variables.

La cobertura temporal de las fuentes es diferente: SPADIES contiene información entre 2010 y 2024, mientras que la API de matrículas utilizada contiene registros entre 2015 y 2021.

Por tanto, la coincidencia temporal de las fuentes se concentra en el periodo 2015–2021. Los registros de deserción de los demás años permanecen en Gold sin coincidencia de matrículas, situación que se documenta en los reportes de cobertura del JOIN.

## 8. Archivos de auditoría y validación generados

Como resultado de las correcciones se generan los siguientes reportes:

- `auditoria_calidad_matriculas.csv`
- `auditoria_registros_matricula_excluidos.csv`
- `auditoria_cobertura_join_por_anio.csv`
- `auditoria_join_sin_coincidencia.csv`
- `auditoria_matriculas_por_anio.csv`
- `auditoria_matriculas_cantidades_diferentes.csv`

Estos archivos permiten consultar los controles realizados, los registros excluidos, las diferencias identificadas y la cobertura de la integración.
