from pydantic import BaseModel
from typing import Optional

class DailyStatsUpdateRequest(BaseModel):
    date: Optional[str] = None
    steps: Optional[int] = None
    water_ml: Optional[int] = None

class MeasurementLogRequest(BaseModel):
    metric_type: str  # 'weight', 'waist', 'chest', 'arms', 'thighs', 'strength'
    value: float
    date: Optional[str] = None
