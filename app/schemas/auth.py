from pydantic import BaseModel, EmailStr
from typing import Optional

class SignupRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class GoogleLoginRequest(BaseModel):
    idToken: str
    displayName: Optional[str] = None
    photoUrl: Optional[str] = None
    email: Optional[str] = None

class AppleLoginRequest(BaseModel):
    identity_token: str
    user_identifier: Optional[str] = None
    email: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
