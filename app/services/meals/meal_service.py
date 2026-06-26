from typing import Optional, List, Dict, Any
from fastapi import UploadFile
from app.repositories.food_repository import food_repository
from app.repositories.meal_repository import meal_repository
from app.repositories.nutrition_repository import nutrition_repository
from app.repositories.db_repository import db_repository
from app.schemas.meals import MealSaveRequest, ManualMealLogRequest, MealTemplateSave
from app.core.exceptions import BadRequestException
from app.services.ai.vision_service import analyze_meal_image_with_ai
from app.services.ai.food_normalizer import food_normalizer
from app.services.nutrition.nutrition_engine import nutrition_engine
from app.services.nutrition.cache_service import cache_service
from app.services.nutrition.fatsecret_service import fatsecret_service
from app.services.nutrition.usda_service import usda_service
from datetime import datetime

class MealService:
    async def analyze_meal_image(self, user_id: str, image: UploadFile) -> dict:
        """
        Sends the uploaded photo to Gemini Vision for food recognition,
        then normalizes food names and resolves exact database nutritional values.
        """
        try:
            image_bytes = await image.read()
            # 1. AI Vision for image understanding only
            ai_response = analyze_meal_image_with_ai(image_bytes, image.content_type)
            
            foods = ai_response.get("foods") or []
            meal_type = ai_response.get("meal_type") or "Lunch"
            image_quality = ai_response.get("image_quality") or "Good"
            
            calculated_foods = []
            total_calories = 0
            total_protein = 0.0
            total_carbs = 0.0
            total_fat = 0.0
            total_fiber = 0.0
            total_weight = 0.0

            for f in foods:
                raw_name = f["name"]
                weight = float(f.get("weight_g") or f.get("weight") or 150.0)
                cooking_method = f.get("cooking_method") or "cooked"
                ingredients = f.get("ingredients") or []
                hidden = f.get("possible_hidden_ingredients") or []
                portion_desc = f.get("portion_description") or f"1 serving"
                confidence = float(f.get("confidence") or 85)

                # 2. Food Normalizer
                normalized_name = food_normalizer.normalize(raw_name)

                # 3. Nutrition Engine (Deterministic nutrition resolution)
                nutri = nutrition_engine.calculate_nutrition(
                    food_name=normalized_name,
                    weight_g=weight,
                    cooking_method=cooking_method,
                    ingredients=ingredients,
                    possible_hidden_ingredients=hidden
                )

                # 4. Confidence Level classification
                if confidence > 90:
                    confidence_level = "high"
                elif confidence >= 70:
                    confidence_level = "medium"
                else:
                    confidence_level = "low"

                nutri_item = {
                    "food_name": raw_name,
                    "normalized_name": normalized_name,
                    "weight_g": weight,
                    "serving": portion_desc,
                    "calories": nutri["calories"],
                    "protein": nutri["protein"],
                    "carbs": nutri["carbs"],
                    "fat": nutri["fat"],
                    "fiber": nutri["fiber"],
                    "confidence": confidence,
                    "confidence_level": confidence_level,
                    "cooking_method": cooking_method,
                    "ingredients": ingredients,
                    "hidden_ingredients": hidden
                }

                calculated_foods.append(nutri_item)
                total_calories += nutri["calories"]
                total_protein += nutri["protein"]
                total_carbs += nutri["carbs"]
                total_fat += nutri["fat"]
                total_fiber += nutri["fiber"]
                total_weight += weight

            # Construct dynamic meal summary name
            meal_name = calculated_foods[0]["normalized_name"] if calculated_foods else "Unknown Meal"
            if len(calculated_foods) > 1:
                meal_name += f" with {calculated_foods[1]['normalized_name']}"
                if len(calculated_foods) > 2:
                    meal_name += f" and {len(calculated_foods)-2} more"

            return {
                "success": True,
                "data": {
                    "name": meal_name,
                    "meal_type": meal_type,
                    "image_quality": image_quality,
                    "total_weight": round(total_weight, 1),
                    "total_calories": total_calories,
                    "protein": round(total_protein, 1),
                    "carbs": round(total_carbs, 1),
                    "fat": round(total_fat, 1),
                    "fiber": round(total_fiber, 1),
                    "foods": calculated_foods
                }
            }
        except Exception as e:
            raise BadRequestException(detail=str(e))

    def save_ai_meal(self, user_id: str, payload: MealSaveRequest) -> dict:
        """Saves a reviewed meal, learns corrections, and logs recents."""
        # 1. Create main meal record
        logged_at = payload.date + "T12:00:00.000Z" if payload.date else datetime.utcnow().isoformat() + "Z"
        
        meal_data = {
            "name": payload.name,
            "meal_type": payload.meal_type or "Lunch",
            "total_weight": float(payload.total_weight or sum(f.weight_g for f in payload.foods)),
            "total_calories": payload.total_calories,
            "protein": payload.protein,
            "carbs": payload.carbs,
            "fat": payload.fat,
            "fiber": payload.fiber,
            "image_url": payload.image_url,
            "logged_at": logged_at
        }
        res_meal = meal_repository.create_meal(user_id, meal_data)
        meal_id = res_meal["id"]

        # 2. Save individual food items and update recent list
        food_items_payload = []
        for food in payload.foods:
            food_items_payload.append({
                "food_name": food.food_name,
                "normalized_name": food_normalizer.normalize(food.food_name),
                "weight_g": food.weight_g,
                "serving": food.serving or "1 serving",
                "calories": food.calories,
                "protein": food.protein,
                "carbs": food.carbs,
                "fat": food.fat,
                "fiber": food.fiber,
                "confidence": food.confidence,
                "cooking_method": food.cooking_method or "cooked",
                "ingredients": food.ingredients or [],
                "hidden_ingredients": food.hidden_ingredients or []
            })
            
            # Add to user's recent foods
            food_repository.add_recent(user_id, food.food_name)
            
            # Check and store corrections (Learning System)
            # If user renamed a food item, save it to build future prompts
            original = food.food_name
            normalized = food_normalizer.normalize(food.food_name)
            if original.lower() != normalized.lower():
                food_repository.create_correction(user_id, {
                    "original_name": original,
                    "corrected_name": normalized,
                    "corrected_weight": food.weight_g,
                    "corrected_cooking_method": food.cooking_method,
                    "corrected_serving": food.serving
                })

        if food_items_payload:
            meal_repository.create_food_items(meal_id, food_items_payload)

        # 3. Synchronize with daily stats table
        date_str = payload.date or datetime.utcnow().strftime("%Y-%m-%d")
        existing_stats = db_repository.get_daily_stats(user_id, date_str)
        if existing_stats:
            # We don't overwrite steps or water, but confirm stats exist
            pass
        else:
            db_repository.create_daily_stats({
                "user_id": user_id,
                "date": date_str,
                "steps": 0,
                "water_ml": 0
            })

        # Fetch meal with populated items
        refetched_meals = meal_repository.get_meals_by_date(user_id, date_str)
        saved_meal = next((m for m in refetched_meals if m["id"] == meal_id), res_meal)
        
        return {"success": True, "data": saved_meal}

    def log_manual_meal(self, user_id: str, payload: ManualMealLogRequest) -> dict:
        """Logs a manually inputted meal directly into journal."""
        date_str = payload.date or datetime.utcnow().strftime("%Y-%m-%d")
        logged_at = f"{date_str}T12:00:00.000Z"
        
        meal_data = {
            "name": payload.name,
            "meal_type": "Other",
            "total_weight": 100.0,
            "total_calories": payload.calories,
            "protein": payload.protein or 0.0,
            "carbs": payload.carbs or 0.0,
            "fat": payload.fats or 0.0,
            "fiber": 0.0,
            "image_url": payload.image_url,
            "logged_at": logged_at
        }
        res = meal_repository.create_meal(user_id, meal_data)
        
        # Log food item for consistency
        food_item = {
            "food_name": payload.name,
            "normalized_name": food_normalizer.normalize(payload.name),
            "weight": 100.0,
            "serving": "1 serving",
            "calories": payload.calories,
            "protein": payload.protein or 0.0,
            "carbs": payload.carbs or 0.0,
            "fat": payload.fats or 0.0,
            "fiber": 0.0,
            "confidence": 100.0,
            "cooking_method": "cooked",
            "ingredients": []
        }
        meal_repository.create_food_items(res["id"], [food_item])
        
        food_repository.add_recent(user_id, payload.name)
        
        return {"success": True, "data": res}

    def get_meal_history(self, user_id: str, page: int = 1, limit: int = 20) -> dict:
        offset = (page - 1) * limit
        meals = meal_repository.get_meal_history(user_id, limit, offset)
        return {"success": True, "data": meals}

    def get_daily_nutrition(self, user_id: str, date_str: str) -> dict:
        summary = nutrition_repository.get_daily_summary(user_id, date_str)
        return {"success": True, "data": summary}

    def get_weekly_nutrition(self, user_id: str) -> dict:
        summary = nutrition_repository.get_weekly_summary(user_id)
        return {"success": True, "data": summary}

    # --- Barcode System ---
    def scan_barcode(self, barcode: str) -> dict:
        """Resolves food items from barcodes using a multi-level caching system."""
        # 1. Check local barcode cache
        cached = cache_service.get_cached_barcode(barcode)
        if cached:
            print(f"BarcodeService: Barcode '{barcode}' resolved from local cache.")
            return {"success": True, "data": cached}

        # 2. Try FatSecret API (contains massive branded/UPC food database)
        fatsecret_item = fatsecret_service.search_branded_food(barcode)
        if fatsecret_item:
            print(f"BarcodeService: Barcode '{barcode}' resolved via FatSecret. Caching...")
            cache_service.cache_barcode_details(barcode, fatsecret_item)
            return {"success": True, "data": fatsecret_item}

        # 3. Try USDA API lookup
        usda_item = usda_service.search_usda_food(barcode)
        if usda_item:
            print(f"BarcodeService: Barcode '{barcode}' resolved via USDA. Caching...")
            cache_service.cache_barcode_details(barcode, usda_item)
            return {"success": True, "data": usda_item}

        raise BadRequestException(detail=f"Barcode {barcode} could not be resolved.")

    # --- Favorite Foods ---
    def get_favorites(self, user_id: str) -> dict:
        favs = food_repository.get_favorites(user_id)
        return {"success": True, "data": favs}

    def add_favorite(self, user_id: str, food_data: dict) -> dict:
        fav = food_repository.add_favorite(user_id, food_data)
        return {"success": True, "data": fav}

    def remove_favorite(self, user_id: str, food_name: str) -> dict:
        success = food_repository.remove_favorite(user_id, food_name)
        return {"success": True, "data": {"success": success}}

    # --- Recent Foods ---
    def get_recents(self, user_id: str, limit: int = 15) -> dict:
        recents = food_repository.get_recents(user_id, limit)
        return {"success": True, "data": recents}

    # --- Meal Templates ---
    def create_template(self, user_id: str, payload: MealTemplateSave) -> dict:
        foods_dict = []
        for food in payload.foods:
            foods_dict.append(food.dict())
        res = meal_repository.create_template(user_id, payload.template_name, foods_dict)
        return {"success": True, "data": res}

    def get_templates(self, user_id: str) -> dict:
        templates = meal_repository.get_templates(user_id)
        return {"success": True, "data": templates}

    def search_foods(self, query: str, limit: int = 15) -> dict:
        foods = food_repository.search_foods(query, limit)
        return {"success": True, "data": foods}

meal_service = MealService()
