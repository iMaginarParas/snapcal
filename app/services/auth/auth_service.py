from app.schemas.auth import SignupRequest, LoginRequest, GoogleLoginRequest
from app.core.exceptions import BadRequestException
from app.database.supabase import supabase_client

class AuthService:
    def signup(self, payload: SignupRequest) -> dict:
        email = payload.email
        password = payload.password
        
        try:
            res = supabase_client.auth.sign_up({"email": email, "password": password})
            if res.user:
                token = res.session.access_token if (hasattr(res, 'session') and res.session) else None
                return {
                    "success": True,
                    "token": token,
                    "data": {
                        "token": token,
                        "user": {"email": res.user.email, "id": res.user.id}
                    }
                }
            raise BadRequestException(detail="Signup failed")
        except Exception as e:
            raise BadRequestException(detail=str(e))

    def login(self, payload: LoginRequest) -> dict:
        email = payload.email
        password = payload.password
        
        try:
            res = supabase_client.auth.sign_in_with_password({"email": email, "password": password})
            if res.session:
                return {"success": True, "token": res.session.access_token, "data": {"token": res.session.access_token}}
            raise BadRequestException(detail="Invalid credentials")
        except Exception as e:
            raise BadRequestException(detail=str(e))

    def google_login(self, payload: GoogleLoginRequest) -> dict:
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
