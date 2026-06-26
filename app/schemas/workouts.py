from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class WorkoutExercise(BaseModel):
    name: str
    sets: Optional[int] = 1
    reps: Optional[int] = None
    weight: Optional[float] = None
    duration_seconds: Optional[int] = None
    notes: Optional[str] = None

class WorkoutLogRequest(BaseModel):
    workout_name: str
    distance: Optional[float] = 0.0
    duration_seconds: Optional[int] = 0
    calories: Optional[int] = 0
    route_points: Optional[List[Dict[str, Any]]] = []
    workout_type: Optional[str] = "cardio"
    category: Optional[str] = None
    exercises: Optional[List[WorkoutExercise]] = []
    date: Optional[str] = None
