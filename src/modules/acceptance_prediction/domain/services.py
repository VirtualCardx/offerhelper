from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import math
import pickle
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class AcceptancePredictionInput:
    current_salary: Decimal
    recommended_offer: Decimal
    market_p50: Decimal
    interview_score: int
    has_other_offer: bool


@dataclass(frozen=True)
class AcceptancePredictionResult:
    probability: Decimal
    model_version: str
    model_name: str


DEFAULT_FEATURE_ORDER = [
    "current_salary",
    "recommended_offer",
    "market_p50",
    "interview_score",
    "has_other_offer",
    "offer_to_market_ratio",
    "raise_ratio",
]


class ProbabilityModelProtocol(Protocol):
    def predict_proba(self, rows: list[list[float]]) -> object: ...


class AcceptancePredictionFeatureExtractor:
    @staticmethod
    def build_feature_map(data: AcceptancePredictionInput) -> dict[str, Decimal]:
        offer_to_market_ratio = Decimal("0")
        if data.market_p50 > Decimal("0"):
            offer_to_market_ratio = data.recommended_offer / data.market_p50

        raise_ratio = Decimal("0")
        if data.current_salary > Decimal("0"):
            raise_ratio = (data.recommended_offer - data.current_salary) / data.current_salary

        return {
            "current_salary": data.current_salary,
            "recommended_offer": data.recommended_offer,
            "market_p50": data.market_p50,
            "interview_score": Decimal(data.interview_score),
            "has_other_offer": Decimal("1") if data.has_other_offer else Decimal("0"),
            "offer_to_market_ratio": offer_to_market_ratio,
            "raise_ratio": raise_ratio,
        }

    @classmethod
    def vectorize(cls, data: AcceptancePredictionInput, feature_order: list[str]) -> list[float]:
        feature_map = cls.build_feature_map(data)
        vector: list[float] = []
        for feature_name in feature_order:
            if feature_name not in feature_map:
                raise ValueError(f"Unsupported feature '{feature_name}' in model artifact.")
            vector.append(float(feature_map[feature_name]))
        return vector


class WeightedProbabilityModel:
    """Minimal scikit-compatible demo model for local artifact inference."""

    def __init__(self, *, intercept: float, coefficients: list[float]) -> None:
        self.intercept = intercept
        self.coefficients = coefficients

    def predict_proba(self, rows: list[list[float]]) -> list[list[float]]:
        results: list[list[float]] = []
        for row in rows:
            if len(row) != len(self.coefficients):
                raise ValueError("Feature vector size does not match weighted model coefficients.")
            logit = self.intercept + sum(
                coefficient * value for coefficient, value in zip(self.coefficients, row)
            )
            probability = 1.0 / (1.0 + math.exp(-logit))
            results.append([1.0 - probability, probability])
        return results


class AcceptancePredictionService:
    def __init__(
        self,
        *,
        model_name: str = "baseline-offer-acceptance",
        model_version: str = "0.1.0",
        base_probability: Decimal = Decimal("0.55"),
        offer_market_bonus: Decimal = Decimal("0.12"),
        raise_bonus: Decimal = Decimal("0.10"),
        high_score_bonus: Decimal = Decimal("0.06"),
        medium_score_bonus: Decimal = Decimal("0.03"),
        competing_offer_penalty: Decimal = Decimal("0.06"),
    ) -> None:
        self.model_name = model_name
        self.model_version = model_version
        self.base_probability = base_probability
        self.offer_market_bonus = offer_market_bonus
        self.raise_bonus = raise_bonus
        self.high_score_bonus = high_score_bonus
        self.medium_score_bonus = medium_score_bonus
        self.competing_offer_penalty = competing_offer_penalty

    def predict(self, data: AcceptancePredictionInput) -> AcceptancePredictionResult:
        probability = self.base_probability

        if data.recommended_offer >= data.market_p50:
            probability += self.offer_market_bonus
        if data.current_salary > Decimal("0") and data.recommended_offer >= data.current_salary * Decimal("1.20"):
            probability += self.raise_bonus
        if data.interview_score >= 90:
            probability += self.high_score_bonus
        elif data.interview_score >= 80:
            probability += self.medium_score_bonus
        if data.has_other_offer:
            probability -= self.competing_offer_penalty

        probability = min(max(probability, Decimal("0.10")), Decimal("0.95")).quantize(Decimal("0.01"))
        return AcceptancePredictionResult(
            probability=probability,
            model_version=self.model_version,
            model_name=self.model_name,
        )


