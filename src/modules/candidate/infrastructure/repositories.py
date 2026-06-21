from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from src.modules.candidate.domain.entities import CandidateProfile
from src.modules.candidate.infrastructure.models import CandidateModel
from src.shared.presentation.errors import DomainValidationError


def _serialize_skills(skills: list[str]) -> str:
    return ",".join(skill.strip() for skill in skills if skill.strip())


def _deserialize_skills(value: str) -> list[str]:
    if not value:
        return []
    return [skill for skill in value.split(",") if skill]


class CandidateRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, profile: CandidateProfile) -> CandidateProfile:
        candidate = CandidateModel(
            id=profile.id,
            company_id=profile.company_id,
            department_id=profile.department_id,
            position_id=profile.position_id,
            name=profile.name,
            current_salary=profile.current_salary,
            expected_salary=profile.expected_salary,
            years_experience=profile.years_experience,
            level=profile.level,
            skills=_serialize_skills(profile.skills),
            interview_score=profile.interview_score,
            has_other_offer=profile.has_other_offer,
            city=profile.city,
        )
        self.session.add(candidate)
        self.session.commit()
        self.session.refresh(candidate)
        return self._to_domain(candidate)

    def get_by_id(self, candidate_id: str) -> CandidateProfile:
        candidate = self.session.get(CandidateModel, candidate_id)
        if candidate is None:
            raise DomainValidationError(f"Candidate '{candidate_id}' does not exist.")
        return self._to_domain(candidate)

    def list_candidates(
        self,
        *,
        company_id: str | None = None,
        department_id: str | None = None,
        position_id: str | None = None,
        limit: int = 100,
    ) -> list[CandidateProfile]:
        query = self.session.query(CandidateModel)
        if company_id is not None:
            query = query.filter(CandidateModel.company_id == company_id)
        if department_id is not None:
            query = query.filter(CandidateModel.department_id == department_id)
        if position_id is not None:
            query = query.filter(CandidateModel.position_id == position_id)
        records = query.order_by(CandidateModel.created_at.desc()).limit(limit).all()
        return [self._to_domain(item) for item in records]

    @staticmethod
    def _to_domain(candidate: CandidateModel) -> CandidateProfile:
        return CandidateProfile(
            id=candidate.id,
            company_id=candidate.company_id,
            department_id=candidate.department_id,
            position_id=candidate.position_id,
            name=candidate.name,
            current_salary=Decimal(candidate.current_salary),
            expected_salary=Decimal(candidate.expected_salary) if candidate.expected_salary is not None else None,
            years_experience=candidate.years_experience,
            level=candidate.level,
            skills=_deserialize_skills(candidate.skills),
            interview_score=candidate.interview_score,
            has_other_offer=candidate.has_other_offer,
            city=candidate.city,
        )
