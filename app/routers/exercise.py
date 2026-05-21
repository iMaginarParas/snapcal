from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date
from .. import database
from ..models.exercise import Exercise
from ..models.user import User
from ..schemas import schemas
from .auth import get_current_user

router = APIRouter(prefix="/exercises", tags=["exercises"])

@router.post("/", response_model=schemas.ExerciseOut)
def log_exercise(
    exercise_data: schemas.ExerciseCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    new_exercise = Exercise(
        user_id=current_user.id,
        **exercise_data.model_dump()
    )
    db.add(new_exercise)
    db.commit()
    db.refresh(new_exercise)
    return new_exercise

@router.get("/", response_model=List[schemas.ExerciseOut])
def get_exercises(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user),
    start_date: date = None,
    end_date: date = None
):
    query = db.query(Exercise).filter(Exercise.user_id == current_user.id)
    if start_date:
        query = query.filter(Exercise.date >= start_date)
    if end_date:
        query = query.filter(Exercise.date <= end_date)
    
    return query.order_by(Exercise.date.desc()).all()

@router.get("/today", response_model=List[schemas.ExerciseOut])
def get_today_exercises(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    today = date.today()
    return db.query(Exercise).filter(Exercise.user_id == current_user.id, Exercise.date == today).all()