class BinaryArtifactAcceptancePredictionService(AcceptancePredictionService):
    def __init__(
        self,
        *,
        model_name: str,
        model_version: str,
        model: ProbabilityModelProtocol,
        feature_order: list[str],
        probability_floor: Decimal = Decimal("0.10"),
        probability_ceiling: Decimal = Decimal("0.95"),
    ) -> None:
        self.model_name = model_name
        self.model_version = model_version
        self.model = model
        self.feature_order = feature_order
        self.probability_floor = probability_floor
        self.probability_ceiling = probability_ceiling

    def predict(self, data: AcceptancePredictionInput) -> AcceptancePredictionResult:
        features = AcceptancePredictionFeatureExtractor.vectorize(data, self.feature_order)
        raw_probabilities = self.model.predict_proba([features])
        probability = self._extract_positive_probability(raw_probabilities)
        probability = min(max(probability, self.probability_floor), self.probability_ceiling).quantize(
            Decimal("0.01")
        )
        return AcceptancePredictionResult(
            probability=probability,
            model_version=self.model_version,
            model_name=self.model_name,
        )

    @staticmethod
    def _extract_positive_probability(raw_probabilities: object) -> Decimal:
        try:
            first_row = raw_probabilities[0]
        except (IndexError, TypeError) as exc:
            raise ValueError("Model prediction result does not contain probabilities.") from exc

        if isinstance(first_row, (list, tuple)):
            if not first_row:
                raise ValueError("Model prediction result is empty.")
            value = first_row[-1]
        else:
            value = first_row

        return Decimal(str(value))


@dataclass(frozen=True)
class RegisteredModel:
    model_name: str
    model_version: str
    framework: str
    artifact_uri: str
    config: dict[str, object]


class AcceptancePredictionServiceFactory:
    def create(self, registered_model: RegisteredModel) -> AcceptancePredictionService:
        if registered_model.framework not in {"rule-based", "sklearn", "xgboost"}:
            raise ValueError(f"Unsupported framework '{registered_model.framework}'.")

        if registered_model.framework == "rule-based":
            return AcceptancePredictionService(
                model_name=registered_model.model_name,
                model_version=registered_model.model_version,
                base_probability=Decimal(str(registered_model.config.get("base_probability", "0.55"))),
                offer_market_bonus=Decimal(str(registered_model.config.get("offer_market_bonus", "0.12"))),
                raise_bonus=Decimal(str(registered_model.config.get("raise_bonus", "0.10"))),
                high_score_bonus=Decimal(str(registered_model.config.get("high_score_bonus", "0.06"))),
                medium_score_bonus=Decimal(str(registered_model.config.get("medium_score_bonus", "0.03"))),
                competing_offer_penalty=Decimal(str(registered_model.config.get("competing_offer_penalty", "0.06"))),
            )

        runtime = registered_model.config.get("_runtime")
        if not isinstance(runtime, dict):
            raise ValueError("Model runtime metadata is required for binary inference artifacts.")

        runtime_type = str(runtime.get("type", ""))
        if runtime_type != "python-pickle-proba":
            raise ValueError(f"Unsupported runtime type '{runtime_type}'.")

        model_path = str(runtime.get("resolvedModelPath") or runtime.get("modelPath") or "")
        feature_order = runtime.get("featureOrder")
        if not model_path:
            raise ValueError("Model runtime metadata must include a modelPath.")
        if not isinstance(feature_order, list) or not feature_order or not all(
            isinstance(feature_name, str) for feature_name in feature_order
        ):
            raise ValueError("Model runtime metadata must include a non-empty featureOrder.")

        model = self._load_pickle_model(Path(model_path))
        return BinaryArtifactAcceptancePredictionService(
            model_name=registered_model.model_name,
            model_version=registered_model.model_version,
            model=model,
            feature_order=feature_order,
            probability_floor=Decimal(str(registered_model.config.get("probability_floor", "0.10"))),
            probability_ceiling=Decimal(str(registered_model.config.get("probability_ceiling", "0.95"))),
        )

    @staticmethod
    def _load_pickle_model(path: Path) -> ProbabilityModelProtocol:
        with path.open("rb") as artifact_file:
            model = pickle.load(artifact_file)
        if not hasattr(model, "predict_proba") or not callable(model.predict_proba):
            raise ValueError(f"Artifact '{path}' does not expose a callable predict_proba method.")
        return model
