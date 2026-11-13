# Requisitos funcionales · Mqueen

> Derivados del modelo de datos y del alcance acordado (inventario del Taller Auto Green).
> **Validar contra las historias de usuario de la actividad A05.** Si alguna historia no aparece aquí, se agrega con un nuevo RF.

| ID | Requisito | Reglas | Fase | Estado |
|---|---|---|---|---|
| RF-01 | Registrar una refacción (nombre, descripción, cantidad, stock mínimo, precio) | RN-03, RN-04 | 2 | Backend listo (pantalla en fase 5) |
| RF-02 | Consultar, buscar y filtrar el inventario | RN-02 | 1–2 | Backend listo (pantalla en fase 5) |
| RF-03 | Editar y eliminar refacciones | RN-01, RN-04 | 2 | Backend listo (pantalla en fase 5) |
| RF-04 | Ver alertas de stock bajo | RN-02 | 2 | Backend listo (pantalla en fase 5) |
| RF-05 | Ver el resumen del inventario (totales y valor) | RN-05 | 2 | Backend listo (pantalla en fase 5) |
| RF-06 | Registrar y consultar clientes | — | 3 | Backend listo (pantalla en fase 6) |
| RF-07 | Registrar vehículos ligados a un cliente | RN-12 | 3 | Backend listo (pantalla en fase 6) |
| RF-08 | Agendar citas y cambiar su estado | RN-06, RN-10, RN-11 | 3 | Backend listo (pantalla en fase 6) |
| RF-09 | Registrar las refacciones usadas en una cita y descontarlas del stock | RN-01, RN-07, RN-08 | 3 | Backend listo (pantalla en fase 6) |
| RF-10 | Generar el ticket o nota de servicio con su total | RN-09 | 3 | Backend listo (pantalla en fase 6) |
| RF-11 | Iniciar sesión como administrador | RN-13, RN-14, RN-15 | 4 | Backend listo (pantalla en fase 6) |
| RF-12 | Consultar el historial de servicios de un vehículo | — | 3 | Backend listo (pantalla en fase 6) |

## Requisitos no funcionales

| ID | Requisito |
|---|---|
| RNF-01 | Interfaz en español, usable en escritorio. |
| RNF-02 | Contraseñas guardadas con hash seguro (bcrypt). |
| RNF-03 | El código del backend tiene pruebas automáticas para cada regla de negocio. |
| RNF-04 | El sistema funciona en local (Windows + PostgreSQL). |

> El equipo actualiza la columna **Estado** al cerrar cada fase. Así esta tabla sirve como **matriz de trazabilidad** para el portafolio.
