import logging
import os
from .notification_service import notify_user

logger = logging.getLogger(__name__)

# Core Thresholds
THRESHOLDS = {
    "api_latency": 0.5,           # seconds
    "worker_queue_length": 50,   # num jobs (simulated)
    "error_rate": 0.05,          # 5%
    "daily_storage_growth": 1 * 1024 * 1024 * 1024, # 1GB
    "max_ai_job_duration": 3.0   # seconds
}

def trigger_alert(metric_name: str, value: float, threshold: float, message: str = ""):
    """
    Triggers a system alert when a threshold is exceeded.
    """
    alert_msg = f"ALERT: {metric_name} ({value}) exceeded threshold ({threshold}). {message}"
    logger.error(alert_msg)
    
    # Notify system admins (User ID 1 is typically the primary admin)
    # We can also extend this to send to a Slack webhook or Sentry
    try:
        notify_user(
            user_id=1,
            title="⚠️ System Health Alert",
            body=f"{metric_name} is abnormally high. View logs for details.",
            data={"metric": metric_name, "value": str(value)}
        )
    except Exception as e:
        logger.error(f"Failed to send alert notification: {str(e)}")

def check_threshold(metric_name: str, value: float):
    """
    Checks a metric against predefined thresholds and triggers alerts if necessary.
    """
    threshold = THRESHOLDS.get(metric_name)
    if threshold is not None and value > threshold:
        trigger_alert(metric_name, value, threshold)
