from decimal import Decimal

from src.modules.offer_decision.domain.services import OfferDecisionEngine, OfferDecisionInput


def test_recommend_offer_with_budget_cap() -> None:
    engine = OfferDecisionEngine()

    result = engine.recommend(
        OfferDecisionInput(
            current_salary=Decimal("30000"),
            market_p50=Decimal("35000"),
            market_p75=Decimal("45000"),
            cr_value=Decimal("1.08"),
            interview_score=90,
            has_other_offer=True,
            budget_limit=Decimal("40000"),
        )
    )

    assert result.raw_offer == Decimal("40824.00")
    assert result.recommended_offer == Decimal("40000.00")
    assert result.range_min == Decimal("38000.00")
    assert result.range_max == Decimal("42000.00")
    assert result.raise_ratio == Decimal("0.3608")


def test_cap_offer_by_budget() -> None:
    engine = OfferDecisionEngine()

    result = engine.recommend(
        OfferDecisionInput(
            current_salary=Decimal("25000"),
            market_p50=Decimal("40000"),
            market_p75=Decimal("50000"),
            cr_value=Decimal("1.20"),
            interview_score=95,
            has_other_offer=True,
            budget_limit=Decimal("42000"),
        )
    )

    assert result.raw_offer == Decimal("51840.00")
    assert result.recommended_offer == Decimal("42000.00")
    assert result.raise_ratio == Decimal("1.0736")
