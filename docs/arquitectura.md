# Arquitectura · Mqueen

## 1. Vista general

```
┌──────────────────┐   HTTP + JSON    ┌───────────────────────────┐   SQL    ┌────────────────────┐
│  React (Vite)    │ ───────────────> │  FastAPI                  │ ───────> │  PostgreSQL        │
│  localhost:5173  │ <─────────────── │  localhost:8000/api       │ <─────── │  esquema "BD"      │
└──────────────────┘                  └───────────────────────────┘          └────────────────────┘
```

Son tres capas simples:
1. El **frontend** solo muestra datos y llama a la API. No tiene reglas de negocio importantes; a lo mucho validaciones rápidas de formulario.
2. El **backend** es donde viven las reglas de negocio (RN-xx). Recibe JSON, valida con Pydantic, aplica las reglas y usa SQLAlchemy.
3. La **base de datos** guarda los datos y aplica algunas restricciones (CHECK, FK, UNIQUE).

## 2. Backend por dentro

```
petición → routers/<recurso>.py → (validación Pydantic) → lógica en la misma función → models.py (SQLAlchemy) → BD
```

- **`main.py`**: crea la app, configura CORS y registra los routers bajo el prefijo `/api`.
- **`db.py`**: lee de `.env` las variables `DB_USUARIO`, `DB_PASSWORD`, `DB_HOST`, `DB_PUERTO` y `DB_NOMBRE`, arma la URL con `URL.create` (el nombre de la base tiene espacios), crea el `engine` y define la función `get_db()` que da una sesión por petición.
- **`errores.py`**: la excepción `ErrorApi` y los manejadores que dan a todos los errores el mismo formato (ver sección 3).
- **`utiles.py`** (desde la fase 3): funciones que comparten los routers, como `quitar_acentos` y `obtener_o_404`.
- **`models.py`**: un modelo por tabla. Todas usan `__table_args__ = {"schema": "BD"}`.
- **`schemas.py`**: modelos Pydantic `XCrear`, `XActualizar` y `XSalida` para cada recurso.
- **`routers/`**: un archivo por recurso. Mientras una función no crezca mucho, la lógica va ahí mismo. Si crece, se extrae a una función auxiliar en el mismo archivo.

## 3. Convenciones de la API

- Todas las rutas empiezan con `/api`.
- Rutas en plural y en español: `/api/inventario`, `/api/clientes`, `/api/vehiculos`, `/api/citas`.
- Éxitos: `200` para consultas y ediciones, `201` al crear y `204` (sin cuerpo) al borrar.
- **Formato único de error** (desde la fase 2). Toda respuesta de error es un JSON así:
  `{"detail": "mensaje en español para el usuario", "errores": [{"campo": "...", "mensaje": "..."}]}`.
  `detail` siempre es texto. `errores` marca los campos con problema y va vacía si el error no es de un campo. Nunca se devuelve texto plano, inglés ni detalles técnicos.
- Los routers lanzan `ErrorApi(status_code, mensaje, errores)`, definida en `app/errores.py`, que también registra los manejadores de toda la API. Códigos:
  - `400`: regla de negocio violada o dato fuera de rango (por ejemplo, "Stock insuficiente"). Se reportan todos los problemas a la vez.
  - `404`: el recurso o la ruta no existe.
  - `409`: conflicto (por ejemplo, borrar una pieza que tiene historial, o un nombre repetido).
  - `422`: tipo de dato equivocado (texto donde va un número, campo faltante). Lo detecta FastAPI y `errores.py` lo traduce.
  - `401`: sin sesión, a partir de la fase 4.
  - `503`: la base de datos no responde.
  - `500`: error no previsto. Mensaje genérico; el detalle solo va a la consola del servidor.
- Los textos que escribe el usuario (nombres y descripciones de piezas, nombres de clientes, marcas, modelos, placas y motivos de citas) se guardan **sin acentos** y conservan la `ñ`. Las búsquedas también quitan los acentos, así que "bujía" y "bujia" encuentran lo mismo. Las placas van además en mayúsculas.
- **Baja lógica** (desde la fase 3): la API nunca borra clientes ni vehículos; los marca con `activo = false`. Las listas solo muestran activos, salvo con `?incluir_inactivos=true`. Las citas no se borran: se cancelan.
- El dinero se serializa como **texto con 2 decimales** (por ejemplo `"95.00"`), que es como Pydantic convierte un `Decimal` a JSON. Así no interviene ningún `float`. El frontend lo convierte con `Number(...)` al mostrarlo.

## 4. Endpoints planeados

| Método | Ruta | Fase | Reglas |
|---|---|---|---|
| GET | `/api/salud` | 0 | — |
| GET | `/api/inventario` (`?buscar=`, `?stock_bajo=`) | 1–2 | RN-02 |
| GET | `/api/inventario/resumen` | 2 | RN-02, RN-05 |
| GET/POST/PUT/DELETE | `/api/inventario/{id}` | 2 | RN-01, RN-03, RN-04 |
| GET/POST | `/api/clientes` (`?buscar=`, `?incluir_inactivos=`) | 3 | — |
| GET/PUT/DELETE | `/api/clientes/{id}` (`DELETE` = baja lógica) | 3 | — |
| POST | `/api/clientes/{id}/reactivar` | 3 | — |
| GET/POST | `/api/vehiculos` (`?buscar=`, `?id_cliente=`, `?incluir_inactivos=`) | 3 | RN-12 |
| GET/PUT/DELETE | `/api/vehiculos/{id}` (`DELETE` = baja lógica) | 3 | RN-12 |
| POST | `/api/vehiculos/{id}/reactivar` | 3 | — |
| GET | `/api/vehiculos/{id}/historial` | 3 | RN-09 |
| GET/POST | `/api/citas` (`?estado=`, `?fecha=`, `?id_vehiculo=`) | 3 | RN-06, RN-12 |
| GET/PUT | `/api/citas/{id}` (sin `DELETE`: las citas se cancelan) | 3 | RN-11 |
| PUT | `/api/citas/{id}/estado` | 3 | RN-06, RN-10, RN-11 |
| POST | `/api/citas/{id}/piezas` | 3 | RN-01, RN-02, RN-07, RN-08, RN-11 |
| DELETE | `/api/citas/{id}/piezas/{id_pieza}` | 3 | RN-07, RN-11 |
| GET | `/api/citas/{id}/ticket` | 3 | RN-09 |
| POST | `/api/auth/login` | 4 | RN-13, RN-14, RN-15 |

## 5. Frontend

- `src/api.js` concentra **todas** las llamadas `fetch`. Así, si cambia la URL del backend, se cambia en un solo lugar.
- `src/pages/`: una página por pantalla (Inventario, NuevaRefaccion, Citas…).
- `src/components/`: piezas que se reutilizan (Sidebar, TarjetaResumen, Badge…).
- Diseño basado en los mockups: barra lateral verde oscuro `#15201A`, acento `#1F7A4D` y fuente Inter.

## 6. Lo que NO se usa (a propósito)

Docker, Redux, TypeScript, Alembic, microservicios ni librerías de componentes pesadas. Se podrían agregar después si el equipo lo decide, y con aprobación.
