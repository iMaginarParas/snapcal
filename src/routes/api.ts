import { Router } from 'express';
import multer from 'multer';
import fs from 'fs';
import path from 'path';
import { analyzeMealImage, generateMockMeal, analyzeMealText, analyzeMealLabel, analyzeMealBarcode } from '../services/gemini';
import { supabase } from '../services/supabase';
import { fallbackDb } from '../services/db_fallback';

const router = Router();
const isSupabaseLive = process.env.SUPABASE_URL && !process.env.SUPABASE_URL.includes('placeholder-url');

// Configure multer for memory storage
const upload = multer({ storage: multer.memoryStorage() });

// --- Authentication ---

router.post('/auth/signup', async (req: any, res: any) => {
  try {
    const { email, password } = req.body;
    if (!email || !password) {
      return res.status(400).json({ success: false, error: 'Email and password are required' });
    }

    if (!isSupabaseLive) {
      // Offline fallback
      const mockId = email.replace(/[^a-zA-Z0-9]/g, '_');
      fallbackDb.getUser(mockId);
      fallbackDb.updateUser(mockId, { email });
      return res.status(201).json({
        success: true,
        token: `mock-user-${mockId}`,
        user: { id: mockId, email }
      });
    }

    const { data, error } = await supabase.auth.signUp({
      email,
      password,
    });

    if (error) {
      return res.status(400).json({ success: false, error: error.message });
    }

    res.status(201).json({
      success: true,
      token: data.session?.access_token || null,
      user: data.user,
    });
  } catch (error: any) {
    console.error('Signup Error:', error);
    res.status(500).json({ success: false, error: error.message || 'Internal server error' });
  }
});

router.post('/auth/login', async (req: any, res: any) => {
  try {
    const { email, password } = req.body;
    if (!email || !password) {
      return res.status(400).json({ success: false, error: 'Email and password are required' });
    }

    if (!isSupabaseLive) {
      // Offline fallback
      const mockId = email.replace(/[^a-zA-Z0-9]/g, '_');
      fallbackDb.getUser(mockId);
      fallbackDb.updateUser(mockId, { email });
      return res.status(200).json({
        success: true,
        token: `mock-user-${mockId}`,
        user: { id: mockId, email }
      });
    }

    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      return res.status(400).json({ success: false, error: error.message });
    }

    res.status(200).json({
      success: true,
      token: data.session?.access_token || null,
      user: data.user,
    });
  } catch (error: any) {
    console.error('Login Error:', error);
    res.status(500).json({ success: false, error: error.message || 'Internal server error' });
  }
});

router.post('/auth/google-login', async (req: any, res: any) => {
  try {
    const { idToken } = req.body;
    if (!idToken) {
      return res.status(400).json({ success: false, error: 'Google ID Token is required' });
    }

    if (!isSupabaseLive) {
      // Offline fallback
      const mockId = 'google_user_' + Math.random().toString(36).substring(2, 7);
      return res.status(200).json({
        success: true,
        token: `mock-user-${mockId}`,
        user: { id: mockId, email: `${mockId}@gmail.com` }
      });
    }

    const { data, error } = await supabase.auth.signInWithIdToken({
      provider: 'google',
      token: idToken,
    });

    if (error) {
      return res.status(400).json({ success: false, error: error.message });
    }

    res.status(200).json({
      success: true,
      token: data.session?.access_token || null,
      user: data.user,
    });
  } catch (error: any) {
    console.error('Google Login Error:', error);
    res.status(500).json({ success: false, error: error.message || 'Internal server error' });
  }
});

// Helper function to save meal to Supabase if authenticated
async function saveMealToDb(authHeader: string | undefined, analysisResult: any) {
  if (authHeader && authHeader.startsWith('Bearer ')) {
    const token = authHeader.split(' ')[1];
    try {
      const { data: { user }, error: userError } = await supabase.auth.getUser(token);
      
      if (!userError && user) {
        const { error: dbError } = await supabase
          .from('meals')
          .insert([
            {
              user_id: user.id,
              name: analysisResult.name,
              calories: analysisResult.calories,
              protein: analysisResult.protein || 0,
              carbs: analysisResult.carbs || 0,
              fats: analysisResult.fats || 0
            }
          ]);
        
        if (dbError) {
          console.error('Failed to save meal to Supabase:', dbError);
        }
      }
    } catch (err) {
      console.error('Supabase Auth error during meal save:', err);
    }
  }
}

