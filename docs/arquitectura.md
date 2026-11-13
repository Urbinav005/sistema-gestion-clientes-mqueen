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
- **`seguridad.py`** (desde la fase 4): contraseñas con bcrypt, tokens JWT y la dependencia `admin_actual` que protege las rutas.
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
  - `401`: sin sesión, o con una sesión vencida o no válida. También el login con usuario o contraseña incorrectos.
  - `503`: la base de datos no responde.
  - `500`: error no previsto. Mensaje genérico; el detalle solo va a la consola del servidor.
- Los textos que escribe el usuario (nombres y descripciones de piezas, nombres de clientes, marcas, modelos, placas y motivos de citas) se guardan **sin acentos** y conservan la `ñ`. Las búsquedas también quitan los acentos, así que "bujía" y "bujia" encuentran lo mismo. Las placas van además en mayúsculas.
- **Inicio de sesión** (desde la fase 4): `POST /api/auth/login` devuelve un token JWT. Todas las rutas, menos `/api/salud`, `/api/auth/login` y la documentación, exigen la cabecera `Authorization: Bearer <token>`. Las contraseñas se guardan con bcrypt. El administrador se registra con el script `backend/crear_admin.py`.
- **Baja lógica** (desde la fase 3): la API nunca borra clientes ni vehículos; los marca con `activo = false`. Las listas solo muestran activos, salvo con `?incluir_inactivos=true`. Las citas no se borran: se cancelan.
- El dinero se serializa como **texto con 2 decimales** (por ejemplo `"95.00"`), que es como Pydantic convierte un `Decimal` a JSON. Así no interviene ningún `float`. El frontend lo convierte con `Number(...)` al mostrarlo.

## 4. Endpoints planeados

| Método | Ruta | Fase | Reglas |
|---|---|---|---|
| GET | `/api/salud` | 0 | — |
| GET | `/api/inventario` (`?buscar=`, `?stock_bajo=`, `?estado_stock=`) | 1–2, 5 | RN-02, RN-16 |
| GET | `/api/inventario/resumen` | 2, 5 | RN-02, RN-05, RN-16 |
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
| GET | `/api/auth/yo` | 4 | RN-13 |
| GET | `/api/resumen` | 6.5 | RN-02, RN-16 |

Pendiente de construir: en la fase 5, cada pieza incluirá el campo `estado_stock` (`suficiente`, `bajo` o `critico`), calculado en el backend con RN-16, y `/api/inventario/resumen` dará el conteo de cada nivel. La tabla y las tarjetas del frontend usan ese mismo campo. `GET /api/resumen` (fase 6.5) alimenta la pantalla de resumen general; es de solo lectura y exige sesión.

## 5. Frontend

- `src/api.js` concentra **todas** las llamadas `fetch`. Así, si cambia la URL del backend, se cambia en un solo lugar. También agrega la cabecera `Authorization` con el token de la sesión.
- `src/pages/`: una página por pantalla (Login, Inventario, FormularioRefaccion, Clientes, Citas…).
- `src/components/`: piezas que se reutilizan (BarraLateral, TarjetaResumen, Etiqueta…).
- **Mockups:** las pantallas siguen los mockups de Figma de `docs/diseno/mockups/` (01 a 08), con los ajustes de su `README.md`. Si el mockup muestra un dato que el sistema no guarda, se ajusta la pantalla, no la base.
- **Estilo visual** (el de Figma; reemplaza al verde que se había planeado): marca "Taller Auto Green" con logo "AG" y el texto "Sistema administrativo", barra lateral azul oscuro `#172130`, acento naranja `#F56329`, fondo `#F5F7FA`, tarjetas blancas y fuente Inter.
- **Sesión:** el token se guarda en `sessionStorage`: aguanta recargar la página y se pierde al cerrar la pestaña. Sin token, la única pantalla visible es el login. Si el backend responde `401`, el frontend borra el token y regresa al login.
- **Orden de construcción:**

  | Fase | Pantallas |
  |---|---|
  | 5 | Layout con barra lateral, login (01), inventario (08) y alta y edición de refacción |
  | 6 | Clientes (03, 04), vehículos (07 y su registro) y citas (05, 06 y detalle / ticket) |
  | 6.5 | Resumen general (02) |

## 6. Lo que NO se usa (a propósito)

Docker, Redux, TypeScript, Alembic, microservicios ni librerías de componentes pesadas. Se podrían agregar después si el equipo lo decide, y con aprobación.
