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
            return None
            
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
            return None

    def search_branded_food(self, query: str) -> Optional[Dict[str, Any]]:
        """Searches FatSecret for a food item and returns canonical macro mappings."""
        if not is_configured:
            print("FatSecret API not configured. Returning simulated branded food.")
            return self._get_mock_branded_food(query)

        token = self.access_token or self._get_access_token()
        if not token:
            print("Could not obtain FatSecret token. Returning simulated branded food.")
            return self._get_mock_branded_food(query)

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
            print(f"FatSecret search error: {e}. Falling back to mock.")
            return self._get_mock_branded_food(query)

    def get_food_details(self, food_id: str) -> Optional[Dict[str, Any]]:
        """Fetches detailed nutrition metrics from food_id."""
        token = self.access_token or self._get_access_token()
        if not token:
            return None

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
            return None

    def _get_mock_branded_food(self, query: str) -> Optional[Dict[str, Any]]:
        """Mock fallback database for international and branded foods."""
        query_lower = query.lower()
        mock_db = {
            "coca cola": {"calories": 42, "protein": 0.0, "carbs": 10.6, "fat": 0.0, "fiber": 0.0, "sodium": 4.0},
            "oreo": {"calories": 480, "protein": 4.0, "carbs": 70.0, "fat": 20.0, "fiber": 2.5, "sodium": 520.0},
            "kellogg": {"calories": 378, "protein": 7.0, "carbs": 84.0, "fat": 0.8, "fiber": 3.0, "sodium": 729.0},
            "whey protein": {"calories": 400, "protein": 80.0, "carbs": 6.0, "fat": 6.0, "fiber": 0.0, "sodium": 160.0},
            "subway": {"calories": 180, "protein": 14.0, "carbs": 24.0, "fat": 3.0, "fiber": 4.0, "sodium": 480.0},
            "mcdonald": {"calories": 250, "protein": 12.0, "carbs": 30.0, "fat": 9.0, "fiber": 2.0, "sodium": 520.0},
            "maggi": {"calories": 420, "protein": 8.0, "carbs": 62.0, "fat": 15.0, "fiber": 3.5, "sodium": 980.0},
            "snickers": {"calories": 488, "protein": 8.6, "carbs": 60.0, "fat": 24.0, "fiber": 2.6, "sodium": 236.0}
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
                    "source": "FatSecret (Mock)"
                }
                
        # Return a smart default branded item if no match
        return {
            "food_name": query.title(),
            "calories": 220,
            "protein": 6.5,
            "carbs": 28.0,
            "fat": 8.0,
            "fiber": 1.5,
            "sodium": 150.0,
            "serving_size_g": 100.0,
            "source": "FatSecret (Simulated)"
        }

fatsecret_service = FatSecretService()
