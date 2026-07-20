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
            raise ValueError("USDA API Key is not configured. Please set USDA_API_KEY in your environment.")

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
            print(f"USDA Search Error: {e}")
            raise e

usda_service = UsdaService()
