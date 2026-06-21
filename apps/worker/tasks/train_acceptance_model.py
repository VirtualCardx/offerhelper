from __future__ import annotations

from pathlib import Path
from typing import Literal

from apps.worker.celery_app import celery_app
from src.modules.acceptance_prediction.application.training_pipeline import AcceptanceModelTrainingPipeline
from src.shared.infrastructure.db.session import SessionLocal, init_db


@celery_app.task(name="models.train_acceptance")
def train_acceptance_model(
    *,
    model_name: str,
    model_version: str | None,
    framework: str,
    source: str,
    activation_mode: Literal["always", "if_better", "never"],
    operator: str = "system",
) -> dict[str, object]:
    init_db()
    session = SessionLocal()
    try:
        pipeline = AcceptanceModelTrainingPipeline(
            session,
            output_dir=Path("artifacts") / "acceptance_prediction",
        )
        result = pipeline.run(
            model_name=model_name,
            model_version=model_version,
            framework=framework,
            source=source,
            activation_mode=activation_mode,
            operator=operator,
        )
        return {
            "status": "completed",
            "modelName": result.model_name,
            "modelVersion": result.model_version,
            "framework": result.framework,
            "source": result.source,
            "activationMode": result.activation_mode,
            "activated": result.activated,
            "activationReason": result.activation_reason,
            "previousActiveVersion": result.previous_active_version,
            "operator": operator,
            "sampleCount": result.sample_count,
            "acceptanceRate": result.acceptance_rate,
            "trainingAccuracy": result.training_accuracy,
            "trainingLogLoss": result.training_log_loss,
            "manifestPath": result.manifest_path,
            "modelPath": result.model_path,
            "artifactUri": result.artifact_uri,
            "registeredModelId": result.registered_model.id,
            "registeredStatus": result.registered_model.status,
            "trainingRunId": result.training_run.id,
            "governanceEventId": result.governance_event.id,
        }
    finally:
        session.close()
