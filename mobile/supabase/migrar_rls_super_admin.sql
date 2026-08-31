-- ============================================================
-- SIAC ERP — Migración: RLS super_admin + empresa activa
-- ============================================================
-- Ejecutar en Supabase SQL Editor después del schema_multi_tenant.sql
-- Fecha: 2026-08-30
-- ============================================================

-- -----------------------------------------------------------
-- 1. FUNCIÓN AUXILIAR: verificar si el usuario es super_admin
-- -----------------------------------------------------------
CREATE OR REPLACE FUNCTION es_super_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM perfiles_usuario
        WHERE id = auth.uid() AND rol = 'super_admin'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

-- -----------------------------------------------------------
-- 2. FUNCIÓN AUXILIAR: verificar si la empresa está activa
-- -----------------------------------------------------------
CREATE OR REPLACE FUNCTION empresa_esta_activa(p_empresa_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM empresas
        WHERE id = p_empresa_id AND activo = true
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

-- -----------------------------------------------------------
-- 3. POLÍTICAS DE SUPER_ADMIN: bypass RLS en TODAS las tablas
-- -----------------------------------------------------------
-- El super_admin puede leer/escribir todo sin restricción de empresa.

-- EMPRESAS: super_admin ve todas
DROP POLICY IF EXISTS "Super admin ve todas las empresas" ON empresas;
CREATE POLICY "Super admin ve todas las empresas"
    ON empresas FOR SELECT
    USING (es_super_admin());

-- EMPRESAS: super_admin puede actualizar (activar/desactivar)
DROP POLICY IF EXISTS "Super admin gestiona empresas" ON empresas;
CREATE POLICY "Super admin gestiona empresas"
    ON empresas FOR UPDATE
    USING (es_super_admin());

-- PERFILES: super_admin ve todos los perfiles
DROP POLICY IF EXISTS "Super admin ve todos los perfiles" ON perfiles_usuario;
CREATE POLICY "Super admin ve todos los perfiles"
    ON perfiles_usuario FOR SELECT
    USING (es_super_admin());

-- PERFILES: super_admin puede actualizar perfiles
DROP POLICY IF EXISTS "Super admin gestiona perfiles" ON perfiles_usuario;
CREATE POLICY "Super admin gestiona perfiles"
    ON perfiles_usuario FOR UPDATE
    USING (es_super_admin());

-- PERFILES: super_admin puede insertar perfiles
DROP POLICY IF EXISTS "Super admin crea perfiles" ON perfiles_usuario;
CREATE POLICY "Super admin crea perfiles"
    ON perfiles_usuario FOR INSERT
    WITH CHECK (es_super_admin());

-- INSUMOS: super_admin lee todo
DROP POLICY IF EXISTS "Super admin lee insumos" ON insumos_movil;
CREATE POLICY "Super admin lee insumos"
    ON insumos_movil FOR SELECT
    USING (es_super_admin());

-- OC: super_admin lee todo
DROP POLICY IF EXISTS "Super admin lee OC" ON ordenes_compra_movil;
CREATE POLICY "Super admin lee OC"
    ON ordenes_compra_movil FOR SELECT
    USING (es_super_admin());

-- DETALLE OC: super_admin lee todo
DROP POLICY IF EXISTS "Super admin lee detalle OC" ON detalle_orden_compra_movil;
CREATE POLICY "Super admin lee detalle OC"
    ON detalle_orden_compra_movil FOR SELECT
    USING (es_super_admin());

-- PUNTOS OC: super_admin lee todo
DROP POLICY IF EXISTS "Super admin lee puntos OC" ON detalle_oc_puntos_movil;
CREATE POLICY "Super admin lee puntos OC"
    ON detalle_oc_puntos_movil FOR SELECT
    USING (es_super_admin());

-- OP: super_admin lee todo
DROP POLICY IF EXISTS "Super admin lee OP" ON ordenes_produccion_movil;
CREATE POLICY "Super admin lee OP"
    ON ordenes_produccion_movil FOR SELECT
    USING (es_super_admin());

-- SEGUIMIENTO: super_admin lee todo
DROP POLICY IF EXISTS "Super admin lee seguimiento" ON seguimiento_produccion_movil;
CREATE POLICY "Super admin lee seguimiento"
    ON seguimiento_produccion_movil FOR SELECT
    USING (es_super_admin());

-- SEGUIMIENTO: super_admin actualiza
DROP POLICY IF EXISTS "Super admin actualiza seguimiento" ON seguimiento_produccion_movil;
CREATE POLICY "Super admin actualiza seguimiento"
    ON seguimiento_produccion_movil FOR UPDATE
    USING (es_super_admin());

-- INCIDENCIAS: super_admin lee todo
DROP POLICY IF EXISTS "Super admin lee incidencias" ON incidencias_produccion_movil;
CREATE POLICY "Super admin lee incidencias"
    ON incidencias_produccion_movil FOR SELECT
    USING (es_super_admin());

-- TALLAS: super_admin lee todo
DROP POLICY IF EXISTS "Super admin lee tallas" ON tallas_catalogo_movil;
CREATE POLICY "Super admin lee tallas"
    ON tallas_catalogo_movil FOR SELECT
    USING (es_super_admin());

-- LOGS: super_admin lee todo
DROP POLICY IF EXISTS "Super admin lee logs" ON logs_movil;
CREATE POLICY "Super admin lee logs"
    ON logs_movil FOR SELECT
    USING (es_super_admin());

-- LOGS: super_admin crea logs
DROP POLICY IF EXISTS "Super admin crea logs" ON logs_movil;
CREATE POLICY "Super admin crea logs"
    ON logs_movil FOR INSERT
    WITH CHECK (es_super_admin());

-- CLIENTES: super_admin lee todo
DROP POLICY IF EXISTS "Super admin lee clientes" ON clientes_movil;
CREATE POLICY "Super admin lee clientes"
    ON clientes_movil FOR SELECT
    USING (es_super_admin());

-- PEDIDOS: super_admin lee todo
DROP POLICY IF EXISTS "Super admin lee pedidos" ON pedidos_cliente_movil;
CREATE POLICY "Super admin lee pedidos"
    ON pedidos_cliente_movil FOR SELECT
    USING (es_super_admin());

-- DETALLE PEDIDO: super_admin lee todo
DROP POLICY IF EXISTS "Super admin lee detalle pedidos" ON detalle_pedido_cliente_movil;
CREATE POLICY "Super admin lee detalle pedidos"
    ON detalle_pedido_cliente_movil FOR SELECT
    USING (es_super_admin());

-- PUNTOS PEDIDO: super_admin lee todo
DROP POLICY IF EXISTS "Super admin lee puntos pedidos" ON detalle_pedido_puntos_movil;
CREATE POLICY "Super admin lee puntos pedidos"
    ON detalle_pedido_puntos_movil FOR SELECT
    USING (es_super_admin());

-- PROGRAMACIÓN SEMANA: super_admin lee todo
DROP POLICY IF EXISTS "Super admin lee semanas prog" ON programacion_semana_movil;
CREATE POLICY "Super admin lee semanas prog"
    ON programacion_semana_movil FOR SELECT
    USING (es_super_admin());

-- PROGRAMACIÓN LÍNEAS: super_admin lee todo
DROP POLICY IF EXISTS "Super admin lee líneas prog" ON programacion_lineas_movil;
CREATE POLICY "Super admin lee líneas prog"
    ON programacion_lineas_movil FOR SELECT
    USING (es_super_admin());

-- PROGRAMACIÓN TALLAS: super_admin lee todo
DROP POLICY IF EXISTS "Super admin lee tallas prog" ON programacion_linea_tallas_movil;
CREATE POLICY "Super admin lee tallas prog"
    ON programacion_linea_tallas_movil FOR SELECT
    USING (es_super_admin());

-- -----------------------------------------------------------
-- 4. POLÍTICAS DE EMPRESA ACTIVA: login solo si empresa activa
-- -----------------------------------------------------------
-- Los usuarios normales NO pueden ver datos de empresas desactivadas

-- Reemplazar política de empresas para que solo vean la suya Y activa
DROP POLICY IF EXISTS "Usuarios ven su empresa" ON empresas;
CREATE POLICY "Usuarios ven su empresa"
    ON empresas FOR SELECT
    USING (
        es_super_admin()
        OR (
            activo = true
            AND id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid()
            )
        )
    );

