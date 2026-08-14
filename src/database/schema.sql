-- ============================================================
-- Goretti ERP - Esquema de Base de Datos
-- Compatible con SQLite y PostgreSQL
-- ============================================================

-- -----------------------------------------------------------
-- 1. CATÁLOGOS BASE
-- -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS modelos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    imagen BLOB,
    activo INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS variantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modelo_id INTEGER NOT NULL REFERENCES modelos(id),
    color TEXT NOT NULL,
    piel TEXT NOT NULL,
    talla TEXT NOT NULL DEFAULT '',
    codigo_variante TEXT NOT NULL UNIQUE,
    activo INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (modelo_id) REFERENCES modelos(id)
);

CREATE TABLE IF NOT EXISTS tallas_catalogo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    talla TEXT NOT NULL UNIQUE,
    activo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS insumos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL,
    unidad_medida TEXT NOT NULL DEFAULT 'pieza',
    stock_actual REAL NOT NULL DEFAULT 0,
    stock_minimo REAL NOT NULL DEFAULT 0,
    imagen BLOB,
    activo INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS lista_materiales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modelo_id INTEGER NOT NULL REFERENCES modelos(id),
    insumo_id INTEGER NOT NULL REFERENCES insumos(id),
    cantidad_por_par REAL NOT NULL,
    unidad TEXT NOT NULL DEFAULT 'pieza',
    FOREIGN KEY (modelo_id) REFERENCES modelos(id),
    FOREIGN KEY (insumo_id) REFERENCES insumos(id)
);

-- -----------------------------------------------------------
-- 2. ÓRDENES DE COMPRA E INVENTARIO
-- -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS proveedores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rfc TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    nombre_comercial TEXT,
    telefono TEXT,
    email TEXT,
    direccion TEXT,
    activo INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Catálogo de unidades de medida
CREATE TABLE IF NOT EXISTS unidades_medida (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    abreviatura TEXT NOT NULL UNIQUE,
    activo INTEGER NOT NULL DEFAULT 1
);

-- Catálogo de colores para variantes de insumo
CREATE TABLE IF NOT EXISTS colores_catalogo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    codigo TEXT NOT NULL UNIQUE,
    orden INTEGER NOT NULL DEFAULT 0,
    activo INTEGER NOT NULL DEFAULT 1
);

-- Productos que provee cada proveedor
CREATE TABLE IF NOT EXISTS proveedor_insumos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proveedor_id INTEGER NOT NULL REFERENCES proveedores(id),
    insumo_id INTEGER NOT NULL REFERENCES insumos(id),
    color TEXT DEFAULT '',
    unidad_medida TEXT NOT NULL DEFAULT 'pieza',
    precio REAL NOT NULL DEFAULT 0,
    comentario TEXT DEFAULT '',
    activo INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id),
    FOREIGN KEY (insumo_id) REFERENCES insumos(id)
);

CREATE TABLE IF NOT EXISTS ordenes_compra (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folio TEXT NOT NULL UNIQUE,
    proveedor_id INTEGER REFERENCES proveedores(id),
    fecha_emision TEXT NOT NULL DEFAULT (datetime('now')),
    fecha_recibido TEXT,
    estatus TEXT NOT NULL DEFAULT 'pendiente',
    total REAL NOT NULL DEFAULT 0,
    observaciones TEXT,
    metodo_pago TEXT NOT NULL DEFAULT 'Transferencia bancaria',
    solo_remision INTEGER NOT NULL DEFAULT 0,
    tipo TEXT NOT NULL DEFAULT 'orden',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
);

CREATE TABLE IF NOT EXISTS detalle_orden_compra (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    orden_compra_id INTEGER NOT NULL REFERENCES ordenes_compra(id),
    insumo_id INTEGER NOT NULL REFERENCES insumos(id),
    cantidad REAL NOT NULL,
    precio_unitario REAL NOT NULL,
    proveedor_id INTEGER REFERENCES proveedores(id),
    FOREIGN KEY (orden_compra_id) REFERENCES ordenes_compra(id),
    FOREIGN KEY (insumo_id) REFERENCES insumos(id),
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
);

