from fastapi import APIRouter, Depends, UploadFile, File, Query
from typing import Optional
from app.schemas.meals import MealSaveRequest, ManualMealLogRequest, MealTemplateSave, BarcodeRequest
from app.services.meals.meal_service import meal_service
from app.core.dependencies import get_current_user_id
from datetime import datetime

router = APIRouter(tags=["Meals"])

# --- AI Meal Recognition ---
@router.post("/meal/analyze")
async def analyze_meal_endpoint(image: UploadFile = File(...), user_id: str = Depends(get_current_user_id)):
    return await meal_service.analyze_meal_image(user_id, image)

# --- Save Meal ---
@router.post("/meal/save")
def save_meal_endpoint(payload: MealSaveRequest, user_id: str = Depends(get_current_user_id)):
    return meal_service.save_ai_meal(user_id, payload)

# Legacy alias for save meal
@router.post("/meal")
def save_ai_meal_legacy(payload: MealSaveRequest, user_id: str = Depends(get_current_user_id)):
    return meal_service.save_ai_meal(user_id, payload)

# --- Manual Logging ---
@router.post("/meal/manual")
def log_manual_meal(payload: ManualMealLogRequest, user_id: str = Depends(get_current_user_id)):
    return meal_service.log_manual_meal(user_id, payload)

# --- Meal History ---
@router.get("/meal/history")
def get_meal_history_endpoint(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1),
    user_id: str = Depends(get_current_user_id)
):
    return meal_service.get_meal_history(user_id, page, limit)

# Legacy alias for get meals
@router.get("/meals")
def get_meals_legacy(date: Optional[str] = Query(None), user_id: str = Depends(get_current_user_id)):
    if date:
        return meal_service.get_daily_nutrition(user_id, date)
    date_today = datetime.utcnow().strftime("%Y-%m-%d")
    return meal_service.get_daily_nutrition(user_id, date_today)

# --- Nutrition Summaries ---
@router.get("/nutrition/daily")
def get_daily_nutrition_endpoint(
    date: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user_id)
):
    date_str = date or datetime.utcnow().strftime("%Y-%m-%d")
    return meal_service.get_daily_nutrition(user_id, date_str)

@router.get("/nutrition/weekly")
def get_weekly_nutrition_endpoint(user_id: str = Depends(get_current_user_id)):
    return meal_service.get_weekly_nutrition(user_id)

# --- Foods Search & Lists ---
@router.get("/foods/search")
def search_foods_endpoint(
    q: str = Query("", min_length=1),
    limit: int = Query(15, ge=1),
    user_id: str = Depends(get_current_user_id)
):
    return meal_service.search_foods(q, limit)

@router.get("/foods/recent")
def get_recent_foods_endpoint(
    limit: int = Query(15, ge=1),
    user_id: str = Depends(get_current_user_id)
):
    return meal_service.get_recents(user_id, limit)

@router.get("/foods/favorites")
def get_favorite_foods_endpoint(user_id: str = Depends(get_current_user_id)):
    return meal_service.get_favorites(user_id)

@router.post("/foods/favorites")
def add_favorite_food_endpoint(payload: dict, user_id: str = Depends(get_current_user_id)):
    # Payload has food details
    return meal_service.add_favorite(user_id, payload)

@router.delete("/foods/favorites/{food_name}")
def delete_favorite_food_endpoint(food_name: str, user_id: str = Depends(get_current_user_id)):
    return meal_service.remove_favorite(user_id, food_name)

# --- Barcode Scanner ---
@router.post("/foods/barcode")
def scan_barcode_endpoint(payload: BarcodeRequest, user_id: str = Depends(get_current_user_id)):
    return meal_service.scan_barcode(payload.barcode)

# Legacy alias for barcode scan
@router.post("/nutrition/barcode")
def scan_barcode_legacy(payload: BarcodeRequest, user_id: str = Depends(get_current_user_id)):
    return meal_service.scan_barcode(payload.barcode)

# --- Meal Templates ---
@router.post("/meal/template")
def create_meal_template_endpoint(payload: MealTemplateSave, user_id: str = Depends(get_current_user_id)):
    return meal_service.create_template(user_id, payload)

@router.get("/meal/templates")
def get_meal_templates_endpoint(user_id: str = Depends(get_current_user_id)):
    return meal_service.get_templates(user_id)
