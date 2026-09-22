from fastapi import APIRouter, Depends, Query, HTTPException, Header
from typing import Optional, List, Dict, Any
from app.schemas.diet_plans import (
    DietPlanCreate,
    SendDailyDietPlanRequest,
    CoachMealFeedbackRequest,
    AIDietPlanGenerateRequest
)
from app.services.diet.diet_service import diet_service
from app.core.dependencies import get_current_user_id

router = APIRouter(tags=["Diet Plans & Nutrition"])

# --- Diet Plans & Templates (Coach & Client Access) ---
@router.get("/diet-plans")
def list_diet_plans(
    coach_id: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None),
    is_template: Optional[bool] = Query(None)
):
    plans = diet_service.list_plans(coach_id=coach_id, client_id=client_id, is_template=is_template)
    return {"success": True, "count": len(plans), "data": plans}

@router.post("/diet-plans")
def create_diet_plan(payload: DietPlanCreate):
    new_plan = diet_service.create_plan(payload)
    return {"success": True, "data": new_plan}

@router.get("/diet-plans/{plan_id}")
def get_diet_plan(plan_id: str):
    plan = diet_service.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Diet plan not found")
    return {"success": True, "data": plan}

@router.put("/diet-plans/{plan_id}")
def update_diet_plan(plan_id: str, updates: Dict[str, Any]):
    updated = diet_service.update_plan(plan_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Diet plan not found")
    return {"success": True, "data": updated}

@router.delete("/diet-plans/{plan_id}")
def delete_diet_plan(plan_id: str):
    ok = diet_service.delete_plan(plan_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Diet plan not found")
    return {"success": True, "message": "Diet plan deleted"}

# --- Trainer Daily Diet Plan Dispatcher ---
@router.post("/diet-plans/send-daily")
def send_daily_diet_plan(payload: SendDailyDietPlanRequest):
    """
    Coach/trainer dispatches today's customized daily diet plan directly to a client.
    The client immediately sees it on SabTrack.
    """
    return diet_service.send_daily_diet_plan(payload)

# --- AI Diet Plan Generator ---
@router.post("/diet-plans/generate-ai")
def generate_ai_diet_plan(payload: AIDietPlanGenerateRequest):
    res = diet_service.generate_ai_diet_plan(payload)
    return {"success": True, "data": res}

# --- SabTrack Client Endpoints ---
@router.get("/client/diet-plan/today")
def get_client_today_diet_plan(
    client_id: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    """
    Called by SabTrack client mobile app or web portal to load today's assigned diet plan,
    macros, hydration target, meal timing, and coach instructions.
    """
    target_id = client_id
    if not target_id and authorization:
        try:
            target_id = get_current_user_id(authorization)
        except Exception:
            target_id = "client_default"
    if not target_id:
        target_id = "client_default"

    return diet_service.get_client_today_plan(target_id, date)
