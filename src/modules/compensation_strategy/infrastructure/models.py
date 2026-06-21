from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.modules.org.infrastructure.models import CompanyModel
from src.shared.infrastructure.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CompensationStrategyModel(Base):
    __tablename__ = "compensation_strategies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    budget_policy_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    company: Mapped[CompanyModel] = relationship()
    factors: Mapped[list["CompensationStrategyFactorModel"]] = relationship(
        back_populates="strategy",
        cascade="all, delete-orphan",
    )


class CompensationStrategyFactorModel(Base):
    __tablename__ = "compensation_strategy_factors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id: Mapped[str] = mapped_column(
        ForeignKey("compensation_strategies.id"),
        nullable=False,
        index=True,
    )
    factor_code: Mapped[str] = mapped_column(String(100), nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    min_value: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    target_value: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    max_value: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    strategy: Mapped[CompensationStrategyModel] = relationship(back_populates="factors")
