from typing import Optional
from app.repositories.db_repository import db_repository
from app.schemas.workouts import WorkoutLogRequest
from app.core.exceptions import NotFoundException
from datetime import datetime

class WorkoutService:
    def get_workouts(self, user_id: str, page: int, limit: int, date: Optional[str]) -> dict:
        offset = (page - 1) * limit
        data = db_repository.get_workouts(user_id, date, offset, limit)
        return {"success": True, "data": data}

    def log_workout(self, user_id: str, payload: WorkoutLogRequest) -> dict:
        date_str = payload.date
        completed_at = f"{date_str}T12:00:00.000Z" if date_str else datetime.utcnow().isoformat() + "Z"
        
        db_payload = {
            "user_id": user_id,
            "workout_name": payload.workout_name,
            "distance": payload.distance,
            "duration_seconds": payload.duration_seconds,
            "calories": payload.calories,
            "route_points": payload.route_points,
            "workout_type": payload.workout_type,
            "category": payload.category,
            "exercises": [e.model_dump() for e in payload.exercises] if payload.exercises else None,
            "completed": True,
            "completed_at": completed_at
        }
        res = db_repository.create_workout(user_id, db_payload)
        return {"success": True, "data": res}

    def delete_workout(self, user_id: str, workout_id: str) -> dict:
        success = db_repository.delete_workout(user_id, workout_id)
        if not success:
            raise NotFoundException(detail="Workout not found")
        return {"success": True}

workout_service = WorkoutService()
