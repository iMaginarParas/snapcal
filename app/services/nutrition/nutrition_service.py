from typing import List, Optional
from app.services.nutrition.nutrition_engine import nutrition_engine

def calculate_nutrition(
    food_name: str, 
    weight_g: float, 
    cooking_method: str = "cooked", 
    ingredients: list = None
) -> dict:
    """
    Legacy wrapper for nutrition calculations, delegating to the new Nutrition Engine.
    Ensures backward compatibility.
    """
    res = nutrition_engine.calculate_nutrition(
        food_name=food_name,
        weight_g=weight_g,
        cooking_method=cooking_method,
        ingredients=ingredients
    )
    
    # Map key names to match original legacy formats if different
    return {
        "food_name": res["food_name"],
        "matched_database_item": res.get("food_name"),
        "weight_g": res["weight_g"],
        "calories": res["calories"],
        "protein": res["protein"],
        "carbs": res["carbs"],
        "fat": res["fat"],
        "fiber": res["fiber"],
        "sodium_mg": res["sodium"],
        "cooking_method": res["cooking_method"],
        "estimated_hidden_fat_g": res["estimated_hidden_fat_g"],
        "estimated_hidden_calories": res["estimated_hidden_calories"]
    }
