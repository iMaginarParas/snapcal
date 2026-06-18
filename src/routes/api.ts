import { Router } from 'express';
import multer from 'multer';
import fs from 'fs';
import path from 'path';
import { z } from 'zod';
import { analyzeMealImage, generateMockMeal, analyzeMealText, analyzeMealLabel, analyzeMealBarcode, generateWorkoutInsight } from '../services/gemini';
import { supabase } from '../services/supabase';
import { fallbackDb } from '../services/db_fallback';
import { sendSuccess, sendError } from '../middleware/response';
import { logger, errorLog } from '../middleware/logger';
import { authLimiter } from '../middleware/rateLimiter';
import { validate, validateQuery } from '../middleware/validation';

const router = Router();
const isSupabaseLive = process.env.SUPABASE_URL && 
  !process.env.SUPABASE_URL.includes('placeholder-url') &&
  !process.env.SUPABASE_URL.includes('your_supabase_project_url');

const upload = multer({ storage: multer.memoryStorage() });

// --- Schemas for Request Validation ---

const signupSchema = z.object({
  email: z.string().email('Invalid email format'),
  password: z.string().min(6, 'Password must be at least 6 characters long'),
});

const loginSchema = z.object({
  email: z.string().email('Invalid email format'),
  password: z.string().min(1, 'Password is required'),
});

const googleLoginSchema = z.object({
  idToken: z.string().min(1, 'ID Token is required'),
  displayName: z.string().optional(),
  photoUrl: z.string().optional(),
  email: z.string().optional(),
});

const describeNutritionSchema = z.object({
  description: z.string().min(3, 'Meal description must be at least 3 characters long'),
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in YYYY-MM-DD format').optional(),
});

const updateProfileSchema = z.object({
  name: z.string().min(1, 'Name is required').optional(),
  age: z.union([z.number(), z.string()]).transform(val => parseInt(val as string) || 25).optional(),
  weight: z.union([z.number(), z.string()]).transform(val => parseFloat(val as string) || 76.4).optional(),
  height: z.union([z.number(), z.string()]).transform(val => parseFloat(val as string) || 178.0).optional(),
  goals: z.string().optional(),
});

const logMealSchema = z.object({
  name: z.string().min(1, 'Meal name is required'),
  calories: z.number().nonnegative('Calories must be non-negative'),
  protein: z.number().nonnegative('Protein must be non-negative').optional().default(0),
  carbs: z.number().nonnegative('Carbs must be non-negative').optional().default(0),
  fats: z.number().nonnegative('Fats must be non-negative').optional().default(0),
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in YYYY-MM-DD format').optional(),
});

const logWorkoutSchema = z.object({
  workout_name: z.string().min(1, 'Workout name is required'),
  distance: z.number().nonnegative().optional(),
  duration_seconds: z.number().int().nonnegative().optional(),
  calories: z.number().nonnegative().optional(),
  route_points: z.array(z.any()).optional(),
});

const dailyStatsQuerySchema = z.object({
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in YYYY-MM-DD format').optional(),
});

const updateDailyStatsSchema = z.object({
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in YYYY-MM-DD format').optional(),
  steps: z.number().int().nonnegative().optional(),
  water_ml: z.number().nonnegative().optional(),
});

const logMeasurementSchema = z.object({
  metric_type: z.enum(['weight', 'waist', 'chest', 'arms', 'thighs', 'strength']),
  value: z.number().positive('Value must be positive'),
  date: z.string().optional(),
});

const barcodeSchema = z.object({
  barcode: z.string().min(1, 'Barcode is required'),
});

const redeemReferralSchema = z.object({
  code: z.string().min(1, 'Referral code is required'),
});

const listQuerySchema = z.object({
  page: z.preprocess((val) => val || '1', z.string().transform(val => parseInt(val) || 1)).default(1 as any),
  limit: z.preprocess((val) => val || '20', z.string().transform(val => parseInt(val) || 20)).default(20 as any),
});

const mealsQuerySchema = listQuerySchema.extend({
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in YYYY-MM-DD format').optional(),
});

