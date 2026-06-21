from __future__ import annotations

from dataclasses import dataclass

from src.modules.acceptance_prediction.application.artifacts import ArtifactValidationResult, ModelArtifactLoader
from src.modules.acceptance_prediction.domain.services import (
    AcceptancePredictionService,
    AcceptancePredictionServiceFactory,
    RegisteredModel,
)
from src.modules.acceptance_prediction.infrastructure.repositories import MLModelVersion, MLModelVersionRepository


@dataclass(frozen=True)
class ActivePredictionModel:
    id: str
    model_name: str
    model_version: str
    framework: str
    artifact_uri: str
    status: str
    config: dict[str, object]
    metrics: dict[str, object]


class ModelRegistryService:
    def __init__(self, repository: MLModelVersionRepository) -> None:
        self.repository = repository
        self.factory = AcceptancePredictionServiceFactory()
        self.artifact_loader = ModelArtifactLoader()

    def ensure_default_versions(self) -> None:
        existing_models = self.repository.list_versions(model_name="baseline-offer-acceptance")
        existing_versions = {(item.model_name, item.model_version) for item in existing_models}
        has_active_version = any(item.status == "ACTIVE" for item in existing_models)
        defaults = [
            (
                "0.1.0",
                "INACTIVE" if has_active_version else "ACTIVE",
                "registry://baseline-offer-acceptance/0.1.0",
                {
                    "base_probability": "0.55",
                    "offer_market_bonus": "0.12",
                    "raise_bonus": "0.10",
                    "high_score_bonus": "0.06",
                    "medium_score_bonus": "0.03",
                    "competing_offer_penalty": "0.06",
                },
                {"baseline": 1.0},
            ),
            (
                "0.2.0",
                "INACTIVE",
                "registry://baseline-offer-acceptance/0.2.0",
                {
                    "base_probability": "0.52",
                    "offer_market_bonus": "0.15",
                    "raise_bonus": "0.12",
                    "high_score_bonus": "0.08",
                    "medium_score_bonus": "0.04",
                    "competing_offer_penalty": "0.04",
                },
                {"aggressive": 1.0},
            ),
        ]
        for model_version, status, artifact_uri, config, metrics in defaults:
            if ("baseline-offer-acceptance", model_version) not in existing_versions:
                self.repository.ensure_exists(
                    model_name="baseline-offer-acceptance",
                    model_version=model_version,
                    framework="rule-based",
                    status=status,
                    artifact_uri=artifact_uri,
                    config=config,
                    metrics=metrics,
                )

    def register_version(
        self,
        *,
        model_name: str,
        model_version: str,
        framework: str,
        artifact_uri: str,
        config: dict[str, object],
        metrics: dict[str, object] | None = None,
        activate: bool = False,
    ) -> ActivePredictionModel:
        candidate = RegisteredModel(
            model_name=model_name,
            model_version=model_version,
            framework=framework,
            artifact_uri=artifact_uri,
            config=config,
        )
        self.artifact_loader.validate(candidate)
        status = "ACTIVE" if activate else "INACTIVE"
        registered = self.repository.ensure_exists(
            model_name=model_name,
            model_version=model_version,
            framework=framework,
            status=status,
            artifact_uri=artifact_uri,
            config=config,
            metrics=metrics or {},
        )
        if activate:
            registered = self.repository.activate_version(model_name=model_name, model_version=model_version)
        return self._to_active_model(registered)

    def get_active_model(self, *, model_name: str) -> ActivePredictionModel:
        self.ensure_default_versions()
        return self._to_active_model(self.repository.get_active_version(model_name=model_name))

    def get_prediction_service(self, *, model_name: str) -> AcceptancePredictionService:
        active = self.get_active_model(model_name=model_name)
        runtime_model = self.artifact_loader.load_runtime_model(
            RegisteredModel(
                model_name=active.model_name,
                model_version=active.model_version,
                framework=active.framework,
                artifact_uri=active.artifact_uri,
                config=active.config,
            )
        )
        return self.factory.create(runtime_model)

    def validate_model_version(self, *, model_name: str, model_version: str) -> ArtifactValidationResult:
        model = self.repository.get_by_name_and_version(model_name=model_name, model_version=model_version)
        return self.artifact_loader.validate(
            RegisteredModel(
                model_name=model.model_name,
                model_version=model.model_version,
                framework=model.framework,
                artifact_uri=model.artifact_uri,
                config=model.config,
            )
        )

    @staticmethod
    def _to_active_model(model: MLModelVersion) -> ActivePredictionModel:
        return ActivePredictionModel(
            id=model.id,
            model_name=model.model_name,
            model_version=model.model_version,
            framework=model.framework,
            artifact_uri=model.artifact_uri,
            status=model.status,
            config=model.config,
            metrics=model.metrics,
        )
