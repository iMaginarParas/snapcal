from fastapi import APIRouter, Depends
from app.repositories.db_repository import db_repository
from app.core.dependencies import get_current_user_id

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("")
def get_notifications(user_id: str = Depends(get_current_user_id)):
    notifs = db_repository.get_notifications(user_id)
    return {"success": True, "data": notifs}

@router.post("/{id}/read")
def mark_notification_read(id: str, user_id: str = Depends(get_current_user_id)):
    db_repository.mark_notification_read(user_id, id)
    return {"success": True}
