from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from .. import database
from ..models.step import Step
from ..models.user import User
from ..schemas import schemas
from .auth import get_current_user
from ..services.analytics_service import track_event
from ..services.cache_service import get_cache, set_cache, invalidate_cache

router = APIRouter(prefix="/steps", tags=["steps"])

@router.post("/", response_model=schemas.StepOut)
def update_steps(
    step_data: schemas.StepCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    db_step = db.query(Step).filter(
        Step.user_id == current_user.id,
        Step.date == step_data.date
    ).first()
    
    if db_step:
        db_step.steps = step_data.step_count
        db_step.distance = step_data.distance
        db_step.calories_burned = step_data.calories_burned
    else:
        db_step = Step(
            user_id=current_user.id,
            date=step_data.date,
            steps=step_data.step_count,
            distance=step_data.distance,
            calories_burned=step_data.calories_burned
        )
        db.add(db_step)
    
    db.commit()
    db.refresh(db_step)

    # Invalidate caches
    invalidate_cache(f"steps_today:{current_user.id}")
    invalidate_cache(f"stats_dashboard:{current_user.id}")

    # Track steps recorded event
    track_event(
        user_id=current_user.id,
        event_name="steps_recorded",
        properties={
            "step_count": db_step.steps,
            "calories_burned": db_step.calories_burned
        }
    )

    return db_step

@router.get("/today", response_model=schemas.StepOut)
def get_today_steps(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    # Try cache
    cache_key = f"steps_today:{current_user.id}"
    cached_steps = get_cache(cache_key)
    if cached_steps:
        return cached_steps

    today = date.today()
    db_step = db.query(Step).filter(
        Step.user_id == current_user.id,
        Step.date == today
    ).first()
    
    if not db_step:
        result = {
            "id": 0,
            "user_id": current_user.id,
            "date": today.isoformat(), 
            "step_count": 0,
            "distance": 0.0,
            "calories_burned": 0.0
        }
        set_cache(cache_key, result)
        return result
    
    set_cache(cache_key, schemas.StepOut.model_validate(db_step).model_dump(mode="json"))
    return db_step
