from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.modules.candidate.infrastructure.models import CandidateModel
from src.modules.compensation_strategy.infrastructure.models import CompensationStrategyModel
from src.shared.infrastructure.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OfferModel(Base):
    __tablename__ = "offers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"), nullable=False, index=True)
    market_snapshot_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    strategy_id: Mapped[str] = mapped_column(
        ForeignKey("compensation_strategies.id"),
        nullable=False,
        index=True,
    )
    recommended_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    range_min: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    range_max: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cr_value: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    accept_probability: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    acceptance_model_version: Mapped[str] = mapped_column(String(50), nullable=False, default="0.1.0")
    competitiveness_score: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    budget_usage_ratio: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    budget_risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    equity_score: Mapped[int] = mapped_column(Integer, nullable=False, default=70)
    equity_risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="LOW")
    equity_p25: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    equity_p50: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    equity_p75: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    inversion_detected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    equity_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    overall_risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    outcome_status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", index=True)
    outcome_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    candidate: Mapped[CandidateModel] = relationship()
    strategy: Mapped[CompensationStrategyModel] = relationship()
    risk_assessment: Mapped["OfferRiskAssessmentModel"] = relationship(
        back_populates="offer",
        cascade="all, delete-orphan",
        uselist=False,
    )
    reports: Mapped[list["OfferReportModel"]] = relationship(
        back_populates="offer",
        cascade="all, delete-orphan",
    )


class OfferRiskAssessmentModel(Base):
    __tablename__ = "offer_risk_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    offer_id: Mapped[str] = mapped_column(ForeignKey("offers.id"), nullable=False, unique=True, index=True)
    reasons: Mapped[str] = mapped_column(Text, nullable=False, default="")

    offer: Mapped[OfferModel] = relationship(back_populates="risk_assessment")


class OfferReportModel(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    offer_id: Mapped[str] = mapped_column(ForeignKey("offers.id"), nullable=False, index=True)
    report_type: Mapped[str] = mapped_column(String(30), nullable=False, default="MARKDOWN")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    offer: Mapped[OfferModel] = relationship(back_populates="reports")
