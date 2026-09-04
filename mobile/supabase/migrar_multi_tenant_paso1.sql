-- ============================================================
-- PASO 1: Crear tabla empresas y empresa_id
-- ============================================================
-- Copia TODO este codigo y pegalo en Supabase SQL Editor
-- Luego haz clic en "Run"
-- ============================================================

-- 1.1 Crear tabla empresas
CREATE TABLE IF NOT EXISTS empresas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre TEXT NOT NULL,
    rfc TEXT,
    activo BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
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

-- 1.2 Insertar empresa por defecto (SIAC ERP)
DO $$
DECLARE
    v_empresa_id UUID;
BEGIN
    SELECT id INTO v_empresa_id FROM empresas LIMIT 1;

    IF v_empresa_id IS NULL THEN
        INSERT INTO empresas (id, nombre, activo)
        VALUES (gen_random_uuid(), 'SIAC ERP', true)
        RETURNING id INTO v_empresa_id;
        RAISE NOTICE 'Empresa creada: %', v_empresa_id;
    ELSE
        RAISE NOTICE 'Empresa ya existe: %', v_empresa_id;
    END IF;
END $$;

-- 1.3 Agregar empresa_id a perfiles_usuario
DO $$
DECLARE
    v_empresa_id UUID;
BEGIN
    SELECT id INTO v_empresa_id FROM empresas LIMIT 1;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'perfiles_usuario' AND column_name = 'empresa_id'
    ) THEN
        ALTER TABLE perfiles_usuario
        ADD COLUMN empresa_id UUID REFERENCES empresas(id);

        UPDATE perfiles_usuario SET empresa_id = v_empresa_id
        WHERE empresa_id IS NULL;

        ALTER TABLE perfiles_usuario
        ALTER COLUMN empresa_id SET NOT NULL;

        RAISE NOTICE 'perfiles_usuario: empresa_id agregado';
    ELSE
        RAISE NOTICE 'perfiles_usuario: empresa_id ya existe';
    END IF;
END $$;

-- 1.4 Agregar empresa_id a insumos_movil
DO $$
DECLARE
    v_empresa_id UUID;
BEGIN
    SELECT id INTO v_empresa_id FROM empresas LIMIT 1;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'insumos_movil' AND column_name = 'empresa_id'
    ) THEN
        ALTER TABLE insumos_movil
        ADD COLUMN empresa_id UUID REFERENCES empresas(id);

        UPDATE insumos_movil SET empresa_id = v_empresa_id
        WHERE empresa_id IS NULL;

        ALTER TABLE insumos_movil
        ALTER COLUMN empresa_id SET NOT NULL;

        RAISE NOTICE 'insumos_movil: empresa_id agregado';
    ELSE
        RAISE NOTICE 'insumos_movil: empresa_id ya existe';
    END IF;
END $$;

-- 1.5 Agregar empresa_id a ordenes_compra_movil
DO $$
DECLARE
    v_empresa_id UUID;
BEGIN
    SELECT id INTO v_empresa_id FROM empresas LIMIT 1;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ordenes_compra_movil' AND column_name = 'empresa_id'
    ) THEN
        ALTER TABLE ordenes_compra_movil
        ADD COLUMN empresa_id UUID REFERENCES empresas(id);

        UPDATE ordenes_compra_movil SET empresa_id = v_empresa_id
        WHERE empresa_id IS NULL;

        ALTER TABLE ordenes_compra_movil
        ALTER COLUMN empresa_id SET NOT NULL;

        RAISE NOTICE 'ordenes_compra_movil: empresa_id agregado';
    ELSE
        RAISE NOTICE 'ordenes_compra_movil: empresa_id ya existe';
    END IF;
END $$;

-- 1.6 Agregar empresa_id a detalle_orden_compra_movil
DO $$
DECLARE
    v_empresa_id UUID;
