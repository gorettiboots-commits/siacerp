-- ============================================================
-- SIAC ERP — Esquema Supabase MULTI-TENANT
-- ============================================================
-- Cada empresa tiene sus datos aislados.
-- Un usuario solo puede ver/escribir datos de SU empresa.
-- ============================================================

-- -----------------------------------------------------------
-- 0. TABLA DE EMPRESAS (nueva)
-- -----------------------------------------------------------
-- Registra cada empresa/tenant que usa el sistema.

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

-- Solo admin puede ver empresas (o usuarios autenticados para la suya)
CREATE POLICY "Usuarios ven su empresa"
    ON empresas FOR SELECT
    USING (
        id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

-- -----------------------------------------------------------
-- 1. PERFILES DE USUARIO (+ empresa_id)
-- -----------------------------------------------------------
-- Cada usuario pertenece a una empresa.

CREATE TABLE IF NOT EXISTS perfiles_usuario (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    empresa_id UUID NOT NULL REFERENCES empresas(id),
    username TEXT NOT NULL,
    nombre_completo TEXT NOT NULL,
    rol TEXT NOT NULL DEFAULT 'operador',
    activo BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(empresa_id, username)
);

ALTER TABLE perfiles_usuario ENABLE ROW LEVEL SECURITY;

-- RLS: Usuarios solo ven su propio perfil
CREATE POLICY "Usuarios ven su propio perfil"
    ON perfiles_usuario FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Usuarios actualizan su propio perfil"
    ON perfiles_usuario FOR UPDATE
    USING (auth.uid() = id);

-- -----------------------------------------------------------
-- 2. INSUMOS (+ empresa_id)
-- -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS insumos_movil (
    id BIGINT NOT NULL,
    empresa_id UUID NOT NULL REFERENCES empresas(id),
    codigo TEXT NOT NULL,
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL,
    unidad_medida TEXT NOT NULL DEFAULT 'pieza',
    stock_actual NUMERIC NOT NULL DEFAULT 0,
    stock_minimo NUMERIC NOT NULL DEFAULT 0,
    activo BOOLEAN NOT NULL DEFAULT true,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id, empresa_id)
);

ALTER TABLE insumos_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios leen insumos de su empresa"
    ON insumos_movil FOR SELECT
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

-- -----------------------------------------------------------
-- 3. ÓRDENES DE COMPRA (+ empresa_id)
-- -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS ordenes_compra_movil (
    id BIGINT NOT NULL,
    empresa_id UUID NOT NULL REFERENCES empresas(id),
    folio TEXT NOT NULL,
    proveedor_nombre TEXT,
    fecha_emision TIMESTAMPTZ,
    estatus TEXT NOT NULL DEFAULT 'pendiente',
    total NUMERIC NOT NULL DEFAULT 0,
    metodo_pago TEXT NOT NULL DEFAULT 'Transferencia bancaria',
    solo_remision BOOLEAN NOT NULL DEFAULT false,
    tipo TEXT NOT NULL DEFAULT 'orden',
    observaciones TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id, empresa_id)
);

ALTER TABLE ordenes_compra_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios leen OC de su empresa"
    ON ordenes_compra_movil FOR SELECT
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

-- Detalle de OC (+ empresa_id)
CREATE TABLE IF NOT EXISTS detalle_orden_compra_movil (
    id BIGINT NOT NULL,
    empresa_id UUID NOT NULL REFERENCES empresas(id),
    orden_compra_id BIGINT NOT NULL,
    insumo_id BIGINT NOT NULL,
    insumo_nombre TEXT,
    cantidad NUMERIC NOT NULL,
    precio_unitario NUMERIC NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id, empresa_id),
    FOREIGN KEY (orden_compra_id, empresa_id)
        REFERENCES ordenes_compra_movil(id, empresa_id)
);

ALTER TABLE detalle_orden_compra_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios leen detalle OC de su empresa"
    ON detalle_orden_compra_movil FOR SELECT
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

-- Puntos/tallas por detalle (+ empresa_id)
CREATE TABLE IF NOT EXISTS detalle_oc_puntos_movil (
    id BIGINT NOT NULL,
    empresa_id UUID NOT NULL REFERENCES empresas(id),
    detalle_id BIGINT NOT NULL,
    talla_id BIGINT NOT NULL,
    talla TEXT NOT NULL,
    pares INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id, empresa_id),
    FOREIGN KEY (detalle_id, empresa_id)
        REFERENCES detalle_orden_compra_movil(id, empresa_id)
);

