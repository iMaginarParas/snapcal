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

    # 3. Generate AI Response using Gemini
    from ..services.ai_service import ai_coach_service
    response_text = await ai_coach_service.get_response(msg.content, history=history)

    # 4. Parse for Commands (Automated Corrections)
    if "[UPDATE_MEAL:" in response_text:
        import json
        import re
        try:
            match = re.search(r"\[UPDATE_MEAL:(.*?)\]", response_text)
            if match:
                update_data = json.loads(match.group(1))
                meal_id = msg.meal_id
                
                # If no meal_id provided, find the latest one
                if not meal_id:
                    latest_meal = db.query(Meal).filter(Meal.user_id == current_user.id).order_by(Meal.created_at.desc()).first()
                    if latest_meal:
                        meal_id = latest_meal.id
                
                if meal_id:
                    from ..models.meal import Meal as MealModel
                    db.query(MealModel).filter(MealModel.id == meal_id).update(update_data)
                    db.commit()
                    # Clean up the output text for the user
                    response_text = re.sub(r"\[UPDATE_MEAL:.*?\]", "✅ I've updated your log as requested.", response_text)
        except Exception as e:
            print(f"Correction Parsing Error: {e}")

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
