from __future__ import annotations


class OfferReportService:
    def generate_markdown(
        self,
        *,
        candidate_name: str,
        level: str,
        city: str,
        market_p50: str,
        market_p75: str,
        strategy_name: str,
        recommended_offer: str,
        cr_value: str,
        accept_probability: str,
        budget_risk: str,
        equity_risk: str,
        equity_message: str,
        overall_risk: str,
        risk_reasons: list[str],
    ) -> str:
        reason_lines = "\n".join(f"- {reason}" for reason in risk_reasons) if risk_reasons else "- no_material_risk"
        return (
            f"# Offer Recommendation Report\n\n"
            f"## Candidate Summary\n"
            f"- Name: {candidate_name}\n"
            f"- Level: {level}\n"
            f"- City: {city}\n\n"
            f"## Market Analysis\n"
            f"- Market P50: {market_p50}\n"
            f"- Market P75: {market_p75}\n\n"
            f"## Compensation Strategy\n"
            f"- Strategy: {strategy_name}\n"
            f"- CR Value: {cr_value}\n\n"
            f"## Recommendation\n"
            f"- Recommended Offer: {recommended_offer}\n"
            f"- Acceptance Probability: {accept_probability}\n\n"
            f"## Risk Summary\n"
            f"- Overall Risk: {overall_risk}\n"
            f"- Budget Risk: {budget_risk}\n"
            f"- Equity Risk: {equity_risk}\n"
            f"- Equity Message: {equity_message}\n\n"
            f"## Risk Reasons\n"
            f"{reason_lines}\n"
        )
