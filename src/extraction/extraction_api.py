from pathlib import Path
import requests
import json
import time


# ============================================================
# CONFIGURACIÓN
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[2]

OUTPUT_DIR = ROOT_DIR / "data" / "bronze" / "api"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

API_URL = "https://www.datos.gov.co/resource/5wck-szir.json"

TAMANO_LOTE = 50000
TIMEOUT = 60


# ============================================================
# EXTRACCIÓN DE LA API REST
# ============================================================

def extraer_api():
    print("=" * 60)
    print("EXTRACCIÓN DE API REST - BRONZE")
    print("=" * 60)

    sesion = requests.Session()
    offset = 0
    total_registros = 0
    numero_archivo = 1

    while True:
        parametros = {
            "$limit": TAMANO_LOTE,
            "$offset": offset
        }

        print(f"Consultando registros desde el desplazamiento {offset}...")

        respuesta = sesion.get(
            API_URL,
            params=parametros,
            timeout=TIMEOUT
        )

        # Detener el proceso si la API devuelve un error HTTP
        respuesta.raise_for_status()

        # Conservar el contenido original de la respuesta
        contenido_original = respuesta.content

        # Comprobar que la respuesta sea JSON válido
        registros = respuesta.json()

        if not isinstance(registros, list):
            raise ValueError(
                "La API no devolvió una lista de registros JSON."
            )

        if not registros:
            print("No hay más registros para descargar.")
            break

        nombre_archivo = (
            OUTPUT_DIR / f"matricula_api_parte_{numero_archivo:03d}.json"
        )

        # Guardar el JSON recibido sin transformar sus campos
        nombre_archivo.write_bytes(contenido_original)

        cantidad = len(registros)
        total_registros += cantidad

        print(
            f"Archivo guardado: {nombre_archivo.name} | "
            f"Registros: {cantidad}"
        )

        offset += cantidad
        numero_archivo += 1

        # Una respuesta menor al tamaño solicitado indica el final
        if cantidad < TAMANO_LOTE:
            break

        time.sleep(0.2)

    print("-" * 60)
    print(f"Total de registros descargados: {total_registros}")
    print(f"Archivos JSON generados: {numero_archivo - 1}")
    print(f"Ubicación: {OUTPUT_DIR}")
    print("Extracción de la API finalizada.")


if __name__ == "__main__":
    extraer_api()