# Artefacto Kanban: métricas de flujo del equipo MQueen

Actividad A03-B · Bloque D (Agilidad y flujo) · Proyecto Integrador I · UTD
Proyecto: Sistema de Gestión de Clientes Mqueen · Responsable del artefacto: Rodolfo Urbina Avitia

## Qué hace

`metricas.py` lee la exportación del tablero de GitHub Projects (`tablero.tsv`) y calcula:

- tiempo de ciclo (promedio y percentil 85),
- throughput semanal (tarjetas terminadas por semana, de lunes a domingo),
- WIP actual y WIP promedio diario,
- una comparación con la ley de Little,
- el diagrama de flujo acumulado (CFD), que guarda como `cfd.png`.

## Cómo ejecutarlo

Requiere Python 3 con `pandas`, `numpy` y `matplotlib`.

```bash
pip install pandas numpy matplotlib
python metricas.py tablero.tsv 2026-10-20
```

El segundo argumento (fecha de corte) es opcional; si se omite, se usa la fecha más reciente de los datos.
En Google Colab: sube `metricas.py` y `tablero.tsv`, y ejecuta `!python metricas.py tablero.tsv 2026-10-20`.

Para actualizar los datos: en el proyecto de GitHub, vista Table, usa "Export view data" y guarda el
resultado como `tablero.tsv`. El script necesita las columnas `Title`, `Status`, `Inicio` y `Fin`, y funciona
directo con la exportación de GitHub. `Creado` (fecha de creación del issue, tomada de la API de GitHub) y
`Nota` son opcionales: si faltan, el CFD cuenta cada tarjeta desde su Inicio, o desde el primer día de los datos si no tiene Inicio.

## Datos: qué es real y qué no

Todos los datos son reales, tomados del repositorio y del tablero del equipo al 20 de octubre de 2026.
No hay datos inventados ni de ejemplo.

- **Creado:** fecha de creación de cada issue (API de GitHub).
- **Inicio:** campo "Inicio" del tablero (exportación del 20 de octubre). Para A03 se registró la fecha de
  creación del issue (2 de octubre) como aproximación, porque no se había anotado su inicio real.
- **Fin:** fecha de cierre del issue A03 (10 de octubre).
- **A02 queda excluida:** el issue se creó y se cerró en 2 segundos (2 de octubre), lo que refleja que se
  marcó como terminado al registrarlo, no el tiempo real de trabajo. Contarla daría un ciclo de 0 días falso.

## Resultados al 20 de octubre de 2026

| Métrica | Valor |
|---|---|
| Tarjetas en el tablero (sin A02) | 24 |
| Tarjetas terminadas con fechas válidas | 1 (A03) |
| Tiempo de ciclo promedio | 8.0 días |
| Percentil 85 | 8.0 días |
| Throughput semanal | semana del 5 oct: 1; semana del 12 oct: 0; semana del 19 oct: 0 |
| WIP actual | 4 (A04, A03B-05, A03B-07 y A03B-08, todas en En Revisión) |
| WIP promedio diario (2 al 20 oct) | 0.68 |

## Limitaciones (importante)

- **n es muy pequeño.** Solo una tarjeta tiene ciclo completo, así que el promedio y el P85 coinciden y no
  son estadísticamente confiables. Las métricas se vuelven útiles conforme se terminen más tarjetas
  (las 19 tarjetas de A03B alimentarán los datos).
- El periodo cubre unas 2.5 semanas de historial real, pero casi todo el movimiento reciente
  (tarjetas A03B) apenas comenzó el 19 y 20 de octubre.
- El tiempo de A03 usa la fecha de creación como inicio, por lo que probablemente sobrestima el ciclo real.
- La comparación con la ley de Little (14.4 días contra 8.0 medidos) es solo de orden de magnitud con un dato.
- Al 20 de octubre, la columna En Revisión tiene 4 tarjetas, por encima de su límite WIP de 3. Es una señal
  de flujo que el tablero muestra: hace falta revisar antes de mandar más trabajo a revisión.

## Verificación

El script valida internamente que los totales del CFD coincidan con los conteos de las columnas. Además se
verificó a mano:

- A03: del 2 al 10 de octubre hay 8 días, igual que el script.
- WIP promedio: 8 días-tarjeta de A03, 2 de A04 y 1 de cada una de A03B-05, A03B-07 y A03B-08 son
  13 días-tarjeta; 13 / 19 días = 0.68.
- Throughput: A03 se cerró el 10 de octubre, dentro de la semana que inicia el 5 de octubre.

## Archivos

- `metricas.py`: script principal.
- `tablero.tsv`: exportación del tablero con los datos reales.
- `cfd.png`: diagrama de flujo acumulado generado.

## Uso de IA

Se usó Claude (Anthropic) para ayudar a depurar y ordenar el código del script y para redactar este README.
Los datos provienen del tablero y del repositorio del equipo, y los cálculos fueron verificados a mano.
