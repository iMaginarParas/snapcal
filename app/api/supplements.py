from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.schemas.supplements import SupplementCreate, SupplementResponse
from app.repositories.db_repository import db_repository
from app.core.dependencies import get_current_user_id

router = APIRouter(prefix="/supplements", tags=["Supplements"])

@router.get("", response_model=List[SupplementResponse])
def get_supplements(user_id: str = Depends(get_current_user_id)):
    supplements = db_repository.get_supplements(user_id)
    formatted = []
    for s in supplements:
        # DB may return time as a datetime.time object
        time_val = s.get("time")
        if not isinstance(time_val, str) and time_val is not None:
            time_str = time_val.strftime("%H:%M")
        else:
            time_str = str(time_val)[:5] if time_val else "08:00"
        
        # Ensure created_at is serialized
        created_at_val = s.get("created_at")
        if not isinstance(created_at_val, str) and created_at_val is not None:
            created_at_str = created_at_val.isoformat()
        else:
            created_at_str = str(created_at_val) if created_at_val else None

        formatted.append(SupplementResponse(
            id=str(s.get("id")),
            user_id=str(s.get("user_id")),
            name=s.get("name"),
            dosage=s.get("dosage"),
            time=time_str,
            created_at=created_at_str
        ))
    return formatted

@router.post("", response_model=SupplementResponse, status_code=status.HTTP_201_CREATED)
def add_supplement(payload: SupplementCreate, user_id: str = Depends(get_current_user_id)):
    try:
        data = {
            "name": payload.name,
            "dosage": payload.dosage,
            "time": payload.time,
        }
        res = db_repository.add_supplement(user_id, data)
        
        time_val = res.get("time")
        if not isinstance(time_val, str) and time_val is not None:
            time_str = time_val.strftime("%H:%M")
        else:
            time_str = str(time_val)[:5] if time_val else "08:00"

        created_at_val = res.get("created_at")
        if not isinstance(created_at_val, str) and created_at_val is not None:
            created_at_str = created_at_val.isoformat()
        else:
            created_at_str = str(created_at_val) if created_at_val else None

        return SupplementResponse(
            id=str(res.get("id")),
            user_id=str(res.get("user_id")),
            name=res.get("name"),
            dosage=res.get("dosage"),
            time=time_str,
            created_at=created_at_str
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add supplement: {str(e)}")

@router.delete("/{supplement_id}")
def delete_supplement(supplement_id: str, user_id: str = Depends(get_current_user_id)):
    success = db_repository.delete_supplement(user_id, supplement_id)
    if not success:
        raise HTTPException(status_code=404, detail="Supplement not found or not owned by user")
    return {"success": True, "message": "Supplement deleted successfully"}
