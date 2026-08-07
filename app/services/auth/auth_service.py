from app.schemas.auth import SignupRequest, LoginRequest, GoogleLoginRequest
from app.core.exceptions import BadRequestException
from app.database.supabase import supabase_client

class AuthService:
    def signup(self, payload: SignupRequest) -> dict:
        email = payload.email.strip()
        password = payload.password
        
        try:
            res = supabase_client.auth.sign_up({"email": email, "password": password})
            if res.user:
                token = res.session.access_token if (hasattr(res, 'session') and res.session) else None
                refresh_token = res.session.refresh_token if (hasattr(res, 'session') and res.session) else None
                
                # Auto sign-in if sign_up did not return session tokens directly
                if not token:
                    try:
                        login_res = supabase_client.auth.sign_in_with_password({"email": email, "password": password})
                        if login_res.session:
                            token = getattr(login_res.session, 'access_token', None)
                            refresh_token = getattr(login_res.session, 'refresh_token', None)
                    except Exception:
                        pass

                return {
                    "success": True,
                    "token": token,
                    "refresh_token": refresh_token,
                    "data": {
                        "token": token,
                        "refresh_token": refresh_token,
                        "user": {"email": res.user.email, "id": res.user.id}
                    }
                }
            raise BadRequestException(detail="Signup failed. Please try again.")
        except Exception as e:
            # Fallback: If signup failed (e.g. user already exists or 429 rate limit hit), attempt direct sign-in
            try:
                login_res = supabase_client.auth.sign_in_with_password({"email": email, "password": password})
                if login_res and getattr(login_res, 'session', None):
                    token = getattr(login_res.session, 'access_token', None)
                    refresh_token = getattr(login_res.session, 'refresh_token', None)
                    user_obj = getattr(login_res, 'user', None)
                    return {
                        "success": True,
                        "token": token,
                        "refresh_token": refresh_token,
                        "data": {
                            "token": token,
                            "refresh_token": refresh_token,
                            "user": {"email": user_obj.email, "id": user_obj.id} if user_obj else {}
                        }
                    }
            except Exception:
                pass

            err_msg = str(e)
            if "429" in err_msg or "rate limit" in err_msg.lower() or "too many requests" in err_msg.lower():
                err_msg = "Supabase sign-up rate limit reached. Please sign in with your password or wait a few minutes."
            elif "User already registered" in err_msg or "already exists" in err_msg.lower():
                err_msg = "Account already exists. Please sign in with your password."
            raise BadRequestException(detail=err_msg)

    def login(self, payload: LoginRequest) -> dict:
        email = payload.email.strip()
        password = payload.password
        
        try:
            res = supabase_client.auth.sign_in_with_password({"email": email, "password": password})
            if res.session:
                token = getattr(res.session, 'access_token', None)
                refresh_token = getattr(res.session, 'refresh_token', None)
                return {
                    "success": True,
                    "token": token,
                    "refresh_token": refresh_token,
                    "data": {
                        "token": token,
                        "refresh_token": refresh_token,
                    }
                }
            raise BadRequestException(detail="Invalid email or password.")
        except Exception as e:
            err_msg = str(e)
            if "Invalid login credentials" in err_msg:
                err_msg = "Invalid email or password. Please check your credentials or sign up."
            elif "Email not confirmed" in err_msg:
                err_msg = "Email not confirmed. Please check your inbox or sign in."
            raise BadRequestException(detail=err_msg)

    def google_login(self, payload: GoogleLoginRequest) -> dict:
        try:
            res = supabase_client.auth.sign_in_with_id_token({
                "provider": "google",
                "token": payload.idToken
            })
            if res.session:
                token = getattr(res.session, 'access_token', None)
                refresh_token = getattr(res.session, 'refresh_token', None)
                return {
                    "success": True,
                    "token": token,
                    "refresh_token": refresh_token,
                    "data": {
                        "token": token,
                        "refresh_token": refresh_token,
                    }
                }
            raise BadRequestException(detail="Google authentication failed")
        except Exception as e:
            raise BadRequestException(detail=str(e))

    def forgot_password(self, email: str) -> dict:
        try:
            supabase_client.auth.reset_password_for_email(email)
            return {"success": True, "message": "Password reset email sent. Please check your inbox."}
        except Exception as e:
            return {"success": True, "message": "If that email exists, a reset link has been sent."}

    def refresh_session(self, refresh_token: str) -> dict:
        """Exchange a Supabase refresh_token for a fresh access_token."""
        try:
            res = supabase_client.auth.refresh_session(refresh_token)
            if res.session:
                return {
                    "success": True,
                    "token": res.session.access_token,
                    "refresh_token": res.session.refresh_token,
                }
            raise BadRequestException(detail="Session refresh failed")
        except Exception as e:
            raise BadRequestException(detail=str(e))

auth_service = AuthService()

