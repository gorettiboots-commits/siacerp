import { supabase } from '../lib/supabase';
import { obtenerEmpresaId } from './auth';
import type {
  PedidoClienteMovil,
  DetallePedidoMovil,
} from '../tipos';

/**
 * Lista pedidos de clientes de la empresa.
 */
export async function listarPedidos(filtro?: string): Promise<{
  ok: boolean;
  datos: PedidoClienteMovil[];
  error?: string;
}> {
  const empresaId = obtenerEmpresaId();
  if (!empresaId) {
    return { ok: false, datos: [], error: 'No hay sesión activa' };
  }

  let query = supabase
    .from('pedidos_cliente_movil')
    .select('*')
    .eq('empresa_id', empresaId)
    .order('id', { ascending: false });

  if (filtro && filtro !== 'todos') {
    query = query.eq('estatus', filtro);
  }

  const { data, error } = await query;

  if (error) {
    return { ok: false, datos: [], error: error.message };
  }

  return { ok: true, datos: data || [] };
}

/**
 * Busca pedidos por folio, cliente o modelo.
 */
export async function buscarPedidos(termino: string): Promise<{
  ok: boolean;
  datos: PedidoClienteMovil[];
  error?: string;
}> {
  const empresaId = obtenerEmpresaId();
  if (!empresaId) {
    return { ok: false, datos: [], error: 'No hay sesión activa' };
  }

  const { data, error } = await supabase
    .from('pedidos_cliente_movil')
    .select('*')
    .eq('empresa_id', empresaId)
    .or(
      `folio.ilike.%${termino}%,cliente_nombre.ilike.%${termino}%,folio_pedido.ilike.%${termino}%`,
    )
    .order('id', { ascending: false });

  if (error) {
    return { ok: false, datos: [], error: error.message };
  }

  return { ok: true, datos: data || [] };
}

/**
 * Obtiene un pedido específico.
 */
export async function obtenerPedido(
  id: number,
): Promise<{
  ok: boolean;
  datos: PedidoClienteMovil | null;
  error?: string;
}> {
  const empresaId = obtenerEmpresaId();
  if (!empresaId) {
    return { ok: false, datos: null, error: 'No hay sesión activa' };
  }

  const { data, error } = await supabase
    .from('pedidos_cliente_movil')
    .select('*')
    .eq('id', id)
    .eq('empresa_id', empresaId)
    .single();

  if (error) {
    return { ok: false, datos: null, error: error.message };
  }

  return { ok: true, datos: data };
}

/**
 * Obtiene el detalle de un pedido con puntos/tallas.
 */
export async function obtenerDetallePedido(
  pedidoId: number,
): Promise<{
  ok: boolean;
  datos: DetallePedidoMovil[];
  error?: string;
}> {
  const empresaId = obtenerEmpresaId();
  if (!empresaId) {
    return { ok: false, datos: [], error: 'No hay sesión activa' };
  }

  const { data: detalle, error: detError } = await supabase
    .from('detalle_pedido_cliente_movil')
    .select('*')
    .eq('pedido_id', pedidoId)
    .eq('empresa_id', empresaId)
    .order('id');

  if (detError) {
    return { ok: false, datos: [], error: detError.message };
  }

  if (!detalle || detalle.length === 0) {
    return { ok: true, datos: [] };
  }

  // Cargar puntos/tallas para cada detalle
  const detalleConPuntos: DetallePedidoMovil[] = [];
  for (const d of detalle) {
    const { data: puntos } = await supabase
      .from('detalle_pedido_puntos_movil')
      .select('talla_id, talla, pares')
      .eq('detalle_id', d.id)
      .eq('empresa_id', empresaId)
      .order('talla');

    detalleConPuntos.push({
      ...d,
      puntos: puntos || [],
    });
  }

  return { ok: true, datos: detalleConPuntos };
}

/**
 * Cambia el estatus de un pedido.
 */
export async function cambiarEstatusPedido(
  pedidoId: number,
  nuevoEstatus: string,
): Promise<{ ok: boolean; error?: string }> {
  const empresaId = obtenerEmpresaId();
  if (!empresaId) {
    return { ok: false, error: 'No hay sesión activa' };
  }

  const { error } = await supabase
    .from('pedidos_cliente_movil')
    .update({
      estatus: nuevoEstatus,
      updated_at: new Date().toISOString(),
    })
    .eq('id', pedidoId)
    .eq('empresa_id', empresaId);

  if (error) {
    return { ok: false, error: error.message };
  }

  return { ok: true };
}
