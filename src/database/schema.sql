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

CREATE TABLE IF NOT EXISTS movimientos_inventario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folio TEXT NOT NULL UNIQUE,
    tipo_movimiento TEXT NOT NULL CHECK(tipo_movimiento IN ('salida','cambio_ubicacion')),
    observaciones TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS detalle_movimiento_inventario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movimiento_id INTEGER NOT NULL REFERENCES movimientos_inventario(id),
    insumo_id INTEGER NOT NULL REFERENCES insumos(id),
    cantidad REAL NOT NULL,
    observaciones TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
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
    valor TEXT NOT NULL,    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
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

-- -----------------------------------------------------------
-- Histórico de etiquetas impresas desde la cola de impresión
-- Las solicitudes llegan de la app móvil (vía Supabase) a la
-- cola. Al imprimirse salen de la cola y quedan aquí para
-- reimpresión. Las reimpresiones cuentan en `reimpresiones`.
-- -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS impresiones_historico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supabase_id TEXT,
    tipo TEXT NOT NULL DEFAULT 'partidas',
    payload TEXT NOT NULL,
    solicitado_en TEXT,
    impreso_en TEXT NOT NULL DEFAULT (datetime('now')),
    usuario TEXT,
    reimpresiones INTEGER NOT NULL DEFAULT 0
);

-- -----------------------------------------------------------
-- Ficha técnica por modelo ("Hoja de especificación de diseño")
-- Campos de característica en texto libre, como en la plantilla
-- Ficha tecnica.xlsx (RD aprobada). Una fila por modelo.
-- -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS fichas_tecnicas (
    modelo_id INTEGER PRIMARY KEY REFERENCES modelos(id),
    proyecto TEXT NOT NULL DEFAULT '',
    etapa TEXT NOT NULL DEFAULT 'MUESTRA',
    id_diseno TEXT NOT NULL DEFAULT '',
    ref_cliente TEXT NOT NULL DEFAULT '',
    color_nombre TEXT NOT NULL DEFAULT '',
    cintilla TEXT DEFAULT '',
    carnuza_chinela TEXT DEFAULT '',
    forro TEXT DEFAULT '',
    piel_corte_1 TEXT DEFAULT '',
    piel_corte_2 TEXT DEFAULT '',
    piel_corte_3 TEXT DEFAULT '',
    piel_corte_4 TEXT DEFAULT '',
    entretela_tubo TEXT DEFAULT '',
    entretela_chinela TEXT DEFAULT '',
    entretela_talon TEXT DEFAULT '',
    rebajado_tubo TEXT DEFAULT '',
    rebajado_chinela TEXT DEFAULT '',
    rebajado_talon TEXT DEFAULT '',
    bordado_tubo TEXT DEFAULT '',
    bordado_chinela TEXT DEFAULT '',
    bordado_calzador TEXT DEFAULT '',
    bordado_oreja TEXT DEFAULT '',
    bordado_logo TEXT DEFAULT '',
    hilo_bordado_tubo TEXT DEFAULT '',
    hilo_bordado_chinela TEXT DEFAULT '',
    hilo_bordado_calzador TEXT DEFAULT '',
    hilo_bordado_oreja TEXT DEFAULT '',
    hilo_logo TEXT DEFAULT '',
    hilo_armado TEXT DEFAULT '',
    hilo_sobrecostura TEXT DEFAULT '',
    vivo TEXT DEFAULT '',
    ribete TEXT DEFAULT '',
    estoperol TEXT DEFAULT '',
    herraje TEXT DEFAULT '',
    acc_1 TEXT DEFAULT '',
    acc_2 TEXT DEFAULT '',
    acc_3 TEXT DEFAULT '',
    acc_4 TEXT DEFAULT '',
    puntera TEXT DEFAULT '',
    planta TEXT DEFAULT '',
    contrafuerte TEXT DEFAULT '',
    casco TEXT DEFAULT '',
    suela TEXT DEFAULT '',
    cambrellon TEXT DEFAULT '',
    cerco TEXT DEFAULT '',
    herradura TEXT DEFAULT '',
    landis TEXT DEFAULT '',
    espinazo TEXT DEFAULT '',
    firme TEXT DEFAULT '',
    tacon TEXT DEFAULT '',
    stein TEXT DEFAULT '',
    acabado TEXT DEFAULT '',
    cierre TEXT DEFAULT '',
    cantos TEXT DEFAULT '',
    plantilla TEXT DEFAULT '',
    transfer TEXT DEFAULT '',
    caja TEXT DEFAULT '',
    serigrafia TEXT DEFAULT '',
    bolsa TEXT DEFAULT '',
    soporte TEXT DEFAULT '',
    asadera TEXT DEFAULT '',
    papel_relleno TEXT DEFAULT '',
    colgante TEXT DEFAULT '',
    grabado_suela TEXT DEFAULT '',
    barranca TEXT DEFAULT '',
    comentarios TEXT DEFAULT '',
    realizo TEXT DEFAULT '',
    recibio TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Fotos de la ficha técnica: producto terminado, tubo, chinela,
-- talón y suela. Una imagen por modelo × tipo.
CREATE TABLE IF NOT EXISTS ficha_tecnica_fotos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modelo_id INTEGER NOT NULL REFERENCES modelos(id) ON DELETE CASCADE,
    tipo_foto TEXT NOT NULL CHECK(tipo_foto IN ('producto','tubo','chinela','talon','suela')),
    imagen BLOB,
    UNIQUE(modelo_id, tipo_foto),
    FOREIGN KEY (modelo_id) REFERENCES modelos(id)
);

