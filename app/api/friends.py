from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from app.repositories.db_repository import db_repository
from app.core.dependencies import get_current_user_id
from pydantic import BaseModel

router = APIRouter(prefix="/friends", tags=["Friends"])

class AddFriendRequest(BaseModel):
    email: str

@router.get("")
def get_friends(user_id: str = Depends(get_current_user_id)):
    friends = db_repository.get_friends(user_id)
    return {"success": True, "data": friends}

@router.get("/suggestions")
def get_friend_suggestions(user_id: str = Depends(get_current_user_id)):
    suggestions = db_repository.get_friend_suggestions(user_id)
    return {"success": True, "data": suggestions}

@router.post("/add")
def add_friend(payload: AddFriendRequest, user_id: str = Depends(get_current_user_id)):
    try:
        res = db_repository.add_friend(user_id, payload.email)
        return {"success": True, "data": res}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to add friend: {str(e)}")
