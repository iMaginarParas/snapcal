from fastapi import APIRouter, Header
from typing import Optional
from pydantic import BaseModel
from app.schemas.auth import SignupRequest, LoginRequest, GoogleLoginRequest
from app.services.auth.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

class ForgotPasswordRequest(BaseModel):
    email: str

class RefreshRequest(BaseModel):
    refresh_token: str

@router.post("/signup")
def auth_signup(payload: SignupRequest):
    return auth_service.signup(payload)

@router.post("/login")
def auth_login(payload: LoginRequest):
    return auth_service.login(payload)

@router.post("/google-login")
def auth_google_login(payload: GoogleLoginRequest):
    return auth_service.google_login(payload)

@router.post("/forgot-password")
def auth_forgot_password(payload: ForgotPasswordRequest):
    return auth_service.forgot_password(payload.email)

@router.post("/refresh")
def auth_refresh(payload: RefreshRequest):
    """Exchange a refresh_token for a new access_token. Called automatically by the app when a 401 is received."""
    return auth_service.refresh_session(payload.refresh_token)

@router.get("/me")
def auth_me(authorization: Optional[str] = Header(None)):
    """Returns the current user's id decoded from their JWT token."""
    from app.core.dependencies import get_current_user_id
    user_id = get_current_user_id(authorization)
    return {"success": True, "user_id": user_id}

