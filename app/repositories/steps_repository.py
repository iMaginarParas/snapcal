from typing import Dict, Any, List, Optional
from datetime import datetime
from app.database.supabase import supabase_client

class StepsRepository:
    def get_steps_by_date(self, user_id: str, date_str: str) -> Optional[Dict[str, Any]]:
        """Retrieves daily step counts for a user on a specific date."""
        res = supabase_client.from_("daily_steps").select("*").eq("user_id", user_id).eq("date", date_str).maybe_single().execute()
        return res.data if res else None

    def get_steps_history(self, user_id: str, start_date_str: str, end_date_str: str) -> List[Dict[str, Any]]:
        """Retrieves steps history for a date range."""
        res = supabase_client.from_("daily_steps").select("*").eq("user_id", user_id).gte("date", start_date_str).lte("date", end_date_str).order("date", desc=False).execute()
        return res.data if res else []

    def sync_steps(self, user_id: str, sync_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronizes step updates and resolves conflicts by keeping the maximum step count.
        """
        date_str = sync_data["date"]
        existing = self.get_steps_by_date(user_id, date_str)

        if existing:
            # Resolve conflict: today's steps = max(local_steps, sync_steps)
            new_final = max(existing.get("final_steps") or 0, sync_data.get("final_steps") or 0)
            new_sensor = max(existing.get("sensor_steps") or 0, sync_data.get("sensor_steps") or 0)
            new_hc = max(existing.get("health_connect_steps") or 0, sync_data.get("health_connect_steps") or 0)
            
            # Keep highest calories, distance, active minutes, and latest sync values
            update_data = {
                "sensor_steps": new_sensor,
                "health_connect_steps": new_hc,
                "final_steps": new_final,
                "distance": max(float(existing.get("distance") or 0.0), float(sync_data.get("distance") or 0.0)),
                "calories": max(int(existing.get("calories") or 0), int(sync_data.get("calories") or 0)),
                "active_minutes": max(int(existing.get("active_minutes") or 0), int(sync_data.get("active_minutes") or 0)),
                "baseline": sync_data.get("baseline") or existing.get("baseline") or 0,
                "last_sensor_value": max(int(existing.get("last_sensor_value") or 0), int(sync_data.get("last_sensor_value") or 0)),
                "last_sync": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z"
            }
            
            res = supabase_client.from_("daily_steps").update(update_data).eq("id", existing["id"]).execute()
            return res.data[0] if res and res.data else {}
        else:
            # Insert new record
            insert_data = {
                "user_id": user_id,
                "date": date_str,
                "sensor_steps": sync_data["sensor_steps"],
                "health_connect_steps": sync_data["health_connect_steps"],
                "final_steps": sync_data["final_steps"],
                "distance": float(sync_data["distance"]),
                "calories": int(sync_data["calories"]),
                "active_minutes": int(sync_data["active_minutes"]),
                "baseline": sync_data["baseline"],
                "last_sensor_value": sync_data["last_sensor_value"],
                "last_sync": datetime.utcnow().isoformat() + "Z",
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z"
            }
            
            res = supabase_client.from_("daily_steps").insert(insert_data).execute()
            return res.data[0] if res and res.data else {}

steps_repository = StepsRepository()
