from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class MarketSalarySnapshot:
    id: str
    position_id: str
    city: str
    p25: Decimal
    p50: Decimal
    p75: Decimal
    source: str
    update_time: datetime
