from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from src.shared.config.settings import get_settings


settings = get_settings()

celery_app = Celery(
    "offer_compensation_engine",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.update(
    task_always_eager=settings.celery_task_always_eager,
    task_store_eager_result=settings.celery_task_store_eager_result,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "scheduled-market-sync-demo": {
            "task": "market.sync_demo_batch",
            "schedule": crontab(minute=f"*/{settings.market_sync_schedule_minutes}"),
        },
        "scheduled-governance-expire-pending": {
            "task": "models.expire_pending_governance",
            "schedule": crontab(minute=f"*/{settings.governance_pending_review_sweep_minutes}"),
        },
        "scheduled-governance-alert-scan": {
            "task": "models.scan_governance_alerts",
            "schedule": crontab(minute=f"*/{settings.governance_pending_review_sweep_minutes}"),
        },
        "scheduled-governance-alert-notify": {
            "task": "models.notify_governance_alerts",
            "schedule": crontab(minute=f"*/{settings.governance_pending_review_sweep_minutes}"),
        }
    },
)
celery_app.autodiscover_tasks(["apps.worker.tasks"])
