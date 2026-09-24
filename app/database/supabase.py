import logging
from typing import Optional
from app.core.logging import logger

_supabase_track_client = None
_supabase_track_available = False

_supabase_coach_client = None
_supabase_coach_available = False


def _init_track_supabase():
    global _supabase_track_client, _supabase_track_available
    try:
        from supabase import create_client
        from app.core.config import settings

        url = settings.track_supabase_url
        key = settings.track_supabase_key

        if (
            not url or not key
            or "your_supabase" in url
            or "your_supabase" in key
        ):
            logger.warning(
                "SabTrack Supabase credentials not configured. "
                "Meals will be stored in local file fallback."
            )
            return None

        client = create_client(url, key)
        _supabase_track_available = True
        logger.info("SabTrack Supabase client initialized successfully.")
        return client
    except Exception as e:
        logger.error(f"SabTrack Supabase initialization failed: {e}")
        return None


def _init_coach_supabase():
    global _supabase_coach_client, _supabase_coach_available
    try:
        from supabase import create_client
        from app.core.config import settings

        url = settings.coach_supabase_url
        key = settings.coach_supabase_key

        if (
            not url or not key
            or "your_supabase" in url
            or "your_supabase" in key
        ):
            logger.warning(
                "SabCoach Supabase credentials not configured. "
                "Coach ecosystem will use local file fallback."
            )
            return None

        client = create_client(url, key)
        _supabase_coach_available = True
        logger.info("SabCoach Supabase client initialized successfully.")
        return client
    except Exception as e:
        logger.error(f"SabCoach Supabase initialization failed: {e}")
        return None


# Lazy singletons — do NOT crash server on import
supabase_track_client = _init_track_supabase()
supabase_coach_client = _init_coach_supabase()

# Backward compatibility alias
supabase_client = supabase_track_client or supabase_coach_client


def get_track_supabase():
    return supabase_track_client


def get_coach_supabase():
    return supabase_coach_client or supabase_track_client


def get_supabase_client(product: str = "track"):
    if product.lower() in ("coach", "sabcoach"):
        return get_coach_supabase()
    return get_track_supabase()


def is_supabase_live() -> bool:
    return _supabase_track_available and supabase_track_client is not None


def is_coach_supabase_live() -> bool:
    return _supabase_coach_available and supabase_coach_client is not None
