from fastapi import APIRouter, Depends, Body
from app.repositories.db_repository import db_repository
from app.core.dependencies import get_current_user_id

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("")
def get_notifications(user_id: str = Depends(get_current_user_id)):
    notifs = db_repository.get_notifications(user_id)
    return {"success": True, "data": notifs}

@router.get("/unread-count")
def get_unread_count(user_id: str = Depends(get_current_user_id)):
    """Returns the unread notification count — used by the app for badge updates."""
    notifs = db_repository.get_notifications(user_id)
    count = sum(1 for n in notifs if not n.get("is_read", False))
    return {"success": True, "unread_count": count}

@router.post("/{id}/read")
def mark_notification_read(id: str, user_id: str = Depends(get_current_user_id)):
    db_repository.mark_notification_read(user_id, id)
    return {"success": True}

@router.post("/fcm-token")
def register_fcm_token(
    token: str = Body(..., embed=True),
    user_id: str = Depends(get_current_user_id)
):
    """
    Stores the device's FCM push token on the user record.
    The app should call this after Firebase initialises and whenever
    the token refreshes (onTokenRefresh).
    """
    try:
        from app.database.supabase import supabase_client
        if supabase_client:
            supabase_client.from_("users").update({"fcm_token": token}).eq("id", user_id).execute()
        return {"success": True, "message": "FCM token registered"}
    except Exception as e:
        return {"success": False, "error": str(e)}
