from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List
from .. import database
from ..models.friend import Friend
from ..models.user import User
from ..models.step import Step
from ..schemas import schemas
from .auth import get_current_user
from datetime import date

router = APIRouter(prefix="/friends", tags=["friends"])

@router.post("/request/{friend_id}")
def send_friend_request(
    friend_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    if friend_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot friend yourself")
    
    # Check if request already exists
    existing = db.query(Friend).filter(
        or_(
            and_(Friend.user_id == current_user.id, Friend.friend_id == friend_id),
            and_(Friend.user_id == friend_id, Friend.friend_id == current_user.id)
        )
    ).first()
    
    if existing:
        return {"message": "Friend request already exists", "status": existing.status}

    new_request = Friend(user_id=current_user.id, friend_id=friend_id, status="pending")
    db.add(new_request)
    db.commit()
    return {"message": "Friend request sent"}

@router.get("/", response_model=List[dict])
def get_friends(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    # Get accepted friendships
    friendships = db.query(Friend).filter(
        and_(
            or_(Friend.user_id == current_user.id, Friend.friend_id == current_user.id),
            Friend.status == "accepted"
        )
    ).all()
    
    friends_list = []
    today = date.today()
    
    for f in friendships:
        friend_id = f.friend_id if f.user_id == current_user.id else f.user_id
        friend_user = db.query(User).filter(User.id == friend_id).first()
        
        # Get friend's today steps
        step_record = db.query(Step).filter(Step.user_id == friend_id, Step.date == today).first()
        steps = step_record.step_count if step_record else 0
        
        friends_list.append({
            "id": friend_user.id,
            "full_name": friend_user.full_name,
            "steps_today": steps,
            "status": f.status
        })
    
    return friends_list

@router.post("/accept/{sender_id}")
def accept_friend_request(
    sender_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    request = db.query(Friend).filter(
        Friend.user_id == sender_id, 
        Friend.friend_id == current_user.id,
        Friend.status == "pending"
    ).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Friend request not found")
    
    request.status = "accepted"
    db.commit()
    return {"message": "Friend request accepted"}

@router.get("/requests/pending", response_model=List[dict])
def get_pending_requests(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user),
):
    pending = db.query(Friend).filter(
        Friend.friend_id == current_user.id,
        Friend.status == "pending",
    ).all()
    result = []
    for req in pending:
        sender = db.query(User).filter(User.id == req.user_id).first()
        if sender:
            result.append({
                "request_id": req.id,
                "id": sender.id,
                "full_name": sender.full_name or sender.email,
                "status": req.status,
            })
    return result

@router.get("/search", response_model=List[dict])
def search_users(
    query: str,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    users = db.query(User).filter(
        User.full_name.ilike(f"%{query}%"),
        User.id != current_user.id
    ).limit(10).all()
    
    return [{"id": u.id, "full_name": u.full_name} for u in users]
