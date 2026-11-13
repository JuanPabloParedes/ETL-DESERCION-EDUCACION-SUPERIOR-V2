
import unittest
import pandas as pd
from unittest.mock import patch

from src.validation import validar_calidad as vc


def gold_valido():
    return pd.DataFrame({
        "departamento_clave": ["05", "76"],
        "anio": [2020, 2021],
        "tasa_desercion_universitario": [0.10, 0.12],
        "tasa_desercion_tyt": [0.15, None],
        "tasa_desercion_tecnico_profesional": [0.20, 0.18],
        "tasa_desercion_tecnologico": [0.13, 0.14],
        "suma_matriculas_reportadas": [1000, None],
        "registros_matricula": [10, None],
        "coincidio_matricula": [True, False],
    })


class TestConversiones(unittest.TestCase):

    def test_convierte_numeros(self):
        resultado = vc.convertir_numerico_validado(
            pd.Series(["10", "20"]), "cantidad"
        )
        self.assertEqual(resultado.tolist(), [10, 20])

    def test_rechaza_texto_no_numerico(self):
        with self.assertRaises(ValueError):
            vc.convertir_numerico_validado(
                pd.Series(["10", "error"]), "cantidad"
            )

    def test_rechaza_infinitos(self):
        with self.assertRaises(ValueError):
            vc.convertir_numerico_validado(
                pd.Series([10, float("inf")]), "cantidad"
            )

    def test_rechaza_na_no_permitido(self):
        with self.assertRaises(ValueError):
            vc.convertir_numerico_validado(
                pd.Series([10, None]), "cantidad",
                permitir_na=False
            )

    def test_convierte_booleanos(self):
        resultado = vc.convertir_booleanos(
            pd.Series(["true", "false", "1", "0"])
        )
        self.assertEqual(
            resultado.tolist(), [True, False, True, False]
        )

    def test_rechaza_booleano_invalido(self):
        with self.assertRaises(ValueError):
            vc.convertir_booleanos(
                pd.Series(["true", "desconocido"])
            )


class TestValidacionGold(unittest.TestCase):

    def validar_dataframe(self, datos):
        with patch.object(
            vc, "validar_archivo", return_value=datos
        ):
            vc.validar_gold()

    def test_gold_valido(self):
        self.validar_dataframe(gold_valido())

    def test_rechaza_claves_duplicadas(self):
        datos = gold_valido()
        datos.loc[1, "departamento_clave"] = "05"
        datos.loc[1, "anio"] = 2020

        with self.assertRaises(ValueError):
            self.validar_dataframe(datos)

    def test_rechaza_tasa_fuera_de_rango(self):
        datos = gold_valido()
        datos.loc[0, "tasa_desercion_universitario"] = 1.5

        with self.assertRaises(ValueError):
            self.validar_dataframe(datos)

    def test_rechaza_matriculas_negativas(self):
        datos = gold_valido()
        datos.loc[0, "suma_matriculas_reportadas"] = -10

        with self.assertRaises(ValueError):
            self.validar_dataframe(datos)

    def test_rechaza_registros_decimales(self):
        datos = gold_valido()
        datos.loc[0, "registros_matricula"] = 2.5

        with self.assertRaises(ValueError):
            self.validar_dataframe(datos)

    def test_rechaza_coincidencia_sin_matriculas(self):
        datos = gold_valido()
        datos.loc[0, "suma_matriculas_reportadas"] = None

        with self.assertRaises(ValueError):
            self.validar_dataframe(datos)

    def test_rechaza_datos_sin_coincidencia(self):
        datos = gold_valido()
        datos.loc[1, "suma_matriculas_reportadas"] = 500

        with self.assertRaises(ValueError):
            self.validar_dataframe(datos)

    def test_rechaza_anio_decimal(self):
        datos = gold_valido()
        datos.loc[0, "anio"] = 2020.5

        with self.assertRaises(ValueError):
            self.validar_dataframe(datos)

    def test_rechaza_departamento_vacio(self):
        datos = gold_valido()
        datos.loc[0, "departamento_clave"] = " "

        with self.assertRaises(ValueError):
            self.validar_dataframe(datos)


if __name__ == "__main__":
    unittest.main()
