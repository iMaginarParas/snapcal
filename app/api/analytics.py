from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.services.analytics.analytics_service import analytics_service
from app.core.dependencies import get_current_user_id

router = APIRouter(prefix="/insights", tags=["Insights"])

@router.get("")
def get_insights(user_id: str = Depends(get_current_user_id)):
    return analytics_service.get_insights(user_id)

@router.get("/daily")
def get_daily_report(date: Optional[str] = Query(None), user_id: str = Depends(get_current_user_id)):
    return analytics_service.get_daily_report(user_id, date)
