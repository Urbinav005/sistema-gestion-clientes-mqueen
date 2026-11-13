-- =====================================================================
--  CONTINUACIÓN: correr esto DESPUÉS del error de citas.
--  (Clientes, vehículos e inventario ya quedaron guardados.)
--  Estados válidos: Pendiente, En proceso, Terminada, Cancelada
-- =====================================================================
SET search_path TO "BD";

-- ---------------------------------------------------------------------
-- 5. Citas (se ligan al vehículo por placas)
-- ---------------------------------------------------------------------
INSERT INTO citas (id_vehiculo, fecha, motivo, estado, costo_mano_obra) VALUES
((SELECT id_vehiculo FROM vehiculos WHERE placas='FGH-123-A'), NOW() - INTERVAL '40 days', 'Cambio de aceite y filtro',        'Terminada', 250),
((SELECT id_vehiculo FROM vehiculos WHERE placas='DUR-789-C'), NOW() - INTERVAL '25 days', 'Cambio de balatas delanteras',     'Terminada', 450),
((SELECT id_vehiculo FROM vehiculos WHERE placas='DUR-321-D'), NOW() - INTERVAL '12 days', 'Afinación mayor',                  'Terminada', 900),
((SELECT id_vehiculo FROM vehiculos WHERE placas='FGH-456-B'), NOW() - INTERVAL '2 days',  'Ruido en suspensión',              'En proceso', 600),
((SELECT id_vehiculo FROM vehiculos WHERE placas='FMX-654-E'), CURRENT_DATE + TIME '10:00','Servicio de 40,000 km',            'Pendiente',  700),
((SELECT id_vehiculo FROM vehiculos WHERE placas='FMX-987-F'), CURRENT_DATE + TIME '13:30','Revisión de frenos',               'Pendiente',  350),
((SELECT id_vehiculo FROM vehiculos WHERE placas='DGO-111-G'), NOW() + INTERVAL '3 days',  'Cambio de batería',                'Pendiente',  150);

-- ---------------------------------------------------------------------
-- 6. Piezas usadas en cada cita (citas_inventario)
-- ---------------------------------------------------------------------
INSERT INTO citas_inventario (id_cita, id_pieza, cantidad, precio_unitario)
SELECT c.id_cita, i.id_pieza, x.cant, i.precio_unitario
FROM (VALUES
  ('FGH-123-A', 'Cambio de aceite y filtro',    'Aceite 5W-30 (1 L)',      4),
  ('FGH-123-A', 'Cambio de aceite y filtro',    'Filtro de aceite',        1),
  ('DUR-789-C', 'Cambio de balatas delanteras', 'Balatas delanteras',      1),
  ('DUR-789-C', 'Cambio de balatas delanteras', 'Líquido de frenos DOT 4', 1),
  ('DUR-321-D', 'Afinación mayor',              'Bujía de iridio',         4),
  ('DUR-321-D', 'Afinación mayor',              'Filtro de aire',          1),
  ('DUR-321-D', 'Afinación mayor',              'Aceite 5W-30 (1 L)',      5),
  ('DUR-321-D', 'Afinación mayor',              'Filtro de aceite',        1),
  ('FGH-456-B', 'Ruido en suspensión',          'Amortiguador delantero',  2)
) AS x(placas, motivo, pieza, cant)
JOIN vehiculos v  ON v.placas = x.placas
JOIN citas c      ON c.id_vehiculo = v.id_vehiculo AND c.motivo = x.motivo
JOIN inventario i ON i.nombre = x.pieza;


-- =====================================================================
--  CONSULTAS DE NEGOCIO (para la demo)
-- =====================================================================

-- Q1. Refacciones con stock bajo (alerta de reabastecimiento)
SELECT nombre, cantidad, stock_minimo,
       stock_minimo - cantidad AS faltan
FROM inventario
WHERE cantidad <= stock_minimo
ORDER BY faltan DESC;

-- Q2. Citas de hoy con cliente y vehículo
SELECT c.fecha::time AS hora, cl.nombre AS cliente, cl.telefono,
       v.marca || ' ' || v.modelo AS vehiculo, v.placas, c.motivo, c.estado
FROM citas c
JOIN vehiculos v ON v.id_vehiculo = c.id_vehiculo
JOIN clientes cl ON cl.id_cliente = v.id_cliente
WHERE c.fecha::date = CURRENT_DATE
ORDER BY c.fecha;

-- Q3. Historial de servicios de un vehículo (por placas)
SELECT c.fecha::date, c.motivo, c.estado, c.costo_mano_obra
FROM citas c
JOIN vehiculos v ON v.id_vehiculo = c.id_vehiculo
WHERE v.placas = 'DUR-321-D'
ORDER BY c.fecha DESC;

-- Q4. Total cobrado por cita (mano de obra + refacciones)
SELECT c.id_cita, v.placas, c.motivo,
       c.costo_mano_obra,
       COALESCE(SUM(ci.cantidad * ci.precio_unitario), 0) AS refacciones,
       c.costo_mano_obra + COALESCE(SUM(ci.cantidad * ci.precio_unitario), 0) AS total
FROM citas c
JOIN vehiculos v ON v.id_vehiculo = c.id_vehiculo
LEFT JOIN citas_inventario ci ON ci.id_cita = c.id_cita
GROUP BY c.id_cita, v.placas, c.motivo, c.costo_mano_obra
ORDER BY c.id_cita;

-- Q5. Refacciones más usadas
SELECT i.nombre, SUM(ci.cantidad) AS unidades_usadas
FROM citas_inventario ci
JOIN inventario i ON i.id_pieza = ci.id_pieza
GROUP BY i.nombre
ORDER BY unidades_usadas DESC;

-- Q6. Valor total del inventario en almacén
SELECT SUM(cantidad * precio_unitario) AS valor_inventario FROM inventario;


-- =====================================================================
--  REGLA DE NEGOCIO: descontar una refacción SOLO si hay stock suficiente
--  (demo en vivo: ejecuta los dos UPDATE y compara las filas afectadas)
-- =====================================================================

-- Caso válido: hay 12 bujías -> se descuentan 4 (1 fila afectada)
UPDATE inventario
SET cantidad = cantidad - 4
WHERE nombre = 'Bujía de iridio' AND cantidad >= 4;

-- Caso de error: solo hay 1 batería -> no se descuenta nada (0 filas)
UPDATE inventario
SET cantidad = cantidad - 2
WHERE nombre = 'Batería 12V 45Ah' AND cantidad >= 2;

-- Verificar
SELECT nombre, cantidad FROM inventario
WHERE nombre IN ('Bujía de iridio', 'Batería 12V 45Ah');
