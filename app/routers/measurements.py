from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from .. import database
from ..models.measurement import Measurement
from ..models.user import User
from ..schemas.measurement import MeasurementCreate, MeasurementResponse
from .auth import get_current_user

router = APIRouter(prefix="/measurements", tags=["measurements"])

@router.post("/", response_model=MeasurementResponse)
def create_measurement(
    measurement: MeasurementCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    db_measurement = Measurement(
        **measurement.model_dump(),
        user_id=current_user.id,
        created_at=datetime.utcnow()
    )
    db.add(db_measurement)
    db.commit()
    db.refresh(db_measurement)
    return db_measurement

@router.get("/", response_model=List[MeasurementResponse])
def get_measurements(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100)
):
    measurements = db.query(Measurement)\
        .filter(Measurement.user_id == current_user.id)\
        .order_by(Measurement.created_at.desc())\
        .limit(limit).all()
    # Reverse to have chronological order for charts
    return measurements[::-1]