CREATE INDEX IF NOT EXISTS idx_historico_campos_campo ON historico_campos (campo);

-- -----------------------------------------------------------
-- ÍNDICES DE RENDIMIENTO
-- -----------------------------------------------------------

-- Variantes: JOIN por modelo_id, ORDER BY codigo_variante
CREATE INDEX IF NOT EXISTS idx_variantes_modelo ON variantes (modelo_id);
CREATE INDEX IF NOT EXISTS idx_variantes_activo ON variantes (activo);

-- Lista de materiales: JOIN por modelo_id
CREATE INDEX IF NOT EXISTS idx_lista_materiales_modelo ON lista_materiales (modelo_id);
CREATE INDEX IF NOT EXISTS idx_lista_materiales_insumo ON lista_materiales (insumo_id);

-- Proveedor-insumos: JOIN por proveedor_id e insumo_id
CREATE INDEX IF NOT EXISTS idx_proveedor_insumos_proveedor ON proveedor_insumos (proveedor_id);
CREATE INDEX IF NOT EXISTS idx_proveedor_insumos_insumo ON proveedor_insumos (insumo_id);

-- Detalle OC: JOIN por orden_compra_id, insumo_id, proveedor_id
CREATE INDEX IF NOT EXISTS idx_detalle_oc_orden ON detalle_orden_compra (orden_compra_id);
CREATE INDEX IF NOT EXISTS idx_detalle_oc_insumo ON detalle_orden_compra (insumo_id);
CREATE INDEX IF NOT EXISTS idx_detalle_oc_proveedor ON detalle_orden_compra (proveedor_id);

-- Detalle OC puntos: JOIN por detalle_idCREATE INDEX IF NOT EXISTS idx_detalle_oc_puntos_detalle ON detalle_orden_compra_puntos (detalle_id);

-- Ordenes de compra: filtros por estatus, fecha_emision, proveedor_id
CREATE INDEX IF NOT EXISTS idx_oc_estatus ON ordenes_compra (estatus);
CREATE INDEX IF NOT EXISTS idx_oc_fecha_emision ON ordenes_compra (fecha_emision);
CREATE INDEX IF NOT EXISTS idx_oc_proveedor ON ordenes_compra (proveedor_id);
CREATE INDEX IF NOT EXISTS idx_oc_estatus_fecha ON ordenes_compra (estatus, fecha_emision);

