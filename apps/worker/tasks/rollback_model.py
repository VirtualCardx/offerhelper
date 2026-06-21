from __future__ import annotations

from apps.worker.celery_app import celery_app
from src.modules.acceptance_prediction.application.governance import ModelGovernanceService
from src.modules.acceptance_prediction.application.registry import ModelRegistryService
from src.modules.acceptance_prediction.infrastructure.repositories import (
    MLGovernanceEventRepository,
    MLModelVersionRepository,
    MLTrainingRunRepository,
)
from src.shared.infrastructure.db.session import SessionLocal, init_db


@celery_app.task(name="models.rollback_active")
def rollback_active_model(
    *,
    model_name: str,
    target_version: str | None = None,
    operator: str = "system",
    approval_ticket: str | None = None,
) -> dict[str, object]:
    init_db()
    session = SessionLocal()
    try:
        version_repository = MLModelVersionRepository(session)
        ModelRegistryService(version_repository).ensure_default_versions()
        result = ModelGovernanceService(
            version_repository=version_repository,
            training_run_repository=MLTrainingRunRepository(session),
            governance_event_repository=MLGovernanceEventRepository(session),
        ).rollback_active_model(
            model_name=model_name,
            target_version=target_version,
            operator=operator,
            approval_ticket=approval_ticket,
        )
        return {
            "status": "completed",
            "modelName": result.model_name,
            "fromVersion": result.from_version,
            "toVersion": result.to_version,
            "reason": result.reason,
            "registeredStatus": result.status,
            "riskLevel": result.risk_level,
            "executed": result.executed,
            "governanceEventId": result.governance_event_id,
            "operator": operator,
            "approvalTicket": approval_ticket,
        }
    finally:
        session.close()
