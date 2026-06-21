from __future__ import annotations

import json
from decimal import Decimal

from src.modules.acceptance_prediction.application.artifacts import ModelArtifactLoader
from src.modules.acceptance_prediction.application.exporter import AcceptanceModelArtifactExporter
from src.modules.acceptance_prediction.application.exporter import AcceptanceTrainingSample
from src.modules.acceptance_prediction.application.trainer import AcceptanceModelTrainer
from src.modules.acceptance_prediction.domain.services import (
    AcceptancePredictionInput,
    AcceptancePredictionServiceFactory,
    RegisteredModel,
)


def test_trainer_fits_coefficients_from_training_samples() -> None:
    trainer = AcceptanceModelTrainer()
    training_samples = [
        AcceptanceTrainingSample(
            current_salary=Decimal("30000"),
            recommended_offer=Decimal("36000"),
            market_p50=Decimal("35000"),
            interview_score=84,
            has_other_offer=False,
            accepted=True,
        ),
        AcceptanceTrainingSample(
            current_salary=Decimal("30000"),
            recommended_offer=Decimal("33000"),
            market_p50=Decimal("35000"),
            interview_score=76,
            has_other_offer=True,
            accepted=False,
        ),
        AcceptanceTrainingSample(
            current_salary=Decimal("29000"),
            recommended_offer=Decimal("39000"),
            market_p50=Decimal("36000"),
            interview_score=93,
            has_other_offer=False,
            accepted=True,
        ),
        AcceptanceTrainingSample(
            current_salary=Decimal("34000"),
            recommended_offer=Decimal("35000"),
            market_p50=Decimal("38000"),
            interview_score=74,
            has_other_offer=True,
            accepted=False,
        ),
    ]

    trained = trainer.train(
        training_samples=training_samples,
        feature_order=[
            "offer_to_market_ratio",
            "raise_ratio",
            "interview_score",
            "has_other_offer",
        ],
    )

    assert trained.sample_count == 4
    assert len(trained.coefficients) == 4
    assert 0.5 <= trained.accuracy <= 1.0
    assert trained.log_loss >= 0.0


def test_trained_coefficients_can_be_used_by_runtime_service(tmp_path) -> None:
    trainer = AcceptanceModelTrainer()
    training_samples = [
        AcceptanceTrainingSample(
            current_salary=Decimal("30000"),
            recommended_offer=Decimal("36000"),
            market_p50=Decimal("35000"),
            interview_score=84,
            has_other_offer=False,
            accepted=True,
        ),
        AcceptanceTrainingSample(
            current_salary=Decimal("30000"),
            recommended_offer=Decimal("33000"),
            market_p50=Decimal("35000"),
            interview_score=76,
            has_other_offer=True,
            accepted=False,
        ),
        AcceptanceTrainingSample(
            current_salary=Decimal("29000"),
            recommended_offer=Decimal("39000"),
            market_p50=Decimal("36000"),
            interview_score=93,
            has_other_offer=False,
            accepted=True,
        ),
        AcceptanceTrainingSample(
            current_salary=Decimal("34000"),
            recommended_offer=Decimal("35000"),
            market_p50=Decimal("38000"),
            interview_score=74,
            has_other_offer=True,
            accepted=False,
        ),
    ]
    trained = trainer.train(
        training_samples=training_samples,
        feature_order=[
            "offer_to_market_ratio",
            "raise_ratio",
            "interview_score",
            "has_other_offer",
        ],
    )

    exported = AcceptanceModelArtifactExporter().export(
        model_name="baseline-offer-acceptance",
        model_version="fit-test",
        framework="xgboost",
        output_dir=tmp_path,
        feature_order=trained.feature_order,
        intercept=trained.intercept,
        coefficients=trained.coefficients,
        training_samples=training_samples,
        metrics={
            "trainingAccuracy": round(trained.accuracy, 4),
            "trainingLogLoss": round(trained.log_loss, 6),
        },
    )
    payload = json.loads(exported.manifest_path.read_text(encoding="utf-8"))
    assert payload["metrics"]["trainingAccuracy"] >= 0.5

    runtime_model = ModelArtifactLoader().load_runtime_model(
        RegisteredModel(
            model_name="baseline-offer-acceptance",
            model_version="fit-test",
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

    assert result.model_version == "fit-test"
    assert Decimal("0.10") <= result.probability <= Decimal("0.95")
