import json
import pickle
from decimal import Decimal

from src.modules.acceptance_prediction.domain.services import (
    AcceptancePredictionInput,
    AcceptancePredictionService,
    AcceptancePredictionServiceFactory,
    RegisteredModel,
    WeightedProbabilityModel,
)


def test_acceptance_prediction_returns_versioned_probability() -> None:
    service = AcceptancePredictionService()

    result = service.predict(
        AcceptancePredictionInput(
            current_salary=Decimal("30000"),
            recommended_offer=Decimal("39501.00"),
            market_p50=Decimal("35000"),
            interview_score=95,
            has_other_offer=True,
        )
    )

    assert result.probability == Decimal("0.77")
    assert result.model_name == "baseline-offer-acceptance"
    assert result.model_version == "0.1.0"


def test_acceptance_prediction_changes_after_model_switch() -> None:
    factory = AcceptancePredictionServiceFactory()
    service = factory.create(
        RegisteredModel(
            model_name="baseline-offer-acceptance",
            model_version="0.2.0",
            framework="rule-based",
            artifact_uri="registry://baseline-offer-acceptance/0.2.0",
            config={
                "base_probability": "0.52",
                "offer_market_bonus": "0.15",
                "raise_bonus": "0.12",
                "high_score_bonus": "0.08",
                "medium_score_bonus": "0.04",
                "competing_offer_penalty": "0.04",
            },
        )
    )

    result = service.predict(
        AcceptancePredictionInput(
            current_salary=Decimal("30000"),
            recommended_offer=Decimal("39501.00"),
            market_p50=Decimal("35000"),
            interview_score=95,
            has_other_offer=True,
        )
    )

    assert result.probability == Decimal("0.83")
    assert result.model_version == "0.2.0"


def test_factory_creates_binary_inference_service_from_pickle_artifact(tmp_path) -> None:
    model_path = tmp_path / "baseline-offer-acceptance-0.3.0.pkl"
    manifest_path = tmp_path / "baseline-offer-acceptance-0.3.0.json"

    with model_path.open("wb") as artifact_file:
        pickle.dump(
            WeightedProbabilityModel(
                intercept=-0.61,
                coefficients=[1.0, 0.8, 0.01, -0.25],
            ),
            artifact_file,
        )

    manifest_path.write_text(
        json.dumps(
            {
                "modelName": "baseline-offer-acceptance",
                "modelVersion": "0.3.0",
                "framework": "xgboost",
                "runtime": {
                    "type": "python-pickle-proba",
                    "modelPath": model_path.name,
                    "featureOrder": [
                        "offer_to_market_ratio",
                        "raise_ratio",
                        "interview_score",
                        "has_other_offer",
                    ],
                },
                "config": {
                    "probability_floor": "0.10",
                    "probability_ceiling": "0.95",
                },
            }
        ),
        encoding="utf-8",
    )

    factory = AcceptancePredictionServiceFactory()
    service = factory.create(
        RegisteredModel(
            model_name="baseline-offer-acceptance",
            model_version="0.3.0",
            framework="xgboost",
            artifact_uri=manifest_path.as_uri(),
            config={
                "_runtime": {
                    "type": "python-pickle-proba",
                    "modelPath": model_path.name,
                    "resolvedModelPath": str(model_path),
                    "featureOrder": [
                        "offer_to_market_ratio",
                        "raise_ratio",
                        "interview_score",
                        "has_other_offer",
                    ],
                },
                "probability_floor": "0.10",
                "probability_ceiling": "0.95",
            },
        )
    )

    result = service.predict(
        AcceptancePredictionInput(
            current_salary=Decimal("30000"),
            recommended_offer=Decimal("39501.00"),
            market_p50=Decimal("35000"),
            interview_score=95,
            has_other_offer=True,
        )
    )

    assert result.probability == Decimal("0.81")
    assert result.model_version == "0.3.0"
