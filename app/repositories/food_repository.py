import json
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

_NUTRITION_CACHE_FILE = os.path.join(os.path.dirname(__file__), "../../../data/nutrition_cache.json")
_BARCODE_CACHE_FILE = os.path.join(os.path.dirname(__file__), "../../../data/barcode_cache.json")
_FAVORITES_FILE = os.path.join(os.path.dirname(__file__), "../../../data/favorites.json")
_RECENTS_FILE = os.path.join(os.path.dirname(__file__), "../../../data/recents.json")
_CORRECTIONS_FILE = os.path.join(os.path.dirname(__file__), "../../../data/corrections.json")


def _ensure_data_dir(path: str):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)


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
        _ensure_data_dir(path)
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


class FoodRepository:
    def __init__(self):
        self._in_memory_nutrition_cache: List[Dict[str, Any]] = _load_json_store(_NUTRITION_CACHE_FILE)
        self._in_memory_barcode_cache: List[Dict[str, Any]] = _load_json_store(_BARCODE_CACHE_FILE)
        self._in_memory_favorites: List[Dict[str, Any]] = _load_json_store(_FAVORITES_FILE)
        self._in_memory_recents: List[Dict[str, Any]] = _load_json_store(_RECENTS_FILE)
        self._in_memory_corrections: List[Dict[str, Any]] = _load_json_store(_CORRECTIONS_FILE)

    # --- Foods & Aliases ---
    def get_food_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        name_lower = name.strip().lower()
        supabase = _get_supabase()
        if supabase:
            try:
                res = supabase.from_("foods").select("*").ilike("name", name_lower).maybe_single().execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"Supabase get_food_by_name error: {e}")
        return None

    def create_food(self, food_data: Dict[str, Any]) -> Dict[str, Any]:
        supabase = _get_supabase()
        if supabase:
            try:
                res = supabase.from_("foods").insert(food_data).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"Supabase create_food error: {e}")
        return food_data

    def get_alias(self, alias: str) -> Optional[Dict[str, Any]]:
        alias_lower = alias.strip().lower()
        supabase = _get_supabase()
        if supabase:
            try:
                res = supabase.from_("food_aliases").select("*").ilike("alias", alias_lower).maybe_single().execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"Supabase get_alias error: {e}")
        return None

    def create_alias(self, alias: str, standard_name: str) -> Dict[str, Any]:
        alias_data = {
            "alias": alias.strip(),
            "standard_name": standard_name.strip()
        }
        supabase = _get_supabase()
        if supabase:
            try:
                res = supabase.from_("food_aliases").insert(alias_data).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"Supabase create_alias error: {e}")
        return alias_data

    def search_foods(self, query: str, limit: int = 15) -> List[Dict[str, Any]]:
        query_clean = query.strip().lower()
        supabase = _get_supabase()
        if supabase:
            try:
                res = supabase.from_("foods").select("*").ilike("name", f"%{query_clean}%").limit(limit).execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"Supabase search_foods error: {e}")
        
        # Search local cache
        results = [
            item for item in self._in_memory_nutrition_cache
            if query_clean in str(item.get("food_name", "")).lower()
        ]
        return results[:limit]

    # --- Nutrition Cache ---
    def get_nutrition_cache(self, food_name: str) -> Optional[Dict[str, Any]]:
        name_lower = food_name.strip().lower()
        
        # Check local cache first
        for item in self._in_memory_nutrition_cache:
            if str(item.get("food_name", "")).strip().lower() == name_lower:
                return item

        supabase = _get_supabase()
        if supabase:
            try:
                res = supabase.from_("nutrition_cache").select("*").ilike("food_name", name_lower).maybe_single().execute()
                if res and res.data:
                    self._in_memory_nutrition_cache.append(res.data)
                    _save_json_store(_NUTRITION_CACHE_FILE, self._in_memory_nutrition_cache)
                    return res.data
            except Exception as e:
                logger.warning(f"Supabase get_nutrition_cache error: {e}")
                
        return None

    def create_nutrition_cache(self, cache_data: Dict[str, Any]) -> Dict[str, Any]:
        name_lower = cache_data["food_name"].strip().lower()
        existing = self.get_nutrition_cache(name_lower)
        if existing:
            return existing

        self._in_memory_nutrition_cache.append(cache_data)
        _save_json_store(_NUTRITION_CACHE_FILE, self._in_memory_nutrition_cache)

        supabase = _get_supabase()
        if supabase:
            try:
                res = supabase.from_("nutrition_cache").insert(cache_data).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"Supabase create_nutrition_cache error: {e}")

        return cache_data

    # --- Barcode Cache ---
    def get_barcode_cache(self, barcode: str) -> Optional[Dict[str, Any]]:
        barcode_clean = barcode.strip()
        for item in self._in_memory_barcode_cache:
            if str(item.get("barcode", "")).strip() == barcode_clean:
                return item

        supabase = _get_supabase()
        if supabase:
            try:
                res = supabase.from_("barcode_cache").select("*").eq("barcode", barcode_clean).maybe_single().execute()
                if res and res.data:
                    self._in_memory_barcode_cache.append(res.data)
                    _save_json_store(_BARCODE_CACHE_FILE, self._in_memory_barcode_cache)
                    return res.data
            except Exception as e:
                logger.warning(f"Supabase get_barcode_cache error: {e}")

        return None

    def create_barcode_cache(self, barcode: str, food_data: Dict[str, Any]) -> Dict[str, Any]:
        cache_data = {
            "barcode": barcode.strip(),
            **food_data
        }
        self._in_memory_barcode_cache.append(cache_data)
        _save_json_store(_BARCODE_CACHE_FILE, self._in_memory_barcode_cache)

        supabase = _get_supabase()
        if supabase:
            try:
                res = supabase.from_("barcode_cache").insert(cache_data).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"Supabase create_barcode_cache error: {e}")

        return cache_data

    # --- Food Corrections (Learning System) ---
    def create_correction(self, user_id: str, correction_data: Dict[str, Any]) -> Dict[str, Any]:
        db_data = {
            "user_id": str(user_id),
            **correction_data
        }
        self._in_memory_corrections.append(db_data)
        _save_json_store(_CORRECTIONS_FILE, self._in_memory_corrections)

        supabase = _get_supabase()
        if supabase:
            try:
                res = supabase.from_("food_corrections").insert(db_data).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"Supabase create_correction error: {e}")

        return db_data

    def get_corrections(self, user_id: str) -> List[Dict[str, Any]]:
        uid_str = str(user_id)
        supabase = _get_supabase()
        if supabase:
            try:
                res = supabase.from_("food_corrections").select("*").eq("user_id", uid_str).execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"Supabase get_corrections error: {e}")

        return [c for c in self._in_memory_corrections if str(c.get("user_id")) == uid_str]

    # --- Favorite Foods ---
    def get_favorites(self, user_id: str) -> List[Dict[str, Any]]:
        uid_str = str(user_id)
        supabase = _get_supabase()
        if supabase:
            try:
                res = supabase.from_("favorite_foods").select("*").eq("user_id", uid_str).order("created_at", desc=True).execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"Supabase get_favorites error: {e}")

        return [f for f in self._in_memory_favorites if str(f.get("user_id")) == uid_str]

    def add_favorite(self, user_id: str, food_data: Dict[str, Any]) -> Dict[str, Any]:
        db_data = {
            "user_id": str(user_id),
            "food_name": food_data["food_name"],
            "calories": food_data.get("calories"),
            "protein": food_data.get("protein"),
            "carbs": food_data.get("carbs"),
            "fat": food_data.get("fat") or food_data.get("fats"),
            "fiber": food_data.get("fiber", 0.0),
            "serving_size_g": food_data.get("serving_size_g", 100.0)
        }
        self._in_memory_favorites.append(db_data)
        _save_json_store(_FAVORITES_FILE, self._in_memory_favorites)

        supabase = _get_supabase()
        if supabase:
            try:
                res = supabase.from_("favorite_foods").upsert(db_data, on_conflict="user_id,food_name").execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"Supabase add_favorite error: {e}")

        return db_data

    def remove_favorite(self, user_id: str, food_name: str) -> bool:
        uid_str = str(user_id)
        fname_lower = food_name.strip().lower()
        self._in_memory_favorites = [
            f for f in self._in_memory_favorites
            if not (str(f.get("user_id")) == uid_str and str(f.get("food_name")).strip().lower() == fname_lower)
        ]
        _save_json_store(_FAVORITES_FILE, self._in_memory_favorites)

        supabase = _get_supabase()
        if supabase:
            try:
                res = supabase.from_("favorite_foods").delete().eq("user_id", uid_str).ilike("food_name", food_name).execute()
                return bool(res.data) if res else True
            except Exception as e:
                logger.warning(f"Supabase remove_favorite error: {e}")

        return True

    # --- Recent Foods ---
    def get_recents(self, user_id: str, limit: int = 15) -> List[Dict[str, Any]]:
        uid_str = str(user_id)
        supabase = _get_supabase()
        if supabase:
            try:
                res = supabase.from_("recent_foods").select("*").eq("user_id", uid_str).order("last_logged_at", desc=True).limit(limit).execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"Supabase get_recents error: {e}")

        user_recents = [r for r in self._in_memory_recents if str(r.get("user_id")) == uid_str]
        user_recents.sort(key=lambda x: x.get("last_logged_at", ""), reverse=True)
        return user_recents[:limit]

    def add_recent(self, user_id: str, food_name: str) -> Dict[str, Any]:
        uid_str = str(user_id)
        fname_clean = food_name.strip()
        db_data = {
            "user_id": uid_str,
            "food_name": fname_clean,
            "last_logged_at": datetime.utcnow().isoformat() + "Z"
        }

        # Update local memory store
        self._in_memory_recents = [
            r for r in self._in_memory_recents
            if not (str(r.get("user_id")) == uid_str and str(r.get("food_name")).strip().lower() == fname_clean.lower())
        ]
        self._in_memory_recents.append(db_data)
        _save_json_store(_RECENTS_FILE, self._in_memory_recents)

        supabase = _get_supabase()
        if supabase:
            try:
                res = supabase.from_("recent_foods").upsert(db_data, on_conflict="user_id,food_name").execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"Supabase add_recent error: {e}")

        return db_data


food_repository = FoodRepository()
