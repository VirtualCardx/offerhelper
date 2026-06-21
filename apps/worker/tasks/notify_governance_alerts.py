from __future__ import annotations

from apps.worker.celery_app import celery_app
from src.modules.acceptance_prediction.application.governance import ModelGovernanceService
from src.modules.acceptance_prediction.application.governance_notifications import GovernanceAlertNotifier
from src.modules.acceptance_prediction.infrastructure.repositories import (
    MLGovernanceEventRepository,
    MLModelVersionRepository,
    MLTrainingRunRepository,
)
from src.shared.infrastructure.db.session import SessionLocal, init_db


@celery_app.task(name="models.notify_governance_alerts")
def notify_governance_alerts(
    *,
    model_name: str | None = None,
    operator: str | None = None,
    severity: str | None = None,
    alert_type: str | None = None,
    channel: str | None = None,
    destination: str | None = None,
    limit: int = 50,
) -> dict[str, object]:
    init_db()
    session = SessionLocal()
    try:
        alerts = ModelGovernanceService(
            version_repository=MLModelVersionRepository(session),
            training_run_repository=MLTrainingRunRepository(session),
            governance_event_repository=MLGovernanceEventRepository(session),
        ).list_governance_alerts(
            model_name=model_name,
            operator=operator,
            severity=severity,
            alert_type=alert_type,
            limit=limit,
        )
        result = GovernanceAlertNotifier().notify(
            alerts=alerts,
            channel=channel,
            destination=destination,
        )
        return {
            "status": "completed",
            "modelName": model_name,
            "operator": operator,
            "severity": severity,
            "alertType": alert_type,
            "channel": result.channel,
            "destination": result.destination,
            "deliveryCount": result.delivery_count,
            "notifiedAlertIds": result.notified_alert_ids,
            "deliveries": [
                {
                    "id": item.id,
                    "alertId": item.alert_id,
                    "channel": item.channel,
                    "destination": item.destination,
                    "subject": item.subject,
                    "body": item.body,
                    "payload": item.payload,
                }
                for item in result.deliveries
            ],
        }
    finally:
        session.close()
