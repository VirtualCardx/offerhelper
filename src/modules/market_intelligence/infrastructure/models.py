from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.modules.org.infrastructure.models import PositionModel
from src.shared.infrastructure.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MarketSalaryModel(Base):
    __tablename__ = "market_salary"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    position_id: Mapped[str] = mapped_column(ForeignKey("positions.id"), nullable=False, index=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    p25: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    p50: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    p75: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    update_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    position: Mapped[PositionModel] = relationship()
