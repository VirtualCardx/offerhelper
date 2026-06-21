from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.modules.org.infrastructure.models import CompanyModel, DepartmentModel, PositionModel
from src.shared.infrastructure.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EmployeeSalaryModel(Base):
    __tablename__ = "employee_salary"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    department_id: Mapped[str] = mapped_column(ForeignKey("departments.id"), nullable=False, index=True)
    position_id: Mapped[str] = mapped_column(ForeignKey("positions.id"), nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    company: Mapped[CompanyModel] = relationship()
    department: Mapped[DepartmentModel] = relationship()
    position: Mapped[PositionModel] = relationship()
