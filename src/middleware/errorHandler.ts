import { Request, Response, NextFunction } from 'express';
import logger from '../logger';

export function errorHandler(err: any, req: Request, res: Response, next: NextFunction) {
  // Log the error
  logger.error({ err }, 'Unhandled error');

  // Do not expose stack traces in production
  const status = err.status || 500;
  const message = process.env.NODE_ENV === 'production' ? 'Internal Server Error' : err.message;

  res.status(status).json({
    error: message,
    // Optionally include stack in non‑production for debugging
    ...(process.env.NODE_ENV !== 'production' && { stack: err.stack }),
  });
}
