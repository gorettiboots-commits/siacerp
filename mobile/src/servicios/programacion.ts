import { supabase } from '../lib/supabase';
import { obtenerEmpresaId } from './auth';
import type {
  ProgramacionSemanaMovil,
  ProgramacionLineaMovil,
} from '../tipos';

/**
 * Lista semanas de programación de la empresa.
 */
export async function listarSemanas(): Promise<{
  ok: boolean;
  datos: ProgramacionSemanaMovil[];
  error?: string;
}> {
  const empresaId = obtenerEmpresaId();
  if (!empresaId) {
    return { ok: false, datos: [], error: 'No hay sesión activa' };
  }

  const { data, error } = await supabase
    .from('programacion_semana_movil')
    .select('*')
    .eq('empresa_id', empresaId)
    .eq('activo', true)
    .order('fecha_inicio');

  if (error) {
    return { ok: false, datos: [], error: error.message };
  }

  return { ok: true, datos: data || [] };
}

/**
 * Lista líneas de programación de una semana.
 */
export async function listarLineas(
  semanaId: number | null,
): Promise<{
  ok: boolean;
  datos: ProgramacionLineaMovil[];
  error?: string;
}> {
  const empresaId = obtenerEmpresaId();
  if (!empresaId) {
    return { ok: false, datos: [], error: 'No hay sesión activa' };
  }

  let query = supabase
    .from('programacion_lineas_movil')
    .select('*')
    .eq('empresa_id', empresaId)
    .order('orden');

  if (semanaId) {
    query = query.eq('semana_id', semanaId);
  }

  const { data, error } = await query;

  if (error) {
    return { ok: false, datos: [], error: error.message };
  }

  return { ok: true, datos: data || [] };
}

/**
 * Lista líneas de programación con tallas de una semana.
 */
export async function lineasConTallas(
  semanaId: number | null,
): Promise<{
  ok: boolean;
  datos: ProgramacionLineaMovil[];
  error?: string;
}> {
  const empresaId = obtenerEmpresaId();
  if (!empresaId) {
    return { ok: false, datos: [], error: 'No hay sesión activa' };
  }

  let query = supabase
    .from('programacion_lineas_movil')
    .select('*')
    .eq('empresa_id', empresaId)
    .order('orden');

  if (semanaId) {
    query = query.eq('semana_id', semanaId);
  }

  const { data: lineas, error: lineasError } = await query;

  if (lineasError) {
    return { ok: false, datos: [], error: lineasError.message };
  }

  if (!lineas || lineas.length === 0) {
    return { ok: true, datos: [] };
  }

  // Cargar tallas para cada línea
  const lineasConTallas: ProgramacionLineaMovil[] = [];
  for (const l of lineas) {
    const { data: tallas } = await supabase
      .from('programacion_linea_tallas_movil')
      .select('talla, pares')
      .eq('linea_id', l.id)
      .eq('empresa_id', empresaId)
      .order('orden');

    lineasConTallas.push({
      ...l,
      tallas: tallas || [],
    });
  }

  return { ok: true, datos: lineasConTallas };
}

/**
 * Obtiene totales de una semana.
 */
export async function totalesSemana(
  semanaId: number | null,
): Promise<{
  ok: boolean;
  datos: { lineas: number; pares: number; clientes: number };
  error?: string;
}> {
  const resultado = await lineasConTallas(semanaId);
  if (!resultado.ok) {
    return {
      ok: false,
      datos: { lineas: 0, pares: 0, clientes: 0 },
      error: resultado.error,
    };
  }

  const lineas = resultado.datos;
  const clientesUnicos = new Set(lineas.map((l) => l.cliente).filter(Boolean));
  const totalPares = lineas.reduce(
    (sum, l) => sum + (l.total_pares || 0),
    0,
  );

  return {
    ok: true,
    datos: {
      lineas: lineas.length,
      pares: totalPares,
      clientes: clientesUnicos.size,
    },
  };
}
