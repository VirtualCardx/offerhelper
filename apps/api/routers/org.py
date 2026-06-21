from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.modules.org.infrastructure.repositories import OrgRepository
from src.shared.infrastructure.db.session import get_db_session


router = APIRouter(prefix="/org", tags=["Organization"])


class CompanyResponse(BaseModel):
    id: str
    name: str
    industry: str
    tenant_code: str = Field(alias="tenantCode")


class DepartmentResponse(BaseModel):
    id: str
    company_id: str = Field(alias="companyId")
    name: str
    domain: str


class PositionResponse(BaseModel):
    id: str
    company_id: str = Field(alias="companyId")
    title: str
    job_family: str = Field(alias="jobFamily")
    level_band: str = Field(alias="levelBand")


@router.get("/companies", response_model=list[CompanyResponse])
async def list_companies(session: Session = Depends(get_db_session)) -> list[CompanyResponse]:
    repository = OrgRepository(session)
    return [
        CompanyResponse(
            id=item.id,
            name=item.name,
            industry=item.industry,
            tenantCode=item.tenant_code,
        )
        for item in repository.list_companies()
    ]


@router.get("/departments", response_model=list[DepartmentResponse])
async def list_departments(
    company_id: str | None = Query(default=None, alias="companyId"),
    session: Session = Depends(get_db_session),
) -> list[DepartmentResponse]:
    repository = OrgRepository(session)
    return [
        DepartmentResponse(
            id=item.id,
            companyId=item.company_id,
            name=item.name,
            domain=item.domain,
        )
        for item in repository.list_departments(company_id=company_id)
    ]


@router.get("/positions", response_model=list[PositionResponse])
async def list_positions(
    company_id: str | None = Query(default=None, alias="companyId"),
    session: Session = Depends(get_db_session),
) -> list[PositionResponse]:
    repository = OrgRepository(session)
    return [
        PositionResponse(
            id=item.id,
            companyId=item.company_id,
            title=item.title,
            jobFamily=item.job_family,
            levelBand=item.level_band,
        )
        for item in repository.list_positions(company_id=company_id)
    ]
