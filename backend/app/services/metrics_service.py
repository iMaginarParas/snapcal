import logging
import os
from datetime import datetime
from ..services.analytics_service import track_event

logger = logging.getLogger(__name__)

# Basic metrics service that logs to console and forwards to PostHog for visualization
def record_metric(name: str, value: float = 1.0, tags: dict = None):
    """
    Records a system metric.
    Metrics are logged and forwarded to PostHog as events for trend analysis.
    """
    metric_data = {
        "metric_name": name,
        "value": value,
        "timestamp": datetime.utcnow().isoformat(),
        "tags": tags or {}
    }
    
    # Log locally for infrastructure monitoring tools (like Datadog or Railway logs)
    logger.info(f"METRIC: {name}={value} | Tags: {tags}")
    
    # Forward to PostHog for visualization dashboards
    track_event(
        user_id="internal_infrastructure",
        event_name=f"metric_{name}",
        properties=metric_data
    )
    
    # Check against thresholds for real-time alerting
    from .alert_service import check_threshold
    check_threshold(name, value)

def track_storage_usage(file_size_bytes: int):
    record_metric("daily_storage_growth", value=file_size_bytes)

def track_api_request(endpoint: str, status_code: int, response_time: float = 0.0):
    record_metric("api_request", tags={"endpoint": endpoint, "status": status_code})
    if response_time > 0:
        record_metric("api_latency", value=response_time, tags={"endpoint": endpoint})

def track_ai_job(model_name: str, duration_sec: float):
    record_metric("ai_processing_job", value=duration_sec, tags={"model": model_name})
    record_metric("max_ai_job_duration", value=duration_sec, tags={"model": model_name})
