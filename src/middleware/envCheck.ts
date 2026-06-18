import config from '../config/configService';
import logger from '../logger';
import { Request, Response, NextFunction } from 'express';

export function envCheck(req: Request, res: Response, next: NextFunction) {
  // Config validation occurs at import time via configService.
  // This middleware simply proceeds; any import errors will be caught by errorHandler.
  logger.info('Env check passed');
  next();
}
