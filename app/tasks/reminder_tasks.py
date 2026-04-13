from ..celery_app import celery
from ..models.user import User
from ..database import SessionLocal
from ..services.notification_service import notify_user
from ..services.analytics_service import is_feature_enabled
import logging

logger = logging.getLogger(__name__)

@celery.task
def send_daily_meal_reminder():
    """
    Sends a daily push notification reminder to all users 
    who haven't logged a meal yet today.
    """
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            # Check feature flag - Fail safe
            if is_feature_enabled(user_id=user.id, flag_name="enable_push_notifications"):
                notify_user(
                    user_id=user.id,
                    title="Time for Dinner? 🥗",
                    body="Don't forget to snap a photo of your meal to track your progress!",
                    db=db
                )
    except Exception as e:
        logger.error(f"Error in send_daily_meal_reminder: {str(e)}")
    finally:
        db.close()

@celery.task
def send_weekly_summary():
    """
    Sends a weekly health summary to users.
    """
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            if is_feature_enabled(user_id=user.id, flag_name="enable_push_notifications"):
                notify_user(
                    user_id=user.id,
                    title="Your Weekly Summary is Ready 📈",
                    body="Check out your step progress and calorie trends from last week.",
                    db=db
                )
    except Exception as e:
        logger.error(f"Error in send_weekly_summary: {str(e)}")
    finally:
        db.close()