-- Insumos: filtros por activo, categoria; ORDER BY nombre
CREATE INDEX IF NOT EXISTS idx_insumos_activo ON insumos (activo);
CREATE INDEX IF NOT EXISTS idx_insumos_categoria ON insumos (categoria);
CREATE INDEX IF NOT EXISTS idx_insumos_stock_bajo ON insumos (activo, stock_actual, stock_minimo);

-- Modelos: filtro por activo
CREATE INDEX IF NOT EXISTS idx_modelos_activo ON modelos (activo);

-- Movimientos de inventario: JOIN por insumo_id, ORDER BY created_at
CREATE INDEX IF NOT EXISTS idx_mov_inv_insumo ON movimiento_inventario (insumo_id);
CREATE INDEX IF NOT EXISTS idx_mov_inv_created ON movimiento_inventario (created_at);
CREATE INDEX IF NOT EXISTS idx_mov_inv_referencia ON movimiento_inventario (referencia_tipo, referencia_id);

-- Detalle movimiento inventario: JOIN por movimiento_id
CREATE INDEX IF NOT EXISTS idx_detalle_mov_inv_movimiento ON detalle_movimiento_inventario (movimiento_id);
CREATE INDEX IF NOT EXISTS idx_detalle_mov_inv_insumo ON detalle_movimiento_inventario (insumo_id);

