-- =====================================================================
-- SABTRACK + SABCOACH  ·  MASTER SUPABASE MIGRATION  (v3 — production)
-- =====================================================================
-- Single shared Supabase project  ·  Option A
--   · SabTrack  →  `public` schema
--   · SabCoach  →  `coach`  schema
--
-- Run once in:  Supabase Dashboard → SQL Editor → "New Query"
-- Paste the entire file and click RUN.
--
-- Fully idempotent — safe to run on a brand-new project OR on an
-- existing project that has older migrations already applied:
--   · CREATE TABLE   IF NOT EXISTS
--   · ALTER TABLE    ADD COLUMN IF NOT EXISTS   (preamble section)
--   · DROP POLICY    IF EXISTS  before every CREATE POLICY
--   · CREATE INDEX   IF NOT EXISTS
--   · INSERT … ON CONFLICT DO NOTHING
--   · Trigger creation wrapped in existence checks
-- =====================================================================


-- ─────────────────────────────────────────────────────────────────────────────
-- 0. EXTENSIONS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ─────────────────────────────────────────────────────────────────────────────
-- 1. SABCOACH SCHEMA
-- ─────────────────────────────────────────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS coach;


-- ─────────────────────────────────────────────────────────────────────────────
-- 2. SHARED UTILITY: updated_at auto-trigger function
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ─────────────────────────────────────────────────────────────────────────────
-- 3. PREAMBLE — PATCH PRE-EXISTING TABLES
--    If older migrations have already created some of these tables,
--    ALTER TABLE ensures every expected column exists before triggers
--    or policies reference it.
-- ─────────────────────────────────────────────────────────────────────────────

-- public.users
ALTER TABLE IF EXISTS public.users ADD COLUMN IF NOT EXISTS username                TEXT UNIQUE;
ALTER TABLE IF EXISTS public.users ADD COLUMN IF NOT EXISTS name                    TEXT;
ALTER TABLE IF EXISTS public.users ADD COLUMN IF NOT EXISTS profile_picture_url     TEXT;
ALTER TABLE IF EXISTS public.users ADD COLUMN IF NOT EXISTS is_pro                  BOOLEAN DEFAULT FALSE;
ALTER TABLE IF EXISTS public.users ADD COLUMN IF NOT EXISTS subscription_tier       TEXT DEFAULT 'free';
ALTER TABLE IF EXISTS public.users ADD COLUMN IF NOT EXISTS subscription_plan_id    TEXT;
ALTER TABLE IF EXISTS public.users ADD COLUMN IF NOT EXISTS subscription_expires_at TIMESTAMPTZ;
ALTER TABLE IF EXISTS public.users ADD COLUMN IF NOT EXISTS referral_code           TEXT UNIQUE;
ALTER TABLE IF EXISTS public.users ADD COLUMN IF NOT EXISTS referred_by             UUID;
ALTER TABLE IF EXISTS public.users ADD COLUMN IF NOT EXISTS updated_at              TIMESTAMPTZ DEFAULT NOW();

-- public.meals  (remove fat/fats ambiguity; add new columns)
ALTER TABLE IF EXISTS public.meals ADD COLUMN IF NOT EXISTS description   TEXT;
ALTER TABLE IF EXISTS public.meals ADD COLUMN IF NOT EXISTS meal_type     TEXT;
ALTER TABLE IF EXISTS public.meals ADD COLUMN IF NOT EXISTS fat           NUMERIC;
ALTER TABLE IF EXISTS public.meals ADD COLUMN IF NOT EXISTS fiber         NUMERIC DEFAULT 0.0;
ALTER TABLE IF EXISTS public.meals ADD COLUMN IF NOT EXISTS total_weight  NUMERIC DEFAULT 0.0;
ALTER TABLE IF EXISTS public.meals ADD COLUMN IF NOT EXISTS total_calories INT;
-- Backfill fat from legacy fats column if present
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema='public' AND table_name='meals' AND column_name='fats') THEN
        UPDATE public.meals SET fat = fats WHERE fat IS NULL AND fats IS NOT NULL;
    END IF;
END $$;

-- public.food_items
ALTER TABLE IF EXISTS public.food_items ADD COLUMN IF NOT EXISTS normalized_name    TEXT;
ALTER TABLE IF EXISTS public.food_items ADD COLUMN IF NOT EXISTS serving            TEXT;
ALTER TABLE IF EXISTS public.food_items ADD COLUMN IF NOT EXISTS hidden_ingredients JSONB;

-- public.workouts  (remove exercises JSONB — use workout_exercises table)
ALTER TABLE IF EXISTS public.workouts ADD COLUMN IF NOT EXISTS workout_type     TEXT DEFAULT 'strength';
ALTER TABLE IF EXISTS public.workouts ADD COLUMN IF NOT EXISTS category         TEXT;
ALTER TABLE IF EXISTS public.workouts ADD COLUMN IF NOT EXISTS distance         NUMERIC;
ALTER TABLE IF EXISTS public.workouts ADD COLUMN IF NOT EXISTS duration_seconds INT;
ALTER TABLE IF EXISTS public.workouts ADD COLUMN IF NOT EXISTS calories         INT;
ALTER TABLE IF EXISTS public.workouts ADD COLUMN IF NOT EXISTS route_points     JSONB;
ALTER TABLE IF EXISTS public.workouts ADD COLUMN IF NOT EXISTS created_at       TIMESTAMPTZ DEFAULT NOW();

-- public.profiles
ALTER TABLE IF EXISTS public.profiles ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- public.daily_steps
ALTER TABLE IF EXISTS public.daily_steps ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- public.payments
ALTER TABLE IF EXISTS public.payments ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- public.subscriptions
ALTER TABLE IF EXISTS public.subscriptions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- public.export_audit_logs
--   Old schema used column name `timestamp`; new schema uses `created_at`.
--   Rename if the old column still exists.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema = 'public'
                 AND table_name   = 'export_audit_logs'
                 AND column_name  = 'timestamp') THEN
        ALTER TABLE public.export_audit_logs RENAME COLUMN "timestamp" TO created_at;
    END IF;
    -- Add if missing entirely
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'public'
                     AND table_name   = 'export_audit_logs'
                     AND column_name  = 'created_at') THEN
        ALTER TABLE public.export_audit_logs ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW();
    END IF;
END $$;

-- public.exports  (custom_start / custom_end stored as DATE not TEXT)
ALTER TABLE IF EXISTS public.exports ADD COLUMN IF NOT EXISTS custom_start DATE;
ALTER TABLE IF EXISTS public.exports ADD COLUMN IF NOT EXISTS custom_end   DATE;


-- =====================================================================
-- ██████╗ ██╗   ██╗██████╗ ██╗     ██╗ ██████╗
-- PUBLIC SCHEMA  —  SabTrack (Nutrition & Fitness Tracker)
-- =====================================================================


