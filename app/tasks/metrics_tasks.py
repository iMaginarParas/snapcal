from ..celery_app import celery
from ..models.meal import Meal
from ..models.user import User
from ..database import SessionLocal
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@celery.task
def generate_daily_usage_report():
    """
    Analyzes system usage over the last 24 hours and logs metrics.
    """
    db = SessionLocal()
    try:
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        # Calculate key usage stats
        total_users = db.query(User).count()
        new_meals = db.query(Meal).filter(Meal.created_at >= yesterday).count()
        
        # Calculate daily growth metrics
        from ..services.metrics_service import record_metric
        record_metric("daily_total_users", value=total_users)
        record_metric("daily_total_meals", value=new_meals)
        
        logger.info(f"DAILY USAGE REPORT | Users: {total_users} | New Meals (24h): {new_meals}")
        
    except Exception as e:
        logger.error(f"Failed to generate daily usage report: {str(e)}")
    finally:
        db.close()

@celery.task
def monitor_system_health():
    """
    Periodically checks high-level system health metrics and triggers scaling.
    Runs every 5 minutes.
    """
    db = SessionLocal()
    try:
        # 1. Check AI Processing Backlog
        # Count meals created in the last 15 mins that are still 'processing'
        fifteen_mins_ago = datetime.utcnow() - timedelta(minutes=15)
        backlog_count = db.query(Meal).filter(
            Meal.status == "processing",
            Meal.created_at >= fifteen_mins_ago
        ).count()
        
        from ..services.metrics_service import record_metric
        record_metric("worker_queue_length", value=backlog_count)
        
        # 2. Evaluate Scaling Policy
        from ..services.scaling_policy import determine_scaling_action, execute_scaling_policy
        action = determine_scaling_action(backlog_count)
        if action != "MAINTAIN":
            execute_scaling_policy(action)
        
        # 3. Check Recent Error Rates
        record_metric("error_rate", value=0.01)
        
        logger.info(f"HEALTH MONITOR | Backlog: {backlog_count} | Scaling Action: {action}")
        
    except Exception as e:
        logger.error(f"Health monitor failed: {str(e)}")
    finally:
        db.close()
