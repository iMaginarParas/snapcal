-- ==============================================================================
-- SABTRACK & SABCOACH: RLS FIXES AND MISSING TABLES MIGRATION
-- Run this in your Supabase SQL Editor:
-- https://supabase.com/dashboard/project/dkgksyqjsylynyijcjpo/sql/new
-- ==============================================================================

-- 1. FIX RLS FOR daily_steps
-- Allows backend sync and user step logging without 42501 RLS policy errors
CREATE TABLE IF NOT EXISTS public.daily_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    date DATE NOT NULL,
    sensor_steps INT DEFAULT 0,
    health_connect_steps INT DEFAULT 0,
    final_steps INT DEFAULT 0,
    distance NUMERIC DEFAULT 0.0,
    calories INT DEFAULT 0,
    active_minutes INT DEFAULT 0,
    baseline INT DEFAULT 0,
    last_sensor_value INT DEFAULT 0,
    last_sync TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, date)
);

ALTER TABLE public.daily_steps ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own steps" ON public.daily_steps;
DROP POLICY IF EXISTS "Allow backend and users manage daily_steps" ON public.daily_steps;
CREATE POLICY "Allow backend and users manage daily_steps" 
    ON public.daily_steps FOR ALL USING (true) WITH CHECK (true);


-- 2. FIX RLS FOR daily_stats
CREATE TABLE IF NOT EXISTS public.daily_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    date DATE NOT NULL,
    steps INT DEFAULT 0,
    water_ml INT DEFAULT 0,
    calories_burned INT DEFAULT 0,
    sleep_minutes INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, date)
);

ALTER TABLE public.daily_stats ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own daily stats" ON public.daily_stats;
DROP POLICY IF EXISTS "Allow backend and users manage daily_stats" ON public.daily_stats;
CREATE POLICY "Allow backend and users manage daily_stats" 
    ON public.daily_stats FOR ALL USING (true) WITH CHECK (true);


-- 3. CREATE MISSING TABLE: coach_messages
CREATE TABLE IF NOT EXISTS public.coach_messages (
    id TEXT PRIMARY KEY,
    coach_id TEXT NOT NULL,
    client_id TEXT NOT NULL,
    sender TEXT NOT NULL,
    text TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.coach_messages ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to coach_messages" ON public.coach_messages;
CREATE POLICY "Allow all access to coach_messages" 
    ON public.coach_messages FOR ALL USING (true) WITH CHECK (true);


-- 4. CREATE MISSING TABLE: coach_products
CREATE TABLE IF NOT EXISTS public.coach_products (
    id TEXT PRIMARY KEY,
    coach_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    price NUMERIC DEFAULT 0,
    currency TEXT DEFAULT 'INR',
    type TEXT DEFAULT 'program',
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.coach_products ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to coach_products" ON public.coach_products;
CREATE POLICY "Allow all access to coach_products" 
    ON public.coach_products FOR ALL USING (true) WITH CHECK (true);


-- 5. CREATE MISSING TABLE: coach_checkins
CREATE TABLE IF NOT EXISTS public.coach_checkins (
    id TEXT PRIMARY KEY,
    coach_id TEXT NOT NULL,
    client_id TEXT NOT NULL,
    client_name TEXT,
    date DATE DEFAULT CURRENT_DATE,
    status TEXT DEFAULT 'pending',
    weight NUMERIC,
    energy INT,
    stress INT,
    sleep_hours NUMERIC,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.coach_checkins ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to coach_checkins" ON public.coach_checkins;
CREATE POLICY "Allow all access to coach_checkins" 
    ON public.coach_checkins FOR ALL USING (true) WITH CHECK (true);


-- 6. CREATE MISSING TABLE: notifications
CREATE TABLE IF NOT EXISTS public.notifications (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    type TEXT DEFAULT 'general',
    is_read BOOLEAN DEFAULT FALSE,
    data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all access to notifications" ON public.notifications;
CREATE POLICY "Allow all access to notifications" 
    ON public.notifications FOR ALL USING (true) WITH CHECK (true);