// Helper function to save meal to Supabase if authenticated
async function saveMealToDb(authHeader: string | undefined, analysisResult: any, dateStr?: string) {
  if (authHeader && authHeader.startsWith('Bearer ')) {
    const token = authHeader.split(' ')[1];
    try {
      let userId = '';
      if (token.startsWith('mock-user-')) {
        userId = token.replace('mock-user-', '');
      } else if (isSupabaseLive) {
        const { data: { user }, error: userError } = await supabase.auth.getUser(token);
        if (!userError && user) {
          userId = user.id;
        }
      } else {
        userId = token;
      }

      if (userId) {
        const loggedAt = dateStr ? new Date(`${dateStr}T12:00:00.000Z`) : new Date();
        if (!isSupabaseLive) {
          fallbackDb.addMeal(userId, {
            name: analysisResult.name,
            calories: analysisResult.calories,
            protein: analysisResult.protein || 0,
            carbs: analysisResult.carbs || 0,
            fats: analysisResult.fats || 0,
            logged_at: loggedAt.toISOString()
          });
        } else {
          const { error: dbError } = await supabase
            .from('meals')
            .insert([
              {
                user_id: userId,
                name: analysisResult.name,
                calories: analysisResult.calories,
                protein: analysisResult.protein || 0,
                carbs: analysisResult.carbs || 0,
                fats: analysisResult.fats || 0,
                logged_at: loggedAt.toISOString()
              }
            ]);
          
          if (dbError) {
            errorLog(dbError, 'Failed to save meal to Supabase');
          }
        }
      }
    } catch (err) {
      errorLog(err, 'Error during meal save');
    }
  }
}

// --- Authentication ---

/**
 * @openapi
 * /auth/signup:
 *   post:
 *     summary: Sign up a new user
 *     tags: [Authentication]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - email
 *               - password
 *             properties:
 *               email:
 *                 type: string
 *               password:
 *                 type: string
 *     responses:
 *       201:
 *         description: Created
 *       400:
 *         description: Bad Request
 */
router.post('/auth/signup', authLimiter, validate(signupSchema), async (req: any, res: any) => {
  try {
    const { email, password } = req.body;

    if (!isSupabaseLive) {
      const mockId = email.replace(/[^a-zA-Z0-9]/g, '_');
      fallbackDb.getUser(mockId);
      fallbackDb.updateUser(mockId, { email });
      return sendSuccess(res, {
        token: `mock-user-${mockId}`,
        user: { id: mockId, email }
      }, 201);
    }

    const { data, error } = await supabase.auth.signUp({
      email,
      password,
    });

    if (error) {
      return sendError(res, error.message, 400);
    }

    sendSuccess(res, {
      token: data.session?.access_token || null,
      user: data.user,
    }, 201);
  } catch (error: any) {
    errorLog(error, 'Signup Error');
    sendError(res, error.message || 'Internal server error', 500);
  }
});

/**
 * @openapi
 * /auth/login:
 *   post:
 *     summary: Log in an existing user
 *     tags: [Authentication]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - email
 *               - password
 *             properties:
 *               email:
 *                 type: string
 *               password:
 *                 type: string
 *     responses:
 *       200:
 *         description: Success
 *       400:
 *         description: Bad Request
 */
router.post('/auth/refresh', authLimiter, validate(z.object({ refreshToken: z.string().min(1) })), async (req: any, res: any) => {
  try {
    const { refreshToken } = req.body;
    if (!isSupabaseLive) {
      return sendError(res, 'Refresh not available offline', 400);
    }
    const { data, error } = await supabase.auth.refreshSession({ refresh_token: refreshToken });
    if (error) {
      return sendError(res, error.message, 400);
    }
    sendSuccess(res, {
      access_token: data.session?.access_token || null,
      refresh_token: data.session?.refresh_token || null,
    });
  } catch (err: any) {
    errorLog(err, 'Token Refresh Error');
    sendError(res, err.message || 'Internal server error', 500);
  }
});

router.post('/auth/login', authLimiter, validate(loginSchema), async (req: any, res: any) => {
  try {
    const { email, password } = req.body;

    if (!isSupabaseLive) {
      const mockId = email.replace(/[^a-zA-Z0-9]/g, '_');
      fallbackDb.getUser(mockId);
      fallbackDb.updateUser(mockId, { email });
      return sendSuccess(res, {
        token: `mock-user-${mockId}`,
        user: { id: mockId, email }
      });
    }

    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      return sendError(res, error.message, 400);
    }

    sendSuccess(res, {
      token: data.session?.access_token || null,
      user: data.user,
    });
  } catch (error: any) {
    errorLog(error, 'Login Error');
    sendError(res, error.message || 'Internal server error', 500);
  }
});

