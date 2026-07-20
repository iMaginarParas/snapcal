-- SABTRACK AI Export & Share Studio Migrations
-- Run this in your Supabase SQL Editor

-- 1. Create Exports Table
CREATE TABLE IF NOT EXISTS public.exports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    metric_type TEXT NOT NULL, -- 'health', 'nutrition', 'workouts', 'sleep', 'body', 'achievements', 'year_in_review', 'custom'
    date_range TEXT NOT NULL, -- 'today', 'yesterday', 'last_7_days', 'last_30_days', 'this_month', 'last_month', 'this_year', 'custom'
    custom_start TEXT, -- optional ISO date
    custom_end TEXT, -- optional ISO date
    layout_type TEXT NOT NULL, -- 'minimal', 'glass', 'rings', etc. (1-20)
    output_format TEXT NOT NULL, -- 'png', 'jpeg', 'pdf', 'csv', 'excel', 'json', 'zip'
    theme TEXT NOT NULL, -- 'light', 'dark', 'glass', 'transparent', etc.
    custom_settings JSONB DEFAULT '{}'::jsonb, -- accent color, background photo, logo url, etc.
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'completed', 'failed'
    file_url TEXT,
    shared_url TEXT,
    is_favorite BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Enable RLS
ALTER TABLE public.exports ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own exports" ON public.exports;
CREATE POLICY "Users can manage own exports" ON public.exports FOR ALL USING (auth.uid() = user_id);

-- 2. Create Export Audit Logs Table
CREATE TABLE IF NOT EXISTS public.export_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    action TEXT NOT NULL, -- 'create_image', 'create_pdf', 'delete_export', 'share_export'
    export_id UUID,
    ip_address TEXT,
    user_agent TEXT,
    details JSONB DEFAULT '{}'::jsonb,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Enable RLS
ALTER TABLE public.export_audit_logs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can view own audit logs" ON public.export_audit_logs;
CREATE POLICY "Users can view own audit logs" ON public.export_audit_logs FOR SELECT USING (auth.uid() = user_id);
