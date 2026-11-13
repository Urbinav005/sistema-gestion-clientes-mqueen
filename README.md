
# Sistema de Gestión de Clientes Mqueen

Repositorio del equipo para el proyecto integrador de la asignatura **Proyecto Integrador I (E-PIN1-1)**.

**Grupo:** 4A
**Fecha de creación:** 30 de septiembre de 2026

## El sistema

Aplicación web para el **Taller Mecánico Auto Green** que gestiona el inventario de refacciones y lo relaciona con clientes, vehículos y citas de servicio. Solo hay un tipo de usuario: el administrador.

- **Backend:** Python, FastAPI, SQLAlchemy y PostgreSQL. Está en `backend/`.
- **Frontend:** React con Vite. Está en `frontend/`.
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
- `/frontend`: la aplicación web en React (`src/`): páginas, componentes y llamadas a la API.
- `/docs`: documentación técnica.
  - `database.md`: modelo de datos y reglas de negocio (RN-01 a RN-16).
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
Copy-Item .env.example .env      # después abre .env y llénalo (ver abajo)
uvicorn app.main:app --reload
```

### Llenar `backend/.env`

`.env` guarda los datos privados de cada computadora y **nunca** se sube al repositorio.

1. Pon la contraseña de tu PostgreSQL en `DB_PASSWORD`.
2. Genera una clave para firmar las sesiones y ponla en `JWT_SECRETO`. Cada quien genera la suya:

   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

   Copia el texto completo (puede empezar o terminar con `-` o `_`) y pégalo entre comillas: `JWT_SECRETO="..."`. Debe tener al menos 32 caracteres; si falta, la API no arranca.
3. `JWT_MINUTOS` es opcional: cuántos minutos dura una sesión (por defecto 480, es decir, 8 horas).

### Crear al administrador

La API solo la usa el administrador, que se registra con un script. Con el entorno virtual activado, desde `backend/`:

```powershell
python crear_admin.py
```

Pide el nombre, el usuario y la contraseña (dos veces). La contraseña no se ve al escribirla, pero sí se está escribiendo. Debe tener al menos 8 caracteres. Se guarda como un hash bcrypt, nunca en texto plano. Si el usuario ya existe, el script le cambia el nombre y la contraseña; así también se recupera una contraseña olvidada.

### Comprobar que funciona

- http://localhost:8000/api/salud debe mostrar `{"bd":"ok","piezas":<n>}`. Esta ruta no pide sesión.
- http://localhost:8000/docs muestra la documentación interactiva de la API.
- Las demás rutas piden sesión. En `/docs`:
  1. `POST /api/auth/login` con el usuario y la contraseña del administrador. Copia el `token` de la respuesta.
  2. Botón **Authorize** (arriba a la derecha), pega el token y acepta.
  3. Ya puedes probar las demás rutas. Sin token responden `401`.

## Cómo levantar el frontend (Windows, PowerShell)

Requisitos:

- Node.js 22.12 o superior (incluye `npm`).
- El backend encendido en http://localhost:8000 y el administrador ya creado.

En otra terminal, desde la raíz del repositorio:

```powershell
cd frontend
npm install          # solo la primera vez
npm run dev
```

Abre http://localhost:5173 e inicia sesión con el usuario y la contraseña del administrador.

- La aplicación siempre usa el puerto **5173**: es el único que la API autoriza (CORS). Si está ocupado, `npm run dev` se detiene con un error en vez de usar otro puerto.
- La sesión se guarda solo en la pestaña actual: aguanta recargar la página, pero al cerrar la pestaña o el navegador hay que volver a iniciar sesión.
- Por ahora están listas las pantallas de acceso e inventario. Las demás opciones del menú muestran un aviso de "disponible próximamente".
- Otros comandos: `npm run build` (genera la versión final en `frontend/dist/`) y `npm run lint` (revisa el código).

## Pruebas

Desde `backend/`, con el entorno virtual activado:

```powershell
pytest
```

Las pruebas usan la base local, pero corren dentro de una transacción que se deshace: no dejan datos guardados.

## Problemas comunes

- **PowerShell no deja ejecutar `Activate.ps1`:** ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- **El frontend dice "No se pudo conectar con el servidor":** el backend está apagado o no corre en el puerto 8000. Enciéndelo con `uvicorn app.main:app --reload`.
- **`/api/salud` responde 503:** PostgreSQL está apagado o algún dato de `backend/.env` está mal. El error real aparece en la consola de `uvicorn`.
- **`RuntimeError: Falta la variable JWT_SECRETO`:** falta la clave de sesiones en `backend/.env` o tiene menos de 32 caracteres. Ver "Llenar `backend/.env`".
- **`DLL load failed ... An Application Control policy has blocked this file` al arrancar o al correr `pytest`:** el **Smart App Control** de Windows 11 está bloqueando la librería de `psycopg` o la de `bcrypt`, que no vienen firmadas. Al equipo le funcionó apagarlo en *Seguridad de Windows → Control de aplicaciones y navegador → Smart App Control*. Es una protección de Windows: apagarla es decisión de cada quien, y en algunas versiones de Windows no se puede volver a encender sin restablecer el equipo.

## Aviso

**No** vuelvas a ejecutar los scripts de `docs/sql/`: ya se corrieron una vez y duplican registros en la base.
