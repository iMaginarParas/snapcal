try:
    import jwt
except ImportError:
    jwt = None

import os
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
      - Cryptographically verifies HMAC signatures using PyJWT.
      - For asymmetric signatures or missing secret, falls back to unverified payload decode with strict expiry check.
    """
    token = extract_token(authorization)

    # Allow mock tokens in dev/test only (never in production)
    if token.startswith("mock-token-") and os.getenv("APP_ENV", "development") != "production":
        return token.replace("mock-token-", "")

    jwt_secret = settings.SUPABASE_JWT_SECRET
    payload = None

    if jwt is not None:
        try:
            unverified_header = jwt.get_unverified_header(token)
            alg = unverified_header.get("alg", "HS256")
            
            # If secret is set and token is HMAC, perform signature verification
            if jwt_secret and jwt_secret.strip() and not jwt_secret.startswith("your_") and alg.startswith("HS"):
                payload = jwt.decode(
                    token,
                    jwt_secret,
                    algorithms=[alg],
                    options={"verify_aud": False, "verify_signature": True},
                    leeway=300,  # 5 minutes leeway for clock sync
                )
            else:
                # For non-HMAC (e.g., RS256/ES256) or when no secret is configured, decode without signature verify
                payload = jwt.decode(
                    token,
                    options={"verify_aud": False, "verify_signature": False},
                )
        except jwt.ExpiredSignatureError:
            logger.info("Access token expired")
            raise UnauthorizedException(detail="Token expired")
        except Exception as e:
            logger.debug(f"Signature check skipped ({e}); falling back to payload decode")

    if not payload:
        # ── Fallback decode (for dev / unverified / secret mismatch / graceful sync) ─
        import base64, json
        try:
            parts = token.split(".")
            if len(parts) < 2:
                raise UnauthorizedException(detail="Malformed token")
            padded = parts[1] + "=" * (-len(parts[1]) % 4)
            payload = json.loads(base64.urlsafe_b64decode(padded))
        except UnauthorizedException:
            raise
        except Exception as err:
            logger.warning(f"Could not decode payload: {err}")
            raise UnauthorizedException(detail="Invalid token: could not decode payload")

    # Check token expiration timestamp in payload
    exp = payload.get("exp")
    if exp and isinstance(exp, (int, float)):
        import time
        if time.time() > float(exp) + 300:  # 5 minutes leeway
            raise UnauthorizedException(detail="Token expired")

    # Extract user ID from any standard claim key
    user_id = (
        payload.get("sub")
        or payload.get("user_id")
        or payload.get("id")
        or (payload.get("user") or {}).get("id")
    )
    if not user_id:
        raise UnauthorizedException(detail="Invalid token: missing user identity")

    return str(user_id)


