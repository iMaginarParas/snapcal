from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class DietFoodItem(BaseModel):
    name: str
    portion: str = "1 serving"
    calories: int = 0
    protein: float = 0.0
    carbs: float = 0.0
    fats: float = 0.0
    notes: Optional[str] = None

class MealSlot(BaseModel):
    id: Optional[str] = None
    slot_name: str  # e.g. "Breakfast", "Mid-Morning", "Lunch", "Evening Snack", "Dinner", "Pre-Workout"
    time: Optional[str] = "08:00"
    target_calories: int = 0
    target_protein: float = 0.0
    target_carbs: float = 0.0
    target_fats: float = 0.0
    instructions: Optional[str] = None
    foods: List[DietFoodItem] = []

class DietPlanCreate(BaseModel):
    title: str
    description: Optional[str] = None
    coach_id: Optional[str] = "coach_default"
    client_id: Optional[str] = None  # None if template, or specific client ID
    target_date: Optional[str] = None  # e.g. "2026-09-22" or "all_days"
    is_template: bool = False
    dietary_tags: List[str] = []  # e.g. ["High Protein", "Gluten Free"]
    total_calories: int = 2000
    protein_g: float = 140.0
    carbs_g: float = 200.0
    fats_g: float = 65.0
    water_liters: float = 3.0
    supplements: List[str] = []
    instructions: Optional[str] = None
    meals: List[MealSlot] = []

class SendDailyDietPlanRequest(BaseModel):
    client_id: str
    client_name: Optional[str] = None
    target_date: str  # YYYY-MM-DD
    title: str = "Daily Nutritional Protocol"
    description: Optional[str] = None
    total_calories: int = 2000
    protein_g: float = 140.0
    carbs_g: float = 200.0
    fats_g: float = 65.0
    water_liters: float = 3.0
    supplements: List[str] = []
    instructions: Optional[str] = None
    meals: List[MealSlot] = []
    notify_client: bool = True

class CoachMealFeedbackRequest(BaseModel):
    client_id: str
    meal_id: Optional[str] = None
    date: str
    feedback_text: str
    rating: Optional[str] = "great"  # "great", "on_track", "needs_adjustment"

class AIDietPlanGenerateRequest(BaseModel):
    client_name: Optional[str] = "Client"
    goal: str = "Fat Loss"  # "Fat Loss", "Muscle Gain", "Maintenance", "Endurance"
    dietary_preference: str = "High Protein"  # "High Protein", "Vegetarian", "Keto", "Balanced", "Vegan"
    target_calories: int = 2000
    allergies: Optional[List[str]] = []
    meals_per_day: int = 4