-- Reemplazar políticas de insumos para verificar empresa activa
DROP POLICY IF EXISTS "Usuarios leen insumos de su empresa" ON insumos_movil;
CREATE POLICY "Usuarios leen insumos de su empresa"
    ON insumos_movil FOR SELECT
    USING (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid()
            )
        )
    );

-- OC: verificar empresa activa
DROP POLICY IF EXISTS "Usuarios leen OC de su empresa" ON ordenes_compra_movil;
CREATE POLICY "Usuarios leen OC de su empresa"
    ON ordenes_compra_movil FOR SELECT
    USING (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid()
            )
        )
    );

-- Detalle OC: verificar empresa activa
DROP POLICY IF EXISTS "Usuarios leen detalle OC de su empresa" ON detalle_orden_compra_movil;
CREATE POLICY "Usuarios leen detalle OC de su empresa"
    ON detalle_orden_compra_movil FOR SELECT
    USING (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid()
            )
        )
    );

-- Puntos OC: verificar empresa activa
DROP POLICY IF EXISTS "Usuarios leen puntos OC de su empresa" ON detalle_oc_puntos_movil;
CREATE POLICY "Usuarios leen puntos OC de su empresa"
    ON detalle_oc_puntos_movil FOR SELECT
    USING (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid()
            )
        )
    );

