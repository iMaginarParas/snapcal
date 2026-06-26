-- SABTRACK AI - AI Food Logging System Migrations
-- Run this in your Supabase SQL Editor

-- 1. Create Foods Table
CREATE TABLE IF NOT EXISTS public.foods (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    calories INT NOT NULL,
    protein NUMERIC NOT NULL,
    carbs NUMERIC NOT NULL,
    fat NUMERIC NOT NULL,
    fiber NUMERIC NOT NULL DEFAULT 0.0,
    sugar NUMERIC DEFAULT 0.0,
    sodium NUMERIC DEFAULT 0.0,
    serving_size_g NUMERIC DEFAULT 100.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Enable RLS on foods
ALTER TABLE public.foods ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow public read access to foods" ON public.foods;
CREATE POLICY "Allow public read access to foods" ON public.foods FOR SELECT USING (true);

-- 2. Create Food Aliases Table
CREATE TABLE IF NOT EXISTS public.food_aliases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alias TEXT UNIQUE NOT NULL,
    standard_name TEXT REFERENCES public.foods(name) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Enable RLS on food_aliases
ALTER TABLE public.food_aliases ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow public read access to food_aliases" ON public.food_aliases;
CREATE POLICY "Allow public read access to food_aliases" ON public.food_aliases FOR SELECT USING (true);

-- 3. Create Nutrition Cache Table
CREATE TABLE IF NOT EXISTS public.nutrition_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    food_name TEXT UNIQUE NOT NULL,
    weight NUMERIC NOT NULL,
    calories INT NOT NULL,
    protein NUMERIC NOT NULL,
    carbs NUMERIC NOT NULL,
    fat NUMERIC NOT NULL,
    fiber NUMERIC NOT NULL DEFAULT 0.0,
    sodium NUMERIC DEFAULT 0.0,
    serving_size TEXT,
    source TEXT NOT NULL, -- 'FatSecret', 'USDA', 'IndianFoodDB', 'Manual'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Enable RLS on nutrition_cache
ALTER TABLE public.nutrition_cache ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow read access to nutrition_cache" ON public.nutrition_cache;
CREATE POLICY "Allow read access to nutrition_cache" ON public.nutrition_cache FOR SELECT USING (true);
DROP POLICY IF EXISTS "Allow system write to nutrition_cache" ON public.nutrition_cache;
CREATE POLICY "Allow system write to nutrition_cache" ON public.nutrition_cache FOR INSERT WITH CHECK (true);

-- 4. Create Barcode Cache Table
CREATE TABLE IF NOT EXISTS public.barcode_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    barcode TEXT UNIQUE NOT NULL,
    food_name TEXT NOT NULL,
    calories INT NOT NULL,
    protein NUMERIC NOT NULL,
    carbs NUMERIC NOT NULL,
    fat NUMERIC NOT NULL,
    fiber NUMERIC NOT NULL DEFAULT 0.0,
    sodium NUMERIC DEFAULT 0.0,
    serving_size TEXT,
    source TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Enable RLS on barcode_cache
ALTER TABLE public.barcode_cache ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow read access to barcode_cache" ON public.barcode_cache;
CREATE POLICY "Allow read access to barcode_cache" ON public.barcode_cache FOR SELECT USING (true);
DROP POLICY IF EXISTS "Allow system write to barcode_cache" ON public.barcode_cache;
CREATE POLICY "Allow system write to barcode_cache" ON public.barcode_cache FOR INSERT WITH CHECK (true);

-- 5. Create Food Corrections Table (Learning System)
CREATE TABLE IF NOT EXISTS public.food_corrections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    original_name TEXT NOT NULL,
    corrected_name TEXT NOT NULL,
    corrected_weight NUMERIC,
    corrected_cooking_method TEXT,
    corrected_serving TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Enable RLS on food_corrections
ALTER TABLE public.food_corrections ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own food corrections" ON public.food_corrections;
CREATE POLICY "Users can manage own food corrections" ON public.food_corrections FOR ALL USING (auth.uid() = user_id);

-- 6. Create Favorite Foods Table
CREATE TABLE IF NOT EXISTS public.favorite_foods (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    food_name TEXT NOT NULL,
    calories INT,
    protein NUMERIC,
    carbs NUMERIC,
    fat NUMERIC,
    fiber NUMERIC DEFAULT 0.0,
    serving_size_g NUMERIC,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    UNIQUE(user_id, food_name)
);

-- Enable RLS on favorite_foods
ALTER TABLE public.favorite_foods ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own favorite foods" ON public.favorite_foods;
CREATE POLICY "Users can manage own favorite foods" ON public.favorite_foods FOR ALL USING (auth.uid() = user_id);

-- 7. Create Recent Foods Table
CREATE TABLE IF NOT EXISTS public.recent_foods (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    food_name TEXT NOT NULL,
    last_logged_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    UNIQUE(user_id, food_name)
);

-- Enable RLS on recent_foods
ALTER TABLE public.recent_foods ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own recent foods" ON public.recent_foods;
CREATE POLICY "Users can manage own recent foods" ON public.recent_foods FOR ALL USING (auth.uid() = user_id);

-- 8. Create Meal Templates Table
CREATE TABLE IF NOT EXISTS public.meal_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    template_name TEXT NOT NULL,
    foods JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Enable RLS on meal_templates
ALTER TABLE public.meal_templates ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own meal templates" ON public.meal_templates;
CREATE POLICY "Users can manage own meal templates" ON public.meal_templates FOR ALL USING (auth.uid() = user_id);

-- 9. Update existing meals table with newer columns for caching
ALTER TABLE public.meals ADD COLUMN IF NOT EXISTS meal_type TEXT;
ALTER TABLE public.meals ADD COLUMN IF NOT EXISTS total_weight NUMERIC DEFAULT 0.0;
ALTER TABLE public.meals ADD COLUMN IF NOT EXISTS total_calories INT;
ALTER TABLE public.meals ADD COLUMN IF NOT EXISTS protein NUMERIC;
ALTER TABLE public.meals ADD COLUMN IF NOT EXISTS carbs NUMERIC;
ALTER TABLE public.meals ADD COLUMN IF NOT EXISTS fat NUMERIC;
ALTER TABLE public.meals ADD COLUMN IF NOT EXISTS fiber NUMERIC DEFAULT 0.0;

-- 10. Update existing food_items table with newer columns
ALTER TABLE public.food_items ADD COLUMN IF NOT EXISTS normalized_name TEXT;
ALTER TABLE public.food_items ADD COLUMN IF NOT EXISTS weight NUMERIC;
ALTER TABLE public.food_items ADD COLUMN IF NOT EXISTS serving TEXT;
ALTER TABLE public.food_items ADD COLUMN IF NOT EXISTS hidden_ingredients JSONB;

-- 11. Create Daily Steps Table
CREATE TABLE IF NOT EXISTS public.daily_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    sensor_steps INT DEFAULT 0,
    health_connect_steps INT DEFAULT 0,
    final_steps INT DEFAULT 0,
    distance NUMERIC DEFAULT 0.0,
    calories INT DEFAULT 0,
    active_minutes INT DEFAULT 0,
    baseline INT DEFAULT 0,
    last_sensor_value INT DEFAULT 0,
    last_sync TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    UNIQUE(user_id, date)
);

