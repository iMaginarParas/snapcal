import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.database.supabase import supabase_client

logger = logging.getLogger(__name__)

_STEPS_FILE = os.path.join(os.path.dirname(__file__), "../../../data/daily_steps.json")


def _ensure_data_dir():
    os.makedirs(os.path.dirname(os.path.abspath(_STEPS_FILE)), exist_ok=True)


def _load_json_store() -> List[Dict[str, Any]]:
    try:
        if os.path.exists(_STEPS_FILE):
            with open(_STEPS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load steps local store: {e}")
    return []


def _save_json_store(data: List[Dict[str, Any]]):
    try:
        _ensure_data_dir()
        with open(_STEPS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Could not save steps local store: {e}")


class StepsRepository:
    def __init__(self):
        self._in_memory_steps: List[Dict[str, Any]] = _load_json_store()

    def get_steps_by_date(self, user_id: str, date_str: str) -> Optional[Dict[str, Any]]:
        """Retrieves daily step counts for a user on a specific date."""
        uid_str = str(user_id)
        if supabase_client:
            try:
                res = supabase_client.from_("daily_steps").select("*").eq("user_id", uid_str).eq("date", date_str).maybe_single().execute()
                if res and res.data:
                    # Update local cache
                    self._update_local_record(res.data)
                    return res.data
            except Exception as e:
                logger.debug(f"Supabase get_steps_by_date failed: {e}")

        # Fallback to local store
        self._in_memory_steps = _load_json_store()
        return next(
            (s for s in self._in_memory_steps if str(s.get("user_id")) == uid_str and s.get("date") == date_str),
            None
        )

    def get_steps_history(self, user_id: str, start_date_str: str, end_date_str: str) -> List[Dict[str, Any]]:
        """Retrieves steps history for a date range."""
        uid_str = str(user_id)
        db_steps = []
        if supabase_client:
            try:
                res = supabase_client.from_("daily_steps").select("*").eq("user_id", uid_str).gte("date", start_date_str).lte("date", end_date_str).order("date", desc=False).execute()
                db_steps = res.data if res and res.data else []
            except Exception as e:
                logger.debug(f"Supabase get_steps_history failed: {e}")

        self._in_memory_steps = _load_json_store()
        mem_steps = [
            s for s in self._in_memory_steps
            if str(s.get("user_id")) == uid_str and start_date_str <= str(s.get("date", "")) <= end_date_str
        ]

        # Merge, deduplicating by date (db preferred, fallback to local)
        date_map: Dict[str, Dict[str, Any]] = {}
        for s in mem_steps:
            d = s.get("date")
            if d:
                date_map[d] = s
        for s in db_steps:
            d = s.get("date")
            if d:
                date_map[d] = s

        return sorted(list(date_map.values()), key=lambda x: x.get("date", ""))

    def _update_local_record(self, record: Dict[str, Any]):
        self._in_memory_steps = _load_json_store()
        idx = next((i for i, x in enumerate(self._in_memory_steps) if x.get("id") == record.get("id") or (str(x.get("user_id")) == str(record.get("user_id")) and x.get("date") == record.get("date"))), None)
        if idx is not None:
            self._in_memory_steps[idx] = {**self._in_memory_steps[idx], **record}
        else:
            self._in_memory_steps.insert(0, record)
        _save_json_store(self._in_memory_steps)

    def sync_steps(self, user_id: str, sync_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronizes step updates and resolves conflicts by keeping the maximum step count.
        Always returns the merged steps safely without failing.
        """
        uid_str = str(user_id)
        date_str = sync_data["date"]
        existing = self.get_steps_by_date(uid_str, date_str)

        now_iso = datetime.utcnow().isoformat() + "Z"

        if existing:
            # Resolve conflict: today's steps = max(local_steps, sync_steps)
            new_final = max(existing.get("final_steps") or 0, sync_data.get("final_steps") or 0)
            new_sensor = max(existing.get("sensor_steps") or 0, sync_data.get("sensor_steps") or 0)
            new_hc = max(existing.get("health_connect_steps") or 0, sync_data.get("health_connect_steps") or 0)
            
            update_data = {
                "sensor_steps": new_sensor,
                "health_connect_steps": new_hc,
                "final_steps": new_final,
                "distance": max(float(existing.get("distance") or 0.0), float(sync_data.get("distance") or 0.0)),
                "calories": max(int(existing.get("calories") or 0), int(sync_data.get("calories") or 0)),
                "active_minutes": max(int(existing.get("active_minutes") or 0), int(sync_data.get("active_minutes") or 0)),
                "baseline": sync_data.get("baseline") or existing.get("baseline") or 0,
                "last_sensor_value": max(int(existing.get("last_sensor_value") or 0), int(sync_data.get("last_sensor_value") or 0)),
                "last_sync": now_iso,
                "updated_at": now_iso
            }
            
            merged_record = {**existing, **update_data}

            if supabase_client and existing.get("id"):
                try:
                    res = supabase_client.from_("daily_steps").update(update_data).eq("id", existing["id"]).execute()
                    if res and res.data:
                        merged_record = res.data[0]
                except Exception as e:
                    logger.warning(f"Supabase daily_steps update failed (saved locally): {e}")

            self._update_local_record(merged_record)
            return merged_record
        else:
            # Insert new record
            insert_data = {
                "id": f"step_{int(datetime.utcnow().timestamp() * 1000)}",
                "user_id": uid_str,
                "date": date_str,
                "sensor_steps": sync_data.get("sensor_steps", 0),
                "health_connect_steps": sync_data.get("health_connect_steps", 0),
                "final_steps": sync_data.get("final_steps", 0),
                "distance": float(sync_data.get("distance", 0.0)),
                "calories": int(sync_data.get("calories", 0)),
                "active_minutes": int(sync_data.get("active_minutes", 0)),
                "baseline": sync_data.get("baseline", 0),
                "last_sensor_value": sync_data.get("last_sensor_value", 0),
                "last_sync": now_iso,
                "created_at": now_iso,
                "updated_at": now_iso
            }
            
            saved_record = insert_data
            if supabase_client:
                try:
                    # Strip client-generated ID if Postgres auto-generates UUID
                    sb_payload = {k: v for k, v in insert_data.items() if k != "id"}
                    res = supabase_client.from_("daily_steps").insert(sb_payload).execute()
                    if res and res.data:
                        saved_record = res.data[0]
                except Exception as e:
                    logger.warning(f"Supabase daily_steps insert failed (saved locally): {e}")

            self._update_local_record(saved_record)
            return saved_record

steps_repository = StepsRepository()
