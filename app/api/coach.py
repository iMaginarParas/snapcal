from fastapi import APIRouter, Depends, Query, HTTPException, Body, Header
from typing import Optional, List, Dict, Any
from app.schemas.diet_plans import CoachMealFeedbackRequest
from app.services.diet.diet_service import diet_service
from app.repositories.coach_repository import coach_repo
from app.core.dependencies import get_current_user_id

router = APIRouter(prefix="/coach", tags=["Coach Operations & Telemetry"])


def _extract_coach_id(authorization: Optional[str] = Header(None), coach_id: Optional[str] = Query(None)) -> str:
    if coach_id:
        return coach_id
    if authorization and authorization.startswith("Bearer "):
        try:
            uid = get_current_user_id(authorization)
            if uid:
                return uid
        except Exception:
            pass
    return "coach_default"


# --- 1. Clients ---
@router.get("/clients")
def get_coach_clients(
    authorization: Optional[str] = Header(None),
    coach_id: Optional[str] = Query(None)
):
    cid = _extract_coach_id(authorization, coach_id)
    clients = coach_repo.get_clients(cid)

    # Attach live telemetry
    enhanced = []
    for c in clients:
        telemetry = diet_service.get_client_diet_telemetry(c["id"])
        prescribed = telemetry.get("prescribed") or {}
        actual = telemetry.get("actual") or {}
        enhanced.append({
            **c,
            "active_plan_title": prescribed.get("title") or "High Protein Protocol",
            "prescribed_calories": prescribed.get("calories") or c.get("target_cals", 2000),
            "actual_calories": actual.get("calories") or 0,
            "adherence_percentage": telemetry.get("adherence_percentage") or 88.0,
            "adherence_status": telemetry.get("status") or "On Track",
            "meals_logged_today": actual.get("meal_count") or 0
        })

    return {"success": True, "count": len(enhanced), "data": enhanced}


@router.post("/clients")
def create_or_update_client(
    payload: Dict[str, Any] = Body(...),
    authorization: Optional[str] = Header(None)
):
    cid = _extract_coach_id(authorization, payload.get("coach_id"))
    payload["coach_id"] = cid
    saved = coach_repo.save_client(payload)
    return {"success": True, "data": saved}


@router.delete("/clients/{client_id}")
def delete_client(
    client_id: str,
    authorization: Optional[str] = Header(None)
):
    cid = _extract_coach_id(authorization)
    res = coach_repo.delete_client(client_id, cid)
    return {"success": res}


# --- 2. Sessions & Calendar ---
@router.get("/sessions")
def get_coach_sessions(
    authorization: Optional[str] = Header(None),
    coach_id: Optional[str] = Query(None)
):
    cid = _extract_coach_id(authorization, coach_id)
    sessions = coach_repo.get_sessions(cid)
    return {"success": True, "count": len(sessions), "data": sessions}


@router.post("/sessions")
def save_coach_session(
    payload: Dict[str, Any] = Body(...),
    authorization: Optional[str] = Header(None)
):
    cid = _extract_coach_id(authorization, payload.get("coach_id"))
    payload["coach_id"] = cid
    saved = coach_repo.save_session(payload)
    return {"success": True, "data": saved}


@router.delete("/sessions/{session_id}")
def delete_coach_session(
    session_id: str,
    authorization: Optional[str] = Header(None)
):
    cid = _extract_coach_id(authorization)
    res = coach_repo.delete_session(session_id, cid)
    return {"success": res}


# --- 3. Workouts & Programs ---
@router.get("/workouts")
def get_coach_workouts(
    authorization: Optional[str] = Header(None),
    coach_id: Optional[str] = Query(None)
):
    cid = _extract_coach_id(authorization, coach_id)
    workouts = coach_repo.get_workouts(cid)
    return {"success": True, "count": len(workouts), "data": workouts}


@router.post("/workouts")
def save_coach_workout(
    payload: Dict[str, Any] = Body(...),
    authorization: Optional[str] = Header(None)
):
    cid = _extract_coach_id(authorization, payload.get("coach_id"))
    payload["coach_id"] = cid
    saved = coach_repo.save_workout(payload)
    return {"success": True, "data": saved}


@router.delete("/workouts/{workout_id}")
def delete_coach_workout(
    workout_id: str,
    authorization: Optional[str] = Header(None)
):
    cid = _extract_coach_id(authorization)
    res = coach_repo.delete_workout(workout_id, cid)
    return {"success": res}


@router.get("/programs")
def get_coach_programs(
    authorization: Optional[str] = Header(None),
    coach_id: Optional[str] = Query(None)
):
    cid = _extract_coach_id(authorization, coach_id)
    programs = coach_repo.get_programs(cid)
    return {"success": True, "count": len(programs), "data": programs}


@router.post("/programs")
def save_coach_program(
    payload: Dict[str, Any] = Body(...),
    authorization: Optional[str] = Header(None)
):
    cid = _extract_coach_id(authorization, payload.get("coach_id"))
    payload["coach_id"] = cid
    saved = coach_repo.save_program(payload)
    return {"success": True, "data": saved}


# --- 4. Invoices & Payments ---
@router.get("/payments")
def get_coach_payments(
    authorization: Optional[str] = Header(None),
    coach_id: Optional[str] = Query(None)
):
    cid = _extract_coach_id(authorization, coach_id)
    payments = coach_repo.get_payments(cid)
    return {"success": True, "count": len(payments), "data": payments}


