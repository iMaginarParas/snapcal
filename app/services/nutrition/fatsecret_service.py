import os
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional

FATSECRET_CLIENT_ID = os.getenv("FATSECRET_CLIENT_ID") or ""
FATSECRET_CLIENT_SECRET = os.getenv("FATSECRET_CLIENT_SECRET") or ""

# Check if client keys are valid and not placeholders
is_configured = (
    FATSECRET_CLIENT_ID 
    and FATSECRET_CLIENT_SECRET 
    and "placeholder" not in FATSECRET_CLIENT_ID.lower()
    and "your_client_id" not in FATSECRET_CLIENT_ID.lower()
)

class FatSecretService:
    def __init__(self):
        self.access_token: Optional[str] = None

    def _get_access_token(self) -> Optional[str]:
        """Obtains OAuth2 access token from FatSecret."""
        if not is_configured:
            raise ValueError("FatSecret API Client ID/Secret are not configured. Please set them in environment variables.")
            
        try:
            url = "https://oauth.fatsecret.com/connect/token"
            data = urllib.parse.urlencode({
                "grant_type": "client_credentials",
                "scope": "basic"
            }).encode("utf-8")
            
            # Setup Basic Auth Header
            req = urllib.request.Request(url, data=data)
            auth_str = f"{FATSECRET_CLIENT_ID}:{FATSECRET_CLIENT_SECRET}"
            import base64
            encoded_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
            req.add_header("Authorization", f"Basic {encoded_auth}")
            
            with urllib.request.urlopen(req, timeout=5) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                self.access_token = res_data.get("access_token")
                return self.access_token
        except Exception as e:
            print(f"FatSecret Authentication Error: {e}")
            raise e

    def search_branded_food(self, query: str) -> Optional[Dict[str, Any]]:
        """Searches FatSecret for a food item and returns canonical macro mappings."""
        if not is_configured:
            raise ValueError("FatSecret API Client ID/Secret are not configured. Please set them in environment variables.")

        token = self.access_token or self._get_access_token()
        if not token:
            raise ValueError("Could not obtain valid access token from FatSecret API.")

        try:
            # FatSecret API request to search foods
            params = urllib.parse.urlencode({
                "method": "foods.search",
                "search_expression": query,
                "format": "json"
            })
            url = f"https://platform.fatsecret.com/rest/server.api?{params}"
            req = urllib.request.Request(url)
            req.add_header("Authorization", f"Bearer {token}")
            
            with urllib.request.urlopen(req, timeout=5) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                foods = res_data.get("foods", {}).get("food", [])
                if not foods:
                    return None
                    
                # Get the first result
                first_food = foods[0] if isinstance(foods, list) else foods
                food_id = first_food.get("food_id")
                
                # Fetch detailed nutrition info
                return self.get_food_details(food_id)
        except Exception as e:
            print(f"FatSecret Search Error: {e}")
            raise e

    def get_food_details(self, food_id: str) -> Optional[Dict[str, Any]]:
        """Fetches detailed nutrition metrics from food_id."""
        token = self.access_token or self._get_access_token()
        if not token:
            raise ValueError("Could not obtain valid access token from FatSecret API.")

        try:
            params = urllib.parse.urlencode({
                "method": "food.get.v2",
                "food_id": food_id,
                "format": "json"
            })
            url = f"https://platform.fatsecret.com/rest/server.api?{params}"
            req = urllib.request.Request(url)
            req.add_header("Authorization", f"Bearer {token}")
            
            with urllib.request.urlopen(req, timeout=5) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                food = res_data.get("food", {})
                servings = food.get("servings", {}).get("serving", [])
                
                # Find standard serving (prefer grams/100g if possible)
                if not servings:
                    return None
                
                serving = servings[0] if isinstance(servings, list) else servings
                for s in (servings if isinstance(servings, list) else [servings]):
                    if s.get("metric_serving_unit") == "g":
                        serving = s
                        break
                
                # Parse macros
                metric_weight = float(serving.get("metric_serving_amount") or 100.0)
                # Calculate macros normalized to 100g basis
                factor = 100.0 / metric_weight if metric_weight > 0 else 1.0
                
                calories = float(serving.get("calories") or 0.0) * factor
                protein = float(serving.get("protein") or 0.0) * factor
                carbs = float(serving.get("carbohydrate") or 0.0) * factor
                fat = float(serving.get("fat") or 0.0) * factor
                fiber = float(serving.get("fiber") or 0.0) * factor
                sodium = float(serving.get("sodium") or 0.0) * factor
                
                return {
                    "food_name": food.get("food_name"),
                    "calories": int(calories),
                    "protein": round(protein, 1),
                    "carbs": round(carbs, 1),
                    "fat": round(fat, 1),
                    "fiber": round(fiber, 1),
                    "sodium": round(sodium, 1),
                    "serving_size_g": 100.0,
                    "source": "FatSecret"
                }
        except Exception as e:
            print(f"FatSecret food details fetch error: {e}")
            raise e

fatsecret_service = FatSecretService()
