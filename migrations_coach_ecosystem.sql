-- =====================================================================
-- SABCOACH AI ECOSYSTEM: FULL SUPABASE POSTGRESQL SCHEMA
-- =====================================================================
-- Run this script in the Supabase SQL Editor (Dashboard -> SQL Editor)
-- to create all tables for Clients, Sessions, Workouts, Programs,
-- Invoices/Payments, CRM Leads, Community Groups, Challenges,
-- Availability, Reports, and Event Automations with Row Level Security (RLS).
-- =====================================================================

-- 1. COACH CLIENTS TABLE
CREATE TABLE IF NOT EXISTS public.coach_clients (
    id TEXT PRIMARY KEY,
    coach_id TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    avatar TEXT,
    status TEXT NOT NULL DEFAULT 'On Track',
    goal TEXT,
    target_cals INTEGER DEFAULT 2000,
    package TEXT,
    join_date TEXT,
    sabtrack_data JSONB DEFAULT '{}'::jsonb,
    notes JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. COACH SESSIONS TABLE
CREATE TABLE IF NOT EXISTS public.coach_sessions (
    id TEXT PRIMARY KEY,
    coach_id TEXT NOT NULL,
    client_id TEXT,
    client_name TEXT NOT NULL,
    client_avatar TEXT,
    title TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    duration TEXT DEFAULT '45 min',
    type TEXT DEFAULT '1:1 Coaching',
    status TEXT DEFAULT 'Scheduled',
    location TEXT DEFAULT 'Virtual / Video Call',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. COACH WORKOUTS TABLE
CREATE TABLE IF NOT EXISTS public.coach_workouts (
    id TEXT PRIMARY KEY,
    coach_id TEXT NOT NULL,
    client_id TEXT,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'Strength',
    difficulty TEXT DEFAULT 'Intermediate',
    duration TEXT DEFAULT '45 min',
    playlist_url TEXT,
    exercises JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. COACH PROGRAMS TABLE
CREATE TABLE IF NOT EXISTS public.coach_programs (
    id TEXT PRIMARY KEY,
    coach_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    duration_weeks INTEGER DEFAULT 12,
    difficulty TEXT DEFAULT 'Intermediate',
    category TEXT DEFAULT 'Hypertrophy',
    schedule JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. COACH PAYMENTS & INVOICES TABLE
CREATE TABLE IF NOT EXISTS public.coach_payments (
    id TEXT PRIMARY KEY,
    coach_id TEXT NOT NULL,
    client_id TEXT,
    client_name TEXT NOT NULL,
    package_name TEXT NOT NULL,
    amount NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    currency TEXT DEFAULT 'INR (₹)',
    status TEXT DEFAULT 'Pending',
    due_date TEXT,
    paid_date TEXT,
    invoice_number TEXT,
    payment_method TEXT DEFAULT 'UPI / Razorpay',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. COACH LEADS & CRM PIPELINE TABLE
CREATE TABLE IF NOT EXISTS public.coach_leads (
    id TEXT PRIMARY KEY,
    coach_id TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    stage TEXT DEFAULT 'New',
    goal TEXT,
    source TEXT DEFAULT 'Instagram',
    value NUMERIC(10,2) DEFAULT 0.00,
    notes TEXT,
    assigned_coach TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. COACH COMMUNITY GROUPS TABLE
CREATE TABLE IF NOT EXISTS public.coach_groups (
    id TEXT PRIMARY KEY,
    coach_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'General',
    image_url TEXT,
    members_count INTEGER DEFAULT 1,
    posts JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. COACH CHALLENGES TABLE
CREATE TABLE IF NOT EXISTS public.coach_challenges (
    id TEXT PRIMARY KEY,
    coach_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'Fitness',
    start_date TEXT,
    end_date TEXT,
    prize TEXT,
    participants JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 9. COACH AVAILABILITY TABLE
CREATE TABLE IF NOT EXISTS public.coach_availability (
    id TEXT PRIMARY KEY,
    coach_id TEXT NOT NULL,
    day TEXT NOT NULL,
    enabled BOOLEAN DEFAULT true,
    slots JSONB DEFAULT '[]'::jsonb,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 10. COACH REPORTS TABLE
CREATE TABLE IF NOT EXISTS public.coach_reports (
    id TEXT PRIMARY KEY,
    coach_id TEXT NOT NULL,
    client_id TEXT,
    client_name TEXT NOT NULL,
    period TEXT DEFAULT 'Monthly',
    summary JSONB DEFAULT '{}'::jsonb,
    coach_notes TEXT,
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 11. COACH AUTOMATIONS TABLE
CREATE TABLE IF NOT EXISTS public.coach_automations (
    id TEXT PRIMARY KEY,
    coach_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    trigger TEXT NOT NULL,
    action TEXT NOT NULL,
    active BOOLEAN DEFAULT true,
    execution_count INTEGER DEFAULT 0,
    last_triggered TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================================
-- ROW-LEVEL SECURITY (RLS) POLICIES
-- =====================================================================
ALTER TABLE public.coach_clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.coach_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.coach_workouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.coach_programs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.coach_payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.coach_leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.coach_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.coach_challenges ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.coach_availability ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.coach_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.coach_automations ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to perform all operations on their coach records
DO $$
BEGIN
    DROP POLICY IF EXISTS "coach_clients_all" ON public.coach_clients;
    CREATE POLICY "coach_clients_all" ON public.coach_clients FOR ALL TO authenticated USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "coach_sessions_all" ON public.coach_sessions;
    CREATE POLICY "coach_sessions_all" ON public.coach_sessions FOR ALL TO authenticated USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "coach_workouts_all" ON public.coach_workouts;
    CREATE POLICY "coach_workouts_all" ON public.coach_workouts FOR ALL TO authenticated USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "coach_programs_all" ON public.coach_programs;
    CREATE POLICY "coach_programs_all" ON public.coach_programs FOR ALL TO authenticated USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "coach_payments_all" ON public.coach_payments;
    CREATE POLICY "coach_payments_all" ON public.coach_payments FOR ALL TO authenticated USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "coach_leads_all" ON public.coach_leads;
    CREATE POLICY "coach_leads_all" ON public.coach_leads FOR ALL TO authenticated USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "coach_groups_all" ON public.coach_groups;
    CREATE POLICY "coach_groups_all" ON public.coach_groups FOR ALL TO authenticated USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "coach_challenges_all" ON public.coach_challenges;
    CREATE POLICY "coach_challenges_all" ON public.coach_challenges FOR ALL TO authenticated USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "coach_availability_all" ON public.coach_availability;
    CREATE POLICY "coach_availability_all" ON public.coach_availability FOR ALL TO authenticated USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "coach_reports_all" ON public.coach_reports;
    CREATE POLICY "coach_reports_all" ON public.coach_reports FOR ALL TO authenticated USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "coach_automations_all" ON public.coach_automations;
    CREATE POLICY "coach_automations_all" ON public.coach_automations FOR ALL TO authenticated USING (true) WITH CHECK (true);
END $$;

-- Indexes for lightning fast queries
CREATE INDEX IF NOT EXISTS idx_coach_clients_coach_id ON public.coach_clients(coach_id);
CREATE INDEX IF NOT EXISTS idx_coach_sessions_coach_id ON public.coach_sessions(coach_id);
CREATE INDEX IF NOT EXISTS idx_coach_workouts_coach_id ON public.coach_workouts(coach_id);
CREATE INDEX IF NOT EXISTS idx_coach_payments_coach_id ON public.coach_payments(coach_id);
CREATE INDEX IF NOT EXISTS idx_coach_leads_coach_id ON public.coach_leads(coach_id);
