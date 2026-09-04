// ─── Impresion de etiquetas (existente) ────────────────────

export interface PartidaFleje {
  id: string;
  texto: string;
  cantidad: number;
}

export interface DatosEtiquetaPartida {
  numero_etiqueta: number;
  codigo_barras: string;
  talla: string;
  modelo: string;
  color: string;
  cliente: string;
}

export interface SolicitudImpresion {
  id: string;
  tipo: 'fleje' | 'partida';
  partidas_fleje: PartidaFleje[];
  partidas: DatosEtiquetaPartida[];
  solicitado_en: string;
  origen: 'movil';
}

// ─── Multi-tenant ──────────────────────────────────────────

export interface Empresa {
  id: string;
  nombre: string;
  rfc?: string;
  activo: boolean;
}

// ─── Autenticacion ─────────────────────────────────────────

export interface UsuarioMovil {
  id: string;
  username: string;
  nombre_completo: string;
  rol: string;
}

// ─── Resultados genericos ──────────────────────────────────

export interface ResultadoBusqueda<T> {
  ok: boolean;
  datos: T[];
  mensaje?: string;
}

// ─── Inventario ────────────────────────────────────────────

export interface InsumoMovil {
  id: number;
  empresa_id: string;
  codigo: string;
  nombre: string;
  categoria: string;
  stock_actual: number;
  stock_minimo: number;
  unidad_medida: string;
}

// ─── Ordenes de Compra ────────────────────────────────────

export interface OrdenCompraMovil {
  id: number;
  empresa_id: string;
  folio: string;
  proveedor_nombre: string;
  fecha_emision: string;
  estatus: string;
  total: number;
  metodo_pago: string;
  solo_remision: boolean;
  tipo: string;
}

export interface DetalleOCMovil {
  id: number;
  empresa_id: string;
  orden_compra_id: number;
  insumo_id: number;
  insumo_nombre: string;
  cantidad: number;
  precio_unitario: number;
}

// ─── Clientes ─────────────────────────────────────────────

export interface ClienteMovil {
  id: number;
  empresa_id: string;
  nombre: string;
  rfc?: string;
  nombre_comercial?: string;
  telefono?: string;
  email?: string;
  direccion?: string;
  activo: boolean;
}

// ─── Pedidos de Cliente ────────────────────────────────────

export interface PedidoClienteMovil {
  id: number;
  empresa_id: string;
  folio: string;
  folio_pedido?: string;
  cliente_id: number;
  cliente_nombre: string;
  fecha_pedido?: string;
  fecha_programado?: string;
  total_pares: number;
  estatus: string;
  suela?: string;
  horma?: string;
  observaciones?: string;
}

export interface DetallePedidoMovil {
  id: number;
  empresa_id: string;
  pedido_id: number;
  modelo: string;
  piel?: string;
  color?: string;
  puntos?: PuntoPedidoMovil[];
}

export interface PuntoPedidoMovil {
  talla_id: number;
  talla: string;
  pares: number;
}

// ─── Programación ──────────────────────────────────────────

export interface ProgramacionSemanaMovil {
  id: number;
  empresa_id: string;
  nombre: string;
  fecha_inicio: string;
  orden: number;
  activo: boolean;
}

export interface ProgramacionLineaMovil {
  id: number;
  empresa_id: string;
  semana_id: number;
  semana?: string;
  folio_prog?: string;
  folio_pedido?: string;
  cliente?: string;
  modelo?: string;
  piel?: string;
  color?: string;
  fecha_prog?: string;
  total_pares: number;
  estatus: string;
  tallas?: ProgramacionTallaMovil[];
}

export interface ProgramacionTallaMovil {
  talla: string;
  pares: number;
}

// ─── Produccion ────────────────────────────────────────────

export interface OrdenProduccionMovil {
  id: number;
  empresa_id: string;
  folio: string;
  modelo_nombre: string;
  codigo_variante: string;
  total_pares: number;
  fecha_entrega: string;
  prioridad: string;
  estatus: string;
}

export interface SeguimientoMovil {
  id: number;
  empresa_id: string;
  orden_produccion_id: number;
  estacion_nombre: string;
  estatus: string;
  pares_procesados: number;
  pares_defectuosos: number;
  observaciones?: string;
}
