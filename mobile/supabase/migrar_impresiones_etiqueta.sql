-- ============================================================
-- SIAC ERP — Migracion: tabla impresiones_etiqueta
-- ============================================================
-- El movil inserta solicitudes de impresion de etiquetas.
-- El escritorio (super_admin o service_role) las lee y procesa.
-- ============================================================

-- 1. Crear tabla
CREATE TABLE IF NOT EXISTS impresiones_etiqueta (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID NOT NULL,
    usuario_id UUID REFERENCES perfiles_usuario(id),
    payload JSONB NOT NULL,
    estatus TEXT NOT NULL DEFAULT 'pendiente',
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    procesado_en TIMESTAMPTZ
);

-- 2. Habilitar RLS
ALTER TABLE impresiones_etiqueta ENABLE ROW LEVEL SECURITY;

-- 3. Politicas

-- Usuarios autenticados INSERTAN solicitudes de su empresa
CREATE POLICY "Usuarios crean impresiones de su empresa"
    ON impresiones_etiqueta FOR INSERT
    WITH CHECK (
        auth.role() = 'authenticated'
        AND empresa_id = (
            SELECT p.empresa_id FROM perfiles_usuario p
            WHERE p.id = auth.uid()
        )
    );

-- Usuarios autenticados LEEN impresiones de su empresa
CREATE POLICY "Usuarios leen impresiones de su empresa"
    ON impresiones_etiqueta FOR SELECT
    USING (
        auth.role() = 'authenticated'
        AND empresa_id = (
            SELECT p.empresa_id FROM perfiles_usuario p
            WHERE p.id = auth.uid()
        )
    );

-- Super admin lee TODAS las impresiones (para la cola del escritorio)
CREATE POLICY "Super admin lee todas las impresiones"
    ON impresiones_etiqueta FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM perfiles_usuario
            WHERE id = auth.uid() AND rol = 'super_admin'
        )
    );

-- Super admin ACTUALIZA estatus (marcar como procesada)
CREATE POLICY "Super admin actualiza impresiones"
    ON impresiones_etiqueta FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM perfiles_usuario
            WHERE id = auth.uid() AND rol = 'super_admin'
        )
    );

-- 4. Indice para la cola de impresion
CREATE INDEX IF NOT EXISTS idx_impresiones_empresa ON impresiones_etiqueta (empresa_id);
CREATE INDEX IF NOT EXISTS idx_impresiones_estatus ON impresiones_etiqueta (estatus);
CREATE INDEX IF NOT EXISTS idx_impresiones_creado ON impresiones_etiqueta (creado_en);
