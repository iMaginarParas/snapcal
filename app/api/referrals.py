from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.repositories.db_repository import db_repository
from app.core.dependencies import get_current_user_id

router = APIRouter(prefix="/referrals", tags=["Referrals"])

class ClaimReferralRequest(BaseModel):
    code: str

@router.get("")
def get_referral_info(user_id: str = Depends(get_current_user_id)):
    try:
        return db_repository.get_referral_info(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch referral info: {str(e)}")

@router.post("/claim")
def claim_referral_code(payload: ClaimReferralRequest, user_id: str = Depends(get_current_user_id)):
    try:
        success = db_repository.claim_referral_code(user_id, payload.code)
        return {"success": success, "message": "Referral code claimed successfully!"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to claim referral code: {str(e)}")
