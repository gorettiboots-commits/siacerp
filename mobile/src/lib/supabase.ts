import { createClient, SupabaseClient } from '@supabase/supabase-js';

const URL = process.env.EXPO_PUBLIC_SUPABASE_URL ?? '';
const ANON_KEY = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY ?? '';

let _supabase: SupabaseClient | null = null;

if (URL && ANON_KEY) {
  try {
    _supabase = createClient(URL, ANON_KEY);
  } catch (e: any) {
    console.error('[Supabase] Error creando cliente:', e.message);
    _supabase = null;
  }
}

export const supabase: SupabaseClient | null = _supabase;

export function supabaseConfigurado(): boolean {
  return supabase !== null;
}