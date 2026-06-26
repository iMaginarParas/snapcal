-- SABTRACK AI (FitFlow AI) Supabase Schema
-- Run this in your Supabase SQL Editor

-- Create extension for UUIDs if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users Table
CREATE TABLE IF NOT EXISTS public.users (
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
DROP POLICY IF EXISTS "Users can view own profile" ON public.users;
CREATE POLICY "Users can view own profile" ON public.users FOR SELECT USING (auth.uid() = id);
DROP POLICY IF EXISTS "Users can update own profile" ON public.users;
CREATE POLICY "Users can update own profile" ON public.users FOR UPDATE USING (auth.uid() = id);

-- Trigger to automatically create a user profile when they sign up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
  base_username TEXT;
  final_username TEXT;
  counter INT := 0;
BEGIN
  -- Extract prefix from email
  base_username := split_part(new.email, '@', 1);
  -- Sanitize base_username to be alphanumeric/underscores only
  base_username := regexp_replace(base_username, '[^a-zA-Z0-9_]', '', 'g');
  -- Fallback if empty
  IF base_username = '' THEN
    base_username := 'user';
  END IF;

  final_username := base_username;

  -- Ensure username is unique by appending counter if necessary
  WHILE EXISTS (SELECT 1 FROM public.users WHERE username = final_username) LOOP
    counter := counter + 1;
    final_username := base_username || counter::TEXT;
  END LOOP;

  INSERT INTO public.users (id, email, username)
  VALUES (new.id, new.email, final_username);
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- 2. Plans Table
CREATE TABLE IF NOT EXISTS public.plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    file_url TEXT,
    parsed_data JSONB,
    plan_type TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);
ALTER TABLE public.plans ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own plans" ON public.plans;
CREATE POLICY "Users can manage own plans" ON public.plans FOR ALL USING (auth.uid() = user_id);

-- 3. Daily Tasks Table
CREATE TABLE IF NOT EXISTS public.daily_tasks (
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
DROP POLICY IF EXISTS "Users can manage own tasks" ON public.daily_tasks;
CREATE POLICY "Users can manage own tasks" ON public.daily_tasks FOR ALL USING (auth.uid() = user_id);

-- 4. Meals Table
CREATE TABLE IF NOT EXISTS public.meals (
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
DROP POLICY IF EXISTS "Users can manage own meals" ON public.meals;
CREATE POLICY "Users can manage own meals" ON public.meals FOR ALL USING (auth.uid() = user_id);

-- 5. Workouts Table
CREATE TABLE IF NOT EXISTS public.workouts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    workout_name TEXT NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP WITH TIME ZONE
);
ALTER TABLE public.workouts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own workouts" ON public.workouts;
CREATE POLICY "Users can manage own workouts" ON public.workouts FOR ALL USING (auth.uid() = user_id);

-- 6. Workout Exercises Table
CREATE TABLE IF NOT EXISTS public.workout_exercises (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workout_id UUID REFERENCES public.workouts(id) ON DELETE CASCADE,
    exercise_name TEXT NOT NULL,
    sets INT NOT NULL,
    reps TEXT NOT NULL,
    completed BOOLEAN DEFAULT FALSE
);
ALTER TABLE public.workout_exercises ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage exercises" ON public.workout_exercises;
CREATE POLICY "Users can manage exercises" ON public.workout_exercises FOR ALL USING (true);


-- --- SABTRACK AI UPDATES (FitFlow AI) ---

-- 1. Alter users table to add profile_picture_url and unique username columns
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS profile_picture_url TEXT;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS username TEXT UNIQUE;

-- 2. Alter workouts table to support live GPS workout details and strength workouts
ALTER TABLE public.workouts ADD COLUMN IF NOT EXISTS distance NUMERIC;
ALTER TABLE public.workouts ADD COLUMN IF NOT EXISTS duration_seconds INT;
ALTER TABLE public.workouts ADD COLUMN IF NOT EXISTS calories INT;
ALTER TABLE public.workouts ADD COLUMN IF NOT EXISTS route_points JSONB;
ALTER TABLE public.workouts ADD COLUMN IF NOT EXISTS workout_type TEXT DEFAULT 'cardio';
ALTER TABLE public.workouts ADD COLUMN IF NOT EXISTS category TEXT;
ALTER TABLE public.workouts ADD COLUMN IF NOT EXISTS exercises JSONB;

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
DROP POLICY IF EXISTS "Users can manage own daily stats" ON public.daily_stats;
CREATE POLICY "Users can manage own daily stats" ON public.daily_stats FOR ALL USING (auth.uid() = user_id);

-- 4. Create Measurement Logs Table for body weight and measurements tracking
CREATE TABLE IF NOT EXISTS public.measurement_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    metric_type TEXT NOT NULL, -- 'weight', 'waist', 'chest', 'arms', 'thighs', 'strength'
    value NUMERIC NOT NULL,
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    date TEXT NOT NULL
);
ALTER TABLE public.measurement_logs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own measurements" ON public.measurement_logs;
CREATE POLICY "Users can manage own measurements" ON public.measurement_logs FOR ALL USING (auth.uid() = user_id);

