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
def send_message(
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

    # 2. Generate AI Response (Mocking LLM for now)
    ai_responses = [
        "That sounds like a healthy choice! Based on your goal, you have about 1200 calories left for today.",
        "Pro tip: Pairing this with some healthy fats like avocado will keep you full longer.",
        "I've updated your log. Would you like to see how this affects your macro balance?",
        "If you're feeling hungry, try drinking a glass of water first. Sometimes thirst feels like hunger!",
        "Excellent! This meal is high in protein, which is great for your muscle recovery."
    ]
    
    response_text = random.choice(ai_responses)
    
    # Optional logic: if the user asks to "correct" or "add", we would trigger meal updates here.
    if "correct" in msg.content.lower() or "wrong" in msg.content.lower():
         response_text = "I understand. I'll flag this for a closer look. What should the correct calories be?"

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
