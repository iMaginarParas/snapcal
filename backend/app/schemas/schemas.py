from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date

# Auth Schemas
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(UserBase):
    password: str

class UserProfileUpdate(BaseModel):
    height: Optional[float] = None
    weight: Optional[float] = None
    age: Optional[int] = None
    gender: Optional[str] = None

class UserOut(UserBase):
    id: int
    height: Optional[float]
    weight: Optional[float]
    age: Optional[int]
    gender: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# Meal Schemas
class MealBase(BaseModel):
    food_name: str
    calories: float
    protein: float
    carbs: float
    fat: float
    portion_size: Optional[str] = None

class MealCreate(MealBase):
    image_url: Optional[str] = None

class MealOut(MealBase):
    id: int
    user_id: int
    image_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# Step Schemas
class StepBase(BaseModel):
    step_count: int
    distance: float
    calories_burned: float

class StepCreate(StepBase):
    date: date

class StepOut(StepBase):
    id: int
    user_id: int
    date: date

    class Config:
        from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Device/Push Gechemas
class DeviceTokenCreate(BaseModel):
    token: str
    platform: Optional[str] = "android"
