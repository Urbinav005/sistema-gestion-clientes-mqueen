-- =====================================================================
--  QUITAR ACENTOS DEL INVENTARIO (2026-11-12)
--  Aprobado por Rodolfo: los nombres y descripciones de las piezas se guardan
--  sin acentos, para que la búsqueda encuentre "bujia" sin importar cómo se
--  escriba. La ñ se conserva.
--  Ejecutado una sola vez, dentro de una transacción.
--  Es registro histórico. Volver a ejecutarlo no cambia nada.
--  No cambia la estructura de ninguna tabla.
-- =====================================================================
UPDATE "BD".inventario
SET nombre      = translate(nombre,      'áéíóúüÁÉÍÓÚÜ', 'aeiouuAEIOUU'),
    descripcion = translate(descripcion, 'áéíóúüÁÉÍÓÚÜ', 'aeiouuAEIOUU')
WHERE nombre      <> translate(nombre,      'áéíóúüÁÉÍÓÚÜ', 'aeiouuAEIOUU')
   OR descripcion <> translate(descripcion, 'áéíóúüÁÉÍÓÚÜ', 'aeiouuAEIOUU');