ALTER TABLE detalle_oc_puntos_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios leen puntos OC de su empresa"
    ON detalle_oc_puntos_movil FOR SELECT
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

-- -----------------------------------------------------------
-- 4. PRODUCCIÓN (+ empresa_id)
-- -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS ordenes_produccion_movil (
    id BIGINT NOT NULL,
    empresa_id UUID NOT NULL REFERENCES empresas(id),
    folio TEXT NOT NULL,
    modelo_nombre TEXT,
    codigo_variante TEXT,
    total_pares INTEGER NOT NULL DEFAULT 0,
    fecha_inicio TEXT,
    fecha_entrega TEXT,
    prioridad TEXT NOT NULL DEFAULT 'normal',
    estatus TEXT NOT NULL DEFAULT 'planeada',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id, empresa_id)
);

ALTER TABLE ordenes_produccion_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios leen OP de su empresa"
    ON ordenes_produccion_movil FOR SELECT
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

-- Seguimiento por estación (+ empresa_id)
CREATE TABLE IF NOT EXISTS seguimiento_produccion_movil (
    id BIGINT NOT NULL,
    empresa_id UUID NOT NULL REFERENCES empresas(id),
    orden_produccion_id BIGINT NOT NULL,
    estacion_nombre TEXT NOT NULL,
    estatus TEXT NOT NULL DEFAULT 'pendiente',
    pares_procesados INTEGER NOT NULL DEFAULT 0,
    pares_defectuosos INTEGER NOT NULL DEFAULT 0,
    observaciones TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id, empresa_id),
    FOREIGN KEY (orden_produccion_id, empresa_id)
        REFERENCES ordenes_produccion_movil(id, empresa_id)
);

ALTER TABLE seguimiento_produccion_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios leen seguimiento de su empresa"
    ON seguimiento_produccion_movil FOR SELECT
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

CREATE POLICY "Usuarios actualizan seguimiento de su empresa"
    ON seguimiento_produccion_movil FOR UPDATE
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