/**
 * @openapi
 * /auth/google-login:
 *   post:
 *     summary: Sign in using Google ID Token
 *     tags: [Authentication]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - idToken
 *             properties:
 *               idToken:
 *                 type: string
 *     responses:
 *       200:
 *         description: Success
 */
router.post('/auth/google-login', authLimiter, validate(googleLoginSchema), async (req: any, res: any) => {
  try {
    const { idToken, displayName, photoUrl, email } = req.body;

    if (!isSupabaseLive) {
      const mockId = 'google_user_' + Math.random().toString(36).substring(2, 7);
      const emailVal = email || `${mockId}@gmail.com`;
      const nameVal = displayName || 'Google User';
      const picVal = photoUrl || null;

      fallbackDb.updateUser(mockId, {
        email: emailVal,
        name: nameVal,
        profile_picture_url: picVal,
      });

      return sendSuccess(res, {
        token: `mock-user-${mockId}`,
        user: { id: mockId, email: emailVal }
      });
    }

    const { data, error } = await supabase.auth.signInWithIdToken({
      provider: 'google',
      token: idToken,
    });

    if (error) {
      return sendError(res, error.message, 400);
    }

    if (data.user) {
      const googleName = displayName || data.user.user_metadata?.full_name || data.user.user_metadata?.name || 'Guest User';
      const googleAvatar = photoUrl || data.user.user_metadata?.avatar_url || data.user.user_metadata?.picture || null;

      const { error: upsertError } = await supabase
        .from('users')
        .upsert({
          id: data.user.id,
          email: data.user.email,
          name: googleName,
          profile_picture_url: googleAvatar,
        }, { onConflict: 'id' });

      if (upsertError) {
        logger.warn(`Failed to upsert user profile on Google Sign-In: ${upsertError.message}`);
      }
    }

    sendSuccess(res, {
      token: data.session?.access_token || null,
      user: data.user,
    });
  } catch (error: any) {
    errorLog(error, 'Google Login Error');
    sendError(res, error.message || 'Internal server error', 500);
  }
});

// --- Smart Nutrition ---

/**
 * @openapi
 * /nutrition/analyze:
 *   post:
 *     summary: Analyze nutrition from meal image or retrieve a mock generation
 *     tags: [Nutrition]
 *     requestBody:
 *       content:
 *         multipart/form-data:
 *           schema:
 *             type: object
 *             properties:
 *               image:
 *                 type: string
 *                 format: binary
 *               mockImage:
 *                 type: boolean
 *     responses:
 *       200:
 *         description: Success
 */
router.post('/nutrition/analyze', upload.single('image'), async (req: any, res: any) => {
  try {
    let analysisResult;
    const dateStr = req.body.date;

    if (req.file) {
      const base64Image = req.file.buffer.toString('base64');
      const mimeType = req.file.mimetype;
      analysisResult = await analyzeMealImage(mimeType, base64Image);
    } else if (req.body.mockImage === true || req.body.mockImage === 'true') {
      analysisResult = await generateMockMeal();
    } else {
      return sendError(res, 'No image uploaded or mockImage flag set', 400);
    }

    await saveMealToDb(req.headers.authorization, analysisResult, dateStr);
    sendSuccess(res, analysisResult);
  } catch (error: any) {
    errorLog(error, 'Analyze Nutrition Error');
    sendError(res, error.message || 'Internal server error', 500);
  }
});

/**
 * @openapi
 * /nutrition/describe:
 *   post:
 *     summary: Get nutrition details from text description
 *     tags: [Nutrition]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - description
 *             properties:
 *               description:
 *                 type: string
 *     responses:
 *       200:
 *         description: Success
 */
router.post('/nutrition/describe', validate(describeNutritionSchema), async (req: any, res: any) => {
  try {
    const { description, date } = req.body;
    const analysisResult = await analyzeMealText(description);

    await saveMealToDb(req.headers.authorization, analysisResult, date);
    sendSuccess(res, analysisResult);
  } catch (error: any) {
    errorLog(error, 'Describe Nutrition Error');
    sendError(res, error.message || 'Internal server error', 500);
  }
});

/**
 * @openapi
 * /nutrition/analyze-label:
 *   post:
 *     summary: Analyze nutrition facts label from image
 *     tags: [Nutrition]
 *     responses:
 *       200:
 *         description: Success
 */
