-- ============================================================
-- SIAC ERP — Migracion a Multi-Tenant
-- ============================================================
-- Ejecutar este script en Supabase SQL Editor si ya tienes
-- datos en las tablas sin empresa_id.
--
-- PASOS:
-- 1. Crear tabla empresas
-- 2. Insertar empresa por defecto
-- 3. Agregar empresa_id a todas las tablas
-- 4. Asignar empresa por defecto a todos los registros
-- 5. Actualizar politicas RLS
-- ============================================================

-- PASO 1: Crear tabla empresas
CREATE TABLE IF NOT EXISTS empresas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre TEXT NOT NULL,
    rfc TEXT,
    direccion TEXT,
    telefono TEXT,
    email TEXT,
    activo BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE empresas ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios ven su empresa"
    ON empresas FOR SELECT
    USING (
        id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

-- PASO 2: Insertar empresa por defecto
DO $$
DECLARE
    v_empresa_id UUID;
BEGIN
    -- Verificar si ya existe una empresa
    SELECT id INTO v_empresa_id FROM empresas LIMIT 1;

    IF v_empresa_id IS NULL THEN
        -- Crear empresa por defecto
        INSERT INTO empresas (id, nombre, activo)
        VALUES (gen_random_uuid(), 'SIAC ERP', true)
        RETURNING id INTO v_empresa_id;

        RAISE NOTICE 'Empresa creada: %', v_empresa_id;
    ELSE
        RAISE NOTICE 'Empresa existente: %', v_empresa_id;
    END IF;
END $$;

-- PASO 3: Agregar empresa_id a perfiles_usuario
DO $$
DECLARE
    v_empresa_id UUID;
BEGIN
    SELECT id INTO v_empresa_id FROM empresas LIMIT 1;

    -- Agregar columna si no existe
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'perfiles_usuario' AND column_name = 'empresa_id'
    ) THEN
        ALTER TABLE perfiles_usuario
        ADD COLUMN empresa_id UUID REFERENCES empresas(id);

        -- Asignar empresa a todos los perfiles
        UPDATE perfiles_usuario SET empresa_id = v_empresa_id
        WHERE empresa_id IS NULL;

        -- Hacer NOT NULL despues de actualizar
        ALTER TABLE perfiles_usuario
        ALTER COLUMN empresa_id SET NOT NULL;

        RAISE NOTICE 'perfiles_usuario: empresa_id agregado';
    END IF;
END $$;

-- PASO 4: Agregar empresa_id a todas las tablas de datos
DO $$
DECLARE
    v_empresa_id UUID;
    v_tabla TEXT;
BEGIN
    SELECT id INTO v_empresa_id FROM empresas LIMIT 1;

    -- Lista de tablas que necesitan empresa_id
    FOR v_tabla IN
        SELECT unnest(ARRAY[
            'insumos_movil',
            'ordenes_compra_movil',
            'detalle_orden_compra_movil',
            'detalle_oc_puntos_movil',
            'ordenes_produccion_movil',
            'seguimiento_produccion_movil',
            'incidencias_produccion_movil',
            'tallas_catalogo_movil',
            'logs_movil'
        ])
    LOOP
        -- Agregar columna si no existe
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = v_tabla AND column_name = 'empresa_id'
        ) THEN
            EXECUTE format(
                'ALTER TABLE %I ADD COLUMN empresa_id UUID REFERENCES empresas(id)',
                v_tabla
            );

            -- Asignar empresa a todos los registros
            EXECUTE format(
                'UPDATE %I SET empresa_id = %L WHERE empresa_id IS NULL',
                v_tabla, v_empresa_id
            );

            -- Hacer NOT NULL
            EXECUTE format(
                'ALTER TABLE %I ALTER COLUMN empresa_id SET NOT NULL',
                v_tabla
            );

            RAISE NOTICE '%: empresa_id agregado', v_tabla;
        ELSE
            RAISE NOTICE '%: empresa_id ya existe', v_tabla;
        END IF;
    END LOOP;
END $$;

-- PASO 5: Actualizar politicas RLS
-- (Eliminar politicas antiguas y crear nuevas)

-- Perfiles: usuario solo ve su propio perfil
DROP POLICY IF EXISTS "Usuarios ven su propio perfil" ON perfiles_usuario;
CREATE POLICY "Usuarios ven su propio perfil"
    ON perfiles_usuario FOR SELECT
    USING (auth.uid() = id);

-- Insumos: solo de su empresa
DROP POLICY IF EXISTS "Usuarios autenticados leen insumos" ON insumos_movil;
DROP POLICY IF EXISTS "Usuarios leen insumos de su empresa" ON insumos_movil;
CREATE POLICY "Usuarios leen insumos de su empresa"
    ON insumos_movil FOR SELECT
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

-- OC: solo de su empresa
DROP POLICY IF EXISTS "Usuarios autenticados leen OC" ON ordenes_compra_movil;
DROP POLICY IF EXISTS "Usuarios leen OC de su empresa" ON ordenes_compra_movil;
CREATE POLICY "Usuarios leen OC de su empresa"
    ON ordenes_compra_movil FOR SELECT
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

-- Detalle OC: solo de su empresa
DROP POLICY IF EXISTS "Usuarios autenticados leen detalle OC" ON detalle_orden_compra_movil;
DROP POLICY IF EXISTS "Usuarios leen detalle OC de su empresa" ON detalle_orden_compra_movil;
CREATE POLICY "Usuarios leen detalle OC de su empresa"
    ON detalle_orden_compra_movil FOR SELECT
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

