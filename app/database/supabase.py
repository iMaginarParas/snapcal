from supabase import create_client, Client
from app.core.config import settings
from app.core.logging import logger

def get_supabase_client() -> Client:
    if not settings.SUPABASE_URL or not settings.supabase_key:
        raise ValueError("Critical Configuration Error: SUPABASE_URL and SUPABASE_ANON_KEY must be configured in environment variables.")
        
    if "your_supabase" in settings.SUPABASE_URL or "your_supabase" in settings.supabase_key:
        raise ValueError("Critical Configuration Error: Default placeholder Supabase credentials detected. Please configure real database credentials in your .env file.")
        
    try:
        return create_client(settings.SUPABASE_URL, settings.supabase_key)
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        raise e

# Exported live client instance
supabase_client: Client = get_supabase_client()

def is_supabase_live() -> bool:
    return supabase_client is not None
