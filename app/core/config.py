import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App config
    PROJECT_NAME: str = "SABTRACK AI Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    PORT: int = int(os.getenv("PORT", 3000))

    # ─────────────────────────────────────────────────────────────────────
    # Supabase — Single Shared Project (Option A)
    # SabTrack uses the `public` schema.
    # SabCoach uses the `coach` schema.
    # Both share the same Supabase project URL, anon key, service role key,
    # and JWT secret. Schema separation + RLS enforce tenant isolation.
    # ─────────────────────────────────────────────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None  # Dashboard → Settings → API → JWT Secret

    # AI Config
    GEMINI_API_KEY: str = ""

    # Razorpay Config
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── Convenience properties (both products → same single project) ──

    @property
    def track_supabase_url(self) -> str:
        """URL for the shared Supabase project (SabTrack uses `public` schema)."""
        return self.SUPABASE_URL

    @property
    def track_supabase_key(self) -> str:
        """Prefer service-role key for backend ops; fall back to anon key."""
        return self.SUPABASE_SERVICE_ROLE_KEY or self.SUPABASE_ANON_KEY or ""

    @property
    def coach_supabase_url(self) -> str:
        """URL for the shared Supabase project (SabCoach uses `coach` schema)."""
        return self.SUPABASE_URL

    @property
    def coach_supabase_key(self) -> str:
        """Prefer service-role key for backend ops; fall back to anon key."""
        return self.SUPABASE_SERVICE_ROLE_KEY or self.SUPABASE_ANON_KEY or ""

    @property
    def supabase_key(self) -> str:
        return self.track_supabase_key


settings = Settings()
