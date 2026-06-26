from fastapi import Header, HTTPException, status
from typing import Optional

def extract_token(authorization: Optional[str] = Header(None)) -> str:
    """Extracts token from Bearer header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header with Bearer token is required"
        )
    return authorization.split(" ")[1]
