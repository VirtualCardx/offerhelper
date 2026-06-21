from __future__ import annotations

from apps.worker.celery_app import celery_app
from src.modules.acceptance_prediction.application.governance import ModelGovernanceService
from src.modules.acceptance_prediction.infrastructure.repositories import (
    MLGovernanceEventRepository,
    MLModelVersionRepository,
    MLTrainingRunRepository,
)
from src.shared.infrastructure.db.session import SessionLocal, init_db


@celery_app.task(name="models.scan_governance_alerts")
def scan_governance_alerts(
    *,
    model_name: str | None = None,
    operator: str | None = None,
    limit: int = 50,
) -> dict[str, object]:
    init_db()
    session = SessionLocal()
    try:
        result = ModelGovernanceService(
            version_repository=MLModelVersionRepository(session),
            training_run_repository=MLTrainingRunRepository(session),
            governance_event_repository=MLGovernanceEventRepository(session),
        ).scan_governance_alerts(
            model_name=model_name,
            operator=operator,
            limit=limit,
        )
        return {
            "status": "completed",
            "modelName": model_name,
            "operator": operator,
            "alertCount": result.alert_count,
            "highSeverityCount": result.high_severity_count,
            "criticalSeverityCount": result.critical_severity_count,
            "alertIds": result.alert_ids,
        }
    finally:
        session.close()
