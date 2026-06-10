-- SABTRACK AI (FitFlow AI) Supabase Schema
-- Run this in your Supabase SQL Editor

-- Create extension for UUIDs if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users Table
CREATE TABLE public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    age INT,
    weight NUMERIC,
    height NUMERIC,
    goals TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Set up Row Level Security (RLS)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own profile" ON public.users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON public.users FOR UPDATE USING (auth.uid() = id);

-- Trigger to automatically create a user profile when they sign up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, email)
  VALUES (new.id, new.email);
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- 2. Plans Table
CREATE TABLE public.plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    file_url TEXT,
    parsed_data JSONB,
    plan_type TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);
ALTER TABLE public.plans ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own plans" ON public.plans FOR ALL USING (auth.uid() = user_id);

-- 3. Daily Tasks Table
CREATE TABLE public.daily_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    task_type TEXT NOT NULL, -- 'meal', 'workout', 'water'
    title TEXT NOT NULL,
    description TEXT,
    scheduled_time TIME,
    completed BOOLEAN DEFAULT FALSE,
    date DATE NOT NULL DEFAULT CURRENT_DATE
);
ALTER TABLE public.daily_tasks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own tasks" ON public.daily_tasks FOR ALL USING (auth.uid() = user_id);

-- 4. Meals Table
CREATE TABLE public.meals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    calories INT NOT NULL,
    protein INT,
    carbs INT,
    fats INT,
    image_url TEXT,
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);
ALTER TABLE public.meals ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own meals" ON public.meals FOR ALL USING (auth.uid() = user_id);

-- 5. Workouts Table
CREATE TABLE public.workouts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    workout_name TEXT NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP WITH TIME ZONE
);
ALTER TABLE public.workouts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own workouts" ON public.workouts FOR ALL USING (auth.uid() = user_id);

-- 6. Workout Exercises Table
CREATE TABLE public.workout_exercises (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workout_id UUID REFERENCES public.workouts(id) ON DELETE CASCADE,
    exercise_name TEXT NOT NULL,
    sets INT NOT NULL,
    reps TEXT NOT NULL,
    completed BOOLEAN DEFAULT FALSE
);
ALTER TABLE public.workout_exercises ENABLE ROW LEVEL SECURITY;
-- For simplicity, users can manage all workout exercises (assuming backend ensures they belong to their workout)
CREATE POLICY "Users can manage exercises" ON public.workout_exercises FOR ALL USING (true);


-- --- SABTRACK AI UPDATES (FitFlow AI) ---

-- 1. Alter users table to add profile_picture_url column
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS profile_picture_url TEXT;

-- 2. Alter workouts table to support live GPS workout details
ALTER TABLE public.workouts ADD COLUMN IF NOT EXISTS distance NUMERIC;
ALTER TABLE public.workouts ADD COLUMN IF NOT EXISTS duration_seconds INT;
ALTER TABLE public.workouts ADD COLUMN IF NOT EXISTS calories INT;
ALTER TABLE public.workouts ADD COLUMN IF NOT EXISTS route_points JSONB;

-- 3. Create Daily Stats Table for steps and water logging
CREATE TABLE IF NOT EXISTS public.daily_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    steps INT DEFAULT 0,
    water_ml INT DEFAULT 0,
    UNIQUE(user_id, date)
);
ALTER TABLE public.daily_stats ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own daily stats" ON public.daily_stats FOR ALL USING (auth.uid() = user_id);
