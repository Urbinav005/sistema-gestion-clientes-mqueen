"""Métricas de flujo Kanban para el tablero del equipo MQueen.

Lee la exportación del tablero (tablero.tsv) y calcula:
  - tiempo de ciclo (promedio y percentil 85)
  - throughput semanal
  - WIP actual y WIP promedio diario
  - verificación con la ley de Little
  - diagrama de flujo acumulado (CFD)

Uso:
    python metricas.py                       # usa tablero.tsv y la fecha más reciente de los datos
    python metricas.py tablero.tsv 2026-10-20 # archivo y fecha de corte explícitos

Columnas esperadas: Title, Status, Creado, Inicio, Fin
(el resto de las columnas de la exportación de GitHub Projects se ignora).
"""
import sys

import matplotlib

matplotlib.use("Agg")  # funciona también en Colab y sin pantalla
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ARCHIVO = sys.argv[1] if len(sys.argv) > 1 else "tablero.tsv"
CORTE = pd.to_datetime(sys.argv[2]) if len(sys.argv) > 2 else None

# ---------------------------------------------------------------- lectura
df = pd.read_csv(ARCHIVO, sep="\t")
# La exportación directa de GitHub Projects no trae "Creado" ni "Nota".
# Sin "Creado", el CFD cuenta cada tarjeta desde su Inicio, o desde el primer día de los datos si no tiene Inicio.
if "Nota" not in df.columns:
    df["Nota"] = "sin fechas de Inicio/Fin en el tablero"
if "Creado" not in df.columns:
    df["Creado"] = df["Inicio"]
for col in ("Creado", "Inicio", "Fin"):
    df[col] = pd.to_datetime(df[col], errors="coerce")
primer_dia = pd.concat([df["Creado"], df["Inicio"], df["Fin"]]).dropna().min()
df["Creado_dia"] = df["Creado"].fillna(primer_dia).dt.normalize()

fechas = pd.concat([df["Creado_dia"], df["Inicio"], df["Fin"]]).dropna()
corte = (CORTE if CORTE is not None else fechas.max()).normalize()
print(f"Fecha de corte: {corte.date()}")
print(f"Tarjetas en el tablero: {len(df)}")
print(df["Status"].value_counts().to_string(), end="\n\n")

# ------------------------------------------------- tarjetas utilizables
completas = df.dropna(subset=["Inicio", "Fin"]).copy()
excluidas = df[(df["Status"] == "Terminado") & df["Inicio"].isna()]
for _, fila in excluidas.iterrows():
    print(f"[excluida] {fila['Title']}: terminada pero sin fechas válidas ({fila['Nota']})")
# Se quitan del CFD y de las métricas para que no aparezcan como "pendientes" por error.
df = df.drop(excluidas.index)

# ------------------------------------------------------ tiempo de ciclo
# Convención: ciclo = días entre Inicio y Fin (misma fecha = 0 días).
completas["Ciclo_dias"] = (completas["Fin"] - completas["Inicio"]).dt.days
n = len(completas)
print(f"\nTarjetas con Inicio y Fin: {n}")
if n:
    print(completas[["Title", "Inicio", "Fin", "Ciclo_dias"]].to_string(index=False))
    ciclo_prom = completas["Ciclo_dias"].mean()
    p85 = np.percentile(completas["Ciclo_dias"], 85)
    print(f"\nTiempo de ciclo promedio: {ciclo_prom:.1f} días")
    print(f"Percentil 85: {p85:.1f} días")
    if n < 5:
        print(f"AVISO: n = {n}; con tan pocas tarjetas el promedio y el P85 no son "
              "estadísticamente confiables (el P85 coincide con el valor máximo).")
else:
    ciclo_prom = p85 = float("nan")
    print("Aún no hay tarjetas terminadas con fechas; el tiempo de ciclo no se puede calcular.")

# ------------------------------------------------------- throughput semanal
if n:
    semana = completas["Fin"].dt.to_period("W-SUN").dt.start_time  # semanas lunes a domingo
    rango = pd.date_range(semana.min(), corte.to_period("W-SUN").start_time, freq="7D")
    throughput = semana.value_counts().reindex(rango, fill_value=0).sort_index()
    print("\nThroughput semanal (tarjetas terminadas por semana, semana que inicia en lunes):")
    print(throughput.to_string())
    thr_prom = throughput.mean()
else:
    thr_prom = float("nan")

# ------------------------------------------------------------------- WIP
en_proceso = df[df["Inicio"].notna() & df["Fin"].isna()]
print(f"\nWIP actual (con Inicio y sin Fin): {len(en_proceso)}")
for t in en_proceso["Title"]:
    print(f"  - {t}")

inicio_serie = df["Inicio"].dropna().min()
dias = pd.date_range(inicio_serie, corte, freq="D")
wip_diario = pd.Series(
    [((df["Inicio"] <= d) & (df["Fin"].isna() | (df["Fin"] > d))).sum() for d in dias],
    index=dias,
)
print(f"WIP promedio diario ({dias[0].date()} a {dias[-1].date()}): {wip_diario.mean():.2f}")

# ------------------------------------------------------------ ley de Little
# Ley de Little: tiempo de ciclo ≈ WIP promedio / throughput (en las mismas unidades).
if n and thr_prom > 0:
    little = wip_diario.mean() / (thr_prom / 7)
    print(f"Ley de Little (WIP prom / throughput diario): {little:.1f} días "
          f"frente a {ciclo_prom:.1f} días medidos")
    print("(Solo es una comparación de orden de magnitud: con 1 tarjeta terminada no valida nada.)")

# ------------------------------------------------------------------- CFD
dias_cfd = pd.date_range(df["Creado_dia"].min(), corte, freq="D")
creadas = np.array([(df["Creado_dia"] <= d).sum() for d in dias_cfd])
iniciadas = np.array([(df["Inicio"] <= d).sum() for d in dias_cfd])
terminadas = np.array([(df["Fin"] <= d).sum() for d in dias_cfd])

por_hacer = creadas - iniciadas
en_proc = iniciadas - terminadas

fig, ax = plt.subplots(figsize=(10, 5))
ax.stackplot(
    dias_cfd,
    terminadas,
    en_proc,
    por_hacer,
    labels=["Terminado", "En proceso o en revisión", "Pendiente (Backlog / Por hacer)"],
    colors=["#2e7d32", "#f9a825", "#9e9e9e"],
    alpha=0.9,
)
ax.set_title("Diagrama de flujo acumulado (CFD) - MQueen")
ax.set_xlabel("Fecha")
ax.set_ylabel("Tarjetas acumuladas")
ax.legend(loc="upper left")
ax.margins(x=0)
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig("cfd.png", dpi=150)
print("\nCFD guardado en cfd.png")

# ------------------------------------------------- verificación interna
# Contrasta el script contra conteos hechos a mano a partir de las columnas.
assert terminadas[-1] == df["Fin"].notna().sum()
assert iniciadas[-1] == df["Inicio"].notna().sum()
assert creadas[-1] == len(df)
print("Verificación interna: los totales del CFD coinciden con los conteos de las columnas.")
