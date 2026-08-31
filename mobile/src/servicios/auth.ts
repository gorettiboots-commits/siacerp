import { supabase } from '../lib/supabase';
import type { UsuarioMovil } from '../tipos';

// ─── Estado de sesión ──────────────────────────────────────

let usuarioActual: UsuarioMovil | null = null;
let empresaActual: string | null = null;
let empresaContexto: string | null = null;
let nombreEmpresaContexto: string | null = null;
let onCambioEmpresa: (() => void)[] = [];

/** Registra un callback que se ejecuta al cambiar de empresa. */
export function registrarCambioEmpresa(fn: () => void): () => void {
  onCambioEmpresa.push(fn);
  return () => {
    onCambioEmpresa = onCambioEmpresa.filter((f) => f !== fn);
  };
}

/**
 * Inicia sesión con email/contraseña y carga el perfil
 * vinculado a la empresa. Verifica que la empresa esté activa
 * (excepto super_admin).
 */
export async function iniciarSesion(
  email: string,
  password: string,
): Promise<{ ok: boolean; usuario?: UsuarioMovil; error?: string }> {
  if (!supabase) {
    return { ok: false, error: 'Supabase no configurado. Verifica las credenciales.' };
  }

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

  // Verificar que la empresa esté activa (excepto super_admin)
  if (perfil.rol !== 'super_admin' && perfil.empresa_id) {
    const { data: empresa } = await supabase
      .from('empresas')
      .select('activo')
      .eq('id', perfil.empresa_id)
      .single();

    if (!empresa || !empresa.activo) {
      return {
        ok: false,
        error: 'Empresa desactivada. Contacte al administrador.',
      };
    }
  }

  usuarioActual = {
    id: perfil.id,
    username: perfil.username,
    nombre_completo: perfil.nombre_completo,
    rol: perfil.rol,
  };

  empresaActual = perfil.empresa_id;

  // Registrar actividad (super_admin puede no tener empresa_id)
  if (empresaActual) {
    await supabase.from('logs_movil').insert({
      empresa_id: empresaActual,
      usuario_id: usuarioActual.id,
      accion: 'login',
      entidad: 'sesion',
      detalle: { email },
    }).catch(() => {});
  }

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
  empresaContexto = null;
  nombreEmpresaContexto = null;
  onCambioEmpresa = [];
}

/** Obtiene el usuario actual en memoria */
export function obtenerUsuarioActual(): UsuarioMovil | null {
  return usuarioActual;
}

/** Obtiene el empresa_id activo (contexto del super_admin o el propio). */
export function obtenerEmpresaId(): string | null {
  // Si el super_admin tiene un contexto seleccionado, usarlo
  if (esSuperAdmin() && empresaContexto) {
    return empresaContexto;
  }
  return empresaActual;
}

/** Obtiene el nombre de la empresa en contexto. */
export function obtenerNombreEmpresaContexto(): string | null {
  return nombreEmpresaContexto;
}

/** Lista todas las empresas (solo super_admin). */
export async function listarEmpresas(): Promise<{
  ok: boolean;
  datos: { id: string; nombre: string; activo: boolean }[];
  error?: string;
}> {
  if (!supabase) {
    return { ok: false, datos: [], error: 'Supabase no configurado' };
  }

  const { data, error } = await supabase
    .from('empresas')
    .select('id, nombre, activo')
    .order('nombre');

  if (error) {
    return { ok: false, datos: [], error: error.message };
  }

  return { ok: true, datos: data || [] };
}

/** Cambia el contexto de empresa del super_admin. */
export async function cambiarEmpresaContexto(
  nuevaEmpresaId: string | null,
  nombre?: string,
): Promise<void> {
  empresaContexto = nuevaEmpresaId;
  nombreEmpresaContexto = nombre || null;
  // Notificar a todos los listeners
  for (const fn of onCambioEmpresa) {
    try {
      fn();
    } catch (e) {
      console.error('Error en listener de cambio de empresa:', e);
    }
  }
}

/** Verifica si el usuario actual es super_admin */
export function esSuperAdmin(): boolean {
  return usuarioActual?.rol === 'super_admin';
}

/** Verifica si el usuario actual es admin (no super_admin) */
export function esAdmin(): boolean {
  return usuarioActual?.rol === 'admin';
}

/** Verifica si hay sesión activa */
export async function verificarSesion(): Promise<UsuarioMovil | null> {
  if (!supabase) return null;

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
