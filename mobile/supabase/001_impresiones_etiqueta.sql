-- ============================================================
-- MIGRACION 001: Tabla impresiones_etiqueta
-- ============================================================
-- Crea la tabla para solicitudes de impresion de etiquetas
-- desde el movil. El escritorio las lee y procesa.
-- Fecha: 2026-08-31
-- ============================================================

-- Eliminar tabla vieja si existe (ya tenia columnas incorrectas)
DROP TABLE IF EXISTS impresiones_etiqueta CASCADE;

-- Crear tabla con empresa_id
CREATE TABLE impresiones_etiqueta (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    empresa_id UUID NOT NULL,
    usuario_id UUID REFERENCES perfiles_usuario(id),
    payload JSONB NOT NULL,
    estatus TEXT NOT NULL DEFAULT 'pendiente',
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    procesado_en TIMESTAMPTZ
);

-- Habilitar RLS
ALTER TABLE impresiones_etiqueta ENABLE ROW LEVEL SECURITY;

-- Politica INSERT: usuarios autenticados crean impresiones de su empresa
CREATE POLICY "Usuarios crean impresiones de su empresa"
    ON impresiones_etiqueta FOR INSERT
    WITH CHECK (
        auth.role() = 'authenticated'
        AND empresa_id = (
            SELECT p.empresa_id FROM perfiles_usuario p
            WHERE p.id = auth.uid()
        )
    );

-- Politica SELECT: usuarios leen impresiones de su empresa
CREATE POLICY "Usuarios leen impresiones de su empresa"
    ON impresiones_etiqueta FOR SELECT
    USING (
        auth.role() = 'authenticated'
        AND empresa_id = (
            SELECT p.empresa_id FROM perfiles_usuario p
            WHERE p.id = auth.uid()
        )
    );

-- Politica SELECT: super_admin lee TODAS las impresiones (cola del escritorio)
CREATE POLICY "Super admin lee todas las impresiones"
    ON impresiones_etiqueta FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM perfiles_usuario
            WHERE id = auth.uid() AND rol = 'super_admin'
        )
    );

-- Politica UPDATE: super_admin actualiza estatus (marcar como procesada)
CREATE POLICY "Super admin actualiza impresiones"
    ON impresiones_etiqueta FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM perfiles_usuario
            WHERE id = auth.uid() AND rol = 'super_admin'
        )
    );

-- Indices para rendimiento
CREATE INDEX idx_impresiones_empresa ON impresiones_etiqueta (empresa_id);
CREATE INDEX idx_impresiones_estatus ON impresiones_etiqueta (estatus);
CREATE INDEX idx_impresiones_creado ON impresiones_etiqueta (creado_en);
