import { supabase } from '../lib/supabase';
import { obtenerEmpresaId } from './auth';
import type { InsumoMovil } from '../tipos';

/**
 * Busca insumos por código, nombre o categoría.
 * Filtra automáticamente por empresa del usuario.
 */
export async function buscarInsumos(
  termino: string,
): Promise<{ ok: boolean; datos: InsumoMovil[]; error?: string }> {
  const empresaId = obtenerEmpresaId();
  if (!empresaId) {
    return { ok: false, datos: [], error: 'No hay sesión activa' };
  }

  const { data, error } = await supabase
    .from('insumos_movil')
    .select('*')
    .eq('empresa_id', empresaId)
    .eq('activo', true)
    .or(
      `codigo.ilike.%${termino}%,nombre.ilike.%${termino}%,categoria.ilike.%${termino}%`,
    )
    .order('codigo');

  if (error) {
    return { ok: false, datos: [], error: error.message };
  }

  return { ok: true, datos: data || [] };
}

/**
 * Lista todos los insumos activos de la empresa.
 */
export async function listarInsumos(): Promise<{
  ok: boolean;
  datos: InsumoMovil[];
  error?: string;
}> {
  const empresaId = obtenerEmpresaId();
  if (!empresaId) {
    return { ok: false, datos: [], error: 'No hay sesión activa' };
  }

  const { data, error } = await supabase
    .from('insumos_movil')
    .select('*')
    .eq('empresa_id', empresaId)
    .eq('activo', true)
    .order('codigo');

  if (error) {
    return { ok: false, datos: [], error: error.message };
  }

  return { ok: true, datos: data || [] };
}

/**
 * Obtiene insumos con stock bajo o crítico.
 */
export async function obtenerStockBajo(): Promise<{
  ok: boolean;
  datos: InsumoMovil[];
  error?: string;
}> {
  const empresaId = obtenerEmpresaId();
  if (!empresaId) {
    return { ok: false, datos: [], error: 'No hay sesión activa' };
  }

  const { data, error } = await supabase
    .from('insumos_movil')
    .select('*')
    .eq('empresa_id', empresaId)
    .eq('activo', true)
    .lte('stock_actual', supabase.rpc ? 'stock_minimo' : 0)
    .order('stock_actual');

  // Fallback: filtrar en cliente si rpc no disponible
  const todos = data || [];
  const stockBajo = todos.filter(
    (i) => i.stock_actual <= i.stock_minimo,
  );

  if (error) {
    return { ok: false, datos: [], error: error.message };
  }

  return { ok: true, datos: stockBajo };
}

/**
 * Obtiene un insumo específico.
 */
export async function obtenerInsumo(
  id: number,
): Promise<{
  ok: boolean;
  datos: InsumoMovil | null;
  error?: string;
}> {
  const empresaId = obtenerEmpresaId();
  if (!empresaId) {
    return { ok: false, datos: null, error: 'No hay sesión activa' };
  }

  const { data, error } = await supabase
    .from('insumos_movil')
    .select('*')
    .eq('id', id)
    .eq('empresa_id', empresaId)
    .single();

  if (error) {
    return { ok: false, datos: null, error: error.message };
  }

  return { ok: true, datos: data };
}