-- Pares por punto (talla) por renglón de la orden de compra
CREATE TABLE IF NOT EXISTS detalle_orden_compra_puntos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    detalle_id INTEGER NOT NULL REFERENCES detalle_orden_compra(id) ON DELETE CASCADE,
    talla_id INTEGER NOT NULL REFERENCES tallas_catalogo(id),
    pares INTEGER NOT NULL DEFAULT 0,
    precio_unitario REAL NOT NULL DEFAULT 0,
    UNIQUE(detalle_id, talla_id),
    FOREIGN KEY (detalle_id) REFERENCES detalle_orden_compra(id),
    FOREIGN KEY (talla_id) REFERENCES tallas_catalogo(id)
);

-- -----------------------------------------------------------
-- 2.1 CLIENTES Y PEDIDOS DE CLIENTE
-- -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rfc TEXT,
    nombre TEXT NOT NULL,
    nombre_comercial TEXT,
    telefono TEXT,
    email TEXT,
    direccion TEXT,
    activo INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS pedidos_cliente (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folio TEXT NOT NULL UNIQUE,
    folio_pedido TEXT NOT NULL DEFAULT '',
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    fecha_pedido TEXT NOT NULL DEFAULT (datetime('now')),
    fecha_programado TEXT,
    estatus TEXT NOT NULL DEFAULT 'pendiente',
    total_pares INTEGER NOT NULL DEFAULT 0,
    suela TEXT NOT NULL DEFAULT '',
    horma TEXT NOT NULL DEFAULT '',
    observaciones TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

CREATE TABLE IF NOT EXISTS detalle_pedido_cliente (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER NOT NULL REFERENCES pedidos_cliente(id) ON DELETE CASCADE,
    modelo TEXT NOT NULL,
    piel TEXT NOT NULL DEFAULT '',
    color TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (pedido_id) REFERENCES pedidos_cliente(id)
);

-- Pares por talla por renglón del pedido de cliente (catálogo unificado RD-1)
CREATE TABLE IF NOT EXISTS detalle_pedido_cliente_puntos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    detalle_id INTEGER NOT NULL REFERENCES detalle_pedido_cliente(id) ON DELETE CASCADE,
    talla_id INTEGER NOT NULL REFERENCES tallas_catalogo(id),
    pares INTEGER NOT NULL DEFAULT 0,
    UNIQUE(detalle_id, talla_id),
    FOREIGN KEY (detalle_id) REFERENCES detalle_pedido_cliente(id),
    FOREIGN KEY (talla_id) REFERENCES tallas_catalogo(id)
);

CREATE TABLE IF NOT EXISTS movimiento_inventario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    insumo_id INTEGER NOT NULL REFERENCES insumos(id),
    tipo_movimiento TEXT NOT NULL CHECK(tipo_movimiento IN ('entrada','salida','ajuste')),
    cantidad REAL NOT NULL,
    referencia_tipo TEXT,
    referencia_id INTEGER,
    observaciones TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (insumo_id) REFERENCES insumos(id)
);

