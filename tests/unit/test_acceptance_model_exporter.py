from __future__ import annotations

import json
from decimal import Decimal

from src.modules.acceptance_prediction.application.exporter import (
    AcceptanceModelArtifactExporter,
    AcceptanceTrainingSample,
)
from src.modules.acceptance_prediction.application.artifacts import ModelArtifactLoader
from src.modules.acceptance_prediction.domain.services import (
    AcceptancePredictionInput,
    AcceptancePredictionServiceFactory,
    RegisteredModel,
)


def test_exporter_writes_standard_manifest_and_pickle(tmp_path) -> None:
    exporter = AcceptanceModelArtifactExporter()
    exported = exporter.export(
        model_name="baseline-offer-acceptance",
        model_version="0.4.0",
        framework="xgboost",
        output_dir=tmp_path,
        feature_order=[
            "offer_to_market_ratio",
            "raise_ratio",
            "interview_score",
            "has_other_offer",
        ],
        intercept=-0.58,
        coefficients=[0.95, 0.72, 0.011, -0.22],
        training_samples=[
            AcceptanceTrainingSample(
                current_salary=Decimal("30000"),
                recommended_offer=Decimal("36000"),
                market_p50=Decimal("35000"),
                interview_score=82,
                has_other_offer=False,
                accepted=True,
            ),
            AcceptanceTrainingSample(
                current_salary=Decimal("30000"),
                recommended_offer=Decimal("33000"),
                market_p50=Decimal("35000"),
                interview_score=78,
                has_other_offer=True,
                accepted=False,
            ),
        ],
        metrics={"auc": 0.87},
    )

    payload = json.loads(exported.manifest_path.read_text(encoding="utf-8"))
    assert exported.model_path.exists()
    assert payload["runtime"]["type"] == "python-pickle-proba"
    assert payload["runtime"]["modelPath"] == exported.model_path.name
    assert payload["metrics"]["trainingSampleCount"] == 2
    assert payload["trainingSummary"]["acceptanceRate"] == "0.5000"


def test_exported_artifact_loads_and_predicts(tmp_path) -> None:
    exporter = AcceptanceModelArtifactExporter()
    exported = exporter.export(
        model_name="baseline-offer-acceptance",
        model_version="0.4.0",
        framework="xgboost",
        output_dir=tmp_path,
        feature_order=[
            "offer_to_market_ratio",
            "raise_ratio",
            "interview_score",
            "has_other_offer",
        ],
        intercept=-0.58,
        coefficients=[0.95, 0.72, 0.011, -0.22],
        training_samples=[
            AcceptanceTrainingSample(
                current_salary=Decimal("30000"),
                recommended_offer=Decimal("36000"),
                market_p50=Decimal("35000"),
                interview_score=82,
                has_other_offer=False,
                accepted=True,
            ),
            AcceptanceTrainingSample(
                current_salary=Decimal("30000"),
                recommended_offer=Decimal("33000"),
                market_p50=Decimal("35000"),
                interview_score=78,
                has_other_offer=True,
                accepted=False,
            ),
        ],
    )

    loader = ModelArtifactLoader()
    runtime_model = loader.load_runtime_model(
        RegisteredModel(
            model_name="baseline-offer-acceptance",
            model_version="0.4.0",
            framework="xgboost",
            artifact_uri=exported.manifest_path.as_uri(),
            config={},
        )
    )
    service = AcceptancePredictionServiceFactory().create(runtime_model)
    result = service.predict(
        AcceptancePredictionInput(
            current_salary=Decimal("30000"),
            recommended_offer=Decimal("39501.00"),
            market_p50=Decimal("35000"),
            interview_score=95,
            has_other_offer=True,
        )
    )

    assert result.model_version == "0.4.0"
    assert Decimal("0.10") <= result.probability <= Decimal("0.95")
