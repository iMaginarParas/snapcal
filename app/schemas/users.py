from pydantic import BaseModel
from typing import Optional

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    age: Optional[int] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    goals: Optional[str] = None
    gender: Optional[str] = None
    activity_level: Optional[str] = None
    target_weight: Optional[float] = None
    goal: Optional[str] = None

