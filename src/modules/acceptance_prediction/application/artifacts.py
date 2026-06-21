from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from src.modules.acceptance_prediction.domain.services import RegisteredModel
from src.shared.presentation.errors import DomainValidationError


@dataclass(frozen=True)
class ArtifactValidationResult:
    artifact_uri: str
    framework: str
    scheme: str
    exists: bool
    loadable: bool
    resolved_path: str | None
    loaded_config: dict[str, object]
    loaded_metrics: dict[str, object]
    loaded_runtime: dict[str, object]


class ModelArtifactLoader:
    def validate(self, registered_model: RegisteredModel) -> ArtifactValidationResult:
        scheme = self._get_scheme(registered_model.artifact_uri)
        if scheme == "registry":
            return ArtifactValidationResult(
                artifact_uri=registered_model.artifact_uri,
                framework=registered_model.framework,
                scheme=scheme,
                exists=True,
                loadable=True,
                resolved_path=None,
                loaded_config=registered_model.config,
                loaded_metrics={},
                loaded_runtime={},
            )
        if scheme == "file":
            resolved_path = self._resolve_file_path(registered_model.artifact_uri)
            if not resolved_path.exists():
                raise DomainValidationError(f"Artifact '{registered_model.artifact_uri}' does not exist.")
            payload = self._load_json_artifact(resolved_path)
            framework = str(payload.get("framework", registered_model.framework))
            loaded_runtime = self._validate_runtime_spec(
                payload=payload,
                framework=framework,
                artifact_path=resolved_path,
            )
            loaded_config = payload.get("config", registered_model.config)
            loaded_metrics = payload.get("metrics", {})
            return ArtifactValidationResult(
                artifact_uri=registered_model.artifact_uri,
                framework=framework,
                scheme=scheme,
                exists=True,
                loadable=True,
                resolved_path=str(resolved_path),
                loaded_config=loaded_config,
                loaded_metrics=loaded_metrics,
                loaded_runtime=loaded_runtime,
            )
        raise DomainValidationError(f"Unsupported artifact URI scheme in '{registered_model.artifact_uri}'.")

    def load_runtime_model(self, registered_model: RegisteredModel) -> RegisteredModel:
        validation = self.validate(registered_model)
        framework = validation.framework or registered_model.framework
        merged_config = dict(registered_model.config)
        merged_config.update(validation.loaded_config)
        if validation.loaded_runtime:
            merged_config["_runtime"] = validation.loaded_runtime
        return RegisteredModel(
            model_name=registered_model.model_name,
            model_version=registered_model.model_version,
            framework=framework,
            artifact_uri=registered_model.artifact_uri,
            config=merged_config,
        )

    @staticmethod
    def _get_scheme(artifact_uri: str) -> str:
        parsed = urlparse(artifact_uri)
        return parsed.scheme

    @staticmethod
    def _resolve_file_path(artifact_uri: str) -> Path:
        parsed = urlparse(artifact_uri)
        if parsed.scheme != "file":
            raise DomainValidationError(f"Artifact '{artifact_uri}' is not a file URI.")
        raw_path = parsed.path
        if raw_path.startswith("/") and len(raw_path) > 2 and raw_path[2] == ":":
            raw_path = raw_path[1:]
        return Path(raw_path)

    @staticmethod
    def _load_json_artifact(path: Path) -> dict[str, object]:
        if path.suffix.lower() != ".json":
            raise DomainValidationError(f"Only JSON artifacts are currently supported, got '{path.name}'.")
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise DomainValidationError(f"Artifact '{path}' contains invalid JSON.") from exc

    def _validate_runtime_spec(
        self,
        *,
        payload: dict[str, object],
        framework: str,
        artifact_path: Path,
    ) -> dict[str, object]:
        if framework not in {"sklearn", "xgboost"}:
            return {}

        runtime = payload.get("runtime")
        if not isinstance(runtime, dict):
            raise DomainValidationError(
                f"Artifact '{artifact_path.name}' must define a runtime object for framework '{framework}'."
            )

        runtime_type = str(runtime.get("type", ""))
        if runtime_type != "python-pickle-proba":
            raise DomainValidationError(f"Unsupported runtime type '{runtime_type}' in '{artifact_path.name}'.")

        model_path_value = runtime.get("modelPath")
        feature_order = runtime.get("featureOrder")
        if not isinstance(model_path_value, str) or not model_path_value:
            raise DomainValidationError(f"Artifact '{artifact_path.name}' must define runtime.modelPath.")
        if not isinstance(feature_order, list) or not feature_order or not all(
            isinstance(feature_name, str) for feature_name in feature_order
        ):
            raise DomainValidationError(f"Artifact '{artifact_path.name}' must define a non-empty runtime.featureOrder.")

        model_path = Path(model_path_value)
        if not model_path.is_absolute():
            model_path = artifact_path.parent / model_path
        if not model_path.exists():
            raise DomainValidationError(f"Referenced model file '{model_path}' does not exist.")

        self._load_pickle_runtime_model(model_path)
        resolved_runtime = dict(runtime)
        resolved_runtime["resolvedModelPath"] = str(model_path.resolve())
        return resolved_runtime

    @staticmethod
    def _load_pickle_runtime_model(model_path: Path) -> object:
        if model_path.suffix.lower() not in {".pkl", ".pickle"}:
            raise DomainValidationError(f"Only pickle model files are supported, got '{model_path.name}'.")
        with model_path.open("rb") as artifact_file:
            model = pickle.load(artifact_file)
        if not hasattr(model, "predict_proba") or not callable(model.predict_proba):
            raise DomainValidationError(f"Model file '{model_path.name}' does not expose predict_proba().")
        return model
