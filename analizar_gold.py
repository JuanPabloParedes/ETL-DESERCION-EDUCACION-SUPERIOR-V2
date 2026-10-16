
import os
import pandas as pd
import matplotlib.pyplot as plt

archivo = "data/gold/gold_final.csv"
salida = "resultados"

os.makedirs(salida, exist_ok=True)

df = pd.read_csv(archivo)

# Gráfica 1: promedio simple por nivel
promedios = (
    df.groupby("nivel_formacion")["tasa_desercion"]
    .mean()
    .sort_values(ascending=False) * 100
)

plt.figure(figsize=(9, 5))
promedios.plot(kind="bar")
plt.title("Tasa promedio de deserción por nivel de formación")
plt.xlabel("Nivel de formación")
plt.ylabel("Tasa promedio (%)")
plt.xticks(rotation=25, ha="right")
plt.tight_layout()
plt.savefig(
    os.path.join(salida, "desercion_por_nivel.png"),
    dpi=150
)
plt.close()

# Gráfica 2: promedio simple por año
anual = (
    df.groupby("anio")["tasa_desercion"].mean() * 100
)

plt.figure(figsize=(9, 5))
anual.plot(kind="line", marker="o")
plt.title("Evolución anual de la tasa promedio de deserción")
plt.xlabel("Año")
plt.ylabel("Tasa promedio (%)")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(
    os.path.join(salida, "desercion_por_anio.png"),
    dpi=150
)
plt.close()

print("Promedio por nivel (%):")
print(promedios.round(2).to_string())
print("\nPromedio por año (%):")
print(anual.round(2).to_string())
print(f"\nGráficas guardadas en: {salida}")
