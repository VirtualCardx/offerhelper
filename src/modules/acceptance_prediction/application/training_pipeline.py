from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Literal

from sqlalchemy.orm import Session

from src.modules.acceptance_prediction.application.exporter import AcceptanceModelArtifactExporter
from src.modules.acceptance_prediction.application.registry import ActivePredictionModel, ModelRegistryService
from src.modules.acceptance_prediction.application.sample_data import build_demo_training_samples
from src.modules.acceptance_prediction.application.trainer import AcceptanceModelTrainer
from src.modules.acceptance_prediction.application.training_data import HistoricalAcceptanceTrainingDataService
from src.modules.acceptance_prediction.infrastructure.repositories import (
    MLGovernanceEvent,
    MLGovernanceEventRepository,
    MLModelVersionRepository,
    MLTrainingRun,
    MLTrainingRunRepository,
)


@dataclass(frozen=True)
class TrainingPipelineResult:
    model_name: str
    model_version: str
    framework: str
    source: str
    activation_mode: str
    activated: bool
    activation_reason: str
    previous_active_version: str | None
    sample_count: int
    acceptance_rate: str
    training_accuracy: float
    training_log_loss: float
    manifest_path: str
    model_path: str
    artifact_uri: str
    registered_model: ActivePredictionModel
    training_run: MLTrainingRun
    governance_event: MLGovernanceEvent


class AcceptanceModelTrainingPipeline:
    def __init__(self, session: Session, *, output_dir: Path) -> None:
        self.session = session
        self.output_dir = output_dir

    def run(
        self,
        *,
        model_name: str,
        model_version: str | None,
        framework: str,
        source: str,
        activation_mode: Literal["always", "if_better", "never"],
        operator: str = "system",
    ) -> TrainingPipelineResult:
        repository = MLModelVersionRepository(self.session)
        registry = ModelRegistryService(repository)
        registry.ensure_default_versions()
        resolved_model_version = model_version or self._generate_next_model_version(model_name=model_name)
        feature_order = [
            "offer_to_market_ratio",
            "raise_ratio",
            "interview_score",
            "has_other_offer",
        ]
        training_samples = self._load_training_samples(source=source)
        trained_model = AcceptanceModelTrainer().train(
            training_samples=training_samples,
            feature_order=feature_order,
        )
        exported = AcceptanceModelArtifactExporter().export(
            model_name=model_name,
            model_version=resolved_model_version,
            framework=framework,
            output_dir=self.output_dir,
            feature_order=trained_model.feature_order,
            intercept=trained_model.intercept,
            coefficients=trained_model.coefficients,
            training_samples=training_samples,
            metrics={
                "source": f"{source}-trained-export-pipeline",
                "trainingAccuracy": round(trained_model.accuracy, 4),
                "trainingLogLoss": round(trained_model.log_loss, 6),
            },
        )
        artifact_uri = exported.manifest_path.resolve().as_uri()
        previous_active_model = registry.get_active_model(model_name=model_name)
        should_activate, activation_reason = self._decide_activation(
            activation_mode=activation_mode,
            previous_active_metrics=previous_active_model.metrics,
            current_training_accuracy=round(trained_model.accuracy, 4),
            current_training_log_loss=round(trained_model.log_loss, 6),
        )
        registered_model = registry.register_version(
            model_name=model_name,
            model_version=resolved_model_version,
            framework=framework,
            artifact_uri=artifact_uri,
            config={},
            metrics={
                "source": source,
                "trainingAccuracy": round(trained_model.accuracy, 4),
                "trainingLogLoss": round(trained_model.log_loss, 6),
                "trainingSampleCount": trained_model.sample_count,
                "trainingAcceptanceRate": str(exported.acceptance_rate),
            },
            activate=should_activate,
        )
        training_run = MLTrainingRunRepository(self.session).create(
            model_name=model_name,
            model_version=resolved_model_version,
            framework=framework,
            source=source,
            status="COMPLETED",
            activation_mode=activation_mode,
            activated=should_activate,
            activation_reason=activation_reason,
            previous_active_version=previous_active_model.model_version,
            artifact_uri=artifact_uri,
            manifest_path=str(exported.manifest_path),
            model_path=str(exported.model_path),
            sample_count=exported.sample_count,
            acceptance_rate=str(exported.acceptance_rate),
            training_accuracy=round(trained_model.accuracy, 4),
            training_log_loss=round(trained_model.log_loss, 6),
            metrics={
                "source": source,
                "framework": framework,
            },
        )
        governance_event = MLGovernanceEventRepository(self.session).create(
            model_name=model_name,
            event_type="TRAIN",
            operator=operator,
            approval_ticket=None,
            risk_level="LOW",
            status="SUCCESS",
            reason=activation_reason,
            from_version=previous_active_model.model_version,
            to_version=resolved_model_version,
            metadata={
                "trainingRunId": training_run.id,
                "activationMode": activation_mode,
                "activated": should_activate,
                "source": source,
            },
        )
        return TrainingPipelineResult(
            model_name=model_name,
            model_version=resolved_model_version,
            framework=framework,
            source=source,
            activation_mode=activation_mode,
            activated=should_activate,
            activation_reason=activation_reason,
            previous_active_version=previous_active_model.model_version,
            sample_count=exported.sample_count,
            acceptance_rate=str(exported.acceptance_rate),
            training_accuracy=round(trained_model.accuracy, 4),
            training_log_loss=round(trained_model.log_loss, 6),
            manifest_path=str(exported.manifest_path),
            model_path=str(exported.model_path),
            artifact_uri=artifact_uri,
            registered_model=registered_model,
            training_run=training_run,
            governance_event=governance_event,
        )

    def _load_training_samples(self, *, source: str):
        if source == "demo":
            return build_demo_training_samples()
        return HistoricalAcceptanceTrainingDataService(self.session).build_training_samples()

    def _generate_next_model_version(self, *, model_name: str) -> str:
        repository = MLModelVersionRepository(self.session)
        numeric_versions: list[tuple[int, int, int]] = []
        for item in repository.list_versions(model_name=model_name):
            parsed = self._parse_semantic_version(item.model_version)
            if parsed is not None:
                numeric_versions.append(parsed)
        if not numeric_versions:
            return "0.1.0"
        major, minor, patch = max(numeric_versions)
        return f"{major}.{minor}.{patch + 1}"

    @staticmethod
    def _parse_semantic_version(model_version: str) -> tuple[int, int, int] | None:
        match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", model_version)
        if match is None:
            return None
        return tuple(int(part) for part in match.groups())

    @staticmethod
    def _decide_activation(
        *,
        activation_mode: Literal["always", "if_better", "never"],
        previous_active_metrics: dict[str, object],
        current_training_accuracy: float,
        current_training_log_loss: float,
    ) -> tuple[bool, str]:
        if activation_mode == "never":
            return False, "Activation mode is set to never."
        if activation_mode == "always":
            return True, "Activation mode is set to always."

        previous_accuracy = previous_active_metrics.get("trainingAccuracy")
        previous_log_loss = previous_active_metrics.get("trainingLogLoss")
        if previous_accuracy is None or previous_log_loss is None:
            return True, "Current active model has no comparable training metrics."

        previous_accuracy_value = float(previous_accuracy)
        previous_log_loss_value = float(previous_log_loss)
        if current_training_accuracy > previous_accuracy_value:
            return True, "New model has higher training accuracy than the active model."
        if (
            current_training_accuracy == previous_accuracy_value
            and current_training_log_loss < previous_log_loss_value
        ):
            return True, "New model matches training accuracy and improves training log loss."
        return False, "New model does not outperform the active model based on training metrics."
