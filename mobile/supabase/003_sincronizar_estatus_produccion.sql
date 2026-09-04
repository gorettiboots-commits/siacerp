-- ============================================================
-- MIGRACION 003: Estatus de produccion para programacion
-- ============================================================
-- Vista que muestra si una semana de programacion tiene
-- una OP asociada en produccion.
-- Fecha: 2026-08-31
-- ============================================================

-- Vista que muestra el estatus de produccion por semana
-- (no intenta unir directamente porque no hay FK entre las tablas)
CREATE OR REPLACE VIEW programacion_estatus_produccion AS
SELECT
    ps.id AS semana_id,
    ps.nombre AS semana_nombre,
    ps.empresa_id,
    -- Contar OPs asociadas a esta empresa
    (SELECT COUNT(*)
     FROM ordenes_produccion_movil op
     WHERE op.empresa_id = ps.empresa_id
       AND op.estatus IN ('en_produccion', 'terminada')
    ) AS ops_en_produccion
FROM programacion_semana_movil ps;