-- -----------------------------------------------------------
-- 2.2 PROGRAMACIÓN SEMANAL
-- El folio_prog es el folio de programación asignado en el
-- Excel (diferente al folio de pedido PED-XXXX).
-- -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS programacion_semana (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    fecha_inicio TEXT NOT NULL DEFAULT '',
    orden INTEGER NOT NULL DEFAULT 0,
    activo INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS programacion_lineas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    semana_id INTEGER NOT NULL REFERENCES programacion_semana(id) ON DELETE CASCADE,
    orden INTEGER NOT NULL DEFAULT 0,
    folio_prog TEXT NOT NULL DEFAULT '',
    folio_pedido TEXT NOT NULL DEFAULT '',
    cliente TEXT NOT NULL,
    modelo TEXT NOT NULL DEFAULT '',
    piel TEXT NOT NULL DEFAULT '',
    color TEXT NOT NULL DEFAULT '',
    fecha_prog TEXT NOT NULL DEFAULT '',
    tubo TEXT NOT NULL DEFAULT '',
    chinela TEXT NOT NULL DEFAULT '',
    total_pares INTEGER NOT NULL DEFAULT 0,
    estatus TEXT NOT NULL DEFAULT 'programado',
    pedido_id INTEGER REFERENCES pedidos_cliente(id),
    detalle_pedido_id INTEGER REFERENCES detalle_pedido_cliente(id),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (semana_id) REFERENCES programacion_semana(id)
);

CREATE TABLE IF NOT EXISTS programacion_linea_tallas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    linea_id INTEGER NOT NULL REFERENCES programacion_lineas(id) ON DELETE CASCADE,
    talla TEXT NOT NULL,
    orden REAL NOT NULL DEFAULT 0,
    pares INTEGER NOT NULL DEFAULT 0,
    UNIQUE(linea_id, talla),
    FOREIGN KEY (linea_id) REFERENCES programacion_lineas(id)
);

-- -----------------------------------------------------------
-- 2.3 ETIQUETAS (impresión a etiquetadora)
-- Reemplaza el diseño de Label Matrix (etiquetaa.qdf.qdf).
-- Guarda el diseño de la etiqueta (tamaño y campos) en JSON.
-- -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS etiqueta_config (
    clave TEXT PRIMARY KEY,
    valor TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- -----------------------------------------------------------
-- 3. PLANIFICACIÓN DE PRODUCCIÓN
-- -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS ordenes_produccion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folio TEXT NOT NULL UNIQUE,
    variante_id INTEGER NOT NULL REFERENCES variantes(id),
    total_pares INTEGER NOT NULL,
    fecha_inicio TEXT,
    fecha_entrega TEXT,
    prioridad TEXT NOT NULL DEFAULT 'normal',
    estatus TEXT NOT NULL DEFAULT 'planeada',
    observaciones TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (variante_id) REFERENCES variantes(id)
);

CREATE TABLE IF NOT EXISTS matriz_tallas_op (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    orden_produccion_id INTEGER NOT NULL REFERENCES ordenes_produccion(id),
    talla_id INTEGER NOT NULL REFERENCES tallas_catalogo(id),
    pares INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (orden_produccion_id) REFERENCES ordenes_produccion(id),
    FOREIGN KEY (talla_id) REFERENCES tallas_catalogo(id)
);

CREATE TABLE IF NOT EXISTS estaciones_produccion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    orden INTEGER NOT NULL,
    descripcion TEXT,
    activo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS seguimiento_produccion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    orden_produccion_id INTEGER NOT NULL REFERENCES ordenes_produccion(id),
    estacion_id INTEGER NOT NULL REFERENCES estaciones_produccion(id),
    fecha_entrada TEXT,
    fecha_salida TEXT,
    estatus TEXT NOT NULL DEFAULT 'pendiente',
    pares_procesados INTEGER DEFAULT 0,
    pares_defectuosos INTEGER DEFAULT 0,
    observaciones TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (orden_produccion_id) REFERENCES ordenes_produccion(id),
    FOREIGN KEY (estacion_id) REFERENCES estaciones_produccion(id)
);

CREATE TABLE IF NOT EXISTS incidencias_produccion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seguimiento_id INTEGER NOT NULL REFERENCES seguimiento_produccion(id),
    tipo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    pares_afectados INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (seguimiento_id) REFERENCES seguimiento_produccion(id)
);

