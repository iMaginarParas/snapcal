import os
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional

USDA_API_KEY = os.getenv("USDA_API_KEY") or ""

# Check if USDA API key is set and not a placeholder
is_configured = (
    USDA_API_KEY 
    and "placeholder" not in USDA_API_KEY.lower() 
    and "your_usda_api_key" not in USDA_API_KEY.lower()
)

class UsdaService:
    def search_usda_food(self, query: str) -> Optional[Dict[str, Any]]:
        """Searches USDA FoodData Central and extracts key nutrients per 100g."""
        if not is_configured:
            print("USDA API not configured. Returning simulated USDA food.")
            return self._get_mock_usda_food(query)

        try:
            params = urllib.parse.urlencode({
                "api_key": USDA_API_KEY,
                "query": query,
                "pageSize": 1,
                "dataType": ["Survey (FNDDS)", "Foundation"]
            })
            url = f"https://api.nal.usda.gov/fdc/v1/foods/search?{params}"
            
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                foods = res_data.get("foods", [])
                if not foods:
                    return None
                    
                first_food = foods[0]
                nutrients = first_food.get("foodNutrients", [])
                
                # Extract macronutrients per 100g
                calories = 0
                protein = 0.0
                carbs = 0.0
                fat = 0.0
                fiber = 0.0
                sodium = 0.0
                
                for n in nutrients:
                    # USDA reports standard nutrients per 100g
                    nid = n.get("nutrientId")
                    val = float(n.get("value") or 0.0)
                    
                    if nid == 1008: # Calories
                        calories = val
                    elif nid == 1003: # Protein
                        protein = val
                    elif nid == 1005: # Carbohydrate
                        carbs = val
                    elif nid == 1004: # Total Lipid (fat)
                        fat = val
                    elif nid == 1079: # Fiber
                        fiber = val
                    elif nid == 1093: # Sodium (mg)
                        sodium = val

                return {
                    "food_name": first_food.get("description"),
                    "calories": int(calories),
                    "protein": round(protein, 1),
                    "carbs": round(carbs, 1),
                    "fat": round(fat, 1),
                    "fiber": round(fiber, 1),
                    "sodium": round(sodium, 1),
                    "serving_size_g": 100.0,
                    "source": "USDA"
                }
        except Exception as e:
            print(f"USDA Search Error: {e}. Falling back to mock.")
            return self._get_mock_usda_food(query)

    def _get_mock_usda_food(self, query: str) -> Optional[Dict[str, Any]]:
        """Mock fallback database for general USDA items (raw meats, grains, vegetables, etc.)"""
        query_lower = query.lower()
        mock_db = {
            "apple": {"calories": 52, "protein": 0.3, "carbs": 13.8, "fat": 0.2, "fiber": 2.4, "sodium": 1.0},
            "banana": {"calories": 89, "protein": 1.1, "carbs": 22.8, "fat": 0.3, "fiber": 2.6, "sodium": 1.0},
            "broccoli": {"calories": 34, "protein": 2.8, "carbs": 6.6, "fat": 0.4, "fiber": 2.6, "sodium": 33.0},
            "chicken breast": {"calories": 165, "protein": 31.0, "carbs": 0.0, "fat": 3.6, "fiber": 0.0, "sodium": 74.0},
            "salmon": {"calories": 208, "protein": 20.0, "carbs": 0.0, "fat": 13.0, "fiber": 0.0, "sodium": 59.0},
            "egg": {"calories": 155, "protein": 13.0, "carbs": 1.1, "fat": 11.0, "fiber": 0.0, "sodium": 124.0},
            "white rice": {"calories": 130, "protein": 2.7, "carbs": 28.0, "fat": 0.3, "fiber": 0.4, "sodium": 1.0},
            "brown rice": {"calories": 111, "protein": 2.6, "carbs": 23.0, "fat": 0.9, "fiber": 1.8, "sodium": 5.0},
            "greek yogurt": {"calories": 59, "protein": 10.0, "carbs": 3.6, "fat": 0.4, "fiber": 0.0, "sodium": 36.0},
            "avocado": {"calories": 160, "protein": 2.0, "carbs": 8.5, "fat": 14.7, "fiber": 6.7, "sodium": 7.0},
            "oats": {"calories": 389, "protein": 16.9, "carbs": 66.3, "fat": 6.9, "fiber": 10.6, "sodium": 2.0},
            "spinach": {"calories": 23, "protein": 2.9, "carbs": 3.6, "fat": 0.4, "fiber": 2.2, "sodium": 79.0},
            "sweet potato": {"calories": 86, "protein": 1.6, "carbs": 20.0, "fat": 0.1, "fiber": 3.0, "sodium": 55.0},
            "milk": {"calories": 42, "protein": 3.4, "carbs": 5.0, "fat": 1.0, "fiber": 0.0, "sodium": 44.0},
            "almonds": {"calories": 579, "protein": 21.0, "carbs": 21.6, "fat": 49.9, "fiber": 12.5, "sodium": 1.0}
        }
        
        for key, val in mock_db.items():
            if key in query_lower:
                return {
                    "food_name": query.title(),
                    "calories": val["calories"],
                    "protein": val["protein"],
                    "carbs": val["carbs"],
                    "fat": val["fat"],
                    "fiber": val["fiber"],
                    "sodium": val["sodium"],
                    "serving_size_g": 100.0,
                    "source": "USDA (Mock)"
                }
                
        return {
            "food_name": query.title(),
            "calories": 80,
            "protein": 2.5,
            "carbs": 15.0,
            "fat": 1.2,
            "fiber": 1.8,
            "sodium": 30.0,
            "serving_size_g": 100.0,
            "source": "USDA (Simulated)"
        }

usda_service = UsdaService()
