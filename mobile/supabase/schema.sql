-- ============================================================
-- SIAC ERP — Esquema Supabase para sincronización móvil
-- ============================================================
-- Este esquema se aplica en Supabase para permitir que la app
-- móvil lea/escriba datos del ERP.
--
-- ESTRATEGIA: Supabase como puente bidireccional:
--   - El escritorio sincroniza datos a Supabase periódicamente
--   - El móvil lee/escribe en Supabase
--   - El escritorio detecta cambios y los aplica a SQLite/PostgreSQL local
-- ============================================================

-- -----------------------------------------------------------
-- 1. AUTENTICACIÓN (Supabase Auth)
-- -----------------------------------------------------------
-- Los usuarios se autentican con Supabase Auth.
-- Se crea un perfil vinculado al usuario del ERP.

CREATE TABLE IF NOT EXISTS perfiles_usuario (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username TEXT UNIQUE NOT NULL,
    nombre_completo TEXT NOT NULL,
    rol TEXT NOT NULL DEFAULT 'operador',
    activo BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- RLS: Los usuarios solo ven su propio perfil
ALTER TABLE perfiles_usuario ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios ven su propio perfil"
    ON perfiles_usuario FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Usuarios actualizan su propio perfil"
    ON perfiles_usuario FOR UPDATE
    USING (auth.uid() = id);

-- -----------------------------------------------------------
-- 2. INVARIOS (solo lectura desde el móvil)
-- -----------------------------------------------------------
-- El móvil consulta stock actual y busca insumos.
-- Solo el escritorio escribe aquí.

CREATE TABLE IF NOT EXISTS insumos_movil (
    id BIGINT PRIMARY KEY,
    codigo TEXT NOT NULL,
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL,
    unidad_medida TEXT NOT NULL DEFAULT 'pieza',
    stock_actual NUMERIC NOT NULL DEFAULT 0,
    stock_minimo NUMERIC NOT NULL DEFAULT 0,
    activo BOOLEAN NOT NULL DEFAULT true,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE insumos_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios autenticados leen insumos"
    ON insumos_movil FOR SELECT
    USING (auth.role() = 'authenticated');

-- -----------------------------------------------------------
-- 3. ÓRDENES DE COMPRA (lectura + recepción parcial)
-- -----------------------------------------------------------
-- El móvil puede ver OCs pendientes y registrar recepciones.

CREATE TABLE IF NOT EXISTS ordenes_compra_movil (
    id BIGINT PRIMARY KEY,
    folio TEXT NOT NULL,
    proveedor_nombre TEXT,
    fecha_emision TIMESTAMPTZ,
    estatus TEXT NOT NULL DEFAULT 'pendiente',
    total NUMERIC NOT NULL DEFAULT 0,
    metodo_pago TEXT NOT NULL DEFAULT 'Transferencia bancaria',
    solo_remision BOOLEAN NOT NULL DEFAULT false,
    tipo TEXT NOT NULL DEFAULT 'orden',
    observaciones TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE ordenes_compra_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios autenticados leen OC"
    ON ordenes_compra_movil FOR SELECT
    USING (auth.role() = 'authenticated');

-- Detalle de OC (lectura)
CREATE TABLE IF NOT EXISTS detalle_orden_compra_movil (
    id BIGINT PRIMARY KEY,
    orden_compra_id BIGINT NOT NULL REFERENCES ordenes_compra_movil(id),
    insumo_id BIGINT NOT NULL,
    insumo_nombre TEXT,
    cantidad NUMERIC NOT NULL,
    precio_unitario NUMERIC NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE detalle_orden_compra_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios autenticados leen detalle OC"
    ON detalle_orden_compra_movil FOR SELECT
    USING (auth.role() = 'authenticated');

-- Puntos/tallas por detalle (lectura)
CREATE TABLE IF NOT EXISTS detalle_oc_puntos_movil (
    id BIGINT PRIMARY KEY,
    detalle_id BIGINT NOT NULL REFERENCES detalle_orden_compra_movil(id),
    talla_id BIGINT NOT NULL,
    talla TEXT NOT NULL,
    pares INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE detalle_oc_puntos_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios autenticados leen puntos OC"
    ON detalle_oc_puntos_movil FOR SELECT
    USING (auth.role() = 'authenticated');

-- -----------------------------------------------------------
-- 4. PRODUCCIÓN (lectura + escritura de avance)
-- -----------------------------------------------------------
-- El móvil puede ver OPs y registrar avance por estación.

CREATE TABLE IF NOT EXISTS ordenes_produccion_movil (
    id BIGINT PRIMARY KEY,
    folio TEXT NOT NULL,
    modelo_nombre TEXT,
    codigo_variante TEXT,
    total_pares INTEGER NOT NULL DEFAULT 0,
    fecha_inicio TEXT,
    fecha_entrega TEXT,
    prioridad TEXT NOT NULL DEFAULT 'normal',
    estatus TEXT NOT NULL DEFAULT 'planeada',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE ordenes_produccion_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios autenticados leen OP"
    ON ordenes_produccion_movil FOR SELECT
    USING (auth.role() = 'authenticated');

-- Seguimiento por estación (lectura + escritura)
CREATE TABLE IF NOT EXISTS seguimiento_produccion_movil (
    id BIGINT PRIMARY KEY,
    orden_produccion_id BIGINT NOT NULL REFERENCES ordenes_produccion_movil(id),
    estacion_nombre TEXT NOT NULL,
    estatus TEXT NOT NULL DEFAULT 'pendiente',
    pares_procesados INTEGER NOT NULL DEFAULT 0,
    pares_defectuosos INTEGER NOT NULL DEFAULT 0,
    observaciones TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE seguimiento_produccion_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios autenticados leen seguimiento"
    ON seguimiento_produccion_movil FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Usuarios autenticados actualizan seguimiento"
    ON seguimiento_produccion_movil FOR UPDATE
    USING (auth.role() = 'authenticated');

-- Incidencias (escritura desde el móvil)
CREATE TABLE IF NOT EXISTS incidencias_produccion_movil (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    seguimiento_id BIGINT NOT NULL REFERENCES seguimiento_produccion_movil(id),
    tipo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    pares_afectados INTEGER NOT NULL DEFAULT 0,
    reportado_por UUID REFERENCES perfiles_usuario(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE incidencias_produccion_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios autenticados leen incidencias"
    ON incidencias_produccion_movil FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Usuarios autenticados crean incidencias"
    ON incidencias_produccion_movil FOR INSERT
    WITH CHECK (auth.role() = 'authenticated');

-- -----------------------------------------------------------
-- 5. TALLAS (catálogo para consultas del móvil)
-- -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS tallas_catalogo_movil (
    id BIGINT PRIMARY KEY,
    talla TEXT NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT true
);

ALTER TABLE tallas_catalogo_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios autenticados leen tallas"
    ON tallas_catalogo_movil FOR SELECT
    USING (auth.role() = 'authenticated');

-- -----------------------------------------------------------
-- 6. LOGS DE ACTIVIDAD MÓVIL
-- -----------------------------------------------------------
-- Registra acciones del móvil para trazabilidad.

CREATE TABLE IF NOT EXISTS logs_movil (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    usuario_id UUID REFERENCES perfiles_usuario(id),
    accion TEXT NOT NULL,
    entidad TEXT NOT NULL,
    entidad_id BIGINT,
    detalle JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE logs_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios autenticados crean logs"
    ON logs_movil FOR INSERT
    WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Admin ve todos los logs"
    ON logs_movil FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM perfiles_usuario
            WHERE id = auth.uid() AND rol = 'admin'
        )
    );

-- -----------------------------------------------------------
-- 7. VISTA DE SINCRONIZACIÓN
-- -----------------------------------------------------------
-- Vista que muestra el estado de sincronización de cada tabla.

CREATE OR REPLACE VIEW estado_sincronizacion AS
SELECT
    'insumos' AS tabla,
    COUNT(*) AS registros,
    MAX(updated_at) AS ultima_sincronizacion
FROM insumos_movil
UNION ALL
SELECT
    'ordenes_compra',
    COUNT(*),
    MAX(updated_at)
FROM ordenes_compra_movil
UNION ALL
SELECT
    'ordenes_produccion',
    COUNT(*),
    MAX(updated_at)
FROM ordenes_produccion_movil
UNION ALL
SELECT
    'seguimiento_produccion',
    COUNT(*),
    MAX(updated_at)
FROM seguimiento_produccion_movil;

-- -----------------------------------------------------------
-- 8. FUNCIONES ÚTILES
-- -----------------------------------------------------------

-- Función para registrar actividad del móvil
CREATE OR REPLACE FUNCTION registrar_actividad_movil(
    p_usuario UUID,
    p_accion TEXT,
    p_entidad TEXT,
    p_entidad_id BIGINT DEFAULT NULL,
    p_detalle JSONB DEFAULT NULL
) RETURNS void AS $$
BEGIN
    INSERT INTO logs_movil (usuario_id, accion, entidad, entidad_id, detalle)
    VALUES (p_usuario, p_accion, p_entidad, p_entidad_id, p_detalle);
END;
$$ LANGUAGE plpgsql;

-- Función para obtener stock de un insumo
CREATE OR REPLACE FUNCTION obtener_stock_insumo(p_insumo_id BIGINT)
RETURNS TABLE (
    codigo TEXT,
    nombre TEXT,
    stock_actual NUMERIC,
    stock_minimo NUMERIC,
    unidad_medida TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT i.codigo, i.nombre, i.stock_actual, i.stock_minimo, i.unidad_medida
    FROM insumos_movil i
    WHERE i.id = p_insumo_id AND i.activo = true;
END;
$$ LANGUAGE plpgsql;

-- Función para buscar insumos
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
    WHERE i.activo = true
      AND (
        i.codigo ILIKE '%' || p_termino || '%'
        OR i.nombre ILIKE '%' || p_termino || '%'
        OR i.categoria ILIKE '%' || p_termino || '%'
      )
    ORDER BY i.codigo;
END;
$$ LANGUAGE plpgsql;

-- Función para actualizar avance de producción
CREATE OR REPLACE FUNCTION actualizar_avance_produccion(
    p_seguimiento_id BIGINT,
    p_pares_procesados INTEGER,
    p_pares_defectuosos INTEGER DEFAULT 0,
    p_observaciones TEXT DEFAULT NULL
) RETURNS void AS $$
BEGIN
    UPDATE seguimiento_produccion_movil
    SET pares_procesados = p_pares_procesados,
        pares_defectuosos = p_pares_defectuosos,
        observaciones = COALESCE(p_observaciones, observaciones),
        updated_at = now()
    WHERE id = p_seguimiento_id;
END;
$$ LANGUAGE plpgsql;

-- Función para cambiar estatus de línea de producción
CREATE OR REPLACE FUNCTION cambiar_estatus_linea(
    p_seguimiento_id BIGINT,
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
    WHERE id = p_seguimiento_id;
END;
$$ LANGUAGE plpgsql;

-- -----------------------------------------------------------
-- 9. TRIGGERS DE SINCRONIZACIÓN
-- -----------------------------------------------------------
-- Estos triggers marcan updated_at cuando se modifican registros.

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
