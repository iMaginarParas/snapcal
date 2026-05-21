import firebase_admin
from firebase_admin import credentials, messaging
import os
import json
import logging
from .metrics_service import record_metric

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
try:
    # Option 1: Load from JSON string in environment variable (Production/Railway)
    firebase_json = os.getenv("FIREBASE_SERVICE_ACCOUNT")
    if firebase_json:
        cred = credentials.Certificate(json.loads(firebase_json))
        firebase_admin.initialize_app(cred)
    # Option 2: Load from local file path
    elif os.path.exists("firebase-service-account.json"):
        cred = credentials.Certificate("firebase-service-account.json")
        firebase_admin.initialize_app(cred)
    else:
        logger.warning("Firebase credentials not found. Push notifications will be disabled.")
except Exception as e:
    logger.error(f"Failed to initialize Firebase: {str(e)}")

def send_push_notification(token: str, title: str, body: str, data: dict = None):
    """
    Sends a push notification to a specific device token using FCM.
    """
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=token,
        )
        response = messaging.send(message)
        logger.info(f"Successfully sent push notification: {response}")
        
        # Track notification success metric
        record_metric("push_notification_sent", tags={"status": "success"})
        
        return response
    except Exception as e:
        logger.error(f"Error sending push notification to token {token}: {str(e)}")
        
        # Track notification failure metric
        record_metric("push_notification_sent", tags={"status": "failed", "error": str(e)})
        
        return None

def notify_user(user_id: int, title: str, body: str, data: dict = None, db=None):
    """
    Push notifications require device registration from the mobile app.
    Currently disabled until in-app push registration is implemented.
    """
    logger.info(f"Notification queued for user {user_id}: {title}")
