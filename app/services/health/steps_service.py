from typing import Dict, Any, List
from app.repositories.steps_repository import steps_repository
from app.repositories.db_repository import db_repository
from app.schemas.steps import StepsSyncRequest
from datetime import datetime

class StepsService:
    def sync_steps(self, user_id: str, payload: StepsSyncRequest) -> dict:
        """Syncs daily step logs and updates both step history and daily stats summary."""
        # 1. Sync steps log
        sync_result = steps_repository.sync_steps(user_id, payload.dict())
        
        # 2. Update stats summary for compatibility (steps count updates inside daily_stats table)
        try:
            date_str = payload.date
            existing_stats = db_repository.get_daily_stats(user_id, date_str)
            if existing_stats:
                # Merge: Keep highest steps count
                new_steps = max(existing_stats.get("steps") or 0, payload.final_steps)
                db_repository.update_daily_stats(user_id, date_str, {"steps": new_steps})
            else:
                db_repository.create_daily_stats({
                    "user_id": user_id,
                    "date": date_str,
                    "steps": payload.final_steps,
                    "water_ml": 0
                })
        except Exception as e:
            print(f"StepsService: Failed to update daily_stats summary: {e}")

        return {"success": True, "data": sync_result}

    def get_daily_steps(self, user_id: str, date_str: str) -> dict:
        steps_record = steps_repository.get_steps_by_date(user_id, date_str)
        if not steps_record:
            # Return a default empty steps log
            steps_record = {
                "user_id": user_id,
                "date": date_str,
                "sensor_steps": 0,
                "health_connect_steps": 0,
                "final_steps": 0,
                "distance": 0.0,
                "calories": 0,
                "active_minutes": 0,
                "baseline": 0,
                "last_sensor_value": 0
            }
        return {"success": True, "data": steps_record}

    def get_steps_history(self, user_id: str, days: int = 7) -> dict:
        end_date = datetime.utcnow().date()
        from datetime import timedelta
        start_date = end_date - timedelta(days=days - 1)
        
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        history = steps_repository.get_steps_history(user_id, start_str, end_str)
        return {"success": True, "data": history}

steps_service = StepsService()