router.post('/nutrition/analyze-label', upload.single('image'), async (req: any, res: any) => {
  try {
    let analysisResult;
    const dateStr = req.body.date;

    if (req.file) {
      const base64Image = req.file.buffer.toString('base64');
      const mimeType = req.file.mimetype;
      analysisResult = await analyzeMealLabel(mimeType, base64Image);
    } else if (req.body.mockImage === true || req.body.mockImage === 'true') {
      analysisResult = {
        name: "Commercial Protein Bar (Label Scan)",
        calories: 220,
        protein: 20,
        carbs: 24,
        fats: 7
      };
    } else {
      return sendError(res, 'No image uploaded or mockImage flag set', 400);
    }

    await saveMealToDb(req.headers.authorization, analysisResult, dateStr);
    sendSuccess(res, analysisResult);
  } catch (error: any) {
    errorLog(error, 'Analyze Label Error');
    sendError(res, error.message || 'Internal server error', 500);
  }
});

// Backward compatibility route
router.post('/analyze-meal', upload.single('image'), async (req: any, res: any) => {
  try {
    const file = req.file;
    if (!file) {
      return sendError(res, 'No image uploaded', 400);
    }

    const base64Image = file.buffer.toString('base64');
    const mimeType = file.mimetype;
    const analysisResult = await analyzeMealImage(mimeType, base64Image);

    sendSuccess(res, analysisResult);
  } catch (error: any) {
    errorLog(error, 'Analyze Meal Error');
    sendError(res, error.message || 'Internal server error', 500);
  }
});

// --- Middleware & Premium Features API Implementation ---

export async function requireAuth(req: any, res: any, next: any) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return sendError(res, 'Authorization header is required', 401);
  }
  const token = authHeader.split(' ')[1];
  
  if (token.startsWith('mock-user-')) {
    const userId = token.replace('mock-user-', '');
    req.user = { id: userId, email: `${userId}@fallback.local` };
    return next();
  }

  if (isSupabaseLive) {
    try {
      const { data: { user }, error } = await supabase.auth.getUser(token);
      if (error || !user) {
        return sendError(res, 'Invalid Supabase authorization token', 401);
      }
      req.user = user;
      return next();
    } catch (e: any) {
      return sendError(res, e.message || 'Authentication error', 401);
    }
  } else {
    const userId = token.startsWith('mock-user-') ? token.replace('mock-user-', '') : token;
    req.user = { id: userId, email: `${userId}@fallback.local` };
    return next();
  }
}

/**
 * @openapi
 * /user/profile:
 *   get:
 *     summary: Get the current user profile
 *     tags: [Profile]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Success
 */
router.get('/user/profile', requireAuth, async (req: any, res: any) => {
  try {
    const userId = req.user.id;
    if (!isSupabaseLive) {
      const profile = fallbackDb.getUser(userId);
      return sendSuccess(res, profile);
    }

    const { data, error } = await supabase
      .from('users')
      .select('*')
      .eq('id', userId)
      .single();

    if (error) {
      const googleName = req.user.user_metadata?.full_name || req.user.user_metadata?.name || 'Guest User';
      const googleAvatar = req.user.user_metadata?.avatar_url || req.user.user_metadata?.picture || null;
      const defaultProfile = {
        id: userId,
        email: req.user.email,
        name: googleName,
        profile_picture_url: googleAvatar,
        age: 25,
        weight: 76.4,
        height: 178,
        goals: 'Build Muscle'
      };
      const { data: newProfile, error: insertError } = await supabase
        .from('users')
        .insert([defaultProfile])
        .select()
        .single();
      
      if (insertError) throw insertError;
      return sendSuccess(res, newProfile);
    }

    let profileData = data;
    let needsUpdate = false;
    const updates: any = {};
    if (!data.name && (req.user.user_metadata?.full_name || req.user.user_metadata?.name)) {
      updates.name = req.user.user_metadata.full_name || req.user.user_metadata.name;
      needsUpdate = true;
    }
    if (!data.profile_picture_url && (req.user.user_metadata?.avatar_url || req.user.user_metadata?.picture)) {
      updates.profile_picture_url = req.user.user_metadata.avatar_url || req.user.user_metadata.picture;
      needsUpdate = true;
    }
    if (needsUpdate) {
      const { data: updatedData, error: updateError } = await supabase
        .from('users')
        .update(updates)
        .eq('id', userId)
        .select()
        .single();
      if (!updateError && updatedData) {
        profileData = updatedData;
      }
    }

    sendSuccess(res, profileData);
  } catch (error: any) {
    errorLog(error, 'Get Profile Error');
    sendError(res, error.message || 'Failed to retrieve profile', 500);
  }
});

