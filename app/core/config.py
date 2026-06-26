import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App config
    PROJECT_NAME: str = "SABTRACK AI Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    PORT: int = int(os.getenv("PORT", 3000))
    
    # Supabase Config
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    
    # AI Config
    GEMINI_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def supabase_key(self) -> str:
        return self.SUPABASE_SERVICE_ROLE_KEY or self.SUPABASE_ANON_KEY or ""

settings = Settings()
