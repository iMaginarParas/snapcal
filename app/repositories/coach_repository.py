import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

_DEFAULT_COACHES = [
    {
        "id": "coach_default",
        "name": "Coach Sunil Kumar",
        "title": "Chief Strength & Conditioning Coach",
        "discipline": "Strength & Conditioning",
        "specialty": "Fitness & Strength",
        "location": "Bangalore, IN",
        "location_type": "In-Person / Hybrid",
        "rating": 4.97,
        "clients_count": 210,
        "invite_code": "SAB-SUNIL",
        "bio": "Master coach with 12+ years optimizing hypertrophy, strength biomechanics, and athlete body recomposition.",
        "avatar": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=300"
    },
    {
        "id": "coach_marcus_vance",
        "name": "Dr. Marcus Vance",
        "title": "Lead Performance Nutritionist",
        "discipline": "Nutrition & Dietetics",
        "specialty": "Nutrition & Dietetics",
        "location": "New York, NY",
        "location_type": "Remote / Online",
        "rating": 4.96,
        "clients_count": 142,
        "invite_code": "SAB-VANCE",
        "bio": "Ph.D. in Human Bioenergetics. Specializes in metabolic flexibility, precision macronutrient cycling, and competition prep.",
        "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=300"
    },
    {
        "id": "coach_priya_sharma",
        "name": "Coach Priya Sharma",
        "title": "Mobility & Structural Recovery Coach",
        "discipline": "Yoga & Mobility",
        "specialty": "Yoga & Mobility",
        "location": "Austin, TX",
        "location_type": "In-Person / Hybrid",
        "rating": 4.98,
        "clients_count": 98,
        "invite_code": "SAB-PRIYA",
        "bio": "Former national gymnast and movement specialist. Focused on joint longevity, functional range conditioning, and breathwork.",
        "avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=300"
    },
    {
        "id": "coach_david_chen",
        "name": "Coach David Chen",
        "title": "Aerobic Capacity & Endurance Specialist",
        "discipline": "Cardio & Endurance",
        "specialty": "Cardio & Endurance",
        "location": "Boulder, CO",
        "location_type": "Remote / Online",
        "rating": 4.93,
        "clients_count": 116,
        "invite_code": "SAB-DAVID",
        "bio": "Ultra-marathoner and physiology coach. Specializes in VO2 max optimization, heart-rate zone training, and lactate clearance.",
        "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=300"
    },
    {
        "id": "coach_elena_rostova",
        "name": "Dr. Elena Rostova",
        "title": "Corrective Exercise & Rehab Director",
        "discipline": "Physio & Rehab",
        "specialty": "Physio & Rehab",
        "location": "Chicago, IL",
        "location_type": "In-Person / Hybrid",
        "rating": 4.99,
        "clients_count": 87,
        "invite_code": "SAB-ELENA",
        "bio": "Doctor of Physical Therapy. Focuses on post-injury kinetic retraining, spine mechanics, and return-to-sport protocols.",
        "avatar": "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=300"
    },
    {
        "id": "coach_test_pro",
        "name": "Coach Samantha Ray",
        "title": "Olympic Lifting & Functional Hypertrophy",
        "discipline": "Strength & Conditioning",
        "specialty": "Olympic Lifting & Functional Hypertrophy",
        "location": "Los Angeles, CA",
        "location_type": "Remote / Online",
        "rating": 4.95,
        "clients_count": 165,
        "invite_code": "SAB-SAMANTHA",
        "bio": "CSCS Certified coach specializing in explosive power development, progressive overload, and athlete conditioning.",
        "avatar": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=300"
    }
]

_STORE_CANDIDATES = [
    os.path.join(os.path.dirname(__file__), "../data/coach_ecosystem.json"),
    os.path.join(os.path.dirname(__file__), "../../../data/coach_ecosystem.json"),
    os.path.join(os.path.dirname(__file__), "../../data/coach_ecosystem.json"),
    os.path.join(os.getcwd(), "data/coach_ecosystem.json"),
    os.path.join(os.getcwd(), "app/data/coach_ecosystem.json"),
]


def _get_store_file() -> str:
    for path in _STORE_CANDIDATES:
        if os.path.exists(path):
            return path
    return _STORE_CANDIDATES[0]


def _ensure_dir():
    target = _get_store_file()
    os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)


def _load_store() -> Dict[str, Any]:
    file_path = _get_store_file()
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to read coach local store: {e}")
    return {}


