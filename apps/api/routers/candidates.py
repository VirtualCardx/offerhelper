from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends
from fastapi import Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.modules.candidate.domain.entities import CandidateProfile
from src.modules.candidate.infrastructure.repositories import CandidateRepository
from src.shared.infrastructure.db.session import get_db_session


router = APIRouter(prefix="/candidates", tags=["Candidates"])


class CandidateCreateRequest(BaseModel):
    company_id: str = Field(alias="companyId")
    department_id: str = Field(alias="departmentId")
    position_id: str = Field(alias="positionId")
    name: str
    current_salary: Decimal = Field(alias="currentSalary")
    expected_salary: Decimal | None = Field(default=None, alias="expectedSalary")
    years_experience: int = Field(alias="yearsExperience")
    level: str
    skills: list[str]
    interview_score: int = Field(alias="interviewScore")
    has_other_offer: bool = Field(alias="hasOtherOffer")
    city: str


class CandidateResponse(BaseModel):
    id: str
    company_id: str = Field(alias="companyId")
    department_id: str = Field(alias="departmentId")
    position_id: str = Field(alias="positionId")
    name: str
    current_salary: Decimal = Field(alias="currentSalary")
    expected_salary: Decimal | None = Field(alias="expectedSalary")
    years_experience: int = Field(alias="yearsExperience")
    level: str
    skills: list[str]
    interview_score: int = Field(alias="interviewScore")
    has_other_offer: bool = Field(alias="hasOtherOffer")
    city: str


def _to_response(profile: CandidateProfile) -> CandidateResponse:
    return CandidateResponse(
        id=profile.id,
        companyId=profile.company_id,
        departmentId=profile.department_id,
        positionId=profile.position_id,
        name=profile.name,
        currentSalary=profile.current_salary,
        expectedSalary=profile.expected_salary,
        yearsExperience=profile.years_experience,
        level=profile.level,
        skills=profile.skills,
        interviewScore=profile.interview_score,
        hasOtherOffer=profile.has_other_offer,
        city=profile.city,
    )


@router.post("", response_model=CandidateResponse)
async def create_candidate(
    request: CandidateCreateRequest,
    session: Session = Depends(get_db_session),
) -> CandidateResponse:
    repository = CandidateRepository(session)
    candidate = repository.create(
        CandidateProfile(
            id=str(uuid.uuid4()),
            company_id=request.company_id,
            department_id=request.department_id,
            position_id=request.position_id,
            name=request.name,
            current_salary=request.current_salary,
            expected_salary=request.expected_salary,
            years_experience=request.years_experience,
            level=request.level,
            skills=request.skills,
            interview_score=request.interview_score,
            has_other_offer=request.has_other_offer,
            city=request.city,
        )
    )
    return _to_response(candidate)


@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: str,
    session: Session = Depends(get_db_session),
) -> CandidateResponse:
    repository = CandidateRepository(session)
    return _to_response(repository.get_by_id(candidate_id))


@router.get("", response_model=list[CandidateResponse])
async def list_candidates(
    company_id: str | None = Query(default=None, alias="companyId"),
    department_id: str | None = Query(default=None, alias="departmentId"),
    position_id: str | None = Query(default=None, alias="positionId"),
    limit: int = Query(default=100, ge=1, le=200),
    session: Session = Depends(get_db_session),
) -> list[CandidateResponse]:
    repository = CandidateRepository(session)
    return [
        _to_response(item)
        for item in repository.list_candidates(
            company_id=company_id,
            department_id=department_id,
            position_id=position_id,
            limit=limit,
        )
    ]