-- Enable RLS on daily_steps
ALTER TABLE public.daily_steps ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own steps" ON public.daily_steps;
CREATE POLICY "Users can manage own steps" ON public.daily_steps FOR ALL USING (auth.uid() = user_id);

-- 9. Profiles Table
CREATE TABLE IF NOT EXISTS public.profiles (
    user_id UUID PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,
    age INT,
    gender TEXT,
    height_cm NUMERIC,
    current_weight NUMERIC,
    target_weight NUMERIC,
    activity_level TEXT,
    goal TEXT,
    bmi NUMERIC,
    bmi_category TEXT,
    bmr NUMERIC,
    tdee NUMERIC,
    target_calories INT,
    protein_target INT,
    carb_target INT,
    fat_target INT,
    fiber_target INT,
    water_target INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own profile details" ON public.profiles;
CREATE POLICY "Users can manage own profile details" ON public.profiles FOR ALL USING (auth.uid() = user_id);

-- 10. Weight History Table
CREATE TABLE IF NOT EXISTS public.weight_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    weight NUMERIC NOT NULL,
    bmi NUMERIC NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

ALTER TABLE public.weight_history ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own weight history" ON public.weight_history;
CREATE POLICY "Users can manage own weight history" ON public.weight_history FOR ALL USING (auth.uid() = user_id);

