from typing import Dict, Any, Optional
from app.services.nutrition.cache_service import cache_service
from app.services.nutrition.indian_food_service import indian_food_service
from app.services.nutrition.fatsecret_service import fatsecret_service
from app.services.nutrition.usda_service import usda_service

class NutritionResolver:
    def resolve_nutrition(self, food_name: str) -> Dict[str, Any]:
        """
        Resolves food nutrition (per 100g base) in strict priority order:
        1. Local Cache
        2. Indian Food DB
        3. FatSecret API
        4. USDA API
        
        Returns unified nutrition facts.
        """
        if not food_name:
            food_name = "Food Item"

        # Step 1: Check local cache
        try:
            cached_item = cache_service.get_cached_food(food_name)
            if cached_item:
                print(f"NutritionResolver: '{food_name}' found in Local Cache.")
                return cached_item
        except Exception as e:
            print(f"NutritionResolver: Local Cache lookup warning for '{food_name}': {e}")

        # Step 2: Check Indian Food Database
        try:
            indian_item = indian_food_service.get_indian_food(food_name)
            if indian_item:
                print(f"NutritionResolver: '{food_name}' found in Indian Food DB. Caching...")
                try:
                    cache_service.cache_food_details(food_name, indian_item)
                except Exception:
                    pass
                return indian_item
        except Exception as e:
            print(f"NutritionResolver: Indian Food DB lookup warning for '{food_name}': {e}")

        # Step 3: Check FatSecret API
        try:
            fatsecret_item = fatsecret_service.search_branded_food(food_name)
            if fatsecret_item:
                print(f"NutritionResolver: '{food_name}' resolved via FatSecret API. Caching...")
                try:
                    cache_service.cache_food_details(food_name, fatsecret_item)
                except Exception:
                    pass
                return fatsecret_item
        except Exception as e:
            print(f"NutritionResolver: FatSecret API lookup skipped for '{food_name}': {e}")

        # Step 4: Check USDA API (Final Fallback)
        try:
            usda_item = usda_service.search_usda_food(food_name)
            if usda_item:
                print(f"NutritionResolver: '{food_name}' resolved via USDA API. Caching...")
                try:
                    cache_service.cache_food_details(food_name, usda_item)
                except Exception:
                    pass
                return usda_item
        except Exception as e:
            print(f"NutritionResolver: USDA API lookup skipped for '{food_name}': {e}")

        # Smart fallback if external APIs are not configured
        print(f"NutritionResolver: Could not resolve '{food_name}' externally. Using deterministic default fallback.")
        fallback_item = {
            "food_name": food_name.title(),
            "calories": 140,
            "protein": 3.0,
            "carbs": 22.0,
            "fat": 3.0,
            "fiber": 1.5,
            "sodium": 100.0,
            "serving_size_g": 100.0,
            "source": "Fallback"
        }
        try:
            cache_service.cache_food_details(food_name, fallback_item)
        except Exception:
            pass
        return fallback_item

nutrition_resolver = NutritionResolver()
