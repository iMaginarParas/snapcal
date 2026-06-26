from typing import Dict, Any, List, Optional
from app.services.nutrition.nutrition_resolver import nutrition_resolver

class NutritionEngine:
    def calculate_nutrition(
        self,
        food_name: str,
        weight_g: float,
        cooking_method: Optional[str] = "cooked",
        ingredients: Optional[List[str]] = None,
        possible_hidden_ingredients: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Determines exact calorie and macro breakdown based on database-derived facts.
        No nutrition calculations are performed using AI.
        Applies modifiers for cooking methods and estimates hidden fats.
        """
        # 1. Resolve base nutrition (normalized to 100g)
        base_nutri = nutrition_resolver.resolve_nutrition(food_name)
        
        factor = float(weight_g) / 100.0
        
        # 2. Base macro calculations
        calories = base_nutri["calories"] * factor
        protein = base_nutri["protein"] * factor
        carbs = base_nutri["carbs"] * factor
        fat = base_nutri["fat"] * factor
        fiber = base_nutri.get("fiber", 0.0) * factor
        sodium = base_nutri.get("sodium", 150.0) * factor
        
        # 3. Apply Cooking Method Modifiers
        method = (cooking_method or "cooked").strip().lower()
        if "fried" in method:
            # Deep fried increases fat content by 50% and adds base cooking oil calories
            fat *= 1.5
            calories += (20 * factor)
        elif "roasted" in method or "grilled" in method:
            # Light roasting adds 10% fat and light calorie addition
            fat *= 1.1
            calories += (5 * factor)
        elif "boiled" in method or "steamed" in method or "raw" in method:
            # Steamed/raw contains slightly less fat
            fat *= 0.95
            
        # 4. Estimate Hidden Ingredients (butter, ghee, oil, cream, cheese)
        hidden_fat_g = 0.0
        hidden_oil_kcal = 0
        
        # Merge visible ingredients and possible hidden ingredients lists for scanning
        all_ingredients = [i.lower() for i in (ingredients or [])]
        if possible_hidden_ingredients:
            all_ingredients.extend([i.lower() for i in possible_hidden_ingredients])
            
        # Ghee, butter, or oil adds hidden fats
        if any(x in all_ingredients for x in ["ghee", "butter", "oil", "cooking oil"]):
            # Add ~5g of hidden fat per 150g portion
            added_fat = 5.0 * (weight_g / 150.0)
            hidden_fat_g += added_fat
            hidden_oil_kcal += int(added_fat * 9)
            
        if any(x in all_ingredients for x in ["cheese", "cream", "mayo"]):
            # Add ~4g of hidden fat and 1g protein per 150g portion
            added_fat = 4.0 * (weight_g / 150.0)
            hidden_fat_g += added_fat
            hidden_oil_kcal += int(added_fat * 9)
            protein += 1.0 * (weight_g / 150.0)

        # 5. Combine totals
        fat += hidden_fat_g
        calories += hidden_oil_kcal
        
        # Keep calories, macros, and sodium normalized
        return {
            "food_name": food_name,
            "weight_g": round(weight_g, 1),
            "calories": int(calories),
            "protein": round(protein, 1),
            "carbs": round(carbs, 1),
            "fat": round(fat, 1),
            "fiber": round(fiber, 1),
            "sodium": int(sodium),
            "cooking_method": cooking_method or "cooked",
            "ingredients": ingredients or [],
            "hidden_ingredients": possible_hidden_ingredients or [],
            "estimated_hidden_fat_g": round(hidden_fat_g, 1),
            "estimated_hidden_calories": int(hidden_oil_kcal),
            "source": base_nutri.get("source") or "Resolver"
        }

nutrition_engine = NutritionEngine()
