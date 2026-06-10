import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import path from 'path';
import fs from 'fs';
import apiRoutes from './routes/api';
import { initFallbackDb } from './services/db_fallback';

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
app.use(cors({
  origin: allowedOrigins === '*' ? '*' : allowedOrigins
}));

app.use(express.json());

// Serve static uploads
app.use('/uploads', express.static(uploadsDir));

// Routes
app.use('/api', apiRoutes);

// Health check
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'healthy', service: 'Sabtrack API' });
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
  console.log('--- Production Config Audit ---');
  console.log(`PORT: ${port}`);
  console.log(`GEMINI_API_KEY: ${process.env.GEMINI_API_KEY ? 'CONFIGURED' : 'MISSING (using placeholder)'}`);
  console.log(`SUPABASE_URL: ${process.env.SUPABASE_URL ? 'CONFIGURED' : 'MISSING (using placeholder)'}`);
  console.log(`SUPABASE_ANON_KEY: ${process.env.SUPABASE_ANON_KEY ? 'CONFIGURED' : 'MISSING (using placeholder)'}`);
  console.log(`ALLOWED_ORIGINS: ${process.env.ALLOWED_ORIGINS || '*'}`);
  console.log('-------------------------------');
});
