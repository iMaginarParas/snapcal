from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.repositories.db_repository import db_repository
from app.core.dependencies import get_current_user_id

router = APIRouter(prefix="/user/badges", tags=["Badges"])

class AwardBadgeRequest(BaseModel):
    badge_id: str

@router.get("")
def get_user_badges(user_id: str = Depends(get_current_user_id)):
    badges = db_repository.get_user_badges(user_id)
    return {"success": True, "data": badges}

@router.post("")
def award_badge(payload: AwardBadgeRequest, user_id: str = Depends(get_current_user_id)):
    res = db_repository.award_badge(user_id, payload.badge_id)
    return {"success": True, "data": res}
