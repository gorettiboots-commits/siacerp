-- ============================================================
-- SIAC ERP — Crear tablas de Clientes, Pedidos y Programación
-- ============================================================
-- Ejecutar ANTES de migrar_rls_super_admin.sql
-- Fecha: 2026-08-30
-- ============================================================

-- -----------------------------------------------------------
-- CLIENTES
-- -----------------------------------------------------------
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

-- -----------------------------------------------------------
-- PEDIDOS DE CLIENTE
-- -----------------------------------------------------------
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

-- -----------------------------------------------------------
-- DETALLE DE PEDIDO
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS detalle_pedido_cliente_movil (
    id BIGINT NOT NULL,
    empresa_id UUID NOT NULL REFERENCES empresas(id),
    pedido_id BIGINT NOT NULL,
    modelo TEXT NOT NULL,
    piel TEXT,
    color TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id, empresa_id)
);

ALTER TABLE detalle_pedido_cliente_movil ENABLE ROW LEVEL SECURITY;

-- -----------------------------------------------------------
-- PUNTOS/TALLAS POR DETALLE DE PEDIDO
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS detalle_pedido_puntos_movil (
    id BIGINT NOT NULL,
    empresa_id UUID NOT NULL REFERENCES empresas(id),
    detalle_id BIGINT NOT NULL,
    talla_id BIGINT NOT NULL,
    talla TEXT NOT NULL,
    pares INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id, empresa_id)
);

ALTER TABLE detalle_pedido_puntos_movil ENABLE ROW LEVEL SECURITY;

-- -----------------------------------------------------------
-- PROGRAMACIÓN SEMANAL
-- -----------------------------------------------------------
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

-- -----------------------------------------------------------
-- LÍNEAS DE PROGRAMACIÓN
-- -----------------------------------------------------------
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
    PRIMARY KEY (id, empresa_id)
);

ALTER TABLE programacion_lineas_movil ENABLE ROW LEVEL SECURITY;

-- -----------------------------------------------------------
-- TALLAS POR LÍNEA DE PROGRAMACIÓN
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS programacion_linea_tallas_movil (
    id BIGINT NOT NULL,
    empresa_id UUID NOT NULL REFERENCES empresas(id),
    linea_id BIGINT NOT NULL,
    talla TEXT NOT NULL,
    orden NUMERIC NOT NULL DEFAULT 0,
    pares INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id, empresa_id)
);

ALTER TABLE programacion_linea_tallas_movil ENABLE ROW LEVEL SECURITY;

-- -----------------------------------------------------------
-- TRIGGERS DE TIMESTAMP
-- -----------------------------------------------------------
CREATE OR REPLACE FUNCTION trigger_actualizar_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar triggers a las nuevas tablas
DROP TRIGGER IF EXISTS tr_clientes_actualizar ON clientes_movil;
CREATE TRIGGER tr_clientes_actualizar
    BEFORE UPDATE ON clientes_movil
    FOR EACH ROW EXECUTE FUNCTION trigger_actualizar_timestamp();

DROP TRIGGER IF EXISTS tr_pedidos_actualizar ON pedidos_cliente_movil;
CREATE TRIGGER tr_pedidos_actualizar
    BEFORE UPDATE ON pedidos_cliente_movil
    FOR EACH ROW EXECUTE FUNCTION trigger_actualizar_timestamp();

DROP TRIGGER IF EXISTS tr_detalle_pedido_actualizar ON detalle_pedido_cliente_movil;
CREATE TRIGGER tr_detalle_pedido_actualizar
    BEFORE UPDATE ON detalle_pedido_cliente_movil
    FOR EACH ROW EXECUTE FUNCTION trigger_actualizar_timestamp();

DROP TRIGGER IF EXISTS tr_puntos_pedido_actualizar ON detalle_pedido_puntos_movil;
CREATE TRIGGER tr_puntos_pedido_actualizar
    BEFORE UPDATE ON detalle_pedido_puntos_movil
    FOR EACH ROW EXECUTE FUNCTION trigger_actualizar_timestamp();

DROP TRIGGER IF EXISTS tr_prog_semana_actualizar ON programacion_semana_movil;
CREATE TRIGGER tr_prog_semana_actualizar
    BEFORE UPDATE ON programacion_semana_movil
    FOR EACH ROW EXECUTE FUNCTION trigger_actualizar_timestamp();

DROP TRIGGER IF EXISTS tr_prog_lineas_actualizar ON programacion_lineas_movil;
CREATE TRIGGER tr_prog_lineas_actualizar
    BEFORE UPDATE ON programacion_lineas_movil
    FOR EACH ROW EXECUTE FUNCTION trigger_actualizar_timestamp();

DROP TRIGGER IF EXISTS tr_prog_tallas_actualizar ON programacion_linea_tallas_movil;
CREATE TRIGGER tr_prog_tallas_actualizar
    BEFORE UPDATE ON programacion_linea_tallas_movil
    FOR EACH ROW EXECUTE FUNCTION trigger_actualizar_timestamp();
