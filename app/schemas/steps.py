from pydantic import BaseModel
from typing import Optional

class StepsSyncRequest(BaseModel):
    date: str  # YYYY-MM-DD
    sensor_steps: int
    health_connect_steps: int
    final_steps: int
    distance: float  # km
    calories: int
    active_minutes: int
    baseline: int
    last_sensor_value: int
