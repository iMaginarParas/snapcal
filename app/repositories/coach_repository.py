import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

_STORE_FILE = os.path.join(os.path.dirname(__file__), "../../../data/coach_ecosystem.json")


def _ensure_dir():
    os.makedirs(os.path.dirname(os.path.abspath(_STORE_FILE)), exist_ok=True)


def _load_store() -> Dict[str, Any]:
    try:
        if os.path.exists(_STORE_FILE):
            with open(_STORE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to read coach local store: {e}")
    return {}


def _save_store(data: Dict[str, Any]):
    try:
        _ensure_dir()
        with open(_STORE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Failed to save coach local store: {e}")


def _get_supabase():
    try:
        from app.database.supabase import supabase_client
        return supabase_client
    except Exception:
        return None


class CoachRepository:
    # --- Generic Table Helpers ---
    def _query_table(self, table: str, coach_id: str) -> List[Dict[str, Any]]:
        sb = _get_supabase()
        if sb:
            try:
                res = sb.from_(table).select("*").eq("coach_id", coach_id).execute()
                if res.data is not None and len(res.data) > 0:
                    return res.data
            except Exception as e:
                logger.warning(f"Supabase query failed for {table}: {e}")

        store = _load_store()
        table_data = store.get(table, [])
        return [item for item in table_data if item.get("coach_id") == coach_id]

    def _upsert_item(self, table: str, item: Dict[str, Any]) -> Dict[str, Any]:
        sb = _get_supabase()
        if sb:
            try:
                res = sb.from_(table).upsert(item).execute()
                if res.data and len(res.data) > 0:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"Supabase upsert failed for {table}: {e}")

        store = _load_store()
        table_data = store.setdefault(table, [])
        item_id = item.get("id")
        existing_idx = next((i for i, x in enumerate(table_data) if x.get("id") == item_id), None)
        if existing_idx is not None:
            table_data[existing_idx] = {**table_data[existing_idx], **item}
        else:
            table_data.insert(0, item)
        _save_store(store)
        return item

    def _delete_item(self, table: str, item_id: str, coach_id: str) -> bool:
        sb = _get_supabase()
        if sb:
            try:
                sb.from_(table).delete().eq("id", item_id).eq("coach_id", coach_id).execute()
            except Exception as e:
                logger.warning(f"Supabase delete failed for {table}: {e}")

        store = _load_store()
        table_data = store.get(table, [])
        store[table] = [x for x in table_data if not (x.get("id") == item_id and x.get("coach_id") == coach_id)]
        _save_store(store)
        return True

    # --- Specific Entity Operations ---
    # Clients
    def get_clients(self, coach_id: str) -> List[Dict[str, Any]]:
        return self._query_table("coach_clients", coach_id)

    def save_client(self, client: Dict[str, Any]) -> Dict[str, Any]:
        if not client.get("id"):
            client["id"] = f"cl_{int(datetime.utcnow().timestamp() * 1000)}"
        return self._upsert_item("coach_clients", client)

    def delete_client(self, client_id: str, coach_id: str) -> bool:
        return self._delete_item("coach_clients", client_id, coach_id)

    # Sessions
    def get_sessions(self, coach_id: str) -> List[Dict[str, Any]]:
        return self._query_table("coach_sessions", coach_id)

    def save_session(self, session: Dict[str, Any]) -> Dict[str, Any]:
        if not session.get("id"):
            session["id"] = f"sess_{int(datetime.utcnow().timestamp() * 1000)}"
        return self._upsert_item("coach_sessions", session)

    def delete_session(self, session_id: str, coach_id: str) -> bool:
        return self._delete_item("coach_sessions", session_id, coach_id)

    # Workouts
    def get_workouts(self, coach_id: str) -> List[Dict[str, Any]]:
        return self._query_table("coach_workouts", coach_id)

    def save_workout(self, workout: Dict[str, Any]) -> Dict[str, Any]:
        if not workout.get("id"):
            workout["id"] = f"w_{int(datetime.utcnow().timestamp() * 1000)}"
        return self._upsert_item("coach_workouts", workout)

    def delete_workout(self, workout_id: str, coach_id: str) -> bool:
        return self._delete_item("coach_workouts", workout_id, coach_id)

    # Programs
    def get_programs(self, coach_id: str) -> List[Dict[str, Any]]:
        return self._query_table("coach_programs", coach_id)

    def save_program(self, program: Dict[str, Any]) -> Dict[str, Any]:
        if not program.get("id"):
            program["id"] = f"prog_{int(datetime.utcnow().timestamp() * 1000)}"
        return self._upsert_item("coach_programs", program)

    def delete_program(self, program_id: str, coach_id: str) -> bool:
        return self._delete_item("coach_programs", program_id, coach_id)

    # Payments & Invoices
    def get_payments(self, coach_id: str) -> List[Dict[str, Any]]:
        return self._query_table("coach_payments", coach_id)

    def save_payment(self, payment: Dict[str, Any]) -> Dict[str, Any]:
        if not payment.get("id"):
            payment["id"] = f"pay_{int(datetime.utcnow().timestamp() * 1000)}"
        return self._upsert_item("coach_payments", payment)

    # Leads CRM
    def get_leads(self, coach_id: str) -> List[Dict[str, Any]]:
        return self._query_table("coach_leads", coach_id)

    def save_lead(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        if not lead.get("id"):
            lead["id"] = f"lead_{int(datetime.utcnow().timestamp() * 1000)}"
        return self._upsert_item("coach_leads", lead)

    def delete_lead(self, lead_id: str, coach_id: str) -> bool:
        return self._delete_item("coach_leads", lead_id, coach_id)

    # Groups
    def get_groups(self, coach_id: str) -> List[Dict[str, Any]]:
        return self._query_table("coach_groups", coach_id)

    def save_group(self, group: Dict[str, Any]) -> Dict[str, Any]:
        if not group.get("id"):
            group["id"] = f"grp_{int(datetime.utcnow().timestamp() * 1000)}"
        return self._upsert_item("coach_groups", group)

    # Challenges
    def get_challenges(self, coach_id: str) -> List[Dict[str, Any]]:
        return self._query_table("coach_challenges", coach_id)

    def save_challenge(self, challenge: Dict[str, Any]) -> Dict[str, Any]:
        if not challenge.get("id"):
            challenge["id"] = f"ch_{int(datetime.utcnow().timestamp() * 1000)}"
        return self._upsert_item("coach_challenges", challenge)

    # Availability
    def get_availability(self, coach_id: str) -> List[Dict[str, Any]]:
        return self._query_table("coach_availability", coach_id)

    def save_availability(self, coach_id: str, availability_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for item in availability_list:
            item["coach_id"] = coach_id
            if not item.get("id"):
                item["id"] = f"avail_{item.get('day', 'day')}_{coach_id}"
            results.append(self._upsert_item("coach_availability", item))
        return results

    # Reports
    def get_reports(self, coach_id: str) -> List[Dict[str, Any]]:
        return self._query_table("coach_reports", coach_id)

    def save_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        if not report.get("id"):
            report["id"] = f"rep_{int(datetime.utcnow().timestamp() * 1000)}"
        return self._upsert_item("coach_reports", report)

    # Automations
    def get_automations(self, coach_id: str) -> List[Dict[str, Any]]:
        return self._query_table("coach_automations", coach_id)

    def save_automation(self, auto: Dict[str, Any]) -> Dict[str, Any]:
        if not auto.get("id"):
            auto["id"] = f"auto_{int(datetime.utcnow().timestamp() * 1000)}"
        return self._upsert_item("coach_automations", auto)

    def delete_automation(self, auto_id: str, coach_id: str) -> bool:
        return self._delete_item("coach_automations", auto_id, coach_id)


coach_repo = CoachRepository()
