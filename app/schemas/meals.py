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
            # Merge fats -> fat so service layer always reads .fat
            fats_val = float(data.get("fats") or 0.0)
            fat_val = float(data.get("fat") or 0.0)
            data["fat"] = fat_val or fats_val
            data["fats"] = data["fat"]
        return data

class FoodItemSave(BaseModel):
    food_name: str
    weight_g: float
    calories: int
    protein: float
    carbs: float
    fat: float
    fiber: float
    confidence: float
    cooking_method: Optional[str] = "cooked"
    ingredients: Optional[List[str]] = []
    hidden_ingredients: Optional[List[str]] = []
    serving: Optional[str] = "1 serving"

class MealSaveRequest(BaseModel):
    name: str
    meal_type: Optional[str] = "Lunch"
    total_weight: Optional[float] = 0.0
    total_calories: int
    protein: float = 0.0
    carbs: float = 0.0
    fat: float = 0.0
    fiber: float = 0.0
    image_url: Optional[str] = None
    date: Optional[str] = None  # YYYY-MM-DD
    foods: List[FoodItemSave] = []

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
