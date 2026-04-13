import os
import multiprocessing
import sentry_sdk
from celery import Celery
from celery.schedules import crontab
from sentry_sdk.integrations.celery import CeleryIntegration

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0"
)

# Initialize Sentry for Celery Worker/Beat
if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[
            CeleryIntegration(),
        ],
        traces_sample_rate=1.0,
        environment="production",
    )

celery = Celery(
    "fitsnap",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.tasks.meal_tasks",
        "app.tasks.reminder_tasks",
        "app.tasks.metrics_tasks",
        "app.tasks.backup_tasks",
        "app.tasks.cleanup_tasks"
    ]
)

# Worker Performance & Cost Tuning
worker_autoscale = (10, 2)
worker_concurrency = multiprocessing.cpu_count() * 2

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_autoscale=worker_autoscale,
    worker_concurrency=worker_concurrency,
    # Cost: Prevent memory leaks by restarting workers after 100 tasks
    worker_max_tasks_per_child=100,
    task_time_limit=300,
    task_soft_time_limit=240,
    timezone="Asia/Kolkata",
)

# Celery Beat Schedule
celery.conf.beat_schedule = {
    "daily-meal-reminder": {
        "task": "app.tasks.reminder_tasks.send_daily_meal_reminder",
        "schedule": crontab(hour=19, minute=0),
    },
    "weekly-summary": {
        "task": "app.tasks.reminder_tasks.send_weekly_summary",
        "schedule": crontab(day_of_week="monday", hour=9, minute=0),
    },
    "daily-infrastructure-report": {
        "task": "app.tasks.metrics_tasks.generate_daily_usage_report",
        "schedule": crontab(hour=0, minute=0),
    },
    "system-health-monitor": {
        "task": "app.tasks.metrics_tasks.monitor_system_health",
        "schedule": crontab(minute="*/5"),
    },
    "backup-integrity-check": {
        "task": "app.tasks.backup_tasks.verify_backup_integrity",
        "schedule": crontab(hour=2, minute=0),
    },
    "weekly-storage-cleanup": {
        "task": "app.tasks.cleanup_tasks.cleanup_old_images",
        # Run every Sunday at 3:00 AM IST
        "schedule": crontab(day_of_week="sunday", hour=3, minute=0),
    },
}