-- ─────────────────────────────────────────────────────────────────────────────
-- 4. USERS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.users (
    id                      UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email                   TEXT UNIQUE NOT NULL,
    username                TEXT UNIQUE,
    name                    TEXT,
    profile_picture_url     TEXT,
    age                     INT,
    weight                  NUMERIC,
    height                  NUMERIC,
    goals                   TEXT,
    is_pro                  BOOLEAN DEFAULT FALSE,
    subscription_tier       TEXT DEFAULT 'free',
    subscription_plan_id    TEXT,
    subscription_expires_at TIMESTAMPTZ,
    referral_code           TEXT UNIQUE,
    referred_by             UUID REFERENCES public.users(id) ON DELETE SET NULL,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Public profiles are viewable by everyone" ON public.users;
CREATE POLICY "Public profiles are viewable by everyone"
    ON public.users FOR SELECT USING (true);
DROP POLICY IF EXISTS "Users can insert own profile" ON public.users;
CREATE POLICY "Users can insert own profile"
    ON public.users FOR INSERT WITH CHECK (auth.uid() = id);
DROP POLICY IF EXISTS "Users can update own profile" ON public.users;
CREATE POLICY "Users can update own profile"
    ON public.users FOR UPDATE USING (auth.uid() = id);

DROP TRIGGER IF EXISTS trg_users_updated_at ON public.users;
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- Auto-create user row + generate referral code on Auth sign-up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
    base_username  TEXT;
    final_username TEXT;
    counter        INT := 0;
BEGIN
    base_username  := regexp_replace(split_part(new.email, '@', 1), '[^a-zA-Z0-9_]', '', 'g');
    IF base_username = '' THEN base_username := 'user'; END IF;
    final_username := base_username;
    WHILE EXISTS (SELECT 1 FROM public.users WHERE username = final_username) LOOP
        counter        := counter + 1;
        final_username := base_username || counter::TEXT;
    END LOOP;
    INSERT INTO public.users (id, email, username, referral_code)
    VALUES (
        new.id,
        new.email,
        final_username,
        upper(substr(replace(gen_random_uuid()::text, '-', ''), 1, 8))
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();


-- ─────────────────────────────────────────────────────────────────────────────
-- 5. USER PROFILES
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.profiles (
    user_id         UUID PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,
    age             INT,
    gender          TEXT,
    height_cm       NUMERIC,
    current_weight  NUMERIC,
    target_weight   NUMERIC,
    activity_level  TEXT,
    goal            TEXT,
    bmi             NUMERIC,
    bmi_category    TEXT,
    bmr             NUMERIC,
    tdee            NUMERIC,
    target_calories INT,
    protein_target  INT,
    carb_target     INT,
    fat_target      INT,
    fiber_target    INT,
    water_target    INT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own profile details" ON public.profiles;
CREATE POLICY "Users can manage own profile details"
    ON public.profiles FOR ALL USING (auth.uid() = user_id);

DROP TRIGGER IF EXISTS trg_profiles_updated_at ON public.profiles;
CREATE TRIGGER trg_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- ─────────────────────────────────────────────────────────────────────────────
-- 6. MEALS  (no `fats` column — use `fat` only)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.meals (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id        UUID REFERENCES public.users(id) ON DELETE CASCADE,
    name           TEXT NOT NULL,
    description    TEXT,
    meal_type      TEXT,
    calories       INT NOT NULL,
    protein        NUMERIC,
    carbs          NUMERIC,
    fat            NUMERIC,
    fiber          NUMERIC DEFAULT 0.0,
    total_weight   NUMERIC DEFAULT 0.0,
    total_calories INT,
    image_url      TEXT,
    logged_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.meals ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own meals" ON public.meals;
CREATE POLICY "Users can manage own meals"
    ON public.meals FOR ALL USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_meals_user_id_logged ON public.meals(user_id, logged_at DESC);


-- ─────────────────────────────────────────────────────────────────────────────
-- 7. FOOD ITEMS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.food_items (
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meal_id            UUID REFERENCES public.meals(id) ON DELETE CASCADE,
    food_name          TEXT NOT NULL,
    normalized_name    TEXT,
    weight             NUMERIC NOT NULL,
    serving            TEXT,
    calories           INT NOT NULL,
    protein            NUMERIC NOT NULL,
    carbs              NUMERIC NOT NULL,
    fat                NUMERIC NOT NULL,
    fiber              NUMERIC NOT NULL DEFAULT 0.0,
    confidence         NUMERIC NOT NULL DEFAULT 1.0,
    cooking_method     TEXT,
    ingredients        JSONB,
    hidden_ingredients JSONB,
    created_at         TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.food_items ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own food items" ON public.food_items;
CREATE POLICY "Users can manage own food items"
    ON public.food_items FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.meals
            WHERE public.meals.id      = public.food_items.meal_id
              AND public.meals.user_id = auth.uid()
        )
    );

CREATE INDEX IF NOT EXISTS idx_food_items_meal_id ON public.food_items(meal_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- 8. FOOD CATALOGUE
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.foods (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name           TEXT UNIQUE NOT NULL,
    calories       INT NOT NULL,
    protein        NUMERIC NOT NULL,
    carbs          NUMERIC NOT NULL,
    fat            NUMERIC NOT NULL,
    fiber          NUMERIC NOT NULL DEFAULT 0.0,
    sugar          NUMERIC DEFAULT 0.0,
    sodium         NUMERIC DEFAULT 0.0,
    serving_size_g NUMERIC DEFAULT 100.0,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.foods ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow public read access to foods" ON public.foods;
CREATE POLICY "Allow public read access to foods"
    ON public.foods FOR SELECT USING (true);


-- ─────────────────────────────────────────────────────────────────────────────
-- 9. FOOD ALIASES
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.food_aliases (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alias         TEXT UNIQUE NOT NULL,
    standard_name TEXT REFERENCES public.foods(name) ON DELETE CASCADE,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.food_aliases ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow public read access to food_aliases" ON public.food_aliases;
CREATE POLICY "Allow public read access to food_aliases"
    ON public.food_aliases FOR SELECT USING (true);


-- ─────────────────────────────────────────────────────────────────────────────
-- 10. NUTRITION CACHE
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.nutrition_cache (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    food_name    TEXT UNIQUE NOT NULL,
    weight       NUMERIC NOT NULL,
    calories     INT NOT NULL,
    protein      NUMERIC NOT NULL,
    carbs        NUMERIC NOT NULL,
    fat          NUMERIC NOT NULL,
    fiber        NUMERIC NOT NULL DEFAULT 0.0,
    sodium       NUMERIC DEFAULT 0.0,
    serving_size TEXT,
    source       TEXT NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.nutrition_cache ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow read access to nutrition_cache" ON public.nutrition_cache;
CREATE POLICY "Allow read access to nutrition_cache"
    ON public.nutrition_cache FOR SELECT USING (true);
DROP POLICY IF EXISTS "Allow system write to nutrition_cache" ON public.nutrition_cache;
CREATE POLICY "Allow system write to nutrition_cache"
    ON public.nutrition_cache FOR INSERT WITH CHECK (true);


-- ─────────────────────────────────────────────────────────────────────────────
-- 11. BARCODE CACHE
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.barcode_cache (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    barcode      TEXT UNIQUE NOT NULL,
    food_name    TEXT NOT NULL,
    calories     INT NOT NULL,
    protein      NUMERIC NOT NULL,
    carbs        NUMERIC NOT NULL,
    fat          NUMERIC NOT NULL,
    fiber        NUMERIC NOT NULL DEFAULT 0.0,
    sodium       NUMERIC DEFAULT 0.0,
    serving_size TEXT,
    source       TEXT NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.barcode_cache ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow read access to barcode_cache" ON public.barcode_cache;
CREATE POLICY "Allow read access to barcode_cache"
    ON public.barcode_cache FOR SELECT USING (true);
DROP POLICY IF EXISTS "Allow system write to barcode_cache" ON public.barcode_cache;
CREATE POLICY "Allow system write to barcode_cache"
    ON public.barcode_cache FOR INSERT WITH CHECK (true);


-- ─────────────────────────────────────────────────────────────────────────────
-- 12. USER CORRECTIONS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.user_corrections (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id        UUID REFERENCES public.users(id) ON DELETE CASCADE,
    original_name  TEXT NOT NULL,
    corrected_name TEXT NOT NULL,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.user_corrections ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own corrections" ON public.user_corrections;
CREATE POLICY "Users can manage own corrections"
    ON public.user_corrections FOR ALL USING (auth.uid() = user_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- 13. FOOD CORRECTIONS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.food_corrections (
    id                       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                  UUID REFERENCES public.users(id) ON DELETE CASCADE,
    original_name            TEXT NOT NULL,
    corrected_name           TEXT NOT NULL,
    corrected_weight         NUMERIC,
    corrected_cooking_method TEXT,
    corrected_serving        TEXT,
    created_at               TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.food_corrections ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own food corrections" ON public.food_corrections;
CREATE POLICY "Users can manage own food corrections"
    ON public.food_corrections FOR ALL USING (auth.uid() = user_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- 14. FAVOURITE FOODS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.favorite_foods (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id        UUID REFERENCES public.users(id) ON DELETE CASCADE,
    food_name      TEXT NOT NULL,
    calories       INT,
    protein        NUMERIC,
    carbs          NUMERIC,
    fat            NUMERIC,
    fiber          NUMERIC DEFAULT 0.0,
    serving_size_g NUMERIC,
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, food_name)
);

ALTER TABLE public.favorite_foods ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own favorite foods" ON public.favorite_foods;
CREATE POLICY "Users can manage own favorite foods"
    ON public.favorite_foods FOR ALL USING (auth.uid() = user_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- 15. RECENT FOODS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.recent_foods (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id        UUID REFERENCES public.users(id) ON DELETE CASCADE,
    food_name      TEXT NOT NULL,
    last_logged_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, food_name)
);

ALTER TABLE public.recent_foods ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own recent foods" ON public.recent_foods;
CREATE POLICY "Users can manage own recent foods"
    ON public.recent_foods FOR ALL USING (auth.uid() = user_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- 16. MEAL TEMPLATES
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.meal_templates (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id       UUID REFERENCES public.users(id) ON DELETE CASCADE,
    template_name TEXT NOT NULL,
    foods         JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.meal_templates ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own meal templates" ON public.meal_templates;
CREATE POLICY "Users can manage own meal templates"
    ON public.meal_templates FOR ALL USING (auth.uid() = user_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- 17. WORKOUTS  (no exercises JSONB column — use workout_exercises table)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.workouts (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id          UUID REFERENCES public.users(id) ON DELETE CASCADE,
    workout_name     TEXT NOT NULL,
    workout_type     TEXT DEFAULT 'strength',
    category         TEXT,
    distance         NUMERIC,
    duration_seconds INT,
    calories         INT,
    route_points     JSONB,
    completed        BOOLEAN DEFAULT FALSE,
    completed_at     TIMESTAMPTZ,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.workouts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own workouts" ON public.workouts;
CREATE POLICY "Users can manage own workouts"
    ON public.workouts FOR ALL USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_workouts_user_created ON public.workouts(user_id, created_at DESC);


-- ─────────────────────────────────────────────────────────────────────────────
-- 18. WORKOUT EXERCISES  (normalised rows — one per exercise per workout)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.workout_exercises (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workout_id    UUID REFERENCES public.workouts(id) ON DELETE CASCADE,
    exercise_name TEXT NOT NULL,
    sets          INT NOT NULL,
    reps          TEXT NOT NULL,
    weight_kg     NUMERIC,
    rest_seconds  INT,
    notes         TEXT,
    sort_order    INT DEFAULT 0,
    completed     BOOLEAN DEFAULT FALSE
);

ALTER TABLE public.workout_exercises ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage exercises" ON public.workout_exercises;
CREATE POLICY "Users can manage exercises"
    ON public.workout_exercises FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.workouts
            WHERE public.workouts.id      = public.workout_exercises.workout_id
              AND public.workouts.user_id = auth.uid()
        )
    );

CREATE INDEX IF NOT EXISTS idx_workout_exercises_workout_id ON public.workout_exercises(workout_id, sort_order);


-- ─────────────────────────────────────────────────────────────────────────────
-- 19. DAILY STATS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.daily_stats (
    id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id  UUID REFERENCES public.users(id) ON DELETE CASCADE,
    date     DATE NOT NULL DEFAULT CURRENT_DATE,
    steps    INT DEFAULT 0,
    water_ml INT DEFAULT 0,
    UNIQUE(user_id, date)
);

ALTER TABLE public.daily_stats ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own daily stats" ON public.daily_stats;
CREATE POLICY "Users can manage own daily stats"
    ON public.daily_stats FOR ALL USING (auth.uid() = user_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- 20. DAILY STEPS  (granular sensor data)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.daily_steps (
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id              UUID REFERENCES public.users(id) ON DELETE CASCADE,
    date                 DATE NOT NULL,
    sensor_steps         INT DEFAULT 0,
    health_connect_steps INT DEFAULT 0,
    final_steps          INT DEFAULT 0,
    distance             NUMERIC DEFAULT 0.0,
    calories             INT DEFAULT 0,
    active_minutes       INT DEFAULT 0,
    baseline             INT DEFAULT 0,
    last_sensor_value    INT DEFAULT 0,
    last_sync            TIMESTAMPTZ DEFAULT NOW(),
    created_at           TIMESTAMPTZ DEFAULT NOW(),
    updated_at           TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, date)
);

ALTER TABLE public.daily_steps ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own steps" ON public.daily_steps;
CREATE POLICY "Users can manage own steps"
    ON public.daily_steps FOR ALL USING (auth.uid() = user_id);

DROP TRIGGER IF EXISTS trg_daily_steps_updated_at ON public.daily_steps;
CREATE TRIGGER trg_daily_steps_updated_at
    BEFORE UPDATE ON public.daily_steps
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- ─────────────────────────────────────────────────────────────────────────────
-- 21. MEASUREMENT LOGS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.measurement_logs (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID REFERENCES public.users(id) ON DELETE CASCADE,
    metric_type TEXT NOT NULL,
    value       NUMERIC NOT NULL,
    date        DATE NOT NULL,
    logged_at   TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.measurement_logs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own measurements" ON public.measurement_logs;
CREATE POLICY "Users can manage own measurements"
    ON public.measurement_logs FOR ALL USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_measurement_logs_user_date
    ON public.measurement_logs(user_id, date DESC);


-- ─────────────────────────────────────────────────────────────────────────────
-- 22. WEIGHT HISTORY
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.weight_history (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID REFERENCES public.users(id) ON DELETE CASCADE,
    weight      NUMERIC NOT NULL,
    bmi         NUMERIC NOT NULL,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.weight_history ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own weight history" ON public.weight_history;
CREATE POLICY "Users can manage own weight history"
    ON public.weight_history FOR ALL USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_weight_history_user_id ON public.weight_history(user_id, recorded_at DESC);


-- ─────────────────────────────────────────────────────────────────────────────
-- 23. FASTING LOGS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.fasting_logs (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id    UUID REFERENCES public.users(id) ON DELETE CASCADE,
    protocol   TEXT NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time   TIMESTAMPTZ,
    completed  BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.fasting_logs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own fasting logs" ON public.fasting_logs;
CREATE POLICY "Users can manage own fasting logs"
    ON public.fasting_logs FOR ALL USING (auth.uid() = user_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- 24. SUPPLEMENTS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.supplements (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id    UUID REFERENCES public.users(id) ON DELETE CASCADE,
    name       TEXT NOT NULL,
    dosage     TEXT,
    time       TIME NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.supplements ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own supplements" ON public.supplements;
CREATE POLICY "Users can manage own supplements"
    ON public.supplements FOR ALL USING (auth.uid() = user_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- 25. PLANS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.plans (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID REFERENCES public.users(id) ON DELETE CASCADE,
    file_url    TEXT,
    parsed_data JSONB,
    plan_type   TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.plans ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own plans" ON public.plans;
CREATE POLICY "Users can manage own plans"
    ON public.plans FOR ALL USING (auth.uid() = user_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- 26. DAILY TASKS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.daily_tasks (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id        UUID REFERENCES public.users(id) ON DELETE CASCADE,
    task_type      TEXT NOT NULL,
    title          TEXT NOT NULL,
    description    TEXT,
    scheduled_time TIME,
    completed      BOOLEAN DEFAULT FALSE,
    date           DATE NOT NULL DEFAULT CURRENT_DATE
);

ALTER TABLE public.daily_tasks ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own tasks" ON public.daily_tasks;
CREATE POLICY "Users can manage own tasks"
    ON public.daily_tasks FOR ALL USING (auth.uid() = user_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- 27. COMMUNITY GROUPS + MEMBERS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.groups (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        TEXT NOT NULL,
    description TEXT,
    is_public   BOOLEAN DEFAULT TRUE,
    created_by  UUID REFERENCES public.users(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.group_members (
    id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id  UUID REFERENCES public.groups(id) ON DELETE CASCADE,
    user_id   UUID REFERENCES public.users(id) ON DELETE CASCADE,
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(group_id, user_id)
);

ALTER TABLE public.groups ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can view public groups" ON public.groups;
CREATE POLICY "Users can view public groups"
    ON public.groups FOR SELECT USING (
        is_public = TRUE
        OR auth.uid() IN (SELECT user_id FROM public.group_members WHERE group_id = id)
    );
DROP POLICY IF EXISTS "Users can manage own created groups" ON public.groups;
CREATE POLICY "Users can manage own created groups"
    ON public.groups FOR ALL USING (auth.uid() = created_by);

ALTER TABLE public.group_members ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Anyone can view group members" ON public.group_members;
CREATE POLICY "Anyone can view group members"
    ON public.group_members FOR SELECT USING (true);
DROP POLICY IF EXISTS "Users can join/leave groups" ON public.group_members;
CREATE POLICY "Users can join/leave groups"
    ON public.group_members FOR ALL USING (auth.uid() = user_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- 28. GROUP MESSAGES
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.group_messages (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id   UUID REFERENCES public.groups(id) ON DELETE CASCADE,
    user_id    UUID REFERENCES public.users(id) ON DELETE CASCADE,
    message    TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.group_messages ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Members can view messages" ON public.group_messages;
CREATE POLICY "Members can view messages"
    ON public.group_messages FOR SELECT USING (true);
DROP POLICY IF EXISTS "Users can insert own messages" ON public.group_messages;
CREATE POLICY "Users can insert own messages"
    ON public.group_messages FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_group_messages_group_id
    ON public.group_messages(group_id, created_at DESC);


-- ─────────────────────────────────────────────────────────────────────────────
-- 29. FRIENDSHIPS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.friendships (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id    UUID REFERENCES public.users(id) ON DELETE CASCADE,
    friend_id  UUID REFERENCES public.users(id) ON DELETE CASCADE,
    status     TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, friend_id)
);

ALTER TABLE public.friendships ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own friendships" ON public.friendships;
CREATE POLICY "Users can manage own friendships"
    ON public.friendships FOR ALL USING (auth.uid() = user_id OR auth.uid() = friend_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- 30. CHALLENGES + ENROLLMENTS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.challenges (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title           TEXT NOT NULL,
    description     TEXT,
    target_workouts INT DEFAULT 5,
    points          INT DEFAULT 500,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.user_challenges (
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id            UUID REFERENCES public.users(id) ON DELETE CASCADE,
    challenge_id       UUID REFERENCES public.challenges(id) ON DELETE CASCADE,
    completed_workouts INT DEFAULT 0,
    completed          BOOLEAN DEFAULT FALSE,
    joined_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, challenge_id)
);

ALTER TABLE public.challenges ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Anyone can view challenges" ON public.challenges;
CREATE POLICY "Anyone can view challenges"
    ON public.challenges FOR SELECT USING (true);

ALTER TABLE public.user_challenges ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own enrollments" ON public.user_challenges;
CREATE POLICY "Users can manage own enrollments"
    ON public.user_challenges FOR ALL USING (auth.uid() = user_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- 31. REFERRALS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.referrals (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    referrer_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    referred_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    code_used   TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.referrals ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can view referrals they are involved in" ON public.referrals;
CREATE POLICY "Users can view referrals they are involved in"
    ON public.referrals FOR SELECT
    USING (auth.uid() = referrer_id OR auth.uid() = referred_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- 32. PAYMENTS  (Razorpay — SabTrack Pro)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.payments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL,
    razorpay_order_id   TEXT NOT NULL,
    razorpay_payment_id TEXT,
    razorpay_signature  TEXT,
    plan_id             TEXT NOT NULL,
    amount              NUMERIC NOT NULL,
    currency            TEXT DEFAULT 'INR',
    status              TEXT DEFAULT 'created',
    receipt             TEXT,
    notes               JSONB DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.subscriptions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL,
    plan_id             TEXT NOT NULL,
    plan_name           TEXT NOT NULL,
    amount              NUMERIC NOT NULL,
    currency            TEXT DEFAULT 'INR',
    status              TEXT DEFAULT 'active',
    starts_at           TIMESTAMPTZ DEFAULT NOW(),
    expires_at          TIMESTAMPTZ NOT NULL,
    razorpay_order_id   TEXT,
    razorpay_payment_id TEXT,
    auto_renew          BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.payments      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own payments" ON public.payments;
CREATE POLICY "Users can view own payments"
    ON public.payments FOR SELECT USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "Users can view own subscriptions" ON public.subscriptions;
CREATE POLICY "Users can view own subscriptions"
    ON public.subscriptions FOR SELECT USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_payments_user_id      ON public.payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_order_id     ON public.payments(razorpay_order_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON public.subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status  ON public.subscriptions(status, expires_at);

DROP TRIGGER IF EXISTS trg_payments_updated_at ON public.payments;
CREATE TRIGGER trg_payments_updated_at
    BEFORE UPDATE ON public.payments
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

DROP TRIGGER IF EXISTS trg_subscriptions_updated_at ON public.subscriptions;
CREATE TRIGGER trg_subscriptions_updated_at
    BEFORE UPDATE ON public.subscriptions
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- ─────────────────────────────────────────────────────────────────────────────
-- 33. EXPORTS + AUDIT LOGS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.exports (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES public.users(id) ON DELETE CASCADE,
    metric_type     TEXT NOT NULL,
    date_range      TEXT NOT NULL,
    custom_start    DATE,
    custom_end      DATE,
    layout_type     TEXT NOT NULL,
    output_format   TEXT NOT NULL,
    theme           TEXT NOT NULL,
    custom_settings JSONB DEFAULT '{}'::jsonb,
    status          TEXT NOT NULL DEFAULT 'pending',
    file_url        TEXT,
    shared_url      TEXT,
    is_favorite     BOOLEAN DEFAULT FALSE,
    error_message   TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.export_audit_logs (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id    UUID REFERENCES public.users(id) ON DELETE SET NULL,
    action     TEXT NOT NULL,
    export_id  UUID,
    ip_address TEXT,
    user_agent TEXT,
    details    JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.exports           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.export_audit_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage own exports" ON public.exports;
CREATE POLICY "Users can manage own exports"
    ON public.exports FOR ALL USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "Users can view own audit logs" ON public.export_audit_logs;
CREATE POLICY "Users can view own audit logs"
    ON public.export_audit_logs FOR SELECT USING (auth.uid() = user_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- 34. SUPPORT TICKETS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.support_tickets (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id    UUID REFERENCES public.users(id) ON DELETE SET NULL,
    email      TEXT NOT NULL,
    category   TEXT NOT NULL,
    message    TEXT NOT NULL,
    status     TEXT DEFAULT 'open',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.support_tickets ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage own support tickets" ON public.support_tickets;
CREATE POLICY "Users can manage own support tickets"
    ON public.support_tickets FOR ALL
    USING (auth.uid() = user_id OR auth.uid() IS NULL);


-- =====================================================================
--  ██████╗ ██████╗  █████╗  ██████╗██╗  ██╗
-- COACH SCHEMA  —  SabCoach (Coaching Management Platform)
-- =====================================================================


-- ─────────────────────────────────────────────────────────────────────────────
-- 35. COACH CLIENTS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS coach.clients (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coach_id      UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name          TEXT NOT NULL,
    email         TEXT,
    phone         TEXT,
    avatar        TEXT,
    status        TEXT NOT NULL DEFAULT 'On Track',
    goal          TEXT,
    target_cals   INT DEFAULT 2000,
    package       TEXT,
    join_date     DATE DEFAULT CURRENT_DATE,
    sabtrack_data JSONB DEFAULT '{}'::jsonb,
    notes         TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE coach.clients ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "coach_clients_isolation" ON coach.clients;
CREATE POLICY "coach_clients_isolation"
    ON coach.clients FOR ALL TO authenticated
    USING      (coach_id = auth.uid())
    WITH CHECK (coach_id = auth.uid());

CREATE INDEX IF NOT EXISTS idx_coach_clients_coach_id ON coach.clients(coach_id);
CREATE INDEX IF NOT EXISTS idx_coach_clients_status   ON coach.clients(coach_id, status);

DROP TRIGGER IF EXISTS trg_coach_clients_updated_at ON coach.clients;
CREATE TRIGGER trg_coach_clients_updated_at
    BEFORE UPDATE ON coach.clients
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- ─────────────────────────────────────────────────────────────────────────────
-- 36. COACH SESSIONS  (single TIMESTAMPTZ — no split DATE + TIME)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS coach.sessions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coach_id      UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_id     UUID REFERENCES coach.clients(id) ON DELETE SET NULL,
    client_name   TEXT NOT NULL,
    client_avatar TEXT,
    title         TEXT NOT NULL,
    scheduled_at  TIMESTAMPTZ NOT NULL,
    duration_mins INT DEFAULT 45,
    type          TEXT DEFAULT '1:1 Coaching',
    status        TEXT DEFAULT 'Scheduled',
    location      TEXT DEFAULT 'Virtual / Video Call',
    notes         TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE coach.sessions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "coach_sessions_isolation" ON coach.sessions;
CREATE POLICY "coach_sessions_isolation"
    ON coach.sessions FOR ALL TO authenticated
    USING      (coach_id = auth.uid())
    WITH CHECK (coach_id = auth.uid());

CREATE INDEX IF NOT EXISTS idx_coach_sessions_coach_id     ON coach.sessions(coach_id);
CREATE INDEX IF NOT EXISTS idx_coach_sessions_scheduled_at ON coach.sessions(coach_id, scheduled_at);
CREATE INDEX IF NOT EXISTS idx_coach_sessions_client_id    ON coach.sessions(client_id);

DROP TRIGGER IF EXISTS trg_coach_sessions_updated_at ON coach.sessions;
CREATE TRIGGER trg_coach_sessions_updated_at
    BEFORE UPDATE ON coach.sessions
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- ─────────────────────────────────────────────────────────────────────────────
-- 37. COACH WORKOUTS + EXERCISES  (normalised — no JSONB exercises column)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS coach.workouts (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coach_id      UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_id     UUID REFERENCES coach.clients(id) ON DELETE SET NULL,
    name          TEXT NOT NULL,
    description   TEXT,
    category      TEXT DEFAULT 'Strength',
    difficulty    TEXT DEFAULT 'Intermediate',
    duration_mins INT DEFAULT 45,
    playlist_url  TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS coach.workout_exercises (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workout_id    UUID NOT NULL REFERENCES coach.workouts(id) ON DELETE CASCADE,
    exercise_name TEXT NOT NULL,
    sets          INT NOT NULL,
    reps          TEXT NOT NULL,
    weight_kg     NUMERIC,
    rest_seconds  INT,
    notes         TEXT,
    sort_order    INT DEFAULT 0
);

ALTER TABLE coach.workouts          ENABLE ROW LEVEL SECURITY;
ALTER TABLE coach.workout_exercises ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "coach_workouts_isolation" ON coach.workouts;
CREATE POLICY "coach_workouts_isolation"
    ON coach.workouts FOR ALL TO authenticated
    USING      (coach_id = auth.uid())
    WITH CHECK (coach_id = auth.uid());

DROP POLICY IF EXISTS "coach_workout_exercises_isolation" ON coach.workout_exercises;
CREATE POLICY "coach_workout_exercises_isolation"
    ON coach.workout_exercises FOR ALL TO authenticated
    USING (
        EXISTS (SELECT 1 FROM coach.workouts w
                WHERE w.id = coach.workout_exercises.workout_id AND w.coach_id = auth.uid())
    );

CREATE INDEX IF NOT EXISTS idx_coach_workouts_coach_id         ON coach.workouts(coach_id);
CREATE INDEX IF NOT EXISTS idx_coach_workout_exercises_workout ON coach.workout_exercises(workout_id, sort_order);

DROP TRIGGER IF EXISTS trg_coach_workouts_updated_at ON coach.workouts;
CREATE TRIGGER trg_coach_workouts_updated_at
    BEFORE UPDATE ON coach.workouts
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- ─────────────────────────────────────────────────────────────────────────────
-- 38. COACH PROGRAMS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS coach.programs (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coach_id       UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title          TEXT NOT NULL,
    description    TEXT,
    duration_weeks INT DEFAULT 12,
    difficulty     TEXT DEFAULT 'Intermediate',
    category       TEXT DEFAULT 'Hypertrophy',
    schedule       JSONB DEFAULT '[]'::jsonb,
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    updated_at     TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE coach.programs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "coach_programs_isolation" ON coach.programs;
CREATE POLICY "coach_programs_isolation"
    ON coach.programs FOR ALL TO authenticated
    USING      (coach_id = auth.uid())
    WITH CHECK (coach_id = auth.uid());

CREATE INDEX IF NOT EXISTS idx_coach_programs_coach_id ON coach.programs(coach_id);

DROP TRIGGER IF EXISTS trg_coach_programs_updated_at ON coach.programs;
CREATE TRIGGER trg_coach_programs_updated_at
    BEFORE UPDATE ON coach.programs
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- ─────────────────────────────────────────────────────────────────────────────
-- 39. COACH PAYMENTS & INVOICES
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS coach.payments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coach_id            UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_id           UUID REFERENCES coach.clients(id) ON DELETE SET NULL,
    client_name         TEXT NOT NULL,
    package_name        TEXT NOT NULL,
    amount              NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    currency            TEXT DEFAULT 'INR',
    status              TEXT DEFAULT 'Pending',
    due_date            DATE,
    paid_date           DATE,
    invoice_number      TEXT,
    payment_method      TEXT DEFAULT 'UPI / Razorpay',
    razorpay_order_id   TEXT,
    razorpay_payment_id TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE coach.payments ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "coach_payments_isolation" ON coach.payments;
CREATE POLICY "coach_payments_isolation"
    ON coach.payments FOR ALL TO authenticated
    USING      (coach_id = auth.uid())
    WITH CHECK (coach_id = auth.uid());

CREATE INDEX IF NOT EXISTS idx_coach_payments_coach_id  ON coach.payments(coach_id);
CREATE INDEX IF NOT EXISTS idx_coach_payments_status    ON coach.payments(coach_id, status);
CREATE INDEX IF NOT EXISTS idx_coach_payments_client_id ON coach.payments(client_id);

DROP TRIGGER IF EXISTS trg_coach_payments_updated_at ON coach.payments;
CREATE TRIGGER trg_coach_payments_updated_at
    BEFORE UPDATE ON coach.payments
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- ─────────────────────────────────────────────────────────────────────────────
-- 40. COACH LEADS  (CRM pipeline)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS coach.leads (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coach_id       UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name           TEXT NOT NULL,
    email          TEXT,
    phone          TEXT,
    stage          TEXT DEFAULT 'New',
    goal           TEXT,
    source         TEXT DEFAULT 'Instagram',
    value          NUMERIC(10,2) DEFAULT 0.00,
    notes          TEXT,
    assigned_coach TEXT,
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    updated_at     TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE coach.leads ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "coach_leads_isolation" ON coach.leads;
CREATE POLICY "coach_leads_isolation"
    ON coach.leads FOR ALL TO authenticated
    USING      (coach_id = auth.uid())
    WITH CHECK (coach_id = auth.uid());

CREATE INDEX IF NOT EXISTS idx_coach_leads_coach_id ON coach.leads(coach_id);
CREATE INDEX IF NOT EXISTS idx_coach_leads_stage    ON coach.leads(coach_id, stage);

DROP TRIGGER IF EXISTS trg_coach_leads_updated_at ON coach.leads;
CREATE TRIGGER trg_coach_leads_updated_at
    BEFORE UPDATE ON coach.leads
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- ─────────────────────────────────────────────────────────────────────────────
-- 41. COACH GROUPS + MEMBERS + POSTS  (normalised child tables)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS coach.groups (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coach_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    description TEXT,
    category    TEXT DEFAULT 'General',
    image_url   TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS coach.group_members (
    id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id  UUID NOT NULL REFERENCES coach.groups(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES coach.clients(id) ON DELETE CASCADE,
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(group_id, client_id)
);

CREATE TABLE IF NOT EXISTS coach.group_posts (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id   UUID NOT NULL REFERENCES coach.groups(id) ON DELETE CASCADE,
    author_id  UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    body       TEXT NOT NULL,
    media_url  TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE coach.groups        ENABLE ROW LEVEL SECURITY;
ALTER TABLE coach.group_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE coach.group_posts   ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "coach_groups_isolation" ON coach.groups;
CREATE POLICY "coach_groups_isolation"
    ON coach.groups FOR ALL TO authenticated
    USING      (coach_id = auth.uid())
    WITH CHECK (coach_id = auth.uid());

DROP POLICY IF EXISTS "coach_group_members_isolation" ON coach.group_members;
CREATE POLICY "coach_group_members_isolation"
    ON coach.group_members FOR ALL TO authenticated
    USING (EXISTS (SELECT 1 FROM coach.groups g
                   WHERE g.id = coach.group_members.group_id AND g.coach_id = auth.uid()));

DROP POLICY IF EXISTS "coach_group_posts_isolation" ON coach.group_posts;
CREATE POLICY "coach_group_posts_isolation"
    ON coach.group_posts FOR ALL TO authenticated
    USING (EXISTS (SELECT 1 FROM coach.groups g
                   WHERE g.id = coach.group_posts.group_id AND g.coach_id = auth.uid()));

CREATE INDEX IF NOT EXISTS idx_coach_groups_coach_id     ON coach.groups(coach_id);
CREATE INDEX IF NOT EXISTS idx_coach_group_members_group ON coach.group_members(group_id);
CREATE INDEX IF NOT EXISTS idx_coach_group_posts_group   ON coach.group_posts(group_id, created_at DESC);

DROP TRIGGER IF EXISTS trg_coach_groups_updated_at ON coach.groups;
CREATE TRIGGER trg_coach_groups_updated_at
    BEFORE UPDATE ON coach.groups
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- ─────────────────────────────────────────────────────────────────────────────
-- 42. COACH CHALLENGES + PARTICIPANTS  (normalised child table)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS coach.challenges (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coach_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title       TEXT NOT NULL,
    description TEXT,
    category    TEXT DEFAULT 'Fitness',
    start_date  DATE,
    end_date    DATE,
    prize       TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS coach.challenge_participants (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    challenge_id UUID NOT NULL REFERENCES coach.challenges(id) ON DELETE CASCADE,
    client_id    UUID NOT NULL REFERENCES coach.clients(id) ON DELETE CASCADE,
    progress     NUMERIC DEFAULT 0,
    completed    BOOLEAN DEFAULT FALSE,
    joined_at    TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(challenge_id, client_id)
);

ALTER TABLE coach.challenges             ENABLE ROW LEVEL SECURITY;
ALTER TABLE coach.challenge_participants ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "coach_challenges_isolation" ON coach.challenges;
CREATE POLICY "coach_challenges_isolation"
    ON coach.challenges FOR ALL TO authenticated
    USING      (coach_id = auth.uid())
    WITH CHECK (coach_id = auth.uid());

DROP POLICY IF EXISTS "coach_challenge_part_isolation" ON coach.challenge_participants;
CREATE POLICY "coach_challenge_part_isolation"
    ON coach.challenge_participants FOR ALL TO authenticated
    USING (EXISTS (SELECT 1 FROM coach.challenges c
                   WHERE c.id = coach.challenge_participants.challenge_id AND c.coach_id = auth.uid()));

CREATE INDEX IF NOT EXISTS idx_coach_challenges_coach_id    ON coach.challenges(coach_id);
CREATE INDEX IF NOT EXISTS idx_coach_challenge_part_chal_id ON coach.challenge_participants(challenge_id);
CREATE INDEX IF NOT EXISTS idx_coach_challenge_part_client  ON coach.challenge_participants(client_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- 43. COACH AVAILABILITY
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS coach.availability (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coach_id   UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    day        TEXT NOT NULL,
    enabled    BOOLEAN DEFAULT TRUE,
    slots      JSONB DEFAULT '[]'::jsonb,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(coach_id, day)
);

ALTER TABLE coach.availability ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "coach_availability_isolation" ON coach.availability;
CREATE POLICY "coach_availability_isolation"
    ON coach.availability FOR ALL TO authenticated
    USING      (coach_id = auth.uid())
    WITH CHECK (coach_id = auth.uid());

CREATE INDEX IF NOT EXISTS idx_coach_availability_coach_id ON coach.availability(coach_id);

DROP TRIGGER IF EXISTS trg_coach_availability_updated_at ON coach.availability;
CREATE TRIGGER trg_coach_availability_updated_at
    BEFORE UPDATE ON coach.availability
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- ─────────────────────────────────────────────────────────────────────────────
-- 44. COACH REPORTS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS coach.reports (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coach_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_id    UUID REFERENCES coach.clients(id) ON DELETE SET NULL,
    client_name  TEXT NOT NULL,
    period       TEXT DEFAULT 'Monthly',
    summary      JSONB DEFAULT '{}'::jsonb,
    coach_notes  TEXT,
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE coach.reports ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "coach_reports_isolation" ON coach.reports;
CREATE POLICY "coach_reports_isolation"
    ON coach.reports FOR ALL TO authenticated
    USING      (coach_id = auth.uid())
    WITH CHECK (coach_id = auth.uid());

CREATE INDEX IF NOT EXISTS idx_coach_reports_coach_id  ON coach.reports(coach_id);
CREATE INDEX IF NOT EXISTS idx_coach_reports_client_id ON coach.reports(client_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- 45. COACH AUTOMATIONS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS coach.automations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coach_id        UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    description     TEXT,
    trigger_event   TEXT NOT NULL,
    action          TEXT NOT NULL,
    active          BOOLEAN DEFAULT TRUE,
    execution_count INT DEFAULT 0,
    last_triggered  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE coach.automations ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "coach_automations_isolation" ON coach.automations;
CREATE POLICY "coach_automations_isolation"
    ON coach.automations FOR ALL TO authenticated
    USING      (coach_id = auth.uid())
    WITH CHECK (coach_id = auth.uid());

CREATE INDEX IF NOT EXISTS idx_coach_automations_coach_id ON coach.automations(coach_id);

DROP TRIGGER IF EXISTS trg_coach_automations_updated_at ON coach.automations;
CREATE TRIGGER trg_coach_automations_updated_at
    BEFORE UPDATE ON coach.automations
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- ─────────────────────────────────────────────────────────────────────────────
-- 46. COACH PRODUCTS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS coach.products (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coach_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title       TEXT NOT NULL,
    description TEXT,
    price       NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    currency    TEXT DEFAULT 'INR',
    duration    TEXT,
    features    JSONB DEFAULT '[]'::jsonb,
    is_active   BOOLEAN DEFAULT TRUE,
    sales_count INT DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE coach.products ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "coach_products_isolation" ON coach.products;
CREATE POLICY "coach_products_isolation"
    ON coach.products FOR ALL TO authenticated
    USING      (coach_id = auth.uid())
    WITH CHECK (coach_id = auth.uid());

CREATE INDEX IF NOT EXISTS idx_coach_products_coach_id ON coach.products(coach_id);

DROP TRIGGER IF EXISTS trg_coach_products_updated_at ON coach.products;
CREATE TRIGGER trg_coach_products_updated_at
    BEFORE UPDATE ON coach.products
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- ─────────────────────────────────────────────────────────────────────────────
-- 47. COACH CHECK-INS
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS coach.checkins (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coach_id       UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_id      UUID NOT NULL REFERENCES coach.clients(id) ON DELETE CASCADE,
    client_name    TEXT NOT NULL,
    client_avatar  TEXT,
    checkin_date   DATE NOT NULL DEFAULT CURRENT_DATE,
    status         TEXT DEFAULT 'Submitted',
    metrics        JSONB DEFAULT '{}'::jsonb,
    adherence      INT DEFAULT 100,
    notes          TEXT,
    coach_feedback TEXT,
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    updated_at     TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE coach.checkins ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "coach_checkins_isolation" ON coach.checkins;
CREATE POLICY "coach_checkins_isolation"
    ON coach.checkins FOR ALL TO authenticated
    USING      (coach_id = auth.uid())
    WITH CHECK (coach_id = auth.uid());

CREATE INDEX IF NOT EXISTS idx_coach_checkins_coach_id    ON coach.checkins(coach_id);
CREATE INDEX IF NOT EXISTS idx_coach_checkins_client_date ON coach.checkins(client_id, checkin_date DESC);

DROP TRIGGER IF EXISTS trg_coach_checkins_updated_at ON coach.checkins;
CREATE TRIGGER trg_coach_checkins_updated_at
    BEFORE UPDATE ON coach.checkins
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- ─────────────────────────────────────────────────────────────────────────────
-- 48. COACH MESSAGES  (thread + items — normalised, pageable)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS coach.message_threads (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coach_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    client_id    UUID NOT NULL REFERENCES coach.clients(id) ON DELETE CASCADE,
    unread_count INT DEFAULT 0,
    last_message TEXT,
    last_msg_at  TIMESTAMPTZ,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(coach_id, client_id)
);

CREATE TABLE IF NOT EXISTS coach.message_items (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id  UUID NOT NULL REFERENCES coach.message_threads(id) ON DELETE CASCADE,
    sender_id  UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    body       TEXT NOT NULL,
    media_url  TEXT,
    read_at    TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE coach.message_threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE coach.message_items   ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "coach_message_threads_isolation" ON coach.message_threads;
CREATE POLICY "coach_message_threads_isolation"
    ON coach.message_threads FOR ALL TO authenticated
    USING      (coach_id = auth.uid())
    WITH CHECK (coach_id = auth.uid());

DROP POLICY IF EXISTS "coach_message_items_isolation" ON coach.message_items;
CREATE POLICY "coach_message_items_isolation"
    ON coach.message_items FOR ALL TO authenticated
    USING (EXISTS (SELECT 1 FROM coach.message_threads t
                   WHERE t.id = coach.message_items.thread_id AND t.coach_id = auth.uid()));

CREATE INDEX IF NOT EXISTS idx_coach_threads_coach_id  ON coach.message_threads(coach_id);
CREATE INDEX IF NOT EXISTS idx_coach_threads_client_id ON coach.message_threads(client_id);
CREATE INDEX IF NOT EXISTS idx_coach_items_thread_id   ON coach.message_items(thread_id, created_at DESC);

DROP TRIGGER IF EXISTS trg_coach_threads_updated_at ON coach.message_threads;
CREATE TRIGGER trg_coach_threads_updated_at
    BEFORE UPDATE ON coach.message_threads
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- =====================================================================
-- STORAGE BUCKETS
-- =====================================================================
INSERT INTO storage.buckets (id, name, public) VALUES ('profile-pictures', 'profile-pictures', true)  ON CONFLICT (id) DO NOTHING;
INSERT INTO storage.buckets (id, name, public) VALUES ('coach-assets',     'coach-assets',     false) ON CONFLICT (id) DO NOTHING;

DROP POLICY IF EXISTS "Public Profile Pictures Access"                   ON storage.objects;
DROP POLICY IF EXISTS "Authenticated users can upload profile pictures"  ON storage.objects;
DROP POLICY IF EXISTS "Authenticated users can update profile pictures"  ON storage.objects;
DROP POLICY IF EXISTS "Coach assets — owner access"                      ON storage.objects;

CREATE POLICY "Public Profile Pictures Access"
    ON storage.objects FOR SELECT USING (bucket_id = 'profile-pictures');
CREATE POLICY "Authenticated users can upload profile pictures"
    ON storage.objects FOR INSERT WITH CHECK (bucket_id = 'profile-pictures' AND auth.role() = 'authenticated');
CREATE POLICY "Authenticated users can update profile pictures"
    ON storage.objects FOR UPDATE USING (bucket_id = 'profile-pictures' AND auth.role() = 'authenticated');
CREATE POLICY "Coach assets — owner access"
    ON storage.objects FOR ALL USING (bucket_id = 'coach-assets' AND auth.role() = 'authenticated');


-- =====================================================================
-- SEED DATA
-- =====================================================================
INSERT INTO public.groups (id, name, description, is_public, created_by) VALUES
    ('00000000-0000-0000-0000-000000000001'::UUID, 'Fitness & Workouts',       'Share daily workouts that match your calorie goals, keep each other accountable.', TRUE, NULL),
    ('00000000-0000-0000-0000-000000000002'::UUID, 'New to Calorie Tracking',  'Beginner questions, quick meal tips, tracking shortcuts, and celebrating first wins.', TRUE, NULL),
    ('00000000-0000-0000-0000-000000000003'::UUID, 'Muscle Gain & Bulking',    'Strategies for eating in a clean surplus, protein recipes, and heavy weight lifting.', TRUE, NULL),
    ('00000000-0000-0000-0000-000000000004'::UUID, 'Clean Fasting Habits',     'Share your intermittent fasting protocols, water fasting tips, and support.', TRUE, NULL)
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.challenges (title, description, target_workouts, points)
VALUES ('7-Day Core Crusher', 'Complete 5 core workouts this week to earn the exclusive Golden Abs badge.', 5, 500)
ON CONFLICT DO NOTHING;


-- =====================================================================
-- GRANT coach schema to authenticated + service_role
-- =====================================================================
GRANT USAGE ON SCHEMA coach TO authenticated, service_role;
GRANT ALL   ON ALL TABLES    IN SCHEMA coach TO authenticated, service_role;
GRANT ALL   ON ALL SEQUENCES IN SCHEMA coach TO authenticated, service_role;

ALTER DEFAULT PRIVILEGES IN SCHEMA coach GRANT ALL ON TABLES    TO authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA coach GRANT ALL ON SEQUENCES TO authenticated, service_role;
