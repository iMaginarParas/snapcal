from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import database
from ..models.medical_history import MedicalHistory
from ..models.user import User
from ..schemas.medical_history import MedicalHistoryCreate, MedicalHistoryUpdate, MedicalHistoryResponse
from .auth import get_current_user

router = APIRouter(prefix="/medical-history", tags=["medical-history"])

@router.get("/", response_model=MedicalHistoryResponse)
def get_medical_history(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    history = db.query(MedicalHistory).filter(MedicalHistory.user_id == current_user.id).first()
    if not history:
        # Return default empty history instead of 404 to simplify frontend
        return MedicalHistory(user_id=current_user.id)
    return history

@router.post("/", response_model=MedicalHistoryResponse)
def update_medical_history(
    history_data: MedicalHistoryUpdate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    history = db.query(MedicalHistory).filter(MedicalHistory.user_id == current_user.id).first()
    
    if history:
        for key, value in history_data.model_dump().items():
            setattr(history, key, value)
    else:
        history = MedicalHistory(**history_data.model_dump(), user_id=current_user.id)
        db.add(history)
    
    db.commit()
    db.refresh(history)
    return history
