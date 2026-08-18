import { supabase, supabaseConfigurado } from '../lib/supabase';
import type { SolicitudImpresion } from '../tipos';

/**
 * Servicio de impresión de etiquetas desde el móvil.
 *
 * Por ahora solo construye el payload y, si Supabase está configurado,
 * lo inserta en la tabla `impresiones_etiqueta`. La comunicación con la
 * impresora local (escritorio) se define cuando se integre el flujo real.
 */
export async function enviarSolicitud(
  solicitud: SolicitudImpresion,
): Promise<{ ok: boolean; mensaje: string }> {
  if (!supabaseConfigurado()) {
    return {
      ok: false,
      mensaje:
        'Supabase no está configurado. Define EXPO_PUBLIC_SUPABASE_URL y ' +
        'EXPO_PUBLIC_SUPABASE_ANON_KEY en .env para enviar a imprimir.',
    };
  }

  const { error } = await supabase!
    .from('impresiones_etiqueta')
    .insert({ payload: solicitud, estatus: 'pendiente' });

  if (error) {
    return { ok: false, mensaje: `Error al enviar: ${error.message}` };
  }
  return { ok: true, mensaje: 'Solicitud enviada a la impresora local.' };
}