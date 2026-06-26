from fastapi import Header, HTTPException, status
from typing import Optional
from app.database.supabase import supabase_client, is_supabase_live
from app.core.exceptions import UnauthorizedException
from app.core.security import extract_token

def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """Extracts user_id from Bearer token. Supports Supabase validation & mock tokens."""
    token = extract_token(authorization)
    
    # Mock authentication handling for local testing
    if token.startswith("mock-user-"):
        return token.replace("mock-user-", "")
    
    # Supabase authentication
    if is_supabase_live() and supabase_client:
        try:
            res = supabase_client.auth.get_user(token)
            if res and res.user:
                return res.user.id
        except Exception as e:
            raise UnauthorizedException(detail="Invalid session token")
            
    # Local fallback: treat the token itself as the local mock userId
    return token
