from pydantic import BaseModel
from typing import Optional, List

class ManualMealLogRequest(BaseModel):
    name: str
    calories: int
    protein: Optional[float] = 0.0
    carbs: Optional[float] = 0.0
    fats: Optional[float] = 0.0
    date: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None

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
    protein: float
    carbs: float
    fat: float
    fiber: float
    image_url: Optional[str] = None
    date: Optional[str] = None  # YYYY-MM-DD
    foods: List[FoodItemSave]

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
