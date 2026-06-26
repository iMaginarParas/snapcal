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
        # Step 1: Check local cache
        cached_item = cache_service.get_cached_food(food_name)
        if cached_item:
            print(f"NutritionResolver: '{food_name}' found in Local Cache.")
            return cached_item

        # Step 2: Check Indian Food Database
        indian_item = indian_food_service.get_indian_food(food_name)
        if indian_item:
            print(f"NutritionResolver: '{food_name}' found in Indian Food DB. Caching...")
            cache_service.cache_food_details(food_name, indian_item)
            return indian_item

        # Step 3: Check FatSecret API
        fatsecret_item = fatsecret_service.search_branded_food(food_name)
        if fatsecret_item:
            print(f"NutritionResolver: '{food_name}' resolved via FatSecret API. Caching...")
            cache_service.cache_food_details(food_name, fatsecret_item)
            return fatsecret_item

        # Step 4: Check USDA API (Final Fallback)
        usda_item = usda_service.search_usda_food(food_name)
        if usda_item:
            print(f"NutritionResolver: '{food_name}' resolved via USDA API. Caching...")
            cache_service.cache_food_details(food_name, usda_item)
            return usda_item

        # Smart fallback if absolutely nothing works
        print(f"NutritionResolver: Could not resolve '{food_name}' anywhere. Using generic fallback.")
        fallback_item = {
            "food_name": food_name.title(),
            "calories": 150,
            "protein": 5.0,
            "carbs": 20.0,
            "fat": 5.0,
            "fiber": 1.5,
            "sodium": 150.0,
            "serving_size_g": 100.0,
            "source": "Fallback"
        }
        cache_service.cache_food_details(food_name, fallback_item)
        return fallback_item

nutrition_resolver = NutritionResolver()