-- Pedidos cliente: JOIN por cliente_id, filtro por estatus
CREATE INDEX IF NOT EXISTS idx_pedidos_cliente_id ON pedidos_cliente (cliente_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_estatus ON pedidos_cliente (estatus);

-- Detalle pedido cliente: JOIN por pedido_id
CREATE INDEX IF NOT EXISTS idx_detalle_pedido_cliente ON detalle_pedido_cliente (pedido_id);

-- Detalle pedido cliente puntos: JOIN por detalle_id
CREATE INDEX IF NOT EXISTS idx_detalle_pedido_puntos_detalle ON detalle_pedido_cliente_puntos (detalle_id);

-- Programación: JOINs y filtros frecuentes
CREATE INDEX IF NOT EXISTS idx_prog_lineas_semana ON programacion_lineas (semana_id);
CREATE INDEX IF NOT EXISTS idx_prog_lineas_pedido ON programacion_lineas (pedido_id);
CREATE INDEX IF NOT EXISTS idx_prog_lineas_detalle ON programacion_lineas (detalle_pedido_id);
CREATE INDEX IF NOT EXISTS idx_prog_lineas_estatus ON programacion_lineas (estatus);
CREATE INDEX IF NOT EXISTS idx_prog_lineas_folio_prog ON programacion_lineas (folio_prog);
CREATE INDEX IF NOT EXISTS idx_prog_lineas_folio_pedido ON programacion_lineas (folio_pedido);
CREATE INDEX IF NOT EXISTS idx_prog_lineas_semana_estatus ON programacion_lineas (semana_id, estatus);
CREATE INDEX IF NOT EXISTS idx_prog_linea_tallas_linea ON programacion_linea_tallas (linea_id);

-- Órdenes de producción: JOIN por variante_id, filtros
CREATE INDEX IF NOT EXISTS idx_op_variante ON ordenes_produccion (variante_id);
CREATE INDEX IF NOT EXISTS idx_op_estatus ON ordenes_produccion (estatus);
CREATE INDEX IF NOT EXISTS idx_op_fecha_entrega ON ordenes_produccion (fecha_entrega);

-- Matriz tallas OP: JOIN por orden_produccion_id
CREATE INDEX IF NOT EXISTS idx_matriz_tallas_op ON matriz_tallas_op (orden_produccion_id);

-- Seguimiento producción: JOIN por orden_produccion_id
CREATE INDEX IF NOT EXISTS idx_seguimiento_op ON seguimiento_produccion (orden_produccion_id);
CREATE INDEX IF NOT EXISTS idx_seguimiento_estacion ON seguimiento_produccion (estacion_id);

-- Incidencias producción: JOIN por seguimiento_id
CREATE INDEX IF NOT EXISTS idx_incidencias_seguimiento ON incidencias_produccion (seguimiento_id);

-- Inventario PT: composite (variante_id, talla_id) para lookups
CREATE INDEX IF NOT EXISTS idx_inventario_pt_variante ON inventario_pt (variante_id);
CREATE INDEX IF NOT EXISTS idx_inventario_pt_talla ON inventario_pt (talla_id);
CREATE INDEX IF NOT EXISTS idx_inventario_pt_variante_talla ON inventario_pt (variante_id, talla_id);

-- Usuario permisos: JOIN por usuario_id y permiso_id
CREATE INDEX IF NOT EXISTS idx_usuario_permisos_usuario ON usuario_permisos (usuario_id);
CREATE INDEX IF NOT EXISTS idx_usuario_permisos_permiso ON usuario_permisos (permiso_id);

-- Logs sistema: JOIN por usuario_id
CREATE INDEX IF NOT EXISTS idx_logs_usuario ON logs_sistema (usuario_id);

-- Impresiones histórico: búsqueda por supabase_id (app móvil)
CREATE INDEX IF NOT EXISTS idx_impresiones_supabase ON impresiones_historico (supabase_id);

-- Programación semana: ORDER BY fecha_inicio, orden
CREATE INDEX IF NOT EXISTS idx_prog_semana_fecha ON programacion_semana (fecha_inicio);

-- -----------------------------------------------------------
-- 11. CONFIGURACIÓN DE EMPRESA
-- -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS configuracion_empresa (
    clave TEXT PRIMARY KEY,
    valor TEXT NOT NULL DEFAULT '',
    tipo TEXT NOT NULL DEFAULT 'texto',
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

INSERT OR IGNORE INTO configuracion_empresa (clave, valor, tipo) VALUES
    ('nombre_empresa', '', 'texto'),
    ('razon_social', '', 'texto'),
    ('logo', '', 'imagen'),
    ('video_splash', '', 'archivo'),
    ('rfc', '', 'texto'),
    ('domicilio', '', 'texto'),
    ('telefono', '', 'texto'),
    ('email', '', 'texto'),
    ('activo', '1', 'booleano');

-- -----------------------------------------------------------
-- 12. COLA DE SINCRONIZACIÓN (OUTBOX)
-- Cada cambio local (INSERT/UPDATE/DELETE) se registra aquí.
-- El SyncService envía los registros pendientes a Supabase
-- y los marca como 'enviado'. Si falla, se marca como 'error'
-- para reintento.
-- -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tabla TEXT NOT NULL,
    registro_id INTEGER NOT NULL,
    operacion TEXT NOT NULL CHECK(operacion IN ('INSERT','UPDATE','DELETE')),
    datos TEXT,
    estatus TEXT NOT NULL DEFAULT 'pendiente' CHECK(estatus IN ('pendiente','enviado','error')),
    intentos INTEGER NOT NULL DEFAULT 0,
    ultimo_error TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    enviado_en TEXT
);

CREATE INDEX IF NOT EXISTS idx_sync_queue_estatus ON sync_queue (estatus);
CREATE INDEX IF NOT EXISTS idx_sync_queue_tabla ON sync_queue (tabla, registro_id);
CREATE INDEX IF NOT EXISTS idx_sync_queue_pendientes ON sync_queue (estatus, created_at);

-- -----------------------------------------------------------
-- Soft delete: columna is_deleted para replicación entre terminales
-- -----------------------------------------------------------
-- Se agrega vía migración (db_manager._migrar_sync()) porque
-- ALTER TABLE ADD COLUMN IF NOT EXISTS es idempotente.
-- Las tablas que llevan soft delete:
--   insumos, modelos, variantes, proveedores, clientes,
--   ordenes_compra, ordenes_produccion, usuarios,
--   pedidos_cliente, programacion_semana, programacion_lineas
