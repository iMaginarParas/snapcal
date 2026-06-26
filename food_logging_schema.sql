-- Food Logging Schema Migrations for Supabase PostgreSQL
-- Run this script in the Supabase SQL Editor to support the AI Food Logging System.

-- 1. Create or alter Meals table to support fiber, and rename column fats if needed
ALTER TABLE public.meals ADD COLUMN IF NOT EXISTS total_calories INT;
ALTER TABLE public.meals ADD COLUMN IF NOT EXISTS protein NUMERIC;
ALTER TABLE public.meals ADD COLUMN IF NOT EXISTS carbs NUMERIC;
ALTER TABLE public.meals ADD COLUMN IF NOT EXISTS fat NUMERIC;
ALTER TABLE public.meals ADD COLUMN IF NOT EXISTS fiber NUMERIC DEFAULT 0.0;

-- Backfill total_calories, fat, protein, carbs from old columns if they exist
UPDATE public.meals SET total_calories = calories WHERE total_calories IS NULL AND calories IS NOT NULL;
UPDATE public.meals SET fat = fats WHERE fat IS NULL AND fats IS NOT NULL;

-- 2. Create Food Items Table
CREATE TABLE IF NOT EXISTS public.food_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meal_id UUID REFERENCES public.meals(id) ON DELETE CASCADE,
    food_name TEXT NOT NULL,
    weight NUMERIC NOT NULL,
    calories INT NOT NULL,
    protein NUMERIC NOT NULL,
    carbs NUMERIC NOT NULL,
    fat NUMERIC NOT NULL,
    fiber NUMERIC NOT NULL,
    confidence NUMERIC NOT NULL,
    cooking_method TEXT,
    ingredients JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Enable RLS on food_items
ALTER TABLE public.food_items ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own food items" ON public.food_items;
CREATE POLICY "Users can manage own food items" ON public.food_items FOR ALL USING (
    EXISTS (
        SELECT 1 FROM public.meals 
        WHERE public.meals.id = public.food_items.meal_id 
        AND public.meals.user_id = auth.uid()
    )
);

-- 3. Create User Corrections Table (Learning system)
CREATE TABLE IF NOT EXISTS public.user_corrections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    original_name TEXT NOT NULL,
    corrected_name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Enable RLS on user_corrections
ALTER TABLE public.user_corrections ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own corrections" ON public.user_corrections;
CREATE POLICY "Users can manage own corrections" ON public.user_corrections FOR ALL USING (auth.uid() = user_id);
