from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from src.modules.acceptance_prediction.domain.services import (
    AcceptancePredictionFeatureExtractor,
    AcceptancePredictionInput,
    WeightedProbabilityModel,
)


@dataclass(frozen=True)
class AcceptanceTrainingSample:
    current_salary: Decimal
    recommended_offer: Decimal
    market_p50: Decimal
    interview_score: int
    has_other_offer: bool
    accepted: bool

    def to_prediction_input(self) -> AcceptancePredictionInput:
        return AcceptancePredictionInput(
            current_salary=self.current_salary,
            recommended_offer=self.recommended_offer,
            market_p50=self.market_p50,
            interview_score=self.interview_score,
            has_other_offer=self.has_other_offer,
        )


@dataclass(frozen=True)
class ExportedModelArtifact:
    manifest_path: Path
    model_path: Path
    sample_count: int
    acceptance_rate: Decimal


class AcceptanceModelArtifactExporter:
    def export(
        self,
        *,
        model_name: str,
        model_version: str,
        framework: str,
        output_dir: Path,
        feature_order: list[str],
        intercept: float,
        coefficients: list[float],
        training_samples: list[AcceptanceTrainingSample],
        metrics: dict[str, object] | None = None,
        probability_floor: Decimal = Decimal("0.10"),
        probability_ceiling: Decimal = Decimal("0.95"),
    ) -> ExportedModelArtifact:
        output_dir.mkdir(parents=True, exist_ok=True)
        file_stem = f"{model_name}-{model_version}"
        manifest_path = output_dir / f"{file_stem}.json"
        model_path = output_dir / f"{file_stem}.pkl"

        weighted_model = WeightedProbabilityModel(intercept=intercept, coefficients=coefficients)
        with model_path.open("wb") as artifact_file:
            pickle.dump(weighted_model, artifact_file)

        training_summary = self._build_training_summary(training_samples, feature_order)
        manifest_payload = {
            "modelName": model_name,
            "modelVersion": model_version,
            "framework": framework,
            "runtime": {
                "type": "python-pickle-proba",
                "modelPath": model_path.name,
                "featureOrder": feature_order,
            },
            "config": {
                "probability_floor": str(probability_floor),
                "probability_ceiling": str(probability_ceiling),
            },
            "metrics": {
                **(metrics or {}),
                "trainingSampleCount": training_summary["sampleCount"],
                "trainingAcceptanceRate": training_summary["acceptanceRate"],
            },
            "trainingSummary": training_summary,
        }
        manifest_path.write_text(json.dumps(manifest_payload, indent=2), encoding="utf-8")

        return ExportedModelArtifact(
            manifest_path=manifest_path,
            model_path=model_path,
            sample_count=training_summary["sampleCount"],
            acceptance_rate=Decimal(training_summary["acceptanceRate"]),
        )

    @staticmethod
    def _build_training_summary(
        training_samples: list[AcceptanceTrainingSample],
        feature_order: list[str],
    ) -> dict[str, object]:
        if not training_samples:
            raise ValueError("At least one training sample is required to export a model artifact.")

        accepted_count = sum(1 for sample in training_samples if sample.accepted)
        feature_totals = {feature_name: Decimal("0") for feature_name in feature_order}

        for sample in training_samples:
            feature_map = AcceptancePredictionFeatureExtractor.build_feature_map(sample.to_prediction_input())
            for feature_name in feature_order:
                if feature_name not in feature_map:
                    raise ValueError(f"Unsupported feature '{feature_name}' in export feature order.")
                feature_totals[feature_name] += feature_map[feature_name]

        sample_count = len(training_samples)
        feature_averages = {
            feature_name: str((total / Decimal(sample_count)).quantize(Decimal("0.0001")))
            for feature_name, total in feature_totals.items()
        }
        acceptance_rate = (Decimal(accepted_count) / Decimal(sample_count)).quantize(Decimal("0.0001"))

        return {
            "sampleCount": sample_count,
            "acceptedCount": accepted_count,
            "acceptanceRate": str(acceptance_rate),
            "featureAverages": feature_averages,
        }
