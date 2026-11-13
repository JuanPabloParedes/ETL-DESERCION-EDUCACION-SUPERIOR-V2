
import json
import tempfile
import unittest

from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd

from src.extraction import extraction_api
from src.extraction import extraction_excel
from src.transformation import transform_silver

from integrar_datos import (
    normalizar_departamento,
    normalizar_codigo,
    preparar_matriculas,
    preparar_desercion,
    validar_claves_integracion,
    integrar_datos,
)


class TestExtraccionAPI(unittest.TestCase):

    def test_extraer_api_guarda_json(self):
        with tempfile.TemporaryDirectory() as temporal:
            carpeta = Path(temporal)

            respuesta = MagicMock()
            respuesta.content = b'[{"id": 1}]'
            respuesta.json.return_value = [{"id": 1}]

            sesion = MagicMock()
            sesion.get.return_value = respuesta

            with patch.object(
                extraction_api,
                "OUTPUT_DIR",
                carpeta
            ), patch.object(
                extraction_api.requests,
                "Session",
                return_value=sesion
            ):
                extraction_api.extraer_api()

            archivo = carpeta / "matricula_api_parte_001.json"

            self.assertTrue(archivo.exists())

            with open(archivo, encoding="utf-8") as entrada:
                datos = json.load(entrada)

            self.assertEqual(len(datos), 1)
            self.assertEqual(datos[0]["id"], 1)


class TestExtraccionExcel(unittest.TestCase):

    def test_extraer_excel_genera_csv(self):
        with tempfile.TemporaryDirectory() as temporal:
            carpeta = Path(temporal)

            excel_falso = carpeta / "archivo.xlsx"
            excel_falso.touch()

            datos = pd.DataFrame([
                ["Titulo", None, None, None],
                ["Departamento", "2015", "2016", "2017"],
                ["Antioquia", 0.12, 0.13, 0.14],
            ])

            libro = MagicMock()
            libro.sheet_names = ["TD - departamento"]

            hojas_originales = extraction_excel.HOJAS.copy()

            try:
                with patch.object(
                    extraction_excel,
                    "EXCEL_FILE",
                    excel_falso
                ), patch.object(
                    extraction_excel,
                    "OUTPUT_DIR",
                    carpeta / "salida"
                ), patch.object(
                    extraction_excel.pd,
                    "ExcelFile",
                    return_value=libro
                ), patch.object(
                    extraction_excel.pd,
                    "read_excel",
                    return_value=datos
                ):
                    extraction_excel.HOJAS = [
                        "TD - departamento"
                    ]

                    extraction_excel.extraer_excel()

                archivo = (
                    carpeta
                    / "salida"
                    / "td_departamento.csv"
                )

                self.assertTrue(archivo.exists())

                resultado = pd.read_csv(
                    archivo,
                    header=None
                )

                self.assertGreater(len(resultado), 0)

            finally:
                extraction_excel.HOJAS = hojas_originales


class TestTransformaciones(unittest.TestCase):

    def test_codigo_dane_departamento(self):
        resultado = transform_silver.clean_dane_code(5, 2)
        self.assertEqual(resultado, "05")

    def test_codigo_dane_municipio(self):
        resultado = transform_silver.clean_dane_code(76001, 5)
        self.assertEqual(resultado, "76001")

    def test_codigo_vacio(self):
        resultado = transform_silver.clean_dane_code(None, 2)
        self.assertIsNone(resultado)

    def test_normalizacion_narino(self):
        resultado = normalizar_departamento("Nariño")
        self.assertEqual(resultado, "NARINO")

    def test_normalizacion_bogota(self):
        resultado = normalizar_departamento("Bogotá D.C.")
        self.assertEqual(resultado, "BOGOTA DC")

    def test_normalizacion_valor_nulo(self):
        resultado = normalizar_departamento(None)
        self.assertIsNone(resultado)

    def test_normalizacion_codigo(self):
        resultado = normalizar_codigo(5)
        self.assertEqual(resultado, "05")

    def test_codigo_no_numerico(self):
        resultado = normalizar_codigo("ABC")
        self.assertIsNone(resultado)


