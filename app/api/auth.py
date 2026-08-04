from fastapi import APIRouter
from pydantic import BaseModel
from app.schemas.auth import SignupRequest, LoginRequest, GoogleLoginRequest
from app.services.auth.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

class ForgotPasswordRequest(BaseModel):
    email: str

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

