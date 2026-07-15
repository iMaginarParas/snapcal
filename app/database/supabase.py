from supabase import create_client, Client
from app.core.config import settings
from app.core.logging import logger

def get_supabase_client() -> Client:
    if not settings.SUPABASE_URL or not settings.supabase_key:
        raise ValueError("CRITICAL: Supabase credentials not fully configured. Running in production mode requires valid credentials.")
        
    if "your_supabase" in settings.SUPABASE_URL or "your_supabase" in settings.supabase_key:
        raise ValueError("CRITICAL: Supabase credentials are using default placeholders. Running in production mode requires valid credentials.")
        
    try:
        return create_client(settings.SUPABASE_URL, settings.supabase_key)
    except Exception as e:
        raise ValueError(f"CRITICAL: Failed to initialize Supabase client: {e}")

supabase_client = get_supabase_client()

def is_supabase_live() -> bool:
    return True
