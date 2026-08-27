import { createClient, SupabaseClient } from '@supabase/supabase-js';

const URL = process.env.EXPO_PUBLIC_SUPABASE_URL ?? '';
const ANON_KEY = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY ?? '';

if (!URL || !ANON_KEY) {
  console.warn('[Supabase] Variables EXPO_PUBLIC no configuradas. Verifica mobile/.env');
}

export const supabase: SupabaseClient | null =
  URL && ANON_KEY ? createClient(URL, ANON_KEY) : null;

export function supabaseConfigurado(): boolean {
  return supabase !== null;
}