from decimal import Decimal

import pytest

from src.modules.compensation_strategy.domain.services import CRCalculationService, CRFactor
from src.shared.presentation.errors import DomainValidationError


def test_calculate_target_cr_value() -> None:
    service = CRCalculationService()

    result = service.calculate(
        factors=[
            CRFactor("company", Decimal("0.3"), Decimal("0.8"), Decimal("1.0"), Decimal("1.1")),
            CRFactor("domain", Decimal("0.3"), Decimal("0.9"), Decimal("1.05"), Decimal("1.2")),
            CRFactor("department", Decimal("0.2"), Decimal("0.95"), Decimal("1.0"), Decimal("1.15")),
            CRFactor("talent", Decimal("0.2"), Decimal("1.0"), Decimal("1.15"), Decimal("1.3")),
        ]
    )

    assert result == Decimal("1.0450")


def test_reject_empty_factor_list() -> None:
    service = CRCalculationService()

    with pytest.raises(DomainValidationError):
        service.calculate(factors=[])
