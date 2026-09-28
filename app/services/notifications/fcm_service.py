import os
import json
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

_firebase_initialized = False

def _init_firebase() -> bool:
    """
    Initializes Firebase Admin SDK if credentials are available.
    Supports:
    1. FIREBASE_SERVICE_ACCOUNT_JSON env var (stringified JSON)
    2. FIREBASE_SERVICE_ACCOUNT_PATH env var (path to JSON file)
    3. Default paths: backend/firebase_service_account.json or firebase_service_account.json
    """
    global _firebase_initialized
    if _firebase_initialized:
        return True

    try:
        import firebase_admin
        from firebase_admin import credentials

        # Check if already initialized by another module
        if firebase_admin._apps:
            _firebase_initialized = True
            return True

        cred = None
        json_env = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
        path_env = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")

        if json_env:
            try:
                cert_dict = json.loads(json_env)
                cred = credentials.Certificate(cert_dict)
            except Exception as e:
                logger.error(f"Failed to parse FIREBASE_SERVICE_ACCOUNT_JSON: {e}")

        if not cred and path_env and os.path.exists(path_env):
            cred = credentials.Certificate(path_env)

        if not cred:
            candidate_paths = [
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "firebase_service_account.json"),
                os.path.join(os.getcwd(), "firebase_service_account.json"),
                os.path.join(os.getcwd(), "backend", "firebase_service_account.json"),
            ]
            for p in candidate_paths:
                p_norm = os.path.normpath(p)
                if os.path.exists(p_norm):
                    cred = credentials.Certificate(p_norm)
                    logger.info(f"Loaded Firebase service account from {p_norm}")
                    break

        if cred:
            firebase_admin.initialize_app(cred)
            _firebase_initialized = True
            logger.info("Firebase Admin SDK initialized successfully for FCM.")
            return True
        else:
            logger.warning(
                "FCM Service: No Firebase service account credentials found. "
                "Push notifications will be logged but not sent over the wire. "
                "To enable FCM push notifications from the backend, download your Service Account "
                "JSON from Firebase Console -> Project Settings -> Service accounts and place it at "
                "backend/firebase_service_account.json or set FIREBASE_SERVICE_ACCOUNT_JSON."
            )
            return False
    except Exception as e:
        logger.error(f"Error initializing Firebase Admin SDK: {e}")
        return False


def send_push_notification(
    token: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Sends a push notification to a specific device via FCM token.
    """
    if not token or not token.strip():
        return False

    if not _init_firebase():
        logger.info(f"[FCM Dry-Run] Token: {token[:12]}... | Title: {title} | Body: {body}")
        return False

    try:
        from firebase_admin import messaging

        str_data = {str(k): str(v) for k, v in (data or {}).items()}

        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=str_data,
            token=token,
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    channel_id="sabtrack_channel_general",
                    sound="default",
                ),
            ),
        )

        response = messaging.send(message)
        logger.info(f"FCM notification sent successfully: {response}")
        return True
    except Exception as e:
        logger.error(f"Failed to send FCM push notification: {e}")
        return False


def send_push_to_user(
    user_id: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Looks up the user's FCM token from Supabase and dispatches the push notification.
    """
    if not user_id:
        return False

    try:
        from app.database.supabase import supabase_client
        if not supabase_client:
            return False

        res = supabase_client.from_("users").select("fcm_token").eq("id", str(user_id)).execute()
        if res and res.data and len(res.data) > 0:
            token = res.data[0].get("fcm_token")
            if token:
                return send_push_notification(token, title, body, data=data)
            else:
                logger.debug(f"User {user_id} has no registered FCM token.")
        return False
    except Exception as e:
        logger.error(f"Error querying FCM token for user {user_id}: {e}")
        return False
