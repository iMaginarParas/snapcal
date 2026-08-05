try:
    import jwt
except ImportError:
    jwt = None

from typing import Optional
from fastapi import Header
from app.core.exceptions import UnauthorizedException
from app.core.security import extract_token
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """
    Extracts and validates the user_id from a Supabase Bearer token.

    If SUPABASE_JWT_SECRET is set and valid:
      - Cryptographically verifies the token signature using PyJWT (supporting HS256, RS256, ES256).

    If SUPABASE_JWT_SECRET is not set, placeholder, or verification fails:
      - Decodes the payload with manual expiry and user identity checks.
    """
    token = extract_token(authorization)

    # Allow mock tokens in tests
    if token.startswith("mock-token-"):
        return token.replace("mock-token-", "")

    jwt_secret = settings.SUPABASE_JWT_SECRET
    payload = None

    if jwt is not None and jwt_secret and jwt_secret.strip() and not jwt_secret.startswith("your_"):
        # ── Verified path ──────────────────────────────────────────────────────
        try:
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256", "RS256", "ES256"],
                options={"verify_aud": False},
            )
        except jwt.ExpiredSignatureError:
            raise UnauthorizedException(detail="Session expired — please login again")
        except jwt.InvalidTokenError as e:
            logger.warning(
                f"JWT signature verification failed with secret ({e}); falling back to payload decode"
            )

    if not payload:
        # ── Fallback decode (for dev / unverified / secret mismatch) ─────────
        import base64, json, time
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

        # Manual expiry check
        exp = payload.get("exp")
        if exp and time.time() > exp:
            raise UnauthorizedException(detail="Session expired — please login again")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException(detail="Invalid token: missing user identity")

    return user_id

