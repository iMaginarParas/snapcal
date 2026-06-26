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
