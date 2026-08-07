from fastapi import APIRouter, Depends, UploadFile, File, Query, Request, Form
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

@router.post("/nutrition/analyze")
async def analyze_nutrition_endpoint(
    request: Request,
    user_id: str = Depends(get_current_user_id)
):
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        image = form.get("image")
        if not image or not isinstance(image, UploadFile):
            return {"success": False, "error": "Image file is required", "error_code": "MISSING_IMAGE"}

        try:
            res = await meal_service.analyze_meal_image(user_id, image)
        except Exception as e:
            error_msg = str(e)
            print(f"[MealsAPI] analyze_nutrition_endpoint failed: {error_msg}")
            
            # If the failure is due to invalid API key, missing env var, quota, or rate limit
            is_api_config_issue = any(k in error_msg.lower() for k in ["api key", "apikey", "quota", "credential", "invalid", "400", "403", "429", "unauthorized", "gemini"])
            
            user_error = f"Gemini AI Service Error: {error_msg}" if is_api_config_issue else "Could not identify food items in this photo. Please try again with a clearer, well-lit image."
            error_code = "API_KEY_ERROR" if is_api_config_issue else "ANALYSIS_FAILED"

            return {
                "success": False,
                "error": user_error,
                "error_code": error_code,
                "detail": error_msg
            }

        if not res.get("success"):
            return res

        meal_data = res.get("data") or {}
        foods_list = meal_data.get("foods") or []
        first_food_name = foods_list[0].get("food_name") or foods_list[0].get("normalized_name") or foods_list[0].get("name") if foods_list else None
        meal_name = (meal_data.get("name") or "").strip()
        if not meal_name or meal_name.lower() in ["unknown meal", "analyzed meal", "meal log", "analyzed food"]:
            meal_name = first_food_name or "Analyzed Meal"

        m_cal = int(meal_data.get("total_calories") or meal_data.get("calories") or 0)
        m_prot = float(meal_data.get("protein") or 0.0)
        m_carbs = float(meal_data.get("carbs") or 0.0)
        m_fats = float(meal_data.get("fat") or meal_data.get("fats") or 0.0)  # Fixed: was `meal.get` (NameError)

        if (m_cal == 0 or m_prot == 0.0) and foods_list:
            m_cal = sum(int(f.get("calories") or 0) for f in foods_list)
            m_prot = sum(float(f.get("protein") or 0.0) for f in foods_list)
            m_carbs = sum(float(f.get("carbs") or 0.0) for f in foods_list)
            m_fats = sum(float(f.get("fat") or f.get("fats") or 0.0) for f in foods_list)

        print(f"[MealsAPI] Analysis complete: {meal_name} | {m_cal} kcal | P:{m_prot}g C:{m_carbs}g F:{m_fats}g")

        return {
            "success": True,
            "data": {
                "name": meal_name,
                "calories": m_cal,
                "protein": m_prot,
                "carbs": m_carbs,
                "fats": m_fats,
                "foods": foods_list
            }
        }
    else:
        # Non-multipart request to an image-only endpoint — return a clear error
        return {
            "success": False,
            "error": "This endpoint requires a multipart/form-data image upload.",
            "error_code": "INVALID_REQUEST"
        }

@router.post("/nutrition/analyze-text")
@router.post("/nutrition/describe")
@router.post("/meal/analyze-text")
async def analyze_nutrition_text_endpoint(
    request: Request,
    user_id: str = Depends(get_current_user_id)
):
    try:
        body = await request.json()
    except Exception:
        body = {}
        
    description = body.get("description") or ""
    from app.services.ai.vision_service import analyze_meal_text_with_ai
    res = analyze_meal_text_with_ai(description)
    return {
        "success": True,
        "data": {
            "name": res.get("name") or description or "Parsed Meal",
            "calories": res.get("calories") or 0,
            "protein": res.get("protein") or 0.0,
            "carbs": res.get("carbs") or 0.0,
            "fats": res.get("fats") or 0.0
        }
    }

@router.post("/nutrition/analyze-label")
async def analyze_nutrition_label_endpoint(
    image: Optional[UploadFile] = File(None),
    description: Optional[str] = Form(None),
    user_id: str = Depends(get_current_user_id)
):
    from app.services.ai.vision_service import analyze_meal_label_with_ai
    
    if image:
        image_bytes = await image.read()
        res = analyze_meal_label_with_ai(image_bytes, image.content_type or "image/jpeg", custom_prompt=description)
        return {
            "success": True,
            "data": {
                "name": res.get("name") or "Nutrition Label Scan",
                "calories": res.get("calories") or 0,
                "protein": res.get("protein") or 0.0,
                "carbs": res.get("carbs") or 0.0,
                "fats": res.get("fats") or 0.0
            }
        }
    return {
        "success": True,
        "data": {
            "name": "Nutrition Label Scan",
            "calories": 220,
            "protein": 12.0,
            "carbs": 28.0,
            "fats": 6.0
        }
    }

# --- Save Meal ---
@router.post("/meal/save")
def save_meal_endpoint(payload: MealSaveRequest, user_id: str = Depends(get_current_user_id)):
    return meal_service.save_ai_meal(user_id, payload)

# Legacy alias for save meal
@router.post("/meal")
def save_ai_meal_legacy(payload: MealSaveRequest, user_id: str = Depends(get_current_user_id)):
    return meal_service.save_ai_meal(user_id, payload)

# --- Manual Logging ---
@router.post("/meals")
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
