from decimal import Decimal

from src.modules.pay_equity.domain.services import PayEquityEngine, PeerSalary


def test_pay_equity_detects_inversion() -> None:
    engine = PayEquityEngine()

    result = engine.evaluate(
        offer=Decimal("39501.00"),
        peers=[
            PeerSalary(salary=Decimal("35000.00")),
            PeerSalary(salary=Decimal("37000.00")),
        ],
    )

    assert result.equity_score == 60
    assert result.risk_level == "RED"
    assert result.p25 == Decimal("35500.00")
    assert result.p50 == Decimal("36000.00")
    assert result.p75 == Decimal("36500.00")
    assert result.inversion_detected is True