-- -----------------------------------------------------------
-- 4. PRODUCTO TERMINADO
-- -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS inventario_pt (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variante_id INTEGER NOT NULL REFERENCES variantes(id),
    talla_id INTEGER NOT NULL REFERENCES tallas_catalogo(id),
    pares INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (variante_id) REFERENCES variantes(id),
    FOREIGN KEY (talla_id) REFERENCES tallas_catalogo(id)
);

-- -----------------------------------------------------------
-- 5. USUARIOS DEL SISTEMA
-- -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    nombre_completo TEXT NOT NULL,
    rol TEXT NOT NULL DEFAULT 'operador',
    activo INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- -----------------------------------------------------------
-- 6. CONTROL DE ACCESO (ACL)
-- -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS permisos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modulo TEXT NOT NULL,
    accion TEXT NOT NULL,
    descripcion TEXT,
    UNIQUE(modulo, accion)
);

CREATE TABLE IF NOT EXISTS usuario_permisos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    permiso_id INTEGER NOT NULL REFERENCES permisos(id),
    permitido INTEGER NOT NULL DEFAULT 1,
    UNIQUE(usuario_id, permiso_id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (permiso_id) REFERENCES permisos(id)
);

-- -----------------------------------------------------------
-- 7. LOGS TÉCNICOS DEL SISTEMA
-- -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS logs_sistema (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL DEFAULT (datetime('now')),
    usuario_id INTEGER,
    usuario TEXT,
    modulo TEXT NOT NULL,
    accion TEXT NOT NULL,
    entidad TEXT,
    entidad_id INTEGER,
    nivel TEXT NOT NULL DEFAULT 'info',
    detalle TEXT,
    datos TEXT,
    metadata TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE INDEX IF NOT EXISTS idx_logs_fecha ON logs_sistema (fecha);
CREATE INDEX IF NOT EXISTS idx_logs_modulo ON logs_sistema (modulo);
CREATE INDEX IF NOT EXISTS idx_logs_entidad ON logs_sistema (entidad, entidad_id);

-- -----------------------------------------------------------
-- DATOS INICIALES
-- -----------------------------------------------------------

INSERT OR IGNORE INTO tallas_catalogo (talla) VALUES
    ('00'), ('01'), ('02'), ('03'), ('04'), ('05'), ('06'), ('07'),
    ('08'), ('09'), ('10'), ('11'), ('12'), ('13'),
    ('22'), ('22.5'), ('23'), ('23.5'), ('24'), ('24.5'), ('25'),
    ('25.5'), ('26'), ('26.5'), ('27'), ('27.5'), ('28'), ('28.5'),
    ('29'), ('29.5'), ('30'), ('30.5'), ('31');

INSERT OR IGNORE INTO estaciones_produccion (nombre, orden, descripcion) VALUES
    ('Corte', 1, 'Corte de piel y forro'),
    ('Pespunte', 2, 'Costura y ensamble del corte'),
    ('Montado', 3, 'Horma, plantilla y suela'),
    ('Ensuelado', 4, 'Pegado de suela, tacón y lijado'),
    ('Acabado', 5, 'Pintura, brillo y cepillado'),
    ('Empaque', 6, 'Control de calidad y empaquetado');

INSERT OR IGNORE INTO usuarios (username, password_hash, nombre_completo, rol) VALUES
    ('admin', '$2b$12$kEIruH3TEa8FcJoALGeXBu7tk3mj9xRxbBMEUvqYteqKmTUMO3Zia', 'Administrador del Sistema', 'admin');

INSERT OR IGNORE INTO permisos (modulo, accion, descripcion) VALUES
    ('ordenes_compra', 'ver', 'Ver el módulo de Órdenes de Compra'),
    ('ordenes_compra', 'crear', 'Crear órdenes de compra'),
    ('ordenes_compra', 'editar', 'Editar proveedores'),
    ('ordenes_compra', 'eliminar', 'Cancelar órdenes y desactivar proveedores'),
    ('ordenes_compra', 'exportar', 'Exportar e imprimir órdenes'),
    ('produccion', 'ver', 'Ver el módulo de Producción'),
    ('produccion', 'crear', 'Crear órdenes, modelos y variantes'),
    ('produccion', 'editar', 'Editar modelos, variantes y lista de materiales'),
    ('produccion', 'eliminar', 'Desactivar modelos y variantes'),
    ('produccion', 'exportar', 'Exportar e imprimir'),
    ('inventario', 'ver', 'Ver el módulo de Inventario'),
    ('inventario', 'crear', 'Crear insumos y movimientos'),
    ('inventario', 'editar', 'Editar insumos'),
    ('inventario', 'eliminar', 'Desactivar insumos'),
    ('inventario', 'exportar', 'Exportar e imprimir'),
    ('configuracion', 'ver', 'Ver la configuración del sistema'),
    ('configuracion', 'crear', 'Crear unidades y áreas'),
    ('configuracion', 'editar', 'Editar unidades y áreas'),
    ('configuracion', 'eliminar', 'Desactivar unidades y áreas'),
    ('configuracion', 'exportar', 'Exportar e imprimir'),
    ('usuarios', 'ver', 'Ver la administración de usuarios'),
    ('usuarios', 'crear', 'Crear usuarios'),
    ('usuarios', 'editar', 'Editar usuarios y permisos'),
    ('usuarios', 'eliminar', 'Desactivar usuarios'),
    ('usuarios', 'exportar', 'Exportar e imprimir'),
    ('clientes', 'ver', 'Ver el módulo de Clientes y Pedidos'),
    ('clientes', 'crear', 'Crear clientes y pedidos de cliente'),
    ('clientes', 'editar', 'Editar clientes y pedidos'),
    ('clientes', 'eliminar', 'Desactivar clientes y cancelar pedidos'),
    ('clientes', 'exportar', 'Exportar e imprimir pedidos'),
    ('programacion', 'ver', 'Ver el módulo de Programación Semanal'),
    ('programacion', 'crear', 'Crear líneas de programación'),
    ('programacion', 'editar', 'Cambiar el estatus de líneas programadas'),
    ('programacion', 'eliminar', 'Eliminar líneas de la programación'),
    ('programacion', 'exportar', 'Exportar e imprimir la programación');

INSERT OR IGNORE INTO unidades_medida (nombre, abreviatura) VALUES
    ('Pieza', 'pieza'),
    ('Decímetro Cuadrado', 'dm2'),
    ('Metro', 'metro'),
    ('Kilogramo', 'kilogramo'),
    ('Litro', 'litro'),
    ('Par', 'par'),
    ('Rollo', 'rollo'),
    ('Caja', 'caja');

INSERT OR IGNORE INTO tallas_catalogo (talla) VALUES
    ('15'), ('15.5'), ('16'), ('16.5'), ('17'),
    ('18'), ('19'), ('20'), ('21');

INSERT OR IGNORE INTO colores_catalogo (nombre, codigo, orden) VALUES
    ('Negro', 'NEG', 1),
    ('Café', 'CAF', 2),
    ('Blanco', 'BL', 3),
    ('Rojo', 'RJO', 4),
    ('Azul', 'AZL', 5);

-- -----------------------------------------------------------
-- Histórico de capturas en campos de texto
-- Almacena los valores antes capturados en cada campo para que,
-- al volver a capturar, el textbox sirva de selector/autocompletado.
-- -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS historico_campos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campo TEXT NOT NULL,
    valor TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (campo, valor)
);

-- -----------------------------------------------------------
-- Configuración general del sistema (clave/valor)
-- Preferencias de la aplicación gestionadas desde la sección
-- de Configuración, por ejemplo la impresora virtual SIAC.
-- -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS configuracion_sistema (
    clave TEXT PRIMARY KEY,
    valor TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_historico_campos_campo ON historico_campos (campo);
