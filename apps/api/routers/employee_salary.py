from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.modules.pay_equity.infrastructure.repositories import EmployeeSalaryRepository
from src.shared.infrastructure.db.session import get_db_session


router = APIRouter(prefix="/employee-salary", tags=["Employee Salary"])


class EmployeeSalaryCreateRequest(BaseModel):
    company_id: str = Field(alias="companyId")
    department_id: str = Field(alias="departmentId")
    position_id: str = Field(alias="positionId")
    level: str
    salary: Decimal


class EmployeeSalaryUpdateRequest(BaseModel):
    company_id: str = Field(alias="companyId")
    department_id: str = Field(alias="departmentId")
    position_id: str = Field(alias="positionId")
    level: str
    salary: Decimal


class EmployeeSalaryResponse(BaseModel):
    id: str
    company_id: str = Field(alias="companyId")
    department_id: str = Field(alias="departmentId")
    position_id: str = Field(alias="positionId")
    level: str
    salary: Decimal


@router.post("", response_model=EmployeeSalaryResponse)
async def create_employee_salary(
    request: EmployeeSalaryCreateRequest,
    session: Session = Depends(get_db_session),
) -> EmployeeSalaryResponse:
    repository = EmployeeSalaryRepository(session)
    record = repository.create(
        company_id=request.company_id,
        department_id=request.department_id,
        position_id=request.position_id,
        level=request.level,
        salary=request.salary,
    )
    return EmployeeSalaryResponse(
        id=record.id,
        companyId=record.company_id,
        departmentId=record.department_id,
        positionId=record.position_id,
        level=record.level,
        salary=record.salary,
    )


@router.get("", response_model=list[EmployeeSalaryResponse])
async def list_employee_salary(
    company_id: str = Query(alias="companyId"),
    department_id: str = Query(alias="departmentId"),
    level: str = Query(...),
    session: Session = Depends(get_db_session),
) -> list[EmployeeSalaryResponse]:
    repository = EmployeeSalaryRepository(session)
    records = repository.list_records(
        company_id=company_id,
        department_id=department_id,
        level=level,
    )
    return [
        EmployeeSalaryResponse(
            id=record.id,
            companyId=record.company_id,
            departmentId=record.department_id,
            positionId=record.position_id,
            level=record.level,
            salary=record.salary,
        )
        for record in records
    ]


@router.patch("/{record_id}", response_model=EmployeeSalaryResponse)
async def update_employee_salary(
    record_id: str,
    request: EmployeeSalaryUpdateRequest,
    session: Session = Depends(get_db_session),
) -> EmployeeSalaryResponse:
    repository = EmployeeSalaryRepository(session)
    record = repository.update(
        record_id,
        company_id=request.company_id,
        department_id=request.department_id,
        position_id=request.position_id,
        level=request.level,
        salary=request.salary,
    )
    return EmployeeSalaryResponse(
        id=record.id,
        companyId=record.company_id,
        departmentId=record.department_id,
        positionId=record.position_id,
        level=record.level,
        salary=record.salary,
    )


@router.delete("/{record_id}", status_code=204)
async def delete_employee_salary(
    record_id: str,
    session: Session = Depends(get_db_session),
) -> None:
    repository = EmployeeSalaryRepository(session)
    repository.delete(record_id)
