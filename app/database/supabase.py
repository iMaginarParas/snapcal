from supabase import create_client, Client
from app.core.config import settings
from app.core.logging import logger

def get_supabase_client() -> Client | None:
    if not settings.SUPABASE_URL or not settings.supabase_key:
        logger.warning("Supabase credentials not fully configured. Running in fallback mode.")
        return None
        
    try:
        return create_client(settings.SUPABASE_URL, settings.supabase_key)
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None

supabase_client = get_supabase_client()

def is_supabase_live() -> bool:
    return supabase_client is not None