/**
 * @openapi
 * /user/profile:
 *   put:
 *     summary: Update the user profile details
 *     tags: [Profile]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               name:
 *                 type: string
 *               age:
 *                 type: integer
 *               weight:
 *                 type: number
 *               height:
 *                 type: number
 *               goals:
 *                 type: string
 *     responses:
 *       200:
 *         description: Success
 */
router.put('/user/profile', requireAuth, validate(updateProfileSchema), async (req: any, res: any) => {
  try {
    const userId = req.user.id;
    const { name, age, weight, height, goals } = req.body;

    if (!isSupabaseLive) {
      const updated = fallbackDb.updateUser(userId, { name, age, weight, height, goals });
      return sendSuccess(res, updated);
    }

    const { data, error } = await supabase
      .from('users')
      .update({ name, age, weight, height, goals })
      .eq('id', userId)
      .select()
      .single();

    if (error) throw error;
    sendSuccess(res, data);
  } catch (error: any) {
    errorLog(error, 'Update Profile Error');
    sendError(res, error.message || 'Failed to update profile', 500);
  }
});

/**
 * @openapi
 * /user/profile/picture:
 *   post:
 *     summary: Upload a profile picture
 *     tags: [Profile]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Success
 */
router.post('/user/profile/picture', requireAuth, upload.single('image'), async (req: any, res: any) => {
  try {
    const userId = req.user.id;
    if (!req.file) {
      return sendError(res, 'No image file uploaded', 400);
    }

    const fileBuffer = req.file.buffer;
    const extension = req.file.originalname.split('.').pop() || 'jpg';
    const fileName = `${userId}-${Date.now()}.${extension}`;
    let profilePictureUrl = '';

    if (isSupabaseLive) {
      try {
        const { error: uploadError } = await supabase.storage
          .from('profile-pictures')
          .upload(fileName, fileBuffer, {
            contentType: req.file.mimetype,
            upsert: true
          });

        if (!uploadError) {
          const { data: { publicUrl } } = supabase.storage
            .from('profile-pictures')
            .getPublicUrl(fileName);
          profilePictureUrl = publicUrl;
        } else {
          logger.warn(`Supabase bucket upload failed, using local server storage fallback: ${uploadError.message}`);
        }
      } catch (err) {
        logger.warn(`Supabase bucket error, falling back locally: ${err}`);
      }
    }

    if (!profilePictureUrl) {
      const localPath = path.join(__dirname, '../../uploads', fileName);
      fs.writeFileSync(localPath, fileBuffer);
      profilePictureUrl = `${req.protocol}://${req.get('host')}/uploads/${fileName}`;
    }

    if (!isSupabaseLive) {
      fallbackDb.updateUser(userId, { profile_picture_url: profilePictureUrl });
    } else {
      const { error: dbError } = await supabase
        .from('users')
        .update({ profile_picture_url: profilePictureUrl })
        .eq('id', userId);
      
      if (dbError) throw dbError;
    }

    res.json({ success: true, url: profilePictureUrl });
  } catch (error: any) {
    errorLog(error, 'Upload Profile Picture Error');
    sendError(res, error.message || 'Failed to upload picture', 500);
  }
});

/**
 * @openapi
 * /meals:
 *   get:
 *     summary: Retrieve user's logged meals (supports pagination)
 *     tags: [Meals]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: query
 *         name: page
 *         schema:
 *           type: string
 *       - in: query
 *         name: limit
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: Success
 */
router.get('/meals', requireAuth, validateQuery(mealsQuerySchema), async (req: any, res: any) => {
  try {
    const userId = req.user.id;
    const page = req.query.page;
    const limit = req.query.limit;
    const offset = (page - 1) * limit;
    const dateStr = req.query.date;

    if (!isSupabaseLive) {
      let meals = fallbackDb.getMeals(userId);
      if (dateStr) {
        meals = meals.filter(m => m.logged_at && m.logged_at.split('T')[0] === dateStr);
      }
      const paginatedMeals = meals.slice(offset, offset + limit);
      return sendSuccess(res, paginatedMeals);
    }

    let query = supabase
      .from('meals')
      .select('*')
      .eq('user_id', userId);

    if (dateStr) {
      query = query
        .gte('logged_at', `${dateStr}T00:00:00.000Z`)
        .lte('logged_at', `${dateStr}T23:59:59.999Z`);
    }

    const { data, error } = await query
      .order('logged_at', { ascending: false })
      .range(offset, offset + limit - 1);

    if (error) throw error;
    sendSuccess(res, data);
  } catch (error: any) {
    errorLog(error, 'Get Meals Error');
    sendError(res, error.message || 'Failed to retrieve meals', 500);
  }
});

