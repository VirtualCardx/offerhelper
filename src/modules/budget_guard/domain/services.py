from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class BudgetAssessment:
    usage_ratio: Decimal
    risk_level: str
    capped_offer: Decimal
    exceeded: bool


class BudgetGuardService:
    def assess(self, budget_limit: Decimal, proposed_offer: Decimal) -> BudgetAssessment:
        usage_ratio = Decimal("0")
        if budget_limit > Decimal("0"):
            usage_ratio = (proposed_offer / budget_limit).quantize(Decimal("0.0001"))

        exceeded = proposed_offer > budget_limit
        capped_offer = min(proposed_offer, budget_limit).quantize(Decimal("0.01"))

        if not exceeded:
            risk_level = "LOW"
        elif usage_ratio > Decimal("1.10"):
            risk_level = "HIGH"
        else:
            risk_level = "MEDIUM"

        return BudgetAssessment(
            usage_ratio=usage_ratio,
            risk_level=risk_level,
            capped_offer=capped_offer,
            exceeded=exceeded,
        )
