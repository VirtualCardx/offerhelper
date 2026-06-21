from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.pay_equity.domain.services import PeerSalary
from src.modules.pay_equity.infrastructure.models import EmployeeSalaryModel
from src.shared.presentation.errors import DomainValidationError


@dataclass(frozen=True)
class EmployeeSalaryRecord:
    id: str
    company_id: str
    department_id: str
    position_id: str
    level: str
    salary: Decimal


class EmployeeSalaryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        company_id: str,
        department_id: str,
        position_id: str,
        level: str,
        salary: Decimal,
    ) -> EmployeeSalaryRecord:
        record = EmployeeSalaryModel(
            id=str(uuid.uuid4()),
            company_id=company_id,
            department_id=department_id,
            position_id=position_id,
            level=level,
            salary=salary,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self._to_domain(record)

    def list_peer_salaries(self, *, company_id: str, department_id: str, level: str) -> list[PeerSalary]:
        stmt = select(EmployeeSalaryModel).where(
            EmployeeSalaryModel.company_id == company_id,
            EmployeeSalaryModel.department_id == department_id,
            EmployeeSalaryModel.level == level,
        )
        records = self.session.execute(stmt).scalars().all()
        return [PeerSalary(salary=Decimal(record.salary)) for record in records]

    def list_records(self, *, company_id: str, department_id: str, level: str) -> list[EmployeeSalaryRecord]:
        stmt = select(EmployeeSalaryModel).where(
            EmployeeSalaryModel.company_id == company_id,
            EmployeeSalaryModel.department_id == department_id,
            EmployeeSalaryModel.level == level,
        )
        records = self.session.execute(stmt).scalars().all()
        return [self._to_domain(record) for record in records]

    def get_by_id(self, record_id: str) -> EmployeeSalaryRecord:
        record = self.session.get(EmployeeSalaryModel, record_id)
        if record is None:
            raise DomainValidationError(f"Employee salary record '{record_id}' does not exist.")
        return self._to_domain(record)

    def update(
        self,
        record_id: str,
        *,
        company_id: str,
        department_id: str,
        position_id: str,
        level: str,
        salary: Decimal,
    ) -> EmployeeSalaryRecord:
        record = self.session.get(EmployeeSalaryModel, record_id)
        if record is None:
            raise DomainValidationError(f"Employee salary record '{record_id}' does not exist.")
        record.company_id = company_id
        record.department_id = department_id
        record.position_id = position_id
        record.level = level
        record.salary = salary
        self.session.commit()
        self.session.refresh(record)
        return self._to_domain(record)

    def delete(self, record_id: str) -> None:
        record = self.session.get(EmployeeSalaryModel, record_id)
        if record is None:
            raise DomainValidationError(f"Employee salary record '{record_id}' does not exist.")
        self.session.delete(record)
        self.session.commit()

    @staticmethod
    def _to_domain(record: EmployeeSalaryModel) -> EmployeeSalaryRecord:
        return EmployeeSalaryRecord(
            id=record.id,
            company_id=record.company_id,
            department_id=record.department_id,
            position_id=record.position_id,
            level=record.level,
            salary=Decimal(record.salary),
        )