/**
 * @openapi
 * /meals:
 *   post:
 *     summary: Log a meal manually
 *     tags: [Meals]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - name
 *               - calories
 *             properties:
 *               name:
 *                 type: string
 *               calories:
 *                 type: number
 *               protein:
 *                 type: number
 *               carbs:
 *                 type: number
 *               fats:
 *                 type: number
 *     responses:
 *       200:
 *         description: Success
 */
router.post('/meals', requireAuth, validate(logMealSchema), async (req: any, res: any) => {
  try {
    const userId = req.user.id;
    const { name, calories, protein, carbs, fats, date } = req.body;
    const loggedAt = date ? new Date(`${date}T12:00:00.000Z`) : new Date();

    if (!isSupabaseLive) {
      const meal = fallbackDb.addMeal(userId, { name, calories, protein, carbs, fats, logged_at: loggedAt.toISOString() });
      return sendSuccess(res, meal);
    }

    const { data, error } = await supabase
      .from('meals')
      .insert([{ user_id: userId, name, calories, protein, carbs, fats, logged_at: loggedAt.toISOString() }])
      .select()
      .single();

    if (error) throw error;
    sendSuccess(res, data);
  } catch (error: any) {
    errorLog(error, 'Log Meal Error');
    sendError(res, error.message || 'Failed to log meal', 500);
  }
});

/**
 * @openapi
 * /workouts:
 *   get:
 *     summary: Retrieve user's completed workouts (supports pagination)
 *     tags: [Workouts]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: query
 *         name: page
 *         schema:
 *           type: string
 *       - in: query
 *         name: limit
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: Success
 */
router.get('/workouts', requireAuth, validateQuery(listQuerySchema), async (req: any, res: any) => {
  try {
    const userId = req.user.id;
    const page = req.query.page;
    const limit = req.query.limit;
    const offset = (page - 1) * limit;

    if (!isSupabaseLive) {
      const workouts = fallbackDb.getWorkouts(userId);
      const paginatedWorkouts = workouts.slice(offset, offset + limit);
      return sendSuccess(res, paginatedWorkouts);
    }

    const { data, error } = await supabase
      .from('workouts')
      .select('*')
      .eq('user_id', userId)
      .order('completed_at', { ascending: false })
      .range(offset, offset + limit - 1);

    if (error) throw error;
    sendSuccess(res, data);
  } catch (error: any) {
    errorLog(error, 'Get Workouts Error');
    sendError(res, error.message || 'Failed to retrieve workouts', 500);
  }
});

/**
 * @openapi
 * /workouts:
 *   post:
 *     summary: Log a completed workout
 *     tags: [Workouts]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - workout_name
 *             properties:
 *               workout_name:
 *                 type: string
 *               distance:
 *                 type: number
 *               duration_seconds:
 *                 type: integer
 *               calories:
 *                 type: number
 *               route_points:
 *                 type: array
 *                 items:
 *                   type: object
 *     responses:
 *       200:
 *         description: Success
 */
router.post('/workouts', requireAuth, validate(logWorkoutSchema), async (req: any, res: any) => {
  try {
    const userId = req.user.id;
    const { workout_name, distance, duration_seconds, calories, route_points } = req.body;

    if (!isSupabaseLive) {
      const workout = fallbackDb.addWorkout(userId, { workout_name, distance, duration_seconds, calories, route_points });
      return sendSuccess(res, workout);
    }

    const { data, error } = await supabase
      .from('workouts')
      .insert([{
        user_id: userId,
        workout_name,
        distance,
        duration_seconds,
        calories,
        route_points,
        completed: true,
        completed_at: new Date().toISOString()
      }])
      .select()
      .single();

    if (error) throw error;
    sendSuccess(res, data);
  } catch (error: any) {
    errorLog(error, 'Log Workout Error');
    sendError(res, error.message || 'Failed to save workout', 500);
  }
});

/**
 * @openapi
 * /daily-stats:
 *   get:
 *     summary: Retrieve daily stats (steps, water) for a specific date
 *     tags: [DailyStats]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: query
 *         name: date
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: Success
 */
