from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date

# Auth Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(UserBase):
    password: str

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
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
    is_pro: bool
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
    fiber: Optional[float] = 0.0
    sugar: Optional[float] = 0.0
    sodium: Optional[float] = 0.0
    cholesterol: Optional[float] = 0.0
    potassium: Optional[float] = 0.0
    saturates: Optional[float] = 0.0
    portion_size: Optional[str] = None

class MealCreate(MealBase):
    image_url: Optional[str] = None

class MealOut(MealBase):
    id: int
    user_id: int
    image_url: Optional[str]
    status: str
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

class MealManualCreate(BaseModel):
    food_name: str
    calories: float
    protein: float = 0
    carbs: float = 0
    fat: float = 0

# Water Schemas
class WaterCreate(BaseModel):
    amount_ml: int
    date: date

class WaterOut(BaseModel):
    id: int
    amount_ml: int
    date: date

    class Config:
        from_attributes = True

# Progress Schemas
class ProgressPhotoCreate(BaseModel):
    weight: Optional[float] = None
    description: Optional[str] = None

class ProgressPhotoOut(BaseModel):
    id: int
    image_url: str
    weight: Optional[float]
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# Exercise Schemas
class ExerciseBase(BaseModel):
    name: str
    duration_minutes: int
    calories_burned: float
    date: date

class ExerciseCreate(ExerciseBase):
    pass

class ExerciseOut(ExerciseBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