-- OP: verificar empresa activa
DROP POLICY IF EXISTS "Usuarios leen OP de su empresa" ON ordenes_produccion_movil;
CREATE POLICY "Usuarios leen OP de su empresa"
    ON ordenes_produccion_movil FOR SELECT
    USING (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid()
            )
        )
    );

-- Seguimiento: verificar empresa activa
DROP POLICY IF EXISTS "Usuarios leen seguimiento de su empresa" ON seguimiento_produccion_movil;
CREATE POLICY "Usuarios leen seguimiento de su empresa"
    ON seguimiento_produccion_movil FOR SELECT
    USING (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid()
            )
        )
    );

DROP POLICY IF EXISTS "Usuarios actualizan seguimiento de su empresa" ON seguimiento_produccion_movil;
CREATE POLICY "Usuarios actualizan seguimiento de su empresa"
    ON seguimiento_produccion_movil FOR UPDATE
    USING (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid()
            )
        )
    );

-- Incidencias: verificar empresa activa
DROP POLICY IF EXISTS "Usuarios leen incidencias de su empresa" ON incidencias_produccion_movil;
CREATE POLICY "Usuarios leen incidencias de su empresa"
    ON incidencias_produccion_movil FOR SELECT
    USING (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid()
            )
        )
    );

DROP POLICY IF EXISTS "Usuarios crean incidencias de su empresa" ON incidencias_produccion_movil;
CREATE POLICY "Usuarios crean incidencias de su empresa"
    ON incidencias_produccion_movil FOR INSERT
    WITH CHECK (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid()
            )
        )
    );

-- Tallas: verificar empresa activa
DROP POLICY IF EXISTS "Usuarios leen tallas de su empresa" ON tallas_catalogo_movil;
CREATE POLICY "Usuarios leen tallas de su empresa"
    ON tallas_catalogo_movil FOR SELECT
    USING (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid()
            )
        )
    );

-- Logs: verificar empresa activa
DROP POLICY IF EXISTS "Usuarios crean logs de su empresa" ON logs_movil;
CREATE POLICY "Usuarios crean logs de su empresa"
    ON logs_movil FOR INSERT
    WITH CHECK (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid()
            )
        )
    );

DROP POLICY IF EXISTS "Admin ve logs de su empresa" ON logs_movil;
CREATE POLICY "Admin ve logs de su empresa"
    ON logs_movil FOR SELECT
    USING (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND EXISTS (
                SELECT 1 FROM perfiles_usuario
                WHERE id = auth.uid()
                  AND rol = 'admin'
                  AND empresa_id = logs_movil.empresa_id
            )
        )
    );

-- Clientes: verificar empresa activa
DROP POLICY IF EXISTS "Usuarios leen clientes de su empresa" ON clientes_movil;
CREATE POLICY "Usuarios leen clientes de su empresa"
    ON clientes_movil FOR SELECT
    USING (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid()
            )
        )
    );

