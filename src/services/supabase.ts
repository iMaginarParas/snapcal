import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
dotenv.config();

const supabaseUrl = process.env.SUPABASE_URL || '';
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_ANON_KEY || '';

if (!supabaseUrl) {
  console.error('ERROR: SUPABASE_URL is not set in environment variables.');
}
if (!supabaseKey) {
  console.error('ERROR: SUPABASE_ANON_KEY / SUPABASE_SERVICE_ROLE_KEY is not set in environment variables.');
}

// Fallback to placeholder values to allow server to boot (e.g. for health checks) without throwing runtime crash.
export const supabase = createClient(
  supabaseUrl || 'https://placeholder-url.supabase.co',
  supabaseKey || 'placeholder-key'
);