BEGIN
    SELECT id INTO v_empresa_id FROM empresas LIMIT 1;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'detalle_orden_compra_movil' AND column_name = 'empresa_id'
    ) THEN
        ALTER TABLE detalle_orden_compra_movil
        ADD COLUMN empresa_id UUID REFERENCES empresas(id);

        UPDATE detalle_orden_compra_movil SET empresa_id = v_empresa_id
        WHERE empresa_id IS NULL;

        ALTER TABLE detalle_orden_compra_movil
        ALTER COLUMN empresa_id SET NOT NULL;

        RAISE NOTICE 'detalle_orden_compra_movil: empresa_id agregado';
    ELSE
        RAISE NOTICE 'detalle_orden_compra_movil: empresa_id ya existe';
    END IF;
END $$;

-- 1.7 Agregar empresa_id a detalle_oc_puntos_movil
DO $$
DECLARE
    v_empresa_id UUID;
BEGIN
    SELECT id INTO v_empresa_id FROM empresas LIMIT 1;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'detalle_oc_puntos_movil' AND column_name = 'empresa_id'
    ) THEN
        ALTER TABLE detalle_oc_puntos_movil
        ADD COLUMN empresa_id UUID REFERENCES empresas(id);

        UPDATE detalle_oc_puntos_movil SET empresa_id = v_empresa_id
        WHERE empresa_id IS NULL;

        ALTER TABLE detalle_oc_puntos_movil
        ALTER COLUMN empresa_id SET NOT NULL;

        RAISE NOTICE 'detalle_oc_puntos_movil: empresa_id agregado';
    ELSE
        RAISE NOTICE 'detalle_oc_puntos_movil: empresa_id ya existe';
    END IF;
END $$;

-- 1.8 Agregar empresa_id a ordenes_produccion_movil
DO $$
DECLARE
    v_empresa_id UUID;
BEGIN
    SELECT id INTO v_empresa_id FROM empresas LIMIT 1;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ordenes_produccion_movil' AND column_name = 'empresa_id'
    ) THEN
        ALTER TABLE ordenes_produccion_movil
        ADD COLUMN empresa_id UUID REFERENCES empresas(id);

        UPDATE ordenes_produccion_movil SET empresa_id = v_empresa_id
        WHERE empresa_id IS NULL;

        ALTER TABLE ordenes_produccion_movil
        ALTER COLUMN empresa_id SET NOT NULL;

        RAISE NOTICE 'ordenes_produccion_movil: empresa_id agregado';
    ELSE
        RAISE NOTICE 'ordenes_produccion_movil: empresa_id ya existe';
    END IF;
END $$;

-- 1.9 Agregar empresa_id a seguimiento_produccion_movil
DO $$
DECLARE
    v_empresa_id UUID;
BEGIN
    SELECT id INTO v_empresa_id FROM empresas LIMIT 1;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'seguimiento_produccion_movil' AND column_name = 'empresa_id'
    ) THEN
        ALTER TABLE seguimiento_produccion_movil
        ADD COLUMN empresa_id UUID REFERENCES empresas(id);

        UPDATE seguimiento_produccion_movil SET empresa_id = v_empresa_id
        WHERE empresa_id IS NULL;

        ALTER TABLE seguimiento_produccion_movil
        ALTER COLUMN empresa_id SET NOT NULL;

        RAISE NOTICE 'seguimiento_produccion_movil: empresa_id agregado';
    ELSE
        RAISE NOTICE 'seguimiento_produccion_movil: empresa_id ya existe';
    END IF;
END $$;

-- 1.10 Agregar empresa_id a incidencias_produccion_movil
DO $$
DECLARE
    v_empresa_id UUID;
BEGIN
    SELECT id INTO v_empresa_id FROM empresas LIMIT 1;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'incidencias_produccion_movil' AND column_name = 'empresa_id'
    ) THEN
        ALTER TABLE incidencias_produccion_movil
        ADD COLUMN empresa_id UUID REFERENCES empresas(id);

        UPDATE incidencias_produccion_movil SET empresa_id = v_empresa_id
        WHERE empresa_id IS NULL;

        ALTER TABLE incidencias_produccion_movil
        ALTER COLUMN empresa_id SET NOT NULL;

        RAISE NOTICE 'incidencias_produccion_movil: empresa_id agregado';
    ELSE
        RAISE NOTICE 'incidencias_produccion_movil: empresa_id ya existe';
    END IF;
