from pathlib import Path
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor


def probar_notebook():
    base_dir = Path(__file__).resolve().parent

    # Buscar cualquier notebook (.ipynb) en el proyecto
    notebooks = list(base_dir.rglob("*.ipynb"))
    notebooks = [
        nb for nb in notebooks if ".ipynb_checkpoints" not in str(nb)
    ]

    if not notebooks:
        print("[ERROR] No se encontró ningún archivo .ipynb en el proyecto.")
        return

    notebook_path = notebooks[0]
    print(f"Ejecutando notebook encontrado: {notebook_path.name} ...")

    with open(notebook_path, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    ep = ExecutePreprocessor(timeout=600, kernel_name="python3")

    try:
        ep.preprocess(nb, {"metadata": {"path": str(notebook_path.parent)}})
        print("[ÉXITO] El notebook se ejecutó por completo sin errores.")
    except Exception as e:
        print(f"[ERROR] La ejecución del notebook falló: {e}")


if __name__ == "__main__":
    probar_notebook()