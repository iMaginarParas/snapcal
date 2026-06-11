import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import path from 'path';
import fs from 'fs';
import apiRoutes from './routes/api';
import swaggerDocsRouter from './docs/swagger';
import { initFallbackDb } from './services/db_fallback';
import { globalLimiter } from './middleware/rateLimiter';
import { logger } from './middleware/logger';

dotenv.config();

// Initialize fallback local database structure
initFallbackDb();

// Ensure uploads folder exists
const uploadsDir = path.join(__dirname, '../uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

const app = express();
const port = process.env.PORT || 3000;

// Configure CORS Allowed Origins
const allowedOrigins = process.env.ALLOWED_ORIGINS ? process.env.ALLOWED_ORIGINS.split(',') : '*';
// CORS configuration is now handled by dedicated middleware
import { corsConfig } from './middleware/corsConfig';
import { envCheck } from './middleware/envCheck';
import { httpsRedirect } from './middleware/httpsRedirect';

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
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'healthy', service: 'Sabtrack API' });
});

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