@router.post("/payments")
def save_coach_payment(
    payload: Dict[str, Any] = Body(...),
    authorization: Optional[str] = Header(None)
):
    cid = _extract_coach_id(authorization, payload.get("coach_id"))
    payload["coach_id"] = cid
    saved = coach_repo.save_payment(payload)
    return {"success": True, "data": saved}


# --- 5. CRM Leads ---
@router.get("/leads")
def get_coach_leads(
    authorization: Optional[str] = Header(None),
    coach_id: Optional[str] = Query(None)
):
    cid = _extract_coach_id(authorization, coach_id)
    leads = coach_repo.get_leads(cid)
    return {"success": True, "count": len(leads), "data": leads}


@router.post("/leads")
def save_coach_lead(
    payload: Dict[str, Any] = Body(...),
    authorization: Optional[str] = Header(None)
):
    cid = _extract_coach_id(authorization, payload.get("coach_id"))
    payload["coach_id"] = cid
    saved = coach_repo.save_lead(payload)
    return {"success": True, "data": saved}


@router.delete("/leads/{lead_id}")
def delete_coach_lead(
    lead_id: str,
    authorization: Optional[str] = Header(None)
):
    cid = _extract_coach_id(authorization)
    res = coach_repo.delete_lead(lead_id, cid)
    return {"success": res}


# --- 6. Community Groups & Challenges ---
@router.get("/groups")
def get_coach_groups(
    authorization: Optional[str] = Header(None),
    coach_id: Optional[str] = Query(None)
):
    cid = _extract_coach_id(authorization, coach_id)
    groups = coach_repo.get_groups(cid)
    return {"success": True, "count": len(groups), "data": groups}


@router.post("/groups")
def save_coach_group(
    payload: Dict[str, Any] = Body(...),
    authorization: Optional[str] = Header(None)
):
    cid = _extract_coach_id(authorization, payload.get("coach_id"))
    payload["coach_id"] = cid
    saved = coach_repo.save_group(payload)
    return {"success": True, "data": saved}


@router.get("/challenges")
def get_coach_challenges(
    authorization: Optional[str] = Header(None),
    coach_id: Optional[str] = Query(None)
):
    cid = _extract_coach_id(authorization, coach_id)
    challenges = coach_repo.get_challenges(cid)
    return {"success": True, "count": len(challenges), "data": challenges}


@router.post("/challenges")
def save_coach_challenge(
    payload: Dict[str, Any] = Body(...),
    authorization: Optional[str] = Header(None)
):
    cid = _extract_coach_id(authorization, payload.get("coach_id"))
    payload["coach_id"] = cid
    saved = coach_repo.save_challenge(payload)
    return {"success": True, "data": saved}


# --- 7. Availability, Reports & Automations ---
@router.get("/availability")
def get_coach_availability(
    authorization: Optional[str] = Header(None),
    coach_id: Optional[str] = Query(None)
):
    cid = _extract_coach_id(authorization, coach_id)
    avail = coach_repo.get_availability(cid)
    return {"success": True, "data": avail}


@router.put("/availability")
def save_coach_availability(
    payload: List[Dict[str, Any]] = Body(...),
    authorization: Optional[str] = Header(None)
):
    cid = _extract_coach_id(authorization)
    saved = coach_repo.save_availability(cid, payload)
    return {"success": True, "data": saved}


@router.get("/reports")
def get_coach_reports(
    authorization: Optional[str] = Header(None),
    coach_id: Optional[str] = Query(None)
):
    cid = _extract_coach_id(authorization, coach_id)
    reports = coach_repo.get_reports(cid)
    return {"success": True, "count": len(reports), "data": reports}


@router.post("/reports")
def save_coach_report(
    payload: Dict[str, Any] = Body(...),
    authorization: Optional[str] = Header(None)
):
    cid = _extract_coach_id(authorization, payload.get("coach_id"))
    payload["coach_id"] = cid
    saved = coach_repo.save_report(payload)
    return {"success": True, "data": saved}


@router.get("/automations")
def get_coach_automations(
    authorization: Optional[str] = Header(None),
    coach_id: Optional[str] = Query(None)
):
    cid = _extract_coach_id(authorization, coach_id)
    automations = coach_repo.get_automations(cid)
    return {"success": True, "count": len(automations), "data": automations}


@router.post("/automations")
def save_coach_automation(
    payload: Dict[str, Any] = Body(...),
    authorization: Optional[str] = Header(None)
):
    cid = _extract_coach_id(authorization, payload.get("coach_id"))
    payload["coach_id"] = cid
    saved = coach_repo.save_automation(payload)
    return {"success": True, "data": saved}


@router.delete("/automations/{automation_id}")
def delete_coach_automation(
    automation_id: str,
    authorization: Optional[str] = Header(None)
):
    cid = _extract_coach_id(authorization)
    res = coach_repo.delete_automation(automation_id, cid)
    return {"success": res}


# --- 8. Telemetry & Feedback (Existing) ---
@router.get("/client/{client_id}/telemetry")
def get_client_telemetry(client_id: str, date: Optional[str] = Query(None)):
    """
    Real-time telemetric inspection for coaches:
    Shows prescribed diet plan vs actual meals logged in SabTrack with macro breakdown and adherence.
    """
    telemetry = diet_service.get_client_diet_telemetry(client_id, date)
    return {"success": True, "data": telemetry}


@router.post("/client/{client_id}/feedback")
def send_coach_meal_feedback(client_id: str, payload: CoachMealFeedbackRequest):
    """
    Coach provides direct written feedback or adjustments to the client's daily meal log.
    """
    payload.client_id = client_id
    res = diet_service.save_coach_feedback(payload)
    return {"success": True, "message": "Feedback sent to client", "data": res}
