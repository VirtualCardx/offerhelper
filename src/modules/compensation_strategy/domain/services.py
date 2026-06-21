from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from src.shared.presentation.errors import DomainValidationError


CRPoint = Literal["min", "target", "max"]


@dataclass(frozen=True)
class CRFactor:
    factor_code: str
    weight: Decimal
    min_value: Decimal
    target_value: Decimal
    max_value: Decimal

    def value_at(self, point: CRPoint) -> Decimal:
        return {
            "min": self.min_value,
            "target": self.target_value,
            "max": self.max_value,
        }[point]


class CRCalculationService:
    def calculate(self, factors: list[CRFactor], selected_point: CRPoint = "target") -> Decimal:
        if not factors:
            raise DomainValidationError("At least one CR factor is required.")

        total_weight = sum((factor.weight for factor in factors), start=Decimal("0"))
        if total_weight <= Decimal("0"):
            raise DomainValidationError("Total CR factor weight must be greater than zero.")

        weighted_score = sum(
            (factor.value_at(selected_point) * factor.weight for factor in factors),
            start=Decimal("0"),
        )
        return (weighted_score / total_weight).quantize(Decimal("0.0001"))
