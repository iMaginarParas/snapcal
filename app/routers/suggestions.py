from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from sqlalchemy import func
from .. import database
from ..models.user import User
from ..models.meal import Meal
from ..models.step import Step
from ..models.water import Water
from ..models.medical_history import MedicalHistory
from ..models.measurement import Measurement
from ..services.ai_service import ai_coach_service
from .auth import get_current_user

router = APIRouter(prefix="/suggestions", tags=["suggestions"])

@router.get("/daily")
async def get_daily_suggestions(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    today = date.today()
    
    # 1. Fetch Today's Data
    total_calories = db.query(func.sum(Meal.calories))\
        .filter(Meal.user_id == current_user.id, func.date(Meal.created_at) == today)\
        .scalar() or 0
    
    meals = db.query(Meal).filter(Meal.user_id == current_user.id, func.date(Meal.created_at) == today).all()
    meal_list = ", ".join([m.food_name for m in meals])

    step_record = db.query(Step)\
        .filter(Step.user_id == current_user.id, Step.date == today)\
        .first()
    total_steps = step_record.step_count if step_record else 0
    
    medical = db.query(MedicalHistory).filter(MedicalHistory.user_id == current_user.id).first()
    medical_info = (
        f"Diabetic: {medical.is_diabetic if medical else False}, "
        f"Hypertension: {medical.has_hypertension if medical else False}, "
        f"Medications: {medical.medications if medical else 'None'}"
    )

    measurement = db.query(Measurement).filter(Measurement.user_id == current_user.id).order_by(Measurement.created_at.desc()).first()
    measurement_info = f"Waist: {measurement.waist if measurement else 'Unknown'} cm"

    # 2. Construct Prompt
    prompt = (
        f"Analyze this user's day so far and provide TWO highly personalized, concise suggestions (one for FOOD, one for EXERCISE).\n\n"
        f"CONTEXT:\n"
        f"- Name: {current_user.full_name}\n"
        f"- Medical: {medical_info}\n"
        f"- Today's Meals: {meal_list if meal_list else 'No meals logged yet'}\n"
        f"- Today's Calories: {total_calories:.0f} kcal\n"
        f"- Today's Steps: {total_steps} steps\n"
        f"- Measurements: {measurement_info}\n\n"
        f"FORMAT: Return exactly two paragraphs. Start first with 'FOOD:' and second with 'EXERCISE:'. Be professional, encouraging, and medically safe."
    )

    # 3. Call AI Service
    try:
        response_text = await ai_coach_service.get_response(prompt, history=[], user_context="You are a health suggestion agent.")
        
        # Simple parsing
        food_sugg = "Log some meals to get food suggestions!"
        exe_sugg = "Keep moving to reach your goals!"
        
        if "FOOD:" in response_text and "EXERCISE:" in response_text:
            parts = response_text.split("EXERCISE:")
            food_sugg = parts[0].replace("FOOD:", "").strip()
            exe_sugg = parts[1].strip()
        else:
            food_sugg = response_text

        return {
            "food_suggestion": food_sugg,
            "exercise_suggestion": exe_sugg,
            "date": today.isoformat()
        }
    except Exception as e:
        print(f"Suggestion Error: {e}")
        return {
            "food_suggestion": "Stay hydrated and focus on protein today.",
            "exercise_suggestion": "Try a 10-minute brisk walk to boost your metabolism.",
            "date": today.isoformat()
        }
