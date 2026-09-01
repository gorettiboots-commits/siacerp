import { supabase } from '../lib/supabase';
import { obtenerEmpresaId } from './auth';
import { enviarSolicitud } from './impresion';
import type {
  ProgramacionSemanaMovil,
  ProgramacionLineaMovil,
  SolicitudImpresion,
  DatosEtiquetaPartida,
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
  if (!empresaId || !supabase) {
    return { ok: false, datos: [], error: supabase ? 'No hay sesión activa' : 'Supabase no configurado' };
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
  if (!empresaId || !supabase) {
    return { ok: false, datos: [], error: supabase ? 'No hay sesión activa' : 'Supabase no configurado' };
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
  if (!empresaId || !supabase) {
    return { ok: false, datos: [], error: supabase ? 'No hay sesión activa' : 'Supabase no configurado' };
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

/**
 * Genera etiquetas de impresion para una linea de programacion.
 * Cada talla = una etiqueta con el codigo de barras.
 */
export async function imprimirLinea(
  linea: ProgramacionLineaMovil,
): Promise<{ ok: boolean; mensaje: string }> {
  const tallas = linea.tallas || [];
  if (tallas.length === 0) {
    return { ok: false, mensaje: 'No hay tallas para imprimir' };
  }

  const partidas: DatosEtiquetaPartida[] = [];
  let numEtiqueta = 1;

  for (const t of tallas) {
    if (t.pares <= 0) continue;
    for (let i = 0; i < t.pares; i++) {
      partidas.push({
        numero_etiqueta: numEtiqueta++,
        codigo_barras: `${linea.folio_prog || ''}-${t.talla}-${i + 1}`,
        talla: t.talla,
        modelo: linea.modelo || '',
        color: linea.color || '',
        cliente: linea.cliente || '',
      });
    }
  }

  const solicitud: SolicitudImpresion = {
    id: `prog-${linea.folio_prog || linea.id}-${Date.now()}`,
    tipo: 'partida',
    partidas_fleje: [],
    partidas,
    solicitado_en: new Date().toISOString(),
    origen: 'movil',
  };

  return enviarSolicitud(solicitud);
}