DROP POLICY IF EXISTS "Admin inserta clientes de su empresa" ON clientes_movil;
CREATE POLICY "Admin inserta clientes de su empresa"
    ON clientes_movil FOR INSERT
    WITH CHECK (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid() AND rol = 'admin'
            )
        )
    );

DROP POLICY IF EXISTS "Admin actualiza clientes de su empresa" ON clientes_movil;
CREATE POLICY "Admin actualiza clientes de su empresa"
    ON clientes_movil FOR UPDATE
    USING (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid() AND rol = 'admin'
            )
        )
    );

-- Pedidos: verificar empresa activa
DROP POLICY IF EXISTS "Usuarios leen pedidos de su empresa" ON pedidos_cliente_movil;
CREATE POLICY "Usuarios leen pedidos de su empresa"
    ON pedidos_cliente_movil FOR SELECT
    USING (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid()
            )
        )
    );

DROP POLICY IF EXISTS "Admin inserta pedidos de su empresa" ON pedidos_cliente_movil;
CREATE POLICY "Admin inserta pedidos de su empresa"
    ON pedidos_cliente_movil FOR INSERT
    WITH CHECK (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid() AND rol = 'admin'
            )
        )
    );

DROP POLICY IF EXISTS "Admin actualiza pedidos de su empresa" ON pedidos_cliente_movil;
CREATE POLICY "Admin actualiza pedidos de su empresa"
    ON pedidos_cliente_movil FOR UPDATE
    USING (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid() AND rol = 'admin'
            )
        )
    );

-- Detalle pedido: verificar empresa activa
DROP POLICY IF EXISTS "Usuarios leen detalle pedidos de su empresa" ON detalle_pedido_cliente_movil;
CREATE POLICY "Usuarios leen detalle pedidos de su empresa"
    ON detalle_pedido_cliente_movil FOR SELECT
    USING (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid()
            )
        )
    );

-- Puntos pedido: verificar empresa activa
DROP POLICY IF EXISTS "Usuarios leen puntos pedidos de su empresa" ON detalle_pedido_puntos_movil;
CREATE POLICY "Usuarios leen puntos pedidos de su empresa"
    ON detalle_pedido_puntos_movil FOR SELECT
    USING (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid()
            )
        )
    );

-- Programación semanas: verificar empresa activa
DROP POLICY IF EXISTS "Usuarios leen semanas de su empresa" ON programacion_semana_movil;
CREATE POLICY "Usuarios leen semanas de su empresa"
    ON programacion_semana_movil FOR SELECT
    USING (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid()
            )
        )
    );

-- Programación líneas: verificar empresa activa
DROP POLICY IF EXISTS "Usuarios leen líneas de su empresa" ON programacion_lineas_movil;
CREATE POLICY "Usuarios leen líneas de su empresa"
    ON programacion_lineas_movil FOR SELECT
    USING (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid()
            )
        )
    );

-- Programación tallas: verificar empresa activa
DROP POLICY IF EXISTS "Usuarios leen tallas línea de su empresa" ON programacion_linea_tallas_movil;
CREATE POLICY "Usuarios leen tallas línea de su empresa"
    ON programacion_linea_tallas_movil FOR SELECT
    USING (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid()
            )
        )
    );

-- -----------------------------------------------------------
-- 5. POLÍTICAS DELETE faltantes (D-12)
-- -----------------------------------------------------------
-- Agregar DELETE donde aplique para completar CRUD

-- TALLAS: admin puede eliminar
DROP POLICY IF EXISTS "Admin elimina tallas" ON tallas_catalogo_movil;
CREATE POLICY "Admin elimina tallas"
    ON tallas_catalogo_movil FOR DELETE
    USING (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid() AND rol = 'admin'
            )
        )
    );

-- PROGRAMACIÓN LÍNEAS: admin puede eliminar
DROP POLICY IF EXISTS "Admin elimina líneas prog" ON programacion_lineas_movil;
CREATE POLICY "Admin elimina líneas prog"
    ON programacion_lineas_movil FOR DELETE
    USING (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid() AND rol = 'admin'
            )
        )
    );

