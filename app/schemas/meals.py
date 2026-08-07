from pydantic import BaseModel, model_validator
from typing import Optional, List, Any

class ManualMealLogRequest(BaseModel):
    name: str
    calories: int
    protein: Optional[float] = 0.0
    carbs: Optional[float] = 0.0
    fats: Optional[float] = 0.0   # frontend sends 'fats'
    fat: Optional[float] = 0.0    # backend DB column is 'fat'
    date: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def normalise_fat(cls, data: Any) -> Any:
        if isinstance(data, dict):
            fats_val = float(data.get("fats") or 0.0)
            fat_val = float(data.get("fat") or 0.0)
            data["fat"] = fat_val or fats_val
            data["fats"] = data["fat"]

            name = (data.get("name") or "").strip()
            desc = (data.get("description") or "").strip()
            if (not name or name.lower() in ["meal log", "analyzed meal", "unknown meal"]) and desc:
                data["name"] = desc.split(",")[0].capitalize()
        return data

class FoodItemSave(BaseModel):
    food_name: str
    weight_g: float = 100.0
    calories: int = 0
    protein: float = 0.0
    carbs: float = 0.0
    fat: float = 0.0
    fiber: float = 0.0
    confidence: float = 85.0
    cooking_method: Optional[str] = "cooked"
    ingredients: Optional[List[str]] = []
    hidden_ingredients: Optional[List[str]] = []
    serving: Optional[str] = "1 serving"

    @model_validator(mode="before")
    @classmethod
    def normalise_food_item(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("food_name"):
                data["food_name"] = data.get("name") or "Food Item"
            fats_val = float(data.get("fats") or 0.0)
            fat_val = float(data.get("fat") or 0.0)
            data["fat"] = fat_val or fats_val
            cal = data.get("calories") or data.get("total_calories") or 0
            data["calories"] = int(cal)
        return data

class MealSaveRequest(BaseModel):
    name: str = "Meal Log"
    meal_type: Optional[str] = "Lunch"
    total_weight: Optional[float] = 0.0
    total_calories: int = 0
    protein: float = 0.0
    carbs: float = 0.0
    fat: float = 0.0
    fiber: float = 0.0
    image_url: Optional[str] = None
    date: Optional[str] = None  # YYYY-MM-DD
    foods: List[FoodItemSave] = []

    @model_validator(mode="before")
    @classmethod
    def normalise_meal_save(cls, data: Any) -> Any:
        if isinstance(data, dict):
            fats_val = float(data.get("fats") or 0.0)
            fat_val = float(data.get("fat") or 0.0)
            data["fat"] = fat_val or fats_val
            cal = data.get("total_calories") or data.get("calories") or 0
            data["total_calories"] = int(cal)

            name = (data.get("name") or "").strip()
            foods = data.get("foods") or []
            if (not name or name.lower() in ["meal log", "analyzed meal", "unknown meal", "food log"]) and foods:
                first = foods[0]
                if isinstance(first, dict):
                    fn = first.get("food_name") or first.get("name")
                    if fn:
                        data["name"] = fn
        return data

class FoodCorrectionSave(BaseModel):
    original_name: str
    corrected_name: str
    corrected_weight: Optional[float] = None
    corrected_cooking_method: Optional[str] = None
    corrected_serving: Optional[str] = None

class MealTemplateSave(BaseModel):
    template_name: str
    foods: List[FoodItemSave]

class BarcodeRequest(BaseModel):
    barcode: str
