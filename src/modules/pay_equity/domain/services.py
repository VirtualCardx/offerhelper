from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PeerSalary:
    salary: Decimal


@dataclass(frozen=True)
class EquityResult:
    equity_score: int
    risk_level: str
    message: str
    p25: Decimal
    p50: Decimal
    p75: Decimal
    inversion_detected: bool


class PayEquityEngine:
    def evaluate(self, offer: Decimal, peers: list[PeerSalary]) -> EquityResult:
        if not peers:
            return EquityResult(
                equity_score=70,
                risk_level="LOW",
                message="No peer salary data available; equity check uses limited evidence.",
                p25=offer,
                p50=offer,
                p75=offer,
                inversion_detected=False,
            )

        sorted_values = sorted(peer.salary for peer in peers)
        p25 = self._percentile(sorted_values, Decimal("0.25"))
        p50 = self._percentile(sorted_values, Decimal("0.50"))
        p75 = self._percentile(sorted_values, Decimal("0.75"))
        max_peer = sorted_values[-1]

        equity_score = 90
        risk_level = "LOW"
        message = "Offer is within the team's reasonable salary range."
        inversion_detected = False

        if offer > p75:
            equity_score = 78
            risk_level = "YELLOW"
            message = "Offer is above the team's P75 salary benchmark."

        if offer > (max_peer * Decimal("1.05")).quantize(Decimal("0.01")):
            equity_score = 60
            risk_level = "RED"
            message = "Offer may cause pay inversion for peers in the same level."
            inversion_detected = True

        return EquityResult(
            equity_score=equity_score,
            risk_level=risk_level,
            message=message,
            p25=p25,
            p50=p50,
            p75=p75,
            inversion_detected=inversion_detected,
        )

    @staticmethod
    def _percentile(values: list[Decimal], percentile: Decimal) -> Decimal:
        if len(values) == 1:
            return values[0].quantize(Decimal("0.01"))

        position = percentile * Decimal(len(values) - 1)
        lower_index = int(position)
        upper_index = min(lower_index + 1, len(values) - 1)
        fraction = position - Decimal(lower_index)
        lower_value = values[lower_index]
        upper_value = values[upper_index]
        return (lower_value + (upper_value - lower_value) * fraction).quantize(Decimal("0.01"))
