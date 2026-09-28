-- Migration: Add FCM push token column to users table
-- Run this in your Supabase SQL editor (public schema)
-- Date: 2026-09-28

-- Add fcm_token column to store Firebase Cloud Messaging device tokens.
-- This allows the backend to send real-time push notifications to the client app.
ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS fcm_token TEXT DEFAULT NULL;

-- Index for fast FCM token lookups when broadcasting notifications
CREATE INDEX IF NOT EXISTS idx_users_fcm_token
  ON public.users (fcm_token)
  WHERE fcm_token IS NOT NULL;

-- Optional: Add updated_at timestamp for token rotation tracking
ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS fcm_token_updated_at TIMESTAMPTZ DEFAULT NULL;
