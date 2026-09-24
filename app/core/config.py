import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App config
    PROJECT_NAME: str = "SABTRACK AI Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    PORT: int = int(os.getenv("PORT", 3000))
    
    # Supabase Config (Single / Legacy fallback)
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None  # From Supabase Dashboard → Settings → API → JWT Secret
    
    # Multi-Project Supabase Config (Railway deployment)
    SUPABASE_URL_TRACK: str = ""
    SUPABASE_ANON_KEY_TRACK: str = ""
    SUPABASE_SERVICE_ROLE_KEY_TRACK: Optional[str] = None

    SUPABASE_URL_COACH: str = ""
    SUPABASE_ANON_KEY_COACH: str = ""
    SUPABASE_SERVICE_ROLE_KEY_COACH: Optional[str] = None

    # AI Config
    GEMINI_API_KEY: str = ""

    # Razorpay Config
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def track_supabase_url(self) -> str:
        return self.SUPABASE_URL_TRACK or self.SUPABASE_URL or ""

    @property
    def track_supabase_key(self) -> str:
        return (
            self.SUPABASE_SERVICE_ROLE_KEY_TRACK
            or self.SUPABASE_ANON_KEY_TRACK
            or self.SUPABASE_SERVICE_ROLE_KEY
            or self.SUPABASE_ANON_KEY
            or ""
        )

    @property
    def coach_supabase_url(self) -> str:
        return self.SUPABASE_URL_COACH or self.SUPABASE_URL or ""

    @property
    def coach_supabase_key(self) -> str:
        return (
            self.SUPABASE_SERVICE_ROLE_KEY_COACH
            or self.SUPABASE_ANON_KEY_COACH
            or self.SUPABASE_SERVICE_ROLE_KEY
            or self.SUPABASE_ANON_KEY
            or ""
        )

    @property
    def supabase_key(self) -> str:
        return self.track_supabase_key

settings = Settings()
