# Mockups de las pantallas · Mqueen

Capturas del prototipo hecho en Figma. Son la **guía visual** del frontend: colores, tipografía, barra lateral y acomodo de cada pantalla.

El prototipo se dibujó antes de terminar el backend, así que algunas pantallas muestran datos que el sistema no guarda. **Donde el mockup y esta lista no coincidan, manda esta lista.** La base de datos no se cambia para parecerse al mockup.

## Pantallas

| Archivo | Pantalla | Se construye en |
|---|---|---|
| `01-login.png` | Acceso del administrador | Fase 5 |
| `02-resumen.png` | Resumen general | Fase 6.5 |
| `03-clientes.png` | Lista de clientes | Fase 6 |
| `04-registrar-cliente.png` | Registrar cliente | Fase 6 |
| `05-agenda-citas.png` | Agenda de citas | Fase 6 |
| `06-agendar-cita.png` | Agendar cita | Fase 6 |
| `07-vehiculos.png` | Lista de vehículos | Fase 6 |
| `08-inventario.png` | Control de inventario | Fase 5 |

## Estilo visual

El estilo de Figma es el oficial del sistema. Colores medidos sobre las capturas:

| Uso | Color |
|---|---|
| Barra lateral y panel izquierdo del login | `#172130` |
| Opción activa de la barra lateral | `#243045`, con una marca naranja a la izquierda |
| Acento (botones principales, logo, marca activa) | `#F56329` |
| Fondo de la página | `#F5F7FA` |
| Tarjetas y tablas | `#FFFFFF` |
| Encabezado de las tablas | `#F7FAFC` |
| Etiqueta verde (Suficiente, Terminada) | fondo `#E3F5EB` |
| Etiqueta amarilla (Stock bajo, Pendiente) | fondo `#FCF5DE` |
| Etiqueta roja (Crítico, Cancelada) | fondo `#FCEBEB` |
| Etiqueta azul (En proceso) | fondo `#E8F2FC` |

- Fuente: **Inter**.
- Marca: logo cuadrado naranja con **"AG"**, el texto **"Taller Auto Green"** y debajo "Sistema administrativo". Reemplaza al "TM" y al "Taller Mecánico" de las capturas, también en el login.
- Todas las pantallas, menos el login, llevan la barra lateral con: Resumen, Clientes, Citas, Vehículos e Inventario. Abajo aparece el administrador que inició sesión.

## Ajustes generales

- Se quita el buscador **"Buscar en el sistema"** de la barra superior en todas las pantallas. Cada lista tiene su propio buscador. En su lugar, la barra superior muestra al administrador y el botón para cerrar sesión.
- Se quitan los textos de prototipo: "Prototipo de sistema", "Pantalla demostrativa", "Datos simulados", "registros de ejemplo" y los pies de página parecidos. La aplicación muestra datos reales.
- Los textos que escribe el usuario se guardan sin acentos (la `ñ` se conserva), así que las listas los muestran así.
- El dinero se muestra en pesos con 2 decimales.
- Los mensajes de error que manda el backend se muestran en pantalla, junto al campo que falló cuando el error es de un campo.

## Ajustes por pantalla

### 01 · Login

- La etiqueta "Correo electrónico" pasa a ser **"Usuario"**. El administrador entra con su nombre de usuario, no con un correo. El texto de ejemplo del campo también cambia (por ejemplo, `admin`).
- Si el usuario o la contraseña no coinciden, se muestra el mensaje del backend.

### 02 · Resumen

- En la tarjeta "Vehículos en taller" se quita **"listos para entrega"**: el sistema no guarda ese dato. "Vehículos en taller" cuenta los vehículos que tienen una cita **En proceso**.
- "Citas de hoy" dice cuántas están pendientes, en lugar de "pendientes de confirmar".
- Las alertas de inventario usan los niveles de la regla RN-16 (Crítico y Stock bajo).
- La columna "Servicio" de "Próximas citas" muestra el motivo de la cita.
- Los datos salen de un endpoint nuevo, `GET /api/resumen`.

### 03 · Clientes

- Se quita la columna **"Estado"**.
- Se quita el filtro **"Todos los clientes"**. Queda el buscador y el botón "Nuevo cliente".
- La lista muestra solo clientes activos.

### 04 · Registrar cliente

- Se quitan **"Dirección"** y **"Notas adicionales"**: la tabla de clientes no tiene esas columnas.
- Quedan nombre completo, teléfono y correo electrónico. El correo es opcional.
- El mismo formulario sirve para editar un cliente.

### 05 · Agenda de citas

- Las etiquetas de estado usan los estados reales: **Pendiente**, **En proceso**, **Terminada** y **Cancelada**. "En taller" y "Confirmada" no existen en el sistema.
- La columna "Servicio" muestra el motivo de la cita.
- Cada cita lleva a su detalle (ver "Pantallas que faltan").

### 06 · Agendar cita

- Se quita **"Responsable"**: el sistema no registra mecánicos.
- **"Servicio solicitado"** y **"Descripción / observaciones"** se juntan en un solo campo, que se guarda en `motivo`.
- Se agrega **"Costo de mano de obra"**.
- "Fecha" y "Hora" se guardan juntas en `fecha`.
- El texto del pie pasa a "La cita quedará registrada como Pendiente".

### 07 · Vehículos

- Sin cambios en la lista.
- El botón "Registrar vehículo" abre una pantalla que no está en Figma (ver "Pantallas que faltan").

### 08 · Inventario

- Se quita la columna **"Código"**: las piezas no tienen código.
- Se agrega la columna **precio unitario**.
- Se agregan el botón **"Nueva refacción"**, un **buscador** por nombre o descripción y las acciones **editar** y **eliminar** en cada renglón.
- La etiqueta de estado y las tarjetas de arriba siguen la regla RN-16. Las dos usan el mismo dato del backend, `estado_stock`, así que siempre coinciden.
- El **valor del inventario** va como subtítulo de la tarjeta "Productos registrados".
- Una pieza que ya se usó en alguna cita no se puede eliminar; se muestra el mensaje del backend.

## Regla RN-16: niveles de stock

Es un cálculo; no se guarda en la base. Se revisa en este orden:

| Nivel | `estado_stock` | Condición | Etiqueta |
|---|---|---|---|
| **Crítico** | `critico` | La pieza está agotada (`cantidad = 0`) o `cantidad <= stock_minimo / 2` | Roja |
| **Stock bajo** | `bajo` | No es crítico y `cantidad <= stock_minimo` | Amarilla |
| **Suficiente** | `suficiente` | `cantidad > stock_minimo` | Verde |

Ejemplo con `stock_minimo = 6`: con 0 a 3 piezas es Crítico, con 4 a 6 es Stock bajo y con 7 o más es Suficiente.

## Pantallas que faltan

No están en Figma. Se diseñan con el mismo estilo que las demás:

| Pantalla | Qué hace | Se construye en |
|---|---|---|
| Alta y edición de refacción | Formulario con nombre, descripción, cantidad, stock mínimo y precio unitario. Avisa si la pieza va a quedar en Stock bajo o Crítico. | Fase 5 |
| Registrar vehículo | Formulario con cliente, placas, marca, modelo, año y kilometraje. También sirve para editar. | Fase 6 |
| Detalle de cita / ticket | Datos de la cita, cambio de estado, piezas usadas (agregar y quitar) y el total: mano de obra más refacciones. | Fase 6 |
