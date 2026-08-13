import json
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# File-based persistence path (survives server restarts when Supabase isn't configured)
_MEALS_FILE = os.path.join(os.path.dirname(__file__), "../../../data/meals.json")
_FOOD_ITEMS_FILE = os.path.join(os.path.dirname(__file__), "../../../data/food_items.json")


def _ensure_data_dir():
    os.makedirs(os.path.dirname(os.path.abspath(_MEALS_FILE)), exist_ok=True)


def _load_json_store(path: str) -> list:
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load {path}: {e}")
    return []


def _save_json_store(path: str, data: list):
    try:
        _ensure_data_dir()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Could not persist {path}: {e}")


def _get_supabase():
    """Lazily import supabase_client so startup doesn't crash if credentials missing."""
    try:
        from app.database.supabase import supabase_client
        return supabase_client
    except Exception as e:
        logger.warning(f"Supabase client unavailable: {e}")
        return None


class MealRepository:
    def __init__(self):
        self._in_memory_meals: List[Dict[str, Any]] = _load_json_store(_MEALS_FILE)
        self._in_memory_food_items: List[Dict[str, Any]] = _load_json_store(_FOOD_ITEMS_FILE)

    def create_meal(self, user_id: str, meal_data: Dict[str, Any]) -> Dict[str, Any]:
        meal_id = f"meal_{int(datetime.utcnow().timestamp() * 1000)}"

        # Normalise fat/fats field — backend DB column is 'fat'
        fat_val = float(
            meal_data.get("fat") or meal_data.get("fats") or 0.0
        )

        db_payload = {
            "id": meal_id,
            "user_id": str(user_id),
            "name": meal_data.get("name") or "Logged Meal",
            "meal_type": meal_data.get("meal_type") or "Lunch",
            "total_weight": float(meal_data.get("total_weight") or 0.0),
            "total_calories": int(meal_data.get("total_calories") or meal_data.get("calories") or 0),
            "protein": float(meal_data.get("protein") or 0.0),
            "carbs": float(meal_data.get("carbs") or 0.0),
            "fat": fat_val,
            "fiber": float(meal_data.get("fiber") or 0.0),
            "image_url": meal_data.get("image_url"),
            "logged_at": meal_data.get("logged_at") or datetime.utcnow().isoformat() + "Z",
        }

        # 1. Try Supabase first (no food_items key — that's a separate table)
        supabase = _get_supabase()
        if supabase:
            try:
                res = supabase.from_("meals").insert(db_payload).execute()
                if res and res.data:
                    saved = res.data[0]
                    saved["food_items"] = []  # attach empty list for callers
                    # Also keep in memory + file for fast local reads
                    self._in_memory_meals.append({**saved, "food_items": []})
                    _save_json_store(_MEALS_FILE, self._in_memory_meals)
                    logger.info(f"Meal {meal_id} saved to Supabase for user {user_id}")
                    return saved
                else:
                    logger.error(f"Supabase insert returned no data for meal {meal_id}")
            except Exception as e:
                logger.error(f"Supabase insert failed for meal {meal_id}: {e}")

        # 2. Fallback: file-based persistence (survives restarts)
        db_payload["food_items"] = []
        self._in_memory_meals.append(db_payload)
        _save_json_store(_MEALS_FILE, self._in_memory_meals)
        logger.info(f"Meal {meal_id} saved to local file store for user {user_id}")
        return db_payload

    def create_food_items(self, meal_id: str, food_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        db_items = []
        for food in food_items:
            fat_val = float(food.get("fat") or food.get("fats") or 0.0)
            db_items.append({
                "meal_id": meal_id,
                "food_name": food.get("food_name") or food.get("name") or "Unknown",
                "normalized_name": food.get("normalized_name") or food.get("food_name") or "Unknown",
                "weight": float(food.get("weight_g") or food.get("weight") or 0.0),
                "serving": food.get("serving") or "1 serving",
                "calories": int(food.get("calories") or 0),
                "protein": float(food.get("protein") or 0.0),
                "carbs": float(food.get("carbs") or 0.0),
                "fat": fat_val,
                "fiber": float(food.get("fiber") or 0.0),
                "confidence": float(food.get("confidence") or 100.0),
                "cooking_method": food.get("cooking_method") or "cooked",
                "ingredients": food.get("ingredients") or [],
                "hidden_ingredients": food.get("hidden_ingredients") or [],
            })

        # Attach food items to the parent meal in memory/file store
        for m in self._in_memory_meals:
            if m.get("id") == meal_id:
                m["food_items"] = db_items
                break
        _save_json_store(_MEALS_FILE, self._in_memory_meals)

        # 1. Try Supabase
        supabase = _get_supabase()
        if supabase and db_items:
            try:
                res = supabase.from_("food_items").insert(db_items).execute()
                if res and res.data:
                    self._in_memory_food_items.extend(res.data)
                    _save_json_store(_FOOD_ITEMS_FILE, self._in_memory_food_items)
                    return res.data
                else:
                    logger.error(f"Supabase insert returned no data for food_items of meal {meal_id}")
            except Exception as e:
                logger.error(f"Supabase food_items insert failed for meal {meal_id}: {e}")

        # 2. Fallback: local file
        self._in_memory_food_items.extend(db_items)
        _save_json_store(_FOOD_ITEMS_FILE, self._in_memory_food_items)
        return db_items

    def get_meals_by_date(self, user_id: str, date_str: str) -> List[Dict[str, Any]]:
        uid_str = str(user_id).lower()

        # Always reload local store to get fresh entries
        self._in_memory_meals = _load_json_store(_MEALS_FILE)
        self._in_memory_food_items = _load_json_store(_FOOD_ITEMS_FILE)

        # 1. Try Supabase
        db_meals = []
        supabase = _get_supabase()
        if supabase:
            try:
                res = (
                    supabase.from_("meals")
                    .select("*, food_items(*)")
                    .eq("user_id", str(user_id))
                    .gte("logged_at", f"{date_str}T00:00:00.000Z")
                    .lte("logged_at", f"{date_str}T23:59:59.999Z")
                    .execute()
                )
                db_meals = res.data if res and res.data else []
            except Exception as e:
                logger.error(f"Supabase get_meals_by_date failed: {e}")

        # 2. Merge with local store (avoids duplicates by ID)
        mem_meals = [
            m for m in self._in_memory_meals
            if str(m.get("user_id", "")).lower() == uid_str
            and (
                str(m.get("logged_at", "")).startswith(date_str)
                or str(m.get("date", "")).startswith(date_str)
                or str(m.get("created_at", "")).startswith(date_str)
            )
        ]

        seen_ids: set = set()
        combined = []
        for m in db_meals + mem_meals:
            mid = m.get("id")
            if mid and mid in seen_ids:
                continue
            if mid:
                seen_ids.add(mid)
            # Attach food_items if missing
            if "food_items" not in m or not m["food_items"]:
                m["food_items"] = [fi for fi in self._in_memory_food_items if str(fi.get("meal_id")) == str(mid)]
            combined.append(m)

        return combined

    def get_meal_history(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        uid_str = str(user_id)
        db_meals = []
        supabase = _get_supabase()
        if supabase:
            try:
                res = (
                    supabase.from_("meals")
                    .select("*, food_items(*)")
                    .eq("user_id", uid_str)
                    .order("logged_at", desc=True)
                    .range(offset, offset + limit - 1)
                    .execute()
                )
                db_meals = res.data if res and res.data else []
            except Exception as e:
                logger.error(f"Supabase get_meal_history failed: {e}")

        mem_meals = [
            m for m in self._in_memory_meals
            if str(m.get("user_id")) == uid_str
        ]

        seen_ids: set = set()
        combined = []
        for m in db_meals + mem_meals:
            mid = m.get("id")
            if mid and mid in seen_ids:
                continue
            if mid:
                seen_ids.add(mid)
            if "food_items" not in m:
                m["food_items"] = [fi for fi in self._in_memory_food_items if fi.get("meal_id") == mid]
            combined.append(m)

        combined.sort(key=lambda m: m.get("logged_at", ""), reverse=True)
        return combined[offset:offset + limit]

    def delete_meal(self, user_id: str, meal_id: str) -> bool:
        self._in_memory_meals = [m for m in self._in_memory_meals if m.get("id") != meal_id]
        self._in_memory_food_items = [fi for fi in self._in_memory_food_items if fi.get("meal_id") != meal_id]
        _save_json_store(_MEALS_FILE, self._in_memory_meals)
        _save_json_store(_FOOD_ITEMS_FILE, self._in_memory_food_items)

        supabase = _get_supabase()
        if supabase:
            try:
                supabase.from_("food_items").delete().eq("meal_id", meal_id).execute()
                res = supabase.from_("meals").delete().eq("id", meal_id).eq("user_id", str(user_id)).execute()
                return bool(res.data) if res else True
            except Exception as e:
                logger.error(f"Supabase delete_meal failed: {e}")
        return True

    # --- Meal Templates ---
    def create_template(self, user_id: str, template_name: str, foods: List[Dict[str, Any]]) -> Dict[str, Any]:
        template_payload = {
            "user_id": user_id,
            "template_name": template_name,
            "foods": foods
        }
        supabase = _get_supabase()
        if supabase:
            try:
                res = supabase.from_("meal_templates").insert(template_payload).execute()
                return res.data[0] if res and res.data else template_payload
            except Exception as e:
                logger.error(f"Supabase create_template failed: {e}")
        return template_payload

    def get_templates(self, user_id: str) -> List[Dict[str, Any]]:
        supabase = _get_supabase()
        if supabase:
            try:
                res = supabase.from_("meal_templates").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
                return res.data if res else []
            except Exception as e:
                logger.error(f"Supabase get_templates failed: {e}")
        return []


meal_repository = MealRepository()
