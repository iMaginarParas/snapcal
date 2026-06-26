import difflib
from typing import Dict, Any, Optional
from app.services.nutrition.nutrition_database import NUTRITION_DB

class IndianFoodService:
    def get_indian_food(self, food_name: str) -> Optional[Dict[str, Any]]:
        """
        Searches the offline Indian Food Database for a matching item.
        Returns nutritional data per 100g base.
        """
        if not food_name:
            return None

        name_lower = food_name.strip().lower()
        keys = list(NUTRITION_DB.keys())
        
        # 1. Exact Match
        if name_lower in NUTRITION_DB:
            db_item = NUTRITION_DB[name_lower]
            return self._format_result(name_lower, db_item)

        # 2. Substring matching (e.g. "chicken biryani spicy" matches "chicken biryani")
        for key in keys:
            if key in name_lower or name_lower in key:
                return self._format_result(key, NUTRITION_DB[key])

        # 3. Fuzzy Match via difflib
        matches = difflib.get_close_matches(name_lower, keys, n=1, cutoff=0.6)
        if matches:
            matched_key = matches[0]
            return self._format_result(matched_key, NUTRITION_DB[matched_key])

        return None

    def _format_result(self, standard_name: str, db_item: Dict[str, Any]) -> Dict[str, Any]:
        """Formats the database metrics into a unified 100g database return."""
        return {
            "food_name": standard_name.title(),
            "calories": db_item["calories"],
            "protein": db_item["protein"],
            "carbs": db_item["carbs"],
            "fat": db_item["fat"],
            "fiber": db_item.get("fiber", 0.0),
            "sodium": db_item.get("sodium", 150),
            "serving_size_g": 100.0,
            "source": "IndianFoodDB"
        }

indian_food_service = IndianFoodService()