// --- Smart Nutrition (Cal AI Feature) ---

router.post('/nutrition/analyze', upload.single('image'), async (req: any, res: any) => {
  try {
    let analysisResult;

    if (req.file) {
      // Analyze uploaded image
      const base64Image = req.file.buffer.toString('base64');
      const mimeType = req.file.mimetype;
      analysisResult = await analyzeMealImage(mimeType, base64Image);
    } else if (req.body.mockImage === true || req.body.mockImage === 'true') {
      // Generate a dynamic mock healthy meal via Gemini
      analysisResult = await generateMockMeal();
    } else {
      return res.status(400).json({ success: false, error: 'No image uploaded or mockImage flag set' });
    }

    // Save to database if authenticated
    await saveMealToDb(req.headers.authorization, analysisResult);

    res.json({
      success: true,
      data: analysisResult
    });
  } catch (error: any) {
    console.error('Analyze Nutrition Error:', error);
    res.status(500).json({ success: false, error: error.message || 'Internal server error' });
  }
});

// --- Text-based Nutrition Analysis ---
router.post('/nutrition/describe', async (req: any, res: any) => {
  try {
    const { description } = req.body;
    if (!description) {
      return res.status(400).json({ success: false, error: 'Meal description is required' });
    }

    const analysisResult = await analyzeMealText(description);

    // Save to database if authenticated
    await saveMealToDb(req.headers.authorization, analysisResult);

    res.json({
      success: true,
      data: analysisResult
    });
  } catch (error: any) {
    console.error('Describe Nutrition Error:', error);
    res.status(500).json({ success: false, error: error.message || 'Internal server error' });
  }
});

// --- Nutrition Label Analysis ---
router.post('/nutrition/analyze-label', upload.single('image'), async (req: any, res: any) => {
  try {
    let analysisResult;

    if (req.file) {
      const base64Image = req.file.buffer.toString('base64');
      const mimeType = req.file.mimetype;
      analysisResult = await analyzeMealLabel(mimeType, base64Image);
    } else if (req.body.mockImage === true || req.body.mockImage === 'true') {
      // Return a mockup label analysis for testing/guest mode
      analysisResult = {
        name: "Commercial Protein Bar (Label Scan)",
        calories: 220,
        protein: 20,
        carbs: 24,
        fats: 7
      };
    } else {
      return res.status(400).json({ success: false, error: 'No image uploaded or mockImage flag set' });
    }

    // Save to database if authenticated
    await saveMealToDb(req.headers.authorization, analysisResult);

    res.json({
      success: true,
      data: analysisResult
    });
  } catch (error: any) {
    console.error('Analyze Label Error:', error);
    res.status(500).json({ success: false, error: error.message || 'Internal server error' });
  }
});


// Keep /analyze-meal for backward compatibility
router.post('/analyze-meal', upload.single('image'), async (req: any, res: any) => {
  try {
    const file = req.file;
    if (!file) {
      return res.status(400).json({ error: 'No image uploaded' });
    }

    const base64Image = file.buffer.toString('base64');
    const mimeType = file.mimetype;

    const analysisResult = await analyzeMealImage(mimeType, base64Image);

    res.json({
      success: true,
      data: analysisResult
    });
  } catch (error: any) {
    console.error('Analyze Meal Error:', error);
    res.status(500).json({ success: false, error: error.message || 'Internal server error' });
  }
});

// --- Middleware & Premium Features API Implementation ---

export async function requireAuth(req: any, res: any, next: any) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ success: false, error: 'Authorization header is required' });
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
        return res.status(401).json({ success: false, error: 'Invalid Supabase authorization token' });
      }
      req.user = user;
      return next();
    } catch (e: any) {
      return res.status(401).json({ success: false, error: e.message || 'Authentication error' });
    }
  } else {
    req.user = { id: token, email: `${token}@fallback.local` };
    return next();
  }
}

