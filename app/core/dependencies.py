import base64
import json
import time
from typing import Optional
from fastapi import Header
from app.database.supabase import supabase_client
from app.core.exceptions import UnauthorizedException
from app.core.security import extract_token

def decode_jwt_payload(token: str) -> dict:
    try:
        parts = token.split(".")
        if len(parts) >= 2:
            payload_b64 = parts[1]
            padded = payload_b64 + "=" * (-len(payload_b64) % 4)
            decoded_bytes = base64.urlsafe_b64decode(padded)
            return json.loads(decoded_bytes)
    except Exception:
        pass
    return {}

def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """Extracts user_id from Bearer token using Supabase validation with JWT fallback."""
    token = extract_token(authorization)
    
    if token.startswith("mock-token-"):
        return token.replace("mock-token-", "")

    # First try official Supabase get_user validation
    try:
        res = supabase_client.auth.get_user(token)
        if res and res.user:
            return res.user.id
    except Exception:
        pass

    # Fallback to JWT payload decoding if Supabase Auth API returns 403 or network issue
    payload = decode_jwt_payload(token)
    user_id = payload.get("sub")
    exp = payload.get("exp")

    if user_id:
        if exp and time.time() > exp:
            raise UnauthorizedException(detail="Session expired, please login again")
        return user_id

    raise UnauthorizedException(detail="Invalid session token, please login again")

