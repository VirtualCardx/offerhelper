from __future__ import annotations

from decimal import Decimal

from src.modules.acceptance_prediction.application.exporter import AcceptanceTrainingSample


def build_demo_training_samples() -> list[AcceptanceTrainingSample]:
    return [
        AcceptanceTrainingSample(
            current_salary=Decimal("30000"),
            recommended_offer=Decimal("36000"),
            market_p50=Decimal("35000"),
            interview_score=82,
            has_other_offer=False,
            accepted=True,
        ),
        AcceptanceTrainingSample(
            current_salary=Decimal("30000"),
            recommended_offer=Decimal("33000"),
            market_p50=Decimal("35000"),
            interview_score=78,
            has_other_offer=True,
            accepted=False,
        ),
        AcceptanceTrainingSample(
            current_salary=Decimal("28000"),
            recommended_offer=Decimal("35500"),
            market_p50=Decimal("34000"),
            interview_score=88,
            has_other_offer=False,
            accepted=True,
        ),
        AcceptanceTrainingSample(
            current_salary=Decimal("32000"),
            recommended_offer=Decimal("36000"),
            market_p50=Decimal("37000"),
            interview_score=75,
            has_other_offer=True,
            accepted=False,
        ),
        AcceptanceTrainingSample(
            current_salary=Decimal("31000"),
            recommended_offer=Decimal("39500"),
            market_p50=Decimal("36000"),
            interview_score=93,
            has_other_offer=True,
            accepted=True,
        ),
        AcceptanceTrainingSample(
            current_salary=Decimal("29000"),
            recommended_offer=Decimal("34500"),
            market_p50=Decimal("35500"),
            interview_score=80,
            has_other_offer=False,
            accepted=True,
        ),
        AcceptanceTrainingSample(
            current_salary=Decimal("34000"),
            recommended_offer=Decimal("36500"),
            market_p50=Decimal("38000"),
            interview_score=77,
            has_other_offer=True,
            accepted=False,
        ),
        AcceptanceTrainingSample(
            current_salary=Decimal("30500"),
            recommended_offer=Decimal("39000"),
            market_p50=Decimal("36000"),
            interview_score=91,
            has_other_offer=False,
            accepted=True,
        ),
    ]
