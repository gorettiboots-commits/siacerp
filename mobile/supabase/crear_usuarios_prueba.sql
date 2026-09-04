-- ============================================================
-- SIAC ERP — Usuarios de prueba para Supabase
-- ============================================================
-- Ejecuta este script en Supabase SQL Editor después de crear
-- el esquema principal (schema.sql) y los usuarios en Auth.
--
-- PASOS:
-- 1. Ve a Authentication → Users
-- 2. Crea el usuario: admin@siac.com / admin123 (Auto Confirm: Sí)
-- 3. Crea el usuario: operador@siac.com / operador123 (Auto Confirm: Sí)
-- 4. Copia los UUIDs de cada usuario
-- 5. Reemplaza 'UUID_ADMIN_AQUI' y 'UUID_OPERADOR_AQUI' abajo
-- 6. Ejecuta este script en SQL Editor
-- ============================================================

-- -----------------------------------------------------------
-- USUARIO ADMIN
-- -----------------------------------------------------------
-- Reemplaza 'UUID_ADMIN_AQUI' con el UUID real del usuario
-- que creaste en Authentication → Users

INSERT INTO perfiles_usuario (id, username, nombre_completo, rol, activo)
VALUES (
    'UUID_ADMIN_AQUI',           -- <-- REEMPLAZA CON EL UUID REAL
    'admin',
    'Administrador del Sistema',
    'admin',
    true
)
ON CONFLICT (id) DO UPDATE SET
    username = EXCLUDED.username,
    nombre_completo = EXCLUDED.nombre_completo,
    rol = EXCLUDED.rol,
    activo = EXCLUDED.activo,
    updated_at = now();

-- -----------------------------------------------------------
-- USUARIO OPERADOR
-- -----------------------------------------------------------
-- Reemplaza 'UUID_OPERADOR_AQUI' con el UUID real del usuario

INSERT INTO perfiles_usuario (id, username, nombre_completo, rol, activo)
VALUES (
    'UUID_OPERADOR_AQUI',        -- <-- REEMPLAZA CON EL UUID REAL
    'operador',
    'Operador de Prueba',
    'operador',
    true
)
ON CONFLICT (id) DO UPDATE SET
    username = EXCLUDED.username,
    nombre_completo = EXCLUDED.nombre_completo,
    rol = EXCLUDED.rol,
    activo = EXCLUDED.activo,
    updated_at = now();

-- -----------------------------------------------------------
-- VERIFICAR QUE LOS PERFILES SE CREARON
-- -----------------------------------------------------------

SELECT id, username, nombre_completo, rol, activo, created_at
FROM perfiles_usuario
ORDER BY created_at;

-- -----------------------------------------------------------
-- FIN
-- -----------------------------------------------------------
