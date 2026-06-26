from fastapi import APIRouter, Depends
from app.schemas.groups import GroupCreateRequest
from app.services.groups.group_service import group_service
from app.core.dependencies import get_current_user_id

router = APIRouter(tags=["Groups and Challenges"])

@router.get("/groups")
def get_groups(user_id: str = Depends(get_current_user_id)):
    return group_service.get_groups(user_id)

@router.post("/groups")
def create_group(payload: GroupCreateRequest, user_id: str = Depends(get_current_user_id)):
    return group_service.create_group(user_id, payload)

@router.get("/challenges")
def get_challenges(user_id: str = Depends(get_current_user_id)):
    return group_service.get_challenges()

@router.post("/challenges/{id}/progress")
def update_challenge_progress(id: str, user_id: str = Depends(get_current_user_id)):
    return group_service.update_challenge_progress(user_id, id)
