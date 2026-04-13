from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date as date_type
from .. import database
from ..models.water import Water
from ..models.user import User
from ..schemas import schemas
from .auth import get_current_user

router = APIRouter(prefix="/water", tags=["water"])

@router.get("/today", response_model=schemas.WaterOut)
def get_today_water(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    today = date_type.today()
    water = db.query(Water).filter(Water.user_id == current_user.id, Water.date == today).first()
    if not water:
        # Create a 0 entry for today
        water = Water(user_id=current_user.id, date=today, amount_ml=0)
        db.add(water)
        db.commit()
        db.refresh(water)
    return water

@router.post("/", response_model=schemas.WaterOut)
def update_water(
    data: schemas.WaterCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    water = db.query(Water).filter(Water.user_id == current_user.id, Water.date == data.date).first()
    if water:
        water.amount_ml = data.amount_ml
    else:
        water = Water(user_id=current_user.id, date=data.date, amount_ml=data.amount_ml)
        db.add(water)
    
    db.commit()
    db.refresh(water)
    return water
