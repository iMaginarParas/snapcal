from typing import Dict, Any, Optional
from app.repositories.food_repository import food_repository

class CacheService:
    def get_cached_food(self, food_name: str) -> Optional[Dict[str, Any]]:
        """Looks up resolved nutrition for a food in the cache."""
        cache_hit = food_repository.get_nutrition_cache(food_name)
        if cache_hit:
            return {
                "food_name": cache_hit["food_name"],
                "calories": int(cache_hit["calories"]),
                "protein": float(cache_hit["protein"]),
                "carbs": float(cache_hit["carbs"]),
                "fat": float(cache_hit["fat"]),
                "fiber": float(cache_hit.get("fiber") or 0.0),
                "sodium": float(cache_hit.get("sodium") or 0.0),
                "serving_size_g": float(cache_hit.get("weight") or 100.0),
                "source": cache_hit.get("source") or "Cache"
            }
        return None

    def cache_food_details(self, food_name: str, food_data: Dict[str, Any]) -> Dict[str, Any]:
        """Saves a resolved food lookup into the nutrition_cache table."""
        cache_data = {
            "food_name": food_name.strip(),
            "weight": float(food_data.get("serving_size_g") or 100.0),
            "calories": int(food_data["calories"]),
            "protein": float(food_data["protein"]),
            "carbs": float(food_data["carbs"]),
            "fat": float(food_data["fat"]),
            "fiber": float(food_data.get("fiber") or 0.0),
            "sodium": float(food_data.get("sodium") or 0.0),
            "serving_size": food_data.get("serving_size") or "100g",
            "source": food_data.get("source") or "Unknown"
        }
        return food_repository.create_nutrition_cache(cache_data)

    def get_cached_barcode(self, barcode: str) -> Optional[Dict[str, Any]]:
        """Checks if a barcode was scanned and cached before."""
        cache_hit = food_repository.get_barcode_cache(barcode)
        if cache_hit:
            return {
                "food_name": cache_hit["food_name"],
                "calories": int(cache_hit["calories"]),
                "protein": float(cache_hit["protein"]),
                "carbs": float(cache_hit["carbs"]),
                "fat": float(cache_hit["fat"]),
                "fiber": float(cache_hit.get("fiber") or 0.0),
                "sodium": float(cache_hit.get("sodium") or 0.0),
                "serving_size": cache_hit.get("serving_size") or "1 serving",
                "source": cache_hit.get("source") or "BarcodeCache"
            }
        return None

    def cache_barcode_details(self, barcode: str, food_data: Dict[str, Any]) -> Dict[str, Any]:
        """Caches barcode scans locally."""
        cache_data = {
            "food_name": food_data["food_name"],
            "calories": int(food_data["calories"]),
            "protein": float(food_data["protein"]),
            "carbs": float(food_data["carbs"]),
            "fat": float(food_data["fat"]),
            "fiber": float(food_data.get("fiber") or 0.0),
            "sodium": float(food_data.get("sodium") or 0.0),
            "serving_size": food_data.get("serving_size") or "1 serving",
            "source": food_data.get("source") or "BarcodeAPI"
        }
        return food_repository.create_barcode_cache(barcode, cache_data)

cache_service = CacheService()
