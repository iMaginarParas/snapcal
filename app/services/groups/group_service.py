from app.repositories.db_repository import db_repository
from app.schemas.groups import GroupCreateRequest
from datetime import datetime

class GroupService:
    def get_groups(self, user_id: str) -> dict:
        groups = db_repository.get_groups(user_id)
        return {"success": True, "data": groups}

    def create_group(self, user_id: str, payload: GroupCreateRequest) -> dict:
        db_payload = {
            "name": payload.name,
            "description": payload.description,
            "is_public": payload.is_public,
            "created_by": user_id,
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        res = db_repository.create_group(db_payload)
        return {"success": True, "data": res}

    def get_challenges(self) -> dict:
        challs = db_repository.get_challenges()
        return {"success": True, "data": challs}

    def update_challenge_progress(self, user_id: str, id: str) -> dict:
        chk = db_repository.get_user_challenge(user_id, id)
        if chk:
            prog = chk["progress"] + 1
            completed = prog >= 5
            res = db_repository.update_user_challenge(chk["id"], {"progress": prog, "completed": completed})
        else:
            ins_payload = {
                "user_id": user_id, 
                "challenge_id": id, 
                "progress": 1, 
                "completed": False, 
                "created_at": datetime.utcnow().isoformat() + "Z"
            }
            res = db_repository.create_user_challenge(ins_payload)
        return {"success": True, "data": res}

group_service = GroupService()