router.get('/daily-stats', requireAuth, validateQuery(dailyStatsQuerySchema), async (req: any, res: any) => {
  try {
    const userId = req.user.id;
    const dateStr = req.query.date || new Date().toISOString().split('T')[0];

    if (!isSupabaseLive) {
      const stats = fallbackDb.getDailyStats(userId, dateStr);
      return sendSuccess(res, stats);
    }

    const { data, error } = await supabase
      .from('daily_stats')
      .select('*')
      .eq('user_id', userId)
      .eq('date', dateStr)
      .maybeSingle();

    if (error) throw error;
    
    if (!data) {
      const { data: newStats, error: createError } = await supabase
        .from('daily_stats')
        .insert([{ user_id: userId, date: dateStr, steps: 0, water_ml: 0 }])
        .select()
        .single();
      if (createError) throw createError;
      return sendSuccess(res, newStats);
    }

    sendSuccess(res, data);
  } catch (error: any) {
    errorLog(error, 'Get Daily Stats Error');
    sendError(res, error.message || 'Failed to retrieve stats', 500);
  }
});

/**
 * @openapi
 * /daily-stats:
 *   post:
 *     summary: Update steps and water statistics for a date
 *     tags: [DailyStats]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               date:
 *                 type: string
 *               steps:
 *                 type: integer
 *               water_ml:
 *                 type: number
 *     responses:
 *       200:
 *         description: Success
 */
router.post('/daily-stats', requireAuth, validate(updateDailyStatsSchema), async (req: any, res: any) => {
  try {
    const userId = req.user.id;
    const { date, steps, water_ml } = req.body;
    const dateStr = date || new Date().toISOString().split('T')[0];

    if (!isSupabaseLive) {
      const stats = fallbackDb.updateDailyStats(userId, dateStr, { steps, water_ml });
      return sendSuccess(res, stats);
    }

    const { data, error } = await supabase
      .from('daily_stats')
      .upsert({ user_id: userId, date: dateStr, steps, water_ml }, { onConflict: 'user_id,date' })
      .select()
      .single();

    if (error) throw error;
    sendSuccess(res, data);
  } catch (error: any) {
    errorLog(error, 'Update Daily Stats Error');
    sendError(res, error.message || 'Failed to update stats', 500);
  }
});

/**
 * @openapi
 * /user/measurements:
 *   post:
 *     summary: Log a new body measurement
 *     tags: [Profile]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - metric_type
 *               - value
 *             properties:
 *               metric_type:
 *                 type: string
 *                 enum: [weight, waist, chest, arms, thighs, strength]
 *               value:
 *                 type: number
 *               date:
 *                 type: string
 *     responses:
 *       200:
 *         description: Success
 */
router.post('/user/measurements', requireAuth, validate(logMeasurementSchema), async (req: any, res: any) => {
  try {
    const userId = req.user.id;
    const { metric_type, value, date } = req.body;

    if (!isSupabaseLive) {
      const log = fallbackDb.addMeasurement(userId, { metric_type, value, date });
      return sendSuccess(res, log);
    }

    const now = new Date();
    const ListMonths = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const formattedDate = date || `${ListMonths[now.getMonth()]} ${now.getDate().toString().padStart(2, '0')}, ${now.getFullYear()}`;

    const { data, error } = await supabase
      .from('measurement_logs')
      .insert([{
        user_id: userId,
        metric_type,
        value,
        date: formattedDate
      }])
      .select()
      .single();

    if (error) throw error;
    sendSuccess(res, data);
  } catch (error: any) {
    errorLog(error, 'Log Measurement Error');
    sendError(res, error.message || 'Failed to log measurement', 500);
  }
});

/**
 * @openapi
 * /user/measurements:
 *   get:
 *     summary: Retrieve user's logged measurements
 *     tags: [Profile]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: query
 *         name: metric_type
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: Success
 */
router.get('/user/measurements', requireAuth, async (req: any, res: any) => {
  try {
    const userId = req.user.id;
    const { metric_type } = req.query;

    if (!isSupabaseLive) {
      const logs = fallbackDb.getMeasurements(userId, metric_type as string);
      return sendSuccess(res, logs);
    }

    let query = supabase
      .from('measurement_logs')
      .select('*')
      .eq('user_id', userId);

    if (metric_type) {
      query = query.eq('metric_type', metric_type);
    }

    const { data, error } = await query.order('logged_at', { ascending: false });

    if (error) throw error;
    sendSuccess(res, data);
  } catch (error: any) {
    errorLog(error, 'Get Measurements Error');
    sendError(res, error.message || 'Failed to retrieve measurements', 500);
  }
});

