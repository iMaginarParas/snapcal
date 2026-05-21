from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date as date_type, timedelta
from typing import List
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

@router.get("/weekly")
def get_weekly_water(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user),
):
    start = date_type.today() - timedelta(days=days - 1)
    records = (
        db.query(Water)
        .filter(Water.user_id == current_user.id, Water.date >= start)
        .order_by(Water.date.asc())
        .all()
    )
    by_date = {r.date.isoformat(): r.amount_ml for r in records}
    result = []
    for i in range(days):
        d = start + timedelta(days=i)
        key = d.isoformat()
        result.append({"date": key, "amount_ml": by_date.get(key, 0)})
    return result
