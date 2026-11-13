
# Sistema de Gestión de Clientes Mqueen

Repositorio del equipo para el proyecto integrador de la asignatura **Proyecto Integrador I (E-PIN1-1)**.

**Grupo:** 4A
**Fecha de creación:** 30 de septiembre de 2026

## El sistema

Aplicación web para el **Taller Mecánico Auto Green** que gestiona el inventario de refacciones y lo relaciona con clientes, vehículos y citas de servicio. Solo hay un tipo de usuario: el administrador.

- **Backend:** Python, FastAPI, SQLAlchemy y PostgreSQL. Está en `backend/`.
- **Frontend:** React con Vite (pendiente).
- **Documentación técnica:** en `docs/`.

## Integrantes y roles

| Integrante | Rol |
|---|---|
| Rodolfo Urbina Avitia | Product Owner / Equipo de desarrollo |
| Luis Francisco Ortega Alvarado | Scrum Master (sprint 1) / Equipo de desarrollo |
| Diego Emmanuel Guzmán Reyes | Equipo de desarrollo |
| Gabriel de Jesús Navar Díaz | Equipo de desarrollo |

## Rotación del Scrum Master

| Sprint | Scrum Master |
|---|---|
| Sprint 0 (diseño) | Gabriel de Jesús Navar Díaz |
| Sprint 1 | Luis Francisco Ortega Alvarado |
| Sprint 2 | Diego Emmanuel Guzmán Reyes |
| Sprint 3 | Gabriel de Jesús Navar Díaz |

## Metodología

Trabajamos con la metodología ágil **Scrum**, organizando el trabajo en sprints y dando seguimiento a las tareas en un tablero Kanban con las columnas: Backlog, Por hacer, En proceso, En revisión y Terminado.

## Herramientas del equipo

- **GitHub:** repositorio del código y los documentos.
- **GitHub Projects:** tablero Kanban.
- **WhatsApp:** comunicación rápida y coordinación diaria.

## Estructura del repositorio

- `/portafolio`: documentos y evidencias de las actividades (por ejemplo, el acta de integración del equipo).
- `/backend`: la API del sistema (`app/`) y sus pruebas automáticas (`tests/`).
- `/docs`: documentación técnica.
  - `database.md`: modelo de datos y reglas de negocio (RN-01 a RN-15).
  - `requisitos.md`: requisitos funcionales y su trazabilidad.
  - `arquitectura.md`: capas, convenciones de la API y lista de endpoints.
  - `diseno/`: diagramas del diseño funcional.
  - `sql/`: scripts de datos de prueba y de cambios a la base.

## Acuerdos de trabajo

- Tiempo de respuesta a mensajes del equipo: menos de 2 horas en días hábiles.
- Scrum diario: todos los días a las 8:00 pm (15 minutos).
- Reunión semanal de seguimiento: viernes al terminar clases.

## Cómo levantar el backend (Windows, PowerShell)

Requisitos:

- Python 3.11 o superior.
- PostgreSQL local con la base `Boceto de BD para Mqueen` ya cargada (tablas en el esquema `"BD"`).

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env      # después abre .env y pon tu contraseña real
uvicorn app.main:app --reload
```

Para comprobar que funciona:

- http://localhost:8000/api/salud debe mostrar `{"bd":"ok","piezas":<n>}`.
- http://localhost:8000/docs muestra la documentación interactiva de la API.

## Pruebas

Desde `backend/`, con el entorno virtual activado:

```powershell
pytest
```

Las pruebas usan la base local, pero corren dentro de una transacción que se deshace: no dejan datos guardados.

## Problemas comunes

- **PowerShell no deja ejecutar `Activate.ps1`:** ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- **`/api/salud` responde 503:** PostgreSQL está apagado o algún dato de `backend/.env` está mal. El error real aparece en la consola de `uvicorn`.
- **`DLL load failed ... An Application Control policy has blocked this file` al arrancar o al correr `pytest`:** el **Smart App Control** de Windows 11 está bloqueando la librería de `psycopg`, que no viene firmada. Al equipo le funcionó apagarlo en *Seguridad de Windows → Control de aplicaciones y navegador → Smart App Control*. Es una protección de Windows: apagarla es decisión de cada quien, y en algunas versiones de Windows no se puede volver a encender sin restablecer el equipo.

## Aviso

**No** vuelvas a ejecutar los scripts de `docs/sql/`: ya se corrieron una vez y duplican registros en la base.
