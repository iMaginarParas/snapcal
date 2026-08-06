import logging
from app.core.logging import logger

_supabase_client = None
_supabase_available = False


def _init_supabase():
    global _supabase_client, _supabase_available
    try:
        from supabase import create_client
        from app.core.config import settings

        url = settings.SUPABASE_URL or ""
        key = settings.supabase_key or ""

        if (
            not url or not key
            or "your_supabase" in url
            or "your_supabase" in key
        ):
            logger.warning(
                "Supabase credentials not configured. "
                "Meals will be stored in local file fallback. "
                "Set SUPABASE_URL and SUPABASE_ANON_KEY in backend/.env to enable cloud persistence."
            )
            return None

        client = create_client(url, key)
        _supabase_available = True
        logger.info("Supabase client initialized successfully.")
        return client
    except Exception as e:
        logger.error(f"Supabase initialization failed: {e}")
        return None


# Lazy singleton — does NOT crash server on import
supabase_client = _init_supabase()


def is_supabase_live() -> bool:
    return _supabase_available and supabase_client is not None
