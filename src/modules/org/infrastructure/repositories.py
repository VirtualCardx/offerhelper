from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from src.modules.org.infrastructure.models import CompanyModel, DepartmentModel, PositionModel


@dataclass(frozen=True)
class Company:
    id: str
    name: str
    industry: str
    tenant_code: str


@dataclass(frozen=True)
class Department:
    id: str
    company_id: str
    name: str
    domain: str


@dataclass(frozen=True)
class Position:
    id: str
    company_id: str
    title: str
    job_family: str
    level_band: str


class OrgRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_companies(self) -> list[Company]:
        statement = select(CompanyModel).order_by(CompanyModel.name.asc())
        return [self._to_company(item) for item in self.session.execute(statement).scalars().all()]

    def list_departments(self, *, company_id: str | None = None) -> list[Department]:
        statement: Select[tuple[DepartmentModel]] = select(DepartmentModel)
        if company_id is not None:
            statement = statement.where(DepartmentModel.company_id == company_id)
        statement = statement.order_by(DepartmentModel.name.asc())
        return [self._to_department(item) for item in self.session.execute(statement).scalars().all()]

    def list_positions(self, *, company_id: str | None = None) -> list[Position]:
        statement: Select[tuple[PositionModel]] = select(PositionModel)
        if company_id is not None:
            statement = statement.where(PositionModel.company_id == company_id)
        statement = statement.order_by(PositionModel.title.asc())
        return [self._to_position(item) for item in self.session.execute(statement).scalars().all()]

    @staticmethod
    def _to_company(record: CompanyModel) -> Company:
        return Company(
            id=record.id,
            name=record.name,
            industry=record.industry,
            tenant_code=record.tenant_code,
        )

    @staticmethod
    def _to_department(record: DepartmentModel) -> Department:
        return Department(
            id=record.id,
            company_id=record.company_id,
            name=record.name,
            domain=record.domain,
        )

    @staticmethod
    def _to_position(record: PositionModel) -> Position:
        return Position(
            id=record.id,
            company_id=record.company_id,
            title=record.title,
            job_family=record.job_family,
            level_band=record.level_band,
        )
