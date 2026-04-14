from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import database
from ..models.chat import ChatMessage
from ..models.user import User
from ..schemas import schemas
from .auth import get_current_user
import random

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/", response_model=schemas.ChatMessageOut)
async def send_message(
    msg: schemas.ChatMessageCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Save User Message
    user_msg = ChatMessage(
        user_id=current_user.id,
        meal_id=msg.meal_id,
        role="user",
        content=msg.content
    )
    db.add(user_msg)
    db.commit()

    # 2. Get Recent Chat History for Context
    history_records = db.query(ChatMessage)\
        .filter(ChatMessage.user_id == current_user.id)\
        .order_by(ChatMessage.created_at.desc())\
        .limit(10).all()
    
    # Reverse to get chronological order
    history = [{"role": m.role, "content": m.content} for m in reversed(history_records[:-1])] if len(history_records) > 1 else []

    # 3. Fetch Today's Progress Stats for AI Context
    from datetime import date
    from ..models.meal import Meal
    from ..models.step import Step
    from ..models.water import Water
    from sqlalchemy import func

    today = date.today()
    
    # Get Today's Calories
    total_calories = db.query(func.sum(Meal.calories))\
        .filter(Meal.user_id == current_user.id, func.date(Meal.created_at) == today)\
        .scalar() or 0
    
    # Get Today's Steps
    step_record = db.query(Step)\
        .filter(Step.user_id == current_user.id, Step.date == today)\
        .first()
    total_steps = step_record.step_count if step_record else 0
    
    # Get Today's Water
    total_water = db.query(func.sum(Water.amount_ml))\
        .filter(Water.user_id == current_user.id, Water.date == today)\
        .scalar() or 0

    # 3. Construct Personal User Context for AI
    user_context = (
        f"User Name: {current_user.full_name or 'User'}\n"
        f"User Stats: {current_user.weight or 'Unknown'}kg, {current_user.height or 'Unknown'}cm, {current_user.age or 'Unknown'} years old.\n"
        f"Pro Member: {'Yes' if current_user.is_pro else 'No'}\n"
        f"TODAY'S PROGRESS ({today}):\n"
        f"- Calories Consumed: {total_calories:.0f} kcal\n"
        f"- Steps Taken: {total_steps} steps\n"
        f"- Water Intake: {total_water} ml\n"
    )

    # 4. Generate AI Response using Gemini
    from ..services.ai_service import ai_coach_service
    response_text = await ai_coach_service.get_response(msg.content, history=history, user_context=user_context)

    # 4. Parse for Commands (Automated Corrections & Updates)
    if any(cmd in response_text for cmd in ["[UPDATE_MEAL:", "[UPDATE_STEPS:", "[UPDATE_WATER:"]):
        import json
        import re
        try:
            # Handle Meal Updates
            meal_match = re.search(r"\[UPDATE_MEAL:(.*?)\]", response_text)
            if meal_match:
                update_data = json.loads(meal_match.group(1))
                meal_id = msg.meal_id
                if not meal_id:
                    latest_meal = db.query(Meal).filter(Meal.user_id == current_user.id).order_by(Meal.created_at.desc()).first()
                    if latest_meal:
                        meal_id = latest_meal.id
                if meal_id:
                    from ..models.meal import Meal as MealModel
                    db.query(MealModel).filter(MealModel.id == meal_id).update(update_data)
                    db.commit()
                    response_text = re.sub(r"\[UPDATE_MEAL:.*?\]", "✅ Meal log updated.", response_text)

            # Handle Step Updates
            step_match = re.search(r"\[UPDATE_STEPS:(.*?)\]", response_text)
            if step_match:
                update_data = json.loads(step_match.group(1))
                if step_record:
                    for key, value in update_data.items():
                        setattr(step_record, key, value)
                else:
                    new_step = Step(user_id=current_user.id, date=today, **update_data)
                    db.add(new_step)
                db.commit()
                response_text = re.sub(r"\[UPDATE_STEPS:.*?\]", "✅ Steps updated.", response_text)

            # Handle Water Updates
            water_match = re.search(r"\[UPDATE_WATER:(.*?)\]", response_text)
            if water_match:
                update_data = json.loads(water_match.group(1))
                # Usually we just add water, but let's allow setting it if AI says so
                new_water = Water(user_id=current_user.id, date=today, amount_ml=update_data.get("amount_ml", 0))
                db.add(new_water)
                db.commit()
                response_text = re.sub(r"\[UPDATE_WATER:.*?\]", "✅ Water logged.", response_text)

        except Exception as e:
            print(f"Command Parsing Error: {e}")

    # 5. Save AI Response
    ai_msg = ChatMessage(
        user_id=current_user.id,
        meal_id=msg.meal_id,
        role="assistant",
        content=response_text
    )
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)
    
    return ai_msg

@router.get("/", response_model=List[schemas.ChatMessageOut])
def get_history(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(ChatMessage).filter(ChatMessage.user_id == current_user.id).order_by(ChatMessage.created_at.asc()).all()
