from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.schemas.workouts import WorkoutLogRequest
from app.services.workouts.workout_service import workout_service
from app.core.dependencies import get_current_user_id

router = APIRouter(prefix="/workouts", tags=["Workouts"])

@router.get("")
def get_workouts(
    page: int = Query(1),
    limit: int = Query(20),
    date: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user_id)
):
    return workout_service.get_workouts(user_id, page, limit, date)

@router.post("")
def log_workout(payload: WorkoutLogRequest, user_id: str = Depends(get_current_user_id)):
    return workout_service.log_workout(user_id, payload)

@router.delete("/{id}")
def delete_workout(id: str, user_id: str = Depends(get_current_user_id)):
    return workout_service.delete_workout(user_id, id)