-- Puntos OC: solo de su empresa
DROP POLICY IF EXISTS "Usuarios autenticados leen puntos OC" ON detalle_oc_puntos_movil;
DROP POLICY IF EXISTS "Usuarios leen puntos OC de su empresa" ON detalle_oc_puntos_movil;
CREATE POLICY "Usuarios leen puntos OC de su empresa"
    ON detalle_oc_puntos_movil FOR SELECT
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

-- OP: solo de su empresa
DROP POLICY IF EXISTS "Usuarios autenticados leen OP" ON ordenes_produccion_movil;
DROP POLICY IF EXISTS "Usuarios leen OP de su empresa" ON ordenes_produccion_movil;
CREATE POLICY "Usuarios leen OP de su empresa"
    ON ordenes_produccion_movil FOR SELECT
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

-- Seguimiento: solo de su empresa
DROP POLICY IF EXISTS "Usuarios autenticados leen seguimiento" ON seguimiento_produccion_movil;
DROP POLICY IF EXISTS "Usuarios leen seguimiento de su empresa" ON seguimiento_produccion_movil;
CREATE POLICY "Usuarios leen seguimiento de su empresa"
    ON seguimiento_produccion_movil FOR SELECT
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Usuarios actualizan seguimiento de su empresa" ON seguimiento_produccion_movil;
CREATE POLICY "Usuarios actualizan seguimiento de su empresa"
    ON seguimiento_produccion_movil FOR UPDATE
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

-- Incidencias: solo de su empresa
DROP POLICY IF EXISTS "Usuarios autenticados leen incidencias" ON incidencias_produccion_movil;
DROP POLICY IF EXISTS "Usuarios leen incidencias de su empresa" ON incidencias_produccion_movil;
CREATE POLICY "Usuarios leen incidencias de su empresa"
    ON incidencias_produccion_movil FOR SELECT
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Usuarios autenticados crean incidencias" ON incidencias_produccion_movil;
DROP POLICY IF EXISTS "Usuarios crean incidencias de su empresa" ON incidencias_produccion_movil;
CREATE POLICY "Usuarios crean incidencias de su empresa"
    ON incidencias_produccion_movil FOR INSERT
    WITH CHECK (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

-- Tallas: solo de su empresa
DROP POLICY IF EXISTS "Usuarios autenticados leen tallas" ON tallas_catalogo_movil;
DROP POLICY IF EXISTS "Usuarios leen tallas de su empresa" ON tallas_catalogo_movil;
CREATE POLICY "Usuarios leen tallas de su empresa"
    ON tallas_catalogo_movil FOR SELECT
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

-- Logs: solo de su empresa
DROP POLICY IF EXISTS "Usuarios autenticados crean logs" ON logs_movil;
DROP POLICY IF EXISTS "Usuarios crean logs de su empresa" ON logs_movil;
CREATE POLICY "Usuarios crean logs de su empresa"
    ON logs_movil FOR INSERT
    WITH CHECK (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Admin ve todos los logs" ON logs_movil;
DROP POLICY IF EXISTS "Admin ve logs de su empresa" ON logs_movil;
CREATE POLICY "Admin ve logs de su empresa"
    ON logs_movil FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM perfiles_usuario
            WHERE id = auth.uid()
              AND rol = 'admin'
              AND empresa_id = logs_movil.empresa_id
        )
    );

-- PASO 6: Crear indices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_insumos_empresa
    ON insumos_movil(empresa_id);
CREATE INDEX IF NOT EXISTS idx_oc_empresa
    ON ordenes_compra_movil(empresa_id);
CREATE INDEX IF NOT EXISTS idx_op_empresa
    ON ordenes_produccion_movil(empresa_id);
CREATE INDEX IF NOT EXISTS idx_seguimiento_empresa
    ON seguimiento_produccion_movil(empresa_id);
CREATE INDEX IF NOT EXISTS idx_perfiles_empresa
    ON perfiles_usuario(empresa_id);

-- PASO 7: Verificar migracion
DO $$
DECLARE
    v_empresa_id UUID;
    v_total INTEGER;
BEGIN
    SELECT id INTO v_empresa_id FROM empresas LIMIT 1;

    RAISE NOTICE '=== Migracion completada ===';
    RAISE NOTICE 'Empresa: %', v_empresa_id;

    SELECT COUNT(*) INTO v_total FROM perfiles_usuario WHERE empresa_id = v_empresa_id;
    RAISE NOTICE 'Perfiles: %', v_total;

    SELECT COUNT(*) INTO v_total FROM insumos_movil WHERE empresa_id = v_empresa_id;
    RAISE NOTICE 'Insumos: %', v_total;

    SELECT COUNT(*) INTO v_total FROM ordenes_compra_movil WHERE empresa_id = v_empresa_id;
    RAISE NOTICE 'OCs: %', v_total;

    SELECT COUNT(*) INTO v_total FROM ordenes_produccion_movil WHERE empresa_id = v_empresa_id;
    RAISE NOTICE 'OPs: %', v_total;

    SELECT COUNT(*) INTO v_total FROM seguimiento_produccion_movil WHERE empresa_id = v_empresa_id;
    RAISE NOTICE 'Seguimientos: %', v_total;

    SELECT COUNT(*) INTO v_total FROM tallas_catalogo_movil WHERE empresa_id = v_empresa_id;
    RAISE NOTICE 'Tallas: %', v_total;
END $$;
