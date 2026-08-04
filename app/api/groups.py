from fastapi import APIRouter, Depends
from app.schemas.groups import GroupCreateRequest, GroupMessageRequest
from app.services.groups.group_service import group_service
from app.core.dependencies import get_current_user_id

router = APIRouter(tags=["Groups and Challenges"])

@router.get("/groups")
def get_groups(user_id: str = Depends(get_current_user_id)):
    return group_service.get_groups(user_id)

@router.post("/groups")
def create_group(payload: GroupCreateRequest, user_id: str = Depends(get_current_user_id)):
    return group_service.create_group(user_id, payload)

@router.post("/groups/{id}/join")
def join_group(id: str, user_id: str = Depends(get_current_user_id)):
    return group_service.join_group(user_id, id)

@router.post("/groups/{id}/leave")
def leave_group(id: str, user_id: str = Depends(get_current_user_id)):
    return group_service.leave_group(user_id, id)

@router.get("/groups/{id}/messages")
def get_group_messages(id: str, user_id: str = Depends(get_current_user_id)):
    return group_service.get_group_messages(id)

@router.post("/groups/{id}/messages")
def send_group_message(id: str, payload: GroupMessageRequest, user_id: str = Depends(get_current_user_id)):
    return group_service.send_group_message(user_id, id, payload.message)

@router.get("/challenges")
def get_challenges(user_id: str = Depends(get_current_user_id)):
    return group_service.get_challenges()

@router.get("/challenges/user")
def get_user_challenges(user_id: str = Depends(get_current_user_id)):
    return group_service.get_user_challenges(user_id)

@router.post("/challenges/{id}/join")
def join_challenge(id: str, user_id: str = Depends(get_current_user_id)):
    return group_service.join_challenge(user_id, id)

@router.post("/challenges/{id}/progress")
def update_challenge_progress(id: str, user_id: str = Depends(get_current_user_id)):
    return group_service.update_challenge_progress(user_id, id)

@router.get("/leaderboard")
def get_leaderboard(user_id: str = Depends(get_current_user_id)):
    return group_service.get_leaderboard(user_id)

@router.post("/groups/{id}/invite")
def invite_to_group(id: str, invitee_id: str, user_id: str = Depends(get_current_user_id)):
    return group_service.invite_to_group(id, user_id, invitee_id)

@router.get("/groups/invites")
def get_group_invites(user_id: str = Depends(get_current_user_id)):
    return group_service.get_group_invites(user_id)

@router.post("/groups/{id}/accept-invite")
def accept_group_invite(id: str, user_id: str = Depends(get_current_user_id)):
    return group_service.accept_group_invite(user_id, id)

