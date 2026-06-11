import { Request, Response, NextFunction } from 'express';

export function envCheck(req: Request, res: Response, next: NextFunction) {
  const required = [
    'GEMINI_API_KEY',
    'SUPABASE_URL',
    'SUPABASE_ANON_KEY',
  ];
  const missing = required.filter(key => !process.env[key]);
  if (missing.length > 0) {
    // Use console.error because logger may not be initialized yet
    console.error('Missing required env vars:', missing.join(', '));
    // Fatal error – stop the process
    process.exit(1);
  }
  next();
}