-- PROGRAMACIÓN TALLAS: admin puede eliminar
DROP POLICY IF EXISTS "Admin elimina tallas prog" ON programacion_linea_tallas_movil;
CREATE POLICY "Admin elimina tallas prog"
    ON programacion_linea_tallas_movil FOR DELETE
    USING (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid() AND rol = 'admin'
            )
        )
    );

-- DETALLE PEDIDO: admin puede eliminar
DROP POLICY IF EXISTS "Admin elimina detalle pedidos" ON detalle_pedido_cliente_movil;
CREATE POLICY "Admin elimina detalle pedidos"
    ON detalle_pedido_cliente_movil FOR DELETE
    USING (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid() AND rol = 'admin'
            )
        )
    );

-- PUNTOS PEDIDO: admin puede eliminar
DROP POLICY IF EXISTS "Admin elimina puntos pedidos" ON detalle_pedido_puntos_movil;
CREATE POLICY "Admin elimina puntos pedidos"
    ON detalle_pedido_puntos_movil FOR DELETE
    USING (
        es_super_admin()
        OR (
            empresa_esta_activa(empresa_id)
            AND empresa_id IN (
                SELECT empresa_id FROM perfiles_usuario
                WHERE id = auth.uid() AND rol = 'admin'
            )
        )
    );

-- -----------------------------------------------------------
-- 6. PERFILES: super_admin bypass + verificar empresa activa
-- -----------------------------------------------------------
DROP POLICY IF EXISTS "Usuarios ven su propio perfil" ON perfiles_usuario;
CREATE POLICY "Usuarios ven su propio perfil"
    ON perfiles_usuario FOR SELECT
    USING (
        es_super_admin()
        OR auth.uid() = id
    );

DROP POLICY IF EXISTS "Usuarios actualizan su propio perfil" ON perfiles_usuario;
CREATE POLICY "Usuarios actualizan su propio perfil"
    ON perfiles_usuario FOR UPDATE
    USING (
        es_super_admin()
        OR auth.uid() = id
    );

-- -----------------------------------------------------------
-- 6. PERFILES: permitir empresa_id NULL para super_admin
-- -----------------------------------------------------------
-- El super_admin puede no tener empresa_id (acceso total)
ALTER TABLE perfiles_usuario ALTER COLUMN empresa_id DROP NOT NULL;

-- -----------------------------------------------------------
-- 7. FUNCIÓN: verificar login (empresa activa + usuario activo)
-- -----------------------------------------------------------
CREATE OR REPLACE FUNCTION verificar_login_movil(p_user_id UUID)
RETURNS TABLE (
    ok BOOLEAN,
    mensaje TEXT,
    empresa_id UUID,
    rol TEXT
) AS $$
DECLARE
    v_perfil RECORD;
    v_empresa RECORD;
BEGIN
    -- Buscar perfil
    SELECT * INTO v_perfil
    FROM perfiles_usuario
    WHERE id = p_user_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT false, 'Perfil no encontrado'::TEXT, NULL::UUID, NULL::TEXT;
        RETURN;
    END IF;

    IF NOT v_perfil.activo THEN
        RETURN QUERY SELECT false, 'Usuario desactivado'::TEXT, NULL::UUID, NULL::TEXT;
        RETURN;
    END IF;

    -- Super admin no necesita empresa activa
    IF v_perfil.rol = 'super_admin' THEN
        RETURN QUERY SELECT true, 'OK'::TEXT, v_perfil.empresa_id, v_perfil.rol;
        RETURN;
    END IF;

    -- Verificar empresa activa
    SELECT * INTO v_empresa
    FROM empresas
    WHERE id = v_perfil.empresa_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT false, 'Empresa no encontrada'::TEXT, NULL::UUID, NULL::TEXT;
        RETURN;
    END IF;

    IF NOT v_empresa.activo THEN
        RETURN QUERY SELECT false, 'Empresa desactivada. Contacte al administrador.'::TEXT, NULL::UUID, NULL::TEXT;
        RETURN;
    END IF;

    RETURN QUERY SELECT true, 'OK'::TEXT, v_perfil.empresa_id, v_perfil.rol;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
