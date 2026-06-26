from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.schemas.health import DailyStatsUpdateRequest, MeasurementLogRequest
from app.services.health.health_service import health_service
from app.core.dependencies import get_current_user_id

router = APIRouter(tags=["Health"])

@router.get("/daily-stats")
def get_daily_stats(date: Optional[str] = Query(None), user_id: str = Depends(get_current_user_id)):
    return health_service.get_daily_stats(user_id, date)

@router.post("/daily-stats")
def update_daily_stats(payload: DailyStatsUpdateRequest, user_id: str = Depends(get_current_user_id)):
    return health_service.update_daily_stats(user_id, payload)

@router.get("/measurements")
def get_measurements(metric_type: Optional[str] = Query(None), user_id: str = Depends(get_current_user_id)):
    return health_service.get_measurements(user_id, metric_type)

@router.post("/measurements")
def log_measurement(payload: MeasurementLogRequest, user_id: str = Depends(get_current_user_id)):
    return health_service.log_measurement(user_id, payload)

@router.delete("/measurements/{id}")
def delete_measurement(id: str, user_id: str = Depends(get_current_user_id)):
    return health_service.delete_measurement(user_id, id)
