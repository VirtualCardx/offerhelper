from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RiskAssessment:
    overall_risk: str
    reasons: list[str]


class RiskEngine:
    def evaluate(
        self,
        *,
        raise_ratio: Decimal,
        above_market_p75: bool,
        budget_exceeded: bool,
        budget_usage_ratio: Decimal,
        equity_risk_level: str = "LOW",
        inversion_detected: bool = False,
    ) -> RiskAssessment:
        reasons: list[str] = []
        overall_risk = "GREEN"

        if raise_ratio > Decimal("0.30"):
            reasons.append("salary_increase_over_30_percent")
            overall_risk = "YELLOW"

        if above_market_p75:
            reasons.append("offer_above_market_p75")
            overall_risk = "YELLOW"

        if budget_exceeded:
            reasons.append("offer_capped_by_budget")
            overall_risk = "RED" if budget_usage_ratio > Decimal("1.10") else "YELLOW"

        if equity_risk_level == "YELLOW":
            reasons.append("equity_above_team_p75")
            overall_risk = "YELLOW" if overall_risk != "RED" else overall_risk

        if inversion_detected:
            reasons.append("pay_inversion_detected")
            overall_risk = "RED"

        return RiskAssessment(overall_risk=overall_risk, reasons=reasons)
