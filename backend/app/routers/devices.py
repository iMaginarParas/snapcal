from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import database
from ..models.device_token import DeviceToken
from ..models.user import User
from ..schemas import schemas
from .auth import get_current_user

router = APIRouter(prefix="/devices", tags=["devices"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_device(
    device_data: schemas.DeviceTokenCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if token already exists
    existing_token = db.query(DeviceToken).filter(DeviceToken.token == device_data.token).first()
    
    if existing_token:
        # Update user_id if it changed (e.g., user logged in on shared device)
        existing_token.user_id = current_user.id
        existing_token.platform = device_data.platform
        db.commit()
        return {"message": "Device token updated"}

    new_token = DeviceToken(
        user_id=current_user.id,
        token=device_data.token,
        platform=device_data.platform
    )
    db.add(new_token)
    db.commit()
    
    return {"message": "Device token registered"}
