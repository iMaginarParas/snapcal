from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.repositories.db_repository import db_repository
from app.core.dependencies import get_current_user_id

router = APIRouter(tags=["Direct Messages"])

class DMRequest(BaseModel):
    message: str

@router.get("/dm/{friend_id}")
def get_dm_messages(friend_id: str, user_id: str = Depends(get_current_user_id)):
    """Get direct messages between current user and a friend."""
    messages = db_repository.get_dm_messages(user_id, friend_id)
    return {"success": True, "data": messages}

@router.post("/dm/{friend_id}")
def send_dm(friend_id: str, payload: DMRequest, user_id: str = Depends(get_current_user_id)):
    """Send a direct message to a friend."""
    result = db_repository.send_dm(user_id, friend_id, payload.message)
    return {"success": True, "data": result}

@router.post("/challenges/invite/{friend_id}")
def invite_friend_to_challenge(friend_id: str, user_id: str = Depends(get_current_user_id)):
    """Invite a friend to join the current active challenge."""
    result = db_repository.invite_friend_to_challenge(user_id, friend_id)
    return {"success": True, "data": result}