// 1. Get User Profile
router.get('/user/profile', requireAuth, async (req: any, res: any) => {
  try {
    const userId = req.user.id;
    if (!isSupabaseLive) {
      const profile = fallbackDb.getUser(userId);
      return res.json({ success: true, data: profile });
    }

    const { data, error } = await supabase
      .from('users')
      .select('*')
      .eq('id', userId)
      .single();

    if (error) {
      // If profile does not exist yet (but auth user does), insert a default one
      const defaultProfile = { id: userId, email: req.user.email, name: 'Guest User', age: 25, weight: 76.4, height: 178, goals: 'Build Muscle' };
      const { data: newProfile, error: insertError } = await supabase
        .from('users')
        .insert([defaultProfile])
        .select()
        .single();
      
      if (insertError) throw insertError;
      return res.json({ success: true, data: newProfile });
    }

    res.json({ success: true, data });
  } catch (error: any) {
    console.error('Get Profile Error:', error);
    res.status(500).json({ success: false, error: error.message || 'Failed to retrieve profile' });
  }
});

// 2. Update User Profile
router.put('/user/profile', requireAuth, async (req: any, res: any) => {
  try {
    const userId = req.user.id;
    const { name, age, weight, height, goals } = req.body;

    if (!isSupabaseLive) {
      const updated = fallbackDb.updateUser(userId, { name, age: parseInt(age) || 25, weight: parseFloat(weight) || 76.4, height: parseFloat(height) || 178, goals });
      return res.json({ success: true, data: updated });
    }

    const { data, error } = await supabase
      .from('users')
      .update({ name, age: parseInt(age) || 25, weight: parseFloat(weight) || 76.4, height: parseFloat(height) || 178, goals })
      .eq('id', userId)
      .select()
      .single();

    if (error) throw error;
    res.json({ success: true, data });
  } catch (error: any) {
    console.error('Update Profile Error:', error);
    res.status(500).json({ success: false, error: error.message || 'Failed to update profile' });
  }
});

// 3. Upload User Profile Picture (Supabase storage with local fallback)
router.post('/user/profile/picture', requireAuth, upload.single('image'), async (req: any, res: any) => {
  try {
    const userId = req.user.id;
    if (!req.file) {
      return res.status(400).json({ success: false, error: 'No image file uploaded' });
    }

    const fileBuffer = req.file.buffer;
    const extension = req.file.originalname.split('.').pop() || 'jpg';
    const fileName = `${userId}-${Date.now()}.${extension}`;
    let profilePictureUrl = '';

    if (isSupabaseLive) {
      try {
        // Try uploading to Supabase Storage Bucket 'profile-pictures'
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
          console.warn('Supabase bucket upload failed, using local server storage fallback:', uploadError.message);
        }
      } catch (err) {
        console.warn('Supabase bucket error, falling back locally:', err);
      }
    }

    // Fallback locally if Supabase is offline, bucket doesn't exist, or bucket upload failed
    if (!profilePictureUrl) {
      const localPath = path.join(__dirname, '../../uploads', fileName);
      fs.writeFileSync(localPath, fileBuffer);
      // Construct local server static url
      profilePictureUrl = `${req.protocol}://${req.get('host')}/uploads/${fileName}`;
    }

    // Save URL to users table
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
    console.error('Upload Profile Picture Error:', error);
    res.status(500).json({ success: false, error: error.message || 'Failed to upload picture' });
  }
});

// 4. Meals Endpoints (Fetch & Log)
router.get('/meals', requireAuth, async (req: any, res: any) => {
  try {
    const userId = req.user.id;
    if (!isSupabaseLive) {
      const meals = fallbackDb.getMeals(userId);
      return res.json({ success: true, data: meals });
    }

    const { data, error } = await supabase
      .from('meals')
      .select('*')
      .eq('user_id', userId)
      .order('logged_at', { ascending: false });

    if (error) throw error;
    res.json({ success: true, data });
  } catch (error: any) {
    res.status(500).json({ success: false, error: error.message || 'Failed to retrieve meals' });
  }
});

