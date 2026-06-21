from __future__ import annotations

import pickle
from pathlib import Path

from src.modules.acceptance_prediction.application.artifacts import ModelArtifactLoader
from src.modules.acceptance_prediction.domain.services import RegisteredModel, WeightedProbabilityModel


def test_load_runtime_model_from_file_artifact() -> None:
    artifact_dir = Path(__file__).resolve().parents[2] / "artifacts" / "acceptance_prediction"
    artifact_uri = (artifact_dir / "baseline-offer-acceptance-0.3.0.json").as_uri()
    model_path = artifact_dir / "baseline-offer-acceptance-0.3.0.pkl"
    loader = ModelArtifactLoader()

    with model_path.open("wb") as artifact_file:
        pickle.dump(
            WeightedProbabilityModel(
                intercept=-0.61,
                coefficients=[1.0, 0.8, 0.01, -0.25],
            ),
            artifact_file,
        )

    runtime_model = loader.load_runtime_model(
        RegisteredModel(
            model_name="baseline-offer-acceptance",
            model_version="0.3.0",
            framework="xgboost",
            artifact_uri=artifact_uri,
            config={"base_probability": "0.01"},
        )
    )

    assert runtime_model.framework == "xgboost"
    assert runtime_model.config["base_probability"] == "0.50"
    assert runtime_model.config["offer_market_bonus"] == "0.16"
    assert runtime_model.config["_runtime"]["type"] == "python-pickle-proba"
    assert runtime_model.config["_runtime"]["resolvedModelPath"].endswith("baseline-offer-acceptance-0.3.0.pkl")
