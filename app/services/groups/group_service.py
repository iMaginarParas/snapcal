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

    def join_group(self, user_id: str, group_id: str) -> dict:
        db_repository.join_group(user_id, group_id)
        return {"success": True}

    def leave_group(self, user_id: str, group_id: str) -> dict:
        db_repository.leave_group(user_id, group_id)
        return {"success": True}

    def get_group_messages(self, group_id: str) -> dict:
        messages = db_repository.get_group_messages(group_id)
        return {"success": True, "data": messages}

    def send_group_message(self, user_id: str, group_id: str, message: str) -> dict:
        msg = db_repository.send_group_message(user_id, group_id, message)
        return {"success": True, "data": msg}

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

    def get_user_challenges(self, user_id: str) -> dict:
        challs = db_repository.get_user_challenges(user_id)
        return {"success": True, "data": challs}

    def join_challenge(self, user_id: str, challenge_id: str) -> dict:
        res = db_repository.join_challenge(user_id, challenge_id)
        return {"success": True, "data": res}

    def get_leaderboard(self, user_id: str) -> dict:
        data = db_repository.get_leaderboard(user_id)
        return {"success": True, "data": data}

    def invite_to_group(self, group_id: str, inviter_id: str, invitee_id: str) -> dict:
        res = db_repository.invite_to_group(group_id, inviter_id, invitee_id)
        return {"success": True, "data": res}

    def get_group_invites(self, user_id: str) -> dict:
        invites = db_repository.get_group_invites(user_id)
        return {"success": True, "data": invites}

    def accept_group_invite(self, user_id: str, group_id: str) -> dict:
        db_repository.accept_group_invite(user_id, group_id)
        return {"success": True}

group_service = GroupService()

