import { supabase } from '../lib/supabase';
import { obtenerEmpresaId } from './auth';

/** Helper: retorna error si supabase no está configurado */
import type {
  OrdenProduccionMovil,
  SeguimientoMovil,
} from '../tipos';

/**
 * Lista órdenes de producción activas de la empresa.
 */
export async function listarOPs(filtro?: string): Promise<{
  ok: boolean;
  datos: OrdenProduccionMovil[];
  error?: string;
}> {
  const empresaId = obtenerEmpresaId();
  if (!empresaId || !supabase) {
    return { ok: false, datos: [], error: supabase ? 'No hay sesión activa' : 'Supabase no configurado' };
  }

  let query = supabase
    .from('ordenes_produccion_movil')
    .select('*')
    .eq('empresa_id', empresaId)
    .order('fecha_entrega');

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
 * Busca OPs por folio, modelo o variante.
 */
export async function buscarOPs(termino: string): Promise<{
  ok: boolean;
  datos: OrdenProduccionMovil[];
  error?: string;
}> {
  const empresaId = obtenerEmpresaId();
  if (!empresaId || !supabase) {
    return { ok: false, datos: [], error: supabase ? 'No hay sesión activa' : 'Supabase no configurado' };
  }

  const { data, error } = await supabase
    .from('ordenes_produccion_movil')
    .select('*')
    .eq('empresa_id', empresaId)
    .or(
      `folio.ilike.%${termino}%,modelo_nombre.ilike.%${termino}%,codigo_variante.ilike.%${termino}%`,
    )
    .order('fecha_entrega');

  if (error) {
    return { ok: false, datos: [], error: error.message };
  }

  return { ok: true, datos: data || [] };
}

/**
 * Obtiene seguimiento por estación de una OP.
 */
export async function obtenerSeguimiento(
  opId: number,
): Promise<{
  ok: boolean;
  datos: SeguimientoMovil[];
  error?: string;
}> {
  const empresaId = obtenerEmpresaId();
  if (!empresaId || !supabase) {
    return { ok: false, datos: [], error: supabase ? 'No hay sesión activa' : 'Supabase no configurado' };
  }

  const { data, error } = await supabase
    .from('seguimiento_produccion_movil')
    .select('*')
    .eq('orden_produccion_id', opId)
    .eq('empresa_id', empresaId)
    .order('id');

  if (error) {
    return { ok: false, datos: [], error: error.message };
  }

  return { ok: true, datos: data || [] };
}

/**
 * Actualiza avance de producción en una estación.
 */
export async function actualizarAvance(
  seguimientoId: number,
  paresProcesados: number,
  paresDefectuosos: number = 0,
  observaciones?: string,
): Promise<{ ok: boolean; error?: string }> {
  const empresaId = obtenerEmpresaId();
  if (!empresaId || !supabase) {
    return { ok: false, error: supabase ? 'No hay sesión activa' : 'Supabase no configurado' };
  }

  const { error } = await supabase
    .from('seguimiento_produccion_movil')
    .update({
      pares_procesados: paresProcesados,
      pares_defectuosos: paresDefectuosos,
      observaciones: observaciones || undefined,
      updated_at: new Date().toISOString(),
    })
    .eq('id', seguimientoId)
    .eq('empresa_id', empresaId);

  if (error) {
    return { ok: false, error: error.message };
  }

  return { ok: true };
}

/**
 * Cambia el estatus de una línea de producción.
 */
export async function cambiarEstatusLinea(
  seguimientoId: number,
  nuevoEstatus: string,
): Promise<{ ok: boolean; error?: string }> {
  const empresaId = obtenerEmpresaId();
  if (!empresaId || !supabase) {
    return { ok: false, error: supabase ? 'No hay sesión activa' : 'Supabase no configurado' };
  }

  const { error } = await supabase
    .from('seguimiento_produccion_movil')
    .update({
      estatus: nuevoEstatus,
      updated_at: new Date().toISOString(),
    })
    .eq('id', seguimientoId)
    .eq('empresa_id', empresaId);

  if (error) {
    return { ok: false, error: error.message };
  }

  return { ok: true };
}

/**
 * Avanza a la siguiente estación de la OP.
 */
export async function avanzarEstacion(
  opId: number,
  estacionActualId: number,
): Promise<{ ok: boolean; error?: string }> {
  const empresaId = obtenerEmpresaId();
  if (!empresaId || !supabase) {
    return { ok: false, error: supabase ? 'No hay sesión activa' : 'Supabase no configurado' };
  }

  // Obtener todas las estaciones de la OP
  const { data: estaciones } = await supabase
    .from('seguimiento_produccion_movil')
    .select('id, estacion_nombre')
    .eq('orden_produccion_id', opId)
    .eq('empresa_id', empresaId)
    .order('id');

  if (!estaciones || estaciones.length === 0) {
    return { ok: false, error: 'No se encontraron estaciones' };
  }

  const idx = estaciones.findIndex((e) => e.id === estacionActualId);
  if (idx === -1 || idx >= estaciones.length - 1) {
    return { ok: false, error: 'No hay siguiente estación' };
  }

  // Marcar actual como completada
  await supabase
    .from('seguimiento_produccion_movil')
    .update({ estatus: 'completado', updated_at: new Date().toISOString() })
    .eq('id', estacionActualId)
    .eq('empresa_id', empresaId);

  // Activar siguiente
  const siguiente = estaciones[idx + 1];
  const { error } = await supabase
    .from('seguimiento_produccion_movil')
    .update({ estatus: 'en_proceso', updated_at: new Date().toISOString() })
    .eq('id', siguiente.id)
    .eq('empresa_id', empresaId);

  if (error) {
    return { ok: false, error: error.message };
  }

  return { ok: true };
}

/**
 * Reporta una incidencia en una estación.
 */
export async function reportarIncidencia(
  seguimientoId: number,
  tipo: string,
  descripcion: string,
  paresAfectados: number,
): Promise<{ ok: boolean; error?: string }> {
  const empresaId = obtenerEmpresaId();
  if (!empresaId || !supabase) {
    return { ok: false, error: supabase ? 'No hay sesión activa' : 'Supabase no configurado' };
  }

  const { error } = await supabase.from('incidencias_produccion_movil').insert({
    empresa_id: empresaId,
    seguimiento_id: seguimientoId,
    tipo,
    descripcion,
    pares_afectados: paresAfectados,
  });

  if (error) {
    return { ok: false, error: error.message };
  }

  return { ok: true };
}
