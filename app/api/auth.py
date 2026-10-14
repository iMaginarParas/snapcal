from fastapi import APIRouter, Header
from typing import Optional
from pydantic import BaseModel
from app.schemas.auth import SignupRequest, LoginRequest, GoogleLoginRequest
from app.services.auth.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

class ForgotPasswordRequest(BaseModel):
    email: str
    redirect_to: Optional[str] = None

class UpdatePasswordRequest(BaseModel):
    password: str

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

@router.get("/oauth/google-url")
def auth_google_oauth_url(redirect_to: str):
    return auth_service.get_google_oauth_url(redirect_to)

@router.post("/forgot-password")
def auth_forgot_password(payload: ForgotPasswordRequest):
    return auth_service.forgot_password(payload.email, payload.redirect_to)

@router.post("/reset-password")
@router.post("/update-password")
def auth_update_password(payload: UpdatePasswordRequest, authorization: Optional[str] = Header(None)):
    return auth_service.update_password(payload.password, authorization)

@router.post("/refresh")
def auth_refresh(payload: RefreshRequest):
    """Exchange a refresh_token for a new access_token. Called automatically by the app when a 401 is received."""
    return auth_service.refresh_session(payload.refresh_token)

class ProvisionCoachRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None
    role: Optional[str] = "Coach"
    practice_name: Optional[str] = None
    admin_key: Optional[str] = None

@router.post("/admin/provision-coach")
def auth_admin_provision_coach(payload: ProvisionCoachRequest):
    """Admin endpoint to provision credentials for a new coach profile."""
    from datetime import datetime
    from app.repositories.coach_repository import coach_repo

    res = auth_service.provision_coach(
        email=payload.email,
        password=payload.password,
        name=payload.name,
        role=payload.role,
        practice_name=payload.practice_name
    )

    coach_id = (res.get("data") or {}).get("id") or f"coach_{payload.email.split('@')[0]}"
    coach_profile = {
        "id": coach_id,
        "name": payload.name or "Coach",
        "email": payload.email,
        "role": payload.role or "Coach",
        "practice_name": payload.practice_name or "SabCoach Practice",
        "status": "pending_onboarding",
        "created_at": datetime.utcnow().isoformat()
    }
    coach_repo.save_profile(coach_id, coach_profile)
    res["user"] = {"id": coach_id, "email": payload.email, "name": payload.name}
    return res

@router.get("/me")
def auth_me(authorization: Optional[str] = Header(None)):
    """Returns the current user's id decoded from their JWT token."""
    from app.core.dependencies import get_current_user_id
    user_id = get_current_user_id(authorization)
    return {"success": True, "user_id": user_id}

