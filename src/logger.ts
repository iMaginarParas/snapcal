import pino from 'pino';
import config from './config/configService';

// Configure pino logger with JSON output for production
const logger = pino({
  level: process.env.NODE_ENV === 'production' ? 'info' : 'debug',
  transport: process.env.NODE_ENV !== 'production' ? {
    target: 'pino-pretty',
    options: { colorize: true, translateTime: true }
  } : undefined,
  base: { pid: false },
});

export default logger;
