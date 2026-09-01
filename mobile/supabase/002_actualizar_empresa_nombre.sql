-- ============================================================
-- MIGRACION 002: Actualizar nombre de empresa
-- ============================================================
-- Cambia el nombre de la empresa de "SIAC ERP" a "EskinBoots"
-- para que coincida con la configuracion del escritorio.
-- Fecha: 2026-08-31
-- ============================================================

-- Ver el registro actual
SELECT id, nombre, rfc, activo FROM empresas;

-- Actualizar nombre
UPDATE empresas
SET nombre = 'EskinBoots'
WHERE nombre = 'SIAC ERP';

-- Verificar cambio
SELECT id, nombre, rfc, activo FROM empresas;
