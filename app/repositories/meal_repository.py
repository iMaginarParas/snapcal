from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from app.database.supabase import supabase_client, is_supabase_live
from app.database.fallback import fallback_db

class MealRepository:
    def create_meal(self, user_id: str, meal_data: Dict[str, Any]) -> Dict[str, Any]:
        db_payload = {
            "user_id": user_id,
            "name": meal_data.get("name") or "Logged Meal",
            "meal_type": meal_data.get("meal_type") or "Lunch",
            "total_weight": float(meal_data.get("total_weight") or 0.0),
            "total_calories": int(meal_data.get("total_calories") or 0),
            "protein": float(meal_data.get("protein") or 0.0),
            "carbs": float(meal_data.get("carbs") or 0.0),
            "fat": float(meal_data.get("fat") or 0.0),
            "fiber": float(meal_data.get("fiber") or 0.0),
            "image_url": meal_data.get("image_url"),
            "logged_at": meal_data.get("logged_at") or datetime.utcnow().isoformat() + "Z"
        }

        if not is_supabase_live():
            res = fallback_db.add_meal(user_id, db_payload)
            return res

        res = supabase_client.from_("meals").insert(db_payload).execute()
        return res.data[0] if res and res.data else {}

    def create_food_items(self, meal_id: str, food_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        db_items = []
        for food in food_items:
            db_items.append({
                "meal_id": meal_id,
                "food_name": food["food_name"],
                "normalized_name": food.get("normalized_name") or food["food_name"],
                "weight": float(food.get("weight") or food.get("weight_g") or 0.0),
                "serving": food.get("serving") or "1 serving",
                "calories": int(food["calories"]),
                "protein": float(food["protein"]),
                "carbs": float(food["carbs"]),
                "fat": float(food["fat"]),
                "fiber": float(food.get("fiber") or 0.0),
                "confidence": float(food.get("confidence") or 100.0),
                "cooking_method": food.get("cooking_method") or "cooked",
                "ingredients": food.get("ingredients") or [],
                "hidden_ingredients": food.get("hidden_ingredients") or []
            })

        if not is_supabase_live():
            # In fallback mode, we append food items directly to the mocked meal object inside storage.json
            for user_id, meals in fallback_db.db["meals"].items():
                for m in meals:
                    if m["id"] == meal_id:
                        if "food_items" not in m:
                            m["food_items"] = []
                        m["food_items"].extend(db_items)
                        break
            fallback_db.save_db()
            return db_items

        res = supabase_client.from_("food_items").insert(db_items).execute()
        return res.data if res else []

    def get_meals_by_date(self, user_id: str, date_str: str) -> List[Dict[str, Any]]:
        if not is_supabase_live():
            meals = fallback_db.get_meals(user_id)
            return [m for m in meals if m.get("logged_at", "").split("T")[0] == date_str]

        res = supabase_client.from_("meals").select("*, food_items(*)").eq("user_id", user_id).gte("logged_at", f"{date_str}T00:00:00.000Z").lte("logged_at", f"{date_str}T23:59:59.999Z").execute()
        return res.data if res else []

    def get_meal_history(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        if not is_supabase_live():
            meals = fallback_db.get_meals(user_id)
            sorted_meals = sorted(meals, key=lambda x: x.get("logged_at", ""), reverse=True)
            return sorted_meals[offset : offset + limit]

        res = supabase_client.from_("meals").select("*, food_items(*)").eq("user_id", user_id).order("logged_at", desc=True).range(offset, offset + limit - 1).execute()
        return res.data if res else []

    def delete_meal(self, user_id: str, meal_id: str) -> bool:
        if not is_supabase_live():
            if user_id in fallback_db.db["meals"]:
                initial_len = len(fallback_db.db["meals"][user_id])
                fallback_db.db["meals"][user_id] = [m for m in fallback_db.db["meals"][user_id] if m["id"] != meal_id]
                fallback_db.save_db()
                return len(fallback_db.db["meals"][user_id]) < initial_len
            return False

        res = supabase_client.from_("meals").delete().eq("id", meal_id).eq("user_id", user_id).execute()
        return bool(res.data) if res else False

    # --- Meal Templates ---
    def create_template(self, user_id: str, template_name: str, foods: List[Dict[str, Any]]) -> Dict[str, Any]:
        template_payload = {
            "user_id": user_id,
            "template_name": template_name,
            "foods": foods
        }

        if not is_supabase_live():
            if user_id not in fallback_db.db["mealTemplates"]:
                fallback_db.db["mealTemplates"][user_id] = []
            template_payload["id"] = str(uuid.uuid4())
            template_payload["created_at"] = datetime.utcnow().isoformat() + "Z"
            fallback_db.db["mealTemplates"][user_id].append(template_payload)
            fallback_db.save_db()
            return template_payload

        res = supabase_client.from_("meal_templates").insert(template_payload).execute()
        return res.data[0] if res and res.data else {}

    def get_templates(self, user_id: str) -> List[Dict[str, Any]]:
        if not is_supabase_live():
            return fallback_db.db.get("mealTemplates", {}).get(user_id, [])

        res = supabase_client.from_("meal_templates").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return res.data if res else []

meal_repository = MealRepository()
