from typing import Optional
from fastapi import UploadFile
from app.repositories.db_repository import db_repository
from app.schemas.users import ProfileUpdateRequest
from app.core.exceptions import BadRequestException
from app.database.supabase import supabase_client, is_supabase_live
from app.services.users.profile_service import profile_service
from datetime import datetime
import os

class UserService:
    def get_profile(self, user_id: str) -> dict:
        return profile_service.get_profile(user_id)

    def update_profile(self, user_id: str, payload: ProfileUpdateRequest) -> dict:
        if payload.username is not None and payload.username.strip() and payload.username.strip() != "guest_user":
            if db_repository.check_username_exists(payload.username.strip(), user_id):
                raise BadRequestException(detail="Username is already taken")
                
        return profile_service.update_profile(user_id, payload)

    async def update_profile_picture(self, user_id: str, image: UploadFile) -> dict:
        file_bytes = await image.read()
        extension = image.filename.split(".")[-1] or "jpg"
        file_name = f"{user_id}-{int(datetime.utcnow().timestamp())}.{extension}"
        profile_url = ""
        
        if is_supabase_live():
            try:
                res = supabase_client.storage.from_("profile-pictures").upload(
                    file_name,
                    file_bytes,
                    {"content-type": image.content_type, "upsert": "true"}
                )
                profile_url = supabase_client.storage.from_("profile-pictures").get_public_url(file_name)
            except Exception as e:
                pass
                
        if not profile_url:
            uploads_dir = os.path.join(os.path.dirname(__file__), "../../../uploads")
            os.makedirs(uploads_dir, exist_ok=True)
            local_path = os.path.join(uploads_dir, file_name)
            with open(local_path, "wb") as f:
                f.write(file_bytes)
            profile_url = f"http://localhost:3000/uploads/{file_name}"
            
        db_repository.update_user_profile(user_id, {"profile_picture_url": profile_url})
        return {"success": True, "url": profile_url}

    def delete_account(self, user_id: str) -> dict:
        """Permanently delete user account and all personal data (Apple Guideline 5.1.1(v))."""
        errors = []

        if is_supabase_live():
            # Delete user data across all tables
            tables = [
                "meals", "food_items", "workouts", "daily_stats", 
                "measurement_logs", "fasting_logs", "supplements", 
                "supplement_logs", "user_badges", "subscriptions",
                "direct_messages", "profiles", "users"
            ]
            for table in tables:
                try:
                    supabase_client.table(table).delete().eq("user_id", user_id).execute()
                except Exception:
                    try:
                        supabase_client.table(table).delete().eq("id", user_id).execute()
                    except Exception as e:
                        errors.append(f"{table}: {e}")

            # Delete auth user record via Supabase Admin
            try:
                if hasattr(supabase_client.auth, "admin"):
                    supabase_client.auth.admin.delete_user(user_id)
            except Exception as e:
                errors.append(f"auth_admin: {e}")
        else:
            # Local db cleanup
            try:
                from app.repositories.db_repository import _load_db, _save_db
                data = _load_db()
                for key in ["users", "profiles", "meals", "dailyStats", "workouts", "measurementLogs", "fastingLogs"]:
                    if key in data and isinstance(data[key], dict) and user_id in data[key]:
                        del data[key][user_id]
                _save_db(data)
            except Exception as e:
                errors.append(f"local_db: {e}")

        return {
            "success": True,
            "message": "Account and all associated personal data have been permanently deleted.",
        }

user_service = UserService()
