from fastapi import Header, HTTPException, status
from typing import Optional
from app.database.supabase import supabase_client
from app.core.exceptions import UnauthorizedException
from app.core.security import extract_token

def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """Extracts user_id from Bearer token using Supabase validation."""
    token = extract_token(authorization)
    
    try:
        res = supabase_client.auth.get_user(token)
        if res and res.user:
            return res.user.id
        raise UnauthorizedException(detail="Invalid session token")
    except Exception:
        raise UnauthorizedException(detail="Invalid session token")
