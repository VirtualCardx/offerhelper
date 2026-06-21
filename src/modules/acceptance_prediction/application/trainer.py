from __future__ import annotations

import math
from dataclasses import dataclass

from src.modules.acceptance_prediction.application.exporter import AcceptanceTrainingSample
from src.modules.acceptance_prediction.domain.services import AcceptancePredictionFeatureExtractor


@dataclass(frozen=True)
class TrainedAcceptanceModel:
    feature_order: list[str]
    intercept: float
    coefficients: list[float]
    accuracy: float
    log_loss: float
    sample_count: int


class AcceptanceModelTrainer:
    def train(
        self,
        *,
        training_samples: list[AcceptanceTrainingSample],
        feature_order: list[str],
        epochs: int = 400,
        learning_rate: float = 0.35,
    ) -> TrainedAcceptanceModel:
        if not training_samples:
            raise ValueError("At least one training sample is required for model training.")

        raw_features = [
            AcceptancePredictionFeatureExtractor.vectorize(sample.to_prediction_input(), feature_order)
            for sample in training_samples
        ]
        labels = [1.0 if sample.accepted else 0.0 for sample in training_samples]

        means = [sum(row[index] for row in raw_features) / len(raw_features) for index in range(len(feature_order))]
        stds = []
        for index in range(len(feature_order)):
            variance = sum((row[index] - means[index]) ** 2 for row in raw_features) / len(raw_features)
            std_value = math.sqrt(variance)
            stds.append(std_value if std_value > 1e-9 else 1.0)

        normalized_features = [
            [(row[index] - means[index]) / stds[index] for index in range(len(feature_order))]
            for row in raw_features
        ]

        intercept = 0.0
        coefficients = [0.0 for _ in feature_order]

        for _ in range(epochs):
            intercept_gradient = 0.0
            coefficient_gradients = [0.0 for _ in feature_order]
            for row, label in zip(normalized_features, labels):
                prediction = self._sigmoid(intercept + sum(weight * value for weight, value in zip(coefficients, row)))
                error = prediction - label
                intercept_gradient += error
                for index, feature_value in enumerate(row):
                    coefficient_gradients[index] += error * feature_value

            sample_count = float(len(training_samples))
            intercept -= learning_rate * (intercept_gradient / sample_count)
            coefficients = [
                weight - learning_rate * (gradient / sample_count)
                for weight, gradient in zip(coefficients, coefficient_gradients)
            ]

        raw_intercept = intercept
        raw_coefficients: list[float] = []
        for index, weight in enumerate(coefficients):
            scaled_weight = weight / stds[index]
            raw_coefficients.append(scaled_weight)
            raw_intercept -= scaled_weight * means[index]

        predictions = [
            self._sigmoid(raw_intercept + sum(weight * value for weight, value in zip(raw_coefficients, row)))
            for row in raw_features
        ]
        accuracy = sum(
            1 for prediction, label in zip(predictions, labels) if (prediction >= 0.5) == bool(label)
        ) / len(predictions)
        log_loss = -sum(
            label * math.log(max(prediction, 1e-9)) + (1.0 - label) * math.log(max(1.0 - prediction, 1e-9))
            for prediction, label in zip(predictions, labels)
        ) / len(predictions)

        return TrainedAcceptanceModel(
            feature_order=feature_order,
            intercept=raw_intercept,
            coefficients=raw_coefficients,
            accuracy=accuracy,
            log_loss=log_loss,
            sample_count=len(training_samples),
        )

    @staticmethod
    def _sigmoid(value: float) -> float:
        return 1.0 / (1.0 + math.exp(-value))
