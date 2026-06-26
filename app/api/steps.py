from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.schemas.steps import StepsSyncRequest
from app.services.health.steps_service import steps_service
from app.core.dependencies import get_current_user_id
from datetime import datetime

router = APIRouter(tags=["Steps"])

@router.post("/steps/sync")
def sync_steps_endpoint(payload: StepsSyncRequest, user_id: str = Depends(get_current_user_id)):
    return steps_service.sync_steps(user_id, payload)

@router.get("/steps/daily")
def get_daily_steps_endpoint(
    date: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user_id)
):
    date_str = date or datetime.utcnow().strftime("%Y-%m-%d")
    return steps_service.get_daily_steps(user_id, date_str)

@router.get("/steps/history")
def get_steps_history_endpoint(
    days: int = Query(7, ge=1, le=90),
    user_id: str = Depends(get_current_user_id)
):
    return steps_service.get_steps_history(user_id, days)