def _save_store(data: Dict[str, Any]):
    file_path = _get_store_file()
    try:
        _ensure_dir()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Failed to save coach local store: {e}")


def _get_supabase():
    try:
        from app.database.supabase import get_coach_supabase
        return get_coach_supabase()
    except Exception:
        return None


def _normalize_discipline(coaching_type: str) -> str:
    """
    Maps free-text coaching type strings to a canonical discipline bucket.
    Only coaches with the same bucket are considered exclusive per client.
    """
    ct = (coaching_type or "").lower().strip()
    if any(k in ct for k in ["fitness", "strength", "sport", "conditioning", "athletic", "personal train", "hypertrophy", "bodybuilding", "powerlifting", "weightlifting"]):
        return "Fitness & Strength"
    if any(k in ct for k in ["nutrition", "diet", "dietitian", "meal plan", "food coach", "macro"]):
        return "Nutrition & Dietetics"
    if any(k in ct for k in ["yoga", "pilates", "mobility", "stretch", "flexibility", "movement"]):
        return "Yoga & Mobility"
    if any(k in ct for k in ["mental", "mindset", "wellness", "stress", "psychology", "life coach"]):
        return "Wellness & Mindset"
    if any(k in ct for k in ["physio", "rehab", "injury", "recovery", "therapy", "physiotherapy"]):
        return "Physio & Rehab"
    if any(k in ct for k in ["cardio", "endurance", "marathon", "running", "cycling", "triathlon", "swim"]):
        return "Cardio & Endurance"
    return ct or "General"


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
        saved_item = item
        sb = _get_supabase()
        if sb:
            try:
                res = sb.from_(table).upsert(item).execute()
                if res.data and len(res.data) > 0:
                    saved_item = res.data[0]
            except Exception as e:
                logger.warning(f"Supabase upsert failed for {table}: {e}")

        store = _load_store()
        table_data = store.setdefault(table, [])
        item_id = saved_item.get("id")
        existing_idx = next((i for i, x in enumerate(table_data) if x.get("id") == item_id), None)
        if existing_idx is not None:
            table_data[existing_idx] = {**table_data[existing_idx], **saved_item}
        else:
            table_data.insert(0, saved_item)
        _save_store(store)
        return saved_item

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

    def get_all_clients(self) -> List[Dict[str, Any]]:
        """Return all client records across all coaches (for cross-coach conflict checking)."""
        sb = _get_supabase()
        if sb:
            try:
                res = sb.from_("coach_clients").select("*").execute()
                if res.data is not None:
                    return res.data
            except Exception as e:
                logger.warning(f"Supabase get_all_clients failed: {e}")
        store = _load_store()
        return store.get("coach_clients", [])

    def find_client_coach_conflict(
        self,
        email: str,
        phone: str,
        incoming_discipline: str,
        requesting_coach_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Checks if a client (matched by email or phone) is already assigned to a different
        coach with the SAME discipline. Returns the conflicting record if found, else None.
        Cross-coach discipline exclusivity: one fitness coach per client, one nutrition coach
        per client, etc. A client CAN have coaches of different disciplines simultaneously.
        """
        norm_email = (email or "").lower().strip()
        norm_phone = "".join(c for c in (phone or "") if c.isdigit())
        incoming_disc = _normalize_discipline(incoming_discipline)

        all_clients = self.get_all_clients()
        for client in all_clients:
            # Skip records belonging to the requesting coach (same-coach dup already handled)
            if client.get("coach_id") == requesting_coach_id:
                continue

            # Match by email or phone
            client_email = (client.get("email") or "").lower().strip()
            client_phone = "".join(c for c in (client.get("phone") or "") if c.isdigit())
            email_match = norm_email and norm_email != "client@example.com" and client_email == norm_email
            phone_match = len(norm_phone) >= 8 and client_phone == norm_phone

            if not (email_match or phone_match):
                continue

            # Check if the OTHER coach's discipline is the same
            existing_discipline = _normalize_discipline(
                client.get("coaching_type") or client.get("package") or ""
            )
            if existing_discipline and existing_discipline == incoming_discipline:
                return {
                    "conflict": True,
                    "client_name": client.get("name", "Unknown"),
                    "existing_coach_id": client.get("coach_id"),
                    "existing_discipline": existing_discipline,
                    "message": f"This client already has a {existing_discipline} coach."
                }
        return None

    def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        sb = _get_supabase()
        if sb:
            try:
                res = sb.from_("coach_clients").select("*").eq("id", client_id).execute()
                if res.data and len(res.data) > 0:
                    return res.data[0]
            except Exception:
                pass
        store = _load_store()
        table_data = store.get("coach_clients", [])
        return next((x for x in table_data if x.get("id") == client_id), None)

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

    # Products
    def get_products(self, coach_id: str) -> List[Dict[str, Any]]:
        return self._query_table("coach_products", coach_id)

    def save_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        if not product.get("id"):
            product["id"] = f"prod_{int(datetime.utcnow().timestamp() * 1000)}"
        return self._upsert_item("coach_products", product)

    def delete_product(self, product_id: str, coach_id: str) -> bool:
        return self._delete_item("coach_products", product_id, coach_id)

    # Checkins
    def get_checkins(self, coach_id: str) -> List[Dict[str, Any]]:
        return self._query_table("coach_checkins", coach_id)

    def save_checkin(self, checkin: Dict[str, Any]) -> Dict[str, Any]:
        if not checkin.get("id"):
            checkin["id"] = f"chk_{int(datetime.utcnow().timestamp() * 1000)}"
        return self._upsert_item("coach_checkins", checkin)

    def delete_checkin(self, checkin_id: str, coach_id: str) -> bool:
        return self._delete_item("coach_checkins", checkin_id, coach_id)

    # Messages
    def get_messages(self, coach_id: str) -> List[Dict[str, Any]]:
        return self._query_table("coach_messages", coach_id)

    def save_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        if not message.get("id"):
            message["id"] = f"msg_{int(datetime.utcnow().timestamp() * 1000)}"
        return self._upsert_item("coach_messages", message)

    # Coach Profiles & Settings
    def get_profile(self, coach_id: str) -> Optional[Dict[str, Any]]:
        sb = _get_supabase()
        if sb:
            try:
                res = sb.from_("coach_profiles").select("*").eq("id", coach_id).execute()
                if res.data and len(res.data) > 0:
                    return res.data[0]
            except Exception:
                pass
        store = _load_store()
        profiles = store.get("coach_profiles", {})
        if isinstance(profiles, dict) and coach_id in profiles:
            return profiles[coach_id]
        if isinstance(profiles, list):
            found = next((p for p in profiles if p.get("id") == coach_id), None)
            if found:
                return found
        for def_c in _DEFAULT_COACHES:
            if def_c.get("id") == coach_id:
                return def_c
        return None

    def save_profile(self, coach_id: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        profile["id"] = coach_id
        profile["updated_at"] = datetime.utcnow().isoformat()
        sb = _get_supabase()
        if sb:
            try:
                sb.from_("coach_profiles").upsert(profile).execute()
            except Exception:
                pass
        store = _load_store()
        profiles = store.setdefault("coach_profiles", {})
        if isinstance(profiles, dict):
            profiles[coach_id] = profile
        elif isinstance(profiles, list):
            idx = next((i for i, p in enumerate(profiles) if p.get("id") == coach_id), None)
            if idx is not None:
                profiles[idx] = profile
            else:
                profiles.append(profile)
        _save_store(store)
        return profile

    def get_available_coaches(self) -> List[Dict[str, Any]]:
        """Returns registered coach profiles that are active and available for athletes."""
        sb = _get_supabase()
        if sb:
            try:
                res = sb.from_("coach_profiles").select("*").execute()
                if res.data and len(res.data) > 0:
                    return res.data
            except Exception:
                pass
        store = _load_store()
        profiles = store.get("coach_profiles", {})
        if isinstance(profiles, dict) and profiles:
            return list(profiles.values())
        if isinstance(profiles, list) and profiles:
            return profiles
        return list(_DEFAULT_COACHES)

    def get_recommended_coaches(self, limit: int = 3) -> List[Dict[str, Any]]:
        """Returns recommended coaches of distinct disciplines/types."""
        all_coaches = self.get_available_coaches()
        if not all_coaches:
            return []

        seen_disciplines = set()
        recommended = []
        for c in all_coaches:
            disc = _normalize_discipline(c.get("specialty") or c.get("discipline") or c.get("title") or "")
            if disc not in seen_disciplines:
                seen_disciplines.add(disc)
                recommended.append(c)
                if len(recommended) >= limit:
                    break

        if len(recommended) < limit:
            for c in all_coaches:
                if c not in recommended:
                    recommended.append(c)
                    if len(recommended) >= limit:
                        break

        return recommended


coach_repo = CoachRepository()

