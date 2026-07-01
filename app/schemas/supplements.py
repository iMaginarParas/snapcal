from pydantic import BaseModel, Field
from typing import Optional

class SupplementCreate(BaseModel):
    name: str = Field(..., description="Supplement name, e.g., Vitamin D3")
    dosage: Optional[str] = Field(None, description="Dosage details, e.g., 1 capsule or 5000 IU")
    time: str = Field(..., description="Time of day in HH:MM format, e.g., 08:30")

class SupplementResponse(BaseModel):
    id: str
    user_id: str
    name: str
    dosage: Optional[str] = None
    time: str
    created_at: Optional[str] = None
