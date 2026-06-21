from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class OfferDecisionInput:
    current_salary: Decimal
    market_p50: Decimal
    market_p75: Decimal
    cr_value: Decimal
    interview_score: int
    has_other_offer: bool
    budget_limit: Decimal


@dataclass(frozen=True)
class OfferDecisionResult:
    raw_offer: Decimal
    recommended_offer: Decimal
    range_min: Decimal
    range_max: Decimal
    competitiveness_score: int
    confidence: Decimal
    raise_ratio: Decimal


class OfferDecisionEngine:
    def recommend(self, data: OfferDecisionInput) -> OfferDecisionResult:
        benchmark = data.market_p50 * data.cr_value
        adjustment_multiplier = Decimal("1.00")

        if data.interview_score >= 90:
            adjustment_multiplier += Decimal("0.03")
        elif data.interview_score >= 80:
            adjustment_multiplier += Decimal("0.01")

        if data.has_other_offer:
            adjustment_multiplier += Decimal("0.05")

        recommended_offer = (benchmark * adjustment_multiplier).quantize(Decimal("0.01"))
        raw_offer = recommended_offer

        raise_ratio = Decimal("0")
        if data.current_salary > Decimal("0"):
            raise_ratio = (recommended_offer - data.current_salary) / data.current_salary

        if recommended_offer > data.budget_limit:
            recommended_offer = data.budget_limit.quantize(Decimal("0.01"))

        offer_range_min = (recommended_offer * Decimal("0.95")).quantize(Decimal("0.01"))
        offer_range_max = (recommended_offer * Decimal("1.05")).quantize(Decimal("0.01"))

        competitiveness_score = 70
        if recommended_offer >= data.market_p50:
            competitiveness_score += 10
        if recommended_offer >= data.market_p75:
            competitiveness_score += 8
        if data.has_other_offer:
            competitiveness_score += 5
        if recommended_offer >= data.current_salary * Decimal("1.20"):
            competitiveness_score += 5

        return OfferDecisionResult(
            raw_offer=raw_offer,
            recommended_offer=recommended_offer,
            range_min=offer_range_min,
            range_max=offer_range_max,
            competitiveness_score=min(competitiveness_score, 100),
            confidence=Decimal("0.87"),
            raise_ratio=raise_ratio.quantize(Decimal("0.0001")),
        )
