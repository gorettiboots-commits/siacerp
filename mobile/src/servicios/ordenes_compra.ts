import { supabase } from '../lib/supabase';
import { obtenerEmpresaId } from './auth';

/** Helper: retorna error si supabase no está configurado */
import type {
  OrdenCompraMovil,
  DetalleOCMovil,
} from '../tipos';

/**
 * Lista órdenes de compra de la empresa.
 */
export async function listarOCs(filtro?: string): Promise<{
  ok: boolean;
  datos: OrdenCompraMovil[];
  error?: string;
}> {
  const empresaId = obtenerEmpresaId();
  if (!empresaId || !supabase) {
    return { ok: false, datos: [], error: supabase ? 'No hay sesión activa' : 'Supabase no configurado' };
  }

  let query = supabase
    .from('ordenes_compra_movil')
    .select('*')
    .eq('empresa_id', empresaId)
    .order('id', { ascending: false });

  if (filtro && filtro !== 'todas') {
    query = query.eq('estatus', filtro);
  }

  const { data, error } = await query;

  if (error) {
    return { ok: false, datos: [], error: error.message };
  }

  return { ok: true, datos: data || [] };
}

/**
 * Busca OCs por folio o proveedor.
 */
export async function buscarOCs(termino: string): Promise<{
  ok: boolean;
  datos: OrdenCompraMovil[];
  error?: string;
}> {
  const empresaId = obtenerEmpresaId();
  if (!empresaId || !supabase) {
    return { ok: false, datos: [], error: supabase ? 'No hay sesión activa' : 'Supabase no configurado' };
  }

  const { data, error } = await supabase
    .from('ordenes_compra_movil')
    .select('*')
    .eq('empresa_id', empresaId)
    .or(
      `folio.ilike.%${termino}%,proveedor_nombre.ilike.%${termino}%`,
    )
    .order('id', { ascending: false });

  if (error) {
    return { ok: false, datos: [], error: error.message };
  }

  return { ok: true, datos: data || [] };
}

/**
 * Obtiene el detalle de una OC.
 */
export async function obtenerDetalleOC(
  ocId: number,
): Promise<{
  ok: boolean;
  datos: DetalleOCMovil[];
  error?: string;
}> {
  const empresaId = obtenerEmpresaId();
  if (!empresaId || !supabase) {
    return { ok: false, datos: [], error: supabase ? 'No hay sesión activa' : 'Supabase no configurado' };
  }

  const { data, error } = await supabase
    .from('detalle_orden_compra_movil')
    .select('*')
    .eq('orden_compra_id', ocId)
    .eq('empresa_id', empresaId);

  if (error) {
    return { ok: false, datos: [], error: error.message };
  }

  return { ok: true, datos: data || [] };
}
