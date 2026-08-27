import { supabase } from '../lib/supabase';
import type { UsuarioMovil } from '../tipos';

// ─── Estado de sesión ──────────────────────────────────────

let usuarioActual: UsuarioMovil | null = null;
let empresaActual: string | null = null;

/**
 * Inicia sesión con email/contraseña y carga el perfil
 * vinculado a la empresa.
 */
export async function iniciarSesion(
  email: string,
  password: string,
): Promise<{ ok: boolean; usuario?: UsuarioMovil; error?: string }> {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) {
    return { ok: false, error: error.message };
  }

  if (!data.user) {
    return { ok: false, error: 'No se obtuvo información del usuario' };
  }

  // Cargar perfil con empresa_id
  const { data: perfil, error: perfilError } = await supabase
    .from('perfiles_usuario')
    .select('*')
    .eq('id', data.user.id)
    .single();

  if (perfilError || !perfil) {
    return {
      ok: false,
      error: 'Perfil no encontrado. Contacte al administrador.',
    };
  }

  if (!perfil.activo) {
    return {
      ok: false,
      error: 'Usuario desactivado. Contacte al administrador.',
    };
  }

  usuarioActual = {
    id: perfil.id,
    username: perfil.username,
    nombre_completo: perfil.nombre_completo,
    rol: perfil.rol,
  };

  empresaActual = perfil.empresa_id;

  // Registrar actividad
  await supabase.from('logs_movil').insert({
    empresa_id: empresaActual,
    usuario_id: usuarioActual.id,
    accion: 'login',
    entidad: 'sesion',
    detalle: { email },
  });

  return { ok: true, usuario: usuarioActual };
}

/** Cierra sesión */
export async function cerrarSesion(): Promise<void> {
  if (usuarioActual && empresaActual) {
    await supabase.from('logs_movil').insert({
      empresa_id: empresaActual,
      usuario_id: usuarioActual.id,
      accion: 'logout',
      entidad: 'sesion',
    }).catch(() => {});
  }

  await supabase.auth.signOut();
  usuarioActual = null;
  empresaActual = null;
}

/** Obtiene el usuario actual en memoria */
export function obtenerUsuarioActual(): UsuarioMovil | null {
  return usuarioActual;
}

/** Obtiene el empresa_id actual */
export function obtenerEmpresaId(): string | null {
  return empresaActual;
}

/** Verifica si hay sesión activa */
export async function verificarSesion(): Promise<UsuarioMovil | null> {
  const { data: { session } } = await supabase.auth.getSession();

  if (!session) return null;

  // Recargar perfil
  const { data: perfil } = await supabase
    .from('perfiles_usuario')
    .select('*')
    .eq('id', session.user.id)
    .single();

  if (!perfil || !perfil.activo) return null;

  usuarioActual = {
    id: perfil.id,
    username: perfil.username,
    nombre_completo: perfil.nombre_completo,
    rol: perfil.rol,
  };

  empresaActual = perfil.empresa_id;

  return usuarioActual;
}
