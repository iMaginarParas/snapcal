import { Request, Response, NextFunction } from 'express';
import { ZodSchema, ZodError } from 'zod';
import { sendError } from './response';

export function validate(schema: ZodSchema) {
  return (req: Request, res: Response, next: NextFunction) => {
    try {
      schema.parse(req.body);
      next();
    } catch (error) {
      if (error instanceof ZodError) {
        const errorMsg = error.issues.map((err: any) => `${err.path.join('.')}: ${err.message}`).join(', ');
        return sendError(res, `Validation failed: ${errorMsg}`, 400);
      }
      return sendError(res, 'Invalid request data', 400);
    }
  };
}

export function validateQuery(schema: ZodSchema) {
  return (req: Request, res: Response, next: NextFunction) => {
    try {
      req.query = schema.parse(req.query) as any;
      next();
    } catch (error) {
      if (error instanceof ZodError) {
        const errorMsg = error.issues.map((err: any) => `${err.path.join('.')}: ${err.message}`).join(', ');
        return sendError(res, `Query validation failed: ${errorMsg}`, 400);
      }
      return sendError(res, 'Invalid query parameters', 400);
    }
  };
}