-- 5. Create Fasting Logs Table
CREATE TABLE IF NOT EXISTS public.fasting_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    protocol TEXT NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);
ALTER TABLE public.fasting_logs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own fasting logs" ON public.fasting_logs;
CREATE POLICY "Users can manage own fasting logs" ON public.fasting_logs FOR ALL USING (auth.uid() = user_id);

-- 6. Create Groups Table
CREATE TABLE IF NOT EXISTS public.groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES public.users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 7. Create Group Members Table
CREATE TABLE IF NOT EXISTS public.group_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id UUID REFERENCES public.groups(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    UNIQUE(group_id, user_id)
);

-- RLS for Groups (Moved here to resolve circular dependency: groups policies query group_members, but group_members references groups)
ALTER TABLE public.groups ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can view public groups" ON public.groups;
CREATE POLICY "Users can view public groups" ON public.groups FOR SELECT USING (is_public = TRUE OR auth.uid() IN (SELECT user_id FROM public.group_members WHERE group_id = id));
DROP POLICY IF EXISTS "Users can manage own created groups" ON public.groups;
CREATE POLICY "Users can manage own created groups" ON public.groups FOR ALL USING (auth.uid() = created_by);

ALTER TABLE public.group_members ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Anyone can view group members" ON public.group_members;
CREATE POLICY "Anyone can view group members" ON public.group_members FOR SELECT USING (true);
DROP POLICY IF EXISTS "Users can join/leave groups" ON public.group_members;
CREATE POLICY "Users can join/leave groups" ON public.group_members FOR ALL USING (auth.uid() = user_id);

-- 8. Create Group Messages Table
CREATE TABLE IF NOT EXISTS public.group_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id UUID REFERENCES public.groups(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);
ALTER TABLE public.group_messages ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Members can view messages" ON public.group_messages;
CREATE POLICY "Members can view messages" ON public.group_messages FOR SELECT USING (true);
DROP POLICY IF EXISTS "Users can insert own messages" ON public.group_messages;
CREATE POLICY "Users can insert own messages" ON public.group_messages FOR INSERT WITH CHECK (auth.uid() = user_id);

-- 9. Create Friendships Table
CREATE TABLE IF NOT EXISTS public.friendships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    friend_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'accepted',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    UNIQUE(user_id, friend_id)
);
ALTER TABLE public.friendships ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own friendships" ON public.friendships;
CREATE POLICY "Users can manage own friendships" ON public.friendships FOR ALL USING (auth.uid() = user_id OR auth.uid() = friend_id);

-- 10. Create Challenges Table
CREATE TABLE IF NOT EXISTS public.challenges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT,
    target_workouts INT DEFAULT 5,
    points INT DEFAULT 500,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);
ALTER TABLE public.challenges ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Anyone can view challenges" ON public.challenges;
CREATE POLICY "Anyone can view challenges" ON public.challenges FOR SELECT USING (true);

-- 11. Create User Challenges Table
CREATE TABLE IF NOT EXISTS public.user_challenges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    challenge_id UUID REFERENCES public.challenges(id) ON DELETE CASCADE,
    completed_workouts INT DEFAULT 2,
    completed BOOLEAN DEFAULT FALSE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    UNIQUE(user_id, challenge_id)
);
ALTER TABLE public.user_challenges ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own enrollments" ON public.user_challenges;
CREATE POLICY "Users can manage own enrollments" ON public.user_challenges FOR ALL USING (auth.uid() = user_id);

-- Seed initial challenges
INSERT INTO public.challenges (title, description, target_workouts, points)
VALUES ('7-Day Core Crusher', 'Complete 5 core workouts this week to earn the exclusive Golden Abs badge.', 5, 500)
ON CONFLICT DO NOTHING;

-- Alter meals table to support optional text description / user note
ALTER TABLE public.meals ADD COLUMN IF NOT EXISTS description TEXT;

-- 12. Profiles Table
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

-- 13. Weight History Table
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


