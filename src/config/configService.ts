import dotenv from 'dotenv';
import { z } from 'zod';

// Load .env file if present (will be ignored if not found, i.e. in containers)
dotenv.config();

// Define schema for required environment variables
const envSchema = z.object({
  GEMINI_API_KEY: z.string().min(1),
  SUPABASE_URL: z.string().url(),
  SUPABASE_ANON_KEY: z.string().min(1),
  ALLOWED_ORIGINS: z.string().optional(),
});

export type EnvConfig = z.infer<typeof envSchema>;

// Parse and validate environment variables.
// Zod will throw a clear error listing any missing required variables.
export const config: EnvConfig = envSchema.parse(process.env);

export default config;
