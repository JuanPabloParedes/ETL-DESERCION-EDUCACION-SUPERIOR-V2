import logging
from pathlib import Path
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

BASE_DIR = Path(__file__).resolve().parent


def ejecutar_pipeline():
    logging.info("==================================================")
    logging.info("      INICIANDO PIPELINE ETL DE DESERCIÓN         ")
    logging.info("==================================================")

    # Paso 1: Transformación Silver (API + Excel + Limpieza de Departamentos)
    logging.info("\n[Paso 1/3] Ejecutando transformaciones Silver...")
    try:
        import src.transformation.limpiar_desercion_departamento
        from src.transformation.transform_silver import (
            ejecutar_transformacion_silver,
        )

        ejecutar_transformacion_silver()
        logging.info("[OK] Transformación Silver completada.")
    except Exception as e:
        logging.error(f"[ERROR] Falló la transformación Silver: {e}")
        sys.exit(1)

    # Paso 2: Integración Gold
    logging.info("\n[Paso 2/3] Ejecutando integración Gold...")
    try:
        from integrar_datos import integrar_datos

        integrar_datos()
        logging.info("[OK] Integración Gold completada.")
    except Exception as e:
        logging.error(f"[ERROR] Falló la integración Gold: {e}")
        sys.exit(1)

    # Paso 3: Validación de Calidad
    logging.info("\n[Paso 3/3] Ejecutando validación de calidad...")
    try:
        from src.validation.validar_calidad import validar_gold

        validar_gold()
        logging.info("[OK] Validación de calidad completada.")
    except Exception as e:
        logging.error(f"[ERROR] Falló la validación de calidad: {e}")
        sys.exit(1)

    logging.info("\n==================================================")
    logging.info("  PIPELINE COMPLETO EJECUTADO CON ÉXITO")
    logging.info("==================================================")


if __name__ == "__main__":
    ejecutar_pipeline()