END $$;

-- 1.11 Agregar empresa_id a tallas_catalogo_movil
DO $$
DECLARE
    v_empresa_id UUID;
BEGIN
    SELECT id INTO v_empresa_id FROM empresas LIMIT 1;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tallas_catalogo_movil' AND column_name = 'empresa_id'
    ) THEN
        ALTER TABLE tallas_catalogo_movil
        ADD COLUMN empresa_id UUID REFERENCES empresas(id);

        UPDATE tallas_catalogo_movil SET empresa_id = v_empresa_id
        WHERE empresa_id IS NULL;

        ALTER TABLE tallas_catalogo_movil
        ALTER COLUMN empresa_id SET NOT NULL;

        RAISE NOTICE 'tallas_catalogo_movil: empresa_id agregado';
    ELSE
        RAISE NOTICE 'tallas_catalogo_movil: empresa_id ya existe';
    END IF;
END $$;

-- 1.12 Agregar empresa_id a logs_movil
DO $$
DECLARE
    v_empresa_id UUID;
BEGIN
    SELECT id INTO v_empresa_id FROM empresas LIMIT 1;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'logs_movil' AND column_name = 'empresa_id'
    ) THEN
        ALTER TABLE logs_movil
        ADD COLUMN empresa_id UUID REFERENCES empresas(id);

        UPDATE logs_movil SET empresa_id = v_empresa_id
        WHERE empresa_id IS NULL;

        ALTER TABLE logs_movil
        ALTER COLUMN empresa_id SET NOT NULL;

        RAISE NOTICE 'logs_movil: empresa_id agregado';
    ELSE
        RAISE NOTICE 'logs_movil: empresa_id ya existe';
    END IF;
END $$;

-- 1.13 Crear indices para rendimiento
CREATE INDEX IF NOT EXISTS idx_insumos_empresa ON insumos_movil(empresa_id);
CREATE INDEX IF NOT EXISTS idx_oc_empresa ON ordenes_compra_movil(empresa_id);
CREATE INDEX IF NOT EXISTS idx_op_empresa ON ordenes_produccion_movil(empresa_id);
CREATE INDEX IF NOT EXISTS idx_seguimiento_empresa ON seguimiento_produccion_movil(empresa_id);
CREATE INDEX IF NOT EXISTS idx_perfiles_empresa ON perfiles_usuario(empresa_id);

-- 1.14 Verificar resultado
DO $$
DECLARE
    v_empresa_id UUID;
    v_total INTEGER;
BEGIN
    SELECT id INTO v_empresa_id FROM empresas LIMIT 1;

    RAISE NOTICE '';
    RAISE NOTICE '=== MIGRACION PASO 1 COMPLETADO ===';
    RAISE NOTICE 'Empresa ID: %', v_empresa_id;

    SELECT COUNT(*) INTO v_total FROM perfiles_usuario WHERE empresa_id = v_empresa_id;
    RAISE NOTICE 'Perfiles: % registros con empresa_id', v_total;

    SELECT COUNT(*) INTO v_total FROM insumos_movil WHERE empresa_id = v_empresa_id;
    RAISE NOTICE 'Insumos: % registros con empresa_id', v_total;

    SELECT COUNT(*) INTO v_total FROM ordenes_compra_movil WHERE empresa_id = v_empresa_id;
    RAISE NOTICE 'OCs: % registros con empresa_id', v_total;

    SELECT COUNT(*) INTO v_total FROM ordenes_produccion_movil WHERE empresa_id = v_empresa_id;
    RAISE NOTICE 'OPs: % registros con empresa_id', v_total;

    SELECT COUNT(*) INTO v_total FROM seguimiento_produccion_movil WHERE empresa_id = v_empresa_id;
    RAISE NOTICE 'Seguimientos: % registros con empresa_id', v_total;

    SELECT COUNT(*) INTO v_total FROM tallas_catalogo_movil WHERE empresa_id = v_empresa_id;
    RAISE NOTICE 'Tallas: % registros con empresa_id', v_total;
END $$;