class TestPreparacionMatriculas(unittest.TestCase):

    def crear_archivo(self, carpeta, datos):
        archivo = Path(carpeta) / "matriculas.csv"
        pd.DataFrame(datos).to_csv(archivo, index=False)
        return archivo

    def test_agrega_matriculas_por_departamento_anio(self):
        with tempfile.TemporaryDirectory() as temporal:
            archivo = self.crear_archivo(
                temporal,
                {
                    "c_digo_del_departamento_programa": [
                        "05", "05", "76"
                    ],
                    "a_o": [2020, 2020, 2020],
                    "matriculados_2015": [100, 50, 200],
                }
            )

            with patch(
                "integrar_datos.ARCHIVO_MATRICULA",
                str(archivo)
            ), patch(
                "integrar_datos.ARCHIVO_AUDITORIA_MATRICULAS",
                str(Path(temporal) / "calidad.csv")
            ), patch(
                "integrar_datos.ARCHIVO_MATRICULAS_EXCLUIDAS",
                str(Path(temporal) / "excluidos.csv")
            ):
                resultado = preparar_matriculas()

            antioquia = resultado[
                resultado["departamento_clave"] == "ANTIOQUIA"
            ]

            self.assertEqual(len(antioquia), 1)
            self.assertEqual(
                antioquia["suma_matriculas_reportadas"].iloc[0],
                150
            )
            self.assertEqual(
                antioquia["registros_matricula"].iloc[0],
                2
            )

    def test_audita_registros_invalidos(self):
        with tempfile.TemporaryDirectory() as temporal:
            archivo = self.crear_archivo(
                temporal,
                {
                    "c_digo_del_departamento_programa": [
                        "05", "XX", "05"
                    ],
                    "a_o": [2020, 2020, "invalido"],
                    "matriculados_2015": [100, 50, 20],
                }
            )

            reporte_calidad = (
                Path(temporal) / "calidad.csv"
            )

            reporte_excluidos = (
                Path(temporal) / "excluidos.csv"
            )

            with patch(
                "integrar_datos.ARCHIVO_MATRICULA",
                str(archivo)
            ), patch(
                "integrar_datos.ARCHIVO_AUDITORIA_MATRICULAS",
                str(reporte_calidad)
            ), patch(
                "integrar_datos.ARCHIVO_MATRICULAS_EXCLUIDAS",
                str(reporte_excluidos)
            ):
                resultado = preparar_matriculas()

            auditoria = pd.read_csv(reporte_calidad)
            excluidos = pd.read_csv(reporte_excluidos)

            self.assertEqual(len(resultado), 1)
            self.assertEqual(
                auditoria["registros_excluidos"].iloc[0],
                2
            )
            self.assertEqual(len(excluidos), 2)
            self.assertIn(
                "motivo_exclusion",
                excluidos.columns
            )

    def test_rechaza_cantidad_negativa(self):
        with tempfile.TemporaryDirectory() as temporal:
            archivo = self.crear_archivo(
                temporal,
                {
                    "c_digo_del_departamento_programa": ["05"],
                    "a_o": [2020],
                    "matriculados_2015": [-10],
                }
            )

            with patch(
                "integrar_datos.ARCHIVO_MATRICULA",
                str(archivo)
            ), patch(
                "integrar_datos.ARCHIVO_AUDITORIA_MATRICULAS",
                str(Path(temporal) / "calidad.csv")
            ), patch(
                "integrar_datos.ARCHIVO_MATRICULAS_EXCLUIDAS",
                str(Path(temporal) / "excluidos.csv")
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "No existen registros válidos"
                ):
                    preparar_matriculas()


class TestPreparacionDesercion(unittest.TestCase):

    def preparar_archivo(self, temporal, datos):
        archivo = Path(temporal) / "desercion.csv"
        pd.DataFrame(datos).to_csv(archivo, index=False)
        return archivo

    def test_preparar_desercion_y_conservar_na(self):
        with tempfile.TemporaryDirectory() as temporal:
            archivo = self.preparar_archivo(
                temporal,
                {
                    "departamento": [
                        "Antioquia",
                        "Antioquia",
                        "Nariño",
                        "Nariño",
                    ],
                    "nivel_formacion": [
                        "Universitario",
                        "TyT",
                        "Universitario",
                        "TyT",
                    ],
                    "anio": [2020, 2020, 2020, 2020],
                    "tasa_desercion": [
                        0.12, 0.15, 0.18, None
                    ],
                }
            )

            with patch(
                "integrar_datos.ARCHIVO_DESERCION",
                str(archivo)
            ):
                resultado = preparar_desercion()

            self.assertEqual(len(resultado), 2)

            self.assertIn(
                "tasa_desercion_universitario",
                resultado.columns
            )

            self.assertIn(
                "tasa_desercion_tyt",
                resultado.columns
            )

            fila_narino = resultado[
                resultado["departamento_clave"] == "NARINO"
            ]

            self.assertTrue(
                pd.isna(
                    fila_narino[
                        "tasa_desercion_tyt"
                    ].iloc[0]
                )
            )

    def test_rechaza_claves_duplicadas(self):
        with tempfile.TemporaryDirectory() as temporal:
            archivo = self.preparar_archivo(
                temporal,
                {
                    "departamento": [
                        "Antioquia", "Antioquia"
                    ],
                    "nivel_formacion": [
                        "Universitario", "Universitario"
                    ],
                    "anio": [2020, 2020],
                    "tasa_desercion": [0.12, 0.15],
                }
            )

            with patch(
                "integrar_datos.ARCHIVO_DESERCION",
                str(archivo)
            ):
                with self.assertRaises(ValueError):
                    preparar_desercion()

    def test_rechaza_tasa_fuera_de_rango(self):
        with tempfile.TemporaryDirectory() as temporal:
            archivo = self.preparar_archivo(
                temporal,
                {
                    "departamento": ["Antioquia"],
                    "nivel_formacion": ["Universitario"],
                    "anio": [2020],
                    "tasa_desercion": [1.25],
                }
            )

            with patch(
                "integrar_datos.ARCHIVO_DESERCION",
                str(archivo)
            ):
                with self.assertRaises(ValueError):
                    preparar_desercion()

    def test_rechaza_nivel_no_reconocido(self):
        with tempfile.TemporaryDirectory() as temporal:
            archivo = self.preparar_archivo(
                temporal,
                {
                    "departamento": ["Antioquia"],
                    "nivel_formacion": ["Nivel desconocido"],
                    "anio": [2020],
                    "tasa_desercion": [0.20],
                }
            )

            with patch(
                "integrar_datos.ARCHIVO_DESERCION",
                str(archivo)
            ):
                with self.assertRaises(ValueError):
                    preparar_desercion()