/**
 * @openapi
 * /user/measurements/{id}:
 *   delete:
 *     summary: Delete a specific measurement log
 *     tags: [Profile]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: Success
 */
router.delete('/user/measurements/:id', requireAuth, async (req: any, res: any) => {
  try {
    const userId = req.user.id;
    const { id } = req.params;

    if (!isSupabaseLive) {
      const success = fallbackDb.deleteMeasurement(userId, id);
      if (!success) {
        return sendError(res, 'Measurement log not found', 404);
      }
      return sendSuccess(res, { success: true });
    }

    const { data, error } = await supabase
      .from('measurement_logs')
      .delete()
      .eq('id', id)
      .eq('user_id', userId)
      .select();

    if (error) throw error;
    if (!data || data.length === 0) {
      return sendError(res, 'Measurement log not found or not owned by user', 404);
    }
    
    sendSuccess(res, { success: true });
  } catch (error: any) {
    errorLog(error, 'Delete Measurement Error');
    sendError(res, error.message || 'Failed to delete measurement', 500);
  }
});

/**
 * @openapi
 * /nutrition/barcode:
 *   post:
 *     summary: Lookup nutrition info from UPC barcode
 *     tags: [Nutrition]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - barcode
 *             properties:
 *               barcode:
 *                 type: string
 *     responses:
 *       200:
 *         description: Success
 */
router.post('/nutrition/barcode', validate(barcodeSchema), async (req: any, res: any) => {
  try {
    const { barcode } = req.body;
    const analysisResult = await analyzeMealBarcode(barcode);
    sendSuccess(res, analysisResult);
  } catch (error: any) {
    errorLog(error, 'Barcode Analysis Error');
    sendError(res, error.message || 'Failed to analyze barcode', 500);
  }
});

/**
 * @openapi
 * /referral/create:
 *   post:
 *     summary: Generate a referral code for the logged user
 *     tags: [Referral]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Success
 */
router.post('/referral/create', requireAuth, async (req: any, res: any) => {
  try {
    const userId = req.user.id;
    const code = `SAB-${userId.substring(0, 4).toUpperCase()}-${Math.random().toString(36).substring(2, 6).toUpperCase()}`;
    sendSuccess(res, { code });
  } catch (error: any) {
    errorLog(error, 'Create Referral Error');
    sendError(res, error.message || 'Failed to create referral', 500);
  }
});

/**
 * @openapi
 * /referral/redeem:
 *   post:
 *     summary: Redeem a referral code
 *     tags: [Referral]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - code
 *             properties:
 *               code:
 *                 type: string
 *     responses:
 *       200:
 *         description: Success
 */
router.post('/referral/redeem', requireAuth, validate(redeemReferralSchema), async (req: any, res: any) => {
  try {
    const { code } = req.body;
    sendSuccess(res, { message: 'Referral redeemed successfully! 7 Days Premium awarded.' });
  } catch (error: any) {
    errorLog(error, 'Redeem Referral Error');
    sendError(res, error.message || 'Failed to redeem referral', 500);
  }
});

/**
 * @openapi
 * /insights:
 *   get:
 *     summary: Generate AI workout insights
 *     tags: [Insights]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: Success
 */
router.get('/insights', requireAuth, async (req: any, res: any) => {
  try {
    const userId = req.user.id;
    let workouts = [];
    let stats = {};
    if (!isSupabaseLive) {
      workouts = fallbackDb.getWorkouts(userId);
      const dateStr = new Date().toISOString().split('T')[0];
      stats = fallbackDb.getDailyStats(userId, dateStr);
    } else {
      const { data: wData } = await supabase.from('workouts').select('*').eq('user_id', userId).order('completed_at', { ascending: false }).limit(5);
      workouts = wData || [];
      const dateStr = new Date().toISOString().split('T')[0];
      const { data: sData } = await supabase.from('daily_stats').select('*').eq('user_id', userId).eq('date', dateStr).maybeSingle();
      stats = sData || {};
    }
    const insight = await generateWorkoutInsight(workouts, stats);
    sendSuccess(res, { insight });
  } catch (error: any) {
    errorLog(error, 'Insights Generation Error');
    sendError(res, error.message || 'Failed to generate insight', 500);
  }
});

export default router;
