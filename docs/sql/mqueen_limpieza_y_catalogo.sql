-- =====================================================================
--  LIMPIEZA DE PIEZAS REPETIDAS + CATÁLOGO AMPLIADO (2026-11-12)
--  Aprobado por Rodolfo. Ejecutado una sola vez, dentro de
--  una transacción. Es registro histórico: NO volver a ejecutarlo.
--  (Si se ejecuta de nuevo, el bloque de verificación lo detiene.)
--
--  Qué hace:
--   1. Unifica las piezas repetidas. Se conservan las del script de datos de
--      prueba (id 4, 5 y 7) y se eliminan las anteriores (id 1, 2 y 3).
--   2. Agrega 24 refacciones nuevas. El inventario queda con 36 piezas.
--  No cambia la estructura de ninguna tabla.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 0. Verificación: solo continúa si los datos están como se esperaba
-- ---------------------------------------------------------------------
DO $$
BEGIN
  IF (SELECT COUNT(*) FROM "BD".inventario
      WHERE (id_pieza, nombre) IN ((1, 'Aceite 5W-30 (litro)'), (2, 'Filtro de aceite'), (3, 'Balatas delanteras'),
                                   (4, 'Aceite 5W-30 (1 L)'),   (5, 'Filtro de aceite'), (7, 'Balatas delanteras'))) <> 6
  THEN
    RAISE EXCEPTION 'Las piezas 1, 2, 3, 4, 5 y 7 no están como se esperaba. No se cambia nada.';
  END IF;
END $$;

-- ---------------------------------------------------------------------
-- 1. Detalle de citas: pasar las piezas viejas a su equivalente
--    1 -> 4 (aceite), 2 -> 5 (filtro de aceite), 3 -> 7 (balatas delanteras)
--    El precio_unitario del renglón NO se toca: es el precio congelado (RN-08).
--    Si la cita ya tiene la pieza nueva, el renglón viejo es un duplicado
--    (lo creó el script de continuación al buscar por nombre) y se borra.
-- ---------------------------------------------------------------------
UPDATE "BD".citas_inventario ci
SET id_pieza = m.nueva
FROM (VALUES (1, 4), (2, 5), (3, 7)) AS m(vieja, nueva)
WHERE ci.id_pieza = m.vieja
  AND NOT EXISTS (
    SELECT 1 FROM "BD".citas_inventario x
    WHERE x.id_cita = ci.id_cita AND x.id_pieza = m.nueva
  );

DELETE FROM "BD".citas_inventario WHERE id_pieza IN (1, 2, 3);

-- ---------------------------------------------------------------------
-- 2. Borrar las piezas viejas, que ya no tienen referencias
-- ---------------------------------------------------------------------
DELETE FROM "BD".inventario WHERE id_pieza IN (1, 2, 3);

-- ---------------------------------------------------------------------
-- 3. Refacciones nuevas (24). Algunas quedan con stock bajo a propósito
--    y una agotada, para poder probar las alertas (RN-02).
-- ---------------------------------------------------------------------
INSERT INTO "BD".inventario (nombre, descripcion, cantidad, stock_minimo, precio_unitario) VALUES
('Aceite 10W-40 (1 L)',             'Aceite semisintético para motores con alto kilometraje', 30, 12,  145),
('Aceite de transmisión ATF (1 L)', 'Aceite para transmisión automática',                     10,  6,  185),
('Filtro de gasolina',              'Filtro de combustible en línea',                          7,  6,  180),
('Filtro de cabina',                'Filtro de aire acondicionado con carbón activado',        5,  6,  230),
('Bujía de cobre',                  'Bujía estándar NGK',                                     32, 16,   45),
('Cables de bujía (juego)',         'Juego de 4 cables de alta tensión',                       3,  2,  520),
('Bobina de encendido',             'Bobina individual tipo lápiz',                            4,  3,  890),
('Disco de freno delantero',        'Disco ventilado, pieza individual',                       6,  4,  780),
('Tambor de freno trasero',         'Tambor para freno trasero de auto compacto',              2,  2,  690),
('Banda de accesorios',             'Banda serpentina multi-V',                                6,  3,  340),
('Bomba de agua',                   'Bomba de agua para motor 1.6 L',                          2,  2, 1250),
('Termostato',                      'Termostato de 82 grados con empaque',                     5,  3,  260),
('Manguera de radiador superior',   'Manguera de hule reforzado',                              4,  2,  310),
('Radiador',                        'Radiador de aluminio para auto compacto',                 1,  1, 2850),
('Amortiguador trasero',            'Amortiguador de gas',                                     4,  2,  980),
('Rótula inferior',                 'Rótula de suspensión delantera',                          0,  2,  420),
('Terminal de dirección',           'Terminal exterior de dirección',                          6,  4,  290),
('Balero de rueda delantera',       'Balero doble de bolas',                                   3,  2,  560),
('Batería 12V 60Ah',                'Batería libre de mantenimiento para sedán y SUV',         2,  2, 2890),
('Alternador remanufacturado',      'Alternador de 90 amperes',                                1,  1, 3400),
('Foco H7',                         'Foco halógeno para luz baja',                            14,  6,  110),
('Plumas limpiaparabrisas (par)',   'Par de plumas de 20 y 22 pulgadas',                      10,  4,  240),
('Fusibles surtidos (caja)',        'Caja con 60 fusibles tipo cuchilla',                      8,  3,   95),
('Refrigerante R-134a (lata)',      'Lata de 340 g para aire acondicionado',                   9,  4,  165);
