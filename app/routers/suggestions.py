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
    meal_list = ", ".join([f"{m.food_name} ({m.calories} kcal)" for m in meals])

    step_record = db.query(Step)\
        .filter(Step.user_id == current_user.id, Step.date == today)\
        .first()
    total_steps = step_record.step_count if step_record else 0
    
    water_record = db.query(func.sum(Water.amount_ml))\
        .filter(Water.user_id == current_user.id, Water.date == today)\
        .scalar() or 0

    medical = db.query(MedicalHistory).filter(MedicalHistory.user_id == current_user.id).first()
    medical_info = (
        f"Diabetic: {medical.is_diabetic if medical else False}, "
        f"Hypertension: {medical.has_hypertension if medical else False}, "
        f"Medications: {medical.medications if medical else 'None'}"
    )

    measurement = db.query(Measurement).filter(Measurement.user_id == current_user.id).order_by(Measurement.created_at.desc()).first()
    measurement_info = f"Latest Weight: {measurement.weight if measurement else 'Unknown'} kg, Waist: {measurement.waist if measurement else 'Unknown'} cm"

    # 3. Get Current Time
    from datetime import datetime
    current_time = datetime.now().strftime("%I:%M %p")

    # 4. Construct Routine-Aware Prompt
    prompt = (
        f"You are the Preferred AI Health Coach. Analyze the user's routine TODAY and provide proactive advice.\n\n"
        f"CURRENT TIME: {current_time}\n"
        f"USER PROFILE:\n"
        f"- Name: {current_user.full_name}\n"
        f"- Medical: {medical_info}\n"
        f"- {measurement_info}\n\n"
        f"TODAY'S ROUTINE SO FAR:\n"
        f"- Meals: {meal_list if meal_list else 'No meals logged yet'}\n"
        f"- Total Calories: {total_calories:.0f} kcal\n"
        f"- Total Steps: {total_steps} steps\n"
        f"- Water Intake: {water_record} ml\n\n"
        f"TASK:\n"
        f"Provide TWO proactive, concise suggestions based on the CURRENT TIME and their ROUTINE.\n"
        f"- If it's late and steps are low, suggest a quick walk.\n"
        f"- If they've eaten heavy, suggest a light next meal.\n"
        f"- If they are dehydrated, remind them of water.\n"
        f"- ALWAYS consider their medical conditions (e.g., if diabetic, watch sugar).\n\n"
        f"FORMAT: Return exactly two paragraphs. Start first with 'FOOD:' and second with 'EXERCISE:'. Be professional and supportive."
    )

    # 5. Call AI Service
    try:
        response_text = await ai_coach_service.get_response(prompt, history=[], user_context="You are a proactive health suggestion agent.")
        
        # Simple parsing
        food_sugg = "Log your meals to get personalized food advice for your routine!"
        exe_sugg = "Keep moving! Every step counts towards your daily goal."
        
        if "FOOD:" in response_text and "EXERCISE:" in response_text:
            parts = response_text.split("EXERCISE:")
            food_sugg = parts[0].replace("FOOD:", "").strip()
            exe_sugg = parts[1].strip()
        else:
            food_sugg = response_text

        return {
            "food_suggestion": food_sugg,
            "exercise_suggestion": exe_sugg,
            "date": today.isoformat(),
            "time_generated": current_time
        }
    except Exception as e:
        print(f"Suggestion Error: {e}")
        return {
            "food_suggestion": "Stay balanced and focus on hydration for now.",
            "exercise_suggestion": "A quick 5-minute stretch would be great right now.",
            "date": today.isoformat()
        }
