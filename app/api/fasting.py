from fastapi import APIRouter, Depends
from app.schemas.fasting import FastingStartRequest, FastingStopRequest
from app.services.fasting.fasting_service import fasting_service
from app.core.dependencies import get_current_user_id

router = APIRouter(prefix="/fasting", tags=["Fasting Logs"])

@router.get("/active")
def get_active_fast(user_id: str = Depends(get_current_user_id)):
    return fasting_service.get_active_fast(user_id)

@router.post("/start")
def start_fast(payload: FastingStartRequest, user_id: str = Depends(get_current_user_id)):
    return fasting_service.start_fast(user_id, payload)

@router.post("/stop")
def stop_fast(payload: FastingStopRequest, user_id: str = Depends(get_current_user_id)):
    return fasting_service.stop_fast(user_id, payload)
