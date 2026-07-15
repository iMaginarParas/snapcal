from typing import List, Dict, Any, Optional
from datetime import datetime
from app.database.supabase import supabase_client

class FoodRepository:
    # --- Foods & Aliases ---
    def get_food_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        name_lower = name.strip().lower()
        res = supabase_client.from_("foods").select("*").ilike("name", name_lower).maybe_single().execute()
        return res.data if res else None

    def create_food(self, food_data: Dict[str, Any]) -> Dict[str, Any]:
        res = supabase_client.from_("foods").insert(food_data).execute()
        return res.data[0]

    def get_alias(self, alias: str) -> Optional[Dict[str, Any]]:
        alias_lower = alias.strip().lower()
        res = supabase_client.from_("food_aliases").select("*").ilike("alias", alias_lower).maybe_single().execute()
        return res.data if res else None

    def create_alias(self, alias: str, standard_name: str) -> Dict[str, Any]:
        alias_data = {
            "alias": alias.strip(),
            "standard_name": standard_name.strip()
        }
        res = supabase_client.from_("food_aliases").insert(alias_data).execute()
        return res.data[0]

    def search_foods(self, query: str, limit: int = 15) -> List[Dict[str, Any]]:
        query_clean = query.strip().lower()
        res = supabase_client.from_("foods").select("*").ilike("name", f"%{query_clean}%").limit(limit).execute()
        return res.data or []

    # --- Nutrition Cache ---
    def get_nutrition_cache(self, food_name: str) -> Optional[Dict[str, Any]]:
        name_lower = food_name.strip().lower()
        res = supabase_client.from_("nutrition_cache").select("*").ilike("food_name", name_lower).maybe_single().execute()
        return res.data if res else None

    def create_nutrition_cache(self, cache_data: Dict[str, Any]) -> Dict[str, Any]:
        name_lower = cache_data["food_name"].strip().lower()
        existing = self.get_nutrition_cache(name_lower)
        if existing:
            return existing
        try:
            res = supabase_client.from_("nutrition_cache").insert(cache_data).execute()
            return res.data[0]
        except Exception:
            return cache_data

    # --- Barcode Cache ---
    def get_barcode_cache(self, barcode: str) -> Optional[Dict[str, Any]]:
        barcode_clean = barcode.strip()
        res = supabase_client.from_("barcode_cache").select("*").eq("barcode", barcode_clean).maybe_single().execute()
        return res.data if res else None

    def create_barcode_cache(self, barcode: str, food_data: Dict[str, Any]) -> Dict[str, Any]:
        cache_data = {
            "barcode": barcode.strip(),
            **food_data
        }
        try:
            res = supabase_client.from_("barcode_cache").insert(cache_data).execute()
            return res.data[0]
        except Exception:
            return cache_data

    # --- Food Corrections (Learning System) ---
    def create_correction(self, user_id: str, correction_data: Dict[str, Any]) -> Dict[str, Any]:
        db_data = {
            "user_id": user_id,
            **correction_data
        }
        res = supabase_client.from_("food_corrections").insert(db_data).execute()
        return res.data[0]

    def get_corrections(self, user_id: str) -> List[Dict[str, Any]]:
        res = supabase_client.from_("food_corrections").select("*").eq("user_id", user_id).execute()
        return res.data or []

    # --- Favorite Foods ---
    def get_favorites(self, user_id: str) -> List[Dict[str, Any]]:
        res = supabase_client.from_("favorite_foods").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return res.data or []

    def add_favorite(self, user_id: str, food_data: Dict[str, Any]) -> Dict[str, Any]:
        db_data = {
            "user_id": user_id,
            "food_name": food_data["food_name"],
            "calories": food_data.get("calories"),
            "protein": food_data.get("protein"),
            "carbs": food_data.get("carbs"),
            "fat": food_data.get("fat"),
            "fiber": food_data.get("fiber", 0.0),
            "serving_size_g": food_data.get("serving_size_g", 100.0)
        }
        try:
            res = supabase_client.from_("favorite_foods").upsert(db_data, on_conflict="user_id,food_name").execute()
            return res.data[0]
        except Exception:
            return db_data

    def remove_favorite(self, user_id: str, food_name: str) -> bool:
        res = supabase_client.from_("favorite_foods").delete().eq("user_id", user_id).ilike("food_name", food_name).execute()
        return bool(res.data)

    # --- Recent Foods ---
    def get_recents(self, user_id: str, limit: int = 15) -> List[Dict[str, Any]]:
        res = supabase_client.from_("recent_foods").select("*").eq("user_id", user_id).order("last_logged_at", desc=True).limit(limit).execute()
        return res.data or []

    def add_recent(self, user_id: str, food_name: str) -> Dict[str, Any]:
        db_data = {
            "user_id": user_id,
            "food_name": food_name.strip(),
            "last_logged_at": datetime.utcnow().isoformat() + "Z"
        }
        try:
            res = supabase_client.from_("recent_foods").upsert(db_data, on_conflict="user_id,food_name").execute()
            return res.data[0]
        except Exception:
            return db_data

food_repository = FoodRepository()
