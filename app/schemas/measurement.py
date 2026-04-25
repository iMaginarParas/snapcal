from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MeasurementBase(BaseModel):
    chest: Optional[float] = None
    waist: Optional[float] = None
    hips: Optional[float] = None
    neck: Optional[float] = None
    shoulders: Optional[float] = None
    left_bicep: Optional[float] = None
    right_bicep: Optional[float] = None
    left_thigh: Optional[float] = None
    right_thigh: Optional[float] = None
    left_calf: Optional[float] = None
    right_calf: Optional[float] = None

class MeasurementCreate(MeasurementBase):
    pass

class MeasurementResponse(MeasurementBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
