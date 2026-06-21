from __future__ import annotations

from apps.worker.celery_app import celery_app
from src.modules.acceptance_prediction.application.governance import ModelGovernanceService
from src.modules.acceptance_prediction.infrastructure.repositories import (
    MLGovernanceEventRepository,
    MLModelVersionRepository,
    MLTrainingRunRepository,
)
from src.shared.infrastructure.db.session import SessionLocal, init_db


@celery_app.task(name="models.expire_pending_governance")
def expire_pending_governance_events(
    *,
    model_name: str | None = None,
    pending_operator: str | None = None,
    operator: str = "governance-bot",
    limit: int = 100,
) -> dict[str, object]:
    init_db()
    session = SessionLocal()
    try:
        result = ModelGovernanceService(
            version_repository=MLModelVersionRepository(session),
            training_run_repository=MLTrainingRunRepository(session),
            governance_event_repository=MLGovernanceEventRepository(session),
        ).expire_pending_governance_events(
            model_name=model_name,
            pending_operator=pending_operator,
            operator=operator,
            limit=limit,
        )
        return {
            "status": "completed",
            "modelName": model_name,
            "pendingOperator": pending_operator,
            "operator": operator,
            "expiredCount": result.expired_count,
            "expiredEventIds": result.expired_event_ids,
        }
    finally:
        session.close()
