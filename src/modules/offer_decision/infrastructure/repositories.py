from __future__ import annotations

import uuid
from datetime import datetime, timezone
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from src.modules.offer_decision.infrastructure.models import OfferModel, OfferReportModel, OfferRiskAssessmentModel
from src.shared.presentation.errors import DomainValidationError


@dataclass(frozen=True)
class SavedOffer:
    id: str
    candidate_id: str
    market_snapshot_id: str | None
    strategy_id: str
    recommended_salary: Decimal
    range_min: Decimal
    range_max: Decimal
    cr_value: Decimal
    accept_probability: Decimal
    acceptance_model_version: str
    competitiveness_score: int
    confidence: Decimal
    budget_usage_ratio: Decimal
    budget_risk_level: str
    equity_score: int
    equity_risk_level: str
    equity_p25: Decimal
    equity_p50: Decimal
    equity_p75: Decimal
    inversion_detected: bool
    equity_message: str
    overall_risk_level: str
    outcome_status: str
    outcome_notes: str | None
    decided_at: datetime | None
    risk_reasons: list[str]
    report_markdown: str | None


class OfferRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        candidate_id: str,
        market_snapshot_id: str | None,
        strategy_id: str,
        recommended_salary: Decimal,
        range_min: Decimal,
        range_max: Decimal,
        cr_value: Decimal,
        accept_probability: Decimal,
        acceptance_model_version: str,
        competitiveness_score: int,
        confidence: Decimal,
        budget_usage_ratio: Decimal,
        budget_risk_level: str,
        equity_score: int,
        equity_risk_level: str,
        equity_p25: Decimal,
        equity_p50: Decimal,
        equity_p75: Decimal,
        inversion_detected: bool,
        equity_message: str,
        overall_risk_level: str,
        risk_reasons: list[str],
        outcome_status: str = "PENDING",
        outcome_notes: str = "",
        decided_at: datetime | None = None,
    ) -> SavedOffer:
        offer = OfferModel(
            id=str(uuid.uuid4()),
            candidate_id=candidate_id,
            market_snapshot_id=market_snapshot_id,
            strategy_id=strategy_id,
            recommended_salary=recommended_salary,
            range_min=range_min,
            range_max=range_max,
            cr_value=cr_value,
            accept_probability=accept_probability,
            acceptance_model_version=acceptance_model_version,
            competitiveness_score=competitiveness_score,
            confidence=confidence,
            budget_usage_ratio=budget_usage_ratio,
            budget_risk_level=budget_risk_level,
            equity_score=equity_score,
            equity_risk_level=equity_risk_level,
            equity_p25=equity_p25,
            equity_p50=equity_p50,
            equity_p75=equity_p75,
            inversion_detected=1 if inversion_detected else 0,
            equity_message=equity_message,
            overall_risk_level=overall_risk_level,
            outcome_status=outcome_status,
            outcome_notes=outcome_notes,
            decided_at=decided_at,
        )
        self.session.add(offer)
        self.session.flush()
        self.session.add(
            OfferRiskAssessmentModel(
                offer_id=offer.id,
                reasons=",".join(risk_reasons),
            )
        )
        self.session.commit()
        self.session.refresh(offer)
        return self.get_by_id(offer.id)

    def update_outcome(
        self,
        *,
        offer_id: str,
        outcome_status: str,
        outcome_notes: str = "",
        decided_at: datetime | None = None,
    ) -> SavedOffer:
        offer = self.session.get(OfferModel, offer_id)
        if offer is None:
            raise DomainValidationError(f"Offer '{offer_id}' does not exist.")
        offer.outcome_status = outcome_status
        offer.outcome_notes = outcome_notes
        offer.decided_at = decided_at or datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(offer)
        return self.get_by_id(offer.id)

    def get_by_id(self, offer_id: str) -> SavedOffer:
        stmt = (
            select(OfferModel)
            .options(
                joinedload(OfferModel.risk_assessment),
                joinedload(OfferModel.reports),
            )
            .where(OfferModel.id == offer_id)
        )
        offer = self.session.execute(stmt).unique().scalar_one_or_none()
        if offer is None:
            raise DomainValidationError(f"Offer '{offer_id}' does not exist.")
        return self._to_domain(offer)

    def list_offers(
        self,
        *,
        candidate_id: str | None = None,
        strategy_id: str | None = None,
        risk_level: str | None = None,
    ) -> list[SavedOffer]:
        stmt = select(OfferModel).options(
            joinedload(OfferModel.risk_assessment),
            joinedload(OfferModel.reports),
        )
        if candidate_id is not None:
            stmt = stmt.where(OfferModel.candidate_id == candidate_id)
        if strategy_id is not None:
            stmt = stmt.where(OfferModel.strategy_id == strategy_id)
        if risk_level is not None:
            stmt = stmt.where(OfferModel.overall_risk_level == risk_level)

        offers = self.session.execute(stmt.order_by(OfferModel.created_at.desc())).unique().scalars().all()
        return [self._to_domain(offer) for offer in offers]

    def save_report(self, *, offer_id: str, content: str, report_type: str = "MARKDOWN") -> str:
        report = OfferReportModel(
            id=str(uuid.uuid4()),
            offer_id=offer_id,
            report_type=report_type,
            content=content,
        )
        self.session.add(report)
        self.session.commit()
        return report.id

    @staticmethod
    def _to_domain(offer: OfferModel) -> SavedOffer:
        reasons: list[str] = []
        if offer.risk_assessment and offer.risk_assessment.reasons:
            reasons = [item for item in offer.risk_assessment.reasons.split(",") if item]
        latest_report = None
        if offer.reports:
            latest_report = sorted(offer.reports, key=lambda item: item.created_at)[-1].content
        return SavedOffer(
            id=offer.id,
            candidate_id=offer.candidate_id,
            market_snapshot_id=offer.market_snapshot_id,
            strategy_id=offer.strategy_id,
            recommended_salary=Decimal(offer.recommended_salary),
            range_min=Decimal(offer.range_min),
            range_max=Decimal(offer.range_max),
            cr_value=Decimal(offer.cr_value),
            accept_probability=Decimal(offer.accept_probability),
            acceptance_model_version=offer.acceptance_model_version,
            competitiveness_score=offer.competitiveness_score,
            confidence=Decimal(offer.confidence),
            budget_usage_ratio=Decimal(offer.budget_usage_ratio),
            budget_risk_level=offer.budget_risk_level,
            equity_score=offer.equity_score,
            equity_risk_level=offer.equity_risk_level,
            equity_p25=Decimal(offer.equity_p25),
            equity_p50=Decimal(offer.equity_p50),
            equity_p75=Decimal(offer.equity_p75),
            inversion_detected=bool(offer.inversion_detected),
            equity_message=offer.equity_message,
            overall_risk_level=offer.overall_risk_level,
            outcome_status=offer.outcome_status,
            outcome_notes=offer.outcome_notes or None,
            decided_at=offer.decided_at,
            risk_reasons=reasons,
            report_markdown=latest_report,
        )
