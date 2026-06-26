from app.schemas.auth import SignupRequest, LoginRequest, GoogleLoginRequest
from app.repositories.db_repository import db_repository
from app.core.exceptions import BadRequestException
from app.database.supabase import supabase_client, is_supabase_live
import uuid

class AuthService:
    def signup(self, payload: SignupRequest) -> dict:
        email = payload.email
        password = payload.password
        
        if not is_supabase_live():
            # Mock signup creation
            mock_id = f"user-{uuid.uuid4()}"
            db_repository.get_user_profile(mock_id)
            db_repository.create_user_profile({"id": mock_id, "email": email, "name": email.split("@")[0]})
            return {"success": True, "token": f"mock-user-{mock_id}", "data": {"user": {"email": email, "id": mock_id}}}
        
        try:
            res = supabase_client.auth.sign_up({"email": email, "password": password})
            if res.user:
                return {"success": True, "data": {"user": {"email": res.user.email, "id": res.user.id}}}
            raise BadRequestException(detail="Signup failed")
        except Exception as e:
            raise BadRequestException(detail=str(e))

    def login(self, payload: LoginRequest) -> dict:
        email = payload.email
        password = payload.password
        
        if not is_supabase_live():
            # Basic mock login simulation
            mock_id = f"user-{uuid.uuid4()}"
            db_repository.create_user_profile({"id": mock_id, "email": email, "name": email.split("@")[0]})
            return {"success": True, "token": f"mock-user-{mock_id}", "data": {"token": f"mock-user-{mock_id}"}}
            
        try:
            res = supabase_client.auth.sign_in_with_password({"email": email, "password": password})
            if res.session:
                return {"success": True, "token": res.session.access_token, "data": {"token": res.session.access_token}}
            raise BadRequestException(detail="Invalid credentials")
        except Exception as e:
            raise BadRequestException(detail=str(e))

    def google_login(self, payload: GoogleLoginRequest) -> dict:
        token = f"mock-google-{payload.idToken[:10]}"
        if not is_supabase_live():
            mock_id = f"user-{payload.idToken[:10]}"
            db_repository.create_user_profile({
                "id": mock_id,
                "email": payload.email or f"{mock_id}@gmail.com",
                "name": payload.displayName or "Google User",
                "profile_picture_url": payload.photoUrl
            })
            return {"success": True, "token": f"mock-user-{mock_id}", "data": {"token": f"mock-user-{mock_id}"}}
        
        try:
            res = supabase_client.auth.sign_in_with_id_token({
                "provider": "google",
                "token": payload.idToken
            })
            if res.session:
                return {"success": True, "token": res.session.access_token, "data": {"token": res.session.access_token}}
            raise BadRequestException(detail="Google authentication failed")
        except Exception as e:
            raise BadRequestException(detail=str(e))

auth_service = AuthService()
