import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
// Load environment variables immediately after imports to ensure env vars are available for middlewares
dotenv.config();

import path from 'path';
import fs from 'fs';
import apiRoutes from './routes/api';
import swaggerDocsRouter from './docs/swagger';
import { initFallbackDb } from './services/db_fallback';
import { globalLimiter } from './middleware/rateLimiter';
import logger from './logger';
import { corsConfig } from './middleware/corsConfig';
import { envCheck } from './middleware/envCheck';
import { httpsRedirect } from './middleware/httpsRedirect';
import { errorHandler } from './middleware/errorHandler';

// Initialize fallback local database structure
initFallbackDb();

// Ensure uploads folder exists
const uploadsDir = path.join(__dirname, '../uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

const app = express();
app.set('trust proxy', 1);
const port = process.env.PORT || 3000;

// Verify required environment variables before proceeding
app.use(envCheck);

// Enforce HTTPS in production
app.use(httpsRedirect);

// Apply CORS configuration
corsConfig(app);

// Apply Global Rate Limiting
app.use(globalLimiter);

app.use(express.json());

// Serve static uploads
app.use('/uploads', express.static(uploadsDir));

// Swagger Documentation Route (only in non‑production)
if (process.env.NODE_ENV !== 'production') {
  app.use('/docs', swaggerDocsRouter);
}

// Routes
app.use('/api', apiRoutes);

// Health check
app.get('/health', (req, res) =>
  res.status(200).json({ status: 'healthy', service: 'Sabtrack API' })
);

// Global error handler (must be after all routes)
app.use(errorHandler);

app.listen(port, () => {
  logger.info(`Server running on port ${port}`);
  logger.info('--- Production Config Audit ---');
  logger.info(`PORT: ${port}`);
  logger.info(`GEMINI_API_KEY: ${process.env.GEMINI_API_KEY ? 'CONFIGURED' : 'MISSING (using placeholder)'}`);
  logger.info(`SUPABASE_URL: ${process.env.SUPABASE_URL ? 'CONFIGURED' : 'MISSING (using placeholder)'}`);
  logger.info(`SUPABASE_ANON_KEY: ${process.env.SUPABASE_ANON_KEY ? 'CONFIGURED' : 'MISSING (using placeholder)'}`);
  logger.info(`ALLOWED_ORIGINS: ${process.env.ALLOWED_ORIGINS || '*'}`);
  logger.info('-------------------------------');
});

