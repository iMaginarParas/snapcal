-- Migration to support referral network
-- Run this in your Supabase SQL Editor

-- 1. Add columns to public.users table
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS referral_code TEXT UNIQUE;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS referred_by UUID REFERENCES public.users(id);

-- 2. Create public.referrals table
CREATE TABLE IF NOT EXISTS public.referrals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    referrer_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    referred_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    code_used TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 3. Enable RLS on referrals table
ALTER TABLE public.referrals ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can view referrals they are involved in" ON public.referrals;
CREATE POLICY "Users can view referrals they are involved in" ON public.referrals
    FOR SELECT USING (auth.uid() = referrer_id OR auth.uid() = referred_id);
