
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
    logging.info("       INICIANDO PIPELINE ETL DE DESERCIÓN")
    logging.info("==================================================")

    # Paso 1: Transformaciones Silver.
    logging.info("\n[Paso 1/3] Ejecutando transformaciones Silver...")

    try:
        # Ejecutar limpieza de tasas de deserción.
        import src.transformation.limpiar_desercion_departamento

        from src.transformation.transform_silver import (
            ejecutar_transformacion_silver,
        )

        resultado = ejecutar_transformacion_silver()

        if not resultado:
            raise RuntimeError(
                "La transformación Silver no terminó correctamente."
            )

        logging.info("[OK] Transformación Silver completada.")

    except Exception as error:
        logging.exception(
            f"[ERROR] Falló la transformación Silver: {error}"
        )
        sys.exit(1)

    # Paso 2: Integración Gold.
    logging.info("\n[Paso 2/3] Ejecutando integración Gold...")

    try:
        from integrar_datos import integrar_datos

        integrar_datos()

        logging.info("[OK] Integración Gold completada.")

    except Exception as error:
        logging.exception(
            f"[ERROR] Falló la integración Gold: {error}"
        )
        sys.exit(1)

    # Paso 3: Validación de calidad.
    logging.info("\n[Paso 3/3] Ejecutando validaciones de calidad...")

    try:
        from src.validation.validar_calidad import (
            ejecutar_validaciones,
        )

        ejecutar_validaciones()

        logging.info("[OK] Validaciones completadas.")

    except Exception as error:
        logging.exception(
            f"[ERROR] Falló la validación de calidad: {error}"
        )
        sys.exit(1)

    logging.info("\n==================================================")
    logging.info("       PIPELINE ETL FINALIZADO CON ÉXITO")
    logging.info("==================================================")


if __name__ == "__main__":
    ejecutar_pipeline()