-- Incidencias (+ empresa_id)
CREATE TABLE IF NOT EXISTS incidencias_produccion_movil (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    empresa_id UUID NOT NULL REFERENCES empresas(id),
    seguimiento_id BIGINT NOT NULL,
    tipo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    pares_afectados INTEGER NOT NULL DEFAULT 0,
    reportado_por UUID REFERENCES perfiles_usuario(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (seguimiento_id, empresa_id)
        REFERENCES seguimiento_produccion_movil(id, empresa_id)
);

ALTER TABLE incidencias_produccion_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios leen incidencias de su empresa"
    ON incidencias_produccion_movil FOR SELECT
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

CREATE POLICY "Usuarios crean incidencias de su empresa"
    ON incidencias_produccion_movil FOR INSERT
    WITH CHECK (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

-- -----------------------------------------------------------
-- 5. TALLAS (+ empresa_id)
-- -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS tallas_catalogo_movil (
    id BIGINT NOT NULL,
    empresa_id UUID NOT NULL REFERENCES empresas(id),
    talla TEXT NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT true,
    PRIMARY KEY (id, empresa_id)
);

ALTER TABLE tallas_catalogo_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios leen tallas de su empresa"
    ON tallas_catalogo_movil FOR SELECT
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

-- -----------------------------------------------------------
-- 6. LOGS (+ empresa_id)
-- -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS logs_movil (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    empresa_id UUID NOT NULL REFERENCES empresas(id),
    usuario_id UUID REFERENCES perfiles_usuario(id),
    accion TEXT NOT NULL,
    entidad TEXT NOT NULL,
    entidad_id BIGINT,
    detalle JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE logs_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios crean logs de su empresa"
    ON logs_movil FOR INSERT
    WITH CHECK (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

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

-- -----------------------------------------------------------
-- 7. FUNCIONES ÚTILES (actualizadas con empresa_id)
-- -----------------------------------------------------------

CREATE OR REPLACE FUNCTION obtener_empresa_usuario()
RETURNS UUID AS $$
DECLARE
    v_empresa UUID;
BEGIN
    SELECT empresa_id INTO v_empresa
    FROM perfiles_usuario
    WHERE id = auth.uid();
    RETURN v_empresa;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION buscar_insumos(p_termino TEXT)
RETURNS TABLE (
    id BIGINT,
    codigo TEXT,
    nombre TEXT,
    categoria TEXT,
    stock_actual NUMERIC,
    unidad_medida TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT i.id, i.codigo, i.nombre, i.categoria, i.stock_actual, i.unidad_medida
    FROM insumos_movil i
    WHERE i.empresa_id = obtener_empresa_usuario()
      AND i.activo = true
      AND (
        i.codigo ILIKE '%' || p_termino || '%'
        OR i.nombre ILIKE '%' || p_termino || '%'
        OR i.categoria ILIKE '%' || p_termino || '%'
      )
    ORDER BY i.codigo;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION cambiar_estatus_linea(
    p_seguimiento_id BIGINT,
    p_empresa_id UUID,
    p_nuevo_estatus TEXT,
    p_pares_procesados INTEGER DEFAULT NULL,
    p_pares_defectuosos INTEGER DEFAULT NULL
) RETURNS void AS $$
BEGIN
    UPDATE seguimiento_produccion_movil
    SET estatus = p_nuevo_estatus,
        pares_procesados = COALESCE(p_pares_procesados, pares_procesados),
        pares_defectuosos = COALESCE(p_pares_defectuosos, pares_defectuosos),
        updated_at = now()
    WHERE id = p_seguimiento_id
      AND empresa_id = p_empresa_id;
END;
$$ LANGUAGE plpgsql;

-- -----------------------------------------------------------
-- 8. CLIENTES, PEDIDOS Y PROGRAMACIÓN (+ empresa_id)
-- -----------------------------------------------------------
-- Módulo de clientes, pedidos y programación semanal.
-- El admin puede crear/editar pedidos y programar desde el móvil.

-- Clientes
CREATE TABLE IF NOT EXISTS clientes_movil (
    id BIGINT NOT NULL,
    empresa_id UUID NOT NULL REFERENCES empresas(id),
    nombre TEXT NOT NULL,
    rfc TEXT,
    nombre_comercial TEXT,
    telefono TEXT,
    email TEXT,
    direccion TEXT,
    activo BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id, empresa_id)
);

ALTER TABLE clientes_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios leen clientes de su empresa"
    ON clientes_movil FOR SELECT
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

CREATE POLICY "Admin inserta clientes de su empresa"
    ON clientes_movil FOR INSERT
    WITH CHECK (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid() AND rol = 'admin'
        )
    );

CREATE POLICY "Admin actualiza clientes de su empresa"
    ON clientes_movil FOR UPDATE
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid() AND rol = 'admin'
        )
    );

-- Pedidos de cliente
CREATE TABLE IF NOT EXISTS pedidos_cliente_movil (
    id BIGINT NOT NULL,
    empresa_id UUID NOT NULL REFERENCES empresas(id),
    folio TEXT NOT NULL,
    folio_pedido TEXT,
    cliente_id BIGINT NOT NULL,
    cliente_nombre TEXT NOT NULL,
    fecha_pedido TEXT,
    fecha_programado TEXT,
    total_pares INTEGER NOT NULL DEFAULT 0,
    estatus TEXT NOT NULL DEFAULT 'pendiente',
    suela TEXT,
    horma TEXT,
    observaciones TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id, empresa_id)
);

ALTER TABLE pedidos_cliente_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios leen pedidos de su empresa"
    ON pedidos_cliente_movil FOR SELECT
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

CREATE POLICY "Admin inserta pedidos de su empresa"
    ON pedidos_cliente_movil FOR INSERT
    WITH CHECK (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid() AND rol = 'admin'
        )
    );

CREATE POLICY "Admin actualiza pedidos de su empresa"
    ON pedidos_cliente_movil FOR UPDATE
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid() AND rol = 'admin'
        )
    );

-- Detalle de pedido
CREATE TABLE IF NOT EXISTS detalle_pedido_cliente_movil (
    id BIGINT NOT NULL,
    empresa_id UUID NOT NULL REFERENCES empresas(id),
    pedido_id BIGINT NOT NULL,
    modelo TEXT NOT NULL,
    piel TEXT,
    color TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id, empresa_id),
    FOREIGN KEY (pedido_id, empresa_id)
        REFERENCES pedidos_cliente_movil(id, empresa_id)
);