class TestValidacionesJOIN(unittest.TestCase):

    def test_acepta_claves_unicas(self):
        matriculas = pd.DataFrame({
            "departamento_clave": [
                "ANTIOQUIA", "VALLE DEL CAUCA"
            ],
            "anio": [2020, 2020],
        })

        desercion = pd.DataFrame({
            "departamento_clave": [
                "ANTIOQUIA", "VALLE DEL CAUCA"
            ],
            "anio": [2020, 2020],
        })

        # No debe generar excepción.
        validar_claves_integracion(
            matriculas,
            desercion
        )

    def test_rechaza_claves_duplicadas(self):
        matriculas = pd.DataFrame({
            "departamento_clave": [
                "ANTIOQUIA", "ANTIOQUIA"
            ],
            "anio": [2020, 2020],
        })

        desercion = pd.DataFrame({
            "departamento_clave": ["ANTIOQUIA"],
            "anio": [2020],
        })

        with self.assertRaises(ValueError):
            validar_claves_integracion(
                matriculas,
                desercion
            )

    def test_rechaza_claves_nulas(self):
        matriculas = pd.DataFrame({
            "departamento_clave": [None],
            "anio": [2020],
        })

        desercion = pd.DataFrame({
            "departamento_clave": ["ANTIOQUIA"],
            "anio": [2020],
        })

        with self.assertRaises(ValueError):
            validar_claves_integracion(
                matriculas,
                desercion
            )


class TestIntegracionGold(unittest.TestCase):

    def test_join_conserva_filas_y_genera_auditorias(self):
        with tempfile.TemporaryDirectory() as temporal:

            carpeta = Path(temporal)

            matriculas = pd.DataFrame({
                "departamento_clave": ["ANTIOQUIA"],
                "anio": [2020],
                "suma_matriculas_reportadas": [1000],
                "registros_matricula": [10],
            })

            desercion = pd.DataFrame({
                "departamento_clave": [
                    "ANTIOQUIA",
                    "NARINO",
                ],
                "anio": [2020, 2020],
                "tasa_desercion_universitario": [
                    0.12, 0.15
                ],
                "tasa_desercion_tyt": [
                    0.14, None
                ],
                "tasa_desercion_tecnico_profesional": [
                    0.16, 0.17
                ],
                "tasa_desercion_tecnologico": [
                    0.18, 0.19
                ],
            })

            with patch(
                "integrar_datos.preparar_matriculas",
                return_value=matriculas
            ), patch(
                "integrar_datos.preparar_desercion",
                return_value=desercion
            ), patch(
                "integrar_datos.RUTA_GOLD",
                str(carpeta)
            ), patch(
                "integrar_datos.ARCHIVO_FINAL",
                str(carpeta / "gold.csv")
            ), patch(
                "integrar_datos.ARCHIVO_AUDITORIA_JOIN",
                str(carpeta / "cobertura.csv")
            ), patch(
                "integrar_datos.ARCHIVO_JOIN_SIN_COINCIDENCIA",
                str(carpeta / "sin_match.csv")
            ), patch(
                "integrar_datos.ARCHIVO_AUDITORIA_MATRICULAS",
                str(carpeta / "calidad.csv")
            ), patch(
                "integrar_datos.ARCHIVO_MATRICULAS_EXCLUIDAS",
                str(carpeta / "excluidos.csv")
            ):

                resultado = integrar_datos()

            self.assertEqual(len(resultado), 2)

            self.assertEqual(
                int(resultado["coincidio_matricula"].sum()),
                1
            )

            self.assertEqual(
                int((~resultado["coincidio_matricula"]).sum()),
                1
            )

            self.assertEqual(
                resultado.duplicated(
                    subset=["departamento_clave", "anio"]
                ).sum(),
                0
            )

            fila_sin_match = resultado[
                resultado["departamento_clave"] == "NARINO"
            ]

            self.assertTrue(
                pd.isna(
                    fila_sin_match[
                        "suma_matriculas_reportadas"
                    ].iloc[0]
                )
            )

            self.assertTrue(
                (carpeta / "gold.csv").exists()
            )

            self.assertTrue(
                (carpeta / "cobertura.csv").exists()
            )

            self.assertTrue(
                (carpeta / "sin_match.csv").exists()
            )

            cobertura = pd.read_csv(
                carpeta / "cobertura.csv"
            )

            self.assertEqual(
                cobertura["coincidencias_matricula"].sum(),
                1
            )

            sin_match = pd.read_csv(
                carpeta / "sin_match.csv"
            )

            self.assertEqual(len(sin_match), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
