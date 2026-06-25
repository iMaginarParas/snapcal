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

// Privacy policy endpoint (Bypasses global CORS to allow anyone/crawlers to view)
app.get('/privacy', (req, res) => {
  res.setHeader('Content-Type', 'text/html');
  res.status(200).send(`
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Privacy Policy - SABTRACK AI</title>
      <style>
        body {
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          line-height: 1.6;
          max-width: 800px;
          margin: 40px auto;
          padding: 0 20px;
          color: #334155;
          background-color: #f8fafc;
        }
        .container {
          background: #ffffff;
          padding: 40px;
          border-radius: 16px;
          box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.05);
          border: 1px solid #e2e8f0;
        }
        h1 {
          color: #0f172a;
          font-size: 28px;
          margin-bottom: 5px;
        }
        .date {
          color: #00d1b2;
          font-weight: bold;
          font-size: 14px;
          margin-bottom: 30px;
        }
        h2 {
          color: #0f172a;
          font-size: 20px;
          margin-top: 30px;
          border-bottom: 2px solid #f1f5f9;
          padding-bottom: 8px;
        }
        p {
          margin-bottom: 16px;
        }
        ul {
          padding-left: 20px;
          margin-bottom: 20px;
        }
        li {
          margin-bottom: 8px;
        }
        a {
          color: #00d1b2;
          text-decoration: none;
        }
        a:hover {
          text-decoration: underline;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>SABTRACK AI Privacy Policy</h1>
        <div class="date">Last Updated: June 2026</div>
        
        <p>We value your privacy and are committed to protecting your personal data. This Privacy Policy details how we collect, use, and secure your information when you use our mobile application and related API services.</p>
        
        <h2>Information We Collect</h2>
        <ul>
          <li><strong>Account Data:</strong> Email and password credentials securely stored via Supabase Authentication.</li>
          <li><strong>Nutritional Logs:</strong> Details of meals tracked, portion sizes, calorie counts, and macro profiles.</li>
          <li><strong>Fasting & Weight History:</strong> Progress data, fasting timers, and weight logs uploaded to monitor personal trends.</li>
          <li><strong>Uploaded Images:</strong> Food pictures sent to the Google Gemini AI backend for macro estimation (we do not store or sell your photos).</li>
          <li><strong>Physical Activity & Sensors:</strong> Access to your device's built-in step counter sensor (pedometer) and Health Connect data (steps, active calories burned) if permissions are explicitly granted. This data is read-only and processed locally.</li>
        </ul>
        
        <h2>How We Use Your Data</h2>
        <p>Your data is exclusively used to provide personal fitness analytics, update progress charts, synchronize dashboard records across devices, and offer community groups feature functionality.</p>
        
        <h2>Third-Party Integrations</h2>
        <p>SABTRACK AI securely coordinates with Supabase for data hosting and authentication, and sends food media/text to the Google Gemini AI backend to extract macronutrient variables. We do not distribute database records to any third-party marketing services.</p>
        
        <h2>Your Rights</h2>
        <p>You maintain full ownership of your data. You can request to delete your account and wipe all linked database tables (meals, fasting records, user stats) at any time by contacting support or from your profile settings.</p>

        <h2>Contact Us</h2>
        <p>If you have any questions or feedback about this Privacy Policy or wish to request data deletion, please contact us at <a href="mailto:support@sabtrack.ai">support@sabtrack.ai</a>.</p>
      </div>
    </body>
    </html>
  `);
});

// Health check endpoint (Bypasses global CORS for status checkers)
app.get('/health', (req, res) =>
  res.status(200).json({ status: 'healthy', service: 'Sabtrack API' })
);

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

