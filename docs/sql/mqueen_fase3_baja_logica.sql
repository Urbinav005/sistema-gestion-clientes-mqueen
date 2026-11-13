-- =====================================================================
--  FASE 3: BAJA LÓGICA Y TEXTOS SIN ACENTOS (2026-11-12)
--  Aprobado por Rodolfo.
--  Ejecutado una sola vez, dentro de una transacción.
--  Es registro histórico: NO volver a ejecutarlo (el ALTER fallaría,
--  porque las columnas ya existen).
--
--  Qué hace:
--   1. Agrega la columna "activo" a clientes y vehiculos (baja lógica).
--      Todos los registros existentes quedan activos.
--   2. Quita los acentos de clientes.nombre, vehiculos.marca,
--      vehiculos.modelo y citas.motivo. La ñ se conserva.
--   3. Deja las placas en mayúsculas y sin espacios sobrantes.
--  No crea ni borra tablas, y no borra ningún dato.
-- =====================================================================

-- 1. Baja lógica
ALTER TABLE "BD".clientes  ADD COLUMN activo boolean NOT NULL DEFAULT true;
ALTER TABLE "BD".vehiculos ADD COLUMN activo boolean NOT NULL DEFAULT true;

-- 2. Textos sin acentos
UPDATE "BD".clientes
SET nombre = translate(nombre, 'áéíóúüÁÉÍÓÚÜ', 'aeiouuAEIOUU')
WHERE nombre <> translate(nombre, 'áéíóúüÁÉÍÓÚÜ', 'aeiouuAEIOUU');

UPDATE "BD".vehiculos
SET marca  = translate(marca,  'áéíóúüÁÉÍÓÚÜ', 'aeiouuAEIOUU'),
    modelo = translate(modelo, 'áéíóúüÁÉÍÓÚÜ', 'aeiouuAEIOUU')
WHERE marca  <> translate(marca,  'áéíóúüÁÉÍÓÚÜ', 'aeiouuAEIOUU')
   OR modelo <> translate(modelo, 'áéíóúüÁÉÍÓÚÜ', 'aeiouuAEIOUU');

UPDATE "BD".citas
SET motivo = translate(motivo, 'áéíóúüÁÉÍÓÚÜ', 'aeiouuAEIOUU')
WHERE motivo <> translate(motivo, 'áéíóúüÁÉÍÓÚÜ', 'aeiouuAEIOUU');

-- 3. Placas en mayúsculas y sin espacios sobrantes
UPDATE "BD".vehiculos
SET placas = upper(btrim(translate(placas, 'áéíóúüÁÉÍÓÚÜ', 'aeiouuAEIOUU')))
WHERE placas <> upper(btrim(translate(placas, 'áéíóúüÁÉÍÓÚÜ', 'aeiouuAEIOUU')));
