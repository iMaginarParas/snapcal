"""
Supabase client — Single Shared Project (Option A)
===================================================
SabTrack  → `public` schema  (nutrition, meals, exercises, users)
SabCoach  → `coach`  schema  (clients, programs, workouts, check-ins)

Both products use the same Supabase project URL, anon key, and service-role
key. Tenant isolation is enforced by Row-Level Security (RLS) policies on each
schema. No separate Supabase project is needed.
"""

from app.core.logging import logger

_supabase_client = None
_supabase_available = False


def _init_supabase():
    global _supabase_client, _supabase_available
    try:
        from supabase import create_client
        from app.core.config import settings

        import os
        url = (
            settings.SUPABASE_URL
            or os.getenv("SUPABASE_URL")
            or os.getenv("SUPABASE_URL_COACH")
            or os.getenv("SUPABASE_URL_TRACK")
            or ""
        )
        key = (
            settings.SUPABASE_SERVICE_ROLE_KEY
            or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            or os.getenv("SUPABASE_SERVICE_ROLE_KEY_TRACK")
            or os.getenv("SUPABASE_SERVICE_ROLE_KEY_COACH")
            or settings.SUPABASE_ANON_KEY
            or os.getenv("SUPABASE_ANON_KEY")
            or os.getenv("SUPABASE_ANON_KEY_TRACK")
            or os.getenv("SUPABASE_ANON_KEY_COACH")
            or ""
        )

        if not url or not key or "your_supabase" in url or "your_supabase" in key:
            logger.warning(
                "Supabase credentials not configured — set SUPABASE_URL, "
                "SUPABASE_ANON_KEY (and optionally SUPABASE_SERVICE_ROLE_KEY) "
                "in your .env file or Railway variables. Backend will run with local fallback functionality."
            )
            return None

        client = create_client(url, key)
        _supabase_available = True
        logger.info("Supabase client initialised successfully (shared project, dual-schema).")
        return client
    except Exception as e:
        logger.error(f"Supabase initialisation failed: {e}")
        return None


# Singleton — instantiated once at import time; does NOT crash the server.
supabase_client = _init_supabase()


# ── Accessors ─────────────────────────────────────────────────────────────────

def get_track_supabase():
    """Return the shared client for SabTrack (public schema)."""
    return supabase_client


def get_coach_supabase():
    """Return the shared client for SabCoach (coach schema)."""
    return supabase_client


def get_supabase_client(product: str = "track"):
    """Generic accessor — both products use the same client."""
    return supabase_client


# ── Health checks ─────────────────────────────────────────────────────────────

def is_supabase_live() -> bool:
    return _supabase_available and supabase_client is not None


def is_coach_supabase_live() -> bool:
    """Coach uses the same client; healthy if the shared client is live."""
    return is_supabase_live()
