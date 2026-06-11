import pino from 'pino';

export const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  transport: process.env.LOG_ENDPOINT ? {
    target: 'pino-http',
    options: {
      url: process.env.LOG_ENDPOINT,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    }
  } : {
    target: 'pino-pretty',
    options: {
      colorize: true,
      translateTime: 'SYS:yyyy-mm-dd HH:MM:ss',
      ignore: 'pid,hostname'
    }
  }
});

export function errorLog(err: any, contextMsg: string) {
  logger.error({ err }, contextMsg);
}
