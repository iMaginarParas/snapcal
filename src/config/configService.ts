import dotenv from 'dotenv';
import dotenvSafe from 'dotenv-safe';
import { z } from 'zod';

// Load .env file and ensure required variables are present
dotenv.config();
// dotenv-safe will verify that all variables in .env.example are defined
// It will also populate process.env with defaults from .env.example if needed
dotenvSafe.config({
  example: '.env.example',
  allowEmptyValues: false,
});

// Define schema for required environment variables
const envSchema = z.object({
  GEMINI_API_KEY: z.string().min(1),
  SUPABASE_URL: z.string().url(),
  SUPABASE_ANON_KEY: z.string().min(1),
  ALLOWED_ORIGINS: z.string().optional(),
});

export type EnvConfig = z.infer<typeof envSchema>;

// Parse and validate environment variables
export const config: EnvConfig = envSchema.parse(process.env);

export default config;