ALTER TABLE detalle_pedido_cliente_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios leen detalle pedidos de su empresa"
    ON detalle_pedido_cliente_movil FOR SELECT
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

-- Puntos/tallas por detalle de pedido
CREATE TABLE IF NOT EXISTS detalle_pedido_puntos_movil (
    id BIGINT NOT NULL,
    empresa_id UUID NOT NULL REFERENCES empresas(id),
    detalle_id BIGINT NOT NULL,
    talla_id BIGINT NOT NULL,
    talla TEXT NOT NULL,
    pares INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id, empresa_id),
    FOREIGN KEY (detalle_id, empresa_id)
        REFERENCES detalle_pedido_cliente_movil(id, empresa_id)
);

ALTER TABLE detalle_pedido_puntos_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios leen puntos pedidos de su empresa"
    ON detalle_pedido_puntos_movil FOR SELECT
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

-- Programación semanal
CREATE TABLE IF NOT EXISTS programacion_semana_movil (
    id BIGINT NOT NULL,
    empresa_id UUID NOT NULL REFERENCES empresas(id),
    nombre TEXT NOT NULL,
    fecha_inicio TEXT NOT NULL,
    orden INTEGER NOT NULL DEFAULT 0,
    activo BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id, empresa_id)
);

ALTER TABLE programacion_semana_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios leen semanas de su empresa"
    ON programacion_semana_movil FOR SELECT
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

-- Líneas de programación
CREATE TABLE IF NOT EXISTS programacion_lineas_movil (
    id BIGINT NOT NULL,
    empresa_id UUID NOT NULL REFERENCES empresas(id),
    semana_id BIGINT NOT NULL,
    orden INTEGER NOT NULL DEFAULT 0,
    folio_prog TEXT,
    folio_pedido TEXT,
    cliente TEXT,
    modelo TEXT,
    piel TEXT,
    color TEXT,
    fecha_prog TEXT,
    total_pares INTEGER NOT NULL DEFAULT 0,
    estatus TEXT NOT NULL DEFAULT 'programacion_incompleta',
    pedido_id BIGINT,
    detalle_pedido_id BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id, empresa_id),
    FOREIGN KEY (semana_id, empresa_id)
        REFERENCES programacion_semana_movil(id, empresa_id)
);

ALTER TABLE programacion_lineas_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios leen líneas de su empresa"
    ON programacion_lineas_movil FOR SELECT
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

-- Tallas por línea de programación
CREATE TABLE IF NOT EXISTS programacion_linea_tallas_movil (
    id BIGINT NOT NULL,
    empresa_id UUID NOT NULL REFERENCES empresas(id),
    linea_id BIGINT NOT NULL,
    talla TEXT NOT NULL,
    orden NUMERIC NOT NULL DEFAULT 0,
    pares INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id, empresa_id),
    FOREIGN KEY (linea_id, empresa_id)
        REFERENCES programacion_lineas_movil(id, empresa_id)
);

ALTER TABLE programacion_linea_tallas_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios leen tallas línea de su empresa"
    ON programacion_linea_tallas_movil FOR SELECT
    USING (
        empresa_id IN (
            SELECT empresa_id FROM perfiles_usuario
            WHERE id = auth.uid()
        )
    );

-- -----------------------------------------------------------
-- 9. TRIGGERS
-- -----------------------------------------------------------

CREATE OR REPLACE FUNCTION trigger_actualizar_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_insumos_actualizar
    BEFORE UPDATE ON insumos_movil
    FOR EACH ROW EXECUTE FUNCTION trigger_actualizar_timestamp();

CREATE TRIGGER tr_oc_actualizar
    BEFORE UPDATE ON ordenes_compra_movil
    FOR EACH ROW EXECUTE FUNCTION trigger_actualizar_timestamp();

CREATE TRIGGER tr_op_actualizar
    BEFORE UPDATE ON ordenes_produccion_movil
    FOR EACH ROW EXECUTE FUNCTION trigger_actualizar_timestamp();

CREATE TRIGGER tr_seguimiento_actualizar
    BEFORE UPDATE ON seguimiento_produccion_movil
    FOR EACH ROW EXECUTE FUNCTION trigger_actualizar_timestamp();

CREATE TRIGGER tr_empresas_actualizar
    BEFORE UPDATE ON empresas
    FOR EACH ROW EXECUTE FUNCTION trigger_actualizar_timestamp();
