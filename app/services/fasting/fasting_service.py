from typing import Optional
from app.repositories.db_repository import db_repository
from app.schemas.fasting import FastingStartRequest, FastingStopRequest
from app.core.exceptions import NotFoundException

class FastingService:
    def get_active_fast(self, user_id: str) -> dict:
        fast = db_repository.get_active_fast(user_id)
        return {"success": True, "data": fast}

    def start_fast(self, user_id: str, payload: FastingStartRequest) -> dict:
        active = db_repository.get_active_fast(user_id)
        if active:
            return {"success": True, "data": active}
            
        fast = db_repository.start_fast(user_id, payload.protocol)
        return {"success": True, "data": fast}

    def stop_fast(self, user_id: str, payload: FastingStopRequest) -> dict:
        fast = db_repository.stop_fast(user_id, payload.id)
        if fast:
            return {"success": True, "data": fast}
        raise NotFoundException(detail="Active fast log not found")

fasting_service = FastingService()
