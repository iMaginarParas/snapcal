from typing import Dict, Any, List, Optional
from app.database.supabase import supabase_client, is_supabase_live
from app.database.fallback import fallback_db
from datetime import datetime
import uuid

class DBRepository:
    """Centralized database repository handling all Supabase and fallback queries."""

    # --- Users & Profiles ---
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not is_supabase_live():
            return fallback_db.get_user(user_id)
        res = supabase_client.from_("users").select("*").eq("id", user_id).single().execute()
        return res.data if res else None

    def create_user_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        if not is_supabase_live():
            fallback_db.update_user(profile["id"], profile)
            return profile
        res = supabase_client.from_("users").insert(profile).execute()
        return res.data[0] if res and res.data else {}

    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        if not is_supabase_live():
            return fallback_db.update_user(user_id, updates)
        res = supabase_client.from_("users").update(updates).eq("id", user_id).execute()
        return res.data[0] if res and res.data else {}

    def check_username_exists(self, username: str, exclude_user_id: str) -> bool:
        if not is_supabase_live():
            return False # Fallback doesn't strictly enforce unique usernames for now
        res = supabase_client.from_("users").select("id").eq("username", username).neq("id", exclude_user_id).execute()
        return bool(res.data)

    def get_calculated_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not is_supabase_live():
            return fallback_db.get_profile(user_id)
        res = supabase_client.from_("profiles").select("*").eq("user_id", user_id).maybe_single().execute()
        return res.data if res else None

    def upsert_calculated_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        profile_data["user_id"] = user_id
        if not is_supabase_live():
            return fallback_db.update_profile(user_id, profile_data)
        res = supabase_client.from_("profiles").upsert(profile_data).execute()
        return res.data[0] if res and res.data else {}

    def add_weight_history_entry(self, user_id: str, weight: float, bmi: float) -> Dict[str, Any]:
        if not is_supabase_live():
            return fallback_db.add_weight_history(user_id, weight, bmi)
        payload = {
            "user_id": user_id,
            "weight": weight,
            "bmi": bmi
        }
        res = supabase_client.from_("weight_history").insert(payload).execute()
        return res.data[0] if res and res.data else {}

    def get_weight_history_records(self, user_id: str) -> List[Dict[str, Any]]:
        if not is_supabase_live():
            return fallback_db.get_weight_history(user_id)
        res = supabase_client.from_("weight_history").select("*").eq("user_id", user_id).order("recorded_at", desc=False).execute()
        return res.data if res else []


    # --- Workouts ---
    def get_workouts(self, user_id: str, date: Optional[str] = None, offset: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        if not is_supabase_live():
            workouts = fallback_db.get_workouts(user_id)
            if date:
                workouts = [w for w in workouts if w.get("completed_at", "").split("T")[0] == date]
            return workouts[offset: offset + limit]
            
        query = supabase_client.from_("workouts").select("*").eq("user_id", user_id)
        if date:
            query = query.gte("completed_at", f"{date}T00:00:00.000Z").lte("completed_at", f"{date}T23:59:59.999Z")
        res = query.order("completed_at", desc=True).range(offset, offset + limit - 1).execute()
        return res.data if res else []

    def create_workout(self, user_id: str, workout_data: Dict[str, Any]) -> Dict[str, Any]:
        if not is_supabase_live():
            return fallback_db.add_workout(user_id, workout_data)
        res = supabase_client.from_("workouts").insert(workout_data).execute()
        return res.data[0] if res and res.data else {}

    def delete_workout(self, user_id: str, workout_id: str) -> bool:
        if not is_supabase_live():
            return fallback_db.delete_workout(user_id, workout_id)
        res = supabase_client.from_("workouts").delete().eq("id", workout_id).eq("user_id", user_id).execute()
        return bool(res.data) if res else False

    # --- Daily Stats ---
    def get_daily_stats(self, user_id: str, date_str: str) -> Optional[Dict[str, Any]]:
        if not is_supabase_live():
            return fallback_db.get_daily_stats(user_id, date_str)
        res = supabase_client.from_("daily_stats").select("*").eq("user_id", user_id).eq("date", date_str).maybe_single().execute()
        return res.data if res else None

    def create_daily_stats(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        if not is_supabase_live():
            return fallback_db.update_daily_stats(stats["user_id"], stats["date"], stats)
        res = supabase_client.from_("daily_stats").insert(stats).execute()
        return res.data[0] if res and res.data else {}

    def update_daily_stats(self, user_id: str, date_str: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        if not is_supabase_live():
            return fallback_db.update_daily_stats(user_id, date_str, updates)
        res = supabase_client.from_("daily_stats").update(updates).eq("user_id", user_id).eq("date", date_str).execute()
        return res.data[0] if res and res.data else {}

    # --- Measurements ---
    def get_measurements(self, user_id: str, metric_type: Optional[str] = None) -> List[Dict[str, Any]]:
        if not is_supabase_live():
            return fallback_db.get_measurements(user_id, metric_type)
        query = supabase_client.from_("measurement_logs").select("*").eq("user_id", user_id)
        if metric_type:
            query = query.eq("metric_type", metric_type)
        res = query.order("logged_at", desc=True).execute()
        return res.data

    def log_measurement(self, user_id: str, measurement: Dict[str, Any]) -> Dict[str, Any]:
        if not is_supabase_live():
            return fallback_db.add_measurement(user_id, measurement)
        res = supabase_client.from_("measurement_logs").insert(measurement).execute()
        return res.data[0] if res and res.data else {}

    def delete_measurement(self, user_id: str, measurement_id: str) -> bool:
        if not is_supabase_live():
            return fallback_db.delete_measurement(user_id, measurement_id)
        res = supabase_client.from_("measurement_logs").delete().eq("id", measurement_id).eq("user_id", user_id).execute()
        return bool(res.data) if res else False

    # --- Fasting Logs ---
    def get_active_fast(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not is_supabase_live():
            return fallback_db.get_active_fast(user_id)
        res = supabase_client.from_("fasting_logs").select("*").eq("user_id", user_id).eq("completed", False).maybe_single().execute()
        return res.data if res else None

    def start_fast(self, user_id: str, protocol: str) -> Dict[str, Any]:
        if not is_supabase_live():
            return fallback_db.start_fast(user_id, protocol)
        db_payload = {
            "user_id": user_id,
            "protocol": protocol,
            "start_time": datetime.utcnow().isoformat() + "Z",
            "completed": False
        }
        res = supabase_client.from_("fasting_logs").insert(db_payload).execute()
        return res.data[0] if res and res.data else {}

    def stop_fast(self, user_id: str, fast_id: str) -> Optional[Dict[str, Any]]:
        if not is_supabase_live():
            return fallback_db.stop_fast(user_id, fast_id)
        db_payload = {
            "completed": True,
            "end_time": datetime.utcnow().isoformat() + "Z"
        }
        res = supabase_client.from_("fasting_logs").update(db_payload).eq("id", fast_id).eq("user_id", user_id).execute()
        return res.data[0] if res and res.data else None

    # --- Meals & Food ---
    def get_meals(self, user_id: str, date_str: str) -> List[Dict[str, Any]]:
        if not is_supabase_live():
            return [m for m in fallback_db.get_meals(user_id) if m.get("logged_at", "").split("T")[0] == date_str]
        res = supabase_client.from_("meals").select("*, food_items(*)").eq("user_id", user_id).gte("logged_at", f"{date_str}T00:00:00.000Z").lte("logged_at", f"{date_str}T23:59:59.999Z").execute()
        return res.data if res else []

    def create_meal(self, meal_data: Dict[str, Any]) -> Dict[str, Any]:
        if not is_supabase_live():
            return fallback_db.add_meal(meal_data["user_id"], meal_data)
        res = supabase_client.from_("meals").insert(meal_data).execute()
        return res.data[0] if res and res.data else {}

    def create_food_items(self, food_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not is_supabase_live():
            return food_items # Handled in fallback_db.add_meal implicitly
        res = supabase_client.from_("food_items").insert(food_items).execute()
        return res.data

    # --- Groups & Challenges ---
    def get_groups(self, user_id: str) -> List[Dict[str, Any]]:
        if not is_supabase_live():
            return fallback_db.get_groups(user_id)
        res = supabase_client.from_("groups").select("*").execute()
        return res.data if res else []

    def create_group(self, group_data: Dict[str, Any]) -> Dict[str, Any]:
        if not is_supabase_live():
            return fallback_db.add_group(group_data)
        res = supabase_client.from_("groups").insert(group_data).execute()
        return res.data[0] if res and res.data else {}

    def get_challenges(self) -> List[Dict[str, Any]]:
        if not is_supabase_live():
            return fallback_db.get_challenges()
        res = supabase_client.from_("challenges").select("*").execute()
        return res.data if res else []

    def get_user_challenge(self, user_id: str, challenge_id: str) -> Optional[Dict[str, Any]]:
        if not is_supabase_live():
            return None # Not strictly implemented in fallback easily
        res = supabase_client.from_("user_challenges").select("*").eq("user_id", user_id).eq("challenge_id", challenge_id).maybe_single().execute()
        return res.data if res else None

    def create_user_challenge(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not is_supabase_live():
            return data
        res = supabase_client.from_("user_challenges").insert(data).execute()
        return res.data[0] if res and res.data else {}

    def update_user_challenge(self, challenge_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        if not is_supabase_live():
            return updates
        res = supabase_client.from_("user_challenges").update(updates).eq("id", challenge_id).execute()
        return res.data[0] if res and res.data else {}

    # --- Supplements ---
    def get_supplements(self, user_id: str) -> List[Dict[str, Any]]:
        if not is_supabase_live():
            return fallback_db.get_supplements(user_id)
        res = supabase_client.from_("supplements").select("*").eq("user_id", user_id).order("created_at", desc=False).execute()
        return res.data if res else []

    def add_supplement(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        data["user_id"] = user_id
        if not is_supabase_live():
            return fallback_db.add_supplement(user_id, data)
        res = supabase_client.from_("supplements").insert(data).execute()
        return res.data[0] if res and res.data else {}

    def delete_supplement(self, user_id: str, supplement_id: str) -> bool:
        if not is_supabase_live():
            return fallback_db.delete_supplement(user_id, supplement_id)
        res = supabase_client.from_("supplements").delete().eq("id", supplement_id).eq("user_id", user_id).execute()
        return bool(res.data) if res else False

db_repository = DBRepository()
