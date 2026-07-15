from typing import List, Dict, Any, Optional
from datetime import datetime
from app.database.supabase import supabase_client

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

        res = supabase_client.from_("food_items").insert(db_items).execute()
        return res.data if res else []

    def get_meals_by_date(self, user_id: str, date_str: str) -> List[Dict[str, Any]]:
        res = supabase_client.from_("meals").select("*, food_items(*)").eq("user_id", user_id).gte("logged_at", f"{date_str}T00:00:00.000Z").lte("logged_at", f"{date_str}T23:59:59.999Z").execute()
        return res.data if res else []

    def get_meal_history(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        res = supabase_client.from_("meals").select("*, food_items(*)").eq("user_id", user_id).order("logged_at", desc=True).range(offset, offset + limit - 1).execute()
        return res.data if res else []

    def delete_meal(self, user_id: str, meal_id: str) -> bool:
        res = supabase_client.from_("meals").delete().eq("id", meal_id).eq("user_id", user_id).execute()
        return bool(res.data) if res else False

    # --- Meal Templates ---
    def create_template(self, user_id: str, template_name: str, foods: List[Dict[str, Any]]) -> Dict[str, Any]:
        template_payload = {
            "user_id": user_id,
            "template_name": template_name,
            "foods": foods
        }

        res = supabase_client.from_("meal_templates").insert(template_payload).execute()
        return res.data[0] if res and res.data else {}

    def get_templates(self, user_id: str) -> List[Dict[str, Any]]:
        res = supabase_client.from_("meal_templates").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return res.data if res else []

meal_repository = MealRepository()
