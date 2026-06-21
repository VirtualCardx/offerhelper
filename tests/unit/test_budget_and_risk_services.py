from decimal import Decimal

from src.modules.budget_guard.domain.services import BudgetGuardService
from src.modules.risk_engine.domain.services import RiskEngine


def test_budget_guard_caps_offer_and_marks_medium_risk() -> None:
    service = BudgetGuardService()

    result = service.assess(
        budget_limit=Decimal("40000"),
        proposed_offer=Decimal("40824.00"),
    )

    assert result.usage_ratio == Decimal("1.0206")
    assert result.risk_level == "MEDIUM"
    assert result.capped_offer == Decimal("40000.00")
    assert result.exceeded is True


def test_risk_engine_marks_red_when_budget_severely_exceeded() -> None:
    engine = RiskEngine()

    result = engine.evaluate(
        raise_ratio=Decimal("0.4500"),
        above_market_p75=True,
        budget_exceeded=True,
        budget_usage_ratio=Decimal("1.1500"),
    )

    assert result.overall_risk == "RED"
    assert "salary_increase_over_30_percent" in result.reasons
    assert "offer_above_market_p75" in result.reasons
    assert "offer_capped_by_budget" in result.reasons
