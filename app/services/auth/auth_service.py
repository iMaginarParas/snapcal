from app.schemas.auth import SignupRequest, LoginRequest, GoogleLoginRequest
from app.core.exceptions import BadRequestException
from app.database.supabase import get_track_supabase, get_coach_supabase, supabase_client


def _get_auth_clients():
    clients = []
    track_sb = get_track_supabase()
    coach_sb = get_coach_supabase()
    if track_sb:
        clients.append(track_sb)
    if coach_sb and coach_sb is not track_sb:
        clients.append(coach_sb)
    if not clients and supabase_client:
        clients.append(supabase_client)
    return clients


class AuthService:
    def signup(self, payload: SignupRequest) -> dict:
        email = payload.email.strip()
        password = payload.password
        
        clients = _get_auth_clients()
        if not clients:
            raise BadRequestException(detail="No Supabase client configured.")

        # Attempt sign up on primary client (Track, or Coach if Track unavailable)
        client = clients[0]
        try:
            res = client.auth.sign_up({"email": email, "password": password})
            if res.user:
                token = res.session.access_token if (hasattr(res, 'session') and res.session) else None
                refresh_token = res.session.refresh_token if (hasattr(res, 'session') and res.session) else None
                
                # Auto sign-in if sign_up did not return session tokens directly
                if not token:
                    try:
                        login_res = client.auth.sign_in_with_password({"email": email, "password": password})
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
            # Fallback: If signup failed (e.g. user already exists or 429 rate limit hit), attempt direct sign-in across clients
            for cl in clients:
                try:
                    login_res = cl.auth.sign_in_with_password({"email": email, "password": password})
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
        
        clients = _get_auth_clients()
        if not clients:
            raise BadRequestException(detail="No Supabase client configured.")

        last_error = "Invalid email or password."
        for client in clients:
            try:
                res = client.auth.sign_in_with_password({"email": email, "password": password})
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
            except Exception as e:
                err_msg = str(e)
                if "Email not confirmed" in err_msg:
                    last_error = "Email not confirmed. Please check your inbox or sign in."
                elif "Invalid login credentials" in err_msg:
                    last_error = "Invalid email or password. Please check your credentials or sign up."
                else:
                    last_error = err_msg

        raise BadRequestException(detail=last_error)

    def google_login(self, payload: GoogleLoginRequest) -> dict:
        clients = _get_auth_clients()
        last_error = "Google authentication failed"
        for client in clients:
            try:
                res = client.auth.sign_in_with_id_token({
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
            except Exception as e:
                last_error = str(e)
        raise BadRequestException(detail=last_error)

    def get_google_oauth_url(self, redirect_to: str) -> dict:
        import urllib.parse
        clients = _get_auth_clients()

        for client in clients:
            try:
                res = client.auth.sign_in_with_oauth({
                    "provider": "google",
                    "options": {"redirect_to": redirect_to}
                })
                if hasattr(res, 'url') and res.url:
                    return {"success": True, "url": res.url}
            except Exception:
                pass

        for client in clients:
            try:
                base = getattr(client.auth, '_url', None) or getattr(client.auth, 'auth_url', None)
                if base:
                    url = f"{base}/authorize?provider=google&redirect_to={urllib.parse.quote(redirect_to)}"
                    return {"success": True, "url": url}
            except Exception:
                pass

        from app.core.config import settings
        sb_url = settings.coach_supabase_url or settings.track_supabase_url
        if sb_url and "your_supabase" not in sb_url:
            url = f"{sb_url}/auth/v1/authorize?provider=google&redirect_to={urllib.parse.quote(redirect_to)}"
            return {"success": True, "url": url}

        raise BadRequestException(detail="Supabase Google OAuth provider is not configured.")

    def forgot_password(self, email: str) -> dict:
        clients = _get_auth_clients()
        for client in clients:
            try:
                client.auth.reset_password_for_email(email)
            except Exception:
                pass
        return {"success": True, "message": "Password reset email sent. Please check your inbox."}

    def refresh_session(self, refresh_token: str) -> dict:
        """Exchange a Supabase refresh_token for a fresh access_token."""
        clients = _get_auth_clients()
        for client in clients:
            try:
                res = client.auth.refresh_session(refresh_token)
                if res.session:
                    return {
                        "success": True,
                        "token": res.session.access_token,
                        "refresh_token": res.session.refresh_token,
                    }
            except Exception:
                pass
        raise BadRequestException(detail="Session refresh failed")

auth_service = AuthService()


