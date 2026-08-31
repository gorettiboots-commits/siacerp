import { supabase } from '../lib/supabase';
import { obtenerEmpresaId } from './auth';
import type { ClienteMovil } from '../tipos';

/**
 * Lista clientes activos de la empresa.
 */
export async function listarClientes(): Promise<{
  ok: boolean;
  datos: ClienteMovil[];
  error?: string;
}> {
  const empresaId = obtenerEmpresaId();
  if (!empresaId) {
    return { ok: false, datos: [], error: 'No hay sesión activa' };
  }

  const { data, error } = await supabase
    .from('clientes_movil')
    .select('*')
    .eq('empresa_id', empresaId)
    .eq('activo', true)
    .order('nombre');

  if (error) {
    return { ok: false, datos: [], error: error.message };
  }

  return { ok: true, datos: data || [] };
}

/**
 * Busca clientes por nombre, RFC o nombre comercial.
 */
export async function buscarClientes(termino: string): Promise<{
  ok: boolean;
  datos: ClienteMovil[];
  error?: string;
}> {
  const empresaId = obtenerEmpresaId();
  if (!empresaId) {
    return { ok: false, datos: [], error: 'No hay sesión activa' };
  }

  const { data, error } = await supabase
    .from('clientes_movil')
    .select('*')
    .eq('empresa_id', empresaId)
    .eq('activo', true)
    .or(
      `nombre.ilike.%${termino}%,rfc.ilike.%${termino}%,nombre_comercial.ilike.%${termino}%`,
    )
    .order('nombre');

  if (error) {
    return { ok: false, datos: [], error: error.message };
  }

  return { ok: true, datos: data || [] };
}

/**
 * Obtiene un cliente específico.
 */
export async function obtenerCliente(
  id: number,
): Promise<{
  ok: boolean;
  datos: ClienteMovil | null;
  error?: string;
}> {
  const empresaId = obtenerEmpresaId();
  if (!empresaId) {
    return { ok: false, datos: null, error: 'No hay sesión activa' };
  }

  const { data, error } = await supabase
    .from('clientes_movil')
    .select('*')
    .eq('id', id)
    .eq('empresa_id', empresaId)
    .single();

  if (error) {
    return { ok: false, datos: null, error: error.message };
  }

  return { ok: true, datos: data };
}
