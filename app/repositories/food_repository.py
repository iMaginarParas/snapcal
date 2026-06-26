from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from app.database.supabase import supabase_client, is_supabase_live
from app.database.fallback import fallback_db

class FoodRepository:
    # --- Foods & Aliases ---
    def get_food_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        name_lower = name.strip().lower()
        if not is_supabase_live():
            foods = fallback_db.db.get("foods", {})
            for f in foods.values():
                if f["name"].lower() == name_lower:
                    return f
            return None
        
        res = supabase_client.from_("foods").select("*").ilike("name", name_lower).maybe_single().execute()
        return res.data if res else None

    def create_food(self, food_data: Dict[str, Any]) -> Dict[str, Any]:
        if not is_supabase_live():
            food_id = str(uuid.uuid4())
            food_data["id"] = food_id
            food_data["created_at"] = datetime.utcnow().isoformat() + "Z"
            fallback_db.db["foods"][food_id] = food_data
            fallback_db.save_db()
            return food_data
            
        res = supabase_client.from_("foods").insert(food_data).execute()
        return res.data[0]

    def get_alias(self, alias: str) -> Optional[Dict[str, Any]]:
        alias_lower = alias.strip().lower()
        if not is_supabase_live():
            aliases = fallback_db.db.get("foodAliases", {})
            for a in aliases.values():
                if a["alias"].lower() == alias_lower:
                    return a
            return None

        res = supabase_client.from_("food_aliases").select("*").ilike("alias", alias_lower).maybe_single().execute()
        return res.data if res else None

    def create_alias(self, alias: str, standard_name: str) -> Dict[str, Any]:
        alias_data = {
            "alias": alias.strip(),
            "standard_name": standard_name.strip()
        }
        if not is_supabase_live():
            alias_id = str(uuid.uuid4())
            alias_data["id"] = alias_id
            alias_data["created_at"] = datetime.utcnow().isoformat() + "Z"
            fallback_db.db["foodAliases"][alias_id] = alias_data
            fallback_db.save_db()
            return alias_data

        res = supabase_client.from_("food_aliases").insert(alias_data).execute()
        return res.data[0]

    def search_foods(self, query: str, limit: int = 15) -> List[Dict[str, Any]]:
        query_clean = query.strip().lower()
        if not is_supabase_live():
            foods = list(fallback_db.db.get("foods", {}).values())
            # Simple substring matching
            results = [f for f in foods if query_clean in f["name"].lower()]
            return results[:limit]

        res = supabase_client.from_("foods").select("*").ilike("name", f"%{query_clean}%").limit(limit).execute()
        return res.data or []

    # --- Nutrition Cache ---
    def get_nutrition_cache(self, food_name: str) -> Optional[Dict[str, Any]]:
        name_lower = food_name.strip().lower()
        if not is_supabase_live():
            cache = fallback_db.db.get("nutritionCache", {})
            for c in cache.values():
                if c["food_name"].lower() == name_lower:
                    return c
            return None

        res = supabase_client.from_("nutrition_cache").select("*").ilike("food_name", name_lower).maybe_single().execute()
        return res.data if res else None

    def create_nutrition_cache(self, cache_data: Dict[str, Any]) -> Dict[str, Any]:
        # Strip ID and check if already exists to prevent duplicate key
        name_lower = cache_data["food_name"].strip().lower()
        existing = self.get_nutrition_cache(name_lower)
        if existing:
            return existing

        if not is_supabase_live():
            cache_id = str(uuid.uuid4())
            cache_data["id"] = cache_id
            cache_data["created_at"] = datetime.utcnow().isoformat() + "Z"
            fallback_db.db["nutritionCache"][cache_id] = cache_data
            fallback_db.save_db()
            return cache_data

        try:
            res = supabase_client.from_("nutrition_cache").insert(cache_data).execute()
            return res.data[0]
        except Exception:
            # Silently fallback on conflict
            return cache_data

    # --- Barcode Cache ---
    def get_barcode_cache(self, barcode: str) -> Optional[Dict[str, Any]]:
        barcode_clean = barcode.strip()
        if not is_supabase_live():
            cache = fallback_db.db.get("barcodeCache", {})
            return cache.get(barcode_clean)

        res = supabase_client.from_("barcode_cache").select("*").eq("barcode", barcode_clean).maybe_single().execute()
        return res.data if res else None

    def create_barcode_cache(self, barcode: str, food_data: Dict[str, Any]) -> Dict[str, Any]:
        cache_data = {
            "barcode": barcode.strip(),
            **food_data
        }
        if not is_supabase_live():
            fallback_db.db["barcodeCache"][barcode.strip()] = cache_data
            fallback_db.save_db()
            return cache_data

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
        if not is_supabase_live():
            correction_id = str(uuid.uuid4())
            db_data["id"] = correction_id
            db_data["created_at"] = datetime.utcnow().isoformat() + "Z"
            fallback_db.db["userCorrections"][correction_id] = db_data
            fallback_db.save_db()
            return db_data

        res = supabase_client.from_("food_corrections").insert(db_data).execute()
        return res.data[0]

    def get_corrections(self, user_id: str) -> List[Dict[str, Any]]:
        if not is_supabase_live():
            corrections = list(fallback_db.db.get("userCorrections", {}).values())
            return [c for c in corrections if c["user_id"] == user_id]

        res = supabase_client.from_("food_corrections").select("*").eq("user_id", user_id).execute()
        return res.data or []

    # --- Favorite Foods ---
    def get_favorites(self, user_id: str) -> List[Dict[str, Any]]:
        if not is_supabase_live():
            favs = fallback_db.db.get("favoriteFoods", {}).get(user_id, [])
            return favs

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
        if not is_supabase_live():
            if user_id not in fallback_db.db["favoriteFoods"]:
                fallback_db.db["favoriteFoods"][user_id] = []
            
            # Remove existing duplicate
            fallback_db.db["favoriteFoods"][user_id] = [
                f for f in fallback_db.db["favoriteFoods"][user_id] 
                if f["food_name"].lower() != db_data["food_name"].lower()
            ]
            
            db_data["id"] = str(uuid.uuid4())
            db_data["created_at"] = datetime.utcnow().isoformat() + "Z"
            fallback_db.db["favoriteFoods"][user_id].append(db_data)
            fallback_db.save_db()
            return db_data

        try:
            res = supabase_client.from_("favorite_foods").upsert(db_data, on_conflict="user_id,food_name").execute()
            return res.data[0]
        except Exception:
            return db_data

    def remove_favorite(self, user_id: str, food_name: str) -> bool:
        if not is_supabase_live():
            if user_id in fallback_db.db["favoriteFoods"]:
                fallback_db.db["favoriteFoods"][user_id] = [
                    f for f in fallback_db.db["favoriteFoods"][user_id]
                    if f["food_name"].lower() != food_name.lower()
                ]
                fallback_db.save_db()
                return True
            return False

        res = supabase_client.from_("favorite_foods").delete().eq("user_id", user_id).ilike("food_name", food_name).execute()
        return bool(res.data)

    # --- Recent Foods ---
    def get_recents(self, user_id: str, limit: int = 15) -> List[Dict[str, Any]]:
        if not is_supabase_live():
            recents = fallback_db.db.get("recentFoods", {}).get(user_id, [])
            return sorted(recents, key=lambda x: x["last_logged_at"], reverse=True)[:limit]

        res = supabase_client.from_("recent_foods").select("*").eq("user_id", user_id).order("last_logged_at", desc=True).limit(limit).execute()
        return res.data or []

    def add_recent(self, user_id: str, food_name: str) -> Dict[str, Any]:
        db_data = {
            "user_id": user_id,
            "food_name": food_name.strip(),
            "last_logged_at": datetime.utcnow().isoformat() + "Z"
        }
        if not is_supabase_live():
            if user_id not in fallback_db.db["recentFoods"]:
                fallback_db.db["recentFoods"][user_id] = []
            
            # Remove existing duplicate
            fallback_db.db["recentFoods"][user_id] = [
                f for f in fallback_db.db["recentFoods"][user_id] 
                if f["food_name"].lower() != food_name.lower()
            ]
            db_data["id"] = str(uuid.uuid4())
            fallback_db.db["recentFoods"][user_id].append(db_data)
            fallback_db.save_db()
            return db_data

        try:
            res = supabase_client.from_("recent_foods").upsert(db_data, on_conflict="user_id,food_name").execute()
            return res.data[0]
        except Exception:
            return db_data

food_repository = FoodRepository()
