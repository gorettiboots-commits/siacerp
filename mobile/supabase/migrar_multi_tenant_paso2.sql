-- ============================================================
-- PASO 2: Actualizar politicas RLS para multi-tenant
-- ============================================================
-- Ejecutar DESPUES del Paso 1.
-- Copia TODO este codigo y pegalo en Supabase SQL Editor.
-- ============================================================

-- 2.1 Insumos: solo ver datos de su empresa
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

-- 2.2 OC: solo ver datos de su empresa
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

-- 2.3 Detalle OC: solo ver datos de su empresa
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

-- 2.4 Puntos OC: solo ver datos de su empresa
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

-- 2.5 OP: solo ver datos de su empresa
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

-- 2.6 Seguimiento: solo ver y actualizar datos de su empresa
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

-- 2.7 Incidencias: solo ver y crear en su empresa
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

-- 2.8 Tallas: solo ver datos de su empresa
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

-- 2.9 Logs: solo ver y crear en su empresa
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

-- 2.10 Verificar politicas actualizadas
SELECT
    schemaname,
    tablename,
    policyname,
    cmd,
    qual
FROM pg_policies
WHERE schemaname = 'public'
  AND tablename IN (
    'insumos_movil',
    'ordenes_compra_movil',
    'detalle_orden_compra_movil',
    'detalle_oc_puntos_movil',
    'ordenes_produccion_movil',
    'seguimiento_produccion_movil',
    'incidencias_produccion_movil',
    'tallas_catalogo_movil',
    'logs_movil',
    'perfiles_usuario'
  )
ORDER BY tablename, policyname;

-- Mensaje final
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== PASO 2 COMPLETADO ===';
    RAISE NOTICE 'Politicas RLS actualizadas para multi-tenant';
    RAISE NOTICE '';
    RAISE NOTICE 'Ahora ejecuta el Paso 3 (sincronizar datos con empresa_id)';
END $$;
