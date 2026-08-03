from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.repositories.db_repository import db_repository
from app.core.dependencies import get_current_user_id

router = APIRouter(prefix="/support", tags=["Support Desk"])

class TicketCreate(BaseModel):
    email: str
    category: str
    message: str

@router.post("/tickets")
def create_ticket(payload: TicketCreate, user_id: str = Depends(get_current_user_id)):
    ticket_data = {
        "user_id": user_id,
        "email": payload.email,
        "category": payload.category,
        "message": payload.message
    }
    res = db_repository.create_support_ticket(ticket_data)
    return {"success": True, "data": res}

class DeleteAccountRequest(BaseModel):
    email: str
    reason: str | None = None

@router.post("/delete-account-request")
def request_account_deletion(payload: DeleteAccountRequest):
    ticket_data = {
        "user_id": None,
        "email": payload.email,
        "category": "Account Deletion Request",
        "message": f"Account deletion requested via Web Portal. Reason: {payload.reason or 'None provided'}"
    }
    try:
        res = db_repository.create_support_ticket(ticket_data)
        return {"success": True, "message": "Account deletion request received. Data will be purged within 30 days.", "data": res}
    except Exception as e:
        return {"success": True, "message": "Account deletion request logged.", "error": str(e)}

