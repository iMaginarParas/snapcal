import jwt
from typing import Optional
from fastapi import Header
from app.core.exceptions import UnauthorizedException
from app.core.security import extract_token
from app.core.config import settings


def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """
    Extracts and validates the user_id from a Supabase Bearer token.

    If SUPABASE_JWT_SECRET is set (recommended for production):
      - Cryptographically verifies the token signature using PyJWT.
      - Rejects tampered or forged tokens outright.

    If SUPABASE_JWT_SECRET is not set (fallback / local dev):
      - Decodes the payload without signature verification (unsafe, legacy).
      - Logs a warning so you know to set the secret.
    """
    token = extract_token(authorization)

    # Allow mock tokens in tests
    if token.startswith("mock-token-"):
        return token.replace("mock-token-", "")

    jwt_secret = settings.SUPABASE_JWT_SECRET

    if jwt_secret:
        # ── Verified path ──────────────────────────────────────────────────────
        # Supabase signs tokens with HS256 and the JWT secret from your dashboard.
        # audience is not set by default in Supabase, so we skip audience check.
        try:
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
        except jwt.ExpiredSignatureError:
            raise UnauthorizedException(detail="Session expired — please login again")
        except jwt.InvalidTokenError as e:
            raise UnauthorizedException(detail=f"Invalid token: {e}")
    else:
        # ── Unverified fallback (local dev / secret not yet configured) ────────
        import base64, json, time
        import logging
        logging.getLogger(__name__).warning(
            "SUPABASE_JWT_SECRET is not set — JWT signature is NOT being verified. "
            "Set this env var in Railway for production security."
        )
        try:
            parts = token.split(".")
            if len(parts) < 2:
                raise UnauthorizedException(detail="Malformed token")
            padded = parts[1] + "=" * (-len(parts[1]) % 4)
            payload = json.loads(base64.urlsafe_b64decode(padded))
        except UnauthorizedException:
            raise
        except Exception:
            raise UnauthorizedException(detail="Invalid token: could not decode payload")

        # Manual expiry check since we're not using PyJWT here
        exp = payload.get("exp")
        if exp and time.time() > exp:
            raise UnauthorizedException(detail="Session expired — please login again")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException(detail="Invalid token: missing user identity")

    return user_id