router.post('/meals', requireAuth, async (req: any, res: any) => {
  try {
    const userId = req.user.id;
    const { name, calories, protein, carbs, fats } = req.body;

    if (!name || calories === undefined) {
      return res.status(400).json({ success: false, error: 'Name and calories are required' });
    }

    if (!isSupabaseLive) {
      const meal = fallbackDb.addMeal(userId, { name, calories, protein, carbs, fats });
      return res.json({ success: true, data: meal });
    }

    const { data, error } = await supabase
      .from('meals')
      .insert([{ user_id: userId, name, calories, protein, carbs, fats }])
      .select()
      .single();

    if (error) throw error;
    res.json({ success: true, data });
  } catch (error: any) {
    res.status(500).json({ success: false, error: error.message || 'Failed to log meal' });
  }
});

// 5. Workouts Endpoints (Fetch & Log)
router.get('/workouts', requireAuth, async (req: any, res: any) => {
  try {
    const userId = req.user.id;
    if (!isSupabaseLive) {
      const workouts = fallbackDb.getWorkouts(userId);
      return res.json({ success: true, data: workouts });
    }

    const { data, error } = await supabase
      .from('workouts')
      .select('*')
      .eq('user_id', userId)
      .order('completed_at', { ascending: false });

    if (error) throw error;
    res.json({ success: true, data });
  } catch (error: any) {
    res.status(500).json({ success: false, error: error.message || 'Failed to retrieve workouts' });
  }
});

router.post('/workouts', requireAuth, async (req: any, res: any) => {
  try {
    const userId = req.user.id;
    const { workout_name, distance, duration_seconds, calories, route_points } = req.body;

    if (!workout_name) {
      return res.status(400).json({ success: false, error: 'Workout name is required' });
    }

    if (!isSupabaseLive) {
      const workout = fallbackDb.addWorkout(userId, { workout_name, distance, duration_seconds, calories, route_points });
      return res.json({ success: true, data: workout });
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
    res.json({ success: true, data });
  } catch (error: any) {
    console.error('Log Workout Error:', error);
    res.status(500).json({ success: false, error: error.message || 'Failed to save workout' });
  }
});

// 6. Daily Stats (Steps & Water Sync)
router.get('/daily-stats', requireAuth, async (req: any, res: any) => {
  try {
    const userId = req.user.id;
    const dateStr = req.query.date || new Date().toISOString().split('T')[0];

    if (!isSupabaseLive) {
      const stats = fallbackDb.getDailyStats(userId, dateStr);
      return res.json({ success: true, data: stats });
    }

    const { data, error } = await supabase
      .from('daily_stats')
      .select('*')
      .eq('user_id', userId)
      .eq('date', dateStr)
      .maybeSingle();

    if (error) throw error;
    
    if (!data) {
      // Create a default row for today if not present
      const { data: newStats, error: createError } = await supabase
        .from('daily_stats')
        .insert([{ user_id: userId, date: dateStr, steps: 0, water_ml: 0 }])
        .select()
        .single();
      if (createError) throw createError;
      return res.json({ success: true, data: newStats });
    }

    res.json({ success: true, data });
  } catch (error: any) {
    res.status(500).json({ success: false, error: error.message || 'Failed to retrieve stats' });
  }
});

router.post('/daily-stats', requireAuth, async (req: any, res: any) => {
  try {
    const userId = req.user.id;
    const { date, steps, water_ml } = req.body;
    const dateStr = date || new Date().toISOString().split('T')[0];

    if (!isSupabaseLive) {
      const stats = fallbackDb.updateDailyStats(userId, dateStr, { steps, water_ml });
      return res.json({ success: true, data: stats });
    }

    // Upsert into daily_stats
    const { data, error } = await supabase
      .from('daily_stats')
      .upsert({ user_id: userId, date: dateStr, steps, water_ml }, { onConflict: 'user_id,date' })
      .select()
      .single();

    if (error) throw error;
    res.json({ success: true, data });
  } catch (error: any) {
    res.status(500).json({ success: false, error: error.message || 'Failed to update stats' });
  }
});

// 7. AI Barcode Nutrition Recognition
router.post('/nutrition/barcode', async (req: any, res: any) => {
  try {
    const { barcode } = req.body;
    if (!barcode) {
      return res.status(400).json({ success: false, error: 'Barcode is required' });
    }

    const analysisResult = await analyzeMealBarcode(barcode);
    res.json({ success: true, data: analysisResult });
  } catch (error: any) {
    console.error('Barcode Analysis Error:', error);
    res.status(500).json({ success: false, error: error.message || 'Failed to analyze barcode' });
  }
});

export default router;

