import config from '../config/configService';
import cors from 'cors';

export function corsConfig(app: any) {
  // Allowed origins from config or default to '*'
  const allowedOrigins = config.ALLOWED_ORIGINS ? config.ALLOWED_ORIGINS.split(',').map(o => o.trim()) : ['*'];

  const corsOptions = {
    origin: (origin: string | undefined, callback: (err: Error | null, allow?: boolean) => void) => {
      // Allow requests with no origin (e.g., mobile apps, curl)
      if (!origin) return callback(null, true);

      // In production, do not allow wildcard
      if (process.env.NODE_ENV === 'production' && allowedOrigins.includes('*')) {
        return callback(new Error('Wildcard origins are not allowed in production'), false);
      }

      if (allowedOrigins.includes('*')) return callback(null, true);
      if (allowedOrigins.includes(origin)) return callback(null, true);
      return callback(new Error('Not allowed by CORS'), false);
    },
    methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    credentials: true,
  };

  app.use(cors(corsOptions));
}
