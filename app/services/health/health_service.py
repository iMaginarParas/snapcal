from typing import Optional
from app.repositories.db_repository import db_repository
from app.schemas.health import DailyStatsUpdateRequest, MeasurementLogRequest
from app.core.exceptions import NotFoundException
from datetime import datetime

class HealthService:
    def get_daily_stats(self, user_id: str, date: Optional[str]) -> dict:
        date_str = date or datetime.utcnow().isoformat().split("T")[0]
        stats = db_repository.get_daily_stats(user_id, date_str)
        if stats:
            return {"success": True, "data": stats}
            
        new_stats = {"user_id": user_id, "date": date_str, "steps": 0, "water_ml": 0}
        res = db_repository.create_daily_stats(new_stats)
        return {"success": True, "data": res}

    def update_daily_stats(self, user_id: str, payload: DailyStatsUpdateRequest) -> dict:
        date_str = payload.date or datetime.utcnow().isoformat().split("T")[0]
        updates = {}
        if payload.steps is not None:
            updates["steps"] = payload.steps
        if payload.water_ml is not None:
            updates["water_ml"] = payload.water_ml
            
        stats = db_repository.get_daily_stats(user_id, date_str)
        if stats:
            res = db_repository.update_daily_stats(user_id, date_str, updates)
        else:
            ins_payload = {"user_id": user_id, "date": date_str, "steps": updates.get("steps", 0), "water_ml": updates.get("water_ml", 0)}
            res = db_repository.create_daily_stats(ins_payload)
        return {"success": True, "data": res}

    def get_measurements(self, user_id: str, metric_type: Optional[str]) -> dict:
        logs = db_repository.get_measurements(user_id, metric_type)
        return {"success": True, "data": logs}

    def log_measurement(self, user_id: str, payload: MeasurementLogRequest) -> dict:
        now = datetime.utcnow()
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        formatted_date = payload.date or f"{months[now.month-1]} {str(now.day).zfill(2)}, {now.year}"
        
        db_payload = {
            "user_id": user_id,
            "metric_type": payload.metric_type,
            "value": payload.value,
            "date": formatted_date,
            "logged_at": now.isoformat() + "Z"
        }
        res = db_repository.log_measurement(user_id, db_payload)
        return {"success": True, "data": res}

    def delete_measurement(self, user_id: str, id: str) -> dict:
        success = db_repository.delete_measurement(user_id, id)
        if not success:
            raise NotFoundException(detail="Measurement log not found")
        return {"success": True}

health_service = HealthService()
