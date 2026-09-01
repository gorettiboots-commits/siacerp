import { supabase, supabaseConfigurado } from '../lib/supabase';
import { obtenerEmpresaId, obtenerUsuarioActual } from './auth';
import type { SolicitudImpresion } from '../tipos';

/**
 * Servicio de impresion de etiquetas desde el movil.
 *
 * Inserta solicitudes en `impresiones_etiqueta` de Supabase.
 * El escritorio (cola de impresion) las lee y procesa.
 */
export async function enviarSolicitud(
  solicitud: SolicitudImpresion,
): Promise<{ ok: boolean; mensaje: string }> {
  const empresaId = obtenerEmpresaId();
  const usuario = obtenerUsuarioActual();

  if (!empresaId || !supabase) {
    return {
      ok: false,
      mensaje: !supabase
        ? 'Supabase no esta configurado.'
        : 'No hay sesion activa.',
    };
  }

  const { error } = await supabase
    .from('impresiones_etiqueta')
    .insert({
      empresa_id: empresaId,
      usuario_id: usuario?.id ?? null,
      payload: solicitud,
      estatus: 'pendiente',
    });

  if (error) {
    return { ok: false, mensaje: `Error al enviar: ${error.message}` };
  }
  return { ok: true, mensaje: 'Solicitud enviada a la impresora local.' };
}
